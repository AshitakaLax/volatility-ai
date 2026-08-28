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
    """Everything the strategy sees about one bar/tick.

    Frozen: a strategy must not be able to alter what it was shown, and
    immutability is what makes it safe to hand the same instance to the
    strategy, the risk clamp, and the cost model in one cycle.

    Carries both market data (OHLC) and portfolio state (cash, equity,
    peak_equity, drawdown, open_lot_count) because sizing decisions need
    both. bar_index is the zero-based position within the run.
    """

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
    # A SECOND, independent event flag rather than more values folded
    # into is_macro_event_day. The two are measured to differ in size --
    # FOMC decision days run +34.1% on realized intraday vol against
    # +11.4% for mega-cap earnings reactions (see src/earnings_calendar.py's
    # MEASURED EFFECT section) -- so a strategy must be able to price
    # them separately. Sharing one flag would force one shared
    # multiplier and average two effects that are not the same size.
    # Defaulted like the fields above so every existing call site is
    # unaffected.
    is_earnings_reaction_day: bool = False
    # Present in every dataset this project loads (historical_data.py's
    # BACKTEST_COLUMNS has always included it) and carried through the
    # audit and Monte Carlo paths, but never until now visible to a
    # strategy. Measured against forward 60-session troughs a volume
    # surge scores -0.095 -- weak, but only 0.36-0.49 correlated with
    # the volatility signals, so it is not simply those again.
    #
    # Defaulted to 0.0 like the fields above, so every existing call
    # site is unaffected. A strategy must treat 0.0 as "unknown"
    # rather than "no volume".
    volume: float = 0.0
    # Weighted, minute-precise event signal -- src/event_calendar.py.
    # is_macro_event_day/is_earnings_reaction_day are calendar-DATE
    # booleans with no notion of which company or how much of the index
    # it moves; these two exist to carry lead time and index weight,
    # which a same-day boolean structurally cannot.
    #
    # event_intensity: sum of INDEX_WEIGHTS_PCT (src/index_weights.py)
    # over every event currently inside its lead-time window. 0.0 means
    # no tracked constituent has a release pending or in its reaction
    # window right now -- the overwhelming majority of bars. Deliberately
    # a SUM, not a max: two overlapping reporters (rare, but real -- see
    # src/earnings_calendar.py on FOMC/earnings overlap for the same
    # pattern at day granularity) should read as more exposure than
    # either alone, the way actual index risk would.
    event_intensity: float = 0.0
    # Minutes until the nearest tracked event's release, or -1 once that
    # release has passed and its reaction window has closed. Sentinel
    # -1 rather than 0.0, following time_of_day_flag's convention
    # (src/intraday_profile.py), because 0 is a real, meaningful value
    # here -- "the release is this minute" -- and must not collide with
    # "no event is scheduled."
    minutes_to_event: float = -1.0

    @property
    def price(self) -> float:
        """The decision price: this bar's close.

        A named alias so strategy code reads as intent ("price") rather
        than as a data field, and so the choice of close-as-decision-price
        is stated in exactly one place.
        """
        return self.close


@dataclass
class SimulationResult:
    """Everything one simulated combination produced.

    metrics is always populated. trade_blotter, equity_curve, and params
    are populated when the caller asks for full results, and are empty
    (not None) otherwise, so callers can iterate them unconditionally.
    """

    metrics: dict  # required from Task 4.1 onward; PerformanceAnalyzer.calculate_metrics output, passed through unmodified
    trade_blotter: pd.DataFrame = field(
        default_factory=pd.DataFrame
    )  # populated starting Task 4.6; empty until then
    equity_curve: pd.Series = field(
        default_factory=pd.Series
    )  # populated starting Task 4.6; empty until then
    params: dict = field(default_factory=dict)  # populated starting Task 4.6; empty until then
