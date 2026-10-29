"""
Equity factor and corporate-event entries of the ranked list (ledger RK5,
RK6, RK9, RK11, RK12, RK13, RK15, RK16, RK27, RK29, RK31, RK35, RK40,
RK45, RK47, RK48, RK49, RK50, RK51, RK57, RK58, RK65, RK90, RK207,
RK209, RK210, RK308). Every one needs a point-in-time stock universe with
fundamentals, which the project does not have (the pages say so), so
these are the scoring and portfolio rules on caller-supplied arrays.
Cross-sections are 1-D arrays over stocks; panels are (time, stocks).
Long-only selections hold the top quantile equally; long/short versions
are provided for measurement (the academic factor definitions).

Sources:

  * Value and momentum everywhere -- Asness, Moskowitz & Pedersen, J.
    Finance 68, 2013 (rank z-scores; 12-1 momentum skipping a month).
  * Fama & French, "A five-factor asset pricing model", J. Financial Econ.
    116, 2015 (2x3 size-characteristic sorts at the NYSE median and 30/70
    percentiles).
  * Quality minus junk -- Asness, Frazzini & Pedersen, Rev. Account. Stud.
    24, 2019 (profitability, growth, safety, payout z-scores).
  * Gross profitability -- Novy-Marx, J. Financial Econ. 108, 2013;
    operating profitability -- Fama & French 2015; asset growth -- Cooper,
    Gulen & Schill, J. Finance 63, 2008; accruals -- Sloan, Account. Rev. 71,
    1996; net issuance -- Pontiff & Woodgate, J. Finance 63, 2008; payout
    yield -- Boudoukh, Michaely, Richardson & Roberts, J. Finance 62, 2007.
  * Residual momentum -- Blitz, Huij & Martens, J. Empirical Finance 18,
    2011 (36-month factor regressions; residual return t-12..t-2 over its
    standard deviation).
  * Intangible capital -- Peters & Taylor, J. Financial Econ. 123, 2017
    (R&D depreciated at 15%, 30% of SG&A as organisation capital at 20%);
    intangibles-adjusted value -- Eisfeldt, Kim & Papanikolaou, RFS 35, 2022.
  * Betting against beta -- Frazzini & Pedersen, J. Financial Econ. 111, 2014
    (beta = rho sigma_i / sigma_m, shrunk 0.6 / 0.4 toward one; rank weights;
    each leg scaled to beta one).
  * Earnings drift -- Bernard & Thomas, J. Account. Res. 27, 1989 (SUE from
    seasonal differences); price + earnings momentum and revisions -- Chan,
    Jegadeesh & Lakonishok, J. Finance 51, 1996.
  * Event studies -- MacKinlay, J. Econ. Lit. 35, 1997 (market-model
    abnormal returns); activism -- Brav, Jiang, Partnoy & Thomas, J. Finance
    63, 2008; buybacks -- Ikenberry, Lakonishok & Vermaelen, J. Financial
    Econ. 39, 1995; index additions -- Patel & Welch, "Extended stock
    returns in response to S&P 500 index changes", RAPS 7, 2017; ex-dividend
    pricing -- Elton & Gruber, Rev. Econ. Stat. 52, 1970.
  * Long-run industry reversal -- per RK90's page; factor momentum -- Gupta &
    Kelly, J. Portfolio Mgmt 45, 2019; Arnott, Clements, Kalesnik & Linnainmaa,
    J. Finance 78, 2023.
  * Size and junk -- Asness, Frazzini, Israel, Moskowitz & Pedersen,
    J. Financial Econ. 129, 2018; low P/E -- Basu, J. Finance 32, 1977.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- shared machinery


def rank_z(x) -> np.ndarray:
    """Cross-sectional rank z-score (NaNs stay NaN), as in AMP and QMJ."""
    v = np.asarray(x, float)
    out = np.full(len(v), np.nan)
    ok = np.isfinite(v)
    if ok.sum() < 2:
        return out
    r = stats.rankdata(v[ok])
    out[ok] = (r - r.mean()) / r.std()
    return out


def quantile_weights(scores, q: float = 0.2, long_short: bool = False) -> np.ndarray:
    """Equal weights on the top `q` share of scores (and -equal on the bottom
    share when long_short, each leg summing to one in magnitude)."""
    s = np.asarray(scores, float)
    ok = np.isfinite(s)
    w = np.zeros(len(s))
    n = max(round(float(q * ok.sum())), 1)
    order = np.argsort(np.where(ok, -s, np.inf))
    w[order[:n]] = 1.0 / n
    if long_short:
        bottom = np.argsort(np.where(ok, s, np.inf))[:n]
        w[bottom] -= 1.0 / n
    return w


def two_by_three_factor(characteristic, market_cap, next_returns, nyse=None) -> dict:
    """Fama-French factor return: split at the (NYSE) size median and the
    30th/70th characteristic percentiles, value-weight the six portfolios,
    factor = (small high + big high) / 2 - (small low + big low) / 2; SMB is
    the average small minus average big."""
    c, m, r = (np.asarray(a, float) for a in (characteristic, market_cap, next_returns))
    ref = np.ones(len(c), bool) if nyse is None else np.asarray(nyse, bool)
    size_bp = np.median(m[ref])
    lo_bp, hi_bp = np.percentile(c[ref], [30, 70])
    out = {}
    for size, smask in (("S", m <= size_bp), ("B", m > size_bp)):
        for lvl, cmask in (("L", c <= lo_bp), ("M", (c > lo_bp) & (c < hi_bp)), ("H", c >= hi_bp)):
            sel = smask & cmask
            out[size + lvl] = float((m[sel] * r[sel]).sum() / m[sel].sum()) if sel.any() else 0.0
    factor = (out["SH"] + out["BH"]) / 2 - (out["SL"] + out["BL"]) / 2
    smb = (out["SL"] + out["SM"] + out["SH"]) / 3 - (out["BL"] + out["BM"] + out["BH"]) / 3
    return {"factor": factor, "smb": smb, "portfolios": out}


def factor_regression(returns, factors) -> dict:
    """RK9 as a measuring stick: OLS of returns on factor returns; alpha,
    loadings, their t-statistics and R^2."""
    y, f = np.asarray(returns, float), np.atleast_2d(np.asarray(factors, float).T).T
    x = np.column_stack([np.ones(len(y)), f])
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ coef
    s2 = resid @ resid / (len(y) - x.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(x.T @ x)))
    return {
        "alpha": float(coef[0]),
        "betas": coef[1:],
        "t": coef / se,
        "r2": float(1 - resid.var() / y.var()),
    }


# ---------------------------------------------------------------- price-based signals


def momentum_12_1(prices, lookback: int = 252, skip: int = 21) -> np.ndarray:
    """RK6: each stock's return from t - lookback to t - skip (prices (T, n))."""
    p = np.asarray(prices, float)
    if len(p) <= lookback:
        raise ConfigurationError("need more than `lookback` rows of prices")
    return p[-1 - skip] / p[-1 - lookback] - 1


