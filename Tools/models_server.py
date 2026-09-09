"""
models_server — 冶金平台统一模型微服务 (FastAPI)

启动:
  cd Tools && uvicorn models_server:app --reload --port 8002

API 文档:
  GET  /api/v1/models               — 列出所有已注册模型
  GET  /api/v1/models/{model_id}    — 获取单个模型详情（含 Schema）
  POST /api/v1/models/{model_id}/invoke  — 调用模型
  GET  /api/v1/health               — 健康检查
"""
from __future__ import annotations
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

# 确保 models_core 可导入
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from models_core import ModelRegistry
from models_core.artifacts import ArtifactError
from models_core.base import InvocationContext
from models_core.services import (
    ExperimentService,
    InMemoryTraceStore,
    ModelExecutionService,
)
from models_core.scenes import SceneError, SceneOrchestrationService

# ── 初始化注册表 ──
registry = ModelRegistry()
count = registry.discover()
print(f"[models-server] registered {count} models: {[m.model_id for m in registry._models.values()]}")


def _load_experiment_eligibility_snapshot() -> dict:
    """Load the frozen acceptance set without re-running any tool qualification cases."""
    snapshot_path = Path(__file__).with_name("tool_eligibility_snapshot_20260903.json")
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "snapshot_id": None, "tools": {}, "errors": [str(exc)]}
    records = payload.get("tools") or []
    errors = []
    approved = {}
    if payload.get("expected_registered_count") != len(registry._models):
        errors.append(
            f"registered_count changed: expected {payload.get('expected_registered_count')}, "
            f"actual {len(registry._models)}"
        )
    for record in records:
        code = record.get("model_code")
        model = registry.get(code) if code else None
        if model is None:
            errors.append(f"snapshot tool missing: {code}")
            continue
        if model.tool_name != record.get("tool_name") or model.version != record.get("model_version"):
            errors.append(f"snapshot identity/version mismatch: {code}")
            continue
        approved[code] = record
    if len(approved) != payload.get("expected_registered_count"):
        errors.append(
            f"approved tool count mismatch: expected {payload.get('expected_registered_count')}, "
            f"actual {len(approved)}"
        )
    return {
        "valid": not errors,
        "snapshot_id": payload.get("snapshot_id"),
        "frozen_at": payload.get("frozen_at"),
        "source_reports": payload.get("source_reports") or [],
        "tools": approved,
        "errors": errors,
    }


experiment_eligibility_snapshot = _load_experiment_eligibility_snapshot()
trace_store = InMemoryTraceStore()
execution_service = ModelExecutionService(registry, trace_store)
experiment_service = ExperimentService(registry, execution_service, trace_store)
scene_service = SceneOrchestrationService(registry, execution_service, trace_store)

# ── FastAPI 应用 ──
app = FastAPI(
    title="冶金平台 — 统一模型微服务",
    version="0.2.0",
    description="真实可执行冶金工具的统一注册、调用与校验服务",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 请求/响应模型 ──

class InvokeRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "input": {"reaction": "FeO + C → Fe + CO", "temperature": 1873},
            "options": {"validate_boundary": True, "return_provenance": True},
        }
    })
    input: dict = Field(..., description="模型输入参数，根据 input_schema 定义")
    options: dict = Field(default_factory=lambda: {
        "validate_boundary": True,
        "return_provenance": True,
    })

class InvokeResponse(BaseModel):
    trace_id: str
    model_id: str
    model_version: str
    status: str  # success / rejected / error
    boundary_check: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    confidence: Optional[float] = None
    provenance: Optional[list] = None
    runtime_ms: float = 0.0


class ModelDetailResponse(BaseModel):
    model_id: str
    name: str
    scenario: str
    model_type: str
    api_name: str
    version: str
    priority: str
    applicable_boundary: str
    input_schema_json: dict
    output_schema_json: dict
    validation_rules: list


class ValidateRequest(BaseModel):
    input: dict = Field(..., description="待校验的模型输入参数")


