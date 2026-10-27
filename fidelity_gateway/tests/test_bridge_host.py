"""fidelity_gateway/bridge/host.py and attach.py: the bridge that stays up
between sessions, and the trading process that attaches to it.

A real BridgeHost on 127.0.0.1 (an ephemeral port) and a real Unix socket;
the extension is bridge_support.FakeExtension, the attached trader the real
AttachedBridge. The host's ticks are called by the test, on its own clock --
nothing here waits for a timer.
"""

from __future__ import annotations

import json
import shutil
import socket
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from engine.core.config import FidelityBridgeConfig, FidelityConfig
from engine.trading.control_inbox import Command, ControlInbox
from fidelity_gateway.bridge.attach import AttachedBridge
from fidelity_gateway.bridge.host import CHECK_RETRY_SECONDS, BridgeHost, session_window
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import BridgeApiKey
from fidelity_gateway.bridge.server import (
    BridgeError,
    BridgeRefusal,
    BridgeServer,
    BridgeUnavailable,
)
from fidelity_gateway.tests.bridge_support import API_KEY, FakeExtension

pytest.importorskip("websockets")

SIGNIN = "https://digital.fidelity.com/prgw/digital/signin/retail"
PORTFOLIO = "https://digital.fidelity.com/ftgw/digital/portfolio/summary"
HEADERS = {"url": "https://digital.fidelity.com/ftgw/digital/x", "headers": {"appid": "A"}}


class Clock:
    def __init__(self, now: float | None = None) -> None:
        self.now = time.time() if now is None else now

    def __call__(self) -> float:
        return self.now


