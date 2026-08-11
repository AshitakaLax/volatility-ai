"""Immutable per-bar market state and simulation result contracts."""

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
    time_of_day_flag: int = 0
    is_macro_event_day: bool = False
    macro_surprise_factor: float = 0.0

    @property
    def price(self) -> float:
        return self.close


@dataclass
class SimulationResult:
    metrics: dict
    trade_blotter: pd.DataFrame = field(default_factory=pd.DataFrame)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    params: dict = field(default_factory=dict)
