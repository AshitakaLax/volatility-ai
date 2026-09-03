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
