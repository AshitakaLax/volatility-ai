"""Stable domain exception hierarchy for the trading system.

The hierarchy gives orchestration and tests stable failure categories without
requiring callers to match exception-message strings. Lower-level failures can
be wrapped with ``raise ... from exc`` so the original cause remains inspectable.
"""


class TradingSystemError(Exception):
    """Root exception for expected trading-system failures."""


class ConfigurationError(TradingSystemError):
    """Invalid strategy, risk, execution, or runtime configuration."""


class DataValidationError(TradingSystemError):
    """Historical or market data violates the validated input contract."""


class StrategyError(TradingSystemError):
    """A strategy cannot evaluate or produce a valid decision."""


class RiskError(TradingSystemError):
    """A risk constraint or risk-state invariant was violated."""


class ExecutionError(TradingSystemError):
    """Order submission or execution failed."""


class SellEconomicsError(ExecutionError):
    """A proposed sell is rejected because net proceeds would not cover
    the allocated cost basis (no-loss Rule One violation).

    Raised by ``validate_sell`` before a sell intent is submitted to the
    broker.  All exit paths must call ``validate_sell`` rather than
    duplicating the net_sell_proceeds / allocated_cost_basis comparison.
    """


class ReconciliationError(TradingSystemError):
    """Internal state cannot be reconciled with observed execution state."""


class PersistenceError(TradingSystemError):
    """Persistent state could not be read, written, or reconciled."""
