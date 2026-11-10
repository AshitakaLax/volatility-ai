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
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import zlib
from dataclasses import dataclass
from datetime import date, timedelta
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
# The daily policy-uncertainty index is posted the next morning, and FRED
# carries it a day after that (measured 2026-11-07: FRED's latest was 11-05).
_EPU_RELEASE = timedelta(days=2)
# The SF Fed's news sentiment is refreshed about weekly (2026-11-07: the
# file ran to 11-01), so a day's value can be up to a week old when read.
_WEEKLY_REFRESH = timedelta(days=7)
# The OFR stress index for a day is posted two business days later
# (measured 2026-11-10, a Tuesday: the file ran to Thursday 11-05), so
# four calendar days covers a weekend in between.
_OFR_RELEASE = timedelta(days=4)
# Commitments of Traders: positions as of Tuesday, published Friday at
# 15:30 Eastern, or the Monday after when a federal holiday falls in the
# week. Six days puts the stamp at Monday's close.
_COT_RELEASE = timedelta(days=6)
# SqueezeMetrics posts a session's figures that evening, after the close
# the row is dated to: readable before the next session, never during
# the one it describes.
_EVENING = timedelta(hours=6)


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
    # News-based uncertainty, daily since 1985 (Baker, Bloom & Davis): the
    # free stand-in for a macro-surprise index, whose consensus forecasts
    # are not public (research/ml/tft_inputs.py, s_macro).
    ("USEPUINDXD", "uncertainty", "Economic policy uncertainty, daily", _EPU_RELEASE),
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
    # Added 2026-11-10 for the risk governor (research/strategies/risk_governor.py).
    ("VIX1D", "vol", "S&P 500 1-day implied volatility, from 2022"),
    ("VXD", "vol", "Dow Jones implied volatility"),
    ("VXEEM", "vol", "Emerging-markets ETF implied volatility"),
    # Implied correlation: how much of index volatility is stocks moving
    # together. It rises into a broad sell-off before the index range does.
    ("COR1M", "correlation", "S&P 500 1-month implied correlation"),
    ("COR3M", "correlation", "S&P 500 3-month implied correlation"),
    ("DSPX", "correlation", "S&P 500 dispersion index"),
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
    # The earnings calendar's sixteen Nasdaq-100 reporters
    # (tools/build_earnings_calendar.py), for each release's price reaction:
    # the free stand-in for earnings sentiment (research/ml/tft_inputs.py).
    ("AAPL", "constituent", "Apple"),
    ("MSFT", "constituent", "Microsoft"),
    ("NVDA", "constituent", "Nvidia"),
    ("AMZN", "constituent", "Amazon"),
    ("GOOGL", "constituent", "Alphabet class A"),
    ("GOOG", "constituent", "Alphabet class C"),
    ("META", "constituent", "Meta Platforms"),
    ("AVGO", "constituent", "Broadcom"),
    ("TSLA", "constituent", "Tesla"),
    ("COST", "constituent", "Costco"),
    ("NFLX", "constituent", "Netflix"),
    ("AMD", "constituent", "Advanced Micro Devices"),
    ("CSCO", "constituent", "Cisco"),
    ("INTC", "constituent", "Intel"),
    ("MU", "constituent", "Micron"),
    ("WMT", "constituent", "Walmart"),
    # Added 2026-11-10 for the risk governor: the cross-asset stress and
    # leadership series the lake lacked.
    ("^MOVE", "vol", "ICE BofA MOVE index: Treasury implied volatility"),
    ("^SOX", "index", "PHLX semiconductor index: the Nasdaq-100's leading sector"),
    ("SMH", "sector", "Semiconductors"),
    ("KRE", "sector", "Regional banks: funding stress shows here first"),
    ("JNK", "bond", "High yield corporates (SPDR)"),
    ("IWF", "factor", "Russell 1000 growth"),
    ("IWD", "factor", "Russell 1000 value"),
    ("ARKK", "factor", "Speculative growth, as a risk-appetite gauge"),
    ("HG=F", "commodity", "Copper futures, front month"),
    ("NQ=F", "futures", "Nasdaq-100 futures, front month"),
    ("DX-Y.NYB", "fx", "US dollar index (DXY)"),
)

