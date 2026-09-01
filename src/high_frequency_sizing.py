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

--------------------------------------------------------------------
vol_scale_exponent -- CONTINUOUS sizing, measured not scheduled

Both boosts above share a ceiling: they fire on a calendar. FOMC days
are 2.8% of sessions and earnings reactions 11.1%, and measured at the
backtest level each moved total return by only ~1-2 percentage points
(FOMC +1.66pp on a 166% return; earnings +1.06 to +1.68pp across three
controlled pairs). Identifying volatile days is not the constraint --
a multiplier that fires on a twentieth of the calendar simply cannot
move a 10-year result much.

This scales size on EVERY bar instead, by short-horizon realized
volatility relative to its own longer-horizon baseline:

    multiplier = clamp((fast_vol / slow_vol) ** exponent, min, max)

It also subsumes much of what a calendar would tell us. CPI, payrolls
and FOMC days are volatile, and this responds to that volatility
without needing to know why it is there -- which matters because the
authoritative release calendars for CPI/payrolls are not currently
obtainable in this environment (bls.gov and fred.stlouisfed.org both
refuse programmatic access), while realized volatility is already in
the data.

  Direction is NOT assumed. Unlike the event boosts, which are
  constrained to >= 1.0 because they encode a measured claim, the
  exponent is free to be negative: negative sizes DOWN into volatility
  (classic vol targeting), positive leans IN (consistent with the
  event boosts). Sweeping across zero measures which is right.

  MEASURED, and the answer is negative. Controlled grid on the full
  10-year SIP dataset, every other parameter fixed (step=0.00075,
  target=0.002, per_lot_pct=0.0002, lookback=0.03, fomc=2.5,
  earnings=1.5), sweeping only this exponent:

      exponent   return   max DD   return/DD
        -1.5     38.99%   55.61%     0.701
        -1.0     34.11%   52.47%     0.650
        -0.5     29.07%   49.55%     0.587
         0.0     25.94%   49.14%     0.528   <- control, exact no-op
        +0.5     24.37%   52.08%     0.468
        +1.0     23.80%   56.88%     0.418

  Monotonic in both directions. Sizing DOWN into volatility is worth
  +13.05 percentage points of return at -1.5 (a ~50% relative gain)
  and improves return/drawdown at every step, while leaning IN is
  strictly worse than doing nothing.

  Note this cuts AGAINST the direction both event boosts assume. They
  are not strictly contradicted -- a scheduled announcement is not the
  same thing as a crash, and this exponent responds to realized
  volatility whenever it appears, which on this dataset is dominated
  by 2020 and 2022 -- but the premise "size up when volatility is
  high" does not survive as a general rule here. A plausible
  explanation is that this strategy never sells at a loss
  (src/no_loss_guard.py), so deploying MORE capital into a decline
  buys lots that then ride it down; deploying less preserves cash for
  lower prices. That explanation is untested.

  The drawdown cost is real: -1.5 also moves max drawdown from 49.14%
  to 55.61%, so this is a favorable trade rather than a free one, and
  -0.5 buys +3.1pp of return for +0.4pp of drawdown if the cap matters
  more than the return.

  CONFIRMED at scale. A 250-combination random sweep over the wider
  space (config/search_hf_volscaled.yaml, 3,240 points, drawdown capped
  at 55%) reproduced it across 85 admissible combinations:

      exponent   n   median return   best return
        -2.0    11       39.76%         57.06%
        -1.5    12       31.95%         67.09%
        -1.0    21       24.38%         53.95%
        -0.5    17       29.25%         51.51%
         0.0    24       23.54%         43.27%   <- control

  Best admissible overall was 67.09% return at 49.06% drawdown, against
  43.27% for the best exponent-0.0 control -- +23.8 percentage points
  from this parameter alone.

  ON THE WINDOWS: vol_fast_days and vol_slow_days were fixed at 0.5 and
  20.0 for the controlled grid above, chosen without evidence. That
  choice was wrong. Swept, 0.5 was the WORST of the three fast windows
  (median 25.94% against 30.41% at 0.25) and 20.0 the middling slow one.
  The best configuration uses 0.25 / 10.0 -- and both sit at the SHORTER
  EDGE of what was swept, so the optimum plausibly lies below both and
  the range should be extended downward before these are treated as
  tuned.

  Defaults: exponent 0.0, an exact no-op -- and at 0.0 the rolling
  windows are not even constructed, so there is no per-bar cost to
  leaving it off.

--------------------------------------------------------------------
time_of_day_exponent -- the same idea, on the clock instead

