"""
Deflated Sharpe ratio and the probability of backtest overfitting --
catalog C-ML4 (docs/research/correction-strategies.md, ML4).

Sources:
  Bailey & Lopez de Prado, "The Deflated Sharpe Ratio: Correcting for
  Selection Bias, Backtest Overfitting and Non-Normality", Journal of
  Portfolio Management 40(5), 2014.
  Bailey, Borwein, Lopez de Prado & Zhu, "The Probability of Backtest
  Overfitting", Journal of Computational Finance 20(4).

PROBABILISTIC AND DEFLATED SHARPE RATIO (non-annualized throughout)

    PSR(SR*) = Z( (SR - SR*) * sqrt(T - 1)
                  / sqrt(1 - g3 * SR + (g4 - 1) / 4 * SR^2) )
    SR0      = sqrt(V[SR_n]) * ( (1 - gamma) * Zinv(1 - 1/N)
                                 + gamma * Zinv(1 - 1/(N e)) )
    DSR      = PSR(SR0)

g3 = skewness, g4 = kurtosis (NOT excess: 3 for Normal returns),
gamma = Euler-Mascheroni, N = number of independent trials, V[SR_n] =
variance of the trials' Sharpe ratios. The paper's worked example (N=100,
V = 1/2 annualized, T=1250, g3=-3, g4=10, SR = 2.5 annualized, 250
observations a year) gives SR0 = 0.1132 and DSR = 0.9004; N=46 would have
given 0.9505; with Normal returns DSR stays above 0.95 through N=88. The
tests reproduce all of it.

PROBABILITY OF BACKTEST OVERFITTING (CSCV)

Split a T x N matrix of per-period performance (rows = periods, columns =
strategy configurations) into S contiguous row groups, S even. For every
choice of S/2 groups as the in-sample set (complement out-of-sample):
take the configuration n* with the best in-sample metric, find its
relative rank w in [0, 1] out of sample, and record the logit
lambda = ln(w / (1 - w)). PBO is the share of splits with lambda <= 0 --
how often the in-sample winner lands at or below the out-of-sample median.
"""

from __future__ import annotations

import math
from itertools import combinations
from statistics import NormalDist

import numpy as np

from engine.core.exceptions import ConfigurationError

EULER_GAMMA = 0.5772156649015329
_Z = NormalDist()


def sharpe_ratio(returns) -> float:
    """Mean over sample stdev (ddof=1), per period, not annualized."""
    r = np.asarray(returns, dtype=float)
    if r.size < 2:
        raise ConfigurationError("need at least two returns for a Sharpe ratio")
    sd = r.std(ddof=1)
    if sd == 0:
        raise ConfigurationError("returns have zero variance")
    return float(r.mean() / sd)


def moments(returns) -> tuple[float, float]:
    """(skewness, kurtosis), population moments; kurtosis is 3 for Normal."""
    r = np.asarray(returns, dtype=float)
    d = r - r.mean()
    m2 = float((d**2).mean())
    if m2 == 0:
        raise ConfigurationError("returns have zero variance")
    return float((d**3).mean() / m2**1.5), float((d**4).mean() / m2**2)


def probabilistic_sharpe(sr: float, sr_star: float, t: int, skew: float, kurt: float) -> float:
    """PSR(SR*): probability the true Sharpe ratio exceeds SR*."""
    if t < 2:
        raise ConfigurationError(f"T must be >= 2, got {t}")
    denominator = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2
    if denominator <= 0:
        raise ConfigurationError("non-positive PSR variance term; check skew and kurtosis")
    return _Z.cdf((sr - sr_star) * math.sqrt(t - 1) / math.sqrt(denominator))


def expected_max_sharpe(sr_variance: float, n_trials: int) -> float:
    """SR0, the expected maximum Sharpe ratio of N independent trials whose
    true Sharpe ratio is zero."""
    if not (isinstance(n_trials, int) and n_trials >= 2):
        raise ConfigurationError(f"n_trials must be an integer >= 2, got {n_trials!r}")
    if sr_variance < 0:
        raise ConfigurationError(f"sr_variance must be >= 0, got {sr_variance}")
    return math.sqrt(sr_variance) * (
        (1 - EULER_GAMMA) * _Z.inv_cdf(1 - 1 / n_trials)
        + EULER_GAMMA * _Z.inv_cdf(1 - 1 / (n_trials * math.e))
    )


def deflated_sharpe(
    sr: float, sr_variance: float, n_trials: int, t: int, skew: float, kurt: float
) -> float:
    """DSR = PSR(SR0)."""
    return probabilistic_sharpe(sr, expected_max_sharpe(sr_variance, n_trials), t, skew, kurt)


def probability_of_backtest_overfitting(
    performance, n_groups: int, metric=sharpe_ratio
) -> dict[str, object]:
    """CSCV: {'pbo', 'logits', 'n_splits'} for a T x N performance matrix."""
    m = np.asarray(performance, dtype=float)
    if m.ndim != 2 or m.shape[1] < 2:
        raise ConfigurationError("performance must be a T x N matrix with N >= 2 strategies")
    if not (isinstance(n_groups, int) and n_groups >= 2 and n_groups % 2 == 0):
        raise ConfigurationError(f"n_groups must be an even integer >= 2, got {n_groups!r}")
    if n_groups > m.shape[0]:
        raise ConfigurationError("n_groups exceeds the number of periods")
    groups = np.array_split(np.arange(m.shape[0]), n_groups)
    n = m.shape[1]
    logits = []
    for chosen in combinations(range(n_groups), n_groups // 2):
        is_rows = np.concatenate([groups[g] for g in chosen])
        oos_rows = np.concatenate([groups[g] for g in range(n_groups) if g not in chosen])
        is_score = np.array([metric(m[is_rows, j]) for j in range(n)])
        oos_score = np.array([metric(m[oos_rows, j]) for j in range(n)])
        best = int(np.argmax(is_score))
        # Relative rank in (0, 1): rank 1..N divided by N + 1, as in the paper.
        rank = 1 + int((oos_score < oos_score[best]).sum())
        w = rank / (n + 1)
        logits.append(math.log(w / (1 - w)))
    logits = np.array(logits)
    return {"pbo": float((logits <= 0).mean()), "logits": logits, "n_splits": logits.size}
