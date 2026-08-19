"""
Task 7.8 acceptance tests (L9, High).

Acceptance criteria:
1. A live-simulating scenario that crosses the configured drawdown
   threshold stops new buy orders while continuing to process sells
   for existing lots.
2. The halt persists across a restart (Task 7.3) until manually
   cleared.

Also covers the HALTED_NEW_BUYS behavior table and the no-loss
shutdown invariant ("must never force liquidation solely because the
system is halted").
"""

from datetime import datetime, timezone

import pytest

from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.live_execution import LiveExecutionLoop
from src.market_context import MarketContext
from src.persistence import LedgerStore
from src.risk_manager import HALT_STATE_KEY, CircuitBreaker, CircuitBreakerState, RiskManager
from src.secrets import API_KEY_ID_ENV_VAR, API_SECRET_KEY_ENV_VAR
from src.size_calculators import FixedPortfolioPercentage

THRESHOLD = 0.20  # halt if drawdown exceeds 20%


def _config():
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "live": {"enabled": True, "paper_trading": True},
        }
    )


def _context(close: float, drawdown: float = 0.0, open_lot_count: int = 0) -> MarketContext:
    return MarketContext(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        open=close, high=close, low=close, close=close,
        cash=100_000.0, equity=100_000.0, peak_equity=100_000.0,
        drawdown=drawdown, open_lot_count=open_lot_count, bar_index=0,
    )


def _started_loop(monkeypatch, breaker=None, threshold=THRESHOLD):
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    loop = LiveExecutionLoop(
        _config(),
        FixedPortfolioPercentage(allocation_pct=0.05),
        RiskManager(halt_new_buys_if_drawdown_exceeds=threshold),
        circuit_breaker=breaker,
    )
    loop.start()
    return loop


def test_starts_active_and_allows_buys():
    breaker = CircuitBreaker()
    assert breaker.state is CircuitBreakerState.ACTIVE
    assert breaker.allows_new_buys is True


def test_trips_when_drawdown_exceeds_the_threshold():
    breaker = CircuitBreaker()
    breaker.evaluate(drawdown=0.25, threshold=THRESHOLD)
    assert breaker.state is CircuitBreakerState.HALTED_NEW_BUYS
    assert breaker.allows_new_buys is False


def test_does_not_trip_at_or_below_the_threshold():
    breaker = CircuitBreaker()
    breaker.evaluate(drawdown=0.20, threshold=THRESHOLD)  # exactly at
    assert breaker.state is CircuitBreakerState.ACTIVE
    breaker.evaluate(drawdown=0.1999, threshold=THRESHOLD)
    assert breaker.state is CircuitBreakerState.ACTIVE


def test_unconfigured_breaker_never_trips():
    breaker = CircuitBreaker()
    breaker.evaluate(drawdown=0.99, threshold=None)
    assert breaker.state is CircuitBreakerState.ACTIVE
    assert breaker.allows_new_buys is True


def test_recovery_does_not_auto_resume_buying():
    """Task 7.8 step 3: no auto-resume once drawdown recovers."""
    breaker = CircuitBreaker()
    breaker.evaluate(drawdown=0.25, threshold=THRESHOLD)
    assert breaker.state is CircuitBreakerState.HALTED_NEW_BUYS

    breaker.evaluate(drawdown=0.01, threshold=THRESHOLD)  # fully recovered
    assert breaker.state is CircuitBreakerState.MANUAL_RESET_REQUIRED
    assert breaker.allows_new_buys is False, "Recovery must NOT silently re-enable buying"


def test_only_manual_reset_returns_to_active():
    breaker = CircuitBreaker()
    breaker.evaluate(drawdown=0.25, threshold=THRESHOLD)
    breaker.evaluate(drawdown=0.01, threshold=THRESHOLD)
    assert breaker.allows_new_buys is False

    breaker.manual_reset(operator="alice", note="reviewed feed anomaly")
    assert breaker.state is CircuitBreakerState.ACTIVE
    assert breaker.allows_new_buys is True
    assert "alice" in breaker.reason