MarketContext.time_of_day_flag was the LAST of Task 7.9's three
macro/seasonality fields still sitting unpopulated and unconsumed. This
is its consumer, and it is populated with minutes since 09:30 Eastern
by optimization_controller (backtest) and live_trading_loop (live),
through the same window and conversion so the two cannot disagree.

  Source dataset: src/intraday_profile.py -- mean intrabar range per
  minute-of-session, measured on this repo's own 10-year dataset at
  2,655 samples per minute and normalized to mean 1.0.

  Why this is worth more than either calendar: it is the largest
  effect measured anywhere in this project, and unlike an event flag
  it applies in EVERY session rather than 3% or 11% of them.

      09:30-10:00   +152% vs the all-day average
      12:00-14:00    -36%

  Why it is not redundant with vol_scale_exponent. That scaler is
  backward-looking and structurally lags the open: even its shortest
  window (0.25 days = 97 bars) is still mostly describing yesterday
  afternoon at 09:30, so it cannot react to the open's volatility
  until most of the open is already gone. This one is known exactly in
  advance, from the clock, with no warm-up and no lag. The two are
  expected to compose, and they multiply.

  Why RANGE rather than close-to-close underlies the profile, and why
  minute 0 is not the 15.6x outlier a naive measurement reports, are
  both in src/intraday_profile.py's docstring. Briefly: the fill model
  fills on intrabar touches, so range is what decides whether a fill
  happens, and a close-to-close return at 09:30 measures the overnight
  gap rather than the minute.

  Defaults: 0.0, an exact no-op, and like vol_scale_exponent it costs
  nothing per bar when off.

--------------------------------------------------------------------
vol_measure -- WHICH volatility, stdev or range

vol_scale_exponent needs a volatility estimate, and the obvious choice
(standard deviation of close-to-close log returns) is measurably not
the best one. Tested against the worst forward return over the next 60
sessions, rank correlation on 2,395 daily observations:

    5d/60d intrabar RANGE ratio    -0.219
    5d/60d close-to-close ratio    -0.172

Range also matches what the strategy actually experiences: the
intrabar fill model fills on TOUCHES inside a bar, so bar range is the
quantity that decides whether a fill happens. It is the same reasoning
that made src/intraday_profile.py range-based.

Defaults to "stdev" -- NOT because it is better, but because every
result recorded in this docstring was produced with it, and silently
switching would leave those numbers describing code that no longer
exists. Sweep the two against each other and let the backtest decide;
a rank correlation against forward troughs is a proxy for the thing we
care about, not the thing itself.

--------------------------------------------------------------------
volume_scale_exponent -- the input that was always there

Volume has been loaded by historical_data.py since the beginning and
carried through the audit and Monte Carlo paths, but no strategy could
see it: MarketContext had no field for it until now. It is the
cheapest possible new input -- already fetched, already stored, no
external dependency, no sourcing problem.

It is also WEAK. A volume surge scores -0.095 against forward
60-session troughs, against -0.219 for the range measure. It is
included on one specific ground: it is only 0.36-0.49 rank-correlated
with the volatility signals, so unlike most candidates it is not
simply those again wearing a different name. Signals that merely
restate each other add parameters without adding information.

Reuses vol_fast_days/vol_slow_days and vol_scale_min/max rather than
introducing four more knobs. Adding an axis for its own sake has a
measured cost here: it once took a sweep from 3.2% coverage to 0.30%.

Defaults: 0.0, an exact no-op, and it should stay there unless a sweep
shows it earning its place.
--------------------------------------------------------------------
dd_throttle_start / dd_throttle_full / dd_throttle_floor -- sizing DOWN
into an extended drawdown, not just a volatile bar

Every lever above reacts to something LOCAL -- a calendar day, a
realized-vol ratio over a handful of hours, the clock. None of them
know whether the strategy is already deep in a multi-month drawdown.
That gap shows up in the numbers: max drawdown sits at 73-82% across
essentially every sweep run against this strategy on the full 10-year
dataset -- vol scaling, volume scaling, wide-target sweeps, Bayesian
comparisons, and the trailing-target sweeps (config/retune_trailing_v3
and its predecessors) all land in that same band regardless of which
of the other knobs moved. No lever tried so far targets the drawdown
number itself.

This one does, directly, using MarketContext.drawdown -- the SAME
peak-equity/drawdown figure optimization_controller.py already tracks
every bar (see its "Peaks/drawdown every bar (B3)" comment) and reports
as "Max Drawdown %". Reusing it here means this throttle sees exactly
the metric it exists to improve, computed once, not a second estimate
that could disagree with it.

    multiplier = 1.0                                   if dd <= start
                 floor                                  if dd >= full
                 linear ramp from 1.0 down to floor      in between