# ------------------------------------------------------------------
# The San Francisco Fed. Its daily news sentiment index (Buckman,
# Shapiro, Sudhof & Wilson 2020): the tone of economics articles in 24
# major US newspapers, from 1980, as one spreadsheet. The free news
# sentiment series there is.

_FRBSF: tuple[tuple[str, str, str, str, timedelta], ...] = (
    (
        "NEWS_SENTIMENT",
        "https://www.frbsf.org/wp-content/uploads/news_sentiment_data.xlsx",
        "sentiment",
        "SF Fed daily news sentiment index",
        _WEEKLY_REFRESH,
    ),
)

# ------------------------------------------------------------------
# The Office of Financial Research's Financial Stress Index. Daily from
# 2000, built from 33 market series (spreads, valuations, funding,
# safe-haven flows, volatility), zero at the average level of stress.
# One CSV holds the index and its eight contributions; each column is a
# series here. It is the one daily, official composite of "is the system
# under stress", which is the question a regime exit asks.

OFR_FSI_URL = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"

_OFR: tuple[tuple[str, str, str], ...] = (
    ("FSI", "OFR FSI", "OFR financial stress index"),
    ("FSI_CREDIT", "Credit", "OFR FSI: credit contribution"),
    ("FSI_EQUITY", "Equity valuation", "OFR FSI: equity valuation contribution"),
    ("FSI_SAFE", "Safe assets", "OFR FSI: safe-asset contribution"),
    ("FSI_FUNDING", "Funding", "OFR FSI: funding contribution"),
    ("FSI_VOL", "Volatility", "OFR FSI: volatility contribution"),
    ("FSI_US", "United States", "OFR FSI: United States contribution"),
    ("FSI_ADVANCED", "Other advanced economies", "OFR FSI: other advanced economies"),
    ("FSI_EMERGING", "Emerging markets", "OFR FSI: emerging markets"),
)

# ------------------------------------------------------------------
# The CFTC's Traders in Financial Futures report (futures only), from
# its public Socrata endpoint. Weekly from mid-2010 for the consolidated
# Nasdaq-100 and S&P 500 contracts. Each series is one trader group's
# net position as a share of open interest: leveraged funds (hedge funds
# and CTAs), asset managers (institutions) and dealers.

CFTC_TFF_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"

_CFTC_CONTRACTS: tuple[tuple[str, str, str], ...] = (
    ("NDX", "20974+", "Nasdaq-100 futures"),
    ("SPX", "13874+", "S&P 500 futures"),
)
# group -> (the report's long field, its short field, description)
_CFTC_GROUPS: dict[str, tuple[str, str, str]] = {
    "LEV": ("lev_money_positions_long", "lev_money_positions_short", "leveraged funds"),
    "AM": ("asset_mgr_positions_long", "asset_mgr_positions_short", "asset managers"),
    "DEALER": ("dealer_positions_long_all", "dealer_positions_short_all", "dealers"),
}

# ------------------------------------------------------------------
# SqueezeMetrics' free daily file: DIX, the short-sale share of off-
# exchange volume in S&P 500 stocks (dark-pool buying shows up as short
# volume, because the dealer filling the buyer sells short), and GEX,
# dealers' net gamma in S&P 500 options in dollars per 1% move. Low or
# negative GEX means dealers hedge WITH the move, and the next days'
# ranges are wider. From 2011. A commercial site's convenience download,
# not an official series: it can change or vanish, and a failed fetch is
# a recorded failure like any other.

SQUEEZE_URL = "https://squeezemetrics.com/monitor/static/DIX.csv"

_SQUEEZE: tuple[tuple[str, str, str, str], ...] = (
    ("DIX", "dix", "positioning", "Dark-pool short-volume share, S&P 500 stocks"),
    ("GEX", "gex", "positioning", "Dealer gamma exposure, S&P 500 options (USD per 1%)"),
)


