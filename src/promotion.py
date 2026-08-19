"""
Paper-trading promotion gate. Task 7.7 (L8).

Nothing previously required a parameter set to prove itself against
real-time-but-risk-free execution before real capital was committed.
This module makes the paper-trading stage a machine-checkable gate
rather than an operator's judgement call.

Promotion criteria contract (implementation_task_specs.md Task 7.7):
thresholds must be explicit, machine-checkable, and RECORDED IN THE
PROMOTION ARTIFACT rather than inferred from operator judgment. Hence
PromotionCriteria is serialized into the artifact via to_dict(), so
the bar a deployment cleared is auditable after the fact -- not just
the fact that someone said it cleared.

All seven required criteria are enforced:
  1. minimum paper-trading duration
  2. minimum number of strategy decisions/fills
  3. zero accounting discrepancies
  4. zero duplicate-order incidents
  5. zero no-loss guard violations
  6. no unresolved reconciliation state
  7. no unhandled runtime exceptions

Comparability (step 2): PaperTradingRecord carries a `metrics` dict
with the same shape SimulationResult.metrics uses (Task 4.6), so a
paper run and a backtest run can be diffed directly rather than
through two incompatible report formats.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from src.exceptions import ConfigurationError

# The lifecycle a parameter set must walk. Index order IS the required
# order -- promotion may not skip a stage.
PROMOTION_STAGES = ("draft", "candidate", "promoted")


@dataclass(frozen=True)
class PromotionCriteria:
    """Explicit, machine-checkable promotion thresholds."""

    min_paper_trading_days: float = 5.0
    min_decisions: int = 20
    min_fills: int = 5
    max_accounting_discrepancies: int = 0
    max_duplicate_order_incidents: int = 0
    max_no_loss_violations: int = 0
    max_unresolved_reconciliations: int = 0
    max_unhandled_exceptions: int = 0

    def __post_init__(self):
        if self.min_paper_trading_days <= 0:
            raise ConfigurationError(
                f"min_paper_trading_days must be positive, got {self.min_paper_trading_days} -- "
                "a zero-length paper stage is not a gate."
            )
        if self.min_decisions <= 0 or self.min_fills <= 0:
            raise ConfigurationError(
                "min_decisions and min_fills must both be positive -- a gate requiring zero "
                "activity would pass a strategy that never actually traded."
            )
        for name in (
            "max_accounting_discrepancies", "max_duplicate_order_incidents",
            "max_no_loss_violations", "max_unresolved_reconciliations", "max_unhandled_exceptions",
        ):
            if getattr(self, name) < 0:
                raise ConfigurationError(f"{name} must be >= 0, got {getattr(self, name)}")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PaperTradingRecord:
    """Observed results of a paper-trading run.

    `metrics` mirrors SimulationResult.metrics (Task 4.6) so paper and
    backtest results are directly comparable.
    """

    deployment_id: str
    paper_trading_days: float
    decision_count: int
    fill_count: int
    accounting_discrepancies: int = 0
    duplicate_order_incidents: int = 0
    no_loss_violations: int = 0
    unresolved_reconciliations: int = 0
    unhandled_exceptions: int = 0
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PromotionEvaluation:
    passed: bool
    failures: tuple
    criteria: dict
    record: dict

    def raise_if_failed(self) -> None:
        if not self.passed:
            raise ConfigurationError(
                "Paper-trading promotion gate FAILED -- live capital must not be enabled. "
                f"Unmet criteria: {list(self.failures)}"
            )


def evaluate_promotion(record: PaperTradingRecord, criteria: PromotionCriteria = None) -> PromotionEvaluation:
    """Check a paper-trading record against the promotion criteria.

    Returns every unmet criterion rather than short-circuiting on the
    first, so an operator sees the full picture in one pass instead of
    fixing and re-running repeatedly.
    """
    criteria = criteria or PromotionCriteria()
    failures = []

    if record.paper_trading_days < criteria.min_paper_trading_days:
        failures.append(
            f"paper_trading_days {record.paper_trading_days} < required {criteria.min_paper_trading_days}"
        )
    if record.decision_count < criteria.min_decisions:
        failures.append(f"decision_count {record.decision_count} < required {criteria.min_decisions}")
    if record.fill_count < criteria.min_fills:
        failures.append(f"fill_count {record.fill_count} < required {criteria.min_fills}")

    for observed_name, limit_name, label in (
        ("accounting_discrepancies", "max_accounting_discrepancies", "accounting discrepancies"),
        ("duplicate_order_incidents", "max_duplicate_order_incidents", "duplicate-order incidents"),
        ("no_loss_violations", "max_no_loss_violations", "no-loss guard violations"),
        ("unresolved_reconciliations", "max_unresolved_reconciliations", "unresolved reconciliations"),
        ("unhandled_exceptions", "max_unhandled_exceptions", "unhandled runtime exceptions"),
    ):
        observed = getattr(record, observed_name)
        limit = getattr(criteria, limit_name)
        if observed > limit:
            failures.append(f"{label}: {observed} exceeds the allowed maximum of {limit}")

    return PromotionEvaluation(
        passed=not failures,
        failures=tuple(failures),
        criteria=criteria.to_dict(),
        record=record.to_dict(),
    )


def assert_promotable_to_live(
    artifact, record: Optional[PaperTradingRecord], criteria: PromotionCriteria = None
) -> PromotionEvaluation:
    """The gate itself: a deployment may only reach live capital by
    passing through a paper-trading stage.

    Rejects, in order:
      - a missing paper-trading record entirely (the "straight from
        backtest to live" path this task exists to eliminate)
      - a record for a different deployment
      - a record that fails any promotion criterion

    Does NOT itself flip promotion_status -- DeploymentArtifact is
    frozen (Task 6.3), so the caller constructs the promoted artifact,
    embedding evaluation.criteria as the recorded threshold set.
    """
    if record is None:
        raise ConfigurationError(
            "Live-capital promotion requires a paper-trading record; none was provided. "
            "A parameter set may not go directly from backtest results to live capital."
        )
    if artifact is not None and record.deployment_id != artifact.deployment_id:
        raise ConfigurationError(
            f"Paper-trading record is for deployment {record.deployment_id!r} but the artifact "
            f"is {artifact.deployment_id!r} -- refusing to promote on another deployment's evidence."
        )
    evaluation = evaluate_promotion(record, criteria)
    evaluation.raise_if_failed()
    return evaluation
