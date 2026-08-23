"""The no-loss guard is switchable (execution.enforce_no_loss).

The guard encodes a real retail edge -- a retail book is never FORCED
to liquidate the way an institution is, so declining to realize a loss
is genuinely available. The cost is that lots ride declines fully
marked to market. These tests pin that the switch actually changes
simulation behavior in the direction claimed, rather than merely
existing as a config field.

The scenario is deliberately the COST-FLOOR case: a profit target
below round-trip cost. That is the only situation the guard can fire
in, because sells are only ever attempted on lots whose target was
touched -- see test_disabling_the_guard_does_not_by_itself_sell_losers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.cost_models import SlippageCommissionModel
from src.risk_manager import RiskManager
from src.size_calculators import FixedPortfolioPercentage

INITIAL_CASH = 100_000.0


def _rising_series(bars: int = 400) -> pd.DataFrame:
    """A dip then a steady climb, so buys trigger early and their
    targets are comfortably touched later."""
    prices = [100.0]
    for i in range(1, bars):
        prices.append(prices[-1] * (0.995 if i < 20 else 1.001))
    index = pd.date_range("2024-01-02 14:30", periods=bars, freq="1min", tz="UTC")
    close = np.array(prices)
    return pd.DataFrame(
        {"open": close, "high": close * 1.0005, "low": close * 0.9995, "close": close},
        index=index,
    )


def _run(enforce: bool):
    """One simulation with a profit target far below round-trip cost, so
    every attempted sell trips the guard."""
    controller = OptimizationController(historical_data=_rising_series())
    return controller._simulate_single(
        step=0.002,
        target=0.001,  # 10bps gross, against 100bps round-trip cost below
        strategy_instance=FixedPortfolioPercentage(allocation_pct=0.05),
        symbol="TQQQ",
        initial_cash=INITIAL_CASH,
        cost_model=SlippageCommissionModel(commission_per_trade=0.0, slippage_bps=50.0),
        risk_manager=RiskManager(),
        fill_model="intrabar",
        enforce_no_loss=enforce,
    )


def test_the_guard_blocks_sells_that_would_not_cover_their_cost_basis():
    """Default behavior, unchanged: nothing closes, because every sell
    that reaches its target still loses money after costs."""
    result = _run(enforce=True)
    assert result.metrics["Closed Trade Count"] == 0
    assert result.metrics["Open Trade Count"] > 0


def test_disabling_the_guard_lets_those_sells_through():
    """The switch has to change behavior, not just exist."""
    guarded = _run(enforce=True)
    permitted = _run(enforce=False)
    assert permitted.metrics["Closed Trade Count"] > guarded.metrics["Closed Trade Count"]


def test_the_guard_wins_in_the_scenario_it_exists_for():
    """The retail edge, demonstrated rather than asserted.

    In this cost-floor scenario the guarded run holds 20 lots through a
    rising market and finishes around +34%, while the permitted run
    churns all 20 out at the cost floor and finishes slightly negative.
    Refusing to realize the loss is worth roughly 34 points here.

    Note what this does NOT show. Realized PnL is not lower in the
    permitted run -- it is HIGHER -- because closing lots frees cash and
    the two runs then buy different lots at different prices. The
    trajectories diverge completely; only the end state is comparable.
    And this is one synthetic rising series, not evidence about the real
    dataset, where holding through 2022 is what produces the ~80%
    drawdown the flag exists to let us measure against.
    """
    guarded = _run(enforce=True)
    permitted = _run(enforce=False)
    assert guarded.metrics["Total Return %"] > permitted.metrics["Total Return %"]
    assert guarded.metrics["Open Trade Count"] > permitted.metrics["Open Trade Count"]


def test_the_flag_is_recorded_in_the_result_params():
    """A run's params are its provenance record. Two runs that differ
    only in this flag must not look identical after the fact."""
    assert _run(enforce=True).params["enforce_no_loss"] is True
    assert _run(enforce=False).params["enforce_no_loss"] is False


def test_disabling_the_guard_does_not_by_itself_sell_losers():
    """The important limitation, pinned so it cannot be forgotten.

    Sells are only ATTEMPTED on lots whose profit target has been
    touched, and a target is above its buy price by construction. So
    turning the guard off permits marginally-unprofitable target sells
    -- it does NOT introduce a capitulation exit, and on its own it
    cannot reduce the drawdown caused by holding losers.

    Here the target is comfortably above round-trip cost, so the guard
    never fires and the flag changes nothing at all.
    """
    controller = OptimizationController(historical_data=_rising_series())
    kwargs = dict(
        step=0.002,
        target=0.02,  # 200bps gross, far above the 2bps round trip below
        symbol="TQQQ",
        initial_cash=INITIAL_CASH,
        cost_model=SlippageCommissionModel(commission_per_trade=0.0, slippage_bps=1.0),
        risk_manager=RiskManager(),
        fill_model="intrabar",
    )
    guarded = controller._simulate_single(
        strategy_instance=FixedPortfolioPercentage(allocation_pct=0.05),
        enforce_no_loss=True,
        **kwargs,
    )
    permitted = controller._simulate_single(
        strategy_instance=FixedPortfolioPercentage(allocation_pct=0.05),
        enforce_no_loss=False,
        **kwargs,
    )
    assert guarded.metrics["Closed Trade Count"] == permitted.metrics["Closed Trade Count"]
    assert guarded.metrics["Realized PnL"] == pytest.approx(permitted.metrics["Realized PnL"])
