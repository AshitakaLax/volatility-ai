"""Tests for tools/measure_vol_signal.py.

The statistics here decide whether a signal earns a knob, so the parts
that could be quietly wrong are the ones worth pinning:

  * `partial_spearman` -- the number the whole conclusion rests on. It
    nearly produced the wrong recommendation when read against only one
    control, so its behaviour under a perfectly-explanatory control and
    an orthogonal one is pinned explicitly.
  * predictor/target alignment -- a target must be the NEXT session. An
    off-by-one here would leak the future into the predictor and make a
    useless signal look excellent.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tools.measure_vol_signal import (
    build,
    partial_spearman,
    spearman,
)


def _series(values, start="2024-01-02"):
    idx = pd.date_range(start, periods=len(values), freq="D").date
    return pd.Series(values, index=idx)


# -- spearman ----------------------------------------------------------


def test_spearman_is_one_for_a_monotonic_relationship():
    a = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    b = _series([10.0, 20.0, 30.0, 40.0, 50.0])
    assert spearman(a, b) == pytest.approx(1.0)


def test_spearman_is_rank_based_not_value_based():
    """The point of using rank correlation: a monotonic but wildly
    non-linear relationship still scores 1.0."""
    a = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    b = _series([1.0, 4.0, 9.0, 1000.0, 1e9])
    assert spearman(a, b) == pytest.approx(1.0)


def test_spearman_is_minus_one_when_reversed():
    a = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert spearman(a, _series([5.0, 4.0, 3.0, 2.0, 1.0])) == pytest.approx(-1.0)


def test_spearman_returns_nan_rather_than_crashing_on_too_few_points():
    assert np.isnan(spearman(_series([1.0]), _series([2.0])))


def test_spearman_drops_rows_where_either_side_is_missing():
    a = _series([1.0, 2.0, np.nan, 4.0, 5.0])
    b = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert spearman(a, b) == pytest.approx(1.0)


# -- partial_spearman: the number the conclusion rests on ---------------


def test_a_candidate_that_merely_restates_the_control_scores_near_zero():
    """THE case that decided this investigation. The implied 5/60 ratio
    scored +0.31 against a weak control and +0.00 against a strong one --
    it was re-encoding information the incumbent already had. A candidate
    that is the control plus independent noise carries nothing about the
    target beyond what the control already said, so it must score ~0."""
    rng = np.random.default_rng(0)
    control_values = rng.normal(size=400)
    control = _series(control_values)
    target = _series(control_values + rng.normal(scale=0.5, size=400))
    # Correlated with the control, but its only extra content is noise
    # unrelated to the target.
    candidate = _series(control_values + rng.normal(scale=0.5, size=400))
    assert abs(partial_spearman(target, candidate, control)) < 0.1


def test_a_candidate_identical_to_the_control_is_undefined_not_zero():
    """Mathematically 0/0. Returning 0.0 would read as 'measured, adds
    nothing' when the truth is 'the question cannot be asked'."""
    rng = np.random.default_rng(3)
    control = _series(rng.normal(size=200))
    target = _series(rng.normal(size=200))
    assert np.isnan(partial_spearman(target, control.copy(), control))


def test_a_candidate_orthogonal_to_the_control_keeps_its_correlation():
    """The mirror case: a candidate carrying genuinely independent
    information must survive the control roughly intact."""
    rng = np.random.default_rng(1)
    control = _series(rng.normal(size=400))
    extra = _series(rng.normal(size=400))
    target = _series(control.to_numpy() + extra.to_numpy())
    raw = spearman(target, extra)
    partial = partial_spearman(target, extra, control)
    assert partial > 0.5
    assert partial > raw, "controlling for an independent factor should sharpen it"


def test_partial_is_nan_when_the_control_explains_the_target_perfectly():
    """Guard against a divide-by-zero producing a confident-looking
    number out of a degenerate denominator."""
    control = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    target = control.copy()
    candidate = _series([2.0, 1.0, 5.0, 3.0, 4.0])
    assert np.isnan(partial_spearman(target, candidate, control))


# -- alignment: targets must be the NEXT session ------------------------


def _frames(n=200):
    rng = np.random.default_rng(7)
    idx = pd.date_range("2020-01-01", periods=n, freq="D").date
    primary = pd.DataFrame(
        {
            "vol": rng.uniform(1, 5, n),
            "open_vol": rng.uniform(1, 6, n),
            "close": rng.uniform(10, 20, n),
        },
        index=idx,
    )
    signal = pd.DataFrame(
        {
            "vol": rng.uniform(1, 5, n),
            "open_vol": rng.uniform(1, 6, n),
            "close": rng.uniform(10, 30, n),
        },
        index=idx,
    )
    return primary, signal


def test_the_target_is_the_next_sessions_value_not_this_ones():
    """An off-by-one here would leak the future into the predictor and
    make any signal look excellent."""
    primary, signal = _frames()
    frame = build(primary, signal)
    # target_vol at row i must equal vol at row i+1.
    assert frame["target_vol"].iloc[0] == pytest.approx(frame["vol"].iloc[1])
    assert frame["target_open_vol"].iloc[5] == pytest.approx(frame["open_vol"].iloc[6])
    # The final row has no next session.
    assert np.isnan(frame["target_vol"].iloc[-1])


def test_predictors_use_only_backward_windows():
    """rolling() is backward by default, but a lookahead here would be
    invisible in the output and fatal to the conclusion."""
    primary, signal = _frames()
    frame = build(primary, signal)
    # A 5-window mean cannot exist before 5 observations.
    assert frame["rv_fast"].iloc[:4].isna().all()
    assert frame["rv_slow"].iloc[:59].isna().all()
    # And it must equal the mean of the trailing window, inclusive of today.
    expected = frame["vol"].iloc[0:5].mean()
    assert frame["rv_fast"].iloc[4] == pytest.approx(expected)


def test_build_intersects_the_two_instruments_calendars():
    """A session present for only one instrument must be dropped, not
    forward-filled -- an implied-vol reading from a different day is not
    an as-of join, it is a fabrication."""
    primary, signal = _frames(50)
    signal = signal.iloc[10:]
    frame = build(primary, signal)
    assert len(frame) == 40
    assert frame.index[0] == signal.index[0]


def test_the_implied_change_column_is_a_percentage_change():
    primary, signal = _frames(30)
    frame = build(primary, signal)
    expected = (signal["close"].iloc[3] / signal["close"].iloc[2] - 1) * 100.0
    assert frame["iv_chg"].iloc[3] == pytest.approx(expected)
