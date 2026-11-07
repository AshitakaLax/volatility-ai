"""
Daily Ultimate: the Ultimate design (ultimate_sizing.py) run for a return on
the DAY's equity -- docs/research/daily-ultimate.md.

Ultimate is measured over years: fixed-dollar lots sized from the equity it
started with, each sold at its own target or by the regime exit. Asked for a
daily return -- the owner's goal, +0.1% of equity a session, about 28.6% a
year over 252 sessions -- three things it does not do matter. Each is one
switch here, off by default, so daily_ultimate with all of them off is
ultimate exactly (research/tests/test_daily_ultimate.py):

  compound_lots       size each session's lots from that session's opening
                      equity rather than the run's first. Ultimate's lots
                      shrink as a share of a growing account, so its return
                      on the day's equity fades year by year; this keeps a
                      lot the same share of the book. Reversal lots
                      (reversal_lot_pct) compound with it.
  daily_goal          the session's target return on its opening equity
                      (0.001 = +0.1%). Once equity reaches it:
                        goal_pause_buys   no new calm-grid buys for the rest
                                          of the session (bank the day);
                        goal_lock         every calm lot already up at least
                                          harvest_min_gain is sold, at the
                                          market, on the bar the goal is met.
  eod_harvest_minute  from this session minute to the close, every calm lot
                      already up at least harvest_min_gain is sold at the
                      market: the day's gains realised, not carried overnight.

--------------------------------------------------------------------
NOTHING HERE CAN SELL BELOW COST

Both market take-profits are PROFIT-TARGET sales. The lot's target is moved
to the current price, as exit_library.SignalTakeProfit does, so the harvest
sells it and engine/trading/no_loss_guard.py checks it like any other target
sale. A lot below harvest_min_gain keeps its target. The one loss path is
still Ultimate's regime exit, behind execution.allow_signal_exit. Reversal
lots are left to their own target: they are capitulation bounces, and
selling one at +0.2% would sell the bounce it was bought for.

--------------------------------------------------------------------
THE SESSION'S OPENING EQUITY

DailyGoal reads it from the first bar of the session that carries a
positive equity. A live loop replays history with equity 0 and, after a
restart, joins a session in progress, so it anchors at its first live bar:
the goal is then measured from the restart, never from a number it did not
see. No state spans sessions, so resume() has nothing to rebuild.

--------------------------------------------------------------------
AS A BUY AND A SELL

`daily_ultimate` is also a buy policy (research/composition/entries.py:
compound_lots, daily_goal and goal_pause_buys buy; the take-profits sell)
and `daily_ultimate_exit` its sell policy (book_exits.py), so
composed(daily_ultimate, daily_ultimate_exit) is this strategy, and either
half pairs with any other. `daily_harvest` (exit_library.py) is the two
take-profits alone, without the regime exit, for any buyer.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.gated_local_reference_sizing import NO_BUY_LEVEL
from research.strategies.ultimate_sizing import CALM, UltimateSizing

SESSION_MINUTES = 390


class DailyGoal:
    """A session's return on its opening equity, and the bars on which it
    opens a market take-profit. Shared by DailyUltimateSizing and the two
    sell policies built from it, so all three read a session identically."""

    def __init__(
        self,
        daily_goal: float | None = None,
        goal_lock: bool = False,
        eod_harvest_minute: int | None = None,
        harvest_min_gain: float = 0.002,
    ) -> None:
        if daily_goal is not None:
            daily_goal = float(daily_goal)
            if not (math.isfinite(daily_goal) and daily_goal > 0):
                raise ConfigurationError(f"daily_goal must be a positive number, got {daily_goal}")
        if goal_lock and daily_goal is None:
            raise ConfigurationError("goal_lock sells when the daily_goal is met: set daily_goal")
        if eod_harvest_minute is not None:
            if (
                isinstance(eod_harvest_minute, bool)
                or int(eod_harvest_minute) != eod_harvest_minute
            ):
                raise ConfigurationError(
                    f"eod_harvest_minute must be a whole minute, got {eod_harvest_minute!r}"
                )
            eod_harvest_minute = int(eod_harvest_minute)
            if not 0 <= eod_harvest_minute < SESSION_MINUTES:
                raise ConfigurationError(
                    f"eod_harvest_minute must be in [0, {SESSION_MINUTES}), got {eod_harvest_minute}"
                )
        harvest_min_gain = float(harvest_min_gain)
        if not (math.isfinite(harvest_min_gain) and harvest_min_gain > 0):
            raise ConfigurationError(
                f"harvest_min_gain must be a positive number, got {harvest_min_gain}"
            )
        self.daily_goal = daily_goal
        self.goal_lock = bool(goal_lock)
        self.eod_harvest_minute = eod_harvest_minute
        self.harvest_min_gain = harvest_min_gain
        self._day: int | None = None
        self.open_equity: float | None = None
        self.reached = False
        self.harvest_now = False
        self.sessions = 0
        self.goal_sessions = 0
        self.take_profits = 0

    def observe(self, context: MarketContext) -> None:
        """Every bar. Outside the regular session (a minute flag below 0)
        nothing is measured and nothing is harvested."""
        minute = context.time_of_day_flag
        if minute < 0:
            self.harvest_now = False
            return
        day = context.timestamp.toordinal()
        if day != self._day:
            self._day = day
            self.open_equity = None
            self.reached = False
        if self.open_equity is None and context.equity > 0:
            self.open_equity = float(context.equity)
            self.sessions += 1
        just_reached = False
        if (
            self.daily_goal is not None
            and not self.reached
            and self.open_equity is not None
            and context.equity >= self.open_equity * (1.0 + self.daily_goal)
        ):
            self.reached = just_reached = True
            self.goal_sessions += 1
        self.harvest_now = (self.goal_lock and just_reached) or (
            self.eod_harvest_minute is not None and minute >= self.eod_harvest_minute
        )

    def take_profit(self, lot, context: MarketContext) -> float | None:
        """The target that sells `lot` at the market now, as a profit-target
        sale, or None to leave its target alone: not a harvest bar, under
        harvest_min_gain, or already marketable at its own target."""
        if not self.harvest_now:
            return None
        price = float(context.price) * (1 - 1e-9)  # at the market, never above it
        gain = price / lot.buy_price - 1.0
        if gain < self.harvest_min_gain or gain >= float(lot.profit_target):
            return None
        self.take_profits += 1
        return gain

    def diagnostics(self) -> dict:
        return {
            "daily_sessions": self.sessions,
            "daily_goal_sessions": self.goal_sessions,
            "daily_goal_reached": self.reached,
            "daily_take_profits": self.take_profits,
        }


class DailyTakeProfit:
    """The two market take-profits on an Ultimate-shaped book: a mixin for
    DailyUltimateSizing and book_exits.DailyUltimateExit, placed BEFORE the
    Ultimate class in the bases so each hook runs Ultimate's own first.
    Expects `self._goal` (a DailyGoal) and Ultimate's `_reversal_ids`."""

    _goal: DailyGoal

    def record_tick(self, context: MarketContext) -> None:
        super().record_tick(context)
        self._goal.observe(context)

    def wants_lot_retargeting(self) -> bool:
        return self._goal.harvest_now or super().wants_lot_retargeting()

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        # Ultimate's walk first: it classes a lot it has not seen (reversal
        # or calm) and gives a reversal lot its target.
        proposed = super().adjust_profit_target(lot, context)
        if lot.order_id in self._reversal_ids:
            return proposed
        market = self._goal.take_profit(lot, context)
        return proposed if market is None else market

    def diagnostics(self) -> dict:
        out = super().diagnostics()
        out.update(self._goal.diagnostics())
        return out


