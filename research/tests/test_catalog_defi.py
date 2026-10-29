"""research/catalog/defi.py -- AMM arbitrage and concentrated liquidity."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.defi import (
    cpmm_out,
    lp_backtest,
    lvr_rate,
    optimal_arbitrage,
    pool_price,
    simulate_arbitrage,
    v3_amounts,
    v3_liquidity,
    v3_value,
)


def test_constant_product_swap_and_optimal_arbitrage():
    out = cpmm_out(10.0, 1000.0, 1000.0, 0.0)
    assert out == pytest.approx(1000 * 10 / 1010)
    arb = optimal_arbitrage(1000.0, 1000.0, 1.2, fee=0.003, cex_fee=0.0)
    assert arb["side"] == "buy_pool" and arb["execute"]
    x, y = 1000.0 - arb["amount_out"], 1000.0 + arb["amount_in"]
    assert pool_price(x, y) == pytest.approx(1.2 * 0.997, rel=1e-3)
    for scale in (0.9, 1.1):  # the closed form is the most profitable size
        dy = arb["amount_in"] * scale
        dx = cpmm_out(dy, 1000.0, 1000.0, 0.003)
        assert dx * 1.2 - dy <= arb["profit"] + 1e-9
    rich = optimal_arbitrage(1000.0, 1000.0, 0.8, cex_fee=0.0)
    assert rich["side"] == "sell_pool" and rich["profit"] > 0
    assert not optimal_arbitrage(1000.0, 1000.0, 1.001)["execute"]
    assert not optimal_arbitrage(1000.0, 1000.0, 1.2, gas=1e6)["execute"]


def test_arbitrage_keeps_the_pool_in_the_fee_band_and_lvr():
    rng = np.random.default_rng(0)
    cex = np.exp(np.cumsum(0.01 * rng.normal(size=300)))
    out = simulate_arbitrage(cex, 1000.0, 1000.0, fee=0.003, cex_fee=0.0)
    gap = np.abs(out["pool_price"] / cex - 1)
    assert gap.max() < 0.0035 and out["profit"] > 0
    assert lvr_rate(0.8, 1e6) == pytest.approx(0.08 * 1e6)


def test_concentrated_liquidity_amounts_and_backtest():
    liq = v3_liquidity(1000.0, 100.0, 90.0, 110.0)
    assert v3_value(liq, 100.0, 90.0, 110.0) == pytest.approx(1000.0)
    x, y = v3_amounts(liq, 80.0, 90.0, 110.0)
    assert y == 0 and x > 0  # below the range: all in X
    x, y = v3_amounts(liq, 120.0, 90.0, 110.0)
    assert x == 0 and y > 0
    with pytest.raises(ConfigurationError):
        v3_amounts(1.0, 1.0, 2.0, 1.0)
    flat = 100 + np.sin(np.arange(200) * 0.3)
    quiet = lp_backtest(flat, np.full(200, 1e5), width=0.05)
    assert quiet["fees"] > 0 and quiet["lp_value"] > quiet["hold_value"]
    trend = np.linspace(100, 160, 200)
    moving = lp_backtest(trend, np.full(200, 1e3), width=0.05)
    assert moving["impermanent_loss"] > 0 and moving["rebalances"] > 0
