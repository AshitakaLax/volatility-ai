"""
The sell-policy library (Phase 3 of docs/research/buy-sell-composition.md).
Each policy is one answer to "when to sell, and how much", pairable with any
buy policy through ComposedStrategy. UNMEASURED: none has been swept.

NO-LOSS TRACK -- every sale is a target harvest the no-loss guard checks, so
none of these can realise a loss under any parameters:

  age_decay            a lot's target falls linearly to a floor once it has
                       been held long enough (harvest_sleeve's target decay)
  vol_scaled_target    each lot's target set at entry from trailing realised
                       volatility, clipped to [min_target, max_target]
  inventory_pressure   targets lowered as the open book grows, so a stuck
                       inventory is worked down at smaller gains
  scale_out            PARTIAL: sell the lot in tranches, each at its own target
  scale_out_trail      PARTIAL: sell part at a fixed target, trail the rest
  signal_take_profit   when a signal-library gate shuts (its bearish reading),
                       sell lots already above a minimum gain at the market

LOSS-CAPABLE TRACK -- signal exits, behind execution.allow_signal_exit:

  regime_exit          every lot sold when the causal NATR regime turns
                       turbulent (regime_sleeve's exit)
  regime_exit_partial  PARTIAL: a fraction of every lot's shares on that flip

Restart safety: a policy's per-lot state is either derived from the lot
(shares / original_shares, its current target) or rebuilt in resume(open_lots),
which the live loop calls with the durable book before the first tick.
"""

from __future__ import annotations

import math
from collections import deque
from datetime import date
from itertools import pairwise

from engine.core.exceptions import ConfigurationError
from engine.core.exit_policy import ExitOrder
from engine.core.market_context import MarketContext
from research.composition.exits import RUNG_TOLERANCE, ExitPolicy, register
from research.optimization.trailing_target import TrailingTargetPolicy

SESSION_MINUTES = 390


def _positive(name: str, value) -> float:
    value = float(value)
    if not (math.isfinite(value) and value > 0):
        raise ConfigurationError(f"{name} must be a positive number, got {value}")
    return value


def _count(name: str, value, minimum: int = 1) -> int:
    if isinstance(value, bool) or int(value) != value or value < minimum:
        raise ConfigurationError(f"{name} must be an integer >= {minimum}, got {value!r}")
    return int(value)


def _fraction(name: str, value) -> float:
    value = float(value)
    if not 0 < value <= 1:
        raise ConfigurationError(f"{name} must be in (0, 1], got {value}")
    return value


class _NewLots:
    """Whether this bar is the first to see a lot bought on the bar before --
    the only bar a policy that sets a lot's target ONCE needs to look."""

    def __init__(self) -> None:
        self._prev = 0
        self.new = False

    def observe(self, context: MarketContext) -> None:
        lots = int(context.open_lot_count)
        self.new = lots > self._prev
        self._prev = lots


# --------------------------------------------------------------- no-loss track


class AgeDecay(ExitPolicy):
    """A lot's target, unchanged for `after_bars` bars, then falling linearly
    over `span_bars` to `floor` -- harvest_sleeve_sizing's target decay as a
    policy of its own. Checked on a lot's first bar and every `check_bars`."""

    exit_id = "age_decay"
    label = "Target decays with age"

    def __init__(
        self,
        after_bars: int = 390,
        span_bars: int = 390,
        floor: float = 0.001,
        check_bars: int = 15,
    ) -> None:
        self.after_bars = _count("after_bars", after_bars, 0)
        self.span_bars = _count("span_bars", span_bars)
        self.floor = _positive("floor", floor)
        self.check_bars = _count("check_bars", check_bars)
        self._bar = 0
        self._lots = _NewLots()
        self._births: dict[str, tuple[int, float]] = {}
        self.retargets = 0

    def record_tick(self, context: MarketContext) -> None:
        self._bar += 1
        self._lots.observe(context)

    def wants_lot_retargeting(self) -> bool:
        return self._lots.new or self._bar % self.check_bars == 0

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        info = self._births.get(lot.order_id)
        if info is None:
            info = (self._bar, float(lot.profit_target))
            self._births[lot.order_id] = info
        age = self._bar - info[0]
        if age <= self.after_bars:
            return None
        frac = min(1.0, (age - self.after_bars) / self.span_bars)
        original = info[1]
        decayed = original - (original - self.floor) * frac
        if decayed < float(lot.profit_target) - 1e-12:
            self.retargets += 1
            return max(decayed, self.floor)
        return None

    def retain_lots(self, open_order_ids) -> None:
        if self._births:
            keep = set(open_order_ids)
            self._births = {k: v for k, v in self._births.items() if k in keep}

    def resume(self, open_lots) -> None:
        """A restarted process counts each open lot's age from now, at the
        target it carries -- a decayed lot keeps what it reached and decays
        on from there, never back up."""
        for lot in open_lots:
            self._births.setdefault(lot.order_id, (self._bar, float(lot.profit_target)))

    def diagnostics(self) -> dict:
        return {"retargets": self.retargets}


