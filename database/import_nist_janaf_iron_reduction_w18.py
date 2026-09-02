"""Safely import the additive NIST-JANAF asset used by E022.

Dry-run is the default.  ``--apply`` uses one transaction and only INSERTs
previously absent natural keys.  Existing rows are compared and any conflict
aborts the entire transaction; no UPDATE/DELETE/TRUNCATE statement is issued.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras


psycopg2.extras.register_uuid()


ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = ROOT / "Tools" / "models_core" / "data" / "nist_janaf_iron_reduction_w18_v1.json"
COEFFICIENT_NAMES = tuple("ABCDEFGH")
REQUIRED_SPECIES = {"Fe", "FeO", "Fe2O3", "Fe3O4", "CO", "CO2", "H2", "H2O"}


def db_config(database: str | None = None) -> dict[str, Any]:
    config: dict[str, Any] = {
        "database": database or os.getenv("METALLURGY_DB_NAME", "metallurgy"),
        "user": os.getenv("METALLURGY_DB_USER", "postgres"),
        "password": os.getenv("METALLURGY_DB_PASSWORD", ""),
        "connect_timeout": int(os.getenv("METALLURGY_DB_CONNECT_TIMEOUT", "5")),
    }
    if os.getenv("METALLURGY_DB_HOST"):
        config["host"] = os.environ["METALLURGY_DB_HOST"]
    if os.getenv("METALLURGY_DB_PORT"):
        config["port"] = int(os.environ["METALLURGY_DB_PORT"])
    return config


def load_and_validate_asset(path: Path = ASSET_PATH) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    asset = json.loads(raw.decode("utf-8"))
    required_top = {
        "asset_id", "dataset_id", "name", "category", "provider", "license",
        "version", "retrieved_at", "quality_grade", "coefficient_units", "records",
    }
    missing = sorted(required_top - set(asset))
    if missing:
        raise ValueError(f"asset缺少字段: {', '.join(missing)}")
    if asset["dataset_id"] != "DS_NIST_JANAF_IRON_REDUCTION_W18":
        raise ValueError("dataset_id与E022固定契约不一致")
    try:
        date.fromisoformat(asset["retrieved_at"])
    except (TypeError, ValueError) as exc:
        raise ValueError("retrieved_at必须是ISO日期") from exc
    records = asset["records"]
    if not isinstance(records, list) or not records:
        raise ValueError("records必须是非空数组")
    keys: set[str] = set()
    species: set[str] = set()
    intervals: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for index, record in enumerate(records, 1):
        required = {
            "species_id", "phase", "temperature_min_k", "temperature_max_k",
            "source_record_key", "source_url", "reference_text", "coefficients",
        }
        absent = sorted(required - set(record))
        if absent:
            raise ValueError(f"records[{index}]缺少字段: {', '.join(absent)}")
        key = str(record["source_record_key"])
        if not key or key in keys:
            raise ValueError(f"source_record_key为空或重复: {key}")
        keys.add(key)
        if not str(record["source_url"]).startswith("https://webbook.nist.gov/"):
            raise ValueError(f"{key}来源URL不是NIST WebBook HTTPS地址")
        lower = float(record["temperature_min_k"])
        upper = float(record["temperature_max_k"])
        if not math.isfinite(lower) or not math.isfinite(upper) or lower < 1 or upper <= lower:
            raise ValueError(f"{key}温区非法")
        coefficients = record["coefficients"]
        if set(coefficients) != set(COEFFICIENT_NAMES):
            raise ValueError(f"{key}必须恰好提供A-H八个Shomate系数")
        if any(isinstance(value, bool) or not math.isfinite(float(value)) for value in coefficients.values()):
            raise ValueError(f"{key}含非有限Shomate系数")
        species_id = str(record["species_id"])
        species.add(species_id)
        intervals.setdefault((species_id, str(record["phase"])), []).append((lower, upper))
    if species != REQUIRED_SPECIES:
        raise ValueError(f"物种集合不闭合: {sorted(species ^ REQUIRED_SPECIES)}")
    # Overlap is permitted only at an exact shared endpoint, matching NIST segments.
    for identity, ranges in intervals.items():
        ordered = sorted(ranges)
        for previous, current in zip(ordered, ordered[1:]):
            if current[0] < previous[1] - 1e-12:
                raise ValueError(f"{identity}温区内部重叠: {previous} / {current}")
    return asset, hashlib.sha256(raw).hexdigest()


def comparable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: comparable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [comparable(item) for item in value]
    return value


def same_number(left: Any, right: Any) -> bool:
    try:
        a, b = float(left), float(right)
    except (TypeError, ValueError):
        return left == right
    return math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12 * max(1.0, abs(a), abs(b)))


def dataset_conflicts(existing: dict[str, Any], planned: dict[str, Any]) -> list[str]:
    conflicts = []
    for field in ("name", "category", "provider", "license", "ingestion_mode", "version", "checksum", "owner", "security_level", "quality_grade"):
        if comparable(existing.get(field)) != comparable(planned.get(field)):
            conflicts.append(field)
    return conflicts


def correlation_conflicts(existing: dict[str, Any], planned: dict[str, Any]) -> list[str]:
    conflicts = []
    for field in ("species_id", "phase", "equation_type", "source_id", "source_record_key", "reference_text", "quality_level"):
        if comparable(existing.get(field)) != comparable(planned.get(field)):
            conflicts.append(field)
    for field in ("temperature_min_k", "temperature_max_k", "reference_temperature_k", "reference_pressure_pa", "priority"):
        if not same_number(existing.get(field), planned.get(field)):
            conflicts.append(field)
    if comparable(existing.get("coefficients")) != comparable(planned.get("coefficients")):
        conflicts.append("coefficients")
    if comparable(existing.get("coefficient_units")) != comparable(planned.get("coefficient_units")):
        conflicts.append("coefficient_units")
    if comparable(existing.get("metadata")) != comparable(planned.get("metadata")):
        conflicts.append("metadata")
    if existing.get("is_active") is not True:
        conflicts.append("is_active")
    return conflicts


def import_asset(asset: dict[str, Any], checksum: str, *, apply: bool, database: str | None) -> dict[str, Any]:
    connection = psycopg2.connect(**db_config(database))
    connection.autocommit = False
    stats = {
        "mode": "apply" if apply else "dry_run",
        "dataset_inserted": 0,
        "correlations_inserted": 0,
        "unchanged": 0,
        "conflicts": [],
    }
    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            dataset_row = {
                "dataset_id": asset["dataset_id"],
                "name": asset["name"],
                "category": asset["category"],
                "provider": asset["provider"],
                "license": asset["license"],
                "access_url": "https://webbook.nist.gov/chemistry/",
                "ingestion_mode": "versioned-json-transactional",
                "version": asset["version"],
                "retrieved_at": asset["retrieved_at"],
                "checksum": checksum,
                "owner": "metallurgy-tools",
                "security_level": "公开",
                "quality_grade": asset["quality_grade"],
                "lineage_json": {
                    "asset_id": asset["asset_id"],
                    "source_urls": sorted({row["source_url"] for row in asset["records"]}),
                    "additive_only": True,
                    "reserved_for": "E022",
                },
            }
            cur.execute("SELECT * FROM metallurgy_v2.dataset_registry WHERE dataset_id=%s FOR SHARE", (asset["dataset_id"],))
            existing_dataset = cur.fetchone()
            if existing_dataset:
                conflicts = dataset_conflicts(dict(existing_dataset), dataset_row)
                if conflicts:
                    stats["conflicts"].append({"natural_key": asset["dataset_id"], "fields": conflicts})
                else:
                    stats["unchanged"] += 1
            elif apply:
                cur.execute(
                    """INSERT INTO metallurgy_v2.dataset_registry
                       (dataset_id,name,category,provider,license,access_url,ingestion_mode,
                        version,retrieved_at,checksum,owner,security_level,quality_grade,lineage_json)
                       VALUES (%(dataset_id)s,%(name)s,%(category)s,%(provider)s,%(license)s,
                               %(access_url)s,%(ingestion_mode)s,%(version)s,%(retrieved_at)s,
                               %(checksum)s,%(owner)s,%(security_level)s,%(quality_grade)s,%(lineage_json)s)""",
                    {**dataset_row, "lineage_json": psycopg2.extras.Json(dataset_row["lineage_json"])},
                )
                stats["dataset_inserted"] += 1
            else:
                stats["dataset_inserted"] += 1

            for record in asset["records"]:
                planned = {
                    "species_id": record["species_id"],
                    "phase": record["phase"],
                    "equation_type": "SHOMATE",
                    "temperature_min_k": record["temperature_min_k"],
                    "temperature_max_k": record["temperature_max_k"],
                    "reference_temperature_k": 298.15,
                    "reference_pressure_pa": 100000,
                    "coefficients": record["coefficients"],
                    "coefficient_units": asset["coefficient_units"],
                    "source_id": asset["dataset_id"],
                    "source_record_key": record["source_record_key"],
                    "reference_text": record["reference_text"],
                    "priority": 250,
                    "quality_level": asset["quality_grade"],
                    "is_active": True,
                    "metadata": {
                        "asset_id": asset["asset_id"],
                        "source_url": record["source_url"],
                        "retrieved_at": asset["retrieved_at"],
                        "reserved_for": "E022",
                    },
                }
                cur.execute(
                    """SELECT * FROM metallurgy_v2.thermodynamic_correlation
                       WHERE source_id=%s AND source_record_key=%s AND species_id=%s
                         AND phase=%s AND equation_type='SHOMATE'
                         AND temperature_min_k=%s AND temperature_max_k=%s FOR SHARE""",
                    (asset["dataset_id"], record["source_record_key"], record["species_id"],
                     record["phase"], record["temperature_min_k"], record["temperature_max_k"]),
                )
                existing = cur.fetchone()
                if existing:
                    conflicts = correlation_conflicts(dict(existing), planned)
                    if conflicts:
                        stats["conflicts"].append({"natural_key": record["source_record_key"], "fields": conflicts})
                    else:
                        stats["unchanged"] += 1
                elif apply and not stats["conflicts"]:
                    cur.execute(
                        """INSERT INTO metallurgy_v2.thermodynamic_correlation
                           (species_id,phase,equation_type,temperature_min_k,temperature_max_k,
                            reference_temperature_k,reference_pressure_pa,coefficients,coefficient_units,
                            source_id,source_record_key,reference_text,priority,quality_level,is_active,metadata)
                           VALUES (%(species_id)s,%(phase)s,%(equation_type)s,%(temperature_min_k)s,
                                   %(temperature_max_k)s,%(reference_temperature_k)s,%(reference_pressure_pa)s,
                                   %(coefficients)s,%(coefficient_units)s,%(source_id)s,%(source_record_key)s,
                                   %(reference_text)s,%(priority)s,%(quality_level)s,%(is_active)s,%(metadata)s)""",
                        {
                            **planned,
                            "coefficients": psycopg2.extras.Json(planned["coefficients"]),
                            "coefficient_units": psycopg2.extras.Json(planned["coefficient_units"]),
                            "metadata": psycopg2.extras.Json(planned["metadata"]),
                        },
                    )
                    stats["correlations_inserted"] += 1
                else:
                    stats["correlations_inserted"] += 1

            if stats["conflicts"]:
                raise ValueError(f"检测到{len(stats['conflicts'])}个数据库冲突")
            if apply:
                run_id = uuid.uuid4()
                details = {
                    "asset_id": asset["asset_id"],
                    "dataset_inserted": stats["dataset_inserted"],
                    "correlations_inserted": stats["correlations_inserted"],
                    "unchanged": stats["unchanged"],
                    "conflict_count": 0,
                    "mutation_policy": "INSERT_ONLY",
                }
                cur.execute(
                    """INSERT INTO metallurgy_v2.dataset_import_run
                       (run_id,dataset_id,source_version,source_checksum,dry_run,status,staged_count,
                        inserted_count,unchanged_count,conflict_count,details,completed_at)
                       VALUES (%s,%s,%s,%s,FALSE,'committed',%s,%s,%s,0,%s,CURRENT_TIMESTAMP)""",
                    (run_id, asset["dataset_id"], asset["version"], checksum, len(asset["records"]) + 1,
                     stats["dataset_inserted"] + stats["correlations_inserted"], stats["unchanged"],
                     psycopg2.extras.Json(details)),
                )
                connection.commit()
            else:
                connection.rollback()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {
        "mode": "apply" if apply else "dry_run",
        "dataset_id": asset["dataset_id"],
        "source_version": asset["version"],
        "source_checksum": checksum,
        "record_count": len(asset["records"]),
        **stats,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="commit additive rows; default is dry-run")
    parser.add_argument("--database", help="target database; defaults to METALLURGY_DB_NAME/metallurgy")
    args = parser.parse_args()
    try:
        asset, checksum = load_and_validate_asset()
        result = import_asset(asset, checksum, apply=args.apply, database=args.database)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "ok", **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
