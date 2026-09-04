"""
An authenticated Fidelity session, driven through a browser the USER owns.

--------------------------------------------------------------------
WHY THIS EXISTS INSTEAD OF fidelity-api

The reconnaissance (2026-09-01, from a DevTools HAR of a real session)
established that everything this project needs is plain JSON:

    POST /ftgw/digital/trade-equity/previewSrvc        -> mints confNum
    POST /ftgw/digital/trade-equity/placeOrder         -> takes/echoes confNum
    POST /ftgw/digital/trade-equity/cancelPlaceOrder   -> cancel by confNum
    POST /ftgw/digital/activityapi/api/v1/transactions/pending -> order list
    POST /ftgw/digital/traderplus-api/api/positions/v1 -> positions
    POST /ftgw/digital/trade-equity/balance            -> cash/settled

fidelity-api reads none of that. It clicks buttons and then waits up to
10 seconds for the literal DOM string "Order received", which is why it
can surface no order ID, no cancel, and no order status -- and why it
returns False for an order that is live at Fidelity if the confirmation
merely renders slowly. The JSON layer has all three, so the DOM layer is
simply the wrong place to be standing.

--------------------------------------------------------------------
WHY IT RUNS INSIDE THE USER'S OWN BROWSER

Fidelity refuses a Playwright-launched browser outright ("Sorry, we
can't complete this action right now"); the account is behind Akamai Bot
Manager, visible in the capture as sensor POSTs to an obfuscated path.
The same person signs in by hand without trouble.

So this attaches over CDP to a Chromium browser the user is already
running and already logged into, and issues every request with
`fetch()` executed INSIDE that authenticated page. Consequences, all of
which matter:

  * Session cookies are attached by the browser. This code never sees,
    stores, or transmits a credential -- there is nothing here to leak.
  * Requests are same-origin, so no CORS preflight and no header the
    page could not have sent itself.
  * What Akamai observes is the real browser making the same calls
    Trader+ makes, because that is precisely what is happening.

Nothing here defeats a bot check. It removes the reason for one.

--------------------------------------------------------------------
THE CSRF TOKEN IS SNIFFED, NOT CONFIGURED

Authenticated calls require `x-csrf-token`, plus `appid`/`appname`. The
token appears in no response body -- it is session-scoped and minted
somewhere in the page. Rather than hardcode a captured value (which
expires at the next login, turning a config into a time bomb), this
watches the page's own outgoing requests and lifts the headers from one.
That self-heals across rotation and requires no knowledge of Fidelity's
internals.

The cost is honest: a fresh session has no token until the page has made
at least one authenticated XHR. `wait_for_credentials` blocks for that
rather than issuing a request that would fail in a confusing way, and
`prime()` provokes one by navigating.

--------------------------------------------------------------------
SAFETY: READ-ONLY BY DEFAULT, ENFORCED BY AN ALLOWLIST

`post_json` refuses any endpoint outside READ_ONLY_ENDPOINTS unless the
session was constructed with `allow_order_endpoints=True`. This is not
decoration. A generic "POST arbitrary JSON to Fidelity" helper is one
typo away from submitting an order, and the plan this implements is
explicit that order placement stays gated behind a deliberate act. The
default must therefore be the safe one, and the unsafe one must be
spelled out at the construction site where a human can see it.

Session expiry raises FidelitySessionExpired rather than returning
something falsy. A semi-attended deployment -- the intended one -- must
halt and alert on expiry, never guess, and never let an auth failure be
mistaken for "no orders found".
"""

from __future__ import annotations

import contextlib
import json
import time
from typing import Any

from src.exceptions import ConfigurationError

FIDELITY_ORIGIN = "https://digital.fidelity.com"

# Read-only endpoints. Everything the strategy needs in order to observe
# state lives here; nothing here can create, modify, or cancel an order.
READ_ONLY_ENDPOINTS = frozenset(
    {
        "/ftgw/digital/activityapi/api/v1/transactions/pending",
        "/ftgw/digital/traderplus-api/api/positions/v1",
        "/ftgw/digital/traderplus-api/api/quotes/v1",
        "/ftgw/digital/trade-equity/balance",
        "/ftgw/digital/trade-equity/positions",
        "/ftgw/digital/trade-equity/getquote",
    }
)

