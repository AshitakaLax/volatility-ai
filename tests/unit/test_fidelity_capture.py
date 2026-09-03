"""Unit tests for src/fidelity_capture.py.

Everything here runs with no browser, no network, and no credentials --
the module never imports playwright and is duck-typed on the page object,
so a fake that emits synthetic events exercises the whole path.

Two properties get the most attention, because they are the ones whose
failure is dangerous rather than merely annoying:

  * Scrubbing. The login POST body carries the password verbatim. If the
    scrubber misses, the dump becomes a plaintext credential file.
  * Handlers never raising. An exception inside a Playwright event
    handler surfaces in the middle of whatever page interaction is in
    flight, which would turn a capture bug into a trading bug.
"""

from __future__ import annotations

import json

from src.fidelity_capture import (
    DEFAULT_MAX_PAYLOAD_BYTES,
    TrafficCapture,
)
from src.secrets import REDACTED


class FakeWebSocket:
    def __init__(self, url: str) -> None:
        self.url = url
        self._handlers: dict[str, list] = {}

    def on(self, event: str, handler) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def emit(self, event: str, payload) -> None:
        for handler in self._handlers.get(event, []):
            handler(payload)


class FakeRequest:
    def __init__(self, method: str = "GET", resource_type: str = "xhr") -> None:
        self.method = method
        self.resource_type = resource_type


class FakeResponse:
    def __init__(
        self,
        url: str,
        body: str | None = "{}",
        status: int = 200,
        method: str = "GET",
        resource_type: str = "xhr",
        raises=None,
    ) -> None:
        self.url = url
        self.status = status
        self.request = FakeRequest(method, resource_type)
        self._body = body
        self._raises = raises

    def text(self) -> str:
        if self._raises is not None:
            raise self._raises
        return self._body


class FakePage:
    """Minimal stand-in for a Playwright Page."""

    def __init__(self) -> None:
        self._handlers: dict[str, list] = {}

    def on(self, event: str, handler) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def emit_websocket(self, ws: FakeWebSocket) -> None:
        for handler in self._handlers.get("websocket", []):
            handler(ws)

    def emit_response(self, response: FakeResponse) -> None:
        for handler in self._handlers.get("response", []):
            handler(response)


class FakeContext:
    """Minimal stand-in for a Playwright BrowserContext."""

    def __init__(self, *pages: FakePage) -> None:
        self.pages = list(pages)
        self._handlers: dict[str, list] = {}

    def on(self, event: str, handler) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def open_page(self, page: FakePage) -> FakePage:
        """Simulate a tab appearing after capture already started."""
        self.pages.append(page)
        for handler in self._handlers.get("page", []):
            handler(page)
        return page


def _attached(**kwargs) -> tuple[TrafficCapture, FakePage]:
    capture = TrafficCapture(**kwargs)
    page = FakePage()
    capture.attach(page)
    return capture, page


# -- attachment --------------------------------------------------------


def test_attach_registers_both_listeners():
    _capture, page = _attached()
    assert "websocket" in page._handlers
    assert "response" in page._handlers


def test_attaching_the_same_page_twice_is_a_no_op():
    """Double-attachment would silently double-record every frame, which
    is not obviously wrong when reading a dump."""
    capture, page = _attached()
    capture.attach(page)
    assert len(page._handlers["websocket"]) == 1


def test_attaching_a_second_page_is_supported():
    """This replaces a test that asserted the OPPOSITE, and that earlier
    assertion encoded the bug rather than a requirement.

    Refusing a second page seemed tidy -- one capture, one page. Then a
    real recon run recorded nothing at all: Fidelity's sign-in moved the
    session to a page that did not exist when capture started, and a
    capture bound to the original tab watched an idle tab for ten
    minutes. Multiple pages are the normal case for any real browsing
    session, so they are now supported."""
    capture, first = _attached()
    second = FakePage()
    capture.attach(second)

    assert capture.attached_page_count == 2
    assert "response" in second._handlers
    # And the first page is still recorded -- not replaced.
    assert "response" in first._handlers


