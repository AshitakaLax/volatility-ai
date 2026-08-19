"""
Immutable experiment/deployment artifacts. Task 6.3.

A winning parameter row alone can't reproduce or safely deploy a
strategy. DeploymentArtifact ties parameters to the code, data,
configuration, and validation status they were produced under, under
one immutable identity.

Canonical artifact hash contract (implementation_task_specs.md Task
6.3): SHA-256 over canonical UTF-8 JSON -- lexical key ordering
(sort_keys=True), no insignificant whitespace (compact separators),
explicit UTF-8 encoding, stable numeric serialization, no secret
fields. The same inputs produce the same hash across processes and
platforms.

On "stable numeric serialization": json.dumps uses repr() for floats,
which is round-trip stable and platform-consistent for IEEE-754
doubles on every platform CPython supports -- so no custom float
formatting is imposed. What IS guarded is that NaN/Infinity (which
json.dumps emits by default as bare NaN/Infinity tokens -- invalid
JSON, and not meaningfully comparable) are rejected outright via
allow_nan=False rather than silently hashed.

Secrets: this module never reads credentials and has no field for
them. Task 6.4 owns the broader secret-separation rules; the only
thing done here is the narrow "never include secrets in the artifact"
requirement of this task -- enforced by _assert_no_secret_fields(),
which rejects suspicious key names outright rather than trusting
callers not to pass them.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.exceptions import ConfigurationError

# Key substrings that must never appear in artifact content. Checked
# case-insensitively against every nested key.
_SECRET_KEY_MARKERS = ("secret", "password", "passwd", "api_key", "apikey", "token", "credential", "private_key")

REQUIRED_PROVENANCE_FIELDS = (
    "deployment_id",
    "strategy_id",
    "strategy_version",
    "code_commit",
    "config_hash",
    "dataset_id",
    "dataset_hash",
    "experiment_id",
    "validation_status",
    "created_at",
    "promotion_status",
)

VALID_VALIDATION_STATUSES = ("pending", "passed", "failed")
VALID_PROMOTION_STATUSES = ("draft", "candidate", "promoted", "retired")


def _assert_no_secret_fields(data, path: str = "") -> None:
    """Recursively REJECT any secret-looking key, naming its path.

    Rejects rather than redacts: an artifact is a permanent provenance
    record, so a credential must never have been put there in the first
    place. (Log payloads differ -- see secrets.redact_secrets, which
    masks the value instead.)
    """
    if isinstance(data, dict):
        for key, value in data.items():
            lowered = str(key).lower()
            for marker in _SECRET_KEY_MARKERS:
                if marker in lowered:
                    raise ConfigurationError(
                        f"Artifact content contains a suspected secret field at {path}{key!r} "
                        f"(matched {marker!r}) -- secrets must never be included in artifacts."
                    )
            _assert_no_secret_fields(value, path=f"{path}{key}.")
    elif isinstance(data, (list, tuple)):
        for i, item in enumerate(data):
            _assert_no_secret_fields(item, path=f"{path}[{i}].")


def canonical_json(data) -> str:
    """Canonical JSON: lexical key ordering, no insignificant
    whitespace, NaN/Infinity rejected. Returns a str; callers hashing
    it must encode UTF-8 explicitly (see canonical_hash)."""
    try:
        return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False)
    except ValueError as e:
        raise ConfigurationError(
            f"Cannot canonically serialize artifact content: {e}. NaN/Infinity values are not "
            "permitted -- they are invalid JSON and not stably comparable."
        ) from e


def canonical_hash(data) -> str:
    """SHA-256 over the canonical UTF-8 JSON encoding of data."""
    _assert_no_secret_fields(data)
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def hash_config(config) -> str:
    """Configuration hash for a BacktestConfig (Task 6.1). Hashes the
    config's own to_dict() form, so two configs that round-trip to the
    same content hash identically regardless of construction path
    (programmatic vs YAML)."""
    return canonical_hash(config.to_dict())


def hash_dataset(df) -> str:
    """Dataset identity hash. Uses pandas' own row-wise hashing rather
    than a DataFrame repr (which truncates large frames and would make
    two genuinely different datasets hash identically)."""
    from pandas.util import hash_pandas_object

    row_hashes = hash_pandas_object(df, index=True).to_numpy()
    return hashlib.sha256(row_hashes.tobytes()).hexdigest()


@dataclass(frozen=True)
class DeploymentArtifact:
    """Immutable (frozen) provenance record. Every field is required
    except promotion_status/validation_status, which have explicit
    lifecycle defaults."""

    deployment_id: str
    strategy_id: str
    strategy_version: str
    code_commit: str
    config_hash: str
    dataset_id: str
    dataset_hash: str
    experiment_id: str
    created_at: str  # ISO 8601, UTC
    validation_status: str = "pending"
    promotion_status: str = "draft"

    @classmethod
    def create(
        cls,
        deployment_id: str,
        strategy_id: str,
        strategy_version: str,
        code_commit: str,
        config,
        dataset_id: str,
        dataset_hash: str,
        experiment_id: str,
        validation_status: str = "pending",
        promotion_status: str = "draft",
        created_at: Optional[str] = None,
    ) -> "DeploymentArtifact":
        """created_at defaults to now (UTC) -- pass it explicitly for a
        deterministic artifact, since a wall-clock timestamp would
        otherwise make two artifacts from identical inputs differ."""
        return cls(
            deployment_id=deployment_id,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            code_commit=code_commit,
            config_hash=hash_config(config),
            dataset_id=dataset_id,
            dataset_hash=dataset_hash,
            experiment_id=experiment_id,
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
            validation_status=validation_status,
            promotion_status=promotion_status,
        )

    def to_dict(self) -> dict:
        """Plain-dict form of this artifact, for hashing or storage."""
        return asdict(self)

    def canonical_hash(self) -> str:
        """This artifact's own identity hash."""
        return canonical_hash(self.to_dict())

    def validate(self) -> None:
        """Rejects an incomplete or malformed artifact. Called by
        assert_deployable() at live startup; also callable directly."""
        content = self.to_dict()
        missing = [f for f in REQUIRED_PROVENANCE_FIELDS if not content.get(f)]
        if missing:
            raise ConfigurationError(f"Artifact is missing required provenance field(s): {missing}")
        if self.validation_status not in VALID_VALIDATION_STATUSES:
            raise ConfigurationError(
                f"validation_status must be one of {VALID_VALIDATION_STATUSES}, got {self.validation_status!r}"
            )
        if self.promotion_status not in VALID_PROMOTION_STATUSES:
            raise ConfigurationError(
                f"promotion_status must be one of {VALID_PROMOTION_STATUSES}, got {self.promotion_status!r}"
            )
        _assert_no_secret_fields(content)


def assert_deployable(artifact: Optional[DeploymentArtifact]) -> None:
    """Live-startup gate (Task 6.3 step 3). Rejects a missing artifact,
    an incomplete one, or one that hasn't actually passed validation --
    'validation_status' being present but "failed"/"pending" is not
    deployable, which a pure presence check would have let through."""
    if artifact is None:
        raise ConfigurationError("Live startup requires a DeploymentArtifact; none was provided.")
    artifact.validate()
    if artifact.validation_status != "passed":
        raise ConfigurationError(
            f"Live startup requires validation_status='passed', got {artifact.validation_status!r}."
        )
    if artifact.promotion_status not in ("candidate", "promoted"):
        raise ConfigurationError(
            f"Live startup requires promotion_status 'candidate' or 'promoted', got {artifact.promotion_status!r}."
        )