class VolScaledTarget(ExitPolicy):
    """Each lot's target, set once on its first bar: `k` times the trailing
    per-bar volatility (stdev of log returns over `window_bars`, through the
    PREVIOUS bar, so never this bar's own move) scaled to `horizon_bars`,
    clipped to [min_target, max_target]. Calm markets take small gains,
    volatile ones wait for big ones."""

    exit_id = "vol_scaled_target"
    label = "Volatility-scaled target"

    def __init__(
        self,
        k: float = 1.0,
        window_bars: int = 390,
        horizon_bars: int = 390,
        min_target: float = 0.002,
        max_target: float = 0.2,
    ) -> None:
        self.k = _positive("k", k)
        self.window_bars = _count("window_bars", window_bars, 2)
        self.horizon_bars = _count("horizon_bars", horizon_bars)
        self.min_target = _positive("min_target", min_target)
        self.max_target = _positive("max_target", max_target)
        if self.max_target < self.min_target:
            raise ConfigurationError("max_target must be >= min_target")
        self._returns: deque = deque(maxlen=self.window_bars)
        self._prev_close: float | None = None
        self._sigma: float | None = None
        self._lots = _NewLots()
        self._known: set[str] = set()

    def record_tick(self, context: MarketContext) -> None:
        self._lots.observe(context)
        # sigma through the previous bar, THEN add this bar's return.
        if len(self._returns) >= 2:
            n = len(self._returns)
            mean = sum(self._returns) / n
            self._sigma = math.sqrt(sum((r - mean) ** 2 for r in self._returns) / (n - 1))
        close = float(context.close)
        if self._prev_close and close > 0:
            self._returns.append(math.log(close / self._prev_close))
        self._prev_close = close

    def target_for(self, sigma: float) -> float:
        raw = self.k * sigma * math.sqrt(self.horizon_bars)
        return min(self.max_target, max(self.min_target, raw))

    def wants_lot_retargeting(self) -> bool:
        return self._lots.new

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        if lot.order_id in self._known:
            return None
        self._known.add(lot.order_id)
        if self._sigma is None:
            return None  # too early to measure: the grid's own target stands
        return self.target_for(self._sigma)

    def retain_lots(self, open_order_ids) -> None:
        if len(self._known) > 2 * len(open_order_ids) + 64:
            self._known &= set(open_order_ids)

    def resume(self, open_lots) -> None:
        """Lots already open were targeted when they were bought."""
        self._known.update(lot.order_id for lot in open_lots)


class InventoryPressure(ExitPolicy):
    """Targets lowered as the open book grows: from `start_lots` open lots
    each lot's target moves toward `floor`, reaching it at `full_lots`.
    Ratchets down only, so a book that shrinks again keeps the lower targets
    (and sells them sooner) rather than stranding them again."""

    exit_id = "inventory_pressure"
    label = "Lower targets as inventory grows"

    def __init__(self, start_lots: int = 50, full_lots: int = 200, floor: float = 0.001) -> None:
        self.start_lots = _count("start_lots", start_lots)
        self.full_lots = _count("full_lots", full_lots)
        if self.full_lots <= self.start_lots:
            raise ConfigurationError("full_lots must be greater than start_lots")
        self.floor = _positive("floor", floor)
        self._open = 0
        self._base: dict[str, float] = {}

    def record_tick(self, context: MarketContext) -> None:
        self._open = int(context.open_lot_count)

    def pressure(self) -> float:
        span = self.full_lots - self.start_lots
        return min(1.0, max(0.0, (self._open - self.start_lots) / span))

    def wants_lot_retargeting(self) -> bool:
        return self._open >= self.start_lots

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        base = self._base.setdefault(lot.order_id, float(lot.profit_target))
        target = max(self.floor, base - (base - self.floor) * self.pressure())
        return target if target < float(lot.profit_target) - 1e-12 else None

    def retain_lots(self, open_order_ids) -> None:
        if len(self._base) > 2 * len(open_order_ids) + 64:
            keep = set(open_order_ids)
            self._base = {k: v for k, v in self._base.items() if k in keep}


