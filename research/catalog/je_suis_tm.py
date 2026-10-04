"""
je-suis-tm/quant-trading's strategies as the original TRADES -- long and
short, with their stops and session exits -- transcribed from the scripts
(ledger section 5). The ledger built most of these only as regimes or no-buy
gates (Q1, Q3, Q5, Q8, Q9, Q10, N1-N4) because shorting, price stops and
end-of-day flattening are out of scope for the platform; this module keeps
the source behaviour itself, quirks included, for the database.

Each function returns per-bar `signals` in the source's convention (+1 buy,
-1 sell, larger magnitudes for a flip) and `positions` = their running sum,
unless noted. Index-based loops are kept index-based so the transcription
can be read side by side with the script.

Source quirks preserved on purpose (each also documented at its function):

  * awesome_trades: the AO-above/below-slow-MA assignment runs after the
    saucer rules on every bar and overwrites them, so the saucers almost
    never take effect -- the script trades long while AO > 0, flat else.
  * psar_script: the script's own SAR seeding (`sar[1] = High[0]` in an
    uptrend) and its 'real sar', not Wilder's textbook seeding; and real
    sar is 0 at index 0, so position[0] is 1.
  * rsi_head_shoulders_trades: the nodes are found on the CLOSE (with an
    absolute tolerance of 0.2), not on the RSI; the RSI only drives the exit.
  * shooting_star_trades: confirmation uses the NEXT bar (shift(-1)) and the
    body test a FULL-SAMPLE mean -- both lookahead. `causal=True` fixes both
    (the ledger's N4 gate does the same).
  * dual_thrust_trades: the daily range is a rolling window that includes
    the CURRENT day's high/low/close, unknown at the session open --
    lookahead. `causal=True` uses the previous `rg` days only.
"""

from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.strategies.mean_reversion import adf

# ---------------------------------------------------------------- Q1 MACD


def macd_crossover(close, ma1: int = 12, ma2: int = 26) -> pd.DataFrame:
    """MACD Oscillator backtest.py: SIMPLE moving averages (min_periods=1);
    from bar ma1 on, long (1) when ma1 >= ma2 else flat (0). The script
    notes 12/26 is classic and 10/21 its preferred choice."""
    if not (isinstance(ma1, int) and isinstance(ma2, int) and 1 <= ma1 < ma2):
        raise ConfigurationError(f"need integers 1 <= ma1 < ma2, got {ma1}, {ma2}")
    s = pd.Series(np.asarray(close, dtype=float))
    m1 = s.rolling(ma1, min_periods=1).mean()
    m2 = s.rolling(ma2, min_periods=1).mean()
    positions = np.zeros(len(s), dtype=int)
    positions[ma1:] = np.where(m1[ma1:] >= m2[ma1:], 1, 0)
    signals = np.diff(positions, prepend=positions[0])
    return pd.DataFrame({"ma1": m1, "ma2": m2, "positions": positions, "signals": signals})


# ---------------------------------------------------------------- Q5 Awesome


def awesome_trades(df: pd.DataFrame) -> pd.DataFrame:
    """Awesome Oscillator backtest.py's awesome_signal_generation, verbatim:
    saucer rules, then the AO-sign override that makes them nearly inert."""
    o, c = df["open"].to_numpy(float), df["close"].to_numpy(float)
    median = (df["high"].astype(float) + df["low"].astype(float)) / 2.0
    ma1 = median.rolling(5).mean().to_numpy()
    ma2 = median.rolling(34).mean().to_numpy()
    ao = ma1 - ma2
    n = len(df)
    sig = np.zeros(n, dtype=int)
    total = 0  # sum of finalised signals before bar i
    for i in range(2, n):
        if (
            o[i] > c[i]
            and o[i - 1] < c[i - 1]
            and o[i - 2] < c[i - 2]
            and ao[i - 1] > ao[i - 2]
            and ao[i - 1] < 0
            and ao[i] < 0
        ):
            sig[i] = 1
        if (
            o[i] < c[i]
            and o[i - 1] > c[i - 1]
            and o[i - 2] > c[i - 2]
            and ao[i - 1] < ao[i - 2]
            and ao[i - 1] > 0
            and ao[i] > 0
        ):
            sig[i] = -1
        if ma1[i] > ma2[i]:
            sig[i] = 1
            if total + sig[i] > 1:
                sig[i] = 0
        if ma1[i] < ma2[i]:
            sig[i] = -1
            if total + sig[i] < 0:
                sig[i] = 0
        total += sig[i]
    return pd.DataFrame({"ao": ao, "signals": sig, "positions": np.cumsum(sig)})


