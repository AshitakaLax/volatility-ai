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