def test_anonymous_reset_is_refused():
    breaker = CircuitBreaker()
    breaker.evaluate(drawdown=0.25, threshold=THRESHOLD)
    for bad in ("", "   ", None):
        with pytest.raises(ConfigurationError, match="operator"):
            breaker.manual_reset(operator=bad)
    assert breaker.allows_new_buys is False


def test_manual_reset_works_directly_from_halted_state():
    breaker = CircuitBreaker()
    breaker.evaluate(drawdown=0.25, threshold=THRESHOLD)
    breaker.manual_reset(operator="bob")
    assert breaker.state is CircuitBreakerState.ACTIVE


def test_trip_is_alerted_via_the_sink_when_provided():
    alerts = []
    breaker = CircuitBreaker(alert_sink=alerts.append)
    breaker.evaluate(drawdown=0.25, threshold=THRESHOLD)
    assert len(alerts) == 1
    assert alerts[0]["event"] == "TRIPPED"
    assert alerts[0]["state"] == "HALTED_NEW_BUYS"


def test_recovery_and_reset_are_also_alerted():
    alerts = []
    breaker = CircuitBreaker(alert_sink=alerts.append)
    breaker.evaluate(drawdown=0.25, threshold=THRESHOLD)
    breaker.evaluate(drawdown=0.01, threshold=THRESHOLD)
    breaker.manual_reset(operator="alice")
    assert [a["event"] for a in alerts] == ["TRIPPED", "AWAITING_MANUAL_RESET", "MANUAL_RESET"]


def test_trip_is_logged_when_no_sink_is_wired(caplog):
    breaker = CircuitBreaker()
    with caplog.at_level("ERROR", logger="Optimizer"):
        breaker.evaluate(drawdown=0.25, threshold=THRESHOLD)
    assert any("CIRCUIT BREAKER" in r.getMessage() for r in caplog.records)


def test_halt_persists_across_a_restart(tmp_path):
    db = str(tmp_path / "ledger.db")

    store1 = LedgerStore(db)
    breaker1 = CircuitBreaker(store=store1)
    breaker1.evaluate(drawdown=0.25, threshold=THRESHOLD)
    assert breaker1.state is CircuitBreakerState.HALTED_NEW_BUYS
    store1.close()  # simulate process death

    store2 = LedgerStore(db)  # fresh process, same store
    breaker2 = CircuitBreaker(store=store2)
    assert breaker2.state is CircuitBreakerState.HALTED_NEW_BUYS, "Halt must survive a restart"
    assert breaker2.allows_new_buys is False
    store2.close()


def test_manual_reset_also_persists_across_a_restart(tmp_path):
    db = str(tmp_path / "ledger.db")

    store1 = LedgerStore(db)
    breaker1 = CircuitBreaker(store=store1)
    breaker1.evaluate(drawdown=0.25, threshold=THRESHOLD)
    breaker1.manual_reset(operator="alice")
    store1.close()

    store2 = LedgerStore(db)
    breaker2 = CircuitBreaker(store=store2)
    assert breaker2.state is CircuitBreakerState.ACTIVE, "A cleared halt must stay cleared"
    store2.close()


def test_restart_cannot_silently_clear_a_halt(tmp_path):
    # The dangerous failure mode: restarting to "fix" a halt.
    db = str(tmp_path / "ledger.db")
    store1 = LedgerStore(db)
    CircuitBreaker(store=store1).evaluate(drawdown=0.30, threshold=THRESHOLD)
    store1.close()

    for _ in range(3):  # repeated restarts must not help
        store = LedgerStore(db)
        assert CircuitBreaker(store=store).allows_new_buys is False
        store.close()


def test_halt_state_is_written_to_durable_storage(tmp_path):
    store = LedgerStore(str(tmp_path / "ledger.db"))
    CircuitBreaker(store=store).evaluate(drawdown=0.25, threshold=THRESHOLD)
    assert store.get_meta(HALT_STATE_KEY) == "HALTED_NEW_BUYS"
    store.close()


