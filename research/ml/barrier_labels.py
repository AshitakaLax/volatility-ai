"""
Triple-barrier and trend-scanning labels -- catalog C-ML1
(docs/research/correction-strategies.md, ML1).

Sources: Lopez de Prado, *Advances in Financial Machine Learning* (2018),
ch. 3 (the triple-barrier method), and *Machine Learning for Asset
Managers* (2020), sec. 5.4 (trend scanning); both as taught in
stefan-jansen/machine-learning-for-trading ch. 7.

TRIPLE BARRIER

For an event at bar t0 with entry price p0, three barriers:

    upper     p0 * (1 + upper)        (None: no upper barrier)
    lower     p0 * (1 - lower)        (None: no lower barrier)
    vertical  bar t0 + max_hold       (clipped at the last bar)

walked forward on closes from t0 + 1. The label is +1 if the upper
barrier is touched first, -1 if the lower one is, and at the vertical
barrier the sign of the return (AFML's getBins) -- or 0 with
`vertical="zero"`, the variant that keeps "neither barrier" as its own
class.

The catalog's mapping onto the no-loss grid is one-to-one: upper = the
lot's take-profit, lower = the regime-exit level, vertical = a maximum
hold. These are TRAINING TARGETS: they look forward by construction and
must never be fed to a strategy as inputs.

TREND SCANNING

For each bar t and each look-forward length L in `spans`, fit
x_{t..t+L-1} = a + b*i by OLS and take the slope's t-value. The label is
the sign of the t-value with the largest |t| over the spans, kept with
that t-value (a confidence weight) and the end bar t + L - 1. Bars with
fewer than min(spans) bars ahead get no label.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

VERTICAL_LABELS: tuple[str, ...] = ("sign", "zero")


def triple_barrier_labels(
    closes: pd.Series,
    event_positions,
    *,
    upper: float | None,
    lower: float | None,
    max_hold: int,
    vertical: str = "sign",
) -> pd.DataFrame:
    """One row per event: t0, t1 (bar of the first touch), barrier
    ('upper' / 'lower' / 'vertical'), ret (close at t1 / entry - 1) and
    label. Positions are integer bar offsets into `closes`."""
    if upper is not None and not upper > 0:
        raise ConfigurationError(f"upper must be > 0 or None, got {upper}")
    if lower is not None and not 0 < lower < 1:
        raise ConfigurationError(f"lower must be in (0, 1) or None, got {lower}")
    if not (isinstance(max_hold, int) and max_hold >= 1):
        raise ConfigurationError(f"max_hold must be an integer >= 1, got {max_hold!r}")
    if vertical not in VERTICAL_LABELS:
        raise ConfigurationError(f"vertical must be one of {VERTICAL_LABELS}, got {vertical!r}")
    prices = closes.to_numpy(dtype=float)
    n = prices.size
    rows = []
    for t0 in event_positions:
        t0 = int(t0)
        if not 0 <= t0 < n - 1:
            continue  # no bar after the entry to walk
        p0 = prices[t0]
        up = None if upper is None else p0 * (1.0 + upper)
        dn = None if lower is None else p0 * (1.0 - lower)
        end = min(t0 + max_hold, n - 1)
        t1, barrier = end, "vertical"
        for t in range(t0 + 1, end + 1):
            if up is not None and prices[t] >= up:
                t1, barrier = t, "upper"
                break
            if dn is not None and prices[t] <= dn:
                t1, barrier = t, "lower"
                break
        ret = prices[t1] / p0 - 1.0
        if barrier == "upper":
            label = 1
        elif barrier == "lower":
            label = -1
        else:
            label = int(np.sign(ret)) if vertical == "sign" else 0
        rows.append({"t0": t0, "t1": t1, "barrier": barrier, "ret": ret, "label": label})
    return pd.DataFrame(rows, columns=["t0", "t1", "barrier", "ret", "label"])


def ols_slope_tvalue(values) -> float:
    """t-value of b in values_i = a + b*i (i = 0..L-1). Infinite for a
    perfect fit with a non-zero slope; 0 for a flat line."""
    y = np.asarray(values, dtype=float)
    length = y.size
    if length < 3:
        raise ConfigurationError("need at least 3 points for a slope t-value")
    x = np.arange(length, dtype=float)
    xc = x - x.mean()
    sxx = float((xc**2).sum())
    b = float((xc * (y - y.mean())).sum()) / sxx
    resid = y - (y.mean() + b * xc)
    s2 = float((resid**2).sum()) / (length - 2)
    if s2 == 0:
        return 0.0 if b == 0 else math.copysign(math.inf, b)
    return b / math.sqrt(s2 / sxx)


def trend_scanning_labels(closes: pd.Series, spans) -> pd.DataFrame:
    """One row per labelled bar t: t1 (= t + L - 1 for the chosen L),
    t_value and label = sign(t_value)."""
    spans = sorted({int(s) for s in spans})
    if not spans or spans[0] < 3:
        raise ConfigurationError("spans must be integers >= 3")
    prices = closes.to_numpy(dtype=float)
    n = prices.size
    rows = []
    for t in range(n - spans[0] + 1):
        best_t, best_end = None, None
        for length in spans:
            if t + length > n:
                break
            tv = ols_slope_tvalue(prices[t : t + length])
            if best_t is None or abs(tv) > abs(best_t):
                best_t, best_end = tv, t + length - 1
        rows.append({"t0": t, "t1": best_end, "t_value": best_t, "label": int(np.sign(best_t))})
    return pd.DataFrame(rows, columns=["t0", "t1", "t_value", "label"])
