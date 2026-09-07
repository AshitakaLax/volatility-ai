"""Public market inputs: a registry of free sources, and fetchers for them.

--------------------------------------------------------------------
THE POINT OF THIS FILE IS BREADTH

The instruction was to reach for as many public inputs as possible and
work backwards from there, so this registry is deliberately wider than
any model needs. Pruning is a later, measured step; it is much cheaper
to drop a column that carries no signal than to discover months in that
a needed series was never collected.

Nothing here requires an API key. Every source is a public endpoint,
and every fetch is verified against a live response before being listed
-- reachable is not the same as usable. Stooq, for one, answers HTTP 200
with a JavaScript bot challenge rather than the CSV it appears to
promise, and is deliberately absent for that reason.

--------------------------------------------------------------------
PUBLICATION LAG, WHICH IS THE WHOLE CORRECTNESS PROBLEM

A macro observation is stamped with the date it DESCRIBES, not the date
it became knowable, and those are different by anything from hours to
six weeks:

    DGS10 for a Tuesday    -- published after that Tuesday's close
    ICSA for a week        -- published the following Thursday
    CPIAUCSL for August    -- published in mid-September

Joining on the observation date would let a backtest read August's CPI
while trading August, and the resulting equity curve would be a
forecast of the past. That error is silent: every number still looks
plausible, the curve is simply better than reality allowed.

So every source declares how late its number actually arrives, and the
written timestamp is the moment the value could FIRST have been read.
ExternalIndexSeries.scalar() returns the most recent value at or before
a bar, which makes the join safe by construction once the stamps are
honest -- the safety lives in the data, not in the caller remembering.

Lags here are deliberately conservative. Being a day late costs a
little signal; being an hour early invents it.

--------------------------------------------------------------------
THE OUTPUT CONTRACT

Every fetcher writes `timestamp,close` with a tz-aware UTC timestamp,
which is exactly what the existing (and until now dormant)
ExternalIndexSeries.from_csv expects. That is the reason for the shape:
the as-of join layer is already written and tested, and this reuses it
rather than growing a second one.
"""

from __future__ import annotations

import gzip
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pandas as pd

# Long enough for FRED's slower series, short enough that a hung
# endpoint cannot stall a 100-source pull.
TIMEOUT_SECONDS = 45

_USER_AGENT = "Mozilla/5.0 (compatible; volatility-ai research; +https://github.com/AshitakaLax/volatility-ai)"

# US equity close, 16:00 ET, in UTC. Standard time is 21:00Z and
# daylight time 20:00Z; the later of the two is used year-round so a
# stamp is never early on either side of a DST boundary.
_CLOSE_HOUR_UTC = 21


@dataclass(frozen=True)
class Source:
    """One public series, and how late its number really is.

    lag is measured from the END of the period the observation
    describes to the moment it could first be read.
    """

    key: str
    provider: str
    remote_id: str
    category: str
    description: str
    lag: timedelta

    @property
    def filename(self) -> str:
        return f"{self.provider}_{self.key}.csv"


# ------------------------------------------------------------------
# Lag constants, named so the reasoning survives in the registry below.

_SAME_DAY_CLOSE = timedelta(hours=0)  # settles at the close it is stamped to
_NEXT_DAY = timedelta(days=1)  # daily macro, published after the close
_WEEKLY_RELEASE = timedelta(days=6)  # e.g. claims: week ends Sat, out Thu
_MONTHLY_RELEASE = timedelta(days=45)  # CPI/payrolls/production, generously
_QUARTERLY_RELEASE = timedelta(days=90)  # GDP-style, revised for longer still


# ------------------------------------------------------------------
# FRED. The Federal Reserve's series archive. Free, no key, deep
# history (DGS10 reaches 1962). Fetched one series per request: the
# multi-id form of fredgraph.csv answers with a malformed body once
# more than a handful are asked for, which is not worth working around
# for a saving of a few seconds.

