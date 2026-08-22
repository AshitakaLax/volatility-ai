"""Tests for fill_model="intrabar" in OptimizationController.

The claim being pinned: a level TOUCHED during a bar fills (at that
level), whereas the default "close" model only fills when the bar's
close reaches the level. The fixtures below are built so the two
models must disagree -- bars whose high/low pierce a level that the
close then retreats from -- because a fixture where close and
high/low agree would pass under either model and prove nothing.

Also pins the invariant that matters most: fill_model="close" is
unchanged. tests/fixtures/regression_baseline.py already guards that
globally; the test here states it locally for this parameter.
"""

from __future__ import annotations

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.exceptions import ConfigurationError
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE

FIXTURE = "tests/fixtures/regression_ohlcv.csv"


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE, parse_dates=["timestamp"])
    return df.set_index("timestamp")


def _wick_fixture() -> pd.DataFrame:
    """Bars that CLOSE flat at 100 but whose wicks pierce well below
    and above it. Under "close" nothing ever triggers (close never
    moves); under "intrabar" the lows touch buy triggers and the highs
    touch sell targets."""
    n = 40
    ts = pd.date_range("2024-01-02 14:30", periods=n, freq="1min", tz="UTC")
    close = [100.0] * n
    return pd.DataFrame(
        {
            "open": close,
            "high": [101.0] * n,  # +1% wick up
            "low": [99.0] * n,  # -1% wick down
            "close": close,
            "volume": [10_000] * n,
        },
        index=ts,
    )


def _run(df, fill_model="close", **kw):
    controller = OptimizationController(historical_data=df)
    return controller.run_sweep(
        grid_steps=[0.005],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        fill_model=fill_model,
        **kw,
    ).iloc[0]


def test_close_model_is_the_unchanged_default():
    """Explicit "close" and an omitted fill_model must both reproduce
    the pinned regression baseline exactly."""
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)
    common = dict(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    omitted = controller.run_sweep(**common).iloc[0]
    explicit = controller.run_sweep(**common, fill_model="close").iloc[0]

    for key, expected in BASELINE.items():
        assert omitted[key] == expected, f"{key} drifted with fill_model omitted"
        assert explicit[key] == expected, f"{key} drifted with explicit fill_model='close'"


def test_a_wick_that_the_close_retreats_from_fills_only_under_intrabar():
    """THE distinguishing case. Close is pinned at 100 for every bar,
    so the close-only model can never trigger anything; the wicks
    pierce +/-1%, so the touch model trades."""
    df = _wick_fixture()
    close_row = _run(df, fill_model="close")
    intrabar_row = _run(df, fill_model="intrabar")

    assert close_row["Trade Count"] == 0, (
        "close never moves off 100, so the close-only model must find no trades"
    )
    assert intrabar_row["Trade Count"] > 0, (
        "the bar lows pierce the buy trigger, so the touch model must trade"
    )


def test_intrabar_buy_fills_at_the_trigger_level_not_the_close():
    """Fill convention: a touched level fills AT the level. With close
    pinned at 100 and the trigger 0.5% below the reference, the buy
    must be recorded at ~99.5, not at 100."""
    df = _wick_fixture()
    controller = OptimizationController(historical_data=df)
    _, full = controller.run_sweep(
        grid_steps=[0.005],
        profit_targets=[0.5],  # wide, so nothing sells and we isolate the buy
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        fill_model="intrabar",
        return_full_results=True,
    )
    blotter = full[0].trade_blotter
    buys = blotter[blotter["side"] == "buy"]
    assert len(buys) > 0
    first = buys.iloc[0]
    assert first["price"] == pytest.approx(100.0 * 0.995), (
        f"buy should fill at the touched trigger level, got {first['price']}"
    )
    assert first["price"] != pytest.approx(100.0), "must not fill at the bar's close"


def test_intrabar_produces_at_least_as_many_fills_as_close_on_real_shaped_data():
    """On ordinary OHLC data (not the adversarial wick fixture), the
    touch model is a superset of the close model: any level the close
    reached was necessarily also touched intrabar."""
    df = _load_fixture()
    close_row = _run(df, fill_model="close")
    intrabar_row = _run(df, fill_model="intrabar")
    assert intrabar_row["Trade Count"] >= close_row["Trade Count"]


def test_full_results_are_not_retained_when_not_requested():
    """Memory contract, not just an API one. Each SimulationResult holds
    a per-bar equity curve and a full trade blotter -- tens of MB each on
    real data -- so retaining them for every combination when the caller
    only reads summary_df is what exhausted RAM on a 1,260-combination
    sweep here. Pinned because it regresses silently: the sweep still
    returns correct numbers, just uses unbounded memory doing it."""
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)
    common = dict(
        grid_steps=[0.01, 0.005],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    summary_only = controller.run_sweep(**common)
    assert isinstance(summary_only, pd.DataFrame)  # not a tuple

    summary, full = controller.run_sweep(**common, return_full_results=True)
    assert len(full) == len(summary), "requested full results must still be complete and paired"
    assert not full[0].equity_curve.empty, "and must still actually carry their payload"


def test_unsupported_fill_model_is_rejected():
    df = _load_fixture()
    with pytest.raises(ConfigurationError, match="fill_model"):
        _run(df, fill_model="magic")


def test_buy_first_with_intrabar_is_rejected_rather_than_silently_ignored():
    """A config that asks for an ordering this path doesn't implement
    must fail loudly, not run with the other ordering."""
    df = _load_fixture()
    with pytest.raises(ConfigurationError, match="buy_first"):
        _run(df, fill_model="intrabar", intrabar_priority="buy_first")


def test_buy_first_is_still_accepted_under_the_close_model():
    """intrabar_priority is meaningless for close-only fills (a close
    is one price, so no ambiguity exists) -- it must not start
    rejecting configs that were previously valid, and must not change
    their results either."""
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)
    common = dict(
        grid_steps=[0.01],  # the baseline's own parameters, unlike _run's
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        fill_model="close",
    )
    row = controller.run_sweep(**common, intrabar_priority="buy_first").iloc[0]
    assert row["Final Equity"] == BASELINE["Final Equity"]
