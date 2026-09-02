"""Strict PostgreSQL repositories for data-qualified metallurgy tools.

Successful calls never fall back to Python constants.  Repository assets are
used only by the audited importer; runtime values and record provenance come
from ``metallurgy_v2`` tables.
"""
from __future__ import annotations

import math
import os
import re
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterable

import psycopg2
import psycopg2.extras

from ..base import Provenance


R_J_MOL_K = 8.31446261815324
_STATE = threading.local()


class RepositoryError(RuntimeError):
    def __init__(self, message: str, error_code: str = "DATA_BACKEND_UNAVAILABLE"):
        super().__init__(message)
        self.error_code = error_code


def _config() -> dict[str, Any]:
    config: dict[str, Any] = {
        "database": os.getenv("METALLURGY_DB_NAME", "metallurgy"),
        "user": os.getenv("METALLURGY_DB_USER", "postgres"),
        "password": os.getenv("METALLURGY_DB_PASSWORD", ""),
        "connect_timeout": int(os.getenv("METALLURGY_DB_CONNECT_TIMEOUT", "3")),
    }
    if os.getenv("METALLURGY_DB_HOST"):
        config["host"] = os.environ["METALLURGY_DB_HOST"]
    if os.getenv("METALLURGY_DB_PORT"):
        config["port"] = int(os.environ["METALLURGY_DB_PORT"])
    return config


@contextmanager
def _cursor():
    config = _config()
    key = tuple(sorted(config.items()))
    connection = getattr(_STATE, "connection", None)
    if connection is not None and (connection.closed or getattr(_STATE, "config_key", None) != key):
        connection.close()
        connection = None
    try:
        if connection is None:
            connection = psycopg2.connect(**config)
            connection.set_session(readonly=True, autocommit=True)
            _STATE.connection = connection
            _STATE.config_key = key
    except Exception as exc:
        raise RepositoryError(f"冶金参考数据库不可用: {exc}") from exc
    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
    except RepositoryError:
        raise
    except Exception as exc:
        raise RepositoryError(f"冶金参考数据查询失败: {exc}") from exc


def _provenance(row: dict, table: str) -> Provenance:
    return Provenance(
        dataset_id=str(row["dataset_id"]),
        name=str(row.get("dataset_name") or row["dataset_id"]),
        version=str(row.get("dataset_version") or row.get("source_version") or "") or None,
        table=table,
        record_id=str(row["id"]),
        source_ref=str(row.get("source_ref") or row.get("reference_text") or "") or None,
        checksum=str(row.get("dataset_checksum") or "") or None,
        applicable_domain={
            key: float(row[key]) for key in ("temperature_min_k", "temperature_max_k")
            if row.get(key) is not None
        } or None,
    )


def atomic_weights(symbols: Iterable[str]) -> tuple[dict[str, float], list[Provenance]]:
    requested = sorted(set(symbols))
    if not requested:
        raise RepositoryError("未请求任何元素原子量", "MISSING_DATA")
    with _cursor() as cur:
        cur.execute(
            """SELECT e.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum
               FROM metallurgy_v2.element_reference e
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE e.dataset_id='DS_IUPAC_AW_2021' AND e.symbol=ANY(%s)
                 AND e.is_active=TRUE
               ORDER BY e.symbol, e.created_at DESC""",
            (requested,),
        )
        rows = [dict(row) for row in cur.fetchall()]
    by_symbol = {}
    selected = []
    for row in rows:
        if row["symbol"] not in by_symbol:
            by_symbol[row["symbol"]] = float(row["atomic_weight_g_mol"])
            selected.append(row)
    missing = sorted(set(requested) - set(by_symbol))
    if missing:
        raise RepositoryError(f"原子量数据库缺少元素: {', '.join(missing)}", "MISSING_DATA")
    return by_symbol, [_provenance(row, "metallurgy_v2.element_reference") for row in selected]


def _species_parts(species: str) -> tuple[str, str]:
    match = re.fullmatch(r"\s*([^()]+)\(([^)]+)\)\s*", species)
    if not match:
        return species.strip(), ""
    clean, phase_token = match.group(1).strip(), match.group(2).lower()
    if phase_token.startswith("s"):
        phase = "solid"
    elif phase_token.startswith("l"):
        phase = "liquid"
    elif phase_token.startswith("g"):
        phase = "gas"
    else:
        phase = phase_token
    return clean, phase


