import pytest

from src.risk_manager import RiskManager


def test_both_limits_none_is_a_no_op_for_any_input():
    rm = RiskManager()
    assert rm.clamp_trade_value(5000.0, equity=100_000.0, cash=90_000.0, open_lot_count=0) == 5000.0
    assert rm.clamp_trade_value(0.0, equity=100_000.0, cash=90_000.0, open_lot_count=10) == 0.0
    assert rm.clamp_trade_value(999_999.0, equity=100_000.0, cash=0.0, open_lot_count=100) == 999_999.0


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
    assert rm.clamp_trade_value(proposed, equity=1_000_000.0, cash=999_000.0, open_lot_count=0) == proposed


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
