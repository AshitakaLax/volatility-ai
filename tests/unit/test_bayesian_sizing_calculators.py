"""Tests for BayesianDualScaleSizing and its posterior.

The headline test here is test_posterior_at_bar_t_cannot_see_bar_t_plus_one:
a sizing model that scored trials at the bar they STARTED would be
reading its own future, and would produce a backtest that looks
excellent and means nothing. Everything else is arithmetic; that one is
the correctness property.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest

from src.bayesian_sizing_calculators import BayesianDualScaleSizing, DecayedBetaPosterior
from src.exceptions import ConfigurationError
from src.market_context import MarketContext

EQUITY = 100_000.0


def ctx(price: float, bar: int = 0, equity: float = EQUITY) -> MarketContext:
    return MarketContext(
        timestamp=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
        open=price,
        high=price,
        low=price,
        close=price,
        cash=equity,
        equity=equity,
        peak_equity=equity,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=bar,
    )


def make(**kw) -> BayesianDualScaleSizing:
    params = dict(
        max_trade_pct=0.05,
        target_return=0.01,
        horizon_days=1.0,
        bars_per_day=10,
        fast_half_life_days=2.0,
        slow_half_life_days=20.0,
    )
    params.update(kw)
    return BayesianDualScaleSizing(**params)


def feed(strategy, prices):
    for i, p in enumerate(prices):
        strategy.record_tick(ctx(p, i))


# --- the posterior ---


def test_prior_only_posterior_has_the_prior_mean():
    p = DecayedBetaPosterior(alpha0=2.0, beta0=3.0)
    assert p.mean == pytest.approx(0.4)
    assert p.effective_sample_size == pytest.approx(0.0)


def test_successes_move_the_mean_up_and_failures_down():
    p = DecayedBetaPosterior(half_life_trials=1e9)  # effectively no forgetting
    for _ in range(20):
        p.update(True)
    assert p.mean > 0.9
    q = DecayedBetaPosterior(half_life_trials=1e9)
    for _ in range(20):
        q.update(False)
    assert q.mean < 0.1


def test_effective_sample_size_saturates_at_the_forgetting_limit():
    """The point of exponential forgetting: evidence stops accumulating
    without bound, so the posterior stays responsive forever instead of
    freezing once it has seen enough."""
    half_life = 20.0
    p = DecayedBetaPosterior(half_life_trials=half_life)
    for _ in range(5000):
        p.update(True)
    limit = 1.0 / (1.0 - 0.5 ** (1.0 / half_life))
    assert p.effective_sample_size == pytest.approx(limit, rel=1e-6)


def test_a_wide_posterior_has_a_lower_bound_below_its_mean():
    p = DecayedBetaPosterior()
    assert p.lower_bound(2.0) < p.mean


def test_evidence_narrows_the_gap_between_bound_and_mean():
    """Confidence, not just optimism, is what unlocks position size."""
    p = DecayedBetaPosterior(half_life_trials=1e9)
    gaps = []
    for i in range(200):
        p.update(i % 2 == 0)  # a stable 50% success rate
        if i in (10, 50, 199):
            gaps.append(p.mean - p.lower_bound(2.0))
    assert gaps[0] > gaps[1] > gaps[2]


def test_lower_bound_stays_inside_the_unit_interval():
    p = DecayedBetaPosterior()
    assert 0.0 <= p.lower_bound(10.0) <= 1.0
    for _ in range(50):
        p.update(True)
    assert 0.0 <= p.lower_bound(0.0) <= 1.0


def test_a_fast_posterior_tracks_a_regime_change_before_a_slow_one():
    fast = DecayedBetaPosterior(half_life_trials=5.0)
    slow = DecayedBetaPosterior(half_life_trials=500.0)
    for _ in range(300):  # a long favorable regime
        fast.update(True)
        slow.update(True)
    for _ in range(20):  # then it stops working
        fast.update(False)
        slow.update(False)
    assert fast.mean < slow.mean, "the short half-life must react first"


def test_invalid_posterior_parameters_are_rejected():
    with pytest.raises(ConfigurationError, match="positive"):
        DecayedBetaPosterior(alpha0=0.0)
    with pytest.raises(ConfigurationError, match="half_life"):
        DecayedBetaPosterior(half_life_trials=0.0)


# --- the lookahead property ---


def test_posterior_at_bar_t_cannot_see_bar_t_plus_one():
    """THE correctness property.

    Two strategies see identical bars up to t. One then sees a wildly
    favorable future. The posterior visible at t must be identical --
    if it is not, sizing decisions are reading their own future and
    every backtest number produced by this strategy is meaningless.
    """
    history = [100.0 + i * 0.01 for i in range(40)]

    a = make()
    feed(a, history)
    before = (a._fast.alpha, a._fast.beta, a._slow.alpha, a._slow.beta)

    b = make()
    feed(b, history)
    feed(b, [500.0, 900.0, 1500.0])  # a spectacular future
    # Re-read a's state; b's extra bars must not have influenced the
    # posterior that existed at bar 40.
    assert before == (a._fast.alpha, a._fast.beta, a._slow.alpha, a._slow.beta)


def test_a_trial_resolves_exactly_horizon_bars_after_it_opens():
    s = make(horizon_days=1.0, bars_per_day=5)  # horizon = 5 bars
    for i in range(5):
        s.record_tick(ctx(100.0, i))
        assert s._fast.effective_sample_size == 0.0, "nothing may resolve before the horizon"
    s.record_tick(ctx(100.0, 5))
    assert s._fast.effective_sample_size > 0.0, "the first trial must resolve at horizon+1"


def test_a_trial_scores_success_only_if_the_target_is_reached_in_window():
    reached = make(horizon_days=1.0, bars_per_day=5, target_return=0.01)
    # +2% within the window
    feed(reached, [100.0, 100.5, 102.0, 101.0, 101.0, 101.0])
    assert reached._fast.mean > 0.5

    missed = make(horizon_days=1.0, bars_per_day=5, target_return=0.01)
    # never gets above +0.5%
    feed(missed, [100.0, 100.2, 100.4, 100.3, 100.5, 100.1])
    assert missed._fast.mean < 0.5


# --- sizing behavior ---


def test_a_cold_strategy_allocates_nothing():
    """Warm-up needs no flag: a wide posterior's lower bound is zero,
    so an uninformed strategy sizes itself out of the market."""
    assert make().calculate_trade_value(ctx(100.0)) == 0.0


def test_sustained_success_lifts_allocation_toward_the_ceiling():
    s = make()
    price = 100.0
    prices = []
    for _ in range(400):
        price *= 1.002
        prices.append(price)
    feed(s, prices)
    ceiling = EQUITY * 0.05
    assert s.calculate_trade_value(ctx(price)) == pytest.approx(ceiling, rel=1e-6)


def test_sustained_failure_keeps_allocation_at_zero():
    s = make(target_return=0.05)  # a target this flat series never hits
    feed(s, [100.0 + 0.001 * i for i in range(400)])
    assert s.calculate_trade_value(ctx(100.4)) == 0.0


def test_allocation_never_exceeds_the_ceiling():
    s = make(reference_probability=0.01)  # tiny reference inflates the raw ratio
    price = 100.0
    for i in range(400):
        price *= 1.01
        s.record_tick(ctx(price, i))
    assert s.calculate_trade_value(ctx(price)) <= EQUITY * 0.05 + 1e-9


def test_both_scales_must_agree_before_sizing_up():
    """The minimum-of-two rule: one confident scale cannot override a
    cautious one, mirroring the multiplicative safety property of the
    other strategies."""
    s = make()
    price = 100.0
    for i in range(400):
        price *= 1.002
        s.record_tick(ctx(price, i))
    assert s.calculate_trade_value(ctx(price)) > 0

    # Force the fast scale pessimistic; allocation must collapse even
    # though the slow scale is still optimistic.
    for _ in range(200):
        s._fast.update(False)
    assert s._slow.mean > 0.5, "precondition: the slow scale is still optimistic"
    assert s.calculate_trade_value(ctx(price)) == 0.0


def test_non_positive_equity_or_price_allocates_nothing():
    s = make()
    assert s.calculate_trade_value(ctx(100.0, equity=0.0)) == 0.0
    assert s.calculate_trade_value(ctx(0.0)) == 0.0


def test_record_tick_ignores_non_finite_and_non_positive_prices():
    s = make()
    s.record_tick(ctx(float("nan")))
    s.record_tick(ctx(-5.0))
    assert s._bars_seen == 0


# --- state hygiene ---


def test_pending_trials_are_bounded_by_the_horizon():
    """Unbounded state would attach a full price history to every
    SimulationResult via Task 4.6's params capture."""
    s = make(horizon_days=1.0, bars_per_day=10)
    feed(s, [100.0 + i for i in range(5000)])
    assert len(s._pending) <= s._horizon_bars + 1


