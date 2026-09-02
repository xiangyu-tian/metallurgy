"""P1-W18 safe simulation, optimization, and constraint tools.

The orchestration tools in this module can call only fully eligible models in
the local registry.  They never evaluate source strings, import caller-chosen
modules, execute shell commands, or write caller-chosen filesystem paths.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import re
from copy import deepcopy
from typing import Any, Iterable, Optional

import numpy as np

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


ORCHESTRATOR_BLOCKLIST = {"G006", "G009", "G010", "G011", "G012"}


def rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def finite(
    value: Any,
    label: str,
    *,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    strict_minimum: bool = False,
) -> tuple[float | None, str | None]:
    if isinstance(value, bool):
        return None, f"{label}必须是数值"
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(parsed):
        return None, f"{label}必须是有限数值"
    if minimum is not None and (parsed <= minimum if strict_minimum else parsed < minimum):
        sign = "大于" if strict_minimum else "不小于"
        return None, f"{label}必须{sign}{minimum:g}"
    if maximum is not None and parsed > maximum:
        return None, f"{label}不能大于{maximum:g}"
    return parsed, None


def integer(value: Any, label: str, minimum: int, maximum: int) -> tuple[int | None, str | None]:
    parsed, error = finite(value, label, minimum=minimum, maximum=maximum)
    if error:
        return None, error
    if not parsed.is_integer():
        return None, f"{label}必须是整数"
    return int(parsed), None


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def split_path(path: Any, label: str) -> tuple[list[str] | None, str | None]:
    if not isinstance(path, str) or not path.strip():
        return None, f"{label}必须是非空点路径"
    tokens = path.split(".")
    if len(tokens) > 16 or any(not token or len(token) > 128 for token in tokens):
        return None, f"{label}路径层级或字段长度超限"
    if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*|0|[1-9][0-9]*", token) for token in tokens):
        return None, f"{label}包含非法路径片段"
    return tokens, None


def read_path(root: Any, path: str, label: str) -> tuple[Any, str | None]:
    tokens, error = split_path(path, label)
    if error:
        return None, error
    current = root
    for token in tokens:
        if isinstance(current, dict):
            if token not in current:
                return None, f"{label}不存在: {path}"
            current = current[token]
        elif isinstance(current, list) and token.isdigit():
            index = int(token)
            if index >= len(current):
                return None, f"{label}数组下标越界: {path}"
            current = current[index]
        else:
            return None, f"{label}无法继续解析: {path}"
    return current, None


def write_numeric_path(root: dict[str, Any], path: str, value: float, label: str) -> str | None:
    tokens, error = split_path(path, label)
    if error:
        return error
    current: Any = root
    for token in tokens[:-1]:
        if isinstance(current, dict):
            if token not in current:
                return f"{label}不存在: {path}"
            current = current[token]
        elif isinstance(current, list) and token.isdigit():
            index = int(token)
            if index >= len(current):
                return f"{label}数组下标越界: {path}"
            current = current[index]
        else:
            return f"{label}无法继续解析: {path}"
    last = tokens[-1]
    if isinstance(current, dict):
        if last not in current:
            return f"{label}不存在: {path}"
        existing = current[last]
        if isinstance(existing, bool) or not isinstance(existing, (int, float)):
            return f"{label}目标不是数值: {path}"
        current[last] = value
        return None
    if isinstance(current, list) and last.isdigit():
        index = int(last)
        if index >= len(current):
            return f"{label}数组下标越界: {path}"
        existing = current[index]
        if isinstance(existing, bool) or not isinstance(existing, (int, float)):
            return f"{label}目标不是数值: {path}"
        current[index] = value
        return None
    return f"{label}无法写入: {path}"


def eligible_target(model_code: Any):
    if not isinstance(model_code, str) or not re.fullmatch(r"[A-Z][0-9]{3}", model_code):
        return None, None, "target_model_code必须是标准模型码"
    if model_code in ORCHESTRATOR_BLOCKLIST:
        return None, None, f"禁止递归或嵌套编排目标: {model_code}"
    from .registry import ModelRegistry

    target_registry = ModelRegistry()
    target_registry.discover()
    target = target_registry.get(model_code)
    if target is None:
        return None, None, f"目标工具不存在: {model_code}"
    eligibility = target_registry.eligibility_report(model_code)
    if not eligibility["fully_eligible"]:
        return None, None, f"目标工具未通过完全准入: {model_code}"
    return target_registry, target, None


def invoke_target(
    registry: Any,
    target: Any,
    params: dict[str, Any],
    *,
    allow_boundary_warning: bool,
) -> tuple[dict[str, Any] | None, str | None, str | None, bool]:
    result = registry.invoke(target.model_id, params)
    if not result.success:
        return None, result.error, result.error_code, False
    boundary_passed = bool(result.boundary_check and result.boundary_check.passed)
    if not boundary_passed and not allow_boundary_warning:
        return None, "目标工具返回边界警告且调用未授权接受", "OUT_OF_DOMAIN", False
    return result.result, None, None, boundary_passed


def parse_variables(raw: Any, *, maximum: int) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= maximum:
        return None, f"variables必须含1至{maximum}项"
    parsed = []
    paths = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) != {"path", "lower_bound", "upper_bound"}:
            return None, f"variables[{index}]字段必须恰为path/lower_bound/upper_bound"
        path, error = split_path(item["path"], f"variables[{index}].path")
        if error:
            return None, error
        path_text = ".".join(path)
        if path_text in paths:
            return None, f"变量路径重复: {path_text}"
        lower, error = finite(item["lower_bound"], f"variables[{index}].lower_bound")
        if error:
            return None, error
        upper, error = finite(item["upper_bound"], f"variables[{index}].upper_bound")
        if error:
            return None, error
        if lower >= upper:
            return None, f"variables[{index}]下界必须小于上界"
        paths.add(path_text)
        parsed.append({"path": path_text, "lower_bound": lower, "upper_bound": upper})
    return parsed, None


def parse_constraints(raw: Any) -> tuple[list[dict[str, Any]] | None, str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list) or len(raw) > 8:
        return None, "constraints必须是至多8项的数组"
    constraints = []
    names = set()
    for index, item in enumerate(raw):
        expected = {"name", "output_path", "operator", "threshold"}
        if not isinstance(item, dict) or set(item) != expected:
            return None, f"constraints[{index}]字段必须恰为name/output_path/operator/threshold"
        name = item["name"]
        if not isinstance(name, str) or not name.strip() or name in names:
            return None, f"constraints[{index}].name为空或重复"
        _, error = split_path(item["output_path"], f"constraints[{index}].output_path")
        if error:
            return None, error
        if item["operator"] not in {"less_than_or_equal", "greater_than_or_equal"}:
            return None, f"constraints[{index}].operator不受支持"
        threshold, error = finite(item["threshold"], f"constraints[{index}].threshold")
        if error:
            return None, error
        names.add(name)
        constraints.append({**item, "threshold": threshold})
    return constraints, None


def constraint_values(output: dict[str, Any], constraints: list[dict[str, Any]]) -> tuple[list[dict[str, Any]] | None, str | None]:
    results = []
    for constraint in constraints:
        raw, error = read_path(output, constraint["output_path"], f"constraint:{constraint['name']}")
        if error:
            return None, error
        value, error = finite(raw, f"constraint:{constraint['name']}")
        if error:
            return None, error
        threshold = constraint["threshold"]
        if constraint["operator"] == "less_than_or_equal":
            violation = max(0.0, value - threshold)
        else:
            violation = max(0.0, threshold - value)
        scale = max(1.0, abs(threshold))
        results.append({
            "name": constraint["name"],
            "value": value,
            "operator": constraint["operator"],
            "threshold": threshold,
            "satisfied": violation <= 1e-12 * scale,
            "normalized_violation": violation / scale,
        })
    return results, None


VARIABLE_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "lower_bound": {"type": "number"},
        "upper_bound": {"type": "number"},
    },
    "required": ["path", "lower_bound", "upper_bound"],
    "additionalProperties": False,
}

CONSTRAINT_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "output_path": {"type": "string"},
        "operator": {"type": "string", "enum": ["less_than_or_equal", "greater_than_or_equal"]},
        "threshold": {"type": "number"},
    },
    "required": ["name", "output_path", "operator", "threshold"],
    "additionalProperties": False,
}


class W18FormulaTool(BaseModelTool):
    scenario = "仿真/优化/智能体支撑"
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class G005_OpenFOAMCaseGenerator(W18FormulaTool):
    model_id, name, version = "G005", "OpenFOAM参数化导热案例生成", "1.0.0"
    tool_name = "metallurgy_generate_openfoam_laplacian_case"
    description = "把受限长方体、网格、扩散率和温度边界渲染为可落盘的OpenFOAM v13 laplacianFoam完整案例清单；不写本机路径、不执行求解器。"
    applicable_boundary = (
        "OpenFOAM Foundation v13 laplacianFoam；单块正交六面体，x向定值温度，其他面零梯度；"
        "总单元数不超过2,000,000。输出是经过结构校验的文件清单，不声称本机已运行OpenFOAM。"
    )
    formula_reference = "OpenFOAM v13 case hierarchy, blockMesh right-handed hexahedron and laplacianFoam field/property dictionaries"
    source_version = "openfoam-foundation-v13-case-template-w18-v1"
    data_source = ["OpenFOAM Foundation v13 User Guide", "OpenFOAM v13 laplacianFoam source guide"]
    source_records = [
        {"source_id": "OPENFOAM-V13-CASE-STRUCTURE", "name": "OpenFOAM v13 case file structure", "version": "v13", "url": "https://doc.cfd.direct/openfoam/user-guide-v13/case-file-structure"},
        {"source_id": "OPENFOAM-V13-BLOCKMESH", "name": "OpenFOAM v13 blockMesh guide", "version": "v13", "url": "https://doc.cfd.direct/openfoam/user-guide-v13/blockmesh"},
        {"source_id": "OPENFOAM-V13-LAPLACIAN", "name": "OpenFOAM v13 laplacianFoam source guide", "version": "v13", "url": "https://cpp.openfoam.org/v13/dir_2eb0e56db9e71973c1240c4d553b433f.html"},
    ]
    failure_modes = ["案例名含路径或非法字符", "几何、扩散率、温度或时间参数越界", "网格数不是整数", "总单元数超限", "写出间隔或步长与终止时间不一致", "模板缺少必需文件或边界名不一致"]
    independent_validation = ["blockMesh含8顶点和6个外表面且顶点顺序为右手系", "总单元数等于三向单元数乘积", "必需0/constant/system文件齐全", "边界名在网格与温度场中一致", "相同输入逐文件及总清单SHA-256一致"]
    dependencies = ["G001"]
    relations = [
        rel("depends_on", "G001", "网格尺度和单元总量可交由G001进一步做质量筛选"),
        rel("overlaps", "G003", "二者都描述导热PDE；G003直接求数值场，G005生成外部OpenFOAM案例"),
        rel("upstream_of", "G006", "G006可在多个参数组合上调用G005生成案例族"),
    ]
    input_fields = [
        InputField("case_name", "安全案例名", "string", description="仅字母数字下划线和短横线，1至64字符"),
        InputField("length_x_m", "x向长度", "number", unit="m", min_value=1e-6, max_value=100),
        InputField("length_y_m", "y向长度", "number", unit="m", min_value=1e-6, max_value=100),
        InputField("length_z_m", "z向长度", "number", unit="m", min_value=1e-6, max_value=100),
        InputField("cells_x", "x向单元数", "number", unit="1", min_value=1, max_value=10000),
        InputField("cells_y", "y向单元数", "number", unit="1", min_value=1, max_value=10000),
        InputField("cells_z", "z向单元数", "number", unit="1", min_value=1, max_value=10000),
        InputField("diffusivity_m2_s", "标量扩散率", "number", unit="m²/s", min_value=1e-12, max_value=1),
        InputField("left_temperature_k", "左侧定值温度", "number", unit="K", min_value=1, max_value=5000),
        InputField("right_temperature_k", "右侧定值温度", "number", unit="K", min_value=1, max_value=5000),
        InputField("time_step_s", "时间步", "number", unit="s", min_value=1e-9, max_value=1e9),
        InputField("end_time_s", "终止时间", "number", unit="s", min_value=1e-9, max_value=1e12),
        InputField("write_interval_s", "写出间隔", "number", unit="s", min_value=1e-9, max_value=1e12),
    ]
    output_fields = [
        OutputField("case_name", "案例名", "string"),
        OutputField("solver", "求解器", "string"),
        OutputField("openfoam_version", "OpenFOAM目标版本", "string"),
        OutputField("cell_count", "单元总数", "number", "1"),
        OutputField("cell_sizes_m", "三向单元尺度", "object"),
        OutputField("files", "相对路径到文件内容的映射", "object"),
        OutputField("file_sha256", "逐文件SHA-256", "object"),
        OutputField("manifest_sha256", "总清单SHA-256", "string"),
        OutputField("execution_steps", "受控落盘后的执行步骤", "array"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "safe_case_name_without_path_components"},
        {"rule": "positive_bounded_geometry_diffusivity_and_time"},
        {"rule": "integer_mesh_counts_and_total_cells_at_most_2000000"},
        {"rule": "openfoam_v13_required_files_and_boundary_names"},
        {"rule": "deterministic_sha256_manifest"},
    ]
    qualification_cases = [
        {"id": "G005-N1", "kind": "normal", "input": {"case_name": "slab_heat_01", "length_x_m": 1.0, "length_y_m": 0.2, "length_z_m": 0.1, "cells_x": 20, "cells_y": 4, "cells_z": 2, "diffusivity_m2_s": 1e-5, "left_temperature_k": 1000, "right_temperature_k": 300, "time_step_s": 0.1, "end_time_s": 10, "write_interval_s": 1}},
        {"id": "G005-N2", "kind": "normal", "input": {"case_name": "billet-A", "length_x_m": 0.5, "length_y_m": 0.5, "length_z_m": 2.0, "cells_x": 5, "cells_y": 5, "cells_z": 20, "diffusivity_m2_s": 8e-6, "left_temperature_k": 1200, "right_temperature_k": 500, "time_step_s": 0.5, "end_time_s": 50, "write_interval_s": 5}},
        {"id": "G005-N3", "kind": "normal", "input": {"case_name": "equal_mesh", "length_x_m": 0.3, "length_y_m": 0.3, "length_z_m": 0.3, "cells_x": 3, "cells_y": 3, "cells_z": 3, "diffusivity_m2_s": 2e-5, "left_temperature_k": 900, "right_temperature_k": 600, "time_step_s": 1, "end_time_s": 20, "write_interval_s": 2}},
        {"id": "G005-B1", "kind": "boundary", "input": {"case_name": "isothermal", "length_x_m": 1, "length_y_m": 0.1, "length_z_m": 0.1, "cells_x": 10, "cells_y": 1, "cells_z": 1, "diffusivity_m2_s": 1e-5, "left_temperature_k": 500, "right_temperature_k": 500, "time_step_s": 1, "end_time_s": 10, "write_interval_s": 10}},
        {"id": "G005-F1", "kind": "failure", "input": {"case_name": "../escape", "length_x_m": 1, "length_y_m": 1, "length_z_m": 1, "cells_x": 10, "cells_y": 10, "cells_z": 10, "diffusivity_m2_s": 1e-5, "left_temperature_k": 500, "right_temperature_k": 300, "time_step_s": 1, "end_time_s": 10, "write_interval_s": 1}},
        {"id": "G005-F2", "kind": "failure", "input": {"case_name": "too_large", "length_x_m": 1, "length_y_m": 1, "length_z_m": 1, "cells_x": 200, "cells_y": 200, "cells_z": 200, "diffusivity_m2_s": 1e-5, "left_temperature_k": 500, "right_temperature_k": 300, "time_step_s": 1, "end_time_s": 10, "write_interval_s": 1}},
    ]

    @staticmethod
    def _header(object_name: str, location: str, class_name: str = "dictionary") -> str:
        return (
            "FoamFile\n{\n    version 2.0;\n    format ascii;\n    class " + class_name + ";\n"
            f"    location \"{location}\";\n    object {object_name};\n}}\n"
        )

    def invoke(self, params: dict, context=None) -> ModelResult:
        case_name = params.get("case_name")
        if not isinstance(case_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", case_name):
            return fail("case_name必须为1至64字符的安全标识，不得含路径分隔符")
        parsed: dict[str, float] = {}
        for key, lower, upper in (
            ("length_x_m", 1e-6, 100), ("length_y_m", 1e-6, 100), ("length_z_m", 1e-6, 100),
            ("diffusivity_m2_s", 1e-12, 1), ("left_temperature_k", 1, 5000),
            ("right_temperature_k", 1, 5000), ("time_step_s", 1e-9, 1e9),
            ("end_time_s", 1e-9, 1e12), ("write_interval_s", 1e-9, 1e12),
        ):
            value, error = finite(params.get(key), key, minimum=lower, maximum=upper)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            parsed[key] = value
        cells: dict[str, int] = {}
        for key in ("cells_x", "cells_y", "cells_z"):
            value, error = integer(params.get(key), key, 1, 10000)
            if error:
                return fail(error)
            cells[key] = value
        cell_count = cells["cells_x"] * cells["cells_y"] * cells["cells_z"]
        if cell_count > 2_000_000:
            return fail("总单元数超过2,000,000配额", "OUT_OF_DOMAIN")
        if parsed["time_step_s"] > parsed["end_time_s"]:
            return fail("time_step_s不能大于end_time_s", "OUT_OF_DOMAIN")
        if parsed["write_interval_s"] > parsed["end_time_s"]:
            return fail("write_interval_s不能大于end_time_s", "OUT_OF_DOMAIN")
        initial_temperature = 0.5 * (parsed["left_temperature_k"] + parsed["right_temperature_k"])
        lx, ly, lz = parsed["length_x_m"], parsed["length_y_m"], parsed["length_z_m"]
        block_mesh = self._header("blockMeshDict", "system") + f"""
