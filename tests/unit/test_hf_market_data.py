"""Tests for the HF Market Data bar provider.

The property that matters most here is the timezone conversion. This
API sends naive Eastern wall-clock with no offset, and the rest of the
project is UTC-aware end to end -- so a silent misreading would shift
every bar by 4-5 hours and still produce a file that loads, validates,
and backtests. Nothing downstream would catch it.
"""

from __future__ import annotations

import io
import json
from contextlib import contextmanager
from datetime import UTC, datetime

import pytest

from src.exceptions import ConfigurationError, DataValidationError
from src.hf_market_data import HFMarketData
from src.historical_data import FetchSpec


def bar(dt: str, close: float = 100.0, volume: float = 1000.0) -> dict:
    return {
        "ticker": "TQQQ",
        "datetime": dt,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": volume,
    }


def fake_opener(pages):
    """Serve a queue of responses, recording the URLs requested."""
    calls: list[str] = []
    queue = list(pages)

    @contextmanager
    def opener(url, timeout=None):
        calls.append(url)
        payload = queue.pop(0) if queue else {"count": 0, "data": []}
        yield io.BytesIO(json.dumps(payload).encode())

    opener.calls = calls
    return opener


def spec(**kw) -> FetchSpec:
    params = dict(
        symbol="TQQQ",
        start=datetime(2024, 6, 3, 0, 0, tzinfo=UTC),
        end=datetime(2024, 6, 4, 6, 0, tzinfo=UTC),
        timeframe="1Min",
        feed="hf",
        adjustment="splitdiv",
        regular_hours_only=False,
    )
    params.update(kw)
    return FetchSpec(**params)


# --- the timezone conversion ---


def test_naive_eastern_is_converted_to_utc():
    """14:00 Eastern on a summer date is 18:00Z, not 14:00Z."""
    opener = fake_opener([{"count": 1, "data": [bar("2024-06-03 14:00:00")]}])
    df, _, _ = HFMarketData(opener=opener).fetch_bars(spec())

    assert df.index[0] == datetime(2024, 6, 3, 18, 0, tzinfo=UTC)


def test_the_winter_offset_differs_from_the_summer_one():
    """EST is -5, EDT is -4. A fixed offset would get one of them wrong."""
    summer = fake_opener([{"count": 1, "data": [bar("2024-06-03 14:00:00")]}])
    winter = fake_opener([{"count": 1, "data": [bar("2024-01-03 14:00:00")]}])

    s = HFMarketData(opener=summer).fetch_bars(spec())[0]
    w = HFMarketData(opener=winter).fetch_bars(
        spec(start=datetime(2024, 1, 3, tzinfo=UTC), end=datetime(2024, 1, 4, tzinfo=UTC))
    )[0]

    assert s.index[0].hour == 18  # EDT, -4
    assert w.index[0].hour == 19  # EST, -5


def test_the_window_is_sent_as_eastern_wall_clock():
    """The API compares start/end against its own naive values, so a
    UTC-shaped window would silently request the wrong hours."""
    opener = fake_opener([{"count": 1, "data": [bar("2024-06-03 04:00:00")]}])
    HFMarketData(opener=opener).fetch_bars(
        spec(start=datetime(2024, 6, 3, 8, 0, tzinfo=UTC))
    )
    # 08:00Z is 04:00 Eastern -- that is what must go on the wire.
    assert "start=2024-06-03T04%3A00%3A00" in opener.calls[0]
    assert "Z" not in opener.calls[0].split("start=")[1].split("&")[0]


# --- pagination ---


def test_pages_are_walked_until_a_short_page_ends_the_range():
    page1 = {"count": 2, "data": [bar("2024-06-03 09:30:00"), bar("2024-06-03 09:31:00")]}
    page2 = {"count": 1, "data": [bar("2024-06-03 09:32:00")]}
    opener = fake_opener([page1, page2])

    df, _, _ = HFMarketData(opener=opener, page_limit=2).fetch_bars(spec())

    assert len(df) == 3
    assert len(opener.calls) == 2
    # The second page resumes one minute after the first page's last bar.
    assert "start=2024-06-03T09%3A32%3A00" in opener.calls[1]


def test_a_full_page_that_does_not_advance_the_cursor_aborts():
    """Without this the loop re-requests the same page forever."""
    stuck = {"count": 1, "data": [bar("2024-06-03 09:30:00")]}
    opener = fake_opener([stuck, stuck, stuck])

    with pytest.raises(DataValidationError, match="pagination stalled"):
        HFMarketData(opener=opener, page_limit=1).fetch_bars(spec())


def test_a_single_short_page_makes_exactly_one_request():
    opener = fake_opener([{"count": 1, "data": [bar("2024-06-03 09:30:00")]}])
    HFMarketData(opener=opener, page_limit=1000).fetch_bars(spec())
    assert len(opener.calls) == 1


# --- error surfaces ---


