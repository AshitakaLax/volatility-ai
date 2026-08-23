"""
HighFrequencyLocalReferenceSizing -- a re-entry mechanism built for
intraday cadence rather than multi-day swings.

--------------------------------------------------------------------
THE PROBLEM THIS EXISTS TO FIX

Every other SizingStrategy in this codebase relies on the DEFAULT
_check_grid_trigger (src/size_calculators.py): a buy fires only when
price falls `step` below `last_buy_price`, and `last_buy_price` is ONE
global scalar (optimization_controller.BacktestState) that only moves
when a real fill happens. That makes the default trigger a monotonic
dip-ladder -- during an uptrend or ordinary chop, no buy can fire at
all, no matter how small `step` is, because the reference never
resets except on a fill.

Measured on this repo's own 10-year TQQQ SIP minute data: even with
`step`/`profit_target` swept down to 3-50bps (bars typically move
6.8bps median, 13.5bps p75, 23.8bps p90 -- see config/search_bayesian_
hf.yaml), trade count only rose from 72 to ~100-165 over the full 10
years. That is not a threshold-tuning problem; the monotonic reference
structurally cannot retrigger on chop.

The other half of the problem is sizing: every existing strategy
prices a buy as `equity * some_fraction` (2-10% typically), and cash
is only replenished by a sell. A handful of sequential buys during one
decline exhausts it, capping ladder depth independent of `step`.

--------------------------------------------------------------------
THE FIX

Trigger: `max(last_buy_price, short-window rolling high)` as the
reference instead of `last_buy_price` alone. During a sustained
decline the rolling high (an intraday-scale window, converted through
bars_per_day the same way BellCurveProbabilitySizing is -- see
src/sizing_indicators.py for why a raw bar count is the wrong unit)
sits at or above `last_buy_price` and dominates, so a buy can retrigger
on any `step`-sized LOCAL pullback rather than requiring a fresh
extreme below the last fill. Immediately after a real fill,
`last_buy_price` drops to that fill's price, which can momentarily
exceed the rolling high and correctly suppresses an instant re-fire at
the same price -- hysteresis that falls out of the composition rather
than being bolted on. This needs no new state threaded through
BacktestState/decision_cycle: `last_buy_price` is still the only fill
signal a strategy receives, and it remains a sufficient input.

Sizing: a fixed dollar amount, `initial_capital * per_lot_pct`,
captured once from equity on the first record_tick (bar_index==0,
before any lot opens, so context.equity == initial_cash exactly --
same pattern _BaselineScaledStrategy._capture_baseline uses for
price). Constant regardless of how many lots are already open or how
much cash has been deployed, so the SAME cash pool supports many more
concurrent small lots than an equity-fraction sizing would. `per_lot_
pct` is meant to be configured an order of magnitude smaller than
max_trade_pct elsewhere (think 0.1%-1%, not 2-10%) -- ladder depth for
this strategy is deliberately capped by risk.max_concurrent_lots
instead, not by cash exhaustion after a handful of buys.

--------------------------------------------------------------------
WHAT THIS DELIBERATELY DOES NOT CHANGE

No other strategy, and no shared machinery (BacktestState,
decision_cycle.py, RiskManager, AssetLotLedger, no_loss_guard) is
touched. _check_grid_trigger is an explicit per-strategy override
point (see its docstring); this is one more override, not a change to
the default or to any other strategy's behavior.

--------------------------------------------------------------------
event_day_boost_multiplier -- Task 7.9's macro-fields discovery gate,
RE-RUN

MarketContext.is_macro_event_day (architecture_overview.md Section
5.1) existed with a safe default and NO consumer anywhere in this
repository -- tests/unit/test_task_7_9_macro_signals_discovery.py
documents that finding and is written to fail the moment a real
consumer appears. This is that consumer, so per that gate's own step
3, its source dataset, join semantics, and defaults are documented
here (and that test module has been updated to reflect the new,
confirmed-and-scoped state rather than silently going stale):

  Source dataset: src/fomc_calendar.py, a static, hand-verified list
  of FOMC decision dates (2016 through this repo's data cutoff),
  sourced from federalreserve.gov's own historical meeting-calendar
  pages. Not NLP, not sentiment, not a live feed -- FOMC dates are
  published a year-plus in advance, so a static calendar is the
  complete, correct implementation, not a stand-in for something more
  sophisticated.

  Why boost rather than reduce: measured on this repo's own 10-year
  TQQQ SIP dataset, FOMC decision days show 33-37% higher realized
  intraday volatility than other days (Welch t-stat ~3.15, a real
  effect) but a slightly NEGATIVE mean/median close-to-open return
  (not statistically distinguishable from zero at n=74, but certainly
  not positive). A grid/harvest strategy profits from volatility
  itself -- more swings mean more dip-buy-then-harvest opportunities
  -- regardless of the day's net direction, which is what justifies
  sizing UP on higher volatility even without a directional edge. This
  is a deliberate choice to trade on the confirmed half of that
  finding (volatility) and not the unconfirmed half (directional
  drift); it has not yet been validated at the strategy/backtest
  level, only at the raw-price level -- that validation is the
  natural next step before relying on this in live trading.

  Defaults: 1.0 (no-op). A config that doesn't set this gets
  IDENTICAL behavior to before this existed.

--------------------------------------------------------------------
earnings_day_boost_multiplier -- the same idea, second event class

  Source dataset: src/earnings_calendar.py, a static list of the
  sessions that TRADE a mega-cap earnings reaction (not the
  announcement dates -- 381 of 385 announcements land after the close,
  so the move is the next morning's; that module documents the gap
  measurement behind the distinction).

  Why a separate multiplier rather than more dates in
  MarketContext.is_macro_event_day: the two effects are measured to be
  different sizes on this repo's dataset -- +34.1% realized intraday
  vol for FOMC decision days (74 sessions) against +11.4% for earnings
  reactions (296 sessions, Welch t=2.89). One shared flag would force
  one shared multiplier and average them.

  Why boost rather than reduce: identical reasoning to the FOMC case
  above -- the confirmed half of the finding is volatility, and a
  grid/harvest strategy profits from swings regardless of direction.
  Same caveat too: validated at the raw-price level, not yet at the
  strategy/backtest level.

  On a session flagged BOTH ways, the larger multiplier wins rather
  than the two compounding -- see calculate_trade_value.

  Defaults: 1.0 (no-op), same as above.
"""