_FRED: tuple[tuple[str, str, str, timedelta], ...] = (
    # Policy and the short end
    ("EFFR", "rates", "Effective federal funds rate", _NEXT_DAY),
    ("SOFR", "rates", "Secured overnight financing rate", _NEXT_DAY),
    ("DGS1MO", "rates", "1-month Treasury constant maturity", _NEXT_DAY),
    ("DGS3MO", "rates", "3-month Treasury constant maturity", _NEXT_DAY),
    ("DGS6MO", "rates", "6-month Treasury constant maturity", _NEXT_DAY),
    ("DGS1", "rates", "1-year Treasury constant maturity", _NEXT_DAY),
    ("DGS2", "rates", "2-year Treasury constant maturity", _NEXT_DAY),
    ("DGS5", "rates", "5-year Treasury constant maturity", _NEXT_DAY),
    ("DGS10", "rates", "10-year Treasury constant maturity", _NEXT_DAY),
    ("DGS30", "rates", "30-year Treasury constant maturity", _NEXT_DAY),
    # Curve shape. Inversion is the most-watched recession tell there is.
    ("T10Y2Y", "curve", "10y minus 2y spread", _NEXT_DAY),
    ("T10Y3M", "curve", "10y minus 3m spread", _NEXT_DAY),
    ("T5YIFR", "curve", "5y forward inflation expectation", _NEXT_DAY),
    ("T10YFF", "curve", "10y minus fed funds, from 1962", _NEXT_DAY),
    # Credit. Widening spreads lead equity stress more reliably than
    # equity vol does.
    #
    # The Moody's pair comes FIRST because it is the one with history:
    # ICE licenses the BAML indices, and FRED serves only a rolling
    # three years of them without an API key (measured 2026-09-06 --
    # BAMLH0A0HYM2 returned 795 rows starting 2023-09-05, and an
    # explicit cosd does not lift it). Over a 2016-2026 training
    # window that is ~28% coverage, so the BAML series are kept as a
    # recent-history bonus and Moody's carries the actual signal.
    ("BAA10Y", "credit", "Moody's Baa minus 10y Treasury, from 1986", _NEXT_DAY),
    ("AAA10Y", "credit", "Moody's Aaa minus 10y Treasury, from 1983", _NEXT_DAY),
    ("DBAA", "credit", "Moody's Baa corporate yield", _NEXT_DAY),
    ("DAAA", "credit", "Moody's Aaa corporate yield", _NEXT_DAY),
    ("BAMLH0A0HYM2", "credit", "ICE BofA US high-yield OAS (3y cap)", _NEXT_DAY),
    ("BAMLC0A0CM", "credit", "ICE BofA US corporate OAS (3y cap)", _NEXT_DAY),
    ("BAMLH0A3HYC", "credit", "ICE BofA CCC and lower OAS (3y cap)", _NEXT_DAY),
    ("BAMLEMCBPIOAS", "credit", "ICE BofA emerging markets OAS (3y cap)", _NEXT_DAY),
    ("TEDRATE", "credit", "TED spread (discontinued 2022)", _NEXT_DAY),
    # Inflation expectations, market-implied and daily
    ("T5YIE", "inflation", "5-year breakeven inflation", _NEXT_DAY),
    ("T10YIE", "inflation", "10-year breakeven inflation", _NEXT_DAY),
    # Dollar and commodities
    ("DTWEXBGS", "fx", "Trade-weighted USD, broad goods and services", _NEXT_DAY),
    ("DTWEXAFEGS", "fx", "Trade-weighted USD, advanced economies", _NEXT_DAY),
    ("DEXUSEU", "fx", "USD per euro", _NEXT_DAY),
    ("DEXJPUS", "fx", "Yen per USD", _NEXT_DAY),
    ("DEXCHUS", "fx", "Yuan per USD", _NEXT_DAY),
    ("DCOILWTICO", "commodity", "WTI crude spot", _NEXT_DAY),
    ("DCOILBRENTEU", "commodity", "Brent crude spot", _NEXT_DAY),
    ("DHHNGSP", "commodity", "Henry Hub natural gas spot", _NEXT_DAY),
    # Financial conditions and stress indices
    ("NFCI", "stress", "Chicago Fed national financial conditions", _WEEKLY_RELEASE),
    ("ANFCI", "stress", "Chicago Fed adjusted NFCI", _WEEKLY_RELEASE),
    ("STLFSI4", "stress", "St. Louis Fed financial stress index", _WEEKLY_RELEASE),
    ("VIXCLS", "vol", "CBOE VIX close, via FRED", _SAME_DAY_CLOSE),
    # Fed balance sheet and money. Weekly, and revised.
    ("WALCL", "liquidity", "Fed total assets", _WEEKLY_RELEASE),
    ("RRPONTSYD", "liquidity", "Overnight reverse repo volume", _NEXT_DAY),
    ("WTREGEN", "liquidity", "Treasury general account", _WEEKLY_RELEASE),
    ("M2SL", "liquidity", "M2 money stock", _MONTHLY_RELEASE),
    # Labour
    ("ICSA", "labour", "Initial jobless claims", _WEEKLY_RELEASE),
    ("CCSA", "labour", "Continuing claims", _WEEKLY_RELEASE),
    ("UNRATE", "labour", "Unemployment rate", _MONTHLY_RELEASE),
    ("PAYEMS", "labour", "Nonfarm payrolls", _MONTHLY_RELEASE),
    ("SAHMREALTIME", "labour", "Sahm rule recession indicator", _MONTHLY_RELEASE),
    # Prices and activity
    ("CPIAUCSL", "macro", "CPI, all urban consumers", _MONTHLY_RELEASE),
    ("CPILFESL", "macro", "Core CPI", _MONTHLY_RELEASE),
    ("PCEPILFE", "macro", "Core PCE price index", _MONTHLY_RELEASE),
    ("INDPRO", "macro", "Industrial production", _MONTHLY_RELEASE),
    ("UMCSENT", "macro", "Michigan consumer sentiment", _MONTHLY_RELEASE),
    ("HOUST", "macro", "Housing starts", _MONTHLY_RELEASE),
    ("MORTGAGE30US", "macro", "30-year fixed mortgage rate", _WEEKLY_RELEASE),
    ("GDPC1", "macro", "Real GDP", _QUARTERLY_RELEASE),
    ("USREC", "macro", "NBER recession indicator", _QUARTERLY_RELEASE),
    ("USSLIND", "macro", "Leading index for the United States", _MONTHLY_RELEASE),
)