def test_live_loop_blocks_new_buys_once_halted(monkeypatch):
    loop = _started_loop(monkeypatch)

    # Below threshold: a triggering tick produces a real buy decision.
    ok = loop.decision_cycle(_context(close=49.0, drawdown=0.05), step=0.01, last_buy_price=50.0)
    assert ok.triggered is True
    assert ok.clamped_trade_value > 0

    # Above threshold: the same triggering tick is blocked.
    halted = loop.decision_cycle(_context(close=49.0, drawdown=0.25), step=0.01, last_buy_price=50.0)
    assert halted.triggered is False, "New buys must be blocked once halted"
    assert halted.clamped_trade_value == 0.0
    assert loop.circuit_breaker.state is CircuitBreakerState.HALTED_NEW_BUYS


def test_halted_loop_still_updates_strategy_rolling_state(monkeypatch):
    """HALTED_NEW_BUYS behavior table: 'Update strategy rolling state: Yes'."""

    class _CountingStrategy(FixedPortfolioPercentage):
        def __init__(self, allocation_pct):
            super().__init__(allocation_pct=allocation_pct)
            self.ticks = 0

        def record_tick(self, context):
            self.ticks += 1

    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    strategy = _CountingStrategy(allocation_pct=0.05)
    loop = LiveExecutionLoop(_config(), strategy, RiskManager(halt_new_buys_if_drawdown_exceeds=THRESHOLD))
    loop.start()

    loop.decision_cycle(_context(close=49.0, drawdown=0.25), step=0.01, last_buy_price=50.0)
    loop.decision_cycle(_context(close=48.0, drawdown=0.30), step=0.01, last_buy_price=50.0)
    assert strategy.ticks == 2, "Strategy must keep seeing ticks while halted"


def test_halted_loop_still_validates_market_data(monkeypatch):
    """Behavior table: 'Receive/validate market data: Yes'."""
    loop = _started_loop(monkeypatch)
    loop.circuit_breaker.evaluate(drawdown=0.30, threshold=THRESHOLD)
    assert loop.validate_tick(100.0).accepted is True
    assert loop.validate_tick(0.0).accepted is False


def test_halt_never_forces_liquidation(monkeypatch):
    """No-loss shutdown invariant: halting must never itself sell.

    The breaker's whole surface is state + allows_new_buys + reset --
    it has no liquidation method at all, so forced selling is
    structurally impossible rather than merely avoided.
    """
    loop = _started_loop(monkeypatch)
    loop.decision_cycle(_context(close=49.0, drawdown=0.30, open_lot_count=4), step=0.01, last_buy_price=50.0)

    breaker = loop.circuit_breaker
    for forbidden in ("liquidate", "close_all", "emergency_sell", "flatten", "force_exit"):
        assert not hasattr(breaker, forbidden), (
            f"CircuitBreaker must not expose {forbidden!r} -- a halt must never force liquidation"
        )


def test_buys_resume_only_after_a_manual_reset(monkeypatch):
    loop = _started_loop(monkeypatch)
    loop.decision_cycle(_context(close=49.0, drawdown=0.25), step=0.01, last_buy_price=50.0)
    assert loop.circuit_breaker.allows_new_buys is False

    # Drawdown recovers -- still blocked.
    recovered = loop.decision_cycle(_context(close=49.0, drawdown=0.01), step=0.01, last_buy_price=50.0)
    assert recovered.triggered is False

    loop.circuit_breaker.manual_reset(operator="alice", note="verified")
    resumed = loop.decision_cycle(_context(close=49.0, drawdown=0.01), step=0.01, last_buy_price=50.0)
    assert resumed.triggered is True
    assert resumed.clamped_trade_value > 0


def test_risk_manager_default_leaves_the_breaker_disabled():
    assert RiskManager().halt_new_buys_if_drawdown_exceeds is None


def test_invalid_halt_threshold_rejected():
    for bad in (-0.1, 1.5):
        with pytest.raises(ConfigurationError):
            RiskManager(halt_new_buys_if_drawdown_exceeds=bad)


def test_clamp_trade_value_is_unchanged_by_the_new_setting():
    # The breaker is distinct from the sizing clamp; adding it must not
    # alter clamping behavior.
    without = RiskManager(max_concurrent_lots=3)
    with_halt = RiskManager(max_concurrent_lots=3, halt_new_buys_if_drawdown_exceeds=0.2)
    args = (5000.0, 100_000.0, 90_000.0, 2)
    assert without.clamp_trade_value(*args) == with_halt.clamp_trade_value(*args)
