"""Read-only PostgreSQL repository for P1-W7 BOF slag/metal parameters."""
from __future__ import annotations

import math
from typing import Any

from ..base import Provenance
from .reference_repository import RepositoryError, _cursor


def _provenance(row: dict[str, Any]) -> Provenance:
    return Provenance(
        dataset_id=str(row["dataset_id"]),
        name=str(row["dataset_name"]),
        version=str(row.get("dataset_version") or row.get("source_version") or "") or None,
        url=str(row.get("source_url") or row.get("dataset_access_url") or "") or None,
        table="metallurgy_v2.bof_slag_model_parameter",
        record_id=str(row["id"]),
        source_ref=str(row.get("source_ref") or "") or None,
        checksum=str(row.get("dataset_checksum") or "") or None,
        applicable_domain={
            "temperature_min_k": float(row["temperature_min_k"]),
            "temperature_max_k": float(row["temperature_max_k"]),
            "usage_scope": row["usage_scope"],
            "parameter_set_id": row["parameter_set_id"],
        },
    )


def approved_parameter_set(model_code: str, parameter_set_id: str,
                           temperature_k: float) -> tuple[dict[str, Any], list[Provenance]]:
    """Load one complete approved set for a temperature without static fallback."""
    if not isinstance(model_code, str) or not model_code.strip():
        raise RepositoryError("model_code不能为空", "INVALID_INPUT")
    if not isinstance(parameter_set_id, str) or not parameter_set_id.strip():
        raise RepositoryError("parameter_set_id不能为空", "INVALID_INPUT")
    if isinstance(temperature_k, bool) or not math.isfinite(float(temperature_k)) \
            or float(temperature_k) <= 0:
        raise RepositoryError("temperature_k必须是有限正值", "INVALID_INPUT")

    with _cursor() as cur:
        cur.execute(
            """SELECT p.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum, d.access_url dataset_access_url
               FROM metallurgy_v2.bof_slag_model_parameter p
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE p.model_code=%s AND p.parameter_set_id=%s
                 AND p.is_approved=TRUE
                 AND %s BETWEEN p.temperature_min_k AND p.temperature_max_k
               ORDER BY p.parameter_code, p.id""",
            (model_code, parameter_set_id, float(temperature_k)),
        )
        rows = [dict(row) for row in cur.fetchall()]
    if not rows:
        with _cursor() as cur:
            cur.execute(
                """SELECT min(temperature_min_k) temperature_min_k,
                          max(temperature_max_k) temperature_max_k,
                          count(*) FILTER (WHERE is_approved=TRUE) approved_count
                   FROM metallurgy_v2.bof_slag_model_parameter
                   WHERE model_code=%s AND parameter_set_id=%s""",
                (model_code, parameter_set_id),
            )
            summary = dict(cur.fetchone())
        if int(summary.get("approved_count") or 0) == 0:
            raise RepositoryError(
                f"没有批准的{model_code}参数集: {parameter_set_id}", "MISSING_DATA"
            )
        raise RepositoryError(
            f"{temperature_k:g} K超出参数集{parameter_set_id}批准温区"
            f"[{summary['temperature_min_k']}, {summary['temperature_max_k']}] K",
            "OUT_OF_DOMAIN",
        )

    values: dict[str, float] = {}
    units: dict[str, str] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = str(row["parameter_code"])
        if code in values:
            raise RepositoryError(
                f"参数集{parameter_set_id}含重复批准参数{code}", "MODEL_ARTIFACT_UNAVAILABLE"
            )
        values[code] = float(row["parameter_value"])
        units[code] = str(row["unit"])
        metadata[code] = dict(row.get("metadata") or {})
    applicability = dict(rows[0].get("applicability") or {})
    usage_scopes = {row["usage_scope"] for row in rows}
    domains = {
        (float(row["temperature_min_k"]), float(row["temperature_max_k"])) for row in rows
    }
    if len(usage_scopes) != 1 or len(domains) != 1:
        raise RepositoryError(
            f"参数集{parameter_set_id}批准记录的适用域不一致", "MODEL_ARTIFACT_UNAVAILABLE"
        )
    lower, upper = next(iter(domains))
    return {
        "model_code": model_code,
        "parameter_set_id": parameter_set_id,
        "temperature_k": float(temperature_k),
        "temperature_range_k": [lower, upper],
        "usage_scope": next(iter(usage_scopes)),
        "values": values,
        "units": units,
        "metadata": metadata,
        "applicability": applicability,
    }, [_provenance(row) for row in rows]
