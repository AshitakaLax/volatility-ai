import math
from datetime import datetime

from src.market_context import MarketContext
from src.size_calculators import RsiMomentumSizing


def context(price: float, equity: float = 100000.0) -> MarketContext:
    return MarketContext(datetime(2024, 1, 1), price, price, price, price, equity, equity, equity, 0.0, 0, 0)


def test_rsi_momentum_waits_for_warmup():
    strategy = RsiMomentumSizing(rsi_period=3, base_percentage=0.10)
    for price in [100.0, 99.0, 98.0]:
        strategy.record_tick(context(price))
    assert strategy.calculate_trade_value(context(98.0)) == 0.0


def test_rsi_momentum_reduces_allocation_when_rsi_is_overbought():
    strategy = RsiMomentumSizing(rsi_period=3, base_percentage=0.10)
    for price in [100.0, 101.0, 102.0, 103.0, 104.0]:
        strategy.record_tick(context(price))
    value = strategy.calculate_trade_value(context(104.0))
    assert 0.0 < value < 10000.0


def test_rsi_momentum_is_deterministic_for_same_tick_sequence():
    prices = [100.0, 99.0, 101.0, 98.0, 100.0, 102.0]
    first = RsiMomentumSizing(rsi_period=3, base_percentage=0.10)
    second = RsiMomentumSizing(rsi_period=3, base_percentage=0.10)
    for price in prices:
        first.record_tick(context(price))
        second.record_tick(context(price))
    assert math.isclose(
        first.calculate_trade_value(context(prices[-1])),
        second.calculate_trade_value(context(prices[-1])),
        rel_tol=0.0,
        abs_tol=1e-12,
    )
