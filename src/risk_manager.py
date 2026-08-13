"""
Risk manager controlling new-buy exposure. Task 3.1 (R1), implemented
exactly per architecture_overview.md Section 5.4.

Risk semantics (implementation_task_specs.md Task 3.1):
- Controls new buy exposure only -- does not decide whether an
  existing profitable lot may be harvested.
- max_total_exposure_pct means gross deployed market value divided by
  current equity.
- A cap produces a deterministic clamped value of
  0 <= approved_value <= proposed_value -- never increases exposure.
- None means unlimited for that specific control.
"""

from __future__ import annotations

from typing import Optional

from src.exceptions import ConfigurationError
from src.validation import validate_positive_int, validate_unit_interval


class RiskManager:
    """Canonical keyword is `max_total_exposure_pct`. `max_total_exposure`
    is also accepted -- src/live_execution.py, pushed directly to main
    mid-session, calls this constructor with that name -- see the chat
    this was produced in. Passing both is only allowed if they agree;
    the stored attribute is always `self.max_total_exposure_pct` either
    way. Both limits are validated here now (previously left as a
    documented gap when Task 4.9 built src/validation.py, since this
    file wasn't in that task's scope) -- validation helpers already
    exist and this file is being touched for the alias anyway."""

    def __init__(
        self,
        max_concurrent_lots: Optional[int] = None,
        max_total_exposure_pct: Optional[float] = None,
        max_total_exposure: Optional[float] = None,
    ):
        if max_total_exposure_pct is not None and max_total_exposure is not None and max_total_exposure_pct != max_total_exposure:
            raise ConfigurationError(
                f"max_total_exposure_pct ({max_total_exposure_pct!r}) and max_total_exposure "
                f"({max_total_exposure!r}) were both given and disagree -- pass only one"
            )
        exposure_value = max_total_exposure_pct if max_total_exposure_pct is not None else max_total_exposure

        if max_concurrent_lots is not None:
            validate_positive_int(max_concurrent_lots, "max_concurrent_lots")
        if exposure_value is not None:
            validate_unit_interval(exposure_value, "max_total_exposure_pct")

        self.max_concurrent_lots = max_concurrent_lots
        self.max_total_exposure_pct = exposure_value

    def clamp_trade_value(self, proposed_value: float, equity: float, cash: float, open_lot_count: int) -> float:
        """Both limits default to None -> unlimited, matching current
        behavior. Takes plain values (not a context object) so it works
        identically before and after Task 4.1's context-object refactor
        -- only the call site changes."""
        if self.max_concurrent_lots is not None and open_lot_count >= self.max_concurrent_lots:
            return 0.0
        if self.max_total_exposure_pct is not None:
            max_dollars = equity * self.max_total_exposure_pct
            deployed = equity - cash
            proposed_value = min(proposed_value, max(0.0, max_dollars - deployed))
        return proposed_value
