import pytest

from src.exceptions import ConfigurationError
from src.secrets import (
    REDACTED,
    FidelityCredentials,
    LiveCredentials,
    load_fidelity_credentials,
    load_live_credentials,
    redact_secrets,
)


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


# -- FidelityCredentials -----------------------------------------------


def _set_fidelity_env(monkeypatch, username="bob", password="hunter2", totp="SEED"):
    for name, value in (
        ("FIDELITY_USERNAME", username),
        ("FIDELITY_PASSWORD", password),
        ("FIDELITY_TOTP_SECRET", totp),
    ):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)


def test_loads_fidelity_credentials_when_present(monkeypatch):
    _set_fidelity_env(monkeypatch)
    creds = load_fidelity_credentials()
    assert isinstance(creds, FidelityCredentials)
    assert creds.username == "bob"
    assert creds.password == "hunter2"
    assert creds.totp_secret == "SEED"


def test_totp_is_optional(monkeypatch):
    """Optional so the recon harness can run against a device-trusted
    account; an UNATTENDED deployment still needs it, because the SMS
    path waits for an out-of-band code with no callback to supply one."""
    _set_fidelity_env(monkeypatch, totp=None)
    assert load_fidelity_credentials().totp_secret is None


def test_blank_totp_becomes_none_rather_than_empty_string(monkeypatch):
    """An empty secret_values entry would scrub every captured payload
    down to nothing -- `"" in payload` is always True."""
    _set_fidelity_env(monkeypatch, totp="")
    assert load_fidelity_credentials().totp_secret is None


def test_raises_when_fidelity_username_missing(monkeypatch):
    _set_fidelity_env(monkeypatch, username=None)
    with pytest.raises(ConfigurationError, match="FIDELITY_USERNAME"):
        load_fidelity_credentials()


def test_raises_when_fidelity_password_missing(monkeypatch):
    _set_fidelity_env(monkeypatch, password=None)
    with pytest.raises(ConfigurationError, match="FIDELITY_PASSWORD"):
        load_fidelity_credentials()


def test_fidelity_error_never_leaks_a_partial_value(monkeypatch):
    _set_fidelity_env(monkeypatch, password=None)
    with pytest.raises(ConfigurationError) as excinfo:
        load_fidelity_credentials()
    assert "bob" not in str(excinfo.value)


def test_fidelity_repr_and_str_are_redacted():
    """repr lands in logs and traceback frames verbatim."""
    creds = FidelityCredentials(username="bob", password="hunter2", totp_secret="SEED")
    for rendered in (repr(creds), str(creds), f"{creds}", f"{creds}"):
        assert "bob" not in rendered
        assert "hunter2" not in rendered
        assert "SEED" not in rendered
        assert REDACTED in rendered


def test_fidelity_credentials_in_a_container_repr_stay_redacted():
    """Dataclass fields are repr=False, so an enclosing structure's repr
    cannot expose them either."""
    creds = FidelityCredentials(username="bob", password="hunter2")
    assert "hunter2" not in repr({"creds": creds})
    assert "hunter2" not in repr([creds])


def test_secret_values_returns_the_raw_strings_for_scrubbing():
    creds = FidelityCredentials(username="bob", password="hunter2", totp_secret="SEED")
    assert creds.secret_values() == ["bob", "hunter2", "SEED"]


def test_secret_values_omits_a_missing_totp():
    creds = FidelityCredentials(username="bob", password="hunter2")
    assert creds.secret_values() == ["bob", "hunter2"]


def test_redact_secrets_masks_totp_secret_and_password_by_name():
    """SECRET_KEY_MARKERS already covers both -- asserted rather than
    assumed, since fidelity_capture depends on it."""
    payload = redact_secrets({"username": "bob", "password": "hunter2", "totp_secret": "SEED"})
    assert payload["password"] == REDACTED
    assert payload["totp_secret"] == REDACTED
    # An identifier, not a secret -- masking it would make a recon dump
    # unreadable for no security gain.
    assert payload["username"] == "bob"
