"""The bridge host's notifications for apps: host.py running the listener
the Notifier app connects to, and saying what only it knows.

A real BridgeHost on 127.0.0.1 (ephemeral ports), a real Unix socket, a real
NotificationServer; the extension is bridge_support.FakeExtension, the app
FakeApp, an attached trader the real AttachedBridge. The host's ticks are
called by the test, on its own clock -- nothing here waits for a timer.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import tempfile
from pathlib import Path

import pytest

from engine.core.config import FidelityNotificationsConfig
from engine.core.exceptions import ConfigurationError
from engine.trading.control_inbox import ControlInbox
from fidelity_gateway.bridge.attach import AttachedBridge
from fidelity_gateway.bridge.host import BIND_RETRY_SECONDS, BridgeHost
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import BridgeApiKey
from fidelity_gateway.bridge.notifications import READINESS_GRACE_SECONDS, Notifications
from fidelity_gateway.bridge.notify_server import NotificationServer
from fidelity_gateway.tests.bridge_support import NOTIFY_KEY, FakeApp, FakeExtension
from fidelity_gateway.tests.test_bridge_host import Clock, _fidelity, _make_server

pytest.importorskip("websockets")

APPS = FidelityNotificationsConfig(enabled=True, port=0, allowed_clients=("127.0.0.1",))


def _with_apps(fidelity, notifications=APPS):
    return dataclasses.replace(
        fidelity, bridge=dataclasses.replace(fidelity.bridge, notifications=notifications)
    )


class Config:
    """What the host's settings() returns, changed by the test."""

    def __init__(self) -> None:
        self.fidelity = _with_apps(_fidelity())

    def __call__(self):
        return self.fidelity, "RSP"


class Notifiers:
    """The host's make_notifier: real listeners, or a refusal while `fail`
    says so (a key not yet in .env)."""

    def __init__(self) -> None:
        self.fail: str | None = None
        self.made: list[NotificationServer] = []

    def __call__(self, settings, notifications) -> NotificationServer:
        if self.fail:
            raise ConfigurationError(self.fail)
        notifier = NotificationServer(
            BridgeApiKey(NOTIFY_KEY),
            notifications,
            host=settings.host,
            port=settings.port,
            policy=AddressPolicy(list(settings.allowed_clients)),
            handshake_timeout=2.0,
        )
        self.made.append(notifier)
        return notifier


@pytest.fixture
def place():
    directory = Path(tempfile.mkdtemp(prefix="vai-notify-", dir="/tmp"))
    yield directory
    shutil.rmtree(directory, ignore_errors=True)


@pytest.fixture
def world(place):
    clock = Clock()
    config = Config()
    notifiers = Notifiers()
    host = BridgeHost(
        make_server=_make_server,
        settings=config,
        socket_path=place / "bridge.sock",
        inbox=ControlInbox(place / "control" / "bridge", clock=clock),
        deployment="fidelity",
        clock=clock,
        log=lambda _message: None,
        notifications=Notifications(clock=clock),
        make_notifier=notifiers,
    )
    host.open_socket()
    assert host.bind()
    host.start_notifier()
    yield host, clock, config, notifiers
    host.close()


def _app(host: BridgeHost, **handshake) -> FakeApp:
    app = FakeApp(host.notifier.url)
    assert app.handshake(**handshake)["type"] == "welcome"
    return app


def _extension(host: BridgeHost) -> FakeExtension:
    extension = FakeExtension(host.server.url)
    assert extension.handshake()["type"] == "welcome"
    assert host.server.wait_for_extension(5)
    return extension


