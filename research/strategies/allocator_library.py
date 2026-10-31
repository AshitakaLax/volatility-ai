"""
The ranked list's portfolio algorithms that need more than one instrument,
each a named allocator for the portfolio book (research/strategies/
portfolio_book.py; `python -m tools.portfolio_book --allocator NAME`).

They extend allocators.py's contract: a function of the daily closes BEFORE
the session it trades (rows oldest first, columns instruments) returning
long-only weights summing to at most 1. Some also read data the warehouse
does not hold, passed as DataFrames (`tools/portfolio_book.py --data
name=file.csv`), always filtered to dates on or before the last close they
are given:

  fundamentals  long table: date, ticker, field, value (point-in-time:
                `date` is when the figure was published)
  events        date, ticker, value [, text]
  deals         announce, close, ticker, offer, fallback
  navs          date, ticker, nav
  macro         date, value (e.g. CPI year-on-year inflation)

Stock-factor algorithms take the long-only top quantile of their score,
equal weight: the short leg is outside the owner's rules. ALLOCATOR_LIBRARY
maps every allocator name (allocators.ALLOCATORS included) to its function
and LEDGER maps it to its ledger ID. UNMEASURED: none has been run on real
data, and the engine trades one symbol per deployment, so these are
backtest books (engine/roadmap.md item 1).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.strategies import allocators as al
from research.strategies.allocators import _full, _need, _returns, _top_k


def _day(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize(None).normalize() if t.tzinfo is not None else t.normalize()


def _asof(frame: pd.DataFrame, column: str, asof) -> pd.DataFrame:
    """Rows of `frame` whose `column` date is on or before `asof`."""
    if frame is None or frame.empty:
        raise ConfigurationError(
            "this allocator needs its data table (tools/portfolio_book --data)"
        )
    dates = pd.to_datetime(frame[column]).dt.tz_localize(None).dt.normalize()
    return frame.assign(**{column: dates})[dates <= _day(asof)]


def field_snapshot(fundamentals, field: str, asof, columns, years_back: float = 0.0) -> pd.Series:
    """Each ticker's latest `field` published on or before `asof` minus
    `years_back` years; NaN where there is none."""
    cut = _day(asof) - pd.DateOffset(days=round(365.25 * years_back))
    f = _asof(fundamentals, "date", cut)
    f = f[f["field"] == field].sort_values("date")
    latest = f.groupby("ticker")["value"].last()
    return latest.reindex(columns).astype(float)


def field_history(fundamentals, field: str, asof, ticker: str) -> np.ndarray:
    f = _asof(fundamentals, "date", asof)
    f = f[(f["field"] == field) & (f["ticker"] == ticker)].sort_values("date")
    return f["value"].to_numpy(dtype=float)


def _quantile(scores: pd.Series, q: float) -> pd.Series:
    """Equal weight on the top `q` share (at least one) of finite scores."""
    s = scores.replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return pd.Series(0.0, index=scores.index)
    k = max(1, int(np.floor(len(s) * q)))
    return _full(_top_k(s, k), scores.index)


# ---------------------------------------------------------------- price-only factors


def momentum_12_1(closes, lookback: int = 252, skip: int = 21, q: float = 0.2) -> pd.Series:
    """RK6, Jegadeesh & Titman's 12-1 momentum: the return from `lookback`
    to `skip` sessions ago; the top `q` share, equal weight."""
    from research.catalog.factors import momentum_12_1 as mom

    _need(closes, lookback + 1, "momentum_12_1")
    return _quantile(pd.Series(mom(closes.to_numpy(), lookback, skip), closes.columns), q)


def residual_momentum(closes, formation: int = 36, q: float = 0.2) -> pd.Series:
    """RK16, Blitz, Huij & Martens (2011): each instrument's monthly returns
    regressed on the equal-weight market's over `formation` months; score =
    the sum of residuals over months t-12..t-2 over their standard deviation."""
    from research.catalog.factors import residual_momentum as rm

    monthly = closes.resample("ME").last().pct_change().dropna(how="all").iloc[:-1]
    if len(monthly) < formation + 1:
        raise ConfigurationError(f"residual_momentum needs {formation + 1} months of history")
    market = monthly.mean(axis=1).to_numpy()[:, None]
    scores = rm(monthly.to_numpy(), market, formation=formation)
    return _quantile(pd.Series(scores, closes.columns), q)


def factor_momentum(closes, lookback: int = 12, top: int = 2) -> pd.Series:
    """RK65, factor momentum (Ehsani & Linnainmaa 2022) over a universe of
    factor ETFs: the `top` instruments by trailing `lookback`-month return,
    held only while that return is positive."""
    from research.catalog.factors import factor_momentum as fm

    monthly = closes.resample("ME").last().pct_change().dropna(how="all")
    if len(monthly) < lookback + 1:
        raise ConfigurationError(f"factor_momentum needs {lookback + 1} months")
    w = fm(monthly.to_numpy(), lookback=lookback, top=top)
    return pd.Series(w, closes.columns)


def industry_reversal(closes, lookback: int = 1260, q: float = 0.2, fundamentals=None) -> pd.Series:
    """RK90, long-term industry reversal (Bornholt, Gharaibeh & Malin 2015)
    over sector ETFs: the bottom `q` share by `lookback`-session return.
    With fundamentals (fields book_to_market and earnings_change), kept only
    with a top-half book-to-market and non-falling earnings -- the valuation
    confirmation."""
    from research.catalog.factors import industry_reversal as ir

    _need(closes, lookback + 1, "industry_reversal")
    long_ret = closes.iloc[-1] / closes.iloc[-1 - lookback] - 1
    if fundamentals is None:
        return _quantile(-long_ret, q)
    bm = field_snapshot(fundamentals, "book_to_market", closes.index[-1], closes.columns)
    chg = field_snapshot(fundamentals, "earnings_change", closes.index[-1], closes.columns)
    w = ir(long_ret.to_numpy(), bm.fillna(bm.median()).to_numpy(), chg.fillna(0).to_numpy(), q=q)
    return pd.Series(w, closes.columns)


def inflation_rotation(closes, macro=None, high: float = 0.03, top: int = 1) -> pd.Series:
    """RK41, Neville et al. (2021): four inflation regimes (low/high x
    falling/rising, from published year-on-year CPI with a one-month lag);
    per regime, the `top` instruments with the best mean monthly return in
    that regime so far; hold those for the current regime."""
    from research.catalog.carry_rates import inflation_regimes

    m = _asof(macro, "date", closes.index[-1]).sort_values("date")
    monthly = closes.resample("ME").last().pct_change().dropna(how="all")
    m = m.set_index("date")["value"].resample("ME").last().ffill()
    idx = monthly.index.tz_localize(None) if monthly.index.tz is not None else monthly.index
    cpi = m.reindex(idx.normalize(), method="ffill").to_numpy()
    ok = np.isfinite(cpi)
    if ok.sum() < 24:
        raise ConfigurationError("inflation_rotation needs 24 months of macro data")
    regimes = inflation_regimes(cpi[ok], high=high)
    rets = monthly.to_numpy()[ok]
    now = regimes[-1]
    past = (regimes[:-1] == now) & np.isfinite(rets[:-1]).all(axis=1)
    if past.sum() < 3:
        return pd.Series(0.0, index=closes.columns)
    means = pd.Series(rets[:-1][past].mean(axis=0), closes.columns)
    return _full(_top_k(means[means > 0], top) if (means > 0).any() else means * 0, closes.columns)


# ---------------------------------------------------------------- optimisers


def min_cvar(closes, lookback: int = 504, alpha: float = 0.95, radius: float = 0.0) -> pd.Series:
    """RK53 (radius 0, Rockafellar & Uryasev) and RK88 (radius > 0, Wasserstein
    distributionally robust): minimum CVaR on the last `lookback` daily
    return scenarios, long-only and fully invested."""
    from research.catalog.allocation import cvar_weights

    _need(closes, lookback + 1, "min_cvar")
    w = cvar_weights(_returns(closes, lookback).to_numpy(), alpha=alpha, radius=radius)
    return pd.Series(np.clip(w, 0, None), closes.columns)


def dro_cvar(closes, lookback: int = 504, alpha: float = 0.95, radius: float = 0.002) -> pd.Series:
    """RK88: min_cvar with a Wasserstein ball of `radius` (Mohajerin
    Esfahani & Kuhn 2018)."""
    return min_cvar(closes, lookback, alpha, radius)


def global_min_variance(closes, lookback: int = 252) -> pd.Series:
    """RK60: the long-only minimum-variance portfolio of the last `lookback`
    daily returns."""
    from research.catalog.je_suis_tm_projects import markowitz_weights

    _need(closes, lookback + 1, "global_min_variance")
    w = markowitz_weights(_returns(closes, lookback))["min_variance"]
    return pd.Series(np.clip(w, 0, None), closes.columns)


def black_litterman(
    closes, lookback: int = 252, view_lookback: int = 126, confidence: float = 0.5
) -> pd.Series:
    """RK63, Black & Litterman: equal-weight prior; one absolute view per
    instrument, its annualised `view_lookback`-session momentum scaled by
    `confidence`; the posterior's long-only mean-variance weights."""
    from research.catalog.allocation import black_litterman_weights

    _need(closes, max(lookback, view_lookback) + 1, "black_litterman")
    rets = _returns(closes, lookback)
    cov = rets.cov().to_numpy() * 252
    n = closes.shape[1]
    view = (closes.iloc[-1] / closes.iloc[-1 - view_lookback] - 1) * 252 / view_lookback
    w = black_litterman_weights(cov, np.full(n, 1 / n), np.eye(n), confidence * view.to_numpy())
    w = np.clip(w, 0, None)
    return pd.Series(w / w.sum() if w.sum() > 0 else w, closes.columns)


