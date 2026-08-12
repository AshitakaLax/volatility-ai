from datetime import datetime, timezone

import pytest

from src.market_context import MarketContext
from src.size_calculators import FixedPortfolioPercentage


def _context(**overrides) -> MarketContext:
    defaults = dict(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        open=50.0, high=50.0, low=50.0, close=50.0,
        cash=95_000.0, equity=100_000.0, peak_equity=100_000.0,
        drawdown=0.0, open_lot_count=0, bar_index=0,
    )
    defaults.update(overrides)
    return MarketContext(**defaults)


def test_calculate_trade_value_is_equity_times_allocation():
    strategy = FixedPortfolioPercentage(allocation_pct=0.05)
    assert strategy.calculate_trade_value(_context(equity=100_000.0)) == pytest.approx(5_000.0)


def test_calculate_trade_value_ignores_price_and_drawdown():
    strategy = FixedPortfolioPercentage(allocation_pct=0.10)
    a = strategy.calculate_trade_value(_context(equity=10_000.0, close=1.0))
    b = strategy.calculate_trade_value(_context(equity=10_000.0, close=999.0, drawdown=0.5))
    assert a == b == pytest.approx(1_000.0)


def test_record_tick_is_a_stateless_noop():
    strategy = FixedPortfolioPercentage(allocation_pct=0.05)
    before = strategy.calculate_trade_value(_context(equity=10_000.0))
    strategy.record_tick(_context(close=50.0))
    strategy.record_tick(_context(close=999.0))
    after = strategy.calculate_trade_value(_context(equity=10_000.0))
    assert before == after


def test_check_grid_trigger_matches_pre_task_4_1_inline_check():
    strategy = FixedPortfolioPercentage(allocation_pct=0.05)
    last_buy_price, step = 100.0, 0.01
    assert strategy._check_grid_trigger(_context(close=98.99), last_buy_price, step) is True  # 98.99 <= 99
    assert strategy._check_grid_trigger(_context(close=99.00), last_buy_price, step) is True  # boundary, inclusive
    assert strategy._check_grid_trigger(_context(close=99.01), last_buy_price, step) is False


@pytest.mark.parametrize("allocation_pct", [0.0, -0.01, 1.01, 2.0])
def test_rejects_out_of_range_allocation(allocation_pct):
    with pytest.raises(ValueError):
        FixedPortfolioPercentage(allocation_pct=allocation_pct)


@pytest.mark.parametrize("allocation_pct", [0.0001, 1.0])
def test_accepts_boundary_allocation(allocation_pct):
    # (0, 1] is inclusive of 1.0, exclusive of 0.0.
    strategy = FixedPortfolioPercentage(allocation_pct=allocation_pct)
    assert strategy.allocation_pct == allocation_pct