from __future__ import annotations

from src.exceptions import ConfigurationError
from src.market_context import MarketContext
from src.size_calculators import SizingStrategy
from src.sizing_indicators import RollingMax, bars_from_days


class HighFrequencyLocalReferenceSizing(SizingStrategy):
    """Retriggers on local pullbacks; sizes off a fixed fraction of
    initial capital rather than current equity. See module docstring."""

    def __init__(
        self,
        per_lot_pct: float,
        lookback_days: float,
        bars_per_day: int,
        event_day_boost_multiplier: float = 1.0,
        earnings_day_boost_multiplier: float = 1.0,
    ) -> None:
        if not 0.0 < per_lot_pct <= 1.0:
            raise ConfigurationError(f"per_lot_pct must be in (0, 1], got {per_lot_pct}")
        if event_day_boost_multiplier < 1.0:
            raise ConfigurationError(
                f"event_day_boost_multiplier must be >= 1.0 (this strategy only sizes UP on "
                f"an FOMC day, never down -- see module docstring), got {event_day_boost_multiplier}"
            )
        if earnings_day_boost_multiplier < 1.0:
            raise ConfigurationError(
                f"earnings_day_boost_multiplier must be >= 1.0 (same size-up-only rule as "
                f"event_day_boost_multiplier), got {earnings_day_boost_multiplier}"
            )
        self.per_lot_pct = per_lot_pct
        self.lookback_days = lookback_days
        self.bars_per_day = bars_per_day
        self.event_day_boost_multiplier = event_day_boost_multiplier
        self.earnings_day_boost_multiplier = earnings_day_boost_multiplier
        self._rolling_high = RollingMax(bars_from_days(lookback_days, bars_per_day))
        self._baseline_capital: float | None = None

    def record_tick(self, context: MarketContext) -> None:
        """Advance the rolling high and capture the capital baseline,
        on EVERY bar -- both are properties of the market/portfolio
        state, not of this strategy's own trading, so gating either on
        a triggered bar would make them functions of `step`."""
        if self._baseline_capital is None and context.equity > 0:
            self._baseline_capital = context.equity
        if context.price > 0:
            self._rolling_high.update(context.price)

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """last_buy_price OR the local rolling high, whichever is
        higher, is the reference a pullback is measured from. See the
        module docstring for why this is what lets a buy retrigger on
        chop instead of only on a fresh multi-day low.

        Overrides the LEVEL rather than _check_grid_trigger's boolean
        so the intrabar fill model measures this strategy's real
        reference against the bar's low, instead of the base class's
        last_buy_price-only formula -- see SizingStrategy._grid_trigger_level."""
        rolling_high = self._rolling_high.value
        reference = last_buy_price if rolling_high is None else max(last_buy_price, rolling_high)
        return reference * (1.0 - step)

    def calculate_trade_value(self, context: MarketContext) -> float:
        """A fixed dollar amount, invariant to current equity/drawdown
        and to how many lots are already open -- see module docstring
        for why that is what lets this strategy support many concurrent
        small lots instead of exhausting cash after a handful of buys.

        Scaled up by event_day_boost_multiplier on an FOMC decision day
        and by earnings_day_boost_multiplier on a mega-cap earnings
        reaction day (see module docstring's Task 7.9 section for why
        these are boosts, not reductions, and what they're based on).

        The two are combined with max(), NOT by multiplying. 14 sessions
        in this repo's dataset are both, and compounding would size
        those at up to 6.25x on the swept range while no measurement
        supports treating a doubly-flagged day as that much more
        volatile than a singly-flagged one -- the two effects overlap
        (both are "a scheduled announcement moves the index") rather
        than stacking. max() keeps a both-flags day at the larger of the
        two boosts, which is the conservative reading."""
        if self._baseline_capital is None or self._baseline_capital <= 0:
            return 0.0
        value = self._baseline_capital * self.per_lot_pct
        boost = 1.0
        if context.is_macro_event_day:
            boost = max(boost, self.event_day_boost_multiplier)
        if context.is_earnings_reaction_day:
            boost = max(boost, self.earnings_day_boost_multiplier)
        return value * boost
