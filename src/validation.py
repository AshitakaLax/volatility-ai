"""
Configuration/domain validation helpers. Task 4.9.

Validates numeric ranges and cross-field relationships before any
simulation work starts, so a bad configuration fails immediately
rather than partway through a potentially expensive sweep.

Deliberately src/validation.py, not src/config.py -- the task offers
either name, but src/config.py is already the import path
live_execution.py (pushed directly to main during this session)
expects BacktestConfig/StrategyConfig container classes at. That's a
different kind of module (config *data*, not validation *logic*) and
a bigger undertaking than this task's actual scope -- see the chat
this was produced in for the full picture, including real naming
conflicts (FixedPortfolioPercentage's constructor kwarg, RiskManager's
exposure-limit kwarg) between this codebase and that file that this
task does not attempt to resolve. Creating src/config.py here with
only validation functions, not those classes, would leave a
half-populated file sitting at the exact path something else needs.

Pure functions only -- nothing here mutates strategy or portfolio
state, per this task's own requirement.
"""

from __future__ import annotations

from collections.abc import Iterable

from src.exceptions import ConfigurationError

VALID_ON_FLAT_REENTRY = ("stale_reference", "reset_to_market")
VALID_INTRABAR_PRIORITY = ("sell_first", "buy_first")


def validate_positive(value: float, field_name: str) -> None:
    """Require value > 0. Zero is rejected -- callers that want to allow
    it should use validate_non_negative instead."""
    if not (value > 0):
        raise ConfigurationError(f"{field_name} must be positive, got {value!r}")


def validate_non_negative(value: float, field_name: str) -> None:
    """Require value >= 0. Used for costs and fees, where zero is a
    legitimate value but a negative one is nonsense."""
    if not (value >= 0):
        raise ConfigurationError(f"{field_name} must be non-negative, got {value!r}")


def validate_unit_interval(value: float, field_name: str) -> None:
    """Require 0 <= value <= 1, INCLUSIVE at both ends.

    For fractions and percentages expressed as decimals (exposure
    limits, drawdown thresholds). 1.0 means 100% and is allowed.
    """
    if not (0 <= value <= 1):
        raise ConfigurationError(f"{field_name} must be in [0, 1], got {value!r}")


def validate_positive_int(value: int, field_name: str) -> None:
    """Require a positive whole number.

    Explicitly rejects bool, which is an int subclass in Python -- so
    True would otherwise sneak through as the integer 1 and silently
    become a count. For lot limits and worker/trial counts.
    """
    if not (isinstance(value, int) and not isinstance(value, bool) and value > 0):
        raise ConfigurationError(f"{field_name} must be a positive integer, got {value!r}")


def validate_one_of(value, allowed: Iterable, field_name: str) -> None:
    """Require value to be one of `allowed`, naming every permitted
    option in the error so a typo is immediately fixable."""
    if value not in allowed:
        raise ConfigurationError(f"{field_name} must be one of {tuple(allowed)}, got {value!r}")


def validate_grid_steps(grid_steps: Iterable[float]) -> None:
    """Validate a list of grid-step fractions.

    Each must be positive and strictly below 1.0. The upper bound is a
    domain check, not a range check: a step of 1.0 means a 100% drop,
    which from any positive price can never trigger twice, so it is
    incompatible with the grid strategy's own mechanics.
    """
    grid_steps = list(grid_steps)
    if not grid_steps:
        raise ConfigurationError("grid_steps must not be empty")
    for step in grid_steps:
        validate_positive(step, "grid_steps entry")
        # Cross-field/domain-semantics check, not a plain range check:
        # a grid_step >= 1.0 (a 100%+ drop) can never trigger a second
        # buy from a positive last_buy_price, since that would require
        # price <= 0 -- numerically representable but incompatible
        # with the grid strategy's own semantics.
        if step >= 1.0:
            raise ConfigurationError(
                f"grid_steps entry {step!r} is >= 1.0 (a 100%+ drop) -- incompatible with the "
                "grid strategy's semantics; a grid step this large can never trigger twice"
            )


def validate_profit_targets(profit_targets: Iterable[float]) -> None:
    """Validate a list of profit-target fractions: non-empty, each
    positive. A zero or negative target would mean exiting at or below
    cost, which the no-loss invariant forbids anyway."""
    profit_targets = list(profit_targets)
    if not profit_targets:
        raise ConfigurationError("profit_targets must not be empty")
    for target in profit_targets:
        validate_positive(target, "profit_targets entry")


def validate_run_sweep_config(
    *,
    grid_steps: Iterable[float],
    profit_targets: Iterable[float],
    n_jobs: int,
    on_flat_reentry: str,
    initial_cash: float,
) -> None:
    """Everything run_sweep needs validated before starting the first
    combination."""
    validate_grid_steps(grid_steps)
    validate_profit_targets(profit_targets)
    validate_positive_int(n_jobs, "n_jobs")
    validate_one_of(on_flat_reentry, VALID_ON_FLAT_REENTRY, "on_flat_reentry")
    validate_positive(initial_cash, "initial_cash")
