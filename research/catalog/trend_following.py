"""
Trend-following and breakout systems as published, shorts and price stops
included: S2 PyTrendFollow, the full Turtle trade behind C-G5, X7's
managed-futures time-series momentum, C-RJ5 Ghost Trader and C-M2's
five-minute opening range breakout. The platform keeps only fragments of
these (long-only regimes, the Turtle scale-in, the N2 breakdown gate); the
ledger says why. Index-based loops follow the sources so they can be read
side by side.

Sources:

  * S2: chrism2671/PyTrendFollow trading/rules.py (ewmac, mr, breakout_fn,
    weather_rule, buy_and_hold), core/utility.py (norm_forecast, norm_vol,
    weight_forecast, chunk_trades), core/instrument.py (position,
    return_volatility) and config/strategy.py.template (12.5% annual
    volatility target).
  * C-G5: letianzj/QuantResearch backtest/turtle.py; the original rules
    from Curtis Faith, "The Original Turtle Trading Rules" (2003).
  * X7: Moskowitz, Ooi & Pedersen, "Time Series Momentum", Journal of
    Financial Economics 104 (2012) -- the strategy DBMF/KMLM-style funds
    run.
  * C-RJ5: letianzj/QuantResearch backtest/ghost_trader.py.
  * C-M2: Zarattini & Aziz, "Can Day Trading Really Be Profitable?" (SSRN
    4416622, 2023); Zarattini, Barbon & Aziz, "A Profitable Day Trading
    Strategy for the U.S. Equity Market" (SSRN 4729284, 2024), as the
    catalog (docs/research/correction-strategies.md#m2) records them.

Source quirks preserved on purpose:

  * PyTrendFollow normalises prices and forecasts with full-sample
    statistics (its own docstrings say "WARNING: Lookahead bias"); its
    bootstrap estimate is replaced by the plain statistic it estimates.
    `causal=True` uses the expanding window the source left commented out.
  * letianzj_turtle_trades: the "10d low" exit is computed as the MAX of
    the last 10 HIGHS, so a position closes as soon as the close slips
    under the recent highest high. `textbook_exit=True` uses the 10-day
    low. Its ATR pairs each high/low with the next close
    (position_sizing.true_ranges mode='source').
  * ghost_trader: the long exit compares the close with the Donchian low
    INCLUDING the current bar, which only fires when the close is the
    bar's low and that low is the n-bar low.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.strategies.position_sizing import true_ranges

# ---------------------------------------------------------------- TA-Lib-compatible helpers


def talib_ema(values, n: int) -> np.ndarray:
    """TA-Lib's EMA: seeded with the simple mean of the first n values,
    then k = 2/(n+1); NaN before index n-1."""
    x = np.asarray(values, dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = x[:n].mean()
    k = 2.0 / (n + 1)
    for i in range(n, len(x)):
        out[i] = out[i - 1] + k * (x[i] - out[i - 1])
    return out


def talib_rsi(values, n: int) -> np.ndarray:
    """TA-Lib's RSI: Wilder smoothing seeded with the simple mean of the
    first n gains and losses; NaN before index n."""
    x = np.asarray(values, dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    d = np.diff(x)
    gain, loss = np.clip(d, 0, None), np.clip(-d, 0, None)
    ag, al = gain[:n].mean(), loss[:n].mean()

    def rsi(g: float, lo: float) -> float:
        return 0.0 if g + lo == 0 else 100.0 * g / (g + lo)

    out[n] = rsi(ag, al)
    for i in range(n, len(d)):
        ag = (ag * (n - 1) + gain[i]) / n
        al = (al * (n - 1) + loss[i]) / n
        out[i + 1] = rsi(ag, al)
    return out


# ---------------------------------------------------------------- S2 PyTrendFollow


def norm_vol(prices, causal: bool = False) -> pd.Series:
    """utility.norm_vol: prices * 10 / std(prices). The source bootstraps
    the full-sample std (lookahead); causal=True uses the commented-out
    `df.expanding(50).std()`."""
    s = pd.Series(prices, dtype=float)
    scale = s.expanding(50).std() if causal else s.dropna().std()
    return s * 10 / scale


def norm_forecast(forecast, causal: bool = False):
    """utility.norm_forecast: scale to an absolute mean of 10, clip to
    +/-20. Full-sample abs mean (lookahead) unless causal=True."""
    f = pd.DataFrame(forecast) if not isinstance(forecast, pd.Series) else forecast
    scale = f.abs().expanding(50).mean() if causal else f.abs().mean()
    return (f * 10 / scale).clip(-20, 20)


def ewmac_forecasts(prices, spans=(8, 16, 32, 64), causal: bool = False) -> pd.DataFrame:
    """rules.ewmac: on volatility-normalised prices, EWMA(span x) minus
    EWMA(span 4x), both with min_periods = 4x, for x in 8/16/32/64, each
    normalised to an absolute mean of 10 and clipped at +/-20."""
    d = norm_vol(prices, causal)
    f = pd.DataFrame(
        {
            f"ewmac{x}": d.ewm(span=x, min_periods=x * 4).mean()
            - d.ewm(span=x * 4, min_periods=x * 4).mean()
            for x in spans
        }
    )
    return norm_forecast(f, causal)


def mr_forecasts(prices, spans=(2, 4, 8, 16, 32, 64)) -> pd.DataFrame:
    """rules.mr, the source's never-profitable mean-reversion rule: the
    negated EWMAC, scaled by 10 / mean |f| and clipped at +/-20."""
    d = norm_vol(prices)
    f = pd.DataFrame(
        {
            f"mr{x}": -(
                d.ewm(span=x, min_periods=x * 4).mean()
                - d.ewm(span=x * 4, min_periods=x * 4).mean()
            )
            for x in spans
        }
    )
    return (f * 10 / f.abs().mean()).clip(-20, 20)


def breakout_forecast(prices, lookback: int, smooth: int | None = None) -> pd.Series:
    """rules.breakout_fn (Carver's breakout rule): position of the price in
    its rolling [min, max] range, (p - mid) / (max - min) in [-0.5, 0.5],
    smoothed by an EWMA of span lookback/4. Unnormalised."""
    s = pd.Series(prices, dtype=float)
    smooth = smooth or max(int(lookback / 4.0), 1)
    roll = s.rolling(lookback, min_periods=int(min(len(s), np.ceil(lookback / 2.0))))
    lo, hi = roll.min(), roll.max()
    b = (s - (hi + lo) / 2.0) / (hi - lo)
    return b.ewm(span=smooth, min_periods=int(np.ceil(smooth / 2.0))).mean()


def breakout_forecasts(prices, lookbacks=(40, 80, 160, 320)) -> pd.DataFrame:
    """rules.breakout: the four lookbacks, normalised."""
    f = pd.DataFrame({f"brk{lb}": breakout_forecast(prices, lb) for lb in lookbacks})
    return norm_forecast(f)


def weather_rule(prices) -> pd.Series:
    """rules.weather_rule: +10 after an up day, -10 after a down day,
    NaN after an unchanged one (the source's `r.ffill()` is not assigned)."""
    r = pd.Series(prices, dtype=float).diff()
    r[r == 0] = np.nan
    return np.sign(r) * 10


def weighted_forecast(forecasts: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """utility.weight_forecast: mean over rules of forecast * weight,
    renormalised and clipped at +/-20."""
    w = pd.Series(weights).reindex(forecasts.columns).fillna(0.0)
    return norm_forecast((forecasts * w).mean(axis=1)).clip(-20, 20)


def pytrendfollow_position(
    forecast,
    prices,
    capital: float = 500_000,
    annual_vol_target: float = 0.125,
    point_value: float = 1.0,
) -> pd.Series:
    """instrument.position: round(forecast * daily_vol_target * capital / 10
    / return_volatility), return_volatility = EWMA(span 36, min 36) std of
    daily price changes in money (point_value). Forecast 10 is an average
    conviction position; 20 doubles it."""
    p = pd.Series(prices, dtype=float)
    vol = (p * point_value).diff().ewm(span=36, min_periods=36).std()
    daily = annual_vol_target / np.sqrt(252)
    return np.around(pd.Series(forecast, dtype=float) * (daily * capital / 10) / vol)


def chunk_trades(positions) -> np.ndarray:
    """utility.chunk_trades: round |position| on a log scale (one decimal of
    ln), so only changes of about 10% or more trade."""
    j = np.asarray(positions, dtype=float)
    return np.around(np.exp(np.around(np.log(np.abs(j)), decimals=1)) * np.sign(j))


# ---------------------------------------------------------------- C-G5 Turtle, as published


def letianzj_turtle_trades(
    high,
    low,
    close,
    short_window: int = 10,
    long_window: int = 20,
    equity: float = 100_000.0,
    textbook_exit: bool = False,
) -> pd.DataFrame:
    """backtest/turtle.py, the whole trade (position_sizing.TurtlePyramid is
    its scale-in only). Per bar, once more than long_window bars exist:

      * ATR = mean of the 14 'source' true ranges over the last 15 bars;
      * enter int(equity * 1% / ATR) shares when the close beats the prior
        long_window-bar high and nothing is held;
      * add the same unit when close > last buy price + 0.5 ATR, up to
        four buys;
      * exit everything when the close is under `don_low` -- the max of the
        prior short_window HIGHS in the source (textbook_exit: their low) --
        or under last buy price - 2 ATR.

    Fills are at the close; equity is held fixed (the source uses the live
    net value). Returns per-bar shares and action."""
    h, lo, c = (np.asarray(v, dtype=float) for v in (high, low, close))
    n = len(c)
    shares = np.zeros(n)
    action = np.array([""] * n, dtype=object)
    held, buys, buy_price = 0.0, 0, 0.0
    for t in range(n):
        if t + 1 <= long_window or t < 14:
            continue
        don_high = h[t - long_window : t].max()
        win = slice(t - short_window, t)
        don_low = lo[win].min() if textbook_exit else h[win].max()
        atr = float(np.mean(true_ranges(h[t - 14 : t + 1], lo[t - 14 : t + 1], c[t - 14 : t + 1])))
        unit = int(equity * 0.01 / atr) if atr > 0 else 0
        if c[t] > don_high and buys == 0:
            held, buys, buy_price, action[t] = unit, 1, c[t], "enter"
        elif c[t] > buy_price + 0.5 * atr and 0 < buys <= 3:
            held, buys, buy_price, action[t] = held + unit, buys + 1, c[t], "add"
        elif c[t] < don_low and buys > 0:
            held, buys, action[t] = 0.0, 0, "exit"
        elif c[t] < buy_price - 2 * atr and buys > 0:
            held, buys, action[t] = 0.0, 0, "stop"
        shares[t] = held
    return pd.DataFrame({"shares": shares, "action": action})


@dataclass
class TurtleTrade:
    direction: int
    entry_bar: int
    fills: list[float] = field(default_factory=list)
    stop: float = 0.0
    exit_bar: int | None = None
    exit_price: float | None = None
    reason: str = ""

    @property
    def pnl_per_unit(self) -> float:
        return sum(self.direction * (self.exit_price - f) for f in self.fills)


def turtle_n(high, low, close, period: int = 20) -> np.ndarray:
    """Faith's N: N = (19 * N_prev + TR) / 20, seeded with the mean of the
    first 20 Wilder true ranges; NaN until then (index 0 has no TR)."""
    tr = true_ranges(high, low, close, mode="wilder")  # tr[k] belongs to bar k+1
    out = np.full(len(tr) + 1, np.nan)
    if len(tr) < period:
        return out
    out[period] = tr[:period].mean()
    for i in range(period, len(tr)):
        out[i + 1] = ((period - 1) * out[i] + tr[i]) / period
    return out


def turtle_original_trades(
    high, low, close, system: int = 1, max_units: int = 4, open_=None
) -> list[TurtleTrade]:
    """The Original Turtle Trading Rules, long and short, one market:

      * System 1: enter on a break of the prior 20-day high/low, exit on a
        break of the prior 10-day low/high; skip the entry if the last
        System-1 breakout (taken or not) was a winner, unless it is also a
        55-day breakout (the failsafe). System 2: 55-day entry, 20-day
        exit, no filter.
      * Pyramid one unit at each further 1/2 N from the last fill (N frozen
        at entry), up to max_units.
      * Stop 2N from the most recent fill, applied to all units.

    Breakouts and stops are intraday (high/low) and fill at the trigger
    level, or at the open when the bar gaps through it. Unit size (1% of
    equity per N) is position_sizing.turtle_unit_shares; here everything is
    in units."""
    h, lo, c = (np.asarray(v, dtype=float) for v in (high, low, close))
    o = np.asarray(open_, dtype=float) if open_ is not None else None
    entry_len, exit_len = {1: (20, 10), 2: (55, 20)}.get(system, (None, None))
    if entry_len is None:
        raise ConfigurationError(f"system must be 1 or 2, got {system}")
    n_arr = turtle_n(h, lo, c)
    trades: list[TurtleTrade] = []
    shadow: TurtleTrade | None = None  # System 1's every-breakout record
    last_breakout_won = False
    pos: TurtleTrade | None = None
    n_entry = 0.0

    def fill(t: int, level: float, direction: int) -> float:
        if o is None:
            return level
        return max(level, o[t]) if direction > 0 else min(level, o[t])

    def exit_hit(tr: TurtleTrade, t: int) -> tuple[float, str] | None:
        stop_hit = lo[t] <= tr.stop if tr.direction > 0 else h[t] >= tr.stop
        if stop_hit:
            return fill(t, tr.stop, -tr.direction), "stop"
        if tr.direction > 0 and lo[t] < lo[t - exit_len : t].min():
            return fill(t, lo[t - exit_len : t].min(), -1), "exit"
        if tr.direction < 0 and h[t] > h[t - exit_len : t].max():
            return fill(t, h[t - exit_len : t].max(), 1), "exit"
        return None

    for t in range(max(entry_len, 21), len(c)):
        n_t = n_arr[t - 1]
        if not n_t > 0:
            continue
        hi_e, lo_e = h[t - entry_len : t].max(), lo[t - entry_len : t].min()
        hi_55, lo_55 = h[max(0, t - 55) : t].max(), lo[max(0, t - 55) : t].min()
        if system == 1 and shadow is not None:
            hit = exit_hit(shadow, t)
            if hit:
                shadow.exit_price, shadow.reason = hit
                last_breakout_won = shadow.pnl_per_unit > 0
                shadow = None
        if pos is not None:
            hit = exit_hit(pos, t)
            if hit:
                pos.exit_bar, (pos.exit_price, pos.reason) = t, hit
                trades.append(pos)
                pos = None
                continue
            nxt = pos.fills[-1] + pos.direction * 0.5 * n_entry
            crossed = h[t] >= nxt if pos.direction > 0 else lo[t] <= nxt
            if len(pos.fills) < max_units and crossed:
                pos.fills.append(fill(t, nxt, pos.direction))
                pos.stop = pos.fills[-1] - pos.direction * 2 * n_entry
            continue
        direction = 1 if h[t] > hi_e else -1 if lo[t] < lo_e else 0
        if not direction:
            continue
        level = hi_e if direction > 0 else lo_e
        if system == 1 and shadow is None:
            px = fill(t, level, direction)
            shadow = TurtleTrade(direction, t, [px], px - direction * 2 * n_t)
        failsafe = h[t] > hi_55 if direction > 0 else lo[t] < lo_55
        if system == 1 and last_breakout_won and not failsafe:
            continue
        if system == 1 and last_breakout_won and failsafe:
            level = hi_55 if direction > 0 else lo_55
        n_entry = n_t
        px = fill(t, level, direction)
        pos = TurtleTrade(direction, t, [px], px - direction * 2 * n_entry)
    if pos is not None:
        trades.append(pos)
    return trades


# ---------------------------------------------------------------- X7 time-series momentum


def tsmom_weights(
    daily_returns: pd.DataFrame,
    lookback: int = 252,
    vol_target: float = 0.40,
    com: float = 60.0,
    annualize: int = 261,
) -> pd.DataFrame:
    """Moskowitz-Ooi-Pedersen time-series momentum: in each instrument go
    long if its own past-`lookback` return is positive, short if negative,
    at weight vol_target / sigma, sigma the ex-ante annualised volatility --
    an exponentially weighted variance of daily returns about their
    exponentially weighted mean, centre of mass `com` days (delta/(1-delta)
    = 60), times 261. Both inputs use data through t-1, so the weight
    applies to day t's return. The paper rebalances monthly and averages
    across instruments; this returns the daily weight matrix."""
    r = pd.DataFrame(daily_returns, dtype=float)
    past = (1 + r).rolling(lookback).apply(np.prod, raw=True) - 1
    delta = com / (1 + com)
    mean = r.ewm(alpha=1 - delta, adjust=False).mean()
    var = ((r - mean) ** 2).ewm(alpha=1 - delta, adjust=False).mean()
    sigma = np.sqrt(var * annualize)
    return (np.sign(past) * vol_target / sigma).shift(1)


# ---------------------------------------------------------------- C-RJ5 Ghost Trader


def ghost_trader(
    high,
    low,
    close,
    ma_short: int = 3,
    ma_long: int = 21,
    rsi_n: int = 9,
    rsi_oversold: float = 30,
    rsi_overbought: float = 70,
    donchian_n: int = 21,
) -> pd.DataFrame:
    """backtest/ghost_trader.py. "If last trade is profitable, next trade
    would more likely be a loss", so a ghost takes each signal first and
    the real trade follows only once the ghost is under water:

      * long signal: flat, EMA(3) > EMA(21), RSI(9) < 70, and a higher
        high. The first signal arms a ghost long at the close; a later
        long-signal bar whose close is below the ghost price disarms it
        and goes long with all capital;
      * short signal mirrored (EMA(3) < EMA(21), RSI > 30, lower low, real
        short once the close is above the ghost short price);
      * exit long when the close <= min of the last donchian_n lows
        (current bar included); exit short when the high >= max of the
        last donchian_n highs.

    EMA and RSI are TA-Lib's. Returns per-bar position (+1/-1/0)."""
    h, lo, c = (np.asarray(v, dtype=float) for v in (high, low, close))
    ema_s, ema_l, rsi = talib_ema(c, ma_short), talib_ema(c, ma_long), talib_rsi(c, rsi_n)
    lookback = max(ma_long, rsi_n, donchian_n)
    position = np.zeros(len(c), dtype=int)
    pos = 0
    long_ghost, long_px, short_ghost, short_px = False, 0.0, False, 0.0
    for t in range(len(c)):
        size = pos
        if t + 1 >= lookback:
            long_stop = lo[t - donchian_n + 1 : t + 1].min()
            short_stop = h[t - donchian_n + 1 : t + 1].max()
            if size == 0 and ema_s[t] > ema_l[t] and rsi[t] < rsi_overbought and h[t] > h[t - 1]:
                if not long_ghost:
                    long_px, long_ghost = c[t], True
                if long_ghost and long_px > c[t]:
                    long_ghost, pos = False, 1
            elif size > 0 and c[t] <= long_stop:
                pos = 0
            if size == 0 and ema_s[t] < ema_l[t] and rsi[t] > rsi_oversold and lo[t] < lo[t - 1]:
                if not short_ghost:
                    short_px, short_ghost = c[t], True
                if short_ghost and short_px < c[t]:
                    short_ghost, pos = False, -1
            elif size < 0 and h[t] >= short_stop:
                pos = 0
        position[t] = pos
    return pd.DataFrame({"ema_short": ema_s, "ema_long": ema_l, "rsi": rsi, "position": position})


# ---------------------------------------------------------------- C-M2 opening range breakout


def orb_trade(
    session: pd.DataFrame,
    equity: float,
    or_bars: int = 1,
    stop_mode: str = "range",
    atr14: float | None = None,
    atr_fraction: float = 0.05,
    target_r: float | None = 10.0,
    risk: float = 0.01,
    max_leverage: float = 4.0,
) -> dict | None:
    """Zarattini & Aziz's opening range breakout on one session of bars
    (open/high/low/close columns, in time order; or_bars of them make the
    opening range -- one 5-minute bar in the papers):

      * direction from the opening-range candle: long if it closed up,
        short if down, no trade on a doji;
      * enter at the open of the next bar;
      * stop at the opening range's low (long) / high (short) -- the 2023
        QQQ paper -- or, stop_mode='atr', atr_fraction of the 14-day ATR
        from entry (5% in the catalog's TQQQ variant, 10% in the 2024
        Stocks-in-Play paper);
      * target target_r times the risk (10R in 2023; None = no target, as
        in 2024); otherwise out at the session close;
      * shares = min(equity * risk / R, max_leverage * equity / entry).

    A bar that touches both the stop and the target is booked at the stop.
    Returns the trade, or None when no trade is taken."""
    df = session.reset_index(drop=True)
    if len(df) <= or_bars:
        raise ConfigurationError("the session needs bars after the opening range")
    o_open, o_close = df["open"].iloc[0], df["close"].iloc[or_bars - 1]
    if o_close == o_open:
        return None
    side = 1 if o_close > o_open else -1
    entry = float(df["open"].iloc[or_bars])
    if stop_mode == "range":
        stop = float(
            df["low"].iloc[:or_bars].min() if side > 0 else df["high"].iloc[:or_bars].max()
        )
    elif stop_mode == "atr":
        if not atr14 or atr14 <= 0:
            raise ConfigurationError("stop_mode='atr' needs a positive atr14")
        stop = entry - side * atr_fraction * atr14
    else:
        raise ConfigurationError(f"stop_mode must be 'range' or 'atr', got {stop_mode!r}")
    r = side * (entry - stop)
    if r <= 0:
        return None  # entry already through the stop
    shares = int(min(equity * risk / r, max_leverage * equity / entry))
    target = entry + side * target_r * r if target_r else None
    exit_px, reason, exit_bar = float(df["close"].iloc[-1]), "close", len(df) - 1
    for t in range(or_bars, len(df)):
        bar = df.iloc[t]
        if (side > 0 and bar["low"] <= stop) or (side < 0 and bar["high"] >= stop):
            gap = bar["open"] if t > or_bars and side * (bar["open"] - stop) < 0 else stop
            exit_px, reason, exit_bar = float(gap), "stop", t
            break
        if target is not None and (
            (side > 0 and bar["high"] >= target) or (side < 0 and bar["low"] <= target)
        ):
            exit_px, reason, exit_bar = float(target), "target", t
            break
    return {
        "side": side,
        "entry": entry,
        "stop": stop,
        "target": target,
        "shares": shares,
        "exit": exit_px,
        "exit_bar": exit_bar,
        "reason": reason,
        "pnl": side * shares * (exit_px - entry),
    }


def stocks_in_play(candidates: pd.DataFrame, top: int = 20) -> pd.DataFrame:
    """The 2024 paper's universe filter: price > $5, 14-day average volume
    >= 1M shares, 14-day ATR > $0.50, opening-range relative volume
    (opening volume / its 14-day average) >= 100%; keep the `top` highest
    relative-volume names. Columns: price, adv14, atr14, opening_volume,
    avg_opening_volume14."""
    df = candidates.copy()
    df["relative_volume"] = df["opening_volume"] / df["avg_opening_volume14"]
    keep = (
        (df["price"] > 5)
        & (df["adv14"] >= 1_000_000)
        & (df["atr14"] > 0.5)
        & (df["relative_volume"] >= 1.0)
    )
    return df[keep].sort_values("relative_volume", ascending=False).head(top)
