"""Safely import versioned reference data required by the 30-tool milestone.

Default mode is a full dry run inside a rolled-back transaction.  ``--apply``
requires a readable PostgreSQL custom backup and performs insert-only imports.
Natural-key content conflicts abort the complete transaction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

import psycopg2
import psycopg2.extras

psycopg2.extras.register_uuid()


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "Tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from models_core.chemical_data import ELEMENT_ATOMIC_WEIGHTS, THERMOCHEMICAL_DB  # noqa: E402
from models_core.thermo_assets import ELLINGHAM_DATA  # noqa: E402


MIGRATION = ROOT / "database" / "migrations" / "006_tool_data_qualification.sql"
NASA_ASSET = TOOLS / "models_core" / "data" / "nasa7_gri30_v1.json"
BOF_ASSET = TOOLS / "models_core" / "data" / "bof_process_parameters_v1.json"
LOCK_KEY = 300120260825


class ImportConflict(RuntimeError):
    pass


def db_config() -> dict[str, Any]:
    config: dict[str, Any] = {
        "database": os.getenv("METALLURGY_DB_NAME", "metallurgy"),
        "user": os.getenv("METALLURGY_DB_USER", "postgres"),
        "password": os.getenv("METALLURGY_DB_PASSWORD", ""),
        "connect_timeout": int(os.getenv("METALLURGY_DB_CONNECT_TIMEOUT", "5")),
    }
    if os.getenv("METALLURGY_DB_HOST"):
        config["host"] = os.environ["METALLURGY_DB_HOST"]
    if os.getenv("METALLURGY_DB_PORT"):
        config["port"] = int(os.environ["METALLURGY_DB_PORT"])
    return config


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_backup(path_text: str | None, apply: bool) -> dict[str, str] | None:
    if not path_text:
        if apply:
            raise ValueError("--apply requires --backup-file from a verified pre-import backup")
        return None
    path = Path(path_text).resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"backup file is missing or empty: {path}")
    digest = sha256(path)
    sums = path.parent / "SHA256SUMS"
    if sums.exists():
        text = sums.read_text(encoding="utf-8")
        if digest not in text:
            raise ValueError("backup SHA256 does not match SHA256SUMS")
    return {"path": str(path), "sha256": digest}


def canonical(value: Any) -> str:
    if isinstance(value, psycopg2.extras.Json):
        value = value.adapted
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))


def equivalent(existing: Any, incoming: Any) -> bool:
    """Compare DB-returned values to asset values without representation noise."""
    if isinstance(existing, psycopg2.extras.Json):
        existing = existing.adapted
    if isinstance(incoming, psycopg2.extras.Json):
        incoming = incoming.adapted
    if isinstance(existing, (int, float, Decimal)) and not isinstance(existing, bool) \
            and isinstance(incoming, (int, float, Decimal)) and not isinstance(incoming, bool):
        return Decimal(str(existing)) == Decimal(str(incoming))
    if isinstance(existing, dict) and isinstance(incoming, dict):
        return set(existing) == set(incoming) and all(
            equivalent(existing[key], incoming[key]) for key in existing
        )
    if isinstance(existing, (list, tuple)) and isinstance(incoming, (list, tuple)):
        return len(existing) == len(incoming) and all(
            equivalent(left, right) for left, right in zip(existing, incoming)
        )
    return existing == incoming


def insert_checked(cur, table: str, key_where: str, key_values: tuple,
                   data: dict[str, Any], compare_fields: Iterable[str]) -> str:
    cur.execute(f"SELECT * FROM {table} WHERE {key_where} FOR SHARE", key_values)
    existing = cur.fetchone()
    if existing:
        mismatches = {}
        for field in compare_fields:
            old = existing[field]
            new = data[field]
            if not equivalent(old, new):
                mismatches[field] = {"existing": old, "incoming": new}
        if mismatches:
            raise ImportConflict(f"content conflict in {table} key={key_values}: {canonical(mismatches)}")
        return "unchanged"
    columns = list(data)
    placeholders = ",".join(["%s"] * len(columns))
    cur.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
        tuple(
            psycopg2.extras.Json(data[column])
            if isinstance(data[column], (dict, list))
            else data[column]
            for column in columns
        ),
    )
    return "inserted"


def dataset_rows(checksums: dict[str, str]) -> list[dict[str, Any]]:
    base = {
        "license": "reference-data snapshot; preserve upstream attribution",
        "ingestion_mode": "versioned repository asset",
        "retrieved_at": "2026-08-25 00:00:00",
        "owner": "metallurgy-tools",
        "security_level": "公开",
        "quality_grade": "B",
    }
    return [
        {**base, "dataset_id": "DS_IUPAC_AW_2021", "name": "IUPAC standard atomic weights 2021 snapshot", "category": "基础化学与计量", "provider": "IUPAC/CIAAW", "version": "2021-snapshot-v1", "checksum": checksums["atomic"], "lineage_json": {"import_source": "models_core.chemical_data:ELEMENT_ATOMIC_WEIGHTS"}},
        {**base, "dataset_id": "DS_NASA7_GRI30", "name": "GRI-Mech 3.0 NASA7 thermodynamic subset", "category": "热力学性质", "provider": "GRI-Mech", "version": "NASA7-GRI30-SUBSET-V1", "checksum": checksums["nasa"], "lineage_json": {"import_source": str(NASA_ASSET.relative_to(ROOT))}},
        {**base, "dataset_id": "DS_BOF_PROCESS_PARAMETERS", "name": "BOF transparent static-balance engineering parameters", "category": "冶金工艺", "provider": "metallurgy-tools", "version": "BOF-ENGINEERING-BASELINE-2026.08-v1", "checksum": checksums["bof"], "lineage_json": {"import_source": str(BOF_ASSET.relative_to(ROOT)), "plant_control_approved": False}},
        {**base, "dataset_id": "DS_ELLINGHAM_BARIN_V1", "name": "Barin Ellingham parameter snapshot", "category": "热力学性质", "provider": "Barin compilation", "version": "ELLINGHAM-BARIN-V1", "checksum": checksums["ellingham"], "lineage_json": {"import_source": "models_core.thermo_assets:ELLINGHAM_DATA"}},
    ]


def import_datasets(cur, checksums: dict[str, str], stats: dict[str, int]) -> None:
    fields = ["name", "category", "provider", "license", "ingestion_mode", "version", "checksum", "owner", "security_level", "quality_grade", "lineage_json"]
    for row in dataset_rows(checksums):
        status = insert_checked(cur, "metallurgy_v2.dataset_registry", "dataset_id=%s", (row["dataset_id"],), row, fields)
        stats[status] += 1


def import_elements(cur, stats: dict[str, int]) -> None:
    for symbol, weight in sorted(ELEMENT_ATOMIC_WEIGHTS.items()):
        data = {
            "dataset_id": "DS_IUPAC_AW_2021", "symbol": symbol,
            "atomic_weight_g_mol": weight, "unit": "g/mol",
            "source_version": "2021-snapshot-v1", "source_ref": "IUPAC/CIAAW standard atomic weights 2021 snapshot",
            "source_record_key": f"IUPAC-AW-2021:{symbol}", "metadata": psycopg2.extras.Json({"natural_isotopic_composition": True}),
        }
        status = insert_checked(cur, "metallurgy_v2.element_reference", "dataset_id=%s AND symbol=%s AND source_version=%s", (data["dataset_id"], symbol, data["source_version"]), data, ["atomic_weight_g_mol", "unit", "source_ref", "source_record_key"])
        stats[status] += 1


def import_nasa(cur, stats: dict[str, int]) -> None:
    asset = json.loads(NASA_ASSET.read_text(encoding="utf-8"))
    for species, entry in asset["species"].items():
        for region, low, high in (
            ("low", entry["temperature_min_k"], entry["temperature_mid_k"]),
            ("high", entry["temperature_mid_k"], entry["temperature_max_k"]),
        ):
            record_key = f"{asset['asset_id']}:{species}:{region}"
            data = {
                "species_id": species, "phase": "gas", "equation_type": "NASA7",
                "temperature_min_k": low, "temperature_max_k": high,
                "coefficients": psycopg2.extras.Json({"a": entry[region], "region": region, "asset_id": asset["asset_id"]}),
                "coefficient_units": psycopg2.extras.Json({"temperature": "K", "cp": "J/(mol*K)", "h": "kJ/mol", "s": "J/(mol*K)"}),
                "source_id": "DS_NASA7_GRI30", "source_record_key": record_key,
                "reference_text": asset["source"], "priority": 10, "quality_level": "B",
                "metadata": psycopg2.extras.Json({"coefficient_order": asset["coefficient_order"]}),
            }
            status = insert_checked(cur, "metallurgy_v2.thermodynamic_correlation", "source_id=%s AND source_record_key=%s", (data["source_id"], record_key), data, ["species_id", "phase", "equation_type", "temperature_min_k", "temperature_max_k", "coefficients", "reference_text"])
            stats[status] += 1


def import_reaction_properties(cur, stats: dict[str, int]) -> None:
    cur.execute("SELECT reaction_id, reaction_equation FROM metallurgy_v2.reaction_definition ORDER BY reaction_id")
    definitions = cur.fetchall()
    if len(definitions) < len(THERMOCHEMICAL_DB):
        raise ImportConflict("existing reaction_definition does not cover the ten fixed reactions")
    by_id = {row["reaction_id"]: row for row in definitions}
    for index, entry in enumerate(THERMOCHEMICAL_DB, start=1):
        reaction_id = f"R{index:03d}"
        if reaction_id not in by_id:
            raise ImportConflict(f"missing reaction definition {reaction_id}")
        for code, value, unit in (("DELTA_H_STD", entry["deltaH"], "kJ/mol-reaction"), ("DELTA_S_STD", entry["deltaS"], "J/(mol-reaction*K)")):
            key = f"REACTION-THERMO-2026.08-v1:{reaction_id}:{code}"
            data = {
                "reaction_id": reaction_id, "dataset_id": "DS002", "property_type": code,
                "temperature": 298.15, "value": value, "unit": unit,
                "data_type": "compiled", "source_ref": "NIST-JANAF / Barin compiled reaction snapshot",
                "quality_grade": "B", "source_version": "REACTION-THERMO-2026.08-v1",
                "source_record_key": key, "temperature_min_k": 1.0, "temperature_max_k": 3500.0,
                "metadata": psycopg2.extras.Json({"approximation": "temperature-independent delta H / delta S", "asset_reaction": entry["reaction"]}),
            }
            status = insert_checked(cur, "metallurgy_v2.reaction_property", "dataset_id=%s AND source_record_key=%s", (data["dataset_id"], key), data, ["reaction_id", "property_type", "value", "unit", "source_version", "temperature_min_k", "temperature_max_k"])
            stats[status] += 1


def import_ellingham(cur, stats: dict[str, int]) -> None:
    definitions = {
        "2Fe + O2 -> 2FeO": ("R011", "2Fe + O2 -> 2FeO", "铁氧化生成氧化亚铁", [{"species":"Fe","coeff":2,"phase":"s"},{"species":"O2","coeff":1,"phase":"g"}], [{"species":"FeO","coeff":2,"phase":"s"}]),
        "4Al + 3O2 -> 2Al2O3": ("R012", "4Al + 3O2 -> 2Al2O3", "铝氧化生成氧化铝", [{"species":"Al","coeff":4,"phase":"s"},{"species":"O2","coeff":3,"phase":"g"}], [{"species":"Al2O3","coeff":2,"phase":"s"}]),
    }
    for equation, entry in ELLINGHAM_DATA.items():
        reaction_id, canonical_eq, name, reactants, products = definitions[equation]
        definition = {"reaction_id": reaction_id, "reaction_equation": canonical_eq, "name": name, "category": "氧化", "reactants": psycopg2.extras.Json(reactants), "products": psycopg2.extras.Json(products)}
        status = insert_checked(cur, "metallurgy_v2.reaction_definition", "reaction_id=%s", (reaction_id,), definition, ["reaction_equation", "name", "category", "reactants", "products"])
        stats[status] += 1
        values = (("DELTA_H_STD", entry["delta_h_kj_mol"], "kJ/mol-reaction"), ("DELTA_S_STD", entry["delta_s_j_mol_k"], "J/(mol-reaction*K)"), ("OXYGEN_COEFFICIENT", entry["oxygen_coefficient"], "mol O2/mol-reaction"))
        for code, value, unit in values:
            key = f"ELLINGHAM-BARIN-V1:{reaction_id}:{code}"
            data = {"reaction_id":reaction_id,"dataset_id":"DS_ELLINGHAM_BARIN_V1","property_type":code,"temperature":298.15,"value":value,"unit":unit,"data_type":"compiled","source_ref":entry["source"],"quality_grade":"B","source_version":"ELLINGHAM-BARIN-V1","source_record_key":key,"temperature_min_k":entry["temperature_min_k"],"temperature_max_k":entry["temperature_max_k"],"metadata":psycopg2.extras.Json({"approximation":"Ellingham straight line"})}
            status = insert_checked(cur, "metallurgy_v2.reaction_property", "dataset_id=%s AND source_record_key=%s", (data["dataset_id"], key), data, ["reaction_id", "property_type", "value", "unit", "temperature_min_k", "temperature_max_k"])
            stats[status] += 1


def import_process_parameters(cur, stats: dict[str, int]) -> None:
    asset = json.loads(BOF_ASSET.read_text(encoding="utf-8"))
    for item in asset["parameters"]:
        data = {"dataset_id":asset["dataset_id"],"parameter_set_id":asset["parameter_set_id"],"process":asset["process"],"parameter_code":item["code"],"parameter_value":item["value"],"unit":item["unit"],"source_version":asset["asset_id"],"source_ref":item["source_ref"],"applicability":psycopg2.extras.Json(asset["applicability"]),"metadata":psycopg2.extras.Json({"asset_id":asset["asset_id"]})}
        status = insert_checked(cur, "metallurgy_v2.process_parameter_set", "dataset_id=%s AND parameter_set_id=%s AND parameter_code=%s AND source_version=%s", (data["dataset_id"],data["parameter_set_id"],data["parameter_code"],data["source_version"]), data, ["process", "parameter_value", "unit", "source_ref", "applicability"])
        stats[status] += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="commit insert-only migration/import")
    parser.add_argument("--backup-file", help="verified pg_dump custom backup required for --apply")
    args = parser.parse_args()
    backup = verify_backup(args.backup_file, args.apply)
    checksums = {
        "atomic": "sha256:" + hashlib.sha256(canonical(ELEMENT_ATOMIC_WEIGHTS).encode()).hexdigest(),
        "nasa": "sha256:" + sha256(NASA_ASSET),
        "bof": "sha256:" + sha256(BOF_ASSET),
        "ellingham": "sha256:" + hashlib.sha256(canonical(ELLINGHAM_DATA).encode()).hexdigest(),
    }
    run_id = uuid.uuid4()
    stats = {"inserted": 0, "unchanged": 0}
    conn = psycopg2.connect(**db_config())
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SET LOCAL statement_timeout='60s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
            cur.execute(MIGRATION.read_text(encoding="utf-8"))
            import_datasets(cur, checksums, stats)
            import_elements(cur, stats)
            import_nasa(cur, stats)
            import_reaction_properties(cur, stats)
            import_ellingham(cur, stats)
            import_process_parameters(cur, stats)
            details = {"backup": backup, "assets": checksums}
            cur.execute("INSERT INTO metallurgy_v2.dataset_import_run (run_id,dataset_id,source_version,source_checksum,dry_run,status,staged_count,inserted_count,unchanged_count,details,completed_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)", (run_id,"30TOOLS-D1","2026.08-v1",checksums["bof"],not args.apply,"committed" if args.apply else "dry_run_passed",stats["inserted"]+stats["unchanged"],stats["inserted"],stats["unchanged"],psycopg2.extras.Json(details)))
        if args.apply:
            conn.commit()
        else:
            conn.rollback()
        print(json.dumps({"mode":"apply" if args.apply else "dry-run","run_id":str(run_id),**stats,"backup":backup},ensure_ascii=False,indent=2))
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