def parse_rungs(text: str) -> list[tuple[float, float]]:
    """ "0.5@0.01,0.5@0.03" -> [(0.5, 0.01), (0.5, 0.03)]: (fraction of the
    lot, profit target) per rung, in selling order. A string, not a list,
    because a list in strategy_params is always a sweep axis."""
    rungs = []
    for part in str(text).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            fraction, target = (float(x) for x in part.split("@"))
        except ValueError:
            raise ConfigurationError(
                f"rung {part!r} must be <fraction>@<target>, e.g. 0.5@0.01"
            ) from None
        rungs.append((_fraction("rung fraction", fraction), _positive("rung target", target)))
    if not rungs:
        raise ConfigurationError("scale_out needs at least one rung")
    if abs(sum(f for f, _ in rungs) - 1.0) > 1e-6:
        raise ConfigurationError(f"rung fractions must add up to 1, got {sum(f for f, _ in rungs)}")
    targets = [t for _, t in rungs]
    if any(b < a for a, b in pairwise(targets)):
        raise ConfigurationError("rung targets must not fall from one rung to the next")
    return rungs


class ScaleOut(ExitPolicy):
    """Sell each lot in tranches: `rungs` "0.5@0.01,0.5@0.03" sells half at +1%
    and the rest at +3%. The rung a lot is on is read from how much of it has
    sold (shares / original_shares), so it survives a restart with nothing
    remembered. The grid's profit target is replaced by the first rung's.

    min_tranche_notional: a tranche, or what it would leave behind, worth less
    than this many dollars sells the whole remainder instead -- a per-trade
    commission or a broker minimum makes dust tranches a loss of their own."""

    exit_id = "scale_out"
    label = "Scale out in tranches"

    def __init__(self, rungs: str = "0.5@0.01,0.5@0.03", min_tranche_notional: float = 0.0) -> None:
        self.rungs = str(rungs)
        self._rungs = parse_rungs(rungs)
        self._cumulative = []
        total = 0.0
        for fraction, _ in self._rungs:
            total += fraction
            self._cumulative.append(total)
        self.min_tranche_notional = float(min_tranche_notional)
        if self.min_tranche_notional < 0:
            raise ConfigurationError("min_tranche_notional must be >= 0")

    def rung(self, lot) -> int:
        sold = lot.sold_fraction
        for index, cumulative in enumerate(self._cumulative):
            if sold < cumulative - RUNG_TOLERANCE:
                return index
        return len(self._rungs) - 1

    def wants_lot_retargeting(self) -> bool:
        return True

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        target = self._rungs[self.rung(lot)][1]
        return target if abs(target - float(lot.profit_target)) > 1e-12 else None

    def harvest_quantity(self, lot, context: MarketContext) -> float:
        index = self.rung(lot)
        if index == len(self._rungs) - 1:
            return lot.shares
        qty = (self._cumulative[index] - lot.sold_fraction) * lot.original_shares
        if self.min_tranche_notional > 0:
            price = float(context.price)
            if qty * price < self.min_tranche_notional:
                return lot.shares
            if (lot.shares - qty) * price < self.min_tranche_notional:
                return lot.shares
        return qty


