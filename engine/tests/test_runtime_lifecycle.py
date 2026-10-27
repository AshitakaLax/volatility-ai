"""
Task 7.12 acceptance tests.

Acceptance criteria:
1. Restart recovery never generates a duplicate order for an
   already-acted-on decision.
2. Graceful shutdown persists state and does not submit new buys after
   shutdown begins.
3. Open profitable harvest opportunities remain available after restart.
4. A shutdown that hits the bounded window without settling exits into
   RECONCILIATION_REQUIRED, not a guessed clean state.
"""

import pytest

from engine.core.exceptions import ExecutionError
from engine.core.idempotency import compute_decision_id
from engine.core.ledger import AssetLotLedger
from engine.core.persistence import LedgerStore
from engine.execution.reconciliation import BrokerSnapshot, Reconciler
from engine.trading.duplicate_order_guard import DuplicateOrderGuard
from engine.trading.risk_manager import CircuitBreaker, CircuitBreakerState
from engine.trading.runtime_lifecycle import (
    BLOCKED_STATES,
    STARTUP_SEQUENCE,
    RuntimeLifecycle,
    RuntimeState,
)


class FakeClock:
    """Deterministic clock so the bounded window is tested without real delays."""

    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "ledger.db"))
    yield s
    s.close()


def _seed_open_lot(store, shares=10.0, symbol="TQQQ", buy_price=50.0, profit_target=0.01):
    ledger = AssetLotLedger()
    lot = ledger.register_buy("lot-1", symbol, buy_price, shares, profit_target)
    store.record_open_lot(lot)
    return lot


def test_startup_walks_every_state_in_the_specified_order(store):
    lifecycle = RuntimeLifecycle(store=store)
    lifecycle.start(
        load_config=lambda: None,
        connect_broker=lambda: None,
        validate_data_clock=lambda: True,
    )
    assert lifecycle.state is RuntimeState.READY
    assert tuple(lifecycle.visited) == STARTUP_SEQUENCE


def test_no_new_buys_before_ready(store):
    lifecycle = RuntimeLifecycle(store=store)
    assert lifecycle.state is RuntimeState.STARTING
    assert lifecycle.allows_new_buys() is False

    for state in STARTUP_SEQUENCE[:-1]:  # every pre-READY state
        lifecycle.state = state
        assert lifecycle.allows_new_buys() is False, f"{state.value} must not permit new buys"

    lifecycle.state = RuntimeState.READY
    assert lifecycle.allows_new_buys() is True


def test_config_failure_exits_to_recovery_required_not_ready(store):
    lifecycle = RuntimeLifecycle(store=store)

    def boom():
        raise RuntimeError("bad config")

    assert lifecycle.start(load_config=boom) is RuntimeState.RECOVERY_REQUIRED
    assert lifecycle.allows_new_buys() is False


def test_unreadable_durable_state_exits_to_recovery_required():
    class _BrokenStore:
        def load_ledger(self):
            raise RuntimeError("corrupt ledger")

    lifecycle = RuntimeLifecycle(store=_BrokenStore())
    assert lifecycle.start() is RuntimeState.RECOVERY_REQUIRED
    assert lifecycle.state in BLOCKED_STATES


def test_broker_connection_failure_exits_to_recovery_required(store):
    lifecycle = RuntimeLifecycle(store=store)

    def boom():
        raise RuntimeError("no network")

    assert lifecycle.start(connect_broker=boom) is RuntimeState.RECOVERY_REQUIRED


def test_a_failed_start_keeps_the_stage_and_the_reason(store):
    """The trader's status said only "see the engine's log" -- on 10-23 the
    reason (the bridge's port taken) was in no place the operator looked."""
    lifecycle = RuntimeLifecycle(store=store)
    error = OSError("[Errno 98] Address already in use")

    def boom():
        raise error

    lifecycle.start(connect_broker=boom)
    assert lifecycle.failed_stage is RuntimeState.CONNECT_BROKER
    assert lifecycle.failure == "broker connection failed: [Errno 98] Address already in use"
    assert lifecycle.failure_error is error


