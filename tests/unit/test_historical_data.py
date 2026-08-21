"""Tests for the historical-bar downloader.

Fakes are built from a REAL alpaca.data.models.BarSet rather than a
hand-rolled DataFrame. That is deliberate: the whole point of this
module is reshaping the SDK's actual MultiIndex/dtype output, so a
hand-built frame would test the transform against a shape the SDK
never produces and would keep passing after an SDK change breaks the
real path.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest
from alpaca.data.models import BarSet

from src.exceptions import ConfigurationError, DataValidationError
from src.historical_data import (
    BACKTEST_COLUMNS,
    AlpacaHistoricalData,
    FetchSpec,
    default_output_path,
    filter_regular_trading_hours,
    parse_timeframe,
    resolve_window,
    to_backtest_frame,
    write_csv,
)
from src.retry_policy import RetryConfig


def bar(ts: str, o=100.0, h=101.0, low=99.0, c=100.5, v=1000):
    """One raw bar in Alpaca's wire shape."""
    return {"t": ts, "o": o, "h": h, "l": low, "c": c, "v": v, "n": 10, "vw": c}


def barset(rows, symbol="TQQQ"):
    return BarSet(raw_data={symbol: rows})


class FakeDataClient:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def get_stock_bars(self, request):
        self.requests.append(request)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


# --- construction ---


def test_refuses_to_construct_without_credentials_or_a_client():
    with pytest.raises(ConfigurationError, match="LiveCredentials"):
        AlpacaHistoricalData()


def test_an_injected_client_needs_no_credentials():
    assert AlpacaHistoricalData(data_client=FakeDataClient(barset([]))) is not None


# --- timeframe / window parsing ---


@pytest.mark.parametrize("text", ["1Min", "5Min", "15Min", "30Min", "1Hour", "1Day"])
def test_known_timeframes_parse(text):
    assert parse_timeframe(text) is not None


def test_an_unknown_timeframe_fails_with_the_valid_options():
    with pytest.raises(ConfigurationError, match="1Day"):
        parse_timeframe("1Fortnight")


def test_days_window_ends_before_the_sip_delay_cutoff():
    """A window ending at 'now' is the most common way to trip Alpaca's
    15-minute recent-SIP restriction, so the default sits outside it."""
    now = datetime(2026, 3, 2, 15, 0, tzinfo=UTC)
    start, end = resolve_window(days=30, now=now)
    assert (now - end).total_seconds() >= 15 * 60
    assert (end - start).days == 30


def test_start_without_end_is_rejected():
    with pytest.raises(ConfigurationError, match="together"):
        resolve_window(start="2026-01-01", end=None)


def test_a_backwards_window_is_rejected():
    with pytest.raises(ConfigurationError, match="Empty window"):
        resolve_window(start="2026-02-01", end="2026-01-01")


def test_negative_days_is_rejected():
    with pytest.raises(ConfigurationError, match="positive"):
        resolve_window(days=-5)


# --- the transform ---


def test_multiindex_is_flattened_and_columns_pinned_to_the_fixture_shape():
    df, _, _ = to_backtest_frame(
        barset([bar("2026-03-02T15:00:00Z"), bar("2026-03-02T15:01:00Z")]).df,
        "TQQQ",
        regular_hours_only=False,
    )
    assert list(df.columns) == BACKTEST_COLUMNS, "trade_count/vwap must be dropped"
    assert df.index.name == "timestamp"
    assert not isinstance(df.index, pd.MultiIndex)


def test_volume_is_written_as_an_integer_not_a_float():
    """Alpaca returns volume as float64; uncast it writes '1000.0',
    diverging from the committed fixture."""
    df, _, _ = to_backtest_frame(
        barset([bar("2026-03-02T15:00:00Z", v=12_000_000)]).df, "TQQQ", regular_hours_only=False
    )
    assert df["volume"].dtype == "int64"


def test_unsorted_bars_are_sorted():
    df, _, _ = to_backtest_frame(
        barset([bar("2026-03-02T15:05:00Z"), bar("2026-03-02T15:01:00Z")]).df,
        "TQQQ",
        regular_hours_only=False,
    )
    assert df.index.is_monotonic_increasing


def test_duplicate_timestamps_are_dropped_and_counted():
    """data_validation rejects duplicates outright, so letting them
    through would turn a download into a backtest-time failure."""
    df, _, dupes = to_backtest_frame(
        barset(
            [
                bar("2026-03-02T15:00:00Z", c=100.0),
                bar("2026-03-02T15:00:00Z", c=101.0),
                bar("2026-03-02T15:01:00Z"),
            ]
        ).df,
        "TQQQ",
        regular_hours_only=False,
    )
    assert dupes == 1
    assert not df.index.duplicated().any()


def test_an_empty_result_names_the_plausible_causes():
    """Alpaca answers an unknown symbol with HTTP 200 and no bars, so
    this message is the only thing that explains what happened."""
    with pytest.raises(DataValidationError, match=r"does not exist|no trading days|entitled"):
        to_backtest_frame(barset([]).df, "NOPE")


def test_a_frame_missing_ohlc_is_rejected_here_not_mid_sweep():
    """data_validation.REQUIRED_COLUMNS is only {'close'}, so a short
    frame passes validation and then AttributeErrors inside
    _simulate_single's itertuples loop. Catch it at fetch time."""
    thin = pd.DataFrame(
        {"close": [100.0]},
        index=pd.DatetimeIndex(["2026-03-02T15:00:00Z"], name="timestamp"),
    )
    with pytest.raises(DataValidationError, match="missing expected column"):
        to_backtest_frame(thin, "TQQQ", regular_hours_only=False)


# --- regular trading hours, including DST ---


