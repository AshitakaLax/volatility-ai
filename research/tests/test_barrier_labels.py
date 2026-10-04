"""research/ml/barrier_labels.py -- catalog C-ML1."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.ml.barrier_labels import (
    ols_slope_tvalue,
    trend_scanning_labels,
    triple_barrier_labels,
)


def test_upper_barrier_first_is_plus_one():
    closes = pd.Series([100, 101, 103, 106, 90, 80], dtype=float)
    out = triple_barrier_labels(closes, [0], upper=0.05, lower=0.05, max_hold=5)
    row = out.iloc[0]
    assert (row.t1, row.barrier, row.label) == (3, "upper", 1)
    assert row.ret == pytest.approx(0.06)


def test_lower_barrier_first_is_minus_one():
    closes = pd.Series([100, 99, 94, 110], dtype=float)
    row = triple_barrier_labels(closes, [0], upper=0.05, lower=0.05, max_hold=3).iloc[0]
    assert (row.t1, row.barrier, row.label) == (2, "lower", -1)


def test_vertical_barrier_labels_by_sign_or_zero():
    closes = pd.Series([100, 101, 102, 101.5], dtype=float)
    signed = triple_barrier_labels(closes, [0], upper=0.1, lower=0.1, max_hold=3).iloc[0]
    assert (signed.t1, signed.barrier, signed.label) == (3, "vertical", 1)
    zero = triple_barrier_labels(closes, [0], upper=0.1, lower=0.1, max_hold=3, vertical="zero")
    assert zero.iloc[0].label == 0


def test_barrier_touch_at_exactly_the_level_counts():
    closes = pd.Series([100, 105, 90], dtype=float)
    assert (
        triple_barrier_labels(closes, [0], upper=0.05, lower=0.05, max_hold=2).iloc[0].barrier
        == "upper"
    )


def test_a_disabled_barrier_is_ignored_and_the_vertical_clips_at_the_end():
    closes = pd.Series([100, 50, 40, 30], dtype=float)
    row = triple_barrier_labels(closes, [0], upper=0.05, lower=None, max_hold=10).iloc[0]
    assert (row.t1, row.barrier, row.label) == (3, "vertical", -1)


def test_events_without_a_following_bar_are_skipped():
    closes = pd.Series([100, 101, 102], dtype=float)
    out = triple_barrier_labels(closes, [0, 2, 5], upper=0.5, lower=0.5, max_hold=1)
    assert list(out.t0) == [0]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"upper": 0.0, "lower": 0.1, "max_hold": 3},
        {"upper": 0.1, "lower": 1.0, "max_hold": 3},
        {"upper": 0.1, "lower": 0.1, "max_hold": 0},
        {"upper": 0.1, "lower": 0.1, "max_hold": 3, "vertical": "drop"},
    ],
)
def test_bad_barrier_parameters_are_rejected(kwargs):
    with pytest.raises(ConfigurationError):
        triple_barrier_labels(pd.Series([1.0, 2.0]), [0], **kwargs)


def test_slope_tvalue_matches_textbook_ols():
    rng = np.random.default_rng(2)
    y = 0.3 * np.arange(20) + rng.normal(0, 1, 20)
    x = np.arange(20, dtype=float)
    design = np.column_stack([np.ones(20), x])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ beta
    cov = (resid @ resid / 18) * np.linalg.inv(design.T @ design)
    assert ols_slope_tvalue(y) == pytest.approx(beta[1] / math.sqrt(cov[1, 1]))


def test_perfect_lines_give_infinite_tvalues_and_flat_gives_zero():
    assert ols_slope_tvalue([1, 2, 3, 4]) == math.inf
    assert ols_slope_tvalue([4, 3, 2, 1]) == -math.inf
    assert ols_slope_tvalue([5, 5, 5]) == 0.0


def test_trend_scanning_picks_the_strongest_span_and_its_sign():
    rng = np.random.default_rng(5)
    up = np.linspace(100, 110, 30) + rng.normal(0, 0.2, 30)
    down = np.linspace(110, 95, 30) + rng.normal(0, 0.2, 30)
    labels = trend_scanning_labels(pd.Series(np.concatenate([up, down])), spans=[5, 10, 20])
    assert labels.iloc[0].label == 1
    assert labels.iloc[35].label == -1
    first = labels.iloc[0]
    tvals = {L: ols_slope_tvalue(np.concatenate([up, down])[:L]) for L in (5, 10, 20)}
    best = max(tvals, key=lambda L: abs(tvals[L]))
    assert first.t1 == best - 1 and first.t_value == pytest.approx(tvals[best])


def test_trend_scanning_stops_where_no_span_fits():
    labels = trend_scanning_labels(pd.Series(np.arange(10, dtype=float)), spans=[4, 6])
    assert labels.t0.max() == 6  # bar 6 is the last with 4 bars ahead (6..9)


def test_trend_scanning_rejects_short_spans():
    with pytest.raises(ConfigurationError):
        trend_scanning_labels(pd.Series(np.arange(10, dtype=float)), spans=[2])