def _yahoo_key(symbol: str) -> str:
    """A Yahoo symbol as a file-name key: ^VIX -> VIX, BTC-USD -> BTCUSD,
    HG=F -> HGF, DX-Y.NYB -> DXY."""
    if symbol == "DX-Y.NYB":
        return "DXY"
    return "".join(ch for ch in symbol if ch.isalnum())


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
                key=_yahoo_key(symbol),
                provider="yahoo",
                remote_id=symbol,
                category=category,
                description=description,
                lag=_SAME_DAY_CLOSE,
            )
        )
    for key, column, description in _OFR:
        sources.append(
            Source(
                key=key,
                provider="ofr",
                remote_id=column,
                category="stress",
                description=description,
                lag=_OFR_RELEASE,
            )
        )
    for market, code, market_name in _CFTC_CONTRACTS:
        for group, (_, _, group_name) in _CFTC_GROUPS.items():
            sources.append(
                Source(
                    key=f"{market}_{group}_NET",
                    provider="cftc",
                    remote_id=f"{code}:{group}",
                    category="positioning",
                    description=f"{market_name}: {group_name} net position, share of open interest",
                    lag=_COT_RELEASE,
                )
            )
    for key, column, category, description in _SQUEEZE:
        sources.append(
            Source(
                key=key,
                provider="squeeze",
                remote_id=column,
                category=category,
                description=description,
                lag=_EVENING,
            )
        )
    for key, url, category, description, lag in _FRBSF:
        sources.append(
            Source(
                key=key,
                provider="frbsf",
                remote_id=url,
                category=category,
                description=description,
                lag=lag,
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


_SHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _xlsx_rows(body: bytes, sheet: str) -> list[dict[str, str | None]]:
    """One worksheet of an .xlsx as rows of {column letter: cell text}.

    An .xlsx is a zip of XML parts; the standard library reads the few a
    two-column sheet needs, so one public spreadsheet does not add
    openpyxl to the requirements. Shared and inline strings are resolved;
    every other cell is its raw text (a date is Excel's day number).
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(body))
    except zipfile.BadZipFile as exc:
        raise SourceUnavailable(f"not an .xlsx file: {exc}") from exc
    with archive:
        names = set(archive.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            for item in ET.fromstring(archive.read("xl/sharedStrings.xml")):
                shared.append("".join(t.text or "" for t in item.iter(f"{_SHEET_NS}t")))
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target", "") for r in rels}
        rid = next(
            (
                s.get(f"{_REL_NS}id")
                for s in workbook.iter(f"{_SHEET_NS}sheet")
                if s.get("name") == sheet
            ),
            None,
        )
        if rid not in targets:
            raise SourceUnavailable(f"no sheet named {sheet!r}")
        target = targets[rid].lstrip("/")
        part = target if target.startswith("xl/") else f"xl/{target}"
        root = ET.fromstring(archive.read(part))
    rows = []
    for row in root.iter(f"{_SHEET_NS}row"):
        cells: dict[str, str | None] = {}
        for cell in row.iter(f"{_SHEET_NS}c"):
            column = "".join(ch for ch in cell.get("r", "") if ch.isalpha())
            kind = cell.get("t")
            if kind == "inlineStr":
                text = "".join(t.text or "" for t in cell.iter(f"{_SHEET_NS}t"))
            else:
                value = cell.find(f"{_SHEET_NS}v")
                text = None if value is None else value.text
                if kind == "s" and text is not None:
                    text = shared[int(text)]
            cells[column] = text
        rows.append(cells)
    return rows


def fetch_frbsf(source: Source) -> pd.DataFrame:
    """The news sentiment spreadsheet's Data sheet: a date and a value."""
    rows = _xlsx_rows(_http_get(source.remote_id), "Data")
    if not rows:
        raise SourceUnavailable(f"FRBSF {source.key}: the Data sheet is empty")
    header = {col: (text or "").strip().lower() for col, text in rows[0].items()}
    date_col = next((c for c, h in header.items() if h == "date"), None)
    value_col = next((c for c, h in header.items() if c != date_col and h), None)
    if date_col is None or value_col is None:
        raise SourceUnavailable(f"FRBSF {source.key}: unexpected header {list(header.values())}")
    raw_dates = pd.Series([r.get(date_col) for r in rows[1:]])
    serial = pd.to_numeric(raw_dates, errors="coerce")
    # Excel's day numbers count from 1899-12-30; a text date is parsed as text.
    dates = pd.to_datetime(serial, unit="D", origin="1899-12-30")
    text = serial.isna() & raw_dates.notna()
    if text.any():
        dates[text] = pd.to_datetime(raw_dates[text], format="mixed", errors="coerce")
    values = pd.to_numeric(pd.Series([r.get(value_col) for r in rows[1:]]), errors="coerce")
    frame = pd.DataFrame({"date": dates, "close": values}).dropna()
    out = pd.DataFrame({"timestamp": _stamp(frame["date"], source.lag), "close": frame["close"]})
    return out.reset_index(drop=True)


# One download serves every series cut from the same file: the OFR CSV
# holds nine, SqueezeMetrics' two, a CFTC contract's report three. Kept
# for a few minutes, so a daily service that fetches the registry again
# tomorrow gets tomorrow's file.
_SHARED_TTL_SECONDS = 600.0
_shared_bodies: dict[str, tuple[float, bytes]] = {}


def _shared_get(url: str) -> bytes:
    held = _shared_bodies.get(url)
    if held is not None and time.monotonic() - held[0] < _SHARED_TTL_SECONDS:
        return held[1]
    body = _http_get(url)
    _shared_bodies[url] = (time.monotonic(), body)
    return body


def _column_of(body: bytes, date_column: str, value_column: str, what: str) -> pd.DataFrame:
    """One dated column of a CSV as `date`, `close`, missing values dropped."""
    frame = pd.read_csv(io.StringIO(body.decode("utf-8", "replace")))
    frame.columns = [str(c).strip() for c in frame.columns]
    if date_column not in frame.columns or value_column not in frame.columns:
        raise SourceUnavailable(f"{what}: no {value_column!r} among {list(frame.columns)}")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(frame[date_column], errors="coerce"),
            "close": pd.to_numeric(frame[value_column], errors="coerce"),
        }
    )
    return out.dropna().reset_index(drop=True)


