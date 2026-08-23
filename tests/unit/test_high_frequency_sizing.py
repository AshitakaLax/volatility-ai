"""Tests for HighFrequencyLocalReferenceSizing.

Pins the two properties the module docstring claims: the trigger
retriggers on a local pullback that the DEFAULT (last_buy_price-only)
trigger would miss, and sizing is invariant to equity/drawdown/open-lot
count rather than scaling with them the way every other strategy does.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.exceptions import ConfigurationError
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from src.market_context import MarketContext

INITIAL_CASH = 100_000.0


def ctx(
    price: float,
    bar: int = 0,
    equity: float = INITIAL_CASH,
    open_lots: int = 0,
    is_macro_event_day: bool = False,
    is_earnings_reaction_day: bool = False,
):
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
        open_lot_count=open_lots,
        bar_index=bar,
        is_macro_event_day=is_macro_event_day,
        is_earnings_reaction_day=is_earnings_reaction_day,
    )


def hf(**kw) -> HighFrequencyLocalReferenceSizing:
    params = dict(per_lot_pct=0.005, lookback_days=0.01, bars_per_day=390)
    params.update(kw)
    return HighFrequencyLocalReferenceSizing(**params)


def feed(strategy, prices, equity=INITIAL_CASH):
    for i, p in enumerate(prices):
        strategy.record_tick(ctx(p, i, equity=equity))


# --- the retrigger-on-chop trigger ---


def test_retriggers_on_a_local_pullback_after_price_recovered_above_last_buy():
    """The scenario the default (last_buy_price-only) trigger cannot
    handle: price dips (buy fires, last_buy_price updates), recovers
    back above the original reference, then dips again by `step` from
    the NEW local high rather than from the stale last_buy_price."""
    s = hf(lookback_days=0.01, bars_per_day=390)  # ~4-bar window
    step = 0.01
    last_buy_price = 99.0  # a fill already happened at 99
    feed(s, [99.0, 100.0, 101.0, 102.0])  # price recovers to a new local high of 102

    # A default (last_buy_price-only) trigger would need price <= 99 * 0.99 = 98.01.
    # This one should fire off the new local high instead: 102 * 0.99 = 100.98.
    assert s._check_grid_trigger(ctx(100.9), last_buy_price, step) is True
    assert s._check_grid_trigger(ctx(101.0), last_buy_price, step) is False


def test_default_trigger_semantics_are_unreachable_from_a_stale_last_buy_price():
    """Direct contrast: same inputs, the base class's last_buy_price-only
    FORMULA says no; this strategy's rolling-high reference says yes.

    The contrast is drawn at _grid_trigger_level, not _check_grid_trigger:
    the base _check_grid_trigger now delegates to whatever level the
    instance defines, so calling it unbound on an HF instance would
    (correctly) use HF's level and prove nothing. The base FORMULA is
    the thing this strategy is meant to differ from."""
    from src.size_calculators import SizingStrategy

    s = hf(lookback_days=0.01, bars_per_day=390)
    last_buy_price = 99.0
    feed(s, [99.0, 100.0, 101.0, 102.0])
    price = 100.9
    context = ctx(price)

    default_level = SizingStrategy._grid_trigger_level(s, context, last_buy_price, 0.01)
    hf_level = s._grid_trigger_level(context, last_buy_price, 0.01)

    assert default_level == pytest.approx(99.0 * 0.99)  # 98.01 -- price never gets there
    assert hf_level == pytest.approx(102.0 * 0.99)  # 100.98 -- measured off the local high
    assert price > default_level, "the default formula would not trigger here"
    assert price <= hf_level, "this strategy's reference does trigger here"
    assert s._check_grid_trigger(context, last_buy_price, 0.01) is True


def test_falls_back_to_last_buy_price_before_any_tick_is_recorded():
    s = hf()
    assert s._check_grid_trigger(ctx(98.0), 100.0, 0.01) is True
    assert s._check_grid_trigger(ctx(99.5), 100.0, 0.01) is False


def test_last_buy_price_is_not_undercut_by_a_decayed_rolling_high():
    """A short rolling window forgets an older high once enough bars
    have passed. last_buy_price still knows about that earlier real
    fill, and max() must use it -- otherwise a decayed window would
    silently make the strategy LESS responsive than intended, requiring
    price to fall further than the actual last fill would justify."""
    s = hf(lookback_days=0.01, bars_per_day=390)  # ~4-bar window
    feed(s, [99.0, 98.0, 97.0, 96.0, 95.0, 94.0, 93.0, 92.0, 91.0, 90.0])
    assert s._rolling_high.value == pytest.approx(93.0)  # window has forgotten prices before it

    last_buy_price = 100.0  # an earlier real fill, outside the rolling window's memory
    step = 0.01
    # Rolling-high-only threshold would be 93 * 0.99 = 92.07 -- 95 would NOT trigger.
    # max(last_buy_price, rolling_high) = 100, so the threshold is 99 -- 95 DOES trigger.
    assert s._check_grid_trigger(ctx(95.0), last_buy_price, step) is True


# --- fixed-capital sizing ---


def test_trade_value_is_invariant_to_current_equity():
    s = hf(per_lot_pct=0.01)
    feed(s, [100.0], equity=INITIAL_CASH)
    at_full_equity = s.calculate_trade_value(ctx(100.0, equity=INITIAL_CASH))
    at_drawdown = s.calculate_trade_value(ctx(100.0, equity=INITIAL_CASH * 0.5))
    at_gain = s.calculate_trade_value(ctx(100.0, equity=INITIAL_CASH * 2.0))
    assert at_full_equity == at_drawdown == at_gain == pytest.approx(INITIAL_CASH * 0.01)


def test_trade_value_is_invariant_to_open_lot_count():
    s = hf(per_lot_pct=0.01)
    feed(s, [100.0])
    assert s.calculate_trade_value(ctx(100.0, open_lots=0)) == s.calculate_trade_value(
        ctx(100.0, open_lots=50)
    )


def test_baseline_capital_is_captured_once_and_never_moves():
    s = hf(per_lot_pct=0.01)
    feed(s, [100.0], equity=INITIAL_CASH)
    feed(s, [100.0], equity=INITIAL_CASH * 3.0)  # simulate a much larger equity, later
    assert s._baseline_capital == INITIAL_CASH


def test_zero_trade_value_before_any_tick_is_recorded():
    s = hf(per_lot_pct=0.01)
    assert s.calculate_trade_value(ctx(100.0)) == 0.0


# --- FOMC event-day boost (Task 7.9 discovery gate re-run; see module docstring) ---


def test_default_multiplier_is_a_no_op_on_an_event_day():
    """A config that never sets event_day_boost_multiplier gets
    IDENTICAL behavior to before it existed, even on a flagged day."""
    s = hf(per_lot_pct=0.01)
    feed(s, [100.0])
    normal = s.calculate_trade_value(ctx(100.0, is_macro_event_day=False))
    event = s.calculate_trade_value(ctx(100.0, is_macro_event_day=True))
    assert normal == event == pytest.approx(INITIAL_CASH * 0.01)


def test_boost_multiplies_trade_value_only_on_an_event_day():
    s = hf(per_lot_pct=0.01, event_day_boost_multiplier=3.0)
    feed(s, [100.0])
    normal = s.calculate_trade_value(ctx(100.0, is_macro_event_day=False))
    event = s.calculate_trade_value(ctx(100.0, is_macro_event_day=True))
    assert normal == pytest.approx(INITIAL_CASH * 0.01)
    assert event == pytest.approx(INITIAL_CASH * 0.01 * 3.0)


def test_default_earnings_multiplier_is_a_no_op_on_an_earnings_day():
    """Same guarantee the FOMC boost gives: a config that never sets
    earnings_day_boost_multiplier behaves exactly as it did before the
    field existed, even on a flagged session."""
    s = hf(per_lot_pct=0.01)
    feed(s, [100.0])
    normal = s.calculate_trade_value(ctx(100.0, is_earnings_reaction_day=False))
    earnings = s.calculate_trade_value(ctx(100.0, is_earnings_reaction_day=True))
    assert normal == earnings == pytest.approx(INITIAL_CASH * 0.01)


def test_earnings_boost_applies_only_on_an_earnings_reaction_day():
    s = hf(per_lot_pct=0.01, earnings_day_boost_multiplier=2.0)
    feed(s, [100.0])
    normal = s.calculate_trade_value(ctx(100.0, is_earnings_reaction_day=False))
    earnings = s.calculate_trade_value(ctx(100.0, is_earnings_reaction_day=True))
    assert normal == pytest.approx(INITIAL_CASH * 0.01)
    assert earnings == pytest.approx(INITIAL_CASH * 0.01 * 2.0)


def test_the_two_event_boosts_are_independent():
    """An FOMC-only day must not pick up the earnings multiplier, and
    vice versa. If these were folded into one flag this would fail."""
    s = hf(per_lot_pct=0.01, event_day_boost_multiplier=3.0, earnings_day_boost_multiplier=2.0)
    feed(s, [100.0])
    fomc_only = s.calculate_trade_value(ctx(100.0, is_macro_event_day=True))
    earnings_only = s.calculate_trade_value(ctx(100.0, is_earnings_reaction_day=True))
    assert fomc_only == pytest.approx(INITIAL_CASH * 0.01 * 3.0)
    assert earnings_only == pytest.approx(INITIAL_CASH * 0.01 * 2.0)


@pytest.mark.parametrize(
    ("fomc_mult", "earnings_mult", "expected_mult"),
    [
        (3.0, 2.0, 3.0),  # FOMC larger
        (1.5, 2.5, 2.5),  # earnings larger
        (2.0, 2.0, 2.0),  # equal
    ],
)
def test_a_day_flagged_both_ways_takes_the_larger_boost_not_the_product(
    fomc_mult, earnings_mult, expected_mult
):
    """14 sessions in the shipped calendars are both an FOMC decision
    day and an earnings reaction day. Compounding them would size those
    at up to 6.25x across the swept range on no evidence -- see
    calculate_trade_value's docstring."""
    s = hf(
        per_lot_pct=0.01,
        event_day_boost_multiplier=fomc_mult,
        earnings_day_boost_multiplier=earnings_mult,
    )
    feed(s, [100.0])
    both = s.calculate_trade_value(
        ctx(100.0, is_macro_event_day=True, is_earnings_reaction_day=True)
    )
    assert both == pytest.approx(INITIAL_CASH * 0.01 * expected_mult)
    # And explicitly NOT the compounded value, which every case here is
    # strictly larger than since both multipliers exceed 1.0.
    compounded = INITIAL_CASH * 0.01 * fomc_mult * earnings_mult
    assert both < compounded


