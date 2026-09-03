"""Tests for FidelitySession -- authenticated JSON calls via the user's browser.

No browser, no network, no account. A fake page stands in for a
Playwright Page, which is enough because the module's whole job is
deciding WHAT to send, WHETHER it is allowed, and HOW to read the answer.

The properties that matter most, and why:

  * An order endpoint is refused unless the session was explicitly built
    to allow it. A generic "POST JSON to Fidelity" helper is otherwise
    one typo from submitting a real order.
  * An expired session RAISES. If it returned something falsy instead,
    "your session died" and "you have no open orders" would be the same
    value at the moment that difference matters most.
  * The CSRF token is sniffed, never configured -- a captured token
    expires at the next login.
"""

from __future__ import annotations

import json

import pytest

from src.exceptions import ConfigurationError
from src.fidelity_session import (
    FIDELITY_ORIGIN,
    ORDER_ENDPOINTS,
    PLACE_ENDPOINTS,
    PREVIEW_ENDPOINTS,
    READ_ONLY_ENDPOINTS,
    FidelitySession,
    FidelitySessionError,
    FidelitySessionExpired,
)

PENDING = "/ftgw/digital/activityapi/api/v1/transactions/pending"
PLACE = "/ftgw/digital/trade-equity/placeOrder"
SIGNED_IN = f"{FIDELITY_ORIGIN}/ftgw/digital/traderplus"
SIGNIN = f"{FIDELITY_ORIGIN}/prgw/digital/signin/retail"


class FakeRequest:
    def __init__(self, headers):
        self.headers = headers


class FakePage:
    def __init__(self, url=SIGNED_IN, result=None, raises=None):
        self.url = url
        self.handlers = {}
        self.evaluated = []
        self.goto_urls = []
        self._result = result or {"status": 200, "url": SIGNED_IN, "body": "{}"}
        self._raises = raises

    def on(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)

    def emit_request(self, headers):
        for handler in self.handlers.get("request", []):
            handler(FakeRequest(headers))

    def evaluate(self, script, arg):
        self.evaluated.append(arg)
        if self._raises:
            raise self._raises
        return self._result

    def goto(self, url):
        self.goto_urls.append(url)

    def wait_for_load_state(self, *a, **k):
        pass


AUTH_HEADERS = {
    "x-csrf-token": "TOKEN-ABC",
    "appid": "AP145890",
    "appname": "Trader Dashboard",
    "cookie": "should-not-be-replayed",
}


def _ready(**kw):
    page = FakePage(**kw)
    session = FidelitySession(page, **kw.pop("session_kw", {}))
    session.attach()
    page.emit_request(AUTH_HEADERS)
    return session, page


def _ready_with(result=None, allow_orders=False, url=SIGNED_IN, raises=None,
                allow_preview=False):
    page = FakePage(url=url, result=result, raises=raises)
    session = FidelitySession(
        page,
        allow_order_endpoints=allow_orders,
        allow_preview_endpoints=allow_preview,
    )
    session.attach()
    page.emit_request(AUTH_HEADERS)
    return session, page


# -- credential sniffing -----------------------------------------------


def test_the_csrf_token_is_lifted_from_the_pages_own_request():
    session, _page = _ready_with()
    assert session.has_credentials is True
    assert session.csrf_token == "TOKEN-ABC"


def test_requests_without_a_csrf_token_are_ignored():
    """Most requests a page makes are not authenticated calls."""
    page = FakePage()
    session = FidelitySession(page)
    session.attach()
    page.emit_request({"accept": "application/json"})
    assert session.has_credentials is False


def test_header_names_are_matched_case_insensitively():
    page = FakePage()
    session = FidelitySession(page)
    session.attach()
    page.emit_request({"X-CSRF-Token": "MIXED", "AppId": "AP1"})
    assert session.csrf_token == "MIXED"


