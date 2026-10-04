"""
Trend-switch regimes from je-suis-tm/quant-trading's technical
indicators, as daily risk-on maps for regime sleeves.

  macd         #1  MACD line above its signal line (EMA 12/26, signal 9)
  awesome      #5  Awesome Oscillator above zero: SMA5 - SMA34 of the
                   median price (H+L)/2
  psar         #8  Parabolic SAR (Wilder) in its rising phase
  heikin_ashi  #3  Heikin-Ashi candles bullish, after `confirm`
                   consecutive candles of the new colour
  sma          catalog R1 (Gayed & Bilello, "Leverage for the Long Run",
                   2016): close above its 200-day simple moving average --
                   not from quant-trading, added with the correction catalog

Each flag is computed at a session's close from that session and those
before it; risk_on_by_date then applies it to the NEXT session through
natr_regime.apply_lag (lag=1), the same causal rule as every other
regime here. True means risk-on: the leveraged sleeve is the active one.

The quant-trading scripts trade these long AND short with stops; under
this project's constraints only the regime survives -- long or out
(or stepped down) -- so these are regime builders, not strategies.
Their recorded prior in plan.md (trend family below buy-and-hold, faster
signals worse in 2022) was measured with the same-session lookahead and
is not evidence either way until re-run causally.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.strategies.natr_regime import apply_lag, debounce

TREND_METHODS: tuple[str, ...] = ("macd", "awesome", "psar", "heikin_ashi", "sma")


def _count(name: str, value) -> int:
    if isinstance(value, bool) or int(value) != value or value < 1:
        raise ConfigurationError(f"{name} must be an integer >= 1, got {value!r}")
    return int(value)


def macd_risk_on(daily: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    fast, slow, signal = _count("fast", fast), _count("slow", slow), _count("signal", signal)
    if fast >= slow:
        raise ConfigurationError(f"macd fast ({fast}) must be < slow ({slow})")
    close = daily["close"].astype(float)
    line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    flags = line > line.ewm(span=signal, adjust=False).mean()
    return flags.iloc[slow + signal :]


def awesome_risk_on(daily: pd.DataFrame, fast: int = 5, slow: int = 34) -> pd.Series:
    fast, slow = _count("fast", fast), _count("slow", slow)
    if fast >= slow:
        raise ConfigurationError(f"awesome fast ({fast}) must be < slow ({slow})")
    median = (daily["high"].astype(float) + daily["low"].astype(float)) / 2.0
    ao = median.rolling(fast).mean() - median.rolling(slow).mean()
    return (ao > 0).iloc[slow - 1 :]


def sma_risk_on(daily: pd.DataFrame, window: int = 200) -> pd.Series:
    """Gayed & Bilello, "Leverage for the Long Run" (2016): hold leverage
    while the unleveraged index closes above its `window`-day simple moving
    average, T-bills below it (catalog R1). Same-session flag; risk_on_by_date
    applies it to the NEXT session, as the paper switches at the next open."""
    window = _count("window", window)
    close = daily["close"].astype(float)
    sma = close.rolling(window).mean()
    return (close > sma).iloc[window - 1 :]


def parabolic_sar(
    daily: pd.DataFrame, step: float = 0.02, max_step: float = 0.2
) -> tuple[np.ndarray, np.ndarray]:
    """Wilder's Parabolic SAR. Returns (sar, rising) per session; index 0
    is the seed (sar NaN). The SAR is never placed inside the previous
    two sessions' range, and a close of the range through it reverses
    the trend with the extreme point as the new SAR."""
    if not 0 < step <= max_step:
        raise ConfigurationError(f"need 0 < step <= max_step, got {step}, {max_step}")
    high = daily["high"].to_numpy(float)
    low = daily["low"].to_numpy(float)
    close = daily["close"].to_numpy(float)
    n = len(close)
    sar_out = np.full(n, np.nan)
    rising = np.zeros(n, dtype=bool)
    if n < 2:
        return sar_out, rising
    up = close[1] >= close[0]
    sar = low[0] if up else high[0]
    ep = high[0] if up else low[0]
    af = step
    rising[0] = up
    for i in range(1, n):
        sar = sar + af * (ep - sar)
        prior = (low[i - 1], low[i - 2] if i >= 2 else low[i - 1])
        prior_h = (high[i - 1], high[i - 2] if i >= 2 else high[i - 1])
        if up:
            sar = min(sar, *prior)
            if low[i] < sar:
                up, sar, ep, af = False, ep, low[i], step
            elif high[i] > ep:
                ep, af = high[i], min(af + step, max_step)
        else:
            sar = max(sar, *prior_h)
            if high[i] > sar:
                up, sar, ep, af = True, ep, high[i], step
            elif low[i] < ep:
                ep, af = low[i], min(af + step, max_step)
        sar_out[i] = sar
        rising[i] = up
    return sar_out, rising


def psar_risk_on(daily: pd.DataFrame, step: float = 0.02, max_step: float = 0.2) -> pd.Series:
    _, rising = parabolic_sar(daily, step, max_step)
    return pd.Series(rising, index=daily.index).iloc[2:]


def heikin_ashi_risk_on(daily: pd.DataFrame, confirm: int = 1) -> pd.Series:
    confirm = _count("confirm", confirm)
    o, h, lo, c = (daily[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    ha_close = (o + h + lo + c) / 4.0
    ha_open = np.empty_like(ha_close)
    ha_open[0] = (o[0] + c[0]) / 2.0
    for i in range(1, len(c)):
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0
    bull = ha_close > ha_open
    state = bool(bull[0])
    run = 0
    out = np.empty(len(c), dtype=bool)
    for i, b in enumerate(bull):
        run = run + 1 if b != state else 0
        if run >= confirm:
            state, run = bool(b), 0
        out[i] = state
    return pd.Series(out, index=daily.index).iloc[1:]


_BUILDERS = {
    "macd": macd_risk_on,
    "awesome": awesome_risk_on,
    "psar": psar_risk_on,
    "heikin_ashi": heikin_ashi_risk_on,
    "sma": sma_risk_on,
}


def risk_on_flags(daily: pd.DataFrame, method: str, **params) -> pd.Series:
    """Same-session flags (lag 0), warm-up removed."""
    if method not in _BUILDERS:
        raise ConfigurationError(f"method must be one of {TREND_METHODS}, got {method!r}")
    return _BUILDERS[method](daily, **params)


def risk_on_by_date(
    daily: pd.DataFrame, method: str = "macd", *, lag: int = 1, min_hold: int = 0, **params
) -> dict[date, bool]:
    """{session: True if risk-on}, keyed by the session it applies to."""
    flags = risk_on_flags(daily, method, **params)
    regime = {ts.date(): bool(v) for ts, v in flags.items()}
    return apply_lag(debounce(regime, min_hold), lag)


__all__ = [
    "TREND_METHODS",
    "awesome_risk_on",
    "heikin_ashi_risk_on",
    "macd_risk_on",
    "parabolic_sar",
    "psar_risk_on",
    "risk_on_by_date",
    "risk_on_flags",
    "sma_risk_on",
]