# ---------------------------------------------------------------- Q3 Heikin-Ashi


def heikin_ashi_candles(df: pd.DataFrame) -> pd.DataFrame:
    """HA close = (O+C+H+L)/4; HA open[0] = Open[0], then the mean of the
    previous HA open and close; HA high/low = max/min of HA open, HA close,
    Low and High (the script's four-column max/min)."""
    o, h, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    ha_close = (o + c + h + lo) / 4.0
    ha_open = np.empty_like(ha_close)
    ha_open[0] = o[0]
    for n in range(1, len(o)):
        ha_open[n] = (ha_open[n - 1] + ha_close[n - 1]) / 2.0
    stack = np.vstack([ha_open, ha_close, lo, h])
    return pd.DataFrame(
        {
            "ha_open": ha_open,
            "ha_close": ha_close,
            "ha_high": stack.max(axis=0),
            "ha_low": stack.min(axis=0),
        }
    )


def heikin_ashi_trades(df: pd.DataFrame, stls: int = 3) -> pd.DataFrame:
    """Heikin-Ashi backtest.py's signal_generation: buy after a strong red
    HA candle with no upper wick following another red one (up to `stls`
    stacked units); sell everything after a green candle with no lower wick
    following another green one. Exact float equality, as in the source."""
    ha = heikin_ashi_candles(df)
    op, cl, hi, lw = (ha[k].to_numpy() for k in ("ha_open", "ha_close", "ha_high", "ha_low"))
    n = len(ha)
    sig = np.zeros(n, dtype=int)
    total = 0
    for k in range(1, n):
        if (
            op[k] > cl[k]
            and op[k] == hi[k]
            and abs(op[k] - cl[k]) > abs(op[k - 1] - cl[k - 1])
            and op[k - 1] > cl[k - 1]
        ):
            sig[k] = 1
            if total + 1 > stls:
                sig[k] = 0
        elif op[k] < cl[k] and op[k] == lw[k] and op[k - 1] < cl[k - 1]:
            sig[k] = -1
            if total - 1 > 0:
                sig[k] = -total
            if total - 1 < 0:
                sig[k] = 0
        total += sig[k]
    out = ha.copy()
    out["signals"], out["positions"] = sig, np.cumsum(sig)
    return out


# ---------------------------------------------------------------- Q8 Parabolic SAR


def psar_script(
    df: pd.DataFrame, initial_af: float = 0.02, step_af: float = 0.02, end_af: float = 0.2
) -> pd.DataFrame:
    """Parabolic SAR backtest.py's own SAR, transcribed line by line (its
    seeding differs from Wilder's: trend from Close[1] vs Close[0],
    sar[1] = High[0] in an uptrend)."""
    h, lo, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    n = len(c)
    trend = np.zeros(n, dtype=int)
    sar, real, ep, af = (np.zeros(n) for _ in range(4))
    if n < 3:
        raise ConfigurationError("need at least three bars")
    trend[1] = 1 if c[1] > c[0] else -1
    sar[1] = h[0] if trend[1] > 0 else lo[0]
    real[1] = sar[1]
    ep[1] = h[1] if trend[1] > 0 else lo[1]
    af[1] = initial_af
    for i in range(2, n):
        temp = sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1])
        if trend[i - 1] < 0:
            sar[i] = max(temp, h[i - 1], h[i - 2])
            t = 1 if sar[i] < h[i] else trend[i - 1] - 1
        else:
            sar[i] = min(temp, lo[i - 1], lo[i - 2])
            t = -1 if sar[i] > lo[i] else trend[i - 1] + 1
        trend[i] = t
        if trend[i] < 0:
            ep[i] = min(lo[i], ep[i - 1]) if trend[i] != -1 else lo[i]
        else:
            ep[i] = max(h[i], ep[i - 1]) if trend[i] != 1 else h[i]
        if abs(trend[i]) == 1:
            real[i] = ep[i - 1]
            af[i] = initial_af
        else:
            real[i] = sar[i]
            af[i] = af[i - 1] if ep[i] == ep[i - 1] else min(end_af, af[i - 1] + step_af)
    positions = np.where(real < c, 1, 0)
    return pd.DataFrame(
        {
            "trend": trend,
            "sar": sar,
            "real_sar": real,
            "ep": ep,
            "af": af,
            "positions": positions,
            "signals": np.diff(positions, prepend=positions[0]),
        }
    )


