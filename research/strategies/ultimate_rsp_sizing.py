"""
Ultimate-RSP: a daily-timed exposure book for RSP (docs/research/ultimate-rsp.md).

Not a grid. Every measurement of a grid on RSP lost to simply holding it
(plan.md), and the Ultimate design's slow, small-lot calm sleeve could not
re-enter after a regime exit (exp19). RSP's documented edge is a long/cash
timing overlay -- plan.md's PLUS_DM-below held buy-and-hold's return at a
third of its drawdown in a shell, then failed inside the grid. This
strategy is that overlay built to survive the engine: it holds a target
fraction of equity in RSP, re-set once a day, and moves to it in whole
lots.

--------------------------------------------------------------------
THE TARGET: TWO UNCORRELATED VOTE FAMILIES, AVERAGED

  PD  PLUS_DM(p) below its own trailing `lb`-session median, for every p
      in pd_periods and lb in pd_lookbacks. PLUS_DM in price units is an
      upside-volatility measure (normalised by ATR the effect vanishes,
      by price it survives): calm tape, and the quiet after a sell-off.
  AD  Chaikin ADOSC(fast, slow) below its trailing median, for every pair
      in ad_params and lb in ad_lookbacks: distribution, i.e. contrarian
      on money flow.

  target = pd_weight * mean(PD votes) + (1 - pd_weight) * mean(AD votes)

The two families are uncorrelated on RSP (-0.03), which is why averaging
them is steadier than either; averaging over their parameters as well
(the default, 6 + 6 votes) removes the parameter choice, which a
walk-forward showed to be noise (in-sample vs out-of-sample rank
correlation 0.16). Each vote is computed from sessions strictly before
the one it applies to: the close of D decides D+1. A vote whose median is
not yet defined counts as out.

--------------------------------------------------------------------
EXECUTION, AND THE ONE LOSS PATH

Once per session, at the first bar at or after `execute_minute` (default
60: minutes 30-120 are a plateau, while the open is the worst moment -- in
the engine its slippage takes Calmar from 0.94 to 0.59 -- and the PLUS_DM
edge fades through the day), the book moves to the target if it is more
than `rebalance_band` away: one buy lot for the shortfall (filled at that
bar's open under intrabar fills), or a signal exit of whole lots, newest
first, for the excess.
That exit is the only sale that may realise a loss, so it needs
execution.allow_signal_exit; lots otherwise carry the run's profit target,
which should be set out of reach (the book is meant to hold, not harvest).

Injected exposure: `exposure_by_date` replaces the computed target with a
precomputed causal {date: fraction} map -- how the research lab reproduces
it and checks the incremental computation against the vectorised one.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from datetime import date
from itertools import islice, pairwise

import numpy as np

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.size_calculators import SizingStrategy

NO_BUY_LEVEL = 0.0


def _ints(text: str, name: str) -> tuple[int, ...]:
    try:
        out = tuple(int(x) for x in str(text).replace(" ", "").split(",") if x)
    except ValueError:
        raise ConfigurationError(f"{name} must be comma-separated integers, got {text!r}") from None
    if not out or min(out) < 1:
        raise ConfigurationError(f"{name} must list positive integers, got {text!r}")
    return out


def _pairs(text: str, name: str) -> tuple[tuple[int, int], ...]:
    out = []
    for part in (p for p in str(text).replace(" ", "").split(",") if p):
        try:
            fast, slow = (int(x) for x in part.split("/"))
        except ValueError:
            raise ConfigurationError(f"{name} must look like '3/10,5/20', got {text!r}") from None
        if not 1 <= fast < slow:
            raise ConfigurationError(f"{name}: need 1 <= fast < slow, got {part!r}")
        out.append((fast, slow))
    if not out:
        raise ConfigurationError(f"{name} is empty")
    return tuple(out)


def _below_median(values: deque, lookback: int) -> bool:
    """The latest value below the median of the latest `lookback` values
    (inclusive). Out while any of them is undefined."""
    if len(values) < lookback:
        return False
    window = np.fromiter(islice(values, len(values) - lookback, None), float, lookback)
    if np.isnan(window).any():
        return False
    return bool(window[-1] < np.median(window))


class _PlusDM:
    """TA-Lib's PLUS_DM, one session at a time: the first value (at session
    index period - 1) is the sum of +DM over sessions 1..period-1, then
    Wilder's smoothing s <- s - s / period + dm. tests pin it to TA-Lib."""

    def __init__(self, period: int) -> None:
        self.period, self.s, self.value = period, 0.0, float("nan")

    def update(self, index: int, dm: float) -> float:
        p = self.period
        if 1 <= index < p:
            self.s += dm
            if index == p - 1:
                self.value = self.s
        elif index >= p:
            self.s = self.s - self.s / p + dm
            self.value = self.s
        return self.value


