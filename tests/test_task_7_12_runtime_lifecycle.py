from types import SimpleNamespace

import pytest

from src.live_execution import LiveExecutionLoop, RuntimeState


class _AuditStore:
    def __init__(self):
        self.audit = []
        self.persisted = 0
        self.closed = False

    def record_audit(self, event_id, event_type, payload):
        if self.closed:
            raise AssertionError("audit written after store close")
        self.audit.append((event_id, event_type, payload))

    def persist_ledger(self, ledger):
        self.persisted += 1

    def close(self):
        self.closed = True


class _Broker:
    def __init__(self):
        self.buy_calls = 0
        self.sell_calls = 0

    def submit_buy(self, symbol, trade_value):
        self.buy_calls += 1
        return "buy"

    def submit_sell(self, symbol, qty, target_price):
        self.sell_calls += 1
        return "sell"


def _loop():
    loop = LiveExecutionLoop.__new__(LiveExecutionLoop)
    loop.runtime_state = RuntimeState.READY
    loop._started = True
    loop.reconciliation_required = False
    loop.state_store = _AuditStore()
    loop.ledger = SimpleNamespace(open_lots=[])
    loop.broker = _Broker()
    loop.config = SimpleNamespace(backtest=SimpleNamespace(symbol="TQQQ"), deployment_id="test-deployment")
    loop.circuit_breaker = SimpleNamespace(halted=False)
    return loop


def test_shutdown_blocks_new_buys_and_persists_before_close():
    loop = _loop()
    decision = SimpleNamespace(clamped_trade_value=100.0)

    loop.shutdown()

    assert loop.runtime_state is RuntimeState.STOPPED
    assert loop._started is False
    assert loop.submit_buy(decision) is None
    assert loop.broker.buy_calls == 0
    assert loop.state_store.persisted == 1
    assert loop.state_store.closed is True
    assert any(item[2]["runtime_state"] == RuntimeState.SHUTTING_DOWN.value for item in loop.state_store.audit)


def test_shutdown_without_settlement_requires_reconciliation():
    loop = _loop()

    state = loop.shutdown(settle=lambda: False, max_wait_seconds=30)

    assert state is RuntimeState.RECONCILIATION_REQUIRED
    assert loop.reconciliation_required is True
    assert loop.state_store.closed is False
    assert loop.submit_buy(SimpleNamespace(clamped_trade_value=100.0)) is None


def test_negative_shutdown_window_is_rejected():
    loop = _loop()
    with pytest.raises(ValueError):
        loop.shutdown(max_wait_seconds=-1)
