"""
Turbulence regime: calm while a basket's returns look like their own
recent history, turbulent when they do not.

From "Deep Reinforcement Learning for Automated Stock Trading: An
Ensemble Strategy" (2020, listed in awesome-ai-in-finance), which stops
trading when market turbulence crosses a threshold. The index itself is
Kritzman & Li's:

    d_t = (y_t - mu)' Sigma^-1 (y_t - mu)

y_t is the vector of the basket's log returns on day t; mu and Sigma
are their mean and covariance over the `lookback` days strictly BEFORE
t. A day is unusual if any single asset moved a lot, OR if assets moved
in a combination the covariance says is rare -- stocks and bonds falling
together, for instance, which single-asset NATR cannot see.

calm on D+1  <=>  d at the close of D  <  the q-quantile of d over the
                  `threshold_lookback` days ending at D

then applied one session later, exactly as natr_regime.calm_by_date
does with lag=1. The basket is DATA only -- nothing here trades TLT or
GLD; it only lets the regime see them.

Sigma is inverted with a pseudo-inverse: a basket of near-collinear
assets (QQQ and TQQQ, say) gives a near-singular covariance, and a
pinv degrades gracefully where an inverse would explode.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.strategies.natr_regime import apply_lag, daily_bars


def basket_closes(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Daily closes per ticker from minute frames, on the sessions ALL
    of them traded (inner join), so no return is computed across a
    missing day."""
    if len(frames) < 2:
        raise ConfigurationError("a turbulence basket needs at least two tickers")
    closes = {name: daily_bars(frame)["close"] for name, frame in frames.items()}
    return pd.DataFrame(closes).dropna(how="any")


def turbulence_index(returns: pd.DataFrame, lookback: int = 252) -> pd.Series:
    """Mahalanobis distance of each day's returns from the previous
    `lookback` days. NaN until `lookback` prior days exist."""
    if lookback < returns.shape[1] + 1:
        raise ConfigurationError(
            f"lookback must exceed the basket size ({returns.shape[1]}), got {lookback}"
        )
    values = returns.to_numpy(float)
    out = np.full(len(values), np.nan)
    for t in range(lookback, len(values)):
        history = values[t - lookback : t]
        diff = values[t] - history.mean(axis=0)
        out[t] = float(diff @ np.linalg.pinv(np.cov(history, rowvar=False)) @ diff)
    return pd.Series(out, index=returns.index)


def calm_by_date(
    closes: pd.DataFrame,
    *,
    lookback: int = 252,
    quantile: float = 0.9,
    threshold_lookback: int = 252,
    lag: int = 1,
) -> dict[date, bool]:
    """{session date: True if calm}, keyed by the session it APPLIES to.

    Warm-up sessions (no index yet, or no full threshold window) are
    omitted rather than reported as turbulent -- a sleeve treats a
    missing date as "regime unknown", not as a call.
    """
    if not 0.0 < quantile < 1.0:
        raise ConfigurationError(f"quantile must be in (0, 1), got {quantile}")
    if threshold_lookback < 2:
        raise ConfigurationError(f"threshold_lookback must be >= 2, got {threshold_lookback}")
    returns = np.log(closes / closes.shift(1)).dropna(how="any")
    index = turbulence_index(returns, lookback)
    threshold = index.rolling(threshold_lookback, min_periods=threshold_lookback).quantile(quantile)
    defined = index.notna() & threshold.notna()
    flags = {ts.date(): bool(v) for ts, v in (index < threshold)[defined].items()}
    return apply_lag(flags, lag)


__all__ = ["basket_closes", "calm_by_date", "turbulence_index"]