This is deliberately a threshold-and-ramp, not the exponent form
vol_scale_exponent uses. That form fits a ratio that is centered on
1.0 and can go either direction; drawdown is bounded in [0, 1) and this
lever is size-DOWN only by design -- there is no direction to sweep
across zero the way there was for vol_scale_exponent, only how early
(dd_throttle_start) and how hard (dd_throttle_full, dd_throttle_floor)
to de-risk. A no-loss strategy (src/no_loss_guard.py) that keeps buying
dips all the way down is, by construction, accumulating lots that can
only be closed once the price recovers past their own cost basis --
each additional lot bought deep in a drawdown adds another position
that needs a larger recovery to exit. Buying LESS once already deep in
one is the direct lever against that, independent of anything vol_scale_
exponent's backward-looking ratio measures.

Composes by multiplication with every other scaler above, same as
vol_scale_exponent and volume_scale_exponent -- a calm bar deep in a
drawdown and a volatile bar deep in the same drawdown are not the same
situation, so this stacks rather than overriding them.

Defaults: dd_throttle_start=None, an exact no-op -- a config that never
sets it gets IDENTICAL behavior to before this existed, and costs
nothing per bar (context.drawdown is already computed by the controller
for every strategy; this only adds one multiply-and-clamp when enabled).

UNMEASURED as of this writing -- this is a new lever, not yet swept.
The next sweep should hold every other parameter at this strategy's
best known configuration (config/retune_uniform_extended_v2.yaml's
target=1.00, untrailed: 38.61% CAGR, 82.4% max DD) and vary
dd_throttle_start/full/floor to see whether de-risking during a deep
drawdown actually trades return for a lower max DD, or whether -- like
vol_scale_exponent leaning IN, or the trailing-target floor -- the
straightforward-sounding direction turns out not to hold on this data.
--------------------------------------------------------------------
weighted_event_boost_multiplier -- minute precision, step 3

MarketContext.event_intensity is a NEW field, not one of Task 7.9's
original four -- see src/market_context.py's own comment on it. This is
its consumer, so per the same discovery-gate process:

Source dataset: src/event_calendar.py's EarningsEventTable, built from
data/earnings_releases_derived.csv (676 release timestamps across 16
tickers, RECOVERED from the tape -- see that module's docstring for
the method and why recovering a scheduled, publicly-announced time is
not lookahead) and src/index_weights.py's single 2026-08-13 QQQ-holdings
snapshot (documented there as lookahead bias applied to all history,
pending quarterly snapshots).

Join semantics: EarningsEventTable.vectorized (backtest) and .scalar
(live) share one window definition -- [release - lead_minutes, release
+ reaction_minutes), lead_minutes=15.0 by default -- and are pinned
equal on every bar by
tests/unit/test_event_calendar.py::test_scalar_and_vectorized_agree_on_every_bar.
event_intensity is the SUM of index weight over every event whose
window currently contains the bar (not max -- see that module's
docstring on why two overlapping releases are independent exposure,
unlike the day-level flags above).

Defaults: weighted_event_boost_multiplier=1.0, an exact no-op --
event_intensity being populated changes nothing until a config sets
this above 1.0.
--------------------------------------------------------------------
implied_vol_exponent -- the first FORWARD-looking volatility input

Task 7.9 step-3 writeup for MarketContext.implied_vol_change:

  Consuming strategy: this one, HighFrequencyLocalReferenceSizing, via
  _implied_vol_scale. It is the only consumer.

  Source dataset: src/implied_vol_signal.py, built from an
  implied-volatility instrument's own minute bars and joined by
  src/external_index_series.py's as-of lookup. Currently VIXY (Alpaca,
  sip, adjustment=all). The RIGHT series is VXN -- Nasdaq-100 implied
  vol, the index TQQQ tracks 3x -- from hfmarketdata.io, which was
  unreachable when this was written (HTTP 000 after 25s while control
  hosts answered in 1.5s; src/hf_market_data.py documents that same
  outage mode). VIXY substitutes VIX for VXN and VIX FUTURES via an ETF
  wrapper for spot, so it is a proxy on two axes. Re-measure against
  real VXN before trusting tuned parameters.

  Join semantics: session-over-session percentage change in the series'
  CLOSE, published to the as-of series at midnight Eastern on the day
  AFTER the session that produced it. Every bar of the following
  session -- pre-market included -- therefore reads a value that was
  already history when that session opened, so there is no lookahead;
  tests/unit/test_implied_vol_signal.py asserts that directly rather
  than inferring it from the construction. Absent file, or bars before
  the series starts, yield 0.0.

  Defaults: implied_vol_exponent=0.0, an exact no-op. A config that
  does not set it, and a deployment with no implied-vol file, both
  reproduce prior behavior bit for bit.

