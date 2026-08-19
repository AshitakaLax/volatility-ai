"""
Task 7.7 acceptance tests (L8).

Acceptance criterion: the documented promotion path requires a
paper-trading period between "passed backtest" and "live capital
enabled" -- no code path exists that goes directly from a backtest
result to live capital.

That criterion is enforced structurally here, not just documented:
constructing a real-capital OrderManagementSystem requires a passing
PromotionEvaluation, which in turn requires an actual
PaperTradingRecord meeting every recorded threshold.
"""

import json

import pytest

from src.artifacts import DeploymentArtifact
from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.live_execution import LiveExecutionLoop
from src.order_management_system import NON_CAPITAL_MODES, Mode, OrderManagementSystem
from src.promotion import (
    PROMOTION_STAGES,
    PaperTradingRecord,
    PromotionCriteria,
    assert_promotable_to_live,
    evaluate_promotion,
)
from src.secrets import API_KEY_ID_ENV_VAR, API_SECRET_KEY_ENV_VAR
from src.size_calculators import FixedPortfolioPercentage


def _good_record(**overrides) -> PaperTradingRecord:
    base = dict(
        deployment_id="d1",
        paper_trading_days=10.0,
        decision_count=50,
        fill_count=10,
        accounting_discrepancies=0,
        duplicate_order_incidents=0,
        no_loss_violations=0,
        unresolved_reconciliations=0,
        unhandled_exceptions=0,
    )
    base.update(overrides)
    return PaperTradingRecord(**base)


def _config(paper_trading=True, live_enabled=True):
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "live": {"enabled": live_enabled, "paper_trading": paper_trading},
        }
    )


def _artifact(deployment_id="d1", **overrides):
    base = dict(
        deployment_id=deployment_id,
        strategy_id="fixed",
        strategy_version="1.0.0",
        code_commit="abc",
        config=_config(),
        dataset_id="TQQQ",
        dataset_hash="h",
        experiment_id="e1",
        created_at="2024-01-01T00:00:00+00:00",
    )
    base.update(overrides)
    return DeploymentArtifact.create(**base)


def test_live_capital_oms_cannot_be_constructed_without_promotion_evidence():
    with pytest.raises(ConfigurationError, match="paper-trading"):
        OrderManagementSystem(mode=Mode.LIVE)


def test_no_boolean_shortcut_enables_live_capital():
    # A truthy-but-not-passing object must not slip through.
    class _FakeEvidence:
        passed = False
        failures = ("nothing was actually checked",)

    with pytest.raises(ConfigurationError, match="did not pass"):
        OrderManagementSystem(mode=Mode.LIVE, live_capital_promotion=_FakeEvidence())


def test_promotion_requires_an_actual_paper_trading_record():
    with pytest.raises(ConfigurationError, match="directly from backtest"):
        assert_promotable_to_live(_artifact(), record=None)


def test_live_capital_reachable_only_after_a_passing_paper_stage():
    evaluation = evaluate_promotion(_good_record())
    assert evaluation.passed
    oms = OrderManagementSystem(mode=Mode.LIVE, live_capital_promotion=evaluation)
    assert oms.mode == Mode.LIVE
    assert oms.live_capital_promotion is evaluation


def test_paper_and_simulation_never_require_promotion_evidence():
    for mode in NON_CAPITAL_MODES:
        oms = OrderManagementSystem(mode=mode)
        assert oms.mode == mode


def test_promotion_stages_place_candidate_before_promoted():
    assert PROMOTION_STAGES == ("draft", "candidate", "promoted")
    assert PROMOTION_STAGES.index("candidate") < PROMOTION_STAGES.index("promoted")


def test_a_fully_clean_record_passes():
    assert evaluate_promotion(_good_record()).passed


@pytest.mark.parametrize(
    "overrides,expected_fragment",
    [
        ({"paper_trading_days": 1.0}, "paper_trading_days"),
        ({"decision_count": 3}, "decision_count"),
        ({"fill_count": 1}, "fill_count"),
        ({"accounting_discrepancies": 1}, "accounting discrepancies"),
        ({"duplicate_order_incidents": 1}, "duplicate-order incidents"),
        ({"no_loss_violations": 1}, "no-loss guard violations"),
        ({"unresolved_reconciliations": 1}, "unresolved reconciliations"),
        ({"unhandled_exceptions": 1}, "unhandled runtime exceptions"),
    ],
)
def test_each_required_criterion_blocks_promotion_individually(overrides, expected_fragment):
    evaluation = evaluate_promotion(_good_record(**overrides))
    assert not evaluation.passed
    assert any(expected_fragment in f for f in evaluation.failures), evaluation.failures
    with pytest.raises(ConfigurationError):
        evaluation.raise_if_failed()


