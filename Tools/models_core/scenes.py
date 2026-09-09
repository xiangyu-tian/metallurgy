"""Five business-scene orchestration and evidence-backed work orders.

Scene recipes are platform workflows, not additional metallurgy tools. They only
invoke fully registered tools through ModelExecutionService, retain every
execution id, and fail closed when a dependency or boundary check fails.
"""

from __future__ import annotations

import json
import time
import uuid
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional

from .registry import ModelRegistry
from .services import InMemoryTraceStore, ModelExecutionService


class SceneError(ValueError):
    """Stable scene-service error exposed by the HTTP adapter."""

    def __init__(self, message: str, error_code: str = "INVALID_INPUT"):
        super().__init__(message)
        self.error_code = error_code


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


def _step(
    step_id: str,
    model_code: str,
    purpose: str,
    *,
    depends_on: Iterable[str] = (),
    bindings: Optional[Dict[str, dict]] = None,
    default_selected: bool = True,
    artifact_recommended: bool = False,
) -> dict:
    return {
        "step_id": step_id,
        "model_code": model_code,
        "purpose": purpose,
        "depends_on": list(depends_on),
        "bindings": deepcopy(bindings or {}),
        "default_selected": default_selected,
        "artifact_recommended": artifact_recommended,
    }


SCENE_DEFINITIONS = {
    "thermodynamics": {
        "name": "热力学推理",
        "short_name": "热力学",
        "description": "以反应配平为入口，组合热化学、平衡常数、活度和相平衡工具。",
        "icon": "fa-fire",
        "color": "#C7472A",
        "families": ["A", "B", "C", "T"],
        "extra_tools": ["G004", "G008", "G009", "G010", "H001"],
        "featured_tools": ["A011", "A006", "B006", "B007", "B008", "B009", "B011", "B023"],
        "recipes": [
            {
                "recipe_id": "reaction-thermodynamics-v1",
                "name": "反应热力学证据链",
                "version": "1.0.0",
                "description": "求解并复核计量系数，再计算反应焓、熵、Gibbs自由能和平衡常数。",
                "steps": [
                    _step("balance", "A011", "求解最小整数反应计量系数"),
                    _step("balance_check", "A006", "独立复核元素守恒", depends_on=["balance"], bindings={"reaction": {"step": "balance", "path": "output.balanced_reaction"}}),
                    _step("enthalpy", "B006", "计算反应焓", depends_on=["balance_check"], bindings={"reaction": {"step": "balance", "path": "output.balanced_reaction"}}),
                    _step("entropy", "B007", "计算反应熵", depends_on=["balance_check"], bindings={"reaction": {"step": "balance", "path": "output.balanced_reaction"}}),
                    _step("gibbs", "B008", "计算反应Gibbs自由能", depends_on=["enthalpy", "entropy"], bindings={"reaction": {"step": "balance", "path": "output.balanced_reaction"}}),
                    _step("equilibrium", "B009", "计算平衡常数", depends_on=["gibbs"], bindings={"reaction": {"step": "balance", "path": "output.balanced_reaction"}}),
                    _step("safety", "G013", "检查守恒和结果完整性", depends_on=["balance_check", "equilibrium"]),
                ],
                "sample_overrides": {
                    "balance": {"reactants": [{"formula": "C"}, {"formula": "O2"}], "products": [{"formula": "CO2"}]},
                    "enthalpy": {"temperature": 1000},
                    "entropy": {"temperature": 1000},
                    "gibbs": {"temperature": 1000},
                    "equilibrium": {"temperature": 1000},
                    "safety": {
                        "rule_set_id": "thermo-evidence",
                        "rule_set_version": "1.0.0",
                        "rules": [{
                            "id": "reaction-balanced",
                            "description": "反应必须通过独立元素守恒校验",
                            "severity": "error",
                            "assertion": {"op": "equal", "args": [{"path": "balance_check.balanced"}, {"constant": True}]},
                            "recommendation": "修正反应式或计量系数后重新执行",
                        }],
                    },
                },
            }
        ],
    },
    "converter": {
        "name": "转炉炼钢工艺优化",
        "short_name": "转炉",
        "description": "组合耗氧、热平衡、造渣、供氧制度和冷却剂优化，形成静态决策工单。",
        "icon": "fa-bullseye",
        "color": "#B8322A",
        "families": ["A", "B", "C", "D", "T", "G", "H"],
        "extra_tools": [],
        "featured_tools": ["D001", "D002", "D005", "D006", "D018", "D020", "G013"],
        "recipes": [
            {
                "recipe_id": "bof-static-plan-v1",
                "name": "BOF静态计算与工单",
                "version": "1.0.0",
                "description": "理论耗氧驱动渣量和分段供氧计算，并组合独立热平衡与冷却剂优化。",
                "steps": [
                    _step("oxygen", "D001", "计算分元素理论耗氧"),
                    _step("heat", "D002", "校核静态热平衡"),
                    _step("slag_mass", "D005", "由进入渣相的氧化元素量估算渣量", depends_on=["oxygen"], bindings={"oxidized_element_masses_kg": {"step": "oxygen", "path": "output.oxidized_element_masses_kg", "include_keys": ["Si", "Mn", "P", "Fe"]}}),
                    _step("basicity", "D006", "计算炉渣碱度", depends_on=["slag_mass"], bindings={"component_masses_kg": {"step": "slag_mass", "path": "output.component_masses_kg"}}),
                    _step("oxygen_schedule", "D018", "优化静态分段供氧制度", depends_on=["oxygen"], bindings={"total_oxygen_nm3": {"step": "oxygen", "path": "output.supplied_oxygen_normal_volume_m3"}}),
                    _step("coolant", "D020", "优化冷却剂与废钢静态加入"),
                    _step("safety", "G013", "复核守恒、温度和工艺边界", depends_on=["heat", "basicity", "oxygen_schedule", "coolant"]),
                ],
                "sample_overrides": {
                    "oxygen": {
                        "metal_inputs": [{"name": "hot metal", "mass_kg": 1000, "composition": {"Fe": 0.95, "C": 0.04, "Si": 0.01}}],
                        "target_steel_mass_kg": 950,
                        "target_composition": {"Fe": 0.995, "C": 0.005},
                        "oxygen_utilization": 0.9,
                    },
                    "slag_mass": {
                        "oxide_product_formulas": {"Si": "SiO2", "Mn": "MnO", "P": "P2O5", "Fe": "FeO"},
                        "flux_streams": [{"name": "lime", "mass_kg": 40, "composition": {"CaO": 0.9, "SiO2": 0.1}}],
                    },
                    "oxygen_schedule": {
                        "stages": [
                            {"name": "early", "oxygen_flow_nm3_min": 5, "duration_min_min": 1, "duration_max_min": 5, "preferred_oxygen_fraction": 0.5, "deviation_weight": 1, "lance_height_m": 1.8, "oxygen_utilization_fraction": 0.82},
                            {"name": "middle", "oxygen_flow_nm3_min": 5, "duration_min_min": 1, "duration_max_min": 5, "preferred_oxygen_fraction": 0.3, "deviation_weight": 1, "lance_height_m": 1.5, "oxygen_utilization_fraction": 0.9},
                            {"name": "finish", "oxygen_flow_nm3_min": 5, "duration_min_min": 1, "duration_max_min": 5, "preferred_oxygen_fraction": 0.2, "deviation_weight": 2, "lance_height_m": 1.3, "oxygen_utilization_fraction": 0.94},
                        ],
                    },
                    "safety": {
                        "rule_set_id": "bof-static-evidence",
                        "rule_set_version": "1.0.0",
                        "rules": [
                            {"id": "heat-closure", "description": "热平衡闭合误差必须接近零", "severity": "error", "assertion": {"op": "within", "args": [{"path": "heat.energy_closure_error_kj"}, {"constant": 0}, {"constant": 1e-6}]}, "recommendation": "检查显热、反应热与热损输入"},
                            {"id": "basicity-finite", "description": "炉渣碱度必须为有限值", "severity": "error", "assertion": {"op": "is_finite", "args": [{"path": "basicity.basicity"}]}, "recommendation": "检查渣中CaO和SiO2质量"},
                            {"id": "oxygen-closure", "description": "分段供氧总量必须闭合", "severity": "error", "assertion": {"op": "within", "args": [{"path": "oxygen_schedule.oxygen_closure_residual_nm3"}, {"constant": 0}, {"constant": 1e-6}]}, "recommendation": "检查各阶段氧量上下限"},
                        ],
                    },
                },
            }
        ],
    },
    "blastfurnace": {
        "name": "高炉低碳运行分析",
        "short_name": "高炉低碳",
        "description": "组合物料、碳氢氧平衡、Rist操作线、喷煤替代、热状态和透气性约束。",
        "icon": "fa-leaf",
        "color": "#24735A",
        "families": ["A", "B", "C", "E", "T", "G"],
        "extra_tools": [],
        "featured_tools": ["E001", "E003", "E106", "E109", "E013", "E014", "E020", "G013"],
        "recipes": [
            {
                "recipe_id": "bf-low-carbon-v1",
                "name": "高炉低碳边界评估",
                "version": "1.0.0",
                "description": "在物料和碳账基础上评估Rist、喷煤替代、风口热状态与料柱压降。",
                "steps": [
                    _step("material", "E001", "闭合高炉总物料平衡"),
                    _step("carbon", "E003", "闭合碳平衡"),
                    _step("rist", "E106", "计算完整物料型Rist操作线", depends_on=["material", "carbon"]),
                    _step("pci", "E109", "计算喷煤等效置换和边际账", depends_on=["carbon"]),
                    _step("raft", "E013", "校核风口回旋区绝热火焰温度", depends_on=["pci"]),
                    _step("permeability", "E014", "校核料柱Ergun压降", depends_on=["material"]),
                    _step("carbon_ledger", "E020", "形成声明边界内碳足迹账本", depends_on=["carbon"]),
                    _step("safety", "G013", "复核低碳候选的热态和透气性边界", depends_on=["rist", "raft", "permeability", "carbon_ledger"]),
                ],
                "sample_overrides": {
                    "safety": {
                        "rule_set_id": "bf-low-carbon-evidence",
                        "rule_set_version": "1.0.0",
                        "rules": [
                            {"id": "material-closure", "description": "高炉物料账必须闭合", "severity": "error", "assertion": {"op": "equal", "args": [{"path": "material.passed"}, {"constant": True}]}, "recommendation": "检查输入输出物流"},
                            {"id": "raft-finite", "description": "风口理论燃烧温度必须可解", "severity": "error", "assertion": {"op": "is_finite", "args": [{"path": "raft.raft_temperature_k"}]}, "recommendation": "检查热输入和燃料元素量"},
                            {"id": "pressure-drop-finite", "description": "料柱压降必须为有限值", "severity": "error", "assertion": {"op": "is_finite", "args": [{"path": "permeability.total_pressure_drop_pa"}]}, "recommendation": "检查粒径、空隙率和煤气物性"},
                        ],
                    },
                },
            }
        ],
    },
    "casting": {
        "name": "连铸质量辅助决策",
        "short_name": "连铸",
        "description": "从液固相线、凝固路径扩展到坯壳、二冷、拉速和热应力的可追溯计算链。",
        "icon": "fa-layer-group",
        "color": "#345B8C",
        "families": ["A", "B", "C", "F", "T", "G"],
        "extra_tools": [],
        "featured_tools": ["F001", "F002", "F004", "F005", "F006", "F008", "F009", "F011", "F014", "G005"],
        "recipes": [
            {
                "recipe_id": "casting-cooling-v1",
                "name": "凝固—二冷—拉速工单",
                "version": "1.0.0",
                "description": "计算相变温区和凝固路径，并可扩展坯壳、二冷、拉速、热应力及OpenFOAM验证案例。",
                "steps": [
                    _step("liquidus", "F001", "计算钢液液相线温度"),
                    _step("solidus", "F002", "计算钢液固相线温度"),
                    _step("superheat", "F003", "计算过热度", depends_on=["liquidus"], bindings={"liquidus_temperature": {"step": "liquidus", "path": "output.liquidus_temperature_k"}, "liquidus_source": {"constant": "F001"}, "upstream_execution_id": {"step": "liquidus", "path": "execution_id"}}),
                    _step("solidification", "F004", "计算凝固分数曲线", depends_on=["liquidus", "solidus"]),
                    _step("shell", "F005", "计算一维坯壳和温度剖面", depends_on=["solidification"], default_selected=False, artifact_recommended=True),
                    _step("endpoint", "F006", "预测凝固终点", depends_on=["shell"], bindings={"upstream_execution_id": {"step": "shell", "path": "execution_id"}}, default_selected=False),
                    _step("secondary_water", "F008", "计算二冷总水量", depends_on=["shell"], default_selected=False),
                    _step("water_zones", "F009", "分配二冷各区水量", depends_on=["secondary_water"], bindings={"total_water_flow_m3_h": {"step": "secondary_water", "path": "output.total_water_flow_m3_h"}}, default_selected=False),
                    _step("casting_speed", "F011", "求最大可行拉速", depends_on=["endpoint", "secondary_water"], default_selected=False),
                    _step("thermal_stress", "F014", "计算分层热应力和应变", depends_on=["shell"], default_selected=False),
                    _step("openfoam_case", "G005", "生成可交付OpenFOAM导热验证案例", depends_on=["shell"], default_selected=False, artifact_recommended=True),
                    _step("safety", "G013", "复核相变、冷却和拉速边界", depends_on=["superheat", "solidification"]),
                ],
                "sample_overrides": {
                    "liquidus": {"composition_wt_percent": {"C": 0.1}, "grid_step_k": 5},
                    "solidus": {"composition_wt_percent": {"C": 0.1}, "grid_step_k": 5},
                    "superheat": {"steel_temperature": 1873.15, "temperature_unit": "K"},
                    "solidification": {"composition_wt_percent": {"C": 0.1}, "model": "equilibrium", "start_temperature_k": 1900, "end_temperature_k": 1400, "step_k": 5},
                    "safety": {
                        "rule_set_id": "casting-thermal-window",
                        "rule_set_version": "1.0.0",
                        "rules": [{
                            "id": "positive-superheat",
                            "description": "钢液过热度必须非负",
                            "severity": "error",
                            "assertion": {"op": "greater_than_or_equal", "args": [{"path": "superheat.superheat_k"}, {"constant": 0}]},
                            "recommendation": "检查钢液温度和液相线来源",
                        }],
                    },
                },
            }
        ],
    },
    "simulation": {
        "name": "仿真与工单协同",
        "short_name": "仿真工单",
        "description": "跨场景复用全部真实工具，完成案例生成、批处理、敏感性、不确定度、优化和工单审核。",
        "icon": "fa-clipboard-check",
        "color": "#A86416",
        "families": ["*"],
        "extra_tools": [],
        "featured_tools": ["G001", "G002", "G003", "G005", "G006", "G009", "G010", "G011", "G012", "G013"],
        "recipes": [
            {
                "recipe_id": "simulation-evidence-v1",
                "name": "仿真证据与工单",
                "version": "1.0.0",
                "description": "生成网格、时间步、数值场或外部求解案例，并用敏感性、不确定度和规则校验支撑工单。",
                "steps": [
                    _step("mesh", "G001", "估计网格尺度"),
                    _step("time_step", "G002", "校验时间步和稳定性"),
                    _step("field", "G003", "求解一维瞬态导热场", depends_on=["mesh", "time_step"], artifact_recommended=True),
                    _step("openfoam_case", "G005", "生成外部OpenFOAM案例包", depends_on=["mesh", "time_step"], artifact_recommended=True),
                    _step("batch", "G006", "执行注册工具参数化批处理", default_selected=False),
                    _step("sensitivity", "G009", "分析注册工具局部敏感性", default_selected=False),
                    _step("uncertainty", "G010", "传播输入不确定度", depends_on=["sensitivity"], default_selected=False),
                    _step("single_objective", "G011", "离线单目标贝叶斯优化", depends_on=["sensitivity"], default_selected=False),
                    _step("multi_objective", "G012", "离线多目标NSGA-II优化", depends_on=["sensitivity"], default_selected=False),
                    _step("safety", "G013", "以版本化规则检查仿真或优化候选", depends_on=["field", "openfoam_case"]),
                ],
                "sample_overrides": {
                    "safety": {
                        "rule_set_id": "simulation-evidence",
                        "rule_set_version": "1.0.0",
                        "rules": [
                            {"id": "field-energy-finite", "description": "数值场能量闭合误差必须为有限值", "severity": "error", "assertion": {"op": "is_finite", "args": [{"path": "field.energy_closure_residual_j_m2"}]}, "recommendation": "检查时间步、边界条件和网格"},
                            {"id": "case-structure", "description": "OpenFOAM案例结构必须通过独立校验", "severity": "error", "assertion": {"op": "equal", "args": [{"path": "openfoam_case.structural_validation.verified"}, {"constant": True}]}, "recommendation": "修正案例字典和边界配置"},
                        ],
                    },
                },
            }
        ],
    },
}