# PREVIEW is separated from PLACE, and the split is load-bearing.
#
# Reconnaissance established that previewSrvc mints the confNum and
# commits nothing -- placeOrder takes that confNum as an INPUT. So a
# dry-run adapter needs preview and must never reach place, and a single
# allow_order_endpoints boolean covering both would have forced it to
# hold the capability it must not have. Splitting them lets dry-run be
# enforced by the TRANSPORT rather than by the adapter remembering not
# to call something.
#
# cancelPreviewOrder sits with preview: it only ever discards a preview.
PREVIEW_ENDPOINTS = frozenset(
    {
        "/ftgw/digital/trade-equity/previewSrvc",
        "/ftgw/digital/trade-equity/cancelPreviewOrder",
    }
)

# Endpoints that put a real order into, or take one out of, the market.
# cancelPlaceOrder is included deliberately: cancelling is state-changing
# and belongs behind the same gate, even though it only ever REDUCES
# exposure. A gate you can reason about beats one with exceptions in it.
PLACE_ENDPOINTS = frozenset(
    {
        "/ftgw/digital/trade-equity/placeOrder",
        "/ftgw/digital/trade-equity/cancelPlaceOrder",
    }
)

# Every state-changing endpoint, for the "is this known at all" check.
ORDER_ENDPOINTS = PREVIEW_ENDPOINTS | PLACE_ENDPOINTS

# Headers lifted from an observed request and replayed on ours. Only
# these three: everything else (cookies, sec-*, user-agent) is supplied
# by the browser itself, and overriding those from script would be both
# unnecessary and a way to look different from the real page.
#
# THESE ARE PER-SERVICE, NOT GLOBAL, and that cost a live order to learn.
# Fidelity's site is several backends behind one origin, and each brands
# its own appid/appname:
#
#     /ftgw/digital/trade-equity/   appid AP145890  "Trader Dashboard"
#     /ftgw/digital/activityapi/    appid AP182052  "Trader Plus Web"
#
# The first version kept ONE flat dict, so whichever service was seen
# last won and its appid was replayed everywhere. A real run placed an
# order through trade-equity perfectly and then got 403 reading the order
# back from activityapi -- with a message blaming the login, which was
# fine the whole time.
#
# Worse, the sniffer only recorded headers from requests carrying an
# x-csrf-token, and activityapi does not send one. Its headers were
# therefore never observable at all, so no amount of browsing would have
# fixed the replay.
_SNIFFED_HEADERS = ("x-csrf-token", "appid", "appname")

# The path segment after /ftgw/digital/ names the backend. Anything that
# does not match keeps its own bucket under the full prefix rather than
# being lumped in with a service it has nothing to do with.
_SERVICE_PREFIX = "/ftgw/digital/"


def service_of(path_or_url: str) -> str:
    """Which Fidelity backend a path belongs to.

    Used to key sniffed headers, so trade-equity's appid is never sent to
    activityapi and vice versa.
    """
    text = str(path_or_url or "")
    if "digital.fidelity.com" in text:
        text = text.split("digital.fidelity.com", 1)[1]
    text = text.split("?", 1)[0]
    if not text.startswith(_SERVICE_PREFIX):
        return text.strip("/").split("/")[0] or "?"
    remainder = text[len(_SERVICE_PREFIX) :]
    return remainder.split("/")[0] or "?"


# A page whose URL matches this is the sign-in flow, not a session.
_SIGNIN_MARKER = "/prgw/digital/signin"
_AUTHENTICATED_MARKER = "/ftgw/digital/"


class FidelitySessionError(RuntimeError):
    """Base for session problems that are not configuration mistakes."""


class FidelitySessionExpired(FidelitySessionError):
    """The browser session is no longer authenticated.

    Distinct from a transport error on purpose. The correct response is
    to halt new buys and alert a human to log in again -- not to retry,
    which cannot succeed, and not to treat the failure as an empty
    result, which would make "session expired" indistinguishable from
    "you have no open orders" at exactly the moment that distinction
    matters most.
    """


