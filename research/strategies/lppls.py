"""
LPPLS bubble confidence -- Sornette's log-periodic power law singularity
model ("Dragon-Kings, Black Swans and the Prediction of Crises", listed
in awesome-ai-in-finance). RESEARCH-GRADE: ten years of daily data hold
very few bubble-and-crash episodes to validate against.

    ln p(t) = A + B f + C1 f cos(w ln(tc - t)) + C2 f sin(w ln(tc - t)),
    f = (tc - t)^m

For fixed (tc, m, w) the model is linear in (A, B, C1, C2) -- Filimonov
& Sornette's linearisation -- so each candidate is one least-squares
solve. (tc, m, w) are searched on a grid; no SciPy needed.

A fit counts as a POSITIVE BUBBLE when it passes the usual filters:
B < 0 (super-exponential rise), 0.1 <= m <= 0.9, 6 <= w <= 13, tc within
`max_ahead` sessions after the window, and damping m|B| / (w|C|) >= 0.5.
Confidence at a session is the fraction of windows ending there whose
best fit is a bubble. Risk-on while confidence is below `threshold`.

Computed every `step` sessions (carried forward between), each from
closes through that session only, then lagged one session like every
other regime here.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.strategies.natr_regime import apply_lag, debounce

DEFAULT_WINDOWS: tuple[int, ...] = (60, 90, 120, 180, 250)
TC_AHEAD: tuple[int, ...] = (1, 3, 5, 10, 20, 40)
M_GRID: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9)
W_GRID: tuple[float, ...] = (6.0, 8.0, 10.0, 12.0)


def fit(log_prices: np.ndarray) -> dict:
    """Best grid fit of one window (time = 0..n-1, tc beyond n-1)."""
    n = len(log_prices)
    t = np.arange(n, dtype=float)
    best: dict | None = None
    for ahead in TC_AHEAD:
        tc = (n - 1) + ahead
        dt = tc - t
        log_dt = np.log(dt)
        for m in M_GRID:
            f = dt**m
            for w in W_GRID:
                x = np.column_stack([np.ones(n), f, f * np.cos(w * log_dt), f * np.sin(w * log_dt)])
                coef, *_ = np.linalg.lstsq(x, log_prices, rcond=None)
                resid = log_prices - x @ coef
                sse = float(resid @ resid)
                if best is None or sse < best["sse"]:
                    best = {
                        "tc_ahead": ahead,
                        "m": m,
                        "omega": w,
                        "A": coef[0],
                        "B": coef[1],
                        "C1": coef[2],
                        "C2": coef[3],
                        "sse": sse,
                    }
    return best


def is_bubble(params: dict, max_ahead: int = 40) -> bool:
    c = math.hypot(params["C1"], params["C2"])
    damping = float("inf") if c == 0 else params["m"] * abs(params["B"]) / (params["omega"] * c)
    return (
        params["B"] < 0
        and 0.1 <= params["m"] <= 0.9
        and 6.0 <= params["omega"] <= 13.0
        and 0 < params["tc_ahead"] <= max_ahead
        and damping >= 0.5
    )


def confidence(log_close: np.ndarray, end: int, windows=DEFAULT_WINDOWS) -> float | None:
    """Fraction of windows ending at index `end` whose fit is a bubble;
    None when no window fits in the data yet."""
    usable = [w for w in windows if end + 1 >= w]
    if not usable:
        return None
    hits = sum(is_bubble(fit(log_close[end + 1 - w : end + 1])) for w in usable)
    return hits / len(usable)


def risk_on_by_date(
    daily: pd.DataFrame,
    *,
    windows=DEFAULT_WINDOWS,
    threshold: float = 0.5,
    step: int = 5,
    lag: int = 1,
    min_hold: int = 0,
) -> dict[date, bool]:
    if not 0 < threshold <= 1:
        raise ConfigurationError(f"threshold must be in (0, 1], got {threshold}")
    if isinstance(step, bool) or int(step) != step or step < 1:
        raise ConfigurationError(f"step must be an integer >= 1, got {step!r}")
    log_close = np.log(daily["close"].to_numpy(float))
    dates = [ts.date() for ts in daily.index]
    regime: dict[date, bool] = {}
    current: bool | None = None
    for i in range(max(windows) - 1, len(dates)):
        if (i - (max(windows) - 1)) % int(step) == 0:
            conf = confidence(log_close, i, windows)
            current = conf is not None and conf < threshold
        regime[dates[i]] = bool(current)
    return apply_lag(debounce(regime, min_hold), lag)


__all__ = ["DEFAULT_WINDOWS", "confidence", "fit", "is_bubble", "risk_on_by_date"]
