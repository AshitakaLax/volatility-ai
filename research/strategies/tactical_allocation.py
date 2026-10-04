"""
Tactical asset allocation with moving-average filters -- catalog C-E2
(docs/research/correction-strategies.md, E2).

Source: letianzj/QuantResearch backtest/mebane_faber_taa.py, after Mebane
Faber's "A Quantitative Approach to Tactical Asset Allocation" (the
original paper was not opened). The script's rules, verbatim in spirit:

    universe   SPY, EFA, TIP, GSG, VNQ, each given 1/N of capital
               ("stock_value = npv / 5")
    signal     hold an asset while its 20-day moving average of daily
               closes is above its 200-day ("if ma_fast > ma_slow: # buy"),
               otherwise that slot is cash ("target_size = 0")
    rebalance  only at a month's last trading day

`faber_targets` returns, for each month-end, the target weight per asset
(1/N or 0), decided from closes through that day; `held_weights` carries
each decision forward until the next month-end, starting the session
AFTER it was made, so no weight ever uses the close it trades on.

The catalog's use is a parking rule for idle correction-sleeve capital;
compare tools/rotation.py --mode defensive (X2), which gates each
defensive ETF on its own NATR regime instead of a moving-average cross.
"""

from __future__ import annotations

import pandas as pd

from engine.core.exceptions import ConfigurationError


def month_end_days(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """The last trading day of each month present in `index`."""
    s = pd.Series(index, index=index)
    return pd.DatetimeIndex(s.groupby([index.year, index.month]).max().to_numpy())


def faber_targets(closes: pd.DataFrame, fast: int = 20, slow: int = 200) -> pd.DataFrame:
    """Target weights (1/N or 0) at each month-end; NaN before `slow` closes."""
    if not (isinstance(fast, int) and isinstance(slow, int) and 1 <= fast < slow):
        raise ConfigurationError(f"need integers 1 <= fast < slow, got {fast}, {slow}")
    if closes.shape[1] < 1:
        raise ConfigurationError("need at least one asset")
    ma_fast = closes.rolling(fast, min_periods=fast).mean()
    ma_slow = closes.rolling(slow, min_periods=slow).mean()
    weight = 1.0 / closes.shape[1]
    signal = (ma_fast > ma_slow).astype(float) * weight
    signal = signal.where(ma_slow.notna())
    return signal.loc[month_end_days(closes.index)]


def held_weights(closes: pd.DataFrame, fast: int = 20, slow: int = 200) -> pd.DataFrame:
    """Daily weights: each month-end decision, held from the next session."""
    targets = faber_targets(closes, fast, slow)
    daily = targets.reindex(closes.index).ffill().shift(1)
    return daily