# ------------------------------------------------------------------
# CBOE. The volatility complex, straight from the exchange, as daily
# OHLC. This is the real index rather than an ETF proxy: VIXY decays
# with roll cost and would teach a model the shape of contango instead
# of the shape of fear.

_CBOE: tuple[tuple[str, str, str], ...] = (
    ("VIX", "vol", "S&P 500 30-day implied volatility"),
    ("VIX9D", "vol", "S&P 500 9-day implied volatility"),
    ("VIX3M", "vol", "S&P 500 3-month implied volatility"),
    ("VIX6M", "vol", "S&P 500 6-month implied volatility"),
    ("VVIX", "vol", "Volatility of VIX"),
    ("SKEW", "vol", "Tail-risk skew of S&P 500 options"),
    ("VXN", "vol", "Nasdaq-100 implied volatility"),
    ("RVX", "vol", "Russell 2000 implied volatility"),
    ("OVX", "vol", "Crude oil implied volatility"),
    ("GVZ", "vol", "Gold implied volatility"),
)

# ------------------------------------------------------------------
# Yahoo. Daily bars for cross-asset context. The sector and factor
# entries matter more than usual here: the funds this project is
# pointed at (RSP, COWZ, SPYD) are defensive tilts, and the way to see
# a defensive tilt working is to watch it against the thing it is a
# tilt AWAY from -- so the offsetting legs (XLK, QQQ, SPY) are
# collected too, as the denominators of ratios rather than as
# candidates to trade.

_YAHOO: tuple[tuple[str, str, str], ...] = (
    # The funds under study, and their reference points
    ("RSP", "fund", "Invesco S&P 500 equal weight"),
    ("COWZ", "fund", "Pacer US cash cows 100"),
    ("SPYD", "fund", "SPDR S&P 500 high dividend"),
    ("SPY", "benchmark", "S&P 500"),
    ("QQQ", "benchmark", "Nasdaq-100"),
    ("IWM", "benchmark", "Russell 2000"),
    ("TQQQ", "benchmark", "3x Nasdaq-100, this project's main dataset"),
    # Broad indices, for breadth and dispersion
    ("^GSPC", "index", "S&P 500 index"),
    ("^NDX", "index", "Nasdaq-100 index"),
    ("^RUT", "index", "Russell 2000 index"),
    ("^DJI", "index", "Dow Jones industrial average"),
    ("^VIX", "index", "VIX index via Yahoo, as a cross-check on CBOE"),
    # Sectors. Defensive-over-cyclical ratios are among the cleanest
    # risk-appetite reads available without paid data.
    ("XLU", "sector", "Utilities (defensive)"),
    ("XLP", "sector", "Consumer staples (defensive)"),
    ("XLV", "sector", "Health care (defensive)"),
    ("XLK", "sector", "Technology (cyclical)"),
    ("XLY", "sector", "Consumer discretionary (cyclical)"),
    ("XLI", "sector", "Industrials (cyclical)"),
    ("XLF", "sector", "Financials"),
    ("XLE", "sector", "Energy"),
    ("XLB", "sector", "Materials"),
    ("XLRE", "sector", "Real estate"),
    ("XLC", "sector", "Communication services"),
    # Factors, which is what these funds actually are
    ("VLUE", "factor", "MSCI USA value"),
    ("MTUM", "factor", "MSCI USA momentum"),
    ("QUAL", "factor", "MSCI USA quality"),
    ("USMV", "factor", "MSCI USA minimum volatility"),
    ("SPHD", "factor", "S&P 500 high dividend low volatility"),
    ("VYM", "factor", "High dividend yield"),
    ("NOBL", "factor", "Dividend aristocrats"),
    # Duration and credit, as traded
    ("TLT", "bond", "20+ year Treasuries"),
    ("IEF", "bond", "7-10 year Treasuries"),
    ("SHY", "bond", "1-3 year Treasuries"),
    ("AGG", "bond", "US aggregate bond"),
    ("LQD", "bond", "Investment grade corporates"),
    ("HYG", "bond", "High yield corporates"),
    ("TIP", "bond", "Inflation protected Treasuries"),
    # Commodities and real assets
    ("GLD", "commodity", "Gold"),
    ("SLV", "commodity", "Silver"),
    ("USO", "commodity", "Crude oil"),
    ("DBC", "commodity", "Broad commodities"),
    ("GDX", "commodity", "Gold miners"),
    # International, for global risk transmission
    ("EFA", "international", "Developed markets ex-US"),
    ("EEM", "international", "Emerging markets"),
    ("VGK", "international", "Europe"),
    ("EWJ", "international", "Japan"),
    ("FXI", "international", "China large cap"),
    # Currency and crypto, as risk-appetite proxies
    ("UUP", "fx", "US dollar bullish fund"),
    ("FXE", "fx", "Euro"),
    ("FXY", "fx", "Japanese yen"),
    ("BTC-USD", "crypto", "Bitcoin"),
    ("ETH-USD", "crypto", "Ethereum"),
)