def test_an_empty_result_is_an_error_not_an_empty_frame():
    """An unknown ticker or wrong asset type answers 200 with count 0."""
    opener = fake_opener([{"count": 0, "data": []}])
    with pytest.raises(DataValidationError, match="no bars"):
        HFMarketData(opener=opener).fetch_bars(spec())


def test_missing_response_fields_are_named():
    opener = fake_opener([{"count": 1, "data": [{"datetime": "2024-06-03 09:30:00"}]}])
    with pytest.raises(DataValidationError, match="missing expected fields"):
        HFMarketData(opener=opener).fetch_bars(spec())


def test_an_unsupported_timeframe_fails_before_the_request():
    opener = fake_opener([])
    with pytest.raises(ConfigurationError, match="does not serve timeframe"):
        HFMarketData(opener=opener).fetch_bars(spec(timeframe="1Week"))
    assert opener.calls == []


def test_a_non_positive_page_limit_is_rejected():
    with pytest.raises(ConfigurationError, match="page_limit"):
        HFMarketData(page_limit=0)


# --- the shared reshape ---


def test_regular_hours_filtering_uses_the_shared_implementation():
    """Extended-hours rows must be dropped by the same code path Alpaca
    downloads go through, not a second copy."""
    rows = [
        bar("2024-06-03 04:00:00"),  # pre-market
        bar("2024-06-03 09:30:00"),  # session open
        bar("2024-06-03 15:59:00"),  # last session minute
        bar("2024-06-03 19:59:00"),  # post-market
    ]
    opener = fake_opener([{"count": len(rows), "data": rows}])

    df, dropped, _ = HFMarketData(opener=opener).fetch_bars(
        spec(regular_hours_only=True)
    )

    assert dropped == 2
    eastern = df.index.tz_convert("America/New_York")
    assert [t.strftime("%H:%M") for t in eastern] == ["09:30", "15:59"]


# --- uniform-grid resampling ---


def uniform_frame(times, closes=None, volumes=None):
    """A one-session frame in UTC, from Eastern wall-clock times."""
    import pandas as pd

    idx = pd.DatetimeIndex(
        [pd.Timestamp(f"2024-06-03 {t}", tz="America/New_York") for t in times]
    ).tz_convert("UTC")
    n = len(times)
    closes = closes or [100.0] * n
    volumes = volumes or [1000.0] * n
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": volumes,
        },
        index=idx,
    )


def test_every_session_gets_the_same_bar_count():
    from src.historical_data import resample_to_uniform_minutes

    df = uniform_frame(["09:30", "09:33", "16:05"])
    out, synth = resample_to_uniform_minutes(df)

    assert len(out) == 960  # 04:00-20:00
    assert synth == 957
    eastern = out.index.tz_convert("America/New_York")
    assert eastern[0].strftime("%H:%M") == "04:00"
    assert eastern[-1].strftime("%H:%M") == "19:59"


def test_synthesized_bars_are_flat_and_zero_volume():
    """They must claim 'nothing traded, price stood', never a move."""
    from src.historical_data import resample_to_uniform_minutes

    df = uniform_frame(["09:30", "09:33"], closes=[100.0, 105.0])
    out, _ = resample_to_uniform_minutes(df)
    eastern = out.tz_convert("America/New_York")

    gap = eastern.loc["2024-06-03 09:31":"2024-06-03 09:32"]
    assert (gap["volume"] == 0).all()
    # Carried forward from 09:30, not interpolated toward 105.
    assert (gap["close"] == 100.0).all()
    assert (gap["open"] == gap["high"]).all()
    assert (gap["high"] == gap["low"]).all()


def test_a_flat_synthetic_bar_cannot_manufacture_an_intrabar_fill():
    """high == low means it reaches no level it was not already at."""
    from src.historical_data import resample_to_uniform_minutes

    df = uniform_frame(["09:30", "09:35"], closes=[100.0, 100.0])
    out, _ = resample_to_uniform_minutes(df)
    synthetic = out[out["volume"] == 0]

    assert len(synthetic) > 0
    assert (synthetic["high"] == synthetic["low"]).all()


def test_real_bars_are_left_untouched():
    from src.historical_data import resample_to_uniform_minutes

    df = uniform_frame(["09:30", "09:31"], closes=[100.0, 101.0], volumes=[5.0, 7.0])
    out, _ = resample_to_uniform_minutes(df)
    eastern = out.tz_convert("America/New_York")

    assert eastern.loc["2024-06-03 09:30", "close"] == 100.0
    assert eastern.loc["2024-06-03 09:30", "volume"] == 5.0
    assert eastern.loc["2024-06-03 09:31", "close"] == 101.0
    assert eastern.loc["2024-06-03 09:31", "volume"] == 7.0


def test_absent_sessions_are_never_invented():
    """Only minutes inside a session that already traded are filled --
    a weekend or holiday must not appear."""
    from src.historical_data import resample_to_uniform_minutes

    df = uniform_frame(["09:30"])
    out, _ = resample_to_uniform_minutes(df)
    dates = {t.date() for t in out.index.tz_convert("America/New_York")}

    assert len(dates) == 1


