import pytest

from src.exceptions import ConfigurationError
from src.risk_manager import RiskManager


def test_both_limits_none_is_a_no_op_for_any_input():
    rm = RiskManager()
    assert rm.clamp_trade_value(5000.0, equity=100_000.0, cash=90_000.0, open_lot_count=0) == 5000.0
    assert rm.clamp_trade_value(0.0, equity=100_000.0, cash=90_000.0, open_lot_count=10) == 0.0
    assert (
        rm.clamp_trade_value(999_999.0, equity=100_000.0, cash=0.0, open_lot_count=100) == 999_999.0
    )


def test_max_concurrent_lots_clamps_to_zero_once_at_cap():
    rm = RiskManager(max_concurrent_lots=3)
    # Under the cap: unaffected.
    assert rm.clamp_trade_value(5000.0, equity=100_000.0, cash=90_000.0, open_lot_count=2) == 5000.0
    # At the cap: a 4th lot would exceed it -> clamped to 0.
    assert rm.clamp_trade_value(5000.0, equity=100_000.0, cash=90_000.0, open_lot_count=3) == 0.0
    # Past the cap (shouldn't normally happen, but must still clamp).
    assert rm.clamp_trade_value(5000.0, equity=100_000.0, cash=90_000.0, open_lot_count=5) == 0.0


def test_max_total_exposure_pct_keeps_deployed_capital_under_the_cap():
    rm = RiskManager(max_total_exposure_pct=0.5)
    equity = 100_000.0
    # Already 40k deployed (60k cash); proposing another 20k would push
    # deployed to 60k (60% of equity) -- must be clamped to 10k (50k cap - 40k deployed).
    clamped = rm.clamp_trade_value(20_000.0, equity=equity, cash=60_000.0, open_lot_count=1)
    assert clamped == pytest.approx(10_000.0)


def test_max_total_exposure_pct_no_op_when_already_under_cap_headroom():
    rm = RiskManager(max_total_exposure_pct=0.5)
    # 10k deployed, proposing 5k more -> 15k total, well under the 50k cap.
    clamped = rm.clamp_trade_value(5_000.0, equity=100_000.0, cash=90_000.0, open_lot_count=1)
    assert clamped == 5_000.0


def test_max_total_exposure_pct_clamps_to_zero_when_already_at_or_over_cap():
    rm = RiskManager(max_total_exposure_pct=0.5)
    # Already 50k deployed (at the cap) -- any further buy clamped to 0.
    clamped = rm.clamp_trade_value(1_000.0, equity=100_000.0, cash=50_000.0, open_lot_count=2)
    assert clamped == 0.0


def test_never_increases_proposed_value():
    rm = RiskManager(max_concurrent_lots=10, max_total_exposure_pct=0.9)
    # Plenty of headroom under both caps -- must still return exactly
    # what was proposed, never more.
    proposed = 123.45
    assert (
        rm.clamp_trade_value(proposed, equity=1_000_000.0, cash=999_000.0, open_lot_count=0)
        == proposed
    )


def test_both_limits_set_the_more_restrictive_applies():
    rm = RiskManager(max_concurrent_lots=1, max_total_exposure_pct=0.9)
    # Exposure cap alone would allow a large buy, but the lot-count cap
    # is already saturated (1 open lot, limit is 1) -> 0 regardless.
    clamped = rm.clamp_trade_value(50_000.0, equity=100_000.0, cash=90_000.0, open_lot_count=1)
    assert clamped == 0.0


def test_result_never_negative():
    rm = RiskManager(max_total_exposure_pct=0.1)
    # Deployed capital already exceeds the cap (e.g. equity dropped
    # after the cap was set) -- clamped value must floor at 0, not go negative.
    clamped = rm.clamp_trade_value(1_000.0, equity=100_000.0, cash=5_000.0, open_lot_count=3)
    assert clamped == 0.0


# --- drawdown-conditioned exposure throttle ---


def test_dd_exposure_defaults_to_an_exact_no_op():
    """dd_exposure_start=None must reproduce the unthrottled clamp
    exactly, at any drawdown -- including a config with no static
    max_total_exposure_pct at all, where the throttled branch would
    otherwise start applying an implicit 1.0 ceiling."""
    rm = RiskManager()
    assert rm._dd_exposure_enabled is False
    for dd in (0.0, 0.3, 0.6, 0.99):
        assert (
            rm.clamp_trade_value(
                999_999.0, equity=100_000.0, cash=0.0, open_lot_count=100, drawdown=dd
            )
            == 999_999.0
        )


def test_unaffected_below_the_start_threshold():
    rm = RiskManager(dd_exposure_start=0.30, dd_exposure_full=0.60, dd_exposure_floor_pct=0.0)
    # No static cap configured, deep headroom, drawdown still below start.
    clamped = rm.clamp_trade_value(
        20_000.0, equity=100_000.0, cash=90_000.0, open_lot_count=0, drawdown=0.30
    )
    assert clamped == 20_000.0


