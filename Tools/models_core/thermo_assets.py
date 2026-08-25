"""Versioned, deterministic thermodynamic assets used by qualified tools."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

from .chemical_data import SHOMATE_PARAMS, THERMOCHEMICAL_DB, calc_shomate


R_J_MOL_K = 8.31446261815324
NASA_ASSET_PATH = Path(__file__).with_name("data") / "nasa7_gri30_v1.json"
_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

ELLINGHAM_DATA = {
    "2Fe + O2 -> 2FeO": {
        "delta_h_kj_mol": -544.0,
        "delta_s_j_mol_k": -133.6,
        "oxygen_coefficient": 1.0,
        "temperature_min_k": 298.15,
        "temperature_max_k": 1650.0,
        "source": "Barin thermochemical compilation snapshot",
    },
    "4Al + 3O2 -> 2Al2O3": {
        "delta_h_kj_mol": -3351.4,
        "delta_s_j_mol_k": -625.1,
        "oxygen_coefficient": 3.0,
        "temperature_min_k": 298.15,
        "temperature_max_k": 2300.0,
        "source": "Barin thermochemical compilation snapshot",
    },
}


@lru_cache(maxsize=1)
def load_nasa_asset() -> dict:
    with NASA_ASSET_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_nasa7(species: str, temperature: float) -> dict | None:
    asset = load_nasa_asset()
    entry = asset["species"].get(species)
    if not entry or not entry["temperature_min_k"] <= temperature <= entry["temperature_max_k"]:
        return None
    region = "low" if temperature <= entry["temperature_mid_k"] else "high"
    a = entry[region]
    t = temperature
    cp = R_J_MOL_K * (a[0] + a[1]*t + a[2]*t**2 + a[3]*t**3 + a[4]*t**4)
    h = R_J_MOL_K * t * (a[0] + a[1]*t/2 + a[2]*t**2/3 + a[3]*t**3/4 + a[4]*t**4/5 + a[5]/t) / 1000
    s = R_J_MOL_K * (a[0]*math.log(t) + a[1]*t + a[2]*t**2/2 + a[3]*t**3/3 + a[4]*t**4/4 + a[6])
    return {
        "Cp": cp, "H": h, "S": s, "G": h - t*s/1000,
        "coefficients": list(a), "coefficient_region": region,
        "temperature_range": [entry["temperature_min_k"], entry["temperature_max_k"]],
        "asset_id": asset["asset_id"],
    }


def reaction_key(value: str) -> str:
    text = value.translate(_SUBSCRIPTS)
    for arrow in ("<=>", "⇌", "→", "=>", "="):
        text = text.replace(arrow, "->")
    return "".join(text.split())


def find_fixed_reaction(reaction: str) -> dict | None:
    wanted = reaction_key(reaction)
    for entry in THERMOCHEMICAL_DB:
        if reaction_key(entry["reaction"]) == wanted:
            return dict(entry)
    return None


def shomate_properties(species: str, temperature: float) -> dict | None:
    return calc_shomate(species, temperature)


def shomate_range(species: str):
    entry = SHOMATE_PARAMS.get(species)
    return [entry["T_min"], entry["T_max"]] if entry else None
