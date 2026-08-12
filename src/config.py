"""Canonical backtest configuration and YAML serialization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.cost_models import TransactionCostModel, ZeroCostModel
from src.exceptions import ConfigurationError
from src.risk_manager import RiskManager
from src.validation import validate_sweep_config


@dataclass(frozen=True)
class StrategyConfig:
    strategy_id: str
    strategy_params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BacktestSection:
    symbol: str = "TQQQ"
    initial_cash: float = 100_000.0
    start: str | None = None
    end: str | None = None
    data_path: str | None = None


@dataclass(frozen=True)
class GridConfig:
    steps: tuple[float, ...] = ()
    profit_targets: tuple[float, ...] = ()


@dataclass(frozen=True)
class CostsConfig:
    model: str = "zero"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskConfig:
    max_concurrent_lots: int | None = None
    max_total_exposure: float | None = None
    halt_new_buys_if_drawdown_exceeds: float | None = None


@dataclass(frozen=True)
class SearchConfig:
    strategy: str = "grid"
    rank_by: str = "Capital Velocity Index"
    direction: str = "maximize"
    seed: int = 0
    n_trials: int | None = None


@dataclass(frozen=True)
class ExecutionConfig:
    n_jobs: int = 1
    on_flat_reentry: str = "stale_reference"


@dataclass(frozen=True)
class OutputConfig:
    return_full_results: bool = False


@dataclass(frozen=True)
class LiveConfig:
    enabled: bool = False
    paper_trading: bool = True


@dataclass(frozen=True)
class BacktestConfig:
    """Validated source-of-truth configuration for reproducible backtests."""

    strategy: StrategyConfig
    backtest: BacktestSection = field(default_factory=BacktestSection)
    grid: GridConfig = field(default_factory=GridConfig)
    costs: CostsConfig = field(default_factory=CostsConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    live: LiveConfig = field(default_factory=LiveConfig)

    def validate(self) -> None:
        if not self.strategy.strategy_id:
            raise ConfigurationError("strategy.strategy_id='': must be non-empty")
        validate_sweep_config(
            grid_steps=list(self.grid.steps),
            profit_targets=list(self.grid.profit_targets),
            n_jobs=self.execution.n_jobs,
            initial_cash=self.backtest.initial_cash,
            max_concurrent_lots=self.risk.max_concurrent_lots,
            max_total_exposure=self.risk.max_total_exposure,
        )
        if self.search.strategy not in {"grid", "bayesian"}:
            raise ConfigurationError(f"search.strategy={self.search.strategy!r}: expected 'grid' or 'bayesian'")
        if self.search.direction not in {"maximize", "minimize"}:
            raise ConfigurationError(f"search.direction={self.search.direction!r}: expected 'maximize' or 'minimize'")
        if self.execution.on_flat_reentry not in {"stale_reference", "reset_to_market"}:
            raise ConfigurationError(f"execution.on_flat_reentry={self.execution.on_flat_reentry!r}: invalid policy")
        if self.costs.model not in {"zero", "slippage_commission", "dynamic_slippage"}:
            raise ConfigurationError(f"costs.model={self.costs.model!r}: unsupported transaction-cost model")
        if self.risk.halt_new_buys_if_drawdown_exceeds is not None and not 0.0 <= self.risk.halt_new_buys_if_drawdown_exceeds <= 1.0:
            raise ConfigurationError(f"risk.halt_new_buys_if_drawdown_exceeds={self.risk.halt_new_buys_if_drawdown_exceeds!r}: expected 0..1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["grid"]["steps"] = list(self.grid.steps)
        data["grid"]["profit_targets"] = list(self.grid.profit_targets)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BacktestConfig":
        if not isinstance(data, dict):
            raise ConfigurationError(f"config={data!r}: expected a mapping")
        try:
            config = cls(
                strategy=StrategyConfig(**data["strategy"]),
                backtest=BacktestSection(**data.get("backtest", {})),
                grid=GridConfig(
                    steps=tuple(data.get("grid", {}).get("steps", [])),
                    profit_targets=tuple(data.get("grid", {}).get("profit_targets", [])),
                ),
                costs=CostsConfig(**data.get("costs", {})),
                risk=RiskConfig(**data.get("risk", {})),
                search=SearchConfig(**data.get("search", {})),
                execution=ExecutionConfig(**data.get("execution", {})),
                output=OutputConfig(**data.get("output", {})),
                live=LiveConfig(**data.get("live", {})),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigurationError(f"config={data!r}: invalid configuration shape") from exc
        config.validate()
        return config

    @classmethod
    def from_yaml(cls, path: str | Path) -> "BacktestConfig":
        try:
            import yaml
        except ImportError as exc:
            raise ConfigurationError("YAML loading requires the PyYAML dependency") from exc
        path = Path(path)
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except OSError as exc:
            raise ConfigurationError(f"config_path={str(path)!r}: unable to read configuration") from exc
        return cls.from_dict(data)


def build_cost_model(config: CostsConfig) -> TransactionCostModel:
    if config.model == "zero":
        return ZeroCostModel()
    raise ConfigurationError(f"costs.model={config.model!r}: model construction is not available in Task 6.1")


def build_risk_manager(config: RiskConfig) -> RiskManager:
    return RiskManager(
        max_concurrent_lots=config.max_concurrent_lots,
        max_total_exposure=config.max_total_exposure,
    )
