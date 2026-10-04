"""research/optimization/purged_cv.py -- catalog C-ML3."""

from __future__ import annotations

from math import comb

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.optimization.purged_cv import (
    combinatorial_purged_splits,
    n_backtest_paths,
    purged_kfold,
    purged_train_indices,
)


def _labels(n=100, horizon=5):
    t0 = np.arange(n)
    return t0, np.minimum(t0 + horizon, n - 1)


def _overlap(t0, t1, train, test):
    start, end = t0[test].min(), t1[test].max()
    return np.any((t0[train] <= end) & (t1[train] >= start))


def test_no_training_label_overlaps_its_test_fold():
    t0, t1 = _labels()
    for train, test in purged_kfold(t0, t1, n_splits=5):
        assert not _overlap(t0, t1, train, test)
        assert np.intersect1d(train, test).size == 0


def test_purge_removes_exactly_the_overlapping_labels_before_the_fold():
    t0, t1 = _labels(n=40, horizon=3)
    test = np.arange(20, 30)
    train = purged_train_indices(t0, t1, test)
    # Labels starting at 17..19 end at 20..22, inside the test span: purged.
    assert 16 in train and not set(range(17, 20)) & set(train)
    # Labels starting after the test span's last label end (32) survive.
    assert set(range(33, 40)) <= set(train)


def test_embargo_drops_the_observations_right_after_the_fold():
    t0 = np.arange(50)
    t1 = t0.copy()  # one-bar labels: no purge needed
    train = purged_train_indices(t0, t1, np.arange(10, 20), embargo=3)
    assert not {20, 21, 22} & set(train) and 23 in train and 9 in train


def test_embargo_pct_is_a_share_of_the_sample():
    t0 = np.arange(100)
    splits = purged_kfold(t0, t0.copy(), n_splits=4, embargo_pct=0.05)
    train, _test = splits[0]
    assert set(range(25, 30)).isdisjoint(train) and 30 in train


def test_cpcv_split_and_path_counts():
    t0, t1 = _labels(n=60, horizon=1)
    splits = combinatorial_purged_splits(t0, t1, n_groups=6, k_test=2)
    assert len(splits) == comb(6, 2) == 15
    assert n_backtest_paths(6, 2) == 5 == 2 / 6 * comb(6, 2)
    # Each group is tested exactly phi times -- one per backtest path.
    counts = np.zeros(6, dtype=int)
    for _, chosen, _ in splits:
        counts[list(chosen)] += 1
    assert set(counts) == {5}


def test_cpcv_purges_around_every_test_group():
    t0, t1 = _labels(n=60, horizon=4)
    for train, _, test in combinatorial_purged_splits(
        t0, t1, n_groups=6, k_test=2, embargo_pct=0.02
    ):
        for g_start in np.split(np.sort(test), np.where(np.diff(np.sort(test)) != 1)[0] + 1):
            assert not _overlap(t0, t1, train, g_start)


@pytest.mark.parametrize(
    "call",
    [
        lambda t0, t1: purged_kfold(t0, t1, n_splits=1),
        lambda t0, t1: purged_kfold(t0, t1, n_splits=3, embargo_pct=1.0),
        lambda t0, t1: n_backtest_paths(4, 4),
        lambda t0, t1: combinatorial_purged_splits(t0, t1, n_groups=200, k_test=1),
        lambda t0, t1: purged_kfold(t0[::-1], t1[::-1], n_splits=3),
        lambda t0, t1: purged_kfold(t0, t0 - 1, n_splits=3),
    ],
)
def test_bad_inputs_are_rejected(call):
    t0, t1 = _labels(n=20)
    with pytest.raises(ConfigurationError):
        call(t0, t1)
