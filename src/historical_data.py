"""
Bulk historical-bar download -- the backtest's data source.

Separate from src/alpaca_market_data.py on purpose. That module is the
live loop's price source and commits to supplying "exactly what
src/live_trading_loop.py needs ... and nothing else": one bar, now.
This is a different lifecycle -- offline, paginated, writes files, and
measured in hundreds of thousands of rows. Putting it in the tick
path's dependency would be a batch concern living inside a hot loop.

--------------------------------------------------------------------
THE OUTPUT MUST BE BACKTEST-READY OR IT IS WORTHLESS.

data_validation.validate() runs HERE, before anything is written. The
downloader is structurally unable to emit a CSV that
OptimizationController.__init__ would later reject -- a failure
surfaces at fetch time, with the download's own context, rather than
three days later in the middle of a sweep.

That matters more than it sounds, because validate()'s REQUIRED_COLUMNS
is only {"close"} while optimization_controller._simulate_single reads
row.open/high/low/close via itertuples. A frame missing OHLC passes
validation cleanly and then dies with an AttributeError mid-sweep. So
this module pins the full column set rather than trusting the
validator to catch a short frame.
--------------------------------------------------------------------
ON THE FEED: iex, and deliberately not sip.

sip is the full consolidated tape and its historical endpoint works on
a free account -- roughly 2.4x the bars. It is still the wrong choice
here, because sip's REALTIME endpoint returns "subscription does not
permit querying recent SIP data" without a paid plan. The live loop
can therefore only ever observe IEX. Backtesting on SIP would tune
parameters against a tape production is structurally unable to see.

Match the feed you will trade on. That is the whole rule.
--------------------------------------------------------------------
ON ADJUSTMENT: "all", and it is not a stylistic default.

An unadjusted split appears as a single bar dropping ~66% (TQQQ split
3:1 in January 2022). A grid strategy reads that as a catastrophic dip
and fires every rung at once, at a price that never existed, producing
a backtest that looks like a spectacular win. The only thing standing
between that and a shipped parameter set is validate()'s >15% move
warning -- a logging.warning that scrolls past unread in a sweep
printing hundreds of lines. So the safe value is the default.

The trade-off, stated plainly: adjusted historical prices differ in
LEVEL from the raw prices the live loop trades. Over a window with no
corporate action they are identical; over years they are not. That is
why the adjustment is recorded in both the filename and the sidecar --
a raw file must never be mistakable for an adjusted one.
--------------------------------------------------------------------
WHAT THIS MODULE WILL NOT DO: fill gaps, forward-fill, or resample to
a uniform grid. Missing minutes are real -- IEX simply had no print --
and fabricated bars pass validate() cleanly (finite, positive,
monotonic, unique). The sweep would then trade invented prices with
zero warning. Gaps are honest; synthetic bars are not.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from src import data_validation
from src.exceptions import ConfigurationError, DataValidationError
from src.retry_policy import RetryConfig, retry_call

logger = logging.getLogger("Optimizer")

# The exact column set and order of tests/fixtures/regression_ohlcv.csv.
# Pinned here rather than inferred, because a frame missing OHLC passes
# data_validation but breaks _simulate_single's itertuples access.
BACKTEST_COLUMNS = ["open", "high", "low", "close", "volume"]

# US regular trading hours, expressed in exchange-local time. NEVER
# hardcode the UTC equivalent: 13:30-20:00Z is correct only outside US
# daylight saving and wrong for roughly half the year.
MARKET_OPEN_ET = "09:30"
MARKET_CLOSE_ET = "16:00"
EXCHANGE_TZ = "America/New_York"

_TIMEFRAMES = {
    "1Min": (1, "Minute"),
    "5Min": (5, "Minute"),
    "15Min": (15, "Minute"),
    "30Min": (30, "Minute"),
    "1Hour": (1, "Hour"),
    "1Day": (1, "Day"),
}


@dataclass(frozen=True)
class FetchSpec:
    """One download request, fully specified.

    Frozen and explicit so the sidecar can record exactly what was
    asked for -- a result whose provenance is ambiguous is not
    reproducible.
    """

    symbol: str
    start: datetime
    end: datetime
    timeframe: str = "1Min"
    feed: str = "iex"
    adjustment: str = "all"
    regular_hours_only: bool = True


@dataclass(frozen=True)
class DownloadReport:
    """What a download actually produced.

    Carries the bar interval and trading-day count specifically so a
    timeframe mismatch is visible in the output. Grid steps chosen for
    daily bars applied to minute bars produce near-zero trades, and
    nothing downstream annualizes or otherwise notices.
    """

    symbol: str
    timeframe: str
    feed: str
    adjustment: str
    rows: int
    first_timestamp: datetime | None
    last_timestamp: datetime | None
    trading_days: int
    dropped_extended_hours: int
    dropped_duplicates: int
    path: Path
    sha256: str


def _require_alpaca_data():
    """Import the market-data SDK lazily, matching the broker and
    live-data adapters' optional-dependency handling."""
    try:
        from alpaca.data.enums import Adjustment, DataFeed
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    except ImportError as e:  # pragma: no cover - only without the SDK
        raise ConfigurationError(
            "alpaca-py is required to download historical data but is not installed. "
            "Install it with `pip install alpaca-py`."
        ) from e
    return (
        Adjustment,
        DataFeed,
        StockHistoricalDataClient,
        StockBarsRequest,
        TimeFrame,
        TimeFrameUnit,
    )


