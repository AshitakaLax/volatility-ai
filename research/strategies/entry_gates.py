"""
Entry-suppression gates: reasons NOT to open a new lot right now.

A gate never sells, never resizes, and never touches an open lot. It
answers one question per bar -- may the grid buy at all? -- and the
strategy that owns it turns "no" into a trigger level no price can
reach. Nothing here can realize a loss, so nothing here needs
`execution.allow_signal_exit`, and engine/trading/no_loss_guard.py is
untouched by construction.

--------------------------------------------------------------------
WHY A GATE, WHEN SIZING LEVERS ALREADY EXIST

Every lever in high_frequency_sizing.py makes a lot SMALLER: the vol
ratio, volume, time of day, dd_throttle. None can make it zero on the
specific bars where a buy is most likely to be stranded. That matters
because of the mechanism the dd_throttle docstring spells out: under the
no-loss guard, each lot bought on the way down a trend day can only exit
once price recovers past that lot's own basis. A lot never opened needs
no recovery.

The two gates here come from the intraday breakout literature, turned
around. A breakout strategy reads a downside break as "go short". This
system is long-only by design, so the same signal is read as "stop
buying until the break is undone":

  BreakdownGate     -- Dual Thrust (je-suis-tm/quant-trading #7, rules
                       per QuantConnect), an opening-range variant of
                       the London Breakout (#4), and a gap below the
                       prior session's low.
  ShootingStarGate  -- the shooting-star reversal (#17), made causal.

UNMEASURED. These are registered so they can be swept, not because any
result supports them yet. See config/probe_entry_gate_*.yaml.

--------------------------------------------------------------------
CAUSALITY: A DECISION FOR BAR t USES BARS < t PLUS BAR t's OPEN

record_tick receives a COMPLETED bar -- its high, low and close are
already known. Under fill_model="intrabar" the engine then asks whether
that same bar's LOW touched the trigger level. A gate that read bar t's
close to decide whether bar t may buy would be using how the bar ended
to rule on something that happened inside it.

So every gate here, on each call:

  1. folds the PREVIOUS bar's high/low/close into its aggregates,
  2. evaluates against THIS bar's open -- the one part of bar t that is
     known when bar t starts -- and
  3. holds this bar back as pending until the next call.

Under fill_model="close" that is one bar conservative. Under "intrabar"
it is the only reading that is not lookahead. The live loop calls
record_tick once per completed bar exactly as the backtest does, so the
same rule holds there.

The reference implementations are NOT causal and are not copied
literally. quant-trading's shooting star confirms with the NEXT bar
(`shift(-1)`) and sizes the body against a FULL-SAMPLE mean
(`np.mean(df['Open'] - df['Close'])`). Both are fixed below -- see
ShootingStarGate.

--------------------------------------------------------------------
SESSIONS

A session is keyed by `timestamp.toordinal()`, on regular-session bars
only (time_of_day_flag >= 0). For a regular-session bar the UTC date and
the Eastern date agree -- 09:30-16:00 Eastern never crosses UTC
midnight -- which is the same reason optimization_controller.py's
settlement clock can use toordinal() directly.

Bars outside the session (time_of_day_flag == -1) are ignored: they move
no aggregate and change no state, so the last regular-session state
stands until the next open. The default dataset is regular-hours only
and the live loop only ticks while the market is open, so this matters
only for a dataset fetched with --include-extended-hours.

A path that never populates time_of_day_flag leaves it at 0 on every
bar. Sessions still roll correctly (they key on the date), but the
opening range never completes (minute 0 is never >= orb_minutes) and
each pattern candle spans a whole session. Both are inert-or-coarse
failures, never a gate stuck shut.

--------------------------------------------------------------------
SYNTHETIC BARS

resample_to_uniform_minutes fills empty minutes with flat carry-forward
bars (engine/data/synthetic_bars.py). Folding one into a high, low or
close aggregate changes nothing -- its price IS the previous print -- and
its open equals the previous close, so evaluating against it repeats the
previous bar's reading. No detector is needed here, unlike the vol
windows, which a run of flat bars would drag toward zero.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.sizing_indicators import RollingMean

BREAKDOWN_MODES: tuple[str, ...] = ("off", "dual_thrust", "opening_range", "prior_low")
RELEASE_MODES: tuple[str, ...] = ("reclaim", "session")
PATTERN_MODES: tuple[str, ...] = ("off", "shooting_star")
MOMENTUM_MODES: tuple[str, ...] = ("off", "early_negative")
SESSION_MINUTES = 390  # 09:30-16:00; a half-day never reaches a late window


def as_count(name: str, value, minimum: int = 1) -> int:
    """An integer constructor argument, accepting an integral float.

    Not pedantry. research/analysis/analyze_annual.py rebuilds a
    strategy from a sweep CSV row, and pandas reads an integer column
    back as float64 the moment any row in the file leaves it blank --
    which every hf_local_reference row in a merged output/ directory
    does for these columns. 5.0 must mean 5; 5.5 must fail loudly rather
    than truncate.
    """
    if isinstance(value, bool):
        raise ConfigurationError(f"{name} must be an integer, got {value!r}")
    if isinstance(value, float):
        if not value.is_integer():
            raise ConfigurationError(f"{name} must be a whole number, got {value!r}")
        value = int(value)
    if not isinstance(value, int):
        raise ConfigurationError(f"{name} must be an integer, got {value!r}")
    if value < minimum:
        raise ConfigurationError(f"{name} must be >= {minimum}, got {value}")
    return value


def _regular_session_minute(context: MarketContext) -> int | None:
    """Minutes since 09:30 Eastern, or None for an out-of-session bar."""
    minute = context.time_of_day_flag
    return minute if minute >= 0 else None


class BreakdownGate:
    """Block new buys once price trades below a session-relative level.

    Three ways to place the level, one shared state machine:

      dual_thrust    session open - dt_k * range, where range is
                     max(HH - LC, HC - LL) over the previous
                     dt_lookback_days completed sessions (HH/LL = highest
                     high / lowest low, HC/LC = highest / lowest close).
                     This is exactly the lower band of the Dual Thrust
                     rules, with its short entry read as "stop buying".
      opening_range  the low of the first orb_minutes of the session.
                     None -- no gating -- until the range has formed.
                     The London Breakout's pre-open window, mapped onto a
                     regular-hours-only dataset.
      prior_low      the previous session's low. Unlike the other two,
                     this can fire on the session's FIRST bar: a gap
                     below yesterday's low is known at the open.

    Release, either way it fired:

      reclaim   buys resume once a bar opens back above the level.
      session   buys stay blocked for the rest of the session.

    Every session starts unblocked. A multi-day correction that breaks
    down every day is gated every day, but each day earns it afresh --
    the gate never carries a breakdown overnight.
    """

    def __init__(
        self,
        mode: str = "off",
        *,
        release: str = "reclaim",
        dt_lookback_days: int = 5,
        dt_k: float = 0.5,
        orb_minutes: int = 30,
    ) -> None:
        if mode not in BREAKDOWN_MODES:
            raise ConfigurationError(
                f"breakdown_gate must be one of {BREAKDOWN_MODES}, got {mode!r}"
            )
        if release not in RELEASE_MODES:
            raise ConfigurationError(
                f"breakdown_release must be one of {RELEASE_MODES}, got {release!r}"
            )
        if dt_k <= 0.0:
            raise ConfigurationError(f"dt_k must be > 0, got {dt_k}")
        self.mode = mode
        self.release = release
        self.dt_lookback_days = as_count("dt_lookback_days", dt_lookback_days)
        self.dt_k = float(dt_k)
        # 390 is the whole session: a range that never completes would be
        # a silent no-op dressed as a configuration.
        self.orb_minutes = as_count("orb_minutes", orb_minutes)
        if self.orb_minutes >= 390:
            raise ConfigurationError(
                f"orb_minutes must be < 390 (one session), got {self.orb_minutes}"
            )

        depth = self.dt_lookback_days if mode == "dual_thrust" else 1
        self._history: deque[tuple[float, float, float]] = deque(maxlen=depth)
        self._day: int | None = None
        self._pending: tuple[int, float, float, float] | None = None
        self._sess_high: float | None = None
        self._sess_low: float | None = None
        self._sess_close: float | None = None
        self._or_high: float | None = None
        self._or_low: float | None = None
        self._level: float | None = None
        self._suppressed = False
        # Diagnostics only -- nothing reads these to decide anything.
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def suppressed(self) -> bool:
        return self._suppressed

    @property
    def level(self) -> float | None:
        """Today's breakdown level, or None while it is undefined."""
        return self._level

    def observe(self, context: MarketContext) -> None:
        """Advance one bar. Call once per bar, from record_tick."""
        if not self.enabled:
            return
        minute = _regular_session_minute(context)
        if minute is None:
            return

        # 1. The previous bar is complete now; fold it BEFORE any session
        #    roll, so a session's last bar lands in that session's range.
        if self._pending is not None:
            self._fold(*self._pending)
            self._pending = None

        day = context.timestamp.toordinal()
        if day != self._day:
            self._start_session(day, context.open)
        elif (
            self.mode == "opening_range"
            and self._level is None
            and self._or_low is not None
            and minute >= self.orb_minutes
        ):
            # Every bar inside the window is strictly earlier than this
            # one and has just been folded, so the range is complete.
            self._level = self._or_low

        # 2. Decide against this bar's OPEN -- see module docstring.
        self._evaluate(context.open)
        if self._suppressed:
            self.suppressed_bars += 1

        # 3. Hold this bar back until it is history.
        self._pending = (minute, context.high, context.low, context.close)

    def _fold(self, minute: int, high: float, low: float, close: float) -> None:
        self._sess_high = high if self._sess_high is None else max(self._sess_high, high)
        self._sess_low = low if self._sess_low is None else min(self._sess_low, low)
        self._sess_close = close
        if self.mode == "opening_range" and minute < self.orb_minutes:
            self._or_high = high if self._or_high is None else max(self._or_high, high)
            self._or_low = low if self._or_low is None else min(self._or_low, low)

    def _start_session(self, day: int, session_open: float) -> None:
        if self._sess_high is not None:
            self._history.append((self._sess_high, self._sess_low, self._sess_close))
        self._day = day
        self._sess_high = self._sess_low = self._sess_close = None
        self._or_high = self._or_low = None
        self._suppressed = False
        self._level = self._session_level(session_open)

    def _session_level(self, session_open: float) -> float | None:
        if self.mode == "dual_thrust":
            if len(self._history) < self.dt_lookback_days:
                return None
            highs = [h for h, _, _ in self._history]
            lows = [lo for _, lo, _ in self._history]
            closes = [c for _, _, c in self._history]
            span = max(max(highs) - min(closes), max(closes) - min(lows))
            return session_open - self.dt_k * span
        if self.mode == "prior_low":
            return self._history[-1][1] if self._history else None
        # opening_range: set once the window has formed, in observe().
        return None

    def _evaluate(self, price: float) -> None:
        if self._level is None:
            return
        if not self._suppressed:
            if price < self._level:
                self._suppressed = True
                self.episodes += 1
        elif self.release == "reclaim" and price > self._level:
            self._suppressed = False


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float


