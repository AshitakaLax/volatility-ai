"""
ComposedStrategy: one buy algorithm and one sell algorithm, chosen
independently (docs/research/buy-sell-composition.md).

    strategy:
      strategy_id: composed
      strategy_params:
        buy:  {id: hf_local_reference, params: {...}}   # entries.py
        sell: {id: trailing, params: {trail_pct: 0.01}} # exits.py

To the engine this is one SizingStrategy like any other: it is reached only
through the port (engine/core/sizing.py), and every sell it asks for still
goes through decision_cycle's shared helpers and the no-loss guard. Inside,
each question the port asks is answered by exactly one side:

  buy side   record_tick (first), the grid trigger, calculate_trade_value,
             next_lot_tag, use_prior_bar_trigger, warm-up, decision_not_sent,
             and the attributes the engine reads off a buyer (ticker,
             target_return, marketable_orders)
  sell side  record_tick (second), adjust_profit_target, wants_lot_retargeting,
             retain_lots, harvest_quantity, lots_to_liquidate
  both       warm_up and live_history_sessions (each side that has one),
             resume, regular_session_only, diagnostics

The two sides share nothing but the bar they are both shown and the tag a
buy leaves on its lot (Lot.entry_tag). That isolation is what makes a
buy x sell matrix's cells comparable.
"""

from __future__ import annotations

import copy
from typing import Any

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from engine.core.sizing import SizingStrategy
from research.composition import entries, exits


def _component(raw: Any, side: str) -> tuple[str, dict]:
    if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not raw["id"]:
        raise ConfigurationError(
            f"composed: `{side}` must be {{id: <name>, params: {{...}}}}, got {raw!r}"
        )
    unknown = set(raw) - {"id", "params"}
    if unknown:
        raise ConfigurationError(f"composed: `{side}` has unknown keys {sorted(unknown)}")
    params = raw.get("params") or {}
    if not isinstance(params, dict):
        raise ConfigurationError(f"composed: `{side}.params` must be a mapping")
    return raw["id"], dict(params)


class ComposedStrategy(SizingStrategy):
    """A buy policy and a sell policy, behind the one SizingStrategy port."""

    def __init__(self, buy: dict, sell: dict) -> None:
        buy_id, buy_params = _component(buy, "buy")
        sell_id, sell_params = _component(sell, "sell")
        self.buy = {"id": buy_id, "params": copy.deepcopy(buy_params)}
        self.sell = {"id": sell_id, "params": copy.deepcopy(sell_params)}
        self._entry = entries.build_entry(buy_id, buy_params)
        self._exit = exits.build_exit(sell_id, sell_params)
        self.can_realize_loss = bool(self._exit.can_realize_loss)
        sides = (self._entry, self._exit)
        self.regular_session_only = any(getattr(s, "regular_session_only", False) for s in sides)
        # What the engine reads off a BUYER, forwarded only when the buyer
        # has it, so getattr(..., default) still sees "absent" otherwise.
        for name in ("ticker", "target_return", "allow_target_return_mismatch"):
            if hasattr(self._entry, name):
                setattr(self, name, getattr(self._entry, name))
        if getattr(self._entry, "marketable_orders", False):
            self.marketable_orders = True
        if callable(getattr(self._entry, "decision_not_sent", None)):
            self.decision_not_sent = self._entry.decision_not_sent

    # -- what the composition is, for the server and the web -------------------

    @classmethod
    def regular_session_only_for(cls, params: dict) -> bool:
        """Whether a run of these params (a sweep's, lists included) needs
        regular-session bars -- strategy_registry.session_bars asks before any
        instance exists. True if any buy or sell variant does."""
        buys, sells = params.get("buy"), params.get("sell")
        for raw in [*(buys if isinstance(buys, list) else [buys])]:
            if isinstance(raw, dict) and isinstance(raw.get("id"), str):
                try:
                    if getattr(entries.entry_class(raw["id"]), "regular_session_only", False):
                        return True
                except ConfigurationError:
                    continue
        for raw in [*(sells if isinstance(sells, list) else [sells])]:
            if isinstance(raw, dict) and isinstance(raw.get("id"), str):
                cls_ = exits.EXITS.get(raw["id"])
                if cls_ is not None and getattr(cls_, "regular_session_only", False):
                    return True
        return False

    @classmethod
    def can_realize_loss_for(cls, params: dict) -> bool:
        """Whether any sell variant of these params may sell below cost."""
        sells = params.get("sell")
        for raw in sells if isinstance(sells, list) else [sells]:
            if isinstance(raw, dict):
                policy = exits.EXITS.get(raw.get("id"))
                if policy is not None and policy.can_realize_loss:
                    return True
        return False

    def describe(self) -> str:
        return f"{self.buy['id']} buying, {self.sell['id']} selling"

    # -- the buy side ----------------------------------------------------------

    def use_prior_bar_trigger(self, enabled: bool) -> None:
        super().use_prior_bar_trigger(enabled)
        self._entry.use_prior_bar_trigger(enabled)

    def record_tick(self, context: MarketContext) -> None:
        self._entry.record_tick(context)
        self._exit.record_tick(context)

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        return self._entry._grid_trigger_level(context, last_buy_price, step)

    def _check_grid_trigger(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> bool:
        return self._entry._check_grid_trigger(context, last_buy_price, step)

    def calculate_trade_value(self, context: MarketContext) -> float:
        return self._entry.calculate_trade_value(context)

    def next_lot_tag(self) -> str | None:
        hook = getattr(self._entry, "next_lot_tag", None)
        return hook() if hook is not None else None

    # -- the sell side ---------------------------------------------------------

    def wants_lot_retargeting(self) -> bool:
        return self._exit.wants_lot_retargeting()

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        return self._exit.adjust_profit_target(lot, context)

    def retain_lots(self, open_order_ids) -> None:
        self._exit.retain_lots(open_order_ids)

    def harvest_quantity(self, lot, context: MarketContext) -> float:
        return self._exit.harvest_quantity(lot, context)

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        return self._exit.lots_to_liquidate(open_lots, context)

    # -- both ------------------------------------------------------------------

    def _sides_with(self, name: str) -> list:
        return [s for s in (self._entry, self._exit) if callable(getattr(s, name, None))]

    def warm_up(self, daily) -> int:
        """Each side that keeps session history is seeded from it. Defined on
        the class so the server always offers the history (warm_up_history);
        a composition whose sides keep none uses none."""
        used = [int(s.warm_up(daily) or 0) for s in self._sides_with("warm_up")]
        return max(used, default=0)

    def live_history_sessions(self) -> int:
        """The most history either side needs replayed before a live session
        (0 for a composition that needs none, which the live loop treats as
        asking for nothing)."""
        return max(
            (int(s.live_history_sessions()) for s in self._sides_with("live_history_sessions")),
            default=0,
        )

    def resume(self, open_lots) -> None:
        for side in self._sides_with("resume"):
            side.resume(open_lots)

    def diagnostics(self) -> dict:
        out: dict[str, Any] = {"buy_policy": self.buy["id"], "sell_policy": self.sell["id"]}
        report = getattr(self._entry, "diagnostics", None)
        if callable(report):
            out.update(report() or {})
        out.update({f"sell_{k}": v for k, v in (self._exit.diagnostics() or {}).items()})
        return out
