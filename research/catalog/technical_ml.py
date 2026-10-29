"""
Technical, machine-learning-pipeline and text entries of the ranked list
(ledger RK44, RK77, RK78, RK212, RK214, RK217, RK271, RK290, RK293, RK311,
RK315). Positions are long-only (1 = hold, 0 = flat) unless a function
says otherwise. Research code: none of these is wired to the engine.

Sources:

  * Supertrend -- Olivier Seban's indicator (bands at (H + L)/2 +- m ATR that
    only ratchet in the trend's direction); ATR -- Wilder, "New Concepts in
    Technical Trading Systems", 1978.
  * Volatility breakout -- Larry Williams, "Long-Term Secrets to Short-Term
    Trading", 1999 (buy at the open plus k times the prior range).
  * Multi-horizon trend -- Hurst, Ooi & Pedersen, "A century of evidence on
    trend-following investing", J. Portfolio Mgmt 44, 2017 (1-, 3- and
    12-month signals); agreement filter after Elder's Triple Screen.
  * Breadth thrust -- Zweig, "Winning on Wall Street", 1986 (10-day EMA of
    advances / (advances + declines) from below 0.40 to above 0.615 within
    10 sessions).
  * Gradient-boosted ranking -- Gu, Kelly & Xiu, RFS 33, 2020 (trees among the
    best cross-sectional forecasters); LambdaRank via LightGBM (xgboost is not
    installed; the ranking objective is the same family).
  * CausalImpact -- Brodersen et al., Ann. Appl. Stat. 9, 2015. Here the
    structural model (local level + regression on controls) is fitted by
    Kalman-filter maximum likelihood instead of the paper's MCMC with
    spike-and-slab priors -- a stated simplification.
  * Sequential bootstrap and average uniqueness -- Lopez de Prado,
    "Advances in Financial Machine Learning", 2018, ch. 4.
  * Random forests -- Breiman, Machine Learning 45, 2001; on S&P 500
    constituents -- Krauss, Do & Huck, Eur. J. Oper. Res. 259, 2017.
  * Media pessimism -- Tetlock, "Giving content to investor sentiment",
    J. Finance 62, 2007; finance word lists -- Loughran & McDonald, J. Finance
    66, 2011 (a short illustrative subset is built in; pass the full lists).
  * FinBERT -- Araci, arXiv:1908.10063, 2019; Huang, Wang & Yang, Contemp.
    Account. Res. 40, 2023. No model weights are available offline, so RK311
    uses the lexicon scorer or a naive-Bayes classifier trained on labelled
    sentences (e.g. Financial PhraseBank) -- a stand-in, stated as such.
  * Empirical mode decomposition and the Hilbert spectrum -- Huang et al.,
    Proc. R. Soc. A 454, 1998 (sifting with cubic-spline envelopes).
"""

from __future__ import annotations

import re

import numpy as np
from lightgbm import LGBMRanker
from scipy.interpolate import CubicSpline
from scipy.optimize import minimize
from scipy.signal import hilbert
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- technical rules


def atr(high, low, close, n: int = 14) -> np.ndarray:
    """Wilder's average true range (recursive smoothing, seeded by the mean)."""
    h, lo, c = (np.asarray(a, float) for a in (high, low, close))
    tr = np.maximum(
        h - lo, np.maximum(np.abs(h - np.r_[c[0], c[:-1]]), np.abs(lo - np.r_[c[0], c[:-1]]))
    )
    out = np.full(len(c), np.nan)
    if len(c) < n:
        return out
    out[n - 1] = tr[:n].mean()
    for t in range(n, len(c)):
        out[t] = (out[t - 1] * (n - 1) + tr[t]) / n
    return out


