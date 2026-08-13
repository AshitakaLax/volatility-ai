"""
Backtest/live configuration containers.

Built to unblock src/live_execution.py and its test, pushed directly
to main mid-session (from src.config import BacktestConfig,
StrategyConfig) -- see the chat this was produced in for the full
context, including two real naming conflicts (FixedPortfolioPercentage's
constructor kwarg, RiskManager's exposure-limit kwarg) that neighbor
files needed dual-keyword support for as a result of this work.

BacktestConfig.validate() delegates to src/validation.py's helpers
(Task 4.9) rather than re-implementing range/cross-field checks here
-- exactly the kind of reuse that module was built for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.exceptions import ConfigurationError
from src.validation import (
    validate_grid_steps,
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


@dataclass(frozen=True)
class GridConfig:
    steps: tuple
    profit_targets: tuple


@dataclass(frozen=True)
class RiskConfig:
    max_concurrent_lots: Optional[int] = None
    max_total_exposure: Optional[float] = None


@dataclass(frozen=True)
class LiveConfig:
    enabled: bool = False
    paper_trading: bool = True


@dataclass(frozen=True)
class BacktestConfig:
    strategy: StrategyConfig
    grid: GridConfig
    backtest: BacktestSection = field(default_factory=BacktestSection)
    risk: RiskConfig = field(default_factory=RiskConfig)
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
        )

        risk_data = data.get("risk", {})
        risk = RiskConfig(
            max_concurrent_lots=risk_data.get("max_concurrent_lots"),
            max_total_exposure=risk_data.get("max_total_exposure"),
        )

        live_data = data.get("live", {})
        live = LiveConfig(
            enabled=live_data.get("enabled", False),
            paper_trading=live_data.get("paper_trading", True),
        )

        return cls(strategy=strategy, grid=grid, backtest=backtest, risk=risk, live=live)

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
        if self.risk.max_concurrent_lots is not None:
            validate_positive_int(self.risk.max_concurrent_lots, "risk.max_concurrent_lots")
        if self.risk.max_total_exposure is not None:
            validate_unit_interval(self.risk.max_total_exposure, "risk.max_total_exposure")
