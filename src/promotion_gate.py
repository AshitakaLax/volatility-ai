"""Machine-checkable paper-trading promotion gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.exceptions import ConfigurationError


@dataclass(frozen=True)
class PaperTradingResult:
    """Comparable paper-trading summary for promotion decisions."""

    started_at: datetime
    ended_at: datetime
    strategy_decisions: int
    fills: int
    accounting_discrepancies: int
    duplicate_order_incidents: int
    no_loss_guard_violations: int
    unresolved_reconciliation: bool
    unhandled_runtime_exceptions: int

    @property
    def duration_seconds(self) -> float:
        return (self.ended_at - self.started_at).total_seconds()


@dataclass(frozen=True)
class PromotionCriteria:
    minimum_paper_trading_seconds: float
    minimum_decisions: int
    minimum_fills: int
    maximum_accounting_discrepancies: int = 0
    maximum_duplicate_order_incidents: int = 0
    maximum_no_loss_guard_violations: int = 0
    maximum_unhandled_runtime_exceptions: int = 0


class PromotionGate:
    """Require explicit, recorded paper-trading evidence before live capital."""

    def __init__(self, criteria: PromotionCriteria) -> None:
        if criteria.minimum_paper_trading_seconds <= 0:
            raise ConfigurationError("minimum paper-trading duration must be positive")
        if criteria.minimum_decisions < 0 or criteria.minimum_fills < 0:
            raise ConfigurationError("minimum decisions/fills cannot be negative")
        self.criteria = criteria
        self._passed = False
        self.last_result: PaperTradingResult | None = None
        self.promotion_id: str | None = None

    def evaluate(self, result: PaperTradingResult, *, promotion_id: str) -> bool:
        if not promotion_id:
            raise ConfigurationError("promotion_id is required")
        if result.ended_at.tzinfo is None or result.started_at.tzinfo is None:
            raise ConfigurationError("paper-trading timestamps must be timezone-aware")
        if result.ended_at < result.started_at:
            raise ConfigurationError("paper-trading end must not precede start")
        c = self.criteria
        self.last_result = result
        self.promotion_id = promotion_id
        self._passed = (
            result.duration_seconds >= c.minimum_paper_trading_seconds
            and result.strategy_decisions >= c.minimum_decisions
            and result.fills >= c.minimum_fills
            and result.accounting_discrepancies <= c.maximum_accounting_discrepancies
            and result.duplicate_order_incidents <= c.maximum_duplicate_order_incidents
            and result.no_loss_guard_violations <= c.maximum_no_loss_guard_violations
            and not result.unresolved_reconciliation
            and result.unhandled_runtime_exceptions <= c.maximum_unhandled_runtime_exceptions
        )
        return self._passed

    @property
    def passed(self) -> bool:
        return self._passed

    def require_live_promotion(self) -> None:
        if not self._passed or not self.promotion_id or self.last_result is None:
            raise ConfigurationError("live capital promotion requires a passed paper-trading gate")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
