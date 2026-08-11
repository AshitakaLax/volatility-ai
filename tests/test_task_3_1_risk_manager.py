import pytest

from src.risk_manager import RiskManager


def test_unlimited_limits_preserve_proposed_value_when_cash_allows():
    manager = RiskManager()
    assert manager.clamp_trade_value(1_000.0, 10_000.0, 2_000.0, 5) == 1_000.0


def test_cash_is_always_a_hard_upper_bound():
    manager = RiskManager()
    assert manager.clamp_trade_value(3_000.0, 10_000.0, 750.0, 0) == 750.0


def test_concurrent_lot_limit_blocks_new_lot():
    manager = RiskManager(max_concurrent_lots=2)
    assert manager.clamp_trade_value(1_000.0, 10_000.0, 5_000.0, 2) == 0.0
    assert manager.clamp_trade_value(1_000.0, 10_000.0, 5_000.0, 1) == 1_000.0


def test_total_exposure_limit_caps_trade_value():
    manager = RiskManager(max_total_exposure=0.50)
    # Equity=10k, current exposure=4k, so only 1k remains under the 50% cap.
    assert manager.clamp_trade_value(3_000.0, 10_000.0, 6_000.0, 0) == pytest.approx(1_000.0)


def test_zero_exposure_limit_blocks_new_exposure():
    manager = RiskManager(max_total_exposure=0.0)
    assert manager.clamp_trade_value(1_000.0, 10_000.0, 10_000.0, 0) == 0.0


def test_invalid_limits_are_rejected():
    with pytest.raises(ValueError):
        RiskManager(max_concurrent_lots=-1)
    with pytest.raises(ValueError):
        RiskManager(max_total_exposure=1.1)