def test_attach_context_covers_pages_that_already_exist():
    capture = TrafficCapture()
    pages = [FakePage(), FakePage()]
    capture.attach_context(FakeContext(*pages))

    assert capture.attached_page_count == 2
    for page in pages:
        assert "response" in page._handlers


def test_attach_context_covers_a_tab_opened_later():
    """A login redirect, a popup, or 'open in new tab' all create pages
    after capture starts. They must be recorded from their first byte,
    not from whenever someone notices they are missing."""
    capture = TrafficCapture()
    context = FakeContext()
    capture.attach_context(context)
    assert capture.attached_page_count == 0

    late = context.open_page(FakePage())
    assert capture.attached_page_count == 1
    assert "response" in late._handlers


def test_attaching_the_same_context_twice_is_a_no_op():
    capture = TrafficCapture()
    page = FakePage()
    context = FakeContext(page)
    capture.attach_context(context)
    capture.attach_context(context)
    assert capture.attached_page_count == 1
    assert len(page._handlers["websocket"]) == 1


def test_a_context_that_cannot_register_handlers_is_recorded_not_raised():
    """Handlers must never propagate into page interaction -- a capture
    problem must not become a trading problem."""

    class Hostile(FakeContext):
        def on(self, event, handler):
            raise RuntimeError("no listeners for you")

    capture = TrafficCapture()
    capture.attach_context(Hostile(FakePage()))
    assert capture.attached_page_count == 1  # existing page still attached
    assert any("context" in err for err in capture.handler_errors)


# -- websocket frames --------------------------------------------------


def test_records_frames_in_both_directions():
    capture, page = _attached()
    ws = FakeWebSocket("wss://digital.fidelity.com/stream")
    page.emit_websocket(ws)
    ws.emit("framesent", '{"a": 1}')
    ws.emit("framereceived", '{"b": 2}')

    assert [f.direction for f in capture.frames] == ["sent", "received"]
    assert capture.frames[0].url == "wss://digital.fidelity.com/stream"
    assert capture.frames[1].payload == '{"b": 2}'


def test_binary_frames_are_decoded_not_dropped():
    """A JSON body sent as bytes is common and perfectly readable."""
    capture, page = _attached()
    ws = FakeWebSocket("wss://digital.fidelity.com/ws")
    page.emit_websocket(ws)
    ws.emit("framereceived", b'{"orderId": "ABC"}')

    assert len(capture.frames) == 1
    assert capture.frames[0].binary is True
    assert "orderId" in capture.frames[0].payload


def test_undecodable_bytes_do_not_raise():
    capture, page = _attached()
    ws = FakeWebSocket("wss://digital.fidelity.com/ws")
    page.emit_websocket(ws)
    ws.emit("framereceived", b"\xff\xfe\x00garbage")

    assert len(capture.frames) == 1
    assert capture.handler_errors == []


# -- responses ---------------------------------------------------------


def test_records_xhr_responses():
    capture, page = _attached()
    page.emit_response(
        FakeResponse("https://digital.fidelity.com/api/orders", body='{"orders": []}')
    )
    assert len(capture.responses) == 1
    assert capture.responses[0].status == 200
    assert capture.responses[0].body == '{"orders": []}'


def test_non_xhr_resources_are_filtered_out():
    """A brokerage page is megabytes of JS, fonts, and images. None of it
    has recon value and all of it would swamp the dump."""
    capture, page = _attached()
    for resource_type in ("script", "image", "stylesheet", "font", "document"):
        page.emit_response(
            FakeResponse("https://x/asset", resource_type=resource_type)
        )
    assert capture.responses == []


def test_an_unreadable_body_is_recorded_rather_than_dropped():
    """.text() throws for redirects and aborted requests. Knowing an
    endpoint was CALLED matters even when its payload is unavailable."""
    capture, page = _attached()
    page.emit_response(
        FakeResponse("https://x/redirect", raises=RuntimeError("no body"))
    )

    assert len(capture.responses) == 1
    record = capture.responses[0]
    assert record.body is None
    assert record.body_error == "RuntimeError: no body"
    assert capture.handler_errors == []


# -- scrubbing ---------------------------------------------------------


