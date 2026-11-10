#!/usr/bin/env python
"""
Option-market readings for a fund, from a DevTools capture of Trader+.

    python -m fidelity_gateway.options_capture --input download.devtools --symbol TQQQ
    python -m fidelity_gateway.options_capture --input X.har --symbol TQQQ --out data/external

Trader+'s option pages call three read-only endpoints (seen 2026-11-10):

    traderplus-api/api/key-statistics/v1?underlying=TQQQ
        30-day implied and historical volatility as percentiles of their
        own year, and the whole chain's call and put volume and open
        interest beside their averages.
    traderplus-api/api/option-expirations/v1?symbol=TQQQ
        every listed expiration.
    traderplus-api/api/slo-chain/v1?strikes=N&expirationDates=...
        calls and puts at N strikes around the money for the expirations
        asked for: bid, ask, volume, open interest, implied volatility and
        the Greeks.

This reads those replies out of a HAR (analyze_har.py says how to save one;
Chrome names it download.devtools), prints what they say, and with --out
appends one row to a series per reading, in research/ml/sources.py's
`timestamp,close` shape and stamped at the capture's own instant -- so a
reading is only ever read after it was taken.

--------------------------------------------------------------------
WHAT THIS IS NOT

One capture is one moment. Nothing here is a signal until there is a
history of it to measure, and Trader+ shows no history of these: the
series start the day they are first collected. Collecting them without a
person saving a capture means the three endpoints joining
session.READ_ONLY_ENDPOINTS and the extension's own allowlist -- a change to
the real-money bridge, and the owner's to make.

A capture slices the chain: the strikes and expirations the page had open.
GEX_NEAR is the dealer-gamma sum over that slice only, not the chain's.

A HAR OF AN AUTHENTICATED SESSION IS CREDENTIAL-EQUIVALENT. This reads
response bodies of the three endpoints and nothing else: no header, cookie
or account field is read or printed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

PROVIDER = "fidelity"
CHAIN_PATH = "/traderplus-api/api/slo-chain/v1"
STATISTICS_PATH = "/traderplus-api/api/key-statistics/v1"
EXPIRATIONS_PATH = "/traderplus-api/api/option-expirations/v1"

WEEK_DTE = 7  # the expiration ATM_IV_7D and SKEW_25D are read at: nearest to a week out
SKEW_DELTA = 0.25
SKEW_TOLERANCE = 0.10  # how far from 25 delta the nearest strike may be
CONTRACT = 100


@dataclass(frozen=True)
class Leg:
    """One strike of one expiration, both sides."""

    expiration: str
    dte: int
    strike: float
    call_iv: float
    put_iv: float
    call_delta: float
    put_delta: float
    call_gamma: float
    put_gamma: float
    call_oi: float
    put_oi: float
    call_intrinsic: float
    put_intrinsic: float


def _number(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def parse_chain(payload: dict) -> list[Leg]:
    """slo-chain's `callsAndPuts` as legs, nearest expiration first. A row
    without a strike or an expiration is left out."""
    legs = []
    for row in payload.get("callsAndPuts") or ():
        expiry = row.get("expirationData") or {}
        strike, dte = _number(row.get("strike")), _number(expiry.get("daysToExpiration"))
        if not expiry.get("date") or math.isnan(strike) or math.isnan(dte):
            continue
        legs.append(
            Leg(
                expiration=str(expiry["date"]),
                dte=int(dte),
                strike=strike,
                call_iv=_number(row.get("callImpliedVolatility")),
                put_iv=_number(row.get("putImpliedVolatility")),
                call_delta=_number(row.get("callDelta")),
                put_delta=_number(row.get("putDelta")),
                call_gamma=_number(row.get("callGamma")),
                put_gamma=_number(row.get("putGamma")),
                call_oi=_number(row.get("callOpenInterest")),
                put_oi=_number(row.get("putOpenInterest")),
                call_intrinsic=_number(row.get("callIntrinsicValue")),
                put_intrinsic=_number(row.get("putIntrinsicValue")),
            )
        )
    return sorted(legs, key=lambda leg: (leg.dte, leg.strike))


def spot(legs: list[Leg]) -> float:
    """The underlying's price the chain was computed at: a strike plus its
    call's intrinsic value (or less its put's), the median over the legs in
    the money. NaN when none is."""
    implied = [leg.strike + leg.call_intrinsic for leg in legs if leg.call_intrinsic > 0]
    implied += [leg.strike - leg.put_intrinsic for leg in legs if leg.put_intrinsic > 0]
    if not implied:
        return math.nan
    implied.sort()
    middle = len(implied) // 2
    return implied[middle] if len(implied) % 2 else (implied[middle - 1] + implied[middle]) / 2


def by_expiration(legs: list[Leg]) -> dict[tuple[int, str], list[Leg]]:
    out: dict[tuple[int, str], list[Leg]] = {}
    for leg in legs:
        out.setdefault((leg.dte, leg.expiration), []).append(leg)
    return out


def atm_iv(legs: list[Leg], price: float) -> float:
    """The mean of the call's and the put's implied volatility at the strike
    nearest `price`, in percent."""
    if not legs or math.isnan(price):
        return math.nan
    leg = min(legs, key=lambda item: abs(item.strike - price))
    ivs = [iv for iv in (leg.call_iv, leg.put_iv) if not math.isnan(iv)]
    return 100.0 * sum(ivs) / len(ivs) if ivs else math.nan


def skew(legs: list[Leg]) -> float:
    """25-delta skew in volatility points: the put's implied volatility
    nearest -0.25 delta less the call's nearest +0.25. NaN when the slice
    has no strike within SKEW_TOLERANCE of either."""
    puts = [leg for leg in legs if not math.isnan(leg.put_delta + leg.put_iv)]
    calls = [leg for leg in legs if not math.isnan(leg.call_delta + leg.call_iv)]
    if not puts or not calls:
        return math.nan
    put = min(puts, key=lambda leg: abs(leg.put_delta + SKEW_DELTA))
    call = min(calls, key=lambda leg: abs(leg.call_delta - SKEW_DELTA))
    if (
        abs(put.put_delta + SKEW_DELTA) > SKEW_TOLERANCE
        or abs(call.call_delta - SKEW_DELTA) > SKEW_TOLERANCE
    ):
        return math.nan
    return 100.0 * (put.put_iv - call.call_iv)


def gamma_exposure(legs: list[Leg], price: float) -> float:
    """Dollars of dealer hedging per 1% move over these legs, on the usual
    convention (dealers long the calls, short the puts)."""
    if math.isnan(price):
        return math.nan
    total = 0.0
    for leg in legs:
        calls = leg.call_gamma * leg.call_oi
        puts = leg.put_gamma * leg.put_oi
        total += (0.0 if math.isnan(calls) else calls) - (0.0 if math.isnan(puts) else puts)
    return total * CONTRACT * price * price * 0.01


def _ratio(a, b) -> float:
    a, b = _number(a), _number(b)
    return a / b if b and not math.isnan(a + b) else math.nan


def readings(chain: dict | None, statistics: dict | None) -> dict[str, float]:
    """Every reading the two replies give, by series name. A reading that
    cannot be formed is NaN and is not stored."""
    out: dict[str, float] = {}
    if statistics:
        out["IV30_PCTL"] = _number(statistics.get("iv30percentile"))
        out["HV30_PCTL"] = _number(statistics.get("hv30percentile"))
        volume = _ratio(statistics.get("putVolume"), statistics.get("callVolume"))
        usual = _ratio(statistics.get("avgPutVolume"), statistics.get("avgCallVolume"))
        out["PC_VOLUME"] = volume
        out["PC_VOLUME_REL"] = _ratio(volume, usual)
        out["PC_OI"] = _ratio(statistics.get("putOpenInterest"), statistics.get("callOpenInterest"))
    if chain:
        legs = parse_chain(chain)
        price = spot(legs)
        groups = by_expiration(legs)
        if groups:
            week = min(groups, key=lambda key: abs(key[0] - WEEK_DTE))
            first, last = min(groups), max(groups)
            out["SPOT"] = price
            out["ATM_IV_7D"] = atm_iv(groups[week], price)
            out["SKEW_25D"] = skew(groups[week])
            near, far = atm_iv(groups[first], price), atm_iv(groups[last], price)
            # Above 1: the nearest expiration is priced hotter than the furthest captured.
            out["TERM_NEAR_FAR"] = _ratio(near, far) if first != last else math.nan
            out["GEX_NEAR"] = gamma_exposure(legs, price)
    return out


# --------------------------------------------------------------------
# A capture
# --------------------------------------------------------------------


@dataclass(frozen=True)
class Capture:
    """The newest reply of each endpoint for one symbol in a HAR."""

    symbol: str
    at: datetime | None
    chain: dict | None
    statistics: dict | None
    expirations: list[str]


def _reply(entry: dict) -> dict | None:
    text = ((entry.get("response") or {}).get("content") or {}).get("text")
    if not text:
        return None
    try:
        body = json.loads(text)
    except (TypeError, ValueError):
        return None
    return body if isinstance(body, dict) else None


def _when(entry: dict) -> datetime | None:
    try:
        moment = datetime.fromisoformat(str(entry.get("startedDateTime")).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment.astimezone(UTC) if moment.tzinfo else None


def read_capture(har: dict, symbol: str) -> Capture:
    """The option replies for `symbol` in a HAR. Later entries replace
    earlier ones; `at` is the chain's instant, else the statistics'."""
    symbol = symbol.upper()
    chain = statistics = None
    chain_at = statistics_at = None
    expirations: list[str] = []
    for entry in (har.get("log") or {}).get("entries") or ():
        url = urlsplit(str((entry.get("request") or {}).get("url") or ""))
        if not url.path.endswith((CHAIN_PATH, STATISTICS_PATH, EXPIRATIONS_PATH)):
            continue
        body = _reply(entry)
        if body is None:
            continue
        if url.path.endswith(CHAIN_PATH):
            if str(body.get("underlyingSymbol", "")).upper() == symbol:
                chain, chain_at = body, _when(entry)
        elif url.path.endswith(STATISTICS_PATH):
            if str(body.get("underlyingsymbol", "")).upper() == symbol:
                statistics, statistics_at = body, _when(entry)
        elif f"symbol={symbol}" in url.query.upper().replace("SYMBOL=", "symbol="):
            expirations = [
                str(x.get("date")) for x in body.get("expirations") or () if x.get("date")
            ]
    return Capture(symbol, chain_at or statistics_at, chain, statistics, expirations)


def series_name(symbol: str, reading: str) -> str:
    return f"{PROVIDER}_{symbol.upper()}_{reading}"


def append_reading(directory: Path, name: str, at: datetime, value: float) -> bool:
    """One `timestamp,close` row into `<name>.csv`, in time order. A stamp
    already there is left as it is. True if a row was added."""
    path = directory / f"{name}.csv"
    stamp = at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S+00:00")
    rows: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines()[1:]:
            key, _, rest = line.partition(",")
            if key:
                rows[key] = rest
    if stamp in rows:
        return False
    rows[stamp] = repr(float(value))
    text = "timestamp,close\n" + "".join(f"{key},{rows[key]}\n" for key in sorted(rows))
    partial = path.with_name(f".{path.name}.partial")
    partial.write_text(text, encoding="utf-8")
    os.replace(partial, path)
    return True


def store(directory: Path, capture: Capture, found: dict[str, float]) -> list[str]:
    """Every formed reading appended to its series; the names written."""
    if capture.at is None:
        raise ValueError("the capture carries no time for these replies")
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for reading, value in found.items():
        if math.isnan(value):
            continue
        name = series_name(capture.symbol, reading)
        if append_reading(directory, name, capture.at, value):
            written.append(name)
    return written


def report(capture: Capture, found: dict[str, float]) -> str:
    lines = [f"{capture.symbol} options, captured {capture.at or 'at an unknown time'}"]
    if capture.statistics is None:
        lines.append("  no key-statistics reply for this symbol")
    if capture.chain is None:
        lines.append("  no option chain reply for this symbol")
    else:
        legs = parse_chain(capture.chain)
        price = found.get("SPOT", math.nan)
        lines.append(
            f"  chain: {len(legs)} strikes over {len(by_expiration(legs))} expirations"
            f" (of {len(capture.expirations) or '?'} listed), underlying {price:.2f}"
        )
        for (dte, expiration), group in by_expiration(legs).items():
            strikes = sorted(leg.strike for leg in group)
            lines.append(
                f"    {expiration:<12} {dte:>3}d  strikes {strikes[0]:g}-{strikes[-1]:g}"
                f"  ATM IV {atm_iv(group, price):6.1f}%  25d skew {skew(group):6.1f}"
            )
    for reading, value in found.items():
        lines.append(f"  {reading:<14} {'not formed' if math.isnan(value) else f'{value:,.4g}'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--input", required=True, type=Path, help="the HAR (download.devtools)")
    parser.add_argument("--symbol", default="TQQQ")
    parser.add_argument(
        "--out", type=Path, help="append each reading to <out>/fidelity_<SYMBOL>_<READING>.csv"
    )
    args = parser.parse_args(argv)
    with open(args.input, encoding="utf-8") as handle:
        capture = read_capture(json.load(handle), args.symbol)
    if capture.chain is None and capture.statistics is None:
        print(f"{args.input} holds no option replies for {args.symbol.upper()}", file=sys.stderr)
        return 1
    found = readings(capture.chain, capture.statistics)
    print(report(capture, found))
    if args.out:
        written = store(args.out, capture, found)
        print(f"  {len(written)} reading(s) appended under {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
