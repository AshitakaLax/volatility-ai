"""Tests for BellCurveProbabilitySizing and RsiMomentumSizing.

These implement the mathematics of a supplied design document. The
tests below pin its stated properties -- the Gaussian peaking at mu and
falling away symmetrically, RSI scaling into oversold, the inverse
term never exceeding 1.0 -- plus the window-length correction this
repo required.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest

from src.exceptions import ConfigurationError
from src.market_context import MarketContext
from src.size_calculators import BellCurveProbabilitySizing, RsiMomentumSizing

EQUITY = 100_000.0
CEILING = EQUITY * 0.05


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


def bell(**kw) -> BellCurveProbabilitySizing:
    params = dict(max_trade_pct=0.05, lookback_days=10.0, bars_per_day=10, mu=0.20, sigma=0.10)
    params.update(kw)
    return BellCurveProbabilitySizing(**params)


def rsi(**kw) -> RsiMomentumSizing:
    params = dict(max_trade_pct=0.05, period=14)
    params.update(kw)
    return RsiMomentumSizing(**params)


def feed(strategy, prices):
    for i, p in enumerate(prices):
        strategy.record_tick(ctx(p, i))


# --- the inverse baseline term (design doc Section 8) ---


def test_baseline_is_captured_once_and_never_moves():
    """Re-baselining as price falls would cancel the protection at
    exactly the moment it is supposed to apply."""
    s = bell(inverse_scale_kappa=2.0)
    feed(s, [100.0, 90.0, 80.0, 70.0])
    assert s._baseline == 100.0


def test_price_above_baseline_does_not_inflate_the_position():
    """max(0, drawdown) is asymmetric on purpose -- the term protects
    against declines and must never push size above the ceiling."""
    s = bell(inverse_scale_kappa=2.0)
    feed(s, [100.0, 150.0])
    assert s._inverse_multiplier(150.0) == 1.0


def test_the_inverse_term_matches_the_documented_exponential():
    s = bell(inverse_scale_kappa=2.0)
    feed(s, [100.0])
    # 20% below a $100 baseline: exp(-2 * 0.20) ~= 0.6703
    assert s._inverse_multiplier(80.0) == pytest.approx(math.exp(-0.4), rel=1e-9)


def test_kappa_zero_disables_the_inverse_term():
    s = bell(inverse_scale_kappa=0.0)
    feed(s, [100.0])
    assert s._inverse_multiplier(10.0) == 1.0


def test_an_explicit_baseline_overrides_capture():
    """Needed for reproducibility: a walk-forward fold would otherwise
    capture a different baseline per fold from the same strategy."""
    s = bell(inverse_scale_kappa=1.0, baseline_price=200.0)
    feed(s, [100.0, 90.0])
    assert s._baseline == 200.0


# --- the bell curve (design doc Section 10) ---


def test_the_multiplier_peaks_when_drawdown_equals_mu():
    s = bell(mu=0.25, sigma=0.10)
    feed(s, [100.0])  # rolling high = 100
    assert s._model_multiplier(ctx(75.0)) == pytest.approx(1.0)


def test_the_multiplier_is_symmetric_around_mu():
    s = bell(mu=0.25, sigma=0.10)
    feed(s, [100.0])
    # D = 0.15 and D = 0.35 are equidistant from mu
    assert s._model_multiplier(ctx(85.0)) == pytest.approx(s._model_multiplier(ctx(65.0)))


def test_an_extreme_drawdown_is_scaled_back_not_doubled_down_on():
    """The capital-preservation half of the model, and the reason a
    plain monotonic function would not do."""
    s = bell(mu=0.20, sigma=0.10)
    feed(s, [100.0])
    at_target = s._model_multiplier(ctx(80.0))
    far_beyond = s._model_multiplier(ctx(20.0))  # 80% down
    assert far_beyond < at_target
    assert far_beyond < 0.01


def test_a_shallow_pullback_is_not_yet_interesting():
    s = bell(mu=0.20, sigma=0.10)
    feed(s, [100.0])
    assert s._model_multiplier(ctx(99.0)) < 0.2


def test_the_rolling_high_advances_on_every_bar_not_only_triggers():
    """record_tick is called per bar; the rolling high is a property of
    the market, so making it depend on grid activity would make the
    window a function of the grid step."""
    s = bell()
    feed(s, [100.0, 130.0, 120.0])
    assert s._rolling_high.value == 130.0


def test_lookback_is_measured_in_days_so_it_survives_a_frequency_change():
    daily = bell(lookback_days=252.0, bars_per_day=1)
    minute = bell(lookback_days=252.0, bars_per_day=390)
    assert daily._rolling_high.window == 252
    assert minute._rolling_high.window == 98_280


def test_sigma_must_be_positive():
    with pytest.raises(ConfigurationError, match="sigma"):
        bell(sigma=0.0)


def test_mu_must_be_a_fraction():
    with pytest.raises(ConfigurationError, match="mu"):
        bell(mu=1.5)


# --- RSI momentum (design doc Sections 13-14) ---


def test_above_the_threshold_the_baseline_multiplier_applies():
    s = rsi(baseline_multiplier=0.10, period=5)
    feed(s, [100.0 + i for i in range(30)])  # strongly rising -> RSI high
    assert s._model_multiplier(ctx(130.0)) == pytest.approx(0.10)


def test_deeply_oversold_approaches_baseline_plus_full_aggression():
    s = rsi(period=5, baseline_multiplier=0.10, aggression_factor=0.90)
    feed(s, [100.0 - i for i in range(30)])  # strictly falling -> RSI ~ 0
    assert s._model_multiplier(ctx(70.0)) == pytest.approx(1.0, abs=1e-6)


def test_an_unseeded_rsi_uses_the_conservative_baseline():
    """Sizing as though NOT oversold under-allocates rather than
    betting on an indicator that cannot yet be computed."""
    s = rsi(period=14, baseline_multiplier=0.10)
    feed(s, [100.0, 101.0])
    assert s._rsi.value is None
    assert s._model_multiplier(ctx(101.0)) == pytest.approx(0.10)


def test_the_multiplier_never_exceeds_one():
    s = rsi(period=5, baseline_multiplier=0.9, aggression_factor=0.9)
    feed(s, [100.0 - i for i in range(30)])
    assert s._model_multiplier(ctx(70.0)) <= 1.0


def test_the_exponent_controls_how_early_aggression_ramps():
    """exponent > 1 is more conservative until deeply oversold;
    exponent < 1 is more aggressive earlier."""
    prices = [100.0 - i * 0.5 for i in range(20)] + [90.5, 91.0]
    conservative = rsi(period=5, exponent=3.0)
    aggressive = rsi(period=5, exponent=0.5)
    feed(conservative, prices)
    feed(aggressive, prices)
    assert conservative._rsi.value == pytest.approx(aggressive._rsi.value)
    if conservative._rsi.value < conservative.oversold_threshold:
        assert conservative._model_multiplier(ctx(91.0)) < aggressive._model_multiplier(ctx(91.0))


@pytest.mark.parametrize(
    "kw,match",
    [
        ({"oversold_threshold": 0.0}, "oversold_threshold"),
        ({"oversold_threshold": 100.0}, "oversold_threshold"),
        ({"baseline_multiplier": 1.5}, "baseline_multiplier"),
        ({"aggression_factor": -0.1}, "aggression_factor"),
        ({"exponent": 0.0}, "exponent"),
        ({"max_trade_pct": 0.0}, "max_trade_pct"),
    ],
)
def test_invalid_rsi_configuration_is_rejected(kw, match):
    with pytest.raises(ConfigurationError, match=match):
        rsi(**kw)


# --- composition, shared by both ---


@pytest.mark.parametrize("factory", [bell, rsi])
def test_no_combination_of_multipliers_can_exceed_the_ceiling(factory):
    s = factory(max_trade_pct=0.05, inverse_scale_kappa=2.0)
    feed(s, [100.0 - i * 0.3 for i in range(60)])
    for price in (100.0, 80.0, 50.0, 10.0):
        assert s.calculate_trade_value(ctx(price)) <= CEILING + 1e-9


@pytest.mark.parametrize("factory", [bell, rsi])
def test_non_positive_equity_or_price_allocates_nothing(factory):
    s = factory()
    feed(s, [100.0])
    assert s.calculate_trade_value(ctx(100.0, equity=0.0)) == 0.0
    assert s.calculate_trade_value(ctx(0.0)) == 0.0


@pytest.mark.parametrize("factory", [bell, rsi])
def test_public_attributes_are_configuration_only(factory):
    """Rolling state must not reach SimulationResult.params."""
    s = factory()
    feed(s, [100.0 + i for i in range(50)])
    for name, value in vars(s).items():
        if name.startswith("_"):
            continue
        assert isinstance(value, (int, float, str, bool, type(None))), (
            f"public attribute {name!r} is a {type(value).__name__}, not a config scalar"
        )
