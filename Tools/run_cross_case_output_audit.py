"""Cross-case runtime output audit for all registered tools except G005.

This is an engineering smoke/audit runner, not a research evaluation dataset.
It deliberately uses the second and third normal qualification inputs instead
of repeating each tool's first demonstration case, then records whether the
HTTP tool call returned a concrete, finite, schema-shaped payload.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any


TOOLS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_ROOT.parent
sys.path.insert(0, str(TOOLS_ROOT))

from models_core import ModelRegistry  # noqa: E402


def http_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def flatten(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        leaves: list[tuple[str, Any]] = []
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            leaves.extend(flatten(item, path))
        return leaves
    if isinstance(value, list):
        leaves = []
        for index, item in enumerate(value):
            path = f"{prefix}.{index}" if prefix else str(index)
            leaves.extend(flatten(item, path))
        return leaves
    return [(prefix, value)]


def value_matches_type(value: Any, declared_type: str) -> bool:
    if declared_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    if declared_type == "boolean":
        return isinstance(value, bool)
    if declared_type == "string":
        return isinstance(value, str)
    if declared_type == "object":
        return isinstance(value, dict)
    if declared_type == "array":
        return isinstance(value, list)
    return True


def compact(value: Any, depth: int = 0) -> Any:
    if depth >= 2:
        if isinstance(value, dict):
            return f"<object:{len(value)}>"
        if isinstance(value, list):
            return f"<array:{len(value)}>"
        return value
    if isinstance(value, dict):
        items = list(value.items())[:4]
        preview = {key: compact(item, depth + 1) for key, item in items}
        if len(value) > 4:
            preview["…"] = f"另{len(value) - 4}项"
        return preview
    if isinstance(value, list):
        return {
            "count": len(value),
            "first": compact(value[0], depth + 1) if value else None,
        }
    if isinstance(value, float):
        return float(f"{value:.10g}")
    return value


def selected_output_preview(model: Any, output: dict[str, Any]) -> dict[str, Any]:
    priorities = []
    for field in model.output_fields:
        value = output.get(field.name)
        if isinstance(value, (int, float, bool)) and value is not None:
            priorities.append(field.name)
    for field in model.output_fields:
        if field.name not in priorities and output.get(field.name) not in (None, "", [], {}):
            priorities.append(field.name)
    return {name: compact(output[name]) for name in priorities[:6]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("METALLURGY_MODELS_BASE_URL"))
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "outputs" / "tool_runtime_cross_audit_20260903"),
    )
    args = parser.parse_args()
    if not args.base_url:
        parser.error("必须提供 --base-url 或 METALLURGY_MODELS_BASE_URL")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    registry = ModelRegistry()
    registry.discover()
    manifest = http_json(f"{args.base_url.rstrip('/')}/api/v1/tools")
    definitions = {entry["model_code"]: entry for entry in manifest["tools"]}
    rows = []
    for model_code in sorted(definitions):
        if model_code == "G005":
            continue
        model = registry.get(model_code)
        normal_cases = [case for case in model.qualification_cases if case.get("kind") == "normal"]
        if len(normal_cases) < 3:
            rows.append({
                "model_code": model_code,
                "name": model.name,
                "passed": False,
                "issues": ["少于3个正常案例，无法选择第二和第三异案例"],
            })
            continue
        selected_cases = normal_cases[1:3]
        executions = []
        issues: list[str] = []
        declared = {field.name: field for field in model.output_fields}
        for case in selected_cases:
            try:
                response = http_json(
                    f"{args.base_url.rstrip('/')}/api/v1/tools/{model.tool_name}/call",
                    {"arguments": case["input"]},
                )
            except Exception as exc:  # audit must retain the exact failure and continue
                executions.append({"case_id": case["id"], "success": False, "error": str(exc)})
                issues.append(f"{case['id']} HTTP调用失败: {exc}")
                continue
            success = response.get("status") == "success" and isinstance(response.get("output"), dict)
            execution = {
                "case_id": case["id"],
                "input": case["input"],
                "success": success,
                "error_code": response.get("error_code"),
                "error": response.get("error"),
                "output": response.get("output"),
                "provenance": response.get("provenance", []),
            }
            executions.append(execution)
            if not success:
                issues.append(f"{case['id']} 返回失败: {response.get('error_code')} {response.get('error')}")
                continue
            output = response["output"]
            missing = sorted(set(declared) - set(output))
            extra = sorted(set(output) - set(declared))
            if missing:
                issues.append(f"{case['id']} 缺少声明输出: {missing}")
            if extra:
                issues.append(f"{case['id']} 含未声明输出: {extra}")
            for name, field in declared.items():
                if name not in output:
                    continue
                value = output[name]
                if value is None and field.nullable:
                    continue
                if not value_matches_type(value, field.type):
                    issues.append(f"{case['id']} 输出{name}不符合{field.type}")
            non_finite = [path for path, value in flatten(output) if isinstance(value, float) and not math.isfinite(value)]
            if non_finite:
                issues.append(f"{case['id']} 含非有限数值: {non_finite[:5]}")
            numeric_leaves = [
                value for _, value in flatten(output)
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            ]
            if not numeric_leaves:
                issues.append(f"{case['id']} 没有任何具体数值输出")

        successful_outputs = [execution["output"] for execution in executions if execution.get("success")]
        output_changed = len(successful_outputs) == 2 and successful_outputs[0] != successful_outputs[1]
        rows.append({
            "model_code": model_code,
            "tool_name": model.tool_name,
            "name": model.name,
            "version": model.version,
            "case_ids": [case["id"] for case in selected_cases],
            "output_contract": [asdict(field) if hasattr(field, "__dataclass_fields__") else {
                "name": field.name,
                "label": field.label,
                "type": field.type,
                "unit": field.unit,
                "nullable": field.nullable,
            } for field in model.output_fields],
            "case_a_preview": selected_output_preview(model, successful_outputs[0]) if successful_outputs else {},
            "case_b_preview": selected_output_preview(model, successful_outputs[1]) if len(successful_outputs) > 1 else {},
            "output_changed_between_cases": output_changed,
            "passed": not issues,
            "issues": issues,
            "executions": executions,
        })

    passed = sum(row.get("passed", False) for row in rows)
    changed = sum(row.get("output_changed_between_cases", False) for row in rows)
    report = {
        "report_type": "engineering_cross_case_runtime_output_audit",
        "not_a_research_dataset": True,
        "date": str(date.today()),
        "base_url": args.base_url,
        "registered_count": manifest.get("registered_count"),
        "qualified_executable_count": manifest.get("qualified_executable_count"),
        "excluded": ["G005（已单独完成真实案例资产专项测试）"],
        "tested_tool_count": len(rows),
        "passed_tool_count": passed,
        "failed_tool_count": len(rows) - passed,
        "outputs_changed_between_case_b_and_c": changed,
        "rows": rows,
    }
    json_path = output_dir / "119工具异案例具体输出审计.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# 119工具异案例具体输出审计",
        "",
        f"日期：{date.today()}",
        "",
        "性质：工程运行审计，不是正式研究数据集；不调用外部大模型 API。",
        "",
        f"范围：排除已单独专项验证的 G005，对其余 {len(rows)} 项工具分别调用第二、第三正常案例。",
        "",
        f"结果：{passed}/{len(rows)} 项同时通过 HTTP 调用、输出字段、类型、有限数值与具体数值检查；"
        f"其中 {changed} 项的两个案例输出发生变化。",
        "",
        "## 逐工具结果",
        "",
        "| 工具 | 两个异案例 | 具体输出示例（第三案例） | 案例间变化 | 结论 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        preview = json.dumps(row.get("case_b_preview", {}), ensure_ascii=False, separators=(",", ":"))
        preview = preview.replace("|", "\\|")
        if len(preview) > 420:
            preview = preview[:417] + "…"
        issues = "；".join(row.get("issues", [])) or "通过"
        escaped_issues = issues.replace("|", "\\|")
        lines.append(
            f"| {row['model_code']} {row['name']} | {' / '.join(row.get('case_ids', []))} | `{preview}` | "
            f"{'是' if row.get('output_changed_between_cases') else '否'} | {escaped_issues} |"
        )
    lines.extend([
        "",
        "## 输出合同说明",
        "",
        "完整输入、完整输出、来源记录和逐字段输出合同保存在同目录 JSON 中；Markdown 仅显示便于人工阅读的压缩示例。",
        "",
    ])
    markdown_path = output_dir / "119工具异案例具体输出审计.md"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "json": str(json_path),
        "markdown": str(markdown_path),
        "tested": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "changed": changed,
    }, ensure_ascii=False))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
