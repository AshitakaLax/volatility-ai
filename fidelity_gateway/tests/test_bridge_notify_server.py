"""bridge/notify_server.py, and the bridge feeding it, over real sockets.

A NotificationServer on 127.0.0.1 with an ephemeral port, driven by
bridge_support.FakeApp (the app's half in Python). The second half runs a
BridgeServer with that notifier and a FakeExtension, and checks what the
app hears as the extension connects, flips its switch, reports orders
and goes away. Nothing here touches Fidelity or a browser.
"""

from __future__ import annotations

import json
import time

import pytest

import fidelity_gateway.bridge.notify_server as notify_server
from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge import build_notifier
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import API_KEY_ENV_VAR, NOTIFY_KEY_ENV_VAR, BridgeApiKey
from fidelity_gateway.bridge.notifications import EVENT_KINDS, Notifications
from fidelity_gateway.bridge.notify_server import NotificationServer, NotifySettings
from fidelity_gateway.bridge.server import BridgeServer
from fidelity_gateway.tests.bridge_support import API_KEY, NOTIFY_KEY, FakeApp, FakeExtension

websockets = pytest.importorskip("websockets")
from websockets.exceptions import ConnectionClosed  # noqa: E402 -- only once known installed


def _notifier(logs: list[str], **kwargs) -> NotificationServer:
    return NotificationServer(
        BridgeApiKey(NOTIFY_KEY),
        kwargs.pop("hub", None) or Notifications(tuple(EVENT_KINDS), stream="s1"),
        host="127.0.0.1",
        port=0,
        policy=kwargs.pop("policy", AddressPolicy(["127.0.0.1"])),
        handshake_timeout=2.0,
        log=logs.append,
        **kwargs,
    )


@pytest.fixture
def notifier():
    logs: list[str] = []
    server = _notifier(logs)
    server.start()
    server.logs = logs
    yield server
    server.stop()


def _app(server, **handshake) -> FakeApp:
    app = FakeApp(server.url)
    assert app.handshake(**handshake)["type"] == "welcome"
    return app