def test_off_grid_prints_outside_the_window_are_dropped():
    """A 03:59 print would otherwise survive as an off-grid row and
    break the exact bar count."""
    from src.historical_data import resample_to_uniform_minutes

    df = uniform_frame(["03:59", "09:30"])
    out, _ = resample_to_uniform_minutes(df)

    assert len(out) == 960
    eastern = out.index.tz_convert("America/New_York")
    assert eastern[0].strftime("%H:%M") == "04:00"


def test_an_empty_frame_is_returned_unchanged():
    import pandas as pd

    from src.historical_data import resample_to_uniform_minutes

    empty = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    empty.index = pd.DatetimeIndex([], tz="UTC")
    out, synth = resample_to_uniform_minutes(empty)

    assert out.empty and synth == 0


# --- retry on transient failures ---


def flaky_opener(exceptions_then_page):
    """Raises each exception in order, then serves the final page."""
    import io as _io

    calls = []
    queue = list(exceptions_then_page)

    @contextmanager
    def opener(url, timeout=None):
        calls.append(url)
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        yield _io.BytesIO(json.dumps(item).encode())

    opener.calls = calls
    return opener


def test_a_timeout_is_retried_not_left_unhandled():
    """TimeoutError is NOT a urllib.error.URLError subclass -- verified
    directly -- so before this was handled explicitly, a slow server
    raised an unhandled TimeoutError instead of DataValidationError."""
    opener = flaky_opener([TimeoutError("timed out"), {"count": 1, "data": [bar("2024-06-03 09:30:00")]}])
    sleeps = []
    df, _, _ = HFMarketData(opener=opener, max_retries=3, sleep=sleeps.append).fetch_bars(spec())
    assert len(df) == 1
    assert len(opener.calls) == 2
    assert len(sleeps) == 1  # one retry, one backoff sleep


def test_retries_are_exhausted_and_reported_as_a_data_validation_error():
    opener = flaky_opener([TimeoutError("t1"), TimeoutError("t2"), TimeoutError("t3")])
    with pytest.raises(DataValidationError, match="unreachable after 3 attempt"):
        HFMarketData(opener=opener, max_retries=2, sleep=lambda _: None).fetch_bars(spec())


def test_backoff_increases_with_each_attempt():
    opener = flaky_opener(
        [TimeoutError("t1"), TimeoutError("t2"), {"count": 1, "data": [bar("2024-06-03 09:30:00")]}]
    )
    sleeps = []
    HFMarketData(
        opener=opener, max_retries=3, retry_backoff_seconds=2.0, sleep=sleeps.append
    ).fetch_bars(spec())
    assert sleeps == [2.0, 4.0]


def test_zero_retries_means_the_first_failure_raises_immediately():
    opener = flaky_opener([TimeoutError("t1")])
    with pytest.raises(DataValidationError, match="unreachable after 1 attempt"):
        HFMarketData(opener=opener, max_retries=0, sleep=lambda _: None).fetch_bars(spec())


def test_a_negative_max_retries_is_rejected():
    with pytest.raises(ConfigurationError, match="max_retries"):
        HFMarketData(max_retries=-1)


def test_an_http_error_is_not_retried():
    """HTTPError means the server answered (e.g. a bad request) --
    retrying an unchanging request is pointless, unlike a timeout."""
    import urllib.error

    opener = flaky_opener(
        [urllib.error.HTTPError("url", 400, "bad request", {}, None), {"count": 1, "data": []}]
    )
    with pytest.raises(DataValidationError, match="HTTP 400"):
        HFMarketData(opener=opener, max_retries=3, sleep=lambda _: None).fetch_bars(spec())
    assert len(opener.calls) == 1


def test_a_connection_reset_is_retried_too():
    """The exact failure that slipped through before this fix: a
    DIFFERENT OSError subclass than TimeoutError, not previously caught
    at all, killed an instrument-screen run with zero retries."""
    opener = flaky_opener(
        [ConnectionResetError("connection reset"), {"count": 1, "data": [bar("2024-06-03 09:30:00")]}]
    )
    df, _, _ = HFMarketData(opener=opener, max_retries=3, sleep=lambda _: None).fetch_bars(spec())
    assert len(df) == 1


def test_http_error_is_still_not_retried_even_though_it_is_an_oserror_subclass():
    """The safety property the broad OSError catch depends on:
    HTTPError is itself an OSError subclass (verified), so this only
    stays correct because Python tries except clauses in order and the
    HTTPError clause is listed first."""
    import urllib.error

    opener = flaky_opener(
        [urllib.error.HTTPError("url", 500, "server error", {}, None), {"count": 1, "data": []}]
    )
    with pytest.raises(DataValidationError, match="HTTP 500"):
        HFMarketData(opener=opener, max_retries=3, sleep=lambda _: None).fetch_bars(spec())
    assert len(opener.calls) == 1
