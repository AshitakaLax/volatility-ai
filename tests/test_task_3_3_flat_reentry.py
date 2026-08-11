import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage


def _data():
    return pd.DataFrame(
        {"close": [100.0, 99.0, 101.0, 102.0, 98.0]},
        index=pd.date_range("2024-01-01", periods=5, freq="D"),
    )


def test_default_stale_reference_policy_is_backward_compatible():
    controller = OptimizationController(_data())
    baseline = controller.run_sweep(
        [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}]
    )
    explicit = controller.run_sweep(
        [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}],
        on_flat_reentry="stale_reference",
    )
    pd.testing.assert_frame_equal(baseline, explicit)


def test_invalid_flat_reentry_policy_is_rejected():
    controller = OptimizationController(_data())
    with pytest.raises(ValueError, match="on_flat_reentry"):
        controller.run_sweep(
            [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}],
            on_flat_reentry="invalid",
        )


def test_reset_to_market_allows_reentry_after_flat_exit():
    class ExitImmediatelySizing(FixedPortfolioPercentage):
        def calculate_trade_value(self, total_equity, current_price, current_dd=0.0):
            return super().calculate_trade_value(total_equity, current_price, current_dd)

    controller = OptimizationController(_data())
    result = controller.run_sweep(
        [0.01], [0.01], ExitImmediatelySizing, [{"percentage": 0.01}],
        on_flat_reentry="reset_to_market",
    )
    assert not result.empty
