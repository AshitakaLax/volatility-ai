"""fidelity_gateway/bridge/server.py, over a real socket.

Each test starts a BridgeServer on 127.0.0.1 with an ephemeral port and
drives it with bridge_support.FakeExtension, a Python implementation of
the extension's side. Nothing here touches Fidelity or a browser.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time

import pytest

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import BridgeApiKey
from fidelity_gateway.bridge.server import (
    EVENT_BACKLOG,
    PRE_SEND_CODES,
    BridgeError,
    BridgeRefusal,
    BridgeServer,
)
from fidelity_gateway.tests.bridge_support import API_KEY, REPO_ROOT, FakeExtension

websockets = pytest.importorskip("websockets")
from websockets.exceptions import ConnectionClosed  # noqa: E402 -- only once known installed


@pytest.fixture
def server():
    logs: list[str] = []
    bridge = BridgeServer(
        BridgeApiKey(API_KEY),
        host="127.0.0.1",
        port=0,
        policy=AddressPolicy(["127.0.0.1"]),
        handshake_timeout=2.0,
        log=logs.append,
    )
    bridge.start()
    bridge.logs = logs
    yield bridge
    bridge.stop()


def _connected(server, answer=None) -> FakeExtension:
    extension = FakeExtension(server.url)
    assert extension.handshake()["type"] == "welcome"
    assert server.wait_for_extension(5)
    if answer is not None:
        extension.serve(answer)
    return extension


def _wait_until(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def _upgrade_status(url: str, **kwargs) -> int | None:
    """The HTTP status the server answers a WebSocket upgrade with."""
    from websockets.exceptions import InvalidStatus
    from websockets.sync.client import connect

    try:
        with connect(url, proxy=None, open_timeout=5, **kwargs):
            return 101
    except InvalidStatus as exc:
        return exc.response.status_code


# -- getting in -------------------------------------------------------------


def test_an_extension_with_the_key_connects_and_the_engine_proves_it_back(server):
    extension = _connected(server)
    assert server.connected
    assert server.extension["version"] == "9.9.9"
    assert any("connected from 127.0.0.1" in line for line in server.logs)
    extension.close()


def test_a_wrong_key_is_denied_and_never_connected(server):
    extension = FakeExtension(server.url, api_key="wrong-key-0123456789abcdefghijklmnopqrst")
    reply = extension.handshake()
    assert reply == {"type": "denied", "reason": "bad_proof"}
    assert not server.connected
    assert any("failed the API key check" in line for line in server.logs)
    extension.close()


def test_a_forged_proof_is_denied(server):
    extension = FakeExtension(server.url)
    assert extension.handshake(proof="0" * 64)["type"] == "denied"
    extension.close()


def test_the_key_never_crosses_the_wire(server):
    extension = FakeExtension(server.url)
    challenge_and_welcome: list[str] = []
    original = extension.ws.recv

    def spy(*args, **kwargs):
        frame = original(*args, **kwargs)
        challenge_and_welcome.append(frame)
        return frame

    extension.ws.recv = spy
    extension.handshake()
    assert all(API_KEY not in frame for frame in challenge_and_welcome)
    extension.close()


def test_a_client_address_outside_the_allowlist_is_refused_at_the_upgrade():
    bridge = BridgeServer(
        BridgeApiKey(API_KEY), host="127.0.0.1", port=0, policy=AddressPolicy(["10.0.0.0/8"])
    )
    bridge.start()
    try:
        assert _upgrade_status(bridge.url) == 403
    finally:
        bridge.stop()


def test_a_blocked_client_address_is_refused_even_when_allowed():
    bridge = BridgeServer(
        BridgeApiKey(API_KEY),
        host="127.0.0.1",
        port=0,
        policy=AddressPolicy(["127.0.0.0/8"], ["127.0.0.1"]),
    )
    bridge.start()
    try:
        assert _upgrade_status(bridge.url) == 403
    finally:
        bridge.stop()


@pytest.mark.parametrize("origin", ["https://evil.example", "http://localhost:3000", "null"])
def test_a_web_pages_origin_is_refused(server, origin):
    assert _upgrade_status(server.url, origin=origin) == 403


def test_an_extension_origin_is_accepted(server):
    assert (
        _upgrade_status(server.url, origin="chrome-extension://abcdefghijklmnopabcdefghijklmnop")
        == 101
    )


def test_a_pinned_extension_origin_refuses_other_extensions():
    pinned = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"
    bridge = BridgeServer(
        BridgeApiKey(API_KEY),
        host="127.0.0.1",
        port=0,
        policy=AddressPolicy(["127.0.0.1"]),
        extension_origin=pinned,
    )
    bridge.start()
    try:
        assert _upgrade_status(bridge.url, origin=pinned) == 101
        assert _upgrade_status(bridge.url, origin="chrome-extension://someoneelse") == 403
    finally:
        bridge.stop()


def test_any_other_path_is_not_found(server):
    assert _upgrade_status(server.url.replace("/fidelity-bridge", "/other")) == 404


def test_a_silent_client_is_dropped_after_the_handshake_timeout(server):
    from websockets.sync.client import connect

    with connect(server.url, proxy=None, open_timeout=5) as ws:
        json.loads(ws.recv(timeout=5))  # the challenge
        time.sleep(2.5)
        with pytest.raises(ConnectionClosed):
            ws.recv(timeout=2)
    assert not server.connected


def test_a_greeting_that_is_not_the_protocol_is_closed(server):
    from websockets.sync.client import connect

    with connect(server.url, proxy=None, open_timeout=5) as ws:
        json.loads(ws.recv(timeout=5))
        ws.send(
            json.dumps({"type": "auth", "protocol": "other/v9", "nonce": "a" * 64, "proof": "x"})
        )
        with pytest.raises(ConnectionClosed):
            ws.recv(timeout=5)
    assert not server.connected


# -- requests ---------------------------------------------------------------


def test_a_request_round_trips(server):
    extension = _connected(server, lambda command, args: {"command": command, "args": args})
    assert server.request("status", {"x": 1}, timeout=5) == {"command": "status", "args": {"x": 1}}
    extension.close()
    assert extension.errors == []


@pytest.mark.parametrize("code", sorted(PRE_SEND_CODES))
def test_pre_send_refusals_become_bridge_refusals(server, code):
    def refuse(command, args):
        raise ValueError(f"{code}: switched off in the extension")

    extension = _connected(server, refuse)
    with pytest.raises(BridgeRefusal, match="switched off") as caught:
        server.request("fetch", {}, timeout=5)
    assert caught.value.code == code
    assert isinstance(caught.value, ConfigurationError), "a refusal is not an ambiguous submission"
    extension.close()


@pytest.mark.parametrize(
    "code", ["fetch_failed", "navigate_failed", "timeout", "internal_error", "new_code"]
)
def test_failures_that_might_have_reached_fidelity_are_bridge_errors(server, code):
    def fail(command, args):
        raise ValueError(f"{code}: something went wrong in the page")

    extension = _connected(server, fail)
    with pytest.raises(BridgeError, match="something went wrong"):
        server.request("fetch", {}, timeout=5)
    extension.close()


def test_no_extension_means_a_refusal_not_an_error(server):
    with pytest.raises(BridgeRefusal, match="No browser extension is connected"):
        server.request("status", {}, timeout=1)


def test_no_answer_in_time_is_an_error_that_admits_it_may_have_run(server):
    extension = _connected(server)  # connected, but answering nothing
    with pytest.raises(BridgeError, match="may still have run it"):
        server.request("fetch", {}, timeout=0.5)
    extension.close()


def test_a_disconnect_mid_request_fails_the_request(server):
    extension = _connected(server)

    def hang_up():
        time.sleep(0.3)
        extension.ws.close()

    threading.Thread(target=hang_up, daemon=True).start()
    with pytest.raises(BridgeError, match="disconnected before answering"):
        server.request("fetch", {}, timeout=5)
    assert _wait_until(lambda: not server.connected)


def test_concurrent_requests_each_get_their_own_answer(server):
    extension = _connected(server, lambda command, args: {"echo": args["n"]})
    results: dict[int, dict] = {}

    def ask(n):
        results[n] = server.request("status", {"n": n}, timeout=5)

    threads = [threading.Thread(target=ask, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results == {n: {"echo": n} for n in range(8)}
    extension.close()
    assert extension.errors == []


# -- events, pings, integrity -----------------------------------------------


def test_events_are_queued_for_the_caller(server):
    extension = _connected(server)
    extension.send(
        {"type": "event", "event": "tab", "data": {"url": "https://digital.fidelity.com/x"}}
    )
    event = None
    deadline = time.monotonic() + 5
    while event is None and time.monotonic() < deadline:
        event = server.next_event(0.1)
    assert event == ("tab", {"url": "https://digital.fidelity.com/x"})
    assert server.next_event(0) is None
    extension.close()


def test_a_ping_is_answered_with_a_pong(server):
    extension = _connected(server)
    extension.send({"type": "ping", "id": "p1"})
    assert extension.receive() == {"type": "pong", "id": "p1"}
    extension.close()


def test_a_tampered_frame_drops_the_extension(server):
    extension = _connected(server)
    envelope = extension.channel.seal({"type": "event", "event": "tab", "data": {}})
    envelope["payload"] = envelope["payload"].replace("tab", "bat")
    extension.ws.send(json.dumps(envelope))
    assert _wait_until(lambda: not server.connected)
    assert any("integrity" in line for line in server.logs)
    assert server.next_event(0) is None


def test_a_replayed_frame_drops_the_extension(server):
    extension = _connected(server)
    envelope = extension.channel.seal({"type": "event", "event": "tab", "data": {"url": None}})
    extension.ws.send(json.dumps(envelope))
    extension.ws.send(json.dumps(envelope))
    assert _wait_until(lambda: not server.connected)


def test_a_new_extension_replaces_the_old_one(server):
    first = _connected(server)
    second = _connected(server, lambda command, args: {"from": "second"})
    assert server.request("status", {}, timeout=5) == {"from": "second"}
    with pytest.raises(ConnectionClosed):
        first.ws.recv(timeout=5)
    second.close()


def test_the_event_backlog_is_bounded(server):
    for n in range(EVENT_BACKLOG + 5):
        server._push_event("tab", {"n": n})
    first = server.next_event(0)
    assert first == ("tab", {"n": 5}), "the oldest events are dropped, the newest kept"


def test_the_server_needs_a_real_key_object():
    with pytest.raises(ConfigurationError, match="BridgeApiKey"):
        BridgeServer(API_KEY)  # a bare string is not accepted


def test_importing_the_bridge_does_not_import_websockets():
    """Like Playwright for recon: optional, and paid for only when used."""
    code = (
        "import sys, fidelity_gateway.bridge, fidelity_gateway.bridge.server; "
        "print('websockets' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd=REPO_ROOT
    )
    assert out.stdout.strip() == "False"


# -- refusals the live loop waits out, and the trading switch ---------------


def test_no_extension_is_a_refusal_the_live_loop_waits_out(server):
    from engine.core.exceptions import BrokerUnavailableError
    from fidelity_gateway.bridge.server import BridgeUnavailable

    with pytest.raises(BridgeUnavailable) as caught:
        server.request("status", {}, timeout=1)
    assert caught.value.code == "not_connected"
    assert isinstance(caught.value, BrokerUnavailableError), "the loop skips, not stops"
    assert isinstance(caught.value, ConfigurationError), "and an order refused so is not ambiguous"


@pytest.mark.parametrize("code", ["no_fidelity_tab", "blocked_endpoint"])
def test_refusals_that_clear_on_their_own_are_unavailable(server, code):
    from engine.core.exceptions import BrokerUnavailableError

    def refuse(command, args):
        raise ValueError(f"{code}: trading is switched off in the extension")

    extension = _connected(server, refuse)
    with pytest.raises(BrokerUnavailableError) as caught:
        server.request("fetch", {}, timeout=5)
    assert isinstance(caught.value, BridgeRefusal) and caught.value.code == code
    extension.close()


@pytest.mark.parametrize(
    "code", ["blocked_header", "blocked_url", "bad_request", "unknown_command"]
)
def test_other_refusals_mean_a_bug_and_are_not_waited_out(server, code):
    from engine.core.exceptions import BrokerUnavailableError

    def refuse(command, args):
        raise ValueError(f"{code}: the engine asked for something it should not")

    extension = _connected(server, refuse)
    with pytest.raises(BridgeRefusal) as caught:
        server.request("fetch", {}, timeout=5)
    assert not isinstance(caught.value, BrokerUnavailableError)
    extension.close()


def test_the_extensions_trading_switch_is_tracked_and_announced(server):
    extension = _connected(server)
    assert server.permissions is None, "nothing known until the extension says"

    extension.send(
        {"type": "event", "event": "permissions", "data": {"preview": True, "place": True}}
    )
    assert _wait_until(lambda: server.permissions == {"preview": True, "place": True})
    assert any("allows trading" in line for line in server.logs)

    extension.send(
        {"type": "event", "event": "permissions", "data": {"preview": True, "place": False}}
    )
    assert _wait_until(lambda: server.permissions == {"preview": True, "place": False})
    assert any("switched OFF" in line for line in server.logs)

    announcements = len(server.logs)
    extension.send(
        {"type": "event", "event": "permissions", "data": {"preview": True, "place": False}}
    )
    extension.send({"type": "ping", "id": "sync"})
    assert extension.receive() == {"type": "pong", "id": "sync"}
    assert len(server.logs) == announcements, "an unchanged switch is not announced again"
    assert server.next_event(0) is None, "permissions are not page events"
    extension.close()


def test_a_malformed_permissions_event_is_ignored(server):
    extension = _connected(server)
    extension.send({"type": "event", "event": "permissions", "data": "everything"})
    extension.send({"type": "ping", "id": "sync"})
    assert extension.receive() == {"type": "pong", "id": "sync"}
    assert server.permissions is None
    extension.close()


# -- the extension's order reports -------------------------------------------

ORDER_REPORT = {
    "id": "2026-10-07T14:00:00.000Z#1",
    "confNum": "2C50H6WV",
    "symbol": "TQQQ",
    "side": "buy",
    "qty": 1,
    "limitPrice": 69.3,
    "state": "filled",
    "filledQty": 1,
    "avgPrice": 69.25,
    "attempts": 1,
    "placedAt": "2026-10-07T14:00:00.000Z",
    "updatedAt": "2026-10-07T14:03:00.000Z",
    "detail": "",
}


def _sync(extension) -> None:
    """Everything sent before this has been handled once the pong is back:
    the server handles one connection's frames in order."""
    extension.send({"type": "ping", "id": "sync"})
    assert extension.receive() == {"type": "pong", "id": "sync"}