def value_momentum_composite(book_to_market, prices, q: float = 0.2) -> dict:
    """RK5: average of value and 12-1 momentum rank z-scores; long top quantile."""
    score = np.nanmean([rank_z(book_to_market), rank_z(momentum_12_1(prices))], axis=0)
    return {"score": score, "weights": quantile_weights(score, q)}


def residual_momentum(
    stock_returns, factor_returns, formation: int = 36, skip: int = 1, window: int = 11
) -> np.ndarray:
    """RK16 (monthly data): regress each stock's last `formation` returns on
    the factors; score = sum of residuals over months t-12..t-2 divided by
    their standard deviation."""
    r, f = np.asarray(stock_returns, float), np.asarray(factor_returns, float)
    x = np.column_stack([np.ones(formation), f[-formation:]])
    scores = np.empty(r.shape[1])
    for i in range(r.shape[1]):
        coef, *_ = np.linalg.lstsq(x, r[-formation:, i], rcond=None)
        e = r[-formation:, i] - x @ coef
        part = e[-skip - window : -skip] if skip else e[-window:]
        scores[i] = part.sum() / (part.std() + 1e-12)
    return scores


def bab_betas(
    stock_returns,
    market_returns,
    vol_window: int = 252,
    corr_window: int = 1260,
    shrink: float = 0.6,
) -> np.ndarray:
    """Frazzini-Pedersen betas: correlation from 3-day overlapping log returns
    over corr_window, volatilities from daily returns over vol_window, then
    shrink * beta + (1 - shrink) * 1."""
    r, m = np.asarray(stock_returns, float), np.asarray(market_returns, float)
    lr, lm = np.log1p(r), np.log1p(m)
    r3 = lr[2:] + lr[1:-1] + lr[:-2]
    m3 = lm[2:] + lm[1:-1] + lm[:-2]
    rho = np.array(
        [np.corrcoef(r3[-corr_window:, i], m3[-corr_window:])[0, 1] for i in range(r.shape[1])]
    )
    beta = rho * r[-vol_window:].std(0) / m[-vol_window:].std()
    return shrink * beta + (1 - shrink)


