"""
Forecast Harvest: Daily Ultimate traded in whole shares, each calm lot split
into a DAY part that takes the session's likely move and a SWING part that
waits for the long target, with the nightly risk report setting the day
part's reward and the lot's size -- docs/research/forecast-harvest.md.

Built on DailyUltimateSizing (daily_ultimate_sizing.py), whose regime does
the work the earlier research found matters most: the calm grid buys only
while NATR(14) is below its median and the fund is within bear_dd of its
high, the turbulent book buys only capitulation reversal lots, and calm lots
are sold an hour into the first turbulent session (the one sale that may
realise a loss). Everything below is added to that, and each addition is
off at its default except whole shares:

  whole_shares        every buy is rounded DOWN to whole shares at the
                      price it fills at, and a buy worth less than one
                      share is not made. Fidelity and Alpaca's whole-share
                      orders trade this way; a fractional backtest
                      overstates a small account.

  DYNAMIC SELLING (the day / swing split)
  day_fraction        the share of each calm lot's shares (rounded down to
                      whole shares) sold at the DAY target; the rest keep
                      the run's profit target (the swing target). 0 is
                      Daily Ultimate's selling; 1 sells whole lots at the
                      day target.
  day_quantile        which of the session's forecast quantiles is the day
                      part's price level: "p75" (default) or "p95" etc.
  day_k               the level is the previous close x (1 + day_k x that
                      quantile). Without a report the quantile is the
                      normal one of the fund's own trailing volatility
                      (EWMA, lambda 0.94, completed sessions only), so the
                      day target is dynamic with or without a report.
  day_target_min/max  the day target, measured from the lot's buy price,
                      is kept within these. The minimum is a profit: a
                      day part never sells below its cost plus this.
  day_close_minute    from this session minute to the close, a day part
                      already up day_target_min is sold at the market (a
                      profit-target sale): the day's gain banked rather
                      than carried. None (default): day parts wait.
  The day target is recomputed at every session's open for every day part
  still open, from that session's forecast: an unfilled day part carries
  the next session's likely move, never a stale one.

  DYNAMIC BUYING (on top of Ultimate's volatility-scaled lots)
  forecast_size_exponent  a lot is multiplied by (sigma_own / sigma_report)
                      ^ exponent, clamped to [size_min, size_max]: a report
                      that expects a wider day than the fund has been
                      having buys smaller, a calmer one larger.
  forecast_tilt       and by 1 + tilt x (the report's median / its sigma),
                      clamped to [0, size_max]: a report leaning down buys
                      less (nothing at all when 1 + tilt x z <= 0).

  THE OPENING (how to start after a deep fall)
  trade_from          no buy of any kind before this session; the regime
                      and the volatility estimates still warm up on the
                      bars before it.
  seed_levels         comma-separated falls below the anchor (the first
                      session's open at or after trade_from), e.g.
                      "0,0.15,0.3": at each, one SEED lot of seed_lot_pct
                      of starting capital is bought once, whatever the
                      regime says. A seed lot sells only at seed_target:
                      the regime exit does not sell it and it is never
                      split. Seeds are the deliberate bet that a fall this
                      deep recovers; the regime book trades beside them.

--------------------------------------------------------------------
THE REPORT

A session's report reaches the strategy as a mapping of its tomorrow
horizon: {"p05", "p25", "p50", "p75", "p95"} in percent (the quantiles of
the session's close against the previous close), from either

  forecast_by_date    {session: {...}} injected (research: the proxy's
                      reports, or synthetic ones at a chosen accuracy --
                      tools/probe_forecast_harvest.py), or
  forecast_db         the forecast database every checked report is kept
                      in (research/risk_overlay/forecasts.py), read once a
                      session for the newest report targeting it, or
  forecast_from_db    that database at its usual place (VAI_FORECAST_DB, else
                      <warehouse>/forecasts/risk_reports.db): what a
                      deployment's profile sets, the path being the
                      container's rather than the profile's.

A session with no report uses the fund's own volatility, as above.

--------------------------------------------------------------------
NOTHING NEW CAN SELL BELOW COST

The day part sells at a profit target (day_target_min > 0 of its cost at
least), through the harvest and engine/trading/no_loss_guard.py like any
target sale. Seed lots sell only at their target. The one loss path is
still Ultimate's regime exit behind execution.allow_signal_exit, and it
sells calm lots only.

--------------------------------------------------------------------
LIVE

A live trader starts every session cold, so resume() rebuilds the lots each
session. Lot kinds are persisted through Lot.entry_tag ("seed"), and a calm
lot's part through its target: a lot whose target is at most day_target_max
still has its day part open, and day_fraction of its shares (rounded as at
the buy) is that part. Its swing target is swing_target -- set it, equal to
the run's profit target, on a deployment -- or else the target of a calm
lot already in its swing part. A seed ladder is the opening of one run: a
resumed one never seeds again.
"""

