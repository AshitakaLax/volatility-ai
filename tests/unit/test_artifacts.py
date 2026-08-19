"""
Task 6.3 acceptance tests.

1. Two artifacts generated from identical inputs have identical
   canonical hashes.
2. Changing code/config/data identity changes the artifact identity.
3. Live startup cannot proceed with missing required provenance
   fields.

Cross-process hash stability (an explicit part of the canonical hash
contract) is verified by an actual subprocess test below with
PYTHONHASHSEED randomized -- confirmed identical across 3 separate
processes in the chat this test was produced in before being written.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pandas as pd
import pytest

from src.artifacts import (
    DeploymentArtifact,
    assert_deployable,
    canonical_hash,
    canonical_json,
    hash_config,
    hash_dataset,
)
from src.config import BacktestConfig
from src.exceptions import ConfigurationError

REPO_ROOT = Path(__file__).resolve().parents[2]


def _config(allocation_pct: float = 0.05) -> BacktestConfig:
    return BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": "fixed",
                "strategy_params": {"allocation_pct": allocation_pct},
            },
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
        }
    )


def _artifact(**overrides) -> DeploymentArtifact:
    base = dict(
        deployment_id="d1",
        strategy_id="fixed",
        strategy_version="1.0.0",
        code_commit="abc123",
        config=_config(),
        dataset_id="TQQQ",
        dataset_hash="datasethash",
        experiment_id="exp1",
        created_at="2024-01-01T00:00:00+00:00",
    )
    base.update(overrides)
    return DeploymentArtifact.create(**base)


def test_canonical_json_is_key_order_independent():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})


def test_canonical_json_has_no_insignificant_whitespace():
    assert canonical_json({"a": 1, "b": 2}) == '{"a":1,"b":2}'


def test_canonical_hash_rejects_nan_and_infinity():
    with pytest.raises(ConfigurationError, match="NaN"):
        canonical_hash({"x": float("nan")})
    with pytest.raises(ConfigurationError):
        canonical_hash({"x": float("inf")})


def test_canonical_hash_rejects_secret_fields():
    for key in ("api_key", "APIKey", "password", "auth_token", "my_secret", "private_key"):
        with pytest.raises(ConfigurationError, match="secret"):
            canonical_hash({key: "value"})


def test_canonical_hash_rejects_nested_secret_fields():
    with pytest.raises(ConfigurationError, match="secret"):
        canonical_hash({"outer": {"inner": {"api_key": "sk-123"}}})


def test_hash_config_stable_and_construction_path_independent():
    from_dict_config = _config()
    yaml_config = BacktestConfig.from_yaml(
        textwrap.dedent(
            """
            strategy:
              strategy_id: fixed
              strategy_params:
                allocation_pct: 0.05
            grid:
              steps: [0.01]
              profit_targets: [0.005]
            """
        ),
        is_path=False,
    )
    assert hash_config(from_dict_config) == hash_config(yaml_config)


def test_config_to_dict_round_trips():
    config = _config()
    assert BacktestConfig.from_dict(config.to_dict()) == config


def test_hash_dataset_stable_and_content_sensitive():
    df = pd.read_csv(
        REPO_ROOT / "tests" / "fixtures" / "regression_ohlcv.csv", parse_dates=["timestamp"]
    ).set_index("timestamp")
    assert hash_dataset(df) == hash_dataset(df)
    modified = df.copy()
    modified.iloc[0, modified.columns.get_loc("close")] += 0.01
    assert hash_dataset(df) != hash_dataset(modified)


def test_identical_inputs_produce_identical_artifact_hashes():
    assert _artifact().canonical_hash() == _artifact().canonical_hash()


def test_artifact_hash_stable_across_processes():
    script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(REPO_ROOT)!r})
        from src.config import BacktestConfig
        from src.artifacts import DeploymentArtifact
        config = BacktestConfig.from_dict({{
            "strategy": {{"strategy_id": "fixed", "strategy_params": {{"allocation_pct": 0.05}}}},
            "grid": {{"steps": [0.01], "profit_targets": [0.005]}},
        }})
        a = DeploymentArtifact.create(
            deployment_id="d1", strategy_id="fixed", strategy_version="1.0.0",
            code_commit="abc123", config=config, dataset_id="TQQQ",
            dataset_hash="datasethash", experiment_id="exp1",
            created_at="2024-01-01T00:00:00+00:00")
        print(a.canonical_hash())
        """
    )
    hashes = []
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=60,
            env={"PYTHONHASHSEED": "random", "PATH": "/usr/bin:/bin"},
        )
        assert result.returncode == 0, result.stderr
        hashes.append(result.stdout.strip())
    assert hashes[0] == hashes[1] == _artifact().canonical_hash()


@pytest.mark.parametrize(
    "overrides",
    [
        {"code_commit": "different"},
        {"config": _config(allocation_pct=0.09)},
        {"dataset_hash": "different"},
        {"dataset_id": "SPXL"},
        {"strategy_version": "2.0.0"},
        {"experiment_id": "exp2"},
        {"deployment_id": "d2"},
        {"created_at": "2025-01-01T00:00:00+00:00"},
    ],
)
def test_changing_any_identity_component_changes_the_artifact_hash(overrides):
    assert _artifact().canonical_hash() != _artifact(**overrides).canonical_hash()


def test_live_startup_rejects_missing_artifact():
    with pytest.raises(ConfigurationError, match="requires a DeploymentArtifact"):
        assert_deployable(None)


@pytest.mark.parametrize(
    "field_name",
    ["deployment_id", "strategy_id", "strategy_version", "code_commit", "experiment_id"],
)
def test_live_startup_rejects_missing_required_provenance_field(field_name):
    artifact = _artifact(validation_status="passed", promotion_status="promoted")
    incomplete = DeploymentArtifact(**{**artifact.to_dict(), field_name: ""})
    with pytest.raises(ConfigurationError, match="missing required provenance"):
        assert_deployable(incomplete)


def test_live_startup_rejects_unvalidated_artifact():
    # Present-but-not-passed must be rejected -- a pure presence check
    # would wrongly let this through.
    with pytest.raises(ConfigurationError, match="validation_status"):
        assert_deployable(_artifact(validation_status="pending", promotion_status="promoted"))
    with pytest.raises(ConfigurationError, match="validation_status"):
        assert_deployable(_artifact(validation_status="failed", promotion_status="promoted"))


def test_live_startup_rejects_unpromoted_artifact():
    with pytest.raises(ConfigurationError, match="promotion_status"):
        assert_deployable(_artifact(validation_status="passed", promotion_status="draft"))


def test_live_startup_accepts_fully_valid_artifact():
    assert_deployable(_artifact(validation_status="passed", promotion_status="promoted"))
    assert_deployable(_artifact(validation_status="passed", promotion_status="candidate"))


def test_invalid_status_values_rejected():
    with pytest.raises(ConfigurationError):
        _artifact(validation_status="bogus").validate()
    with pytest.raises(ConfigurationError):
        _artifact(promotion_status="bogus").validate()


def test_artifact_is_immutable():
    import dataclasses

    artifact = _artifact()
    with pytest.raises(dataclasses.FrozenInstanceError):
        artifact.code_commit = "tampered"
