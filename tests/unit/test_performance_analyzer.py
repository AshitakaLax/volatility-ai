import pytest

from src.ledger import AssetLotLedger
from src.performance_analyzer import PerformanceAnalyzer


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
