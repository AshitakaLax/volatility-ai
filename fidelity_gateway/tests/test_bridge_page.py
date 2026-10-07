"""fidelity_gateway/bridge/page.py -- FidelitySession's page, over the bridge.

A stub stands in for BridgeServer, so these run without sockets. The
point is that FidelitySession, and the brokers on top of it, behave over
the bridge exactly as they did over a debugging port -- including which
failures are ambiguous and which are not.
"""

from __future__ import annotations

import json
import queue
import threading
import time

import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.retry_policy import AmbiguousSubmissionError
from fidelity_gateway.bridge.page import BridgePage, BridgeRequest
from fidelity_gateway.bridge.server import BridgeError, BridgeRefusal
from fidelity_gateway.placing_broker import FidelityPlacingBroker
from fidelity_gateway.session import FETCH_SCRIPT, FidelitySession, FidelitySessionError

PENDING = "/ftgw/digital/activityapi/api/v1/transactions/pending"
TRADE_URL = "https://digital.fidelity.com/ftgw/digital/trade-equity/getquote"
ACTIVITY_URL = "https://digital.fidelity.com" + PENDING
ACCOUNT = "999888777"


class StubServer:
    """Answers requests with `answer(command, args)`; queues events."""

    def __init__(self, answer=None):
        self.events: queue.Queue = queue.Queue()
        self.calls: list[tuple] = []
        self.answer = answer or (lambda command, args: {})

    def push(self, name, data):
        self.events.put((name, data))

    def next_event(self, timeout=0.0):
        try:
            return self.events.get_nowait() if timeout <= 0 else self.events.get(timeout=timeout)
        except queue.Empty:
            return None

    def request(self, command, args, *, timeout=45.0):
        self.calls.append((command, args, timeout))
        return self.answer(command, args)

    # What connect_live and cli.py tell the extension, recorded.
    statuses: list
    registered: dict

    def set_engine_status(self, status):
        self.__dict__.setdefault("statuses", []).append(dict(status))

    def register_call(self, method, handler):
        self.__dict__.setdefault("registered", {})[method] = handler


def _fetch_args(path=PENDING, payload=None, headers=None, timeout_ms=30_000):
    return [path, payload or {}, headers or {"accept": "application/json"}, timeout_ms]


# -- evaluate ---------------------------------------------------------------


def test_any_script_but_the_sessions_fetch_is_refused_locally():
    server = StubServer()
    page = BridgePage(server)
    with pytest.raises(BridgeRefusal, match="runs no scripts"):
        page.evaluate("() => document.cookie", None)
    assert server.calls == [], "nothing reached the extension"


def test_the_fetch_becomes_the_extensions_fetch_command():
    server = StubServer(
        lambda command, args: {
            "status": 200,
            "url": "https://x",
            "body": "{}",
            "tabUrl": "https://digital.fidelity.com/ftgw/digital/traderplus",
        }
    )
    page = BridgePage(server)
    result = page.evaluate(FETCH_SCRIPT, _fetch_args(payload={"a": 1}, timeout_ms=5000))
    assert result == {"status": 200, "url": "https://x", "body": "{}"}
    command, args, timeout = server.calls[0]
    assert command == "fetch"
    assert args == {
        "path": PENDING,
        "body": {"a": 1},
        "headers": {"accept": "application/json"},
        "timeoutMs": 5000,
    }
    assert timeout == pytest.approx(20.0), "the fetch's own timeout plus slack"
    assert page.url == "https://digital.fidelity.com/ftgw/digital/traderplus"


# -- events arrive on the caller's thread, inside calls -----------------------


def test_events_wait_for_a_call_like_playwrights_do():
    server = StubServer()
    page = BridgePage(server)
    seen = []
    page.on("request", lambda request: seen.append((threading.get_ident(), request.url)))
    server.push("request", {"url": TRADE_URL, "headers": {"appid": "AP1"}})
    assert seen == [], "nothing is delivered between calls"
    page.wait_for_timeout(0)
    assert seen == [(threading.get_ident(), TRADE_URL)]


