"""Orchestration-only tests for the frozen experiment tool registry.

These tests must not invoke any metallurgy tool or re-run qualification cases.
"""

import re
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from Tools import models_server


ROOT = Path(__file__).resolve().parents[2]


def test_frozen_registry_exposes_120_without_dynamic_qualification():
    client = TestClient(models_server.app)
    with patch.object(
        models_server.registry,
        "qualification_report",
        side_effect=AssertionError("experiment registry must not run qualification cases"),
    ), patch.object(
        models_server.registry,
        "eligibility_report",
        side_effect=AssertionError("experiment registry must use the frozen snapshot"),
    ):
        response = client.get("/api/v1/experiments/tool-registry")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 120
    assert payload["qualification_execution_count"] == 0
    assert payload["eligibility_snapshot_id"] == "TOOL-ELIGIBILITY-20260903-120"


def test_complex_tool_contracts_are_model_visible_and_complete():
    payload = TestClient(models_server.app).get(
        "/api/v1/experiments/tool-registry"
    ).json()
    tools = {item["model_code"]: item for item in payload["tools"]}

    assert tools["D018"]["input_contract"]["status"] == "complete"
    assert tools["D019"]["input_contract"]["status"] == "complete"
    assert tools["D021"]["input_contract"]["status"] == "complete"
    assert tools["D019"]["function"]["parameters"]["properties"] \
        ["current_composition_wt_pct"]["additionalProperties"]["maximum"] == 100
    assert tools["D021"]["function"]["parameters"]["properties"] \
        ["input_streams"]["items"]["required"] == [
            "name", "category", "mass_kg", "composition"
        ]


def test_all_120_tools_have_complete_model_visible_input_contracts():
    payload = TestClient(models_server.app).get(
        "/api/v1/experiments/tool-registry"
    ).json()
    incomplete = {
        item["model_code"]: item["input_contract"]["gaps"]
        for item in payload["tools"]
        if item["input_contract"]["status"] != "complete"
    }

    assert payload["total"] == 120
    assert incomplete == {}


def test_e013_fuel_element_mapping_contract_is_complete():
    payload = TestClient(models_server.app).get(
        "/api/v1/experiments/tool-registry"
    ).json()
    tool = next(item for item in payload["tools"] if item["model_code"] == "E013")
    fuel_schema = tool["function"]["parameters"]["properties"] \
        ["reacting_fuel_element_atoms_kmol"]

    assert tool["input_contract"] == {"status": "complete", "gaps": []}
    assert fuel_schema["type"] == "object"
    assert fuel_schema["required"] == ["C"]
    assert fuel_schema["additionalProperties"] is False
    assert set(fuel_schema["properties"]) == {"C", "H", "O", "N"}
    assert fuel_schema["properties"]["C"]["minimum"] == 0
    assert fuel_schema["properties"]["H"]["default"] == 0
    assert fuel_schema["properties"]["O"]["default"] == 0
    assert fuel_schema["properties"]["N"]["default"] == 0


def test_professional_manual_cases_only_reference_production_ready_tools():
    case_text = (ROOT / "docs" / "工具调用编排专业场景人工测试题_v2_20260903.md").read_text(
        encoding="utf-8"
    )
    referenced_codes = set(re.findall(r"\b[A-Z]\d{3}\b", case_text))
    payload = TestClient(models_server.app).get(
        "/api/v1/experiments/tool-registry"
    ).json()
    tools = {item["model_code"]: item for item in payload["tools"]}
    missing = sorted(referenced_codes - set(tools))
    incomplete = {
        code: tools[code]["input_contract"]["gaps"]
        for code in sorted(referenced_codes & set(tools))
        if tools[code]["input_contract"]["status"] != "complete"
    }

    assert missing == []
    assert incomplete == {}


def test_experiment_call_route_uses_snapshot_and_reuses_execution_service():
    client = TestClient(models_server.app)
    expected = {
        "status": "success",
        "execution_id": "EXEC-MOCK",
        "model_code": "A001",
    }
    with patch.object(
        models_server.registry,
        "eligibility_report",
        side_effect=AssertionError("experiment call must use the frozen snapshot"),
    ), patch.object(
        models_server.execution_service,
        "execute",
        return_value=expected,
    ) as execute:
        response = client.post(
            "/api/v1/experiments/tools/metallurgy_a001/call",
            json={"arguments": {"value": 100}},
        )

    assert response.status_code == 200
    assert response.json() == expected
    execute.assert_called_once_with(
        "A001",
        {"value": 100},
        options={"validate_boundary": True, "return_provenance": True},
        user_or_agent="llm-orchestration-experiment",
    )
