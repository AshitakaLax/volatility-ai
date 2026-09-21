"""
Task 4.3 acceptance tests (A4, S1, S2).

1. run_sweep(...) with no symbol/initial_cash reproduces the existing
   regression baseline exactly.
2. symbol="SPXL" runs without hardcoded "TQQQ" leaking into order
   calls, verified via a stub OMS recording what symbol it was
   actually called with.
"""

import pandas as pd

from research.optimization.optimization_controller import OptimizationController
from research.strategies.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_default_symbol_and_initial_cash_reproduce_baseline_exactly():
    df = _load_fixture()
    result = (
        OptimizationController(historical_data=df)
        .run_sweep(
            grid_steps=[BASELINE["Grid Step"]],
            profit_targets=[BASELINE["Profit Target"]],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
            # symbol/initial_cash both omitted -- must default exactly as before.
        )
        .iloc[0]
    )
    for key, expected in BASELINE.items():
        assert result[key] == expected


def test_row_carries_every_execution_flag_it_was_actually_called_with():
    """engine.warehouse.hashing.EXECUTION_FLAG_FIELDS names 8 fields as
    part of a simulation's warehouse dedup identity; the row returned by
    _run_one_combination silently omitted all of them for as long as the
    warehouse-recording feature existed, so every recorded simulation
    hashed as if execution were always {}. Non-default values here, not
    just presence, so a call site that hardcodes a flag rather than
    threading it through would still be caught."""
    df = _load_fixture()
    result = (
        OptimizationController(historical_data=df)
        .run_sweep(
            grid_steps=[BASELINE["Grid Step"]],
            profit_targets=[BASELINE["Profit Target"]],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
            symbol="SPXL",
            initial_cash=250_000.0,
            fill_model="intrabar",
            intrabar_priority="sell_first",
            on_flat_reentry="reset_to_market",
            enforce_no_loss=False,
            allow_signal_exit=True,
            settlement_days=1,
        )
        .iloc[0]
    )
    assert result["symbol"] == "SPXL"
    assert result["initial_cash"] == 250_000.0
    assert result["fill_model"] == "intrabar"
    assert result["intrabar_priority"] == "sell_first"
    assert result["on_flat_reentry"] == "reset_to_market"
    # == not is: this value comes back through a pandas column, which
    # types a bool as numpy's np.bool_ -- equal to, but not the same
    # object as, the Python bool singleton.
    assert result["enforce_no_loss"] == False  # noqa: E712
    assert result["allow_signal_exit"] == True  # noqa: E712
    assert result["settlement_days"] == 1


def test_custom_symbol_does_not_leak_hardcoded_tqqq(monkeypatch):
    from engine.execution.order_management_system import OrderManagementSystem as RealOMS

    calls = {"buy_symbols": [], "sell_symbols": []}

    class RecordingOMS:
        def __init__(self, mode="SIMULATION"):
            self._real = RealOMS(mode=mode)

        def execute_buy(self, symbol, trade_value, price):
            calls["buy_symbols"].append(symbol)
            return self._real.execute_buy(symbol, trade_value, price)

        def execute_sell(self, symbol, qty, price):
            calls["sell_symbols"].append(symbol)
            return self._real.execute_sell(symbol, qty, price)

    import research.optimization.optimization_controller as oc_module

    monkeypatch.setattr(oc_module, "OrderManagementSystem", RecordingOMS)

    df = _load_fixture()
    OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
        symbol="SPXL",
    )

    assert len(calls["buy_symbols"]) > 0, (
        "Fixture didn't attempt a buy -- can't verify symbol threading"
    )
    assert set(calls["buy_symbols"]) == {"SPXL"}
    assert len(calls["sell_symbols"]) > 0, (
        "Fixture didn't attempt a sell -- can't verify symbol threading"
    )
    assert set(calls["sell_symbols"]) == {"SPXL"}
    assert "TQQQ" not in calls["buy_symbols"] and "TQQQ" not in calls["sell_symbols"]


def test_custom_initial_cash_reflected_in_final_equity():
    df = _load_fixture()
    default_row = (
        OptimizationController(historical_data=df)
        .run_sweep(
            grid_steps=[BASELINE["Grid Step"]],
            profit_targets=[BASELINE["Profit Target"]],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
        )
        .iloc[0]
    )
    custom_row = (
        OptimizationController(historical_data=df)
        .run_sweep(
            grid_steps=[BASELINE["Grid Step"]],
            profit_targets=[BASELINE["Profit Target"]],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
            initial_cash=200_000.0,
        )
        .iloc[0]
    )
    # Double the starting cash roughly doubles the absolute profit in
    # dollar terms (allocation_pct sizes off equity, which scales
    # with initial_cash) -- final equity should be meaningfully higher,
    # not identical to the default-cash run.
    assert custom_row["Final Equity"] != default_row["Final Equity"]
    assert custom_row["Final Equity"] > 190_000.0