def supertrend(high, low, close, n: int = 10, mult: float = 3.0) -> dict:
    """RK44: bands ratchet (upper only falls, lower only rises, unless price
    closed through them); the trend flips when the close crosses the active
    band. Returns trend (+1/-1), the active stop line and long-only positions."""
    h, lo, c = (np.asarray(a, float) for a in (high, low, close))
    a = atr(h, lo, c, n)
    mid = (h + lo) / 2
    up, dn = mid + mult * a, mid - mult * a
    trend = np.ones(len(c))
    line = np.full(len(c), np.nan)
    fu, fl = up.copy(), dn.copy()
    for t in range(n, len(c)):
        fu[t] = (
            up[t]
            if (up[t] < fu[t - 1] or c[t - 1] > fu[t - 1] or np.isnan(fu[t - 1]))
            else fu[t - 1]
        )
        fl[t] = (
            dn[t]
            if (dn[t] > fl[t - 1] or c[t - 1] < fl[t - 1] or np.isnan(fl[t - 1]))
            else fl[t - 1]
        )
        if trend[t - 1] > 0:
            trend[t] = -1 if c[t] < fl[t] else 1
        else:
            trend[t] = 1 if c[t] > fu[t] else -1
        line[t] = fl[t] if trend[t] > 0 else fu[t]
    trend[:n] = 0
    return {"trend": trend, "line": line, "positions": (trend > 0).astype(float)}


def williams_breakout(open_, high, low, k: float = 0.5) -> np.ndarray:
    """RK77 (Williams): the entry level each day is open + k x prior range;
    returns a boolean array of days whose high reached it."""
    o, h, lo = (np.asarray(a, float) for a in (open_, high, low))
    level = o[1:] + k * (h[:-1] - lo[:-1])
    return np.r_[False, h[1:] >= level]


def volatility_expansion_breakout(
    high, low, close, lookback: int = 20, atr_n: int = 14, expansion: float = 1.1
) -> np.ndarray:
    """RK77: long when the close breaks the prior `lookback`-day high while ATR
    is at least `expansion` times its value `lookback` days earlier; exit on a
    close below the prior `lookback`-day low."""
    h, lo, c = (np.asarray(x, float) for x in (high, low, close))
    a = atr(h, lo, c, atr_n)
    pos, out = 0, np.zeros(len(c))
    for t in range(max(lookback, atr_n) + lookback, len(c)):
        hi_prev, lo_prev = h[t - lookback : t].max(), lo[t - lookback : t].min()
        if pos == 0 and c[t] > hi_prev and a[t] >= expansion * a[t - lookback]:
            pos = 1
        elif pos == 1 and c[t] < lo_prev:
            pos = 0
        out[t] = pos
    return out


def multi_timeframe_trend(close, horizons=(21, 63, 252), mode: str = "agree") -> np.ndarray:
    """RK78: time-series momentum signs over several horizons. 'agree' holds
    only when all are positive (Triple-Screen style); 'average' holds the
    fraction of positive signals (Hurst-Ooi-Pedersen's equal blend, long-only)."""
    c = np.asarray(close, float)
    if mode not in ("agree", "average"):
        raise ConfigurationError("mode must be 'agree' or 'average'")
    out = np.zeros(len(c))
    for t in range(max(horizons), len(c)):
        signs = np.array([c[t] > c[t - h] for h in horizons], float)
        out[t] = float(signs.all()) if mode == "agree" else signs.mean()
    return out


def zweig_breadth_thrust(
    advances, declines, low: float = 0.40, high: float = 0.615, window: int = 10
) -> dict:
    """RK212: 10-day EMA of A / (A + D); a thrust fires the first day it is
    above `high` having been below `low` within the last `window` days."""
    a, d = np.asarray(advances, float), np.asarray(declines, float)
    ratio = a / (a + d)
    alpha = 2 / (window + 1)
    ema = np.empty(len(ratio))
    ema[0] = ratio[0]
    for t in range(1, len(ratio)):
        ema[t] = alpha * ratio[t] + (1 - alpha) * ema[t - 1]
    fired = np.zeros(len(ema), bool)
    for t in range(1, len(ema)):
        if ema[t] > high and ema[t - 1] <= high and (ema[max(0, t - window) : t] < low).any():
            fired[t] = True
    return {"ema": ema, "signal": fired}


# ---------------------------------------------------------------- ML pipeline


