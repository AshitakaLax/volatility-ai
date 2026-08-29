"""
HF Market Data (hfmarketdata.io) as a bar source, alongside Alpaca.

--------------------------------------------------------------------
WHY A SECOND PROVIDER

Alpaca is the right source for anything the live loop trades, because
backtest/live feed parity matters more than coverage (see
src/historical_data.py's module docstring). This provider exists for
one thing Alpaca's free tier cannot give this project: a usable
EXTENDED-HOURS history.

Alpaca does return extended-hours bars -- the shipped sidecar for
data/TQQQ_1Min_sip_all_*.csv records dropped_extended_hours: 987,959
against 1,035,332 kept -- so extended hours could be had by re-running
fetch-data with --include-extended-hours. This provider is here because
its session runs 04:00 to ~20:00 Eastern, which is where a post-close
earnings release actually lands, and because it serves per-symbol
minute bars for index constituents (AAPL, NVDA, ...) under the same
API, which is what makes a weighted event signal measurable rather
than assumed.

--------------------------------------------------------------------
TIMESTAMPS ARE NAIVE US/EASTERN. This is the one thing that will
silently corrupt a dataset if it is got wrong, so it was verified
against this repo's own Alpaca data rather than assumed:

    HF     2024-06-03 14:00:00   close 30.4057
    Alpaca 2024-06-03 18:00:00Z  close 30.40     <- 14:00 Eastern

    (the UTC reading, 14:00Z = 10:00 Eastern, shows close 31.12 --
     not the same bar, and not close)

So the wire format carries no offset and means Eastern wall-clock.
Localization uses ambiguous="raise"/nonexistent="raise" rather than a
silent default: the 04:00-20:00 session never overlaps the 01:00-03:00
DST transition window, so either condition firing means an assumption
here is wrong and should stop the download, not be guessed at.

--------------------------------------------------------------------
VOLUME RUNS ~4.3% BELOW ALPACA SIP, systematically. Measured across a
full regular session (2024-06-03, all 390 bars matched by timestamp):

    close  : max abs diff 0.0091, median 0.0039  (rounding -- Alpaca's
             CSV carries 2dp, this API 4dp)
    volume : median -4.29%, mean -4.40%

So prices agree and volume does not. The venue set behind the
consolidation evidently differs. This matters because volume is a live
sizing input here (volume_scale_exponent in
src/high_frequency_sizing.py): a volume exponent tuned on one
provider's tape should be re-fit, not carried across.

Bar COVERAGE is also better: this API returns all 390 regular-session
minutes for that date, where the Alpaca SIP dataset averages 387.2.
That difference is why bars_per_day has to be re-measured per provider
rather than reused -- see src/historical_data.default_output_path.

--------------------------------------------------------------------
PAGINATION. The API caps a response well below a full history, so a
range is walked forward in pages of `page_limit`, each page resuming
one bar after the last row of the previous one. A page that fails to
advance the cursor aborts rather than looping forever.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

import pandas as pd

from src.exceptions import ConfigurationError, DataValidationError
from src.historical_data import FetchSpec, to_backtest_frame

logger = logging.getLogger("Optimizer")

BASE_URL = "https://www.hfmarketdata.io"

# The wire format's implicit timezone -- see the module docstring.
SOURCE_TZ = "America/New_York"

# The API's own timeframe vocabulary, which is not this repo's. Mapping
# rather than lowercasing so an unsupported timeframe fails here with
# the valid options instead of reaching the API as an opaque empty
# result (this API answers an unknown timeframe with count: 0, not an
# error, which would otherwise look like "no data for that window").
_TIMEFRAMES = {
    "1Min": "1min",
    "5Min": "5min",
    "30Min": "30min",
    "1Hour": "1hour",
    "1Day": "1day",
}

# Observed server-side cap: a request for 2,000 rows returns 1,000.
DEFAULT_PAGE_LIMIT = 1000


def _api_timeframe(timeframe: str) -> str:
    try:
        return _TIMEFRAMES[timeframe]
    except KeyError:
        raise ConfigurationError(
            f"HF Market Data does not serve timeframe {timeframe!r}. "
            f"Valid values: {', '.join(sorted(_TIMEFRAMES))}"
        ) from None


class HFMarketData:
    """Fetches bars from hfmarketdata.io into the backtest CSV schema.

    Mirrors AlpacaHistoricalData's fetch_bars contract exactly --
    (frame, dropped_extended_hours, dropped_duplicates) -- so
    historical_data.download() can drive either one without knowing
    which it holds.

    State ownership: holds connection settings only. It owns no frame,
    no cache, and no credentials (the API is unauthenticated), so there
    is nothing here that can drift from the server.
    """

    def __init__(
        self,
        *,
        asset: str = "etf",
        base_url: str = BASE_URL,
        page_limit: int = DEFAULT_PAGE_LIMIT,
        timeout: float = 60.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 5.0,
        opener=None,
        sleep=None,
    ) -> None:
        """Configure the source.

        asset is part of the URL path ("etf", "stock", "index", ...),
        not a query parameter, and the API answers a wrong-but-valid
        asset with an empty result rather than a 404 -- so it is stated
        explicitly instead of guessed from the symbol.

        opener is injectable so tests exercise the pagination and
        timezone logic against a double rather than the network.

        max_retries/retry_backoff_seconds exist because a plain read
        TIMEOUT does not raise urllib.error.URLError -- verified
        directly: TimeoutError is not a URLError subclass, so before
        this was added, a slow or overloaded server made _get raise an
        unhandled TimeoutError instead of the DataValidationError every
        other failure mode here produces. Retried with linear backoff
        because a provider-side slowdown (observed directly: this
        provider went unresponsive on every endpoint, including ones
        confirmed working minutes earlier, while unrelated hosts stayed
        reachable throughout) is exactly the kind of transient
        condition a retry is for, not a hard failure to surface
        immediately.
        """
        if page_limit <= 0:
            raise ConfigurationError(f"page_limit must be positive, got {page_limit}")
        if max_retries < 0:
            raise ConfigurationError(f"max_retries must be >= 0, got {max_retries}")
        self.asset = asset
        self.base_url = base_url.rstrip("/")
        self.page_limit = int(page_limit)
        self.timeout = timeout
        self.max_retries = int(max_retries)
        self.retry_backoff_seconds = retry_backoff_seconds
        self._opener = opener or urllib.request.urlopen
        self._sleep = sleep or time.sleep

    def _get(self, path: str, params: dict) -> dict:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        for attempt in range(self.max_retries + 1):
            try:
                with self._opener(url, timeout=self.timeout) as response:
                    return json.load(response)
            except urllib.error.HTTPError as e:
                raise DataValidationError(
                    f"HF Market Data returned HTTP {e.code} for {path}. "
                    "Check the asset type and ticker."
                ) from e
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt >= self.max_retries:
                    reason = getattr(e, "reason", e)
                    raise DataValidationError(
                        f"HF Market Data unreachable after {attempt + 1} attempt(s) for "
                        f"{path}: {reason}"
                    ) from e
                logger.warning(
                    f"HF Market Data request failed ({e!r}), "
                    f"retrying ({attempt + 1}/{self.max_retries})..."
                )
                self._sleep(self.retry_backoff_seconds * (attempt + 1))
        raise AssertionError("unreachable")  # the loop always returns or raises above

    def _fetch_pages(self, symbol: str, spec: FetchSpec) -> list[dict]:
        """Walk the range forward, one page at a time.

        The API compares start/end against its own naive Eastern values,
        so the window is converted to Eastern and sent WITHOUT an offset.
        Sending a "Z" would be silently interpreted as Eastern anyway --
        verified -- which would shift every window by the UTC offset.
        """
        start_et = pd.Timestamp(spec.start).tz_convert(SOURCE_TZ).tz_localize(None)
        end_et = pd.Timestamp(spec.end).tz_convert(SOURCE_TZ).tz_localize(None)

        rows: list[dict] = []
        cursor = start_et
        prev_last = None
        while cursor <= end_et:
            payload = self._get(
                f"/v1/bars/{self.asset}/{symbol}",
                {
                    "timeframe": _api_timeframe(spec.timeframe),
                    "start": cursor.isoformat(),
                    "end": end_et.isoformat(),
                    "order": "asc",
                    "limit": self.page_limit,
                    "format": "json",
                },
            )
            page = payload.get("data") or []
            if not page:
                break
            rows.extend(page)

            last = pd.Timestamp(page[-1]["datetime"])
            # Compared against the PREVIOUS page's last bar, not against
            # the cursor: the cursor is set one bar past the previous
            # page, so a well-behaved next page legitimately BEGINS at
            # it and its single row can equal it. Only a page that fails
            # to advance beyond where the last one ended is a stall, and
            # without this check that loops forever.
            if prev_last is not None and last <= prev_last:
                raise DataValidationError(
                    f"HF Market Data pagination stalled at {last} for {symbol!r}."
                )
            prev_last = last
            if len(page) < self.page_limit:
                break
            cursor = last + timedelta(minutes=1)
            logger.info(f"HF Market Data: {len(rows):,} bars for {symbol} through {last}")
        return rows

    def fetch_bars(self, spec: FetchSpec) -> tuple[pd.DataFrame, int, int]:
        """Download one symbol's bars and reshape them for the backtest.

        Returns (frame, dropped_extended_hours, dropped_duplicates),
        matching AlpacaHistoricalData.fetch_bars. The reshape, the
        duplicate handling, the regular-hours filter and the contract
        validation are all to_backtest_frame's -- deliberately not
        reimplemented here, so a dataset from this provider cannot pass
        checks a dataset from Alpaca would fail.
        """
        rows = self._fetch_pages(spec.symbol, spec)
        if not rows:
            raise DataValidationError(
                f"HF Market Data returned no bars for {spec.symbol!r} "
                f"({spec.start.isoformat()} to {spec.end.isoformat()}, asset={self.asset!r}). "
                "An unknown ticker or wrong asset type answers with an empty result, not an error."
            )

        frame = pd.DataFrame(rows)
        missing = {"datetime", "open", "high", "low", "close", "volume"} - set(frame.columns)
        if missing:
            raise DataValidationError(
                f"HF Market Data response is missing expected fields: {sorted(missing)}"
            )

        # The one conversion this module exists to get right.
        naive = pd.DatetimeIndex(pd.to_datetime(frame["datetime"]))
        frame = frame.drop(columns=["datetime"])
        frame.index = naive.tz_localize(
            SOURCE_TZ, ambiguous="raise", nonexistent="raise"
        ).tz_convert("UTC")
        frame.index.name = "timestamp"

        return to_backtest_frame(
            frame, spec.symbol, regular_hours_only=spec.regular_hours_only
        )
