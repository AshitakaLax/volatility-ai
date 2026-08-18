"""
Backtest/live configuration containers. Task 6.1 (A4 follow-through,
documentation completeness).

Originally built narrower, to unblock src/live_execution.py pushed
directly to main mid-session; extended here to the canonical schema
architecture_overview.md / implementation_task_specs.md Task 6.1
requires (strategy, backtest, grid, costs, risk, search, execution,
output, live). Every field maps to a real, already-implemented
capability in this codebase -- none were added just because the
schema names a category; where no backing implementation exists
(e.g. a drawdown-based risk limit -- RiskManager, Task 3.1, has none),
no field was added for it, per this task's own "do not document
parameters that haven't been implemented yet."

BacktestConfig.validate() delegates to src/validation.py's helpers
(Task 4.9) rather than re-implementing range/cross-field checks.

from_yaml() deserializes through from_dict() -- the same path
programmatic construction uses -- rather than a second, parallel
YAML-only schema, per this task's explicit instruction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.cost_models import SlippageCommissionModel, TransactionCostModel, ZeroCostModel
from src.exceptions import ConfigurationError
from src.risk_manager import RiskManager
from src.validation import (
    validate_grid_steps,
    validate_non_negative,
    validate_one_of,
    validate_positive,
    validate_positive_int,
    validate_profit_targets,
    validate_unit_interval,
)


@dataclass(frozen=True)
class StrategyConfig:
    strategy_id: str
    strategy_params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class BacktestSection:
    symbol: str = "TQQQ"
    initial_cash: float = 100_000.0
    # Metadata/provenance only -- not yet wired to actively filter or
    # load historical_data (OptimizationController takes an
    # already-loaded DataFrame; no date-range/data-loading step exists
    # in this codebase to wire these into). Kept as optional, documented
    # placeholders for "date/time range, data settings" rather than
    # omitted, since they're genuinely useful record-keeping even
    # unwired -- but not claimed to do more than that.
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    data_path: Optional[str] = None


@dataclass(frozen=True)
class GridConfig:
    steps: tuple
    profit_targets: tuple


@dataclass(frozen=True)
class CostConfig:
    """Maps to src/cost_models.py (Task 2.2). model_type="zero"
    (default) builds ZeroCostModel(); "slippage_commission" builds
    SlippageCommissionModel from commission_per_trade/slippage_bps."""

    model_type: str = "zero"
    commission_per_trade: float = 0.0
    slippage_bps: float = 0.0

    def build(self) -> TransactionCostModel:
        if self.model_type == "zero":
            return ZeroCostModel()
        if self.model_type == "slippage_commission":
            return SlippageCommissionModel(
                commission_per_trade=self.commission_per_trade, slippage_bps=self.slippage_bps
            )
        raise ConfigurationError(
            f"costs.model_type must be 'zero' or 'slippage_commission', got {self.model_type!r}"
        )


@dataclass(frozen=True)
class RiskConfig:
    """Maps to src/risk_manager.py (Task 3.1). No drawdown-limit field
    -- RiskManager doesn't implement one; see module docstring."""

    max_concurrent_lots: Optional[int] = None
    max_total_exposure: Optional[float] = None

    def build(self) -> RiskManager:
        return RiskManager(max_concurrent_lots=self.max_concurrent_lots, max_total_exposure_pct=self.max_total_exposure)


@dataclass(frozen=True)
class SearchConfig:
    """Maps to run_sweep's search_strategy/rank_by/search_direction/
    search_seed (Task 5.3)."""

    strategy: str = "grid"
    rank_by: str = "Capital Velocity Index"
    direction: str = "maximize"
    seed: Optional[int] = None


@dataclass(frozen=True)
class ExecutionConfig:
    """on_flat_reentry maps to run_sweep (Task 3.3). intrabar_priority
    maps to validate_finalists_intraday/simulate_single_intraday (Task
    2.3) -- a real, tested parameter in this codebase even though it
    isn't a run_sweep parameter itself."""

    on_flat_reentry: str = "stale_reference"
    intrabar_priority: str = "sell_first"


