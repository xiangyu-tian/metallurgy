"""Read-only PostgreSQL access for F006 machine configurations and benchmarks.

The reviewed JSON asset is import input only. Runtime calls deliberately have
no file or Python-constant fallback: successful results must carry provenance
from approved PostgreSQL records.
"""
from __future__ import annotations

from typing import Any

from ..base import Provenance
from .reference_repository import RepositoryError, _cursor


def _provenance(row: dict[str, Any], table: str) -> Provenance:
    return Provenance(
        dataset_id=str(row["dataset_id"]),
        name=str(row["dataset_name"]),
        version=str(row.get("dataset_version") or "") or None,
        url=str(row.get("source_url") or row.get("dataset_access_url") or "") or None,
        table=table,
        record_id=str(row["id"]),
        source_ref=str(row.get("source_ref") or "") or None,
        checksum=str(row.get("dataset_checksum") or "") or None,
        applicable_domain={
            "usage_scope": row["usage_scope"],
            "casting_speed_min_m_s": float(row["casting_speed_min_m_s"]),
            "casting_speed_max_m_s": float(row["casting_speed_max_m_s"]),
            "effective_metallurgical_length_m": float(
                row["effective_metallurgical_length_m"]
            ),
        },
    )


def approved_machine_configuration(
    machine_configuration_id: str,
) -> tuple[dict[str, Any], Provenance]:
    """Return one approved configuration and record-level provenance."""
    with _cursor() as cur:
        cur.execute(
            """SELECT c.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum, d.access_url dataset_access_url
               FROM metallurgy_v2.casting_machine_configuration c
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE c.machine_configuration_id=%s AND c.is_approved=TRUE""",
            (machine_configuration_id,),
        )
        row = cur.fetchone()
    if not row:
        raise RepositoryError(
            f"没有批准的连铸机配置: {machine_configuration_id}", "MISSING_DATA"
        )
    payload = dict(row)
    return payload, _provenance(
        payload, "metallurgy_v2.casting_machine_configuration"
    )


def endpoint_benchmark_cases(model_code: str = "F006") -> list[dict[str, Any]]:
    """Return approved in-domain endpoint benchmarks for qualification tests."""
    with _cursor() as cur:
        cur.execute(
            """SELECT b.*
               FROM metallurgy_v2.casting_endpoint_benchmark_case b
               JOIN metallurgy_v2.casting_machine_configuration c
                 USING(machine_configuration_id)
               WHERE b.model_code=%s AND b.within_domain=TRUE AND c.is_approved=TRUE
               ORDER BY b.benchmark_id""",
            (model_code,),
        )
        return [dict(row) for row in cur.fetchall()]
