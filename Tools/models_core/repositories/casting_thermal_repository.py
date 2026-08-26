"""Read-only PostgreSQL access for casting thermal properties and benchmarks.

There is deliberately no JSON or Python-constant fallback. The versioned JSON
asset is importer input only; successful runtime reads must return approved
database records with record-level provenance.
"""
from __future__ import annotations

import bisect
import math
from typing import Any, Iterable

from ..base import Provenance
from .reference_repository import RepositoryError, _cursor


def _provenance(row: dict[str, Any], table: str) -> Provenance:
    applicable_domain = {"usage_scope": row.get("usage_scope")}
    for key in ("temperature_min_k", "temperature_max_k"):
        if row.get(key) is not None:
            applicable_domain[key] = float(row[key])
    return Provenance(
        dataset_id=str(row["dataset_id"]),
        name=str(row["dataset_name"]),
        version=str(row.get("dataset_version") or "") or None,
        url=str(row.get("source_url") or row.get("dataset_access_url") or "") or None,
        table=table,
        record_id=str(row["id"]),
        source_ref=str(row.get("source_ref") or "") or None,
        checksum=str(row.get("dataset_checksum") or "") or None,
        applicable_domain=applicable_domain,
    )


def approved_property_set(property_set_id: str) -> tuple[dict[str, Any], Provenance]:
    with _cursor() as cur:
        cur.execute(
            """SELECT p.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum, d.access_url dataset_access_url
               FROM metallurgy_v2.casting_material_property_set p
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE p.property_set_id=%s AND p.is_approved=TRUE""",
            (property_set_id,),
        )
        row = cur.fetchone()
    if not row:
        raise RepositoryError(f"没有批准的连铸热物性集: {property_set_id}", "MISSING_DATA")
    payload = dict(row)
    return payload, _provenance(payload, "metallurgy_v2.casting_material_property_set")


def _interpolate(points: list[list[float]], temperature_k: float) -> float:
    temperatures = [float(point[0]) for point in points]
    index = bisect.bisect_left(temperatures, temperature_k)
    if index < len(points) and temperatures[index] == temperature_k:
        return float(points[index][1])
    if index == 0 or index == len(points):
        raise RepositoryError("禁止对热物性表进行温区外外推", "OUT_OF_DOMAIN")
    x0, y0 = map(float, points[index - 1])
    x1, y1 = map(float, points[index])
    return y0 + (temperature_k - x0) * (y1 - y0) / (x1 - x0)


def _evaluate(row: dict[str, Any], temperature_k: float) -> float:
    equation = row["equation_type"]
    coefficients = row["coefficients"]
    if equation == "CONSTANT":
        value = float(coefficients["value"])
    elif equation == "POLYNOMIAL_T":
        value = (float(coefficients.get("a", 0.0))
                 + float(coefficients.get("b", 0.0)) * temperature_k
                 + float(coefficients.get("c", 0.0)) * temperature_k ** 2)
    elif equation == "PIECEWISE_LINEAR_TABLE":
        value = _interpolate(coefficients["points"], temperature_k)
    elif equation == "LINEAR_ENDPOINTS":
        x0, y0 = float(coefficients["x0"]), float(coefficients["y0"])
        x1, y1 = float(coefficients["x1"]), float(coefficients["y1"])
        value = y0 + (temperature_k - x0) * (y1 - y0) / (x1 - x0)
    elif equation == "LINEAR_SOLID_FRACTION":
        solidus = float(coefficients["solidus_k"])
        liquidus = float(coefficients["liquidus_k"])
        value = min(1.0, max(0.0, (liquidus - temperature_k) / (liquidus - solidus)))
    elif equation == "WIEDEMANN_FRANZ_FROM_RESISTIVITY_TABLE":
        resistivity_microohm_m = _interpolate(
            coefficients["resistivity_points_microohm_m"], temperature_k
        )
        resistivity_ohm_m = resistivity_microohm_m * 1e-6
        value = float(coefficients["lorenz_number_w_ohm_per_k2"]) * temperature_k / resistivity_ohm_m
    else:
        raise RepositoryError(f"未认证的热物性方程类型: {equation}", "MODEL_ARTIFACT_UNAVAILABLE")
    if not math.isfinite(value):
        raise RepositoryError("热物性计算产生非有限值", "MODEL_EXECUTION_ERROR")
    return value