def _events(place: Path) -> list[dict]:
    lines = []
    for path in sorted((place / "control" / "bridge").rglob("*.jsonl")):
        lines += [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return lines


def _attach(host: BridgeHost, process: str = "loop") -> AttachedBridge:
    return AttachedBridge.attach(host.socket_path, client={"process": process, "pid": 41})


# -- the listener belongs to the host ----------------------------------------------------


def test_an_app_connects_to_the_host_and_is_shown_its_readiness(world):
    host, _clock, _config, _notifiers = world
    app = _app(host)
    host.tick()
    status = app.receive_until(lambda m: m["type"] == "status" and "bridge" in m["status"])
    bridge = status["status"]["bridge"]
    assert bridge["ready"] is False and bridge["blocking"] == "extension"
    assert [item["id"] for item in bridge["items"]][:2] == ["bridge", "extension"]
    assert bridge["mode"] == "live" and bridge["symbol"] == "RSP"
    assert bridge["nextOpen"] and bridge["attached"] is None
    app.close()


def test_the_extension_arriving_reaches_an_app_through_the_host(world):
    host, *_ = world
    app = _app(host)
    extension = _extension(host)
    assert app.notification()["title"] == "Extension connected"
    extension.close()
    gone = app.notification()
    assert gone["kind"] == "disconnected"
    app.close()


def test_not_ready_is_said_after_the_grace(world):
    host, clock, *_ = world
    app = _app(host)
    host.tick()
    clock.now += READINESS_GRACE_SECONDS
    host.tick()
    said = app.notification()
    assert (said["kind"], said["title"]) == ("readiness", "Not ready to trade")
    assert said["data"]["blocking"] == "extension"
    app.close()


def test_the_checklist_is_not_resent_every_second(world):
    host, clock, *_ = world
    extension = _extension(host)
    host.tick()
    bridge_updates: list[dict] = []
    host.notifications.subscribe(
        lambda kind, status: kind == "status" and bridge_updates.append(status["bridge"])
    )
    for _ in range(10):  # "last heard N s ago" changes, nothing else does
        clock.now += 1
        host.tick()
    assert bridge_updates == []
    clock.now += 60
    host.tick()
    assert len(bridge_updates) == 1, "its wording is refreshed once a minute"
    extension.close()


# -- what only the host knows -------------------------------------------------------------


def test_a_second_trader_and_a_session_that_ends_without_stopping(world):
    host, *_ = world
    app = _app(host)
    extension = _extension(host)
    app.notification()  # connected
    first = _attach(host)
    second = None
    try:
        with pytest.raises(Exception, match="one process"):
            second = _attach(host, "check")
        refused = app.notification()
        assert (refused["kind"], refused["title"]) == ("session", "A second trader was turned away")
        first.set_engine_status({"mode": "live", "state": "running", "detail": "trading"})
        assert app.notification()["title"] == "Engine running"
    finally:
        first.stop()
        if second is not None:
            second.stop()
    ended = app.notification()
    assert (ended["kind"], ended["title"]) == ("session", "Trading session ended unexpectedly")
    assert "Its last report: running -- trading." in ended["body"]
    extension.close()
    app.close()


def test_a_session_that_says_it_stopped_ends_quietly(world):
    host, *_ = world
    app = _app(host)
    extension = _extension(host)
    app.notification()  # connected
    trader = _attach(host)
    trader.set_engine_status({"mode": "live", "state": "running", "detail": "trading"})
    trader.set_engine_status({"mode": "live", "state": "stopped", "detail": "the session ended"})
    assert app.notification()["title"] == "Engine running"
    assert app.notification()["title"] == "Engine stopped"
    trader.stop()
    host.tick()  # the host stands by again: mode "bridge", not an engine
    assert host.notifications.status["engine"] is None
    assert [n.kind for n in host.notifications.recent()] == ["connected", "engine", "engine"]
    extension.close()
    app.close()


def test_a_failed_account_check_is_said(world):
    host, *_ = world
    app = _app(host)
    result = host.run_check(by="10 min before the open")
    assert result["ok"] is False
    failed = app.notification()
    assert (failed["kind"], failed["title"]) == ("account_check", "Account check failed")
    assert "(10 min before the open)" in failed["body"]
    app.close()


# -- settings changes, and a listener that cannot start --------------------------------


def test_editing_only_the_notifications_restarts_their_listener_not_the_bridge(world):
    host, _clock, config, notifiers = world
    extension = _extension(host)
    app = _app(host)
    server, stream = host.server, host.notifications.stream
    config.fidelity = _with_apps(config.fidelity, dataclasses.replace(APPS, events=("buy", "sell")))
    assert host.reload() is False, "the extension's bridge did not restart"
    assert host.server is server and host.server.connected
    assert app.receive_until(lambda m: m["type"] == "goodbye")
    assert len(notifiers.made) == 2 and host.notifications.events == ("buy", "sell")
    again = _app(host)
    assert again.hello["stream"] == stream, "the same stream: nothing is replayed twice"
    again.close()
    extension.close()


def test_editing_the_bridge_keeps_the_apps_connected_and_says_so(world):
    host, _clock, config, _notifiers = world
    app = _app(host)
    server, stream = host.server, host.notifications.stream
    config.fidelity = dataclasses.replace(
        config.fidelity,
        bridge=dataclasses.replace(config.fidelity.bridge, allowed_clients=("127.0.0.1", "::1")),
    )
    assert host.reload() is True
    assert host.server is not server
    restarting = app.notification()
    assert (restarting["kind"], restarting["title"]) == ("bridge", "Bridge restarting")
    assert host.notifications.stream == stream
    extension = _extension(host)
    assert app.notification()["title"] == "Extension connected"
    extension.close()
    app.close()


def test_a_listener_that_cannot_start_never_stops_the_bridge_and_is_retried(world, place):
    host, clock, _config, notifiers = world
    host._stop_notifier("test")
    notifiers.fail = "FIDELITY_BRIDGE_NOTIFY_KEY is not set"
    host.start_notifier()
    assert host.notifier is None
    extension = _extension(host)  # the extension's bridge works regardless
    host.tick()
    assert any(
        e["kind"] == "notifications" and "could not start" in e["detail"] for e in _events(place)
    )
    notifiers.fail = None
    clock.now += BIND_RETRY_SECONDS
    host.tick()
    assert host.notifier is not None, "retried, and now it runs"
    extension.close()


def test_stopping_the_host_says_goodbye_to_apps(world):
    host, *_ = world
    app = _app(host)
    host.close()
    goodbye = app.receive_until(lambda m: m["type"] == "goodbye")
    assert "restart or a deploy" in goodbye["reason"]


def test_without_a_notifications_section_no_listener_runs(place):
    clock = Clock()
    notifiers = Notifiers()
    host = BridgeHost(
        make_server=_make_server,
        settings=lambda: (_fidelity(), "RSP"),
        socket_path=place / "bridge.sock",
        clock=clock,
        log=lambda _message: None,
        notifications=Notifications(clock=clock),
        make_notifier=notifiers,
    )
    host.open_socket()
    try:
        assert host.bind()
        host.start_notifier()
        assert host.notifier is None and notifiers.made == []
    finally:
        host.close()
