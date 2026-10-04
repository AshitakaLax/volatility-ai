"""
Information-driven bars and fractional differentiation -- catalog C-ML5
(docs/research/correction-strategies.md, ML5).

Source: Lopez de Prado, *Advances in Financial Machine Learning* (2018),
ch. 2 (bars) and ch. 5 (fractional differentiation); orderflow-metrics
implements tick, volume and dollar bars by the same names.

BARS sample by activity instead of the clock, so a heavy-volume selloff
yields more bars -- more resolution exactly when it matters.

  tick_bars     every `n` rows
  volume_bars   close a bar once accumulated volume reaches `threshold`
  dollar_bars   the same on price * volume
  tick_imbalance_bars
                AFML 2.3.2.1: b_t is the tick rule (+1 on an uptick, -1 on
                a downtick, the previous b on no change); theta_T = sum b_t
                over the bar, closed once |theta_T| >= E0[T] * |2P[b=1] - 1|.
                The expectations start at `expected_ticks` and `p_buy` and,
                with `ewm_alpha` > 0, are updated by an EWMA of each closed
                bar's length and buy share (alpha = 0 keeps them fixed).

Each bar is a row of open/high/low/close/volume/rows taken from whole input
rows; a row is never split.

FRACTIONAL DIFFERENTIATION, fixed-width window (FFD):

    w_0 = 1,  w_k = -w_{k-1} * (d - k + 1) / k
    keep weights while |w_k| >= threshold
    x~_t = sum_k w_k * x_{t-k}

d = 1 is the first difference and d = 0 the series itself; 0 < d < 1 makes
a price series closer to stationary while keeping more memory than returns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError


def _bar(rows: pd.DataFrame) -> dict[str, float]:
    return {
        "open": float(rows["close"].iloc[0] if "open" not in rows else rows["open"].iloc[0]),
        "high": float(rows["high"].max() if "high" in rows else rows["close"].max()),
        "low": float(rows["low"].min() if "low" in rows else rows["close"].min()),
        "close": float(rows["close"].iloc[-1]),
        "volume": float(rows["volume"].sum()) if "volume" in rows else 0.0,
        "rows": len(rows),
    }


def _bars_from_cuts(df: pd.DataFrame, cut_after: list[int]) -> pd.DataFrame:
    out, start = [], 0
    for end in cut_after:
        out.append(_bar(df.iloc[start : end + 1]))
        start = end + 1
    return pd.DataFrame(out, columns=["open", "high", "low", "close", "volume", "rows"])


def tick_bars(df: pd.DataFrame, n: int) -> pd.DataFrame:
    if not (isinstance(n, int) and n >= 1):
        raise ConfigurationError(f"n must be an integer >= 1, got {n!r}")
    cuts = list(range(n - 1, len(df), n))
    return _bars_from_cuts(df, cuts)


def _threshold_bars(df: pd.DataFrame, amounts: np.ndarray, threshold: float) -> pd.DataFrame:
    if not threshold > 0:
        raise ConfigurationError(f"threshold must be > 0, got {threshold}")
    cuts, acc = [], 0.0
    for i, amount in enumerate(amounts):
        acc += amount
        if acc >= threshold:
            cuts.append(i)
            acc = 0.0
    return _bars_from_cuts(df, cuts)


def volume_bars(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    return _threshold_bars(df, df["volume"].to_numpy(dtype=float), threshold)


def dollar_bars(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    amounts = (df["close"] * df["volume"]).to_numpy(dtype=float)
    return _threshold_bars(df, amounts, threshold)


def tick_rule(prices) -> np.ndarray:
    """b_t: +1 uptick, -1 downtick, previous b on no change (the first row,
    with no previous price, is +1 by convention)."""
    p = np.asarray(prices, dtype=float)
    b = np.empty(p.size)
    prev = 1.0
    for i in range(p.size):
        if i > 0 and p[i] > p[i - 1]:
            prev = 1.0
        elif i > 0 and p[i] < p[i - 1]:
            prev = -1.0
        b[i] = prev
    return b


def tick_imbalance_bars(
    df: pd.DataFrame, expected_ticks: float, p_buy: float = 0.5, ewm_alpha: float = 0.0
) -> pd.DataFrame:
    if not expected_ticks > 0:
        raise ConfigurationError(f"expected_ticks must be > 0, got {expected_ticks}")
    if not 0 <= p_buy <= 1 or not 0 <= ewm_alpha <= 1:
        raise ConfigurationError("p_buy and ewm_alpha must be in [0, 1]")
    b = tick_rule(df["close"].to_numpy(dtype=float))
    e_t, e_p = float(expected_ticks), float(p_buy)
    cuts, theta, start = [], 0.0, 0
    for i, sign in enumerate(b):
        theta += sign
        threshold = e_t * abs(2.0 * e_p - 1.0)
        if abs(theta) >= threshold:
            length = i - start + 1
            buys = float((b[start : i + 1] > 0).mean())
            e_t = (1 - ewm_alpha) * e_t + ewm_alpha * length
            e_p = (1 - ewm_alpha) * e_p + ewm_alpha * buys
            cuts.append(i)
            theta, start = 0.0, i + 1
    return _bars_from_cuts(df, cuts)


def ffd_weights(d: float, threshold: float = 1e-5, max_terms: int = 10_000) -> np.ndarray:
    """w_0..w_l with |w_k| >= threshold (fixed-width window)."""
    if d < 0:
        raise ConfigurationError(f"d must be >= 0, got {d}")
    if not threshold > 0:
        raise ConfigurationError(f"threshold must be > 0, got {threshold}")
    weights = [1.0]
    for k in range(1, max_terms):
        w = -weights[-1] * (d - k + 1) / k
        if abs(w) < threshold:
            break
        weights.append(w)
    return np.array(weights)


def frac_diff_ffd(series: pd.Series, d: float, threshold: float = 1e-5) -> pd.Series:
    """x~_t = sum_k w_k x_{t-k}; NaN until the window has filled."""
    w = ffd_weights(d, threshold)
    x = series.astype(float).to_numpy()
    out = np.full(x.size, np.nan)
    width = w.size
    for t in range(width - 1, x.size):
        window = x[t - width + 1 : t + 1][::-1]  # x_t, x_{t-1}, ...
        out[t] = float(w @ window)
    return pd.Series(out, index=series.index)
