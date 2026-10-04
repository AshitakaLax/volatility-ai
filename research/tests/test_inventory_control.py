"""research/strategies/inventory_control.py -- catalog C-G2, C-MM1, C-MM2,
C-MM3, C-S4."""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.inventory_control import (
    alpha_shifted_quotes,
    as_optimal_spread,
    as_quotes,
    as_reservation_price,
    fit_arrival_intensity,
    glft_coefficients,
    glft_quotes,
    inventory_capped_lot,
    inventory_decay_multiplier,
    inventory_skewed_level,
    skewed_depths,
)

# ---------------------------------------------------------------- C-G2


def test_skewed_depths_follow_the_tutorial_formula():
    bid, ask = skewed_depths(half_spread=10.0, normalized_position=3.0, skew=0.1)
    assert bid == pytest.approx(10.0 * (1 + 0.1 * 3))
    assert ask == pytest.approx(10.0 * (1 - 0.1 * 3))


def test_flat_inventory_quotes_symmetrically():
    assert skewed_depths(7.0, 0.0, 0.5) == (7.0, 7.0)


def test_no_open_lots_reproduces_the_champion_level():
    assert inventory_skewed_level(100.0, 0.01, open_lots=0, skew=0.2) == pytest.approx(99.0)


def test_each_open_lot_pushes_the_next_buy_lower():
    levels = [inventory_skewed_level(100.0, 0.01, n, skew=0.25) for n in range(6)]
    assert all(b < a for a, b in pairwise(levels))
    assert levels[4] == pytest.approx(100.0 * (1 - 0.01 * (1 + 0.25 * 4)))


def test_max_depth_keeps_a_deep_inventory_off_zero():
    assert inventory_skewed_level(100.0, 0.01, 10_000, skew=1.0, max_depth=0.2) == pytest.approx(
        80.0
    )


@pytest.mark.parametrize(
    "args",
    [(100.0, 0.0, 0, 0.1), (100.0, 1.0, 0, 0.1), (100.0, 0.01, -1, 0.1), (100.0, 0.01, 0, -0.1)],
)
def test_skewed_level_rejects_bad_inputs(args):
    with pytest.raises(ConfigurationError):
        inventory_skewed_level(*args)


# ---------------------------------------------------------------- C-MM1

PAPER = {"s": 100.0, "T": 1.0, "sigma": 2.0, "k": 1.5}


def test_reservation_price_formula():
    r = as_reservation_price(100.0, q=3, gamma=0.1, sigma=2.0, tau=0.5)
    assert r == pytest.approx(100.0 - 3 * 0.1 * 4.0 * 0.5)


def test_flat_inventory_reservation_is_the_mid_and_long_inventory_lowers_it():
    assert as_reservation_price(100.0, 0, 0.1, 2.0, 1.0) == 100.0
    assert as_reservation_price(100.0, 5, 0.1, 2.0, 1.0) < 100.0
    assert as_reservation_price(100.0, -5, 0.1, 2.0, 1.0) > 100.0


def test_spread_formula_and_its_terminal_value():
    tau = 0.3
    expected = 0.1 * 4.0 * tau + (2 / 0.1) * math.log(1 + 0.1 / 1.5)
    assert as_optimal_spread(0.1, 2.0, tau, 1.5) == pytest.approx(expected)
    # At T the inventory term vanishes and only the order-arrival term is left.
    assert as_optimal_spread(0.1, 2.0, 0.0, 1.5) == pytest.approx(20 * math.log(1 + 0.1 / 1.5))


@pytest.mark.parametrize("gamma, published", [(0.1, 1.49), (0.01, 1.35), (1.0, 3.02)])
def test_time_averaged_spread_matches_the_papers_tables(gamma, published):
    # Avellaneda & Stoikov (2008), Tables 1-3: 1000 simulations with s=100,
    # T=1, sigma=2, k=1.5; reported average spread for each gamma.
    taus = np.linspace(0.0, PAPER["T"], 2001)
    spreads = [as_optimal_spread(gamma, PAPER["sigma"], t, PAPER["k"]) for t in taus]
    assert round(float(np.trapezoid(spreads, taus) / PAPER["T"]), 2) == published


def test_quotes_are_symmetric_around_the_reservation_price():
    bid, ask = as_quotes(100.0, 2, 0.1, 2.0, 0.5, 1.5)
    r = as_reservation_price(100.0, 2, 0.1, 2.0, 0.5)
    assert (bid + ask) / 2 == pytest.approx(r)
    assert ask - bid == pytest.approx(as_optimal_spread(0.1, 2.0, 0.5, 1.5))


@pytest.mark.parametrize(
    "args",
    [(0.0, 2.0, 1.0, 1.5), (0.1, -1.0, 1.0, 1.5), (0.1, 2.0, -1.0, 1.5), (0.1, 2.0, 1.0, 0.0)],
)
def test_as_rejects_bad_parameters(args):
    with pytest.raises(ConfigurationError):
        as_optimal_spread(*args)


# ---------------------------------------------------------------- C-MM2


def test_glft_coefficients_transcribe_compute_coeff():
    xi, gamma, delta, A, k = 0.05, 0.05, 1.0, 1.2, 0.8
    c1, c2 = glft_coefficients(xi, gamma, delta, A, k)
    assert c1 == pytest.approx(1 / (xi * delta) * math.log(1 + xi * delta / k))
    assert c2 == pytest.approx(
        math.sqrt(gamma / (2 * A * delta * k) * (1 + xi * delta / k) ** (k / (xi * delta) + 1))
    )