def test_literal_credentials_are_scrubbed_from_frames():
    capture, page = _attached(secret_values=["hunter2", "my-username"])
    ws = FakeWebSocket("wss://digital.fidelity.com/ws")
    page.emit_websocket(ws)
    ws.emit("framesent", '{"user": "my-username", "pw": "hunter2"}')

    payload = capture.frames[0].payload
    assert "hunter2" not in payload
    assert "my-username" not in payload
    assert payload.count(REDACTED) == 2


def test_literal_credentials_are_scrubbed_from_response_bodies():
    """The login POST body carries the password verbatim -- this is the
    single most important thing the scrubber does."""
    capture, page = _attached(secret_values=["hunter2"])
    page.emit_response(
        FakeResponse("https://x/login", body="username=bob&password=hunter2")
    )
    assert "hunter2" not in capture.responses[0].body


def test_credentials_are_scrubbed_from_urls_too():
    capture, page = _attached(secret_values=["hunter2"])
    page.emit_response(FakeResponse("https://x/cb?token=hunter2", body="{}"))
    assert "hunter2" not in capture.responses[0].url


def test_empty_secret_values_are_ignored():
    """`"" in payload` is always True -- a blank credential would scrub
    every payload down to nothing."""
    capture, page = _attached(secret_values=["", None])
    page.emit_response(FakeResponse("https://x/y", body="untouched"))
    assert capture.responses[0].body == "untouched"


def test_secret_looking_json_keys_are_redacted_by_name():
    """For tokens whose values we do not know in advance."""
    capture, page = _attached()
    page.emit_response(
        FakeResponse(
            "https://x/session",
            body=json.dumps({"sessionToken": "abc123", "accountId": "Z1"}),
        )
    )
    parsed = json.loads(capture.responses[0].body)
    assert parsed["sessionToken"] == REDACTED
    # Not a secret, and redacting it would make the dump useless.
    assert parsed["accountId"] == "Z1"


def test_non_json_bodies_pass_through_key_redaction_untouched():
    """Guessing at the structure of an unknown format is how a redactor
    destroys the thing it was supposed to preserve."""
    capture, page = _attached()
    page.emit_response(FakeResponse("https://x/y", body="<html>token=abc</html>"))
    assert capture.responses[0].body == "<html>token=abc</html>"


def test_malformed_json_does_not_raise():
    capture, page = _attached()
    page.emit_response(FakeResponse("https://x/y", body='{"broken": '))
    assert capture.responses[0].body == '{"broken": '
    assert capture.handler_errors == []


# -- bounds ------------------------------------------------------------


def test_oversized_payloads_are_truncated_and_marked():
    capture, page = _attached(max_payload_bytes=100)
    ws = FakeWebSocket("wss://digital.fidelity.com/ws")
    page.emit_websocket(ws)
    ws.emit("framereceived", "z" * 500)

    frame = capture.frames[0]
    assert frame.truncated is True
    assert "TRUNCATED" in frame.payload
    assert len(frame.payload) < 500


def test_record_cap_stops_growth_and_counts_drops():
    capture, page = _attached(max_records=3)
    ws = FakeWebSocket("wss://digital.fidelity.com/ws")
    page.emit_websocket(ws)
    for _ in range(10):
        ws.emit("framereceived", "x")

    assert len(capture.frames) == 3
    assert capture.dropped_records == 7


def test_default_payload_cap_is_generous_enough_to_be_useful():
    assert DEFAULT_MAX_PAYLOAD_BYTES >= 100_000


# -- handlers never raise ----------------------------------------------


def test_a_broken_websocket_object_does_not_propagate():
    """An exception in a Playwright handler surfaces inside whatever page
    interaction is in flight -- a capture bug must not become a trading
    bug."""

    class ExplodingWebSocket:
        url = "wss://digital.fidelity.com/ws"

        def on(self, event, handler):
            raise RuntimeError("boom")

    capture, page = _attached()
    page.emit_websocket(ExplodingWebSocket())  # must not raise

    assert any("boom" in e for e in capture.handler_errors)


