"""
Live-broker credential loading and redaction. Task 6.4.

Originally built narrower (credential loading only) to unblock
src/live_execution.py, pushed directly to main mid-session; extended
here with the secret-policy enforcement Task 6.4 requires.

Secret policy (implementation_task_specs.md Task 6.4): credentials
come from the environment using APCA_API_KEY_ID / APCA_API_SECRET_KEY
(this repo's already-established names -- confirmed in use by
live_execution.py's own tests before adopting them). Secrets are
forbidden in YAML/JSON configuration, command-line arguments, source
control, artifact snapshots, audit payloads, and exception/log
messages.

The last of those is the easiest to violate by accident, so it's
enforced structurally rather than by convention: LiveCredentials
overrides __repr__/__str__ so the raw values cannot reach a log line,
f-string, or traceback frame even when someone logs the object
directly. Before this, its auto-generated dataclass repr printed both
secrets in full -- verified concretely, not assumed.

This module does not implement the artifact/provenance hashing that
also touches secret policy -- that's Task 6.3's scope (already built,
src/artifacts.py, which independently rejects secret-looking keys).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from src.exceptions import ConfigurationError

API_KEY_ID_ENV_VAR = "APCA_API_KEY_ID"
API_SECRET_KEY_ENV_VAR = "APCA_API_SECRET_KEY"

REDACTED = "***REDACTED***"

# Substrings marking a key whose VALUE must be redacted before
# serialization. Matches src/artifacts.py's own marker list (which
# rejects such keys outright rather than redacting them) -- the two
# serve different purposes on the same threat.
SECRET_KEY_MARKERS = (
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "token",
    "credential",
    "private_key",
)


@dataclass(frozen=True)
class LiveCredentials:
    """Holds live-broker credentials. repr/str are redacted so the raw
    values never reach logs, f-strings, or traceback frames -- use the
    attributes explicitly when a real value is genuinely needed."""

    api_key_id: str = field(repr=False)
    api_secret_key: str = field(repr=False)

    def __repr__(self) -> str:
        """Redacted representation. __str__ is aliased to this, so no
        f-string, %-format, .format() call, log record, or traceback
        frame can expose the raw values."""
        return f"LiveCredentials(api_key_id={REDACTED}, api_secret_key={REDACTED})"

    __str__ = __repr__


def load_live_credentials() -> LiveCredentials:
    """Reads APCA_API_KEY_ID / APCA_API_SECRET_KEY from the environment.
    Raises ConfigurationError naming exactly which are missing (by env
    var NAME -- never a partial value) if either is absent or empty,
    rather than returning blank fields that would fail later inside a
    broker call, or silently falling back to simulation mode."""
    api_key_id = os.environ.get(API_KEY_ID_ENV_VAR)
    api_secret_key = os.environ.get(API_SECRET_KEY_ENV_VAR)

    missing = [
        name
        for name, value in (
            (API_KEY_ID_ENV_VAR, api_key_id),
            (API_SECRET_KEY_ENV_VAR, api_secret_key),
        )
        if not value
    ]
    if missing:
        raise ConfigurationError(
            f"Missing required live-credential environment variable(s): {missing}"
        )

    return LiveCredentials(api_key_id=api_key_id, api_secret_key=api_secret_key)


def redact_secrets(data):
    """Recursively returns a copy of data with any secret-looking key's
    VALUE replaced by REDACTED. Non-mutating -- the caller's original
    object is untouched, so redacting for a log line can't accidentally
    destroy the live values still in use.

    Complements src/artifacts.py's _assert_no_secret_fields, which
    rejects such keys outright: artifacts must never contain them at
    all, whereas a log payload may legitimately carry the key with its
    value masked."""
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in SECRET_KEY_MARKERS):
                redacted[key] = REDACTED
            else:
                redacted[key] = redact_secrets(value)
        return redacted
    if isinstance(data, list):
        return [redact_secrets(item) for item in data]
    if isinstance(data, tuple):
        return tuple(redact_secrets(item) for item in data)
    return data
