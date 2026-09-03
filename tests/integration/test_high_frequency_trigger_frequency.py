"""Integration test for HighFrequencyLocalReferenceSizing.

The unit tests (tests/unit/test_high_frequency_sizing.py) prove the
trigger/sizing mathematics in isolation. This proves the qualitative
claim the whole strategy exists for -- "this retriggers on chop; the
default last_buy_price-only trigger structurally cannot" -- as a real
assertion against OptimizationController.run_sweep, on IDENTICAL data,
step, and profit_target for both strategies. A synthetic sideways-chop
fixture is deliberately used (not a trending one): the default trigger
needs a fresh decline below its last fill to ever buy again, so a
market that oscillates within a band without trending is exactly the
condition under which the two strategies' trade counts should diverge
most starkly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from optimization_controller import OptimizationController
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from src.size_calculators import FixedPortfolioPercentage


def _chop_fixture(n: int = 2000, seed: int = 7) -> pd.DataFrame:
    """Price oscillates within a band around 100 -- no sustained trend
    in either direction, via a bounded sine plus small noise."""
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    price = 100.0 + 3.0 * np.sin(idx / 15.0) + rng.normal(0, 0.05, size=n)
    ts = pd.date_range("2026-01-02 14:30", periods=n, freq="1min", tz="UTC")
    return pd.DataFrame(
        {
            "open": price,
            "high": price * 1.0004,
            "low": price * 0.9996,
            "close": price,
            "volume": 10_000,
        },
        index=ts,
    )


def test_hf_strategy_trades_materially_more_often_on_chop_than_the_default_trigger():
    df = _chop_fixture()
    controller = OptimizationController(historical_data=df)
    common = {"grid_steps": [0.005], "profit_targets": [0.01]}

    default_trigger = controller.run_sweep(
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.02}],
        **common,
    ).iloc[0]

    hf_trigger = controller.run_sweep(
        strategy_class=HighFrequencyLocalReferenceSizing,
        strategy_params_grid=[{"per_lot_pct": 0.005, "lookback_days": 0.01, "bars_per_day": 390}],
        **common,
    ).iloc[0]

    assert hf_trigger["Trade Count"] > default_trigger["Trade Count"] * 3, (
        f"expected the local-reference trigger to retrigger on chop far more often "
        f"than the last-buy-price-only default; got hf={hf_trigger['Trade Count']} "
        f"vs default={default_trigger['Trade Count']}"
    )


def test_hf_strategy_completes_a_real_sweep_without_errors():
    df = _chop_fixture()
    controller = OptimizationController(historical_data=df)
    results = controller.run_sweep(
        grid_steps=[0.003],
        profit_targets=[0.006],
        strategy_class=HighFrequencyLocalReferenceSizing,
        strategy_params_grid=[{"per_lot_pct": 0.005, "lookback_days": 0.01, "bars_per_day": 390}],
    )
    assert len(results) == 1
    assert "error" not in results.columns, results.to_dict("records")
    assert results["Strategy"].iloc[0] == "HighFrequencyLocalReferenceSizing"