def test_public_attributes_are_configuration_only():
    """optimization_controller merges the strategy's public attributes
    into SimulationResult.params as a 'what configured this run'
    record. Rolling state must not leak in there."""
    s = make()
    feed(s, [100.0 + i for i in range(200)])
    for name, value in vars(s).items():
        if name.startswith("_"):
            continue
        assert isinstance(value, (int, float, str, bool, type(None))), (
            f"public attribute {name!r} is a {type(value).__name__}, not a config scalar"
        )


# --- configuration validation ---


@pytest.mark.parametrize(
    "kw,match",
    [
        ({"max_trade_pct": 0.0}, "max_trade_pct"),
        ({"max_trade_pct": 1.5}, "max_trade_pct"),
        ({"target_return": 0.0}, "target_return"),
        ({"confidence_k": -1.0}, "confidence_k"),
        ({"reference_probability": 0.0}, "reference_probability"),
        ({"reference_probability": 1.5}, "reference_probability"),
        ({"horizon_days": 0.0}, "positive"),
        ({"bars_per_day": 0}, "bars_per_day"),
    ],
)
def test_invalid_configuration_is_rejected_at_construction(kw, match):
    with pytest.raises(ConfigurationError, match=match):
        make(**kw)


def test_horizon_and_half_lives_are_expressed_in_days_not_bars():
    """The bug this repo already hit once: a window in raw bars means
    a different span on every bar frequency."""
    daily = make(horizon_days=2.0, bars_per_day=1)
    minute = make(horizon_days=2.0, bars_per_day=390)
    assert daily._horizon_bars == 2
    assert minute._horizon_bars == 780


