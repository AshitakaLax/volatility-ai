"""The engine against the REAL extension.

Everything else in the bridge suite tests one side at a time. This runs
the extension's own JavaScript (its BridgeClient and command handler,
from the fidelity-bridge-chrome-extension submodule) in Node, against a
live BridgeServer, and drives it through FidelitySession -- so a mismatch
in the handshake, the sealing, the message shapes or the error codes
fails here even if both sides' own tests pass.

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
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import API_KEY_ENV_VAR, BridgeApiKey
from fidelity_gateway.bridge.page import BridgePage
from fidelity_gateway.bridge.server import BridgeRefusal, BridgeServer
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


class Extension:
    """The harness process, with its status lines collected."""

    def __init__(self, server: BridgeServer, *, key: str = API_KEY, settings: dict | None = None):
        env = {
            **os.environ,
            API_KEY_ENV_VAR: key,
            "BRIDGE_TEST_SETTINGS": json.dumps(settings or {}),
        }
        self.process = subprocess.Popen(
            [NODE, str(HARNESS), str(EXTENSION_ROOT), "127.0.0.1", str(server.port)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.statuses: queue.Queue = queue.Queue()
        self.output: list[str] = []
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        # Read everything, so a chatty process can never fill the pipe and
        # stall; keep non-status lines for the failure message.
        for line in self.process.stdout:
            self.output.append(line.rstrip())
            if line.startswith('{"status"'):
                self.statuses.put(json.loads(line)["status"])

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

    def make(allowed=("127.0.0.1",)) -> BridgeServer:
        server = BridgeServer(
            BridgeApiKey(API_KEY), host="127.0.0.1", port=0, policy=AddressPolicy(allowed)
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
    with pytest.raises(BridgeRefusal, match="REAL ORDER") as caught:
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
