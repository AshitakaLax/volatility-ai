"""research/strategies/microstructure.py -- catalog C-MS1, C-MS2, C-MS5,
C-MS6, C-MS7, C-MM4, C-MM5."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.microstructure import (
    QueuePositionEstimator,
    abdi_ranaldo,
    amihud_illiquidity,
    bvc_buy_fraction,
    corwin_schultz,
    depth_imbalance,
    kyle_lambda,
    letf_rebalance_demand,
    micro_price,
    ofi,
    ofi_events,
    point_of_control,
    price_buckets,
    roll_spread,
    standardized,
    tpo_profile,
    value_area,
    volume_buckets,
    volume_profile,
    vpin,
)

# ---------------------------------------------------------------- C-MS1


def test_ofi_branches_follow_cont_kukanov_stoikov():
    # Bid size grows at an unchanged price: +delta. Ask unchanged: 0.
    assert ofi_events([10, 10], [100, 130], [11, 11], [50, 50]).tolist() == [30.0]
    # Bid price rises: + the new bid size. Ask price rises: + the old ask size.
    assert ofi_events([10, 10.1], [100, 40], [11, 11.1], [50, 70]).tolist() == [40 + 50]
    # Bid price falls: - the old bid size. Ask price falls: - the new ask size.
    assert ofi_events([10, 9.9], [100, 40], [11, 10.9], [50, 70]).tolist() == [-100 - 70]


def test_ofi_sums_its_events():
    bp, bq, ap, aq = [10, 10, 10.1], [100, 120, 80], [11, 11, 11], [50, 40, 40]
    assert ofi(bp, bq, ap, aq) == pytest.approx(ofi_events(bp, bq, ap, aq).sum())


# ---------------------------------------------------------------- C-MS2


def test_micro_price_leans_toward_the_thin_side():
    assert micro_price(100.0, 100.02, bid_qty=300, ask_qty=100) == pytest.approx(
        (100 * 100 + 100.02 * 300) / 400
    )
    assert micro_price(100.0, 100.02, 100, 100) == pytest.approx(100.01)


def test_depth_imbalance_and_standardisation():
    assert depth_imbalance(300, 100) == pytest.approx(0.5)
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    z = standardized(s, 4)
    assert z.iloc[-1] == pytest.approx((4 - 2.5) / np.std([1, 2, 3, 4]))


# ---------------------------------------------------------------- C-MS5


def test_roll_recovers_a_planted_bid_ask_bounce():
    rng = np.random.default_rng(0)
    mid = 100 + np.cumsum(rng.normal(0, 0.01, 50_000))
    prices = mid + 0.05 * rng.choice([-1, 1], size=mid.size)  # half-spread 0.05
    assert roll_spread(prices) == pytest.approx(0.10, rel=0.05)


def test_roll_is_zero_without_negative_autocovariance():
    assert roll_spread(np.arange(10, dtype=float) ** 2) == 0.0


def test_corwin_schultz_matches_its_formula():
    h, lo = np.array([101.0, 102.0]), np.array([99.0, 100.5])
    beta = math.log(101 / 99) ** 2 + math.log(102 / 100.5) ** 2
    gamma = math.log(102 / 99) ** 2
    k = 3 - 2 * math.sqrt(2)
    alpha = (math.sqrt(2 * beta) - math.sqrt(beta)) / k - math.sqrt(gamma / k)
    expected = max(0.0, 2 * (math.exp(alpha) - 1) / (1 + math.exp(alpha)))
    assert corwin_schultz(h, lo)[0] == pytest.approx(expected)


def test_corwin_schultz_floors_negative_estimates_at_zero():
    assert corwin_schultz([101.0, 110.0], [100.0, 109.0])[0] == 0.0


def test_abdi_ranaldo_matches_its_formula():
    h, lo, c = [101.0, 102.0, 101.5], [99.0, 100.0, 99.5], [100.5, 100.2, 101.0]
    lh, ll, lc = np.log(h), np.log(lo), np.log(c)
    eta = (lh + ll) / 2
    product = np.mean((lc[:-1] - eta[:-1]) * (lc[:-1] - eta[1:]))
    assert abdi_ranaldo(h, lo, c) == pytest.approx(2 * math.sqrt(product) if product > 0 else 0.0)


def test_amihud_and_kyle_lambda():
    assert amihud_illiquidity([0.01, -0.02], [1000, 2000]) == pytest.approx(
        (0.01 / 1000 + 0.02 / 2000) / 2
    )
    rng = np.random.default_rng(1)
    flow = rng.normal(0, 1000, 5000)
    dp = 2e-5 * flow + rng.normal(0, 0.005, 5000)
    assert kyle_lambda(dp, flow) == pytest.approx(2e-5, rel=0.05)


def test_bvc_buy_fraction():
    assert bvc_buy_fraction(0.0, 0.1) == 0.5
    assert bvc_buy_fraction(0.3, 0.1) > 0.99
    assert bvc_buy_fraction(-0.1, 0.1) == pytest.approx(1 - 0.8413447, abs=1e-6)


# ---------------------------------------------------------------- C-MS6


def test_letf_rebalance_demand_follows_cheng_madhavan():
    assert letf_rebalance_demand(1e9, 3.0, 0.02) == pytest.approx(
        1e9 * 6 * 0.02
    )  # buys after up days
    assert letf_rebalance_demand(1e9, -1.0, 0.02) == pytest.approx(
        1e9 * 2 * 0.02
    )  # inverse: same direction
    assert letf_rebalance_demand(1e9, 1.0, 0.05) == 0.0
    assert letf_rebalance_demand(1e9, 3.0, -0.03) < 0


# ---------------------------------------------------------------- C-MS7


def test_buckets_and_volume_profile_reproduce_the_notebook():
    closes, vols = [100.1, 100.3, 100.6, 100.3], [10, 20, 30, 40]
    edges = price_buckets(closes, 0.25)
    assert edges[0] == pytest.approx(100.0)
    assert edges[-1] >= max(closes)
    profile = volume_profile(closes, vols, 0.25)
    assert profile.sum() == pytest.approx(100)
    assert profile.loc[100.375] == pytest.approx(60)  # both 100.3 closes
    assert point_of_control(profile) == pytest.approx(100.375)


def test_tpo_fills_every_bucket_between_low_and_high():
    edges = np.arange(100.0, 101.25, 0.25)
    assert tpo_profile([100.9], [100.1], edges).tolist() == [1, 1, 1, 1]
    assert tpo_profile([100.2, 100.6], [100.1, 100.55], edges).tolist() == [1, 0, 1, 0]


def test_value_area_covers_seventy_percent_around_the_poc():
    profile = pd.Series([5, 10, 40, 20, 15, 10], index=[1, 2, 3, 4, 5, 6], dtype=float)
    lo, hi = value_area(profile)
    inside = profile.loc[lo:hi]
    assert inside.sum() >= 0.7 * profile.sum()
    assert lo <= point_of_control(profile) <= hi
    assert (lo, hi) == (3, 5)  # 40 -> +20 above -> +15 above (75 of 100)


# ---------------------------------------------------------------- C-MM4


def test_buckets_hold_exactly_the_bucket_volume_and_split_bars():
    buckets = volume_buckets([0.1, -0.1, 0.2], [70, 50, 90], bucket_volume=100)
    assert len(buckets) == 2  # 210 volume -> two full buckets, 10 left over
    assert [sum(v for _, v in b) for b in buckets] == pytest.approx([100, 100])
    assert buckets[0] == [(0.1, 70.0), (-0.1, 30.0)]


def test_vpin_is_low_for_balanced_flow_and_high_for_one_sided_flow():
    rng = np.random.default_rng(2)
    balanced = vpin(rng.choice([-0.01, 0.01], 5000), np.full(5000, 10.0), 100.0, n_buckets=50)
    one_sided = vpin(np.full(5000, 0.05), np.full(5000, 10.0), 100.0, n_buckets=50, sigma=0.01)
    assert balanced < 0.3 and one_sided > 0.99


def test_vpin_needs_enough_buckets():
    assert vpin([0.1] * 5, [10] * 5, 100.0, n_buckets=50) is None


# ---------------------------------------------------------------- C-MM5


def test_queue_probability_follows_rigtorp():
    est = QueuePositionEstimator(order_size=10, queue_ahead=30, level_size=100)
    assert est.probability() == pytest.approx(30 / (30 + 60))
    log_est = QueuePositionEstimator(10, 30, 100, prob="log")
    assert log_est.probability() == pytest.approx(
        math.log1p(30) / (math.log1p(30) + math.log1p(60))
    )
    sq = QueuePositionEstimator(10, 30, 100, power=2)
    assert sq.probability() == pytest.approx(900 / (900 + 3600))


def test_head_and_tail_probabilities_are_zero_and_one():
    assert QueuePositionEstimator(10, 0, 100).probability() == 0.0
    assert QueuePositionEstimator(10, 90, 100).probability() == 1.0


def test_cancellations_advance_us_by_p_times_the_decrease():
    est = QueuePositionEstimator(10, 30, 100)
    est.on_level_change(91)  # 9 cancelled, p = 1/3
    assert est.ahead == pytest.approx(27.0)
    est.on_level_change(120)  # additions join behind
    assert est.ahead == pytest.approx(27.0)


def test_trades_consume_the_queue_ahead_then_fill_us():
    est = QueuePositionEstimator(10, 30, 100)
    assert est.on_trade(25) == 0.0 and est.ahead == pytest.approx(5.0)
    assert est.on_trade(8) == pytest.approx(3.0) and est.ahead == 0.0
    assert est.on_trade(20) == pytest.approx(7.0) and est.filled == pytest.approx(10.0)


@pytest.mark.parametrize(
    "call",
    [
        lambda: ofi_events([1], [1], [1], [1]),
        lambda: micro_price(1, 2, 0, 0),
        lambda: corwin_schultz([1.0, 2.0], [2.0, 1.0]),
        lambda: kyle_lambda([1, 2, 3], [1, 1, 1]),
        lambda: price_buckets([1.0, 2.0], 0.0),
        lambda: value_area(pd.Series([0.0, 0.0])),
        lambda: volume_buckets([0.1], [1], 0.0),
        lambda: QueuePositionEstimator(10, 95, 100),
        lambda: QueuePositionEstimator(10, 30, 100, prob="cubic"),
    ],
)
def test_bad_inputs_are_rejected(call):
    with pytest.raises(ConfigurationError):
        call()
