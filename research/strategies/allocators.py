"""
Long-only multi-asset allocators for the ranked list's portfolio entries
(ledger RK7, RK10, RK18, RK19, RK52, RK61, RK99, RK117, RK129, RK132,
RK144, RK215, RK269), run by research/strategies/portfolio_book.py.

Every allocator is a pure function of a history of daily closes (rows =
completed sessions, oldest first; columns = instruments) and returns
target weights: a pd.Series over the columns, each >= 0, summing to at
most 1 (the rest is cash). The CALLER passes only sessions before the one
it trades on; nothing here looks at a row it was not given.

Nothing here trades live. The engine runs one symbol per deployment, so
these are backtest books until a multi-asset deployment exists (engine/
roadmap.md). UNMEASURED: none of these has been run on real data.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.strategies.mean_reversion import decayed_reversal_scores
from research.strategies.position_sizing import split_conformal_interval

Allocator = Callable[..., pd.Series]

SECTOR_ETFS: tuple[str, ...] = (
    "XLB",
    "XLC",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLRE",
    "XLU",
    "XLV",
    "XLY",
)


def _returns(closes: pd.DataFrame, window: int | None = None) -> pd.DataFrame:
    rets = closes.pct_change().iloc[1:]
    return rets if window is None else rets.iloc[-window:]


def _need(closes: pd.DataFrame, rows: int, what: str) -> None:
    if len(closes) < rows:
        raise ConfigurationError(f"{what} needs {rows} sessions of history, got {len(closes)}")


def _top_k(scores: pd.Series, k: int) -> pd.Series:
    """Equal weight on the k highest finite scores."""
    scores = scores.dropna()
    if not (isinstance(k, int) and k >= 1):
        raise ConfigurationError(f"k must be an integer >= 1, got {k!r}")
    chosen = scores.sort_values(ascending=False).index[:k]
    w = pd.Series(0.0, index=scores.index)
    if len(chosen):
        w[chosen] = 1.0 / len(chosen)
    return w


def _full(weights: pd.Series, columns) -> pd.Series:
    return weights.reindex(columns).fillna(0.0).astype(float)


# ---------------------------------------------------------------- RK117


def equal_weight(closes: pd.DataFrame) -> pd.Series:
    """RK117: 1/N on every instrument (DeMiguel, Garlappi & Uppal 2009's
    hard-to-beat benchmark)."""
    n = closes.shape[1]
    return pd.Series(1.0 / n, index=closes.columns)


# ---------------------------------------------------------------- RK129


def inverse_volatility(closes: pd.DataFrame, lookback: int = 63) -> pd.Series:
    """RK129: w_i proportional to 1 / sigma_i of the last `lookback` daily
    returns."""
    _need(closes, lookback + 1, "inverse_volatility")
    vol = _returns(closes, lookback).std()
    if (vol <= 0).any():
        raise ConfigurationError("every instrument needs a positive volatility")
    inv = 1.0 / vol
    return inv / inv.sum()


# ---------------------------------------------------------------- RK61


def erc_weights(
    cov: np.ndarray, budgets=None, tol: float = 1e-10, iters: int = 10_000
) -> np.ndarray:
    """Equal (or budgeted) risk contributions, Maillard, Roncalli &
    Teiletche (2010), by Griveau-Billion et al.'s cyclical coordinate
    descent on Spinu's convex form min 1/2 y'Sy - sum b_i log y_i; the
    weights are y / sum(y). Each instrument's contribution w_i (Sw)_i
    then equals b_i times the portfolio variance."""
    cov = np.asarray(cov, dtype=float)
    n = cov.shape[0]
    b = np.full(n, 1.0 / n) if budgets is None else np.asarray(budgets, dtype=float)
    if np.any(np.diag(cov) <= 0) or np.any(b <= 0):
        raise ConfigurationError("ERC needs positive variances and positive budgets")
    b = b / b.sum()
    y = 1.0 / np.sqrt(np.diag(cov))
    for _ in range(iters):
        prev = y.copy()
        for i in range(n):
            rest = cov[i] @ y - cov[i, i] * y[i]
            y[i] = (-rest + np.sqrt(rest * rest + 4.0 * cov[i, i] * b[i])) / (2.0 * cov[i, i])
        if np.max(np.abs(y - prev)) < tol * np.max(y):
            break
    return y / y.sum()


def risk_contributions(weights, cov) -> np.ndarray:
    """Each instrument's share of portfolio variance."""
    w = np.asarray(weights, dtype=float)
    cov = np.asarray(cov, dtype=float)
    rc = w * (cov @ w)
    return rc / rc.sum()