WHY THE CHANGE AND NOT THE LEVEL OR THE RATIO -- measured, and the
obvious answer was wrong. tools/measure_vol_signal.py, 2,671 sessions,
partial rank correlation against next-session OPENING volatility:

                        raw    partial|rv_ratio   partial|rv_fast
    implied level     -0.180        -0.188            -0.085
    implied 1d change +0.119        +0.136            +0.257
    implied 5/60 ratio+0.429        +0.277            -0.039

The RATIO looks like the winner against the realized 5/60 ratio and
collapses to nothing against trailing realized vol -- the first control
is much the weaker predictor (rho +0.41 vs +0.79), so the ratio was
only re-encoding volatility persistence this strategy already has. The
LEVEL is negatively correlated because a VIX-futures ETF carries roll
decay, which is drift, not signal. Only the CHANGE strengthens under
the harder control, which is what an input carrying genuinely new
information looks like.

WHY THIS EARNS AN AXIS WHEN THE CALENDARS DID NOT. It is not scheduled
-- it fires on every session, not on a twentieth of them, which is the
exact ceiling the event boosts hit above. And it is the only signal
here that is not derived from TQQQ's own past bars, so it is the only
one that can be non-redundant with vol_scale_exponent by construction.

WHY LINEAR RATHER THAN AN EXPONENT. _vol_scale raises a strictly
positive RATIO to a power. This input is a signed CHANGE centred on
zero, and a negative base to a fractional power is undefined -- so the
ratio form is not merely awkward here, it is wrong. See
_implied_vol_scale.

--------------------------------------------------------------------
SYNTHETIC BARS, AND WHY THE VOL WINDOWS ARE GATED BY VOLUME TOO

src/historical_data.resample_to_uniform_minutes exists for the
extended-hours dataset, where real bar density drifted 2.08x from 2016
to 2026 as pre/post-market liquidity grew -- a problem bars_per_day
cannot express since it is one constant for the whole backtest. The fix
gives every session the same bar count by inserting flat, zero-volume
bars into quiet minutes: open==high==low==close of the last real print,
volume==0.0.