def _wait_until(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def _upgrade_status(url: str, **kwargs) -> int | None:
    from websockets.exceptions import InvalidStatus
    from websockets.sync.client import connect

    try:
        with connect(url, proxy=None, open_timeout=5, **kwargs):
            return 101
    except InvalidStatus as exc:
        return exc.response.status_code


# -- getting in -----------------------------------------------------------------


def test_an_app_with_the_key_connects_and_is_told_the_stream_and_the_kinds(notifier):
    app = _app(notifier)
    assert app.hello["stream"] == "s1"
    assert app.hello["events"] == list(EVENT_KINDS)
    assert app.hello["protocol"] == "fidelity-bridge-notify/v1"
    assert _wait_until(lambda: notifier.app_count == 1)
    # Logged just after the app is counted, on the connection's own thread.
    assert _wait_until(
        lambda: any("fake-app 0.0.1 at 127.0.0.1 connected" in line for line in notifier.logs)
    )
    app.close()
    assert _wait_until(lambda: notifier.app_count == 0)


def test_a_wrong_key_is_denied(notifier):
    app = FakeApp(notifier.url, api_key="wrong-key-0123456789abcdefghijklmnopqrstuvw")
    assert app.handshake() == {"type": "denied", "reason": "bad_proof"}
    assert notifier.app_count == 0
    assert any("failed the API key check" in line for line in notifier.logs)
    app.close()


def test_the_extensions_key_does_not_open_this_door(notifier):
    app = FakeApp(notifier.url, api_key=API_KEY)
    assert app.handshake()["type"] == "denied"
    app.close()


def test_the_key_never_crosses_the_wire(notifier):
    app = FakeApp(notifier.url)
    frames: list[str] = []
    original_recv, original_send = app.ws.recv, app.ws.send
    app.ws.recv = lambda *a, **k: frames.append(original_recv(*a, **k)) or frames[-1]
    app.ws.send = lambda frame: frames.append(frame) or original_send(frame)
    app.handshake()
    assert frames and all(NOTIFY_KEY not in frame for frame in frames)
    app.close()


def test_an_address_outside_the_allowlist_is_refused_before_the_handshake():
    logs: list[str] = []
    server = _notifier(logs, policy=AddressPolicy(["192.0.2.0/24"]))
    server.start()
    try:
        assert _upgrade_status(server.url) == 403
        assert any("refused an app's connection" in line for line in logs)
    finally:
        server.stop()


def test_a_web_page_cannot_connect(notifier):
    assert _upgrade_status(notifier.url, origin="https://evil.example") == 403


def test_only_the_notifications_path_is_served(notifier):
    assert _upgrade_status(notifier.url.replace("/notifications", "/fidelity-bridge")) == 404


def test_one_app_too_many_is_turned_away():
    logs: list[str] = []
    server = _notifier(logs, max_apps=1)
    server.start()
    try:
        first = _app(server)
        second = FakeApp(server.url)
        assert second.handshake() == {"type": "denied", "reason": "too_many_apps"}
        first.close()
        second.close()
    finally:
        server.stop()


# -- what an app is sent --------------------------------------------------------------


def test_notifications_arrive_as_they_happen(notifier):
    app = _app(notifier)
    notifier.notifications.publish("sell", "Sold 3 TQQQ", "3 at $71.20", data={"qty": 3})
    sent = app.notification()
    assert (sent["id"], sent["kind"], sent["title"]) == (1, "sell", "Sold 3 TQQQ")
    assert sent["data"] == {"qty": 3}
    app.close()


def test_a_reconnecting_app_is_sent_what_it_missed_as_replays(notifier):
    hub = notifier.notifications
    for n in range(3):
        hub.publish("buy", f"n{n}", "")
    app = _app(notifier, since={"stream": "s1", "id": 1})
    first = app.receive()
    second = app.receive()
    assert [first["replay"], second["replay"]] == [True, True]
    assert [first["notification"]["id"], second["notification"]["id"]] == [2, 3]
    hub.publish("buy", "live", "")
    live = app.receive_until(lambda m: m["type"] == "notification")
    assert live["notification"]["id"] == 4 and "replay" not in live
    app.close()


def test_status_changes_are_sent(notifier):
    app = _app(notifier)
    notifier.notifications.update_status(engine={"state": "running"})
    message = app.receive_until(lambda m: m["type"] == "status")
    assert message["status"] == {"engine": {"state": "running"}}
    app.close()


def test_an_app_may_ask_for_a_test_notification_and_nothing_else(notifier):
    app = _app(notifier)
    app.send({"type": "place", "symbol": "TQQQ"})  # ignored: there is no such thing here
    app.send({"type": "test"})
    test = app.notification()
    assert (test["kind"], test["id"]) == ("test", 0)
    assert notifier.notifications.recent() == [], "a test is for that app alone, never kept"
    app.close()


def test_test_requests_are_rate_limited():
    logs: list[str] = []
    # One reading per test request, in the order they arrive: 1s apart,
    # then 9s later.
    readings = iter([100.0, 101.0, 110.0])
    server = _notifier(logs, clock=lambda: next(readings))
    server.start()
    try:
        app = _app(server)
        for _ in range(3):
            app.send({"type": "test"})
        assert app.notification()["kind"] == "test"
        assert app.notification()["kind"] == "test"
        server.notifications.publish("buy", "marker", "")
        assert app.notification()["kind"] == "buy", "the second request was refused"
        app.close()
    finally:
        server.stop()


def test_a_forged_frame_from_an_app_closes_its_connection(notifier):
    app = _app(notifier)
    sealed = app.channel.seal({"type": "test"})
    app.ws.send(json.dumps(dict(sealed, payload='{"type":"other"}')))
    with pytest.raises(ConnectionClosed):
        while True:
            app.ws.recv(timeout=5)
    assert any("dropped fake-app" in line for line in notifier.logs)


def test_an_app_that_falls_behind_is_let_go_to_catch_up(notifier, monkeypatch):
    app = _app(notifier)
    monkeypatch.setattr(notify_server, "APP_BACKLOG", 0)
    notifier.notifications.publish("buy", "lost in the queue", "")
    with pytest.raises(ConnectionClosed) as closed:
        while True:
            app.ws.recv(timeout=5)
    assert closed.value.rcvd.code == 1013
    assert any("fell behind" in line for line in notifier.logs)


def test_stopping_says_goodbye():
    logs: list[str] = []
    server = _notifier(logs)
    server.start()
    app = _app(server)
    server.stop()
    assert app.receive_until(lambda m: m["type"] == "goodbye")["reason"]
    with pytest.raises(ConnectionClosed):
        app.ws.recv(timeout=5)


# -- the bridge feeding it ----------------------------------------------------------


@pytest.fixture
def bridge():
    """A BridgeServer telling apps through a hub whose listener runs beside
    it -- as the bridge host and `serve --notify` run them."""
    logs: list[str] = []
    notifier = _notifier(logs)
    server = BridgeServer(
        BridgeApiKey(API_KEY),
        host="127.0.0.1",
        port=0,
        policy=AddressPolicy(["127.0.0.1"]),
        handshake_timeout=2.0,
        log=logs.append,
        notifications=notifier.notifications,
    )
    notifier.start()
    server.start()
    server.notifier = notifier
    yield server
    server.stop()
    notifier.stop()


def _extension(server) -> FakeExtension:
    extension = FakeExtension(server.url)
    assert extension.handshake()["type"] == "welcome"
    assert server.wait_for_extension(5)
    return extension


def test_an_app_first_sees_no_extension_and_no_engine(bridge):
    app = _app(bridge.notifier)
    assert app.hello["status"]["extension"]["connected"] is False
    assert app.hello["status"]["engine"] is None
    app.close()


def test_an_app_hears_the_extension_connect_go_away_and_come_back(bridge):
    app = _app(bridge.notifier)
    extension = _extension(bridge)
    connected = app.notification()
    assert connected["title"] == "Extension connected"
    assert "9.9.9" in connected["body"]
    extension.close()
    gone = app.notification()
    assert (gone["kind"], gone["severity"]) == ("disconnected", "warning")
    status = bridge.notifications.status
    assert status["extension"]["connected"] is False
    assert status["extension"]["disconnectedAt"]
    again = _extension(bridge)
    assert app.notification()["title"] == "Extension reconnected"
    again.close()
    app.close()


def test_the_status_an_app_sees_follows_the_extension_and_never_holds_the_key(bridge):
    app = _app(bridge.notifier)
    extension = _extension(bridge)
    extension.send({"type": "event", "event": "permissions", "data": {"preview": True}})
    message = app.receive_until(
        lambda m: m["type"] == "status" and m["status"]["extension"]["previews"] is True
    )
    assert message["status"]["extension"]["trading"] is False
    assert message["status"]["extension"]["version"] == "9.9.9"
    assert API_KEY not in json.dumps(message) and NOTIFY_KEY not in json.dumps(message)
    extension.close()
    app.close()


def test_the_trading_switch_is_news_only_when_it_changes(bridge):
    app = _app(bridge.notifier)
    extension = _extension(bridge)
    app.notification()  # connected
    # Its first word is how things are, not a change.
    extension.send({"type": "event", "event": "permissions", "data": {"place": True}})
    extension.send({"type": "event", "event": "permissions", "data": {"place": False}})
    switched = app.notification()
    assert switched["title"] == "Trading switched OFF"
    assert [n.kind for n in bridge.notifications.recent()] == ["connected", "trading_switch"]
    extension.close()
    app.close()


def test_an_order_report_becomes_a_buy_or_a_sell(bridge):
    app = _app(bridge.notifier)
    extension = _extension(bridge)
    app.notification()  # connected
    report = {
        "id": "r1",
        "confNum": "2C50H6WV",
        "symbol": "TQQQ",
        "side": "sell",
        "qty": 3,
        "limitPrice": 71.2,
        "state": "filled",
        "filledQty": 3,
        "avgPrice": 71.25,
        "attempts": 1,
        "placedAt": "2026-10-24T14:00:00.000Z",
        "updatedAt": "2026-10-24T14:00:01.000Z",
        "detail": "",
    }
    extension.send({"type": "event", "event": "order", "data": report})
    sold = app.notification()
    assert (sold["kind"], sold["title"]) == ("sell", "Sold 3 TQQQ")
    assert sold["data"]["confNum"] == "2C50H6WV"
    extension.close()
    app.close()


def test_the_engines_state_is_news_when_it_changes_not_at_every_tick(bridge):
    app = _app(bridge.notifier)
    bridge.set_engine_status({"state": "running", "detail": "trading", "lastTickAt": "t1"})
    bridge.set_engine_status({"state": "running", "detail": "trading", "lastTickAt": "t2"})
    bridge.set_engine_status({"state": "halted", "detail": "ambiguous order", "lastTickAt": "t3"})
    first, second = app.notification(), app.notification()
    assert (first["title"], second["title"]) == ("Engine running", "Engine HALTED")
    assert second["severity"] == "critical"
    assert [n.kind for n in bridge.notifications.recent()] == ["engine", "engine"]
    assert bridge.notifications.status["engine"]["lastTickAt"] == "t3"
    app.close()


def test_the_bridges_own_standby_status_is_not_an_engines(bridge):
    """Between sessions the bridge host stands in for the engine in the
    extension's popup (mode "bridge"); apps are not told an engine ran."""
    app = _app(bridge.notifier)
    bridge.set_engine_status({"mode": "bridge", "state": "running", "detail": "standing by"})
    bridge.set_engine_status({"mode": "bridge", "state": "paused", "detail": "not ready"})
    bridge.set_engine_status({"mode": "live", "state": "starting", "detail": "a session"})
    starting = app.notification()
    assert (starting["title"], starting["data"]["previous"]) == ("Engine starting", None)
    assert bridge.notifications.status["engine"]["mode"] == "live"
    bridge.set_engine_status({"mode": "bridge", "state": "running", "detail": "standing by"})
    assert bridge.notifications.status["engine"] is None
    assert [n.kind for n in bridge.notifications.recent()] == ["engine"]
    app.close()


def test_stopping_the_bridge_is_not_a_disconnection(bridge):
    app = _app(bridge.notifier)
    extension = _extension(bridge)
    app.notification()  # connected
    bridge.stop()
    bridge.notifier.stop()
    goodbye = app.receive_until(lambda m: m["type"] in ("goodbye", "notification"))
    assert goodbye["type"] == "goodbye"
    assert [n.kind for n in bridge.notifications.recent()] == ["connected"]
    extension.ws.close()


def test_a_sign_out_is_news_and_the_first_signed_in_report_is_not(bridge):
    signin = "https://digital.fidelity.com/prgw/digital/signin/retail"
    portfolio = "https://digital.fidelity.com/ftgw/digital/portfolio/summary"
    app = _app(bridge.notifier)
    extension = _extension(bridge)
    app.notification()  # connected
    extension.send({"type": "event", "event": "tab", "data": {"url": portfolio}})
    extension.send({"type": "event", "event": "tab", "data": {"url": signin}})
    gone = app.notification()
    assert (gone["kind"], gone["title"]) == ("fidelity_signin", "Fidelity signed you out")
    assert app.receive_until(
        lambda m: m["type"] == "status" and m["status"]["extension"]["fidelity"] == "signed_out"
    )
    extension.close()
    app.close()


def test_a_refused_extension_is_said_once_not_at_every_retry(bridge):
    app = _app(bridge.notifier)
    for _ in range(2):
        wrong = FakeExtension(bridge.url, api_key="wrong-key-0123456789abcdefghijklmnopqrstuvw")
        assert wrong.handshake()["type"] == "denied"
        wrong.close()
    refused = app.notification()
    assert (refused["kind"], refused["severity"]) == ("refused", "warning")
    assert "FIDELITY_BRIDGE_API_KEY" in refused["body"]
    assert [n.kind for n in bridge.notifications.recent()] == ["refused"]
    app.close()


def test_a_disconnect_says_how_it_ended(bridge):
    app = _app(bridge.notifier)
    extension = _extension(bridge)
    app.notification()  # connected
    extension.ws.close(1001, "browser closing")
    gone = app.notification()
    assert gone["data"]["code"] == 1001
    assert "going away" in gone["body"] and "browser closing" in gone["body"]
    app.close()


def test_a_bridge_without_a_notifier_keeps_nothing():
    server = BridgeServer(BridgeApiKey(API_KEY), host="127.0.0.1", port=0)
    server.start()
    try:
        extension = _extension(server)
        assert server.notifications.events == ()
        assert server.notifications.recent() == []
        extension.close()
    finally:
        server.stop()


# -- building one --------------------------------------------------------------------


def test_build_notifier_reads_the_apps_own_key(tmp_path, monkeypatch):
    monkeypatch.setenv(NOTIFY_KEY_ENV_VAR, NOTIFY_KEY)
    server = build_notifier(NotifySettings(port=0, events=("buy",)), BridgeApiKey(API_KEY))
    assert server.notifications.events == ("buy",)


def test_build_notifier_refuses_the_extensions_key(monkeypatch):
    monkeypatch.setenv(NOTIFY_KEY_ENV_VAR, API_KEY)
    with pytest.raises(ConfigurationError, match="key of their own"):
        build_notifier(NotifySettings(port=0), BridgeApiKey(API_KEY))


def test_build_notifier_without_a_key_says_how_to_make_one(tmp_path, monkeypatch):
    monkeypatch.delenv(NOTIFY_KEY_ENV_VAR, raising=False)
    monkeypatch.setenv(API_KEY_ENV_VAR, API_KEY)
    with pytest.raises(ConfigurationError, match="keygen --notify"):
        build_notifier(NotifySettings(port=0), BridgeApiKey(API_KEY), env_file=tmp_path / ".e")


def test_build_notifier_refuses_a_host_name_in_the_allowlist(monkeypatch):
    monkeypatch.setenv(NOTIFY_KEY_ENV_VAR, NOTIFY_KEY)
    with pytest.raises(ConfigurationError, match="Host names"):
        build_notifier(NotifySettings(port=0, allowed_clients=("my-phone",)), BridgeApiKey(API_KEY))
