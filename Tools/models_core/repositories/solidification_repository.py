"""Read-only access to approved CALPHAD solidification model assets."""
from __future__ import annotations

import hashlib
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any

from pycalphad import Database

from ..base import Provenance
from .reference_repository import RepositoryError, _cursor


ROOT = Path(__file__).resolve().parents[3]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def approved_model(model_asset_id: str) -> tuple[dict[str, Any], Provenance]:
    with _cursor() as cur:
        cur.execute(
            """SELECT m.*, d.name dataset_name, d.version dataset_version,
                      d.checksum dataset_checksum
               FROM metallurgy_v2.solidification_model_definition m
               JOIN metallurgy_v2.dataset_registry d USING(dataset_id)
               WHERE m.model_asset_id=%s AND m.is_approved=TRUE""",
            (model_asset_id,),
        )
        row = cur.fetchone()
    if not row:
        raise RepositoryError(f"没有批准的凝固模型资产: {model_asset_id}", "MISSING_DATA")
    payload = dict(row)
    provenance = Provenance(
        dataset_id=str(payload["dataset_id"]),
        name=str(payload["dataset_name"]),
        version=str(payload["dataset_version"]),
        url=str(payload["source_url"]),
        table="metallurgy_v2.solidification_model_definition",
        record_id=str(payload["id"]),
        source_ref=f"{payload['model_asset_id']}@{payload['source_commit']}",
        checksum=str(payload["dataset_checksum"]),
        applicable_domain={
            "temperature_min_k": float(payload["temperature_min_k"]),
            "temperature_max_k": float(payload["temperature_max_k"]),
            "composition_basis": payload["composition_basis"],
            **payload["domain_json"],
        },
    )
    return payload, provenance


@lru_cache(maxsize=4)
def _database_from_verified_asset(asset_uri: str, expected_sha256: str) -> Database:
    path = (ROOT / asset_uri).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise RepositoryError("凝固模型资产路径越出项目根目录", "MODEL_ARTIFACT_UNAVAILABLE") from exc
    if not path.is_file():
        raise RepositoryError(f"凝固模型资产不存在: {asset_uri}", "MODEL_ARTIFACT_UNAVAILABLE")
    actual = _sha256(path)
    if actual != expected_sha256:
        raise RepositoryError("凝固模型资产SHA-256与批准记录不一致", "MODEL_ARTIFACT_UNAVAILABLE")
    try:
        # pycalphad's path loader follows the Windows locale.  The reviewed TDB
        # is UTF-8, so decode explicitly and pass text to avoid locale damage.
        text = path.read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="The type definition character.*", category=UserWarning
            )
            return Database(text)
    except UnicodeDecodeError as exc:
        raise RepositoryError("凝固模型资产不是有效UTF-8", "MODEL_ARTIFACT_UNAVAILABLE") from exc
    except Exception as exc:
        raise RepositoryError(f"凝固模型资产无法解析: {exc}", "MODEL_ARTIFACT_UNAVAILABLE") from exc


def load_database(model_asset_id: str) -> tuple[Database, dict[str, Any], list[Provenance]]:
    row, provenance = approved_model(model_asset_id)
    db = _database_from_verified_asset(str(row["asset_uri"]), str(row["asset_sha256"]))
    return db, row, [provenance]


def benchmark_cases(model_asset_id: str) -> list[dict[str, Any]]:
    with _cursor() as cur:
        cur.execute(
            """SELECT * FROM metallurgy_v2.solidification_benchmark_case
               WHERE model_asset_id=%s ORDER BY benchmark_id""",
            (model_asset_id,),
        )
        return [dict(row) for row in cur.fetchall()]
