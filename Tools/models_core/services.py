"""统一执行与三模式实验服务；不依赖 Web 框架，便于离线回归测试。"""

from __future__ import annotations

import json
import threading
import time
import uuid
from copy import deepcopy
from dataclasses import asdict
from typing import Dict, List, Optional

from .base import InvocationContext
from .registry import ModelRegistry


def _identifier(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


def _result_payload(result) -> dict:
    payload = asdict(result)
    payload["status"] = (
        "success" if result.success
        else "error" if result.error_code == "INTERNAL_ERROR"
        else "rejected"
    )
    return payload


class InMemoryTraceStore:
    """进程内追踪存储；数据库迁移提供同构的持久化表。"""

    def __init__(self):
        self._executions: Dict[str, dict] = {}
        self._experiments: Dict[str, dict] = {}
        self._lock = threading.RLock()

    def save_execution(self, record: dict) -> None:
        with self._lock:
            self._executions[record["execution_id"]] = deepcopy(record)

    def get_execution(self, execution_id: str) -> Optional[dict]:
        with self._lock:
            record = self._executions.get(execution_id)
            return deepcopy(record) if record else None

    def save_experiment(self, record: dict) -> None:
        with self._lock:
            self._experiments[record["experiment_id"]] = deepcopy(record)

    def get_experiment(self, experiment_id: str) -> Optional[dict]:
        with self._lock:
            record = self._experiments.get(experiment_id)
            return deepcopy(record) if record else None


class ModelExecutionService:
    """模型协议的 validate / execute 垂直切片。"""

    def __init__(self, registry: ModelRegistry, store: InMemoryTraceStore):
        self.registry = registry
        self.store = store

    def validate(self, model_code: str, arguments: dict) -> dict:
        return self.registry.validate(model_code, arguments)

    def execute(
        self,
        model_code: str,
        arguments: dict,
        *,
        trace_id: str = "",
        user_or_agent: str = "api",
        options: Optional[dict] = None,
    ) -> dict:
        options = options or {}
        execution_id = _identifier("EXEC")
        trace_id = trace_id or _identifier("TRACE")
        started_at = time.time()
        model = self.registry.get(model_code)

        context = InvocationContext(
            user_or_agent=user_or_agent,
            trace_id=trace_id,
            validate_boundary=options.get("validate_boundary", True),
            return_provenance=options.get("return_provenance", True),
        )
        result = self.registry.invoke(model_code, arguments, context)
        payload = _result_payload(result)
        record = {
            "execution_id": execution_id,
            "trace_id": result.trace_id or trace_id,
            "model_code": model_code,
            "tool_uid": model.tool_uid if model else None,
            "catalog_id": model.catalog_id if model else None,
            "model_version": model.version if model else None,
            "input": deepcopy(arguments),
            "actual_data_records": payload.get("provenance", []),
            "output": payload.get("result"),
            "boundary_check": payload.get("boundary_check"),
            "status": payload["status"],
            "error": payload.get("error"),
            "error_code": payload.get("error_code"),
            "runtime_ms": payload.get("runtime_ms", 0.0),
            "started_at": started_at,
            "completed_at": time.time(),
            "user_or_agent": user_or_agent,
        }
        self.store.save_execution(record)
        return record


class ExperimentService:
    """直接回答、强制调用、自主调用三种策略的可重复实验。"""

    MODE_DIRECT = "direct"
    MODE_FORCED = "forced"
    MODE_AUTONOMOUS = "autonomous"
    MODES = (MODE_DIRECT, MODE_FORCED, MODE_AUTONOMOUS)

    _KEYWORDS = {
        "A001": ("单位换算", "换算", "摄氏", "开尔文", "mpa", "kg"),
        "A002": ("解析化学式", "元素组成", "原子数"),
        "A003": ("摩尔质量", "分子量"),
        "A004": ("组成归一", "成分归一"),
        "A005": ("质量守恒", "物料衡算"),
        "A006": ("反应配平", "配平校验", "元素残差"),
        "A007": ("氧当量", "还原剂当量", "电子当量"),
        "A011": ("计量系数求解", "反应系数求解", "自动配平", "最小整数系数"),
        "A101": ("电荷平衡", "价态平衡", "氧化态校验"),
        "A008": ("缺失值", "数据填补", "插值填补", "knn填补"),
        "B001": ("shomate", "定压热容", "热容", "cp"),
        "B002": ("nasa7", "nasa热物性"),
        "B003": ("显热", "焓积分"),
        "B004": ("熵积分",),
        "B005": ("物种gibbs", "物种吉布斯"),
        "B006": ("反应焓", "焓变"),
        "B007": ("反应熵", "熵变"),
        "B008": ("反应gibbs", "反应吉布斯", "反应方向"),
        "B009": ("平衡常数",),
        "B010": ("van't hoff", "vant hoff", "温度修正平衡常数"),
        "B011": ("ellingham", "氧势", "氧分压线"),
        "B014": ("理想溶液活度", "raoult"),
        "B015": ("正则溶液活度", "正则溶液"),
        "B018": ("gibbs相律", "相律", "自由度"),
        "B019": ("杠杆规则", "相分数"),
        "C001": ("arrhenius", "速率常数"),
        "C002": ("扩散系数", "扩散距离"),
        "C003": ("fick", "半无限扩散", "浓度剖面"),
        "C004": ("jmak", "avrami", "转变动力学"),
        "C009": ("导热系数混合", "有效导热系数", "maxwell-eucken", "串并联导热"),
        "C010": ("填充床传质", "传质系数", "sherwood", "wakao"),
        "C011": ("无量纲数", "reynolds", "prandtl", "schmidt", "peclet", "lewis"),
        "T001": ("平板导热", "稳态导热", "fourier"),
        "T002": ("灰体辐射", "辐射换热", "stefan-boltzmann"),
        "T003": ("集总热容", "瞬态温度", "biot", "时间常数"),
        "T004": ("多层热阻", "复合壁", "接触热阻", "温度剖面"),
        "D001": ("bof耗氧", "转炉耗氧", "理论耗氧"),
        "D002": ("bof热平衡", "转炉热平衡", "可熔废钢"),
        "D021": ("转炉装料物料平衡", "转炉装料平衡", "bof装料"),
        "D004": ("石灰加入量", "白云石加入量", "熔剂加入量", "目标碱度"),
        "D005": ("炉渣量", "渣量估算", "氧化产物入渣"),
        "D006": ("炉渣碱度", "渣碱度", "二元碱度", "cao/sio2"),
        "D010": ("磷分配比", "lp", "脱磷平衡"),
        "D011": ("硫分配比", "硫容量", "ls", "脱硫平衡"),
        "D012": ("锰氧化平衡", "mno平衡", "mn氧化"),
        "D013": ("硅氧化平衡", "sio2平衡", "si氧化"),
        "D014": ("tfe", "铁损", "渣中全铁", "金属夹带"),
        "D007": ("脱碳速率", "分段脱碳", "碳轨迹"),
        "D015": ("炉气生成", "炉气量", "co/co2炉气"),
        "D016": ("氧利用率", "供氧效率", "氧损失"),
        "D023": ("合金补加", "合金加入量", "元素收得率", "目标成分"),
        "E005": ("高炉氢平衡", "氢原子平衡", "氢平衡"),
        "E011": ("co利用率", "h2利用率", "炉顶气利用率"),
        "E006": ("rist", "高炉操作线", "碳氧操作线"),
        "E007": ("高炉热平衡", "高炉两区热平衡", "高温区热平衡"),
        "E009": ("喷煤替代", "焦炭替代比", "pci替代"),
        "E012": ("风口前煤气", "风口煤气量", "理论煤气量"),
        "E014": ("ergun", "料柱压降", "填充床压降"),
        "E021": ("boudouard", "布德瓦反应", "碳溶反应", "co/co2平衡", "平衡驱动力"),
        "G001": ("网格尺度", "网格加密", "gci", "网格收敛"),
        "G002": ("cfl", "时间步稳定", "fourier数", "显式稳定性"),
    }

    def __init__(
        self,
        registry: ModelRegistry,
        executor: ModelExecutionService,
        store: InMemoryTraceStore,
    ):
        self.registry = registry
        self.executor = executor
        self.store = store

    def recall_candidates(self, user_query: str) -> List[dict]:
        query = user_query.lower()
        candidates = []
        for model_code, keywords in self._KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in query)
            if score:
                model = self.registry.get(model_code)
                candidates.append({
                    "model_code": model_code,
                    "model_name": model.name if model else model_code,
                    "score": score,
                    "matched_keywords": [k for k in keywords if k.lower() in query],
                })
        return sorted(candidates, key=lambda item: (-item["score"], item["model_code"]))

    @staticmethod
    def _needs_tool(user_query: str, candidates: List[dict]) -> bool:
        query = user_query.lower()
        conceptual = ("什么是", "定义", "为什么", "介绍", "原理")
        asks_calculation = any(token in query for token in ("计算", "求", "换算", "多少", "预测"))
        return bool(candidates) and (asks_calculation or not any(x in query for x in conceptual))

    def run(
        self,
        *,
        user_query: str,
        mode: str,
        model_code: Optional[str] = None,
        arguments: Optional[dict] = None,
        baseline_answer: str = "",
        llm_name: str = "external-orchestrator",
        prompt_version: str = "v1",
        result_validation_enabled: bool = True,
    ) -> dict:
        if mode not in self.MODES:
            raise ValueError(f"mode 必须是 {self.MODES} 之一")
        if not user_query.strip():
            raise ValueError("user_query 不能为空")

        experiment_id = _identifier("EXP")
        trace_id = _identifier("TRACE")
        started = time.perf_counter()
        candidates = self.recall_candidates(user_query)
        selected_model = None
        selection_reason = ""
        validation_result = None
        execution_result = None
        final_answer = baseline_answer

        if mode == self.MODE_DIRECT:
            selection_reason = "实验策略禁止调用工具"
            final_answer = final_answer or "本次为直接回答组，答案由外部大模型生成。"
        elif mode == self.MODE_FORCED:
            selected_model = model_code
            selection_reason = "实验策略强制调用指定工具"
        elif self._needs_tool(user_query, candidates):
            selected_model = model_code or candidates[0]["model_code"]
            selection_reason = "自主策略识别为数值计算问题并选择最高分候选模型"
        else:
            selection_reason = "自主策略判断为知识问答或无匹配工具"
            final_answer = final_answer or "本次自主策略未调用专业计算工具。"

        if mode == self.MODE_FORCED and not selected_model:
            validation_result = {
                "valid": False,
                "errors": [{
                    "code": "INVALID_INPUT",
                    "field": "model_code",
                    "message": "强制调用模式必须提供 model_code",
                }],
            }
        elif selected_model:
            validation_result = self.executor.validate(selected_model, arguments or {})
            if validation_result["valid"]:
                execution_result = self.executor.execute(
                    selected_model,
                    arguments or {},
                    trace_id=trace_id,
                    user_or_agent=llm_name,
                )
                if execution_result["status"] == "success":
                    final_answer = final_answer or json.dumps(
                        execution_result["output"], ensure_ascii=False
                    )
            else:
                final_answer = final_answer or "工具参数校验未通过，未执行计算。"

        record = {
            "experiment_id": experiment_id,
            "trace_id": trace_id,
            "user_query": user_query,
            "mode": mode,
            "llm_name": llm_name,
            "prompt_version": prompt_version,
            "candidate_models": candidates,
            "selected_model": selected_model,
            "selection_reason": selection_reason,
            "generated_arguments": deepcopy(arguments or {}),
            "validation_result": validation_result,
            "execution_result": execution_result,
            "retry_count": 0,
            "result_validation_enabled": result_validation_enabled,
            "final_answer": final_answer,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "token_usage": None,
            "created_at": time.time(),
        }
        self.store.save_experiment(record)
        return record
