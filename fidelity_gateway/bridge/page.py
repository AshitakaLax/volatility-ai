"""
A Playwright Page, as far as FidelitySession can tell -- backed by the
Fidelity Bridge extension instead of a debugging port.

FidelitySession only ever does six things with its page: on("request"),
url, goto(), wait_for_load_state(), wait_for_timeout() and evaluate().
This class does those six over the bridge, so the session -- with every
gate in it -- works unchanged, and so does every broker built on it.

Two properties are kept on purpose:

  * evaluate() runs NO script. It accepts only session.FETCH_SCRIPT and
    turns its arguments into the extension's fixed `fetch` command;
    anything else is refused before it leaves the engine. The extension
    could not run a script anyway -- this makes the refusal local and
    loud rather than a remote error code.

  * Events (observed auth headers, the tab's URL) are delivered to
    handlers ON THE CALLER'S THREAD, inside url/goto/evaluate/waits --
    the same moments Playwright's sync API delivers them. Handlers never
    run concurrently with the session's own code, so nothing in it needs
    a lock.
"""

from __future__ import annotations

import contextlib
import time
from typing import Any

from fidelity_gateway.bridge.server import BridgeRefusal, BridgeServer
from fidelity_gateway.session import FETCH_SCRIPT

NAVIGATION_TIMEOUT_SECONDS = 45.0
# Slack on top of the fetch's own timeout, for the round trip to the
# extension and back.
REQUEST_SLACK_SECONDS = 15.0
# After a navigation, how long to keep listening for the requests the new
# page makes -- they carry the headers prime() navigated to provoke.
SETTLE_SECONDS = 2.0


class BridgeRequest:
    """What a Playwright Request offers FidelitySession._on_request."""

    def __init__(self, url: str, headers: dict) -> None:
        self.url = url
        self.headers = headers


class BridgePage:
    def __init__(self, server: BridgeServer, *, settle_seconds: float = SETTLE_SECONDS) -> None:
        self._server = server
        self._settle_seconds = settle_seconds
        self._handlers: dict[str, list] = {}
        self._url = ""

    # -- events -------------------------------------------------------------

    def on(self, event: str, handler: Any) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def _deliver(self, event: tuple[str, dict]) -> None:
        name, data = event
        if name == "tab":
            url = data.get("url")
            self._url = url if isinstance(url, str) else ""
        elif name == "request":
            url, headers = data.get("url"), data.get("headers")
            if not isinstance(url, str) or not isinstance(headers, dict):
                return
            request = BridgeRequest(url, {str(k): str(v) for k, v in headers.items()})
            for handler in self._handlers.get("request", []):
                # A handler's failure is not the page's: keep delivering.
                with contextlib.suppress(Exception):
                    handler(request)

    def _drain(self) -> None:
        while (event := self._server.next_event(0)) is not None:
            self._deliver(event)

    # -- the Page surface FidelitySession uses ------------------------------

    @property
    def url(self) -> str:
        """The Fidelity tab's URL as last reported, or "" with no tab."""
        self._drain()
        return self._url

    def wait_for_timeout(self, ms: float) -> None:
        deadline = time.monotonic() + max(0.0, float(ms)) / 1000
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._drain()
                return
            event = self._server.next_event(remaining)
            if event is not None:
                self._deliver(event)

    def goto(self, url: str, **_kwargs: Any) -> None:
        """Send the Fidelity tab to `url`. The extension only goes to pages
        under https://digital.fidelity.com/ftgw/digital/ and waits for the
        load to finish."""
        self._drain()
        result = self._server.request("navigate", {"url": url}, timeout=NAVIGATION_TIMEOUT_SECONDS)
        tab_url = result.get("tabUrl")
        self._url = tab_url if isinstance(tab_url, str) and tab_url else url
        self._drain()

    def wait_for_load_state(self, state: str = "load", **_kwargs: Any) -> None:
        """goto() already waited for the load; this keeps listening a
        little longer for the requests the new page makes."""
        self.wait_for_timeout(self._settle_seconds * 1000)

    def evaluate(self, script: str, arg: Any = None) -> dict:
        if script != FETCH_SCRIPT:
            raise BridgeRefusal(
                "The Fidelity bridge runs no scripts. It sends Fidelity JSON requests "
                "through the extension's fixed fetch, and nothing else.",
                code="no_scripts",
            )
        path, payload, headers, timeout_ms = arg
        self._drain()
        result = self._server.request(
            "fetch",
            {"path": path, "body": payload, "headers": headers, "timeoutMs": int(timeout_ms)},
            timeout=int(timeout_ms) / 1000 + REQUEST_SLACK_SECONDS,
        )
        tab_url = result.get("tabUrl")
        if isinstance(tab_url, str) and tab_url:
            self._url = tab_url
        self._drain()
        return {
            "status": result.get("status"),
            "url": result.get("url"),
            "body": result.get("body"),
        }
