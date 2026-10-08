"""The engine against the REAL extension.

Everything else in the bridge suite tests one side at a time. This runs
the extension's own JavaScript (its whole background, from the
fidelity-bridge-chrome-extension submodule) in Node, against a live
BridgeServer, and drives it through FidelitySession and the placing
broker -- so a mismatch in the handshake, the sealing, the message
shapes, the error codes or the order reports fails here even if both
sides' own tests pass.

Skipped when Node or the submodule is missing (CI checks out neither).
Also here: the endpoint allowlists in the two repositories must name the
same paths, so neither can quietly grow without the other.
"""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

from engine.core.exceptions import BrokerUnavailableError
from engine.execution.order_lifecycle import OrderState
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import API_KEY_ENV_VAR, BridgeApiKey
from fidelity_gateway.bridge.page import BridgePage
from fidelity_gateway.bridge.server import (
    PRE_SEND_CODES,
    UNAVAILABLE_CODES,
    BridgeRefusal,
    BridgeServer,
)
from fidelity_gateway.placing_broker import FidelityPlacingBroker, FileConfNumJournal
from fidelity_gateway.session import (
    _SNIFFED_HEADERS,
    PLACE_ENDPOINTS,
    PREVIEW_ENDPOINTS,
    READ_ONLY_ENDPOINTS,
    FidelitySession,
)
from fidelity_gateway.tests.bridge_support import API_KEY, EXTENSION_ROOT

NODE = shutil.which("node")
HARNESS = Path(__file__).with_name("bridge_extension_harness.mjs")
ENDPOINTS_JS = EXTENSION_ROOT / "src" / "lib" / "endpoints.js"
HAVE_EXTENSION = (EXTENSION_ROOT / "src" / "lib" / "bridge-client.js").is_file()

needs_extension = pytest.mark.skipif(
    not HAVE_EXTENSION, reason="extension submodule not checked out"
)
needs_node = pytest.mark.skipif(
    NODE is None or not HAVE_EXTENSION, reason="needs Node 22+ and the extension submodule"
)

PENDING = "/ftgw/digital/activityapi/api/v1/transactions/pending"
PLACE = "/ftgw/digital/trade-equity/placeOrder"
ACCOUNT = "999888777"


