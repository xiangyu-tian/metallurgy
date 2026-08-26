"""Workbook capability-catalog metadata for the executable tool registry.

The workbook remains the planning authority, while runtime model codes remain
backwards-compatible implementation identifiers.  This module deliberately
contains no spreadsheet parser and performs no database access at import time;
it only loads the reviewed, versioned crosswalk asset.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


CROSSWALK_PATH = Path(__file__).with_name("data") / "tool_catalog_crosswalk_v5.json"


@lru_cache(maxsize=1)
def load_catalog_crosswalk() -> Dict[str, Any]:
    with CROSSWALK_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    entries = payload.get("entries", [])
    runtime_codes = [entry.get("runtime_model_code") for entry in entries]
    expected_count = payload.get("runtime_registry", {}).get("registered_count_at_baseline")
    if not isinstance(expected_count, int) or expected_count <= 0:
        raise ValueError("工具目录交叉映射缺少有效registered_count_at_baseline")
    if len(entries) != expected_count or len(runtime_codes) != len(set(runtime_codes)):
        raise ValueError(f"工具目录交叉映射必须完整且唯一地覆盖当前{expected_count}项运行时资产")
    covered = [entry.get("catalog_id") for entry in entries if entry.get("catalog_coverage")]
    if None in covered or len(covered) != len(set(covered)):
        raise ValueError("可覆盖的表格目录ID必须非空且唯一")
    summary = payload.get("summary", {})
    if summary.get("runtime_assets_preserved") != len(entries) or summary.get("catalog_entries_covered") != len(covered):
        raise ValueError("工具目录交叉映射汇总计数与条目不一致")
    return payload


@lru_cache(maxsize=1)
def catalog_entry_by_runtime_code() -> Dict[str, Dict[str, Any]]:
    return {
        entry["runtime_model_code"]: entry
        for entry in load_catalog_crosswalk()["entries"]
    }


def apply_catalog_metadata(model: Any) -> None:
    """Attach reviewed catalog identity to a model instance without renaming it."""
    entry = catalog_entry_by_runtime_code().get(model.model_id)
    if entry is None:
        model.catalog_id = None
        model.catalog_mapping_status = "unmapped"
        model.catalog_coverage = False
        model.legacy_model_codes = []
        model.tool_uid = f"metallurgy.runtime.{model.model_id.lower()}.v1"
        return

    model.catalog_id = entry.get("catalog_id")
    model.catalog_mapping_status = entry["mapping_status"]
    model.catalog_coverage = bool(entry.get("catalog_coverage", False))
    model.legacy_model_codes = list(entry.get("legacy_model_codes", []))
    model.related_catalog_ids = list(entry.get("related_catalog_ids", []))
    model.tool_uid = entry.get("proposed_tool_uid") or (
        f"metallurgy.catalog.{model.catalog_id.lower()}.v1"
        if model.catalog_id
        else f"metallurgy.extension.{model.model_id.lower()}.v1"
    )