def fetch_ofr(source: Source) -> pd.DataFrame:
    frame = _column_of(_shared_get(OFR_FSI_URL), "Date", source.remote_id, f"OFR {source.key}")
    return pd.DataFrame({"timestamp": _stamp(frame["date"], source.lag), "close": frame["close"]})


def fetch_squeeze(source: Source) -> pd.DataFrame:
    frame = _column_of(
        _shared_get(SQUEEZE_URL), "date", source.remote_id, f"SqueezeMetrics {source.key}"
    )
    return pd.DataFrame({"timestamp": _stamp(frame["date"], source.lag), "close": frame["close"]})


def cftc_net_share(rows: list[dict], long_field: str, short_field: str) -> pd.DataFrame:
    """(long - short) / open interest for each report in `rows`, as
    `date`, `close`. A report missing a field, or with no open interest,
    is dropped rather than read as zero."""
    records = []
    for row in rows:
        try:
            held_long = float(row[long_field])
            held_short = float(row[short_field])
            open_interest = float(row["open_interest_all"])
        except (KeyError, TypeError, ValueError):
            continue
        if open_interest <= 0:
            continue
        records.append(
            (row.get("report_date_as_yyyy_mm_dd"), (held_long - held_short) / open_interest)
        )
    frame = pd.DataFrame(records, columns=["date", "close"])
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame.dropna().sort_values("date").reset_index(drop=True)


def fetch_cftc(source: Source) -> pd.DataFrame:
    code, _, group = source.remote_id.partition(":")
    if group not in _CFTC_GROUPS:
        raise SourceUnavailable(f"CFTC {source.key}: unknown trader group {group!r}")
    long_field, short_field, _ = _CFTC_GROUPS[group]
    query = urllib.parse.urlencode(
        {
            "cftc_contract_market_code": code,
            "$select": "report_date_as_yyyy_mm_dd,open_interest_all,"
            + ",".join(f"{a},{b}" for a, b, _ in _CFTC_GROUPS.values()),
            "$order": "report_date_as_yyyy_mm_dd",
            # Weekly since 2010 is under a thousand reports; the default page is 1,000.
            "$limit": "50000",
        }
    )
    try:
        rows = json.loads(_shared_get(f"{CFTC_TFF_URL}?{query}").decode("utf-8", "replace"))
    except json.JSONDecodeError as exc:
        raise SourceUnavailable(f"CFTC {source.key}: not JSON ({exc})") from exc
    if not isinstance(rows, list):
        raise SourceUnavailable(f"CFTC {source.key}: unexpected answer {str(rows)[:120]}")
    frame = cftc_net_share(rows, long_field, short_field)
    return pd.DataFrame({"timestamp": _stamp(frame["date"], source.lag), "close": frame["close"]})