# ---------------------------------------------------------------- Q9 Bollinger W


def bollinger_bands(price, window: int = 20, k: float = 2.0) -> pd.DataFrame:
    p = pd.Series(np.asarray(price, dtype=float))
    std = p.rolling(window, min_periods=window).std()
    mid = p.rolling(window, min_periods=window).mean()
    return pd.DataFrame(
        {"price": p, "std": std, "mid": mid, "upper": mid + k * std, "lower": mid - k * std}
    )


def bollinger_w_trades(
    price,
    period: int = 75,
    alpha: float = 0.0001,
    beta: float = 0.0001,
    window: int = 20,
    k: float = 2.0,
) -> pd.DataFrame:
    """Bollinger Bands Pattern Recognition backtest.py, verbatim: at a close
    above the upper band, search back for j (price at the mid band, mid at
    today's upper), k (price at the lower band; threshold = that price),
    l (price above the mid band), then forward m (price just above the lower
    band and below the threshold) -> buy. Exit when the band std < beta."""
    bands = bollinger_bands(price, window, k)
    p, mid, up, low, std = (bands[c].to_numpy() for c in ("price", "mid", "upper", "lower", "std"))
    n = len(p)
    sig = np.zeros(n, dtype=int)
    coords = [""] * n
    total = 0
    for i in range(period, n):
        moveon = False
        threshold = 0.0
        if p[i] > up[i] and total == 0:
            for j in range(i, i - period, -1):
                if abs(mid[j] - p[j]) < alpha and abs(mid[j] - up[i]) < alpha:
                    moveon = True
                    break
            if moveon:
                moveon = False
                for kk in range(j, i - period, -1):
                    if abs(low[kk] - p[kk]) < alpha:
                        threshold = p[kk]
                        moveon = True
                        break
            if moveon:
                moveon = False
                for ll in range(kk, i - period, -1):
                    if mid[ll] < p[ll]:
                        moveon = True
                        break
            if moveon:
                moveon = False
                for m in range(i, j, -1):
                    if p[m] - low[m] < alpha and p[m] > low[m] and p[m] < threshold:
                        sig[i] = 1
                        coords[i] = f"{ll},{kk},{j},{m},{i}"
                        moveon = True
                        break
        total_now = total + sig[i]
        if total_now != 0 and std[i] < beta and not moveon:
            sig[i] = -1
        total += sig[i]
    out = bands.copy()
    out["signals"], out["positions"], out["coordinates"] = sig, np.cumsum(sig), coords
    return out


# ---------------------------------------------------------------- Q10 RSI


def smma(series, n: int) -> list[float]:
    """The script's smoothed moving average: seeded with series[0], then
    (prev * (n - 1) + x) / n."""
    values = list(series)
    out = [values[0]]
    for x in values[1:]:
        out.append((out[-1] * (n - 1) + x) / n)
    return out


def rsi_script(close, n: int = 14) -> np.ndarray:
    """The script's rsi(): 100 - 100 / (1 + smma(up) / smma(down)), from the
    (n-1)-th value on -- len(close) - n values, aligned to close[n:]."""
    delta = np.diff(np.asarray(close, dtype=float))
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = np.divide(smma(up, n), smma(down, n))
        out = 100.0 - 100.0 / (1.0 + rs)
    return out[n - 1 :]


def rsi_overbought_oversold(close, n: int = 14) -> pd.DataFrame:
    """Long (1) below 30, short (-1) above 70, else flat; rows from n on."""
    c = np.asarray(close, dtype=float)
    rsi = np.zeros(c.size)
    rsi[n:] = rsi_script(c, n)
    positions = np.select([rsi < 30, rsi > 70], [1, -1], default=0)
    signals = np.diff(positions, prepend=positions[0])
    return pd.DataFrame({"rsi": rsi, "positions": positions, "signals": signals}).iloc[n:]


