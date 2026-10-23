"""python -m fidelity_gateway.bridge -- keygen, serve, check.

keygen is exercised against temporary env files only. serve and check run
against a real BridgeServer on an ephemeral port, with no browser and no
Fidelity: check's failure path is what is testable here, and its success
path is the one the extension interop test covers.
"""

from __future__ import annotations

import subprocess
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


def _fake_open_bridge(reports_sent, *, version="0.4.0", latest="0.4.0"):
    """open_bridge, standing in: a stub extension that already sent its
    order log (or not) and answers status and reads."""
    from fidelity_gateway.bridge.page import BridgePage
    from fidelity_gateway.tests.test_bridge_page import TRADE_URL, StubServer

    def answer(command, args):
        if command == "status":
            return {
                "extensionVersion": "0.2.0",
                "fidelityTab": {"url": TRADE_URL},
                "permissions": {"preview": False, "place": False},
            }
        return {"status": 200, "url": "", "body": "{}"}

    def open_bridge(**kwargs):
        server = StubServer(answer)
        server.extension = {"name": "fidelity-bridge-extension", "version": version}
        server.extension_versions = {"minimum": "0.3.0", "latest": latest}
        server.order_reports = kwargs["order_reports"]
        if reports_sent is not None:
            server.order_reports.note_all({"orders": reports_sent})
        server.stop = lambda: None
        server.push("request", {"url": TRADE_URL, "headers": {"x-csrf-token": "T"}})
        return server, BridgePage(server, settle_seconds=0)

    return open_bridge


def test_check_shows_what_the_extension_reports_about_its_orders(monkeypatch, capsys):
    report = {
        "id": "r1",
        "confNum": "2C50H6WV",
        "symbol": "TQQQ",
        "side": "buy",
        "qty": 1,
        "limitPrice": 69.3,
        "state": "filled",
        "filledQty": 1,
        "avgPrice": 69.25,
    }
    monkeypatch.setattr(cli, "open_bridge", _fake_open_bridge([report]))
    assert cli.main(["check", "--account", "999888777"]) == 0
    captured = capsys.readouterr()
    assert "orders the extension reports:" in captured.out
    line = next(line for line in captured.out.splitlines() if "2C50H6WV" in line)
    assert "BUY 1 TQQQ @ $69.30" in line and "filled" in line
    assert "The bridge works end to end." in captured.out
    assert "[bridge]" not in captured.err, "said once, in the summary, not per order"


def test_check_says_when_the_extension_sent_no_order_log(monkeypatch, capsys):
    monkeypatch.setattr(cli, "ORDER_LOG_WAIT_SECONDS", 0.01)
    monkeypatch.setattr(cli, "open_bridge", _fake_open_bridge(None))
    assert cli.main(["check", "--account", "999888777"]) == 0
    assert "sent no order log (an older version?)" in capsys.readouterr().out


def test_check_says_when_there_are_no_orders_yet(monkeypatch, capsys):
    monkeypatch.setattr(cli, "open_bridge", _fake_open_bridge([]))
    assert cli.main(["check", "--account", "999888777"]) == 0
    assert "orders the extension reports: none yet" in capsys.readouterr().out


def test_check_says_when_the_extension_needs_building_and_reloading(monkeypatch, capsys):
    monkeypatch.setattr(cli, "open_bridge", _fake_open_bridge([], version="0.3.0", latest="0.4.0"))
    assert cli.main(["check", "--account", "999888777"]) == 0
    out = capsys.readouterr().out
    assert "update: 0.4.0 is checked out beside the engine" in out


def test_check_says_nothing_about_an_up_to_date_extension(monkeypatch, capsys):
    monkeypatch.setattr(cli, "open_bridge", _fake_open_bridge([]))
    assert cli.main(["check", "--account", "999888777"]) == 0
    assert "update:" not in capsys.readouterr().out


# -- build-extension -----------------------------------------------------------


def _extension_source(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "build.mjs").write_text("// stand-in", encoding="utf-8")
    return tmp_path


def test_build_extension_runs_the_extensions_own_build(tmp_path, monkeypatch, capsys):
    root = _extension_source(tmp_path)
    ran = {}

    def run(command, **kwargs):
        ran["command"], ran["cwd"] = command, kwargs["cwd"]
        return subprocess.CompletedProcess(
            command, 0, stdout="Built Fidelity Bridge 0.4.0 -> x\n", stderr=""
        )

    monkeypatch.setattr(cli.subprocess, "run", run)
    args = cli.parse_args(["build-extension", "--node", "node-22"])
    assert cli.run_build_extension(args, root=root) == 0
    assert ran["command"] == ["node-22", str(root / "scripts" / "build.mjs")]
    assert ran["cwd"] == root
    out = capsys.readouterr().out
    assert "Built Fidelity Bridge 0.4.0" in out and "Reload now" in out


def test_build_extension_says_what_is_missing(tmp_path, monkeypatch, capsys):
    args = cli.parse_args(["build-extension"])
    assert cli.run_build_extension(args, root=tmp_path / "absent") == 2
    assert "git submodule update --init" in capsys.readouterr().err

    root = _extension_source(tmp_path)
    monkeypatch.setattr(cli.shutil, "which", lambda _name: None)
    assert cli.run_build_extension(args, root=root) == 2
    assert "Node 22" in capsys.readouterr().err


def test_a_failed_build_is_reported_not_hidden(tmp_path, monkeypatch, capsys):
    root = _extension_source(tmp_path)
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda command, **_kw: subprocess.CompletedProcess(
            command, 1, stdout="", stderr="manifest.json names x"
        ),
    )
    assert (
        cli.run_build_extension(cli.parse_args(["build-extension", "--node", "node"]), root=root)
        == 2
    )
    assert "manifest.json names x" in capsys.readouterr().err