class ToolCallRequest(BaseModel):
    """大模型function call的统一参数信封。"""
    arguments: dict = Field(..., description="必须符合工具parameters JSON Schema")
    options: dict = Field(default_factory=lambda: {
        "validate_boundary": True,
        "return_provenance": True,
    }, description=(
        "执行选项；可用artifact={mode:directory|directory_and_zip,name?:安全文件名}"
        "把成功执行导出到项目固定目录。G005继续使用arguments.artifact_mode。"
    ))


class ArtifactRequest(BaseModel):
    """把一个已成功执行记录导出为可读取结果包。"""
    mode: str = Field(default="directory", description="directory / directory_and_zip")
    name: Optional[str] = Field(default=None, description="可选安全文件名，不是调用者路径")


class ExperimentRequest(BaseModel):
    user_query: str
    mode: str = Field(..., description="direct / forced / autonomous")
    model_code: Optional[str] = None
    arguments: dict = Field(default_factory=dict)
    baseline_answer: str = ""
    llm_name: str = "external-orchestrator"
    prompt_version: str = "v1"
    result_validation_enabled: bool = True
    artifact: Optional[ArtifactRequest] = Field(
        default=None,
        description="可选文件产物请求；G005映射为原生案例包，其他工具生成统一结果包",
    )


class SceneRunRequest(BaseModel):
    selected_steps: Optional[list[str]] = None
    arguments_by_step: dict = Field(default_factory=dict)
    options: dict = Field(default_factory=lambda: {
        "stop_on_error": True,
        "artifact_steps": [],
        "artifact_mode": "directory_and_zip",
    })


class WorkOrderCompileRequest(BaseModel):
    run_id: str
    title: Optional[str] = None
    operator_notes: str = ""


class WorkOrderReviewRequest(BaseModel):
    action: str
    reviewer: str
    comment: str = ""


# ── API 路由 ──

@app.get("/api/v1/health")
def health():
    counts = registry.get_counts()
    return {
        "status": "ok",
        "service": "models-server",
        **counts,
        "registered_models": counts["registered_count"],
        "model_ids": sorted(registry._models.keys()),
    }


@app.get("/api/models")
@app.get("/api/v1/models")
def list_models(scenario: Optional[str] = None):
    """列出所有模型，可按场景筛选"""
    if scenario:
        models = registry.list_by_scenario(scenario)
    else:
        models = registry.list_models()

    return {
        **registry.get_counts(),
        "total": len(models),
        "models": models,
    }


@app.get("/api/tools")
@app.get("/api/v1/tools")
def list_llm_tools(
    fully_eligible: bool = True,
    scenario: Optional[str] = None,
):
    """返回大模型可直接使用的function-tool清单，默认只暴露最终合格项。"""
    tools = registry.list_tool_definitions(
        fully_eligible_only=fully_eligible,
        scenario=scenario,
    )
    for definition in tools:
        model = registry.get(definition["model_code"])
        definition["artifact_capability"] = execution_service.artifact_service.capability(model)
    return {
        **registry.get_counts(),
        "fully_eligible_filter": fully_eligible,
        "total": len(tools),
        "tools": tools,
        "call_endpoint_template": "/api/v1/tools/{function.name}/call",
    }


@app.get("/api/v1/experiments/tool-registry")
def list_experiment_llm_tools(scenario: Optional[str] = None):
    """Return the frozen 120-tool experiment catalog without re-running acceptance tests."""
    snapshot = experiment_eligibility_snapshot
    if not snapshot["valid"]:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "TOOL_ELIGIBILITY_SNAPSHOT_INVALID",
                "errors": snapshot["errors"],
            },
        )
    tools = []
    for model_code in sorted(snapshot["tools"]):
        model = registry.get(model_code)
        if scenario and model.scenario != scenario:
            continue
        definition = model.get_tool_definition({"fully_eligible": True})
        definition["eligibility_source"] = "frozen_acceptance_snapshot"
        definition["eligibility_snapshot_id"] = snapshot["snapshot_id"]
        definition["artifact_capability"] = execution_service.artifact_service.capability(model)
        tools.append(definition)
    return {
        "registered_count": len(registry._models),
        "qualified_executable_count": len(snapshot["tools"]),
        "fully_eligible_count": len(snapshot["tools"]),
        "qualification_execution_count": 0,
        "eligibility_source": "frozen_acceptance_snapshot",
        "eligibility_snapshot_id": snapshot["snapshot_id"],
        "eligibility_frozen_at": snapshot["frozen_at"],
        "source_reports": snapshot["source_reports"],
        "input_contract_complete_count": sum(
            tool["input_contract"]["status"] == "complete" for tool in tools
        ),
        "input_contract_incomplete_count": sum(
            tool["input_contract"]["status"] != "complete" for tool in tools
        ),
        "total": len(tools),
        "tools": tools,
        "call_endpoint_template": "/api/v1/experiments/tools/{function.name}/call",
    }