def rsi_head_shoulders_trades(
    close,
    lag: int = 14,
    period: int = 25,
    delta: float = 0.2,
    head: float = 1.1,
    shoulder: float = 1.1,
    exit_rsi: float = 4,
    exit_days: int = 5,
) -> pd.DataFrame:
    """RSI Pattern Recognition backtest.py's pattern_recognition, verbatim.
    The node search runs on the CLOSE (the source's df['Close']); a found
    head-and-shoulders shorts (-1); the short is covered (+1) once the RSI
    has risen more than exit_rsi from entry or after exit_days bars."""
    c = np.asarray(close, dtype=float)
    n_bars = c.size
    rsi = np.zeros(n_bars)
    rsi[lag:] = rsi_script(c, lag)
    sig = np.zeros(n_bars, dtype=int)
    coords = [""] * n_bars
    total, entry_rsi, counter = 0, 0.0, 0
    for i in range(period + lag, n_bars):
        moveon = False
        window = c[i - period : i]
        if total == 0 and c[i] != window.max():
            j = i - period + int(np.argmax(window))
            if abs(c[j] - c[i]) > head * delta:
                bottom = c[i]
                moveon = True
            if moveon:
                moveon = False
                for k in range(j, i):
                    if abs(c[k] - bottom) < delta:
                        moveon = True
                        break
            if moveon:
                moveon = False
                for ll in range(j, i - period + 1, -1):
                    if abs(c[ll] - bottom) < delta:
                        moveon = True
                        break
            if moveon:
                moveon = False
                for m in range(i - period, ll):
                    if abs(c[m] - bottom) < delta:
                        moveon = True
                        break
            if moveon:
                moveon = False
                nn = m + int(np.argmax(c[m:ll]))
                if c[nn] - bottom > shoulder * delta and c[j] - c[nn] > shoulder * delta:
                    top = c[nn]
                    moveon = True
            if moveon:
                moveon = False
                for o in range(k, i):
                    if abs(c[o] - top) < delta:
                        sig[i] = -1
                        coords[i] = f"{m},{nn},{ll},{j},{k},{o},{i}"
                        total += -1
                        entry_rsi = rsi[i]
                        moveon = True
                        break
        if entry_rsi != 0 and not moveon:
            counter += 1
            if rsi[i] - entry_rsi > exit_rsi or counter > exit_days:
                sig[i] = 1
                total += 1
                counter, entry_rsi = 0, 0.0
    return pd.DataFrame(
        {"close": c, "rsi": rsi, "signals": sig, "positions": np.cumsum(sig), "coordinates": coords}
    )


# ---------------------------------------------------------------- Q17 Shooting star


def shooting_star_conditions(
    df: pd.DataFrame, lower_bound: float = 0.2, body_size: float = 0.5, causal: bool = False
) -> pd.Series:
    """The script's eight conditions. causal=False is verbatim (full-sample
    mean body; conditions 7-8 on the NEXT bar). causal=True uses the mean
    body of bars before t and moves confirmation onto the bar that confirms,
    so the signal lands one bar later and uses nothing after its bar."""
    o, h, lo, c = (df[k].astype(float) for k in ("open", "high", "low", "close"))
    body = o - c
    mean_body = body.expanding().mean().shift(1) if causal else abs(np.mean(body))
    cond = (
        (o >= c)
        & ((c - lo) < lower_bound * abs(c - o))
        & (abs(o - c) < abs(mean_body) * body_size)
        & ((h - o) >= 2 * (o - c))
        & (c >= c.shift(1))
        & (c.shift(1) >= c.shift(2))
    )
    if not causal:
        return (cond & (h.shift(-1) <= h) & (c.shift(-1) <= c)).astype(int)
    star = cond.shift(1, fill_value=False)
    return (star & (h <= h.shift(1)) & (c <= c.shift(1))).astype(int)


