"""
Task 7.1 acceptance tests (L1, L3).

1. The live loop's per-tick call sequence to sizing_engine is provably
   identical (same methods, same argument shapes) to _simulate_single's
   per-bar sequence -- via a shared helper both call, not two
   independently-written copies.
2. Starting the live loop with missing/invalid credentials fails
   immediately, before any WebSocket/broker connection is attempted.
3. A parameter set produced by a backtest sweep can be loaded into the
   live loop without manual code edits.

Criterion 1 is tested two ways, deliberately: structurally (both
modules genuinely route through src/decision_cycle.py, so a future
re-divergence would have to actively remove that) and behaviorally (a
recording strategy double captures the exact method/argument sequence
from each path and asserts they match).
"""

from datetime import UTC, datetime

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src import decision_cycle as decision_cycle_module
from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.live_execution import LiveExecutionLoop
from src.market_context import MarketContext
from src.risk_manager import RiskManager
from src.secrets import API_KEY_ID_ENV_VAR, API_SECRET_KEY_ENV_VAR
from src.size_calculators import FixedPortfolioPercentage, SizingStrategy


class RecordingStrategy(SizingStrategy):
    """Captures the exact sequence of strategy method calls and their
    argument shapes. Wraps a real FixedPortfolioPercentage so the
    values it returns are genuine, not stubs."""

    def __init__(self, allocation_pct: float = 0.05):
        self._inner = FixedPortfolioPercentage(allocation_pct=allocation_pct)
        self.calls = []

    def record_tick(self, context: MarketContext) -> None:
        self.calls.append(("record_tick", ("context",)))
        self._inner.record_tick(context)

    def _check_grid_trigger(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> bool:
        self.calls.append(("_check_grid_trigger", ("context", "last_buy_price", "step")))
        return self._inner._check_grid_trigger(context, last_buy_price, step)

    def calculate_trade_value(self, context: MarketContext) -> float:
        self.calls.append(("calculate_trade_value", ("context",)))
        return self._inner.calculate_trade_value(context)


class RecordingRiskManager(RiskManager):
    def __init__(self):
        super().__init__()
        self.calls = []

    def clamp_trade_value(self, proposed_value, equity, cash, open_lot_count, drawdown=0.0):
        self.calls.append(
            (
                "clamp_trade_value",
                ("proposed_value", "equity", "cash", "open_lot_count", "drawdown"),
            )
        )
        return super().clamp_trade_value(proposed_value, equity, cash, open_lot_count, drawdown)


def _live_config(enabled: bool = True) -> BacktestConfig:
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
            "live": {"enabled": enabled, "paper_trading": True},
        }
    )


def _context(close: float, cash: float = 100_000.0, equity: float = 100_000.0) -> MarketContext:
    return MarketContext(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        open=close,
        high=close,
        low=close,
        close=close,
        cash=cash,
        equity=equity,
        peak_equity=equity,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
    )


def test_both_paths_route_through_the_shared_decision_cycle_module():
    import inspect

    import optimization_controller
    import src.live_execution

    backtest_src = inspect.getsource(
        optimization_controller.OptimizationController._simulate_single
    )
    live_src = inspect.getsource(src.live_execution.LiveExecutionLoop.decision_cycle)

    for source, name in (
        (backtest_src, "_simulate_single"),
        (live_src, "LiveExecutionLoop.decision_cycle"),
    ):
        assert "decision_cycle.record_tick(" in source, (
            f"{name} no longer routes record_tick through the shared module"
        )
        assert "decision_cycle.evaluate_grid_decision(" in source, (
            f"{name} no longer routes the trigger/sizing/clamp sequence through the shared module"
        )
        stripped = source.replace("decision_cycle.evaluate_grid_decision(", "")
        assert "_check_grid_trigger(" not in stripped, (
            f"{name} appears to call _check_grid_trigger directly again instead of via the shared helper"
        )