def test_all_unmet_criteria_are_reported_not_just_the_first():
    evaluation = evaluate_promotion(
        _good_record(paper_trading_days=1.0, decision_count=1, no_loss_violations=3)
    )
    assert not evaluation.passed
    assert len(evaluation.failures) >= 3, evaluation.failures


def test_boundary_exactly_meeting_a_threshold_passes():
    criteria = PromotionCriteria(min_paper_trading_days=5.0, min_decisions=20, min_fills=5)
    exact = _good_record(paper_trading_days=5.0, decision_count=20, fill_count=5)
    assert evaluate_promotion(exact, criteria).passed


def test_boundary_just_below_a_threshold_fails():
    criteria = PromotionCriteria(min_paper_trading_days=5.0)
    assert not evaluate_promotion(_good_record(paper_trading_days=4.99), criteria).passed


def test_criteria_are_recorded_in_the_evaluation_for_the_artifact():
    criteria = PromotionCriteria(min_paper_trading_days=7.0, min_decisions=30, min_fills=8)
    evaluation = evaluate_promotion(_good_record(), criteria)
    assert evaluation.criteria["min_paper_trading_days"] == 7.0
    assert evaluation.criteria["min_decisions"] == 30
    assert evaluation.criteria["min_fills"] == 8
    # And the observed record travels with it, so the pass is auditable.
    assert evaluation.record["paper_trading_days"] == 10.0


def test_recorded_criteria_are_json_serializable_for_the_artifact():
    evaluation = evaluate_promotion(_good_record())
    json.dumps(evaluation.criteria)  # must not raise
    json.dumps(evaluation.record)


def test_paper_record_metrics_mirror_simulation_result_shape():
    # Step 2: paper results tracked the same way SimulationResult
    # tracks backtest results, so the two are directly comparable.
    record = _good_record(metrics={"Final Equity": 101_000.0, "Capital Velocity Index": 1.0})
    assert "Final Equity" in record.metrics
    assert "Capital Velocity Index" in record.metrics


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_paper_trading_days": 0},
        {"min_paper_trading_days": -1},
        {"min_decisions": 0},
        {"min_fills": 0},
        {"max_no_loss_violations": -1},
    ],
)
def test_a_meaningless_gate_configuration_is_rejected(kwargs):
    with pytest.raises(ConfigurationError):
        PromotionCriteria(**kwargs)


def test_a_record_for_a_different_deployment_is_refused():
    with pytest.raises(ConfigurationError, match="another deployment"):
        assert_promotable_to_live(_artifact("d1"), _good_record(deployment_id="d2"))


def test_assert_promotable_returns_the_evaluation_on_success():
    evaluation = assert_promotable_to_live(_artifact("d1"), _good_record())
    assert evaluation.passed


def test_live_loop_defaults_to_paper_mode(monkeypatch):
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    loop = LiveExecutionLoop(
        _config(paper_trading=True), FixedPortfolioPercentage(allocation_pct=0.05)
    )
    assert loop.oms.mode == Mode.PAPER, "paper_trading=True must not build a real-capital OMS"


def test_live_loop_with_paper_trading_false_still_needs_promotion_evidence(monkeypatch):
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    with pytest.raises(ConfigurationError, match="paper-trading"):
        LiveExecutionLoop(
            _config(paper_trading=False), FixedPortfolioPercentage(allocation_pct=0.05)
        )


def test_live_loop_reaches_live_capital_only_with_passing_evidence(monkeypatch):
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    evaluation = evaluate_promotion(_good_record())
    loop = LiveExecutionLoop(
        _config(paper_trading=False),
        FixedPortfolioPercentage(allocation_pct=0.05),
        live_capital_promotion=evaluation,
    )
    assert loop.oms.mode == Mode.LIVE