def shooting_star_trades(
    df: pd.DataFrame,
    lower_bound: float = 0.2,
    body_size: float = 0.5,
    stop_threshold: float = 0.05,
    holding_period: int = 7,
    causal: bool = False,
) -> pd.DataFrame:
    """Short (-1) on a star; cover (+1) once |close / entry - 1| exceeds
    stop_threshold or after holding_period bars (the script's while loop,
    later assignments overwriting earlier ones as in the source)."""
    c = df["close"].to_numpy(float)
    sig = -shooting_star_conditions(df, lower_bound, body_size, causal).to_numpy().astype(int)
    entries = np.flatnonzero(sig == -1)
    for ind in entries:
        entry = c[ind]
        counter = 0
        while True:
            ind += 1
            counter += 1
            if ind >= c.size:
                break
            done = False
            if abs(c[ind] / entry - 1) > stop_threshold:
                done = True
                sig[ind] = 1
            if counter >= holding_period:
                done = True
                sig[ind] = 1
            if done:
                break
    return pd.DataFrame({"signals": sig, "positions": np.cumsum(sig)})


# ---------------------------------------------------------------- Q7 Dual Thrust


def dual_thrust_range(daily: pd.DataFrame, rg: int = 5, causal: bool = False) -> pd.Series:
    """max(HH - LC, HC - LL) over rg days (HH/LL highest high/lowest low,
    HC/LC highest/lowest close). Verbatim it includes the current day;
    causal=True shifts it so a session uses only completed days."""
    h, lo, c = (daily[k].astype(float) for k in ("high", "low", "close"))
    range1 = h.rolling(rg).max() - c.rolling(rg).min()
    range2 = c.rolling(rg).max() - lo.rolling(rg).min()
    rng = pd.Series(np.where(range1 > range2, range1, range2), index=daily.index)
    rng[range1.isna() | range2.isna()] = np.nan
    return rng.shift(1) if causal else rng


def dual_thrust_trades(
    prices: pd.Series,
    daily: pd.DataFrame,
    param: float = 0.5,
    rg: int = 5,
    open_at: time = time(3, 0),
    close_at: time = time(12, 0),
    causal: bool = False,
) -> pd.DataFrame:
    """Dual Thrust backtest.py's signal loop: at the session open, upper =
    open + param * range and lower = open - (1 - param) * range; long above
    upper, short below lower, a flip trades +/-2, the session close flattens.
    `prices` is intraday, indexed by timestamp; `daily` holds high/low/close
    indexed by date (normalised timestamps)."""
    if not 0 < param < 1:
        raise ConfigurationError(f"param must be in (0, 1), got {param}")
    rng = dual_thrust_range(daily, rg, causal)
    p = prices.astype(float)
    sig = np.zeros(len(p), dtype=int)
    upper_out, lower_out = np.zeros(len(p)), np.zeros(len(p))
    sigup = siglo = 0.0
    total = 0
    for i, (ts, price) in enumerate(p.items()):
        if ts.time() == open_at:
            day_range = rng.get(ts.normalize(), np.nan)
            if np.isfinite(day_range):
                sigup = param * day_range + price
                siglo = -(1 - param) * day_range + price
        if sigup != 0 and price > sigup:
            sig[i] = 1
        if siglo != 0 and price < siglo:
            sig[i] = -1
        if sig[i] != 0:
            cum = total + sig[i]
            if cum > 1 or cum < -1:
                sig[i] = 0
            if cum == 0:
                if price > sigup:
                    sig[i] = 2
                if price < siglo:
                    sig[i] = -2
        if ts.time() == close_at:
            sigup = siglo = 0.0
            # The source sets signals[i] = -cumsum[i], where cumsum[i] already
            # includes this bar's signal.
            sig[i] = -(total + sig[i])
        upper_out[i], lower_out[i] = sigup, siglo
        total += sig[i]
    return pd.DataFrame(
        {
            "price": p.to_numpy(),
            "upper": upper_out,
            "lower": lower_out,
            "signals": sig,
            "positions": np.cumsum(sig),
        },
        index=p.index,
    )


# ---------------------------------------------------------------- Q4 London Breakout