def _ny_index(times):
    return pd.DatetimeIndex(
        [pd.Timestamp(t, tz="America/New_York") for t in times], name="timestamp"
    ).tz_convert("UTC")


def _frame(times):
    idx = _ny_index(times)
    return pd.DataFrame(
        {c: [100.0] * len(idx) for c in BACKTEST_COLUMNS},
        index=idx,
    )


def test_regular_hours_keeps_0930_and_excludes_1600():
    kept, dropped = filter_regular_trading_hours(
        _frame(["2026-03-02 09:29", "2026-03-02 09:30", "2026-03-02 15:59", "2026-03-02 16:00"])
    )
    local = kept.tz_convert("America/New_York")
    assert [str(t.time()) for t in local.index] == ["09:30:00", "15:59:00"]
    assert dropped == 2


def test_extended_hours_bars_are_dropped():
    kept, dropped = filter_regular_trading_hours(
        _frame(["2026-03-02 04:00", "2026-03-02 08:00", "2026-03-02 12:00", "2026-03-02 18:00"])
    )
    assert len(kept) == 1 and dropped == 3


@pytest.mark.parametrize(
    "day,label",
    [("2026-01-15", "EST (UTC-5)"), ("2026-07-15", "EDT (UTC-4)")],
)
def test_session_boundaries_hold_on_both_sides_of_dst(day, label):
    """The test that catches a hardcoded UTC window.

    13:30-20:00Z is the right session only outside US daylight saving.
    Filtering in exchange-local time is correct year-round; anyone who
    'simplifies' this to fixed UTC hours breaks half the calendar.
    """
    kept, _ = filter_regular_trading_hours(
        _frame([f"{day} 09:29", f"{day} 09:30", f"{day} 15:59", f"{day} 16:00"])
    )
    local = kept.tz_convert("America/New_York")
    assert [str(t.time()) for t in local.index] == ["09:30:00", "15:59:00"], (
        f"session boundary wrong under {label}"
    )


def test_a_window_containing_only_extended_hours_fails_with_a_usable_hint():
    with pytest.raises(DataValidationError, match="include-extended-hours"):
        to_backtest_frame(barset([bar("2026-03-02T09:00:00Z")]).df, "TQQQ", regular_hours_only=True)


# --- writing ---


def test_written_timestamps_match_the_committed_fixture_format(tmp_path):
    """to_csv's own rendering uses a SPACE and date_format gives +0000;
    only isoformat() reproduces the fixture's exact form."""
    df, _, _ = to_backtest_frame(
        barset([bar("2024-01-02T14:30:00Z")]).df, "TQQQ", regular_hours_only=False
    )
    path = write_csv(df, tmp_path / "out.csv")
    lines = path.read_text().splitlines()
    assert lines[0] == "timestamp,open,high,low,close,volume"
    assert lines[1].startswith("2024-01-02T14:30:00+00:00,")


def test_refuses_to_clobber_an_existing_file_without_force(tmp_path):
    """data/ is git-ignored, so an overwritten download is gone."""
    df, _, _ = to_backtest_frame(
        barset([bar("2026-03-02T15:00:00Z")]).df, "TQQQ", regular_hours_only=False
    )
    path = tmp_path / "out.csv"
    write_csv(df, path)
    with pytest.raises(ConfigurationError, match="--force"):
        write_csv(df, path)
    assert write_csv(df, path, force=True) == path


def test_default_filename_records_feed_and_adjustment():
    """A raw file and an adjusted file of the same window are different
    data; the name must not let them be confused."""
    spec = FetchSpec(
        symbol="TQQQ",
        start=datetime(2024, 8, 20, tzinfo=UTC),
        end=datetime(2026, 8, 20, tzinfo=UTC),
        feed="iex",
        adjustment="raw",
    )
    name = default_output_path(spec, Path("data")).name
    assert "iex" in name and "raw" in name and "TQQQ" in name and "1Min" in name


# --- fetch wiring ---


def test_fetch_passes_symbol_timeframe_feed_and_adjustment_through():
    client = FakeDataClient(barset([bar("2026-03-02T15:00:00Z")]))
    spec = FetchSpec(
        symbol="TQQQ",
        start=datetime(2026, 3, 1, tzinfo=UTC),
        end=datetime(2026, 3, 2, tzinfo=UTC),
        feed="iex",
        adjustment="all",
        regular_hours_only=False,
    )
    AlpacaHistoricalData(data_client=client).fetch_bars(spec)

    req = client.requests[0]
    assert req.symbol_or_symbols == "TQQQ"
    assert req.feed.value == "iex"
    assert req.adjustment.value == "all"
    assert getattr(req, "limit", None) is None, (
        "limit must never be sent -- it truncates silently into a partial dataset"
    )


def test_a_transient_network_failure_is_retried():
    import requests

    class Flaky:
        def __init__(self):
            self.calls = 0

        def get_stock_bars(self, request):
            self.calls += 1
            if self.calls < 3:
                raise requests.exceptions.ConnectionError("boom")
            return barset([bar("2026-03-02T15:00:00Z")])

    client = Flaky()
    fetcher = AlpacaHistoricalData(
        # base_delay must be positive per RetryConfig's own validation;
        # 1ms keeps the backoff real but the test instant.
        data_client=client,
        retry_config=RetryConfig(max_attempts=5, base_delay=0.001, jitter=0.0),
    )
    spec = FetchSpec(
        symbol="TQQQ",
        start=datetime(2026, 3, 1, tzinfo=UTC),
        end=datetime(2026, 3, 2, tzinfo=UTC),
        regular_hours_only=False,
    )
    df, _, _ = fetcher.fetch_bars(spec)
    assert client.calls == 3 and len(df) == 1
