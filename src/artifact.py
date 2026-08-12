"""Immutable experiment/deployment artifact and deterministic provenance hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from src.exceptions import ConfigurationError


_REQUIRED_FIELDS = (
    "deployment_id",
    "strategy_id",
    "strategy_version",
    "code_commit",
    "configuration_hash",
    "dataset_identity",
    "dataset_hash",
    "experiment_id",
    "validation_status",
    "created_at",
    "promotion_status",
)


def canonical_json(data: dict[str, Any]) -> str:
    """Return the canonical UTF-8 JSON representation used for hashing."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_hash(data: dict[str, Any]) -> str:
    """Return the SHA-256 hash of canonical JSON data."""
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DeploymentArtifact:
    deployment_id: str
    strategy_id: str
    strategy_version: str
    code_commit: str
    configuration_hash: str
    dataset_identity: str
    dataset_hash: str
    experiment_id: str
    validation_status: str
    created_at: str
    promotion_status: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @property
    def artifact_hash(self) -> str:
        return canonical_hash(self.to_dict())

    def validate(self) -> None:
        values = self.to_dict()
        for field_name in _REQUIRED_FIELDS:
            value = values[field_name]
            if not isinstance(value, str) or not value.strip():
                raise ConfigurationError(f"artifact.{field_name}={value!r}: required provenance field is missing")
        if not _is_utc_timestamp(self.created_at):
            raise ConfigurationError(f"artifact.created_at={self.created_at!r}: expected ISO-8601 UTC timestamp")

    def to_json(self) -> str:
        self.validate()
        return canonical_json(self.to_dict())


def _is_utc_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def create_artifact(*, deployment_id: str, strategy_id: str, strategy_version: str,
                    code_commit: str, configuration_hash: str, dataset_identity: str,
                    dataset_hash: str, experiment_id: str, validation_status: str,
                    promotion_status: str, created_at: str | None = None) -> DeploymentArtifact:
    """Create and validate an immutable provenance artifact."""
    artifact = DeploymentArtifact(
        deployment_id=deployment_id,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        code_commit=code_commit,
        configuration_hash=configuration_hash,
        dataset_identity=dataset_identity,
        dataset_hash=dataset_hash,
        experiment_id=experiment_id,
        validation_status=validation_status,
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
        promotion_status=promotion_status,
    )
    artifact.validate()
    return artifact


def validate_live_artifact(artifact: DeploymentArtifact) -> None:
    """Fail closed when live startup receives incomplete provenance."""
    artifact.validate()