def test_an_order_report_is_kept_logged_and_not_a_page_event(server):
    extension = _connected(server)
    extension.send({"type": "event", "event": "order", "data": ORDER_REPORT})
    _sync(extension)
    report = server.order_reports.for_conf_num("2C50H6WV")
    assert report is not None and report.state == "filled" and report.avg_price == 69.25
    assert any("the extension confirms order 2C50H6WV FILLED" in line for line in server.logs)
    assert server.next_event(0) is None, "reports are the server's, not the page's"
    extension.close()


def test_the_order_log_sent_on_connecting_is_taken_whole(server):
    extension = _connected(server)
    assert not server.order_reports.wait_for_log(0)
    older = {**ORDER_REPORT, "id": "r0", "confNum": "2C50AAAA", "state": "cancelled"}
    extension.send({"type": "event", "event": "orders", "data": {"orders": [ORDER_REPORT, older]}})
    _sync(extension)
    assert server.order_reports.wait_for_log(0)
    assert [r.conf_num for r in server.order_reports.recent()] == ["2C50H6WV", "2C50AAAA"]
    extension.close()


def test_a_malformed_order_report_is_ignored_and_the_line_stays_up(server):
    extension = _connected(server)
    extension.send({"type": "event", "event": "order", "data": {"state": "filled"}})
    extension.send({"type": "event", "event": "orders", "data": "everything"})
    _sync(extension)
    assert server.order_reports.recent() == []
    assert server.connected
    extension.close()