def registry() -> list[Source]:
    """Every source, in one list."""
    sources: list[Source] = []
    for series_id, category, description, lag in _FRED:
        sources.append(
            Source(
                key=series_id,
                provider="fred",
                remote_id=series_id,
                category=category,
                description=description,
                lag=lag,
            )
        )
    for index_id, category, description in _CBOE:
        sources.append(
            Source(
                key=index_id,
                provider="cboe",
                remote_id=index_id,
                category=category,
                description=description,
                # An index level settles at the close it is stamped to.
                lag=_SAME_DAY_CLOSE,
            )
        )
    for symbol, category, description in _YAHOO:
        sources.append(
            Source(
                key=symbol.replace("^", "").replace("-", ""),
                provider="yahoo",
                remote_id=symbol,
                category=category,
                description=description,
                lag=_SAME_DAY_CLOSE,
            )
        )
    return sources


# ------------------------------------------------------------------
# Fetching


class SourceUnavailable(RuntimeError):
    """A source could not be fetched, or answered with something unusable."""


def _http_get(url: str, *, retries: int = 3) -> bytes:
    """GET with backoff, transparently decompressing.

    Some of these endpoints answer gzipped without being asked, and
    urllib does not decompress for you -- a body read as UTF-8 then
    fails on the gzip magic bytes rather than on anything meaningful.
    """
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    last: Exception | None = None

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                body = response.read()
                encoding = (response.headers.get("Content-Encoding") or "").lower()
            if body[:2] == b"\x1f\x8b" or "gzip" in encoding:
                body = gzip.decompress(body)
            elif "deflate" in encoding:
                body = zlib.decompress(body, -zlib.MAX_WBITS)
            return body
        except (TimeoutError, urllib.error.URLError, OSError, EOFError, zlib.error) as exc:
            last = exc
            if attempt < retries - 1:
                # Linear, not exponential: these are rate limits and
                # transient resets, not a queue that needs draining.
                time.sleep(1.5 * (attempt + 1))

    raise SourceUnavailable(f"{url}: {type(last).__name__}: {last}")


def _stamp(dates: pd.Series, lag: timedelta) -> pd.Series:
    """Observation dates -> the UTC moment each value could be read.

    The close hour is added on top of the lag so that a same-day series
    lands at the close rather than at midnight, which would otherwise
    make a whole trading day's bars read a level that had not printed.
    """
    naive = pd.to_datetime(dates).dt.normalize()
    return naive.dt.tz_localize("UTC") + lag + timedelta(hours=_CLOSE_HOUR_UTC)


