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
    minute: int = 0,
    volume: float = 0.0,
    high: float | None = None,
    low: float | None = None,
    event_intensity: float = 0.0,
    minutes_to_event: float = -1.0,
):
    return MarketContext(
        timestamp=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
        open=price,
        high=price if high is None else high,
        low=price if low is None else low,
        close=price,
        cash=equity,
        equity=equity,
        peak_equity=equity,
        drawdown=0.0,
        open_lot_count=open_lots,
        bar_index=bar,
        is_macro_event_day=is_macro_event_day,
        is_earnings_reaction_day=is_earnings_reaction_day,
        time_of_day_flag=minute,
        volume=volume,
        event_intensity=event_intensity,
        minutes_to_event=minutes_to_event,
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


# --- time-of-day sizing ---


def test_time_of_day_defaults_to_an_exact_no_op():
    """exponent 0.0 must reproduce the unscaled strategy at every minute
    of the session, not merely on average."""
    s = hf(per_lot_pct=0.01)
    s.record_tick(ctx(100.0))
    for m in (0, 30, 240, 389, -1):
        assert s.calculate_trade_value(ctx(100.0, minute=m)) == pytest.approx(
            INITIAL_CASH * 0.01
        ), f"minute {m} was scaled despite an exponent of 0.0"


def test_a_negative_exponent_sizes_down_at_the_open_and_up_at_midday():
    """The open is the most volatile minute and midday the least, so a
    negative exponent -- the direction the vol-ratio scaler measured as
    correct -- must shrink the open lot and grow the midday one."""
    s = hf(per_lot_pct=0.01, time_of_day_exponent=-1.0)
    s.record_tick(ctx(100.0))
    at_open = s.calculate_trade_value(ctx(100.0, minute=0))
    at_midday = s.calculate_trade_value(ctx(100.0, minute=240))
    assert at_open < INITIAL_CASH * 0.01 < at_midday


def test_a_positive_exponent_reverses_that_ordering():
    s = hf(per_lot_pct=0.01, time_of_day_exponent=1.0)
    s.record_tick(ctx(100.0))
    assert s.calculate_trade_value(ctx(100.0, minute=0)) > s.calculate_trade_value(
        ctx(100.0, minute=240)
    )


def test_bars_outside_the_regular_session_are_left_unscaled():
    """time_of_day_flag is -1 outside 09:30-16:00. Scaling such a bar by
    a profile measured only on regular hours would apply a number from a
    different regime; live can legitimately see these bars."""
    s = hf(per_lot_pct=0.01, time_of_day_exponent=-1.0)
    s.record_tick(ctx(100.0))
    assert s.calculate_trade_value(ctx(100.0, minute=-1)) == pytest.approx(INITIAL_CASH * 0.01)


def test_time_of_day_and_vol_scaling_compose():
    """They measure different things -- one is the clock, the other is
    realized volatility -- so they multiply rather than one overriding
    the other."""
    common = dict(per_lot_pct=0.01, vol_fast_days=0.1, vol_slow_days=2.0)
    tod_only = hf(time_of_day_exponent=-1.0, **common)
    both = hf(time_of_day_exponent=-1.0, vol_scale_exponent=-1.0, **common)
    for s in (tod_only, both):
        _vol_feed(s, _calm_then_wild())
    assert both.calculate_trade_value(ctx(100.0, minute=0)) < tod_only.calculate_trade_value(
        ctx(100.0, minute=0)
    )


def test_the_time_of_day_multiplier_is_bounded_by_its_safety_rails():
    """An extreme exponent must not produce an absurd lot. The rails are
    fixed rather than swept because the profile is already bounded."""
    s = hf(per_lot_pct=0.01, time_of_day_exponent=-12.0)
    s.record_tick(ctx(100.0))
    smallest = min(s.calculate_trade_value(ctx(100.0, minute=m)) for m in range(390))
    largest = max(s.calculate_trade_value(ctx(100.0, minute=m)) for m in range(390))
    assert smallest >= INITIAL_CASH * 0.01 * 0.1 - 1e-9
    assert largest <= INITIAL_CASH * 0.01 * 3.0 + 1e-9


# --- vol_measure: stdev vs intrabar range ---


def _wide_bars(strategy, n=300, widen_from=250):
    """Closes follow a fixed repeating pattern while high/low widen late.
    Close-to-close volatility is therefore UNCHANGED throughout, and only
    the intrabar range moves -- which is exactly what separates the two
    measures."""
    for i in range(n):
        p = 100.0 + (i % 3)
        wide = i >= widen_from
        strategy.record_tick(
            ctx(p, i, high=p * (1.02 if wide else 1.0005), low=p * (0.98 if wide else 0.9995))
        )


def test_range_measure_reacts_to_widening_bars_that_stdev_cannot_see():
    """The two measures are genuinely different quantities, not two
    spellings of one. With closes held to a fixed pattern, close-to-close
    vol is flat while intrabar range triples."""
    common = dict(per_lot_pct=0.01, vol_scale_exponent=-1.0, vol_fast_days=0.05, vol_slow_days=0.5)
    by_stdev = hf(vol_measure="stdev", **common)
    by_range = hf(vol_measure="range", **common)
    _wide_bars(by_stdev)
    _wide_bars(by_range)
    probe = ctx(100.0, high=102.0, low=98.0)
    assert by_stdev.calculate_trade_value(probe) == pytest.approx(INITIAL_CASH * 0.01, rel=0.05)
    assert by_range.calculate_trade_value(probe) < INITIAL_CASH * 0.01 * 0.8


def test_vol_measure_defaults_to_stdev():
    """Defaulting to the measured-worse option is deliberate: every
    number in the module docstring was produced with it."""
    assert hf().vol_measure == "stdev"


@pytest.mark.parametrize("measure", ["", "STDEV", "variance", None])
def test_rejects_an_unknown_vol_measure(measure):
    with pytest.raises(ConfigurationError, match="vol_measure"):
        hf(vol_measure=measure)


# --- volume scaling ---


def test_volume_scaling_defaults_to_an_exact_no_op():
    s = hf(per_lot_pct=0.01)
    for i in range(50):
        s.record_tick(ctx(100.0, i, volume=1000.0 * (5 if i > 40 else 1)))
    assert s.calculate_trade_value(ctx(100.0, volume=5000.0)) == pytest.approx(INITIAL_CASH * 0.01)


def test_a_negative_volume_exponent_sizes_down_into_a_volume_surge():
    s = hf(
        per_lot_pct=0.01,
        volume_scale_exponent=-1.0,
        vol_fast_days=0.05,
        vol_slow_days=0.5,
    )
    for i in range(300):
        s.record_tick(ctx(100.0, i, volume=5000.0 if i > 250 else 1000.0))
    assert s.calculate_trade_value(ctx(100.0, volume=5000.0)) < INITIAL_CASH * 0.01


def test_unpopulated_volume_is_treated_as_unknown_not_as_zero():
    """MarketContext.volume defaults to 0.0. Feeding that in as a real
    observation would drag the slow mean toward nothing and blow the
    ratio up, so a strategy configured for volume scaling must simply
    stay neutral on a feed that does not supply it."""
    s = hf(per_lot_pct=0.01, volume_scale_exponent=-1.0)
    for i in range(300):
        s.record_tick(ctx(100.0, i))  # volume defaults to 0.0
    assert s.calculate_trade_value(ctx(100.0)) == pytest.approx(INITIAL_CASH * 0.01)


def test_volume_and_vol_scaling_compose():
    """Different inputs -- one is trade activity, the other price
    movement -- and they are only partly correlated, so they multiply."""
    common = dict(per_lot_pct=0.01, vol_fast_days=0.05, vol_slow_days=0.5)
    vol_only = hf(vol_scale_exponent=-1.0, **common)
    both = hf(vol_scale_exponent=-1.0, volume_scale_exponent=-1.0, **common)
    for s in (vol_only, both):
        for i in range(300):
            p = 100.0 + (i % 3) * (4 if i > 250 else 1)
            s.record_tick(ctx(p, i, volume=5000.0 if i > 250 else 1000.0))
    probe = ctx(100.0, volume=5000.0)
    assert both.calculate_trade_value(probe) < vol_only.calculate_trade_value(probe)


# --- synthetic-bar exclusion from vol windows ---


def test_a_flat_unchanged_bar_does_not_update_the_vol_windows():
    """The resample_to_uniform_minutes signature: high==low==price,
    unchanged from the previous real print."""
    s = hf(per_lot_pct=0.01, vol_scale_exponent=-1.0, vol_fast_days=0.1, vol_slow_days=2.0)
    real = _calm_then_wild()
    _vol_feed(s, real)
    before = s.calculate_trade_value(ctx(real[-1]))

    # 50 synthetic bars: flat, at the last real price.
    last = real[-1]
    for i in range(50):
        s.record_tick(ctx(last, len(real) + i, high=last, low=last))
    after = s.calculate_trade_value(ctx(real[-1]))

    assert after == pytest.approx(before)


def test_a_real_flat_bar_with_no_prior_price_still_counts():
    """The very first tick has no prev_price to compare against, so it
    must not be misread as synthetic and silently dropped."""
    s = hf(per_lot_pct=0.01, vol_scale_exponent=-1.0, vol_fast_days=0.1, vol_slow_days=2.0)
    s.record_tick(ctx(100.0, 0))
    assert s._prev_price == pytest.approx(100.0)


def test_vol_scaling_is_unaffected_by_context_volume_being_zero():
    """The live path's context.volume is ALWAYS 0.0 (LiveBar has no
    volume field) -- vol scaling must not be gated on it, or it would
    silently disable itself forever in live trading."""
    s = hf(per_lot_pct=0.01, vol_scale_exponent=-1.0, vol_fast_days=0.1, vol_slow_days=2.0)
    for i, p in enumerate(_calm_then_wild()):
        s.record_tick(ctx(p, i, volume=0.0))  # volume=0.0 is the ctx() default too
    assert s._fast_vol.value is not None
    assert s.calculate_trade_value(ctx(100.0)) < INITIAL_CASH * 0.01


# --- weighted event boost (event_intensity) ---


def test_weighted_event_boost_defaults_to_an_exact_no_op():
    s = hf(per_lot_pct=0.01)
    assert s.weighted_event_boost_multiplier == 1.0
    feed(s, [100.0])
    value = s.calculate_trade_value(
        ctx(100.0, event_intensity=8.5, minutes_to_event=3.0)
    )
    assert value == pytest.approx(INITIAL_CASH * 0.01)


def test_event_intensity_scales_the_boost_by_its_own_weight():
    """8.5 out of the 0-100 scale gets 8.5% of the configured boost."""
    s = hf(per_lot_pct=0.01, weighted_event_boost_multiplier=2.0)
    feed(s, [100.0])
    value = s.calculate_trade_value(ctx(100.0, event_intensity=8.5))
    expected_multiplier = 1.0 + (2.0 - 1.0) * (8.5 / 100.0)
    assert value == pytest.approx(INITIAL_CASH * 0.01 * expected_multiplier)


def test_full_scale_event_intensity_applies_the_full_boost():
    s = hf(per_lot_pct=0.01, weighted_event_boost_multiplier=2.5)
    feed(s, [100.0])
    value = s.calculate_trade_value(ctx(100.0, event_intensity=100.0))
    assert value == pytest.approx(INITIAL_CASH * 0.01 * 2.5)


def test_weighted_boost_combines_with_day_flags_by_max_not_multiply():
    """Same underlying claim at two granularities -- must not compound."""
    s = hf(
        per_lot_pct=0.01,
        earnings_day_boost_multiplier=1.5,
        weighted_event_boost_multiplier=3.0,
    )
    feed(s, [100.0])
    value = s.calculate_trade_value(
        ctx(100.0, is_earnings_reaction_day=True, event_intensity=8.5)
    )
    # weighted contributes 1 + 2*0.085 = 1.17, day flag contributes 1.5 --
    # max wins, not 1.5 * 1.17.
    assert value == pytest.approx(INITIAL_CASH * 0.01 * 1.5)


def test_rejects_a_weighted_boost_below_one():
    with pytest.raises(ConfigurationError, match="weighted_event_boost_multiplier"):
        hf(weighted_event_boost_multiplier=0.5)


# --- drawdown regime throttle ---


def test_dd_throttle_defaults_to_an_exact_no_op():
    """dd_throttle_start=None must reproduce the unscaled strategy bit
    for bit, at any drawdown level -- including one deep enough that an
    enabled throttle would floor it."""
    s = hf(per_lot_pct=0.01)
    assert s._dd_throttle_enabled is False
    feed(s, [100.0])
    for dd in (0.0, 0.3, 0.6, 0.9):
        assert s.calculate_trade_value(ctx(100.0, equity=INITIAL_CASH)) == pytest.approx(
            INITIAL_CASH * 0.01
        ), f"drawdown {dd} scaled trade value despite dd_throttle_start being unset"


def test_size_is_unaffected_below_the_start_threshold():
    s = hf(per_lot_pct=0.01, dd_throttle_start=0.30, dd_throttle_full=0.60, dd_throttle_floor=0.25)
    feed(s, [100.0])
    context = MarketContext(
        timestamp=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
        open=100.0, high=100.0, low=100.0, close=100.0,
        cash=INITIAL_CASH, equity=INITIAL_CASH, peak_equity=INITIAL_CASH,
        drawdown=0.30, open_lot_count=0, bar_index=1,
    )
    assert s.calculate_trade_value(context) == pytest.approx(INITIAL_CASH * 0.01)


def _dd_context(drawdown: float) -> MarketContext:
    return MarketContext(
        timestamp=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
        open=100.0, high=100.0, low=100.0, close=100.0,
        cash=INITIAL_CASH, equity=INITIAL_CASH, peak_equity=INITIAL_CASH,
        drawdown=drawdown, open_lot_count=0, bar_index=1,
    )


def test_size_reaches_the_floor_at_and_beyond_full_drawdown():
    s = hf(per_lot_pct=0.01, dd_throttle_start=0.30, dd_throttle_full=0.60, dd_throttle_floor=0.25)
    feed(s, [100.0])
    for dd in (0.60, 0.75, 0.99):
        assert s.calculate_trade_value(_dd_context(dd)) == pytest.approx(
            INITIAL_CASH * 0.01 * 0.25
        )


def test_size_ramps_linearly_between_start_and_full():
    s = hf(per_lot_pct=0.01, dd_throttle_start=0.30, dd_throttle_full=0.60, dd_throttle_floor=0.0)
    feed(s, [100.0])
    # Halfway between 0.30 and 0.60 (dd=0.45) should land halfway between
    # 1.0 and the floor (0.0) -- i.e. exactly half size.
    halfway = s.calculate_trade_value(_dd_context(0.45))
    assert halfway == pytest.approx(INITIAL_CASH * 0.01 * 0.5)


def test_size_is_monotonically_non_increasing_as_drawdown_deepens():
    s = hf(per_lot_pct=0.01, dd_throttle_start=0.20, dd_throttle_full=0.70, dd_throttle_floor=0.1)
    feed(s, [100.0])
    values = [s.calculate_trade_value(_dd_context(dd)) for dd in (0.0, 0.2, 0.3, 0.5, 0.7, 0.9)]
    assert values == sorted(values, reverse=True)
    assert values[-1] == pytest.approx(INITIAL_CASH * 0.01 * 0.1)


def test_dd_throttle_composes_with_vol_scale():
    """Different axes -- a calm bar deep in a drawdown and a turbulent
    one are not the same situation -- so these multiply."""
    s = hf(
        per_lot_pct=0.01,
        dd_throttle_start=0.20,
        dd_throttle_full=0.70,
        dd_throttle_floor=0.5,
        vol_scale_exponent=1.0,
        vol_fast_days=0.1,
        vol_slow_days=2.0,
    )
    _vol_feed(s, _calm_then_wild())
    calm_no_dd = s.calculate_trade_value(_dd_context(0.0))
    calm_deep_dd = s.calculate_trade_value(_dd_context(0.70))
    assert calm_deep_dd == pytest.approx(calm_no_dd * 0.5)


@pytest.mark.parametrize("start", [0.0, -0.1, 1.0, 1.5])
def test_rejects_an_out_of_range_start_threshold(start):
    with pytest.raises(ConfigurationError, match="dd_throttle_start"):
        hf(dd_throttle_start=start)


@pytest.mark.parametrize(("start", "full"), [(0.5, 0.5), (0.5, 0.3), (0.5, 1.5)])
def test_rejects_a_full_threshold_not_above_start_or_above_one(start, full):
    with pytest.raises(ConfigurationError, match="dd_throttle_full"):
        hf(dd_throttle_start=start, dd_throttle_full=full)


@pytest.mark.parametrize("floor", [-0.1, 1.1])
def test_rejects_an_out_of_range_floor(floor):
    with pytest.raises(ConfigurationError, match="dd_throttle_floor"):
        hf(dd_throttle_start=0.3, dd_throttle_floor=floor)


def test_weighted_event_boost_multiplies_with_vol_scale():
    """Different axis from vol, same convention as the day-level boosts."""
    s = hf(
        per_lot_pct=0.01,
        weighted_event_boost_multiplier=2.0,
        vol_scale_exponent=1.0,
        vol_fast_days=0.1,
        vol_slow_days=2.0,
    )
    _vol_feed(s, _calm_then_wild())
    plain = s.calculate_trade_value(ctx(100.0))
    on_event = s.calculate_trade_value(ctx(100.0, event_intensity=100.0))
    assert on_event == pytest.approx(plain * 2.0)


# --- implied-vol change scaling ---


def _iv_ctx(change: float):
    return MarketContext(
        timestamp=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
        open=100.0, high=100.0, low=100.0, close=100.0,
        cash=INITIAL_CASH, equity=INITIAL_CASH, peak_equity=INITIAL_CASH,
        drawdown=0.0, open_lot_count=0, bar_index=1,
        implied_vol_change=change,
    )


def test_implied_vol_scaling_defaults_to_an_exact_no_op():
    """A config that never sets the exponent, and a deployment with no
    implied-vol file, must both reproduce prior behavior bit for bit."""
    s = hf(per_lot_pct=0.01)
    feed(s, [100.0])
    for change in (-40.0, -5.0, 0.0, 5.0, 40.0):
        assert s.calculate_trade_value(_iv_ctx(change)) == pytest.approx(
            INITIAL_CASH * 0.01
        ), f"change {change} scaled despite an exponent of 0.0"


def test_a_negative_exponent_sizes_down_after_implied_vol_jumps():
    """Vol-targeting direction -- the one _vol_scale measured as correct
    for realized vol. Whether it is right here is for a sweep to say."""
    s = hf(per_lot_pct=0.01, implied_vol_exponent=-1.0)
    feed(s, [100.0])
    assert s.calculate_trade_value(_iv_ctx(20.0)) < INITIAL_CASH * 0.01
    assert s.calculate_trade_value(_iv_ctx(-20.0)) > INITIAL_CASH * 0.01


def test_a_positive_exponent_leans_into_an_implied_vol_jump():
    s = hf(per_lot_pct=0.01, implied_vol_exponent=1.0)
    feed(s, [100.0])
    assert s.calculate_trade_value(_iv_ctx(20.0)) > INITIAL_CASH * 0.01


def test_the_response_is_linear_in_the_change():
    """Linear, NOT an exponent on a ratio: the input is a signed change
    centred on zero, and a negative base to a fractional power is
    undefined."""
    s = hf(per_lot_pct=0.01, implied_vol_exponent=0.5)
    feed(s, [100.0])
    # 1 + 0.5 * (10/100) = 1.05
    assert s.calculate_trade_value(_iv_ctx(10.0)) == pytest.approx(
        INITIAL_CASH * 0.01 * 1.05
    )
    # 1 + 0.5 * (-10/100) = 0.95
    assert s.calculate_trade_value(_iv_ctx(-10.0)) == pytest.approx(
        INITIAL_CASH * 0.01 * 0.95
    )


def test_a_large_negative_change_cannot_invert_the_lot_size():
    """The clamp is load-bearing: an unclamped linear response goes
    NEGATIVE at a large enough exponent x change, which would flip a buy
    into a nonsense value rather than merely a small one."""
    s = hf(per_lot_pct=0.01, implied_vol_exponent=5.0, implied_vol_scale_min=0.25)
    feed(s, [100.0])
    value = s.calculate_trade_value(_iv_ctx(-80.0))  # 1 + 5*(-0.8) = -3.0 unclamped
    assert value > 0
    assert value == pytest.approx(INITIAL_CASH * 0.01 * 0.25)


def test_the_scale_is_clamped_at_the_top_too():
    s = hf(per_lot_pct=0.01, implied_vol_exponent=5.0, implied_vol_scale_max=1.5)
    feed(s, [100.0])
    assert s.calculate_trade_value(_iv_ctx(90.0)) == pytest.approx(
        INITIAL_CASH * 0.01 * 1.5
    )


def test_a_zero_change_is_neutral_whatever_the_exponent():
    """0.0 means both 'the index was flat' and 'no reading available',
    and leaving size unchanged is the right answer to both."""
    for exponent in (-2.0, -0.5, 0.5, 2.0):
        s = hf(per_lot_pct=0.01, implied_vol_exponent=exponent)
        feed(s, [100.0])
        assert s.calculate_trade_value(_iv_ctx(0.0)) == pytest.approx(INITIAL_CASH * 0.01)


def test_implied_vol_scaling_composes_with_vol_scaling():
    """Independent axes -- measured as such (partial rho +0.257 holding
    trailing realized vol fixed) -- so they multiply."""
    common = dict(per_lot_pct=0.01, vol_fast_days=0.1, vol_slow_days=2.0)
    vol_only = hf(vol_scale_exponent=-1.0, **common)
    both = hf(vol_scale_exponent=-1.0, implied_vol_exponent=-1.0, **common)
    for s in (vol_only, both):
        _vol_feed(s, _calm_then_wild())
    assert both.calculate_trade_value(_iv_ctx(30.0)) < vol_only.calculate_trade_value(
        _iv_ctx(30.0)
    )


@pytest.mark.parametrize(("low", "high"), [(0.0, 2.0), (-1.0, 2.0), (1.5, 1.0)])
def test_rejects_an_invalid_implied_vol_scale_range(low, high):
    with pytest.raises(ConfigurationError, match="implied_vol_scale_min"):
        hf(implied_vol_scale_min=low, implied_vol_scale_max=high)