def test_reports_go_where_the_caller_says(tmp_path):
    from fidelity_gateway.bridge.order_reports import OrderReports

    reports = OrderReports(path=tmp_path / "reports.jsonl")
    bridge = BridgeServer(
        BridgeApiKey(API_KEY),
        host="127.0.0.1",
        port=0,
        policy=AddressPolicy(["127.0.0.1"]),
        order_reports=reports,
    )
    bridge.start()
    try:
        assert bridge.order_reports is reports
        extension = _connected(bridge)
        extension.send({"type": "event", "event": "order", "data": ORDER_REPORT})
        _sync(extension)
        assert '"state": "filled"' in (tmp_path / "reports.jsonl").read_text(encoding="utf-8")
        extension.close()
    finally:
        bridge.stop()


# -- the engine's status, sent to the extension ------------------------------


def test_the_engine_status_is_sent_on_connecting_and_on_change(server):
    status = {"mode": "live", "state": "running", "symbol": "TQQQ"}
    server.set_engine_status(status)
    extension = _connected(server)
    assert extension.receive() == {"type": "status", "engine": status}

    server.set_engine_status(status)  # unchanged: not sent again
    server.set_engine_status({**status, "state": "paused"})
    assert extension.receive() == {"type": "status", "engine": {**status, "state": "paused"}}
    _sync(extension)
    assert server.engine_status == {**status, "state": "paused"}
    extension.close()