SUNDAY = datetime(2026, 10, 25, 12, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()


def _fidelity(port: int = 0, dry_run: bool = False) -> FidelityConfig:
    return FidelityConfig(
        allowed_accounts=("999888777",),
        account="999888777",
        dry_run=dry_run,
        account_name="Traditional IRA",
        allowed_symbols=("RSP",),
        max_order_value=1_000.0,
        bridge=FidelityBridgeConfig(host="127.0.0.1", port=port, allowed_clients=("127.0.0.1",)),
    )


def _make_server(settings, on_event) -> BridgeServer:
    return BridgeServer(
        BridgeApiKey(API_KEY),
        host=settings.host,
        port=settings.port,
        policy=AddressPolicy(list(settings.allowed_clients)),
        handshake_timeout=2.0,
        on_event=on_event,
    )


@pytest.fixture
def place():
    # Unix socket paths are limited to ~100 bytes: a short directory of its own.
    directory = Path(tempfile.mkdtemp(prefix="vai-host-", dir="/tmp"))
    yield directory
    shutil.rmtree(directory, ignore_errors=True)


def _host(place, *, check=None, settings=None, clock=None) -> BridgeHost:
    # A Sunday unless a test says otherwise: between sessions whenever the
    # suite runs. On the wall clock, tests behaved differently during market
    # hours (the standby's words, a check run before trading).
    clock = clock or Clock(SUNDAY)
    settings = settings or (lambda: (_fidelity(), "RSP"))

    def make_server(settings, on_event) -> BridgeServer:
        server = _make_server(settings, on_event)
        server._clock = clock  # one clock for the host and its bridge
        return server

    host = BridgeHost(
        make_server=make_server,
        settings=settings,
        socket_path=place / "bridge.sock",
        inbox=ControlInbox(place / "control" / "bridge", clock=clock),
        check=check,
        deployment="fidelity",
        clock=clock,
        log=lambda _message: None,
    )
    host.open_socket()
    assert host.bind()
    return host


@pytest.fixture
def host(place):
    bridge_host = _host(place)
    yield bridge_host
    bridge_host.close()


def _wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def _extension(host: BridgeHost, answer=None) -> FakeExtension:
    extension = FakeExtension(host.server.url)
    assert extension.handshake()["type"] == "welcome"
    assert host.server.wait_for_extension(5)
    if answer is not None:
        extension.serve(answer)
    return extension


def _attach(host: BridgeHost, process: str = "loop") -> AttachedBridge:
    return AttachedBridge.attach(host.socket_path, client={"process": process})


def _event(extension: FakeExtension, name: str, data: dict) -> None:
    extension.send({"type": "event", "event": name, "data": data})


def _next(bridge, timeout: float = 5.0):
    return bridge.next_event(timeout)


# -- attaching ----------------------------------------------------------------------


def test_an_attached_trader_reaches_the_extension_through_the_host(host):
    extension = _extension(host, answer=lambda command, args: {"echo": command, "args": args})
    trader = _attach(host)
    try:
        assert trader.wait_for_extension(5), "the host said the extension is there"
        assert trader.request("status", {"x": 1}) == {"echo": "status", "args": {"x": 1}}
        assert host.attached["process"] == "loop"
    finally:
        trader.stop()
        extension.close()


def test_what_the_extension_already_said_is_replayed_on_attaching(host):
    """The trader of a session that starts at 09:30 gets the headers the
    extension sent at 08:00 -- no wait, and no navigation to provoke them."""
    extension = _extension(host)
    _event(extension, "request", HEADERS)
    _event(extension, "tab", {"url": PORTFOLIO})
    _event(extension, "permissions", {"preview": True, "place": True})
    _event(extension, "orders", {"orders": []})
    assert _wait_until(lambda: host._permissions_event is not None and host._orders_event)
    trader = _attach(host)
    try:
        assert _next(trader) == ("request", HEADERS)
        assert _next(trader) == ("tab", {"url": PORTFOLIO})
        assert trader.permissions == {"preview": True, "place": True}
        assert trader.order_reports.wait_for_log(1)
        _event(extension, "tab", {"url": SIGNIN})  # and live events after the replay
        assert _next(trader) == ("tab", {"url": SIGNIN})
    finally:
        trader.stop()
        extension.close()


def test_one_process_at_a_time(host):
    """Two trading loops on one account duplicate orders: the second is
    refused, naming the first, and may attach once the first detaches."""
    first = _attach(host, "loop")
    with pytest.raises(BridgeUnavailable) as caught:
        _attach(host, "check")
    assert caught.value.code == "attached_elsewhere"
    assert "the trading loop" in str(caught.value)
    first.stop()
    assert _wait_until(lambda: host.attached is None)
    second = _attach(host, "check")
    assert host.attached["process"] == "check"
    second.stop()


def test_no_host_is_a_wait_not_a_failure(place):
    with pytest.raises(BridgeUnavailable) as caught:
        AttachedBridge.attach(place / "nothing.sock")
    assert caught.value.code == "no_host"
    assert "fidelity-bridge" in str(caught.value)


@pytest.mark.parametrize(
    ("code", "kind"),
    [
        ("no_fidelity_tab", BridgeUnavailable),
        ("blocked_url", BridgeRefusal),
        ("fetch_failed", BridgeError),
    ],
)
def test_an_error_means_what_it_meant_without_the_host(host, code, kind):
    """A refusal is still a refusal (nothing sent) and a failure is still
    "may have reached Fidelity": the placing broker's ambiguity rule must not
    change because a host sits in between."""

    def refuse(_command, _args):
        raise ValueError(f"{code}: no")

    extension = _extension(host, answer=refuse)
    trader = _attach(host)
    try:
        with pytest.raises(kind) as caught:
            trader.request("fetch", {})
        if kind is BridgeRefusal:
            assert not isinstance(caught.value, BridgeUnavailable)
        if kind is BridgeError:
            assert not isinstance(caught.value, BridgeRefusal)
    finally:
        trader.stop()
        extension.close()


def test_no_extension_is_still_a_wait(host):
    trader = _attach(host)
    try:
        with pytest.raises(BridgeUnavailable) as caught:
            trader.request("status", {})
        assert caught.value.code == "not_connected"
    finally:
        trader.stop()


def test_losing_the_host_mid_request_may_have_run_it(host):
    extension = _extension(host)  # never answers
    trader = _attach(host)
    failures: list[BaseException] = []

    def ask() -> None:
        try:
            trader.request("fetch", {}, timeout=30)
        except BaseException as exc:
            failures.append(exc)

    asker = threading.Thread(target=ask)
    asker.start()
    assert _wait_until(lambda: bool(host._attached and host._attached.welcomed))
    time.sleep(0.2)  # the request is on its way to the extension
    host._attached.line.close()  # the host's end of the link goes away
    asker.join(timeout=10)
    assert len(failures) == 1 and type(failures[0]) is BridgeError
    assert "may have run it" in str(failures[0])
    extension.close()


# -- the extension's calls, and its status line ---------------------------------------


def test_the_extensions_calls_reach_the_attached_trader_and_only_it(host):
    extension = _extension(host)
    trader = _attach(host)
    trader.register_call("algorithm.describe", lambda _args: {"current": "ultimate_rsp"})
    assert _wait_until(lambda: "algorithm.describe" in host._attached.methods)

    def call() -> dict:
        extension.send({"type": "call", "id": "c1", "method": "algorithm.describe", "args": {}})
        while True:
            message = extension.receive()
            if message.get("type") == "result":
                return message

    assert call() == {
        "type": "result",
        "id": "c1",
        "ok": True,
        "result": {"current": "ultimate_rsp"},
    }
    trader.stop()
    assert _wait_until(lambda: host.attached is None)
    refused = call()
    assert refused["ok"] is False and refused["error"]["code"] == "not_allowed"
    assert "Live page" in refused["error"]["message"]
    extension.close()


def _statuses(extension: FakeExtension, count: int = 1, timeout: float = 5.0) -> list[dict]:
    found: list[dict] = []
    deadline = time.monotonic() + timeout
    while len(found) < count and time.monotonic() < deadline:
        try:
            message = extension.receive(timeout=max(0.05, deadline - time.monotonic()))
        except TimeoutError:
            break
        if message.get("type") == "status":
            found.append(message["engine"])
    return found


def test_the_extension_hears_the_trader_while_attached_and_the_host_otherwise(place):

    # A Sunday: between sessions whenever the suite runs (it failed during
    # a session on the wall clock).
    sunday = datetime(2026, 10, 25, 12, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()
    host = _host(place, clock=Clock(sunday))
    try:
        extension = _extension(host)
        host.tick()
        (standby,) = _statuses(extension)
        assert standby["mode"] == "bridge" and isinstance(standby["ready"], bool)
        assert "next session" in standby["detail"]
        trader = _attach(host)
        trader.set_engine_status({"mode": "live", "state": "running", "detail": "trading"})
        (running,) = _statuses(extension)
        assert running["mode"] == "live" and running["detail"] == "trading"
        trader.stop()
        assert _wait_until(lambda: host.attached is None)
        host.tick()
        (back,) = _statuses(extension)
        assert back["mode"] == "bridge"
        extension.close()
    finally:
        host.close()


# -- what the Live page and the supervisor read --------------------------------------


def _status(host: BridgeHost) -> dict:
    return host.inbox.status()


def test_the_status_says_ready_or_the_one_thing_to_fix(host):
    host.tick()
    status = _status(host)
    assert status["process"] == "bridge" and status["listening"] is True
    assert status["readiness"]["ready"] is False
    assert status["readiness"]["blocking"] == "extension"

    extension = _extension(host)
    _event(extension, "tab", {"url": SIGNIN})
    _event(extension, "permissions", {"preview": True, "place": True})
    assert _wait_until(lambda: (host.server.connection_report()["fidelity_tab"] or {}).get("state"))
    host.tick()
    readiness = _status(host)["readiness"]
    assert readiness["ready"] is False and readiness["blocking"] == "fidelity"
    assert "signed you out" in readiness["summary"]

    _event(extension, "tab", {"url": PORTFOLIO})
    assert _wait_until(
        lambda: host.server.connection_report()["fidelity_tab"]["state"] == "signed_in"
    )
    host.tick()
    assert _status(host)["readiness"]["ready"] is True
    extension.close()


def test_the_journal_tells_the_story_of_a_disconnect(host):
    extension = _extension(host)
    _event(extension, "tab", {"url": PORTFOLIO})
    _event(extension, "permissions", {"preview": True, "place": False})
    assert _wait_until(
        lambda: (
            host.server.connection_report()["fidelity_tab"] is not None
            and host.server.permissions is not None
        )
    )
    host.tick()
    trader = _attach(host)
    assert _wait_until(lambda: host.attached is not None)
    trader.stop()
    assert _wait_until(lambda: host.attached is None)
    extension.ws.close(1001, "browser closed")
    assert _wait_until(lambda: not host.server.connected)
    host.tick()

    events = host.inbox.events()
    kinds = [event["kind"] for event in events]
    for kind in ("listening", "connected", "fidelity", "trading", "attached", "detached"):
        assert kind in kinds, kinds
    gone = next(event for event in events if event["kind"] == "disconnected")
    assert gone["code"] == 1001 and "going away" in gone["detail"]
    assert next(e for e in events if e["kind"] == "trading")["on"] is False
    assert events == sorted(events, key=lambda event: event["t"])


def test_a_taken_port_is_reported_and_taken_back_when_freed(place):
    holder = socket.socket()
    holder.bind(("127.0.0.1", 0))
    holder.listen()
    port = holder.getsockname()[1]
    clock = Clock()
    host = BridgeHost(
        make_server=_make_server,
        settings=lambda: (_fidelity(port), "RSP"),
        socket_path=place / "bridge.sock",
        inbox=ControlInbox(place / "control" / "bridge", clock=clock),
        clock=clock,
        log=lambda _message: None,
    )
    host.open_socket()
    try:
        assert host.bind() is False
        host.tick()
        status = _status(host)
        assert status["state"] == "port_conflict" and status["listening"] is False
        assert status["readiness"]["blocking"] == "bridge"
        assert f"Port {port}" in status["readiness"]["summary"]

        holder.close()
        clock.now += 31
        host.tick()
        assert _status(host)["listening"] is True
        assert [e["kind"] for e in host.inbox.events()].count("port_conflict") == 1
    finally:
        holder.close()
        host.close()


def test_a_config_change_restarts_the_bridge_with_it(place):
    current = {"fidelity": _fidelity()}
    host = _host(place, settings=lambda: (current["fidelity"], "RSP"))
    try:
        first = host.server.port
        assert host.reload() is False, "nothing changed"
        current["fidelity"] = FidelityConfig(
            **{
                **current["fidelity"].__dict__,
                "bridge": FidelityBridgeConfig(
                    host="127.0.0.1", port=0, allowed_clients=("127.0.0.1", "10.0.0.5")
                ),
            }
        )
        assert host.reload() is True
        assert host._listening and host.server.port != 0
        assert first != 0
    finally:
        host.close()


# -- the read-only account check --------------------------------------------------------


def test_check_connection_from_the_page_runs_the_check_and_records_it(place):
    seen: list[bool] = []

    def check(page, *, may_navigate: bool) -> str:
        seen.append(may_navigate)
        assert page.url == PORTFOLIO  # the replayed tab reached its page
        return "2 order(s) listed, RSP 0 share(s), settled cash $25,000.00"

    host = _host(place, check=check)
    extension = _extension(host)
    try:
        _event(extension, "tab", {"url": PORTFOLIO})
        assert _wait_until(lambda: host._tab_event is not None)
        host.inbox.enqueue(
            Command.new("check_connection", reason="before the open", operator="tester")
        )
        (result,) = host.poll_commands()
        assert result["status"] == "applied" and "settled cash" in result["detail"]
        assert seen == [True], "nothing attached: it may load Trader+ for the headers"
        host.tick()
        last = _status(host)["last_check"]
        assert last["ok"] is True and last["by"] == "tester"
        assert _status(host)["readiness"]["items"][-1]["state"] == "ok"
    finally:
        extension.close()
        host.close()


def test_a_check_that_fails_is_rejected_with_its_reason(place):
    def check(page, *, may_navigate: bool) -> str:
        raise RuntimeError("Fidelity answered 401")

    host = _host(place, check=check)
    extension = _extension(host)
    try:
        host.inbox.enqueue(Command.new("check_connection", reason="look", operator="tester"))
        (result,) = host.poll_commands()
        assert result["status"] == "rejected" and "401" in result["detail"]
        host.tick()
        assert _status(host)["readiness"]["blocking"] == "account"
    finally:
        extension.close()
        host.close()


def test_the_host_cannot_place_or_preview_an_order():
    """Read-only by construction: the session it builds takes FidelitySession's
    defaults (no previews, no orders) and the placing broker is never imported."""
    source = (Path(__file__).resolve().parents[1] / "bridge" / "host.py").read_text()
    assert "placing_broker" not in source
    assert "allow_order_endpoints" not in source and "allow_preview_endpoints" not in source


# -- when sessions are --------------------------------------------------------------


def test_the_session_window_follows_the_trading_calendar():

    eastern = ZoneInfo("America/New_York")
    saturday = datetime(2026, 10, 24, 12, 0, tzinfo=eastern).timestamp()
    window = session_window(saturday)
    assert window["open"] is False
    assert window["next_open"] == datetime(2026, 10, 26, 9, 30, tzinfo=eastern)

    tuesday_morning = datetime(2026, 10, 27, 10, 0, tzinfo=eastern).timestamp()
    assert session_window(tuesday_morning)["open"] is True

    thanksgiving = datetime(2026, 11, 26, 10, 0, tzinfo=eastern).timestamp()
    assert session_window(thanksgiving)["open"] is False


def test_a_pre_market_deployments_day_starts_at_seven():
    """live.sessions with the pre-market: the account is checked and
    readiness warned of before 07:00 ET (05:00 Mountain), not 09:30."""
    eastern = ZoneInfo("America/New_York")
    sessions = ("pre_market", "regular")
    early = datetime(2026, 10, 27, 6, 40, tzinfo=eastern).timestamp()
    window = session_window(early, sessions)
    assert window["open"] is False
    assert window["next_open"] == datetime(2026, 10, 27, 7, 0, tzinfo=eastern)
    pre = datetime(2026, 10, 27, 8, 0, tzinfo=eastern).timestamp()
    assert session_window(pre, sessions)["open"] is True
    assert session_window(pre)["open"] is False, "the regular session alone is unchanged"
    evening = datetime(2026, 10, 27, 17, 0, tzinfo=eastern).timestamp()
    late = session_window(evening, ("regular", "after_hours"))
    assert late["open"] is True and late["closes"] == datetime(2026, 10, 27, 20, 0, tzinfo=eastern)


def test_checks_run_by_themselves_before_the_open(place):

    calls: list[str] = []
    clock = Clock(datetime(2026, 10, 26, 9, 5, tzinfo=ZoneInfo("America/New_York")).timestamp())
    host = _host(place, check=lambda page, *, may_navigate: calls.append("x") or "ok", clock=clock)
    extension = _extension(host)
    try:
        host.tick()  # 25 min before: the 30-minute check is due, once
        assert _wait_until(lambda: len(calls) == 1)
        host.tick()
        clock.now += 16 * 60  # 9 min before: the 10-minute one
        host.tick()
        assert _wait_until(lambda: len(calls) == 2)
        host.tick()
        assert len(calls) == 2
    finally:
        extension.close()
        host.close()


MONDAY_11 = datetime(2026, 10, 26, 11, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()


def _account(host: BridgeHost) -> dict:
    return next(i for i in _status(host)["readiness"]["items"] if i["id"] == "account")


def test_during_a_session_a_connection_is_read_before_it_is_ready(place):
    """10-26: the bridge restarted mid-session, the tab's address said signed
    in, and the trader started at once -- on a tab that could not fetch. It
    failed five times and left a halt in its ledger. Now the account is read
    first, and again every CHECK_RETRY_SECONDS while that fails."""
    calls: list[bool] = []

    def check(page, *, may_navigate: bool) -> str:
        calls.append(may_navigate)
        if len(calls) == 1:
            raise RuntimeError("the Fidelity tab returned no response")
        return "0 order(s) listed, RSP 0 share(s), settled cash $25,000.00"

    clock = Clock(MONDAY_11)
    host = _host(place, check=check, clock=clock)
    extension = _extension(host)
    try:
        host.tick()
        account = _account(host)
        assert account["state"] == "fail" and "reading it now" in account["detail"]
        assert _status(host)["readiness"]["blocking"] == "account"
        assert _wait_until(lambda: host.last_check is not None)
        assert host.last_check["by"] == "the extension connected"

        host.tick()
        assert "returned no response" in _account(host)["detail"]
        clock.now += CHECK_RETRY_SECONDS - 1
        host.tick()
        assert len(calls) == 1, "not retried before CHECK_RETRY_SECONDS"
        clock.now += 1
        host.tick()
        assert _wait_until(lambda: len(calls) == 2 and host.last_check["ok"])
        assert host.last_check["by"] == "again: the last check failed"
        host.tick()
        assert _account(host)["state"] == "ok"
        clock.now += CHECK_RETRY_SECONDS
        host.tick()
        assert len(calls) == 2, "a connection that passed is not read again"
    finally:
        extension.close()
        host.close()


def test_a_trader_attached_is_not_held_to_reading_first(place):
    """The trader's own requests show the connection works; the host never
    reads the account under it."""
    calls: list[bool] = []
    host = _host(
        place,
        check=lambda page, *, may_navigate: calls.append(may_navigate) or "ok",
        clock=Clock(MONDAY_11),
    )
    extension = _extension(host)
    trader = _attach(host)
    try:
        assert _wait_until(lambda: host.attached is not None)
        host.tick()
        assert _account(host)["state"] == "unknown"
        assert calls == []
    finally:
        trader.stop()
        extension.close()
        host.close()


def test_the_status_is_json_the_page_can_read(host):
    host.tick()
    path = host.inbox.root / "status.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["readiness"]["items"][0]["id"] == "bridge"
    assert data["deployment"] == "fidelity" and data["mode"] == "live"
