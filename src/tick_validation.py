"""
Live tick sanity-checking. Task 7.6 (L7).

src/data_validation.py (Task 2.1) validates the whole historical_data
frame once at OptimizationController.__init__ -- it needs the full
series in hand (monotonic index, duplicate timestamps, pct_change
across all bars) and so cannot validate a stream arriving one tick at
a time. This is the streaming counterpart, reusing that module's
checks in spirit (non-finite, non-positive, implausible move) without
reusing its batch machinery.

Deliberately lightweight, per this task's step 1: a tick check runs on
the hot path of every incoming WebSocket message.

State ownership: TickValidator owns exactly one piece of mutable
state, last_good_price. A rejected tick must NOT update it -- otherwise
a single bad print would poison the reference the next tick is
measured against, and a feed glitch could walk the "known-good" price
arbitrarily far from reality one rejected tick at a time.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("Optimizer")


class TickRejectionReason(str, Enum):
    """Why a tick was rejected.

    Recorded on every rejection so an operator can distinguish a
    malformed feed (NON_FINITE / NON_POSITIVE) from a plausible-looking
    but implausibly large move (IMPLAUSIBLE_MOVE), which have very
    different causes.
    """

    NON_FINITE = "NON_FINITE"
    NON_POSITIVE = "NON_POSITIVE"
    IMPLAUSIBLE_MOVE = "IMPLAUSIBLE_MOVE"


@dataclass(frozen=True)
class TickCheck:
    """Outcome of validating one tick.

    `price` is the parsed value that was examined -- present on
    rejections too, so the offending value can be logged.
    """

    accepted: bool
    price: float
    reason: TickRejectionReason | None = None
    detail: str = ""


class TickValidator:
    """Per-tick streaming validation.

    max_move_pct is the largest single-tick move accepted versus the
    last known-good price. Default 0.20 (20%) is deliberately loose:
    the goal is catching feed glitches and erroneous prints, not
    second-guessing real volatility. TQQQ is 3x-leveraged, so genuine
    intraday moves of several percent are routine and must not be
    rejected as spikes.
    """

    def __init__(self, max_move_pct: float = 0.20, audit_sink=None):
        """Configure the tick validator.

        The 20% default is deliberately loose: TQQQ is 3x-leveraged, so
        genuine multi-percent intraday moves are routine and the goal is
        catching feed glitches, not second-guessing real volatility.
        """
        if not (max_move_pct > 0):
            raise ValueError(f"max_move_pct must be positive, got {max_move_pct}")
        self.max_move_pct = max_move_pct
        self.last_good_price: float | None = None
        # Canonical observability/audit path when one is wired in
        # (Task 7.14); falls back to structured logging otherwise.
        # Either way a rejected tick is never silently dropped.
        self._audit_sink = audit_sink
        self.rejected_count = 0
        self.accepted_count = 0

    def _reject(self, price: float, reason: TickRejectionReason, detail: str) -> TickCheck:
        """Record and report a rejection.

        Critically does NOT advance last_good_price: a bad tick must not
        become the reference the next tick is measured against, or a
        stuck feed could walk the baseline arbitrarily far from reality.
        """
        self.rejected_count += 1
        check = TickCheck(accepted=False, price=price, reason=reason, detail=detail)
        record = {
            "event": "tick_rejected",
            "reason": reason.value,
            "price": price,
            "last_good_price": self.last_good_price,
            "detail": detail,
        }
        if self._audit_sink is not None:
            self._audit_sink(record)
        else:
            logger.warning(
                f"Rejected live tick: reason={reason.value} price={price!r} "
                f"last_good_price={self.last_good_price!r} -- {detail}"
            )
        return check

    def validate(self, price: float) -> TickCheck:
        """Check one incoming tick.

        Returns TickCheck(accepted=False, ...) for a bad tick; the
        caller must not evaluate strategy or submit orders on it.
        last_good_price is advanced only on acceptance.
        """
        try:
            price = float(price)
        except (TypeError, ValueError):
            return self._reject(price, TickRejectionReason.NON_FINITE, "price is not a number")

        if not math.isfinite(price):
            return self._reject(price, TickRejectionReason.NON_FINITE, "price is NaN or infinite")

        if price <= 0:
            return self._reject(price, TickRejectionReason.NON_POSITIVE, "price must be positive")

        if self.last_good_price is not None:
            move = abs(price - self.last_good_price) / self.last_good_price
            if move > self.max_move_pct:
                return self._reject(
                    price,
                    TickRejectionReason.IMPLAUSIBLE_MOVE,
                    f"single-tick move {move:.2%} exceeds the {self.max_move_pct:.2%} limit",
                )

        # Accepted: this is now the reference for the next tick.
        self.last_good_price = price
        self.accepted_count += 1
        return TickCheck(accepted=True, price=price)