def is_shooting_star(
    star: Candle,
    prior1: Candle,
    prior2: Candle,
    confirm: Candle,
    typical_body: float | None,
    lower_shadow: float,
    body_size: float,
) -> bool:
    """The eight shooting-star conditions from je-suis-tm/quant-trading,
    evaluated causally.

    `prior2`, `prior1`, `star`, `confirm` are four CONSECUTIVE completed
    candles, oldest first. The original's conditions 7-8 read the bar
    AFTER the star through shift(-1); here that bar is `confirm`, and
    the caller only asks once `confirm` has itself completed -- so the
    signal lands one candle later than the original plots it, which is
    when it could actually have been known.

    `typical_body` replaces the original's
    `abs(np.mean(df['Open'] - df['Close']))`, which is a FULL-SAMPLE
    mean of the SIGNED body. Full-sample is lookahead; signed is also
    close to zero on any long series (up and down candles cancel),
    which makes "body smaller than half of it" nearly unsatisfiable. A
    trailing mean of the ABSOLUTE body, as a fraction of price, is what
    the condition evidently means. None (unwarmed) means no signal.
    """
    if typical_body is None or star.open <= 0:
        return False
    body = star.open - star.close
    return (
        body >= 0  # 1. bearish (or flat) body
        and (star.close - star.low) < lower_shadow * body  # 2. ~no lower shadow
        and body / star.open < body_size * typical_body  # 3. small body
        and (star.high - star.open) >= 2 * body  # 4. long upper shadow
        and star.close >= prior1.close  # 5-6. into it on a rise
        and prior1.close >= prior2.close
        and confirm.high <= star.high  # 7-8. not undone next candle
        and confirm.close <= star.close
    )


