"""
The forecast generator's market data: Yahoo's chart API and Cboe's daily
index files, the same public sources the pre-market forecast generator reads
(there through yfinance; here through research/ml/sources.py's HTTP getter,
so this repository gains no dependency).

  daily(ticker)     every daily bar, OHLCV, adjusted for dividends and
                    splits the way yfinance's auto_adjust does (each price x
                    adjclose / close), indexed by the session's Eastern date
  minutes(ticker)   the last five days of 1-minute bars WITH pre/post, tz-aware
                    America/New_York -- the pre-market window, the overnight
                    futures and the overnight VIX
  cboe(symbol)      a Cboe {SYM}_History.csv: CLOSE by session date

The parsers are pure and tested offline; MarketData adds the network and a
short in-process cache (MARKET_DATA_CACHE_SECONDS, default 600 s) so two
forecasts a few minutes apart do not refetch fifteen years of bars.

Every request is a GET to a fixed public host: no key, no account, nothing
that reaches a broker.
"""

from __future__ import annotations

import io
import json
import os
import threading
import time
import urllib.parse
from collections.abc import Callable
from typing import Any, Protocol

import numpy as np
import pandas as pd

from engine.core.trading_calendar import EASTERN

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/"
CBOE_DAILY = "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/"
OHLC = ("Open", "High", "Low", "Close")


class MarketDataUnavailable(RuntimeError):
    """A source answered with nothing usable."""


class MarketSource(Protocol):
    """What the generator reads; tests hand it canned frames instead."""

    def daily(self, ticker: str) -> pd.DataFrame: ...

    def minutes(self, ticker: str) -> pd.DataFrame: ...

    def cboe(self, symbol: str) -> pd.Series: ...


def yahoo_daily_url(ticker: str) -> str:
    return (
        f"{YAHOO_CHART}{urllib.parse.quote(ticker, safe='')}"
        "?period1=0&period2=9999999999&interval=1d&events=div%2Csplit"
    )


def yahoo_minutes_url(ticker: str) -> str:
    return f"{YAHOO_CHART}{urllib.parse.quote(ticker, safe='')}?range=5d&interval=1m&includePrePost=true"


def cboe_csv_url(symbol: str) -> str:
    return f"{CBOE_DAILY}{symbol}_History.csv"


def _chart_result(payload: dict[str, Any], ticker: str) -> dict[str, Any]:
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise MarketDataUnavailable(f"Yahoo {ticker}: {chart['error']}")
    results = chart.get("result") or []
    if not results or not results[0].get("timestamp"):
        raise MarketDataUnavailable(f"Yahoo {ticker}: no bars")
    return results[0]


def _quote_frame(result: dict[str, Any]) -> pd.DataFrame:
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    columns = {
        name: pd.to_numeric(pd.Series(quote.get(name.lower()) or []), errors="coerce")
        for name in (*OHLC, "Volume")
    }
    length = len(result["timestamp"])
    return pd.DataFrame(
        {
            name: series.reindex(range(length)).to_numpy(dtype=float)
            for name, series in columns.items()
        }
    )


def parse_yahoo_daily(payload: dict[str, Any], ticker: str = "") -> pd.DataFrame:
    """Yahoo's daily chart JSON -> adjusted OHLCV by Eastern session date."""
    result = _chart_result(payload, ticker)
    frame = _quote_frame(result)
    adjusted = ((result.get("indicators") or {}).get("adjclose") or [{}])[0].get("adjclose")
    if adjusted:
        factor = pd.to_numeric(pd.Series(adjusted), errors="coerce").to_numpy(dtype=float) / frame[
            "Close"
        ].to_numpy(dtype=float)
        factor = np.where(np.isfinite(factor) & (factor > 0), factor, 1.0)
        for name in OHLC:
            frame[name] = frame[name] * factor
    zone = (result.get("meta") or {}).get("exchangeTimezoneName") or "America/New_York"
    stamps = pd.to_datetime(pd.Series(result["timestamp"]), unit="s", utc=True).dt.tz_convert(zone)
    frame.index = pd.DatetimeIndex(stamps.dt.tz_localize(None).dt.normalize())
    frame = frame[np.isfinite(frame["Close"]) & (frame["Close"] > 0)]
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    if frame.empty:
        raise MarketDataUnavailable(f"Yahoo {ticker}: no closes")
    return frame