def test_c1_tends_to_one_over_k_as_risk_aversion_vanishes():
    c1, _ = glft_coefficients(xi=1e-9, gamma=1e-9, delta=1.0, A=1.0, k=2.0)
    assert c1 == pytest.approx(0.5, rel=1e-6)


def test_glft_quotes_follow_the_tutorial_lines():
    c1, c2 = glft_coefficients(0.05, 0.05, 1.0, 1.2, 0.8)
    q = glft_quotes(
        mid=100.0, position=4.0, volatility=0.6, c1=c1, c2=c2, delta=1.0, adj1=1.5, adj2=0.5
    )
    half = (c1 + 1.0 / 2 * c2 * 0.6) * 1.5
    skew = c2 * 0.6 * 0.5
    assert q["half_spread"] == pytest.approx(half)
    assert q["skew"] == pytest.approx(skew)
    assert q["reservation"] == pytest.approx(100.0 - skew * 4.0)
    assert q["bid"] == pytest.approx(100.0 - skew * 4.0 - half)
    assert q["ask"] == pytest.approx(100.0 - skew * 4.0 + half)


def test_flat_position_quotes_around_the_mid():
    q = glft_quotes(50.0, 0.0, 0.3, 1.0, 0.5, 1.0)
    assert (q["bid"] + q["ask"]) / 2 == pytest.approx(50.0)


def test_arrival_intensity_fit_recovers_a_and_k_exactly():
    depths = np.arange(0, 20, dtype=float)
    rates = 3.5 * np.exp(-0.42 * depths)
    a_hat, k_hat = fit_arrival_intensity(depths, rates)
    assert a_hat == pytest.approx(3.5)
    assert k_hat == pytest.approx(0.42)


def test_arrival_intensity_fit_is_close_under_noise():
    rng = np.random.default_rng(0)
    depths = np.linspace(0, 10, 200)
    rates = 2.0 * np.exp(-0.3 * depths) * np.exp(rng.normal(0, 0.05, depths.size))
    a_hat, k_hat = fit_arrival_intensity(depths, rates)
    assert a_hat == pytest.approx(2.0, rel=0.05)
    assert k_hat == pytest.approx(0.3, rel=0.05)


def test_arrival_fit_rejects_zero_rates_and_flat_depths():
    with pytest.raises(ConfigurationError):
        fit_arrival_intensity([0, 1, 2], [1.0, 0.0, 0.5])
    with pytest.raises(ConfigurationError):
        fit_arrival_intensity([1, 1, 1], [1.0, 0.8, 0.5])


# ---------------------------------------------------------------- C-MM3


def test_alpha_shifted_reservation_follows_the_readme():
    q = alpha_shifted_quotes(
        mid=100.0, forecast=0.2, position=3.0, volatility=0.1, a=2.0, b=0.5, c=0.05, hs=1.5
    )
    risk = (0.05 + 0.1) * 3.0
    assert q["reservation"] == pytest.approx(100.0 + 2.0 * 0.2 - 0.5 * risk)
    assert q["half_spread"] == pytest.approx((0.05 + 0.1) * 1.5)
    assert q["bid"] == pytest.approx(q["reservation"] - q["half_spread"])


def test_negative_forecast_lowers_the_bid_instead_of_stopping():
    neutral = alpha_shifted_quotes(100.0, 0.0, 0.0, 0.1, 1.0, 0.0, 0.0, 1.0)
    bearish = alpha_shifted_quotes(100.0, -0.5, 0.0, 0.1, 1.0, 0.0, 0.0, 1.0)
    assert bearish["bid"] < neutral["bid"]
    assert bearish["half_spread"] == neutral["half_spread"]


# ---------------------------------------------------------------- C-S4


def test_decay_multiplier_is_geometric_in_open_lots():
    assert inventory_decay_multiplier(0, 0.9) == 1.0
    assert inventory_decay_multiplier(3, 0.9) == pytest.approx(0.729)
    assert inventory_decay_multiplier(10, 1.0) == 1.0  # decay 1 = off


def test_capped_lot_shrinks_then_stops_at_the_lot_cap():
    lots = [inventory_capped_lot(1000.0, n, 0.8, max_lots=5) for n in range(7)]
    assert lots[:5] == pytest.approx([1000.0 * 0.8**n for n in range(5)])
    assert lots[5] == 0.0 and lots[6] == 0.0


def test_exposure_cap_trims_and_then_blocks():
    # 50% cap on $100k: $48k open leaves room for only $2k of a $5k lot.
    assert inventory_capped_lot(
        5000.0, 0, 1.0, exposure=48_000, equity=100_000, max_exposure=0.5
    ) == pytest.approx(2000.0)
    assert (
        inventory_capped_lot(5000.0, 0, 1.0, exposure=60_000, equity=100_000, max_exposure=0.5)
        == 0.0
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"base_lot": -1.0, "open_lots": 0, "decay": 0.9},
        {"base_lot": 1.0, "open_lots": 0, "decay": 0.0},
        {"base_lot": 1.0, "open_lots": 0, "decay": 1.1},
        {"base_lot": 1.0, "open_lots": 0, "decay": 0.9, "max_lots": 0},
        {"base_lot": 1.0, "open_lots": 0, "decay": 0.9, "max_exposure": 0.5},  # no equity
        {"base_lot": 1.0, "open_lots": 0, "decay": 0.9, "max_exposure": 1.5, "equity": 10.0},
    ],
)
def test_capped_lot_rejects_bad_inputs(kwargs):
    with pytest.raises(ConfigurationError):
        inventory_capped_lot(**kwargs)