@pytest.mark.parametrize("multiplier", [0.0, 0.5, 0.99, -1.0])
def test_rejects_a_below_one_earnings_boost_multiplier(multiplier):
    """Same size-up-only rule as the FOMC multiplier: rejected at
    construction rather than silently ignored."""
    with pytest.raises(ConfigurationError, match="earnings_day_boost_multiplier"):
        hf(earnings_day_boost_multiplier=multiplier)


def test_boost_never_reduces_trade_value():
    """This strategy only ever sizes UP on an FOMC day -- a multiplier
    below 1.0 is rejected at construction (see below), not merely
    unused, so a config mistake can't silently de-risk instead."""
    s = hf(per_lot_pct=0.01, event_day_boost_multiplier=1.0)
    feed(s, [100.0])
    assert s.calculate_trade_value(ctx(100.0, is_macro_event_day=True)) == pytest.approx(
        s.calculate_trade_value(ctx(100.0, is_macro_event_day=False))
    )


@pytest.mark.parametrize("multiplier", [0.0, 0.5, 0.99, -1.0])
def test_rejects_a_below_one_boost_multiplier(multiplier):
    with pytest.raises(ConfigurationError, match="event_day_boost_multiplier"):
        hf(event_day_boost_multiplier=multiplier)


# --- configuration ---