def _get_path(payload: Any, path: str) -> Any:
    current = payload
    if not path:
        return current
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        elif isinstance(current, list) and segment.isdigit() and int(segment) < len(current):
            current = current[int(segment)]
        else:
            raise SceneError(f"绑定来源路径不存在: {path}", "SCENE_BINDING_ERROR")
    return deepcopy(current)


def _set_path(payload: dict, path: str, value: Any) -> None:
    segments = path.split(".")
    current = payload
    for segment in segments[:-1]:
        node = current.get(segment)
        if node is None:
            node = {}
            current[segment] = node
        if not isinstance(node, dict):
            raise SceneError(f"绑定目标路径不是对象: {path}", "SCENE_BINDING_ERROR")
        current = node
    current[segments[-1]] = deepcopy(value)


def _scalar_snapshot(value: Any, *, limit: int = 18) -> List[dict]:
    rows: List[dict] = []

    def visit(node: Any, path: str) -> None:
        if len(rows) >= limit:
            return
        if isinstance(node, dict):
            for key, child in node.items():
                child_path = f"{path}.{key}" if path else str(key)
                # File bodies and generated case dictionaries belong in the
                # artifact bundle, not in the compact work-order evidence.
                if str(key).lower() in {"files", "file_contents", "content"}:
                    continue
                visit(child, child_path)
                if len(rows) >= limit:
                    break
        elif isinstance(node, list):
            for index, child in enumerate(node[:4]):
                visit(child, f"{path}.{index}" if path else str(index))
                if len(rows) >= limit:
                    break
        elif isinstance(node, (str, int, float, bool)) or node is None:
            if isinstance(node, str) and len(node) > 240:
                rows.append({"path": path, "value": "<large text omitted>", "character_count": len(node)})
            else:
                rows.append({"path": path, "value": node})

    visit(value, "")
    return rows


