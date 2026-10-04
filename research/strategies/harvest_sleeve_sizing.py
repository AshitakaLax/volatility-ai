"""
A regime sleeve built to HARVEST volatility with a bounded inventory --
the turbulent-regime half of the Ultimate algorithm
(docs/research/ultimate-algorithm.md).

RegimeSleeveSizing (the champion gated to one regime) plus five levers
from the correction-strategy catalog, every one OFF by default, so with
no new parameter set this class is RegimeSleeveSizing exactly:

  inventory_decay      C-S4  lot x decay ** open_lots: each open lot makes
                             the next one smaller.
  inventory_skew       C-G2  the pullback that triggers a buy deepens with
                             inventory: step x (1 + skew x open_lots),
                             capped at skew_max_depth (Avellaneda-Stoikov's
                             reservation-price skew, long side only).
  vol_step_window      C-G3  step = vol_step_multiple x the per-bar sigma
                             of the last vol_step_window bars (x sqrt of
                             vol_step_horizon), clamped -- wide rungs when
                             the tape is violent, tight when it is quiet.
  target_decay_*       C-X2  a lot still open target_decay_after_bars after
                             it was bought has its profit target lowered,
                             linearly over target_decay_span_bars, toward
                             target_floor. Profit-only by construction:
                             the no-loss guard still rejects any sale below
                             cost basis, so this frees a stuck lot on the
                             first bounce back above cost rather than
                             waiting for the full target.
  noise / vwap /       C-M1, C-MS3, C-X4  three more entry gates: no buys
  session throttle           below the Noise Area's lower bound, none far
                             below VWAP while still falling, and a per-
                             session lot cap / spacing / adverse-run
                             cooldown.

--------------------------------------------------------------------
WHY THE TARGET DECAY IS CHEAP

decision_cycle.adjust_open_lot_targets walks every open lot on every bar
unless wants_lot_retargeting() answers False -- profiled at 63% of
runtime when it does nothing. This class answers True only on bars that
can change a target: the bar after a buy (to record the new lot's age)
and every target_decay_check_bars bars. A lot's age is counted from the
bar it was first seen, which is the bar after its purchase.

--------------------------------------------------------------------
CAUSALITY

Everything here reads state record_tick updated from bars up to and
including the current one -- and _grid_trigger_level honors
use_prior_bar_trigger (fill_model="intrabar", intrabar_fill="causal") by
using the volatility step as of the PREVIOUS bar, the same discipline as
the parent's rolling high. Inventory (open_lot_count) is known at the
bar's open.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.gated_local_reference_sizing import NO_BUY_LEVEL
from research.strategies.grid_spacing import VolatilityScaledStep, volatility_scaled_step
from research.strategies.intraday_gates import NoiseAreaGate, SessionLotThrottle, VwapGate
from research.strategies.regime_sleeve_sizing import RegimeSleeveSizing

REVERSAL_MODES: tuple[str, ...] = ("off", "close")
SESSION_MINUTES = 390


class CloseReversalSignal:
    """Buy-the-capitulation-close signal (Ultimate algorithm, L11).

    Opens in the last `minutes` minutes of a regular session whose close is
    at least |threshold| below the previous session's close, for at most
    `max_per_session` buys per session. `observe` runs every bar from
    record_tick; `level` is the resting buy price for the CURRENT bar, or
    None. Under the causal intrabar fill the level is the previous bar's
    close and the decision is the previous bar's, a decision never carries
    across a session boundary, and the signal will not re-arm on the bar
    right after an armed one (the buy it armed is not yet visible in
    open_lot_count), so it cannot buy twice."""

    def __init__(
        self, threshold: float = -0.02, minutes: int = 10, max_per_session: int = 1
    ) -> None:
        if not threshold < 0:
            raise ConfigurationError(f"reversal_threshold must be < 0, got {threshold}")
        if not 1 <= minutes <= SESSION_MINUTES or max_per_session < 1:
            raise ConfigurationError(
                "need 1 <= reversal_minutes <= 390 and reversal_max_per_session >= 1"
            )
        self.threshold = float(threshold)
        self.minutes = int(minutes)
        self.max_per_session = int(max_per_session)
        self._day: int | None = None
        self._prev_session_close: float | None = None
        self._last_close: float | None = None
        self._close_prev_bar: float | None = None
        self._buys = 0
        self._open_now = False
        self._open_prev = False
        self.signals = 0

    def observe(self, context: MarketContext, new_lot: bool, causal: bool) -> None:
        self._open_prev = self._open_now
        self._close_prev_bar = self._last_close
        if new_lot:
            self._buys += 1  # charged to the session it filled in, before any reset
        minute = context.time_of_day_flag
        if minute < 0:
            self._open_now = False
            return
        day = context.timestamp.toordinal()
        if day != self._day:
            if self._day is not None:
                self._prev_session_close = self._last_close
            self._day = day
            self._buys = 0
            self._open_prev = False
        self._last_close = context.close
        ref = self._prev_session_close
        is_open = (
            ref is not None
            and minute >= SESSION_MINUTES - self.minutes
            and context.close / ref - 1.0 <= self.threshold
            and self._buys < self.max_per_session
        )
        if is_open and causal and self._open_prev:
            is_open = False
        if is_open and not self._open_now:
            self.signals += 1
        self._open_now = is_open

    def level(self, causal: bool) -> float | None:
        if causal:
            return self._close_prev_bar if self._open_prev and self._close_prev_bar else None
        return self._last_close if self._open_now and self._last_close else None


class HarvestSleeveSizing(RegimeSleeveSizing):
    """RegimeSleeveSizing with bounded-inventory harvest levers. See module docstring."""

    def __init__(
        self,
        *,
        sleeve: str = "always",
        regime_by_date: Mapping[date, bool] | None = None,
        inventory_decay: float = 1.0,
        inventory_skew: float = 0.0,
        skew_max_depth: float | None = None,
        vol_step_window: int | None = None,
        vol_step_multiple: float = 1.0,
        vol_step_min: float = 0.0005,
        vol_step_max: float | None = None,
        vol_step_horizon: int = 1,
        target_decay_after_bars: int | None = None,
        target_decay_span_bars: int = 390,
        target_floor: float = 0.001,
        target_decay_check_bars: int = 15,
        noise_gate: str = "off",
        noise_lookback_days: int = 14,
        noise_check_minutes: int = 30,
        vwap_gate: str = "off",
        vwap_far_k: float = 3.0,
        vwap_near_k: float = 1.0,
        vwap_vol_window: int = 30,
        session_throttle: str = "off",
        throttle_max_lots: int | None = None,
        throttle_min_bars: int = 0,
        throttle_adverse_run: int | None = None,
        throttle_cooldown_bars: int = 30,
        reversal_gate: str = "off",
        reversal_threshold: float = -0.02,
        reversal_minutes: int = 10,
        reversal_max_per_session: int = 1,
        liquidate_minute: int = 0,
        liquidate_fraction: float = 1.0,
        **params,
    ) -> None:
        super().__init__(sleeve=sleeve, regime_by_date=regime_by_date, **params)
        if not 0 <= liquidate_minute < SESSION_MINUTES:
            raise ConfigurationError(
                f"liquidate_minute must be in [0, 390), got {liquidate_minute}"
            )
        if not 0 < liquidate_fraction <= 1:
            raise ConfigurationError(
                f"liquidate_fraction must be in (0, 1], got {liquidate_fraction}"
            )
        self.liquidate_minute = int(liquidate_minute)
        self.liquidate_fraction = float(liquidate_fraction)
        self._liq_pending = False
        self._liq_now = False
        if not 0 < inventory_decay <= 1:
            raise ConfigurationError(f"inventory_decay must be in (0, 1], got {inventory_decay}")
        if inventory_skew < 0:
            raise ConfigurationError(f"inventory_skew must be >= 0, got {inventory_skew}")
        if skew_max_depth is not None and not 0 < skew_max_depth < 1:
            raise ConfigurationError(f"skew_max_depth must be in (0, 1), got {skew_max_depth}")
        if target_decay_after_bars is not None:
            if target_decay_after_bars < 0 or target_decay_span_bars < 1:
                raise ConfigurationError("need target_decay_after_bars >= 0 and span >= 1")
            if not target_floor > 0:
                raise ConfigurationError(f"target_floor must be > 0, got {target_floor}")
            if target_decay_check_bars < 1:
                raise ConfigurationError("target_decay_check_bars must be >= 1")
        if reversal_gate not in REVERSAL_MODES:
            raise ConfigurationError(
                f"reversal_gate must be one of {REVERSAL_MODES}, got {reversal_gate!r}"
            )
        self.reversal_gate = reversal_gate
        # Built (so validated) even when off, like the gates.
        self._reversal = CloseReversalSignal(
            reversal_threshold, reversal_minutes, reversal_max_per_session
        )
        self.inventory_decay = float(inventory_decay)
        self.inventory_skew = float(inventory_skew)
        self.skew_max_depth = skew_max_depth
        self._volstep = (
            VolatilityScaledStep(
                window=vol_step_window,
                vol_multiple=vol_step_multiple,
                min_step=vol_step_min,
                max_step=vol_step_max,
                horizon_bars=vol_step_horizon,
            )
            if vol_step_window
            else None
        )
        self._step_now: float | None = None
        self._step_prev: float | None = None
        self.target_decay_after_bars = target_decay_after_bars
        self.target_decay_span_bars = int(target_decay_span_bars)
        self.target_floor = float(target_floor)
        self.target_decay_check_bars = int(target_decay_check_bars)
        self._births: dict[str, tuple[int, float]] = {}
        self._bar = -1
        self._lots_prev = 0
        self._new_lot = False
        self.retargets = 0
        self.noise = NoiseAreaGate(
            noise_gate, lookback_days=noise_lookback_days, check_minutes=noise_check_minutes
        )
        self.vwap = VwapGate(
            vwap_gate, far_k=vwap_far_k, near_k=vwap_near_k, vol_window=vwap_vol_window
        )
        self.throttle = SessionLotThrottle(
            session_throttle,
            max_lots_per_session=throttle_max_lots,
            min_bars_between_buys=throttle_min_bars,
            adverse_run=throttle_adverse_run,
            cooldown_bars=throttle_cooldown_bars,
        )
        self._gates = self._gates + tuple(
            g for g in (self.noise, self.vwap, self.throttle) if g.enabled
        )

    # ------------------------------------------------------------ per bar

    def record_tick(self, context: MarketContext) -> None:
        super().record_tick(context)
        self._bar += 1
        lots = context.open_lot_count
        self._new_lot = lots > self._lots_prev
        self._lots_prev = lots
        if self.reversal_gate != "off":
            self._reversal.observe(context, self._new_lot, self._trigger_from_prior_bars)
        # Regime-exit timing: the parent flags the flip on the session's first
        # bar; a later liquidate_minute holds the exit until that minute of
        # the same session (or the session's last bar, if it ends sooner).
        self._liq_now = False
        if self._flipped_out:
            self._liq_pending = True
        minute = context.time_of_day_flag
        if (
            self._liq_pending
            and minute >= 0
            and (minute >= self.liquidate_minute or minute == SESSION_MINUTES - 1)
        ):
            self._liq_now = True
            self._liq_pending = False
        if self._volstep is not None:
            self._step_prev = self._step_now
            self._volstep.observe(context.close)
            sigma = self._volstep.sigma  # one np.std per bar, not two
            vs = self._volstep
            self._step_now = (
                None
                if sigma is None
                else volatility_scaled_step(
                    sigma, vs.vol_multiple, vs.min_step, vs.max_step, vs.quantize
                )
            )

    def _effective_step(self, context: MarketContext, step: float) -> float:
        eff = step
        if self._volstep is not None:
            vs = self._step_prev if self._trigger_from_prior_bars else self._step_now
            if vs is not None:
                eff = vs
        if self.inventory_skew > 0 and context.open_lot_count > 0:
            eff = eff * (1.0 + self.inventory_skew * context.open_lot_count)
            if self.skew_max_depth is not None:
                eff = min(eff, self.skew_max_depth)
        return min(eff, 0.95)

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        if self.reversal_gate == "close":
            # Buy ONLY on the close-reversal signal, inside the regime and gates.
            if not self._active or self._entry_suppressed:
                return NO_BUY_LEVEL
            level = self._reversal.level(self._trigger_from_prior_bars)
            return NO_BUY_LEVEL if level is None else level
        return super()._grid_trigger_level(
            context, last_buy_price, self._effective_step(context, step)
        )

    def calculate_trade_value(self, context: MarketContext) -> float:
        value = super().calculate_trade_value(context)
        if value > 0 and self.inventory_decay < 1.0 and context.open_lot_count > 0:
            value *= self.inventory_decay**context.open_lot_count
        return value

    # ------------------------------------------------------------ exits

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        """The parent's regime exit, optionally delayed (liquidate_minute)
        and partial: the highest-cost liquidate_fraction of open lots, the
        rest left to their profit targets."""
        if self.liquidate_minute == 0 and self.liquidate_fraction == 1.0:
            return super().lots_to_liquidate(open_lots, context)
        if not self._liq_now:
            return []
        lots = sorted(open_lots, key=lambda lot: lot.buy_price, reverse=True)
        k = math.ceil(self.liquidate_fraction * len(lots))
        return lots[:k]

    def wants_lot_retargeting(self) -> bool:
        if self.target_decay_after_bars is None:
            return super().wants_lot_retargeting()
        return (
            self._new_lot
            or self._bar % self.target_decay_check_bars == 0
            or super().wants_lot_retargeting()
        )

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        proposed = super().adjust_profit_target(lot, context)
        if self.target_decay_after_bars is None:
            return proposed
        info = self._births.get(lot.order_id)
        if info is None:
            info = (self._bar, float(lot.profit_target))
            self._births[lot.order_id] = info
        age = self._bar - info[0]
        if age <= self.target_decay_after_bars:
            return proposed
        frac = min(1.0, (age - self.target_decay_after_bars) / self.target_decay_span_bars)
        original = info[1]
        decayed = original - (original - self.target_floor) * frac
        current = proposed if proposed is not None else float(lot.profit_target)
        if decayed < current - 1e-12:
            self.retargets += 1
            return max(decayed, self.target_floor)
        return proposed

    def retain_lots(self, open_order_ids) -> None:
        parent = getattr(super(), "retain_lots", None)
        if parent is not None:
            parent(open_order_ids)
        if self._births:
            keep = set(open_order_ids)
            self._births = {k: v for k, v in self._births.items() if k in keep}

    def diagnostics(self) -> dict:
        out = super().diagnostics()
        out.update(
            harvest_step=self._step_now,
            harvest_retargets=self.retargets,
            noise_gate=self.noise.mode,
            noise_suppressed_bars=self.noise.suppressed_bars,
            vwap_gate=self.vwap.mode,
            vwap_suppressed_bars=self.vwap.suppressed_bars,
            session_throttle=self.throttle.mode,
            throttle_suppressed_bars=self.throttle.suppressed_bars,
            reversal_gate=self.reversal_gate,
            reversal_signals=self._reversal.signals,
        )
        return out


__all__ = ["REVERSAL_MODES", "CloseReversalSignal", "HarvestSleeveSizing"]
