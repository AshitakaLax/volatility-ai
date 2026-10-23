"""fidelity_gateway/bridge/keys.py -- the API key in .env.

Every test uses a temporary env file. None reads the repository's real
.env, and none should: that file holds live credentials.
"""

from __future__ import annotations

import pytest

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.keys import (
    API_KEY_ENV_VAR,
    MIN_KEY_LENGTH,
    BridgeApiKey,
    default_env_file,
    generate_api_key,
    key_looks_valid,
    load_api_key,
    read_env_value,
    write_api_key,
)

GOOD = "a" * 20 + "B" * 20 + "_-9"


def test_the_environment_wins_over_the_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(f"{API_KEY_ENV_VAR}={'f' * 40}\n", encoding="utf-8")
    key = load_api_key(environ={API_KEY_ENV_VAR: GOOD}, env_file=env_file)
    assert key.value == GOOD


def test_the_file_is_read_when_the_environment_has_nothing(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(f"APCA_API_KEY_ID=other\n{API_KEY_ENV_VAR}={GOOD}\n", encoding="utf-8")
    assert load_api_key(environ={}, env_file=env_file).value == GOOD


def test_a_missing_key_names_the_variable_and_the_fix(tmp_path):
    with pytest.raises(ConfigurationError) as caught:
        load_api_key(environ={}, env_file=tmp_path / "absent.env")
    message = str(caught.value)
    assert API_KEY_ENV_VAR in message and "keygen" in message


def test_an_unusable_key_is_refused_without_being_quoted(tmp_path):
    bad = "short key with spaces"
    with pytest.raises(ConfigurationError) as caught:
        load_api_key(environ={API_KEY_ENV_VAR: bad}, env_file=tmp_path / "absent.env")
    assert bad not in str(caught.value)


def test_the_key_never_appears_in_a_repr_or_str():
    key = BridgeApiKey(GOOD)
    assert GOOD not in repr(key) and GOOD not in str(key) and GOOD not in f"{key}"


@pytest.mark.parametrize(
    "line,expected",
    [
        (f"{API_KEY_ENV_VAR}={GOOD}", GOOD),
        (f'{API_KEY_ENV_VAR}="{GOOD}"', GOOD),
        (f"{API_KEY_ENV_VAR}='{GOOD}'", GOOD),
        (f"export {API_KEY_ENV_VAR}={GOOD}", GOOD),
        (f"  {API_KEY_ENV_VAR} = {GOOD}  ", GOOD),
        (f"{API_KEY_ENV_VAR}={GOOD} # the bridge", GOOD),
        (f"# {API_KEY_ENV_VAR}={GOOD}", None),
        (f"OTHER_{API_KEY_ENV_VAR}={GOOD}", None),
    ],
)
def test_the_env_file_reader_handles_hand_edited_lines(tmp_path, line, expected):
    env_file = tmp_path / ".env"
    env_file.write_text(f"# comment\n\n{line}\n", encoding="utf-8")
    assert read_env_value(env_file, API_KEY_ENV_VAR) == expected


def test_the_last_assignment_wins(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"{API_KEY_ENV_VAR}={'x' * 40}\n{API_KEY_ENV_VAR}={GOOD}\n", encoding="utf-8"
    )
    assert read_env_value(env_file, API_KEY_ENV_VAR) == GOOD


def test_generated_keys_are_valid_and_unique():
    keys = {generate_api_key() for _ in range(20)}
    assert len(keys) == 20
    assert all(key_looks_valid(key) and len(key) >= MIN_KEY_LENGTH for key in keys)


@pytest.mark.parametrize(
    "candidate,ok",
    [
        ("a" * 32, True),
        ("a" * 31, False),
        ("a" * 256, True),
        ("a" * 257, False),
        ("a" * 31 + " ", False),
        (None, False),
    ],
)
def test_the_key_alphabet_matches_the_extensions(candidate, ok):
    assert key_looks_valid(candidate) is ok


def test_write_appends_to_an_existing_file_without_touching_it(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APCA_API_KEY_ID=keep-me", encoding="utf-8")  # no trailing newline
    key = write_api_key(env_file)
    text = env_file.read_text(encoding="utf-8")
    assert text == f"APCA_API_KEY_ID=keep-me\n{API_KEY_ENV_VAR}={key}\n"
    assert load_api_key(environ={}, env_file=env_file).value == key


def test_write_creates_the_file(tmp_path):
    env_file = tmp_path / ".env"
    key = write_api_key(env_file, GOOD)
    assert key == GOOD
    assert env_file.read_text(encoding="utf-8") == f"{API_KEY_ENV_VAR}={GOOD}\n"


def test_write_refuses_to_replace_a_key(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(f"{API_KEY_ENV_VAR}={GOOD}\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="already defines"):
        write_api_key(env_file)
    assert env_file.read_text(encoding="utf-8") == f"{API_KEY_ENV_VAR}={GOOD}\n"


def test_write_refuses_a_key_the_extension_would_reject(tmp_path):
    with pytest.raises(ConfigurationError):
        write_api_key(tmp_path / ".env", "too short")


def test_the_default_env_file_is_the_repositorys():
    assert default_env_file().name == ".env"
    assert (default_env_file().parent / "cli.py").is_file()
