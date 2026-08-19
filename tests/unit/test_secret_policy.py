"""
Task 6.4 acceptance tests.

1. No secret value appears in serialized config, experiment artifacts,
   logs, or error messages.
2. Live startup fails clearly when required credentials are absent
   rather than silently falling back to simulation.
"""

import json

import pytest

from src.artifacts import DeploymentArtifact, canonical_hash
from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.secrets import (
    API_KEY_ID_ENV_VAR,
    API_SECRET_KEY_ENV_VAR,
    REDACTED,
    LiveCredentials,
    load_live_credentials,
    redact_secrets,
)

SECRET_KEY = "PKTEST_LEAKCANARY_KEYID"
SECRET_VALUE = "sk-LEAKCANARY-supersecret"


@pytest.mark.parametrize(
    "to_string",
    [
        repr,
        str,
        lambda c: f"{c}",
        lambda c: "%s" % c,  # noqa: UP031 -- %-format is the code path under test
        lambda c: "{}".format(c),  # noqa: UP032 -- .format() is likewise under test
    ],
)
def test_credentials_redacted_in_every_string_conversion(to_string):
    creds = LiveCredentials(api_key_id=SECRET_KEY, api_secret_key=SECRET_VALUE)
    rendered = to_string(creds)
    assert SECRET_KEY not in rendered
    assert SECRET_VALUE not in rendered
    assert REDACTED in rendered


def test_credentials_still_readable_via_attributes():
    # Redaction must not make the real values unusable -- only unloggable.
    creds = LiveCredentials(api_key_id=SECRET_KEY, api_secret_key=SECRET_VALUE)
    assert creds.api_key_id == SECRET_KEY
    assert creds.api_secret_key == SECRET_VALUE


def test_credentials_do_not_leak_through_a_log_record(caplog):
    import logging

    creds = LiveCredentials(api_key_id=SECRET_KEY, api_secret_key=SECRET_VALUE)
    logger = logging.getLogger("Optimizer")
    with caplog.at_level("INFO", logger="Optimizer"):
        logger.info("connecting with %s", creds)
    combined = " ".join(r.getMessage() for r in caplog.records)
    assert SECRET_KEY not in combined and SECRET_VALUE not in combined


def test_credentials_do_not_leak_through_a_traceback():
    import traceback

    creds = LiveCredentials(api_key_id=SECRET_KEY, api_secret_key=SECRET_VALUE)
    try:
        raise RuntimeError(f"broker failure with {creds}")
    except RuntimeError:
        tb = traceback.format_exc()
    assert SECRET_KEY not in tb and SECRET_VALUE not in tb


def test_redact_secrets_masks_nested_and_listed_secret_keys():
    payload = {
        "symbol": "TQQQ",
        "api_key": SECRET_VALUE,
        "nested": {"auth_token": SECRET_VALUE, "safe_value": 42},
        "items": [{"password": SECRET_VALUE}, {"ok": 1}],
    }
    redacted = redact_secrets(payload)
    serialized = json.dumps(redacted)
    assert SECRET_VALUE not in serialized
    assert redacted["symbol"] == "TQQQ"
    assert redacted["nested"]["safe_value"] == 42
    assert redacted["items"][1]["ok"] == 1


def test_redact_secrets_does_not_mutate_the_original():
    payload = {"api_key": SECRET_VALUE}
    redact_secrets(payload)
    assert payload["api_key"] == SECRET_VALUE  # original untouched


def test_redact_secrets_is_case_insensitive():
    redacted = redact_secrets({"API_KEY": SECRET_VALUE, "Api_Secret_Key": SECRET_VALUE})
    assert all(v == REDACTED for v in redacted.values())


def test_serialized_config_contains_no_credentials():
    # BacktestConfig has no credential fields at all by design -- this
    # asserts that structurally, so a future field addition that broke
    # it would fail here.
    config = BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "live": {"enabled": True, "paper_trading": True},
        }
    )
    serialized = json.dumps(config.to_dict())
    for marker in ("api_key", "secret", "password", "token", "credential"):
        assert marker not in serialized.lower(), f"Serialized config contains a {marker!r} field"


def test_artifact_rejects_any_secret_bearing_content():
    config = BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
        }
    )
    artifact = DeploymentArtifact.create(
        deployment_id="d1",
        strategy_id="fixed",
        strategy_version="1.0.0",
        code_commit="abc",
        config=config,
        dataset_id="TQQQ",
        dataset_hash="h",
        experiment_id="e1",
        created_at="2024-01-01T00:00:00+00:00",
    )
    serialized = json.dumps(artifact.to_dict())
    assert SECRET_VALUE not in serialized
    for marker in ("api_key", "password", "token", "credential"):
        assert marker not in serialized.lower()

    # And a secret smuggled in via strategy_params is rejected outright.
    with pytest.raises(ConfigurationError, match="secret"):
        canonical_hash({"strategy_params": {"api_key": SECRET_VALUE}})


@pytest.mark.parametrize(
    "present,missing",
    [
        ({}, [API_KEY_ID_ENV_VAR, API_SECRET_KEY_ENV_VAR]),
        ({API_KEY_ID_ENV_VAR: "k"}, [API_SECRET_KEY_ENV_VAR]),
        ({API_SECRET_KEY_ENV_VAR: "s"}, [API_KEY_ID_ENV_VAR]),
    ],
)
def test_live_startup_fails_clearly_when_credentials_absent(monkeypatch, present, missing):
    monkeypatch.delenv(API_KEY_ID_ENV_VAR, raising=False)
    monkeypatch.delenv(API_SECRET_KEY_ENV_VAR, raising=False)
    for key, value in present.items():
        monkeypatch.setenv(key, value)

    with pytest.raises(ConfigurationError) as exc_info:
        load_live_credentials()
    message = str(exc_info.value)
    for name in missing:
        assert name in message, f"Error should name the missing variable {name}"


def test_credential_error_message_never_contains_a_partial_secret(monkeypatch):
    # Present-but-empty: the error must name the VARIABLE, never echo
    # any value (even a partial one) back into the message.
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, SECRET_VALUE)
    with pytest.raises(ConfigurationError) as exc_info:
        load_live_credentials()
    assert SECRET_VALUE not in str(exc_info.value)


def test_missing_credentials_do_not_silently_fall_back(monkeypatch):
    # The failure must be an exception, not a None/default return that
    # a caller could mistake for "simulation mode is fine".
    monkeypatch.delenv(API_KEY_ID_ENV_VAR, raising=False)
    monkeypatch.delenv(API_SECRET_KEY_ENV_VAR, raising=False)
    with pytest.raises(ConfigurationError):
        load_live_credentials()
