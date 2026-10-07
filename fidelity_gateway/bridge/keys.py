"""
The API key shared by the engine and the Fidelity Bridge extension.

The engine reads FIDELITY_BRIDGE_API_KEY from its environment, or failing
that from the repository's .env -- the same file docker compose hands to
the containers, so one entry serves both ways of running. You paste the
same key into the extension's welcome form.

It follows engine/core/secrets.py's policy:
  * never on the command line (no flag accepts it),
  * never in a log line or exception message (BridgeApiKey's repr is
    redacted, and no error quotes a value),
  * never in configuration files that are committed (.env is ignored).

`python -m fidelity_gateway.bridge keygen` makes one and appends it to
.env, refusing if the file already has one: replacing a key silently
would disconnect the extension, which still holds the old one, with
nothing to say why.
"""

from __future__ import annotations

import contextlib
import os
import re
import secrets
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from engine.core.exceptions import ConfigurationError
from engine.core.secrets import REDACTED

API_KEY_ENV_VAR = "FIDELITY_BRIDGE_API_KEY"
MIN_KEY_LENGTH = 32
MAX_KEY_LENGTH = 256

# The extension accepts exactly this alphabet and length range
# (src/lib/settings.js); keep the two the same or a key valid here is
# refused there. 32 and 256 are MIN_KEY_LENGTH and MAX_KEY_LENGTH.
_KEY_PATTERN = re.compile(r"[A-Za-z0-9._~+/=-]{32,256}")
_ASSIGNMENT = re.compile(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)")


@dataclass(frozen=True)
class BridgeApiKey:
    """The key, redacted everywhere it might be printed."""

    value: str = field(repr=False)

    def __repr__(self) -> str:
        return f"BridgeApiKey({REDACTED})"

    __str__ = __repr__


def default_env_file() -> Path:
    """The repository's .env, wherever the command is run from."""
    return Path(__file__).resolve().parents[2] / ".env"


def read_env_value(path: Path, name: str) -> str | None:
    """One variable's value from a dotenv-style file, or None.

    Understands what a hand-edited .env contains: blank lines, # comments,
    an optional `export`, and single- or double-quoted values. Looks only
    at the named variable -- nothing else in the file is parsed into
    memory as a value.
    """
    if not path.is_file():
        return None
    found = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _ASSIGNMENT.fullmatch(line)
        if match is None or match.group(1) != name:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        found = value
    return found


def key_looks_valid(value: object) -> bool:
    return isinstance(value, str) and _KEY_PATTERN.fullmatch(value) is not None


def load_api_key(
    *, environ: Mapping[str, str] | None = None, env_file: Path | None = None
) -> BridgeApiKey:
    """The key, from the environment first and the .env file second.

    Raises ConfigurationError naming the variable -- never a value -- when
    it is missing or unusable.
    """
    environ = os.environ if environ is None else environ
    path = env_file or default_env_file()
    value = environ.get(API_KEY_ENV_VAR)
    source = "the environment"
    if not value:
        value = read_env_value(path, API_KEY_ENV_VAR)
        source = str(path)
    if not value:
        raise ConfigurationError(
            f"{API_KEY_ENV_VAR} is not set, in the environment or in {path}. Run "
            "`python -m fidelity_gateway.bridge keygen` to create one there, then paste "
            "the key it prints into the extension's settings."
        )
    if not key_looks_valid(value):
        raise ConfigurationError(
            f"{API_KEY_ENV_VAR} from {source} is not a usable key: it must be "
            f"{MIN_KEY_LENGTH}-{MAX_KEY_LENGTH} characters of letters, digits and ._~+/=- "
            "with no spaces. `python -m fidelity_gateway.bridge keygen --print-only` "
            "makes a fresh one."
        )
    return BridgeApiKey(value)


def generate_api_key() -> str:
    """32 random bytes, URL-safe base64: 43 characters."""
    return secrets.token_urlsafe(32)


def write_api_key(path: Path, key: str | None = None) -> str:
    """Append a new key to the env file and return it.

    Refuses when the file already defines one. A new file is created
    readable by this user only, where the platform supports that.
    """
    if read_env_value(path, API_KEY_ENV_VAR):
        raise ConfigurationError(
            f"{path} already defines {API_KEY_ENV_VAR}. Replacing it would disconnect the "
            "extension, which still holds the old key. To rotate it, delete that line, "
            "run keygen again, and paste the new key into the extension."
        )
    key = key or generate_api_key()
    if not key_looks_valid(key):
        raise ConfigurationError("Refusing to write a key the extension would not accept.")
    existed = path.exists()
    text = path.read_text(encoding="utf-8") if existed else ""
    separator = "" if not text or text.endswith("\n") else "\n"
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{separator}{API_KEY_ENV_VAR}={key}\n")
    if not existed:
        with contextlib.suppress(OSError):
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return key
