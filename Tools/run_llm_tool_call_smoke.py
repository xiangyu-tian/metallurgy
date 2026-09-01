"""Run isolated real-LLM function-call smoke tests against the unified tool API.

This is an opt-in integration runner, not part of the offline pytest suite and
not a research dataset generator.  Provider credentials are read from the
process environment or an explicitly supplied env file and are never emitted.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if value[:1] == value[-1:] and value[:1] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 120.0,
    attempts: int = 3,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=request_headers, method="POST" if body is not None else "GET")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from {url}: {response_body[:1000]}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt)
    raise RuntimeError(f"request failed after {attempts} attempts: {url}: {last_error}")


def value_at_path(payload: Any, path: str) -> Any:
    value = payload
    for part in path.split("."):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def assert_expected(execution: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    for check in checks:
        actual = value_at_path(execution, check["path"])
        expected = check["value"]
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            tolerance = float(check.get("absolute_tolerance", 0.0))
            if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance):
                raise AssertionError(f"{check['path']}: expected {expected}, got {actual}")
        elif actual != expected:
            raise AssertionError(f"{check['path']}: expected {expected!r}, got {actual!r}")


def provider_message(response: dict[str, Any]) -> dict[str, Any]:
    try:
        return response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"provider response has no assistant message: {response}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--case-file", type=Path, required=True)
    parser.add_argument("--tools-api-base", required=True, help="Unified metallurgy tool API base URL")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--model-code", action="append", dest="model_codes")
    args = parser.parse_args()

    config = dict(os.environ)
    if args.env_file:
        config.update(load_env_file(args.env_file))
    api_key = config.get("DEEPSEEK_API_KEY", "")
    base_url = config.get("DEEPSEEK_BASE_URL", "").rstrip("/")
    model_name = config.get("DEEPSEEK_MODEL", "")
    if not api_key or not base_url or not model_name:
        raise RuntimeError("DEEPSEEK_API_KEY/DEEPSEEK_BASE_URL/DEEPSEEK_MODEL must be configured")

    tools_base = args.tools_api_base.rstrip("/")
    manifest = request_json(f"{tools_base}/api/v1/tools")
    definitions = {item["model_code"]: item for item in manifest["tools"]}
    case_payload = json.loads(args.case_file.read_text(encoding="utf-8"))
    cases = [
        case for case in case_payload["cases"]
        if not args.model_codes or case["model_code"] in set(args.model_codes)
    ]
    provider_url = f"{base_url}/chat/completions"
    provider_headers = {"Authorization": f"Bearer {api_key}"}
    results = []

    for case in cases:
        started = time.perf_counter()
        code = case["model_code"]
        definition = definitions.get(code)
        if not definition:
            raise RuntimeError(f"eligible tool manifest has no model_code {code}")
        isolated_tool = {"type": "function", "function": definition["function"]}
        messages = [
            {
                "role": "system",
                "content": "你正在执行单工具接口测试。必须调用唯一提供的函数，不得直接给出计算答案。参数必须完全来自用户输入，不得添加隐藏默认值。工具执行后，最终答复必须原样包含execution_id和model_code。",
            },
            {"role": "user", "content": case["prompt"]},
        ]
        first_payload = {
            "model": model_name,
            "messages": messages,
            "tools": [isolated_tool],
            "stream": False,
            "temperature": 0,
            "max_tokens": 4096,
        }
        thinking_mode = case.get("thinking_mode")
        if thinking_mode is not None:
            if thinking_mode not in {"enabled", "disabled"}:
                raise ValueError(
                    f"{case['case_id']}: thinking_mode must be enabled or disabled"
                )
            first_payload["thinking"] = {"type": thinking_mode}
        if case.get("force_tool_choice", False):
            if thinking_mode == "enabled":
                raise ValueError(
                    f"{case['case_id']}: named tool_choice is incompatible with thinking_mode=enabled"
                )
            first_payload["tool_choice"] = {
                "type": "function",
                "function": {"name": definition["function"]["name"]},
            }
        first = request_json(
            provider_url,
            payload=first_payload,
            headers=provider_headers,
        )
        assistant = provider_message(first)
        tool_calls = assistant.get("tool_calls") or []
        if len(tool_calls) != 1:
            raise AssertionError(f"{case['case_id']}: expected exactly one tool call, got {len(tool_calls)}")
        tool_call = tool_calls[0]
        function = tool_call.get("function", {})
        if function.get("name") != definition["function"]["name"]:
            raise AssertionError(f"{case['case_id']}: wrong function {function.get('name')}")
        raw_arguments = function.get("arguments", "{}")
        arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        execution = request_json(
            f"{tools_base}/api/v1/tools/{function['name']}/call",
            payload={"arguments": arguments, "options": {"validate_boundary": True, "return_provenance": True}},
        )
        if execution.get("status") != "success" or execution.get("model_code") != code:
            raise AssertionError(f"{case['case_id']}: tool execution failed: {execution}")
        assert_expected(execution, case.get("expected", []))

        assistant_history = {
            key: assistant[key]
            for key in ("role", "content", "reasoning_content", "tool_calls")
            if key in assistant
        }
        final_payload = {
            "model": model_name,
            "messages": messages + [
                assistant_history,
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function["name"],
                    "content": json.dumps(execution, ensure_ascii=False),
                },
            ],
            "stream": False,
            "temperature": 0,
            "max_tokens": 512,
        }
        if thinking_mode is not None:
            final_payload["thinking"] = {"type": thinking_mode}
        final = request_json(
            provider_url,
            payload=final_payload,
            headers=provider_headers,
        )
        final_content = str(provider_message(final).get("content") or "")
        if execution["execution_id"] not in final_content or code not in final_content:
            raise AssertionError(f"{case['case_id']}: final answer did not echo execution identity")
        results.append({
            "case_id": case["case_id"],
            "model_code": code,
            "function_name": function["name"],
            "arguments": arguments,
            "execution_id": execution["execution_id"],
            "tool_uid": execution.get("tool_uid"),
            "catalog_id": execution.get("catalog_id"),
            "status": "passed",
            "provider_tool_choice_forced": bool(case.get("force_tool_choice", False)),
            "provider_thinking_mode": thinking_mode or "provider_default",
            "expected_checks": len(case.get("expected", [])),
            "roundtrip_identity_echoed": True,
            "runtime_ms": round((time.perf_counter() - started) * 1000, 2),
        })
        print(f"PASS {case['case_id']} {function['name']} {execution['execution_id']}", flush=True)

    report = {
        "schema_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": case_payload.get("purpose"),
        "provider_model": model_name,
        "tool_manifest_total": manifest.get("total"),
        "passed": len(results),
        "failed": 0,
        "results": results,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("provider_model", "tool_manifest_total", "passed", "failed")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