class DailyUltimateSizing(DailyTakeProfit, UltimateSizing):
    """Ultimate, sized and harvested for a daily return. See module docstring.

    The constructor repeats every UltimateSizing parameter explicitly, as
    UltimateSizing does its parent's, so the run form and analyze_annual.py
    see them through inspect.signature.
    """

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
        dd_throttle_full: float = 0.6,
        dd_throttle_floor: float = 0.25,
        implied_vol_exponent: float = 0.0,
        implied_vol_scale_min: float = 0.5,
        implied_vol_scale_max: float = 2.0,
        breakdown_gate: str = "off",
        breakdown_release: str = "reclaim",
        dt_lookback_days: int = 5,
        dt_k: float = 0.5,
        orb_minutes: int = 30,
        pattern_gate: str = "off",
        pattern_candle_minutes: int = 30,
        pattern_hold_candles: int = 4,
        pattern_lower_shadow: float = 0.2,
        pattern_body_size: float = 0.5,
        pattern_body_lookback: int = 20,
        momentum_gate: str = "off",
        momentum_early_minutes: int = 30,
        momentum_late_minutes: int = 30,
        momentum_threshold: float = 0.0,
        vol_target: float | None = None,
        vol_target_days: int = 20,
        vol_target_estimator: str = "yang_zhang",
        vol_target_min: float = 0.25,
        vol_target_max: float = 2.0,
        bounce_gate: str = "off",
        bounce_candle_minutes: int = 30,
        bounce_window: int = 20,
        bounce_k: float = 2.0,
        bounce_hold_candles: int = 8,
        bounce_max_span: int = 40,
        bounce_tolerance: float = 0.01,
        rsi_gate: str = "off",
        rsi_candle_minutes: int = 30,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_tolerance: float = 5.0,
        rsi_hold_candles: int = 8,
        regime_by_date: Mapping[date, bool] | None = None,
        natr_period: int = 10,
        natr_lookback: int = 100,
        regime_min_hold: int = 5,
        bear_dd: float | None = 0.5,
        bear_window: int = 250,
        bear_sma: int | None = None,
        turbulent_mode: str = "reversal",
        reversal_threshold: float = -0.09,
        reversal_minutes: int = 10,
        reversal_max_per_session: int = 1,
        reversal_lot_pct: float = 0.2,
        reversal_target: float = 0.06,
        reversal_max_lots: int = 4,
        liquidate_reversal_on_calm: bool = False,
        liquidate_minute: int = 60,
        # -- the Daily layer (defaults: off, which is ultimate exactly) ----
        compound_lots: bool = False,
        daily_goal: float | None = None,
        goal_pause_buys: bool = False,
        goal_lock: bool = False,
        eod_harvest_minute: int | None = None,
        harvest_min_gain: float = 0.002,
    ) -> None:
        super().__init__(
            per_lot_pct=per_lot_pct,
            lookback_days=lookback_days,
            bars_per_day=bars_per_day,
            event_day_boost_multiplier=event_day_boost_multiplier,
            earnings_day_boost_multiplier=earnings_day_boost_multiplier,
            vol_scale_exponent=vol_scale_exponent,
            vol_fast_days=vol_fast_days,
            vol_slow_days=vol_slow_days,
            vol_scale_min=vol_scale_min,
            vol_scale_max=vol_scale_max,
            time_of_day_exponent=time_of_day_exponent,
            vol_measure=vol_measure,
            volume_scale_exponent=volume_scale_exponent,
            trail_pct=trail_pct,
            trail_min_profit_target=trail_min_profit_target,
            weighted_event_boost_multiplier=weighted_event_boost_multiplier,
            dd_throttle_start=dd_throttle_start,
            dd_throttle_full=dd_throttle_full,
            dd_throttle_floor=dd_throttle_floor,
            implied_vol_exponent=implied_vol_exponent,
            implied_vol_scale_min=implied_vol_scale_min,
            implied_vol_scale_max=implied_vol_scale_max,
            breakdown_gate=breakdown_gate,
            breakdown_release=breakdown_release,
            dt_lookback_days=dt_lookback_days,
            dt_k=dt_k,
            orb_minutes=orb_minutes,
            pattern_gate=pattern_gate,
            pattern_candle_minutes=pattern_candle_minutes,
            pattern_hold_candles=pattern_hold_candles,
            pattern_lower_shadow=pattern_lower_shadow,
            pattern_body_size=pattern_body_size,
            pattern_body_lookback=pattern_body_lookback,
            momentum_gate=momentum_gate,
            momentum_early_minutes=momentum_early_minutes,
            momentum_late_minutes=momentum_late_minutes,
            momentum_threshold=momentum_threshold,
            vol_target=vol_target,
            vol_target_days=vol_target_days,
            vol_target_estimator=vol_target_estimator,
            vol_target_min=vol_target_min,
            vol_target_max=vol_target_max,
            bounce_gate=bounce_gate,
            bounce_candle_minutes=bounce_candle_minutes,
            bounce_window=bounce_window,
            bounce_k=bounce_k,
            bounce_hold_candles=bounce_hold_candles,
            bounce_max_span=bounce_max_span,
            bounce_tolerance=bounce_tolerance,
            rsi_gate=rsi_gate,
            rsi_candle_minutes=rsi_candle_minutes,
            rsi_period=rsi_period,
            rsi_overbought=rsi_overbought,
            rsi_tolerance=rsi_tolerance,
            rsi_hold_candles=rsi_hold_candles,
            regime_by_date=regime_by_date,
            natr_period=natr_period,
            natr_lookback=natr_lookback,
            regime_min_hold=regime_min_hold,
            bear_dd=bear_dd,
            bear_window=bear_window,
            bear_sma=bear_sma,
            turbulent_mode=turbulent_mode,
            reversal_threshold=reversal_threshold,
            reversal_minutes=reversal_minutes,
            reversal_max_per_session=reversal_max_per_session,
            reversal_lot_pct=reversal_lot_pct,
            reversal_target=reversal_target,
            reversal_max_lots=reversal_max_lots,
            liquidate_reversal_on_calm=liquidate_reversal_on_calm,
            liquidate_minute=liquidate_minute,
        )
        if goal_pause_buys and daily_goal is None:
            raise ConfigurationError(
                "goal_pause_buys stops buying at the daily_goal: set daily_goal"
            )
        self.compound_lots = bool(compound_lots)
        self.goal_pause_buys = bool(goal_pause_buys)
        self._goal = DailyGoal(daily_goal, goal_lock, eod_harvest_minute, harvest_min_gain)
        self.daily_goal = self._goal.daily_goal
        self.goal_lock = self._goal.goal_lock
        self.eod_harvest_minute = self._goal.eod_harvest_minute
        self.harvest_min_gain = self._goal.harvest_min_gain

    def record_tick(self, context: MarketContext) -> None:
        super().record_tick(context)
        if self.compound_lots and self._goal.open_equity is not None:
            # The champion's lot is per_lot_pct of _baseline_capital; this
            # moves the baseline to the session's opening equity, which
            # calculate_trade_value (grid and reversal lots alike) reads.
            self._baseline_capital = self._goal.open_equity

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        if self.goal_pause_buys and self._goal.reached and self.mode == CALM:
            return NO_BUY_LEVEL
        return super()._grid_trigger_level(context, last_buy_price, step)


__all__ = ["DailyGoal", "DailyTakeProfit", "DailyUltimateSizing"]