def test_the_ceiling_reaches_the_floor_at_and_beyond_full_drawdown():
    rm = RiskManager(dd_exposure_start=0.30, dd_exposure_full=0.60, dd_exposure_floor_pct=0.10)
    equity = 100_000.0
    for dd in (0.60, 0.75, 0.99):
        # floor_pct=0.10 -> ceiling is 10k regardless of how deep dd goes past full.
        clamped = rm.clamp_trade_value(
            50_000.0, equity=equity, cash=equity, open_lot_count=0, drawdown=dd
        )
        assert clamped == pytest.approx(10_000.0)


def test_the_ceiling_ramps_linearly_between_start_and_full():
    rm = RiskManager(dd_exposure_start=0.20, dd_exposure_full=0.60, dd_exposure_floor_pct=0.0)
    equity = 100_000.0
    # Halfway between 0.20 and 0.60 (dd=0.40): base is 1.0 (no static
    # cap set), floor is 0.0, so the ceiling should be 0.5 * equity.
    clamped = rm.clamp_trade_value(
        1_000_000.0, equity=equity, cash=equity, open_lot_count=0, drawdown=0.40
    )
    assert clamped == pytest.approx(50_000.0)


def test_ramps_down_from_a_configured_static_cap_not_from_1_0():
    """When a static max_total_exposure_pct IS set, the ramp must start
    from that value, not silently override it with 1.0."""
    rm = RiskManager(
        max_total_exposure_pct=0.5,
        dd_exposure_start=0.20,
        dd_exposure_full=0.60,
        dd_exposure_floor_pct=0.0,
    )
    equity = 100_000.0
    # Halfway (dd=0.40): base=0.5, floor=0.0 -> ceiling = 0.25 * equity.
    clamped = rm.clamp_trade_value(
        1_000_000.0, equity=equity, cash=equity, open_lot_count=0, drawdown=0.40
    )
    assert clamped == pytest.approx(25_000.0)


def test_ceiling_is_monotonically_non_increasing_as_drawdown_deepens():
    rm = RiskManager(dd_exposure_start=0.10, dd_exposure_full=0.70, dd_exposure_floor_pct=0.05)
    equity = 100_000.0
    ceilings = [
        rm.clamp_trade_value(1_000_000.0, equity=equity, cash=equity, open_lot_count=0, drawdown=dd)
        for dd in (0.0, 0.1, 0.3, 0.5, 0.7, 0.9)
    ]
    assert ceilings == sorted(ceilings, reverse=True)
    assert ceilings[-1] == pytest.approx(5_000.0)


def test_default_drawdown_argument_leaves_every_pre_existing_call_unaffected():
    """Every test above this section calls clamp_trade_value without a
    drawdown argument -- confirms the parameter's default (0.0) can
    never itself trigger a throttle that was never configured."""
    rm = RiskManager(dd_exposure_start=0.0001, dd_exposure_full=0.5, dd_exposure_floor_pct=0.0)
    # drawdown omitted -> defaults to 0.0, which is NOT > dd_exposure_start
    # (0.0001) so this must still be a no-op, even with an aggressively
    # low start threshold.
    clamped = rm.clamp_trade_value(5_000.0, equity=100_000.0, cash=90_000.0, open_lot_count=0)
    assert clamped == 5_000.0


@pytest.mark.parametrize("start", [0.0, -0.1, 1.0, 1.5])
def test_rejects_an_out_of_range_start_threshold(start):
    with pytest.raises(ConfigurationError, match="dd_exposure_start"):
        RiskManager(dd_exposure_start=start)


@pytest.mark.parametrize(("start", "full"), [(0.5, 0.5), (0.5, 0.3), (0.5, 1.5)])
def test_rejects_a_full_threshold_not_above_start_or_above_one(start, full):
    with pytest.raises(ConfigurationError, match="dd_exposure_full"):
        RiskManager(dd_exposure_start=start, dd_exposure_full=full)


def test_rejects_a_floor_above_the_base_ceiling():
    with pytest.raises(ConfigurationError, match="dd_exposure_floor_pct"):
        RiskManager(max_total_exposure_pct=0.5, dd_exposure_start=0.3, dd_exposure_floor_pct=0.6)


def test_rejects_a_negative_floor():
    with pytest.raises(ConfigurationError, match="dd_exposure_floor_pct"):
        RiskManager(dd_exposure_start=0.3, dd_exposure_floor_pct=-0.1)


def test_still_composes_with_the_max_concurrent_lots_cap():
    """The lot-count cap is checked first and short-circuits regardless
    of the exposure throttle -- must remain true with the new lever."""
    rm = RiskManager(
        max_concurrent_lots=1,
        dd_exposure_start=0.1,
        dd_exposure_full=0.5,
        dd_exposure_floor_pct=0.5,
    )
    clamped = rm.clamp_trade_value(
        50_000.0, equity=100_000.0, cash=90_000.0, open_lot_count=1, drawdown=0.9
    )
    assert clamped == 0.0
