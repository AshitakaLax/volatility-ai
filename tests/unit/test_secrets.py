import pytest

from src.exceptions import ConfigurationError
from src.secrets import LiveCredentials, load_live_credentials


def test_loads_both_credentials_when_present(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "my-key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "my-secret")
    creds = load_live_credentials()
    assert isinstance(creds, LiveCredentials)
    assert creds.api_key_id == "my-key"
    assert creds.api_secret_key == "my-secret"


def test_raises_when_both_missing(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="APCA_API_KEY_ID"):
        load_live_credentials()


def test_raises_when_only_key_id_missing(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.setenv("APCA_API_SECRET_KEY", "my-secret")
    with pytest.raises(ConfigurationError, match="APCA_API_KEY_ID"):
        load_live_credentials()


def test_raises_when_only_secret_missing(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "my-key")
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="APCA_API_SECRET_KEY"):
        load_live_credentials()


def test_raises_when_env_var_present_but_empty(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "my-secret")
    with pytest.raises(ConfigurationError):
        load_live_credentials()
