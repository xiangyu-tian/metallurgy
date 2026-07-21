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
import os
import sys
import uuid
from typing import Optional

# 确保 models_core 可导入
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models_core import ModelRegistry
from models_core.base import InvocationContext

# ── 初始化注册表 ──
registry = ModelRegistry()
count = registry.discover()
print(f"✅ 已注册 {count} 个模型: {[m.model_id for m in registry._models.values()]}")

# ── FastAPI 应用 ──
app = FastAPI(
    title="冶金平台 — 统一模型微服务",
    version="0.1.0",
    description="120个小模型的统一注册、调用与校验服务",
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
    input: dict = Field(..., description="模型输入参数，根据 input_schema 定义")
    options: dict = Field(default_factory=lambda: {
        "validate_boundary": True,
        "return_provenance": True,
    })

    class Config:
        json_schema_extra = {
            "example": {
                "input": {"reaction": "FeO + C → Fe + CO", "temperature": 1873},
                "options": {"validate_boundary": True, "return_provenance": True},
            }
        }


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


# ── API 路由 ──

@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "service": "models-server",
        "registered_models": len(registry._models),
        "model_ids": sorted(registry._models.keys()),
    }


@app.get("/api/v1/models")
def list_models(scenario: Optional[str] = None):
    """列出所有模型，可按场景筛选"""
    if scenario:
        models = registry.list_by_scenario(scenario)
    else:
        models = registry.list_models()

    return {
        "total": len(models),
        "models": models,
    }


@app.get("/api/v1/models/{model_id}")
def get_model(model_id: str):
    """获取单个模型详情"""
    model = registry.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"未知模型: {model_id}")
    return model.get_registry_entry()


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


@app.get("/api/v1/scenarios")
def list_scenarios():
    """列出所有业务场景"""
    scenarios = sorted(set(m.scenario for m in registry._models.values()))
    return {
        "total": len(scenarios),
        "scenarios": scenarios,
    }


# ═══════════════════════════════════════════════
# 数据查询 API — 从 PostgreSQL 读取
# ═══════════════════════════════════════════════

import psycopg2
import psycopg2.extras

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'metallurgy',
    'user': 'postgres',
    'password': '',
    'connect_timeout': 3,
}


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