class _Adosc:
    """TA-Lib's ADOSC, one session at a time: fast and slow EMAs of the
    accumulation/distribution line, both seeded with its first value, the
    difference defined from session index slow - 1. tests pin it to TA-Lib."""

    def __init__(self, fast: int, slow: int) -> None:
        self.kf, self.ks, self.slow = 2.0 / (fast + 1), 2.0 / (slow + 1), slow
        self.f = self.s = 0.0

    def update(self, index: int, ad: float) -> float:
        if index == 0:
            self.f = self.s = ad
        else:
            self.f = self.kf * ad + (1.0 - self.kf) * self.f
            self.s = self.ks * ad + (1.0 - self.ks) * self.s
        return self.f - self.s if index >= self.slow - 1 else float("nan")


class RspTimingSignal:
    """The daily exposure target, computed bar by bar from the bars a
    strategy sees. Sessions are calendar days of the bar timestamps (one
    regular session each for a regular-hours dataset). `target` is the
    fraction for the session the latest bar belongs to, from sessions
    before it; None until a session has closed.

    Both indicators are updated incrementally with TA-Lib's own recursions
    (no TA-Lib import: the strategy registry is loaded by the live loop,
    which must start without the optional indicator libraries), so the
    state is a few floats plus the last max(lookback) values of each."""

    def __init__(
        self,
        pd_periods: tuple[int, ...] = (14, 21, 42),
        pd_lookbacks: tuple[int, ...] = (100, 250),
        ad_params: tuple[tuple[int, int], ...] = ((3, 10), (5, 20), (10, 40)),
        ad_lookbacks: tuple[int, ...] = (100, 250),
        pd_weight: float = 0.5,
    ) -> None:
        if not 0.0 <= pd_weight <= 1.0:
            raise ConfigurationError(f"pd_weight must be in [0, 1], got {pd_weight}")
        if min(pd_periods) < 2:
            raise ConfigurationError(f"PLUS_DM periods must be >= 2, got {pd_periods}")
        self.pd_periods, self.pd_lookbacks = tuple(pd_periods), tuple(pd_lookbacks)
        self.ad_params, self.ad_lookbacks = tuple(ad_params), tuple(ad_lookbacks)
        self.pd_weight = float(pd_weight)
        self._pd = {p: _PlusDM(p) for p in self.pd_periods}
        self._ad = {fs: _Adosc(*fs) for fs in self.ad_params}
        self._pd_hist = {p: deque(maxlen=max(self.pd_lookbacks)) for p in self.pd_periods}
        self._ad_hist = {fs: deque(maxlen=max(self.ad_lookbacks)) for fs in self.ad_params}
        self._day: date | None = None
        self._h = self._l = self._c = None
        self._v = 0.0
        self._sessions = 0
        self._prev_h = self._prev_l = None
        self._acc_dist = 0.0
        self.target: float | None = None
        self.votes: dict[str, bool] = {}

    def observe(self, timestamp, high: float, low: float, close: float, volume: float) -> None:
        day = timestamp.date()
        if day != self._day:
            if self._day is not None:
                self._close_session()
            self._day = day
            self._h, self._l, self._c, self._v = high, low, close, float(volume)
            return
        self._h = max(self._h, high)
        self._l = min(self._l, low)
        self._c = close
        self._v += float(volume)

    def warm_up(self, daily) -> int:
        """Seed from session OHLCV (one row per session, a datetime index,
        high/low/close/volume columns) before the first bar; the last row
        may be today's partial session. Rows must be in date order and
        after any session already observed. Returns the rows consumed."""
        missing = {"high", "low", "close", "volume"} - set(daily.columns)
        if missing:
            raise ConfigurationError(f"daily bars are missing {sorted(missing)}")
        days = [ts.date() for ts in daily.index]
        if any(b <= a for a, b in pairwise(days)):
            raise ConfigurationError("warm-up sessions must be in strictly increasing date order")
        if days and self._day is not None and days[0] <= self._day:
            raise ConfigurationError(
                f"warm-up starts {days[0]}, not after the latest observed session {self._day}"
            )
        for ts, h, lo, c, v in zip(
            daily.index,
            daily["high"].to_numpy(float),
            daily["low"].to_numpy(float),
            daily["close"].to_numpy(float),
            daily["volume"].to_numpy(float),
            strict=True,
        ):
            self.observe(ts, float(h), float(lo), float(c), float(v))
        return len(days)

    def _close_session(self) -> None:
        i, h, lo, c, v = self._sessions, self._h, self._l, self._c, self._v
        dm = 0.0
        if self._prev_h is not None:
            up, down = h - self._prev_h, self._prev_l - lo
            dm = up if (up > 0.0 and up > down) else 0.0
        for p, ind in self._pd.items():
            self._pd_hist[p].append(ind.update(i, dm))
        if h - lo > 0.0:
            self._acc_dist += ((c - lo) - (h - c)) / (h - lo) * v
        for fs, ind in self._ad.items():
            self._ad_hist[fs].append(ind.update(i, self._acc_dist))
        self._prev_h, self._prev_l = h, lo
        self._sessions += 1
        self.target = self._vote()

    def _vote(self) -> float:
        votes: dict[str, bool] = {}
        pd_votes, ad_votes = [], []
        for p in self.pd_periods:
            for lb in self.pd_lookbacks:
                v = _below_median(self._pd_hist[p], lb)
                votes[f"PD{p}/{lb}"] = v
                pd_votes.append(v)
        for fast, slow in self.ad_params:
            for lb in self.ad_lookbacks:
                v = _below_median(self._ad_hist[(fast, slow)], lb)
                votes[f"AD{fast}-{slow}/{lb}"] = v
                ad_votes.append(v)
        self.votes = votes
        pd_part = sum(pd_votes) / len(pd_votes) if pd_votes else 0.0
        ad_part = sum(ad_votes) / len(ad_votes) if ad_votes else 0.0
        return self.pd_weight * pd_part + (1.0 - self.pd_weight) * ad_part