def test_a_wait_delivers_events_that_arrive_during_it():
    server = StubServer()
    page = BridgePage(server)
    seen = []
    page.on("request", lambda request: seen.append(request.headers))
    threading.Timer(
        0.05, lambda: server.push("request", {"url": TRADE_URL, "headers": {"x-csrf-token": "T"}})
    ).start()
    started = time.monotonic()
    page.wait_for_timeout(300)
    assert seen == [{"x-csrf-token": "T"}]
    assert time.monotonic() - started >= 0.29, "it still waits out the full time"


def test_tab_events_track_the_url_and_none_means_no_tab():
    server = StubServer()
    page = BridgePage(server)
    server.push("tab", {"url": "https://digital.fidelity.com/ftgw/digital/portfolio"})
    assert page.url == "https://digital.fidelity.com/ftgw/digital/portfolio"
    server.push("tab", {"url": None})
    assert page.url == ""


def test_malformed_events_are_ignored_and_a_failing_handler_does_not_stop_the_rest():
    server = StubServer()
    page = BridgePage(server)
    seen = []

    def broken(_request):
        raise RuntimeError("boom")

    page.on("request", broken)
    page.on("request", lambda request: seen.append(request))
    server.push("request", {"url": TRADE_URL, "headers": "not a dict"})
    server.push("request", {"url": 5, "headers": {}})
    server.push("something", {"x": 1})
    server.push("request", {"url": TRADE_URL, "headers": {"appid": "AP1"}})
    page.wait_for_timeout(0)
    assert len(seen) == 1 and isinstance(seen[0], BridgeRequest)


# -- navigation ---------------------------------------------------------------


def test_goto_navigates_the_tab_and_records_where_it_landed():
    server = StubServer(
        lambda command, args: {"tabUrl": "https://digital.fidelity.com/ftgw/digital/traderplus#x"}
    )
    page = BridgePage(server)
    page.goto("https://digital.fidelity.com/ftgw/digital/traderplus")
    assert server.calls[0][:2] == (
        "navigate",
        {"url": "https://digital.fidelity.com/ftgw/digital/traderplus"},
    )
    assert page.url.endswith("#x")


def test_wait_for_load_state_listens_for_a_while():
    page = BridgePage(StubServer(), settle_seconds=0.1)
    started = time.monotonic()
    page.wait_for_load_state("networkidle")
    assert time.monotonic() - started >= 0.09


# -- FidelitySession over the bridge ---------------------------------------


def _fidelity(command, args):
    """The extension, with Fidelity behind it: echoes what it was sent."""
    if command == "fetch":
        body = json.dumps({"path": args["path"], "headers": args["headers"]})
        return {
            "status": 200,
            "url": "https://digital.fidelity.com" + args["path"],
            "body": body,
            "tabUrl": TRADE_URL,
        }
    return {}


def test_the_session_sniffs_headers_and_posts_through_the_bridge():
    server = StubServer(_fidelity)
    page = BridgePage(server)
    session = FidelitySession(page)
    session.attach()
    server.push(
        "request", {"url": ACTIVITY_URL, "headers": {"x-csrf-token": "T", "appid": "AP182052"}}
    )
    session.wait_for_credentials(timeout_seconds=2)
    answer = session.post_json(PENDING, {"filter": {}})
    assert answer["headers"]["x-csrf-token"] == "T"
    assert answer["headers"]["appid"] == "AP182052"


def test_the_sessions_own_gate_still_fires_before_the_bridge_is_asked():
    server = StubServer(_fidelity)
    page = BridgePage(server)
    session = FidelitySession(page)
    session.attach()
    server.push("request", {"url": TRADE_URL, "headers": {"x-csrf-token": "T"}})
    session.wait_for_credentials(timeout_seconds=2)
    with pytest.raises(ConfigurationError, match="PLACES OR CANCELS A REAL ORDER"):
        session.post_json("/ftgw/digital/trade-equity/placeOrder", {})
    assert [call[0] for call in server.calls] == [], "the extension was never asked"