def max_diversification(closes, lookback: int = 252) -> pd.Series:
    """RK66, Choueifaty & Coignard: maximise the diversification ratio."""
    from research.catalog.allocation import max_diversification_weights

    _need(closes, lookback + 1, "max_diversification")
    w = max_diversification_weights(_returns(closes, lookback).cov().to_numpy())
    return pd.Series(np.clip(w, 0, None), closes.columns)


def tail_risk_parity(closes, lookback: int = 504, alpha: float = 0.95) -> pd.Series:
    """RK95, asymmetric tail-risk parity (Boudt, Carl & Peterson 2013):
    equal CVaR contributions over the last `lookback` daily scenarios."""
    from research.catalog.allocation import cvar_risk_parity

    _need(closes, lookback + 1, "tail_risk_parity")
    w = cvar_risk_parity(_returns(closes, lookback).to_numpy(), alpha=alpha)
    return pd.Series(np.clip(w, 0, None) / max(np.clip(w, 0, None).sum(), 1e-12), closes.columns)


def wdro_mean_variance(closes, lookback: int = 252, radius: float = 0.01) -> pd.Series:
    """RK225, Wasserstein-robust mean-variance (Blanchet, Chen & Zhou 2022)."""
    from research.catalog.allocation import wdro_mean_variance as wmv

    _need(closes, lookback + 1, "wdro_mean_variance")
    w = wmv(_returns(closes, lookback).to_numpy(), radius=radius)
    return pd.Series(np.clip(w, 0, None), closes.columns)


