"""
Risk manager controlling new-buy exposure. Task 3.1 (R1), implemented
exactly per architecture_overview.md Section 5.4.

Risk semantics (implementation_task_specs.md Task 3.1):
- Controls new buy exposure only -- does not decide whether an
  existing profitable lot may be harvested.
- max_total_exposure_pct means gross deployed market value divided by
  current equity.
- A cap produces a deterministic clamped value of
  0 <= approved_value <= proposed_value -- never increases exposure.
- None means unlimited for that specific control.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from src.exceptions import ConfigurationError
from src.validation import validate_positive_int, validate_unit_interval

logger = logging.getLogger("Optimizer")

# Durable key for the halt state (Task 7.3's LedgerStore meta table).
HALT_STATE_KEY = "circuit_breaker_state"
HALT_REASON_KEY = "circuit_breaker_reason"


class CircuitBreakerState(StrEnum):
    """Explicit states per Task 7.8's State contract.

    ACTIVE                -- normal operation, new buys permitted.
    HALTED_NEW_BUYS       -- tripped, and the tripping condition still
                             holds. No new buy exposure.
    MANUAL_RESET_REQUIRED -- tripped earlier; the condition has since
                             recovered, but buying stays blocked until
                             a human explicitly resets. This state is
                             what implements the task's step 3 ("don't
                             auto-resume once the drawdown recovers,
                             since the point is to force a human look
                             at what happened") -- without it,
                             recovery would silently re-enable buying
                             and nobody would ever review the event.

    Both non-ACTIVE states block new buys identically; they differ only
    in whether the underlying condition is still breached, which is
    what an operator needs to know when they come to look.
    """

    ACTIVE = "ACTIVE"
    HALTED_NEW_BUYS = "HALTED_NEW_BUYS"
    MANUAL_RESET_REQUIRED = "MANUAL_RESET_REQUIRED"


class CircuitBreaker:
    """Live-only hard stop on NEW BUY exposure.

    No-loss shutdown invariant (Task 7.8): this NEVER forces
    liquidation. Its only action is halting new buys plus alerting.
    Existing lots remain fully eligible for normal profitable harvest,
    and the no-loss guard still governs every sell. There is
    deliberately no emergency-liquidation path here -- the task
    requires that be a separate, explicitly approved policy.

    State ownership: this object owns the halt state. When a `store`
    (Task 7.3 LedgerStore) is supplied, the store is the durable source
    of truth and the halt survives a restart; the in-memory attribute
    is a cache of it.
    """

    def __init__(self, store=None, alert_sink=None):
        """Restore any persisted halt, or start ACTIVE.

        When `store` is given it is the durable source of truth and a
        halt survives restarts -- the in-memory state is a cache of it.
        Without a store the breaker is process-local, which is fine for
        backtests but means a restart silently clears a halt, so live
        use should always pass one.
        """
        self._store = store
        # Canonical observability path when wired (Task 7.14); falls
        # back to structured logging so a halt is never silent.
        self._alert_sink = alert_sink
        self._state = CircuitBreakerState.ACTIVE
        self._reason = ""
        if store is not None:
            persisted = store.get_meta(HALT_STATE_KEY)
            if persisted:
                self._state = CircuitBreakerState(persisted)
                self._reason = store.get_meta(HALT_REASON_KEY) or ""

    @property
    def state(self) -> CircuitBreakerState:
        """Current breaker state, reloaded from durable storage at
        construction when a store is attached.

        Prefer `allows_new_buys` for gating decisions -- two distinct
        states block buying, so comparing against a single state here is
        an easy way to get it wrong.
        """
        return self._state

    @property
    def reason(self) -> str:
        """Human-readable explanation of the current state, for the
        operator who has to decide whether to reset."""
        return self._reason

    @property
    def allows_new_buys(self) -> bool:
        """Whether new buy exposure is currently permitted.

        Only ACTIVE permits buying. Both HALTED_NEW_BUYS and
        MANUAL_RESET_REQUIRED block it -- including after the drawdown
        has recovered, which is the point: recovery must not silently
        re-enable trading before a human has looked.
        """
        return self._state is CircuitBreakerState.ACTIVE

    def _persist(self) -> None:
        """Write state and reason to durable storage, if a store exists."""
        if self._store is not None:
            self._store.set_meta(HALT_STATE_KEY, self._state.value)
            self._store.set_meta(HALT_REASON_KEY, self._reason)

    def _alert(self, event: str, detail: str) -> None:
        """Emit a breaker transition to the alert sink, or to ERROR-level
        logging when none is wired -- a halt must never be silent."""
        record = {"event": event, "state": self._state.value, "detail": detail}
        if self._alert_sink is not None:
            self._alert_sink(record)
        else:
            logger.error(f"CIRCUIT BREAKER {event}: state={self._state.value} -- {detail}")

    def evaluate(self, drawdown: float, threshold: float | None) -> CircuitBreakerState:
        """Check the current drawdown against the halt threshold.

        Called at the same point as clamp_trade_value but kept distinct
        from it: the clamp reduces size, this blocks entry outright.

        Once tripped, a recovering drawdown moves HALTED_NEW_BUYS ->
        MANUAL_RESET_REQUIRED but never back to ACTIVE. Only
        manual_reset() does that.
        """
        if threshold is None:
            return self._state  # breaker not configured; never auto-trips

        breached = drawdown > threshold
        if self._state is CircuitBreakerState.ACTIVE:
            if breached:
                self._state = CircuitBreakerState.HALTED_NEW_BUYS
                self._reason = f"drawdown {drawdown:.4%} exceeded halt threshold {threshold:.4%}"
                self._persist()
                self._alert("TRIPPED", self._reason)
        elif self._state is CircuitBreakerState.HALTED_NEW_BUYS and not breached:
            self._state = CircuitBreakerState.MANUAL_RESET_REQUIRED
            self._reason = (
                f"drawdown recovered to {drawdown:.4%} (threshold {threshold:.4%}) after a halt; "
                "new buys stay blocked pending manual review"
            )
            self._persist()
            self._alert("AWAITING_MANUAL_RESET", self._reason)
        return self._state

    def halt_for_reconciliation(self, detail: str) -> None:
        """Halt new buys because reconciliation found an ambiguous
        discrepancy (Task 7.11 step 4).

        Reuses this breaker rather than introducing a second halt
        mechanism, so an operator has exactly ONE thing to inspect and
        reset regardless of which subsystem tripped it. Like every
        other halt here, it requires an explicit manual_reset and
        never forces liquidation.

        Already-halted stays halted -- a reconciliation failure must
        never downgrade or clear an existing halt.
        """
        if self._state is CircuitBreakerState.ACTIVE:
            self._state = CircuitBreakerState.HALTED_NEW_BUYS
            self._reason = f"reconciliation required: {detail}"
            self._persist()
            self._alert("TRIPPED_RECONCILIATION", self._reason)
        else:
            self._alert("RECONCILIATION_WHILE_HALTED", f"already {self._state.value}: {detail}")

    def manual_reset(self, operator: str, note: str = "") -> None:
        """Explicit human reset -- the ONLY way back to ACTIVE.

        operator is required and must be non-empty: an anonymous reset
        would defeat the purpose of forcing a human to look at what
        happened.
        """
        if not operator or not str(operator).strip():
            raise ConfigurationError(
                "manual_reset requires a non-empty operator identifier -- an anonymous reset "
                "defeats the purpose of forcing a human review."
            )
        previous = self._state
        self._state = CircuitBreakerState.ACTIVE
        self._reason = f"manually reset by {operator}" + (f": {note}" if note else "")
        self._persist()
        self._alert("MANUAL_RESET", f"from {previous.value} -- {self._reason}")


class RiskManager:
    """Canonical keyword is `max_total_exposure_pct`. `max_total_exposure`
    is also accepted -- src/live_execution.py, pushed directly to main
    mid-session, calls this constructor with that name -- see the chat
    this was produced in. Passing both is only allowed if they agree;
    the stored attribute is always `self.max_total_exposure_pct` either
    way. Both limits are validated here now (previously left as a
    documented gap when Task 4.9 built src/validation.py, since this
    file wasn't in that task's scope) -- validation helpers already
    exist and this file is being touched for the alias anyway."""

    def __init__(
        self,
        max_concurrent_lots: int | None = None,
        max_total_exposure_pct: float | None = None,
        max_total_exposure: float | None = None,
        halt_new_buys_if_drawdown_exceeds: float | None = None,
    ):
        """Configure the risk limits; every one defaults to unlimited.

        max_total_exposure and max_total_exposure_pct are two names for
        the same setting (the former is what src/live_execution.py
        expects); passing both is allowed only if they agree.

        halt_new_buys_if_drawdown_exceeds is live-only and drives the
        CircuitBreaker, not the sizing clamp -- it blocks entry outright
        rather than reducing size.
        """
        if (
            max_total_exposure_pct is not None
            and max_total_exposure is not None
            and max_total_exposure_pct != max_total_exposure
        ):
            raise ConfigurationError(
                f"max_total_exposure_pct ({max_total_exposure_pct!r}) and max_total_exposure "
                f"({max_total_exposure!r}) were both given and disagree -- pass only one"
            )
        exposure_value = (
            max_total_exposure_pct if max_total_exposure_pct is not None else max_total_exposure
        )

        if max_concurrent_lots is not None:
            validate_positive_int(max_concurrent_lots, "max_concurrent_lots")
        if exposure_value is not None:
            validate_unit_interval(exposure_value, "max_total_exposure_pct")

        if halt_new_buys_if_drawdown_exceeds is not None:
            validate_unit_interval(
                halt_new_buys_if_drawdown_exceeds, "halt_new_buys_if_drawdown_exceeds"
            )

        self.max_concurrent_lots = max_concurrent_lots
        self.max_total_exposure_pct = exposure_value
        # Task 7.8: live-only hard stop. None (default) means the
        # breaker never trips -- backtests are entirely unaffected.
        self.halt_new_buys_if_drawdown_exceeds = halt_new_buys_if_drawdown_exceeds

    def clamp_trade_value(
        self, proposed_value: float, equity: float, cash: float, open_lot_count: int
    ) -> float:
        """Both limits default to None -> unlimited, matching current
        behavior. Takes plain values (not a context object) so it works
        identically before and after Task 4.1's context-object refactor
        -- only the call site changes."""
        if self.max_concurrent_lots is not None and open_lot_count >= self.max_concurrent_lots:
            return 0.0
        if self.max_total_exposure_pct is not None:
            max_dollars = equity * self.max_total_exposure_pct
            deployed = equity - cash
            proposed_value = min(proposed_value, max(0.0, max_dollars - deployed))
        return proposed_value
