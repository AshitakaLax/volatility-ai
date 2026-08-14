"""Runtime secret loading and redaction helpers.

Secrets intentionally live outside BacktestConfig and experiment artifacts.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.exceptions import ConfigurationError

SECRET_ENV_VARS = ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY")
_SECRET_KEY_RE = re.compile(
    r"(?:api[_-]?key|api[_-]?secret|secret[_-]?key|access[_-]?token|password|token)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LiveCredentials:
    """Runtime-only Alpaca credentials; never serialized as configuration."""

    api_key_id: str
    api_secret_key: str

    def __repr__(self) -> str:
        return "LiveCredentials(api_key_id='***', api_secret_key='***')"


def load_live_credentials(environ: Mapping[str, str] | None = None) -> LiveCredentials:
    """Load required Alpaca credentials from the environment, failing closed."""
    env = os.environ if environ is None else environ
    key = env.get("APCA_API_KEY_ID")
    secret = env.get("APCA_API_SECRET_KEY")
    missing = [name for name in SECRET_ENV_VARS if not env.get(name)]
    if missing:
        raise ConfigurationError(
            f"missing required live credential environment variable(s): {', '.join(missing)}"
        )
    return LiveCredentials(api_key_id=key, api_secret_key=secret)


def redact_secrets(value: Any) -> Any:
    """Return a recursively redacted copy suitable for logs and artifacts."""
    if isinstance(value, Mapping):
        return {
            key: "***REDACTED***" if _SECRET_KEY_RE.search(str(key)) else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    return value