Measured on that dataset: 52.2% of 2016's bars are synthetic against
0.6% of 2026's. Before this gate, record_tick fed every one of those
into _fast_vol/_slow_vol. A flat bar is a genuine zero under EITHER
vol_measure -- zero intrabar range, and a zero log return against an
unchanged price -- so realized vol read low precisely through the
years with the most synthetic filler, and with a NEGATIVE
vol_scale_exponent (this strategy's measured direction, see above)
that means sizing UP more in 2016-2019 than 2022-2026: an artifact of
the fill pattern, not a market signal.

The detector is NOT context.volume > 0, even though that is what gates
the volume windows just below for an unrelated reason. It was the
first thing tried, and it is wrong: on the live path context.volume is
ALWAYS 0.0 (LiveBar carries no volume field), so gating vol scaling on
it would not merely skip synthetic bars, it would disable this
strategy's primary measured lever -- vol_scale_exponent -- in live
trading permanently, including on the config running in production as
this was written.

The actual detector is structural: a bar is treated as synthetic when
it is flat (high == low == price) AND unchanged from the previous real
price, which is exactly what a carried-forward fabricated bar is by
construction. This is a heuristic, not an exact test -- 2-5% of
genuinely real bars on the extended-hours dataset are also flat and
unchanged (thin liquidity), and those get skipped too. Measured across
every year, that rate does not track the 52% -> 0.6% ramp the
synthetic bars themselves produce, so it does not reintroduce a
year-correlated bias; it is small, roughly flat noise instead. See
record_tick for the exact condition and the year-by-year numbers.
"""

from __future__ import annotations

from math import log

from src.exceptions import ConfigurationError
from src.intraday_profile import relative_range
from src.market_context import MarketContext
from src.size_calculators import SizingStrategy
from src.synthetic_bars import is_synthetic_bar
from src.sizing_indicators import RollingMax, RollingMean, RollingStdev, bars_from_days, clamp
from src.trailing_target import TrailingTargetPolicy

# Below this, a realized-vol estimate is numerical noise rather than a
# measurement -- see _vol_scale. Per-bar log returns here run ~1e-4.
_VOL_EPSILON = 1e-9

# Safety rails on the time-of-day multiplier, not tuning knobs -- see
# _time_of_day_scale. Non-binding for any |exponent| <= 1.
_TOD_SCALE_FLOOR = 0.1
_TOD_SCALE_CEIL = 3.0


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
        vol_scale_exponent: float = 0.0,
        vol_fast_days: float = 0.5,
        vol_slow_days: float = 20.0,
        vol_scale_min: float = 0.5,
        vol_scale_max: float = 2.0,
        time_of_day_exponent: float = 0.0,
        vol_measure: str = "stdev",
        volume_scale_exponent: float = 0.0,
        trail_pct: float | None = None,
        trail_min_profit_target: float = 0.001,
        weighted_event_boost_multiplier: float = 1.0,
        dd_throttle_start: float | None = None,
        dd_throttle_full: float = 0.60,
        dd_throttle_floor: float = 0.25,
        implied_vol_exponent: float = 0.0,
        implied_vol_scale_min: float = 0.5,
        implied_vol_scale_max: float = 2.0,
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
        if weighted_event_boost_multiplier < 1.0:
            raise ConfigurationError(
                f"weighted_event_boost_multiplier must be >= 1.0 (same size-up-only rule as "
                f"the other event boosts), got {weighted_event_boost_multiplier}"
            )
        self.weighted_event_boost_multiplier = weighted_event_boost_multiplier
        self.per_lot_pct = per_lot_pct
        self.lookback_days = lookback_days
        self.bars_per_day = bars_per_day
        if vol_scale_min <= 0.0 or vol_scale_max < vol_scale_min:
            raise ConfigurationError(
                f"need 0 < vol_scale_min <= vol_scale_max, got "
                f"{vol_scale_min} and {vol_scale_max}"
            )
        if vol_measure not in ("stdev", "range"):
            raise ConfigurationError(
                f"vol_measure must be 'stdev' or 'range', got {vol_measure!r}"
            )
        self.event_day_boost_multiplier = event_day_boost_multiplier
        self.earnings_day_boost_multiplier = earnings_day_boost_multiplier
        self.vol_scale_exponent = vol_scale_exponent
        self.vol_measure = vol_measure
        self.volume_scale_exponent = volume_scale_exponent
        self.vol_fast_days = vol_fast_days
        self.vol_slow_days = vol_slow_days
        self.vol_scale_min = vol_scale_min
        self.vol_scale_max = vol_scale_max
        self.time_of_day_exponent = time_of_day_exponent
        self._tod_enabled = time_of_day_exponent != 0.0
        # Built ONLY when the feature is on. At exponent 0.0 the scaler
        # is an exact no-op, so constructing the two rolling windows
        # would add a per-bar update on a 1M-bar dataset, for every
        # combination in a sweep, to compute a number that is then
        # raised to the power zero.
        self._vol_enabled = vol_scale_exponent != 0.0
        self._prev_price: float | None = None
        self._volume_enabled = volume_scale_exponent != 0.0
        fast_bars = max(2, bars_from_days(vol_fast_days, bars_per_day))
        slow_bars = max(2, bars_from_days(vol_slow_days, bars_per_day))
        if self._vol_enabled:
            # RollingStdev over log returns for "stdev"; RollingMean over
            # intrabar range for "range". Both yield a fast/slow ratio,
            # so _vol_scale is identical downstream either way.
            make = RollingStdev if vol_measure == "stdev" else RollingMean
            self._fast_vol = make(fast_bars)
            self._slow_vol = make(slow_bars)
        if self._volume_enabled:
            # Deliberately reuses vol_fast_days/vol_slow_days rather than
            # adding two more sweepable windows. Volume surges and
            # volatility surges are the same events on this data (0.36-0.49
            # rank correlation), so separate horizons would mostly add
            # search-space dilution -- which measurably cost coverage the
            # last time an axis was added for its own sake.
            self._fast_volume = RollingMean(fast_bars)
            self._slow_volume = RollingMean(slow_bars)
        self._rolling_high = RollingMax(bars_from_days(lookback_days, bars_per_day))
        self._baseline_capital: float | None = None
        # None (the default) leaves exits exactly as they were: fixed at
        # entry from grid.profit_targets. Set it and each lot's target
        # instead trails the peak that lot has reached -- see
        # src/trailing_target.py for why that matters at the wide
        # targets this strategy's sweeps selected.
        self.trail_pct = trail_pct
        self.trail_min_profit_target = trail_min_profit_target
        self._trailing = (
            TrailingTargetPolicy(trail_pct, min_profit_target=trail_min_profit_target)
            if trail_pct is not None
            else None
        )
        # See the module docstring's "dd_throttle_start / dd_throttle_full
        # / dd_throttle_floor" section. None (the default) is an exact
        # no-op, same convention as trail_pct above.
        self._dd_throttle_enabled = dd_throttle_start is not None
        if self._dd_throttle_enabled:
            if not 0.0 < dd_throttle_start < 1.0:
                raise ConfigurationError(
                    f"dd_throttle_start must be in (0, 1), got {dd_throttle_start}"
                )
            if not dd_throttle_start < dd_throttle_full <= 1.0:
                raise ConfigurationError(
                    f"dd_throttle_full must be in (dd_throttle_start, 1], got "
                    f"{dd_throttle_full} with dd_throttle_start={dd_throttle_start}"
                )
            if not 0.0 <= dd_throttle_floor <= 1.0:
                raise ConfigurationError(
                    f"dd_throttle_floor must be in [0, 1] -- this lever only sizes DOWN, "
                    f"got {dd_throttle_floor}"
                )
        self.dd_throttle_start = dd_throttle_start
        self.dd_throttle_full = dd_throttle_full
        self.dd_throttle_floor = dd_throttle_floor
        # See the module docstring's implied_vol_exponent section. 0.0 is
        # an exact no-op, so every existing config and recorded result is
        # unaffected.
        if implied_vol_scale_min <= 0.0 or implied_vol_scale_max < implied_vol_scale_min:
            raise ConfigurationError(
                f"need 0 < implied_vol_scale_min <= implied_vol_scale_max, got "
                f"{implied_vol_scale_min} and {implied_vol_scale_max}"
            )
        self.implied_vol_exponent = implied_vol_exponent
        self.implied_vol_scale_min = implied_vol_scale_min
        self.implied_vol_scale_max = implied_vol_scale_max

    def record_tick(self, context: MarketContext) -> None:
        """Advance the rolling high and capture the capital baseline,
        on EVERY bar -- both are properties of the market/portfolio
        state, not of this strategy's own trading, so gating either on
        a triggered bar would make them functions of `step`."""
        if self._baseline_capital is None and context.equity > 0:
            self._baseline_capital = context.equity
        if context.price > 0:
            self._rolling_high.update(context.price)
            # A fabricated bar from resample_to_uniform_minutes (see
            # module docstring's "SYNTHETIC BARS" section) is flat --
            # high==low==price -- AND unchanged from the previous real
            # print, because that is exactly what it carries forward.
            # Both conditions together are the detector, deliberately
            # NOT context.volume==0: on the live path volume is ALWAYS
            # 0.0 (LiveBar has no volume field), so gating on volume
            # would silently disable vol scaling in live trading
            # forever, not just on resampled backtests.
            #
            # This is a heuristic, not an exact test, and was measured
            # rather than assumed: on the real (non-resampled) extended-
            # hours dataset, 2.9% of genuine bars are ALSO flat and
            # unchanged (thin extended-hours liquidity, mostly), so this
            # skips a small number of real observations too. That is a
            # different, much smaller problem than the one this exists
            # to fix -- the false-positive rate is 2-5% in every year
            # measured (2016: 2.1%, 2019: 5.0%, 2023: 5.2%, 2026: 0.7%),
            # not the 52% -> 0.6% ramp the synthetic bars produced, so it
            # does not reintroduce a year-correlated bias. The correct
            # fix is giving the live path real volume (LiveBar has no
            # volume field today -- a separate, pre-existing gap), which
            # would let this reuse context.volume directly; not done
            # here because it touches the live data adapter.
            synthetic = is_synthetic_bar(
                context.high, context.low, context.price, self._prev_price
            )
            if self._vol_enabled and not synthetic:
                if self.vol_measure == "range":
                    # Intrabar range, scaled by price so the two windows
                    # compare across a dataset where TQQQ spans ~8x-90x.
                    # Measured to predict a forward 60-session trough
                    # better than the close-to-close form (-0.219 rank
                    # correlation against -0.172), and it is also what
                    # the intrabar fill model actually experiences.
                    self._fast_vol.update((context.high - context.low) / context.price)
                    self._slow_vol.update((context.high - context.low) / context.price)
                elif self._prev_price is not None and self._prev_price > 0:
                    # Log return, so the two windows measure the same
                    # thing at any price level.
                    log_return = log(context.price / self._prev_price)
                    self._fast_vol.update(log_return)
                    self._slow_vol.update(log_return)
            # Advances on every REAL price (this whole block is already
            # inside `if context.price > 0`) regardless of whether the
            # vol window updated -- kept outside the volume gate above
            # so a synthetic bar's flat price still becomes the
            # reference the NEXT real return is measured from, rather
            # than silently skipping a price update and measuring that
            # next return against a stale, older price.
            self._prev_price = context.price
            if self._volume_enabled and context.volume > 0:
                # 0.0 means "unknown" (the MarketContext default), not
                # "no volume", so an unpopulated feed must not be fed in
                # as a genuine zero -- that would drag the slow mean
                # toward nothing and blow the ratio up.
                self._fast_volume.update(context.volume)
                self._slow_volume.update(context.volume)

    def _vol_scale(self) -> float:
        """Size multiplier from short-horizon realized vol relative to
        its own longer-horizon baseline.

        Deliberately NOT constrained to >= 1.0, unlike the two event
        boosts. Those encode a measured claim (specific scheduled days
        are more volatile) and only ever size up. This encodes an open
        question -- whether to lean into volatility or away from it --
        and the evidence so far says drawdown, not return, is this
        strategy's binding constraint. A NEGATIVE exponent sizes down
        when volatility spikes, which is the classic vol-targeting
        direction and the one more likely to help; a positive exponent
        leans in, matching the event boosts. Sweeping across zero
        measures which is right instead of assuming.

        Returns 1.0 until both windows have enough observations, so the
        warm-up period behaves exactly as the unscaled strategy does.
        """
        if not self._vol_enabled:
            return 1.0
        fast = self._fast_vol.value
        slow = self._slow_vol.value
        # Guarded well above zero, not merely at it. RollingStdev's
        # running sum-of-squares leaves a residue of order 1e-11 on a
        # perfectly constant series rather than an exact 0.0, which
        # would clear a `> 0.0` test and then divide into an enormous
        # ratio that only the clamp contains. A realized vol this small
        # is not a signal at all -- per-bar log returns on this dataset
        # run around 1e-4 -- so treat it as "no estimate yet".
        if fast is None or slow is None or slow < _VOL_EPSILON or fast < _VOL_EPSILON:
            return 1.0
        return clamp(
            (fast / slow) ** self.vol_scale_exponent,
            self.vol_scale_min,
            self.vol_scale_max,
        )

    def _volume_scale(self) -> float:
        """Size multiplier from short-horizon volume relative to its own
        longer-horizon baseline.

        Volume is the one input this project already had and never used:
        historical_data.py has always loaded it and audit/monte_carlo
        carry it, but no strategy could see it until MarketContext gained
        the field.

        It is a WEAK signal on its own -- a volume surge scores -0.095
        against forward 60-session troughs, versus -0.219 for the range
        measure -- and it is included because it is only 0.36-0.49
        correlated with the volatility signals, so it is not merely those
        again. An exponent of 0.0 (the default) is an exact no-op, which
        is how it should stay unless a sweep shows it earning its place.

        Shares _vol_scale's clamp bounds rather than introducing its own:
        both are multipliers on the same lot, and four bound parameters
        for two bounded quantities would dilute a search budget for
        nothing.
        """
        if not self._volume_enabled:
            return 1.0
        fast = self._fast_volume.value
        slow = self._slow_volume.value
        if fast is None or slow is None or slow <= 0.0 or fast <= 0.0:
            return 1.0
        return clamp(
            (fast / slow) ** self.volume_scale_exponent,
            self.vol_scale_min,
            self.vol_scale_max,
        )

    def _time_of_day_scale(self, context: MarketContext) -> float:
        """Size multiplier from WHERE IN THE SESSION this bar falls.

        The static profile (src/intraday_profile.py) is normalized to
        mean 1.0, so an exponent of 0.0 is an exact no-op and needs no
        separate enable flag. Negative sizes down where the session is
        reliably volatile -- the first minutes, 10:00, the close --
        matching the direction the vol-ratio scaler measured as correct.

        This is deliberately NOT the same signal as _vol_scale. That one
        is backward-looking and lags: even a 0.25-day fast window is 97
        bars, so at 09:30 it is still mostly describing yesterday
        afternoon and cannot see the open's volatility until it is half
        over. This one is known exactly, in advance, from the clock.

        Outside the regular session the profile returns 1.0, so an
        extended-hours bar in the live path is left unscaled rather than
        being scaled by a number measured on a different regime.

        Clamped by fixed rails rather than tunable bounds: the profile's
        own range is 0.71-2.56, so for any |exponent| <= 1 the rails are
        not binding at all and exist only to stop an extreme exponent
        producing an absurd lot. Two more sweepable knobs for a bounded
        quantity would be noise in a search budget.
        """
        if not self._tod_enabled:
            return 1.0
        relative = relative_range(context.time_of_day_flag)
        return clamp(
            relative**self.time_of_day_exponent, _TOD_SCALE_FLOOR, _TOD_SCALE_CEIL
        )

    def _dd_throttle_scale(self, context: MarketContext) -> float:
        """Size multiplier from how deep INTO an extended drawdown the
        strategy already is, using context.drawdown -- the same
        peak-equity/drawdown figure optimization_controller.py tracks
        every bar and reports as "Max Drawdown %". See the module
        docstring's dd_throttle section for why this is a threshold-and-
        ramp rather than an exponent form, and why it only ever sizes
        down.

        Returns 1.0 (no-op) while off, and while the drawdown has not
        yet reached dd_throttle_start -- so a config that leaves this
        unset, or a run that never draws down past the threshold,
        behaves exactly as it did before this existed.
        """
        if not self._dd_throttle_enabled:
            return 1.0
        dd = context.drawdown
        if dd <= self.dd_throttle_start:
            return 1.0
        if dd >= self.dd_throttle_full:
            return self.dd_throttle_floor
        span = self.dd_throttle_full - self.dd_throttle_start
        frac = (dd - self.dd_throttle_start) / span
        return 1.0 - frac * (1.0 - self.dd_throttle_floor)

    def _implied_vol_scale(self, context: MarketContext) -> float:
        """Size multiplier from the last closed session's change in
        implied volatility -- context.implied_vol_change, in percent.

        A LINEAR response, not the exponent-on-a-ratio form _vol_scale
        uses, because the input is a signed CHANGE centred on zero
        rather than a strictly-positive ratio centred on one. Raising a
        possibly-negative number to a fractional power is undefined, so
        the ratio form is not merely awkward here, it is wrong:

            multiplier = clamp(1 + exponent * (change / 100), min, max)

        Sign is not assumed, exactly as _vol_scale's is not. A NEGATIVE
        exponent sizes down after implied vol jumps (the vol-targeting
        direction, and the one _vol_scale measured as correct for
        realized vol); a positive one leans in. Sweeping across zero
        measures which is right rather than encoding a guess.

        Returns 1.0 when the exponent is 0.0 (the default), and when no
        reading is available -- context.implied_vol_change is 0.0 both
        for "the index was flat" and for "no implied-vol file is
        configured", and leaving size unchanged is the right answer to
        both.
        """
        if self.implied_vol_exponent == 0.0:
            return 1.0
        return clamp(
            1.0 + self.implied_vol_exponent * (context.implied_vol_change / 100.0),
            self.implied_vol_scale_min,
            self.implied_vol_scale_max,
        )

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        """Trail this lot's exit target, when trail_pct is configured.

        Returns None (leave the target alone) when trailing is off,
        which is the default -- so this override changes nothing for any
        existing config or recorded sweep result."""
        if self._trailing is None:
            return None
        return self._trailing.propose(lot, context.price)

    def retain_lots(self, open_order_ids) -> None:
        """Release peak state for lots that have closed. See
        decision_cycle.adjust_open_lot_targets."""
        if self._trailing is not None:
            self._trailing.retain_lots(open_order_ids)

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
        # event_intensity (src/event_calendar.py) is a minute-precise,
        # index-weighted REFINEMENT of the same claim
        # is_earnings_reaction_day makes at day granularity -- "an
        # earnings-moving event is happening" -- not a new axis, so it
        # combines with max(), same as the other two above, rather than
        # multiplying (which would double-count a day this project has
        # BOTH day-level and minute-level knowledge of).
        #
        # Graded by weight, not a step function: at
        # weighted_event_boost_multiplier's default of 1.0 this is an
        # exact no-op; at the configured multiplier, event_intensity's
        # own scale (index-weight percent, e.g. NVDA alone = 8.50) sets
        # how much of that multiplier applies. A single non-tracked
        # symbol's release contributes 0.0 intensity and this evaluates
        # to boost's floor, same as an ordinary bar.
        if context.event_intensity > 0:
            weighted = 1.0 + (self.weighted_event_boost_multiplier - 1.0) * min(
                context.event_intensity, 100.0
            ) / 100.0
            boost = max(boost, weighted)
        # The event boost and the vol scaler MULTIPLY, unlike the two
        # event boosts which take a max of each other. Those two are
        # alternative labels for the same underlying claim ("today is a
        # scheduled announcement"), so compounding them would double-count
        # one effect. This is a different axis -- realized volatility
        # right now, measured rather than scheduled -- so a calm FOMC day
        # and a turbulent one are genuinely different situations.
        # _vol_scale is clamped, so the product stays bounded.
        return (
            value
            * boost
            * self._vol_scale()
            * self._time_of_day_scale(context)
            * self._volume_scale()
            * self._dd_throttle_scale(context)
            # MULTIPLIES rather than max()-ing with the event boosts. It
            # is a genuinely independent axis, and that was measured, not
            # asserted: holding trailing realized vol fixed, this change
            # still scores partial rho +0.257 against next-session
            # opening volatility (tools/measure_vol_signal.py). It says
            # something the other scalers do not. Clamped, so the product
            # stays bounded.
            * self._implied_vol_scale(context)
        )