def london_breakout_trades(
    prices: pd.Series,
    range_hour: int = 2,
    open_hour: int = 3,
    open_minutes: int = 30,
    close_hour: int = 12,
    risky_stop: float = 0.01,
) -> pd.DataFrame:
    """London Breakout backtest.py: the range is every price in the hour
    before the open; in the first `open_minutes` after it, trade a break of
    the range unless it overshoots by more than risky_stop (an 'abnormal'
    break); exit at +/- risky_stop/2 from the fill or at close_hour."""
    p = prices.astype(float)
    sig = np.zeros(len(p), dtype=int)
    tokyo: list[float] = []
    upper = lower = None
    executed = 0.0
    total = 0
    for i, (ts, price) in enumerate(p.items()):
        if ts.hour == range_hour:
            tokyo.append(price)
        elif ts.hour == open_hour and ts.minute == 0:
            if tokyo:
                upper, lower = max(tokyo), min(tokyo)
            tokyo = []
        elif ts.hour == open_hour and ts.minute < open_minutes and upper is not None:
            if price - upper > 0:
                sig[i] = 1
                if price - upper > risky_stop or total + 1 > 1:
                    sig[i] = 0
                else:
                    executed = price
            if price - lower < 0:
                sig[i] = -1
                if lower - price > risky_stop or total - 1 < -1:
                    sig[i] = 0
                else:
                    executed = price
        elif ts.hour == close_hour or (
            total != 0 and (price > executed + risky_stop / 2 or price < executed - risky_stop / 2)
        ):
            sig[i] = -total
        total += sig[i]
    return pd.DataFrame(
        {"price": p.to_numpy(), "signals": sig, "positions": np.cumsum(sig)}, index=p.index
    )


# ---------------------------------------------------------------- Q2 Pair trading


def _ols(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    return beta, y - x @ beta


def eg_method(x, y) -> tuple[bool, np.ndarray, np.ndarray]:
    """The script's EG_method: (cointegrated, [const, slope], residuals).
    Step 1: OLS y on x, ADF on the residual -- the script requires
    statsmodels' adfuller p-value <= 0.05; with no statsmodels here that is
    the equivalent test, the ADF statistic below its 5% critical value
    (same default lag cap 12 * (n/100)^(1/4), chosen by AIC). Step 2: the
    error-correction regression dy on [1, dx, e_{t-1}] must have a
    non-positive coefficient on e_{t-1}."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    params, resid = _ols(y, np.column_stack([np.ones(x.size), x]))
    maxlag = int(12 * (resid.size / 100.0) ** 0.25)
    test = adf(resid, maxlag=maxlag, autolag=True)
    if not test["stat"] < test["critical_values"]["5%"]:
        return False, params, resid
    design = np.column_stack([np.ones(x.size - 1), np.diff(x), resid[:-1]])
    coef, _ = _ols(np.diff(y), design)
    return (coef[-1] <= 0), params, resid


def pair_trading_signals(asset1, asset2, bandwidth: int = 250) -> pd.DataFrame:
    """Pair trading backtest.py's signal_generation, verbatim: re-test
    cointegration on a rolling `bandwidth` window; when it switches on,
    standardise the residual by the fit's mean and std and set bands at
    z +/- std(resid); long asset1 above the upper band, short below the
    lower, asset2 the opposite leg; flatten when cointegration breaks."""
    a1, a2 = np.asarray(asset1, float), np.asarray(asset2, float)
    n = a1.size
    s1 = np.zeros(n, dtype=int)
    z = np.full(n, np.nan)
    zu, zl = np.full(n, np.nan), np.full(n, np.nan)
    prev = False
    for i in range(bandwidth, n):
        status, params, resid = eg_method(a1[i - bandwidth : i], a2[i - bandwidth : i])
        if prev and not status and s1[i - 1] != 0:
            s1[i] = 0
            z[i:] = zu[i:] = zl[i:] = np.nan
        if not prev and status:
            fitted = params[0] + params[1] * a1[i:]
            res = a2[i:] - fitted
            z[i:] = (res - np.mean(resid)) / np.std(resid)
            zu[i:] = z[i] + np.std(resid)
            zl[i:] = z[i] - np.std(resid)
        if status and z[i] > zu[i]:
            s1[i] = 1
        if status and z[i] < zl[i]:
            s1[i] = -1
        prev = status
    return pd.DataFrame(
        {
            "z": z,
            "z_upper": zu,
            "z_lower": zl,
            "signals1": s1,
            "positions1": np.diff(s1, prepend=0),
            "signals2": -s1,
        }
    )
