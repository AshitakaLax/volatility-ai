"""The tier calibration in tools/build_proxy_reports.py: thresholds set by
frequency, with ties kept on one side of a threshold."""

from __future__ import annotations

from tools import build_proxy_reports as B


def test_a_tie_is_not_taken_whole_into_the_higher_tier():
    # 40% score below 0.1, 15% exactly 0.1, 45% above: the top 50% would
    # grow to 60% by taking the tie, and 45% is nearer.
    scores = [0.0] * 40 + [0.1] * 15 + [0.2 + i / 1000 for i in range(45)]
    threshold = B.threshold_at(scores, 0.50)
    assert 0.1 < threshold < 0.2
    assert sum(s >= threshold for s in scores) == 45


def test_the_tie_goes_up_when_that_is_nearer():
    scores = [0.0] * 45 + [0.1] * 15 + [0.2] * 40
    threshold = B.threshold_at(scores, 0.50)
    assert sum(s >= threshold for s in scores) == 55


def test_no_score_sits_on_a_threshold():
    scores = [round(i / 97, 4) for i in range(97)] * 3
    for threshold in B.thresholds_for(scores, B.TIER_SHARES):
        assert threshold not in scores


def test_the_shares_follow_the_plan_on_continuous_scores():
    scores = [i / 1000 for i in range(1000)]
    thresholds = B.thresholds_for(scores, B.TIER_SHARES)
    assert thresholds[0] < thresholds[1] < thresholds[2]
    assert B.tier_shares(scores, thresholds) == [0.5, 0.25, 0.15, 0.1]