def test_a_sniffing_failure_never_escapes_into_the_page():
    """This runs inside a Playwright event handler -- an exception would
    surface in the middle of an unrelated page interaction."""

    class Hostile:
        @property
        def headers(self):
            raise RuntimeError("boom")

    page = FakePage()
    session = FidelitySession(page)
    session.attach()
    for handler in page.handlers["request"]:
        handler(Hostile())  # must not raise
    assert session.has_credentials is False


def test_only_the_three_auth_headers_are_replayed():
    """Cookies and sec-* headers are the browser's business. Replaying
    them from script is unnecessary and would make our request look
    unlike the page's own."""
    session, page = _ready_with()
    session.post_json(PENDING, {})
    sent_headers = page.evaluated[0][2]
    assert sent_headers["x-csrf-token"] == "TOKEN-ABC"
    assert "cookie" not in sent_headers


def test_wait_for_credentials_requires_attach_first():
    session = FidelitySession(FakePage())
    with pytest.raises(ConfigurationError, match="attach"):
        session.wait_for_credentials(timeout_seconds=0.1)


def test_wait_for_credentials_times_out_with_an_actionable_message():
    page = FakePage()
    session = FidelitySession(page)
    session.attach()
    with pytest.raises(FidelitySessionError, match="prime"):
        session.wait_for_credentials(timeout_seconds=0.2)


def test_prime_navigates_to_traderplus_to_provoke_a_request():
    page = FakePage()
    FidelitySession(page).prime()
    assert page.goto_urls == [f"{FIDELITY_ORIGIN}/ftgw/digital/traderplus"]


# -- the order-endpoint gate -------------------------------------------


@pytest.mark.parametrize("path", sorted(ORDER_ENDPOINTS))
def test_order_endpoints_are_refused_on_a_read_only_session(path):
    """Every state-changing endpoint, preview and place alike.

    Matches on the refusal, not on the wording: preview and place now
    give different messages because they are different capabilities, and
    pinning the prose would make this test about the sentence rather
    than about the gate.
    """
    session, _ = _ready_with()
    with pytest.raises(ConfigurationError):
        session.post_json(path, {})


@pytest.mark.parametrize("path", sorted(PLACE_ENDPOINTS))
def test_preview_permission_never_unlocks_placing(path):
    """THE POINT OF THE SPLIT.

    A dry-run adapter holds allow_preview_endpoints and must not be one
    typo away from submitting. Preview mints the confNum and commits
    nothing; place takes that confNum and commits. Granting the first
    must never grant the second.
    """
    session, _ = _ready_with(allow_preview=True)
    with pytest.raises(ConfigurationError, match="PLACES OR CANCELS A REAL ORDER"):
        session.post_json(path, {})


@pytest.mark.parametrize("path", sorted(PREVIEW_ENDPOINTS))
def test_preview_permission_allows_previewing(path):
    session, page = _ready_with(allow_preview=True)
    session.post_json(path, {})
    assert page.evaluated[0][0] == path


@pytest.mark.parametrize("path", sorted(PREVIEW_ENDPOINTS))
def test_place_permission_implies_preview_permission(path):
    """Placing needs a confNum only preview can mint, so the stronger
    capability has to carry the weaker one or nothing could ever place."""
    session, page = _ready_with(allow_orders=True)
    session.post_json(path, {})
    assert page.evaluated[0][0] == path


@pytest.mark.parametrize("path", sorted(ORDER_ENDPOINTS))
def test_order_endpoints_are_permitted_once_explicitly_enabled(path):
    session, page = _ready_with(allow_orders=True)
    session.post_json(path, {})
    assert page.evaluated[0][0] == path


def test_read_only_endpoints_need_no_opt_in():
    session, page = _ready_with()
    session.post_json(PENDING, {})
    assert page.evaluated[0][0] == PENDING


def test_cancel_is_gated_too_even_though_it_only_reduces_exposure():
    """A gate you can reason about beats one with exceptions in it."""
    assert "/ftgw/digital/trade-equity/cancelPlaceOrder" in ORDER_ENDPOINTS