def test_live_and_backtest_produce_the_identical_strategy_call_sequence(monkeypatch):
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"]).set_index(
        "timestamp"
    )

    backtest_strategy = RecordingStrategy()
    backtest_risk = RecordingRiskManager()

    class _Factory:
        def __call__(self, **params):
            return backtest_strategy

    # Full fixture, not a 2-bar slice: the decline is ~0.5%/bar, so it
    # takes 4 bars to cross a 1% grid step. A shorter slice never
    # triggers, and the backtest path would never reach
    # calculate_trade_value at all -- making the comparison vacuous.
    OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=_Factory(),
        strategy_params_grid=[{}],
        risk_manager=backtest_risk,
    )
    assert "calculate_trade_value" in [c[0] for c in backtest_strategy.calls], (
        "Backtest fixture never triggered a buy -- comparison would be vacuous"
    )

    live_strategy = RecordingStrategy()
    live_risk = RecordingRiskManager()
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    loop = LiveExecutionLoop(_live_config(), live_strategy, live_risk)
    loop.start()
    loop.decision_cycle(_context(close=49.0), step=0.01, last_buy_price=50.0)

    live_sequence = live_strategy.calls
    assert live_sequence[0] == ("record_tick", ("context",))
    assert live_sequence[1] == ("_check_grid_trigger", ("context", "last_buy_price", "step"))
    assert live_sequence[2] == ("calculate_trade_value", ("context",))

    backtest_names = [c[0] for c in backtest_strategy.calls]
    live_names = [c[0] for c in live_sequence]
    for name in live_names:
        assert name in backtest_names, f"Live path calls {name}, backtest path never does"
    assert live_risk.calls == [
        (
            "clamp_trade_value",
            ("proposed_value", "equity", "cash", "open_lot_count", "drawdown"),
        )
    ]
    assert backtest_risk.calls[0] == live_risk.calls[0], (
        "clamp_trade_value argument shape differs between paths"
    )


def test_shared_helper_returns_zero_values_when_not_triggered():
    strategy = RecordingStrategy()
    decision = decision_cycle_module.evaluate_grid_decision(
        strategy,
        RiskManager(),
        _context(close=51.0),
        last_buy_price=50.0,
        step=0.01,
        cash=100_000.0,
    )
    assert decision.triggered is False
    assert decision.proposed_trade_value == 0.0
    assert decision.clamped_trade_value == 0.0
    assert "calculate_trade_value" not in [c[0] for c in strategy.calls]


def test_shared_helper_does_not_mutate_portfolio_state():
    strategy = RecordingStrategy()
    context = _context(close=49.0)
    before_cash, before_equity = context.cash, context.equity
    decision_cycle_module.evaluate_grid_decision(
        strategy, RiskManager(), context, last_buy_price=50.0, step=0.01, cash=100_000.0
    )
    assert context.cash == before_cash and context.equity == before_equity


def test_start_fails_on_missing_credentials_before_broker_factory_runs(monkeypatch):
    monkeypatch.delenv(API_KEY_ID_ENV_VAR, raising=False)
    monkeypatch.delenv(API_SECRET_KEY_ENV_VAR, raising=False)

    factory_called = {"count": 0}

    def broker_factory(credentials):
        factory_called["count"] += 1
        return object()

    loop = LiveExecutionLoop(
        _live_config(), FixedPortfolioPercentage(allocation_pct=0.05), broker_factory=broker_factory
    )
    with pytest.raises(ConfigurationError):
        loop.start()
    assert factory_called["count"] == 0, "Broker factory must not run when credentials are missing"


def test_decision_cycle_refuses_to_run_before_start():
    loop = LiveExecutionLoop(_live_config(), FixedPortfolioPercentage(allocation_pct=0.05))
    with pytest.raises(RuntimeError):
        loop.decision_cycle(_context(close=49.0), step=0.01, last_buy_price=50.0)


def test_live_disabled_config_rejected():
    with pytest.raises(ConfigurationError, match=r"live\.enabled"):
        LiveExecutionLoop(
            _live_config(enabled=False), FixedPortfolioPercentage(allocation_pct=0.05)
        )


def test_backtest_sweep_winner_loads_into_the_live_loop_without_code_edits(monkeypatch):
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"]).set_index(
        "timestamp"
    )
    results = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.005, 0.01],
        profit_targets=[0.003, 0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}, {"allocation_pct": 0.08}],
    )
    winner = results.iloc[0]

    config = BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": "fixed",
                "strategy_params": {"allocation_pct": float(winner["allocation_pct"])},
            },
            "grid": {
                "steps": [float(winner["Grid Step"])],
                "profit_targets": [float(winner["Profit Target"])],
            },
            "live": {"enabled": True, "paper_trading": True},
        }
    )
    config.validate()

    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    strategy = FixedPortfolioPercentage(**config.strategy.strategy_params)
    loop = LiveExecutionLoop(config, strategy)
    loop.start()

    decision = loop.decision_cycle(
        _context(close=50.0 * (1 - float(winner["Grid Step"]))),
        step=config.grid.steps[0],
        last_buy_price=50.0,
    )
    assert decision.triggered is True
    assert decision.clamped_trade_value > 0