def vine_copula_cvar(
    closes, lookback: int = 504, alpha: float = 0.95, n_sim: int = 2000
) -> pd.Series:
    """RK296: minimum CVaR over scenarios simulated from a C-vine copula fitted
    to the last `lookback` daily returns (Low et al. 2013)."""
    from research.catalog.allocation import vine_cvar_weights

    _need(closes, lookback + 1, "vine_copula_cvar")
    w = vine_cvar_weights(_returns(closes, lookback).to_numpy(), alpha=alpha, n_sim=n_sim, rng=0)
    return pd.Series(np.clip(w, 0, None), closes.columns)


def sparse_bayesian_factor(closes, lookback: int = 252, q: float = 0.5) -> pd.Series:
    """RK218, sparse Bayesian learning (ARD) factor model: each instrument's
    returns on two factors (the equal-weight market and a 12-1 momentum
    spread), irrelevant loadings pruned; expected return = loadings x the
    factors' trailing means. The top `q` share by expected return over
    variance, equal weight."""
    from research.catalog.allocation import ard_factor_loadings

    _need(closes, lookback + 22, "sparse_bayesian_factor")
    rets = _returns(closes, lookback)
    market = rets.mean(axis=1)
    mom = closes.pct_change(21).shift(1).iloc[-lookback:]
    rank = mom.rank(axis=1, pct=True)
    spread = (rets * (rank > 0.5)).mean(axis=1) - (rets * (rank <= 0.5)).mean(axis=1)
    factors = np.column_stack([market.to_numpy(), spread.fillna(0).to_numpy()])
    loadings = ard_factor_loadings(rets.to_numpy(), factors)
    loadings = np.asarray(loadings)
    if loadings.shape[0] != rets.shape[1]:
        loadings = loadings.T
    expected = loadings @ factors.mean(axis=0)
    score = pd.Series(expected / rets.var().to_numpy(), closes.columns)
    return _quantile(score[score > 0].reindex(closes.columns), q)


def topk_dropout(
    closes, current=None, lookback: int = 126, k: int = 3, n_drop: int = 1
) -> pd.Series:
    """RK216, Qlib's TopK-Dropout: rank by `lookback`-session momentum, keep
    k holdings and replace at most `n_drop` of them per rebalance -- a
    turnover limit on the ranking."""
    from research.catalog.allocation import topk_dropout as tkd

    _need(closes, lookback + 1, "topk_dropout")
    score = closes.iloc[-1] / closes.iloc[-1 - lookback] - 1
    held = set() if current is None else {c for c, w in current.items() if w > 1e-9}
    names = list(closes.columns)
    new, _, _ = tkd(
        score.to_numpy(), {names.index(h) for h in held if h in names}, k=k, n_drop=n_drop
    )
    w = pd.Series(0.0, index=closes.columns)
    for i in new:
        w.iloc[int(i)] = 1.0 / len(new)
    return w