def equal_risk_contribution(closes: pd.DataFrame, lookback: int = 252) -> pd.Series:
    """RK61: ERC on the sample covariance of the last `lookback` returns."""
    _need(closes, lookback + 1, "equal_risk_contribution")
    rets = _returns(closes, lookback)
    return pd.Series(erc_weights(rets.cov().to_numpy()), index=closes.columns)


# ---------------------------------------------------------------- RK99


def conformal_risk_parity(
    closes: pd.DataFrame,
    lookback: int = 252,
    alpha: float = 0.05,
    max_daily_loss: float = 0.02,
) -> pd.Series:
    """RK99: ERC weights, scaled so the split-conformal (1 - alpha) bound on
    the ERC portfolio's absolute daily return stays within `max_daily_loss`.
    The calibration residuals are the ERC portfolio's own returns over the
    lookback (a zero forecast), so exposure = min(1, max_daily_loss / q)."""
    w = equal_risk_contribution(closes, lookback)
    port = _returns(closes, lookback).to_numpy() @ w.to_numpy()
    _, high = split_conformal_interval(0.0, port, alpha)
    exposure = 1.0 if high <= 0 else min(1.0, max_daily_loss / high)
    return w * exposure


# ---------------------------------------------------------------- RK132


def conformal_allocation(
    closes: pd.DataFrame,
    horizon: int = 21,
    calibration: int = 250,
    alpha: float = 0.2,
    vol_lookback: int = 63,
) -> pd.Series:
    """RK132: per instrument, forecast the next `horizon`-session return
    by the last one (time-series momentum) and calibrate on that
    forecast's own past errors; an instrument is held only when the
    split-conformal (1 - alpha) interval lies wholly above zero. Held
    instruments are inverse-volatility weighted; nothing qualifying
    leaves the book in cash."""
    _need(closes, calibration + 2 * horizon + 1, "conformal_allocation")
    logc = np.log(closes)
    fwd = logc.shift(-horizon) - logc  # realised forward return at t
    past = logc - logc.shift(horizon)  # forecast at t
    held = {}
    vol = _returns(closes, vol_lookback).std()
    for name in closes.columns:
        pairs = pd.concat([past[name], fwd[name]], axis=1).dropna().iloc[-calibration:]
        if len(pairs) < 20:
            continue
        residuals = (pairs.iloc[:, 1] - pairs.iloc[:, 0]).to_numpy()
        low, _ = split_conformal_interval(float(past[name].iloc[-1]), residuals, alpha)
        if low > 0 and vol[name] > 0:
            held[name] = 1.0 / vol[name]
    if not held:
        return pd.Series(0.0, index=closes.columns)
    w = pd.Series(held)
    return _full(w / w.sum(), closes.columns)


# ---------------------------------------------------------------- RK7 / RK19


def cross_sectional_momentum(
    closes: pd.DataFrame, lookback: int = 252, skip: int = 21, k: int = 3
) -> pd.Series:
    """RK7 (and RK19 on a sector-ETF universe, SECTOR_ETFS): rank by the
    return from `lookback` to `skip` sessions ago (Jegadeesh & Titman's
    12-1 month; Moskowitz & Grinblatt for industries) and hold the top k
    equally. Long-only: the short leg is dropped."""
    _need(closes, lookback + 1, "cross_sectional_momentum")
    if not 0 <= skip < lookback:
        raise ConfigurationError("need 0 <= skip < lookback")
    score = closes.iloc[-1 - skip] / closes.iloc[-1 - lookback] - 1.0
    return _full(_top_k(score, k), closes.columns)


# ---------------------------------------------------------------- RK10


def state_filtered_momentum(
    closes: pd.DataFrame,
    market: str,
    state_lookback: int = 756,
    lookback: int = 252,
    skip: int = 21,
    k: int = 3,
) -> pd.Series:
    """RK10, Cooper, Gutierrez & Hameed (2004): momentum pays after UP
    markets and fails after down ones. Cross-sectional momentum over every
    column but `market` while the market's return over `state_lookback`
    sessions (36 months) is positive; cash otherwise."""
    if market not in closes.columns:
        raise ConfigurationError(f"market column {market!r} not in the universe")
    _need(closes, state_lookback + 1, "state_filtered_momentum")
    state = closes[market].iloc[-1] / closes[market].iloc[-1 - state_lookback] - 1.0
    if state <= 0:
        return pd.Series(0.0, index=closes.columns)
    others = closes.drop(columns=[market])
    return _full(cross_sectional_momentum(others, lookback, skip, k), closes.columns)


# ---------------------------------------------------------------- RK18


def low_volatility(closes: pd.DataFrame, lookback: int = 252, k: int = 3) -> pd.Series:
    """RK18, the low-volatility anomaly (Ang et al. 2006; Blitz & van
    Vliet 2007): hold the k instruments with the lowest volatility of the
    last `lookback` daily returns, equally."""
    _need(closes, lookback + 1, "low_volatility")
    vol = _returns(closes, lookback).std()
    return _full(_top_k(-vol, k), closes.columns)