def test_only_a_broker_that_cannot_be_reached_for_now_is_retryable(store):
    """EXIT_BROKER_UNAVAILABLE's test: a BrokerUnavailableError while
    connecting clears on its own; a bad key, or a book that disagrees with
    the broker's, needs a human."""
    from engine.core.exceptions import BrokerUnavailableError, ConfigurationError

    def raising(error):
        def connect():
            raise error

        return connect

    unavailable = RuntimeLifecycle(store=store)
    unavailable.start(connect_broker=raising(BrokerUnavailableError("signed out")))
    assert unavailable.retryable

    misconfigured = RuntimeLifecycle(store=store)
    misconfigured.start(connect_broker=raising(ConfigurationError("no key")))
    assert not misconfigured.retryable

    _seed_open_lot(store, shares=10.0)
    mismatched = RuntimeLifecycle(store=store, reconciler=Reconciler(store))
    mismatched.start(broker_snapshot_provider=lambda: BrokerSnapshot(positions={"TQQQ": 7.0}))
    assert mismatched.failed_stage is RuntimeState.RECONCILE
    assert not mismatched.retryable

    ready = RuntimeLifecycle(store=store, reconciler=Reconciler(store))
    ready.start(broker_snapshot_provider=lambda: BrokerSnapshot(positions={"TQQQ": 10.0}))
    assert ready.failed_stage is None and ready.failure is None and not ready.retryable


def test_an_account_that_cannot_be_read_for_now_is_a_wait_not_a_halt(store):
    """10-26: the Fidelity tab could not fetch, the startup snapshot failed,
    and a reconciliation halt was left in the real-money ledger that only a
    human could clear -- though nothing was known to disagree."""
    from engine.core.exceptions import BrokerUnavailableError

    def unreadable():
        raise BrokerUnavailableError("the Fidelity tab returned no response")

    breaker = CircuitBreaker()
    lifecycle = RuntimeLifecycle(
        store=store, circuit_breaker=breaker, reconciler=Reconciler(store, circuit_breaker=breaker)
    )
    assert lifecycle.start(broker_snapshot_provider=unreadable) is RuntimeState.RECOVERY_REQUIRED
    assert lifecycle.failed_stage is RuntimeState.RECONCILE and lifecycle.retryable
    assert "the Fidelity tab returned no response" in lifecycle.failure
    assert breaker.state is not CircuitBreakerState.HALTED_NEW_BUYS, "no halt to clear by hand"

    def broken():
        raise ValueError("an answer that cannot be parsed")

    breaker = CircuitBreaker()
    unknown = RuntimeLifecycle(
        store=store, circuit_breaker=breaker, reconciler=Reconciler(store, circuit_breaker=breaker)
    )
    assert unknown.start(broker_snapshot_provider=broken) is RuntimeState.RECONCILIATION_REQUIRED
    assert not unknown.retryable
    assert breaker.state is CircuitBreakerState.HALTED_NEW_BUYS, "anything else still halts"


def test_the_engine_is_ready_before_the_broker_is_asked_anything(store):
    """The engine warms up (its history replayed) and says it is ready; only
    then does startup wait for the broker -- two answers, the first never
    waiting on the second."""
    from engine.core.exceptions import BrokerUnavailableError

    order = []
    lifecycle = RuntimeLifecycle(store=store)
    state = lifecycle.start(
        warm_up=lambda: order.append(("warm_up", lifecycle.state)),
        on_engine_ready=lambda: order.append(("engine_ready", lifecycle.state)),
        wait_for_broker=lambda: order.append(("wait", lifecycle.state)),
        connect_broker=lambda: order.append(("connect", lifecycle.state)),
    )
    assert state is RuntimeState.READY
    assert order == [
        ("warm_up", RuntimeState.WARM_UP),
        ("engine_ready", RuntimeState.ENGINE_READY),
        ("wait", RuntimeState.CONNECT_BROKER),
        ("connect", RuntimeState.CONNECT_BROKER),
    ]

    def never_ready():
        raise BrokerUnavailableError("Fidelity is not ready: Fidelity signed you out")

    waited = RuntimeLifecycle(store=store)
    assert waited.start(wait_for_broker=never_ready) is RuntimeState.RECOVERY_REQUIRED
    assert waited.retryable and "signed you out" in waited.failure

    cold = RuntimeLifecycle(store=store)
    assert cold.start(warm_up=lambda: 1 / 0) is RuntimeState.RECOVERY_REQUIRED
    assert cold.failed_stage is RuntimeState.WARM_UP and not cold.retryable

    noisy = RuntimeLifecycle(store=store)
    assert noisy.start(on_engine_ready=lambda: 1 / 0) is RuntimeState.READY, (
        "a report never stops it"
    )


def test_failed_reconciliation_blocks_ready_and_halts(store):
    _seed_open_lot(store, shares=10.0)
    breaker = CircuitBreaker()
    lifecycle = RuntimeLifecycle(
        store=store, circuit_breaker=breaker, reconciler=Reconciler(store, circuit_breaker=breaker)
    )
    result = lifecycle.start(
        broker_snapshot_provider=lambda: BrokerSnapshot(positions={"TQQQ": 7.0})  # mismatch
    )
    assert result is RuntimeState.RECONCILIATION_REQUIRED
    assert lifecycle.allows_new_buys() is False
    assert breaker.state is CircuitBreakerState.HALTED_NEW_BUYS