class FidelitySession:
    """Issues authenticated JSON calls from inside the user's own page."""

    def __init__(
        self,
        page: Any,
        *,
        allow_order_endpoints: bool = False,
        allow_preview_endpoints: bool = False,
        request_timeout_ms: int = 30_000,
    ) -> None:
        self._page = page
        self._allow_order_endpoints = bool(allow_order_endpoints)
        # Placing implies previewing -- placeOrder needs a confNum that
        # only previewSrvc mints -- so granting the stronger capability
        # grants the weaker one. The reverse is never true.
        self._allow_preview_endpoints = bool(allow_preview_endpoints or allow_order_endpoints)
        self._request_timeout_ms = request_timeout_ms
        # service -> {header: value}. Never a flat dict again.
        self._headers: dict[str, dict[str, str]] = {}
        self._attached = False

    # -- credential sniffing -------------------------------------------

    def attach(self) -> None:
        """Start watching the page's own requests for the auth headers."""
        if self._attached:
            return
        self._page.on("request", self._on_request)
        self._attached = True

    def _on_request(self, request: Any) -> None:
        """Lift auth headers per BACKEND from the page's own calls.

        Deliberately does NOT require an x-csrf-token to record a
        request. The first version did, and that silently excluded every
        service which does not use one -- activityapi among them -- so
        its appid could never be learned and another service's was sent
        instead, drawing a 403 that read like an expired login.

        A request is recorded when it carries any header we replay AND is
        aimed at Fidelity's own origin. Requests to third parties (the
        site loads a device-fingerprinting iframe, among others) are
        ignored: their headers are not ours to replay and could carry a
        vendor's identifiers into our calls.

        Never raises: this runs inside a Playwright event handler, where
        an exception would surface in the middle of whatever page
        interaction happened to be in flight.
        """
        try:
            url = str(request.url or "")
            if "digital.fidelity.com" not in url:
                return
            lowered = {str(k).lower(): str(v) for k, v in (request.headers or {}).items()}
            found = {name: lowered[name] for name in _SNIFFED_HEADERS if lowered.get(name)}
            if not found:
                return
            self._headers.setdefault(service_of(url), {}).update(found)
        except Exception:
            return

    def headers_for(self, path: str) -> dict[str, str]:
        """The sniffed headers for the backend `path` belongs to.

        Empty when that backend has not been observed yet. Returning
        another service's headers instead is exactly the bug this
        replaced, so an empty result is reported as empty.
        """
        return dict(self._headers.get(service_of(path), {}))

    @property
    def observed_services(self) -> tuple[str, ...]:
        """Backends whose headers have been seen. Useful in diagnostics."""
        return tuple(sorted(self._headers))

    @property
    def has_credentials(self) -> bool:
        """True once ANY Fidelity backend has shown us a CSRF token.

        Still the right proxy for "is this session authenticated at all",
        even though the token itself is per-service: an unauthenticated
        page never produces one anywhere.
        """
        return any("x-csrf-token" in headers for headers in self._headers.values())

    @property
    def csrf_token(self) -> str | None:
        for headers in self._headers.values():
            token = headers.get("x-csrf-token")
            if token:
                return token
        return None

    def wait_for_credentials(self, timeout_seconds: float = 60.0) -> None:
        """Block until the page has made an authenticated request.

        Better than issuing a call that would fail with an opaque 403:
        the reason we cannot proceed yet is "no token seen", and that is
        what the error should say.
        """
        if not self._attached:
            raise ConfigurationError(
                "attach() must be called before wait_for_credentials(); nothing "
                "is watching the page's requests yet."
            )
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self.has_credentials:
                return
            time.sleep(0.5)
        raise FidelitySessionError(
            f"No authenticated request observed within {timeout_seconds:.0f}s, so no "
            "x-csrf-token could be captured. The page may be idle -- call prime(), "
            "or interact with Trader+ so it issues a request."
        )

    def prime(self, url: str | None = None) -> None:
        """Provoke an authenticated request so headers can be sniffed.

        Navigating is the least surprising way to do it: it is what the
        human would do, and it is what the page is built to respond to.
        """
        target = url or f"{FIDELITY_ORIGIN}/ftgw/digital/traderplus"
        self._page.goto(target)
        with contextlib.suppress(Exception):
            self._page.wait_for_load_state("networkidle")

    # -- session validity ----------------------------------------------

    def assert_authenticated(self) -> None:
        """Raise if the page is sitting on the sign-in flow."""
        try:
            url = str(self._page.url)
        except Exception as exc:
            raise FidelitySessionExpired(f"The page is gone: {exc}") from exc
        if _SIGNIN_MARKER in url:
            raise FidelitySessionExpired(
                f"The browser is on Fidelity's sign-in page ({url}). Log in again; "
                "this session cannot issue authenticated calls."
            )

    # -- the request itself ---------------------------------------------

    def post_json(self, path: str, payload: dict | list) -> Any:
        """POST JSON to `path` from inside the authenticated page.

        `path` is a site-relative path, never a full URL: this can only
        ever talk to Fidelity's own origin, and accepting a full URL
        would make that a matter of the caller getting it right.
        """
        if not path.startswith("/"):
            raise ConfigurationError(f"path must be site-relative and start with '/', got {path!r}")
        if path in PLACE_ENDPOINTS and not self._allow_order_endpoints:
            raise ConfigurationError(
                f"{path} PLACES OR CANCELS A REAL ORDER and this session does not "
                "permit that. Construct FidelitySession(..., "
                "allow_order_endpoints=True) to allow it -- deliberately, at a call "
                "site a human can see. A dry-run caller wants "
                "allow_preview_endpoints=True instead, which can never reach here."
            )
        if path in PREVIEW_ENDPOINTS and not self._allow_preview_endpoints:
            raise ConfigurationError(
                f"{path} is an order-preview endpoint and this session was created "
                "read-only. Construct FidelitySession(..., "
                "allow_preview_endpoints=True) to permit it. Preview commits "
                "nothing, but it does open a ticket against a real account."
            )
        if path not in READ_ONLY_ENDPOINTS and path not in ORDER_ENDPOINTS:
            raise ConfigurationError(
                f"{path} is not a known Fidelity endpoint. Add it to "
                "READ_ONLY_ENDPOINTS or ORDER_ENDPOINTS in src/fidelity_session.py "
                "after confirming from a capture what it does -- an allowlist that "
                "silently accepts anything is not an allowlist."
            )
        if not self.has_credentials:
            raise FidelitySessionError(
                "No x-csrf-token captured yet -- call attach() then "
                "wait_for_credentials() (or prime()) first."
            )

        self.assert_authenticated()

        # The headers for THIS backend, never another's. An empty set is
        # sent as-is rather than back-filled from a service that happens
        # to have been seen: a wrong appid is not better than none, and
        # _interpret says so if the venue refuses.
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            **self.headers_for(path),
        }
        # Executed in the PAGE, so the browser attaches cookies and the
        # request is same-origin. credentials:"same-origin" is explicit
        # rather than relying on the fetch default, which has changed
        # across specification revisions.
        script = """
        async ([path, payload, headers, timeoutMs]) => {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), timeoutMs);
            try {
                const response = await fetch(path, {
                    method: "POST",
                    headers: headers,
                    body: JSON.stringify(payload),
                    credentials: "same-origin",
                    signal: controller.signal,
                });
                const text = await response.text();
                return {status: response.status, url: response.url, body: text};
            } finally {
                clearTimeout(timer);
            }
        }
        """
        try:
            result = self._page.evaluate(script, [path, payload, headers, self._request_timeout_ms])
        except Exception as exc:
            raise FidelitySessionError(f"POST {path} failed in the page: {exc}") from exc

        return self._interpret(path, result)

    def _interpret(self, path: str, result: dict) -> Any:
        status = int(result.get("status", 0))
        body = result.get("body") or ""
        final_url = str(result.get("url") or "")

        # An expired session most often shows up as a redirect INTO the
        # sign-in flow with a 200, not as a 401 -- which is exactly how a
        # naive caller ends up parsing a login page as though it were an
        # empty order list.
        if _SIGNIN_MARKER in final_url:
            raise FidelitySessionExpired(
                f"POST {path} was redirected to the sign-in flow ({final_url}); "
                "the session has expired. Log in again."
            )
        if status in (401, 403):
            # A 403 is NOT proof the login died. This exact message once
            # followed a perfectly good session that had just placed an
            # order: the call went out with another backend's appid,
            # because none had been observed for this one. Say which case
            # it is rather than sending an operator to re-authenticate a
            # session that is fine.
            service = service_of(path)
            if not self.headers_for(path):
                raise FidelitySessionError(
                    f"POST {path} returned {status}, and NO headers have been "
                    f"observed for the {service!r} backend -- the request went out "
                    "without the appid/appname that backend expects.\n"
                    f"    observed so far: {list(self.observed_services) or 'none'}\n"
                    "This is very likely a header problem, NOT an expired login. "
                    "Open the page that uses this backend (for transactions/pending "
                    "that is Orders / Activity) so its headers can be sniffed, then "
                    "retry."
                )
            raise FidelitySessionExpired(
                f"POST {path} returned {status} using the {service!r} backend's own "
                "observed headers. The session or CSRF token is no longer valid; "
                "log in again."
            )
        if status >= 400:
            raise FidelitySessionError(f"POST {path} returned {status}: {body[:300]}")

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            # HTML where JSON was expected is nearly always an interstitial
            # or an error page, so say that rather than reporting a parse
            # error at column 1.
            hint = " (looks like HTML, not JSON)" if body.lstrip()[:1] == "<" else ""
            raise FidelitySessionError(
                f"POST {path} returned {status} but the body did not parse as "
                f"JSON{hint}: {body[:200]}"
            ) from exc
