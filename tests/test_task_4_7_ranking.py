import math

import pandas as pd

from optimization_controller import _rank_results


def test_ranking_handles_missing_nan_and_infinite_metrics():
    frame = pd.DataFrame(
        [
            {"Grid Step": 0.03, "Capital Velocity Index": float("nan")},
            {"Grid Step": 0.01, "Capital Velocity Index": 2.0},
            {"Grid Step": 0.02},
            {"Grid Step": 0.04, "Capital Velocity Index": float("inf")},
            {"Grid Step": 0.05, "Capital Velocity Index": -1.0},
        ]
    )
    ranked = _rank_results(frame)
    assert list(ranked["Grid Step"])[:2] == [0.01, 0.05]
    assert ranked.iloc[2]["Grid Step"] == 0.03
    assert ranked.iloc[3]["Grid Step"] == 0.02
    assert ranked.iloc[4]["Grid Step"] == 0.04


def test_ties_are_stable_and_preserve_input_order():
    frame = pd.DataFrame(
        [
            {"Grid Step": 0.02, "Capital Velocity Index": 1.0},
            {"Grid Step": 0.01, "Capital Velocity Index": 1.0},
            {"Grid Step": 0.03, "Capital Velocity Index": 2.0},
        ]
    )
    ranked = _rank_results(frame)
    assert list(ranked["Grid Step"]) == [0.03, 0.02, 0.01]


def test_missing_ranking_column_is_created_and_sortable():
    ranked = _rank_results(pd.DataFrame([{"Grid Step": 0.01}, {"Grid Step": 0.02}]))
    assert len(ranked) == 2
    assert "Capital Velocity Index" in ranked.columns
    assert all(math.isinf(float(value)) and value < 0 for value in ranked["Capital Velocity Index"])