def test_no_status_set_means_none_is_sent(server):
    extension = _connected(server)
    _sync(extension)  # the pong is the first thing back
    assert server.engine_status is None
    extension.close()


# -- calls from the extension -----------------------------------------------


def _call(extension, method, args=None, call_id="c1"):
    extension.send({"type": "call", "id": call_id, "method": method, "args": args or {}})
    return extension.receive()


def test_a_registered_call_is_answered_with_its_result(server):
    seen = []

    def describe(args):
        seen.append(args)
        return {"strategy": "fixed"}

    server.register_call("algorithm.describe", describe)
    extension = _connected(server)
    reply = _call(extension, "algorithm.describe", {"verbose": True})
    assert reply == {"type": "result", "id": "c1", "ok": True, "result": {"strategy": "fixed"}}
    assert seen == [{"verbose": True}]
    extension.close()


def test_an_unregistered_call_is_refused(server):
    extension = _connected(server)
    reply = _call(extension, "algorithm.set")
    assert reply["ok"] is False and reply["error"]["code"] == "unknown_method"
    extension.close()


def test_refusals_and_failures_come_back_as_codes(server):
    from engine.core.exceptions import ConfigurationError

    def invalid(_args):
        raise ConfigurationError("profit_target must be positive")

    def not_allowed(_args):
        raise PermissionError("this deployment does not allow it")

    def broken(_args):
        raise RuntimeError("disk full")

    server.register_call("invalid", invalid)
    server.register_call("not_allowed", not_allowed)
    server.register_call("broken", broken)
    extension = _connected(server)
    assert _call(extension, "invalid")["error"] == {
        "code": "invalid",
        "message": "profit_target must be positive",
    }
    assert _call(extension, "not_allowed")["error"]["code"] == "not_allowed"
    failed = _call(extension, "broken")["error"]
    assert failed == {"code": "internal_error", "message": "RuntimeError: disk full"}
    assert any("broken failed" in line for line in server.logs)
    extension.close()


def test_a_slow_call_does_not_hold_up_the_connection(server):
    release = threading.Event()

    def slow(_args):
        release.wait(5)
        return {"done": True}

    server.register_call("slow", slow)
    extension = _connected(server)
    extension.send({"type": "call", "id": "slow-1", "method": "slow", "args": {}})
    _sync(extension)  # the ping is answered while the call is still running
    release.set()
    assert extension.receive() == {
        "type": "result",
        "id": "slow-1",
        "ok": True,
        "result": {"done": True},
    }
    extension.close()


def test_a_call_with_no_id_is_dropped_and_the_line_stays_up(server):
    server.register_call("algorithm.describe", lambda _args: {})
    extension = _connected(server)
    extension.send({"type": "call", "method": "algorithm.describe", "args": {}})
    extension.send({"type": "call", "id": "", "method": "algorithm.describe"})
    _sync(extension)
    assert server.connected
    extension.close()