def parse_yahoo_minutes(payload: dict[str, Any], ticker: str = "") -> pd.DataFrame:
    """Yahoo's 1-minute chart JSON -> OHLCV with a tz-aware Eastern index."""
    result = _chart_result(payload, ticker)
    frame = _quote_frame(result)
    frame.index = pd.DatetimeIndex(
        pd.to_datetime(pd.Series(result["timestamp"]), unit="s", utc=True).dt.tz_convert(EASTERN)
    )
    frame = frame[np.isfinite(frame["Close"]) & (frame["Close"] > 0)]
    return frame[~frame.index.duplicated(keep="last")].sort_index()


def parse_cboe_daily_csv(text: str) -> pd.Series:
    """CLOSE from a Cboe {SYM}_History.csv, indexed by session date."""
    frame = pd.read_csv(io.StringIO(text))
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    if "DATE" not in frame or "CLOSE" not in frame:
        raise MarketDataUnavailable(
            f"Cboe CSV is missing DATE/CLOSE columns: {list(frame.columns)[:6]}"
        )
    dates = pd.to_datetime(frame["DATE"], format="%m/%d/%Y", errors="coerce")
    closes = pd.to_numeric(frame["CLOSE"], errors="coerce")
    series = pd.Series(closes.to_numpy(), index=[d.date() if pd.notna(d) else None for d in dates])
    series = series[[index is not None for index in series.index]]
    series = series[(series > 0) & series.notna()]
    series = series[~series.index.duplicated(keep="last")].sort_index()
    if series.empty:
        raise MarketDataUnavailable("Cboe CSV has no valid CLOSE rows")
    return series.astype(float)


def minute_closes(frame: pd.DataFrame | None) -> pd.Series:
    """Finite positive 1-minute closes, Eastern."""
    if frame is None or frame.empty or "Close" not in frame:
        return pd.Series(dtype=float)
    closes = pd.to_numeric(frame["Close"], errors="coerce")
    closes = closes[(closes > 0) & closes.notna()]
    return closes[~closes.index.duplicated(keep="last")].sort_index().astype(float)


def _default_get(url: str) -> bytes:
    # Imported here: research/ml/sources.py's getter (backoff, gzip) is the
    # one this repository already trusts with these hosts.
    from research.ml.sources import _http_get

    return _http_get(url)


class MarketData:
    """The live MarketSource: HTTP plus a short in-process cache."""

    def __init__(
        self,
        get: Callable[[str], bytes] | None = None,
        ttl_seconds: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._get = get or _default_get
        self._ttl = (
            float(ttl_seconds)
            if ttl_seconds is not None
            else max(60.0, float(os.getenv("MARKET_DATA_CACHE_SECONDS", "600")))
        )
        self._clock = clock
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def _cached(self, key: str, load: Callable[[], Any], ttl: float | None = None) -> Any:
        now = self._clock()
        with self._lock:
            hit = self._cache.get(key)
            if hit and now - hit[0] < (ttl if ttl is not None else self._ttl):
                return hit[1].copy()
        value = load()
        with self._lock:
            self._cache[key] = (self._clock(), value.copy())
        return value

    def _json(self, url: str) -> dict[str, Any]:
        return json.loads(self._get(url).decode("utf-8", "replace"))

    def daily(self, ticker: str) -> pd.DataFrame:
        return self._cached(
            f"daily:{ticker}",
            lambda: parse_yahoo_daily(self._json(yahoo_daily_url(ticker)), ticker),
        )

    def minutes(self, ticker: str) -> pd.DataFrame:
        # A minute bar is news within the minute: cache it briefly.
        return self._cached(
            f"minutes:{ticker}",
            lambda: parse_yahoo_minutes(self._json(yahoo_minutes_url(ticker)), ticker),
            ttl=30.0,
        )

    def cboe(self, symbol: str) -> pd.Series:
        # Republished once a day (~17:30 ET): an hour keeps runs cheap.
        return self._cached(
            f"cboe:{symbol}",
            lambda: parse_cboe_daily_csv(
                self._get(cboe_csv_url(symbol)).decode("utf-8", "replace")
            ),
            ttl=3600.0,
        )


__all__ = [
    "MarketData",
    "MarketDataUnavailable",
    "MarketSource",
    "cboe_csv_url",
    "minute_closes",
    "parse_cboe_daily_csv",
    "parse_yahoo_daily",
    "parse_yahoo_minutes",
    "yahoo_daily_url",
    "yahoo_minutes_url",
]
