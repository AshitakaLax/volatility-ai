import pytest

from src.artifact import DeploymentArtifact, canonical_hash, create_artifact, validate_live_artifact
from src.exceptions import ConfigurationError


def artifact_kwargs():
    return dict(
        deployment_id="dep-001",
        strategy_id="grid",
        strategy_version="1.0.0",
        code_commit="abc123",
        configuration_hash="cfg123",
        dataset_identity="prices-2024",
        dataset_hash="data123",
        experiment_id="exp-001",
        validation_status="passed",
        promotion_status="approved",
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_identical_inputs_have_identical_hashes():
    first = create_artifact(**artifact_kwargs())
    second = create_artifact(**artifact_kwargs())
    assert first.artifact_hash == second.artifact_hash
    assert first.to_json() == second.to_json()


def test_identity_changes_change_artifact_hash():
    first = create_artifact(**artifact_kwargs())
    changed = artifact_kwargs()
    changed["code_commit"] = "different"
    second = create_artifact(**changed)
    assert first.artifact_hash != second.artifact_hash


@pytest.mark.parametrize("field", [
    "deployment_id", "strategy_id", "strategy_version", "code_commit",
    "configuration_hash", "dataset_identity", "dataset_hash", "experiment_id",
    "validation_status", "created_at", "promotion_status",
])
def test_missing_required_provenance_rejected(field):
    values = artifact_kwargs()
    values[field] = ""
    artifact = DeploymentArtifact(**values)
    with pytest.raises(ConfigurationError):
        validate_live_artifact(artifact)


def test_nan_cannot_enter_canonical_artifact():
    with pytest.raises(ValueError):
        canonical_hash({"value": float("nan")})