@app.get("/api/models/{model_id}")
@app.get("/api/v1/models/{model_id}")
def get_model(model_id: str):
    """获取单个模型详情"""
    model = registry.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"未知模型: {model_id}")
    entry = next(
        entry for entry in registry.list_models()
        if entry["model_code"] == model_id
    )
    entry["artifact_capability"] = execution_service.artifact_service.capability(model)
    return entry


@app.get("/api/tools/{tool_name}")
@app.get("/api/v1/tools/{tool_name}")
def get_llm_tool(tool_name: str):
    """读取单个最终合格的大模型工具定义。"""
    model = registry.get_by_tool_name(tool_name)
    if not model:
        known = registry.get_by_tool_name(tool_name, fully_eligible_only=False)
        if known:
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "TOOL_NOT_FULLY_ELIGIBLE",
                    "model_code": known.model_id,
                    "eligibility": registry.eligibility_report(known.model_id),
                },
            )
        raise HTTPException(status_code=404, detail=f"未知工具函数: {tool_name}")
    definition = model.get_tool_definition(registry.eligibility_report(model.model_id))
    definition["artifact_capability"] = execution_service.artifact_service.capability(model)
    return definition


@app.post("/api/v1/models/{model_id}/invoke", response_model=InvokeResponse)
def invoke_model(model_id: str, req: InvokeRequest):
    """调用模型执行计算"""
    model = registry.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"未知模型: {model_id}")

    trace_id = f"TRACE-{uuid.uuid4().hex[:12].upper()}"
    ctx = InvocationContext(
        user_or_agent="api",
        trace_id=trace_id,
        validate_boundary=req.options.get("validate_boundary", True),
        return_provenance=req.options.get("return_provenance", True),
    )

    result = registry.invoke(model_id, req.input, ctx)

    status_map = {
        True: "success",
        False: "rejected" if result.error_code != "INTERNAL_ERROR" else "error",
    }

    return InvokeResponse(
        trace_id=result.trace_id,
        model_id=model_id,
        model_version=model.version,
        status=status_map.get(result.success, "error"),
        boundary_check={
            "passed": result.boundary_check.passed,
            "warnings": [{"field": w.field, "message": w.message, "level": w.level}
                         for w in result.boundary_check.warnings],
        } if result.boundary_check else None,
        result=result.result,
        error=result.error,
        error_code=result.error_code,
        confidence=result.confidence,
        provenance=[{"dataset_id": p.dataset_id, "name": p.name, "version": p.version}
                     for p in result.provenance] if result.provenance else None,
        runtime_ms=result.runtime_ms,
    )


@app.post("/api/models/{model_id}/validate")
@app.post("/api/v1/models/{model_id}/validate")
def validate_model(model_id: str, req: ValidateRequest):
    """仅执行格式、单位枚举和适用域前置校验。"""
    return execution_service.validate(model_id, req.input)


@app.post("/api/models/{model_id}/execute")
@app.post("/api/v1/models/{model_id}/execute")
def execute_model(model_id: str, req: InvokeRequest):
    """按统一协议执行模型并保存完整执行轨迹。"""
    return execution_service.execute(
        model_id,
        req.input,
        options=req.options,
        user_or_agent="api",
    )


