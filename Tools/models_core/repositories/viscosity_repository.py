"""Read-only access to approved melt-viscosity correlation definitions."""

from __future__ import annotations

from typing import Any

from ..base import Provenance
from .reference_repository import RepositoryError, _cursor


TABLE = "metallurgy_v2.melt_viscosity_model_definition"


def approved_model(model_id: str, temperature_k: float) -> tuple[dict[str, Any], list[Provenance]]:
    with _cursor() as cur:
        cur.execute(
            """SELECT m.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum
               FROM metallurgy_v2.melt_viscosity_model_definition m
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE m.model_id=%s AND m.is_approved=TRUE
                 AND %s BETWEEN m.temperature_min_k AND m.temperature_max_k
               ORDER BY m.created_at DESC, m.id DESC
               LIMIT 1""",
            (model_id, temperature_k),
        )
        row = cur.fetchone()
    if not row:
        with _cursor() as cur:
            cur.execute(
                """SELECT temperature_min_k,temperature_max_k
                   FROM metallurgy_v2.melt_viscosity_model_definition
                   WHERE model_id=%s AND is_approved=TRUE
                   ORDER BY created_at DESC,id DESC LIMIT 1""",
                (model_id,),
            )
            available = cur.fetchone()
        if available:
            raise RepositoryError(
                f"{model_id} 温度适用域为 {float(available['temperature_min_k']):g}–"
                f"{float(available['temperature_max_k']):g} K",
                "OUT_OF_DOMAIN",
            )
        raise RepositoryError(f"没有批准的黏度关联式: {model_id}", "MISSING_DATA")

    payload = dict(row)
    provenance = Provenance(
        dataset_id=str(payload["dataset_id"]),
        name=str(payload["dataset_name"]),
        version=str(payload["dataset_version"]),
        url=str(payload["source_url"]),
        table=TABLE,
        record_id=str(payload["id"]),
        source_ref=f"{payload['model_id']}@{payload['source_version']}",
        checksum=str(payload["dataset_checksum"]),
        applicable_domain={
            "temperature_min_k": float(payload["temperature_min_k"]),
            "temperature_max_k": float(payload["temperature_max_k"]),
            **dict(payload["applicability"]),
        },
    )
    return payload, [provenance]