def parse_timeframe(text: str):
    """Map a CLI timeframe string to an alpaca-py TimeFrame.

    A closed set rather than free-form parsing: an unrecognized string
    should fail immediately with the valid options, not reach the API
    and come back as an opaque 422.
    """
    *_, TimeFrame, TimeFrameUnit = _require_alpaca_data()
    if text not in _TIMEFRAMES:
        raise ConfigurationError(
            f"Unknown timeframe {text!r}. Valid values: {', '.join(sorted(_TIMEFRAMES))}"
        )
    amount, unit = _TIMEFRAMES[text]
    return TimeFrame(amount, getattr(TimeFrameUnit, unit))


def resolve_window(
    *, days: int | None = None, start: str | None = None, end: str | None = None, now=None
) -> tuple[datetime, datetime]:
    """Turn CLI arguments into an explicit UTC window.

    The end defaults to 16 minutes ago, not "now". Alpaca's free tier
    refuses SIP data inside the last 15 minutes, and a window ending at
    the current instant is the single most common way to trip that --
    so the default sits just outside it rather than leaving the user to
    discover the rule from a 403.
    """
    now = now or datetime.now(UTC)
    if start is not None or end is not None:
        if start is None or end is None:
            raise ConfigurationError("--start and --end must be given together.")
        s = pd.Timestamp(start).to_pydatetime()
        e = pd.Timestamp(end).to_pydatetime()
        s = s.replace(tzinfo=UTC) if s.tzinfo is None else s.astimezone(UTC)
        e = e.replace(tzinfo=UTC) if e.tzinfo is None else e.astimezone(UTC)
    else:
        if days is None:
            raise ConfigurationError("Pass either --days or both --start and --end.")
        if days <= 0:
            raise ConfigurationError(f"--days must be positive, got {days}")
        e = now - timedelta(minutes=16)
        s = e - timedelta(days=days)
    if s >= e:
        raise ConfigurationError(
            f"Empty window: start {s.isoformat()} is not before end {e.isoformat()}"
        )
    return s, e