def _narrative_actions(actions: List[dict]) -> List[dict]:
    """Return the minimum tool evidence allowed to leave the deterministic layer."""

    excluded_path_terms = {"path", "directory", "file", "content", "sha256", "manifest"}
    safe_actions = []
    for action in actions:
        safe_snapshot = []
        for row in action.get("result_snapshot") or []:
            path_terms = {term.lower() for term in str(row.get("path", "")).replace("[", ".").split(".")}
            if path_terms & excluded_path_terms:
                continue
            value = row.get("value")
            if isinstance(value, str) and (len(value) > 160 or value == "<large text omitted>"):
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                safe_snapshot.append({"path": row.get("path"), "value": value})
        safe_actions.append({
            "sequence": action["sequence"],
            "step_id": action["step_id"],
            "model_code": action["model_code"],
            "model_version": action["model_version"],
            "execution_id": action["execution_id"],
            "result_snapshot": safe_snapshot[:8],
        })
    return safe_actions


class SceneOrchestrationService:
    """Versioned recipes, deterministic execution graphs and reviewable work orders."""

    def __init__(self, registry: ModelRegistry, executor: ModelExecutionService, store: InMemoryTraceStore):
        self.registry = registry
        self.executor = executor
        self.store = store
        self._validate_catalog()

    def _validate_catalog(self) -> None:
        recipe_ids = set()
        for scene_id, scene in SCENE_DEFINITIONS.items():
            for recipe in scene["recipes"]:
                if recipe["recipe_id"] in recipe_ids:
                    raise RuntimeError(f"重复场景配方ID: {recipe['recipe_id']}")
                recipe_ids.add(recipe["recipe_id"])
                seen = set()
                for step in recipe["steps"]:
                    if step["step_id"] in seen:
                        raise RuntimeError(f"{recipe['recipe_id']}存在重复步骤: {step['step_id']}")
                    seen.add(step["step_id"])
                    if not self.registry.get(step["model_code"]):
                        raise RuntimeError(f"{scene_id}配方引用未知工具: {step['model_code']}")
                    missing = set(step["depends_on"]) - seen
                    if missing:
                        raise RuntimeError(f"{step['step_id']}依赖未按拓扑顺序定义: {sorted(missing)}")

    def _scene_tool_ids(self, scene: dict) -> List[str]:
        all_ids = sorted(self.registry._models)
        if "*" in scene["families"]:
            return all_ids
        allowed = set(scene["extra_tools"])
        allowed.update(code for code in all_ids if code[0] in scene["families"])
        return sorted(allowed)

    def _recipe(self, scene_id: str, recipe_id: str) -> tuple[dict, dict]:
        scene = SCENE_DEFINITIONS.get(scene_id)
        if not scene:
            raise SceneError(f"未知业务场景: {scene_id}", "SCENE_NOT_FOUND")
        recipe = next((item for item in scene["recipes"] if item["recipe_id"] == recipe_id), None)
        if not recipe:
            raise SceneError(f"场景{scene_id}中不存在配方: {recipe_id}", "RECIPE_NOT_FOUND")
        return scene, recipe

    def _normal_example(self, model_code: str) -> dict:
        model = self.registry.get(model_code)
        for case in model.qualification_cases:
            if case.get("kind") == "normal":
                return deepcopy(case["input"])
        return {}

    def _public_recipe(self, scene_id: str, recipe: dict, include_contract: bool) -> dict:
        steps = []
        sample_arguments = {}
        overrides = recipe.get("sample_overrides", {})
        for raw in recipe["steps"]:
            model = self.registry.get(raw["model_code"])
            step = {**deepcopy(raw), "model_name": model.name, "model_version": model.version}
            if include_contract:
                step["input_schema"] = model.get_llm_input_schema()
                step["applicable_boundary"] = model.applicable_boundary
            steps.append(step)
            if raw["default_selected"]:
                sample_arguments[raw["step_id"]] = deepcopy(overrides.get(raw["step_id"], self._normal_example(raw["model_code"])))
        public_steps = steps if include_contract else [
            {key: step[key] for key in ("step_id", "model_code", "model_name", "purpose", "depends_on", "default_selected", "artifact_recommended")}
            for step in steps
        ]
        return {
            "scene_id": scene_id,
            "recipe_id": recipe["recipe_id"],
            "name": recipe["name"],
            "version": recipe["version"],
            "description": recipe["description"],
            "steps": public_steps,
            "default_selected_steps": [step["step_id"] for step in recipe["steps"] if step["default_selected"]],
            "sample_request": {
                "selected_steps": [step["step_id"] for step in recipe["steps"] if step["default_selected"]],
                "arguments_by_step": sample_arguments,
                "options": {
                    "stop_on_error": True,
                    "artifact_steps": [step["step_id"] for step in recipe["steps"] if step["default_selected"] and step["artifact_recommended"]],
                    "artifact_mode": "directory_and_zip",
                },
            } if include_contract else None,
        }

    def list_scenes(self) -> dict:
        counts = self.registry.get_counts()
        scenes = []
        for scene_id, scene in SCENE_DEFINITIONS.items():
            tool_ids = self._scene_tool_ids(scene)
            scenes.append({
                "scene_id": scene_id,
                "name": scene["name"],
                "short_name": scene["short_name"],
                "description": scene["description"],
                "icon": scene["icon"],
                "color": scene["color"],
                "applicable_tool_count": len(tool_ids),
                "applicable_tool_ids": tool_ids,
                "featured_tools": [{"model_code": code, "name": self.registry.get(code).name} for code in scene["featured_tools"]],
                "recipes": [self._public_recipe(scene_id, recipe, False) for recipe in scene["recipes"]],
            })
        return {
            **counts,
            "scene_count": len(scenes),
            "tool_count_semantics": "场景复用注册工具；同一工具跨场景出现仍只计数一次",
            "scenes": scenes,
        }

    def get_recipe(self, scene_id: str, recipe_id: str) -> dict:
        _, recipe = self._recipe(scene_id, recipe_id)
        return self._public_recipe(scene_id, recipe, True)

    def get_scene(self, scene_id: str) -> dict:
        scene = next((item for item in self.list_scenes()["scenes"] if item["scene_id"] == scene_id), None)
        if not scene:
            raise SceneError(f"未知业务场景: {scene_id}", "SCENE_NOT_FOUND")
        return scene

    def execute_recipe(self, scene_id: str, recipe_id: str, request: dict) -> dict:
        _, recipe = self._recipe(scene_id, recipe_id)
        arguments_by_step = request.get("arguments_by_step")
        if not isinstance(arguments_by_step, dict):
            raise SceneError("arguments_by_step必须是对象")
        selected = request.get("selected_steps")
        if selected is None:
            selected = [step["step_id"] for step in recipe["steps"] if step["default_selected"]]
        if not isinstance(selected, list) or not selected or any(not isinstance(item, str) for item in selected):
            raise SceneError("selected_steps必须是非空字符串数组")
        if len(selected) != len(set(selected)):
            raise SceneError("selected_steps不能重复")

        steps_by_id = {step["step_id"]: step for step in recipe["steps"]}
        unknown = set(selected) - set(steps_by_id)
        if unknown:
            raise SceneError(f"配方中不存在步骤: {sorted(unknown)}", "SCENE_STEP_NOT_FOUND")
        selected_set = set(selected)
        for step_id in selected:
            missing = set(steps_by_id[step_id]["depends_on"]) - selected_set
            if missing:
                raise SceneError(f"步骤{step_id}缺少依赖: {sorted(missing)}", "SCENE_DEPENDENCY_MISSING")

        options = request.get("options") or {}
        if not isinstance(options, dict):
            raise SceneError("options必须是对象")
        stop_on_error = options.get("stop_on_error", True)
        artifact_steps = options.get("artifact_steps", [])
        artifact_mode = options.get("artifact_mode", "directory_and_zip")
        if not isinstance(stop_on_error, bool):
            raise SceneError("stop_on_error必须是布尔值")
        if not isinstance(artifact_steps, list) or not set(artifact_steps).issubset(selected_set):
            raise SceneError("artifact_steps必须是selected_steps的子集")
        if artifact_mode not in {"directory", "directory_and_zip"}:
            raise SceneError("artifact_mode必须为directory或directory_and_zip")

        run_id = _id("SCENE")
        trace_id = _id("TRACE")
        started_at = time.time()
        records: Dict[str, dict] = {}
        ordered_records = []
        failed = False
        for step in recipe["steps"]:
            step_id = step["step_id"]
            if step_id not in selected_set:
                continue
            if failed and stop_on_error:
                ordered_records.append({
                    "step_id": step_id,
                    "model_code": step["model_code"],
                    "status": "skipped",
                    "error": "上游步骤失败，按stop_on_error停止",
                    "error_code": "SCENE_UPSTREAM_FAILED",
                })
                continue
            arguments = deepcopy(arguments_by_step.get(step_id, {}))
            if not isinstance(arguments, dict):
                raise SceneError(f"arguments_by_step.{step_id}必须是对象")
            for target_path, binding in step["bindings"].items():
                if "constant" in binding:
                    value = binding["constant"]
                else:
                    source = records.get(binding["step"])
                    if not source or source.get("status") != "success":
                        raise SceneError(f"步骤{step_id}无法读取上游{binding['step']}", "SCENE_BINDING_ERROR")
                    value = _get_path(source, binding["path"])
                    include_keys = binding.get("include_keys")
                    if include_keys is not None:
                        if not isinstance(value, dict):
                            raise SceneError(f"步骤{step_id}的include_keys只能用于对象绑定", "SCENE_BINDING_ERROR")
                        value = {key: value.get(key, 0.0) for key in include_keys}
                _set_path(arguments, target_path, value)
            if step["model_code"] == "G013" and "context" not in arguments:
                arguments["context"] = {key: value.get("output") for key, value in records.items() if value.get("status") == "success"}

            execute_options = {"validate_boundary": True, "return_provenance": True}
            if step_id in artifact_steps:
                if step["model_code"] == "G005":
                    arguments["artifact_mode"] = artifact_mode
                else:
                    execute_options["artifact"] = {"mode": artifact_mode, "name": f"{run_id.lower()}-{step_id}"}
            record = self.executor.execute(
                step["model_code"],
                arguments,
                trace_id=trace_id,
                user_or_agent=f"scene:{scene_id}:{recipe_id}",
                options=execute_options,
            )
            public_record = {"step_id": step_id, "purpose": step["purpose"], **record}
            records[step_id] = public_record
            ordered_records.append(public_record)
            if record["status"] != "success":
                failed = True

        succeeded = [item for item in ordered_records if item["status"] == "success"]
        safety = [item for item in succeeded if item["model_code"] == "G013"]
        safety_passed = bool(safety) and all(bool(item.get("output", {}).get("passed")) for item in safety)
        boundary_warning_count = sum(len((item.get("boundary_check") or {}).get("warnings") or []) for item in succeeded)
        status = "success" if len(succeeded) == len(selected) else "rejected" if failed else "partial"
        run = {
            "run_id": run_id,
            "trace_id": trace_id,
            "scene_id": scene_id,
            "recipe_id": recipe_id,
            "recipe_version": recipe["version"],
            "status": status,
            "selected_steps": selected,
            "steps": ordered_records,
            "successful_step_count": len(succeeded),
            "requested_step_count": len(selected),
            "safety_gate_present": bool(safety),
            "safety_gate_passed": safety_passed,
            "boundary_warning_count": boundary_warning_count,
            "work_order_release_eligible": status == "success" and safety_passed and any(item["model_code"] != "G013" for item in succeeded),
            "started_at": started_at,
            "completed_at": time.time(),
            "tool_count_effect": 0,
        }
        self.store.save_scene_run(run)
        return run

    def get_run(self, run_id: str) -> dict:
        run = self.store.get_scene_run(run_id)
        if not run:
            raise SceneError(f"未知场景运行: {run_id}", "SCENE_RUN_NOT_FOUND")
        return run

    def compile_work_order(self, scene_id: str, request: dict) -> dict:
        run_id = request.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise SceneError("run_id不能为空")
        run = self.get_run(run_id)
        if run["scene_id"] != scene_id:
            raise SceneError("run_id不属于请求场景", "SCENE_RUN_MISMATCH")
        successful = [step for step in run["steps"] if step.get("status") == "success"]
        if not successful:
            raise SceneError("没有成功的工具执行，不能编译工单", "WORK_ORDER_NO_EVIDENCE")
        scene = SCENE_DEFINITIONS[scene_id]
        work_order_id = _id("WO")
        title = request.get("title") or f"{scene['short_name']} · {run['recipe_id']} 技术工单"
        if not isinstance(title, str) or not title.strip() or len(title) > 160:
            raise SceneError("title必须是1至160字符字符串")
        operator_notes = request.get("operator_notes", "")
        if not isinstance(operator_notes, str) or len(operator_notes) > 2000:
            raise SceneError("operator_notes必须是不超过2000字符的字符串")

        actions = []
        artifacts = []
        provenance = []
        for index, step in enumerate(successful, start=1):
            model = self.registry.get(step["model_code"])
            snapshot = _scalar_snapshot(step.get("output"))
            actions.append({
                "sequence": index,
                "step_id": step["step_id"],
                "action": f"复核{model.name}的计算结果、单位、适用域和边界警告",
                "model_code": model.model_id,
                "model_version": model.version,
                "execution_id": step["execution_id"],
                "result_snapshot": snapshot,
                "boundary_check": step.get("boundary_check"),
            })
            provenance.extend(step.get("actual_data_records") or [])
            artifact = step.get("artifact")
            if artifact:
                artifacts.append({"step_id": step["step_id"], "execution_id": step["execution_id"], **artifact})
            native_output = step.get("output") or {}
            if step["model_code"] == "G005" and native_output.get("materialized"):
                artifacts.append({
                    "step_id": step["step_id"],
                    "execution_id": step["execution_id"],
                    "delivery": "native_case_bundle",
                    "zip_path": native_output.get("zip_path"),
                    "verified": native_output.get("readback_verified", False),
                    "solver_status": "case_generated_not_solved",
                })

        safety_steps = [step for step in successful if step["model_code"] == "G013"]
        violations = []
        for step in safety_steps:
            violations.extend((step.get("output") or {}).get("violations") or [])
        release_eligible = bool(run["work_order_release_eligible"])
        status = "ready_for_human_review" if release_eligible else "draft_unverified"
        unique_provenance = []
        seen_sources = set()
        for item in provenance:
            key = json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
            if key not in seen_sources:
                seen_sources.add(key)
                unique_provenance.append(item)

        lines = [
            f"# {title}",
            "",
            f"- 工单编号：{work_order_id}",
            f"- 场景：{scene['name']}",
            f"- 配方：{run['recipe_id']} / {run['recipe_version']}",
            f"- 运行编号：{run_id}",
            f"- 状态：{status}",
            f"- 安全规则：{'通过' if run['safety_gate_passed'] else '未通过或未执行'}",
            "- 执行范围：决策支持；平台不会自动下发生产控制指令",
            "",
            "## 计算与复核步骤",
            "",
        ]
        for action in actions:
            lines.append(f"{action['sequence']}. {action['model_code']} {action['action']}（执行ID：{action['execution_id']}）")
        lines.extend(["", "## 人工复核", "", "- 当前状态：等待人工审核", "- 审核前不得作为自动控制指令下发"])
        if operator_notes:
            lines.extend(["", "## 操作备注", "", operator_notes])

        work_order = {
            "work_order_id": work_order_id,
            "scene_id": scene_id,
            "scene_name": scene["name"],
            "title": title,
            "status": status,
            "release_eligible": release_eligible,
            "dispatch_supported": False,
            "scope": "decision_support_only",
            "source_run_id": run_id,
            "source_trace_id": run["trace_id"],
            "recipe_id": run["recipe_id"],
            "recipe_version": run["recipe_version"],
            "actions": actions,
            "safety": {
                "gate_present": run["safety_gate_present"],
                "passed": run["safety_gate_passed"],
                "violations": violations,
                "boundary_warning_count": run["boundary_warning_count"],
            },
            "artifacts": artifacts,
            "provenance": unique_provenance,
            "operator_notes": operator_notes,
            "approval": {"status": "pending", "reviewer": None, "comment": "", "reviewed_at": None},
            "deterministic_markdown": "\n".join(lines),
            "narrative_context": {
                "title": title,
                "scene": scene["name"],
                "recipe_id": run["recipe_id"],
                "run_id": run_id,
                "release_eligible": release_eligible,
                "safety": {"passed": run["safety_gate_passed"], "violations": violations},
                "actions": _narrative_actions(actions),
            },
            "text_generation_policy": {
                "deterministic_template_available": True,
                "llm_assistance_optional": True,
                "llm_may_change_numeric_results": False,
                "llm_may_approve_or_dispatch": False,
                "human_review_required": True,
                "data_minimization": "仅发送执行标识和短标量结果；文件正文、路径、来源记录及操作备注不进入模型上下文",
            },
            "created_at": time.time(),
            "updated_at": time.time(),
            "tool_count_effect": 0,
        }
        self.store.save_work_order(work_order)
        return work_order

    def get_work_order(self, work_order_id: str) -> dict:
        work_order = self.store.get_work_order(work_order_id)
        if not work_order:
            raise SceneError(f"未知工单: {work_order_id}", "WORK_ORDER_NOT_FOUND")
        return work_order

    def review_work_order(self, work_order_id: str, request: dict) -> dict:
        work_order = self.get_work_order(work_order_id)
        if work_order["approval"]["status"] != "pending":
            raise SceneError("工单已经完成审核，不能重复审核", "WORK_ORDER_ALREADY_REVIEWED")
        action = request.get("action")
        reviewer = request.get("reviewer")
        comment = request.get("comment", "")
        if action not in {"approve", "reject"}:
            raise SceneError("action必须为approve或reject")
        if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 120:
            raise SceneError("reviewer必须是1至120字符字符串")
        if not isinstance(comment, str) or len(comment) > 1000:
            raise SceneError("comment必须是不超过1000字符的字符串")
        if action == "approve" and not work_order["release_eligible"]:
            raise SceneError("安全规则未通过或工具链不完整，禁止批准", "WORK_ORDER_NOT_RELEASE_ELIGIBLE")
        previous_status = work_order["status"]
        work_order["approval"] = {
            "status": "approved" if action == "approve" else "rejected",
            "reviewer": reviewer.strip(),
            "comment": comment,
            "reviewed_at": time.time(),
        }
        work_order["status"] = "approved_for_manual_execution" if action == "approve" else "rejected_by_reviewer"
        review_label = "已批准，仅供人工执行" if action == "approve" else "已驳回"
        work_order["deterministic_markdown"] = work_order["deterministic_markdown"].replace(
            f"- 状态：{previous_status}",
            f"- 状态：{work_order['status']}",
            1,
        ).replace(
            "- 当前状态：等待人工审核",
            f"- 当前状态：{review_label}\n- 审核人：{reviewer.strip()}\n- 审核意见：{comment or '无'}",
            1,
        )
        work_order["updated_at"] = time.time()
        self.store.save_work_order(work_order)
        return work_order