class ScaleOutTrail(ExitPolicy):
    """Sell `first_fraction` of each lot at `first_target`, then let the rest
    run: its target is lifted to `runner_target` and trails the best price
    the lot has reached by `trail_pct` (ratcheting down only, never below
    `min_profit_target`) -- research/optimization/trailing_target.py."""

    exit_id = "scale_out_trail"
    label = "Scale out, then trail the rest"

    def __init__(
        self,
        first_fraction: float = 0.5,
        first_target: float = 0.01,
        trail_pct: float = 0.01,
        min_profit_target: float = 0.002,
        runner_target: float = 0.5,
    ) -> None:
        self.first_fraction = _fraction("first_fraction", first_fraction)
        if self.first_fraction >= 1:
            raise ConfigurationError("first_fraction must leave something to trail (< 1)")
        self.first_target = _positive("first_target", first_target)
        self.runner_target = _positive("runner_target", runner_target)
        if self.runner_target <= self.first_target:
            raise ConfigurationError("runner_target must be above first_target")
        self.trail_pct = trail_pct
        self.min_profit_target = min_profit_target
        self._trailing = TrailingTargetPolicy(trail_pct, min_profit_target=min_profit_target)
        self._runners: set[str] = set()

    def _is_runner(self, lot) -> bool:
        return lot.sold_fraction >= self.first_fraction - RUNG_TOLERANCE

    def wants_lot_retargeting(self) -> bool:
        return True

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        if not self._is_runner(lot):
            self._trailing.observe(lot, float(context.price))  # the peak counts from entry
            target = self.first_target
            return target if abs(target - float(lot.profit_target)) > 1e-12 else None
        if lot.order_id not in self._runners:
            self._runners.add(lot.order_id)
            return self.runner_target
        return self._trailing.propose(lot, float(context.price))

    def harvest_quantity(self, lot, context: MarketContext) -> float:
        if self._is_runner(lot):
            return lot.shares
        return (self.first_fraction - lot.sold_fraction) * lot.original_shares

    def retain_lots(self, open_order_ids) -> None:
        self._trailing.retain_lots(open_order_ids)
        if len(self._runners) > 2 * len(open_order_ids) + 64:
            self._runners &= set(open_order_ids)

    def resume(self, open_lots) -> None:
        """A lot already past its first tranche is a runner whose target was
        lifted (and may have trailed down since): never lift it again."""
        self._runners.update(lot.order_id for lot in open_lots if self._is_runner(lot))


class SignalTakeProfit(ExitPolicy):
    """When a signal-library GATE shuts -- its reading that buying should
    pause -- sell `fraction` of every lot already up at least
    `min_gain`, at the market: its target is moved to the current price, so
    the harvest takes it as a profit-target sale the no-loss guard checks. A
    lot below `min_gain` keeps its target. With fraction < 1 the rest goes
    back to the target it had.

    Which gate matters: a mean-reversion gate (zscore, bollinger -- the
    default is zscore) shuts when price is stretched HIGH, which is when a
    take-profit has lots in profit to sell; a trend gate (supertrend,
    ma_cross) shuts in a downtrend, when most lots are underwater and the
    policy mostly does nothing."""

    exit_id = "signal_take_profit"
    label = "Take profit on a bearish signal"

    def __init__(
        self,
        signal: str = "zscore",
        signal_params: str = "",
        min_gain: float = 0.002,
        fraction: float = 1.0,
    ) -> None:
        from research.strategies.signal_library import build_signal

        self.signal = signal
        self.signal_params = signal_params
        self._component = build_signal(signal, signal_params)
        if getattr(self._component, "kind", "gate") != "gate":
            raise ConfigurationError(f"{signal} is a {self._component.kind}, not a gate")
        self.min_gain = _positive("min_gain", min_gain)
        self.fraction = _fraction("fraction", fraction)
        self._was = False
        self._fire = False
        self._marked: set[str] = set()
        self._restore: dict[str, float] = {}
        self.fires = 0

    @property
    def history_sessions(self) -> int:
        return int(getattr(self._component, "history_sessions", 0) or 0)

    def record_tick(self, context: MarketContext) -> None:
        self._component.observe(context)
        shut = bool(self._component.suppressed)
        self._fire = shut and not self._was
        self._was = shut
        if self._fire:
            self.fires += 1

    def wants_lot_retargeting(self) -> bool:
        return self._fire or bool(self._restore)

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        oid = lot.order_id
        if oid in self._restore and oid not in self._marked:
            return self._restore.pop(oid)  # the part that was sold has gone
        if not self._fire:
            return None
        price = float(context.price) * (1 - 1e-9)  # at the market, never above it
        gain = price / lot.buy_price - 1.0
        if gain < self.min_gain or gain >= float(lot.profit_target):
            return None
        self._marked.add(oid)
        if self.fraction < 1:
            self._restore[oid] = float(lot.profit_target)
        return gain

    def harvest_quantity(self, lot, context: MarketContext) -> float:
        if lot.order_id in self._marked:
            self._marked.discard(lot.order_id)
            return lot.shares * self.fraction
        return lot.shares

    def retain_lots(self, open_order_ids) -> None:
        keep = set(open_order_ids)
        self._marked &= keep
        self._restore = {k: v for k, v in self._restore.items() if k in keep}

    def live_history_sessions(self) -> int:
        return self.history_sessions

    def diagnostics(self) -> dict:
        return {"take_profit_signals": self.fires}


# -------------------------------------------------------- loss-capable track