@pytest.mark.parametrize("per_lot_pct", [0.0, -0.01, 1.01, 2.0])
def test_rejects_out_of_range_per_lot_pct(per_lot_pct):
    with pytest.raises(ConfigurationError, match="per_lot_pct"):
        hf(per_lot_pct=per_lot_pct)


@pytest.mark.parametrize("kw", [{"lookback_days": 0.0}, {"bars_per_day": 0}])
def test_rejects_invalid_window_configuration(kw):
    with pytest.raises(ConfigurationError):
        hf(**kw)


# --- continuous volatility scaling ---


def _vol_feed(strategy, prices):
    """Drive record_tick over a price path so the rolling vol windows fill."""
    for i, p in enumerate(prices):
        strategy.record_tick(ctx(p, i))


def _calm_then_wild(n_calm=400, n_wild=60):
    """A long calm stretch followed by a volatile one, so fast_vol rises
    well above slow_vol without the price level drifting far."""
    prices = [100.0]
    for i in range(n_calm):
        prices.append(prices[-1] * (1.0004 if i % 2 else 0.9996))
    for i in range(n_wild):
        prices.append(prices[-1] * (1.010 if i % 2 else 0.990))
    return prices


def test_vol_scaling_defaults_to_an_exact_no_op():
    """exponent 0.0 must reproduce the unscaled strategy bit for bit,
    and must not even build the rolling windows."""
    s = hf(per_lot_pct=0.01)
    assert s._vol_enabled is False
    _vol_feed(s, _calm_then_wild())
    assert s.calculate_trade_value(ctx(100.0)) == pytest.approx(INITIAL_CASH * 0.01)