convertToMeters 1;
vertices
(
    (0 0 0) ({lx:.17g} 0 0) ({lx:.17g} {ly:.17g} 0) (0 {ly:.17g} 0)
    (0 0 {lz:.17g}) ({lx:.17g} 0 {lz:.17g}) ({lx:.17g} {ly:.17g} {lz:.17g}) (0 {ly:.17g} {lz:.17g})
);
blocks
(
    hex (0 1 2 3 4 5 6 7) ({cells['cells_x']} {cells['cells_y']} {cells['cells_z']}) simpleGrading (1 1 1)
);
edges ();
boundary
(
    left {{ type patch; faces ((0 4 7 3)); }}
    right {{ type patch; faces ((1 2 6 5)); }}
    insulated {{ type wall; faces ((0 1 5 4) (3 7 6 2) (0 3 2 1) (4 5 6 7)); }}
);
mergePatchPairs ();
"""
        field = self._header("T", "0", "volScalarField") + f"""
dimensions [0 0 0 1 0 0 0];
internalField uniform {initial_temperature:.17g};
boundaryField
{{
    left {{ type fixedValue; value uniform {parsed['left_temperature_k']:.17g}; }}
    right {{ type fixedValue; value uniform {parsed['right_temperature_k']:.17g}; }}
    insulated {{ type zeroGradient; }}
}}
"""
        transport = self._header("transportProperties", "constant") + f"""
DT DT [0 2 -1 0 0 0 0] {parsed['diffusivity_m2_s']:.17g};
"""
        control = self._header("controlDict", "system") + f"""
