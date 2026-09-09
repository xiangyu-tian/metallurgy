"""Safe, deterministic file bundles for completed tool executions.

G005 owns its OpenFOAM case files because those files are the scientific
product of that tool.  This module serves the different need shared by other
tools: exporting a completed numerical result for download, review, or reuse
without changing the tool's scientific input/output schema.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_ARTIFACT_ROOT = PROJECT_ROOT / "outputs" / "tool_artifacts"
ARTIFACT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

# These tools normally produce trajectories, grids, batches, reports, or
# optimisation histories whose reuse benefits materially from a file bundle.
RECOMMENDED_ARTIFACT_TOOLS = {
    "A008", "A009", "A010",
    "B011", "B012", "B013", "B022", "B024", "B025",
    "C003", "C004", "C103",
    "D002", "D005", "D007",
    "E020", "E106",
    "F004", "F005", "F007", "F009",
    "G001", "G003", "G004", "G006", "G009", "G010", "G011", "G012", "G013",
}


class ArtifactError(ValueError):
    def __init__(self, message: str, error_code: str = "MODEL_ARTIFACT_UNAVAILABLE"):
        super().__init__(message)
        self.error_code = error_code


def _json_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    except (TypeError, ValueError) as exc:
        raise ArtifactError(f"结果不能序列化为有限JSON: {exc}") from exc
    return text.encode("utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _csv_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def _list_to_csv_bytes(values: list[Any]) -> bytes:
    stream = io.StringIO(newline="")
    if values and all(isinstance(item, dict) for item in values):
        columns: list[str] = []
        for item in values:
            for key in item:
                if key not in columns:
                    columns.append(str(key))
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for item in values:
            writer.writerow({key: _csv_cell(item.get(key)) for key in columns})
    elif values and all(isinstance(item, (list, tuple)) for item in values):
        width = max(len(item) for item in values)
        columns = [f"column_{index + 1}" for index in range(width)]
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        for item in values:
            writer.writerow([_csv_cell(item[index]) if index < len(item) else "" for index in range(width)])
    else:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["index", "value"])
        for index, value in enumerate(values):
            writer.writerow([index, _csv_cell(value)])
    return stream.getvalue().encode("utf-8")


def _deterministic_zip(bundle_name: str, files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative_path, content in sorted(files.items()):
            info = zipfile.ZipInfo(f"{bundle_name}/{relative_path}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue()


class ToolArtifactService:
    """Materialize execution results below one fixed project directory."""

    MODES = ("directory", "directory_and_zip")

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root is not None else TOOL_ARTIFACT_ROOT

    @staticmethod
    def capability(model: Any) -> dict[str, Any]:
        if model.model_id == "G005":
            return {
                "supported": True,
                "delivery": "native_case_bundle",
                "request_location": "arguments.artifact_mode",
                "modes": ["manifest_only", "directory", "directory_and_zip"],
                "formats": ["OpenFOAM case directory", "JSON manifest", "ZIP"],
                "recommended": True,
                "note": "G005文件本身是科学产物，继续使用工具原生artifact_mode。",
            }
        array_fields = [field.name for field in model.output_fields if field.type == "array"]
        return {
            "supported": True,
            "delivery": "execution_result_bundle",
            "request_location": "ToolCallRequest.options.artifact or POST /api/v1/executions/{execution_id}/artifact",
            "modes": list(ToolArtifactService.MODES),
            "formats": ["input.json", "result.json", "provenance.json", "README.md", "manifest.json", "CSV for top-level arrays", "optional ZIP"],
            "csv_output_fields": array_fields,
            "recommended": model.model_id in RECOMMENDED_ARTIFACT_TOOLS,
            "note": "这是执行结果导出，不改变科学输出Schema，也不新增或重复计算工具。",
        }

    @staticmethod
    def validate_request(model_code: str, raw: Any) -> dict[str, Any] | None:
        if raw is None:
            return None
        if model_code == "G005":
            raise ArtifactError("G005必须使用arguments.artifact_mode生成原生OpenFOAM案例", "INVALID_INPUT")
        if not isinstance(raw, dict):
            raise ArtifactError("options.artifact必须是对象", "INVALID_INPUT")
        unknown = set(raw) - {"mode", "name"}
        if unknown:
            raise ArtifactError(f"options.artifact包含未知字段: {sorted(unknown)}", "INVALID_INPUT")
        mode = raw.get("mode", "directory")
        if mode not in ToolArtifactService.MODES:
            raise ArtifactError(f"options.artifact.mode必须是{list(ToolArtifactService.MODES)}之一", "INVALID_INPUT")
        name = raw.get("name")
        if name is not None and (not isinstance(name, str) or not ARTIFACT_NAME_PATTERN.fullmatch(name)):
            raise ArtifactError("options.artifact.name必须为1至64位安全文件名，只能含字母、数字、点、下划线和连字符", "INVALID_INPUT")
        return {"mode": mode, "name": name}

    @staticmethod
    def _directory_matches(directory: Path, expected: dict[str, bytes]) -> bool:
        if directory.is_symlink() or not directory.is_dir():
            return False
        descendants = list(directory.rglob("*"))
        if any(path.is_symlink() for path in descendants):
            return False
        actual_names = {
            path.relative_to(directory).as_posix()
            for path in descendants
            if path.is_file()
        }
        if actual_names != set(expected):
            return False
        return all((directory / name).read_bytes() == content for name, content in expected.items())

    @staticmethod
    def _zip_matches(path: Path, expected: bytes) -> bool:
        return path.is_file() and not path.is_symlink() and path.read_bytes() == expected

    def materialize(
        self,
        *,
        execution_id: str,
        model: Any,
        arguments: dict[str, Any],
        output: dict[str, Any],
        provenance: list[dict[str, Any]],
        request: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(output, dict):
            raise ArtifactError("只有成功且输出为对象的执行才能生成结果资产")
        root = self.root.resolve()
        model_root = (root / model.model_id.lower()).resolve()
        if model_root.parent != root:
            raise ArtifactError("模型资产目录越出固定输出根目录")
        model_root.mkdir(parents=True, exist_ok=True)
        bundle_name = request.get("name") or execution_id
        if not ARTIFACT_NAME_PATTERN.fullmatch(bundle_name):
            raise ArtifactError("生成的资产名称不符合安全文件名规则", "INVALID_INPUT")
        directory = (model_root / bundle_name).resolve()
        zip_path = (model_root / f"{bundle_name}.zip").resolve()
        if directory.parent != model_root or zip_path.parent != model_root:
            raise ArtifactError("资产输出路径越出模型固定目录")

        files: dict[str, bytes] = {
            "input.json": _json_bytes(arguments),
            "result.json": _json_bytes(output),
            "provenance.json": _json_bytes(provenance),
        }
        csv_files = []
        for field_name, value in output.items():
            if isinstance(value, list):
                relative_path = f"tables/{field_name}.csv"
                files[relative_path] = _list_to_csv_bytes(value)
                csv_files.append(relative_path)
        readme = [
            f"# {model.model_id} {model.name} execution bundle",
            "",
            f"- Execution ID: `{execution_id}`",
            f"- Tool UID: `{model.tool_uid}`",
            f"- Model version: `{model.version}`",
            f"- Delivery profile: `{'recommended' if model.model_id in RECOMMENDED_ARTIFACT_TOOLS else 'optional'}`",
            "",
            "The numerical result remains the registered tool's JSON output. This bundle is a lossless export for review and reuse.",
            "",
            "## Files",
            "",
            "- `input.json`: exact execution input",
            "- `result.json`: exact scientific output",
            "- `provenance.json`: source/version records returned by the tool",
            "- `manifest.json`: hashes and execution identity",
        ]
        if csv_files:
            readme.extend(["- `tables/*.csv`: top-level array outputs rendered as UTF-8 CSV", ""])
        files["README.md"] = ("\n".join(readme).rstrip() + "\n").encode("utf-8")
        file_hashes = {name: _sha256(content) for name, content in sorted(files.items())}
        manifest = {
            "artifact_schema_version": "tool-execution-bundle-v1",
            "execution_id": execution_id,
            "model_code": model.model_id,
            "tool_uid": model.tool_uid,
            "model_version": model.version,
            "delivery_profile": "recommended" if model.model_id in RECOMMENDED_ARTIFACT_TOOLS else "optional",
            "input_sha256": _sha256(files["input.json"]),
            "result_sha256": _sha256(files["result.json"]),
            "file_sha256": file_hashes,
            "csv_files": csv_files,
        }
        files["manifest.json"] = _json_bytes(manifest)
        expected_zip = _deterministic_zip(bundle_name, files)

        reused = False
        created_directory = False
        if request["mode"] == "directory_and_zip" and (zip_path.exists() or zip_path.is_symlink()):
            if not self._zip_matches(zip_path, expected_zip):
                raise ArtifactError("同名结果ZIP已存在且内容不同，拒绝覆盖")
        if directory.exists() or directory.is_symlink():
            if not self._directory_matches(directory, files):
                raise ArtifactError("同名结果目录已存在且内容不同，拒绝覆盖")
            reused = True
        else:
            temporary = Path(tempfile.mkdtemp(prefix=f".{bundle_name}.", dir=model_root))
            try:
                for relative_path, content in files.items():
                    target = temporary / relative_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                if not self._directory_matches(temporary, files):
                    raise ArtifactError("临时结果目录写入后回读不一致")
                os.replace(temporary, directory)
                created_directory = True
            except Exception:
                if temporary.exists() and temporary.parent == model_root:
                    shutil.rmtree(temporary)
                raise

        zip_sha256 = None
        if request["mode"] == "directory_and_zip":
            if zip_path.exists() or zip_path.is_symlink():
                reused = True
            else:
                descriptor, temporary_name = tempfile.mkstemp(prefix=f".{bundle_name}.", suffix=".zip", dir=model_root)
                os.close(descriptor)
                temporary_zip = Path(temporary_name)
                try:
                    temporary_zip.write_bytes(expected_zip)
                    if temporary_zip.read_bytes() != expected_zip:
                        raise ArtifactError("临时结果ZIP写入后回读不一致")
                    os.replace(temporary_zip, zip_path)
                except Exception:
                    if temporary_zip.exists() and temporary_zip.parent == model_root:
                        temporary_zip.unlink()
                    if created_directory and directory.parent == model_root and self._directory_matches(directory, files):
                        shutil.rmtree(directory)
                    raise
            zip_sha256 = _sha256(expected_zip)

        readback_verified = self._directory_matches(directory, files)
        if request["mode"] == "directory_and_zip":
            readback_verified = readback_verified and self._zip_matches(zip_path, expected_zip)
        if not readback_verified:
            raise ArtifactError("结果资产最终回读验证失败")
        return {
            "artifact_schema_version": "tool-execution-bundle-v1",
            "mode": request["mode"],
            "materialized": True,
            "artifact_reused": reused,
            "artifact_directory": str(directory),
            "manifest_path": str(directory / "manifest.json"),
            "zip_path": str(zip_path) if request["mode"] == "directory_and_zip" else None,
            "zip_sha256": zip_sha256,
            "files": sorted(files),
            "file_sha256": {name: _sha256(content) for name, content in sorted(files.items())},
            "csv_files": csv_files,
            "readback_verified": True,
            "delivery_profile": "recommended" if model.model_id in RECOMMENDED_ARTIFACT_TOOLS else "optional",
        }

    def resolve_zip_download(self, execution_record: dict[str, Any]) -> dict[str, Any]:
        """Resolve a trusted ZIP from a successful in-memory execution record.

        The client never supplies a filesystem path.  Both generic result
        bundles and G005 native OpenFOAM cases are constrained to their fixed
        project output roots and verified against the hash stored at creation.
        """
        if execution_record.get("status") != "success":
            raise ArtifactError("只有成功执行生成的ZIP可以下载", "INVALID_INPUT")
        model_code = execution_record.get("model_code")
        if model_code == "G005":
            output = execution_record.get("output") or {}
            raw_path = output.get("zip_path")
            expected_hash = output.get("zip_sha256")
            case_name = output.get("case_name")
            trusted_root = (PROJECT_ROOT / "outputs" / "openfoam_cases").resolve()
            expected_name = f"{case_name}.zip" if case_name else None
        else:
            artifact = execution_record.get("artifact") or {}
            raw_path = artifact.get("zip_path")
            expected_hash = artifact.get("zip_sha256")
            trusted_root = (self.root.resolve() / str(model_code).lower()).resolve()
            expected_name = Path(raw_path).name if raw_path else None
        if not raw_path or not expected_hash or not expected_name:
            raise ArtifactError("该执行记录没有ZIP产物；请使用directory_and_zip模式重新生成")
        candidate = Path(raw_path)
        if candidate.is_symlink() or not candidate.is_file():
            raise ArtifactError("ZIP产物不存在或不是普通文件")
        resolved = candidate.resolve()
        if resolved.parent != trusted_root or resolved.name != expected_name:
            raise ArtifactError("ZIP产物路径不在该工具的固定输出目录")
        actual_hash = _sha256(resolved.read_bytes())
        if actual_hash != expected_hash:
            raise ArtifactError("ZIP产物哈希与执行记录不一致，拒绝下载")
        return {
            "path": resolved,
            "filename": resolved.name,
            "sha256": actual_hash,
            "media_type": "application/zip",
        }