def correlation(species: str, temperature: float, equation_type: str) -> dict:
    clean, phase = _species_parts(species)
    candidates = [species.strip(), clean]
    with _cursor() as cur:
        cur.execute(
            """SELECT c.*, c.source_id dataset_id, d.name dataset_name,
                      d.version dataset_version, d.checksum dataset_checksum,
                      c.reference_text source_ref
               FROM metallurgy_v2.thermodynamic_correlation c
               JOIN metallurgy_v2.dataset_registry d ON d.dataset_id=c.source_id
               WHERE c.species_id=ANY(%s) AND c.equation_type=%s
                 AND %s BETWEEN c.temperature_min_k AND c.temperature_max_k
                 AND c.is_active=TRUE
                 AND (%s='' OR c.phase=%s)
               ORDER BY CASE WHEN c.species_id=%s THEN 0 ELSE 1 END, c.priority, c.id
               LIMIT 1""",
            (candidates, equation_type, temperature, phase, phase, species.strip()),
        )
        row = cur.fetchone()
    if not row:
        with _cursor() as cur:
            cur.execute(
                """SELECT 1 FROM metallurgy_v2.thermodynamic_correlation
                   WHERE species_id=ANY(%s) AND equation_type=%s AND is_active=TRUE LIMIT 1""",
                (candidates, equation_type),
            )
            exists = cur.fetchone() is not None
        code = "OUT_OF_DOMAIN" if exists else "MISSING_DATA"
        raise RepositoryError(f"数据库无 {species} 在 {temperature:g} K 的 {equation_type} 记录", code)
    return dict(row)


def shomate(species: str, temperature: float) -> tuple[dict[str, float], list[Provenance]]:
    row = correlation(species, temperature, "SHOMATE")
    c = row["coefficients"]
    t = temperature / 1000.0
    cp = float(c["A"])+float(c["B"])*t+float(c["C"])*t**2+float(c["D"])*t**3+float(c["E"])/t**2
    h = float(c["A"])*t+float(c["B"])*t**2/2+float(c["C"])*t**3/3+float(c["D"])*t**4/4-float(c["E"])/t+float(c["F"])-float(c["H"])
    s = float(c["A"])*math.log(t)+float(c["B"])*t+float(c["C"])*t**2/2+float(c["D"])*t**3/3-float(c["E"])/(2*t**2)+float(c["G"])
    result = {"Cp": cp, "H_minus_H298": h, "S": s, "temperature_range": [float(row["temperature_min_k"]), float(row["temperature_max_k"])]}
    return result, [_provenance(row, "metallurgy_v2.thermodynamic_correlation")]


def nasa7(species: str, temperature: float) -> tuple[dict[str, Any], list[Provenance]]:
    row = correlation(species, temperature, "NASA7")
    coeffs = [float(value) for value in row["coefficients"]["a"]]
    a1,a2,a3,a4,a5,a6,a7 = coeffs
    cp = R_J_MOL_K*(a1+a2*temperature+a3*temperature**2+a4*temperature**3+a5*temperature**4)
    h = R_J_MOL_K*temperature*(a1+a2*temperature/2+a3*temperature**2/3+a4*temperature**3/4+a5*temperature**4/5+a6/temperature)/1000
    s = R_J_MOL_K*(a1*math.log(temperature)+a2*temperature+a3*temperature**2/2+a4*temperature**3/3+a5*temperature**4/4+a7)
    result = {"Cp":cp,"H":h,"S":s,"G":h-temperature*s/1000,"coefficients":coeffs,"coefficient_region":row["coefficients"]["region"],"asset_id":row["coefficients"]["asset_id"],"temperature_range":[float(row["temperature_min_k"]),float(row["temperature_max_k"])]}
    return result, [_provenance(row, "metallurgy_v2.thermodynamic_correlation")]


_SUBSCRIPT = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _normalize_reaction(value: str) -> str:
    value = value.translate(_SUBSCRIPT).replace("→", "->")
    return re.sub(r"\s+", "", value)


