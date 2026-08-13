from datetime import datetime, timedelta, timezone

import pytest

from src.config import BacktestConfig, StrategyConfig, LiveConfig
from src.exceptions import ConfigurationError
from src.promotion_gate import PaperTradingResult, PromotionCriteria, PromotionGate


def _result(**overrides):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    values = dict(
        started_at=now,
        ended_at=now + timedelta(days=7),
        strategy_decisions=100,
        fills=20,
        accounting_discrepancies=0,
        duplicate_order_incidents=0,
        no_loss_guard_violations=0,
        unresolved_reconciliation=False,
        unhandled_runtime_exceptions=0,
    )
    values.update(overrides)
    return PaperTradingResult(**values)


def test_promotion_requires_all_machine_checkable_thresholds():
    gate = PromotionGate(PromotionCriteria(7 * 86400, 100, 20))
    assert gate.evaluate(_result(), promotion_id="promo-001") is True
    gate.require_live_promotion()


def test_promotion_rejects_short_or_unsafe_paper_run():
    gate = PromotionGate(PromotionCriteria(7 * 86400, 100, 20))
    assert gate.evaluate(_result(ended_at=datetime(2026, 1, 2, tzinfo=timezone.utc)), promotion_id="promo-002") is False
    with pytest.raises(ConfigurationError):
        gate.require_live_promotion()

    assert gate.evaluate(_result(duplicate_order_incidents=1), promotion_id="promo-003") is False
    with pytest.raises(ConfigurationError):
        gate.require_live_promotion()


def test_live_capital_config_cannot_start_without_passed_gate():
    from src.live_execution import LiveExecutionLoop

    config = BacktestConfig(strategy=StrategyConfig("test"), live=LiveConfig(enabled=True, paper_trading=False))
    with pytest.raises(ConfigurationError, match="promotion gate"):
        LiveExecutionLoop(config, strategy=object())
