"""Generate and verify representative native and execution-result artifacts.

The calculations are performed through the running HTTP tool-call API.  The
local registry is used only to obtain the same approved normal inputs that are
used by qualification tests; it is not used to execute the tools.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOLS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_ROOT.parent
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from models_core import ModelRegistry


API_ROOT = os.environ.get("METALLURGY_MODELS_API_ROOT", "").rstrip("/")
AUDIT_ROOT = PROJECT_ROOT / "outputs" / "tool_artifact_audit_20260903"
TARGETS = ("G005", "G004", "F004", "G006", "G011", "T001")


def _normal_input(registry: ModelRegistry, model_code: str) -> dict[str, Any]:
    for case in registry.get(model_code).qualification_cases:
        if case.get("kind") == "normal":
            return json.loads(json.dumps(case["input"], ensure_ascii=False))
    raise RuntimeError(f"{model_code}没有正常资格用例")


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_summaries(directory: Path, relative_paths: list[str]) -> list[dict[str, Any]]:
    summaries = []
    for relative_path in relative_paths:
        path = directory / relative_path
        with path.open("r", encoding="utf-8", newline="") as stream:
            rows = list(csv.reader(stream))
        summaries.append({
            "path": relative_path,
            "header": rows[0] if rows else [],
            "data_row_count": max(len(rows) - 1, 0),
        })
    return summaries


def _verify_generic(record: dict[str, Any]) -> dict[str, Any]:
    artifact = record["artifact"]
    directory = Path(artifact["artifact_directory"])
    expected_hashes = artifact["file_sha256"]
    actual_hashes = {name: _sha256(directory / name) for name in expected_hashes}
    result_readback = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    zip_path = Path(artifact["zip_path"]) if artifact.get("zip_path") else None
    zip_names: list[str] = []
    if zip_path:
        with zipfile.ZipFile(zip_path) as archive:
            zip_names = sorted(archive.namelist())
    return {
        "directory_exists": directory.is_dir(),
        "zip_exists": bool(zip_path and zip_path.is_file()),
        "all_file_hashes_match": actual_hashes == expected_hashes,
        "result_readback_equal": result_readback == record["output"],
        "csv": _csv_summaries(directory, artifact["csv_files"]),
        "zip_entry_count": len(zip_names),
        "zip_sha256_match": bool(zip_path and _sha256(zip_path) == artifact["zip_sha256"]),
    }


def _verify_g005(record: dict[str, Any]) -> dict[str, Any]:
    output = record["output"]
    directory = Path(output["case_directory"])
    zip_path = Path(output["zip_path"])
    actual_hashes = {name: _sha256(directory / name) for name in output["file_sha256"]}
    manifest = json.loads(Path(output["case_manifest_path"]).read_text(encoding="utf-8"))
    with zipfile.ZipFile(zip_path) as archive:
        zip_names = sorted(archive.namelist())
    return {
        "directory_exists": directory.is_dir(),
        "zip_exists": zip_path.is_file(),
        "all_case_file_hashes_match": actual_hashes == output["file_sha256"],
        "manifest_model_code": manifest["generator_model_code"],
        "manifest_sha256_match": manifest["manifest_sha256"] == output["manifest_sha256"],
        "zip_sha256_match": _sha256(zip_path) == output["zip_sha256"],
        "zip_entry_count": len(zip_names),
        "structural_validation": output["structural_validation"],
    }


def _summary(model_code: str, output: dict[str, Any]) -> dict[str, Any]:
    if model_code == "G005":
        return {"case_name": output["case_name"], "cell_count": output["cell_count"], "solver": output["solver"]}
    if model_code == "G004":
        return {"time_point_count": len(output["time_series"]), "final_concentrations_mol_m3": output["final_concentrations_mol_m3"]}
    if model_code == "F004":
        return {key: output[key] for key in output if key in {"liquidus_temperature_k", "solidus_temperature_k", "freezing_range_k", "eutectic_fraction"}}
    if model_code == "G006":
        return {key: output[key] for key in output if key in {"total_runs", "success_count", "failure_count"}}
    if model_code == "G011":
        return {key: output[key] for key in output if key in {"best_objective", "best_parameters", "evaluation_count"}}
    return {key: output[key] for key in list(output)[:5]}


def main() -> int:
    if not API_ROOT:
        raise RuntimeError("必须通过 METALLURGY_MODELS_API_ROOT 配置模型服务 API 地址")
    registry = ModelRegistry()
    registry.discover()
    run_token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    results = []
    for model_code in TARGETS:
        model = registry.get(model_code)
        arguments = _normal_input(registry, model_code)
        if model_code == "G005":
            arguments["case_name"] = "g005_case_artifact_audit_20260903"
            arguments["artifact_mode"] = "directory_and_zip"
            options = {"validate_boundary": True, "return_provenance": True}
            artifact_kind = "native_openfoam_case_bundle"
        else:
            options = {
                "validate_boundary": True,
                "return_provenance": True,
                "artifact": {
                    "mode": "directory_and_zip",
                    "name": f"{model_code.lower()}_{run_token}",
                },
            }
            artifact_kind = "execution_result_bundle"
        record = _post_json(
            f"{API_ROOT}/tools/{model.tool_name}/call",
            {"arguments": arguments, "options": options},
        )
        if record.get("status") != "success":
            raise RuntimeError(f"{model_code}执行失败: {record}")
        verification = _verify_g005(record) if model_code == "G005" else _verify_generic(record)
        output = record["output"]
        artifact = output if model_code == "G005" else record["artifact"]
        results.append({
            "model_code": model_code,
            "tool_name": model.tool_name,
            "name": model.name,
            "artifact_kind": artifact_kind,
            "execution_id": record["execution_id"],
            "status": record["status"],
            "artifact_directory": artifact.get("case_directory") or artifact.get("artifact_directory"),
            "zip_path": artifact["zip_path"],
            "files": sorted(output["files"]) if model_code == "G005" else artifact["files"],
            "scientific_output_summary": _summary(model_code, output),
            "verification": verification,
        })

    capabilities = json.loads(urllib.request.urlopen(f"{API_ROOT}/artifacts/capabilities", timeout=60).read().decode("utf-8"))
    report = {
        "audit_schema_version": "tool-artifact-audit-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_path": "HTTP /api/v1/tools/{tool_name}/call",
        "capability_counts": {
            "total": capabilities["total"],
            "native_case_bundle": capabilities["native_case_bundle_count"],
            "recommended_result_bundle": capabilities["recommended_result_bundle_count"],
            "optional_result_bundle": capabilities["optional_result_bundle_count"],
        },
        "all_targets_passed": all(
            item["status"] == "success" and all(
                value is True or not key.endswith(("match", "equal", "exists"))
                for key, value in item["verification"].items()
            )
            for item in results
        ),
        "targets": results,
    }
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = AUDIT_ROOT / f"artifact_audit_{run_token}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"report_path": str(report_path), **report}, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
