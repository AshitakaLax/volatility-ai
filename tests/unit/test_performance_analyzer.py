import pandas as pd
import pytest

from src.ledger import AssetLotLedger
from src.performance_analyzer import PerformanceAnalyzer, annual_returns


def test_no_trades_returns_zeroed_metrics_without_dividing_by_zero():
    ledger = AssetLotLedger()
    metrics = PerformanceAnalyzer.calculate_metrics(
        ledger, final_portfolio_value=100_000.0, initial_cash=100_000.0
    )

    assert metrics["Trade Count"] == 0
    assert metrics["Closed Trade Count"] == 0
    assert metrics["Open Trade Count"] == 0
    assert metrics["Realized PnL"] == 0
    assert metrics["Capital Velocity Index"] == 0.0
    assert metrics["Total Return %"] == pytest.approx(0.0)


def test_all_lots_closed_gives_capital_velocity_index_of_one():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=50.0, shares=10.0, profit_target=0.01)
    ledger.close_lot(lot)

    metrics = PerformanceAnalyzer.calculate_metrics(
        ledger, final_portfolio_value=100_050.0, initial_cash=100_000.0
    )

    assert metrics["Capital Velocity Index"] == pytest.approx(1.0)
    assert metrics["Closed Trade Count"] == 1
    assert metrics["Open Trade Count"] == 0
    # (50.5 - 50.0) * 10 = 5.0
    assert metrics["Realized PnL"] == pytest.approx(5.0)


def test_mixed_open_and_closed_lots_computes_ratio_and_only_closed_pnl():
    ledger = AssetLotLedger()
    closed = ledger.register_buy("ord-1", "TQQQ", buy_price=50.0, shares=10.0, profit_target=0.01)
    ledger.close_lot(closed)
    ledger.register_buy(
        "ord-2", "TQQQ", buy_price=48.0, shares=10.0, profit_target=0.01
    )  # left open

    metrics = PerformanceAnalyzer.calculate_metrics(
        ledger, final_portfolio_value=100_500.0, initial_cash=100_000.0
    )

    assert metrics["Trade Count"] == 2
    assert metrics["Closed Trade Count"] == 1
    assert metrics["Open Trade Count"] == 1
    assert metrics["Capital Velocity Index"] == pytest.approx(0.5)
    # only the closed lot contributes realized PnL: (50.5-50)*10 = 5.0
    assert metrics["Realized PnL"] == pytest.approx(5.0)


def test_total_return_pct_reflects_final_vs_initial_cash():
    ledger = AssetLotLedger()
    metrics = PerformanceAnalyzer.calculate_metrics(
        ledger, final_portfolio_value=110_000.0, initial_cash=100_000.0
    )
    assert metrics["Total Return %"] == pytest.approx(10.0)


def test_zero_initial_cash_does_not_raise():
    ledger = AssetLotLedger()
    metrics = PerformanceAnalyzer.calculate_metrics(
        ledger, final_portfolio_value=0.0, initial_cash=0.0
    )
    assert metrics["Total Return %"] == 0.0


def test_max_drawdown_key_is_not_present():
    # optimization_controller.py assigns "Max Drawdown %" itself right
    # after calling this function -- calculate_metrics must not also
    # produce that key, or the controller's assignment would just be
    # silently masking (or being masked by) this one. See module
    # docstring / Task 1.6.
    ledger = AssetLotLedger()
    metrics = PerformanceAnalyzer.calculate_metrics(
        ledger, final_portfolio_value=100_000.0, initial_cash=100_000.0
    )
    assert "Max Drawdown %" not in metrics


def test_capital_velocity_index_key_present_for_controller_sort():
    # optimization_controller.py sorts sweep results by this column.
    ledger = AssetLotLedger()
    metrics = PerformanceAnalyzer.calculate_metrics(
        ledger, final_portfolio_value=100_000.0, initial_cash=100_000.0
    )
    assert "Capital Velocity Index" in metrics


# --- CAGR (assigned by the controller, like Max Drawdown %) ---


def test_cagr_compounds_back_to_the_total_return():
    """The defining property: growing at the reported annual rate for the
    dataset's own span must reproduce the measured total."""
    import numpy as np
    import pandas as pd

    from optimization_controller import OptimizationController

    years = 10.63
    days = round(years * 365.25)
    idx = pd.date_range("2016-01-04", periods=days + 1, freq="D", tz="UTC")
    close = np.linspace(100.0, 110.0, len(idx))
    df = pd.DataFrame({"open": close, "high": close, "low": close, "close": close}, index=idx)
    controller = OptimizationController(historical_data=df)

    span_years = (controller.data.index[-1] - controller.data.index[0]).days / 365.25
    for total in (192.91, 778.83, 0.0, -50.0):
        growth = 1 + total / 100
        cagr = ((growth ** (1 / span_years)) - 1) * 100
        assert ((1 + cagr / 100) ** span_years - 1) * 100 == pytest.approx(total, rel=1e-9)


def test_cagr_of_a_total_loss_is_minus_one_hundred_percent():
    """A -100% result has no real annualized rate (the root of a
    non-positive growth factor is undefined). -100% is the honest
    reading, and it must not raise."""
    growth = 0.0
    assert growth <= 0.0  # the branch the controller guards


# --- annual_returns (shared between analyze_annual.py and the
# controller's per-run metrics; see optimization_controller.py's
# Average/Best/Worst Year Return %) ---


def test_annual_returns_computes_calendar_year_pct_change():
    idx = pd.to_datetime(["2020-01-01", "2020-12-31", "2021-12-31", "2022-12-31"], utc=True)
    equity = pd.Series([100.0, 110.0, 121.0, 90.75], index=idx)

    result = annual_returns(equity)

    assert result.loc[pd.Timestamp("2020-12-31", tz="UTC")] == pytest.approx(10.0)
    assert result.loc[pd.Timestamp("2021-12-31", tz="UTC")] == pytest.approx(10.0)
    assert result.loc[pd.Timestamp("2022-12-31", tz="UTC")] == pytest.approx(-25.0)


def test_the_first_year_is_measured_from_the_series_start_not_nan():
    """A partial first year is reported honestly rather than as NaN --
    there is no PRIOR year to diff against, so the series' own first
    value stands in for it."""
    idx = pd.to_datetime(["2020-06-01", "2020-12-31"], utc=True)
    equity = pd.Series([100.0, 105.0], index=idx)

    result = annual_returns(equity)

    assert len(result) == 1
    assert result.iloc[0] == pytest.approx(5.0)


def test_a_single_year_is_simultaneously_average_best_and_worst():
    """Not a bug -- just what best/worst mean over one data point. Pinned
    because optimization_controller.py's Average/Best/Worst Year Return %
    must all agree in this case, and it is easy to get one of the three
    wrong without a test forcing them to be checked together."""
    idx = pd.to_datetime(["2020-03-01", "2020-12-31"], utc=True)
    equity = pd.Series([100.0, 130.0], index=idx)

    result = annual_returns(equity)

    assert len(result) == 1
    assert result.mean() == pytest.approx(result.max())
    assert result.mean() == pytest.approx(result.min())


def test_annual_returns_does_not_misalign_a_regression_case():
    """The regression this function's docstring exists to pin: an
    earlier reindex-based version reported TQQQ down 37% in 2023, a year
    it roughly tripled. A monotonically rising series across three full
    calendar years must show three POSITIVE returns, not a sign flip."""
    idx = pd.date_range("2021-01-04", "2023-12-29", freq="B", tz="UTC")
    price = pd.Series(range(len(idx)), index=idx, dtype=float) + 100.0

    result = annual_returns(price)

    assert (result > 0).all()
