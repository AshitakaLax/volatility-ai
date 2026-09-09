"""
Domain exception hierarchy. Task 4.8.

Gives orchestration, tests, and live recovery code a way to
distinguish failure categories without matching error-message
strings. All domain exceptions descend from TradingSystemError.

Wrapping a lower-level exception should always use `raise
XError(...) from original` (Python's native exception chaining) so
the original remains inspectable via __cause__ -- these classes don't
need special handling for that themselves, chaining is a language
feature, not something a class opts into.
"""

from __future__ import annotations


class TradingSystemError(Exception):
    """Root of the domain exception hierarchy."""


class ConfigurationError(TradingSystemError):
    """Invalid configuration -- bad parameters, missing required
    settings, mode/mode-like flags that aren't one of their allowed
    values."""


class DataValidationError(TradingSystemError):
    """Historical/live market data fails schema or sanity checks."""


class StrategyError(TradingSystemError):
    """A sizing/trading strategy fails internally (e.g. an invalid
    internal state, a strategy-specific precondition violation)."""


class RiskError(TradingSystemError):
    """A risk control rejects or cannot evaluate a proposed trade."""


class ExecutionError(TradingSystemError):
    """An order fails to execute as expected (rejected, unfillable,
    broker-reported failure)."""


class ReconciliationError(TradingSystemError):
    """Local state disagrees with the broker's reported state."""


class PersistenceError(TradingSystemError):
    """Durable state fails to save, load, or stays inconsistent
    across a restart."""