def lambdarank(closes, horizon: int = 21, train: int = 750, k: int = 3) -> pd.Series:
    """RK214, gradient-boosted LambdaRank (LightGBM; the CSV names XGBoost):
    features 12-1, 6-1 and 1-month momentum per instrument per month-end,
    relevance = the next `horizon` sessions' return rank; trained on the
    last `train` sessions of month-ends whose outcome is known; hold the
    top k equally."""
    from research.catalog.cross_section import momentum_features
    from research.catalog.technical_ml import rank_select, train_ranker

    _need(closes, 253 + horizon + 40, "lambdarank")
    p = closes.to_numpy()
    ends = list(range(253, len(p) - horizon, horizon))[-max(3, train // horizon) :]
    feats, nxt, groups = [], [], []
    for t in ends:
        feats.append(momentum_features(p[: t + 1]))
        nxt.append(p[t + horizon] / p[t] - 1)
        groups.append(p.shape[1])
    if len(ends) < 3:
        return pd.Series(0.0, index=closes.columns)
    model = train_ranker(np.vstack(feats), np.concatenate(nxt), groups)
    w = rank_select(model, momentum_features(p), k)
    return pd.Series(w, closes.columns)


def domain_adversarial_momentum(
    closes, horizon: int = 21, train: int = 1000, k: int = 3, steps: int = 150
) -> pd.Series:
    """RK98, domain-adversarial momentum: a forecaster of the next
    `horizon`-session return from 12-1, 6-1 and 1-month momentum, trained
    with a gradient-reversal domain classifier (each instrument a domain)
    so its features carry across markets; hold the top k forecasts."""
    from research.catalog.cross_section import DomainAdversarialForecaster, momentum_features

    _need(closes, 253 + horizon + 40, "domain_adversarial_momentum")
    p = closes.to_numpy()
    n = p.shape[1]
    ends = list(range(253, len(p) - horizon, horizon))[-max(3, train // horizon) :]
    x = np.vstack([momentum_features(p[: t + 1]) for t in ends])
    y = np.concatenate([p[t + horizon] / p[t] - 1 for t in ends])
    domains = np.tile(np.arange(n), len(ends))
    model = DomainAdversarialForecaster(n_features=3, n_domains=n, seed=0)
    model.fit(x, y, domains, steps=steps)
    forecast = pd.Series(model.predict(momentum_features(p)), closes.columns)
    return (
        _full(_top_k(forecast[forecast > 0], k), closes.columns)
        if (forecast > 0).any()
        else forecast * 0
    )


# ---------------------------------------------------------------- scenario generators


def _scenario_cvar(scenarios: np.ndarray, columns, alpha: float) -> pd.Series:
    from research.catalog.allocation import cvar_weights

    w = cvar_weights(np.asarray(scenarios, float), alpha=alpha)
    return pd.Series(np.clip(w, 0, None), columns)


def diffusion_scenarios(
    closes, lookback: int = 504, steps: int = 200, n: int = 2000, alpha: float = 0.95
) -> pd.Series:
    """RK200: a denoising diffusion model of the joint daily returns over the
    last `lookback` sessions; minimum CVaR over `n` sampled scenarios."""
    from research.catalog.generative import DDPM

    _need(closes, lookback + 1, "diffusion_scenarios")
    r = _returns(closes, lookback).to_numpy()
    model = DDPM(dim=r.shape[1], seed=0)
    model.fit(r, steps=steps)
    return _scenario_cvar(model.sample(n, rng=0), closes.columns, alpha)


def gmmn_scenarios(
    closes, lookback: int = 504, steps: int = 200, n: int = 2000, alpha: float = 0.95
) -> pd.Series:
    """RK373: a generative moment-matching network (trained by MMD) of the
    joint daily returns; minimum CVaR over quasi-Monte-Carlo scenarios."""
    from research.catalog.generative import GMMN

    _need(closes, lookback + 1, "gmmn_scenarios")
    r = _returns(closes, lookback).to_numpy()
    model = GMMN(dim=r.shape[1], seed=0)
    model.fit(r, steps=steps)
    return _scenario_cvar(model.sample(n, rng=0), closes.columns, alpha)


def timegan_scenarios(
    closes, lookback: int = 504, length: int = 5, steps: int = 40, n: int = 500, alpha: float = 0.95
) -> pd.Series:
    """RK349: TimeGAN (Yoon et al. 2019) on `length`-session paths of the
    joint daily returns; minimum CVaR over the sampled paths' cumulative
    returns."""
    from research.catalog.generative import TimeGAN

    _need(closes, lookback + 1, "timegan_scenarios")
    r = _returns(closes, lookback).to_numpy()
    seqs = np.stack([r[i : i + length] for i in range(0, len(r) - length, length)])
    model = TimeGAN(n_features=r.shape[1], seed=0)
    model.fit(seqs, steps=steps)
    paths = model.sample(n, length, rng=0)
    return _scenario_cvar(paths.sum(axis=1), closes.columns, alpha)


def factor_diffusion_scenarios(
    closes,
    lookback: int = 504,
    factors: int = 2,
    n: int = 2000,
    alpha: float = 0.95,
    steps: int = 200,
) -> pd.Series:
    """RK395: PCA factors of the joint daily returns, a diffusion model on
    the factor returns only, cross-sections rebuilt with residual noise;
    minimum CVaR over the sampled scenarios."""
    from research.catalog.generative import FactorDiffusion

    _need(closes, lookback + 1, "factor_diffusion_scenarios")
    r = _returns(closes, lookback).to_numpy()
    model = FactorDiffusion(factors=min(factors, r.shape[1]), seed=0)
    model.fit(r, steps=steps)
    return _scenario_cvar(model.sample(n, rng=0), closes.columns, alpha)


# ---------------------------------------------------------------- fundamentals


def _bm(fund, asof, cols) -> pd.Series:
    return field_snapshot(fund, "book_equity", asof, cols) / field_snapshot(
        fund, "market_cap", asof, cols
    )


def value_momentum(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK5, Asness, Moskowitz & Pedersen (2013): the average of the rank
    z-scores of book-to-market and 12-1 momentum; top `q` share."""
    from research.catalog.factors import value_momentum_composite

    _need(closes, 253, "value_momentum")
    bm = _bm(fundamentals, closes.index[-1], closes.columns)
    ok = bm.notna().to_numpy()
    out = pd.Series(0.0, index=closes.columns)
    if ok.sum() < 2:
        return out
    res = value_momentum_composite(bm.to_numpy()[ok], closes.to_numpy()[:, ok], q=q)
    out[closes.columns[ok]] = res["weights"]
    return out


def _score_allocator(score: pd.Series, q: float) -> pd.Series:
    return _quantile(score, q)


def operating_profitability(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK12, Fama & French's operating profitability: (revenue - COGS - SG&A
    - interest) / book equity; top `q` share."""
    from research.catalog.factors import operating_profitability as op

    a, c = closes.index[-1], closes.columns
    s = op(
        *(
            field_snapshot(fundamentals, f, a, c)
            for f in ("revenue", "cogs", "sga", "interest", "book_equity")
        )
    )
    return _score_allocator(pd.Series(s, c), q)


def gross_profitability(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK13, Novy-Marx (2013): (revenue - COGS) / total assets; top `q`."""
    from research.catalog.factors import gross_profitability as gp

    a, c = closes.index[-1], closes.columns
    s = gp(*(field_snapshot(fundamentals, f, a, c) for f in ("revenue", "cogs", "total_assets")))
    return _score_allocator(pd.Series(s, c), q)


def _asset_growth(fund, asof, cols) -> pd.Series:
    now = field_snapshot(fund, "total_assets", asof, cols)
    prev = field_snapshot(fund, "total_assets", asof, cols, years_back=1.0)
    return now / prev - 1


def conservative_investment(closes, fundamentals=None, q: float = 0.3) -> pd.Series:
    """RK15, Fama & French's CMA leg, long-only and size-neutral: within each
    half split at the median market cap, the lowest `q` share by asset
    growth, weighted equally across the two halves."""
    a, c = closes.index[-1], closes.columns
    growth = _asset_growth(fundamentals, a, c)
    cap = field_snapshot(fundamentals, "market_cap", a, c)
    ok = growth.notna() & cap.notna()
    if ok.sum() < 2:
        return pd.Series(0.0, index=c)
    small = cap[ok] <= cap[ok].median()
    parts = [_quantile(-growth[ok][m], q) for m in (small, ~small) if m.any()]
    w = sum(p.reindex(c).fillna(0) for p in parts) / len(parts)
    return w


def asset_growth(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK51, Cooper, Gulen & Schill (2008): the lowest `q` share by
    year-on-year total-asset growth."""
    return _score_allocator(-_asset_growth(fundamentals, closes.index[-1], closes.columns), q)


def shareholder_yield(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK27: (dividends + buybacks - issuance + debt paydown) / market cap;
    top `q` share."""
    from research.catalog.factors import shareholder_yield as sy

    a, c = closes.index[-1], closes.columns
    f = {
        k: field_snapshot(fundamentals, k, a, c)
        for k in ("dividends", "buybacks", "issuance", "market_cap", "debt_paydown")
    }
    s = sy(
        f["dividends"], f["buybacks"], f["issuance"], f["market_cap"], f["debt_paydown"].fillna(0)
    )
    return _score_allocator(pd.Series(s, c), q)


def _sue_now(fund, asof, cols, window: int = 8) -> pd.Series:
    from research.catalog.factors import sue

    out = {}
    for t in cols:
        eps = field_history(fund, "eps", asof, t)
        if len(eps) >= window + 4:
            out[t] = float(sue(eps, window)[-1])
    return pd.Series(out, dtype=float).reindex(cols)


def standardized_unexpected_earnings(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK207, Foster, Olsen & Shevlin (1984): SUE = (EPS_q - EPS_{q-4}) / sd
    of the last eight such differences, from quarterly `eps` rows; top `q`."""
    return _score_allocator(_sue_now(fundamentals, closes.index[-1], closes.columns), q)


def price_earnings_momentum(closes, fundamentals=None, q: float = 1 / 3) -> pd.Series:
    """RK29, Chan, Jegadeesh & Lakonishok (1996): the intersection of the top
    `q` by 12-1 momentum and by SUE, equal weight."""
    from research.catalog.factors import price_earnings_momentum as pem

    _need(closes, 253, "price_earnings_momentum")
    s = _sue_now(fundamentals, closes.index[-1], closes.columns)
    ok = s.notna().to_numpy()
    out = pd.Series(0.0, index=closes.columns)
    if ok.sum() >= 2:
        out[closes.columns[ok]] = pem(closes.to_numpy()[:, ok], s.to_numpy()[ok], q=q)
    return out


def intangibles_value(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK31, Peters & Taylor capital: book-to-market with capitalised R&D and
    30% of SG&A added to book (from annual `rd` and `sga` histories), plus the
    matching profitability; top `q` by the sum of their rank z-scores."""
    from research.catalog.factors import intangibles_adjusted, rank_z

    a, c = closes.index[-1], closes.columns
    rows = []
    for t in c:
        rd, sga = field_history(fundamentals, "rd", a, t), field_history(fundamentals, "sga", a, t)
        rows.append((t, rd, sga))
    hist_len = min((min(len(r), len(s)) for _, r, s in rows), default=0)
    if hist_len < 2:
        return pd.Series(0.0, index=c)
    rd_hist = np.column_stack([r[-hist_len:] for _, r, _ in rows])
    sga_hist = np.column_stack([s[-hist_len:] for _, _, s in rows])
    snap = {
        k: field_snapshot(fundamentals, k, a, c).to_numpy()
        for k in ("book_equity", "market_cap", "gross_profit", "total_assets")
    }
    res = intangibles_adjusted(
        snap["book_equity"],
        snap["market_cap"],
        rd_hist,
        sga_hist,
        snap["gross_profit"],
        snap["total_assets"],
    )
    keys = [k for k in res if "bm" in k.lower() or "prof" in k.lower()]
    score = sum(rank_z(np.asarray(res[k], float)) for k in keys)
    return _score_allocator(pd.Series(score, c), q)


def net_issuance(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK35, Pontiff & Woodgate (2008): the lowest `q` share by the log change
    in shares outstanding over a year."""
    from research.catalog.factors import net_issuance as ni

    a, c = closes.index[-1], closes.columns
    now = field_snapshot(fundamentals, "shares", a, c)
    prev = field_snapshot(fundamentals, "shares", a, c, years_back=1.0)
    return _score_allocator(-pd.Series(ni(now, prev), c), q)


def estimate_revisions(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK40, analyst revision momentum: the change in the consensus EPS
    estimate over ~a month (`eps_estimate` rows) scaled by price; top `q`."""
    from research.catalog.factors import revision_score

    a, c = closes.index[-1], closes.columns
    now = field_snapshot(fundamentals, "eps_estimate", a, c)
    prev = field_snapshot(fundamentals, "eps_estimate", a, c, years_back=30 / 365.25)
    return _score_allocator(pd.Series(revision_score(now, prev, closes.iloc[-1]), c), q)


def book_to_market(closes, fundamentals=None, q: float = 0.3) -> pd.Series:
    """RK48, Fama & French's HML leg, long-only: the top `q` by book equity /
    market cap."""
    return _score_allocator(_bm(fundamentals, closes.index[-1], closes.columns), q)


def low_accruals(closes, fundamentals=None, q: float = 0.2) -> pd.Series:
    """RK50, Sloan (1996): the lowest `q` share by (net income - cash from
    operations) / average total assets."""
    from research.catalog.factors import accruals

    a, c = closes.index[-1], closes.columns
    s = accruals(
        *(field_snapshot(fundamentals, f, a, c) for f in ("net_income", "cfo", "avg_total_assets"))
    )
    return _score_allocator(-pd.Series(s, c), q)


def low_pe(
    closes, fundamentals=None, q: float = 0.2, max_leverage: float = 1.0, min_roe: float = 0.0
) -> pd.Series:
    """RK57, the Graham-style screen: no losses, debt/equity <= max_leverage,
    ROE >= min_roe; the cheapest `q` by P/E."""
    from research.catalog.factors import low_pe_screen

    a, c = closes.index[-1], closes.columns
    f = {
        k: field_snapshot(fundamentals, k, a, c).to_numpy()
        for k in ("eps", "debt_to_equity", "roe")
    }
    w = low_pe_screen(
        closes.iloc[-1].to_numpy(),
        f["eps"],
        f["debt_to_equity"],
        f["roe"],
        max_leverage,
        min_roe,
        q,
    )
    return pd.Series(np.nan_to_num(w), c)


def small_cap_quality(
    closes, fundamentals=None, q: float = 0.2, min_quality: float = 0.0
) -> pd.Series:
    """RK58, size controlling for junk (Asness et al. 2018): among names with
    quality (a `quality` score field) z above `min_quality`, the smallest `q`
    by market cap."""
    from research.catalog.factors import size_with_quality

    a, c = closes.index[-1], closes.columns
    cap = field_snapshot(fundamentals, "market_cap", a, c).to_numpy()
    quality = field_snapshot(fundamentals, "quality", a, c).to_numpy()
    w = size_with_quality(cap, quality, q, min_quality)
    return pd.Series(np.nan_to_num(w), c)


# ---------------------------------------------------------------- events


def _recent_events(events, asof, hold: int):
    e = _asof(events, "date", asof)
    return e[e["date"] > _day(asof) - pd.Timedelta(days=int(hold * 1.45))]


def _equal(names, columns) -> pd.Series:
    names = [n for n in dict.fromkeys(names) if n in columns]
    w = pd.Series(0.0, index=columns)
    if names:
        w[names] = 1.0 / len(names)
    return w


def earnings_drift(closes, fundamentals=None, threshold: float = 1.0, hold: int = 60) -> pd.Series:
    """RK45, post-earnings-announcement drift (Bernard & Thomas 1989): hold,
    equally, names whose latest quarterly SUE is above `threshold` and whose
    report was published within the last `hold` sessions."""
    a, c = closes.index[-1], closes.columns
    s = _sue_now(fundamentals, a, c)
    recent = _recent_events(
        fundamentals[fundamentals["field"] == "eps"].rename(columns={"value": "eps"}), a, hold
    )
    names = [t for t in recent["ticker"].unique() if s.get(t, np.nan) > threshold]
    return _equal(names, c)


def activist_13d(closes, events=None, threshold: float = 0.1, hold: int = 60) -> pd.Series:
    """RK47, Brav et al. (2008): hold names with a 13D filing in the last
    `hold` sessions whose activist score (stake x (1 + demands named in the
    `text`)) exceeds `threshold`."""
    from research.catalog.factors import activist_score

    e = _recent_events(events, closes.index[-1], hold)
    names = [
        r.ticker
        for r in e.itertuples()
        if activist_score(float(r.value), str(getattr(r, "text", "") or "")) > threshold
    ]
    return _equal(names, closes.columns)


def buyback_drift(closes, events=None, min_size: float = 0.02, hold: int = 60) -> pd.Series:
    """RK209, Ikenberry, Lakonishok & Vermaelen (1995): hold names that
    announced a buyback of at least `min_size` of shares (event `value`) in
    the last `hold` sessions."""
    e = _recent_events(events, closes.index[-1], hold)
    return _equal(list(e.loc[e["value"] >= min_size, "ticker"]), closes.columns)


def merger_arbitrage(
    closes, deals=None, p_success: float = 0.9, min_annual: float = 0.05
) -> pd.Series:
    """RK39, cash-deal merger arbitrage, long the target only: for each
    announced, unclosed deal, the expected annualised return of buying at
    the last close given `p_success`; hold, equally, the targets above
    `min_annual`."""
    from research.catalog.stat_arb import merger_arb_return

    asof = _day(closes.index[-1])
    d = _asof(deals, "announce", asof)
    d = d[pd.to_datetime(d["close"]).dt.tz_localize(None) > asof]
    names = []
    for r in d.itertuples():
        if r.ticker not in closes.columns:
            continue
        days = max(1, (pd.Timestamp(r.close).tz_localize(None) - asof).days)
        out = merger_arb_return(
            float(closes[r.ticker].iloc[-1]), float(r.offer), float(r.fallback), p_success, days
        )
        if out.get("annualised", out.get("annualized", 0.0)) > min_annual:
            names.append(r.ticker)
    return _equal(names, closes.columns)


def cef_discount(
    closes, navs=None, window: int = 250, entry: float = -2.0, exit: float = 0.0
) -> pd.Series:
    """RK82, closed-end fund discount reversion (Pontiff 1995), long-only:
    hold, equally, the funds whose discount (price / NAV - 1) z-score over
    `window` sessions went below `entry` and has not yet recovered to `exit`."""
    from research.catalog.stat_arb import cef_positions

    n = _asof(navs, "date", closes.index[-1])
    wide = n.pivot_table(index="date", columns="ticker", values="nav")
    idx = (
        closes.index.tz_localize(None).normalize() if closes.index.tz is not None else closes.index
    )
    names = []
    for t in closes.columns:
        if t not in wide:
            continue
        nav = wide[t].reindex(idx, method="ffill").to_numpy()
        ok = np.isfinite(nav)
        if ok.sum() > window + 1:
            pos = cef_positions(closes[t].to_numpy()[ok], nav[ok], window, entry, exit)
            if pos[-1] > 0:
                names.append(t)
    return _equal(names, closes.columns)


# ---------------------------------------------------------------- the library

NEW: dict[str, str] = {
    "momentum_12_1": "RK6",
    "residual_momentum": "RK16",
    "factor_momentum": "RK65",
    "industry_reversal": "RK90",
    "inflation_rotation": "RK41",
    "min_cvar": "RK53",
    "dro_cvar": "RK88",
    "global_min_variance": "RK60",
    "black_litterman": "RK63",
    "max_diversification": "RK66",
    "tail_risk_parity": "RK95",
    "wdro_mean_variance": "RK225",
    "vine_copula_cvar": "RK296",
    "sparse_bayesian_factor": "RK218",
    "topk_dropout": "RK216",
    "lambdarank": "RK214",
    "domain_adversarial_momentum": "RK98",
    "diffusion_scenarios": "RK200",
    "gmmn_scenarios": "RK373",
    "timegan_scenarios": "RK349",
    "factor_diffusion_scenarios": "RK395",
    "value_momentum": "RK5",
    "operating_profitability": "RK12",
    "gross_profitability": "RK13",
    "conservative_investment": "RK15",
    "asset_growth": "RK51",
    "shareholder_yield": "RK27",
    "standardized_unexpected_earnings": "RK207",
    "price_earnings_momentum": "RK29",
    "intangibles_value": "RK31",
    "net_issuance": "RK35",
    "estimate_revisions": "RK40",
    "book_to_market": "RK48",
    "low_accruals": "RK50",
    "low_pe": "RK57",
    "small_cap_quality": "RK58",
    "earnings_drift": "RK45",
    "activist_13d": "RK47",
    "buyback_drift": "RK209",
    "merger_arbitrage": "RK39",
    "cef_discount": "RK82",
}

# allocators.py's, completed earlier (RK19 is cross_sectional_momentum on a
# sector-ETF universe: --preset sectors).
EARLIER: dict[str, str] = {
    "cross_sectional_momentum": "RK7",
    "state_filtered_momentum": "RK10",
    "low_volatility": "RK18",
    "dividend_yield": "RK52",
    "equal_risk_contribution": "RK61",
    "conformal_risk_parity": "RK99",
    "equal_weight": "RK117",
    "inverse_volatility": "RK129",
    "conformal_allocation": "RK132",
    "alpha_stacking": "RK144",
    "risk_neutral_reversal": "RK215",
    "contagion_guard": "RK269",
}
LEDGER: dict[str, str] = {**EARLIER, **NEW}
ALLOCATOR_LIBRARY: dict = {**al.ALLOCATORS, **{name: globals()[name] for name in NEW}}

# What each data-reading allocator needs, for tools/portfolio_book.py's --data.
DATA_NEEDS: dict[str, tuple[str, ...]] = {
    **dict.fromkeys(
        (
            "value_momentum",
            "operating_profitability",
            "gross_profitability",
            "conservative_investment",
            "asset_growth",
            "shareholder_yield",
            "standardized_unexpected_earnings",
            "price_earnings_momentum",
            "intangibles_value",
            "net_issuance",
            "estimate_revisions",
            "book_to_market",
            "low_accruals",
            "low_pe",
            "small_cap_quality",
            "earnings_drift",
        ),
        ("fundamentals",),
    ),
    "activist_13d": ("events",),
    "buyback_drift": ("events",),
    "merger_arbitrage": ("deals",),
    "cef_discount": ("navs",),
    "inflation_rotation": ("macro",),
    "dividend_yield": ("dividends",),
}

__all__ = ["ALLOCATOR_LIBRARY", "DATA_NEEDS", "EARLIER", "LEDGER", "NEW", "field_snapshot"]