# ---------------------------------------------------------------- RK52


def trailing_yield(closes: pd.DataFrame, dividends: pd.DataFrame, window: int = 252) -> pd.Series:
    """Trailing dividend yield at the last row: dividends with an ex-date
    in the last `window` sessions of `closes` (strictly up to its last
    session), divided by the last close. `dividends` has columns ticker,
    ex_date, amount."""
    if closes.empty:
        raise ConfigurationError("no closes")
    start, end = closes.index[max(0, len(closes) - window)], closes.index[-1]
    d = dividends.copy()
    d["ex_date"] = pd.to_datetime(d["ex_date"])
    idx = closes.index
    tz = getattr(idx, "tz", None)
    if tz is not None and d["ex_date"].dt.tz is None:
        d["ex_date"] = d["ex_date"].dt.tz_localize(tz)
    inside = d[(d["ex_date"] > start) & (d["ex_date"] <= end)]
    paid = inside.groupby("ticker")["amount"].sum()
    return (paid.reindex(closes.columns).fillna(0.0) / closes.iloc[-1]).astype(float)


def dividend_yield(
    closes: pd.DataFrame,
    dividends: pd.DataFrame,
    k: int = 3,
    window: int = 252,
    require_growth: bool = False,
) -> pd.Series:
    """RK52: hold the k highest trailing-yield instruments equally.
    require_growth keeps only those whose dividends over the last year
    exceed the year before's (the dividend-growth variant)."""
    _need(closes, window + 1, "dividend_yield")
    y = trailing_yield(closes, dividends, window)
    y = y[y > 0]
    if require_growth and len(closes) >= 2 * window + 1:
        before = trailing_yield(closes.iloc[:-window], dividends, window)
        paid_now = y * closes.iloc[-1].reindex(y.index)
        paid_then = before.reindex(y.index) * closes.iloc[-1 - window].reindex(y.index)
        y = y[paid_now > paid_then]
    if y.empty:
        return pd.Series(0.0, index=closes.columns)
    return _full(_top_k(y, k), closes.columns)


# ---------------------------------------------------------------- RK144


def _signal_panel(closes: pd.DataFrame) -> dict[str, pd.DataFrame]:
    logc = np.log(closes)
    return {
        "mom20": logc - logc.shift(20),
        "mom60": logc - logc.shift(60),
        "rev5": -(logc - logc.shift(5)),
        "trend": (closes / closes.rolling(50).mean()) - 1.0,
    }


def alpha_stacking(
    closes: pd.DataFrame,
    horizon: int = 21,
    train: int = 750,
    vol_lookback: int = 63,
    max_gross: float = 1.0,
) -> pd.Series:
    """RK144, stacked generalisation (Wolpert 1992) over four base signals
    (20- and 60-session momentum, 5-session reversal, distance from the
    50-session mean). The meta-model is a pooled least-squares fit of the
    forward `horizon`-session return on the signals over the last `train`
    sessions whose forward return is already known (so it never reaches
    past the last row). Its forecasts set long-only weights proportional
    to forecast / variance (a diagonal mean-variance optimiser), capped at
    `max_gross` total; no positive forecast is all cash."""
    _need(closes, 60 + horizon + 50, "alpha_stacking")
    panel = _signal_panel(closes)
    logc = np.log(closes)
    fwd = (logc.shift(-horizon) - logc).iloc[:-horizon].iloc[-train:]
    rows = fwd.index
    x = np.column_stack([panel[k].loc[rows].to_numpy().ravel() for k in panel])
    y = fwd.to_numpy().ravel()
    ok = np.isfinite(x).all(axis=1) & np.isfinite(y)
    if ok.sum() < 30:
        return pd.Series(0.0, index=closes.columns)
    design = np.column_stack([np.ones(ok.sum()), x[ok]])
    coef, *_ = np.linalg.lstsq(design, y[ok], rcond=None)
    latest = np.column_stack([panel[k].iloc[-1].to_numpy() for k in panel])
    forecast = pd.Series(coef[0] + latest @ coef[1:], index=closes.columns)
    var = _returns(closes, vol_lookback).var() * horizon
    raw = (forecast.clip(lower=0.0) / var.where(var > 0)).fillna(0.0)
    if raw.sum() <= 0:
        return pd.Series(0.0, index=closes.columns)
    return raw / raw.sum() * max_gross


# ---------------------------------------------------------------- RK215