def test_an_unknown_endpoint_is_refused_rather_than_forwarded():
    """An allowlist that silently accepts anything is not an allowlist."""
    session, _ = _ready_with(allow_orders=True)
    with pytest.raises(ConfigurationError, match="not a known Fidelity endpoint"):
        session.post_json("/ftgw/digital/trade-equity/somethingNew", {})


def test_a_full_url_is_refused():
    """Site-relative only -- this can talk to exactly one origin, and that
    must not depend on the caller getting it right."""
    session, _ = _ready_with()
    with pytest.raises(ConfigurationError, match="site-relative"):
        session.post_json("https://evil.example.com/steal", {})


def test_read_only_and_order_endpoint_sets_do_not_overlap():
    assert READ_ONLY_ENDPOINTS.isdisjoint(ORDER_ENDPOINTS)


# -- session expiry ----------------------------------------------------


def test_a_redirect_into_signin_raises_expired_not_empty_data():
    """THE failure mode worth naming: an expired session usually returns
    200 with a login page, not a 401. Parsed naively that is an empty
    order list, which would read as 'no open orders' at exactly the wrong
    moment."""
    session, _ = _ready_with(
        result={"status": 200, "url": SIGNIN, "body": "<html>sign in</html>"}
    )
    with pytest.raises(FidelitySessionExpired, match="expired"):
        session.post_json(PENDING, {})


@pytest.mark.parametrize("status", [401, 403])
def test_auth_statuses_raise_expired(status):
    session, _ = _ready_with(result={"status": status, "url": SIGNED_IN, "body": ""})
    with pytest.raises(FidelitySessionExpired):
        session.post_json(PENDING, {})


def test_a_page_sitting_on_signin_is_refused_before_any_request():
    session, page = _ready_with(url=SIGNIN)
    with pytest.raises(FidelitySessionExpired, match="sign-in"):
        session.post_json(PENDING, {})
    assert page.evaluated == [], "a request was issued despite an expired session"


def test_expired_is_distinguishable_from_a_transport_error():
    """The two need different responses -- halt-and-alert versus retry --
    so they must not share a type."""
    assert issubclass(FidelitySessionExpired, FidelitySessionError)
    assert not issubclass(FidelitySessionError, FidelitySessionExpired)


# -- responses ---------------------------------------------------------


def test_a_json_body_is_parsed():
    payload = {"data": {"orders": [{"orderNum": "2C3239SF"}]}}
    session, _ = _ready_with(
        result={"status": 200, "url": SIGNED_IN, "body": json.dumps(payload)}
    )
    assert session.post_json(PENDING, {}) == payload


def test_html_where_json_was_expected_says_so():
    session, _ = _ready_with(
        result={"status": 200, "url": SIGNED_IN, "body": "<html>nope</html>"}
    )
    with pytest.raises(FidelitySessionError, match="looks like HTML"):
        session.post_json(PENDING, {})


def test_a_server_error_reports_its_status():
    session, _ = _ready_with(result={"status": 500, "url": SIGNED_IN, "body": "oops"})
    with pytest.raises(FidelitySessionError, match="500"):
        session.post_json(PENDING, {})


def test_an_evaluate_failure_is_wrapped_not_leaked():
    session, _ = _ready_with(raises=RuntimeError("page crashed"))
    with pytest.raises(FidelitySessionError, match="failed in the page"):
        session.post_json(PENDING, {})


def test_posting_without_credentials_says_what_to_do():
    page = FakePage()
    session = FidelitySession(page)
    session.attach()
    with pytest.raises(FidelitySessionError, match="wait_for_credentials"):
        session.post_json(PENDING, {})


def test_the_payload_is_sent_as_given():
    session, page = _ready_with()
    session.post_json(PENDING, {"acctNum": "231930409"})
    assert page.evaluated[0][1] == {"acctNum": "231930409"}
