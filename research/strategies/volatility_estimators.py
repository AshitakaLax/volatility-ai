"""
Daily volatility estimators from Euan Sinclair's *Volatility Trading*,
as collected in volest (jasonstrimpel/volatility-trading, listed in
awesome-systematic-trading) -- and a per-session tracker that feeds one
of them causally to a strategy.

  close_to_close   sample stdev of ln(C_t / C_{t-1})
  parkinson        high-low range           (ignores drift and gaps)
  garman_klass     range + open-to-close     (ignores gaps)
  rogers_satchell  drift-independent range   (ignores gaps)
  yang_zhang       overnight + open-to-close + Rogers-Satchell, weighted
                   to minimise estimator variance; the only one here that
                   both uses the intraday range AND counts the overnight
                   gap

WHY YANG-ZHANG IS THE DEFAULT

Corrections tend to arrive overnight: a gap down at the open is often
most of the day's move. Range-only estimators (Parkinson, Garman-Klass,
Rogers-Satchell) never see a gap -- the bar opens where the gap ended.
Close-to-close sees it but throws away the intraday range, so it needs
many more days to reach the same precision. Yang-Zhang keeps both.

Every estimator returns a DAILY variance for a window; `annualized`
turns it into an annualized volatility with 252 sessions a year.

CAUSALITY

SessionVolatility only ever estimates from COMPLETED sessions, so any
decision taken during session D sees sessions strictly before D. A
session is complete when the first regular-session bar of the next one
arrives. Its value equals the vectorized `estimate_series(...)` at the
previous session, which the tests pin.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext

VOL_ESTIMATORS: tuple[str, ...] = (
    "yang_zhang",
    "close_to_close",
    "parkinson",
    "garman_klass",
    "rogers_satchell",
)
SESSIONS_PER_YEAR = 252


def window_variance(
    estimator: str,
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    prev_closes: np.ndarray,
) -> float:
    """Daily variance over one window of n sessions.

    `prev_closes[i]` is the close of the session before session i, so
    the first session's overnight and close-to-close returns are
    defined. All arrays have length n >= 2.
    """
    n = len(closes)
    if n < 2:
        raise ConfigurationError(f"a volatility window needs >= 2 sessions, got {n}")
    if estimator == "close_to_close":
        r = np.log(closes / prev_closes)
        return float(np.var(r, ddof=1))
    hl = np.log(highs / lows)
    if estimator == "parkinson":
        return float(np.sum(hl**2) / (4.0 * n * math.log(2.0)))
    co = np.log(closes / opens)
    if estimator == "garman_klass":
        return float(np.mean(0.5 * hl**2 - (2.0 * math.log(2.0) - 1.0) * co**2))
    rs = np.log(highs / closes) * np.log(highs / opens) + np.log(lows / closes) * np.log(
        lows / opens
    )
    if estimator == "rogers_satchell":
        return float(np.mean(rs))
    if estimator == "yang_zhang":
        overnight = np.log(opens / prev_closes)
        k = 0.34 / (1.34 + (n + 1) / (n - 1))
        return float(np.var(overnight, ddof=1) + k * np.var(co, ddof=1) + (1 - k) * np.mean(rs))
    raise ConfigurationError(f"estimator must be one of {VOL_ESTIMATORS}, got {estimator!r}")


def annualized(daily_variance: float) -> float:
    return math.sqrt(max(daily_variance, 0.0) * SESSIONS_PER_YEAR)


def estimate_series(daily: pd.DataFrame, estimator: str, n: int) -> pd.Series:
    """Annualized volatility at each session from that session and the
    n-1 before it (NaN until n sessions plus one prior close exist).
    The offline reference SessionVolatility is pinned against."""
    if estimator not in VOL_ESTIMATORS:
        raise ConfigurationError(f"estimator must be one of {VOL_ESTIMATORS}, got {estimator!r}")
    o, h, lo, c = (daily[col].to_numpy(float) for col in ("open", "high", "low", "close"))
    out = np.full(len(c), np.nan)
    for end in range(n, len(c)):
        s = slice(end - n + 1, end + 1)
        out[end] = annualized(window_variance(estimator, o[s], h[s], lo[s], c[s], c[end - n : end]))
    return pd.Series(out, index=daily.index)


class SessionVolatility:
    """Annualized volatility of the last n COMPLETED sessions, updated
    once per session from a strategy's bar stream.

    Regular-session bars only (time_of_day_flag >= 0); a session is keyed
    by timestamp.toordinal(), as in entry_gates.py. `value` is None until
    n sessions and the close before them have completed.
    """

    def __init__(self, estimator: str = "yang_zhang", n: int = 20) -> None:
        if estimator not in VOL_ESTIMATORS:
            raise ConfigurationError(
                f"vol_target_estimator must be one of {VOL_ESTIMATORS}, got {estimator!r}"
            )
        if isinstance(n, bool) or int(n) != n or n < 2:
            raise ConfigurationError(f"vol_target_days must be an integer >= 2, got {n!r}")
        self.estimator = estimator
        self.n = int(n)
        self._sessions: deque[tuple[float, float, float, float]] = deque(maxlen=self.n + 1)
        self._day: int | None = None
        self._ohlc: list[float] | None = None
        self.value: float | None = None

    def observe(self, context: MarketContext) -> None:
        minute = context.time_of_day_flag
        if minute < 0:
            return  # out of session: not part of any session's OHLC
        day = context.timestamp.toordinal()
        if day != self._day:
            if self._ohlc is not None:
                self._sessions.append(tuple(self._ohlc))
                self._recompute()
            self._day = day
            self._ohlc = [context.open, context.high, context.low, context.close]
            return
        self._ohlc[1] = max(self._ohlc[1], context.high)
        self._ohlc[2] = min(self._ohlc[2], context.low)
        self._ohlc[3] = context.close

    def _recompute(self) -> None:
        if len(self._sessions) < self.n + 1:
            return
        arr = np.asarray(self._sessions, dtype=float)
        o, h, lo, c = arr[1:, 0], arr[1:, 1], arr[1:, 2], arr[1:, 3]
        self.value = annualized(window_variance(self.estimator, o, h, lo, c, arr[:-1, 3]))


__all__ = [
    "SESSIONS_PER_YEAR",
    "VOL_ESTIMATORS",
    "SessionVolatility",
    "annualized",
    "estimate_series",
    "window_variance",
]