class RegimeExit(ExitPolicy):
    """Sell every open lot when the causal NATR regime (natr_regime.
    IncrementalNatrRegime) turns from calm to turbulent -- on the flip
    session's first bar, or at `liquidate_minute` of it. The sale is at the
    market and MAY realise a loss, so it needs execution.allow_signal_exit.

    regime_by_date injects a precomputed {date: calm} map instead of the
    internal regime (research only; never offered on the web)."""

    exit_id = "regime_exit"
    label = "Sell on a turbulent regime"
    can_realize_loss = True

    def __init__(
        self,
        natr_period: int = 10,
        natr_lookback: int = 100,
        regime_min_hold: int = 5,
        liquidate_minute: int = 0,
        regime_by_date: dict | None = None,
    ) -> None:
        from research.strategies.natr_regime import IncrementalNatrRegime

        if not 0 <= int(liquidate_minute) < SESSION_MINUTES:
            raise ConfigurationError(
                f"liquidate_minute must be in [0, 390), got {liquidate_minute}"
            )
        self.natr_period = natr_period
        self.natr_lookback = natr_lookback
        self.regime_min_hold = regime_min_hold
        self.liquidate_minute = int(liquidate_minute)
        self._map: dict[date, bool] | None = dict(regime_by_date) if regime_by_date else None
        self._natr = (
            None
            if self._map is not None
            else IncrementalNatrRegime(natr_period, natr_lookback, regime_min_hold)
        )
        self._day: int | None = None
        self._calm: bool | None = None
        self._pending: int | None = None
        self._now = False
        self.flips = 0
        self.exits = 0

    def warm_up(self, daily) -> int:
        return self._natr.warm_up(daily) if self._natr is not None else 0

    def live_history_sessions(self) -> int:
        return self._natr.history_sessions + 5 if self._natr is not None else 0

    def record_tick(self, context: MarketContext) -> None:
        if self._natr is not None:
            self._natr.observe(context.timestamp, context.high, context.low, context.close)
        self._now = False
        minute = context.time_of_day_flag
        if minute < 0:
            return
        day = context.timestamp.toordinal()
        if day != self._day:
            self._day = day
            was = self._calm
            calm = (
                self._map.get(context.timestamp.date(), self._calm)
                if self._map is not None
                else self._natr.calm
            )
            self._calm = calm
            if was is True and calm is False:
                self.flips += 1
                self._pending = day
        if self._pending is not None:
            carried = day != self._pending
            if carried or minute >= self.liquidate_minute or minute == SESSION_MINUTES - 1:
                self._now = True
                self._pending = None

    def _condemn(self, lot):
        return lot

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        if not self._now or not open_lots:
            return []
        self.exits += 1
        return [self._condemn(lot) for lot in open_lots]

    def diagnostics(self) -> dict:
        return {"regime_flips": self.flips, "regime_exits": self.exits, "calm": self._calm}


class RegimeExitPartial(RegimeExit):
    """RegimeExit, selling `fraction` of every lot's shares on the flip and
    leaving the rest to its target -- unlike harvest_sleeve's
    liquidate_fraction, which sells that fraction of the LOTS (highest cost
    first). Both stay available so they can be compared."""

    exit_id = "regime_exit_partial"
    label = "Sell part on a turbulent regime"

    def __init__(self, fraction: float = 0.5, **regime) -> None:
        super().__init__(**regime)
        self.fraction = _fraction("fraction", fraction)

    def _condemn(self, lot):
        return ExitOrder(lot, lot.shares * self.fraction)


register(AgeDecay, {"after_bars": 390, "span_bars": 390, "floor": 0.001})
register(VolScaledTarget, {"k": 1.0, "window_bars": 390, "horizon_bars": 390})
register(InventoryPressure, {"start_lots": 50, "full_lots": 200, "floor": 0.001})
register(ScaleOut, {"rungs": "0.5@0.01,0.5@0.03", "min_tranche_notional": 0.0})
register(
    ScaleOutTrail,
    {"first_fraction": 0.5, "first_target": 0.01, "trail_pct": 0.01, "runner_target": 0.5},
)
register(SignalTakeProfit, {"signal": "zscore", "min_gain": 0.002, "fraction": 1.0})
register(RegimeExit, {"natr_period": 10, "natr_lookback": 100, "regime_min_hold": 5})
register(RegimeExitPartial, {"fraction": 0.5, "natr_period": 10, "natr_lookback": 100})
