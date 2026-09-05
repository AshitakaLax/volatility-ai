"""The metrics the web UI adds, checked against hand-computed answers.

Every expected value below is worked out by hand in its own comment. A
metric test that builds its expectation with the same code under test
proves only that the code is deterministic.

THE ONE THAT MATTERS IS WIN RATE. PerformanceAnalyzer.calculate_metrics
derives realised PnL as (target_sell_price - buy_price) * shares, which
is right only while signal exits are off -- the backtest path calls
close_lot(lot) with no execution_price, so a closed lot never records
what it actually sold for. A target is ALWAYS above its own basis, so a
win rate computed from targets would report 100% on every run forever.
test_a_losing_signal_exit_is_counted_as_a_loss is the guard against
that: it is the case the target-based figure cannot represent.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.performance_analyzer import PerformanceAnalyzer, curve_metrics, trade_metrics


def blotter(rows: list[dict]) -> pd.DataFrame:
    """A blotter shaped like the engine's, with only the fields used."""
    return pd.DataFrame(rows)


def sell(lot_id: str, pnl: float, bar: int = 10) -> dict:
    return {
        "side": "sell",
        "lot_id": lot_id,
        "bar_index": bar,
        "profit_realized": pnl,
        "price": 100.0,
        "qty": 1.0,
    }


def buy(lot_id: str, bar: int = 0) -> dict:
    return {"side": "buy", "lot_id": lot_id, "bar_index": bar, "price": 90.0, "qty": 1.0}


class TestTradeMetrics:
    def test_win_rate_and_profit_factor_from_a_mixed_book(self):
        # 3 wins (+10, +20, +30 = 60), 2 losses (-5, -15 = 20).
        # win rate  = 3/5            = 60.0%
        # profit factor = 60 / 20    = 3.0
        rows = [
            sell("a", 10.0),
            sell("b", -5.0),
            sell("c", 20.0),
            sell("d", -15.0),
            sell("e", 30.0),
        ]
        got = trade_metrics(blotter(rows))
        assert got["Win Rate %"] == pytest.approx(60.0)
        assert got["Profit Factor"] == pytest.approx(3.0)

    def test_a_losing_signal_exit_is_counted_as_a_loss(self):
        """The case a target-based win rate structurally cannot show."""
        rows = [sell("a", 10.0), sell("b", -40.0)]
        got = trade_metrics(blotter(rows))
        assert got["Win Rate %"] == pytest.approx(50.0)
        assert got["Profit Factor"] == pytest.approx(10.0 / 40.0)

    def test_max_consecutive_losses_counts_the_longest_run_not_the_total(self):
        # -1, -1, +1, -1, -1, -1, +1  -> longest run is 3, total is 5.
        rows = [
            sell("a", -1.0),
            sell("b", -1.0),
            sell("c", 1.0),
            sell("d", -1.0),
            sell("e", -1.0),
            sell("f", -1.0),
            sell("g", 1.0),
        ]
        assert trade_metrics(blotter(rows))["Max Consecutive Losses"] == 3

    def test_a_book_with_no_losses_reports_gross_profit_not_infinity(self):
        """inf serialises to JSON as null and sorts unpredictably."""
        got = trade_metrics(blotter([sell("a", 10.0), sell("b", 5.0)]))
        assert got["Profit Factor"] == pytest.approx(15.0)
        assert got["Win Rate %"] == pytest.approx(100.0)

    def test_average_hold_duration_is_per_lot_from_first_buy_to_last_sell(self):
        # lot a: bar 0 -> 10  (10 bars)
        # lot b: bar 2 -> 22  (20 bars)
        # mean = 15
        rows = [buy("a", 0), buy("b", 2), sell("a", 1.0, bar=10), sell("b", 1.0, bar=22)]
        assert trade_metrics(blotter(rows))["Average Hold Duration"] == pytest.approx(15.0)

    def test_an_empty_or_unenriched_blotter_returns_zeros_rather_than_raising(self):
        """A run with no closed trades is a real outcome."""
        for frame in (
            pd.DataFrame(),
            pd.DataFrame([{"side": "buy", "price": 1.0}]),  # no profit_realized column
            blotter([buy("a")]),  # enriched, but nothing sold
        ):
            got = trade_metrics(frame)
            assert got["Win Rate %"] == 0.0
            assert got["Max Consecutive Losses"] == 0


