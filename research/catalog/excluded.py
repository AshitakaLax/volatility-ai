"""
Strategies the ledger EXCLUDES by constraint or evidence -- short legs,
inverse and volatility ETFs, ruin-prone sizing, authorised-participant
access -- implemented so the database records what each one does.

  * A6 / C-MR8  jamesmawm/High-Frequency-Trading-Model-with-IB,
                models/hft_model_1.py: beta = mean(A) / mean(B) and
                volatility ratio = std(%chg A) / std(%chg B) over a trailing
                hour of 30-second mids; long the A-B spread on uptrend +
                'oversold', short on downtrend + 'overbought', flatten on
                the opposite signal. Plus the catalog's long-only form.
  * X5          long Treasuries as the hedge: a periodically rebalanced
                stock/bond mix (the classic 60/40 is the default weight).
  * X6 / V20    the inverse-ETF regime sleeve: hold a daily-reset inverse
                ETF while the regime is off; `daily_reset_path` shows the
                compounding drag the ledger's V20 losses reflect.
  * X8          the long-volatility sleeve: hold VIXY while a stress trigger
                (e.g. VIX/VIX3M backwardation) is on, with hysteresis.
  * C-RJ3       binary martingale sizing (awesome-quant's binary-martingale):
                double the stake after each loss, reset after a win, and the
                exact probability that a losing streak exhausts capital.
  * C-RJ6       ETF creation/redemption arbitrage: an authorised participant
                creates units when the ETF trades above NAV by more than the
                creation costs, redeems when below (the mechanism as the
                SEC and ICI describe it).

Source quirk preserved: in hft_model_1 `is_overbought` is "A cheaper than
beta x B" and `is_oversold` "A dearer" -- the labels are swapped relative
to their comments' intent, so the BUY signal (uptrend and 'oversold') buys
the spread when A is RICH. `fixed_labels=True` swaps them back.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- A6 IB HFT pairs


def ib_hft_signals(mid_a, mid_b, window: int = 120, fixed_labels: bool = False) -> pd.DataFrame:
    """hft_model_1 on regular bars (the source resamples ticks to 30 s and
    keeps one hour: window=120). At each bar, from the trailing window:
    beta = mean(A) / mean(B), vr = std(pct A) / std(pct B); buy = vr > 1 and
    'oversold', sell = vr < 1 and 'overbought'. Spread position (+1 long A /
    short B): flat -> -1 on sell, flat -> +1 on buy, -1 -> 0 on buy,
    +1 -> 0 on sell (checked in that order). The source refreshes beta and
    vr on a timer; here every bar."""
    a, b = pd.Series(mid_a, dtype=float), pd.Series(mid_b, dtype=float)
    if len(a) != len(b):
        raise ConfigurationError("mid_a and mid_b must align")
    beta = a.rolling(window).mean() / b.rolling(window).mean()
    vr = a.pct_change().rolling(window - 1).std() / b.pct_change().rolling(window - 1).std()
    expected = beta * b
    cheap, rich = a < expected, a > expected
    overbought, oversold = (rich, cheap) if fixed_labels else (cheap, rich)
    buy = (vr > 1) & oversold
    sell = (vr < 1) & overbought
    pos, out = 0, np.zeros(len(a), dtype=int)
    for t in range(len(a)):
        if pos == 0 and sell.iloc[t]:
            pos = -1
        elif pos == 0 and buy.iloc[t]:
            pos = 1
        elif (pos == -1 and buy.iloc[t]) or (pos == 1 and sell.iloc[t]):
            pos = 0
        out[t] = pos
    return pd.DataFrame({"beta": beta, "vol_ratio": vr, "buy": buy, "sell": sell, "position": out})


def ib_pairs_long_only(mid_a, mid_b, window: int = 120) -> pd.Series:
    """The catalog's long-only reading (C-MR8): hold A only while it is
    cheap to beta x B; no short leg."""
    a, b = pd.Series(mid_a, dtype=float), pd.Series(mid_b, dtype=float)
    beta = a.rolling(window).mean() / b.rolling(window).mean()
    return (a < beta * b).astype(int)


# ---------------------------------------------------------------- X5 stock/bond mix


def rebalanced_mix(
    returns_a, returns_b, weight_a: float = 0.6, rebalance_every: int = 21
) -> pd.Series:
    """Value of a two-asset mix reset to weight_a / (1 - weight_a) every
    `rebalance_every` periods, drifting in between."""
    ra, rb = np.asarray(returns_a, dtype=float), np.asarray(returns_b, dtype=float)
    va, vb, values = weight_a, 1 - weight_a, []
    for t, (x, y) in enumerate(zip(ra, rb, strict=True)):
        if t and t % rebalance_every == 0:
            total = va + vb
            va, vb = total * weight_a, total * (1 - weight_a)
        va, vb = va * (1 + x), vb * (1 + y)
        values.append(va + vb)
    return pd.Series(values)


# ---------------------------------------------------------------- X6 / X8 sleeves


def daily_reset_path(returns, leverage: float) -> np.ndarray:
    """A daily-reset leveraged/inverse ETF: value_t = prod(1 + L r_t). Over a
    round trip of the underlying the product is below 1 for |L| > 0 when
    returns vary (volatility drag), which is what sank the V20 SQQQ grid."""
    return np.cumprod(1 + leverage * np.asarray(returns, dtype=float))


def regime_sleeve_returns(risk_on, on_returns, off_returns) -> pd.Series:
    """X6's sleeve: the risk-on asset while the (already lagged) regime is
    on, the off asset -- an inverse ETF -- while it is off."""
    flag = pd.Series(risk_on, dtype=float).fillna(1.0).to_numpy()
    on, off = np.asarray(on_returns, dtype=float), np.asarray(off_returns, dtype=float)
    return pd.Series(np.where(flag > 0, on, off))


def hysteresis_switch(signal, enter: float, exit: float) -> np.ndarray:
    """1 from the first bar signal >= enter until signal < exit."""
    if exit > enter:
        raise ConfigurationError("exit must not exceed enter")
    on, out = False, []
    for s in np.asarray(signal, dtype=float):
        on = s >= enter if not on else s >= exit
        out.append(int(on))
    return np.array(out)


def long_vol_sleeve(trigger, vol_etf_returns, enter: float = 1.0, exit: float = 0.95, lag: int = 1):
    """X8: hold the long-volatility ETF (VIXY) while the trigger -- e.g. the
    VIX/VIX3M ratio -- is in stress, decided on the prior bar; cash
    otherwise."""
    held = np.r_[np.zeros(lag, dtype=int), hysteresis_switch(trigger, enter, exit)[:-lag]]
    return pd.Series(held * np.asarray(vol_etf_returns, dtype=float)), held


# ---------------------------------------------------------------- C-RJ3 martingale


def martingale_path(
    outcomes, capital: float, base: float = 1.0, factor: float = 2.0
) -> pd.DataFrame:
    """Even-money bets: stake base, multiply by `factor` after each loss,
    reset to base after a win; stop (ruined) when the next stake exceeds
    capital. outcomes are 1 win / 0 loss."""
    stake, cap, rows = base, capital, []
    for o in outcomes:
        if stake > cap:
            rows.append((cap, stake, "ruined"))
            break
        cap += stake if o else -stake
        rows.append((cap, stake, "win" if o else "loss"))
        stake = base if o else stake * factor
    return pd.DataFrame(rows, columns=["capital", "stake", "result"])


def martingale_ruin_probability(p_win: float, n_bets: int, streak: int) -> float:
    """Probability that n_bets independent bets contain a run of `streak`
    consecutive losses -- for a doubling martingale with capital
    base * (2^streak - 1), the chance of ruin within n_bets (wins along the
    way add to capital, so this is the ruin chance of the initial stake
    ladder). Exact, by dynamic programming over the current loss run."""
    q = 1 - p_win
    state = np.zeros(streak)  # probability of a current run of k losses, no ruin yet
    state[0] = 1.0
    ruined = 0.0
    for _ in range(n_bets):
        nxt = np.zeros(streak)
        nxt[0] = state.sum() * p_win
        nxt[1:] = state[:-1] * q
        ruined += state[-1] * q
        state = nxt
    return float(ruined)


# ---------------------------------------------------------------- C-RJ6 creation/redemption


def creation_redemption_action(
    etf_price: float,
    nav: float,
    unit_shares: int = 50_000,
    fixed_fee: float = 500.0,
    variable_cost: float = 0.0005,
) -> dict:
    """An authorised participant's choice for one creation unit: create
    (deliver the basket at NAV, receive and sell ETF shares) when the
    premium covers the fixed creation fee and variable trading costs;
    redeem (buy ETF shares, return them for the basket) on a discount that
    covers them; else nothing."""
    gross = (etf_price - nav) * unit_shares
    costs = fixed_fee + variable_cost * nav * unit_shares
    if gross > costs:
        return {"action": "create", "profit": gross - costs, "premium": etf_price / nav - 1}
    if -gross > costs:
        return {"action": "redeem", "profit": -gross - costs, "premium": etf_price / nav - 1}
    return {"action": "none", "profit": 0.0, "premium": etf_price / nav - 1}
