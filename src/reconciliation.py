"""
Broker/account reconciliation. Task 7.11.

Local state can diverge from broker state after crashes, network
failures, manual broker actions, or missed callbacks. This is the
formal reconciliation operation that must run before trading resumes.

Consumes, never rebuilds (per this task's Non-goals):
  - Task 7.3's LedgerStore for persisted local state
  - Task 7.10's OrderState/OrderRecord for order identity and status
  - Task 7.8's CircuitBreaker for the halt itself

Governing rule, from the "Unambiguously derivable" contract: auto-repair
ONLY when a broker-confirmed event trail exactly and uniquely explains
the delta. Everything else halts. The contract's own tiebreaker is
adopted literally -- "when in doubt, treat it as ambiguous; an
unnecessary halt is recoverable, an incorrect auto-repair is not."

Step 5 is enforced structurally: this module has no code path that
creates a lot, a fill, or a cash movement from anything other than a
broker-confirmed fill matched to a known local order. It cannot
manufacture a transaction to make totals agree, because no such
function exists here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.order_lifecycle import OrderState

logger = logging.getLogger("Optimizer")


class ReconciliationOutcome(str, Enum):
    """Terminal outcome of one reconciliation pass."""

    READY = "READY"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class Discrepancy:
    """One specific unexplained difference.

    `detail` must name the actual delta -- the acceptance criterion
    requires "an actionable diagnostic naming the specific unexplained
    delta", not a generic "state mismatch".
    """

    kind: str
    detail: str
    auto_repairable: bool = False


@dataclass
class ReconciliationReport:
    outcome: ReconciliationOutcome
    discrepancies: list = field(default_factory=list)
    repairs_applied: list = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.outcome is ReconciliationOutcome.READY

    def diagnostic(self) -> str:
        if self.ready:
            return "READY -- local and broker state agree."
        lines = [f"  - [{d.kind}] {d.detail}" for d in self.discrepancies]
        return "RECONCILIATION_REQUIRED -- unresolved differences:\n" + "\n".join(lines)


@dataclass(frozen=True)
class BrokerSnapshot:
    """What the broker says. Supplied by the caller's adapter -- this
    module does not talk to Alpaca itself (that's the broker adapter's
    job, and fabricating one here would exceed this task's scope).

    positions: {symbol: total_shares}
    orders:    {client_order_id: {"state": OrderState, "filled_qty": float,
                                  "avg_fill_price": float, "symbol": str}}
    """

    positions: dict = field(default_factory=dict)
    orders: dict = field(default_factory=dict)
    cash: Optional[float] = None


class Reconciler:
    """Compares persisted local state against a broker snapshot.

    State ownership: the LedgerStore owns persisted local state and is
    the only thing mutated here, and only via its own methods. The
    CircuitBreaker owns the halt. This object owns neither; it decides
    and delegates.
    """

    QTY_EPSILON = 1e-9
    CASH_EPSILON = 0.01  # one cent

    def __init__(self, store, circuit_breaker=None, alert_sink=None):
        self.store = store
        self.circuit_breaker = circuit_breaker
        self._alert_sink = alert_sink

    def _alert(self, report: ReconciliationReport) -> None:
        record = {
            "event": "reconciliation_required",
            "discrepancies": [{"kind": d.kind, "detail": d.detail} for d in report.discrepancies],
        }
        if self._alert_sink is not None:
            self._alert_sink(record)
        else:
            logger.error(f"RECONCILIATION REQUIRED:\n{report.diagnostic()}")

    def reconcile(
        self,
        snapshot: BrokerSnapshot,
        local_orders: dict = None,
        expected_cash: Optional[float] = None,
    ) -> ReconciliationReport:
        """Run one reconciliation pass.

        local_orders: {client_order_id: OrderRecord} from Task 7.10.
        Ambiguity halts new buys via the circuit breaker (step 4) --
        never a forced liquidation, per Task 7.8's no-loss shutdown
        invariant.
        """
        local_orders = local_orders or {}
        discrepancies: list = []
        repairs: list = []

        self._reconcile_orders(snapshot, local_orders, discrepancies, repairs)
        self._reconcile_positions(snapshot, discrepancies)
        self._reconcile_cash(snapshot, expected_cash, discrepancies)

        if discrepancies:
            report = ReconciliationReport(
                outcome=ReconciliationOutcome.RECONCILIATION_REQUIRED,
                discrepancies=discrepancies,
                repairs_applied=repairs,
            )
            self._halt(report)
            return report

        return ReconciliationReport(outcome=ReconciliationOutcome.READY, repairs_applied=repairs)

    def _halt(self, report: ReconciliationReport) -> None:
        """Step 4: enter HALTED_NEW_BUYS and alert. Reuses Task 7.8's
        breaker rather than inventing a second halt mechanism, so there
        is exactly one thing an operator must reset."""
        if self.circuit_breaker is not None:
            self.circuit_breaker.halt_for_reconciliation(report.diagnostic())
        self._alert(report)

    # --- decision table rows ---

    def _reconcile_orders(self, snapshot, local_orders, discrepancies, repairs) -> None:
        for client_order_id, broker_order in snapshot.orders.items():
            local = local_orders.get(client_order_id)

            if local is None:
                # "Broker has an unknown fill/order -> import/reconstruct".
                # Only safe when it carries OUR stable client order ID
                # (Task 7.4's decision_id), which a trade placed outside
                # this system would not have.
                if self.store.has_processed(client_order_id):
                    repairs.append(
                        f"Imported broker order {client_order_id!r} "
                        f"(known decision, absent from in-memory state)"
                    )
                else:
                    discrepancies.append(
                        Discrepancy(
                            kind="UNKNOWN_BROKER_ORDER",
                            detail=(
                                f"Broker reports order client_order_id={client_order_id!r} "
                                f"({broker_order.get('filled_qty', 0)} filled @ "
                                f"{broker_order.get('avg_fill_price', 0)}) that this system has no "
                                "record of deciding. It may have been placed outside this system -- "
                                "not importing it."
                            ),
                        )
                    )
                continue

            broker_filled = float(broker_order.get("filled_qty", 0.0))

            # "Cumulative fill decreases -> never reverse automatically."
            if broker_filled < local.filled_qty - self.QTY_EPSILON:
                discrepancies.append(
                    Discrepancy(
                        kind="FILL_REGRESSION",
                        detail=(
                            f"Order {client_order_id!r}: broker cumulative filled_qty "
                            f"{broker_filled} is BELOW the locally recorded {local.filled_qty}. "
                            "Not reversing prior accounting automatically."
                        ),
                    )
                )
                continue

            broker_state = broker_order.get("state")
            if broker_filled > local.filled_qty + self.QTY_EPSILON:
                # Unambiguous: a broker-confirmed fill on an order we
                # already know, under a known client order ID.
                if local.state in (OrderState.ACCEPTED, OrderState.PARTIALLY_FILLED, OrderState.SUBMITTED):
                    repairs.append(
                        f"Order {client_order_id!r}: adopted broker-confirmed fill "
                        f"{local.filled_qty} -> {broker_filled}"
                    )
                else:
                    discrepancies.append(
                        Discrepancy(
                            kind="FILL_ON_TERMINAL_ORDER",
                            detail=(
                                f"Order {client_order_id!r} is locally {local.state.value} "
                                f"(terminal) but the broker reports filled_qty {broker_filled} "
                                f"vs local {local.filled_qty}. No safe interpretation."
                            ),
                        )
                    )

            # "Local order absent at broker -> query by client order ID;
            # if unresolved, UNKNOWN/halt" -- an order the broker still
            # reports as live while we think it's terminal is ambiguous.
            if broker_state is not None and local.state in (
                OrderState.FILLED, OrderState.CANCELED, OrderState.REJECTED, OrderState.EXPIRED
            ) and broker_state not in (
                OrderState.FILLED, OrderState.CANCELED, OrderState.REJECTED, OrderState.EXPIRED
            ):
                discrepancies.append(
                    Discrepancy(
                        kind="STALE_TERMINAL_STATE",
                        detail=(
                            f"Order {client_order_id!r} is locally {local.state.value} but the "
                            f"broker still reports it as {getattr(broker_state, 'value', broker_state)}."
                        ),
                    )
                )

        # Local orders the broker has never heard of.
        for client_order_id, local in local_orders.items():
            if client_order_id in snapshot.orders:
                continue
            if local.state in (OrderState.FILLED, OrderState.CANCELED, OrderState.REJECTED, OrderState.EXPIRED):
                continue  # settled and aged out of the broker's window -- expected
            discrepancies.append(
                Discrepancy(
                    kind="ORDER_ABSENT_AT_BROKER",
                    detail=(
                        f"Local order {client_order_id!r} is {local.state.value} but the broker "
                        "has no record of it. Query by client order ID before resubmitting; "
                        "unresolved means UNKNOWN."
                    ),
                )
            )

    def _reconcile_positions(self, snapshot, discrepancies) -> None:
        """"Position quantity mismatch -> RECONCILIATION_REQUIRED; never
        invent a fill." Reuses the store's own comparison so there is
        one definition of a position mismatch, not two."""
        report = self.store.compare_with_broker(snapshot.positions)
        if report.agrees:
            return
        for symbol, sides in report.quantity_mismatches.items():
            discrepancies.append(
                Discrepancy(
                    kind="POSITION_MISMATCH",
                    detail=(
                        f"{symbol}: local open lots total {sides['local']} shares, broker reports "
                        f"{sides['broker']} (delta {sides['broker'] - sides['local']:+}). "
                        "Not inventing a fill to close the gap."
                    ),
                )
            )
        for symbol, qty in report.missing_locally.items():
            discrepancies.append(
                Discrepancy(
                    kind="POSITION_ONLY_AT_BROKER",
                    detail=(
                        f"{symbol}: broker holds {qty} shares this system has no local lot for. "
                        "Possibly traded outside this system -- not importing."
                    ),
                )
            )
        for symbol, qty in report.missing_at_broker.items():
            discrepancies.append(
                Discrepancy(
                    kind="POSITION_ONLY_LOCAL",
                    detail=(
                        f"{symbol}: local records {qty} open shares the broker does not report. "
                        "Not deleting local lots to match."
                    ),
                )
            )

    def _reconcile_cash(self, snapshot, expected_cash, discrepancies) -> None:
        """"Cash mismatch -> RECONCILIATION_REQUIRED; no trading from
        guessed cash." """
        if snapshot.cash is None or expected_cash is None:
            return
        delta = snapshot.cash - expected_cash
        if abs(delta) > self.CASH_EPSILON:
            discrepancies.append(
                Discrepancy(
                    kind="CASH_MISMATCH",
                    detail=(
                        f"Broker cash {snapshot.cash:.2f} vs locally expected {expected_cash:.2f} "
                        f"(delta {delta:+.2f}). Refusing to trade from a guessed cash balance."
                    ),
                )
            )
