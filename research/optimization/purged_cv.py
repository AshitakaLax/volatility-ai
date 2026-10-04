"""
Purged k-fold, embargo and combinatorial purged cross-validation (CPCV)
-- catalog C-ML3 (docs/research/correction-strategies.md, ML3).

Source: Lopez de Prado, *Advances in Financial Machine Learning* (2018),
ch. 7 (PurgedKFold) and ch. 12 (CPCV); the same method as
eslazarev/purged-cross-validation.

A label that spans [t0, t1] leaks into any test fold its span overlaps,
because the training row then "knows" part of the test period's
outcome. So:

  PURGE    drop every training observation whose [t0, t1] overlaps the
           test fold's time span [min t0, max t1].
  EMBARGO  also drop the `embargo` observations immediately after the test
           fold (embargo = round(embargo_pct * n)), because serial
           correlation lets the test period's information leak forward.

CPCV splits the observations into `n_groups` contiguous groups and tests on
every combination of `k_test` groups, purging and embargoing around each
test group. That gives C(N, k) splits, and each group is tested
C(N-1, k-1) times, which is also the number of distinct backtest paths:
phi = k / N * C(N, k) = C(N-1, k-1).

Inputs are aligned arrays: observation i's label starts at t0[i] and ends
at t1[i] (any orderable type: bar positions or timestamps), sorted by
t0. Outputs are integer index arrays.
"""

from __future__ import annotations

from itertools import combinations
from math import comb

import numpy as np

from engine.core.exceptions import ConfigurationError


def _check(t0, t1) -> tuple[np.ndarray, np.ndarray]:
    t0, t1 = np.asarray(t0), np.asarray(t1)
    if t0.shape != t1.shape or t0.ndim != 1 or t0.size == 0:
        raise ConfigurationError("t0 and t1 must be equal-length 1-D arrays")
    if np.any(t1 < t0):
        raise ConfigurationError("every label must end at or after it starts (t1 >= t0)")
    if np.any(t0[1:] < t0[:-1]):
        raise ConfigurationError("observations must be sorted by t0")
    return t0, t1


def _embargo_size(n: int, embargo_pct: float) -> int:
    if not 0 <= embargo_pct < 1:
        raise ConfigurationError(f"embargo_pct must be in [0, 1), got {embargo_pct}")
    return round(embargo_pct * n)


def purged_train_indices(t0, t1, test_idx, embargo: int = 0) -> np.ndarray:
    """Training indices for one test set: every observation outside the
    test set whose label does not overlap any contiguous block of the test
    set, minus `embargo` observations after each block."""
    t0, t1 = _check(t0, t1)
    n = t0.size
    test_idx = np.unique(np.asarray(test_idx, dtype=int))
    keep = np.ones(n, dtype=bool)
    keep[test_idx] = False
    # Purge and embargo around each contiguous block of the test set.
    blocks = np.split(test_idx, np.where(np.diff(test_idx) != 1)[0] + 1)
    for block in blocks:
        if block.size == 0:
            continue
        start, end = t0[block[0]], t1[block].max()
        overlaps = (t0 <= end) & (t1 >= start)
        keep &= ~overlaps
        last = block[-1]
        keep[last + 1 : min(n, last + 1 + embargo)] = False
    return np.flatnonzero(keep)


def purged_kfold(t0, t1, n_splits: int, embargo_pct: float = 0.0):
    """[(train_idx, test_idx), ...] over `n_splits` contiguous test folds."""
    t0, t1 = _check(t0, t1)
    if not (isinstance(n_splits, int) and 2 <= n_splits <= t0.size):
        raise ConfigurationError(f"n_splits must be an integer in [2, {t0.size}], got {n_splits!r}")
    embargo = _embargo_size(t0.size, embargo_pct)
    folds = np.array_split(np.arange(t0.size), n_splits)
    return [(purged_train_indices(t0, t1, test, embargo), test) for test in folds]


def n_backtest_paths(n_groups: int, k_test: int) -> int:
    """phi[N, k] = k / N * C(N, k) = C(N - 1, k - 1)."""
    if not 1 <= k_test < n_groups:
        raise ConfigurationError(f"need 1 <= k_test < n_groups, got {k_test}, {n_groups}")
    return comb(n_groups - 1, k_test - 1)


def combinatorial_purged_splits(t0, t1, n_groups: int, k_test: int, embargo_pct: float = 0.0):
    """[(train_idx, test_groups, test_idx), ...] for every C(N, k) choice of
    `k_test` test groups out of `n_groups` contiguous groups."""
    t0, t1 = _check(t0, t1)
    n_backtest_paths(n_groups, k_test)  # validates the pair
    if n_groups > t0.size:
        raise ConfigurationError(f"n_groups ({n_groups}) exceeds the observations ({t0.size})")
    embargo = _embargo_size(t0.size, embargo_pct)
    groups = np.array_split(np.arange(t0.size), n_groups)
    splits = []
    for chosen in combinations(range(n_groups), k_test):
        test = np.concatenate([groups[g] for g in chosen])
        splits.append((purged_train_indices(t0, t1, test, embargo), chosen, test))
    return splits