def bab_weights(betas) -> dict:
    """RK49: rank weights w_H ~ (z - zbar)^+, w_L ~ (z - zbar)^-, each summing
    to one; the low leg is scaled by 1 / beta_L and the high leg by 1 / beta_H,
    so the long/short book has beta zero. The long-only reading holds the low
    leg alone (unlevered)."""
    b = np.asarray(betas, float)
    z = stats.rankdata(b)
    d = z - z.mean()
    wh = np.clip(d, 0, None) / np.clip(d, 0, None).sum()
    wl = np.clip(-d, 0, None) / np.clip(-d, 0, None).sum()
    beta_l, beta_h = wl @ b, wh @ b
    return {
        "long": wl / beta_l,
        "short": wh / beta_h,
        "long_only": wl,
        "beta_long": float(beta_l),
        "beta_short": float(beta_h),
    }


def factor_momentum(factor_returns, lookback: int = 12, top: int | None = None) -> np.ndarray:
    """RK65: time-series factor momentum (long factors whose trailing return is
    positive, equal weight); with `top`, cross-sectional (the best `top`)."""
    f = np.asarray(factor_returns, float)
    trail = np.prod(1 + f[-lookback:], axis=0) - 1
    if top is None:
        w = (trail > 0).astype(float)
    else:
        w = np.zeros(f.shape[1])
        w[np.argsort(-trail)[:top]] = 1.0
    return w / w.sum() if w.sum() else w


# ---------------------------------------------------------------- fundamental scores


def gross_profitability(revenue, cogs, total_assets) -> np.ndarray:
    """RK13: (revenue - COGS) / total assets."""
    return (np.asarray(revenue, float) - np.asarray(cogs, float)) / np.asarray(total_assets, float)


def operating_profitability(revenue, cogs, sga, interest, book_equity) -> np.ndarray:
    """RK12 (Fama-French RMW measure): (revenue - COGS - SG&A - interest) / book equity."""
    return (
        np.asarray(revenue, float)
        - np.asarray(cogs, float)
        - np.asarray(sga, float)
        - np.asarray(interest, float)
    ) / np.asarray(book_equity, float)


def asset_growth(assets_now, assets_prev) -> np.ndarray:
    """RK15/RK51: annual total-asset growth (low = conservative = good)."""
    return np.asarray(assets_now, float) / np.asarray(assets_prev, float) - 1


def accruals(net_income, cash_from_operations, avg_total_assets) -> np.ndarray:
    """RK50 (cash-flow form of Sloan's measure): (NI - CFO) / average assets."""
    return (np.asarray(net_income, float) - np.asarray(cash_from_operations, float)) / np.asarray(
        avg_total_assets, float
    )


def net_issuance(shares_now, shares_prev) -> np.ndarray:
    """RK35: log change in split-adjusted shares outstanding (low = good)."""
    return np.log(np.asarray(shares_now, float) / np.asarray(shares_prev, float))


def shareholder_yield(dividends, buybacks, issuance, market_cap, debt_paydown=None) -> np.ndarray:
    """RK27: (dividends + buybacks - issuance [+ net debt paydown]) / market cap."""
    total = np.asarray(dividends, float) + np.asarray(buybacks, float) - np.asarray(issuance, float)
    if debt_paydown is not None:
        total = total + np.asarray(debt_paydown, float)
    return total / np.asarray(market_cap, float)


