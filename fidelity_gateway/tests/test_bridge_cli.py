"""python -m fidelity_gateway.bridge -- keygen, serve, check.

keygen is exercised against temporary env files only. serve and check run
against a real BridgeServer on an ephemeral port, with no browser and no
Fidelity: check's failure path is what is testable here, and its success
path is the one the extension interop test covers.
"""

from __future__ import annotations

import threading
import time

import pytest

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge import __main__ as cli
from fidelity_gateway.bridge import open_bridge
from fidelity_gateway.bridge.keys import API_KEY_ENV_VAR, read_env_value
from fidelity_gateway.tests.bridge_support import API_KEY


def test_keygen_writes_the_key_once_and_prints_it(tmp_path, capsys):
    env_file = tmp_path / ".env"
    assert cli.main(["keygen", "--env-file", str(env_file)]) == 0
    key = read_env_value(env_file, API_KEY_ENV_VAR)
    assert key and key in capsys.readouterr().out
    assert cli.main(["keygen", "--env-file", str(env_file)]) == 2
    assert "already defines" in capsys.readouterr().err
    assert read_env_value(env_file, API_KEY_ENV_VAR) == key, "the first key is untouched"


def test_keygen_print_only_writes_nothing(tmp_path, capsys):
    env_file = tmp_path / ".env"
    assert cli.main(["keygen", "--print-only", "--env-file", str(env_file)]) == 0
    assert len(capsys.readouterr().out.strip()) >= 32
    assert not env_file.exists()


def test_no_flag_accepts_the_key_itself():
    """Secret policy: never on a command line, where shell history and
    process listings keep it."""
    for command in ("serve", "check"):
        argv = [command, "--account", "1"] if command == "check" else [command]
        args = cli.parse_args(argv)
        assert not any("key" in name for name in vars(args) if name != "command")


def test_server_flags_default_to_this_computer_only():
    args = cli.parse_args(["serve"])
    assert args.host == "127.0.0.1"
    assert args.port == 8765
    assert args.allow_client is None  # meaning 127.0.0.1 and ::1
    args = cli.parse_args(
        ["serve", "--allow-client", "172.16.0.50", "--allow-client", "172.16.0.0/24"]
    )
    assert args.allow_client == ["172.16.0.50", "172.16.0.0/24"]


def test_serve_refuses_to_start_without_a_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    assert cli.main(["serve", "--env-file", str(tmp_path / "none.env"), "--port", "0"]) == 2
    assert API_KEY_ENV_VAR in capsys.readouterr().err


def test_serve_refuses_a_host_name_in_the_allowlist(monkeypatch, capsys):
    monkeypatch.setenv(API_KEY_ENV_VAR, API_KEY)
    assert cli.main(["serve", "--port", "0", "--allow-client", "my-laptop"]) == 2
    assert "Host names are not accepted" in capsys.readouterr().err


def test_serve_runs_until_told_to_stop(monkeypatch):
    pytest.importorskip("websockets")
    monkeypatch.setenv(API_KEY_ENV_VAR, API_KEY)
    stop = threading.Event()
    args = cli.parse_args(["serve", "--port", "0"])
    finished = []
    runner = threading.Thread(
        target=lambda: finished.append(cli.run_serve(args, stop)), daemon=True
    )
    runner.start()
    time.sleep(0.3)
    assert runner.is_alive()
    stop.set()
    runner.join(timeout=5)
    assert finished == [0]


def test_open_bridge_says_what_to_check_when_no_extension_comes(monkeypatch):
    pytest.importorskip("websockets")
    monkeypatch.setenv(API_KEY_ENV_VAR, API_KEY)
    with pytest.raises(ConfigurationError) as caught:
        open_bridge(port=0, wait_seconds=0.2, log=lambda _m: None)
    message = str(caught.value)
    assert "did not connect" in message and API_KEY_ENV_VAR in message and "127.0.0.1" in message


def test_check_reports_a_missing_extension_without_a_traceback(monkeypatch, capsys):
    pytest.importorskip("websockets")
    monkeypatch.setenv(API_KEY_ENV_VAR, API_KEY)
    assert cli.main(["check", "--account", "999888777", "--port", "0", "--wait", "0.2"]) == 2
    assert "did not connect" in capsys.readouterr().err