def risk_neutral_reversal(
    closes: pd.DataFrame,
    beta_lookback: int = 126,
    formation: int = 5,
    half_life: float = 2.4,
    vol_lookback: int = 63,
    k: int = 3,
) -> pd.Series:
    """RK215, short-term reversal with risk neutralisation (Blitz, Huij,
    Lansdorp & Verbeek 2013's residual reversal): each instrument's daily
    returns are residualised on the equal-weight market return with a
    beta from the last `beta_lookback` sessions, scored by
    decayed_reversal_scores over `formation` sessions, and the k biggest
    residual losers are held with inverse-volatility weights. Long-only:
    the winners' short leg is dropped."""
    _need(closes, beta_lookback + 1, "risk_neutral_reversal")
    rets = _returns(closes, beta_lookback)
    market = rets.mean(axis=1)
    mvar = float(market.var())
    if mvar <= 0:
        return equal_weight(closes)
    beta = rets.apply(lambda col: float(np.cov(col, market)[0, 1]) / mvar)
    resid = rets - np.outer(market, beta)
    resid = pd.DataFrame(resid, index=rets.index, columns=rets.columns)
    score = decayed_reversal_scores(resid, half_life=half_life, formation=formation).iloc[-1]
    losers = _top_k(-score, k)
    vol = _returns(closes, vol_lookback).std()
    raw = losers / vol.where(vol > 0)
    raw = raw.fillna(0.0)
    return raw / raw.sum() if raw.sum() > 0 else losers


# ---------------------------------------------------------------- RK269


def betti0(corr, eps: float) -> int:
    """Connected components of the correlation-distance graph
    d = sqrt((1 - rho) / 2) with edges d <= eps: the Betti-0 number of the
    Vietoris-Rips complex at scale eps (single linkage)."""
    c = np.asarray(corr, dtype=float)
    n = len(c)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    dist = np.sqrt(np.clip((1.0 - c) / 2.0, 0.0, None))
    for i in range(n):
        for j in range(i + 1, n):
            if dist[i, j] <= eps:
                parent[find(i)] = find(j)
    return len({find(i) for i in range(n)})


def contagion_score(closes: pd.DataFrame, window: int = 63, scales=(0.3, 0.4, 0.5)) -> float:
    """Mean over `scales` of 1 - (Betti-0 - 1) / (n - 1): 0 when every
    instrument is its own cluster at every scale, 1 when the whole universe
    has collapsed into one connected component -- correlations converging,
    the multiscale filtration's contagion signature."""
    _need(closes, window + 1, "contagion_score")
    corr = _returns(closes, window).corr().to_numpy()
    n = corr.shape[0]
    if n < 2:
        raise ConfigurationError("contagion needs two or more instruments")
    return float(np.mean([1.0 - (betti0(corr, e) - 1) / (n - 1) for e in scales]))


def contagion_guard(
    closes: pd.DataFrame,
    window: int = 63,
    history: int = 252,
    z: float = 1.5,
    floor: float = 0.25,
    base: Allocator = equal_weight,
) -> pd.Series:
    """RK269: `base` weights, scaled to `floor` while today's contagion
    score is more than `z` standard deviations above its own trailing
    `history` (sampled every 5 sessions) -- de-risking when the universe's
    clusters merge, as in the 2008 and 2020 sell-offs."""
    _need(closes, window + history + 1, "contagion_guard")
    now = contagion_score(closes, window)
    past = [
        contagion_score(closes.iloc[: len(closes) - lag], window)
        for lag in range(5, history + 1, 5)
    ]
    mu, sd = float(np.mean(past)), float(np.std(past))
    weights = base(closes)
    if sd > 0 and (now - mu) / sd > z:
        return weights * floor
    return weights


ALLOCATORS: dict[str, Allocator] = {
    "equal_weight": equal_weight,  # RK117
    "inverse_volatility": inverse_volatility,  # RK129
    "equal_risk_contribution": equal_risk_contribution,  # RK61
    "conformal_risk_parity": conformal_risk_parity,  # RK99
    "conformal_allocation": conformal_allocation,  # RK132
    "cross_sectional_momentum": cross_sectional_momentum,  # RK7, RK19
    "state_filtered_momentum": state_filtered_momentum,  # RK10
    "low_volatility": low_volatility,  # RK18
    "dividend_yield": dividend_yield,  # RK52
    "alpha_stacking": alpha_stacking,  # RK144
    "risk_neutral_reversal": risk_neutral_reversal,  # RK215
    "contagion_guard": contagion_guard,  # RK269
}

__all__ = [
    "ALLOCATORS",
    "SECTOR_ETFS",
    "alpha_stacking",
    "betti0",
    "conformal_allocation",
    "conformal_risk_parity",
    "contagion_guard",
    "contagion_score",
    "cross_sectional_momentum",
    "dividend_yield",
    "equal_risk_contribution",
    "equal_weight",
    "erc_weights",
    "inverse_volatility",
    "low_volatility",
    "risk_contributions",
    "risk_neutral_reversal",
    "state_filtered_momentum",
    "trailing_yield",
]
