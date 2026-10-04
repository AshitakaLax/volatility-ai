"""research/strategies/tactical_allocation.py -- catalog C-E2."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.tactical_allocation import faber_targets, held_weights, month_end_days


def _closes(n=320):
    idx = pd.bdate_range("2024-01-01", periods=n)
    up = np.linspace(100, 160, n)  # steady uptrend: fast MA above slow
    down = np.linspace(160, 100, n)  # steady downtrend: fast below slow
    return pd.DataFrame({"UP": up, "DOWN": down}, index=idx)


def test_month_ends_are_the_last_trading_day_of_each_month():
    idx = pd.bdate_range("2024-01-01", "2024-03-31")
    ends = month_end_days(idx)
    assert list(ends.strftime("%Y-%m-%d")) == ["2024-01-31", "2024-02-29", "2024-03-29"]


def test_targets_are_one_over_n_when_fast_is_above_slow_else_cash():
    targets = faber_targets(_closes())
    live = targets.dropna()
    assert (live["UP"] == 0.5).all()
    assert (live["DOWN"] == 0.0).all()


def test_no_target_before_the_slow_window_fills():
    targets = faber_targets(_closes())
    first_valid = _closes().index[199]
    assert targets.loc[targets.index < first_valid].isna().all().all()


def test_targets_change_only_at_month_ends_and_apply_from_the_next_session():
    closes = _closes()
    daily = held_weights(closes)
    changes = daily["UP"].diff().fillna(0).ne(0)
    ends = set(month_end_days(closes.index))
    for day in daily.index[changes]:
        prev = daily.index[daily.index.get_loc(day) - 1]
        assert prev in ends  # the decision was made at the previous month-end close


def test_bad_windows_are_rejected():
    with pytest.raises(ConfigurationError):
        faber_targets(_closes(), fast=200, slow=20)