def quality_score(profitability: dict, growth: dict, safety: dict, payout: dict) -> dict:
    """RK11 (QMJ): each component is the average rank z-score of its inputs
    (dict of name -> cross-section; higher = better, so pass e.g. -leverage);
    quality = z(z(prof) + z(growth) + z(safety) + z(payout))."""

    def comp(d):
        return rank_z(np.nanmean([rank_z(v) for v in d.values()], axis=0))

    parts = {
        "profitability": comp(profitability),
        "growth": comp(growth),
        "safety": comp(safety),
        "payout": comp(payout),
    }
    parts["quality"] = rank_z(sum(parts.values()))
    return parts


def intangible_capital(spend_history, depreciation: float, share: float = 1.0) -> np.ndarray:
    """Perpetual inventory K_t = (1 - d) K_{t-1} + share x spend_t per firm;
    spend_history (years, firms), oldest first."""
    s = np.asarray(spend_history, float)
    k = np.zeros(s.shape[1])
    for row in s:
        k = (1 - depreciation) * k + share * row
    return k


def intangibles_adjusted(
    book_equity, market_cap, rd_history, sga_history, gross_profit, total_assets
) -> dict:
    """RK31 (Peters-Taylor capital, Eisfeldt-Kim-Papanikolaou value): adjusted
    book = book + K_R&D(15%) + K_org(30% of SG&A, 20%); adjusted B/M and an
    adjusted profitability = (gross profit + R&D + 0.3 SG&A) / (assets + K)."""
    k_rd = intangible_capital(rd_history, 0.15)
    k_org = intangible_capital(sga_history, 0.20, 0.30)
    k = k_rd + k_org
    adj_book = np.asarray(book_equity, float) + k
    rd_now, sga_now = np.asarray(rd_history, float)[-1], np.asarray(sga_history, float)[-1]
    prof = (np.asarray(gross_profit, float) + rd_now + 0.3 * sga_now) / (
        np.asarray(total_assets, float) + k
    )
    return {
        "intangibles": k,
        "adj_book_to_market": adj_book / np.asarray(market_cap, float),
        "adj_profitability": prof,
    }


def low_pe_screen(
    price, eps, debt_to_equity, roe, max_leverage: float = 1.0, min_roe: float = 0.0, q: float = 0.2
) -> np.ndarray:
    """RK57: exclude losses, leverage above `max_leverage` and ROE below
    `min_roe`; hold the cheapest `q` by P/E (highest E/P)."""
    ep = np.asarray(eps, float) / np.asarray(price, float)
    ok = (
        (np.asarray(eps) > 0)
        & (np.asarray(debt_to_equity) <= max_leverage)
        & (np.asarray(roe) >= min_roe)
    )
    return quantile_weights(np.where(ok, ep, np.nan), q)


def size_with_quality(market_cap, quality, q: float = 0.2, min_quality: float = 0.0) -> np.ndarray:
    """RK58 (size controlling for junk): among stocks with quality z above
    `min_quality`, hold the smallest `q`."""
    m, qz = np.asarray(market_cap, float), np.asarray(quality, float)
    return quantile_weights(np.where(qz > min_quality, -np.log(m), np.nan), q)


def industry_reversal(
    industry_returns_long,
    book_to_market,
    fundamental_change,
    q: float = 0.2,
    min_bm_rank: float = 0.5,
) -> np.ndarray:
    """RK90: industries in the bottom `q` of long-horizon (3-5 year) returns,
    kept only if their B/M rank is in the top half and fundamentals have
    stopped deteriorating (fundamental_change >= 0); equal weight."""
    r = np.asarray(industry_returns_long, float)
    pct = stats.rankdata(np.asarray(book_to_market, float)) / len(r)
    losers = r <= np.quantile(r, q)
    keep = losers & (pct >= min_bm_rank) & (np.asarray(fundamental_change, float) >= 0)
    return keep / keep.sum() if keep.any() else np.zeros(len(r))


def revision_score(estimates_now, estimates_prev, price) -> np.ndarray:
    """RK40: change in the consensus EPS estimate scaled by price."""
    return (np.asarray(estimates_now, float) - np.asarray(estimates_prev, float)) / np.asarray(
        price, float
    )


# ---------------------------------------------------------------- earnings events (RK29, RK45, RK207)