application laplacianFoam;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime {parsed['end_time_s']:.17g};
deltaT {parsed['time_step_s']:.17g};
writeControl runTime;
writeInterval {parsed['write_interval_s']:.17g};
purgeWrite 0;
writeFormat ascii;
writePrecision 10;
writeCompression off;
timeFormat general;
timePrecision 10;
runTimeModifiable true;
"""
        schemes = self._header("fvSchemes", "system") + """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes { default none; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
"""
        solution = self._header("fvSolution", "system") + """
solvers
{
    T
    {
        solver PCG;
        preconditioner DIC;
        tolerance 1e-10;
        relTol 0;
    }
}
"""
        files = {
            "0/T": field,
            "constant/transportProperties": transport,
            "system/blockMeshDict": block_mesh,
            "system/controlDict": control,
            "system/fvSchemes": schemes,
            "system/fvSolution": solution,
        }
        required = {"0/T", "constant/transportProperties", "system/blockMeshDict", "system/controlDict", "system/fvSchemes", "system/fvSolution"}
        if set(files) != required or any(not isinstance(content, str) or not content.strip() for content in files.values()):
            return fail("生成的OpenFOAM案例缺少必需文件", "NUMERICAL_ERROR")
        for boundary in ("left", "right", "insulated"):
            if boundary not in block_mesh or boundary not in field:
                return fail(f"边界{boundary}未在网格和温度场中同时声明", "NUMERICAL_ERROR")
        file_hashes = {path: hashlib.sha256(content.encode("utf-8")).hexdigest() for path, content in sorted(files.items())}
        warnings = []
        if math.isclose(parsed["left_temperature_k"], parsed["right_temperature_k"], rel_tol=0, abs_tol=1e-12):
            warnings.append(BoundaryWarning("left_temperature_k", "两端温度相同，合法案例的稳态梯度为零"))
        if min(cells.values()) == 1:
            warnings.append(BoundaryWarning("mesh", "至少一个方向仅有1个单元，结果仅适合低维筛选"))
        return ModelResult(True, result={
            "case_name": case_name,
            "solver": "laplacianFoam",
            "openfoam_version": "OpenFOAM Foundation v13",
            "cell_count": cell_count,
            "cell_sizes_m": {"x": lx / cells["cells_x"], "y": ly / cells["cells_y"], "z": lz / cells["cells_z"]},
            "files": files,
            "file_sha256": file_hashes,
            "manifest_sha256": digest({"case_name": case_name, "files": files, "file_sha256": file_hashes}),
            "execution_steps": ["create case directory from returned relative paths", "run: blockMesh -case <caseDir>", "run: laplacianFoam -case <caseDir>"],
            "model_version": "openfoam-foundation-v13-case-template-w18-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


GRID_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "values": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 16},
    },
    "required": ["path", "values"],
    "additionalProperties": False,
}


class G006_ParametricRegisteredToolBatch(W18FormulaTool):
    model_id, name, version = "G006", "注册工具参数化仿真批处理", "1.0.0"
    tool_name = "metallurgy_run_registered_parametric_batch"
    description = "在受控配额内对一个已完全准入的注册工具执行笛卡尔参数网格，逐运行返回真实调用结果、错误与可复现摘要；不执行shell。"
    applicable_boundary = "1至4个数值参数轴，每轴2至16值，最多256个组合；目标必须已完全准入，禁止递归编排；失败重试至多2次。"
    formula_reference = "Cartesian product parameter design with deterministic registry execution, bounded retries and closure of planned/completed/success/failed counts"
    source_version = "registered-parametric-batch-w18-v1"
    data_source = ["Python itertools Cartesian product", "Local fully eligible ModelRegistry contract"]
    source_records = [{"source_id": "PYTHON-ITERTOOLS-PRODUCT", "name": "Python standard-library Cartesian product", "version": "Python 3.11", "url": "https://docs.python.org/3/library/itertools.html#itertools.product"}]
    failure_modes = ["目标不存在或未完全准入", "递归/嵌套编排目标", "参数路径缺失或不是数值", "网格项重复、非有限或超过配额", "全部运行失败", "目标返回边界警告且未授权"]
    independent_validation = ["计划运行数等于各轴长度乘积", "每个成功输出等于相同输入的直接注册调用", "参数组合顺序稳定", "完成数等于成功数加失败数", "相同批次摘要SHA-256一致"]
    dependencies = ["G005"]
    relations = [
        rel("downstream_of", "G005", "可批量调用G005生成不同网格/物性案例"),
        rel("overlaps", "G011", "都重复执行注册工具；G006穷举显式网格，G011用采集函数选择点"),
        rel("overlaps", "G012", "都批量评估候选；G006不做Pareto排序或进化"),
    ]
    input_fields = [
        InputField("target_model_code", "目标模型码", "string"),
        InputField("base_params", "目标基础参数", "object"),
        InputField("parameter_grid", "参数网格", "array", items=GRID_ITEM_SCHEMA, min_items=1, max_items=4),
        InputField("max_runs", "最大运行数", "number", unit="1", min_value=1, max_value=256),
        InputField("retry_count", "失败重试次数", "number", unit="1", min_value=0, max_value=2),
        InputField("allow_boundary_warning", "是否接受目标边界警告", "boolean"),
        InputField("stop_on_failure", "首次失败后停止", "boolean"),
    ]
    output_fields = [
        OutputField("target_model_code", "目标模型码", "string"),
        OutputField("grid_shape", "各轴长度", "array"),
        OutputField("planned_runs", "计划运行数", "number", "1"),
        OutputField("completed_runs", "完成运行数", "number", "1"),
        OutputField("successful_runs", "成功运行数", "number", "1"),
        OutputField("failed_runs", "失败运行数", "number", "1"),
        OutputField("runs", "逐运行记录", "array"),
        OutputField("batch_sha256", "批次摘要SHA-256", "string"),
        OutputField("stop_reason", "停止原因", "string"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "fully_eligible_non_recursive_target"},
        {"rule": "unique_numeric_parameter_paths_and_values"},
        {"rule": "cartesian_product_within_max_runs_and_256"},
        {"rule": "completed_equals_success_plus_failure"},
        {"rule": "successful_output_matches_direct_registry_call"},
    ]
    qualification_cases = [
        {"id": "G006-N1", "kind": "normal", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "parameter_grid": [{"path": "thermal_conductivity", "values": [10, 20, 40]}], "max_runs": 10, "retry_count": 0, "allow_boundary_warning": False, "stop_on_failure": False}},
        {"id": "G006-N2", "kind": "normal", "input": {"target_model_code": "A001", "base_params": {"value": 1, "source_unit": "kg", "target_unit": "g"}, "parameter_grid": [{"path": "value", "values": [1, 2, 3, 4]}], "max_runs": 4, "retry_count": 1, "allow_boundary_warning": False, "stop_on_failure": False}},
        {"id": "G006-N3", "kind": "normal", "input": {"target_model_code": "G005", "base_params": {"case_name": "batch_case", "length_x_m": 1, "length_y_m": 0.1, "length_z_m": 0.1, "cells_x": 10, "cells_y": 2, "cells_z": 2, "diffusivity_m2_s": 1e-5, "left_temperature_k": 900, "right_temperature_k": 300, "time_step_s": 1, "end_time_s": 10, "write_interval_s": 1}, "parameter_grid": [{"path": "cells_x", "values": [10, 20]}, {"path": "diffusivity_m2_s", "values": [1e-5, 2e-5]}], "max_runs": 4, "retry_count": 0, "allow_boundary_warning": False, "stop_on_failure": False}},
        {"id": "G006-B1", "kind": "boundary", "input": {"target_model_code": "C001", "base_params": {"A": 1, "Ea": 1000, "temperature": 1000, "Ea_unit": "J/mol"}, "parameter_grid": [{"path": "Ea", "values": [-1, 1000]}], "max_runs": 2, "retry_count": 1, "allow_boundary_warning": False, "stop_on_failure": False}},
        {"id": "G006-F1", "kind": "failure", "input": {"target_model_code": "G006", "base_params": {"value": 1}, "parameter_grid": [{"path": "value", "values": [1, 2]}], "max_runs": 2, "retry_count": 0, "allow_boundary_warning": False, "stop_on_failure": False}},
        {"id": "G006-F2", "kind": "failure", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "parameter_grid": [{"path": "thermal_conductivity", "values": [10, 20, 30]}, {"path": "area", "values": [1, 2, 3]}], "max_runs": 8, "retry_count": 0, "allow_boundary_warning": False, "stop_on_failure": False}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        target_registry, target, error = eligible_target(params.get("target_model_code"))
        if error:
            return fail(error, "MODEL_NOT_APPLICABLE")
        base_params = params.get("base_params")
        if not isinstance(base_params, dict):
            return fail("base_params必须是对象")
        grid = params.get("parameter_grid")
        if not isinstance(grid, list) or not 1 <= len(grid) <= 4:
            return fail("parameter_grid必须含1至4项")
        paths = set()
        axes: list[tuple[str, list[float]]] = []
        for index, item in enumerate(grid):
            if not isinstance(item, dict) or set(item) != {"path", "values"}:
                return fail(f"parameter_grid[{index}]字段必须恰为path/values")
            tokens, error = split_path(item["path"], f"parameter_grid[{index}].path")
            if error:
                return fail(error)
            path = ".".join(tokens)
            if path in paths:
                return fail(f"参数路径重复: {path}")
            values = item["values"]
            if not isinstance(values, list) or not 2 <= len(values) <= 16:
                return fail(f"parameter_grid[{index}].values必须含2至16项")
            parsed_values = []
            for value_index, raw in enumerate(values):
                value, error = finite(raw, f"parameter_grid[{index}].values[{value_index}]")
                if error:
                    return fail(error)
                parsed_values.append(value)
            if len(set(parsed_values)) != len(parsed_values):
                return fail(f"parameter_grid[{index}].values含重复值")
            probe = deepcopy(base_params)
            error = write_numeric_path(probe, path, parsed_values[0], f"parameter_grid[{index}].path")
            if error:
                return fail(error)
            paths.add(path)
            axes.append((path, parsed_values))
        max_runs, error = integer(params.get("max_runs"), "max_runs", 1, 256)
        if error:
            return fail(error)
        retry_count, error = integer(params.get("retry_count"), "retry_count", 0, 2)
        if error:
            return fail(error)
        allow_boundary_warning = params.get("allow_boundary_warning")
        stop_on_failure = params.get("stop_on_failure")
        if not isinstance(allow_boundary_warning, bool) or not isinstance(stop_on_failure, bool):
            return fail("allow_boundary_warning和stop_on_failure必须是布尔值")
        grid_shape = [len(values) for _, values in axes]
        planned = math.prod(grid_shape)
        if planned > max_runs:
            return fail(f"参数笛卡尔积{planned}超过max_runs={max_runs}", "OUT_OF_DOMAIN")
        runs = []
        successful = 0
        failed = 0
        stop_reason = "completed"
        for run_index, values in enumerate(itertools.product(*(values for _, values in axes)), 1):
            run_params = deepcopy(base_params)
            parameter_values = {}
            for (path, _), value in zip(axes, values):
                error = write_numeric_path(run_params, path, value, "parameter_grid.path")
                if error:
                    return fail(error)
                parameter_values[path] = value
            output = None
            error_message = None
            error_code = None
            boundary_passed = False
            attempt_count = 0
            for attempt in range(retry_count + 1):
                attempt_count = attempt + 1
                output, error_message, error_code, boundary_passed = invoke_target(
                    target_registry, target, run_params, allow_boundary_warning=allow_boundary_warning
                )
                if output is not None:
                    break
            if output is not None:
                successful += 1
                status = "success"
            else:
                failed += 1
                status = "failed"
            runs.append({
                "run_index": run_index,
                "parameter_values": parameter_values,
                "status": status,
                "attempt_count": attempt_count,
                "boundary_passed": boundary_passed,
                "output": output,
                "error_code": error_code,
                "error": error_message,
            })
            if status == "failed" and stop_on_failure:
                stop_reason = "stopped_on_failure"
                break
        completed = len(runs)
        if successful == 0:
            return fail("参数批次全部运行失败", "MODEL_NOT_APPLICABLE")
        warnings = []
        if failed:
            warnings.append(BoundaryWarning("runs", f"{failed}个参数组合失败；成功结果仍予返回"))
        if completed < planned:
            warnings.append(BoundaryWarning("stop_on_failure", "批次按请求在首次失败后提前停止"))
        stable_summary = {
            "target_model_code": target.model_id,
            "grid_shape": grid_shape,
            "planned_runs": planned,
            "completed_runs": completed,
            "successful_runs": successful,
            "failed_runs": failed,
            "runs": runs,
            "stop_reason": stop_reason,
        }
        return ModelResult(True, result={
            **stable_summary,
            "batch_sha256": digest(stable_summary),
            "model_version": "registered-parametric-batch-w18-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


RULE_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "description": {"type": "string"},
        "severity": {"type": "string", "enum": ["error", "warning"]},
        "assertion": {"type": "object"},
        "recommendation": {"type": "string"},
    },
    "required": ["id", "description", "severity", "assertion", "recommendation"],
    "additionalProperties": False,
}


class ExpressionError(ValueError):
    pass


class ExpressionEvaluator:
    MAX_DEPTH = 12
    MAX_NODES = 512

    def __init__(self, context: dict[str, Any]):
        self.context = context
        self.node_count = 0

    def evaluate(self, node: Any, depth: int = 0) -> Any:
        if depth > self.MAX_DEPTH:
            raise ExpressionError("表达式深度超过12")
        self.node_count += 1
        if self.node_count > self.MAX_NODES:
            raise ExpressionError("表达式节点数超过512")
        if not isinstance(node, dict):
            raise ExpressionError("表达式节点必须是对象")
        if set(node) == {"constant"}:
            value = node["constant"]
            if isinstance(value, float) and not math.isfinite(value):
                raise ExpressionError("常量必须是有限JSON值")
            return value
        if set(node) == {"path"}:
            value, error = read_path(self.context, node["path"], "expression.path")
            if error:
                raise ExpressionError(error)
            return value
        if set(node) != {"op", "args"} or not isinstance(node["op"], str) or not isinstance(node["args"], list):
            raise ExpressionError("运算节点必须恰含op和args")
        op = node["op"]
        args = [self.evaluate(item, depth + 1) for item in node["args"]]
        if op in {"add", "subtract", "multiply", "divide", "sum", "min", "max", "abs"}:
            numbers = []
            for index, value in enumerate(args):
                parsed, error = finite(value, f"{op}.args[{index}]")
                if error:
                    raise ExpressionError(error)
                numbers.append(parsed)
            if op == "add" and len(numbers) == 2:
                result = numbers[0] + numbers[1]
            elif op == "subtract" and len(numbers) == 2:
                result = numbers[0] - numbers[1]
            elif op == "multiply" and len(numbers) == 2:
                result = numbers[0] * numbers[1]
            elif op == "divide" and len(numbers) == 2:
                if numbers[1] == 0:
                    raise ExpressionError("表达式除零")
                result = numbers[0] / numbers[1]
            elif op == "sum" and numbers:
                result = sum(numbers)
            elif op == "min" and numbers:
                result = min(numbers)
            elif op == "max" and numbers:
                result = max(numbers)
            elif op == "abs" and len(numbers) == 1:
                result = abs(numbers[0])
            else:
                raise ExpressionError(f"{op}参数个数非法")
            if not math.isfinite(result):
                raise ExpressionError(f"{op}结果非有限")
            return result
        if op in {"less_than", "less_than_or_equal", "greater_than", "greater_than_or_equal", "equal", "not_equal"}:
            if len(args) != 2:
                raise ExpressionError(f"{op}必须有2个参数")
            return {
                "less_than": lambda: args[0] < args[1],
                "less_than_or_equal": lambda: args[0] <= args[1],
                "greater_than": lambda: args[0] > args[1],
                "greater_than_or_equal": lambda: args[0] >= args[1],
                "equal": lambda: args[0] == args[1],
                "not_equal": lambda: args[0] != args[1],
            }[op]()
        if op == "within":
            if len(args) != 3:
                raise ExpressionError("within必须有value/target/tolerance三个参数")
            value, target, tolerance = args
            for label, raw in (("value", value), ("target", target), ("tolerance", tolerance)):
                _, error = finite(raw, f"within.{label}")
                if error:
                    raise ExpressionError(error)
            if tolerance < 0:
                raise ExpressionError("within容差不能为负")
            return abs(value - target) <= tolerance
        if op in {"and", "or"}:
            if not args or any(not isinstance(value, bool) for value in args):
                raise ExpressionError(f"{op}必须有一个以上布尔参数")
            return all(args) if op == "and" else any(args)
        if op == "not":
            if len(args) != 1 or not isinstance(args[0], bool):
                raise ExpressionError("not必须有1个布尔参数")
            return not args[0]
        if op == "is_finite":
            if len(args) != 1:
                raise ExpressionError("is_finite必须有1个参数")
            return isinstance(args[0], (int, float)) and not isinstance(args[0], bool) and math.isfinite(float(args[0]))
        raise ExpressionError(f"未知表达式操作: {op}")


class G013_ConstraintRuleValidator(W18FormulaTool):
    model_id, name, version = "G013", "安全约束规则校验器", "1.0.0"
    tool_name = "metallurgy_validate_versioned_constraints"
    description = "以受限JSON表达式树校验模型输入输出和工艺约束，返回逐规则结论、违反项及摘要；不执行字符串代码。"
    applicable_boundary = "1至64条显式规则，表达式深度不超过12、总节点不超过512；仅常量、路径、算术、聚合、比较和布尔操作。"
    formula_reference = "Deterministic typed expression-tree evaluation with explicit operators, bounded depth/node count, and no code evaluation"
    source_version = "safe-constraint-expression-tree-w18-v1"
    data_source = ["Versioned caller-supplied JSON rules", "Mass/energy/process-boundary identities"]
    source_records = [{"source_id": "W18-SAFE-EXPRESSION-TREE", "name": "Reviewed finite expression-tree operator contract", "version": "1.0.0"}]
    failure_modes = ["规则ID重复或字段不完整", "表达式深度/节点数超限", "路径缺失", "未知操作", "除零或非数值算术", "断言结果不是布尔值"]
    independent_validation = ["质量与能量闭合规则直接复算", "比较和德摩根恒等式验证", "规则顺序变化不影响各ID结论", "未知操作和缺失路径关闭式失败", "违反项计数等于错误加警告"]
    dependencies = ["A005"]
    relations = [
        rel("depends_on", "A005", "守恒类规则与A005的物料闭合语义一致"),
        rel("downstream_of", "G006", "可校验批次结果中的计数和工艺边界"),
        rel("complements", "G011", "可对优化候选增加显式后验规则，但不替代目标工具内部边界"),
        rel("complements", "G012", "可独立审计Pareto解的约束满足性"),
    ]
    input_fields = [
        InputField("rule_set_id", "规则集ID", "string"),
        InputField("rule_set_version", "规则集版本", "string"),
        InputField("context", "待校验JSON上下文", "object"),
        InputField("rules", "显式规则数组", "array", items=RULE_ITEM_SCHEMA, min_items=1, max_items=64),
    ]
    output_fields = [
        OutputField("rule_set_id", "规则集ID", "string"),
        OutputField("rule_set_version", "规则集版本", "string"),
        OutputField("passed", "是否通过全部error规则", "boolean"),
        OutputField("rule_count", "规则数", "number", "1"),
        OutputField("error_count", "error违反数", "number", "1"),
        OutputField("warning_count", "warning违反数", "number", "1"),
        OutputField("evaluations", "逐规则结论", "array"),
        OutputField("violations", "违反规则", "array"),
        OutputField("rules_sha256", "规则集摘要SHA-256", "string"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "unique_complete_rule_records"},
        {"rule": "explicit_allowlisted_expression_operators_only"},
        {"rule": "maximum_depth_12_and_nodes_512"},
        {"rule": "assertion_must_evaluate_to_boolean"},
        {"rule": "violation_counts_close_exactly"},
    ]
    qualification_cases = [
        {"id": "G013-N1", "kind": "normal", "input": {"rule_set_id": "mass_balance", "rule_set_version": "1", "context": {"input": 100, "output": 99.99}, "rules": [{"id": "closure", "description": "质量残差不超过0.02", "severity": "error", "assertion": {"op": "within", "args": [{"path": "input"}, {"path": "output"}, {"constant": 0.02}]}, "recommendation": "检查物流"}]}},
        {"id": "G013-N2", "kind": "normal", "input": {"rule_set_id": "energy", "rule_set_version": "1", "context": {"in": [40, 60], "out": 100}, "rules": [{"id": "energy_closure", "description": "能量闭合", "severity": "error", "assertion": {"op": "equal", "args": [{"op": "sum", "args": [{"path": "in.0"}, {"path": "in.1"}]}, {"path": "out"}]}, "recommendation": "检查热项"}]}},
        {"id": "G013-N3", "kind": "normal", "input": {"rule_set_id": "process", "rule_set_version": "1", "context": {"temperature": 1873, "oxygen": 0.001}, "rules": [{"id": "domain", "description": "温度和氧同时在域内", "severity": "error", "assertion": {"op": "and", "args": [{"op": "greater_than_or_equal", "args": [{"path": "temperature"}, {"constant": 1773}]}, {"op": "less_than_or_equal", "args": [{"path": "oxygen"}, {"constant": 0.01}]}]}, "recommendation": "调整工况"}]}},
        {"id": "G013-B1", "kind": "boundary", "input": {"rule_set_id": "warning", "rule_set_version": "1", "context": {"value": 11}, "rules": [{"id": "limit", "description": "值不大于10", "severity": "warning", "assertion": {"op": "less_than_or_equal", "args": [{"path": "value"}, {"constant": 10}]}, "recommendation": "降低值"}]}},
        {"id": "G013-F1", "kind": "failure", "input": {"rule_set_id": "bad", "rule_set_version": "1", "context": {"value": 1}, "rules": [{"id": "unknown", "description": "未知操作", "severity": "error", "assertion": {"op": "execute", "args": [{"path": "value"}]}, "recommendation": "修正规则"}]}},
        {"id": "G013-F2", "kind": "failure", "input": {"rule_set_id": "missing", "rule_set_version": "1", "context": {"value": 1}, "rules": [{"id": "missing", "description": "缺失路径", "severity": "error", "assertion": {"op": "equal", "args": [{"path": "absent"}, {"constant": 1}]}, "recommendation": "补字段"}]}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        rule_set_id = params.get("rule_set_id")
        rule_set_version = params.get("rule_set_version")
        if not isinstance(rule_set_id, str) or not rule_set_id.strip() or len(rule_set_id) > 128:
            return fail("rule_set_id必须是1至128字符的非空字符串")
        if not isinstance(rule_set_version, str) or not rule_set_version.strip() or len(rule_set_version) > 64:
            return fail("rule_set_version必须是1至64字符的非空字符串")
        payload = params.get("context")
        rules = params.get("rules")
        if not isinstance(payload, dict):
            return fail("context必须是对象")
        if not isinstance(rules, list) or not 1 <= len(rules) <= 64:
            return fail("rules必须含1至64项")
        ids = set()
        evaluations = []
        violations = []
        evaluator = ExpressionEvaluator(payload)
        for index, rule in enumerate(rules):
            expected = {"id", "description", "severity", "assertion", "recommendation"}
            if not isinstance(rule, dict) or set(rule) != expected:
                return fail(f"rules[{index}]字段必须恰为id/description/severity/assertion/recommendation")
            rule_id = rule["id"]
            if not isinstance(rule_id, str) or not rule_id.strip() or rule_id in ids:
                return fail(f"rules[{index}].id为空或重复")
            if rule["severity"] not in {"error", "warning"}:
                return fail(f"rules[{index}].severity不受支持")
            if not isinstance(rule["description"], str) or not rule["description"].strip():
                return fail(f"rules[{index}].description不能为空")
            if not isinstance(rule["recommendation"], str):
                return fail(f"rules[{index}].recommendation必须是字符串")
            ids.add(rule_id)
            try:
                outcome = evaluator.evaluate(rule["assertion"])
            except ExpressionError as exc:
                code = "DIVISION_BY_ZERO" if "除零" in str(exc) else "INVALID_INPUT"
                return fail(f"规则{rule_id}求值失败: {exc}", code)
            if not isinstance(outcome, bool):
                return fail(f"规则{rule_id}断言结果不是布尔值")
            record = {"id": rule_id, "description": rule["description"], "severity": rule["severity"], "passed": outcome}
            evaluations.append(record)
            if not outcome:
                violations.append({**record, "recommendation": rule["recommendation"]})
        error_count = sum(item["severity"] == "error" for item in violations)
        warning_count = sum(item["severity"] == "warning" for item in violations)
        warnings = [BoundaryWarning("rules", f"规则{item['id']}未通过: {item['description']}", level=item["severity"]) for item in violations]
        rules_identity = {"rule_set_id": rule_set_id, "rule_set_version": rule_set_version, "rules": sorted(rules, key=lambda row: row["id"])}
        return ModelResult(True, result={
            "rule_set_id": rule_set_id,
            "rule_set_version": rule_set_version,
            "passed": error_count == 0,
            "rule_count": len(rules),
            "error_count": error_count,
            "warning_count": warning_count,
            "evaluations": evaluations,
            "violations": violations,
            "rules_sha256": digest(rules_identity),
            "model_version": "safe-constraint-expression-tree-w18-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


def first_primes(count: int) -> list[int]:
    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        if all(candidate % prime for prime in primes if prime * prime <= candidate):
            primes.append(candidate)
        candidate += 1
    return primes


def van_der_corput(index: int, base: int) -> float:
    fraction = 1.0
    value = 0.0
    while index:
        fraction /= base
        index, remainder = divmod(index, base)
        value += remainder * fraction
    return value


def halton_points(count: int, dimension: int, *, skip: int = 0) -> list[list[float]]:
    primes = first_primes(dimension)
    return [
        [van_der_corput(index + skip + 1, base) for base in primes]
        for index in range(count)
    ]


def scale_point(unit_point: Iterable[float], variables: list[dict[str, Any]]) -> list[float]:
    return [
        variable["lower_bound"] + float(unit) * (variable["upper_bound"] - variable["lower_bound"])
        for unit, variable in zip(unit_point, variables)
    ]


def point_key(point: Iterable[float]) -> tuple[float, ...]:
    return tuple(round(float(value), 14) for value in point)


def normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


class G011_BayesianOptimization(W18FormulaTool):
    model_id, name, version = "G011", "离线高斯过程贝叶斯优化", "1.0.0"
    tool_name = "metallurgy_run_offline_bayesian_optimization"
    description = "对一个已完全准入注册工具的连续参数执行固定RBF高斯过程与Expected Improvement离线序贯优化；不连接生产系统。"
    applicable_boundary = "1至4个连续变量，总评估预算5至40；目标和约束必须来自同一次受控注册工具输出；固定种子、固定核超参数、无观测噪声工程筛选。"
    formula_reference = "Gaussian-process regression with squared-exponential kernel and expected-improvement acquisition following Jones, Schonlau and Welch (1998)"
    source_version = "deterministic-gp-ei-w18-v1"
    data_source = ["Jones, Schonlau & Welch (1998)", "Local fully eligible ModelRegistry contract"]
    source_records = [{"source_id": "JONES-SCHONLAU-WELCH-1998", "name": "Efficient Global Optimization of Expensive Black-Box Functions", "version": "Journal of Global Optimization 13 (1998)", "url": "https://doi.org/10.1023/A:1008306431147"}]
    failure_modes = ["目标不存在、未准入或递归", "变量路径不可写或边界非法", "目标/约束输出不存在或非数值", "目标调用失败或未授权边界警告", "无可行点", "核矩阵分解或采集计算失败"]
    independent_validation = ["固定种子和输入产生完全相同历史", "单调目标的最优点落在已知边界", "最小化/最大化方向变换一致", "Expected Improvement非负", "可行最优点满足全部显式约束"]
    dependencies = ["G009", "G013"]
    relations = [
        rel("downstream_of", "G009", "可用G009先识别局部敏感变量，本工具再做全局序贯搜索"),
        rel("overlaps", "G006", "G006穷举显式网格，本工具用GP/EI按预算选点"),
        rel("overlaps", "G012", "均优化注册工具；本工具单目标且使用概率代理，G012返回多目标Pareto集"),
        rel("complements", "G013", "显式约束可由G013独立复核"),
    ]
    input_fields = [
        InputField("target_model_code", "目标模型码", "string"),
        InputField("base_params", "目标基础参数", "object"),
        InputField("variables", "连续变量", "array", items=VARIABLE_ITEM_SCHEMA, min_items=1, max_items=4),
        InputField("objective_output_path", "数值目标输出路径", "string"),
        InputField("objective_sense", "目标方向", "select", enum=["minimize", "maximize"]),
        InputField("constraints", "同次目标输出约束", "array", required=False, items=CONSTRAINT_ITEM_SCHEMA, min_items=0, max_items=8),
        InputField("initial_samples", "初始样本数", "number", unit="1", min_value=3, max_value=20),
        InputField("evaluation_budget", "总评估预算", "number", unit="1", min_value=5, max_value=40),
        InputField("seed", "固定随机/序列种子", "number", unit="1", min_value=0, max_value=1000000000),
        InputField("expected_improvement_xi", "EI探索量", "number", unit="1", min_value=0, max_value=1),
        InputField("allow_boundary_warning", "是否接受目标边界警告", "boolean"),
    ]
    output_fields = [
        OutputField("target_model_code", "目标模型码", "string"),
        OutputField("objective_output_path", "目标输出路径", "string"),
        OutputField("objective_sense", "目标方向", "string"),
        OutputField("evaluation_count", "评估数", "number", "1"),
        OutputField("feasible_evaluation_count", "可行评估数", "number", "1"),
        OutputField("best_parameters", "最优参数", "object"),
        OutputField("best_objective_value", "最优目标值", "number", "target output unit"),
        OutputField("best_target_output", "最优目标工具输出", "object"),
        OutputField("history", "序贯评估历史", "array"),
        OutputField("gp_state", "固定核与训练摘要", "object"),
        OutputField("last_expected_improvement", "最后一次EI", "number", "standardized objective"),
        OutputField("stop_reason", "停止原因", "string"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "fully_eligible_non_recursive_target"},
        {"rule": "one_to_four_unique_continuous_variables"},
        {"rule": "initial_samples_between_three_and_budget"},
        {"rule": "registered_output_objective_and_constraints_are_finite"},
        {"rule": "rbf_gp_expected_improvement_nonnegative_and_reproducible"},
    ]
    qualification_cases = [
        {"id": "G011-N1", "kind": "normal", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}], "objective_output_path": "heat_rate_w", "objective_sense": "maximize", "constraints": [], "initial_samples": 5, "evaluation_budget": 9, "seed": 11, "expected_improvement_xi": 0.01, "allow_boundary_warning": False}},
        {"id": "G011-N2", "kind": "normal", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}, {"path": "area", "lower_bound": 0.5, "upper_bound": 2}], "objective_output_path": "heat_rate_w", "objective_sense": "maximize", "constraints": [], "initial_samples": 6, "evaluation_budget": 10, "seed": 7, "expected_improvement_xi": 0.01, "allow_boundary_warning": False}},
        {"id": "G011-N3", "kind": "normal", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}], "objective_output_path": "thermal_resistance_k_per_w", "objective_sense": "minimize", "constraints": [{"name": "heat_cap", "output_path": "heat_rate_w", "operator": "less_than_or_equal", "threshold": 300000}], "initial_samples": 5, "evaluation_budget": 12, "seed": 3, "expected_improvement_xi": 0.02, "allow_boundary_warning": False}},
        {"id": "G011-B1", "kind": "boundary", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}], "objective_output_path": "heat_rate_w", "objective_sense": "maximize", "constraints": [], "initial_samples": 5, "evaluation_budget": 5, "seed": 0, "expected_improvement_xi": 0, "allow_boundary_warning": False}},
        {"id": "G011-F1", "kind": "failure", "input": {"target_model_code": "G011", "base_params": {"value": 1}, "variables": [{"path": "value", "lower_bound": 0, "upper_bound": 1}], "objective_output_path": "value", "objective_sense": "minimize", "constraints": [], "initial_samples": 3, "evaluation_budget": 5, "seed": 0, "expected_improvement_xi": 0, "allow_boundary_warning": False}},
        {"id": "G011-F2", "kind": "failure", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}], "objective_output_path": "missing", "objective_sense": "minimize", "constraints": [], "initial_samples": 3, "evaluation_budget": 5, "seed": 0, "expected_improvement_xi": 0, "allow_boundary_warning": False}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        target_registry, target, error = eligible_target(params.get("target_model_code"))
        if error:
            return fail(error, "MODEL_NOT_APPLICABLE")
        base_params = params.get("base_params")
        if not isinstance(base_params, dict):
            return fail("base_params必须是对象")
        variables, error = parse_variables(params.get("variables"), maximum=4)
        if error:
            return fail(error)
        for variable in variables:
            probe = deepcopy(base_params)
            error = write_numeric_path(probe, variable["path"], variable["lower_bound"], "variables.path")
            if error:
                return fail(error)
        objective_path = params.get("objective_output_path")
        _, error = split_path(objective_path, "objective_output_path")
        if error:
            return fail(error)
        objective_sense = params.get("objective_sense")
        if objective_sense not in {"minimize", "maximize"}:
            return fail("objective_sense必须是minimize或maximize")
        constraints, error = parse_constraints(params.get("constraints"))
        if error:
            return fail(error)
        initial_samples, error = integer(params.get("initial_samples"), "initial_samples", 3, 20)
        if error:
            return fail(error)
        budget, error = integer(params.get("evaluation_budget"), "evaluation_budget", 5, 40)
        if error:
            return fail(error)
        if initial_samples > budget:
            return fail("initial_samples不能大于evaluation_budget")
        seed, error = integer(params.get("seed"), "seed", 0, 1_000_000_000)
        if error:
            return fail(error)
        xi, error = finite(params.get("expected_improvement_xi"), "expected_improvement_xi", minimum=0, maximum=1)
        if error:
            return fail(error)
        allow_boundary = params.get("allow_boundary_warning")
        if not isinstance(allow_boundary, bool):
            return fail("allow_boundary_warning必须是布尔值")
        dimension = len(variables)
        unit_initial = [[0.0] * dimension, [1.0] * dimension, [0.5] * dimension]
        unit_initial.extend(halton_points(max(0, initial_samples - len(unit_initial)), dimension, skip=seed))
        initial_points: list[list[float]] = []
        seen = set()
        for unit in unit_initial:
            point = scale_point(unit, variables)
            if point_key(point) not in seen:
                initial_points.append(point)
                seen.add(point_key(point))
        next_halton = initial_samples + seed
        while len(initial_points) < initial_samples:
            point = scale_point(halton_points(1, dimension, skip=next_halton)[0], variables)
            next_halton += 1
            if point_key(point) not in seen:
                initial_points.append(point)
                seen.add(point_key(point))

        history: list[dict[str, Any]] = []
        any_boundary = False

        def evaluate(point: list[float], acquisition: float | None) -> str | None:
            nonlocal any_boundary
            run_params = deepcopy(base_params)
            parameter_values = {}
            for variable, value in zip(variables, point):
                path = variable["path"]
                path_error = write_numeric_path(run_params, path, value, "variables.path")
                if path_error:
                    return path_error
                parameter_values[path] = value
            output, target_error, target_code, boundary_passed = invoke_target(
                target_registry, target, run_params, allow_boundary_warning=allow_boundary
            )
            if output is None:
                return f"目标调用失败[{target_code}]: {target_error}"
            any_boundary = any_boundary or not boundary_passed
            raw_objective, path_error = read_path(output, objective_path, "objective_output_path")
            if path_error:
                return path_error
            objective, numeric_error = finite(raw_objective, "objective_output")
            if numeric_error:
                return numeric_error
            checks, constraint_error = constraint_values(output, constraints)
            if constraint_error:
                return constraint_error
            feasible = all(item["satisfied"] for item in checks)
            history.append({
                "evaluation_index": len(history) + 1,
                "parameters": parameter_values,
                "objective_value": objective,
                "feasible": feasible,
                "constraints": checks,
                "expected_improvement_at_selection": acquisition,
                "target_output": output,
            })
            return None

        for point in initial_points:
            error = evaluate(point, None)
            if error:
                return fail(error, "MODEL_NOT_APPLICABLE")

        length_scale = 0.35
        nugget = 1e-10
        last_ei = 0.0
        stop_reason = "evaluation_budget_reached"
        candidate_units = [[0.0] * dimension, [1.0] * dimension]
        candidate_units.extend(halton_points(512, dimension, skip=seed + 1000))
        candidate_points = [scale_point(unit, variables) for unit in candidate_units]
        while len(history) < budget:
            x_train = np.asarray([
                [(row["parameters"][variable["path"]] - variable["lower_bound"]) / (variable["upper_bound"] - variable["lower_bound"]) for variable in variables]
                for row in history
            ], dtype=float)
            objective_values = np.asarray([row["objective_value"] for row in history], dtype=float)
            transformed = objective_values if objective_sense == "minimize" else -objective_values
            mean = float(np.mean(transformed))
            std = float(np.std(transformed))
            scale = std if std > 1e-14 else 1.0
            y_train = (transformed - mean) / scale
            distances = x_train[:, None, :] - x_train[None, :, :]
            kernel = np.exp(-0.5 * np.sum((distances / length_scale) ** 2, axis=2))
            kernel.flat[:: len(history) + 1] += nugget
            try:
                chol = np.linalg.cholesky(kernel)
                alpha = np.linalg.solve(chol.T, np.linalg.solve(chol, y_train))
            except np.linalg.LinAlgError:
                return fail("高斯过程核矩阵Cholesky分解失败", "NUMERICAL_ERROR")
            feasible_rows = [row for row in history if row["feasible"]]
            best_transformed = min(
                (row["objective_value"] if objective_sense == "minimize" else -row["objective_value"])
                for row in (feasible_rows or history)
            )
            best_standardized = (best_transformed - mean) / scale
            best_candidate = None
            best_ei = -1.0
            for point in candidate_points:
                if point_key(point) in seen:
                    continue
                unit = np.asarray([
                    (value - variable["lower_bound"]) / (variable["upper_bound"] - variable["lower_bound"])
                    for value, variable in zip(point, variables)
                ])
                k_star = np.exp(-0.5 * np.sum(((x_train - unit) / length_scale) ** 2, axis=1))
                mu = float(k_star @ alpha)
                v = np.linalg.solve(chol, k_star)
                variance = max(0.0, 1.0 - float(v @ v))
                sigma = math.sqrt(variance)
                improvement = best_standardized - mu - xi
                if sigma <= 1e-14:
                    expected_improvement = max(0.0, improvement)
                else:
                    z = improvement / sigma
                    expected_improvement = improvement * normal_cdf(z) + sigma * normal_pdf(z)
                    expected_improvement = max(0.0, expected_improvement)
                if expected_improvement > best_ei + 1e-15:
                    best_ei = expected_improvement
                    best_candidate = point
            if best_candidate is None:
                stop_reason = "candidate_pool_exhausted"
                break
            seen.add(point_key(best_candidate))
            last_ei = best_ei
            error = evaluate(best_candidate, best_ei)
            if error:
                return fail(error, "MODEL_NOT_APPLICABLE")
        feasible_rows = [row for row in history if row["feasible"]]
        if not feasible_rows:
            return fail("评估预算内没有满足显式约束的候选", "OUT_OF_DOMAIN")
        best = min(feasible_rows, key=lambda row: row["objective_value"] if objective_sense == "minimize" else -row["objective_value"])
        transformed_values = [row["objective_value"] if objective_sense == "minimize" else -row["objective_value"] for row in history]
        warnings = []
        if initial_samples == budget:
            warnings.append(BoundaryWarning("evaluation_budget", "预算全部用于初始设计，未执行Expected Improvement迭代"))
        if stop_reason != "evaluation_budget_reached":
            warnings.append(BoundaryWarning("candidate_pool", "候选池在预算前耗尽"))
        if any_boundary:
            warnings.append(BoundaryWarning("target", "至少一个评估接受了目标工具边界警告"))
        return ModelResult(True, result={
            "target_model_code": target.model_id,
            "objective_output_path": objective_path,
            "objective_sense": objective_sense,
            "evaluation_count": len(history),
            "feasible_evaluation_count": len(feasible_rows),
            "best_parameters": best["parameters"],
            "best_objective_value": best["objective_value"],
            "best_target_output": best["target_output"],
            "history": history,
            "gp_state": {
                "kernel": "squared_exponential_rbf",
                "length_scale_normalized": length_scale,
                "nugget": nugget,
                "training_points": len(history),
                "transformed_objective_mean": float(np.mean(transformed_values)),
                "transformed_objective_standard_deviation": float(np.std(transformed_values)),
            },
            "last_expected_improvement": last_ei,
            "stop_reason": stop_reason,
            "model_version": "deterministic-gp-ei-w18-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


OBJECTIVE_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "output_path": {"type": "string"},
        "sense": {"type": "string", "enum": ["minimize", "maximize"]},
    },
    "required": ["name", "output_path", "sense"],
    "additionalProperties": False,
}


def parse_objectives(raw: Any) -> tuple[list[dict[str, str]] | None, str | None]:
    if not isinstance(raw, list) or not 2 <= len(raw) <= 4:
        return None, "objectives必须含2至4项"
    parsed: list[dict[str, str]] = []
    names = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) != {"name", "output_path", "sense"}:
            return None, f"objectives[{index}]字段必须恰为name/output_path/sense"
        if not isinstance(item["name"], str) or not item["name"].strip() or item["name"] in names:
            return None, f"objectives[{index}].name为空或重复"
        _, error = split_path(item["output_path"], f"objectives[{index}].output_path")
        if error:
            return None, error
        if item["sense"] not in {"minimize", "maximize"}:
            return None, f"objectives[{index}].sense不受支持"
        names.add(item["name"])
        parsed.append(dict(item))
    return parsed, None


def constrained_dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left["feasible"] and not right["feasible"]:
        return True
    if not left["feasible"] and right["feasible"]:
        return False
    if not left["feasible"] and not right["feasible"]:
        return left["constraint_violation"] < right["constraint_violation"] - 1e-15
    a, b = left["minimized_objectives"], right["minimized_objectives"]
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def nondominated_fronts(population: list[dict[str, Any]]) -> list[list[int]]:
    dominates: list[list[int]] = [[] for _ in population]
    dominated_count = [0 for _ in population]
    fronts: list[list[int]] = [[]]
    for i, left in enumerate(population):
        for j, right in enumerate(population):
            if i == j:
                continue
            if constrained_dominates(left, right):
                dominates[i].append(j)
            elif constrained_dominates(right, left):
                dominated_count[i] += 1
        if dominated_count[i] == 0:
            left["rank"] = 0
            fronts[0].append(i)
    rank = 0
    while fronts[rank]:
        next_front = []
        for i in fronts[rank]:
            for j in dominates[i]:
                dominated_count[j] -= 1
                if dominated_count[j] == 0:
                    population[j]["rank"] = rank + 1
                    next_front.append(j)
        rank += 1
        fronts.append(next_front)
    return fronts[:-1]


def assign_crowding(population: list[dict[str, Any]], front: list[int]) -> None:
    for index in front:
        population[index]["crowding_distance"] = 0.0
    if len(front) <= 2:
        for index in front:
            population[index]["crowding_distance"] = float("inf")
        return
    objective_count = len(population[front[0]]["minimized_objectives"])
    for objective_index in range(objective_count):
        ordered = sorted(front, key=lambda index: population[index]["minimized_objectives"][objective_index])
        population[ordered[0]]["crowding_distance"] = float("inf")
        population[ordered[-1]]["crowding_distance"] = float("inf")
        low = population[ordered[0]]["minimized_objectives"][objective_index]
        high = population[ordered[-1]]["minimized_objectives"][objective_index]
        if high <= low:
            continue
        for position in range(1, len(ordered) - 1):
            index = ordered[position]
            if math.isinf(population[index]["crowding_distance"]):
                continue
            previous = population[ordered[position - 1]]["minimized_objectives"][objective_index]
            following = population[ordered[position + 1]]["minimized_objectives"][objective_index]
            population[index]["crowding_distance"] += (following - previous) / (high - low)


def tournament(left: dict[str, Any], right: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    if left["rank"] != right["rank"]:
        return left if left["rank"] < right["rank"] else right
    if left["crowding_distance"] != right["crowding_distance"]:
        return left if left["crowding_distance"] > right["crowding_distance"] else right
    return left if rng.random() < 0.5 else right


def sbx_pair(
    first: list[float],
    second: list[float],
    variables: list[dict[str, Any]],
    rng: random.Random,
    eta: float = 20.0,
) -> tuple[list[float], list[float]]:
    child1, child2 = list(first), list(second)
    if rng.random() > 0.9:
        return child1, child2
    for index, variable in enumerate(variables):
        if rng.random() > 0.5 or math.isclose(first[index], second[index], rel_tol=0, abs_tol=1e-15):
            continue
        x1, x2 = sorted((first[index], second[index]))
        lower, upper = variable["lower_bound"], variable["upper_bound"]
        rand = rng.random()
        beta = 1.0 + 2.0 * (x1 - lower) / (x2 - x1)
        alpha = 2.0 - beta ** -(eta + 1.0)
        if rand <= 1.0 / alpha:
            beta_q = (rand * alpha) ** (1.0 / (eta + 1.0))
        else:
            beta_q = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta + 1.0))
        c1 = 0.5 * ((x1 + x2) - beta_q * (x2 - x1))
        beta = 1.0 + 2.0 * (upper - x2) / (x2 - x1)
        alpha = 2.0 - beta ** -(eta + 1.0)
        if rand <= 1.0 / alpha:
            beta_q = (rand * alpha) ** (1.0 / (eta + 1.0))
        else:
            beta_q = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta + 1.0))
        c2 = 0.5 * ((x1 + x2) + beta_q * (x2 - x1))
        child1[index] = min(upper, max(lower, c1))
        child2[index] = min(upper, max(lower, c2))
        if rng.random() < 0.5:
            child1[index], child2[index] = child2[index], child1[index]
    return child1, child2


def polynomial_mutate(point: list[float], variables: list[dict[str, Any]], rng: random.Random, eta: float = 20.0) -> list[float]:
    mutated = list(point)
    probability = 1.0 / len(variables)
    for index, variable in enumerate(variables):
        if rng.random() > probability:
            continue
        lower, upper = variable["lower_bound"], variable["upper_bound"]
        value = mutated[index]
        delta1 = (value - lower) / (upper - lower)
        delta2 = (upper - value) / (upper - lower)
        rand = rng.random()
        mutation_power = 1.0 / (eta + 1.0)
        if rand < 0.5:
            xy = 1.0 - delta1
            val = 2.0 * rand + (1.0 - 2.0 * rand) * xy ** (eta + 1.0)
            delta_q = val ** mutation_power - 1.0
        else:
            xy = 1.0 - delta2
            val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * xy ** (eta + 1.0)
            delta_q = 1.0 - val ** mutation_power
        mutated[index] = min(upper, max(lower, value + delta_q * (upper - lower)))
    return mutated


class G012_MultiobjectiveNSGA2(W18FormulaTool):
    model_id, name, version = "G012", "注册工具NSGA-II多目标优化", "1.0.0"
    tool_name = "metallurgy_run_registered_nsga2"
    description = "对一个已完全准入注册工具执行预算受控、固定种子的约束NSGA-II，返回真实评估得到的非支配Pareto集和透明折中解。"
    applicable_boundary = "1至5个连续变量、2至4个同次工具输出目标；种群8至48、代数1至24、总评估不超过1200；不连接现场或生产控制。"
    formula_reference = "Deb et al. (2002) NSGA-II: constrained dominance, fast nondominated sorting, crowding distance, SBX crossover and polynomial mutation"
    source_version = "deterministic-constrained-nsga2-w18-v1"
    data_source = ["Deb et al. IEEE Transactions on Evolutionary Computation 6 (2002)", "Local fully eligible ModelRegistry contract"]
    source_records = [{"source_id": "DEB-NSGA2-2002", "name": "A fast and elitist multiobjective genetic algorithm: NSGA-II", "version": "IEEE TEC 6(2), 2002", "url": "https://doi.org/10.1109/4235.996017"}]
    failure_modes = ["目标不存在、未准入或递归", "变量/目标/权重契约非法", "目标调用失败或输出非有限", "全部候选不可行", "总评估超限", "Pareto或折中归一化失败"]
    independent_validation = ["返回Pareto解逐对互不支配", "固定种子和输入完全可复现", "冲突目标保留两端解", "每个可行解满足全部约束", "折中权重归一且折中解属于Pareto集"]
    dependencies = ["G009", "G013"]
    relations = [
        rel("overlaps", "G011", "共享受控注册调用层；本工具多目标进化，G011单目标GP/EI"),
        rel("overlaps", "F011", "F011解析求单调约束下最大拉速，本工具处理一般多目标黑箱"),
        rel("complements", "G013", "Pareto解的工艺规则可由G013独立复核"),
    ]
    input_fields = [
        InputField("target_model_code", "目标模型码", "string"),
        InputField("base_params", "目标基础参数", "object"),
        InputField("variables", "连续变量", "array", items=VARIABLE_ITEM_SCHEMA, min_items=1, max_items=5),
        InputField("objectives", "多目标定义", "array", items=OBJECTIVE_ITEM_SCHEMA, min_items=2, max_items=4),
        InputField("constraints", "同次目标输出约束", "array", required=False, items=CONSTRAINT_ITEM_SCHEMA, min_items=0, max_items=8),
        InputField("population_size", "种群规模", "number", unit="1", min_value=8, max_value=48),
        InputField("generations", "进化代数", "number", unit="1", min_value=1, max_value=24),
        InputField("seed", "固定随机种子", "number", unit="1", min_value=0, max_value=1000000000),
        InputField("compromise_weights", "目标折中权重", "array", items={"type": "number"}, min_items=2, max_items=4),
        InputField("allow_boundary_warning", "是否接受目标边界警告", "boolean"),
    ]
    output_fields = [
        OutputField("target_model_code", "目标模型码", "string"),
        OutputField("evaluation_count", "真实评估数", "number", "1"),
        OutputField("feasible_evaluation_count", "可行评估数", "number", "1"),
        OutputField("pareto_count", "Pareto解数", "number", "1"),
        OutputField("pareto_solutions", "非支配解集", "array"),
        OutputField("objective_ranges", "Pareto目标范围", "object"),
        OutputField("compromise_solution", "归一化加权折中解", "object"),
        OutputField("algorithm_parameters", "NSGA-II参数", "object"),
        OutputField("stop_reason", "停止原因", "string"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "fully_eligible_non_recursive_target"},
        {"rule": "one_to_five_variables_and_two_to_four_objectives"},
        {"rule": "population_times_generations_plus_one_at_most_1200"},
        {"rule": "constrained_nondominated_sort_and_crowding_selection"},
        {"rule": "returned_pareto_members_are_pairwise_nondominated"},
    ]
    qualification_cases = [
        {"id": "G012-N1", "kind": "normal", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}], "objectives": [{"name": "heat", "output_path": "heat_rate_w", "sense": "maximize"}, {"name": "resistance", "output_path": "thermal_resistance_k_per_w", "sense": "maximize"}], "constraints": [], "population_size": 10, "generations": 3, "seed": 5, "compromise_weights": [0.5, 0.5], "allow_boundary_warning": False}},
        {"id": "G012-N2", "kind": "normal", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}, {"path": "area", "lower_bound": 0.5, "upper_bound": 2}], "objectives": [{"name": "heat", "output_path": "heat_rate_w", "sense": "maximize"}, {"name": "resistance", "output_path": "thermal_resistance_k_per_w", "sense": "maximize"}], "constraints": [], "population_size": 12, "generations": 2, "seed": 9, "compromise_weights": [0.7, 0.3], "allow_boundary_warning": False}},
        {"id": "G012-N3", "kind": "normal", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}], "objectives": [{"name": "heat", "output_path": "heat_rate_w", "sense": "maximize"}, {"name": "resistance", "output_path": "thermal_resistance_k_per_w", "sense": "maximize"}], "constraints": [{"name": "heat_cap", "output_path": "heat_rate_w", "operator": "less_than_or_equal", "threshold": 400000}], "population_size": 10, "generations": 2, "seed": 4, "compromise_weights": [0.5, 0.5], "allow_boundary_warning": False}},
        {"id": "G012-B1", "kind": "boundary", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}], "objectives": [{"name": "heat", "output_path": "heat_rate_w", "sense": "maximize"}, {"name": "resistance", "output_path": "thermal_resistance_k_per_w", "sense": "maximize"}], "constraints": [], "population_size": 8, "generations": 1, "seed": 1, "compromise_weights": [1, 0], "allow_boundary_warning": False}},
        {"id": "G012-F1", "kind": "failure", "input": {"target_model_code": "G012", "base_params": {"value": 1}, "variables": [{"path": "value", "lower_bound": 0, "upper_bound": 1}], "objectives": [{"name": "a", "output_path": "value", "sense": "minimize"}, {"name": "b", "output_path": "value", "sense": "maximize"}], "constraints": [], "population_size": 8, "generations": 1, "seed": 0, "compromise_weights": [0.5, 0.5], "allow_boundary_warning": False}},
        {"id": "G012-F2", "kind": "failure", "input": {"target_model_code": "T001", "base_params": {"thermal_conductivity": 20, "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500}, "variables": [{"path": "thermal_conductivity", "lower_bound": 10, "upper_bound": 100}], "objectives": [{"name": "heat", "output_path": "heat_rate_w", "sense": "maximize"}, {"name": "resistance", "output_path": "thermal_resistance_k_per_w", "sense": "maximize"}], "constraints": [], "population_size": 8, "generations": 1, "seed": 0, "compromise_weights": [1], "allow_boundary_warning": False}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        target_registry, target, error = eligible_target(params.get("target_model_code"))
        if error:
            return fail(error, "MODEL_NOT_APPLICABLE")
        base_params = params.get("base_params")
        if not isinstance(base_params, dict):
            return fail("base_params必须是对象")
        variables, error = parse_variables(params.get("variables"), maximum=5)
        if error:
            return fail(error)
        for variable in variables:
            probe = deepcopy(base_params)
            error = write_numeric_path(probe, variable["path"], variable["lower_bound"], "variables.path")
            if error:
                return fail(error)
        objectives, error = parse_objectives(params.get("objectives"))
        if error:
            return fail(error)
        constraints, error = parse_constraints(params.get("constraints"))
        if error:
            return fail(error)
        population_size, error = integer(params.get("population_size"), "population_size", 8, 48)
        if error:
            return fail(error)
        generations, error = integer(params.get("generations"), "generations", 1, 24)
        if error:
            return fail(error)
        if population_size * (generations + 1) > 1200:
            return fail("总评估预算超过1200", "OUT_OF_DOMAIN")
        seed, error = integer(params.get("seed"), "seed", 0, 1_000_000_000)
        if error:
            return fail(error)
        weights_raw = params.get("compromise_weights")
        if not isinstance(weights_raw, list) or len(weights_raw) != len(objectives):
            return fail("compromise_weights数量必须等于objectives数量")
        weights = []
        for index, raw in enumerate(weights_raw):
            value, error = finite(raw, f"compromise_weights[{index}]", minimum=0)
            if error:
                return fail(error)
            weights.append(value)
        if sum(weights) <= 0:
            return fail("compromise_weights至少一项必须大于0")
        weights = [value / sum(weights) for value in weights]
        allow_boundary = params.get("allow_boundary_warning")
        if not isinstance(allow_boundary, bool):
            return fail("allow_boundary_warning必须是布尔值")
        rng = random.Random(seed)
        dimension = len(variables)
        unit_points = [[0.0] * dimension, [1.0] * dimension, [0.5] * dimension]
        unit_points.extend(halton_points(population_size, dimension, skip=seed))
        initial_points = []
        seen = set()
        for unit in unit_points:
            point = scale_point(unit, variables)
            if point_key(point) not in seen:
                initial_points.append(point)
                seen.add(point_key(point))
            if len(initial_points) == population_size:
                break
        while len(initial_points) < population_size:
            point = [rng.uniform(variable["lower_bound"], variable["upper_bound"]) for variable in variables]
            if point_key(point) not in seen:
                initial_points.append(point)
                seen.add(point_key(point))

        evaluation_count = 0
        feasible_evaluation_count = 0
        any_boundary = False

        def evaluate(point: list[float]) -> tuple[dict[str, Any] | None, str | None]:
            nonlocal evaluation_count, feasible_evaluation_count, any_boundary
            run_params = deepcopy(base_params)
            parameter_values = {}
            for variable, value in zip(variables, point):
                path = variable["path"]
                path_error = write_numeric_path(run_params, path, value, "variables.path")
                if path_error:
                    return None, path_error
                parameter_values[path] = value
            output, target_error, target_code, boundary_passed = invoke_target(
                target_registry, target, run_params, allow_boundary_warning=allow_boundary
            )
            if output is None:
                return None, f"目标调用失败[{target_code}]: {target_error}"
            any_boundary = any_boundary or not boundary_passed
            values = {}
            minimized = []
            for objective in objectives:
                raw, path_error = read_path(output, objective["output_path"], f"objective:{objective['name']}")
                if path_error:
                    return None, path_error
                value, numeric_error = finite(raw, f"objective:{objective['name']}")
                if numeric_error:
                    return None, numeric_error
                values[objective["name"]] = value
                minimized.append(value if objective["sense"] == "minimize" else -value)
            checks, constraint_error = constraint_values(output, constraints)
            if constraint_error:
                return None, constraint_error
            feasible = all(item["satisfied"] for item in checks)
            violation = sum(item["normalized_violation"] for item in checks)
            evaluation_count += 1
            feasible_evaluation_count += int(feasible)
            return {
                "point": point,
                "parameters": parameter_values,
                "objectives": values,
                "minimized_objectives": minimized,
                "constraints": checks,
                "feasible": feasible,
                "constraint_violation": violation,
                "target_output": output,
                "rank": 0,
                "crowding_distance": 0.0,
            }, None

        population = []
        for point in initial_points:
            individual, error = evaluate(point)
            if error:
                return fail(error, "MODEL_NOT_APPLICABLE")
            population.append(individual)
        for _generation in range(generations):
            fronts = nondominated_fronts(population)
            for front in fronts:
                assign_crowding(population, front)
            children_points = []
            while len(children_points) < population_size:
                left = tournament(population[rng.randrange(population_size)], population[rng.randrange(population_size)], rng)
                right = tournament(population[rng.randrange(population_size)], population[rng.randrange(population_size)], rng)
                first, second = sbx_pair(left["point"], right["point"], variables, rng)
                children_points.extend([polynomial_mutate(first, variables, rng), polynomial_mutate(second, variables, rng)])
            children = []
            for point in children_points[:population_size]:
                individual, error = evaluate(point)
                if error:
                    return fail(error, "MODEL_NOT_APPLICABLE")
                children.append(individual)
            combined = population + children
            fronts = nondominated_fronts(combined)
            next_population = []
            for front in fronts:
                assign_crowding(combined, front)
                if len(next_population) + len(front) <= population_size:
                    next_population.extend(combined[index] for index in front)
                else:
                    ranked = sorted(front, key=lambda index: combined[index]["crowding_distance"], reverse=True)
                    remaining = population_size - len(next_population)
                    next_population.extend(combined[index] for index in ranked[:remaining])
                    break
            population = next_population
        final_fronts = nondominated_fronts(population)
        for front in final_fronts:
            assign_crowding(population, front)
        pareto = [population[index] for index in final_fronts[0] if population[index]["feasible"]]
        if not pareto:
            return fail("进化预算内没有可行Pareto解", "OUT_OF_DOMAIN")
        # Deduplicate numerically identical decision vectors while preserving deterministic order.
        unique = {}
        for individual in pareto:
            unique.setdefault(point_key(individual["point"]), individual)
        pareto = list(unique.values())
        ranges = {}
        for objective in objectives:
            values = [individual["objectives"][objective["name"]] for individual in pareto]
            ranges[objective["name"]] = {"minimum": min(values), "maximum": max(values), "sense": objective["sense"]}
        best_compromise = None
        best_score = float("inf")
        pareto_solutions = []
        for individual in pareto:
            normalized_terms = []
            for objective, weight in zip(objectives, weights):
                bounds = ranges[objective["name"]]
                span = bounds["maximum"] - bounds["minimum"]
                value = individual["objectives"][objective["name"]]
                if span <= 1e-15 * max(1.0, abs(bounds["minimum"]), abs(bounds["maximum"])):
                    loss = 0.0
                elif objective["sense"] == "minimize":
                    loss = (value - bounds["minimum"]) / span
                else:
                    loss = (bounds["maximum"] - value) / span
                normalized_terms.append(weight * loss)
            score = sum(normalized_terms)
            record = {
                "parameters": individual["parameters"],
                "objectives": individual["objectives"],
                "constraints": individual["constraints"],
                "crowding_distance": None if math.isinf(individual["crowding_distance"]) else individual["crowding_distance"],
                "compromise_score": score,
                "target_output": individual["target_output"],
            }
            pareto_solutions.append(record)
            if score < best_score - 1e-15:
                best_score = score
                best_compromise = record
        pareto_solutions.sort(key=lambda row: tuple(row["parameters"][variable["path"]] for variable in variables))
        # Re-select after stable ordering when scores tie.
        best_compromise = min(pareto_solutions, key=lambda row: (row["compromise_score"], tuple(row["parameters"][variable["path"]] for variable in variables)))
        warnings = []
        if generations == 1:
            warnings.append(BoundaryWarning("generations", "仅1代，结果是最小进化筛选而非收敛证明"))
        if any_boundary:
            warnings.append(BoundaryWarning("target", "至少一个评估接受了目标工具边界警告"))
        return ModelResult(True, result={
            "target_model_code": target.model_id,
            "evaluation_count": evaluation_count,
            "feasible_evaluation_count": feasible_evaluation_count,
            "pareto_count": len(pareto_solutions),
            "pareto_solutions": pareto_solutions,
            "objective_ranges": ranges,
            "compromise_solution": best_compromise,
            "algorithm_parameters": {"algorithm": "NSGA-II", "population_size": population_size, "generations": generations, "seed": seed, "sbx_eta": 20.0, "mutation_eta": 20.0, "normalized_compromise_weights": weights},
            "stop_reason": "generation_budget_reached",
            "model_version": "deterministic-constrained-nsga2-w18-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
