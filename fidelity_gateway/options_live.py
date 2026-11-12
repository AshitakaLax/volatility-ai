"""
A fund's option-market readings, read live through a FidelitySession.

options_capture.py forms the readings (volatility percentiles, put/call
ratios, at-the-money IV, 25-delta skew, near-chain dealer gamma) from
Trader+'s three option replies, and appends each to a `timestamp,close`
series. That module finds the replies in a capture a person saved; this
one asks for them: three GETs of market data, the ones in
session.READ_ONLY_GET_ENDPOINTS, which the browser extension allows from
version 0.8.0 (its `get` command).

The bridge host runs it once a trading day, after the close and only
while no trading loop is attached (bridge/host.py, COLLECT), for the
funds in live.fidelity.bridge.options.symbols.

--------------------------------------------------------------------
THE CHAIN'S QUERY, AND WHAT IS NOT KNOWN ABOUT IT

Seen once, 2026-11-10, for five expirations whose days all had two
digits:

    strikes=10
    expirationDates=11/11/2026,11/13/2026,...
    settlementTypes=Nov 11 2026|W,Nov 13 2026|W,...,Nov 20 2026|M
    symbol=TQQQ
    adjustedOptionsData=true

Whether a day below ten is written "12/04/2026" and "Dec 04 2026" or
"12/4/2026" and "Dec 4 2026" that capture cannot say. The padded form is
asked first; when it comes back with no strikes, the unpadded one. What
worked is in the collector's line, so the first single-digit day settles
it.

Nothing here navigates, previews or places, and FidelitySession's
defaults allow neither of the last two.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime
from pathlib import Path

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.options_capture import (
    CHAIN_PATH,
    EXPIRATIONS_PATH,
    STATISTICS_PATH,
    Capture,
    parse_chain,
    readings,
    store,
)

API = "/ftgw/digital"
EXTERNAL_DIR_ENV = "VAI_EXTERNAL_DIR"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MINIMUM_EXTENSION = "0.8.0"


def external_directory() -> Path:
    """Where the series go: VAI_EXTERNAL_DIR, else data/external/ -- the
    directory tools/refresh_external.py keeps and the risk governor reads."""
    named = os.environ.get(EXTERNAL_DIR_ENV)
    return Path(named) if named else Path(__file__).resolve().parents[1] / "data" / "external"


def nearest_expirations(payload: dict, count: int, today: date) -> list[tuple[date, str]]:
    """The `count` nearest listed expirations on or after `today`, each with
    its periodicity ("W", "M"), from option-expirations' reply."""
    found = []
    for item in (payload or {}).get("expirations") or ():
        try:
            day = date.fromisoformat(str(item.get("date")))
        except ValueError:
            continue
        if day >= today:
            found.append((day, str(item.get("optionPeriodicity") or "")))
    return sorted(found)[:count]


def chain_query(
    symbol: str, expirations: list[tuple[date, str]], strikes: int, *, padded: bool
) -> dict[str, str]:
    """slo-chain's query for these expirations (module docstring)."""

    def day_of(day: date) -> str:
        return f"{day.day:02d}" if padded else str(day.day)

    def month_of(day: date) -> str:
        return f"{day.month:02d}" if padded else str(day.month)

    return {
        "strikes": str(strikes),
        "expirationDates": ",".join(f"{month_of(d)}/{day_of(d)}/{d.year}" for d, _ in expirations),
        "settlementTypes": ",".join(
            f"{MONTHS[d.month - 1]} {day_of(d)} {d.year}|{kind}" for d, kind in expirations
        ),
        "symbol": symbol,
        "adjustedOptionsData": "true",
    }


def collect(
    session, symbol: str, *, strikes: int = 10, expirations: int = 5, now: datetime | None = None
) -> tuple[Capture, str]:
    """The three replies for `symbol` as a Capture stamped `now`, and a word
    on how the chain was asked for. A chain that cannot be read leaves the
    statistics' readings; statistics that cannot be read raise."""
    now = now or datetime.now(UTC)
    symbol = symbol.upper()
    statistics = session.get_json(API + STATISTICS_PATH, {"underlying": symbol})
    listed = session.get_json(API + EXPIRATIONS_PATH, {"symbol": symbol})
    nearest = nearest_expirations(listed, expirations, now.date())
    chain, how = None, "no expirations listed"
    if nearest:
        forms = [True] if all(d.day >= 10 and d.month >= 10 for d, _ in nearest) else [True, False]
        for padded in forms:
            reply = session.get_json(
                API + CHAIN_PATH, chain_query(symbol, nearest, strikes, padded=padded)
            )
            if isinstance(reply, dict) and parse_chain(reply):
                chain = reply
                how = "padded dates" if padded else "unpadded dates"
                break
            how = "the chain came back empty"
    dates = [d.isoformat() for d, _ in nearest]
    return Capture(
        symbol, now, chain, statistics if isinstance(statistics, dict) else None, dates
    ), how


def options_collector(
    settings: Callable[[], object],
    directory: Callable[[], Path] = external_directory,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Callable[[object], str]:
    """The bridge host's collector: `collect(page)` reads every fund in
    `settings()` (a FidelityOptionsConfig) through `page` and appends the
    readings under `directory()`. Returns what it did, for the journal;
    raises when nothing could be read for any fund."""

    def run(page) -> str:
        from fidelity_gateway.session import FidelitySession

        options = settings()
        symbols: Iterable[str] = getattr(options, "symbols", ()) or ()
        if not symbols:
            return "no funds are named in live.fidelity.bridge.options.symbols"
        session = FidelitySession(page)
        session.attach()
        lines, failures = [], []
        for symbol in symbols:
            try:
                capture, how = collect(
                    session,
                    symbol,
                    strikes=options.strikes,
                    expirations=options.expirations,
                    now=clock(),
                )
                found = readings(capture.chain, capture.statistics)
                written = store(directory(), capture, found)
                lines.append(f"{capture.symbol}: {len(written)} reading(s) ({how})")
            except ConfigurationError as exc:
                # Refused before anything was sent. An extension from before
                # the `get` command answers unknown_command.
                hint = (
                    f" -- the extension must be {MINIMUM_EXTENSION} or newer: build and reload it"
                    if "unknown_command" in str(exc) or "not a command" in str(exc)
                    else ""
                )
                failures.append(f"{symbol}: refused ({exc}){hint}")
            except Exception as exc:
                failures.append(f"{symbol}: {type(exc).__name__}: {exc}")
        if failures and not lines:
            raise RuntimeError("; ".join(failures)[:600])
        return "; ".join([*lines, *failures])[:600]

    return run


__all__ = [
    "chain_query",
    "collect",
    "external_directory",
    "nearest_expirations",
    "options_collector",
]
