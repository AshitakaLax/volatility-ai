"""
Startup recovery and graceful shutdown. Task 7.12.

Container restarts and deployment signals must not leave the strategy
half-active. This module SEQUENCES the pieces already built -- Task
7.3's LedgerStore, Task 7.8's CircuitBreaker, Task 7.11's Reconciler,
Task 7.4's DuplicateOrderGuard -- and reimplements none of them, per
this task's Non-goals.

Startup sequence (step 1), in exactly this order. New buys are
impossible before READY because allows_new_buys() checks the state,
not a flag someone can forget to set:

    STARTING -> LOAD_CONFIG -> LOAD_STATE -> CONNECT_BROKER
             -> RECONCILE -> VALIDATE_DATA_CLOCK -> READY

Shutdown sequence contract, implemented step for step:

    1. transition to SHUTTING_DOWN
    2. stop accepting new buy decisions
    3. stop new market-triggered strategy evaluations
    4. continue consuming broker/order/fill events
    5. apply confirmed fills through the normal accounting path
    6. enforce the no-loss guard for any exit still allowed
    7. persist durable state and audit events
    8. if in-flight state cannot settle in the bounded window ->
       RECONCILIATION_REQUIRED
    9. close connections and exit WITHOUT forced liquidation

Steps 4-6 are why shutdown is not simply "stop everything": an
in-flight fill that lands mid-shutdown must still be accounted for
correctly, or the next startup reconciles against a state that never
recorded it.

No forced liquidation, ever (steps 4/9 and Task 7.8's no-loss shutdown
invariant). There is no liquidation code path in this module, so it is
structurally impossible rather than merely omitted. Existing orders are
also not auto-canceled -- the contract requires a separate explicit
policy for that.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from enum import StrEnum

from src.exceptions import ExecutionError

logger = logging.getLogger("Optimizer")

DEFAULT_SETTLE_TIMEOUT_SECONDS = 30.0


class RuntimeState(StrEnum):
    """Startup/shutdown lifecycle states."""

    STARTING = "STARTING"
    LOAD_CONFIG = "LOAD_CONFIG"
    LOAD_STATE = "LOAD_STATE"
    CONNECT_BROKER = "CONNECT_BROKER"
    RECONCILE = "RECONCILE"
    VALIDATE_DATA_CLOCK = "VALIDATE_DATA_CLOCK"
    READY = "READY"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    STOPPED = "STOPPED"
    # Terminal-until-human states.
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


# Ordered startup path, used to assert the sequence actually ran in
# order rather than being asserted only in a docstring.
STARTUP_SEQUENCE = (
    RuntimeState.STARTING,
    RuntimeState.LOAD_CONFIG,
    RuntimeState.LOAD_STATE,
    RuntimeState.CONNECT_BROKER,
    RuntimeState.RECONCILE,
    RuntimeState.VALIDATE_DATA_CLOCK,
    RuntimeState.READY,
)

# States in which a human must act before trading can resume.
BLOCKED_STATES = frozenset({RuntimeState.RECONCILIATION_REQUIRED, RuntimeState.RECOVERY_REQUIRED})


class RuntimeLifecycle:
    """Owns the runtime state machine and the startup/shutdown order.

    State ownership: this object owns `state` and the visited-state
    trail. It does NOT own the ledger (LedgerStore), the halt
    (CircuitBreaker), or reconciliation outcomes (Reconciler) -- it
    calls into those and reacts.
    """

    def __init__(
        self,
        store=None,
        circuit_breaker=None,
        reconciler=None,
        settle_timeout_seconds: float = DEFAULT_SETTLE_TIMEOUT_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        """Assemble the lifecycle from its collaborators.

        All are optional so a partial system can still be sequenced;
        each stage is simply skipped when its collaborator is absent.
        clock defaults to time.monotonic (not wall time) so the shutdown
        window is immune to clock adjustments.
        """
        self.store = store
        self.circuit_breaker = circuit_breaker
        self.reconciler = reconciler
        self.settle_timeout_seconds = settle_timeout_seconds
        # clock/sleep are injectable so the bounded settle window can be
        # tested deterministically without real delays.
        self._clock = clock
        self._sleep = sleep
        self.state = RuntimeState.STARTING
        self.visited: list = [RuntimeState.STARTING]
        self.recovered_ledger = None

    # --- state ---

    def _enter(self, state: RuntimeState) -> None:
        """Move to a state and append it to the visited trail.

        The trail is what lets tests assert the startup sequence ran in
        the specified ORDER, not merely that it reached READY.
        """
        self.state = state
        self.visited.append(state)
        logger.info(f"Runtime state -> {state.value}")

    @property
    def is_ready(self) -> bool:
        """Whether startup completed. Note this is NOT sufficient to
        permit buying -- use allows_new_buys(), which also honors a
        persisted circuit-breaker halt."""
        return self.state is RuntimeState.READY

    def allows_new_buys(self) -> bool:
        """Step 2: no new buys before READY -- and none after shutdown
        begins either. Derived from the state itself rather than a
        separate flag, so the two can't disagree.

        Also respects Task 7.8's circuit breaker: READY is necessary
        but not sufficient if the breaker is halted.
        """
        if self.state is not RuntimeState.READY:
            return False
        if self.circuit_breaker is None:
            return True
        return self.circuit_breaker.allows_new_buys

    # --- startup ---

    def start(
        self,
        load_config: Callable[[], object] | None = None,
        connect_broker: Callable[[], object] | None = None,
        broker_snapshot_provider: Callable[[], object] | None = None,
        validate_data_clock: Callable[[], bool] | None = None,
        local_orders: dict | None = None,
        expected_cash: float | None = None,
    ) -> RuntimeState:
        """Walk the startup sequence in order, stopping at the first
        stage that cannot complete safely.

        Step 5: any stage that cannot persist/reconcile safely exits
        into a state requiring explicit recovery -- it never guesses
        and never silently proceeds to READY.
        """
        self._enter(RuntimeState.LOAD_CONFIG)
        if load_config is not None:
            try:
                load_config()
            except Exception as e:
                return self._fail(RuntimeState.RECOVERY_REQUIRED, f"config load failed: {e}")

        self._enter(RuntimeState.LOAD_STATE)
        if self.store is not None:
            try:
                self.recovered_ledger = self.store.load_ledger()
            except Exception as e:
                # Never proceed on an unreadable ledger -- that is
                # exactly the "guessing" step 5 forbids.
                return self._fail(RuntimeState.RECOVERY_REQUIRED, f"durable state load failed: {e}")

        self._enter(RuntimeState.CONNECT_BROKER)
        if connect_broker is not None:
            try:
                connect_broker()
            except Exception as e:
                return self._fail(RuntimeState.RECOVERY_REQUIRED, f"broker connection failed: {e}")

        self._enter(RuntimeState.RECONCILE)
        if self.reconciler is not None and broker_snapshot_provider is not None:
            try:
                snapshot = broker_snapshot_provider()
            except Exception as e:
                return self._fail(
                    RuntimeState.RECONCILIATION_REQUIRED, f"broker snapshot failed: {e}"
                )
            report = self.reconciler.reconcile(
                snapshot, local_orders=local_orders, expected_cash=expected_cash
            )
            if not report.ready:
                return self._fail(RuntimeState.RECONCILIATION_REQUIRED, report.diagnostic())

        self._enter(RuntimeState.VALIDATE_DATA_CLOCK)
        if validate_data_clock is not None:
            try:
                if not validate_data_clock():
                    return self._fail(
                        RuntimeState.RECOVERY_REQUIRED, "data/clock validation returned false"
                    )
            except Exception as e:
                return self._fail(
                    RuntimeState.RECOVERY_REQUIRED, f"data/clock validation failed: {e}"
                )

        # A halt persisted from a previous run (Task 7.8) survives
        # startup: reaching READY does not clear it, and
        # allows_new_buys() still returns False until a manual reset.
        self._enter(RuntimeState.READY)
        return self.state

    def _fail(self, state: RuntimeState, detail: str) -> RuntimeState:
        """Abort startup into a blocked state, logging why.

        A reconciliation failure additionally halts the circuit breaker,
        so the block persists across a restart rather than evaporating
        when someone restarts the process to "fix" it.
        """
        self._enter(state)
        logger.error(f"Startup halted in {state.value}: {detail}")
        if self.circuit_breaker is not None and state is RuntimeState.RECONCILIATION_REQUIRED:
            self.circuit_breaker.halt_for_reconciliation(detail)
        return self.state

    # --- shutdown ---

    def shutdown(
        self,
        in_flight_settled: Callable[[], bool] | None = None,
        persist_state: Callable[[], None] | None = None,
        flush_audit: Callable[[], None] | None = None,
        close_connections: Callable[[], None] | None = None,
        poll_interval: float = 0.05,
    ) -> RuntimeState:
        """Graceful shutdown, following the contract step for step.

        in_flight_settled is polled until it returns True or the
        bounded window elapses. While polling, broker/order/fill events
        are still expected to be consumed and applied by the caller's
        normal accounting path (steps 4-6) -- this method does not stop
        that, which is the point.

        Never force-liquidates and never force-persists a guessed
        state: an unsettled window exits into RECONCILIATION_REQUIRED
        so the NEXT startup reconciles rather than trusting a snapshot
        taken mid-flight.
        """
        self._enter(RuntimeState.SHUTTING_DOWN)  # steps 1-3

        settled = True
        if in_flight_settled is not None:
            deadline = self._clock() + self.settle_timeout_seconds
            settled = bool(in_flight_settled())
            while not settled and self._clock() < deadline:
                self._sleep(poll_interval)
                settled = bool(in_flight_settled())

        if not settled:
            # Step 8. Deliberately BEFORE persisting: persisting an
            # unsettled snapshot is exactly the "guessed state" the
            # bounded-window contract forbids.
            detail = (
                f"In-flight state did not settle within {self.settle_timeout_seconds}s. "
                "Not force-liquidating and not persisting a guessed state -- exiting into "
                "RECONCILIATION_REQUIRED so the next startup reconciles."
            )
            self._enter(RuntimeState.RECONCILIATION_REQUIRED)
            logger.error(detail)
            if self.circuit_breaker is not None:
                self.circuit_breaker.halt_for_reconciliation(detail)
            if flush_audit is not None:
                flush_audit()  # audit still flushes -- the record of WHY matters most here
            if close_connections is not None:
                close_connections()
            return self.state

        # Step 7: settled, so persisting is recording reality, not guessing.
        if persist_state is not None:
            try:
                persist_state()
            except Exception as e:
                self._enter(RuntimeState.RECONCILIATION_REQUIRED)
                logger.error(f"Shutdown persistence failed: {e}")
                if close_connections is not None:
                    close_connections()
                raise ExecutionError(f"Shutdown could not persist durable state: {e}") from e
        if flush_audit is not None:
            flush_audit()
        if close_connections is not None:
            close_connections()  # step 9

        self._enter(RuntimeState.STOPPED)
        return self.state