@app.post("/api/tools/{tool_name}/call")
@app.post("/api/v1/tools/{tool_name}/call")
def call_llm_tool(tool_name: str, req: ToolCallRequest):
    """执行大模型function call；未通过四维资格的工具不会进入此入口。"""
    model = registry.get_by_tool_name(tool_name)
    if not model:
        known = registry.get_by_tool_name(tool_name, fully_eligible_only=False)
        if known:
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "TOOL_NOT_FULLY_ELIGIBLE",
                    "model_code": known.model_id,
                    "eligibility": registry.eligibility_report(known.model_id),
                },
            )
        raise HTTPException(status_code=404, detail=f"未知工具函数: {tool_name}")
    return execution_service.execute(
        model.model_id,
        req.arguments,
        options=req.options,
        user_or_agent="llm-function-call",
    )


@app.post("/api/v1/experiments/tools/{tool_name}/call")
def call_experiment_llm_tool(tool_name: str, req: ToolCallRequest):
    """Execute a frozen-snapshot tool without re-running its accepted qualification cases."""
    snapshot = experiment_eligibility_snapshot
    if not snapshot["valid"]:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "TOOL_ELIGIBILITY_SNAPSHOT_INVALID",
                "errors": snapshot["errors"],
            },
        )
    model = registry.get_by_tool_name(tool_name, fully_eligible_only=False)
    if not model:
        raise HTTPException(status_code=404, detail=f"未知工具函数: {tool_name}")
    if model.model_id not in snapshot["tools"]:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "TOOL_NOT_IN_ELIGIBILITY_SNAPSHOT",
                "model_code": model.model_id,
                "eligibility_snapshot_id": snapshot["snapshot_id"],
            },
        )
    return execution_service.execute(
        model.model_id,
        req.arguments,
        options=req.options,
        user_or_agent="llm-orchestration-experiment",
    )


@app.get("/api/executions/{execution_id}")
@app.get("/api/v1/executions/{execution_id}")
def get_execution(execution_id: str):
    record = trace_store.get_execution(execution_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"未知执行记录: {execution_id}")
    return record


@app.get("/api/v1/artifacts/capabilities")
def list_artifact_capabilities():
    """列出原生案例包和统一执行结果包能力，不增加工具计数。"""
    capabilities = []
    for model in sorted(registry._models.values(), key=lambda item: item.model_id):
        capabilities.append({
            "model_code": model.model_id,
            "name": model.name,
            **execution_service.artifact_service.capability(model),
        })
    return {
        "total": len(capabilities),
        "native_case_bundle_count": sum(item["delivery"] == "native_case_bundle" for item in capabilities),
        "recommended_result_bundle_count": sum(
            item["delivery"] == "execution_result_bundle" and item["recommended"]
            for item in capabilities
        ),
        "optional_result_bundle_count": sum(
            item["delivery"] == "execution_result_bundle" and not item["recommended"]
            for item in capabilities
        ),
        "capabilities": capabilities,
    }


@app.post("/api/executions/{execution_id}/artifact")
@app.post("/api/v1/executions/{execution_id}/artifact")
def materialize_execution_artifact(execution_id: str, request: ArtifactRequest):
    """按执行编号在固定目录生成JSON/CSV/README/manifest及可选ZIP。"""
    try:
        return execution_service.materialize_execution_artifact(
            execution_id,
            request.model_dump(exclude_none=True),
        )
    except ArtifactError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": exc.error_code, "message": str(exc)},
        ) from exc


@app.get("/api/executions/{execution_id}/artifact/download")
@app.get("/api/v1/executions/{execution_id}/artifact/download")
def download_execution_artifact(execution_id: str):
    """下载已校验的ZIP产物；文件系统路径永不由调用方提供。"""
    record = trace_store.get_execution(execution_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"未知执行记录: {execution_id}")
    try:
        descriptor = execution_service.artifact_service.resolve_zip_download(record)
    except ArtifactError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": exc.error_code, "message": str(exc)},
        ) from exc
    return FileResponse(
        path=descriptor["path"],
        media_type=descriptor["media_type"],
        filename=descriptor["filename"],
        headers={"X-Artifact-SHA256": descriptor["sha256"]},
    )


