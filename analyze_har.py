#!/usr/bin/env python
"""
Answer the Fidelity reconnaissance questions from a Firefox DevTools HAR.

WHY THIS EXISTS. The Playwright-driven recon harness (fidelity_recon.py)
cannot get past Fidelity's sign-in: a fresh automated browser with no
cookies and no history is refused with "Sorry, we can't complete this
action right now." The same human logs in fine in their ordinary
Firefox. So the traffic is observable -- just not from a browser we
launched.

Firefox's own DevTools records every request already. Exporting a HAR
needs no automation, defeats no controls, and produces a STRICTLY MORE
COMPLETE record than the Playwright capture would have: it is the real
session, in the real browser, with the real profile.

This reads that export and answers the same three questions
fidelity_recon.py's summary does:

  1. Does an order submission round-trip an order/confirmation ID?
  2. Is there an orders-list endpoint the Orders/Positions page calls?
  3. Can a client reference be attached to an order?

HOW TO PRODUCE THE INPUT

  1. Open Firefox. Press F12 for DevTools, choose the Network tab.
  2. Tick "Persist Logs" so a navigation does not clear what you have.
  3. Log into Fidelity as you normally do.
  4. Visit the pages you care about -- Trader+
     (https://digital.fidelity.com/ftgw/digital/traderplus), the
     Orders/Activity page, Positions.
  5. Right-click anywhere in the request list -> "Save All As HAR".
  6. Run:  python analyze_har.py --input <that-file>.har

WEBSOCKET FRAMES: it depends on the browser, and the difference matters.

The HAR *specification* has no place for WebSocket payloads. But
Chromium DevTools (Chrome, Edge) writes them anyway, into a
non-standard `_webSocketMessages` array on the socket's entry -- the
leading underscore is the spec's own extension convention. Firefox does
not. So a HAR from Edge normally DOES carry the frames, and one from
Firefox does not.

This script reads `_webSocketMessages` when present and says explicitly
when a socket was opened but carries no recorded frames -- because
"this format cannot show me X" and "X did not happen" are different
statements, and conflating them has already produced one wrong
conclusion on this project ("Fidelity uses no WebSockets", drawn from a
Firefox HAR that could not have shown one).

A HAR OF AN AUTHENTICATED SESSION IS CREDENTIAL-EQUIVALENT. It contains
Cookie and Authorization headers for a live brokerage login. This script
never prints header values, and --redact writes a scrubbed copy safe to
keep. Delete the original when you are done with it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from src.exceptions import ConfigurationError
from src.fidelity_capture import _ID_KEY_PATTERN, _find_id_keys

# Headers whose values authenticate a session. Never printed; removed by
# --redact. Matched case-insensitively against the header name.
_SENSITIVE_HEADERS = frozenset(
    {
        "cookie",
        "set-cookie",
        "authorization",
        "proxy-authorization",
        "x-csrf-token",
        "x-xsrf-token",
        "x-auth-token",
    }
)

# Content types worth reading a body for. A HAR of a real session is
# mostly images, fonts and CSS; none of that answers any question here.
_INTERESTING_TYPES = ("json", "javascript", "text/plain", "xml")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Answer the Fidelity recon questions from a Firefox DevTools HAR export."
    )
    parser.add_argument("--input", required=True, help="Path to the .har file")
    parser.add_argument(
        "--host-filter",
        default="fidelity.com",
        help="Only consider requests to hosts containing this (default: fidelity.com). "
        "Pass an empty string to consider everything.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=40,
        help="How many endpoints to list (default: 40).",
    )
    parser.add_argument(
        "--show-bodies",
        type=int,
        default=0,
        help="Print the first N characters of each ID-bearing body (default: 0, "
        "meaning print none). Bodies from an authenticated session may contain "
        "account numbers and balances.",
    )
    parser.add_argument(
        "--redact",
        metavar="OUT.har",
        default=None,
        help="Write a copy with authenticating headers removed, safe to keep or share.",
    )
    return parser.parse_args(argv)


def load_har(path: Path) -> list[dict]:
    """Return the HAR's entries, with the format's own quirks stated."""
    if not path.exists():
        raise ConfigurationError(f"HAR file not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"{path} is not valid JSON ({exc}). A HAR is a JSON file -- if you saved "
            "the Network panel some other way (a screenshot, a .txt), re-export with "
            'right-click -> "Save All As HAR".'
        ) from exc
    log = raw.get("log")
    if not isinstance(log, dict) or "entries" not in log:
        raise ConfigurationError(
            f"{path} is JSON but has no log.entries -- it does not look like a HAR."
        )
    return log["entries"]


def _header(entry_part: dict, name: str) -> str:
    for header in entry_part.get("headers", []) or []:
        if str(header.get("name", "")).lower() == name:
            return str(header.get("value", ""))
    return ""


def _body_text(response: dict) -> str:
    content = response.get("content", {}) or {}
    return content.get("text") or ""


def _is_interesting(response: dict) -> bool:
    mime = str((response.get("content", {}) or {}).get("mimeType", "")).lower()
    return any(t in mime for t in _INTERESTING_TYPES)


def endpoint_of(url: str) -> str:
    """Path without query string -- the query is per-request noise and
    would splinter one endpoint into hundreds of rows."""
    parsed = urlparse(url)
    return f"{parsed.netloc}{parsed.path}"


def analyze(entries: list[dict], host_filter: str) -> dict:
    kept = []
    for entry in entries:
        url = str(entry.get("request", {}).get("url", ""))
        if host_filter and host_filter not in urlparse(url).netloc:
            continue
        kept.append(entry)

    endpoints: Counter = Counter()
    id_hits: list[dict] = []
    websockets: list[str] = []

    for entry in kept:
        request = entry.get("request", {}) or {}
        response = entry.get("response", {}) or {}
        url = str(request.get("url", ""))

        is_socket = (
            url.startswith("ws://")
            or url.startswith("wss://")
            or str(response.get("status", "")) == "101"
            or _header(request, "upgrade").lower() == "websocket"
        )
        if is_socket:
            # _webSocketMessages is Chromium DevTools' extension field;
            # absent from Firefox exports and from the HAR spec itself.
            messages = entry.get("_webSocketMessages") or []
            websockets.append({"url": url, "messages": messages})
            continue

        endpoints[f"{request.get('method', '?')} {endpoint_of(url)}"] += 1

        if not _is_interesting(response):
            continue

        body = _body_text(response)
        if not body:
            continue

        found = _find_id_keys(body)
        # The URL itself can carry the signal even when the body does not
        # parse as JSON -- an /orders endpoint is interesting regardless.
        url_hit = bool(_ID_KEY_PATTERN.search(url))
        if found or url_hit:
            id_hits.append(
                {
                    "method": request.get("method", "?"),
                    "url": url,
                    "endpoint": endpoint_of(url),
                    "status": response.get("status"),
                    "keys": found,
                    "matched_on": "body" if found else "url",
                    "body": body,
                }
            )

    return {
        "total": len(entries),
        "kept": len(kept),
        "endpoints": endpoints,
        "id_hits": id_hits,
        "websockets": websockets,
    }


def analyze_socket_frames(sockets: list[dict]) -> dict:
    """Summarise WebSocket frames: direction counts, and which frames
    carry ID-shaped keys.

    The question this exists to answer is narrow and consequential: does
    the stream carry ORDER UPDATES, or only market data? Order updates
    would replace polling transactions/pending with push. Market data
    duplicates what this project already gets from Alpaca and is worth
    little.

    Chromium records direction as `type`: "send" (browser -> server) and
    "receive" (server -> browser).
    """
    sent = received = 0
    id_frames: list[dict] = []
    samples: list[dict] = []

    for socket in sockets:
        for message in socket.get("messages") or []:
            direction = str(message.get("type", "")).lower()
            if direction == "send":
                sent += 1
            else:
                received += 1
            data = message.get("data")
            if not isinstance(data, str) or not data:
                continue
            found = _find_id_keys(data)
            if found:
                id_frames.append(
                    {
                        "url": socket["url"],
                        "direction": direction,
                        "keys": found,
                        "data": data,
                    }
                )
            elif len(samples) < 6:
                samples.append(
                    {"url": socket["url"], "direction": direction, "data": data}
                )

    return {
        "sent": sent,
        "received": received,
        "id_frames": id_frames,
        "samples": samples,
    }


def redact(path: Path, out_path: Path) -> int:
    """Write a copy with authenticating headers stripped. Returns the
    number of header values removed."""
    raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    removed = 0
    for entry in raw.get("log", {}).get("entries", []):
        for part in ("request", "response"):
            headers = (entry.get(part, {}) or {}).get("headers", []) or []
            for header in headers:
                if str(header.get("name", "")).lower() in _SENSITIVE_HEADERS:
                    header["value"] = "[REDACTED]"
                    removed += 1
        # Cookies are also broken out separately in the HAR schema.
        for part in ("request", "response"):
            cookies = (entry.get(part, {}) or {}).get("cookies", []) or []
            for cookie in cookies:
                if "value" in cookie:
                    cookie["value"] = "[REDACTED]"
                    removed += 1
    out_path.write_text(json.dumps(raw, indent=1), encoding="utf-8")
    return removed


def report(result: dict, args: argparse.Namespace) -> None:
    print("\n===== HAR RECON SUMMARY =====")
    print(f"entries: {result['total']} total, {result['kept']} matching the host filter")

    sockets = result["websockets"]
    print("\n-- WebSocket connections --")
    if sockets:
        for socket in sockets:
            n = len(socket.get("messages") or [])
            print(f"  {n:5d} frames  {socket['url']}")

        frames = analyze_socket_frames(sockets)
        total = frames["sent"] + frames["received"]
        if total == 0:
            print(
                "\n  Sockets were opened but NO frames are recorded in this file.\n"
                "  That is a property of the EXPORT, not of Fidelity: only Chromium\n"
                "  DevTools (Chrome/Edge) writes _webSocketMessages. Re-export from\n"
                "  Edge to capture payloads -- do not read this as 'the stream is\n"
                "  silent'."
            )
        else:
            print(f"\n  frames: {frames['sent']} sent, {frames['received']} received")
            hits = frames["id_frames"]
            print(f"\n  -- frames carrying ID-shaped keys ({len(hits)}) --")
            for hit in hits[:15]:
                print(f"    [{hit['direction']:7s}] keys: {','.join(hit['keys'][:8])}")
                if args.show_bodies:
                    print(f"              {hit['data'][: args.show_bodies]}")
            if hits:
                print(
                    "\n  ORDER UPDATES OVER THE STREAM look likely -- that would replace\n"
                    "  polling transactions/pending with push."
                )
            else:
                print(
                    "    (none)\n"
                    "\n  No order-ID-shaped keys in any frame. Consistent with a\n"
                    "  MARKET-DATA-only stream, which duplicates what this project\n"
                    "  already gets from Alpaca and is worth little here."
                )
            if frames["samples"]:
                print("\n  -- sample frames (to judge what the stream actually is) --")
                for sample in frames["samples"]:
                    print(f"    [{sample['direction']:7s}] {sample['data'][:180]}")
    else:
        print(
            "  (no WebSocket connections in this capture)\n"
            "  THIS IS NOT EVIDENCE OF ABSENCE, whichever browser exported it.\n"
            "  Firefox omits WebSocket entries from a HAR entirely. Chrome/Edge\n"
            "  DevTools ('WebInspector') shows WS traffic in the Network panel but\n"
            "  does not reliably serialise frames into the export either, so a\n"
            "  capture with no ws:// entries and no _webSocketMessages is equally\n"
            "  consistent with 'no socket was opened' and 'the export dropped it'.\n"
            "  This tool cannot tell those apart -- do not let it be read as a\n"
            "  finding, which is a mistake this project has already made once.\n"
            "  It is also only meaningful if you exercised a page that opens one:\n"
            "  a quote stream usually starts on a trade ticket, not a summary.\n"
            "  Settle it with fidelity_recon.py --cdp-url, which registers\n"
            "  page.on('websocket') and records frames directly."
        )

    print(f"\n-- Endpoints, most-called first (top {args.top}) --")
    for endpoint, count in result["endpoints"].most_common(args.top):
        print(f"  {count:5d}  {endpoint}")
    if not result["endpoints"]:
        print("  (none matched the host filter)")

    hits = result["id_hits"]
    print(f"\n-- Responses carrying ID-shaped keys ({len(hits)}) --")
    for hit in hits:
        keys = ",".join(hit["keys"][:8]) if hit["keys"] else "(url match)"
        print(f"  [{hit['status']}] {hit['method']:5s} {hit['endpoint']}")
        print(f"          keys: {keys}")
        if args.show_bodies:
            snippet = hit["body"][: args.show_bodies].replace("\n", " ")
            print(f"          body: {snippet}")
    if not hits:
        print(
            "  (none)\n"
            "  Before concluding Fidelity exposes no order IDs, check that the capture\n"
            "  actually covers an Orders/Activity page load -- an endpoint that was\n"
            "  never called cannot appear here."
        )

    if not args.show_bodies and hits:
        print(
            "\n  Bodies not shown. Re-run with --show-bodies 400 to see them --\n"
            "  they may contain account numbers and balances."
        )


def main(argv=None) -> int:
    args = parse_args(argv)
    path = Path(args.input)
    try:
        entries = load_har(path)
    except ConfigurationError as exc:
        print(f"[har] {exc}", file=sys.stderr)
        return 1

    result = analyze(entries, args.host_filter)
    report(result, args)

    if args.redact:
        out_path = Path(args.redact)
        removed = redact(path, out_path)
        print(f"\nRedacted copy: {out_path}  ({removed} header/cookie values removed)")

    print(
        f"\nSource HAR: {path}\n"
        "It contains live session cookies for an authenticated brokerage login.\n"
        "Delete it when you are done."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