def property_value(property_set_id: str, property_type: str,
                   temperature_k: float) -> tuple[dict[str, Any], list[Provenance]]:
    if not math.isfinite(temperature_k) or temperature_k <= 0:
        raise RepositoryError("温度必须是有限正Kelvin值", "INVALID_INPUT")
    property_set, set_provenance = approved_property_set(property_set_id)
    if not (float(property_set["temperature_min_k"]) <= temperature_k
            <= float(property_set["temperature_max_k"])):
        raise RepositoryError(
            f"{temperature_k:g} K超出物性集{property_set_id}批准温区", "OUT_OF_DOMAIN"
        )
    with _cursor() as cur:
        cur.execute(
            """SELECT c.*, p.usage_scope, p.dataset_id, d.name dataset_name,
                      d.version dataset_version, d.checksum dataset_checksum,
                      d.access_url dataset_access_url
               FROM metallurgy_v2.casting_material_property_correlation c
               JOIN metallurgy_v2.casting_material_property_set p USING(property_set_id)
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE c.property_set_id=%s AND c.property_type=%s
                 AND %s BETWEEN c.temperature_min_k AND c.temperature_max_k
                 AND c.is_active=TRUE AND p.is_approved=TRUE
               ORDER BY c.priority, c.id
               LIMIT 1""",
            (property_set_id, property_type, temperature_k),
        )
        row = cur.fetchone()
    if not row:
        with _cursor() as cur:
            cur.execute(
                """SELECT 1 FROM metallurgy_v2.casting_material_property_correlation
                   WHERE property_set_id=%s AND property_type=%s AND is_active=TRUE LIMIT 1""",
                (property_set_id, property_type),
            )
            exists = cur.fetchone() is not None
        code = "OUT_OF_DOMAIN" if exists else "MISSING_DATA"
        raise RepositoryError(
            f"物性集{property_set_id}没有{temperature_k:g} K的{property_type}批准记录", code
        )
    payload = dict(row)
    result = {
        "property_set_id": property_set_id,
        "property_type": property_type,
        "temperature_k": float(temperature_k),
        "value": _evaluate(payload, float(temperature_k)),
        "unit": payload["output_unit"],
        "phase": payload["phase"],
        "equation_type": payload["equation_type"],
        "correlation_id": payload["correlation_id"],
        "source_kind": payload["source_kind"],
        "usage_scope": payload["usage_scope"],
        "uncertainty": payload["uncertainty_json"],
    }
    return result, [set_provenance, _provenance(
        payload, "metallurgy_v2.casting_material_property_correlation"
    )]


def property_bundle(property_set_id: str, temperature_k: float,
                    property_types: Iterable[str]) -> tuple[dict[str, dict[str, Any]], list[Provenance]]:
    results: dict[str, dict[str, Any]] = {}
    provenance: list[Provenance] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for property_type in property_types:
        result, records = property_value(property_set_id, property_type, temperature_k)
        results[property_type] = result
        for record in records:
            key = (record.table, record.record_id, record.dataset_id)
            if key not in seen:
                seen.add(key)
                provenance.append(record)
    return results, provenance


def boundary_profile(boundary_profile_id: str, independent_value: float | None = None) \
        -> tuple[dict[str, Any], list[Provenance]]:
    with _cursor() as cur:
        cur.execute(
            """SELECT b.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum, d.access_url dataset_access_url,
                      p.temperature_min_k, p.temperature_max_k
               FROM metallurgy_v2.casting_boundary_profile b
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               LEFT JOIN metallurgy_v2.casting_material_property_set p USING(property_set_id)
               WHERE b.boundary_profile_id=%s AND b.is_approved=TRUE""",
            (boundary_profile_id,),
        )
        row = cur.fetchone()
    if not row:
        raise RepositoryError(f"没有批准的连铸边界曲线: {boundary_profile_id}", "MISSING_DATA")
    payload = dict(row)
    value = None
    if independent_value is not None:
        if not math.isfinite(independent_value):
            raise RepositoryError("边界自变量必须为有限数值", "INVALID_INPUT")
        if not (float(payload["domain_min"]) <= independent_value <= float(payload["domain_max"])):
            raise RepositoryError("边界曲线查询点超出批准域", "OUT_OF_DOMAIN")
        equation_type = payload["profile_json"].get("equation_type")
        if equation_type != "CONSTANT":
            raise RepositoryError("未认证的边界曲线方程", "MODEL_ARTIFACT_UNAVAILABLE")
        value = float(payload["profile_json"]["value"])
    result = {
        "boundary_profile_id": boundary_profile_id,
        "profile_type": payload["profile_type"],
        "independent_variable": payload["independent_variable"],
        "domain": [float(payload["domain_min"]), float(payload["domain_max"])],
        "independent_unit": payload["independent_unit"],
        "value_unit": payload["value_unit"],
        "value": value,
        "sign_convention": payload["profile_json"].get("sign_convention"),
        "usage_scope": payload["usage_scope"],
        "equipment_scope": payload["equipment_scope"],
    }
    return result, [_provenance(payload, "metallurgy_v2.casting_boundary_profile")]


def benchmark_cases(model_code: str = "F005") -> list[dict[str, Any]]:
    with _cursor() as cur:
        cur.execute(
            """SELECT * FROM metallurgy_v2.casting_model_benchmark_case
               WHERE model_code=%s AND within_domain=TRUE ORDER BY benchmark_id""",
            (model_code,),
        )
        return [dict(row) for row in cur.fetchall()]
