"""Pure configuration/domain validation helpers.

These helpers validate inputs before simulation/live execution. They do not
mutate strategy, controller, portfolio, or ledger state.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

from src.exceptions import ConfigurationError


def _number(field: str, value: object) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{field} must be numeric; got {value!r}") from exc
    if not math.isfinite(result):
        raise ConfigurationError(f"{field} must be finite; got {value!r}")
    return result


def validate_positive(field: str, value: object) -> float:
    result = _number(field, value)
    if result <= 0:
        raise ConfigurationError(f"{field} must be positive; got {value!r}")
    return result


def validate_non_negative(field: str, value: object) -> float:
    result = _number(field, value)
    if result < 0:
        raise ConfigurationError(f"{field} must be non-negative; got {value!r}")
    return result


def validate_exposure_pct(field: str, value: object) -> float:
    result = _number(field, value)
    if not 0.0 <= result <= 1.0:
        raise ConfigurationError(f"{field} must be between 0 and 1; got {value!r}")
    return result


def validate_positive_int(field: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigurationError(f"{field} must be a positive integer; got {value!r}")
    return value


def validate_mode(field: str, value: object, allowed_modes: Iterable[str]) -> str:
    allowed = tuple(allowed_modes)
    if value not in allowed:
        raise ConfigurationError(
            f"{field} must be one of {allowed}; got {value!r}"
        )
    return str(value)


def validate_grid_relationship(grid_step: object, profit_target: object) -> tuple[float, float]:
    """Validate the grid semantics used by the current controller.

    A target must be strictly above the grid step so a completed grid move can
    represent a positive harvesting threshold.
    """
    step = validate_positive("grid_step", grid_step)
    target = validate_positive("profit_target", profit_target)
    if target <= step:
        raise ConfigurationError(
            f"profit_target must be greater than grid_step; "
            f"profit_target={profit_target!r}, grid_step={grid_step!r}"
        )
    return step, target


def validate_sweep_config(
    *,
    grid_steps: Iterable[object],
    profit_targets: Iterable[object],
    n_jobs: object,
    initial_cash: object,
    max_concurrent_lots: object | None = None,
    max_total_exposure: object | None = None,
    search_mode: object | None = None,
    search_modes: Iterable[str] | None = None,
    ranking_mode: object | None = None,
    ranking_modes: Iterable[str] | None = None,
) -> None:
    """Validate sweep configuration without mutating any runtime state."""
    validate_positive("initial_cash", initial_cash)
    validate_positive_int("n_jobs", n_jobs)

    steps = list(grid_steps)
    targets = list(profit_targets)
    if not steps:
        raise ConfigurationError("grid_steps must not be empty; got []")
    if not targets:
        raise ConfigurationError("profit_targets must not be empty; got []")
    for step in steps:
        for target in targets:
            validate_grid_relationship(step, target)

    if max_concurrent_lots is not None:
        validate_positive_int("max_concurrent_lots", max_concurrent_lots)
    if max_total_exposure is not None:
        validate_exposure_pct("max_total_exposure", max_total_exposure)

    if search_mode is not None:
        if search_modes is None:
            raise ConfigurationError(
                f"search_mode was supplied without an allowed-mode set; got {search_mode!r}"
            )
        validate_mode("search_mode", search_mode, search_modes)
    if ranking_mode is not None:
        if ranking_modes is None:
            raise ConfigurationError(
                f"ranking_mode was supplied without an allowed-mode set; got {ranking_mode!r}"
            )
        validate_mode("ranking_mode", ranking_mode, ranking_modes)