def test_an_extension_refusal_is_not_wrapped_as_a_session_failure():
    def refuse(command, args):
        raise BridgeRefusal("switched off in the extension (blocked_endpoint)", "blocked_endpoint")

    page = BridgePage(StubServer(refuse))
    session = FidelitySession(page, allow_order_endpoints=True)
    session.attach()
    page._server.push("request", {"url": TRADE_URL, "headers": {"x-csrf-token": "T"}})
    session.wait_for_credentials(timeout_seconds=2)
    with pytest.raises(BridgeRefusal):
        session.post_json("/ftgw/digital/trade-equity/placeOrder", {})


def test_a_bridge_failure_still_reads_as_a_session_failure():
    def fail(command, args):
        raise BridgeError("the extension disconnected before answering fetch")

    page = BridgePage(StubServer(fail))
    session = FidelitySession(page)
    session.attach()
    page._server.push("request", {"url": TRADE_URL, "headers": {"x-csrf-token": "T"}})
    session.wait_for_credentials(timeout_seconds=2)
    with pytest.raises(FidelitySessionError, match="disconnected before answering"):
        session.post_json(PENDING, {})


# -- and the placing broker on top of it -------------------------------------


class _Journal:
    def __init__(self):
        self.records = []

    def record(self, decision_id, conf_num, detail):
        self.records.append((decision_id, conf_num, detail))

    def read_all(self):
        return []


def _placing_session(place_behaviour):
    def answer(command, args):
        path = args.get("path")
        if path == "/ftgw/digital/trade-equity/previewSrvc":
            body = {"preview": {"orderConfirmDetail": {"confNum": "2C50BRDG"}}}
            return {"status": 200, "url": "", "body": json.dumps(body)}
        if path == "/ftgw/digital/trade-equity/placeOrder":
            return place_behaviour()
        return {"status": 200, "url": "", "body": "{}"}

    page = BridgePage(StubServer(answer))
    session = FidelitySession(page, allow_order_endpoints=True)
    session.attach()
    page._server.push("request", {"url": TRADE_URL, "headers": {"x-csrf-token": "T"}})
    session.wait_for_credentials(timeout_seconds=2)
    return session


def _broker(session):
    return FidelityPlacingBroker(
        session,
        ACCOUNT,
        (ACCOUNT,),
        confirm_live_orders=True,
        allowed_symbols=("CWH",),
        max_order_value=100.0,
        journal=_Journal(),
    )


def test_an_order_the_extension_refused_is_not_reported_as_maybe_live():
    def refused():
        raise BridgeRefusal(
            "placing is switched off in the extension (blocked_endpoint)", "blocked_endpoint"
        )

    broker = _broker(_placing_session(refused))
    with pytest.raises(ConfigurationError, match="switched off") as caught:
        broker.place("CWH", "buy", 1, 20.0, "dec-bridge-1")
    assert not isinstance(caught.value, AmbiguousSubmissionError)


def test_an_order_lost_in_the_bridge_is_ambiguous():
    def lost():
        raise BridgeError(
            "The extension did not answer fetch within 45s. It may still have run it."
        )

    broker = _broker(_placing_session(lost))
    with pytest.raises(AmbiguousSubmissionError, match="MAY BE LIVE"):
        broker.place("CWH", "buy", 1, 20.0, "dec-bridge-2")


def test_an_order_refused_because_trading_is_off_is_waited_out_not_ambiguous():
    """The extension's trading switch, off: the order never left the
    browser, so it is not ambiguous -- and it clears when the switch goes
    back on, so the live loop waits rather than stopping."""
    from engine.core.exceptions import BrokerUnavailableError
    from fidelity_gateway.bridge.server import BridgeUnavailable

    def switched_off():
        raise BridgeUnavailable(
            "placing is switched off in the extension (blocked_endpoint)", "blocked_endpoint"
        )

    broker = _broker(_placing_session(switched_off))
    with pytest.raises(BrokerUnavailableError) as caught:
        broker.place("CWH", "buy", 1, 20.0, "dec-bridge-3")
    assert isinstance(caught.value, ConfigurationError)
    assert not isinstance(caught.value, AmbiguousSubmissionError)
