"""Tests for AlpacaMarketData / LiveBar.

The headline property: latest_bar() must carry real volume through to
LiveBar, not the always-0.0 default a missing field silently produced
before. context.volume is a live sizing input
(volume_scale_exponent), and 0.0 there means "unknown" -- so a bug
here doesn't crash anything, it just makes a configured feature a
silent no-op forever, which is exactly what shipped undetected.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from src.alpaca_market_data import AlpacaMarketData, LiveBar
from src.exceptions import ConfigurationError, DataValidationError


def alpaca_bar(**kw):
    """A stand-in for alpaca-py's Bar model -- a plain attribute bag,
    matching how the real SDK object is consumed here (attribute
    access, not dict access)."""
    defaults = dict(
        timestamp=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=12345.0,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def data_client(bar_by_symbol: dict):
    return SimpleNamespace(get_stock_latest_bar=lambda request: bar_by_symbol)


def market_data(bar_by_symbol: dict, **kw) -> AlpacaMarketData:
    return AlpacaMarketData(data_client=data_client(bar_by_symbol), **kw)


# --- the volume fix ---


def test_latest_bar_carries_real_volume_through():
    md = market_data({"TQQQ": alpaca_bar(volume=987654.0)})
    bar = md.latest_bar("TQQQ")
    assert bar.volume == pytest.approx(987654.0)


def test_a_bar_with_no_volume_attribute_degrades_to_the_unknown_default():
    """Matches MarketContext.volume's own convention: 0.0 means
    unknown, not none traded. Must not raise if some future SDK
    response ever omits the field."""
    bar_without_volume = SimpleNamespace(
        timestamp=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    md = market_data({"TQQQ": bar_without_volume})
    bar = md.latest_bar("TQQQ")
    assert bar.volume == 0.0


def test_live_bar_defaults_volume_to_zero_when_not_specified():
    bar = LiveBar(timestamp=datetime(2026, 3, 2, tzinfo=UTC), open=1, high=1, low=1, close=1)
    assert bar.volume == 0.0


# --- pre-existing behavior, unaffected ---


def test_ohlc_and_timestamp_still_pass_through_correctly():
    md = market_data({"TQQQ": alpaca_bar(open=10.0, high=11.0, low=9.0, close=10.5)})
    bar = md.latest_bar("TQQQ")
    assert (bar.open, bar.high, bar.low, bar.close) == (10.0, 11.0, 9.0, 10.5)


def test_a_missing_bar_raises_rather_than_fabricating_one():
    md = market_data({})
    with pytest.raises(DataValidationError, match="No bar returned"):
        md.latest_bar("TQQQ")


def test_is_open_requires_a_trading_client():
    md = market_data({"TQQQ": alpaca_bar()})
    with pytest.raises(ConfigurationError, match="trading client"):
        md.is_open()


def test_is_open_reads_the_trading_clients_clock():
    trading_client = SimpleNamespace(get_clock=lambda: SimpleNamespace(is_open=True))
    md = market_data({}, trading_client=trading_client)
    assert md.is_open() is True


# --- the EXTENDED session ---------------------------------------------
#
# clock.is_open is the REGULAR session alone, and the Calendar model
# carries only date/open/close. Gating the loop on is_open() meant it
# never woke outside 09:30-16:00 ET, which made live.extended_hours
# inert: the broker could build a pre-market limit order perfectly well
# and nothing ever asked it to.


def _calendar_client(now, close_hour=16, close_minute=0, trading_day=True):
    """A trading client whose calendar reports one day."""
    from datetime import time as _time

    day = SimpleNamespace(date=now.date(), open=_time(9, 30), close=_time(close_hour, close_minute))
    return SimpleNamespace(
        get_clock=lambda: SimpleNamespace(is_open=False, timestamp=now),
        get_calendar=lambda _request: [day] if trading_day else [],
    )


def _at(hour, minute=0):
    from datetime import datetime

    from src.fomc_calendar import EASTERN_TZ

    return datetime(2026, 9, 3, hour, minute, tzinfo=EASTERN_TZ)


@pytest.mark.parametrize(
    "hour,minute,expected",
    [
        (3, 59, False),  # before pre-market
        (4, 0, True),  # pre-market opens
        (9, 0, True),  # pre-market
        (12, 0, True),  # regular session
        (17, 0, True),  # after-hours
        (20, 0, True),  # after-hours ends
        (20, 1, False),  # past it
    ],
)
def test_the_extended_window_runs_from_0400_to_2000(hour, minute, expected, monkeypatch):
    import src.alpaca_market_data as module

    now = _at(hour, minute)
    monkeypatch.setattr(module, "datetime", _FrozenDatetime(now))
    md = market_data({}, trading_client=_calendar_client(now))
    assert md.is_open_extended() is expected


def test_a_half_day_ends_after_hours_four_hours_after_the_early_close(monkeypatch):
    """close + 4h is correct for BOTH cases without a special case: a
    16:00 close gives 20:00, a 13:00 half-day close gives 17:00. That is
    exactly when after-hours ends on those days, and it falls out of
    anchoring to the calendar's own close rather than a hardcoded 20:00.
    """
    import src.alpaca_market_data as module

    now = _at(18, 0)
    monkeypatch.setattr(module, "datetime", _FrozenDatetime(now))
    md = market_data({}, trading_client=_calendar_client(now, close_hour=13))
    assert md.is_open_extended() is False, "18:00 is past a half day's 17:00 close"

    md_full = market_data({}, trading_client=_calendar_client(now, close_hour=16))
    assert md_full.is_open_extended() is True, "18:00 is inside a normal day's 20:00"


def test_a_non_trading_day_has_no_extended_session_either(monkeypatch):
    """Holidays stay authoritative because the window is derived from
    the calendar, not from a weekday rule."""
    import src.alpaca_market_data as module

    now = _at(12, 0)
    monkeypatch.setattr(module, "datetime", _FrozenDatetime(now))
    md = market_data({}, trading_client=_calendar_client(now, trading_day=False))
    assert md.is_open_extended() is False


def test_is_open_extended_requires_a_trading_client():
    md = market_data({})
    with pytest.raises(ConfigurationError, match="trading client"):
        md.is_open_extended()


class _FrozenDatetime:
    """Freezes datetime.now() while leaving the rest of the class intact."""

    def __init__(self, now):
        self._now = now

    def now(self, tz=None):
        return self._now

    def __getattr__(self, name):
        from datetime import datetime as _real

        return getattr(_real, name)
