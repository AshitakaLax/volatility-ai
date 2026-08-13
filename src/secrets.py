"""
Live-broker credential loading.

Built to unblock src/live_execution.py, pushed directly to main
mid-session (from src.secrets import LiveCredentials,
load_live_credentials) -- see the chat this was produced in for the
full context. Neither file references any field on LiveCredentials
directly (it's only ever passed through as an opaque object to a
broker factory), so this module had full latitude on its exact shape;
api_key_id/api_secret_key follow Alpaca's own naming convention,
matching the env var names this reads.

Deliberately minimal: reading and validating presence of the two
required credentials, nothing about *using* them to actually talk to
a broker -- that's Phase 7's broker-adapter work, well outside this
module's scope, and not attempted here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from src.exceptions import ConfigurationError


@dataclass(frozen=True)
class LiveCredentials:
    api_key_id: str
    api_secret_key: str


def load_live_credentials() -> LiveCredentials:
    """Reads APCA_API_KEY_ID / APCA_API_SECRET_KEY from the environment
    -- Alpaca's own standard env var names. Raises ConfigurationError
    naming exactly which are missing if either is absent or empty,
    rather than returning a LiveCredentials with blank fields that
    would only fail later, confusingly, inside a real broker call."""
    api_key_id = os.environ.get("APCA_API_KEY_ID")
    api_secret_key = os.environ.get("APCA_API_SECRET_KEY")

    missing = [
        name
        for name, value in (("APCA_API_KEY_ID", api_key_id), ("APCA_API_SECRET_KEY", api_secret_key))
        if not value
    ]
    if missing:
        raise ConfigurationError(f"Missing required live-credential environment variable(s): {missing}")

    return LiveCredentials(api_key_id=api_key_id, api_secret_key=api_secret_key)