@app.post("/api/experiments/run")
@app.post("/api/v1/experiments/run")
def run_experiment(req: ExperimentRequest):
    """运行直接回答、强制调用或自主调用实验。"""
    try:
        return experiment_service.run(
            user_query=req.user_query,
            mode=req.mode,
            model_code=req.model_code,
            arguments=req.arguments,
            baseline_answer=req.baseline_answer,
            llm_name=req.llm_name,
            prompt_version=req.prompt_version,
            result_validation_enabled=req.result_validation_enabled,
            artifact_request=req.artifact.model_dump(exclude_none=True) if req.artifact else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/experiments/{experiment_id}")
@app.get("/api/v1/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    record = trace_store.get_experiment(experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"未知实验记录: {experiment_id}")
    return record


@app.get("/api/v1/scenarios")
def list_scenarios():
    """列出所有业务场景"""
    scenarios = sorted(set(m.scenario for m in registry._models.values()))
    return {
        "total": len(scenarios),
        "scenarios": scenarios,
    }


def _scene_http_error(exc: SceneError):
    status = 404 if exc.error_code in {
        "SCENE_NOT_FOUND", "RECIPE_NOT_FOUND", "SCENE_RUN_NOT_FOUND", "WORK_ORDER_NOT_FOUND"
    } else 409 if exc.error_code in {
        "SCENE_DEPENDENCY_MISSING", "SCENE_BINDING_ERROR", "WORK_ORDER_NOT_RELEASE_ELIGIBLE",
        "WORK_ORDER_ALREADY_REVIEWED",
    } else 400
    raise HTTPException(
        status_code=status,
        detail={"error_code": exc.error_code, "message": str(exc)},
    ) from exc


@app.get("/api/v1/scenes")
def list_business_scenes():
    """五大业务场景；只复用注册工具，不改变工具计数。"""
    return scene_service.list_scenes()


@app.get("/api/v1/scenes/{scene_id}")
def get_business_scene(scene_id: str):
    try:
        return scene_service.get_scene(scene_id)
    except SceneError as exc:
        _scene_http_error(exc)


@app.get("/api/v1/scenes/{scene_id}/recipes/{recipe_id}")
def get_scene_recipe(scene_id: str, recipe_id: str):
    try:
        return scene_service.get_recipe(scene_id, recipe_id)
    except SceneError as exc:
        _scene_http_error(exc)


@app.post("/api/v1/scenes/{scene_id}/recipes/{recipe_id}/execute")
def execute_scene_recipe(scene_id: str, recipe_id: str, req: SceneRunRequest):
    try:
        return scene_service.execute_recipe(
            scene_id,
            recipe_id,
            req.model_dump(exclude_none=True),
        )
    except SceneError as exc:
        _scene_http_error(exc)


@app.get("/api/v1/scene-runs/{run_id}")
def get_scene_run(run_id: str):
    try:
        return scene_service.get_run(run_id)
    except SceneError as exc:
        _scene_http_error(exc)


@app.post("/api/v1/scenes/{scene_id}/work-orders")
def compile_scene_work_order(scene_id: str, req: WorkOrderCompileRequest):
    try:
        return scene_service.compile_work_order(
            scene_id,
            req.model_dump(exclude_none=True),
        )
    except SceneError as exc:
        _scene_http_error(exc)


@app.get("/api/v1/work-orders/{work_order_id}")
def get_work_order(work_order_id: str):
    try:
        return scene_service.get_work_order(work_order_id)
    except SceneError as exc:
        _scene_http_error(exc)


@app.post("/api/v1/work-orders/{work_order_id}/review")
def review_work_order(work_order_id: str, req: WorkOrderReviewRequest):
    try:
        return scene_service.review_work_order(
            work_order_id,
            req.model_dump(exclude_none=True),
        )
    except SceneError as exc:
        _scene_http_error(exc)


# ═══════════════════════════════════════════════
# 数据查询 API — 从 PostgreSQL 读取
# ═══════════════════════════════════════════════

import psycopg2
import psycopg2.extras

DB_CONFIG = {
    'database': os.getenv('METALLURGY_DB_NAME', 'metallurgy'),
    'user': os.getenv('METALLURGY_DB_USER', 'postgres'),
    'password': os.getenv('METALLURGY_DB_PASSWORD', ''),
    'connect_timeout': int(os.getenv('METALLURGY_DB_CONNECT_TIMEOUT', '3')),
}
if os.getenv('METALLURGY_DB_HOST'):
    DB_CONFIG['host'] = os.environ['METALLURGY_DB_HOST']
if os.getenv('METALLURGY_DB_PORT'):
    DB_CONFIG['port'] = int(os.environ['METALLURGY_DB_PORT'])


def _get_db():
    return psycopg2.connect(**DB_CONFIG)


@app.get("/api/v1/data/sources")
def list_data_sources():
    """列出所有数据源"""
    try:
        conn = _get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT dataset_id, name, category, provider, license,
                   access_url, ingestion_mode, version, security_level, quality_grade
            FROM metallurgy_v2.dataset_registry
            ORDER BY dataset_id
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"total": len(rows), "sources": rows}
    except Exception as e:
        return {"total": 0, "sources": [], "error": str(e)}


@app.get("/api/v1/data/thermodynamics")
def query_thermodynamics(
    system: str = "", species: str = "", property_type: str = "",
    temp_min: float = None, temp_max: float = None,
    source: str = "", quality: str = "", data_type: str = "",
    page: int = 1, page_size: int = 20
):
    """查询热力学物性数据"""
    try:
        conn = _get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        conditions = []
        params = []
        idx = 1

        if system:
            conditions.append("species ILIKE %s")
            params.append(f'%{system}%')
        if property_type:
            conditions.append("(property_code = %s OR property_type = %s)")
            params.extend([property_type, property_type])
        if temp_min is not None:
            conditions.append("(temperature >= %s OR temperature IS NULL)")
            params.append(temp_min)
        if temp_max is not None:
            conditions.append("(temperature <= %s OR temperature IS NULL)")
            params.append(temp_max)
        if quality:
            conditions.append("quality_grade = %s")
            params.append(quality)

        where = " AND ".join(conditions) if conditions else "TRUE"

        # Count
        cur.execute(f"SELECT COUNT(*) as count FROM metallurgy_v2.thermodynamic_property WHERE {where}", params)
        total = cur.fetchone()["count"]

        # Data
        offset = (page - 1) * page_size
        data_params = params + [page_size, offset]
        cur.execute(f"""
            SELECT id, dataset_id, species, property_type, temperature,
                   value, unit, uncertainty, data_type, source_ref, quality_grade
            FROM metallurgy_v2.thermodynamic_property
            WHERE {where}
            ORDER BY species, temperature
            LIMIT %s OFFSET %s
        """, data_params)
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return {"total": total, "page": page, "page_size": page_size, "data": rows}
    except Exception as e:
        return {"total": 0, "data": [], "error": str(e)}


@app.get("/api/v1/data/reactions")
def query_reactions(
    reaction: str = "", category: str = "", source: str = "",
    page: int = 1, page_size: int = 20
):
    """查询反应定义"""
    try:
        conn = _get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        conditions = []
        params = []
        idx = 1

        if reaction:
            conditions.append("reaction_equation ILIKE %s")
            params.append(f'%{reaction}%')
        if category:
            conditions.append("category = %s")
            params.append(category)

        where = " AND ".join(conditions) if conditions else "TRUE"

        cur.execute(f"SELECT COUNT(*) as count FROM metallurgy_v2.reaction_definition WHERE {where}", params)
        total = cur.fetchone()["count"]

        offset = (page - 1) * page_size
        data_params = params + [page_size, offset]
        cur.execute(f"""
            SELECT reaction_id, reaction_equation, name, category, reactants, products
            FROM metallurgy_v2.reaction_definition
            WHERE {where}
            ORDER BY reaction_id
            LIMIT %s OFFSET %s
        """, data_params)
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return {"total": total, "page": page, "page_size": page_size, "data": rows}
    except Exception as e:
        return {"total": 0, "data": [], "error": str(e)}


# ═══════════════════════════════════════════════
# 热力学评价 API — 查询 + 溯源
# ═══════════════════════════════════════════════

@app.get("/api/v1/data/thermodynamic/evaluate")
def evaluate_thermo(
    species: str, temperature: float, phase: str = "solid",
    properties: str = "cp,entropy,enthalpy"
):
    """评价指定物种在指定温度的热力学性质，返回数据溯源"""
    try:
        conn = _get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        prop_list = [p.strip() for p in properties.split(",")]
        results = {}
        provenance = {}

        # 1. 先查 correlation 表找 Shomate 系数
        cur.execute("""
            SELECT id, equation_type, temperature_min_k, temperature_max_k,
                   coefficients, source_id
            FROM metallurgy_v2.thermodynamic_correlation
            WHERE species_id = %s AND phase = %s
              AND %s BETWEEN temperature_min_k AND temperature_max_k
              AND equation_type = 'SHOMATE'
              AND is_active = TRUE
            ORDER BY priority
            LIMIT 1
        """, (species, phase, temperature))
        corr = cur.fetchone()

        if corr:
            coeffs = corr["coefficients"]
            A, B, C, D, E = coeffs["A"], coeffs["B"], coeffs["C"], coeffs["D"], coeffs["E"]
            F, G, H_val = coeffs["F"], coeffs["G"], coeffs["H"]

            t = temperature / 1000.0
            import math
            ln_t = math.log(t) if t > 0 else 0

            Cp = A + B*t + C*t**2 + D*t**3 + E/t**2
            H_inc = A*t + B*t**2/2 + C*t**3/3 + D*t**4/4 - E/t + F - H_val
            S = A * ln_t + B*t + C*t**2/2 + D*t**3/3 - E/(2*t**2) + G
            G_val = H_inc - temperature * S / 1000.0

            for p in prop_list:
                if p == "cp":
                    results["cp"] = {"value": round(Cp, 6), "unit": "J/(mol·K)"}
                elif p == "entropy":
                    results["entropy"] = {"value": round(S, 6), "unit": "J/(mol·K)"}
                elif p == "enthalpy":
                    results["enthalpy"] = {"value": round(H_inc, 6), "unit": "kJ/mol"}
                elif p == "gibbs":
                    results["gibbs"] = {"value": round(G_val, 6), "unit": "kJ/mol"}

            provenance = {
                "method": "SHOMATE",
                "equation_type": corr["equation_type"],
                "correlation_id": corr["id"],
                "temperature_range": [corr["temperature_min_k"], corr["temperature_max_k"]],
                "source_id": corr["source_id"],
            }
        else:
            # 2. 没找到关联式，查离散点
            for p in prop_list:
                code_map = {"cp": "CP_STD", "entropy": "S_STD", "enthalpy": "H_INCREMENT_298", "gibbs": "G_STD"}
                code = code_map.get(p)
                if code:
                    cur.execute("""
                        SELECT value, unit, data_origin, source_ref
                        FROM metallurgy_v2.thermodynamic_property
                        WHERE species LIKE %s AND property_code = %s
                          AND ABS(temperature - %s) < 1
                        LIMIT 1
                    """, (f'{species}%', code, temperature))
                    row = cur.fetchone()
                    if row:
                        results[p] = {"value": row["value"], "unit": row["unit"]}
                        provenance[p] = {"source": row.get("source_ref", "unknown"), "origin": row.get("data_origin", "unknown")}

        cur.close()
        conn.close()

        return {
            "species": species,
            "phase": phase,
            "temperature": temperature,
            "results": results,
            "provenance": provenance,
        }
    except Exception as e:
        return {"species": species, "temperature": temperature, "error": str(e), "results": {}}


@app.get("/api/v1/data/thermodynamic/correlations")
def list_correlations(species: str = "", equation_type: str = ""):
    """列出热力学关联式"""
    try:
        conn = _get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        where = []
        params = []
        if species:
            where.append("species_id = %s"); params.append(species)
        if equation_type:
            where.append("equation_type = %s"); params.append(equation_type)
        w = " AND ".join(where) if where else "TRUE"

        cur.execute(f"""
            SELECT id, species_id, phase, equation_type,
                   temperature_min_k, temperature_max_k, coefficients,
                   source_id, quality_level, is_active
            FROM metallurgy_v2.thermodynamic_correlation
            WHERE {w} ORDER BY species_id, temperature_min_k
        """, params)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"total": len(rows), "correlations": rows}
    except Exception as e:
        return {"total": 0, "correlations": [], "error": str(e)}


# ── 直接运行 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
