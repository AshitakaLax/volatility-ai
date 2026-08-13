from src.live_circuit_breaker import CircuitState, LiveCircuitBreaker, SQLiteCircuitBreakerStore
from src.risk_manager import RiskManager


def test_drawdown_halts_new_buys_but_state_is_explicit():
    breaker = LiveCircuitBreaker(threshold=0.10)
    assert breaker.evaluate(0.09) is False
    assert breaker.state is CircuitState.ACTIVE
    assert breaker.evaluate(0.10) is True
    assert breaker.state is CircuitState.MANUAL_RESET_REQUIRED


def test_halted_state_blocks_sizing_but_sell_path_is_not_risk_clamped():
    breaker = LiveCircuitBreaker(threshold=0.10)
    breaker.evaluate(0.20)
    risk = RiskManager(circuit_breaker=breaker)
    assert risk.clamp_trade_value(5000, 10000, 10000, 0) == 0.0
    assert breaker.halted is True


def test_manual_reset_reenables_new_buys():
    breaker = LiveCircuitBreaker(threshold=0.10)
    breaker.evaluate(0.10)
    breaker.reset()
    risk = RiskManager(circuit_breaker=breaker)
    assert breaker.state is CircuitState.ACTIVE
    assert risk.clamp_trade_value(5000, 10000, 10000, 0) == 5000.0


def test_halt_survives_restart(tmp_path):
    path = tmp_path / "state.sqlite"
    store = SQLiteCircuitBreakerStore(str(path))
    breaker = LiveCircuitBreaker(threshold=0.10)
    breaker.evaluate(0.15)
    store.save(breaker.state)
    store.close()

    restored_store = SQLiteCircuitBreakerStore(str(path))
    assert restored_store.load() is CircuitState.MANUAL_RESET_REQUIRED
    restored_store.close()
