"""research/ml/info_bars.py -- catalog C-ML5."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.ml.info_bars import (
    dollar_bars,
    ffd_weights,
    frac_diff_ffd,
    tick_bars,
    tick_imbalance_bars,
    tick_rule,
    volume_bars,
)


def _rows(closes, volumes=None):
    closes = np.asarray(closes, dtype=float)
    volumes = np.ones(closes.size) if volumes is None else np.asarray(volumes, dtype=float)
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes + 0.1,
            "low": closes - 0.1,
            "close": closes,
            "volume": volumes,
        }
    )


def test_ffd_weights_follow_the_recursion():
    assert ffd_weights(0.5, threshold=0.05) == pytest.approx([1.0, -0.5, -0.125, -0.0625])
    assert ffd_weights(1.0, threshold=1e-8) == pytest.approx([1.0, -1.0])  # w_2 = 0
    assert ffd_weights(0.0) == pytest.approx([1.0])


def test_d_one_is_the_first_difference_and_d_zero_the_series():
    s = pd.Series([1.0, 3.0, 6.0, 10.0])
    pd.testing.assert_series_equal(frac_diff_ffd(s, 1.0, threshold=1e-8), s.diff())
    pd.testing.assert_series_equal(frac_diff_ffd(s, 0.0), s)


def test_ffd_applies_the_weights_to_the_trailing_window():
    s = pd.Series([1.0, 2.0, 4.0, 7.0, 11.0])
    w = ffd_weights(0.5, threshold=0.05)
    out = frac_diff_ffd(s, 0.5, threshold=0.05)
    assert out.iloc[:3].isna().all()
    assert out.iloc[3] == pytest.approx(w @ np.array([7.0, 4.0, 2.0, 1.0]))


def test_tick_bars_group_every_n_rows():
    bars = tick_bars(_rows(range(10)), 4)
    assert bars["rows"].tolist() == [4, 4]  # the last 2 rows do not complete a bar
    assert bars.iloc[0][["open", "close"]].tolist() == [0.0, 3.0]


def test_volume_bars_close_once_the_threshold_is_reached():
    bars = volume_bars(_rows([10, 11, 12, 13, 14], [30, 40, 50, 60, 70]), threshold=100)
    assert bars["volume"].tolist() == [120.0, 130.0]  # 30+40+50, then 60+70
    assert bars["rows"].tolist() == [3, 2]


def test_dollar_bars_use_price_times_volume():
    bars = dollar_bars(_rows([10, 20, 10, 50], [1, 1, 1, 1]), threshold=30)
    assert bars["rows"].tolist() == [2, 2]  # 10+20 = 30, then 10+50


def test_tick_rule_carries_the_previous_sign_on_no_change():
    assert tick_rule([10, 11, 11, 10, 10, 12]).tolist() == [1, 1, 1, -1, -1, 1]


def test_imbalance_bars_close_when_the_signed_run_crosses_the_threshold():
    # Fixed expectations: E[T] = 4, P[b=1] = 1 -> threshold 4 * |2*1 - 1| = 4.
    closes = [10, 11, 12, 13, 14, 13, 12, 11, 10, 9]
    bars = tick_imbalance_bars(_rows(closes), expected_ticks=4, p_buy=1.0)
    # b = +1 x5 then -1 x5. Bar 1: theta hits +4 after 4 rows. Bar 2 starts on
    # the fifth uptick (+1), then needs five downticks to reach -4: 6 rows.
    assert bars["rows"].tolist() == [4, 6]


def test_ewma_updates_change_the_next_threshold():
    closes = list(range(10, 40))  # every row an uptick
    # Threshold 8 * |2 * 0.75 - 1| = 4, so the first bar is 4 rows either way.
    fixed = tick_imbalance_bars(_rows(closes), expected_ticks=8, p_buy=0.75)
    assert fixed["rows"].tolist()[:2] == [4, 4]
    # alpha 0.5: E[T] -> 0.5*8 + 0.5*4 = 6, P -> 0.5*0.75 + 0.5*1 = 0.875,
    # next threshold 6 * |2 * 0.875 - 1| = 4.5 -> 5 rows.
    adapted = tick_imbalance_bars(_rows(closes), expected_ticks=8, p_buy=0.75, ewm_alpha=0.5)
    assert adapted["rows"].tolist()[:2] == [4, 5]


@pytest.mark.parametrize(
    "call",
    [
        lambda: ffd_weights(-0.1),
        lambda: tick_bars(_rows([1, 2]), 0),
        lambda: volume_bars(_rows([1, 2]), 0.0),
        lambda: tick_imbalance_bars(_rows([1, 2]), expected_ticks=0),
    ],
)
def test_bad_inputs_are_rejected(call):
    with pytest.raises(ConfigurationError):
        call()