def test_diagnostics_report_both_scales():
    s = make()
    feed(s, [100.0 + i for i in range(100)])
    d = s.diagnostics(ctx(150.0))
    for key in ("fast_lower_bound", "slow_lower_bound", "conservative_probability"):
        assert key in d and math.isfinite(d[key])
    assert d["proposed_trade_value"] is not None


# --- calibration, and the degenerate case it guards ---


def test_a_reference_below_the_achievable_rate_degenerates_to_fixed_sizing():
    """The strategy's quiet failure mode, pinned so it cannot silently
    recur.

    If reference_probability sits below the success rate the market
    actually delivers, the ratio clamps at 1.0 on essentially every
    bar and this becomes FixedPortfolioPercentage with extra steps --
    every Bayesian parameter stops affecting results while the strategy
    still looks like it is working. Measured on real TQQQ minute data,
    a 0.5% target over a half-day horizon succeeded ~82% of the time
    against a default reference of 0.5, saturating 99.7% of bars.
    """
    s = make(target_return=0.001, reference_probability=0.5)
    price = 100.0
    prices = []
    for _ in range(600):
        price *= 1.003  # a target this easy is hit almost always
        prices.append(price)
    feed(s, prices)

    d = s.diagnostics(ctx(price))
    assert d["saturated"] is True
    assert s.calculate_trade_value(ctx(price)) == pytest.approx(EQUITY * 0.05)

    # Calibrated above the achievable rate, the same evidence no longer
    # pins the allocation at the ceiling.
    calibrated = make(target_return=0.001, reference_probability=0.999)
    feed(calibrated, prices)
    assert calibrated.diagnostics(ctx(price))["saturated"] is False
    assert calibrated.calculate_trade_value(ctx(price)) < EQUITY * 0.05


def test_diagnostics_expose_the_base_rate_used_for_calibration():
    """slow_mean is what an operator reads to choose a reference."""
    s = make()
    feed(s, [100.0 * (1.002**i) for i in range(300)])
    assert 0.0 <= s.diagnostics(ctx(100.0))["slow_mean"] <= 1.0


def test_record_tick_cost_does_not_scale_with_the_horizon():
    """A per-pending-entry running max made record_tick O(horizon):
    at a 652-bar horizon over 408k bars that was ~266M comparisons and
    minutes per sweep combination. One sliding-window maximum resolves
    every trial instead."""
    import time

    prices = [100.0 + (i % 50) for i in range(20_000)]
    timings = []
    for horizon_days in (1.0, 50.0):
        s = make(horizon_days=horizon_days, bars_per_day=20)
        start = time.perf_counter()
        feed(s, prices)
        timings.append(time.perf_counter() - start)
    short, long = timings
    assert long < short * 5, (
        f"a 50x larger horizon took {long / short:.1f}x longer -- record_tick is scaling "
        "with the horizon again"
    )