def test_a_negative_exponent_sizes_down_when_volatility_spikes():
    """Vol-targeting direction: turbulence should shrink the lot."""
    s = hf(per_lot_pct=0.01, vol_scale_exponent=-1.0, vol_fast_days=0.1, vol_slow_days=2.0)
    _vol_feed(s, _calm_then_wild())
    assert s.calculate_trade_value(ctx(100.0)) < INITIAL_CASH * 0.01


def test_a_positive_exponent_sizes_up_when_volatility_spikes():
    """Lean-in direction, matching what the event boosts do."""
    s = hf(per_lot_pct=0.01, vol_scale_exponent=1.0, vol_fast_days=0.1, vol_slow_days=2.0)
    _vol_feed(s, _calm_then_wild())
    assert s.calculate_trade_value(ctx(100.0)) > INITIAL_CASH * 0.01


def test_the_scale_is_clamped_at_both_ends():
    s = hf(
        per_lot_pct=0.01,
        vol_scale_exponent=8.0,  # would explode without the clamp
        vol_fast_days=0.1,
        vol_slow_days=2.0,
        vol_scale_max=1.25,
    )
    _vol_feed(s, _calm_then_wild())
    assert s.calculate_trade_value(ctx(100.0)) <= INITIAL_CASH * 0.01 * 1.25 + 1e-9


def test_scale_is_one_until_the_windows_have_warmed():
    """Before there is any return history the strategy must behave
    exactly as the unscaled one, not size off a half-formed estimate."""
    s = hf(per_lot_pct=0.01, vol_scale_exponent=-1.0)
    s.record_tick(ctx(100.0, 0))
    assert s.calculate_trade_value(ctx(100.0)) == pytest.approx(INITIAL_CASH * 0.01)


def test_vol_scaling_multiplies_with_the_event_boost():
    """Different axes -- a calm FOMC day and a turbulent one are not the
    same situation -- so these compound, unlike the two event boosts."""
    s = hf(
        per_lot_pct=0.01,
        event_day_boost_multiplier=2.0,
        vol_scale_exponent=1.0,
        vol_fast_days=0.1,
        vol_slow_days=2.0,
    )
    _vol_feed(s, _calm_then_wild())
    plain = s.calculate_trade_value(ctx(100.0))
    on_event = s.calculate_trade_value(ctx(100.0, is_macro_event_day=True))
    assert on_event == pytest.approx(plain * 2.0)


@pytest.mark.parametrize(("low", "high"), [(0.0, 2.0), (-1.0, 2.0), (1.5, 1.0)])
def test_rejects_an_invalid_vol_scale_range(low, high):
    with pytest.raises(ConfigurationError, match="vol_scale_min"):
        hf(vol_scale_min=low, vol_scale_max=high)
