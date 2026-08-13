"""
MarketContext and SimulationResult. Task 4.1 (A1).

Canonical definitions -- architecture_overview.md Section 5.1
(MarketContext) and Section 5.6 (SimulationResult). Both live here
per Section 5.6's own note: "a one-field dataclass doesn't need a
file of its own" once this module exists for MarketContext.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass(frozen=True)
class MarketContext:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    cash: float
    equity: float
    peak_equity: float
    drawdown: float
    open_lot_count: int
    bar_index: int
    # Added to unblock src/live_execution.py (pushed directly to main
    # mid-session -- see the chat this was produced in). Defaulted so
    # every pre-existing MarketContext(...) call site (all keyword-arg,
    # confirmed before this change) keeps working unmodified. Defaults
    # match exactly what live_execution.py's own build_context already
    # assumed before these fields existed on this class.
    time_of_day_flag: int = 0
    is_macro_event_day: bool = False
    macro_surprise_factor: float = 0.0

    @property
    def price(self) -> float:
        return self.close


@dataclass
class SimulationResult:
    metrics: dict  # required from Task 4.1 onward; PerformanceAnalyzer.calculate_metrics output, passed through unmodified
    trade_blotter: pd.DataFrame = field(default_factory=pd.DataFrame)  # populated starting Task 4.6; empty until then
    equity_curve: pd.Series = field(default_factory=pd.Series)  # populated starting Task 4.6; empty until then
    params: dict = field(default_factory=dict)  # populated starting Task 4.6; empty until then