_FETCHERS = {
    "fred": fetch_fred,
    "cboe": fetch_cboe,
    "yahoo": fetch_yahoo,
    "frbsf": fetch_frbsf,
    "ofr": fetch_ofr,
    "cftc": fetch_cftc,
    "squeeze": fetch_squeeze,
}


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


def manifest_entry(source: Source, frame: pd.DataFrame) -> dict:
    """A fetched series' row in manifest.json: what the external lake's
    ingest reads its provider, category and publication lag from."""
    return {
        "provider": source.provider,
        "remote_id": source.remote_id,
        "category": source.category,
        "description": source.description,
        "lag_days": source.lag.total_seconds() / 86400,
        "file": source.filename,
        "rows": len(frame),
        "first": str(frame["timestamp"].iloc[0]),
        "last": str(frame["timestamp"].iloc[-1]),
        "columns": list(frame.columns),
    }


def manifest_key(source: Source) -> str:
    """Keyed by provider AND key: Yahoo's ^VIX and CBOE's VIX both reduce
    to "VIX", and keying on that alone silently drops one of the two."""
    return f"{source.provider}_{source.key}"


# ------------------------------------------------------------------
# The FOMC's meeting calendar. Not a series: the dates the strategies'
# event-day sizing reads (engine/data/fomc_calendar.py holds them as a
# list in the source). The Federal Reserve publishes the schedule two
# years ahead on one page, and tools/refresh_external.py reads it daily
# to say when that list has fallen behind.

FOMC_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

_MONTHS = {
    name: number
    for number, names in enumerate(
        (
            ("january", "jan"),
            ("february", "feb"),
            ("march", "mar"),
            ("april", "apr"),
            ("may",),
            ("june", "jun"),
            ("july", "jul"),
            ("august", "aug"),
            ("september", "sep", "sept"),
            ("october", "oct"),
            ("november", "nov"),
            ("december", "dec"),
        ),
        start=1,
    )
    for name in names
}
_FOMC_YEAR = re.compile(r">\s*(\d{4}) FOMC Meetings\s*<")
_FOMC_MEETING = re.compile(
    r'fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>\s*</div>\s*'
    r'<div class="fomc-meeting__date[^>]*>([^<]+)<'
)


def fomc_decision_dates(html: str) -> list[date]:
    """The decision day (the last day) of every scheduled meeting on the
    Federal Reserve's calendar page, in date order.

    A row is a month ("March", or "Apr/May" for a meeting that spans two)
    and its days ("17-18*", "30-1"). Notation votes, unscheduled meetings
    and cancelled ones carry a note in parentheses and are left out: the
    event-day research was done on scheduled decisions.
    """
    years = [(m.start(), int(m.group(1))) for m in _FOMC_YEAR.finditer(html)]
    found: set[date] = set()
    for match in _FOMC_MEETING.finditer(html):
        before = [year for position, year in years if position < match.start()]
        days_text = match.group(2).strip()
        if not before or "(" in days_text:
            continue
        months = [
            _MONTHS[part.strip().lower()]
            for part in match.group(1).split("/")
            if part.strip().lower() in _MONTHS
        ]
        days = [int(day) for day in re.findall(r"\d+", days_text)]
        if not months or not days:
            continue
        try:
            found.add(date(before[-1], months[-1], days[-1]))
        except ValueError:
            continue
    return sorted(found)


def fetch_fomc_decision_dates() -> list[date]:
    dates = fomc_decision_dates(_http_get(FOMC_CALENDAR_URL).decode("utf-8", "replace"))
    if not dates:
        raise SourceUnavailable(f"{FOMC_CALENDAR_URL}: no meeting dates found (page changed?)")
    return dates


def default_directory() -> Path:
    """Where fetched series live. Gitignored: this is downloaded data."""
    return Path(__file__).resolve().parent.parent.parent / "data" / "external"