def relevance_labels(next_returns, groups, levels: int = 5) -> np.ndarray:
    """Per date, bucket next returns into 0..levels-1 (higher = better)."""
    r, out, start = np.asarray(next_returns, float), [], 0
    for g in groups:
        ranks = np.argsort(np.argsort(r[start : start + g]))
        out.append((ranks * levels // g).astype(int))
        start += g
    return np.concatenate(out)


def train_ranker(features, next_returns, groups, seed: int = 0, **kw) -> LGBMRanker:
    """RK214: LambdaRank gradient-boosted trees on (date-grouped) stock
    features; `groups` lists how many stocks each date has, in row order."""
    params = {
        "n_estimators": 100,
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_child_samples": 5,
        "random_state": seed,
        "verbose": -1,
    } | kw
    model = LGBMRanker(**params)
    model.fit(
        np.asarray(features, float), relevance_labels(next_returns, groups), group=list(groups)
    )
    return model


def rank_select(model: LGBMRanker, features, k: int) -> np.ndarray:
    s = model.booster_.predict(np.asarray(features, float))  # skips sklearn's name check
    w = np.zeros(len(s))
    w[np.argsort(-s)[:k]] = 1.0 / k
    return w


def lag_feature_matrix(close, lags=(1, 2, 3, 5, 10, 21)) -> tuple[np.ndarray, np.ndarray]:
    """Past returns over each lag as features at t; label = next-day return > 0."""
    c = np.asarray(close, float)
    m = max(lags)
    x = np.column_stack([c[m:-1] / c[m - lg : -1 - lg] - 1 for lg in lags])
    y = (c[m + 1 :] > c[m:-1]).astype(int)
    return x, y


def random_forest_signal(
    close, train: int, lags=(1, 2, 3, 5, 10, 21), seed: int = 0, threshold: float = 0.5
) -> dict:
    """RK290: random forest on lagged returns, trained on the first `train`
    rows and applied after; long when P(up) > threshold."""
    x, y = lag_feature_matrix(close, lags)
    rf = RandomForestClassifier(n_estimators=200, min_samples_leaf=5, random_state=seed)
    rf.fit(x[:train], y[:train])
    p = rf.predict_proba(x[train:])[:, 1]
    return {
        "model": rf,
        "proba": p,
        "positions": (p > threshold).astype(float),
        "hit_rate": float(((p > 0.5) == y[train:]).mean()),
    }


def indicator_matrix(bar_count: int, spans) -> np.ndarray:
    """1 where label i's span [start, end] covers bar t."""
    m = np.zeros((bar_count, len(spans)))
    for i, (a, b) in enumerate(spans):
        m[a : b + 1, i] = 1.0
    return m


def average_uniqueness(ind) -> np.ndarray:
    ind = np.asarray(ind, float)
    conc = ind.sum(1)
    u = np.divide(ind, conc[:, None], out=np.zeros_like(ind), where=conc[:, None] > 0)
    return np.array([u[ind[:, i] > 0, i].mean() for i in range(ind.shape[1])])


def sequential_bootstrap(ind, size: int | None = None, rng=None) -> np.ndarray:
    """RK271: draw labels one at a time with probability proportional to the
    average uniqueness each would have given the draws so far."""
    rng = np.random.default_rng(rng)
    ind = np.asarray(ind, float)
    n = ind.shape[1]
    chosen: list[int] = []
    for _ in range(size or n):
        conc = ind[:, chosen].sum(1) if chosen else np.zeros(len(ind))
        avg = np.empty(n)
        for i in range(n):
            col = ind[:, i] > 0
            avg[i] = (1.0 / (conc[col] + 1.0)).mean()
        chosen.append(int(rng.choice(n, p=avg / avg.sum())))
    return np.array(chosen)


# ---------------------------------------------------------------- causal impact (RK217)


def causal_impact(y, controls, pre_end: int) -> dict:
    """RK217: y_t = mu_t + beta'x_t + e, mu a random walk. Variances and beta
    are fitted by Kalman maximum likelihood on the pre-period; the post-
    period counterfactual is the filtered model run without updating on y
    (so its variance grows), giving point effects and 95% bands."""
    y, x = np.asarray(y, float), np.atleast_2d(np.asarray(controls, float).T).T
    k = x.shape[1]

    def local_level(resid, s_level, s_obs):
        """Scalar Kalman filter for a random-walk level: (loglik, level, var)."""
        level, var, ll = resid[0], 1.0, 0.0
        for v in resid:
            var += s_level
            f = var + s_obs
            e = v - level
            ll -= 0.5 * (np.log(2 * np.pi * f) + e * e / f)
            gain = var / f
            level, var = level + gain * e, (1 - gain) * var
        return ll, level, var

    def nll(p):
        return -local_level(y[:pre_end] - x[:pre_end] @ p[2:], *np.exp(p[:2]))[0]

    start = np.r_[np.log(np.var(y) * 0.01), np.log(np.var(y) * 0.1), np.zeros(k)]
    res = minimize(nll, start, method="Nelder-Mead", options={"maxiter": 3000})
    s_level, s_obs = np.exp(res.x[:2])
    beta = res.x[2:]
    _, level, var = local_level(y[:pre_end] - x[:pre_end] @ beta, s_level, s_obs)
    steps = np.arange(1, len(y) - pre_end + 1)
    mean = level + x[pre_end:] @ beta
    sd = np.sqrt(var + steps * s_level + s_obs)
    effect = y[pre_end:] - mean
    return {
        "counterfactual": mean,
        "lower": mean - 1.96 * sd,
        "upper": mean + 1.96 * sd,
        "effect": effect,
        "cumulative": float(effect.sum()),
        "beta": beta,
        "significant": bool(abs(effect.mean()) > 1.96 * sd.mean() / np.sqrt(len(sd))),
    }


# ---------------------------------------------------------------- text (RK293, RK311)

POSITIVE = {
    "gain",
    "gains",
    "growth",
    "improve",
    "improved",
    "strong",
    "beat",
    "beats",
    "record",
    "profit",
    "profitable",
    "upgrade",
    "surge",
    "rally",
    "exceed",
    "exceeded",
    "robust",
}
NEGATIVE = {
    "loss",
    "losses",
    "decline",
    "declined",
    "weak",
    "miss",
    "missed",
    "lawsuit",
    "fall",
    "fell",
    "downgrade",
    "risk",
    "risks",
    "concern",
    "concerns",
    "plunge",
    "default",
    "impairment",
    "recession",
    "layoffs",
    "fraud",
}
NEGATIONS = {"not", "no", "never", "without", "hardly"}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def lexicon_score(text: str, positive=POSITIVE, negative=NEGATIVE) -> dict:
    """Counts with a three-word negation window (a negated positive counts as
    negative and vice versa); tone = (pos - neg) / words."""
    words = tokenize(text)
    pos = neg = 0
    for i, w in enumerate(words):
        flipped = any(v in NEGATIONS for v in words[max(0, i - 3) : i])
        if w in positive:
            pos, neg = (pos, neg + 1) if flipped else (pos + 1, neg)
        elif w in negative:
            pos, neg = (pos + 1, neg) if flipped else (pos, neg + 1)
    n = max(len(words), 1)
    return {"positive": pos, "negative": neg, "tone": (pos - neg) / n, "pessimism": neg / n}


def pessimism_index(texts) -> np.ndarray:
    """RK293 (Tetlock): share of negative words per day's text."""
    return np.array([lexicon_score(t)["pessimism"] for t in texts])


def tetlock_positions(
    pessimism, window: int = 60, z: float = 1.5, wait: int = 2, hold: int = 3
) -> np.ndarray:
    """Long-only reading of Tetlock: after a pessimism spike (trailing z-score
    above z) prices fall and then revert, so stay flat for `wait` days and
    then hold for `hold` days to collect the reversal."""
    p = np.asarray(pessimism, float)
    pos = np.zeros(len(p))
    for t in range(window, len(p)):
        hist = p[t - window : t]
        if (p[t] - hist.mean()) / (hist.std() + 1e-12) > z:
            pos[t + wait + 1 : t + wait + 1 + hold] = 1.0
    return pos[: len(p)]


class SentenceClassifier:
    """RK311's stand-in for FinBERT: bag-of-words naive Bayes trained on
    labelled financial sentences (labels -1/0/+1)."""

    def __init__(self):
        self.vec = CountVectorizer(ngram_range=(1, 2), min_df=1)
        self.nb = MultinomialNB()

    def fit(self, sentences, labels) -> SentenceClassifier:
        self.nb.fit(self.vec.fit_transform(sentences), labels)
        return self

    def score(self, sentences) -> np.ndarray:
        """Expected label (P(+) - P(-))."""
        proba = self.nb.predict_proba(self.vec.transform(sentences))
        classes = list(self.nb.classes_)
        pos = proba[:, classes.index(1)] if 1 in classes else 0.0
        neg = proba[:, classes.index(-1)] if -1 in classes else 0.0
        return pos - neg


def event_sentiment_trades(
    event_index, scores, returns, threshold: float = 0.2, hold: int = 5
) -> dict:
    """RK311: buy at the close of event days whose sentiment score exceeds
    `threshold` and hold `hold` days (long-only); returns each trade's return
    and the cumulative abnormal return vs the unconditional mean."""
    r = np.asarray(returns, float)
    trades = []
    for i, s in zip(event_index, scores, strict=True):
        if s > threshold and i + hold < len(r):
            trades.append(float(np.prod(1 + r[i + 1 : i + 1 + hold]) - 1))
    base = (np.prod(1 + r) ** (hold / len(r))) - 1
    return {"trades": np.array(trades), "car": float(np.mean(trades) - base) if trades else 0.0}


# ---------------------------------------------------------------- EMD / Hilbert-Huang (RK315)


def _extrema(x):
    d = np.diff(x)
    maxima = np.flatnonzero((np.r_[d, 0] < 0) & (np.r_[0, d] > 0))
    minima = np.flatnonzero((np.r_[d, 0] > 0) & (np.r_[0, d] < 0))
    return maxima, minima


def emd(series, max_imfs: int = 4, sift: int = 10) -> list[np.ndarray]:
    """Sifting: subtract the mean of cubic-spline envelopes through the maxima
    and minima (ends pinned to the end points) `sift` times per IMF; the last
    element is the residual trend."""
    r = np.asarray(series, float).copy()
    t = np.arange(len(r))
    imfs = []
    for _ in range(max_imfs):
        h = r.copy()
        for _ in range(sift):
            mx, mn = _extrema(h)
            if len(mx) < 2 or len(mn) < 2:
                break
            upper = CubicSpline(np.r_[0, mx, len(h) - 1], np.r_[h[0], h[mx], h[-1]])(t)
            lower = CubicSpline(np.r_[0, mn, len(h) - 1], np.r_[h[0], h[mn], h[-1]])(t)
            h = h - (upper + lower) / 2
        mx, mn = _extrema(h)
        if len(mx) < 2 or len(mn) < 2:
            break
        imfs.append(h)
        r = r - h
    return [*imfs, r]


def instantaneous_phase(imf) -> np.ndarray:
    return np.angle(hilbert(np.asarray(imf, float)))


def emd_scalper_positions(close, window: int = 128, imf_index: int = 1) -> np.ndarray:
    """RK315: on each trailing window (causal; the last point carries EMD's
    end effect), take the chosen IMF's last Hilbert phase and hold long while
    it is in the rising half of the cycle (-pi < phase < 0: trough to peak)."""
    c = np.log(np.asarray(close, float))
    out = np.zeros(len(c))
    for t in range(window, len(c)):
        imfs = emd(c[t - window : t + 1])
        if len(imfs) > imf_index + 1:
            phase = instantaneous_phase(imfs[imf_index])[-1]
            out[t] = float(-np.pi < phase < 0)
    return out