def filter_regular_trading_hours(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Keep only bars inside the 09:30-16:00 ET regular session.

    Parity, not tidiness: src/live_trading_loop.py only ticks when
    AlpacaMarketData.is_open() is true, and that reads Alpaca's clock,
    which is regular hours. Extended-hours bars are bars the live
    strategy structurally cannot act on, so scoring a strategy on them
    books trades that could never happen.

    Converts to exchange-local time rather than filtering a UTC window,
    so US daylight saving is handled by the tz database instead of by
    an offset that is wrong half the year. No holiday calendar is
    needed -- Alpaca returns no bars on holidays at all, and early
    closes simply produce no bars after 13:00.
    """
    if df.empty:
        return df, 0
    local = df.tz_convert(EXCHANGE_TZ)
    # inclusive="left" keeps the 09:30 bar and drops the 16:00 one --
    # that last bar is the post-close print, not part of the session.
    kept = local.between_time(MARKET_OPEN_ET, MARKET_CLOSE_ET, inclusive="left")
    return kept.tz_convert("UTC"), len(df) - len(kept)


def to_backtest_frame(
    barset_df: pd.DataFrame, symbol: str, *, regular_hours_only: bool = True
) -> tuple[pd.DataFrame, int, int]:
    """Reshape Alpaca's BarSet frame into the backtest's CSV schema.

    Returns (frame, dropped_extended_hours, dropped_duplicates).

    Alpaca hands back a MultiIndex (symbol, timestamp) frame with
    columns [open, high, low, close, volume, trade_count, vwap]. Each
    step below guards a specific way that shape goes wrong.
    """
    # Empty FIRST. An empty BarSet's .df has ZERO columns, so any
    # column access or index operation below raises an opaque KeyError
    # instead of saying what actually happened.
    if barset_df is None or barset_df.empty:
        raise DataValidationError(
            f"Alpaca returned no bars for {symbol!r}. Alpaca answers an unknown symbol with an "
            "empty result and HTTP 200 rather than an error, so this means one of: the symbol "
            "does not exist, the requested window contains no trading days, or the account is "
            "not entitled to the requested feed."
        )

    df = barset_df
    if isinstance(df.index, pd.MultiIndex):
        # xs() rather than droplevel(): it fails loudly if the returned
        # symbol is not the one requested, where droplevel would
        # silently interleave rows if this ever became multi-symbol.
        df = df.xs(symbol, level="symbol")

    missing = [c for c in BACKTEST_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"Alpaca response for {symbol!r} is missing expected column(s): {missing}. "
            f"Got: {list(df.columns)}"
        )
    df = df[BACKTEST_COLUMNS].copy()

    # Volume arrives as float64; left alone it writes "12000000.0",
    # which diverges from the committed fixture's integer form.
    df["volume"] = df["volume"].astype("int64")

    df.index = pd.DatetimeIndex(df.index).tz_convert("UTC")
    df.index.name = "timestamp"
    df = df.sort_index(kind="stable")

    dup_mask = df.index.duplicated(keep="last")
    dropped_duplicates = int(dup_mask.sum())
    if dropped_duplicates:
        # Logged rather than silent: validate() rejects duplicates
        # outright, so swallowing them would turn a download into a
        # backtest-time failure with no trace of the cause.
        logger.warning(f"Dropped {dropped_duplicates} duplicate timestamp(s) from {symbol!r} bars.")
        df = df[~dup_mask]

    dropped_eh = 0
    if regular_hours_only:
        df, dropped_eh = filter_regular_trading_hours(df)

    if df.empty:
        raise DataValidationError(
            f"No bars left for {symbol!r} after filtering. {dropped_eh} bar(s) were outside "
            "regular trading hours -- pass --include-extended-hours to keep them."
        )

    # The contract check. Anything that would make OptimizationController
    # reject this frame must fail here, not mid-sweep.
    data_validation.validate(df)
    return df, dropped_eh, dropped_duplicates


def write_csv(df: pd.DataFrame, path: Path, *, force: bool = False) -> Path:
    """Write the backtest CSV, matching the committed fixture exactly.

    Timestamps go through Timestamp.isoformat() rather than to_csv's
    own rendering. to_csv writes "2024-01-02 14:30:00+00:00" with a
    SPACE, and date_format="%...%z" writes "+0000" -- neither matches
    tests/fixtures/regression_ohlcv.csv's "2024-01-02T14:30:00+00:00".
    Both parse fine on read, so this is cosmetic; it is also the only
    committed reference for what these files look like.

    Refuses to clobber without force, because data/ is git-ignored --
    an overwritten download is genuinely unrecoverable.
    """
    path = Path(path)
    if path.exists() and not force:
        raise ConfigurationError(
            f"{path} already exists. Pass --force to overwrite it (data/ is git-ignored, so "
            "the existing file cannot be recovered afterward)."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out.index = out.index.map(lambda ts: ts.isoformat())
    out.to_csv(path, index=True, index_label="timestamp")
    return path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def session_scope_tag(regular_hours_only: bool) -> str:
    """Filename component naming which session a dataset covers.

    "rth" is spelled out rather than left implicit so the two scopes
    sort together and neither is the silent default on disk.
    """
    return "rth" if regular_hours_only else "ext"


def default_output_path(spec: FetchSpec, data_dir: Path) -> Path:
    """Timestamped filename carrying the parameters that change meaning.

    feed and adjustment are in the name because a raw file and an
    adjusted file of the same symbol and window are different data, and
    confusing them silently corrupts a backtest.

    SESSION SCOPE is in the name for a stronger version of the same
    reason. Without it a regular-hours and an extended-hours download of
    the same symbol/window/feed/adjustment produce the IDENTICAL
    filename, so the second either aborts on write_csv's exists-check or,
    with --force, overwrites the first -- and data/ is git-ignored, so
    that loss is unrecoverable. The two files also differ in a way
    nothing downstream detects: bars_per_day is a hand-set strategy
    parameter (387 for this repo's regular-hours SIP data, ~757 with
    extended hours) and src/sizing_indicators.bars_from_days validates
    only that it is positive. Feeding an extended-hours file to a config
    pinning 387 silently halves every window this project tunes.
    """
    return Path(data_dir) / (
        f"{spec.symbol}_{spec.timeframe}_{spec.feed}_{spec.adjustment}"
        f"_{session_scope_tag(spec.regular_hours_only)}"
        f"_{spec.start.date().isoformat()}_{spec.end.date().isoformat()}.csv"
    )


def write_sidecar(csv_path: Path, spec: FetchSpec, report_fields: dict) -> Path:
    """Record provenance next to the CSV.

    This is what makes an accumulating data/ a HISTORY rather than a
    pile of files: a sweep result stays traceable to the exact input it
    ran against, including the checksum, after later refreshes.

    Contains no credentials -- not because anything would redact them,
    but because they are never put in.
    """
    meta_path = csv_path.with_suffix(".meta.json")
    try:
        from importlib.metadata import version

        sdk_version = version("alpaca-py")
    except Exception:  # pragma: no cover - metadata always present in practice
        sdk_version = "unknown"

    meta = {
        "symbol": spec.symbol,
        "timeframe": spec.timeframe,
        "feed": spec.feed,
        "adjustment": spec.adjustment,
        "regular_hours_only": spec.regular_hours_only,
        "requested_start": spec.start.isoformat(),
        "requested_end": spec.end.isoformat(),
        "fetched_at": datetime.now(UTC).isoformat(),
        "alpaca_py_version": sdk_version,
        **report_fields,
    }
    meta_path.write_text(json.dumps(meta, indent=2, default=str) + "\n")
    return meta_path


def update_latest_symlink(csv_path: Path, *, regular_hours_only: bool = True) -> Path | None:
    """Point <SYMBOL>_<TF>_latest.csv at the newest download.

    A RELATIVE symlink, so it still resolves inside the container when
    data/ is bind-mounted at /app/data -- an absolute host path would
    dangle there.

    Extended-hours downloads get their OWN link
    (<SYMBOL>_<TF>_ext_latest.csv) rather than sharing one. A single
    shared link would mean the last download of either scope silently
    redefines what every `--data data/TQQQ_1Min_latest.csv` invocation
    reads, and the two datasets need different bars_per_day -- see
    default_output_path for why that particular swap is invisible
    downstream. Defaults to the regular-hours name so existing callers
    keep the link they already reference.
    """
    parts = csv_path.name.split("_")
    suffix = "latest" if regular_hours_only else "ext_latest"
    link = csv_path.parent / f"{parts[0]}_{parts[1]}_{suffix}.csv"
    try:
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(csv_path.name)
        return link
    except OSError as e:  # pragma: no cover - filesystems without symlinks
        logger.warning(f"Could not update {link}: {e}")
        return None


class AlpacaHistoricalData:
    """Fetches historical bars from Alpaca."""

    def __init__(
        self,
        credentials=None,
        *,
        data_client: Any = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Build a downloader.

        data_client is injectable so the whole transform path can be
        tested without network, matching AlpacaMarketData. Credentials
        are used here and never retained on the instance.
        """
        self._retry_config = retry_config or RetryConfig()
        if data_client is not None:
            self._data_client = data_client
            return
        if credentials is None:
            raise ConfigurationError(
                "AlpacaHistoricalData requires either LiveCredentials or an injected data_client."
            )
        _, _, StockHistoricalDataClient, _, _, _ = _require_alpaca_data()
        self._data_client = StockHistoricalDataClient(
            api_key=credentials.api_key_id,
            secret_key=credentials.api_secret_key,
        )

    def fetch_bars(self, spec: FetchSpec) -> tuple[pd.DataFrame, int, int]:
        """Download and reshape bars for one spec.

        Retries via the shared policy with after_submission=False: this
        is a read, so no order is ever at stake and a transport failure
        classifies RETRYABLE rather than AMBIGUOUS. Passing True here
        would make every flaky connection demand reconciliation for a
        data fetch.
        """
        Adjustment, DataFeed, _, StockBarsRequest, _, _ = _require_alpaca_data()
        request = StockBarsRequest(
            symbol_or_symbols=spec.symbol,
            timeframe=parse_timeframe(spec.timeframe),
            start=spec.start,
            end=spec.end,
            feed=DataFeed(spec.feed),
            adjustment=Adjustment(spec.adjustment),
        )
        # No limit= is passed. alpaca-py paginates internally; a limit
        # truncates silently into a partial dataset indistinguishable
        # from a complete one.
        barset = retry_call(
            lambda: self._data_client.get_stock_bars(request),
            self._retry_config,
            after_submission=False,
        )
        return to_backtest_frame(barset.df, spec.symbol, regular_hours_only=spec.regular_hours_only)


def download(
    spec: FetchSpec,
    *,
    out_path: Path | None = None,
    market_data: AlpacaHistoricalData | None = None,
    credentials=None,
    data_dir: Path = Path("data"),
    force: bool = False,
    write_metadata: bool = True,
) -> DownloadReport:
    """Fetch, validate, and write one dataset. Returns what it produced."""
    client = market_data or AlpacaHistoricalData(credentials=credentials)
    df, dropped_eh, dropped_dupes = client.fetch_bars(spec)

    path = Path(out_path) if out_path else default_output_path(spec, data_dir)
    write_csv(df, path, force=force)
    digest = _sha256(path)

    trading_days = len({ts.tz_convert(EXCHANGE_TZ).date() for ts in df.index})
    report = DownloadReport(
        symbol=spec.symbol,
        timeframe=spec.timeframe,
        feed=spec.feed,
        adjustment=spec.adjustment,
        rows=len(df),
        first_timestamp=df.index[0],
        last_timestamp=df.index[-1],
        trading_days=trading_days,
        dropped_extended_hours=dropped_eh,
        dropped_duplicates=dropped_dupes,
        path=path,
        sha256=digest,
    )
    if write_metadata:
        write_sidecar(
            path,
            spec,
            {
                "rows": report.rows,
                "first_timestamp": report.first_timestamp,
                "last_timestamp": report.last_timestamp,
                "trading_days": report.trading_days,
                "dropped_extended_hours": dropped_eh,
                "dropped_duplicates": dropped_dupes,
                "sha256": digest,
            },
        )
    update_latest_symlink(path, regular_hours_only=spec.regular_hours_only)
    return report


def median_bar_interval_seconds(df: pd.DataFrame) -> float | None:
    """Median spacing between bars, for the download report.

    Surfaced because a timeframe mismatch is otherwise invisible: grid
    steps chosen against daily bars produce almost no trades on minute
    bars, and PerformanceAnalyzer is bar-agnostic, so nothing
    downstream flags it.
    """
    if len(df) < 2:
        return None
    return float(df.index.to_series().diff().dt.total_seconds().median())