class ShootingStarGate:
    """Block new buys after a confirmed shooting star on N-minute candles.

    One-minute candles are mostly noise for a pattern defined on daily
    bars, so regular-session bars are aggregated into candle_minutes
    buckets aligned to the open (09:30, 10:00, ... for 30). A candle is
    complete when the first bar of the NEXT bucket arrives.

    Once a star is confirmed, buys are blocked until either:

      * hold_candles more candles complete, or
      * a bar opens above the star's high -- the reversal is undone.

    Candles never span sessions, and a block expires at the session end.
    A star whose confirming candle is the session's last one is
    therefore never acted on: by the time it could be known, the next
    session has opened.
    """

    def __init__(
        self,
        mode: str = "off",
        *,
        candle_minutes: int = 30,
        hold_candles: int = 4,
        lower_shadow: float = 0.2,
        body_size: float = 0.5,
        body_lookback: int = 20,
    ) -> None:
        if mode not in PATTERN_MODES:
            raise ConfigurationError(f"pattern_gate must be one of {PATTERN_MODES}, got {mode!r}")
        if lower_shadow <= 0.0:
            raise ConfigurationError(f"pattern_lower_shadow must be > 0, got {lower_shadow}")
        if body_size <= 0.0:
            raise ConfigurationError(f"pattern_body_size must be > 0, got {body_size}")
        self.mode = mode
        self.candle_minutes = as_count("pattern_candle_minutes", candle_minutes)
        if self.candle_minutes > 195:
            # Fewer than two candles a session can never show the four
            # consecutive candles the pattern needs.
            raise ConfigurationError(
                f"pattern_candle_minutes must be <= 195, got {self.candle_minutes}"
            )
        self.hold_candles = as_count("pattern_hold_candles", hold_candles)
        self.lower_shadow = float(lower_shadow)
        self.body_size = float(body_size)
        self.body_lookback = as_count("pattern_body_lookback", body_lookback)

        self._bodies = RollingMean(self.body_lookback)
        self._day: int | None = None
        self._pending: tuple[tuple[int, int], float, float, float, float] | None = None
        self._building: list[float] | None = None
        self._building_bucket: tuple[int, int] | None = None
        # (candle, typical body BEFORE this candle) for the current session.
        self._candles: deque[tuple[Candle, float | None]] = deque(maxlen=4)
        self._suppressed = False
        self._star_high: float | None = None
        self._hold_remaining = 0
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def suppressed(self) -> bool:
        return self._suppressed

    def observe(self, context: MarketContext) -> None:
        """Advance one bar. Call once per bar, from record_tick."""
        if not self.enabled:
            return
        minute = _regular_session_minute(context)
        if minute is None:
            return
        day = context.timestamp.toordinal()
        bucket = (day, minute // self.candle_minutes)

        # 1. Fold the previous bar into the candle it belongs to.
        if self._pending is not None:
            pending_bucket, o, h, lo, c = self._pending
            self._pending = None
            if self._building is None:
                self._building = [o, h, lo, c]
                self._building_bucket = pending_bucket
            else:
                self._building[1] = max(self._building[1], h)
                self._building[2] = min(self._building[2], lo)
                self._building[3] = c

        # That bar was its candle's last if this one starts a new bucket.
        if self._building is not None and bucket != self._building_bucket:
            self._complete_candle()

        if day != self._day:
            self._day = day
            self._candles.clear()
            self._suppressed = False
            self._star_high = None
            self._hold_remaining = 0

        # 2. Invalidation, against this bar's open.
        if self._suppressed and self._star_high is not None and context.open > self._star_high:
            self._suppressed = False
        if self._suppressed:
            self.suppressed_bars += 1

        # 3. Hold this bar back until it is history.
        self._pending = (bucket, context.open, context.high, context.low, context.close)

    def _complete_candle(self) -> None:
        o, h, lo, c = self._building
        self._building = None
        self._building_bucket = None
        candle = Candle(o, h, lo, c)

        # The typical body is measured BEFORE this candle joins it, so a
        # star is never compared against an average that includes itself.
        typical = self._bodies.value if self._bodies.count >= self.body_lookback else None
        if o > 0:
            self._bodies.update(abs(o - c) / o)
        self._candles.append((candle, typical))

        if self._suppressed:
            self._hold_remaining -= 1
            if self._hold_remaining <= 0:
                self._suppressed = False
                self._star_high = None

        if len(self._candles) == 4:
            (p2, _), (p1, _), (star, star_typical), (confirm, _) = self._candles
            if is_shooting_star(
                star, p1, p2, confirm, star_typical, self.lower_shadow, self.body_size
            ):
                self._suppressed = True
                self._star_high = star.high
                self._hold_remaining = self.hold_candles
                self.episodes += 1


class IntradayMomentumGate:
    """Block buys late in a session that started badly.

    Gao, Han, Li & Zhou, "Market Intraday Momentum" (Journal of Financial
    Economics, 2018): the return from the previous close to the end of
    the first half hour predicts the last half hour's, more strongly on
    volatile days. This system is long-only, so the usable half is the
    negative one: when the early window closed below the previous
    session's close by more than `threshold`, the last `late_minutes`
    are expected to keep falling, and buying into them adds lots the
    no-loss guard can only exit after a recovery.

      early return = close at the end of the first early_minutes
                     / previous session's last close - 1
      blocked      = minute >= 390 - late_minutes  and
                     early return < -threshold

    Causal like the other gates: the early return becomes known at the
    start of the first bar after the early window (the window's last bar
    is folded then), long before the late window it governs. It clears
    at the session end. Half-days (13:00 close) never reach a late window
    of a 390-minute session, so the gate is inert on them.
    """

    def __init__(
        self,
        mode: str = "off",
        *,
        early_minutes: int = 30,
        late_minutes: int = 30,
        threshold: float = 0.0,
    ) -> None:
        if mode not in MOMENTUM_MODES:
            raise ConfigurationError(f"momentum_gate must be one of {MOMENTUM_MODES}, got {mode!r}")
        if threshold < 0.0:
            raise ConfigurationError(f"momentum_threshold must be >= 0, got {threshold}")
        self.mode = mode
        self.early_minutes = as_count("momentum_early_minutes", early_minutes)
        self.late_minutes = as_count("momentum_late_minutes", late_minutes)
        if self.early_minutes + self.late_minutes > SESSION_MINUTES:
            raise ConfigurationError(
                "momentum_early_minutes + momentum_late_minutes must fit in one "
                f"{SESSION_MINUTES}-minute session"
            )
        self.threshold = float(threshold)
        self._late_start = SESSION_MINUTES - self.late_minutes
        self._day: int | None = None
        self._pending: tuple[int, float] | None = None
        self._last_close: float | None = None
        self._prev_session_close: float | None = None
        self._early_close: float | None = None
        self._early_return: float | None = None
        self._suppressed = False
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def suppressed(self) -> bool:
        return self._suppressed

    @property
    def early_return(self) -> float | None:
        """This session's early-window return, once known."""
        return self._early_return

    def observe(self, context: MarketContext) -> None:
        """Advance one bar. Call once per bar, from record_tick."""
        if not self.enabled:
            return
        minute = _regular_session_minute(context)
        if minute is None:
            return
        # 1. Fold the previous bar -- BEFORE any session roll, so the
        #    previous session's last close is the reference for this one.
        if self._pending is not None:
            pending_minute, pending_close = self._pending
            self._pending = None
            self._last_close = pending_close
            if pending_minute < self.early_minutes:
                self._early_close = pending_close
        day = context.timestamp.toordinal()
        if day != self._day:
            self._day = day
            self._prev_session_close = self._last_close
            self._early_close = None
            self._early_return = None
            self._suppressed = False
        # 2. The early window is complete once a bar starts after it.
        if (
            self._early_return is None
            and minute >= self.early_minutes
            and self._early_close is not None
            and self._prev_session_close
        ):
            self._early_return = self._early_close / self._prev_session_close - 1.0
        was = self._suppressed
        self._suppressed = (
            minute >= self._late_start
            and self._early_return is not None
            and self._early_return < -self.threshold
        )
        if self._suppressed and not was:
            self.episodes += 1
        if self._suppressed:
            self.suppressed_bars += 1
        # 3. Hold this bar back until it is history.
        self._pending = (minute, context.close)


__all__ = [
    "BREAKDOWN_MODES",
    "MOMENTUM_MODES",
    "PATTERN_MODES",
    "RELEASE_MODES",
    "SESSION_MINUTES",
    "BreakdownGate",
    "Candle",
    "IntradayMomentumGate",
    "ShootingStarGate",
    "as_count",
    "is_shooting_star",
]