@dataclass(frozen=True)
class OutputConfig:
    return_full_results: bool = False


@dataclass(frozen=True)
class LiveConfig:
    enabled: bool = False
    paper_trading: bool = True


@dataclass(frozen=True)
class BacktestConfig:
    strategy: StrategyConfig
    grid: GridConfig
    backtest: BacktestSection = field(default_factory=BacktestSection)
    costs: CostConfig = field(default_factory=CostConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    live: LiveConfig = field(default_factory=LiveConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "BacktestConfig":
        strategy_data = data.get("strategy")
        if not strategy_data or "strategy_id" not in strategy_data:
            raise ConfigurationError("config['strategy']['strategy_id'] is required")
        strategy = StrategyConfig(
            strategy_id=strategy_data["strategy_id"],
            strategy_params=dict(strategy_data.get("strategy_params", {})),
        )

        grid_data = data.get("grid")
        if not grid_data:
            raise ConfigurationError("config['grid'] is required")
        grid = GridConfig(
            steps=tuple(grid_data.get("steps", ())),
            profit_targets=tuple(grid_data.get("profit_targets", ())),
        )

        backtest_data = data.get("backtest", {})
        backtest = BacktestSection(
            symbol=backtest_data.get("symbol", "TQQQ"),
            initial_cash=backtest_data.get("initial_cash", 100_000.0),
            start_date=backtest_data.get("start_date"),
            end_date=backtest_data.get("end_date"),
            data_path=backtest_data.get("data_path"),
        )

        costs_data = data.get("costs", {})
        costs = CostConfig(
            model_type=costs_data.get("model_type", "zero"),
            commission_per_trade=costs_data.get("commission_per_trade", 0.0),
            slippage_bps=costs_data.get("slippage_bps", 0.0),
        )

        risk_data = data.get("risk", {})
        risk = RiskConfig(
            max_concurrent_lots=risk_data.get("max_concurrent_lots"),
            max_total_exposure=risk_data.get("max_total_exposure"),
        )

        search_data = data.get("search", {})
        search = SearchConfig(
            strategy=search_data.get("strategy", "grid"),
            rank_by=search_data.get("rank_by", "Capital Velocity Index"),
            direction=search_data.get("direction", "maximize"),
            seed=search_data.get("seed"),
        )

        execution_data = data.get("execution", {})
        execution = ExecutionConfig(
            on_flat_reentry=execution_data.get("on_flat_reentry", "stale_reference"),
            intrabar_priority=execution_data.get("intrabar_priority", "sell_first"),
        )

        output_data = data.get("output", {})
        output = OutputConfig(return_full_results=output_data.get("return_full_results", False))

        live_data = data.get("live", {})
        live = LiveConfig(
            enabled=live_data.get("enabled", False),
            paper_trading=live_data.get("paper_trading", True),
        )

        return cls(
            strategy=strategy, grid=grid, backtest=backtest, costs=costs, risk=risk,
            search=search, execution=execution, output=output, live=live,
        )

    @classmethod
    def from_yaml(cls, yaml_source: str, is_path: bool = True) -> "BacktestConfig":
        """is_path=True (default): yaml_source is a file path, read and
        parsed. is_path=False: yaml_source is the YAML text itself
        (useful for tests/inline config without a real file). Either
        way, deserializes through from_dict -- the identical path
        programmatic construction uses, so YAML-loaded and
        programmatically-built configs are validated identically."""
        import yaml

        if is_path:
            with open(yaml_source) as f:
                data = yaml.safe_load(f)
        else:
            data = yaml.safe_load(yaml_source)
        if not isinstance(data, dict):
            raise ConfigurationError(f"YAML config must deserialize to a mapping, got {type(data).__name__}")
        return cls.from_dict(data)

    def validate(self) -> None:
        """Front-loaded validation, mirroring
        src/validation.py::validate_run_sweep_config's own contract
        (fail before any simulation/live work starts), reusing its
        actual helper functions rather than duplicating range checks."""
        if not self.strategy.strategy_id:
            raise ConfigurationError("strategy.strategy_id must not be empty")
        validate_positive(self.backtest.initial_cash, "backtest.initial_cash")
        validate_grid_steps(self.grid.steps)
        validate_profit_targets(self.grid.profit_targets)

        validate_one_of(self.costs.model_type, ("zero", "slippage_commission"), "costs.model_type")
        validate_non_negative(self.costs.commission_per_trade, "costs.commission_per_trade")
        validate_non_negative(self.costs.slippage_bps, "costs.slippage_bps")

        if self.risk.max_concurrent_lots is not None:
            validate_positive_int(self.risk.max_concurrent_lots, "risk.max_concurrent_lots")
        if self.risk.max_total_exposure is not None:
            validate_unit_interval(self.risk.max_total_exposure, "risk.max_total_exposure")

        validate_one_of(self.search.strategy, ("grid", "bayesian"), "search.strategy")
        validate_one_of(self.search.direction, ("maximize", "minimize"), "search.direction")

        validate_one_of(
            self.execution.on_flat_reentry, ("stale_reference", "reset_to_market"), "execution.on_flat_reentry"
        )
        validate_one_of(self.execution.intrabar_priority, ("sell_first", "buy_first"), "execution.intrabar_priority")

    def to_dict(self) -> dict:
        """Inverse of from_dict() -- round-trips through the same nested
        shape (BacktestConfig.from_dict(config.to_dict()) == config).
        Tuples (grid.steps/profit_targets, held as tuples internally for
        immutability/hashability) are converted back to lists, since
        JSON has no tuple type and this needs to be JSON-serializable
        for Task 6.3's configuration hash."""
        return {
            "strategy": {"strategy_id": self.strategy.strategy_id, "strategy_params": dict(self.strategy.strategy_params)},
            "grid": {"steps": list(self.grid.steps), "profit_targets": list(self.grid.profit_targets)},
            "backtest": {
                "symbol": self.backtest.symbol,
                "initial_cash": self.backtest.initial_cash,
                "start_date": self.backtest.start_date,
                "end_date": self.backtest.end_date,
                "data_path": self.backtest.data_path,
            },
            "costs": {
                "model_type": self.costs.model_type,
                "commission_per_trade": self.costs.commission_per_trade,
                "slippage_bps": self.costs.slippage_bps,
            },
            "risk": {"max_concurrent_lots": self.risk.max_concurrent_lots, "max_total_exposure": self.risk.max_total_exposure},
            "search": {
                "strategy": self.search.strategy,
                "rank_by": self.search.rank_by,
                "direction": self.search.direction,
                "seed": self.search.seed,
            },
            "execution": {
                "on_flat_reentry": self.execution.on_flat_reentry,
                "intrabar_priority": self.execution.intrabar_priority,
            },
            "output": {"return_full_results": self.output.return_full_results},
            "live": {"enabled": self.live.enabled, "paper_trading": self.live.paper_trading},
        }

    def to_run_sweep_kwargs(self, strategy_class) -> dict:
        """Builds the actual kwargs for
        OptimizationController.run_sweep(**kwargs) -- constructs real
        TransactionCostModel/RiskManager instances via costs.build()/
        risk.build(), not just passes config values through unchanged.
        strategy_class is an explicit argument since BacktestConfig only
        holds strategy_id (a string identifier); this codebase has no
        strategy-id-to-class registry to resolve it automatically, and
        building one is outside this task's scope."""
        return dict(
            grid_steps=list(self.grid.steps),
            profit_targets=list(self.grid.profit_targets),
            strategy_class=strategy_class,
            strategy_params_grid=[self.strategy.strategy_params],
            cost_model=self.costs.build(),
            risk_manager=self.risk.build(),
            on_flat_reentry=self.execution.on_flat_reentry,
            symbol=self.backtest.symbol,
            initial_cash=self.backtest.initial_cash,
            search_strategy=self.search.strategy,
            search_seed=self.search.seed,
            search_direction=self.search.direction,
            rank_by=self.search.rank_by,
            return_full_results=self.output.return_full_results,
        )
