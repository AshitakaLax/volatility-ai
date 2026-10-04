"""research/strategies/position_sizing.py -- catalog C-S2, C-G5, R5/S3 ladder."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.position_sizing import (
    DrawdownLadder,
    TurtlePyramid,
    kelly_growth_rate,
    kelly_leverage,
    kelly_portfolio,
    true_ranges,
    turtle_atr,
    turtle_unit_shares,
)

# ---------------------------------------------------------------- C-S2


def test_single_strategy_kelly_is_mean_over_variance():
    assert kelly_leverage(0.08, 0.04) == pytest.approx(2.0)


def test_independent_strategies_reduce_to_componentwise_kelly():
    m = np.array([0.08, 0.05])
    cov = np.diag([0.04, 0.0625])
    assert kelly_portfolio(m, cov) == pytest.approx(m / np.diag(cov))


def test_portfolio_kelly_solves_c_f_equals_m():
    m = np.array([0.06, 0.04, 0.02])
    cov = np.array([[0.04, 0.01, 0.0], [0.01, 0.03, 0.005], [0.0, 0.005, 0.02]])
    f = kelly_portfolio(m, cov, long_only=False)
    assert cov @ f == pytest.approx(m)


def test_growth_at_the_optimum_is_r_plus_half_the_squared_sharpe():
    m = np.array([0.06, 0.04])
    cov = np.array([[0.04, 0.01], [0.01, 0.03]])
    f = kelly_portfolio(m, cov, long_only=False)
    sharpe_sq = m @ np.linalg.solve(cov, m)
    assert kelly_growth_rate(0.02, f, cov) == pytest.approx(0.02 + sharpe_sq / 2)


def test_fractional_and_long_only_kelly():
    m = np.array([0.06, -0.03])
    cov = np.diag([0.04, 0.04])
    assert kelly_portfolio(m, cov, fraction=0.5) == pytest.approx([0.75, 0.0])
    assert kelly_portfolio(m, cov, long_only=False)[1] < 0


def test_kelly_rejects_bad_inputs():
    with pytest.raises(ConfigurationError):
        kelly_leverage(0.1, 0.0)
    with pytest.raises(ConfigurationError):
        kelly_portfolio([0.1], [[0.04]], fraction=1.5)


# ---------------------------------------------------------------- C-G5


def test_source_true_range_pairs_each_bar_with_the_next_close():
    h, lo, c = [10, 12, 11], [9, 10, 8], [9.5, 11.5, 13]
    assert true_ranges(h, lo, c, "source") == pytest.approx(
        [max(10 - 9, abs(11.5 - 10), abs(11.5 - 9)), max(12 - 10, abs(13 - 12), abs(13 - 10))]
    )
    assert true_ranges(h, lo, c, "wilder") == pytest.approx(
        [max(12 - 10, abs(12 - 9.5), abs(10 - 9.5)), max(11 - 8, abs(11 - 11.5), abs(8 - 11.5))]
    )


def test_turtle_atr_is_the_mean_of_the_last_fourteen_true_ranges():
    rng = np.random.default_rng(1)
    close = 100 + np.cumsum(rng.normal(0, 1, 40))
    high, low = close + rng.uniform(0, 1, 40), close - rng.uniform(0, 1, 40)
    expected = np.mean(true_ranges(high[-15:], low[-15:], close[-15:], "source"))
    assert turtle_atr(high, low, close) == pytest.approx(expected)
    assert len(true_ranges(high[-15:], low[-15:], close[-15:])) == 14


def test_unit_is_one_percent_of_equity_per_atr():
    assert turtle_unit_shares(100_000, 2.5) == 400
    assert turtle_unit_shares(100_000, 3.0) == 333  # int() truncates


def test_pyramid_enters_on_breakout_and_adds_every_half_atr_up_to_four_buys():
    p = TurtlePyramid()
    assert p.on_price(99.0, donchian_high=100.0, atr=2.0) is None
    assert p.on_price(101.0, 100.0, 2.0) == "enter"
    assert p.on_price(101.9, 100.0, 2.0) is None  # less than +0.5 ATR above the last buy
    assert p.on_price(102.1, 100.0, 2.0) == "add"
    assert p.on_price(103.2, 100.0, 2.0) == "add"
    assert p.on_price(104.3, 100.0, 2.0) == "add"
    assert p.buy_count == 4
    assert p.on_price(110.0, 100.0, 2.0) is None  # the source's limit
    p.reset()
    assert p.on_price(101.0, 100.0, 2.0) == "enter"


def test_turtle_inputs_are_validated():
    with pytest.raises(ConfigurationError):
        turtle_unit_shares(1000, 0.0)
    with pytest.raises(ConfigurationError):
        turtle_atr([1] * 10, [1] * 10, [1] * 10)
    with pytest.raises(ConfigurationError):
        true_ranges([1, 2], [1, 2], [1, 2], "textbook")


# ---------------------------------------------------------------- drawdown ladder


def test_ladder_steps_down_through_its_tiers():
    ladder = DrawdownLadder()
    assert [ladder.tier_multiplier(d) for d in (0.0, 0.05, 0.07, 0.10, 0.19, 0.20, 0.5)] == [
        1.0,
        0.75,
        0.75,
        0.5,
        0.5,
        0.0,
        0.0,
    ]


def test_halt_holds_until_drawdown_recovers_below_resume():
    ladder = DrawdownLadder(resume_below=0.08)
    assert ladder.observe(0.21) == 0.0
    assert ladder.observe(0.15) == 0.0  # still halted: not yet below 8%
    assert ladder.observe(0.07) == 0.75  # resumed, at the tier it is now in


def test_liquidation_is_a_request_past_its_threshold():
    ladder = DrawdownLadder(liquidate_at=0.25)
    assert not ladder.liquidation_requested(0.24)
    assert ladder.liquidation_requested(0.25)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"tiers": ()},
        {"tiers": ((0.05, 0.5), (0.10, 0.8))},  # multiplier rises: invalid
        {"tiers": ((1.2, 0.5),)},
        {"liquidate_at": 0.01},
        {"tiers": ((0.05, 0.5),), "resume_below": 0.02},  # no halt tier
    ],
)
def test_ladder_rejects_bad_configurations(kwargs):
    with pytest.raises(ConfigurationError):
        DrawdownLadder(**kwargs)
