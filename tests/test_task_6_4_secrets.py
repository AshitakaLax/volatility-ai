import json

import pytest

from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.secrets import load_live_credentials, redact_secrets


def test_live_credentials_are_loaded_only_from_environment():
    credentials = load_live_credentials({"APCA_API_KEY_ID": "key-123", "APCA_API_SECRET_KEY": "secret-456"})
    assert credentials.api_key_id == "key-123"
    assert credentials.api_secret_key == "secret-456"
    assert "key-123" not in repr(credentials)
    assert "secret-456" not in repr(credentials)


def test_missing_live_credentials_fail_closed():
    with pytest.raises(ConfigurationError, match="APCA_API_KEY_ID"):
        load_live_credentials({"APCA_API_SECRET_KEY": "secret-456"})


def test_backtest_serialization_contains_no_secret_fields():
    config = BacktestConfig.from_dict({
        "strategy": {"strategy_id": "fixed", "strategy_params": {"api_key": "should-not-persist"}},
    })
    serialized = json.dumps(config.to_dict(), sort_keys=True)
    assert "should-not-persist" not in serialized
    assert "api_key" in serialized
    assert "REDACTED" in serialized


def test_redaction_removes_secret_values_from_nested_payloads():
    payload = {"broker": {"api_key": "abc", "api_secret": "xyz"}, "safe": "value"}
    redacted = redact_secrets(payload)
    assert redacted == {
        "broker": {"api_key": "***REDACTED***", "api_secret": "***REDACTED***"},
        "safe": "value",
    }
    assert "abc" not in json.dumps(redacted)
    assert "xyz" not in json.dumps(redacted)