class UltimateRspSizing(SizingStrategy):
    """A daily-timed exposure book: see the module docstring."""

    def __init__(
        self,
        pd_periods: str = "14,21,42",
        pd_lookbacks: str = "100,250",
        ad_params: str = "3/10,5/20,10/40",
        ad_lookbacks: str = "100,250",
        pd_weight: float = 0.5,
        execute_minute: int = 60,
        rebalance_band: float = 0.05,
        max_exposure: float = 1.0,
        cash_buffer: float = 0.005,
        exposure_by_date: Mapping[date, float] | None = None,
    ) -> None:
        if not 0 <= execute_minute < 390:
            raise ConfigurationError(f"execute_minute must be in [0, 390), got {execute_minute}")
        if not 0.0 < rebalance_band < 1.0:
            raise ConfigurationError(f"rebalance_band must be in (0, 1), got {rebalance_band}")
        if not 0.0 < max_exposure <= 1.0:
            raise ConfigurationError(f"max_exposure must be in (0, 1], got {max_exposure}")
        if not 0.0 <= cash_buffer < 0.1:
            raise ConfigurationError(f"cash_buffer must be in [0, 0.1), got {cash_buffer}")
        self.execute_minute = int(execute_minute)
        self.rebalance_band = float(rebalance_band)
        self.max_exposure = float(max_exposure)
        self.cash_buffer = float(cash_buffer)
        self._map = dict(exposure_by_date) if exposure_by_date else None
        self._signal = (
            None
            if self._map is not None
            else RspTimingSignal(
                pd_periods=_ints(pd_periods, "pd_periods"),
                pd_lookbacks=_ints(pd_lookbacks, "pd_lookbacks"),
                ad_params=_pairs(ad_params, "ad_params"),
                ad_lookbacks=_ints(ad_lookbacks, "ad_lookbacks"),
                pd_weight=pd_weight,
            )
        )
        self._day: int | None = None
        self.target: float | None = None
        self._done = True
        self._gap = 0.0  # signed fraction of equity to move this bar; 0 = no action
        self._equity = 0.0
        self.rebalances = 0
        self.exposure: float | None = None

    def warm_up(self, daily) -> int:
        """Seed the timing signal from session history before the first bar
        (RspTimingSignal.warm_up). A no-op with an injected exposure map."""
        if self._signal is None:
            return 0
        return self._signal.warm_up(daily)

    # ------------------------------------------------------------ per bar

    def record_tick(self, context: MarketContext) -> None:
        if self._signal is not None:
            self._signal.observe(
                context.timestamp, context.high, context.low, context.close, context.volume
            )
        self._gap = 0.0
        minute = context.time_of_day_flag
        if minute < 0:
            return
        day = context.timestamp.toordinal()
        if day != self._day:
            self._day = day
            if self._map is not None:
                self.target = self._map.get(context.timestamp.date())
            else:
                self.target = self._signal.target
            self._done = self.target is None
        if self._done or minute < self.execute_minute:
            return
        self._done = True
        equity = float(context.equity)
        if equity <= 0:
            return
        exposure = max(0.0, (equity - float(context.cash)) / equity)
        self.exposure = exposure
        want = min(self.target, self.max_exposure)
        if abs(want - exposure) > self.rebalance_band or (want == 0.0 and exposure > 1e-6):
            self._gap = want - exposure
            self._equity = equity
            self.rebalances += 1

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """ "Buy this bar": the bar's high, which every fill model accepts.
        It triggers under both models (low <= high, close <= high); with
        causal or open_or_level booking the engine fills at min(level,
        open), the open; with close fills, at the close; with the legacy
        level booking, at the high -- conservative. An unreachable sentinel
        would be booked AS the price under level booking."""
        if self._gap <= 0:
            return NO_BUY_LEVEL
        return max(float(context.high), float(context.open), float(context.close))

    def calculate_trade_value(self, context: MarketContext) -> float:
        if self._gap <= 0:
            return 0.0
        room = float(context.cash) * (1.0 - self.cash_buffer)
        return max(0.0, min(self._gap * self._equity, room))

    # ------------------------------------------------------------ lots

    def wants_lot_retargeting(self) -> bool:
        return False  # every lot keeps the run's (out-of-reach) target

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        """Whole lots, newest first, worth about the excess exposure. A
        shortfall of more than half the band takes one more lot, because
        cutting risk is the point of the exit."""
        if self._gap >= 0 or not open_lots:
            return []
        if self.target is not None and min(self.target, self.max_exposure) == 0.0:
            return list(open_lots)
        price = float(context.close)
        amount = -self._gap * self._equity
        slack = 0.5 * self.rebalance_band * self._equity
        chosen, total, rest = [], 0.0, []
        for lot in reversed(list(open_lots)):
            value = float(lot.shares) * price
            if total + value <= amount + slack:
                chosen.append(lot)
                total += value
            else:
                rest.append((value, lot))
            if total >= amount - slack:
                return chosen
        if rest and total < amount - slack:
            need = amount - total
            fits = [r for r in rest if r[0] >= need]
            pick = min(fits, key=lambda r: r[0]) if fits else max(rest, key=lambda r: r[0])
            chosen.append(pick[1])
        return chosen

    def diagnostics(self) -> dict:
        return {
            "ultimate_rsp_target": self.target,
            "ultimate_rsp_exposure": self.exposure,
            "ultimate_rsp_rebalances": self.rebalances,
        }


__all__ = ["NO_BUY_LEVEL", "RspTimingSignal", "UltimateRspSizing"]
