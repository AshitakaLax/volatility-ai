"""research/catalog/excluded.py -- strategies the ledger excludes."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.excluded import (
    creation_redemption_action,
    daily_reset_path,
    hysteresis_switch,
    ib_hft_signals,
    ib_pairs_long_only,
    long_vol_sleeve,
    martingale_path,
    martingale_ruin_probability,
    rebalanced_mix,
    regime_sleeve_returns,
)


def _pair(n=300, seed=0):
    rng = np.random.default_rng(seed)
    b = 50 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
    a = 2 * b * np.exp(rng.normal(0, 0.003, n))
    return a, b


def test_ib_hft_signals_follow_the_source_state_machine():
    a, b = _pair()
    out = ib_hft_signals(a, b, window=60)
    assert np.isnan(out["beta"].iloc[58]) and out["beta"].iloc[60] == pytest.approx(
        a[1:61].mean() / b[1:61].mean()
    )
    pos = out["position"].to_numpy()
    assert set(np.unique(pos)) <= {-1, 0, 1}
    assert not np.any(np.abs(np.diff(pos)) == 2)  # flips go through flat
    t = int(np.flatnonzero(pos == 1)[0])
    assert out["buy"].iloc[t] and a[t] > out["beta"].iloc[t] * b[t]  # buys A when RICH
    fixed = ib_hft_signals(a, b, window=60, fixed_labels=True)
    t2 = int(np.flatnonzero(fixed["position"].to_numpy() == 1)[0])
    assert a[t2] < fixed["beta"].iloc[t2] * b[t2]
    lo = ib_pairs_long_only(a, b, 60)
    assert set(lo.unique()) <= {0, 1}
    with pytest.raises(ConfigurationError):
        ib_hft_signals(a, b[:-1])


def test_rebalanced_mix_resets_weights():
    v = rebalanced_mix([0.1, 0.0, 0.0], [0.0, 0.0, 0.0], weight_a=0.5, rebalance_every=2)
    assert v.tolist() == pytest.approx([1.05, 1.05, 1.05])
    v2 = rebalanced_mix([0.1, 0.1], [-0.1, -0.1], weight_a=0.5, rebalance_every=1)
    assert v2.iloc[-1] == pytest.approx(1.0 * 1.0 * 1.0)  # 0.5*1.1 + 0.5*0.9 = 1 each step


def test_daily_reset_decay_and_regime_sleeve():
    r = np.tile([0.1, -1 / 11], 10)  # the underlying round-trips exactly
    assert np.prod(1 + r) == pytest.approx(1.0)
    assert daily_reset_path(r, -1)[-1] < 0.99 and daily_reset_path(r, 3)[-1] < 0.99
    s = regime_sleeve_returns([1, 0, None], [0.01, 0.02, 0.03], [-0.01, -0.02, -0.03])
    assert s.tolist() == [0.01, -0.02, 0.03]


def test_long_vol_sleeve_hysteresis_and_lag():
    assert hysteresis_switch([0.9, 1.05, 0.97, 0.9, 1.1], 1.0, 0.95).tolist() == [0, 1, 1, 0, 1]
    rets, held = long_vol_sleeve([0.9, 1.05, 0.97, 0.9], [0.1, 0.2, 0.3, 0.4])
    assert held.tolist() == [0, 0, 1, 1] and rets.tolist() == [0.0, 0.0, 0.3, 0.4]
    with pytest.raises(ConfigurationError):
        hysteresis_switch([1.0], 0.9, 1.0)


def test_martingale_path_and_exact_ruin_probability():
    path = martingale_path([0, 0, 1, 0, 0, 0], capital=7)
    assert path["stake"].tolist() == [1, 2, 4, 1, 2, 4]
    assert path["capital"].tolist() == [6, 4, 8, 7, 5, 1]
    assert martingale_path([0, 0, 0, 0], capital=7)["result"].iloc[-1] == "ruined"
    # brute force over all outcome sequences
    p, n, k = 0.45, 8, 3
    total = 0.0
    for code in range(2**n):
        bits = [(code >> i) & 1 for i in range(n)]
        run = best = 0
        for b in bits:
            run = run + 1 if b == 0 else 0
            best = max(best, run)
        if best >= k:
            total += np.prod([p if b else 1 - p for b in bits])
    assert martingale_ruin_probability(p, n, k) == pytest.approx(total)


def test_creation_redemption():
    c = creation_redemption_action(
        100.10, 100.0, unit_shares=50_000, fixed_fee=500, variable_cost=0.0005
    )
    assert c["action"] == "create" and c["profit"] == pytest.approx(5000 - 500 - 2500)
    assert creation_redemption_action(99.85, 100.0)["action"] == "redeem"
    assert creation_redemption_action(100.02, 100.0)["action"] == "none"