def reaction_properties(reaction: str, dataset_id: str = "DS002") -> tuple[dict[str, Any], list[Provenance]]:
    with _cursor() as cur:
        cur.execute(
            """SELECT reaction_id,reaction_equation,reactants,products
               FROM metallurgy_v2.reaction_definition ORDER BY reaction_id"""
        )
        definitions = [dict(row) for row in cur.fetchall()]
    target = _normalize_reaction(reaction)
    definition = next((row for row in definitions if _normalize_reaction(row["reaction_equation"]) == target), None)
    if not definition:
        raise RepositoryError("反应不在数据库热化学记录中", "MISSING_DATA")
    with _cursor() as cur:
        cur.execute(
            """SELECT p.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum
               FROM metallurgy_v2.reaction_property p
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE p.reaction_id=%s AND p.dataset_id=%s
                 AND p.property_type IN ('DELTA_H_STD','DELTA_S_STD','OXYGEN_COEFFICIENT')
               ORDER BY p.id""",
            (definition["reaction_id"], dataset_id),
        )
        rows = [dict(row) for row in cur.fetchall()]
    values = {row["property_type"]: float(row["value"]) for row in rows}
    required = {"DELTA_H_STD", "DELTA_S_STD"}
    if not required.issubset(values):
        raise RepositoryError("反应热化学记录缺少ΔH或ΔS", "MISSING_DATA")
    return {
        "reaction": definition["reaction_equation"],
        "reaction_id": definition["reaction_id"],
        "reactants": list(definition["reactants"]),
        "products": list(definition["products"]),
        **values,
        "temperature_min_k": float(rows[0]["temperature_min_k"]),
        "temperature_max_k": float(rows[0]["temperature_max_k"]),
        "source_ref": rows[0]["source_ref"],
        "source_version": rows[0]["source_version"],
    }, [_provenance(row, "metallurgy_v2.reaction_property") for row in rows]


def process_parameters(codes: Iterable[str], parameter_set_id: str = "BOF_ENGINEERING_BASELINE_V1") -> tuple[dict[str, float], list[Provenance]]:
    requested = sorted(set(codes))
    with _cursor() as cur:
        cur.execute(
            """SELECT p.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum
               FROM metallurgy_v2.process_parameter_set p
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE p.dataset_id='DS_BOF_PROCESS_PARAMETERS'
                 AND p.parameter_set_id=%s AND p.parameter_code=ANY(%s)
                 AND p.is_active=TRUE ORDER BY p.parameter_code""",
            (parameter_set_id, requested),
        )
        rows = [dict(row) for row in cur.fetchall()]
    values = {row["parameter_code"]: float(row["parameter_value"]) for row in rows}
    missing = sorted(set(requested)-set(values))
    if missing:
        raise RepositoryError(f"BOF参数集缺少: {', '.join(missing)}", "MISSING_DATA")
    return values, [_provenance(row, "metallurgy_v2.process_parameter_set") for row in rows]


def emission_factors(
    codes: Iterable[str],
    factor_set_id: str = "BF_GHG_FACTORS_W15_V1",
) -> tuple[dict[str, dict[str, Any]], list[Provenance]]:
    """Read one immutable, approved factor record for every requested code."""
    requested = sorted(set(codes))
    if not requested:
        raise RepositoryError("未请求任何排放因子", "MISSING_DATA")
    with _cursor() as cur:
        cur.execute(
            """SELECT f.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum
               FROM metallurgy_v2.emission_factor f
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE f.dataset_id='DS_BF_GHG_FACTORS_W15'
                 AND f.factor_set_id=%s AND f.factor_code=ANY(%s)
                 AND f.is_approved=TRUE
               ORDER BY f.factor_code, f.id DESC""",
            (factor_set_id, requested),
        )
        rows = [dict(row) for row in cur.fetchall()]
    selected: dict[str, dict[str, Any]] = {}
    provenance: list[Provenance] = []
    for row in rows:
        code = str(row["factor_code"])
        if code not in selected:
            selected[code] = row
            provenance.append(_provenance(row, "metallurgy_v2.emission_factor"))
    missing = sorted(set(requested) - set(selected))
    if missing:
        raise RepositoryError(f"排放因子集缺少: {', '.join(missing)}", "MISSING_DATA")
    return selected, provenance
