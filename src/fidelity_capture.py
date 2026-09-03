"""Network-layer traffic capture for the Fidelity browser session.

WHY THIS EXISTS
---------------
`fidelity-api` surfaces no order ID. It clicks submit and then waits up to
10s for the literal DOM string "Order received" -- there is no order-ID
return, no lookup-by-ID, no cancel, and no order-status query anywhere in
its 1,588 lines. That is a problem for this repo specifically, because the
entire safety architecture is built on `client_order_id` round-tripping:
`duplicate_order_guard.resolve_ambiguous_submission` queries the broker by
it, `reconciliation._reconcile_orders` keys `snapshot.orders` by it, and
`live_trading_loop` reads `.id` off the object a submit returns.

The DOM is the wrong place to read that from. The answer, if it exists at
all, is in the traffic underneath it -- and Playwright can see all of it.
This module is the listener that watches.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not parse. No Fidelity-specific field names, no payload schema, no
"the order ID is at `data.orderId`". Nothing here knows what an order
looks like, because at the time of writing NOBODY here knows what Fidelity
actually transmits on submit -- whether an ID comes back over WebSocket,
over XHR, or not at all. That question is settled empirically by running
`fidelity_recon.py` and reading the dump, not by guessing in advance.
Writing a parser before seeing the data would be inventing a format.

So this records, verbatim (modulo scrubbing, below), and stops there.
`candidate_id_fields()` is a *recon aid* -- it greps captured JSON for
key names that look like they might carry an ID, to point a human at the
interesting payloads. It is not a parser and nothing should depend on it.

NO PLAYWRIGHT IMPORT
--------------------
This module never imports playwright, and is duck-typed on the `page`
object. That is deliberate: it keeps `requirements-fidelity.txt` optional
(the Dockerfile installs only `requirements.txt`), and it means the whole
module is unit-testable by driving it with a fake page that emits
synthetic frames -- no browser, no network, no credentials. The tests do
exactly that.

THE DUMP FILE IS CREDENTIAL-EQUIVALENT
--------------------------------------
Captured traffic from an authenticated brokerage session contains session
tokens, account numbers, and -- during login -- the password itself, in
the request body. Two defenses, and neither is sufficient alone:

1. `secret_values`: literal scrubbing. The caller passes the exact
   credential strings it already holds, and any occurrence of them in any
   payload is replaced before it is ever stored. This is exact rather
   than heuristic, which is why it is the primary defense.
2. Key-based redaction via `redact_secrets` on JSON bodies, for the
   tokens we do not know the values of in advance.

Request headers are never captured at all -- `Cookie` and `Authorization`
live there and have no recon value.

Even so: treat the dump as a secret. It is gitignored and dockerignored,
and `fidelity_recon.py` writes it outside the repo by default.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from src.secrets import REDACTED, redact_secrets

# Per-payload cap. A brokerage page streams a lot -- quote ticks over
# WebSocket, JS bundles over XHR -- and an unbounded recorder attached for
# a whole session is a memory leak with a nice name. Truncated payloads are
# marked (see _TRUNCATION_MARKER) so a reader never mistakes a cut-off body
# for a complete one.
DEFAULT_MAX_PAYLOAD_BYTES = 200_000

# Total records across both streams. Chosen to comfortably hold a login +
# navigation + one order preview with room to spare; the point is only to
# bound a runaway, not to ration.
DEFAULT_MAX_RECORDS = 20_000

_TRUNCATION_MARKER = "...[TRUNCATED]"

# Resource types worth recording. Quote streams and order round-trips are
# xhr/fetch; everything else on a brokerage page is JS bundles, fonts,
# images, and CSS, which are megabytes of noise with no recon value.
DEFAULT_RESOURCE_TYPES = frozenset({"xhr", "fetch"})

# Hosts whose WebSocket frames are worth recording. Observed in a real
# session (2026-09-02):
#   spservice.fidelity.com/event/realtime  -- ORDER LIFECYCLE EVENTS, the
#       reason this capture exists at all. accounts.orders.updated /
#       accounts.orders.canceled, keyed by CONFIRMATION_NUM.
#   mdds-i-tc.fidelity.com                 -- the quote stream. 3,057 of
#       3,058 frames in one session were market data this project already
#       gets from Alpaca. Allowed anyway: it is Fidelity's, it is cheap to
#       drop later, and excluding it would make "no quotes seen" ambiguous.
#   prod-presence-1.glance.net             -- NOT LISTED. A third-party
#       co-browsing vendor. See _on_websocket for why that matters.
DEFAULT_WEBSOCKET_HOSTS = frozenset({"fidelity.com"})

# Key names that MIGHT carry an order identifier. Used only by
# candidate_id_fields() to point a human at interesting payloads -- this is
# a search hint, not a schema. Deliberately broad: a false positive costs a
# glance, a false negative costs a missed answer.
_ID_KEY_PATTERN = re.compile(
    r"(order.?(id|num|number|ref|reference)|confirm(ation)?.?(id|num|number|code)"
    r"|transaction.?id|client.?(order.?)?id|trade.?id)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CapturedFrame:
    """One WebSocket frame, in whichever direction."""

    direction: str  # "sent" | "received"
    url: str
    payload: str
    at: str  # ISO-8601 UTC
    truncated: bool = False
    binary: bool = False


@dataclass(frozen=True)
class CapturedResponse:
    """One HTTP response. Headers are deliberately absent -- see module docstring."""

    url: str
    method: str
    status: int
    resource_type: str
    body: str | None  # None when the body could not be read at all
    at: str  # ISO-8601 UTC
    truncated: bool = False
    body_error: str | None = None


class TrafficCapture:
    """Records WebSocket frames and HTTP response bodies from a Playwright page.

    Attach BEFORE navigation. Playwright only delivers events for
    activity that happens after a listener is registered, and
    `FidelityAutomation.__init__` launches the browser without navigating
    (`login()` is a separate call), so the hook point is:

        fid = FidelityAutomation(...)   # browser + page exist, nothing loaded
        capture = TrafficCapture(secret_values=[password, ...])
        capture.attach(fid.page)        # listeners live before any traffic
        fid.login(...)                  # captured from the first byte

    Handlers never raise. An exception thrown inside a Playwright event
    handler surfaces in the middle of whatever page interaction happened
    to be in flight, which would turn a capture bug into a trading bug.
    Failures are recorded in `handler_errors` and swallowed.
    """

    def __init__(
        self,
        secret_values: list[str] | None = None,
        resource_types: frozenset[str] | None = None,
        max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
        max_records: int = DEFAULT_MAX_RECORDS,
        websocket_host_allowlist: frozenset[str] | None = None,
    ) -> None:
        # Empty strings are dropped: `"" in payload` is always True, so a
        # blank credential would scrub every payload down to nothing.
        self._secret_values = [s for s in (secret_values or []) if s]
        self._resource_types = DEFAULT_RESOURCE_TYPES if resource_types is None else resource_types
        self._max_payload_bytes = max_payload_bytes
        self._max_records = max_records
        self._ws_hosts = (
            DEFAULT_WEBSOCKET_HOSTS
            if websocket_host_allowlist is None
            else websocket_host_allowlist
        )

        # Recorded by URL only, never by content, so a dump still SHOWS
        # that a socket was skipped. "No frames from X" and "X was never
        # opened" look identical otherwise, and this project has already
        # mistaken an absent record for an absent thing once.
        self._out_of_scope_websockets: list[str] = []

        self.frames: list[CapturedFrame] = []
        self.responses: list[CapturedResponse] = []
        self.handler_errors: list[str] = []
        self.dropped_records = 0

        # A LIST, not a single page. The original design assumed one
        # page for the whole session and refused a second attach. That
        # assumption cost a real recon run: Fidelity's sign-in moves the
        # user to a different page object, so a capture bound to the
        # original tab recorded nothing at all while the human browsed a
        # fully authenticated session next to it. Pages are now tracked
        # individually and attaching to several is the normal case.
        self._attached_pages: list[Any] = []
        self._attached_context: Any | None = None

    # -- attachment ----------------------------------------------------

    def attach(self, page: Any) -> None:
        """Register listeners on a Playwright Page.

        Idempotent per page: attaching twice would double-record every
        frame, which is not obviously wrong when reading a dump, so a
        repeat attach to the SAME page is ignored. Attaching to several
        DIFFERENT pages is supported and expected -- see attach_context.
        """
        for existing in self._attached_pages:
            if existing is page:
                return
        page.on("websocket", self._on_websocket)
        page.on("response", self._on_response)
        self._attached_pages.append(page)

    def attach_context(self, context: Any) -> None:
        """Attach to every page in a BrowserContext, now and in future.

        This is the one that matches how a real browsing session behaves.
        A login flow, a popup, or a "open in new tab" all produce page
        objects that did not exist when capture started, and traffic on
        them is invisible to a listener bound to the original page.

        Registering for the context's own "page" event means a tab opened
        after this call is captured from its first byte, rather than from
        whenever someone noticed it was missing.
        """
        if self._attached_context is context:
            return
        for page in list(getattr(context, "pages", []) or []):
            self.attach(page)
        try:
            context.on("page", self._on_new_page)
        except Exception as exc:  # never propagate into page interaction
            self._note_error("context", exc)
        self._attached_context = context

    def _on_new_page(self, page: Any) -> None:
        try:
            self.attach(page)
        except Exception as exc:  # never propagate into page interaction
            self._note_error("newpage", exc)

    @property
    def attached_page_count(self) -> int:
        """How many pages are being recorded -- surfaced so a caller can
        report it, since 'captured nothing' and 'attached to nothing' look
        identical in a dump and have completely different causes."""
        return len(self._attached_pages)

    # -- handlers ------------------------------------------------------

    def _on_websocket(self, ws: Any) -> None:
        try:
            url = str(getattr(ws, "url", ""))
            if not self._websocket_in_scope(url):
                # NOT a size optimisation. A real Fidelity session opens a
                # socket to prod-presence-1.glance.net, a third-party
                # co-browsing vendor, and recording it would write another
                # company's traffic into a dump that already carries this
                # session's secrets. Recon should collect what it came for
                # and nothing else -- the same discipline the REST endpoint
                # allowlists already apply.
                self._out_of_scope_websockets.append(url)
                return
            ws.on("framesent", lambda payload: self._on_frame("sent", url, payload))
            ws.on(
                "framereceived",
                lambda payload: self._on_frame("received", url, payload),
            )
        except Exception as exc:  # never propagate into page interaction
            self._note_error("websocket", exc)

    def _websocket_in_scope(self, url: str) -> bool:
        """True when `url`'s host ends with an allowlisted domain.

        Suffix match on the HOST, not a substring match on the whole URL:
        "fidelity.com" appears in a query string as easily as in a host,
        and `evil-fidelity.com.attacker.net` would pass a naive `in` test.
        """
        try:
            host = urlparse(url).hostname or ""
        except ValueError:
            return False
        host = host.lower()
        return any(host == d or host.endswith("." + d) for d in self._ws_hosts)

    def _on_frame(self, direction: str, url: str, payload: Any) -> None:
        try:
            if not self._has_room():
                return
            binary = isinstance(payload, bytes | bytearray)
            if binary:  # noqa: SIM108 -- the comment belongs to this branch
                # Binary frames are decoded leniently rather than dropped:
                # a JSON body sent as bytes is common and readable, and a
                # genuinely binary frame still yields a recognizable shape.
                text = bytes(payload).decode("utf-8", errors="replace")
            else:
                text = str(payload)
            text, truncated = self._truncate(self._scrub(text))
            self.frames.append(
                CapturedFrame(
                    direction=direction,
                    url=url,
                    payload=text,
                    at=_now(),
                    truncated=truncated,
                    binary=binary,
                )
            )
        except Exception as exc:
            self._note_error("frame", exc)

    def _on_response(self, response: Any) -> None:
        try:
            request = getattr(response, "request", None)
            resource_type = str(getattr(request, "resource_type", "") or "")
            if self._resource_types and resource_type not in self._resource_types:
                return
            if not self._has_room():
                return

            body: str | None = None
            body_error: str | None = None
            truncated = False
            try:
                # .text() throws for redirects, for bodies already
                # discarded, and for responses whose request was aborted.
                # A response we cannot read is still worth recording --
                # knowing an endpoint was called matters even without its
                # payload -- so the failure is captured, not the record
                # dropped.
                raw = response.text()
                body, truncated = self._truncate(self._scrub(self._redact_json(raw)))
            except Exception as exc:
                body_error = f"{type(exc).__name__}: {exc}"

            self.responses.append(
                CapturedResponse(
                    url=self._scrub(str(getattr(response, "url", ""))),
                    method=str(getattr(request, "method", "") or ""),
                    status=int(getattr(response, "status", 0) or 0),
                    resource_type=resource_type,
                    body=body,
                    at=_now(),
                    truncated=truncated,
                    body_error=body_error,
                )
            )
        except Exception as exc:
            self._note_error("response", exc)

    # -- scrubbing -----------------------------------------------------

    def _scrub(self, text: str) -> str:
        """Replace literal credential values wherever they appear.

        Exact, not heuristic. The caller already holds these strings, so
        there is no reason to guess at them -- and the login POST body
        contains the password verbatim, which no key-name heuristic would
        reliably catch across an unknown form encoding.
        """
        for secret in self._secret_values:
            if secret in text:
                text = text.replace(secret, REDACTED)
        return text

    def _redact_json(self, text: str) -> str:
        """Key-based redaction for JSON bodies, for tokens whose values we
        do not know in advance (session tokens, bearer tokens, CSRF).

        Non-JSON bodies pass through untouched -- guessing at the
        structure of an unknown format is how a redactor destroys the
        thing it was supposed to preserve. Literal scrubbing above still
        applies to those.
        """
        stripped = text.lstrip()
        if not stripped.startswith(("{", "[")):
            return text
        try:
            parsed = json.loads(text)
        except (ValueError, RecursionError):
            return text
        try:
            return json.dumps(redact_secrets(parsed))
        except (TypeError, ValueError):
            return text

    def _truncate(self, text: str) -> tuple[str, bool]:
        if len(text) <= self._max_payload_bytes:
            return text, False
        return text[: self._max_payload_bytes] + _TRUNCATION_MARKER, True

    def _has_room(self) -> bool:
        if len(self.frames) + len(self.responses) >= self._max_records:
            self.dropped_records += 1
            return False
        return True

    def _note_error(self, where: str, exc: Exception) -> None:
        # Bounded: a handler that fails once usually fails on every event,
        # and an unbounded error list would be the same memory leak the
        # record caps exist to prevent.
        if len(self.handler_errors) < 100:
            self.handler_errors.append(f"{where}: {type(exc).__name__}: {exc}")

    # -- output --------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """Counts and endpoint inventory -- safe to print to a terminal."""
        ws_urls: dict[str, int] = {}
        for frame in self.frames:
            ws_urls[frame.url] = ws_urls.get(frame.url, 0) + 1
        endpoints: dict[str, int] = {}
        for response in self.responses:
            key = f"{response.method} {_strip_query(response.url)}"
            endpoints[key] = endpoints.get(key, 0) + 1
        return {
            "frames": len(self.frames),
            "responses": len(self.responses),
            "websocket_urls": ws_urls,
            "endpoints": endpoints,
            "handler_errors": list(self.handler_errors),
            "dropped_records": self.dropped_records,
        }

    def candidate_id_fields(self) -> list[dict[str, Any]]:
        """Records whose JSON contains a key that LOOKS like an order ID.

        A recon aid for a human reading the dump, nothing more. It answers
        "which of these 4,000 payloads should I look at first", not "what
        is the order ID". Nothing should ever depend on its output.
        """
        hits: list[dict[str, Any]] = []
        for index, frame in enumerate(self.frames):
            found = _find_id_keys(frame.payload)
            if found:
                hits.append(
                    {
                        "kind": "frame",
                        "index": index,
                        "url": frame.url,
                        "direction": frame.direction,
                        "keys": found,
                    }
                )
        for index, response in enumerate(self.responses):
            found = _find_id_keys(response.body or "")
            if found:
                hits.append(
                    {
                        "kind": "response",
                        "index": index,
                        "url": response.url,
                        "method": response.method,
                        "keys": found,
                    }
                )
        return hits

    def to_dict(self) -> dict[str, Any]:
        return {
            "captured_at": _now(),
            "summary": self.summary(),
            "candidate_id_fields": self.candidate_id_fields(),
            "frames": [asdict(f) for f in self.frames],
            "responses": [asdict(r) for r in self.responses],
        }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _strip_query(url: str) -> str:
    return url.split("?", 1)[0]


def _find_id_keys(text: str) -> list[str]:
    """Key names matching the ID heuristic, found anywhere in a JSON blob.

    Walks parsed JSON rather than regexing the raw text so that a match is
    genuinely a KEY and not a value that happens to contain the word
    "order". Non-JSON payloads return nothing -- they are still in the
    dump for a human to read; they just do not get a hint attached.
    """
    stripped = text.lstrip()
    if not stripped.startswith(("{", "[")):
        return []
    try:
        parsed = json.loads(text)
    except (ValueError, RecursionError):
        return []

    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if _ID_KEY_PATTERN.search(str(key)) and str(key) not in found:
                    found.append(str(key))
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(parsed)
    return found