def test_a_broken_response_object_does_not_propagate():
    class ExplodingResponse:
        @property
        def request(self):
            raise RuntimeError("kaboom")

    capture, page = _attached()
    page.emit_response(ExplodingResponse())  # must not raise

    assert any("kaboom" in e for e in capture.handler_errors)


def test_handler_error_list_is_bounded():
    class ExplodingWebSocket:
        url = "wss://digital.fidelity.com/ws"

        def on(self, event, handler):
            raise RuntimeError("boom")

    capture, page = _attached()
    for _ in range(500):
        page.emit_websocket(ExplodingWebSocket())

    assert len(capture.handler_errors) == 100


# -- recon aids --------------------------------------------------------


def test_candidate_id_fields_finds_id_shaped_keys():
    capture, page = _attached()
    ws = FakeWebSocket("wss://digital.fidelity.com/ws")
    page.emit_websocket(ws)
    ws.emit("framereceived", json.dumps({"data": {"orderId": "ABC123"}}))
    page.emit_response(
        FakeResponse("https://x/o", body=json.dumps({"confirmationNumber": "9"}))
    )

    hits = capture.candidate_id_fields()
    keys = {k for hit in hits for k in hit["keys"]}
    assert "orderId" in keys
    assert "confirmationNumber" in keys


def test_candidate_id_fields_matches_keys_not_values():
    """A value containing the word 'order' is not a hint."""
    capture, page = _attached()
    page.emit_response(
        FakeResponse("https://x/y", body=json.dumps({"message": "order received"}))
    )
    assert capture.candidate_id_fields() == []


def test_summary_inventories_endpoints_without_query_strings():
    capture, page = _attached()
    page.emit_response(FakeResponse("https://x/api/orders?page=1", method="POST"))
    page.emit_response(FakeResponse("https://x/api/orders?page=2", method="POST"))

    assert capture.summary()["endpoints"] == {"POST https://x/api/orders": 2}


def test_to_dict_is_json_serializable():
    capture, page = _attached(secret_values=["hunter2"])
    ws = FakeWebSocket("wss://digital.fidelity.com/ws")
    page.emit_websocket(ws)
    ws.emit("framereceived", '{"orderId": "1", "pw": "hunter2"}')
    page.emit_response(FakeResponse("https://x/y"))

    text = json.dumps(capture.to_dict())
    assert "hunter2" not in text
    assert "orderId" in text


# --- WebSocket host scoping ---
#
# A real Fidelity session opens a socket to prod-presence-1.glance.net, a
# third-party co-browsing vendor. Recording it would write another
# company's traffic into a dump that already carries session secrets.


def test_third_party_websockets_are_not_recorded():
    capture = TrafficCapture()
    assert capture._websocket_in_scope("wss://spservice.fidelity.com/event/realtime")
    assert capture._websocket_in_scope("wss://mdds-i-tc.fidelity.com/?productId=x")
    assert not capture._websocket_in_scope("wss://prod-presence-1.glance.net/visitorws")


def test_the_host_filter_cannot_be_spoofed_by_a_lookalike_domain():
    """Suffix match on the HOST, not a substring match on the URL."""
    capture = TrafficCapture()
    assert not capture._websocket_in_scope("wss://evil-fidelity.com.attacker.net/x")
    assert not capture._websocket_in_scope("wss://attacker.net/?ref=fidelity.com")
    assert not capture._websocket_in_scope("wss://notfidelity.com/ws")


def test_a_skipped_socket_is_still_noted_by_url():
    """'No frames from X' and 'X was never opened' must not look identical.

    This project has already mistaken an absent record for an absent
    thing once -- the retracted "Fidelity uses no WebSockets" claim.
    """
    capture = TrafficCapture()

    class _WS:
        url = "wss://prod-presence-1.glance.net/visitorws"

        def on(self, *_args):  # pragma: no cover - must never be reached
            raise AssertionError("a skipped socket must not be subscribed to")

    capture._on_websocket(_WS())
    assert capture._out_of_scope_websockets == ["wss://prod-presence-1.glance.net/visitorws"]
    assert capture.frames == []
    assert capture.handler_errors == []
