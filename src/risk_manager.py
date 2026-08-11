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


class RiskManager:
    def __init__(self, max_concurrent_lots: Optional[int] = None, max_total_exposure_pct: Optional[float] = None):
        self.max_concurrent_lots = max_concurrent_lots
        self.max_total_exposure_pct = max_total_exposure_pct

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