def fetch_fred(source: Source) -> pd.DataFrame:
    body = _http_get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={source.remote_id}")
    frame = pd.read_csv(io.StringIO(body.decode("utf-8", "replace")))

    # FRED renamed this column from DATE to observation_date; accept both
    # so a future rename is a clear error rather than a KeyError.
    date_column = next(
        (c for c in ("observation_date", "DATE", "date") if c in frame.columns), None
    )
    if date_column is None or len(frame.columns) < 2:
        raise SourceUnavailable(
            f"FRED {source.remote_id}: unexpected columns {list(frame.columns)}"
        )

    value_column = next(c for c in frame.columns if c != date_column)
    # FRED writes "." for a missing observation (a holiday, or a series
    # that has not printed yet). Coerced to NaN and dropped, so the
    # as-of lookup never returns a hole as though it were a reading.
    values = pd.to_numeric(frame[value_column], errors="coerce")

    out = pd.DataFrame({"timestamp": _stamp(frame[date_column], source.lag), "close": values})
    return out.dropna().reset_index(drop=True)


def fetch_cboe(source: Source) -> pd.DataFrame:
    body = _http_get(
        f"https://cdn.cboe.com/api/global/us_indices/daily_prices/{source.remote_id}_History.csv"
    )
    frame = pd.read_csv(io.StringIO(body.decode("utf-8", "replace")))
    frame.columns = [str(c).strip().upper() for c in frame.columns]

    if "DATE" not in frame.columns or len(frame.columns) < 2:
        raise SourceUnavailable(
            f"CBOE {source.remote_id}: unexpected columns {list(frame.columns)}"
        )

    # CBOE publishes two shapes and does not say which you will get:
    # the headline indices come as DATE,OPEN,HIGH,LOW,CLOSE, while
    # VVIX, SKEW, OVX and GVZ come as DATE,<NAME> with the close only.
    # Both are accepted; the second simply carries no daily range.
    close_column = "CLOSE" if "CLOSE" in frame.columns else frame.columns[1]

    columns = {
        "timestamp": _stamp(pd.to_datetime(frame["DATE"], format="mixed"), source.lag),
        "close": pd.to_numeric(frame[close_column], errors="coerce"),
    }
    # OHLC where it is offered: the daily RANGE of a volatility index
    # carries information its close does not.
    if "HIGH" in frame.columns and "LOW" in frame.columns:
        columns["high"] = pd.to_numeric(frame["HIGH"], errors="coerce")
        columns["low"] = pd.to_numeric(frame["LOW"], errors="coerce")

    return pd.DataFrame(columns).dropna(subset=["close"]).reset_index(drop=True)


def fetch_yahoo(source: Source) -> pd.DataFrame:
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(source.remote_id)}"
        "?period1=0&period2=9999999999&interval=1d&events=div%2Csplit"
    )
    payload = json.loads(_http_get(url).decode("utf-8", "replace"))

    error = (payload.get("chart") or {}).get("error")
    if error:
        raise SourceUnavailable(f"Yahoo {source.remote_id}: {error}")
    results = (payload.get("chart") or {}).get("result") or []
    if not results:
        raise SourceUnavailable(f"Yahoo {source.remote_id}: empty result")

    result = results[0]
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    adjusted = ((result.get("indicators") or {}).get("adjclose") or [{}])[0].get("adjclose")

    if not timestamps or not quote.get("close"):
        raise SourceUnavailable(f"Yahoo {source.remote_id}: no close series")

    # Adjusted close where offered. These are dividend payers -- SPYD
    # yields around 4% -- and an unadjusted series would show each
    # distribution as a price drop the strategy never actually suffered.
    close = adjusted if adjusted else quote["close"]

    # Yahoo stamps a daily bar at the session OPEN. The close is what is
    # being recorded, so the stamp is moved to the close.
    stamped = pd.to_datetime(pd.Series(timestamps), unit="s", utc=True).dt.normalize()

    out = pd.DataFrame(
        {
            "timestamp": stamped + source.lag + timedelta(hours=_CLOSE_HOUR_UTC),
            "close": pd.to_numeric(pd.Series(close), errors="coerce"),
            "volume": pd.to_numeric(pd.Series(quote.get("volume")), errors="coerce"),
        }
    )
    return out.dropna(subset=["close"]).reset_index(drop=True)


_FETCHERS = {"fred": fetch_fred, "cboe": fetch_cboe, "yahoo": fetch_yahoo}


def fetch(source: Source) -> pd.DataFrame:
    fetcher = _FETCHERS.get(source.provider)
    if fetcher is None:
        raise SourceUnavailable(f"no fetcher for provider {source.provider!r}")
    frame = fetcher(source)
    if frame.empty:
        raise SourceUnavailable(f"{source.provider} {source.remote_id}: no rows after cleaning")
    # Duplicate stamps would make an as-of lookup depend on row order.
    frame = frame.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    return frame.reset_index(drop=True)


def default_directory() -> Path:
    """Where fetched series live. Gitignored: this is downloaded data."""
    return Path(__file__).resolve().parent.parent.parent / "data" / "external"
