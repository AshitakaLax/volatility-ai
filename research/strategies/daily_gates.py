"""
Daily regime levers for the grid, from the algorithm ledger: RK55's ADX
gate and RK297's Hurst-adaptive step.

Both read completed regular sessions only: a session is keyed by the date
of its regular-session bars (time_of_day_flag >= 0), its high, low and
close fold in bar by bar, and a value computed when a session closes
governs the NEXT session -- never the one it was computed from (the
same-session lookahead of the ledger's caveat 1). Neither sells.

RK55  AdxTrendGate -- Wilder's ADX ("New Concepts in Technical Trading
      Systems", 1978), one session at a time:

        TR  = max(H - L, |H - C_prev|, |L - C_prev|)
        +DM = H - H_prev if it exceeds L_prev - L and is positive, else 0
        -DM = L_prev - L if it exceeds H - H_prev and is positive, else 0
        each smoothed s <- s - s / n + x (seeded with the sum of the first
        n - 1, TA-Lib's own start, which tests pin it to)
        +DI = 100 +DM_s / TR_s,  -DI = 100 -DM_s / TR_s
        DX  = 100 |+DI - -DI| / (+DI + -DI),  ADX = Wilder's mean of DX

      The ledger's use is a harvest gate: "pause new lots in strong
      trends", direction-agnostic (`strong_trend`: ADX above `threshold`),
      or only strong DOWN trends (`strong_downtrend`: also -DI > +DI).

RK297 HurstStep -- a rolling Hurst exponent of the last `window` session
      log closes (mean_reversion.hurst_exponent, the C-MR4 estimator)
      scales the grid step by clamp((H / 0.5) ** exponent, lo, hi): with a
      positive exponent a trending tape (H > 0.5) spaces buys wider and a
      mean-reverting one (H < 0.5) tighter. 1.0 until the window is full.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.entry_gates import as_count

ADX_MODES: tuple[str, ...] = ("off", "strong_trend", "strong_downtrend")


def _minute(context: MarketContext) -> int | None:
    """Minutes since 09:30 Eastern, or None for an out-of-session bar."""
    minute = context.time_of_day_flag
    return minute if minute >= 0 else None


class _Sessions:
    """Folds regular-session bars into (high, low, close) per session and
    says when one has closed."""

    def __init__(self) -> None:
        self._day: int | None = None
        self.h = self.l = self.c = None

    def observe(self, context: MarketContext) -> tuple[float, float, float] | None:
        """The session that just CLOSED, when this bar starts a new one."""
        if _minute(context) is None:
            return None
        day = context.timestamp.toordinal()
        closed = None
        if day != self._day:
            if self._day is not None:
                closed = (self.h, self.l, self.c)
            self._day = day
            self.h, self.l, self.c = context.high, context.low, context.close
            return closed
        self.h, self.l, self.c = max(self.h, context.high), min(self.l, context.low), context.close
        return None


class AdxTrendGate:
    """Pause new buys through a session that follows a strong-trend close."""

    def __init__(self, mode: str = "off", *, period: int = 14, threshold: float = 25.0) -> None:
        if mode not in ADX_MODES:
            raise ConfigurationError(f"adx_gate must be one of {ADX_MODES}, got {mode!r}")
        if not 0 < threshold < 100:
            raise ConfigurationError(f"adx_threshold must be in (0, 100), got {threshold}")
        self.mode = mode
        self.period = as_count("adx_period", period, minimum=2)
        self.threshold = float(threshold)
        self._sessions = _Sessions()
        self._prev: tuple[float, float, float] | None = None
        self._n = 0  # sessions with a previous one (a TR / DM value)
        self._tr = self._pdm = self._mdm = 0.0
        self._dx: list[float] = []
        self.adx: float | None = None
        self.plus_di: float | None = None
        self.minus_di: float | None = None
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
    def history_sessions(self) -> int:
        """Sessions before the first ADX: n for the smoothed sums, n DX values."""
        return 2 * self.period + 1

    def observe(self, context: MarketContext) -> None:
        closed = self._sessions.observe(context)
        if closed is not None:
            self._close(*closed)
            was = self._suppressed
            self._suppressed = self._decide()
            if self._suppressed and not was:
                self.episodes += 1
        if self._suppressed and _minute(context) is not None:
            self.suppressed_bars += 1

    def _close(self, h: float, lo: float, c: float) -> None:
        prev, self._prev = self._prev, (h, lo, c)
        if prev is None:
            return
        ph, pl, pc = prev
        tr = max(h - lo, abs(h - pc), abs(lo - pc))
        up, down = h - ph, pl - lo
        pdm = up if up > down and up > 0 else 0.0
        mdm = down if down > up and down > 0 else 0.0
        n = self.period
        self._n += 1
        if self._n < n:  # seed: the sum of the first n - 1, as TA-Lib does
            self._tr += tr
            self._pdm += pdm
            self._mdm += mdm
            return
        self._tr += tr - self._tr / n
        self._pdm += pdm - self._pdm / n
        self._mdm += mdm - self._mdm / n
        if self._tr <= 0:
            return
        self.plus_di, self.minus_di = 100 * self._pdm / self._tr, 100 * self._mdm / self._tr
        total = self.plus_di + self.minus_di
        dx = 0.0 if total <= 0 else 100 * abs(self.plus_di - self.minus_di) / total
        if self.adx is None:
            self._dx.append(dx)
            if len(self._dx) == n:
                self.adx = float(np.mean(self._dx))
        else:
            self.adx = (self.adx * (n - 1) + dx) / n

    def _decide(self) -> bool:
        if not self.enabled or self.adx is None or self.adx <= self.threshold:
            return False
        if self.mode == "strong_downtrend":
            return bool(self.minus_di is not None and self.minus_di > (self.plus_di or 0.0))
        return True


class HurstStep:
    """The grid-step multiplier from a rolling Hurst exponent (RK297)."""

    def __init__(
        self,
        exponent: float = 0.0,
        *,
        window: int = 100,
        max_lag: int = 20,
        lo: float = 0.5,
        hi: float = 2.0,
    ) -> None:
        if not 0 < lo <= 1 <= hi:
            raise ConfigurationError(
                f"need 0 < hurst_step_min <= 1 <= hurst_step_max, got {lo}, {hi}"
            )
        self.exponent = float(exponent)
        self.max_lag = as_count("hurst_max_lag", max_lag, minimum=4)
        self.window = as_count("hurst_window", window, minimum=self.max_lag + 2)
        self.lo, self.hi = float(lo), float(hi)
        self._sessions = _Sessions()
        self._closes: deque[float] = deque(maxlen=self.window)
        self.hurst: float | None = None
        self.multiplier = 1.0

    @property
    def enabled(self) -> bool:
        return self.exponent != 0.0

    @property
    def history_sessions(self) -> int:
        return self.window + 1

    def observe(self, context: MarketContext) -> None:
        closed = self._sessions.observe(context)
        if closed is None:
            return
        self._closes.append(np.log(closed[2]))
        if len(self._closes) < self.window:
            return
        from research.strategies.mean_reversion import hurst_exponent

        h = hurst_exponent(np.fromiter(self._closes, float), self.max_lag)
        if not np.isfinite(h) or h <= 0:
            return
        self.hurst = h
        self.multiplier = float(np.clip((h / 0.5) ** self.exponent, self.lo, self.hi))


__all__ = ["ADX_MODES", "AdxTrendGate", "HurstStep"]