def sue(eps_history, window: int = 8) -> np.ndarray:
    """RK207: (EPS_q - EPS_{q-4}) / sd of the last `window` such seasonal
    differences, for each quarter with enough history (NaN before)."""
    e = np.asarray(eps_history, float)
    d = np.r_[np.full(4, np.nan), e[4:] - e[:-4]]
    out = np.full(len(e), np.nan)
    for t in range(4 + window, len(e)):
        hist = d[t - window : t]
        out[t] = d[t] / (np.nanstd(hist) + 1e-12)
    return out


def price_earnings_momentum(prices, sue_now, q: float = 1 / 3) -> np.ndarray:
    """RK29: hold the intersection of the top `q` by 12-1 momentum and by SUE."""
    mom, s = momentum_12_1(prices), np.asarray(sue_now, float)
    keep = (mom >= np.nanquantile(mom, 1 - q)) & (s >= np.nanquantile(s, 1 - q))
    return keep / keep.sum() if keep.any() else np.zeros(len(mom))


def market_model_car(
    returns, market, event_index: int, estimation=(-250, -30), window=(0, 20)
) -> dict:
    """Event-study abnormal returns AR = r - (a + b m) with a, b estimated over
    the estimation window (days relative to the event); CAR over `window`."""
    r, m = np.asarray(returns, float), np.asarray(market, float)
    e0, e1 = event_index + estimation[0], event_index + estimation[1]
    if e0 < 0 or event_index + window[1] >= len(r):
        raise ConfigurationError("event too close to the start or end of the data")
    b, a = np.polyfit(m[e0:e1], r[e0:e1], 1)
    w0, w1 = event_index + window[0], event_index + window[1] + 1
    ar = r[w0:w1] - (a + b * m[w0:w1])
    return {"ar": ar, "car": float(ar.sum()), "alpha": float(a), "beta": float(b)}


def event_drift_trades(
    event_index, signal, returns, threshold: float, hold: int = 60
) -> np.ndarray:
    """RK45/RK209/RK47: buy the close after each event whose signal exceeds
    `threshold` and hold `hold` days; returns each trade's compounded return."""
    r = np.asarray(returns, float)
    out = [
        np.prod(1 + r[i + 1 : i + 1 + hold]) - 1
        for i, s in zip(event_index, signal, strict=True)
        if s > threshold and i + hold < len(r)
    ]
    return np.array(out)


ACTIVIST_TERMS = (
    "board",
    "strategic alternatives",
    "sale of the company",
    "spin",
    "buyback",
    "repurchase",
    "management",
    "proxy",
    "nominate",
    "undervalued",
)


def activist_score(stake: float, purpose_text: str) -> float:
    """RK47: a 13D filing's score = stake (fraction) x (1 + number of distinct
    activist demands named in Item 4)."""
    text = purpose_text.lower()
    return float(stake * (1 + sum(term in text for term in ACTIVIST_TERMS)))


# ---------------------------------------------------------------- index and dividend events (RK210, RK308)


def predict_index_changes(market_caps, members, index_size: int, buffer: float = 0.2) -> dict:
    """RK210: rank all stocks by market cap; non-members ranked inside
    index_size x (1 - buffer) are predicted additions, members ranked beyond
    index_size x (1 + buffer) predicted deletions (a buffer rule like the
    Russell bands)."""
    m = np.asarray(market_caps, float)
    mem = np.asarray(members, bool)
    rank = np.empty(len(m), int)
    rank[np.argsort(-m)] = np.arange(1, len(m) + 1)
    adds = np.flatnonzero(~mem & (rank <= index_size * (1 - buffer)))
    dels = np.flatnonzero(mem & (rank > index_size * (1 + buffer)))
    return {"additions": adds, "deletions": dels, "rank": rank}


def dividend_capture(close_cum, close_ex, dividend, tax_rate: float = 0.0) -> dict:
    """RK308: buy at the cum-dividend close, sell at the ex-day close: return
    (P_ex - P_cum + (1 - tax) D) / P_cum, and the ex-day drop ratio
    (P_cum - P_ex) / D (Elton-Gruber; 1 = full drop)."""
    pc, pe, d = (np.asarray(a, float) for a in (close_cum, close_ex, dividend))
    return {"return": (pe - pc + (1 - tax_rate) * d) / pc, "drop_ratio": (pc - pe) / d}
