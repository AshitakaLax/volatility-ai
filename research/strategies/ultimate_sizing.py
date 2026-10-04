"""
The Ultimate algorithm, single-instrument form (docs/research/ultimate-algorithm.md).

One strategy, one ticker, two modes chosen by a causal volatility regime:

  CALM        the champion accumulation grid (hf_local_reference): fixed
              dollar lots on every local pullback, each sold at the grid's
              profit target through the no-loss guard. This is the trend-
              capture engine.
  TURBULENT   no grid buys. Capitulation entries only: in the last
              `reversal_minutes` of a session that closed at least
              |reversal_threshold| below the previous session, buy one
              event lot (reversal_lot_pct of starting capital) with its own
              small profit target (reversal_target), at most
              reversal_max_lots open at once (L11).

The regime is NATR(natr_period) against its natr_lookback-session median,
read at the previous session's close (lag 1), debounced by
regime_min_hold sessions, optionally ANDed with a bear filter (bear_dd /
bear_window, bear_sma) on CALM -- research/strategies/natr_regime.
IncrementalNatrRegime, computed from the bars this strategy sees, so the
strategy carries its own regime into the server and the live loop. A
precomputed causal map can be injected instead (regime_by_date), which is
how the research lab reproduces it.

--------------------------------------------------------------------
EXITS AND THE ONE LOSS PATH

Every lot exits at its target through the no-loss guard, except on the
first bar of the first session of a TURBULENT spell: there,
lots_to_liquidate returns every CALM-mode lot (the step-down's regime
exit, L6) -- the only sale that may be below cost, and only with
execution.allow_signal_exit. Reversal lots are kept through the flip back
to calm unless liquidate_reversal_on_calm.

--------------------------------------------------------------------
LOT TAGGING, CHEAPLY

The engine registers every buy with the run's single profit target, so a
reversal lot is retargeted to reversal_target the bar after it is bought.
wants_lot_retargeting() answers True only then and on the two flip bars
(when the lots open at that moment are classified), so the champion's
63%-of-runtime per-lot walk stays off on almost every bar.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.gated_local_reference_sizing import (
    NO_BUY_LEVEL,
    GatedLocalReferenceSizing,
)
from research.strategies.harvest_sleeve_sizing import CloseReversalSignal
from research.strategies.natr_regime import IncrementalNatrRegime

CALM, TURBULENT = "calm", "turbulent"


class UltimateSizing(GatedLocalReferenceSizing):
    """Calm: the champion. Turbulent: capitulation-close event lots. See module docstring."""

    def __init__(
        self,
        *,
        regime_by_date: Mapping[date, bool] | None = None,
        natr_period: int = 10,
        natr_lookback: int = 100,
        regime_min_hold: int = 5,
        bear_dd: float | None = None,
        bear_window: int = 60,
        bear_sma: int | None = None,
        turbulent_mode: str = "reversal",
        reversal_threshold: float = -0.06,
        reversal_minutes: int = 10,
        reversal_max_per_session: int = 1,
        reversal_lot_pct: float = 0.10,
        reversal_target: float = 0.03,
        reversal_max_lots: int = 3,
        liquidate_reversal_on_calm: bool = False,
        **params,
    ) -> None:
        super().__init__(**params)
        if turbulent_mode not in ("reversal", "cash"):
            raise ConfigurationError(
                f"turbulent_mode must be 'reversal' or 'cash', got {turbulent_mode!r}"
            )
        if not 0 < reversal_lot_pct <= 1:
            raise ConfigurationError(f"reversal_lot_pct must be in (0, 1], got {reversal_lot_pct}")
        if not reversal_target > 0 or reversal_max_lots < 1:
            raise ConfigurationError("need reversal_target > 0 and reversal_max_lots >= 1")
        self._map = dict(regime_by_date) if regime_by_date else None
        self._natr = (
            None
            if self._map is not None
            else IncrementalNatrRegime(
                period=natr_period,
                lookback=natr_lookback,
                min_hold=regime_min_hold,
                bear_dd=bear_dd,
                bear_window=bear_window,
                bear_sma=bear_sma,
            )
        )
        self.turbulent_mode = turbulent_mode
        self._reversal = CloseReversalSignal(
            reversal_threshold, reversal_minutes, reversal_max_per_session
        )
        self.reversal_lot_pct = float(reversal_lot_pct)
        self.reversal_target = float(reversal_target)
        self.reversal_max_lots = int(reversal_max_lots)
        self.liquidate_reversal_on_calm = bool(liquidate_reversal_on_calm)

        self.mode: str | None = None  # None until the regime is known
        self._mode_prev: str | None = None
        self._day: int | None = None
        self._calm_flag: bool | None = None
        self._flip_to_turbulent = False
        self._flip_to_calm = False
        self._fresh = False  # calm re-entry: measure from the market, not a stale fill
        self._lots_prev = 0
        self._new_lot = False
        self._reversal_ids: set[str] = set()
        self._known_ids: set[str] = set()
        self.flips_to_turbulent = 0
        self.reversal_buys = 0

    # ------------------------------------------------------------ per bar

    def record_tick(self, context: MarketContext) -> None:
        super().record_tick(context)
        lots = context.open_lot_count
        self._new_lot = lots > self._lots_prev
        self._lots_prev = lots
        if self._natr is not None:
            self._natr.observe(context.timestamp, context.high, context.low, context.close)
        self._mode_prev = self.mode
        self._flip_to_turbulent = self._flip_to_calm = False
        if self._fresh and self._new_lot and self.mode == CALM:
            self._fresh = False  # a calm-mode fill now anchors the reference
        minute = context.time_of_day_flag
        if minute >= 0:
            day = context.timestamp.toordinal()
            if day != self._day:
                self._day = day
                if self._map is not None:
                    self._calm_flag = self._map.get(context.timestamp.date(), self._calm_flag)
                else:
                    self._calm_flag = self._natr.calm
                new_mode = (
                    None if self._calm_flag is None else (CALM if self._calm_flag else TURBULENT)
                )
                if self.mode == CALM and new_mode == TURBULENT:
                    self._flip_to_turbulent = True
                    self.flips_to_turbulent += 1
                if self.mode == TURBULENT and new_mode == CALM:
                    self._flip_to_calm = True
                if new_mode == CALM and self.mode != CALM:
                    self._fresh = True
                self.mode = new_mode
        self._reversal.observe(
            context, self._new_lot and self.mode == TURBULENT, self._trigger_from_prior_bars
        )

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        if self.mode is None:
            return NO_BUY_LEVEL
        if self.mode == TURBULENT:
            # Entry gates govern the calm grid only: a breakdown gate would
            # block exactly the down-day closes this mode exists to buy.
            if (
                self.turbulent_mode != "reversal"
                or self.reversal_open(context) >= self.reversal_max_lots
            ):
                return NO_BUY_LEVEL
            level = self._reversal.level(self._trigger_from_prior_bars)
            return NO_BUY_LEVEL if level is None else level
        if self._entry_suppressed:
            return NO_BUY_LEVEL
        if self._fresh:
            rolling_high = self._trigger_rolling_high()
            reference = context.open if rolling_high is None else rolling_high
            return reference * (1.0 - step)
        return super()._grid_trigger_level(context, last_buy_price, step)

    def reversal_open(self, context: MarketContext) -> int:
        """Open reversal lots. The engine does not tell a strategy when a lot
        sells, so the tagged set can be stale between retargeting walks;
        open_lot_count is exact and, in TURBULENT mode, counts reversal lots
        plus at most the calm lots a disabled signal exit left behind."""
        return min(len(self._reversal_ids), context.open_lot_count)

    def calculate_trade_value(self, context: MarketContext) -> float:
        if self.mode == TURBULENT:
            if self._baseline_capital is None or self._baseline_capital <= 0:
                return 0.0
            return self._baseline_capital * self.reversal_lot_pct
        return super().calculate_trade_value(context)

    # ------------------------------------------------------------ lots

    def wants_lot_retargeting(self) -> bool:
        return (
            (self._new_lot and self._mode_prev == TURBULENT)
            or self._flip_to_turbulent
            or self._flip_to_calm
            or super().wants_lot_retargeting()
        )

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        proposed = super().adjust_profit_target(lot, context)
        oid = lot.order_id
        if oid in self._known_ids:
            return proposed
        self._known_ids.add(oid)
        # A lot first seen now was bought on the previous bar, in that bar's mode.
        if self._mode_prev == TURBULENT and not self._flip_to_turbulent:
            self._reversal_ids.add(oid)
            self.reversal_buys += 1
            return self.reversal_target
        return proposed

    def retain_lots(self, open_order_ids) -> None:
        parent = getattr(super(), "retain_lots", None)
        if parent is not None:
            parent(open_order_ids)
        keep = set(open_order_ids)
        self._known_ids &= keep
        self._reversal_ids &= keep

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        if self._flip_to_turbulent:
            return [lot for lot in open_lots if lot.order_id not in self._reversal_ids]
        if self._flip_to_calm and self.liquidate_reversal_on_calm:
            return [lot for lot in open_lots if lot.order_id in self._reversal_ids]
        return []

    def diagnostics(self) -> dict:
        out = super().diagnostics()
        out.update(
            ultimate_mode=self.mode,
            ultimate_flips_to_turbulent=self.flips_to_turbulent,
            ultimate_reversal_signals=self._reversal.signals,
            ultimate_reversal_buys=self.reversal_buys,
            ultimate_reversal_tagged=len(self._reversal_ids),
        )
        return out


__all__ = ["CALM", "TURBULENT", "UltimateSizing"]