def test_clean_reconciliation_reaches_ready(store):
    _seed_open_lot(store, shares=10.0)
    lifecycle = RuntimeLifecycle(store=store, reconciler=Reconciler(store))
    result = lifecycle.start(
        broker_snapshot_provider=lambda: BrokerSnapshot(positions={"TQQQ": 10.0}),
        validate_data_clock=lambda: True,
    )
    assert result is RuntimeState.READY


def test_failed_data_clock_validation_blocks_ready(store):
    lifecycle = RuntimeLifecycle(store=store)
    assert lifecycle.start(validate_data_clock=lambda: False) is RuntimeState.RECOVERY_REQUIRED


def test_a_persisted_halt_survives_startup(tmp_path):
    """Reaching READY must not clear a halt from a previous run."""
    db = str(tmp_path / "ledger.db")
    store1 = LedgerStore(db)
    CircuitBreaker(store=store1).evaluate(drawdown=0.5, threshold=0.2)
    store1.close()

    store2 = LedgerStore(db)
    breaker = CircuitBreaker(store=store2)
    lifecycle = RuntimeLifecycle(store=store2, circuit_breaker=breaker)
    assert lifecycle.start(validate_data_clock=lambda: True) is RuntimeState.READY
    assert lifecycle.allows_new_buys() is False, "READY must not override a persisted halt"
    store2.close()


def test_restart_recovery_never_duplicates_an_acted_on_decision(tmp_path):
    db = str(tmp_path / "ledger.db")
    decision_id = compute_decision_id(
        deployment_id="d1",
        strategy_id="fixed",
        symbol="TQQQ",
        market_event_id="bar-1",
        decision_type="grid_buy",
        sequence_number=1,
    )
    submissions = []

    def submit(cid):
        submissions.append(cid)
        return "broker-order-1"

    store1 = LedgerStore(db)
    DuplicateOrderGuard(store1).submit_once(decision_id, submit)
    store1.close()  # crash

    store2 = LedgerStore(db)
    lifecycle = RuntimeLifecycle(store=store2)
    lifecycle.start(validate_data_clock=lambda: True)
    DuplicateOrderGuard(store2).submit_once(decision_id, submit)  # replay after restart
    store2.close()

    assert len(submissions) == 1, "Restart must not re-submit an already-acted-on decision"


def test_open_profitable_harvest_opportunities_survive_restart(tmp_path):
    db = str(tmp_path / "ledger.db")
    store1 = LedgerStore(db)
    lot = _seed_open_lot(store1, shares=10.0, buy_price=50.0, profit_target=0.01)
    original_target = lot.target_sell_price
    store1.close()

    store2 = LedgerStore(db)
    lifecycle = RuntimeLifecycle(store=store2)
    lifecycle.start(validate_data_clock=lambda: True)

    recovered = lifecycle.recovered_ledger
    assert len(recovered.open_lots) == 1
    recovered_lot = recovered.open_lots[0]
    assert recovered_lot.shares == 10.0
    assert recovered_lot.target_sell_price == original_target

    # And it is genuinely marketable at a price above its target.
    assert recovered.get_marketable_lots(original_target + 0.01) == [recovered_lot]
    store2.close()


def test_shutdown_stops_new_buys_immediately(store):
    lifecycle = RuntimeLifecycle(store=store)
    lifecycle.start(validate_data_clock=lambda: True)
    assert lifecycle.allows_new_buys() is True

    lifecycle.shutdown(in_flight_settled=lambda: True)
    assert lifecycle.allows_new_buys() is False
    assert lifecycle.state is RuntimeState.STOPPED


def test_shutdown_persists_state_and_flushes_audit(store):
    calls = []
    lifecycle = RuntimeLifecycle(store=store)
    lifecycle.start(validate_data_clock=lambda: True)
    lifecycle.shutdown(
        in_flight_settled=lambda: True,
        persist_state=lambda: calls.append("persist"),
        flush_audit=lambda: calls.append("flush"),
        close_connections=lambda: calls.append("close"),
    )
    assert calls == ["persist", "flush", "close"], "Shutdown must persist, then flush, then close"


def test_shutdown_transitions_through_shutting_down(store):
    lifecycle = RuntimeLifecycle(store=store)
    lifecycle.start(validate_data_clock=lambda: True)
    lifecycle.shutdown(in_flight_settled=lambda: True)
    assert RuntimeState.SHUTTING_DOWN in lifecycle.visited