from __future__ import annotations

import inspect
import math
from collections.abc import Mapping
from datetime import date
from typing import Any

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.daily_ultimate_sizing import DailyUltimateSizing
from research.strategies.gated_local_reference_sizing import NO_BUY_LEVEL
from research.strategies.ultimate_sizing import CALM

SEED = "seed"
QUANTILES = ("p05", "p25", "p50", "p75", "p95")
# The standard normal quantile of each, for a report-less session.
NORMAL_Z = {"p05": -1.6449, "p25": -0.6745, "p50": 0.0, "p75": 0.6745, "p95": 1.6449}
EWMA_LAMBDA = 0.94
SHARE_SLACK = 1e-12  # a whole-share buy's dollars, so qty is never a hair under


def _date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _levels(value: Any) -> tuple[float, ...]:
    if value is None or value == "":
        return ()
    items = value if isinstance(value, (list, tuple)) else str(value).split(",")
    out = tuple(sorted(float(x) for x in items))
    if any(not (0.0 <= x < 1.0) for x in out):
        raise ConfigurationError(f"seed_levels must be falls in [0, 1), got {value!r}")
    return out


def forecast_sigma(forecast: Mapping[str, float]) -> float | None:
    """The report's one-day sigma (a fraction), from its 5-95 spread."""
    try:
        spread = (float(forecast["p95"]) - float(forecast["p05"])) / 100.0
    except (KeyError, TypeError, ValueError):
        return None
    return spread / (2 * NORMAL_Z["p95"]) if spread > 0 else None