class TestCurveMetrics:
    def test_a_flat_curve_has_no_ratio_rather_than_a_division_by_zero(self):
        index = pd.date_range("2024-01-01", periods=10, freq="1D", tz="UTC")
        flat = pd.Series([100.0] * 10, index=index)
        assert curve_metrics(flat) == {"Sharpe": 0.0, "Sortino": 0.0}

    def test_a_monotonically_rising_curve_has_no_downside_so_sortino_is_zero(self):
        """Sortino divides by DOWNSIDE deviation. With no down day there
        is none, and reporting 0.0 is honest where inf would not be."""
        index = pd.date_range("2024-01-01", periods=20, freq="1D", tz="UTC")
        rising = pd.Series([100.0 * (1.01**i) for i in range(20)], index=index)
        got = curve_metrics(rising)
        assert got["Sharpe"] > 0
        assert got["Sortino"] == 0.0

    def test_a_falling_curve_gives_a_negative_sharpe(self):
        index = pd.date_range("2024-01-01", periods=20, freq="1D", tz="UTC")
        falling = pd.Series([100.0 * (0.99**i) for i in range(20)], index=index)
        assert curve_metrics(falling)["Sharpe"] < 0

    def test_minute_bars_are_resampled_to_daily_before_measuring(self):
        """Annualising a per-MINUTE standard deviation by sqrt(252) is
        not a Sharpe ratio anyone would recognise, and this project's
        data is minute bars. Two curves covering the same days with the
        same daily closes must agree regardless of sampling."""
        days = pd.date_range("2024-01-01", periods=30, freq="1D", tz="UTC")
        daily = pd.Series([100.0 * (1.001**i) for i in range(30)], index=days)

        minutes = pd.date_range("2024-01-01", periods=30 * 24 * 60, freq="1min", tz="UTC")
        # Same closing value on each day, sampled far more often.
        per_minute = pd.Series(
            [100.0 * (1.001 ** (i // (24 * 60))) for i in range(len(minutes))], index=minutes
        )

        assert curve_metrics(per_minute)["Sharpe"] == pytest.approx(
            curve_metrics(daily)["Sharpe"], rel=0.05
        )

    def test_too_short_a_series_returns_zeros(self):
        index = pd.date_range("2024-01-01", periods=2, freq="1D", tz="UTC")
        assert curve_metrics(pd.Series([1.0, 2.0], index=index)) == {"Sharpe": 0.0, "Sortino": 0.0}


class _Lot:
    def __init__(self, shares: float, buy_price: float, target: float):
        self.shares = shares
        self.buy_price = buy_price
        self.target_sell_price = target


class _Ledger:
    def __init__(self, open_lots, closed_lots):
        self.open_lots = open_lots
        self.closed_lots = closed_lots


class TestStuckCapital:
    def test_stuck_capital_is_open_inventory_at_the_final_mark(self):
        # 2 lots x 10 shares, marked at 50.0 -> 1000.0
        ledger = _Ledger(
            open_lots=[_Lot(10.0, 40.0, 44.0), _Lot(10.0, 45.0, 49.5)],
            closed_lots=[_Lot(10.0, 30.0, 33.0)],
        )
        got = PerformanceAnalyzer.calculate_metrics(ledger, 5000.0, 4000.0, mark_price=50.0)
        assert got["Stuck Capital Value"] == pytest.approx(1000.0)

    def test_without_a_mark_price_it_is_zero_rather_than_silently_wrong(self):
        """The three-argument call site predates this metric."""
        ledger = _Ledger(open_lots=[_Lot(10.0, 40.0, 44.0)], closed_lots=[])
        got = PerformanceAnalyzer.calculate_metrics(ledger, 5000.0, 4000.0)
        assert got["Stuck Capital Value"] == 0.0

    def test_harvest_to_stuck_ratio_is_separate_from_capital_velocity_index(self):
        """They are different definitions and must not be conflated.

        3 closed, 1 open:
          Capital Velocity Index = 3/4 = 0.75   (closed / TOTAL)
          Harvest to Stuck Ratio = 3/1 = 3.0    (closed / STUCK)

        Capital Velocity Index is run_sweep's default rank_by and orders
        every sweep result recorded in README.md, so redefining it would
        restate published rankings.
        """
        ledger = _Ledger(
            open_lots=[_Lot(1.0, 1.0, 1.1)],
            closed_lots=[_Lot(1.0, 1.0, 1.1) for _ in range(3)],
        )
        got = PerformanceAnalyzer.calculate_metrics(ledger, 100.0, 100.0, mark_price=1.0)
        assert got["Capital Velocity Index"] == pytest.approx(0.75)
        assert got["Harvest to Stuck Ratio"] == pytest.approx(3.0)

    def test_with_nothing_stuck_the_ratio_is_the_closed_count(self):
        ledger = _Ledger(open_lots=[], closed_lots=[_Lot(1.0, 1.0, 1.1) for _ in range(4)])
        got = PerformanceAnalyzer.calculate_metrics(ledger, 100.0, 100.0, mark_price=1.0)
        assert got["Harvest to Stuck Ratio"] == pytest.approx(4.0)
        assert got["Capital Velocity Index"] == pytest.approx(1.0)


class TestBlotterLinkage:
    """The enrichment that makes closed-cycle connectors possible."""

    def test_a_real_run_produces_joinable_buy_and_sell_rows(self):
        import pandas as pd_

        from optimization_controller import OptimizationController
        from src.config import BacktestConfig
        from src.strategy_registry import resolve_strategy

        frame = pd_.read_csv(
            "tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"]
        ).set_index("timestamp")
        config = BacktestConfig.from_yaml("config/staging.yaml")
        kwargs = config.to_run_sweep_kwargs(resolve_strategy(config.strategy.strategy_id))
        kwargs["return_full_results"] = True
        _, full = OptimizationController(historical_data=frame).run_sweep(**kwargs)

        book = full[0].trade_blotter
        for column in ("lot_id", "ticker", "bar_index", "sell_reason", "profit_realized"):
            assert column in book.columns, f"blotter lost {column!r}"

        sells = book[book.side == "sell"]
        buys = book[book.side == "buy"]
        assert not sells.empty
        # Every sold lot is traceable to the buy that opened it, which
        # is what a cycle connector draws between.
        assert set(sells.lot_id) <= set(buys.lot_id)