def test_shutdown_keeps_consuming_events_while_waiting_to_settle(store):
    """Steps 4-6: in-flight fills must still be applied during shutdown."""
    clock = FakeClock()
    polls = {"count": 0}

    def settled():
        polls["count"] += 1
        return polls["count"] >= 3  # settles on the third poll

    lifecycle = RuntimeLifecycle(store=store, clock=clock, sleep=lambda s: clock.advance(s))
    lifecycle.start(validate_data_clock=lambda: True)
    result = lifecycle.shutdown(in_flight_settled=settled, poll_interval=0.05)

    assert polls["count"] >= 3, "Shutdown must keep polling for in-flight settlement"
    assert result is RuntimeState.STOPPED


def test_unsettled_shutdown_exits_into_reconciliation_required(store):
    clock = FakeClock()
    lifecycle = RuntimeLifecycle(
        store=store, settle_timeout_seconds=30.0, clock=clock, sleep=lambda s: clock.advance(10.0)
    )
    lifecycle.start(validate_data_clock=lambda: True)

    result = lifecycle.shutdown(in_flight_settled=lambda: False)  # never settles
    assert result is RuntimeState.RECONCILIATION_REQUIRED
    assert lifecycle.state in BLOCKED_STATES


def test_unsettled_shutdown_does_not_persist_a_guessed_state(store):
    clock = FakeClock()
    persisted = []
    lifecycle = RuntimeLifecycle(store=store, clock=clock, sleep=lambda s: clock.advance(10.0))
    lifecycle.start(validate_data_clock=lambda: True)

    lifecycle.shutdown(
        in_flight_settled=lambda: False,
        persist_state=lambda: persisted.append("persist"),
    )
    assert persisted == [], "An unsettled shutdown must NOT persist a guessed state"


def test_unsettled_shutdown_still_flushes_audit_and_closes(store):
    clock = FakeClock()
    calls = []
    lifecycle = RuntimeLifecycle(store=store, clock=clock, sleep=lambda s: clock.advance(10.0))
    lifecycle.start(validate_data_clock=lambda: True)
    lifecycle.shutdown(
        in_flight_settled=lambda: False,
        flush_audit=lambda: calls.append("flush"),
        close_connections=lambda: calls.append("close"),
    )
    # The record of WHY it failed matters most here.
    assert calls == ["flush", "close"]


def test_unsettled_shutdown_halts_the_breaker_for_the_next_startup(store):
    clock = FakeClock()
    breaker = CircuitBreaker()
    lifecycle = RuntimeLifecycle(
        store=store, circuit_breaker=breaker, clock=clock, sleep=lambda s: clock.advance(10.0)
    )
    lifecycle.start(validate_data_clock=lambda: True)
    lifecycle.shutdown(in_flight_settled=lambda: False)
    assert breaker.allows_new_buys is False


def test_settle_timeout_is_configurable():
    assert RuntimeLifecycle().settle_timeout_seconds == 30.0
    assert RuntimeLifecycle(settle_timeout_seconds=5.0).settle_timeout_seconds == 5.0


def test_failed_persistence_during_shutdown_raises_and_blocks(store):
    lifecycle = RuntimeLifecycle(store=store)
    lifecycle.start(validate_data_clock=lambda: True)

    def boom():
        raise RuntimeError("disk full")

    with pytest.raises(ExecutionError, match="persist"):
        lifecycle.shutdown(in_flight_settled=lambda: True, persist_state=boom)
    assert lifecycle.state is RuntimeState.RECONCILIATION_REQUIRED


def test_shutdown_never_liquidates_open_lots(store):
    _seed_open_lot(store, shares=10.0)
    lifecycle = RuntimeLifecycle(store=store)
    lifecycle.start(validate_data_clock=lambda: True)
    lifecycle.shutdown(in_flight_settled=lambda: True)

    assert len(store.load_ledger().open_lots) == 1, "Shutdown must never liquidate open lots"


def test_unsettled_shutdown_also_never_liquidates(store):
    clock = FakeClock()
    _seed_open_lot(store, shares=10.0)
    lifecycle = RuntimeLifecycle(store=store, clock=clock, sleep=lambda s: clock.advance(10.0))
    lifecycle.start(validate_data_clock=lambda: True)
    lifecycle.shutdown(in_flight_settled=lambda: False)

    assert len(store.load_ledger().open_lots) == 1


def test_lifecycle_exposes_no_liquidation_or_cancel_path():
    lifecycle = RuntimeLifecycle()
    for forbidden in ("liquidate", "close_all", "flatten", "cancel_all_orders", "emergency_exit"):
        assert not hasattr(lifecycle, forbidden), (
            f"RuntimeLifecycle must not expose {forbidden!r} -- shutdown must never force "
            "liquidation, and existing orders are not auto-canceled without an explicit policy"
        )