class ForecastHarvestSizing(DailyUltimateSizing):
    """See module docstring. strategy_id: forecast_harvest."""

    def __init__(
        self,
        *,
        whole_shares: bool = True,
        day_fraction: float = 0.0,
        day_quantile: str = "p75",
        day_k: float = 1.0,
        day_target_min: float = 0.004,
        day_target_max: float = 0.04,
        day_close_minute: int | None = None,
        swing_target: float | None = None,
        forecast_size_exponent: float = 0.0,
        forecast_tilt: float = 0.0,
        size_min: float = 0.25,
        size_max: float = 2.0,
        forecast_by_date: Mapping[date, Mapping[str, float]] | None = None,
        forecast_db: str | None = None,
        forecast_from_db: bool = False,
        forecast_symbol: str = "TQQQ",
        trade_from: str | date | None = None,
        seed_levels: str | None = None,
        seed_lot_pct: float = 0.1,
        seed_target: float = 0.6,
        **ultimate: Any,
    ) -> None:
        super().__init__(**ultimate)
        if not 0.0 <= float(day_fraction) <= 1.0:
            raise ConfigurationError(f"day_fraction must be in [0, 1], got {day_fraction}")
        if day_quantile not in QUANTILES:
            raise ConfigurationError(f"day_quantile must be one of {QUANTILES}")
        if not 0.0 < float(day_target_min) <= float(day_target_max):
            raise ConfigurationError("need 0 < day_target_min <= day_target_max")
        if not 0.0 <= float(size_min) <= 1.0 <= float(size_max):
            raise ConfigurationError("need 0 <= size_min <= 1 <= size_max")
        if not 0.0 < float(seed_lot_pct) <= 1.0 or float(seed_target) <= 0:
            raise ConfigurationError("seed_lot_pct in (0, 1] and seed_target > 0")
        self.whole_shares = bool(whole_shares)
        self.day_fraction = float(day_fraction)
        self.day_quantile = day_quantile
        self.day_k = float(day_k)
        self.day_target_min = float(day_target_min)
        self.day_target_max = float(day_target_max)
        if day_close_minute is not None and not 0 <= int(day_close_minute) < 390:
            raise ConfigurationError(
                f"day_close_minute must be in [0, 390), got {day_close_minute}"
            )
        self.day_close_minute = None if day_close_minute is None else int(day_close_minute)
        if swing_target is not None and not float(swing_target) > float(day_target_max):
            raise ConfigurationError("swing_target must be above day_target_max")
        self.swing_target = None if swing_target is None else float(swing_target)
        self._day_close_now = False
        self.forecast_size_exponent = float(forecast_size_exponent)
        self.forecast_tilt = float(forecast_tilt)
        self.size_min = float(size_min)
        self.size_max = float(size_max)
        self.forecast_symbol = forecast_symbol
        self.trade_from = _date(trade_from)
        self.seed_levels = _levels(seed_levels)
        self.seed_lot_pct = float(seed_lot_pct)
        self.seed_target = float(seed_target)
        self._forecasts = dict(forecast_by_date) if forecast_by_date else None
        self._forecast_db = forecast_db
        self.forecast_from_db = bool(forecast_from_db)
        # Session state.
        self._session: date | None = None
        self._last_close: float | None = None
        self._ref_close: float | None = None  # the previous session's close
        self._closes: list[float] = []  # completed sessions' closes (last two)
        self._ewma_var: float | None = None
        self.forecast: Mapping[str, float] | None = None
        self.day_level: float | None = None
        self._size_mult = 1.0
        self._open = False  # trade_from reached
        # Lots.
        self._day_parts: dict[str, float] = {}  # lot id -> shares still in its day part
        self._swing: dict[str, float] = {}  # lot id -> its swing target
        self._seed_ids: set[str] = set()
        self._anchor: float | None = None
        self._seeds_bought = 0
        self._buying_seed = False
        self._retarget_all = False
        self._split_pending: set[str] = set()
        self._held: dict[str, float] = {}  # lot id -> its shares before its day part sold
        self._sized_buy = False
        self._walk_next = False
        # Counters.
        self.forecast_sessions = 0
        self.day_sales = 0
        self.whole_share_refusals = 0

    # ------------------------------------------------------------ the report

    def _forecast_for(self, session: date) -> Mapping[str, float] | None:
        if self._forecasts is not None:
            return self._forecasts.get(session)
        if self._forecast_db or self.forecast_from_db:
            return self._read_db(session)
        return None

    def _read_db(self, session: date) -> Mapping[str, float] | None:
        """The newest report targeting `session` in the forecast database,
        as its tomorrow quantiles. Never raises: a missing or unreadable
        database is a session without a report."""
        try:
            from research.risk_overlay.forecasts import ForecastStore, default_path

            path = self._forecast_db or default_path()
            rows = ForecastStore(path).sessions(self.forecast_symbol, limit=5)
        except Exception:
            return None
        for row in rows:
            if row.get("session") == session.isoformat():
                q = row.get("quantiles") or {}
                if all(k in q for k in ("p05", "p25", "p75", "p95")):
                    return {**q, "p50": row.get("median_pct", 0.0)}
        return None

    def _own_sigma(self) -> float | None:
        return math.sqrt(self._ewma_var) if self._ewma_var else None

    def _new_session(self, context: MarketContext) -> None:
        session = context.timestamp.date()
        if self._last_close is not None:
            self._closes = [*self._closes, self._last_close][-2:]
            if len(self._closes) == 2:
                r = self._closes[1] / self._closes[0] - 1.0
                self._ewma_var = (
                    r * r
                    if self._ewma_var is None
                    else EWMA_LAMBDA * self._ewma_var + (1 - EWMA_LAMBDA) * r * r
                )
        self._ref_close = self._closes[-1] if self._closes else None
        self._session = session
        if self.trade_from is None or session >= self.trade_from:
            if not self._open and self.seed_levels:
                self._anchor = float(context.open)
            self._open = True
        self.forecast = self._forecast_for(session)
        self.forecast_sessions += self.forecast is not None
        own = self._own_sigma()
        # The day part's price level for this session.
        if self.forecast is not None:
            q = float(self.forecast[self.day_quantile]) / 100.0
        elif own is not None:
            q = NORMAL_Z[self.day_quantile] * own
        else:
            q = None
        self.day_level = (
            None if q is None or self._ref_close is None else self._ref_close * (1 + self.day_k * q)
        )
        # The session's size multiplier.
        mult = 1.0
        sigma = forecast_sigma(self.forecast) if self.forecast is not None else None
        if sigma and own and self.forecast_size_exponent:
            mult *= (own / sigma) ** self.forecast_size_exponent
            mult = min(self.size_max, max(self.size_min, mult))
        if sigma and self.forecast_tilt:
            z = float(self.forecast.get("p50", 0.0)) / 100.0 / sigma
            mult *= min(self.size_max, max(0.0, 1.0 + self.forecast_tilt * z))
        self._size_mult = mult
        self._retarget_all = bool(self._day_parts)

    # ------------------------------------------------------------ per bar

    def record_tick(self, context: MarketContext) -> None:
        # A buy sized on the previous bar is classified (day part, seed) on
        # this one; open_lot_count alone misses a bar that sold one lot and
        # bought another.
        self._walk_next, self._sized_buy = self._sized_buy, False
        self._retarget_all = False
        minute = context.time_of_day_flag  # below 0 outside the regular session
        regular = minute >= 0
        if regular and context.timestamp.date() != self._session:
            self._new_session(context)
        super().record_tick(context)
        if regular:
            self._last_close = float(context.close)
        self._day_close_now = (
            self.day_close_minute is not None
            and minute >= self.day_close_minute
            and bool(self._day_parts)
        )

    def _seed_level(self) -> float | None:
        if not self._open or self._anchor is None or self._seeds_bought >= len(self.seed_levels):
            return None
        return self._anchor * (1.0 - self.seed_levels[self._seeds_bought])

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        self._buying_seed = False
        if not self._open:
            return NO_BUY_LEVEL
        level = super()._grid_trigger_level(context, last_buy_price, step)
        seed = self._seed_level()
        if seed is not None and seed >= level:
            self._buying_seed = True
            return seed
        return level

    def next_lot_tag(self) -> str | None:
        return SEED if self._buying_seed else super().next_lot_tag()

    def risk_overlay_exempt(self) -> bool:
        return self._buying_seed or super().risk_overlay_exempt()

    def calculate_trade_value(self, context: MarketContext) -> float:
        if self._buying_seed:
            base = self._baseline_capital or 0.0
            value = base * self.seed_lot_pct
        else:
            value = super().calculate_trade_value(context)
            if self.mode == CALM:
                value *= self._size_mult
        if value <= 0:
            return 0.0
        if self.whole_shares:
            price = float(context.price)
            shares = math.floor(value / price + 1e-9)
            if shares < 1:
                self.whole_share_refusals += 1
                return 0.0
            value = shares * price * (1 + SHARE_SLACK)
        if self._buying_seed:
            self._seeds_bought += 1
        self._sized_buy = True
        return value

    # ------------------------------------------------------------ lots

    def resume(self, open_lots) -> None:
        lots = list(open_lots)
        super().resume(lots)
        calm = []
        for lot in lots:
            oid = lot.order_id
            if getattr(lot, "entry_tag", None) == SEED:
                self._seed_ids.add(oid)
                self._reversal_ids.discard(oid)
            elif oid not in self._reversal_ids:
                calm.append(lot)
        # The swing target a resumed day part goes on to: swing_target, else
        # the target of a calm lot already in its swing part.
        swing = self.swing_target
        if swing is None:
            above = [
                float(lot.profit_target)
                for lot in calm
                if float(lot.profit_target) > self.day_target_max + 1e-12
            ]
            swing = max(above) if above else None
        if self.day_fraction > 0:
            for lot in calm:
                if float(lot.profit_target) <= self.day_target_max + 1e-12:
                    part = self._whole(float(lot.shares) * self.day_fraction)
                    if part > 0:
                        self._day_parts[lot.order_id] = part
                        if swing is not None:
                            self._swing[lot.order_id] = swing
        # A seed ladder is the opening of ONE run: a restarted one never seeds
        # again, whether its seeds are open, sold or were never all bought.
        self._seeds_bought = len(self.seed_levels)

    def _whole(self, shares: float) -> float:
        return float(math.floor(shares + 1e-6)) if self.whole_shares else shares

    def _day_target(self, lot) -> float:
        buy = float(lot.buy_price)
        target = self.day_target_min
        if self.day_level is not None and buy > 0:
            target = self.day_level / buy - 1.0
        return min(self.day_target_max, max(self.day_target_min, target))

    def wants_lot_retargeting(self) -> bool:
        return (
            self._retarget_all
            or self._day_close_now
            or bool(self._split_pending)
            or self._walk_next
            or super().wants_lot_retargeting()
        )

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        oid = lot.order_id
        if oid in self._seed_ids:
            return None
        if oid not in self._known_ids and getattr(lot, "entry_tag", None) == SEED:
            self._known_ids.add(oid)
            self._seed_ids.add(oid)
            return self.seed_target
        first_seen = oid not in self._known_ids
        proposed = super().adjust_profit_target(lot, context)
        if oid in self._reversal_ids or self.day_fraction <= 0:
            return proposed
        if first_seen:
            part = self._whole(float(lot.shares) * self.day_fraction)
            if part <= 0:
                return proposed
            self._swing[oid] = (
                self.swing_target
                if self.swing_target is not None
                else float(lot.profit_target if proposed is None else proposed)
            )
            self._day_parts[oid] = part
            return self._day_target(lot)
        if oid in self._split_pending:
            part = self._day_parts.get(oid)
            if part is not None and float(lot.shares) < self._swing_shares(oid, lot) + 1e-6:
                # The day part sold: the rest waits for the swing target.
                self._split_pending.discard(oid)
                self._day_parts.pop(oid, None)
                self.day_sales += 1
                return self._swing.get(oid, proposed)
            self._split_pending.discard(oid)
        if oid in self._day_parts and self._day_close_now:
            # The closing sale: a day part already up day_target_min is sold
            # at the market, as a profit-target sale (no_loss_guard checks it).
            gain = float(context.price) * (1 - 1e-9) / float(lot.buy_price) - 1.0
            if self.day_target_min <= gain < float(lot.profit_target):
                return gain
        if oid in self._day_parts and self._retarget_all:
            return self._day_target(lot)
        return proposed

    def _swing_shares(self, oid: str, lot) -> float:
        """Shares the lot keeps once its day part has sold."""
        return self._held.get(oid, float(lot.shares)) - self._day_parts.get(oid, 0.0)

    def harvest_quantity(self, lot, context: MarketContext) -> float:
        oid = lot.order_id
        part = self._day_parts.get(oid)
        if part is None:
            return float(lot.shares)
        if part >= float(lot.shares) - 1e-6:
            # The whole lot is its day part (day_fraction 1, or what is left).
            self._day_parts.pop(oid, None)
            self.day_sales += 1
            return float(lot.shares)
        self._held[oid] = float(lot.shares)
        self._split_pending.add(oid)
        return part

    def retain_lots(self, open_order_ids) -> None:
        super().retain_lots(open_order_ids)
        keep = set(open_order_ids)
        for store in (self._day_parts, self._swing, self._held):
            for oid in [k for k in store if k not in keep]:
                store.pop(oid, None)
        self._seed_ids &= keep
        self._split_pending &= keep

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        return [
            lot
            for lot in super().lots_to_liquidate(open_lots, context)
            if lot.order_id not in self._seed_ids
        ]

    def diagnostics(self) -> dict:
        out = super().diagnostics()
        out.update(
            forecast_present=self.forecast is not None,
            forecast_sessions=self.forecast_sessions,
            day_level=self.day_level,
            size_multiplier=self._size_mult,
            day_parts_open=len(self._day_parts),
            day_sales=self.day_sales,
            seed_lots=len(self._seed_ids),
            seeds_bought=self._seeds_bought,
            whole_share_refusals=self.whole_share_refusals,
        )
        return out


def _signature() -> inspect.Signature:
    """The run form reads parameters through inspect.signature and skips a
    **kwargs catch-all, so the signature is the parent's parameters plus
    this class's own, spelled out."""
    own = [
        p
        for p in inspect.signature(ForecastHarvestSizing.__init__).parameters.values()
        if p.kind is inspect.Parameter.KEYWORD_ONLY
    ]
    parent = list(inspect.signature(DailyUltimateSizing.__init__).parameters.values())
    names = {p.name for p in own}
    kept = [p for p in parent if p.name not in names]
    return inspect.Signature(
        [kept[0]] + [p.replace(kind=inspect.Parameter.KEYWORD_ONLY) for p in kept[1:]] + own
    )


ForecastHarvestSizing.__init__.__signature__ = _signature()  # type: ignore[attr-defined]
# ... and their annotations, which the form and the live checks read types from
# (typing.get_type_hints resolves them against this module, which imports the
# names they use).
ForecastHarvestSizing.__init__.__annotations__ = {
    **{k: v for k, v in DailyUltimateSizing.__init__.__annotations__.items() if k != "return"},
    **ForecastHarvestSizing.__init__.__annotations__,
}

__all__ = ["SEED", "ForecastHarvestSizing", "forecast_sigma"]
