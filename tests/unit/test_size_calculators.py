import pytest

from src.size_calculators import FixedPortfolioPercentage


def test_calculate_trade_value_is_equity_times_allocation():
    strategy = FixedPortfolioPercentage(allocation_pct=0.05)
    assert strategy.calculate_trade_value(total_equity=100_000.0, current_price=50.0) == pytest.approx(5_000.0)


def test_calculate_trade_value_ignores_price_and_drawdown():
    strategy = FixedPortfolioPercentage(allocation_pct=0.10)
    a = strategy.calculate_trade_value(total_equity=10_000.0, current_price=1.0)
    b = strategy.calculate_trade_value(total_equity=10_000.0, current_price=999.0, current_dd=0.5)
    assert a == b == pytest.approx(1_000.0)


def test_record_tick_is_a_stateless_noop():
    strategy = FixedPortfolioPercentage(allocation_pct=0.05)
    before = strategy.calculate_trade_value(10_000.0, 50.0)
    strategy.record_tick(50.0)
    strategy.record_tick(999.0)
    after = strategy.calculate_trade_value(10_000.0, 50.0)
    assert before == after


@pytest.mark.parametrize("allocation_pct", [0.0, -0.01, 1.01, 2.0])
def test_rejects_out_of_range_allocation(allocation_pct):
    with pytest.raises(ValueError):
        FixedPortfolioPercentage(allocation_pct=allocation_pct)


@pytest.mark.parametrize("allocation_pct", [0.0001, 1.0])
def test_accepts_boundary_allocation(allocation_pct):
    # (0, 1] is inclusive of 1.0, exclusive of 0.0.
    strategy = FixedPortfolioPercentage(allocation_pct=allocation_pct)
    assert strategy.allocation_pct == allocation_pct