class Extension:
    """The harness process, with its status lines collected."""

    def __init__(
        self,
        server: BridgeServer,
        *,
        key: str = API_KEY,
        settings: dict | None = None,
        calls: list | None = None,
    ):
        env = {
            **os.environ,
            API_KEY_ENV_VAR: key,
            "BRIDGE_TEST_SETTINGS": json.dumps(settings or {}),
            "BRIDGE_TEST_CALLS": json.dumps(calls or []),
        }
        self.process = subprocess.Popen(
            [NODE, str(HARNESS), str(EXTENSION_ROOT), "127.0.0.1", str(server.port)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.statuses: queue.Queue = queue.Queue()
        self.toasts: queue.Queue = queue.Queue()
        self.badges: queue.Queue = queue.Queue()
        self.calls: queue.Queue = queue.Queue()
        self.versions: queue.Queue = queue.Queue()
        self.output: list[str] = []
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        # Read everything, so a chatty process can never fill the pipe and
        # stall; keep every line for the failure message.
        for line in self.process.stdout:
            self.output.append(line.rstrip())
            if line.startswith('{"status"'):
                self.statuses.put(json.loads(line)["status"])
            elif line.startswith('{"toast"'):
                self.toasts.put(json.loads(line)["toast"])
            elif line.startswith('{"badge"'):
                self.badges.put(json.loads(line)["badge"])
            elif line.startswith('{"call"'):
                self.calls.put(json.loads(line)["call"])
            elif line.startswith('{"versions"'):
                self.versions.put(json.loads(line)["versions"])

    def wait_for_state(self, state: str, timeout: float = 15.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                status = self.statuses.get(timeout=0.2)
            except queue.Empty:
                continue
            if status["state"] == state:
                return status
        output = "\n".join(self.output)
        raise AssertionError(f"the extension never reached {state!r}. Its output:\n{output}")

    def wait_for_badge(self, words: str, timeout: float = 15.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                badge = self.badges.get(timeout=0.2)
            except queue.Empty:
                continue
            if words in badge["title"]:
                return badge
        output = "\n".join(self.output)
        raise AssertionError(f"no badge said {words!r}. The extension's output:\n{output}")

    def stop(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()


@pytest.fixture
def make_server():
    pytest.importorskip("websockets")
    servers: list[BridgeServer] = []

    def make(allowed=("127.0.0.1",), extension_versions=None) -> BridgeServer:
        server = BridgeServer(
            BridgeApiKey(API_KEY),
            host="127.0.0.1",
            port=0,
            policy=AddressPolicy(allowed),
            extension_versions=extension_versions,
        )
        server.start()
        servers.append(server)
        return server

    yield make
    for server in servers:
        server.stop()


@pytest.fixture
def extensions():
    started: list[Extension] = []

    def start(server, **kwargs) -> Extension:
        extension = Extension(server, **kwargs)
        started.append(extension)
        return extension

    yield start
    for extension in started:
        extension.stop()


def _session(server, **kwargs) -> FidelitySession:
    session = FidelitySession(BridgePage(server), **kwargs)
    session.attach()
    session.wait_for_credentials(timeout_seconds=10)
    return session


# -- the real extension, end to end ------------------------------------------


@needs_node
def test_the_real_extension_authenticates_and_serves_a_read(make_server, extensions):
    server = make_server()
    extension = extensions(server)
    assert server.wait_for_extension(15), "the extension never connected"
    extension.wait_for_state("ready")
    assert server.extension == {"name": "fidelity-bridge-extension", "version": "interop"}

    session = _session(server)
    answer = session.post_json(PENDING, {"filter": {"accounts": []}})
    assert answer["path"] == PENDING
    assert answer["body"] == {"filter": {"accounts": []}}
    # activityapi's own appid, not trade-equity's: per-backend headers
    # survive the trip through the extension.
    assert answer["headers"]["appid"] == "AP182052"


@needs_node
def test_the_extensions_order_lock_holds_even_when_the_engine_allows_orders(
    make_server, extensions
):
    server = make_server()
    extensions(server)
    assert server.wait_for_extension(15)
    session = _session(server, allow_order_endpoints=True)
    with pytest.raises(BridgeRefusal, match="Trading is off") as caught:
        session.post_json(PLACE, {"orderDetails": {}})
    assert caught.value.code == "blocked_endpoint"
    # Trading off is a pause, not a failure: the live loop waits it out.
    assert isinstance(caught.value, BrokerUnavailableError)
    assert server.permissions == {"preview": False, "place": False}


@needs_node
def test_with_both_locks_open_an_order_request_goes_through(make_server, extensions):
    server = make_server()
    extensions(server, settings={"allowPlace": True})
    assert server.wait_for_extension(15)
    session = _session(server, allow_order_endpoints=True)
    assert session.post_json(PLACE, {"orderDetails": {"qty": 1}})["path"] == PLACE
    assert server.permissions == {"preview": True, "place": True}


@needs_node
def test_navigation_is_held_to_the_extensions_own_rule(make_server, extensions):
    server = make_server()
    extensions(server)
    assert server.wait_for_extension(15)
    page = BridgePage(server)
    with pytest.raises(BridgeRefusal) as caught:
        page.goto("https://evil.example/ftgw/digital/x")
    assert caught.value.code == "blocked_url"
    page.goto("https://digital.fidelity.com/ftgw/digital/portfolio/summary")
    assert page.url == "https://digital.fidelity.com/ftgw/digital/portfolio/summary"


@needs_node
def test_an_extension_with_the_wrong_key_never_connects(make_server, extensions):
    server = make_server()
    extension = extensions(server, key="the-wrong-key-0123456789abcdefghijklmnop")
    status = extension.wait_for_state("auth_failed")
    assert "refused the API key" in status["detail"]
    assert not server.connected


@needs_node
def test_the_engine_refuses_an_extension_from_an_address_it_does_not_allow(make_server, extensions):
    server = make_server(allowed=("10.0.0.0/8",))
    extension = extensions(server)
    status = extension.wait_for_state("disconnected")
    assert "Could not reach the engine" in status["detail"]
    assert not server.connected


@needs_node
def test_the_extension_refuses_an_engine_address_it_does_not_allow(make_server, extensions):
    server = make_server()
    extension = extensions(server, settings={"allowedAddresses": ["10.0.0.0/8"]})
    status = extension.wait_for_state("blocked")
    assert "not in the allowed addresses" in status["detail"]
    time.sleep(0.5)
    assert not server.connected


@needs_node
def test_the_real_extension_sends_its_order_log_on_connecting(make_server, extensions):
    server = make_server()
    extensions(server)
    assert server.wait_for_extension(15)
    assert server.order_reports.wait_for_log(15), "no order log came"
    assert server.order_reports.recent() == []


@needs_node
def test_an_order_through_the_real_extension_is_confirmed_back_to_the_engine(
    make_server, extensions, tmp_path, caplog
):
    """The whole loop: the engine places, the extension relays it and
    reports Fidelity's acceptance, the engine polls, and the extension's
    report of the fill is there -- and agrees -- by the time the poll
    returns. With toasts on, the fill also opens one."""
    server = make_server()
    extension = extensions(server, settings={"allowPlace": True, "showToasts": True})
    assert server.wait_for_extension(15)
    session = _session(server, allow_preview_endpoints=True, allow_order_endpoints=True)
    broker = FidelityPlacingBroker(
        session,
        ACCOUNT,
        (ACCOUNT,),
        account_name="Traditional IRA",
        confirm_live_orders=True,
        allowed_symbols=("TQQQ",),
        max_order_value=1_000.0,
        journal=FileConfNumJournal(str(tmp_path / "orders.jsonl")),
        order_reports=server.order_reports,
    )

    order = broker.place("TQQQ", "buy", 2, 70.12, "dec-interop-1")
    accepted = server.order_reports.for_conf_num(order.id)
    assert accepted is not None, "the report is sent ahead of the reply it came from"
    assert (accepted.state, accepted.summary) == ("submitted", "BUY 2 TQQQ @ $70.12")

    with caplog.at_level("WARNING", logger="Optimizer"):
        found = broker.get_order_by_client_id("dec-interop-1")
    assert found.state is OrderState.FILLED
    filled = server.order_reports.for_conf_num(order.id)
    assert (filled.state, filled.filled_qty, filled.avg_price) == ("filled", 2.0, 70.12)
    assert any(
        "ORDER COMPLETE" in record.message
        and "confirmed by the browser extension" in record.message
        for record in caplog.records
    )
    assert not [record for record in caplog.records if record.levelname == "ERROR"]

    toast = extension.toasts.get(timeout=10)
    assert toast["type"] == "popup" and toast["focused"] is False
    assert toast["url"].endswith("/src/ui/toast.html")


@needs_node
def test_an_order_the_real_extension_refuses_is_reported_as_refused(make_server, extensions):
    server = make_server()
    extensions(server)
    assert server.wait_for_extension(15)
    session = _session(server, allow_order_endpoints=True)
    ticket = {"orderDetails": {"symbol": "TQQQ", "orderAction": "B", "qty": 1, "limitPrice": 69.3}}
    with pytest.raises(BridgeRefusal):
        session.post_json(PLACE, ticket)
    refused = server.order_reports.recent()[0]
    assert refused.state == "blocked"
    assert refused.summary == "BUY 1 TQQQ @ $69.30"
    assert refused.detail.startswith(
        "Trading is off in Fidelity Bridge, so this order was not sent."
    )


@needs_node
def test_the_real_extension_shows_what_the_engine_says_it_is_doing(make_server, extensions):
    """The engine's status, through the sealed channel, into the
    extension's monitor -- which sets the toolbar badge from it."""
    server = make_server()
    server.set_engine_status({"mode": "live", "state": "running", "symbol": "TQQQ"})
    extension = extensions(server)
    assert server.wait_for_extension(15)
    assert extension.wait_for_badge("connected")["text"] == "ON"
    server.set_engine_status(
        {
            "mode": "live",
            "state": "paused",
            "symbol": "TQQQ",
            "detail": "Trading is off in Fidelity Bridge",
        }
    )
    paused = extension.wait_for_badge("paused")
    assert paused["text"] == "!"
    assert "Trading is off in Fidelity Bridge" in paused["title"]
    server.set_engine_status(
        {
            "mode": "live",
            "state": "halted",
            "symbol": "TQQQ",
            "detail": "AmbiguousSubmissionError: may be live",
        }
    )
    assert "halted: AmbiguousSubmissionError" in extension.wait_for_badge("halted")["title"]


@needs_node
def test_the_real_extensions_algorithm_calls_reach_the_engine(make_server, extensions):
    """The algorithm editor's calls, made the way its page makes them, to
    handlers the engine registered -- and the engine's refusal back."""
    from engine.core.exceptions import ConfigurationError

    server = make_server()
    received = []

    def describe(args):
        received.append(("describe", args))
        return {"editable": True, "current": {"strategy_id": "fixed"}}

    def change(args):
        received.append(("set", args))
        raise ConfigurationError("step must be a fraction of the price between 0 and 1")

    server.register_call("algorithm.describe", describe)
    server.register_call("algorithm.set", change)
    extension = extensions(
        server,
        calls=[
            {"method": "algorithm.describe", "args": {}},
            {"method": "algorithm.set", "args": {"strategy_id": "fixed", "step": 5}},
            {"method": "algorithm.reset", "args": {}},
        ],
    )
    assert server.wait_for_extension(15)
    described, refused, unknown = (extension.calls.get(timeout=15) for _ in range(3))
    assert described["answer"] == {
        "ok": True,
        "result": {"editable": True, "current": {"strategy_id": "fixed"}},
    }
    assert refused["answer"] == {
        "ok": False,
        "error": {
            "code": "invalid",
            "message": "step must be a fraction of the price between 0 and 1",
        },
    }
    assert unknown["answer"]["error"]["code"] == "unknown_method", "not registered by this engine"
    assert received == [("describe", {}), ("set", {"strategy_id": "fixed", "step": 5})]


@needs_node
def test_the_real_extension_hears_which_versions_the_engine_expects(make_server, extensions):
    """The versions every connecting extension is sent, as its popup will
    show them -- here, a newer one checked out beside the engine."""
    server = make_server(extension_versions={"minimum": "0.3.0", "latest": "9.9.9"})
    extension = extensions(server)
    assert server.wait_for_extension(15)
    deadline = time.monotonic() + 15
    seen = None
    while time.monotonic() < deadline:
        try:
            seen = extension.versions.get(timeout=0.2)
        except queue.Empty:
            continue
        if seen.get("latest") == "9.9.9":
            break
    assert seen == {"loaded": "interop", "minimum": "0.3.0", "latest": "9.9.9"}


@needs_extension
def test_the_refusal_the_extension_sends_while_reloading_is_one_the_engine_waits_out():
    """A reload that arrives mid-conversation must not halt the engine: the
    extension answers what reaches it meanwhile with a refusal, and that
    refusal has to be one the engine treats as "nothing was sent, try again"
    -- or an order refused so would be taken for one of unknown outcome."""
    source = (EXTENSION_ROOT / "src" / "lib" / "bridge-client.js").read_text(encoding="utf-8")
    match = re.search(r'export const RELOADING_CODE = "([a-z_]+)"', source)
    assert match, "RELOADING_CODE not found in bridge-client.js"
    code = match.group(1)
    assert code in PRE_SEND_CODES, "it is a refusal made before anything is sent"
    assert code in UNAVAILABLE_CODES, "and one the live loop waits out instead of stopping"


# -- the two allowlists name the same endpoints ------------------------------


def _js_list(source: str, name: str) -> set[str]:
    match = re.search(rf"export const {name} = Object\.freeze\(\[(.*?)\]\);", source, re.S)
    assert match, f"{name} not found in endpoints.js"
    return set(re.findall(r'"([^"]+)"', match.group(1)))


@needs_extension
def test_the_extension_and_the_engine_allow_the_same_endpoints_in_the_same_tiers():
    source = ENDPOINTS_JS.read_text(encoding="utf-8")
    assert _js_list(source, "READ_ONLY_ENDPOINTS") == set(READ_ONLY_ENDPOINTS)
    assert _js_list(source, "PREVIEW_ENDPOINTS") == set(PREVIEW_ENDPOINTS)
    assert _js_list(source, "PLACE_ENDPOINTS") == set(PLACE_ENDPOINTS)


@needs_extension
def test_the_extension_lets_through_every_header_the_session_sends():
    allowed = _js_list(ENDPOINTS_JS.read_text(encoding="utf-8"), "ALLOWED_REQUEST_HEADERS")
    assert {"accept", "content-type", *_SNIFFED_HEADERS} == allowed
