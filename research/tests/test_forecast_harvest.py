"""Forecast Harvest (research/strategies/forecast_harvest_sizing.py): with
every addition off it is Daily Ultimate exactly; whole shares are whole;
the day part sells its share of a lot at a profit and the rest waits for
the swing target; a report moves the day level and the lot size; seed lots
are bought once at their levels and never sold by the regime exit."""

from __future__ import annotations

import inspect
from datetime import date

import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.optimization.optimization_controller import OptimizationController
from research.strategies.daily_ultimate_sizing import DailyUltimateSizing
from research.strategies.forecast_harvest_sizing import (
    SEED,
    ForecastHarvestSizing,
    forecast_sigma,
)
from research.strategies.strategy_registry import STRATEGIES, may_realize_loss
from tests.fixtures import composition_baseline as fixture
from tools import probe_forecast_harvest as probe

SIGNAL = {"fill_model": "intrabar", "intrabar_fill": "causal", "allow_signal_exit": True}
OFF = {"whole_shares": False}


@pytest.fixture(scope="module")
def ohlcv():
    return fixture.load_ohlcv()


@pytest.fixture(scope="module")
def ultimate_params(ohlcv):
    case = next(c for c in fixture.CASES if c.name == "ultimate")
    return case.params(ohlcv)


def _run(df, cls, params, target=0.05, cash=100_000.0):
    summary, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[params],
        return_full_results=True,
        initial_cash=cash,
        **SIGNAL,
    )
    assert full[0] is not None, summary.to_dict("records")
    return summary.iloc[0], full[0].trade_blotter


def _lots(blotter):
    buys = blotter[blotter["side"] == "buy"].set_index("lot_id")
    sells = blotter[blotter["side"] == "sell"]
    return buys, sells


def test_registered_and_may_realise_a_loss_only_through_the_regime_exit():
    assert STRATEGIES["forecast_harvest"] is ForecastHarvestSizing
    assert may_realize_loss("forecast_harvest", {})


def test_the_run_form_sees_every_parameter():
    names = set(inspect.signature(ForecastHarvestSizing).parameters)
    assert {"per_lot_pct", "natr_period", "daily_goal", "day_fraction", "seed_levels"} <= names
    assert not any(
        p.kind is inspect.Parameter.VAR_KEYWORD
        for p in inspect.signature(ForecastHarvestSizing).parameters.values()
    )


def test_every_addition_off_is_daily_ultimate(ohlcv, ultimate_params):
    row_a, blot_a = _run(ohlcv, DailyUltimateSizing, ultimate_params)
    row_b, blot_b = _run(ohlcv, ForecastHarvestSizing, {**ultimate_params, **OFF})
    assert fixture.blotter_digest(blot_a) == fixture.blotter_digest(blot_b)
    for column in ("Final Equity", "Trade Count", "Signal Exit Count"):
        assert row_a[column] == row_b[column], column


def test_every_buy_and_sale_is_whole_shares(ohlcv, ultimate_params):
    _, blot = _run(
        ohlcv,
        ForecastHarvestSizing,
        {**ultimate_params, "whole_shares": True, "day_fraction": 0.5, "per_lot_pct": 0.02},
    )
    qty = blot["qty"].astype(float)
    assert len(qty) > 10
    assert (qty - qty.round()).abs().max() < 1e-6
    assert (qty >= 1 - 1e-9).all()


def test_the_day_part_sells_its_share_at_a_profit_and_the_rest_waits(ohlcv, ultimate_params):
    params = {
        **ultimate_params,
        "whole_shares": True,
        "day_fraction": 0.5,
        "day_target_min": 0.002,
        "day_target_max": 0.01,
        "per_lot_pct": 0.02,
    }
    _, blot = _run(ohlcv, ForecastHarvestSizing, params, target=0.05)
    buys, sells = _lots(blot)
    first = sells.groupby("lot_id").first()
    split = first[sells.groupby("lot_id").size() == 2]
    assert len(split) > 0
    bought = buys["qty"].reindex(split.index).astype(float)
    # The day part is day_fraction of the lot, rounded down to whole shares.
    assert ((split["qty"].astype(float) - (bought * 0.5).apply(int)).abs() < 1e-6).all()
    targets = sells[sells["sell_reason"] == "profit_target"]
    assert (targets["profit_realized"].astype(float) >= -1e-6).all()


def test_the_closing_sale_banks_day_parts_and_only_day_parts(ohlcv, ultimate_params):
    params = {
        **ultimate_params,
        "whole_shares": True,
        "day_fraction": 0.5,
        "day_k": 3.0,  # levels the day rarely reaches: the close does the selling
        "day_target_min": 0.001,
        "day_target_max": 0.03,
        "day_close_minute": 380,
        "per_lot_pct": 0.02,
    }
    _, blot = _run(ohlcv, ForecastHarvestSizing, params, target=0.2)
    sells = blot[blot["side"] == "sell"]
    minute = (
        pd.to_datetime(sells["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.hour * 60
        + pd.to_datetime(sells["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.minute
        - 570
    )
    pnl = sells["profit_realized"].astype(float)
    gain = pnl / (sells["qty"].astype(float) * sells["price"].astype(float) - pnl)
    # Reversal lots (the fixture's +2% target) sell whole at their own target.
    closing = sells[(minute >= 380) & (sells["sell_reason"] == "profit_target") & (gain < 0.0195)]
    assert len(closing) > 0
    assert (closing["profit_realized"].astype(float) >= -1e-6).all()
    # A lot sold at the close keeps its swing part: no lot is emptied there
    # unless its day part was the whole of what it held.
    buys = blot[blot["side"] == "buy"].set_index("lot_id")["qty"].astype(float)
    sold = closing.groupby("lot_id")["qty"].sum().astype(float)
    assert (sold <= (buys.reindex(sold.index) * 0.5).apply(int) + 1e-6).all()


def test_a_report_moves_the_day_level_and_the_lot():
    s = ForecastHarvestSizing(
        per_lot_pct=0.01,
        lookback_days=0.02,
        bars_per_day=390,
        day_fraction=0.5,
        forecast_size_exponent=1.0,
        forecast_tilt=0.5,
        forecast_by_date={date(2024, 1, 3): {"p05": -8, "p25": -3, "p50": 1, "p75": 4, "p95": 9}},
    )
    s._last_close, s._closes, s._ewma_var = 100.0, [99.0], 0.03**2
    s._new_session(_ctx(date(2024, 1, 3)))
    assert s.day_level == pytest.approx(104.0)
    sigma = forecast_sigma(s.forecast)
    expected = (s._own_sigma() / sigma) * (1 + 0.5 * 0.01 / sigma)
    assert s._size_mult == pytest.approx(expected)
    # A session with no report: the fund's own volatility sets the level.
    s._last_close = 104.0
    s._new_session(_ctx(date(2024, 1, 4)))
    assert s.forecast is None and s._size_mult == 1.0
    assert s.day_level == pytest.approx(104.0 * (1 + 0.6745 * s._own_sigma()))


def test_a_leaning_down_report_buys_nothing():
    s = ForecastHarvestSizing(
        per_lot_pct=0.01,
        lookback_days=0.02,
        bars_per_day=390,
        forecast_tilt=2.0,
        forecast_by_date={
            date(2024, 1, 3): {"p05": -10, "p25": -6, "p50": -4, "p75": -2, "p95": 2}
        },
    )
    s._last_close, s._closes, s._ewma_var = 100.0, [99.0], 0.03**2
    s._new_session(_ctx(date(2024, 1, 3)))
    assert s._size_mult == 0.0


def test_seed_lots_are_bought_once_and_the_regime_exit_keeps_them(ohlcv, ultimate_params):
    first = pd.Timestamp(ohlcv.index[0]).tz_convert("America/New_York")
    start = (first + pd.Timedelta(days=60)).date().isoformat()
    params = {
        **ultimate_params,
        "whole_shares": True,
        "trade_from": start,
        "seed_levels": "0,0.05",
        "seed_lot_pct": 0.1,
        "seed_target": 5.0,  # never reached: the seeds stay open
    }
    _, blot = _run(ohlcv, ForecastHarvestSizing, params)
    buys, sells = _lots(blot)
    ts = pd.to_datetime(blot["timestamp"], utc=True).dt.tz_convert("America/New_York")
    assert ts[blot["side"] == "buy"].min().date().isoformat() >= start
    first_buy = buys.iloc[0]
    assert float(first_buy["qty"]) * float(first_buy["price"]) == pytest.approx(10_000, rel=0.01)
    # The first seed stays open through every regime exit of the run.
    assert first_buy.name not in set(sells["lot_id"])


def test_resume_reads_seeds_and_open_day_parts():
    s = ForecastHarvestSizing(
        per_lot_pct=0.01,
        lookback_days=0.02,
        bars_per_day=390,
        day_fraction=0.5,
        day_target_max=0.04,
        seed_levels="0,0.1",
    )
    lots = [
        _Lot("a", 10, 0.6, SEED),
        _Lot("b", 9, 0.01, None),
        _Lot("c", 9, 0.12, None),
    ]
    s.resume(lots)
    assert s._seed_ids == {"a"} and s._day_parts == {"b": 4.0}
    assert s._seeds_bought == 2
    # The resumed day part goes on to the swing part's target, read from a
    # calm lot already in its swing part when swing_target is not set ...
    assert s._swing == {"b": 0.12}
    # ... and swing_target when it is.
    t = ForecastHarvestSizing(
        per_lot_pct=0.01,
        lookback_days=0.02,
        bars_per_day=390,
        day_fraction=0.5,
        swing_target=0.2,
    )
    t.resume([_Lot("b", 9, 0.01, None)])
    assert t._swing == {"b": 0.2}


def test_a_restarted_run_never_seeds_again():
    s = ForecastHarvestSizing(
        per_lot_pct=0.01, lookback_days=0.02, bars_per_day=390, seed_levels="0,0.1,0.2"
    )
    s.resume([])  # its seeds sold, or were never all bought
    assert s._seeds_bought == 3 and s._seed_level() is None


def test_bad_settings_are_refused():
    for bad in (
        {"day_fraction": 1.5},
        {"day_quantile": "p60"},
        {"day_target_min": 0.0},
        {"seed_levels": "0,1.2"},
        {"size_min": 1.5},
        {"swing_target": 0.03},  # not above day_target_max
    ):
        with pytest.raises(ConfigurationError):
            ForecastHarvestSizing(per_lot_pct=0.01, lookback_days=0.02, bars_per_day=390, **bad)


def test_synthetic_reports_are_calibrated_and_rho_one_knows_the_close():
    import numpy as np

    days = pd.date_range("2024-01-01", periods=400, freq="B")
    rng = np.random.default_rng(1)
    closes = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.03, len(days)))), index=days)
    proxy = {d.date(): {"p05": -4.93, "p25": -2.0, "p50": 0, "p75": 2.0, "p95": 4.93} for d in days}
    oracle = probe.synthetic(proxy, closes, 1.0, 0)
    r = closes.pct_change().dropna()
    for d, v in r.items():
        assert oracle[d.date()]["p50"] == pytest.approx(v * 100, abs=1e-3)
        # a sliver of spread (5% of sigma) so the sizing levers can read it
        assert 0 < oracle[d.date()]["p95"] - oracle[d.date()]["p05"] < 0.6
    # Accuracy 0 is the proxy's sigma and nothing more: the same report daily.
    blind = probe.synthetic(proxy, closes, 0.0, 0)
    assert len({tuple(v.values()) for v in blind.values()}) == 1
    assert next(iter(blind.values()))["p50"] == 0
    wrong = probe.synthetic(proxy, closes, -0.5, 0)
    med = pd.Series({d: wrong[d.date()]["p50"] for d in r.index})
    assert med.corr(r) < -0.2


class _Lot:
    def __init__(self, oid, shares, target, tag):
        self.order_id, self.shares, self.profit_target, self.entry_tag = oid, shares, target, tag
        self.buy_price = 10.0


def _ctx(day: date):
    from engine.core.market_context import MarketContext

    ts = pd.Timestamp(day.isoformat() + " 09:30", tz="America/New_York")
    return MarketContext(
        timestamp=ts,
        open=100.0,
        high=100.0,
        low=100.0,
        close=100.0,
        cash=0.0,
        equity=0.0,
        peak_equity=0.0,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
    )


def test_the_pinned_config_is_the_forms_defaults():
    from pathlib import Path

    from engine.core.config import BacktestConfig
    from research.strategies.param_schema import STRATEGY_DEFAULTS

    path = Path(__file__).resolve().parents[2] / "config" / "forecast_harvest_tqqq.yaml"
    config = BacktestConfig.from_yaml(path)
    config.validate()
    assert config.strategy.strategy_id == "forecast_harvest"
    assert dict(config.strategy.strategy_params) == STRATEGY_DEFAULTS["forecast_harvest"]
    kwargs = config.to_run_sweep_kwargs(ForecastHarvestSizing)
    assert kwargs["allow_signal_exit"] is True
    assert kwargs["intrabar_fill"] == "causal"
    assert kwargs["initial_cash"] == 250_000.0
    ForecastHarvestSizing(**STRATEGY_DEFAULTS["forecast_harvest"])


def test_live_reads_the_sessions_report_from_the_forecast_database(tmp_path):
    import json
    from pathlib import Path

    from research.risk_overlay.forecasts import ForecastStore

    fixture_path = (
        Path(__file__).resolve().parents[2] / "tests/fixtures/risk_reports/tqqq_2026-11-20.json"
    )
    db = tmp_path / "forecasts" / "risk_reports.db"
    ForecastStore(db).record(json.loads(fixture_path.read_text(encoding="utf-8")), via="import")
    s = ForecastHarvestSizing(
        per_lot_pct=0.01, lookback_days=0.02, bars_per_day=390, forecast_db=str(db)
    )
    s._last_close, s._closes = 48.99, [52.47]
    s._new_session(_ctx(date(2026, 11, 20)))
    assert s.forecast is not None
    assert s.forecast["p75"] == 4.55 and s.forecast["p05"] == -13.42
    assert s.day_level == pytest.approx(48.99 * (1 + 0.0455))
    # No report for the next session: the fund's own volatility instead.
    s._new_session(_ctx(date(2026, 11, 23)))
    assert s.forecast is None
    # A database that is not there is a session without a report.
    gone = ForecastHarvestSizing(
        per_lot_pct=0.01, lookback_days=0.02, bars_per_day=390, forecast_db=str(tmp_path / "x.db")
    )
    gone._new_session(_ctx(date(2026, 11, 20)))
    assert gone.forecast is None


def test_the_live_profile_is_the_pinned_config():
    from pathlib import Path

    import yaml

    from engine.core.config import BacktestConfig

    root = Path(__file__).resolve().parents[2]
    profile = yaml.safe_load(
        (root / "config/live_profiles/forecast-harvest-tqqq.yaml").read_text(encoding="utf-8")
    )
    config = BacktestConfig.from_yaml(root / "config/forecast_harvest_tqqq.yaml")
    assert profile["strategy_id"] == config.strategy.strategy_id
    assert profile["strategy_params"] == dict(config.strategy.strategy_params)
    assert profile["step"] == 0.002 and profile["profit_target"] == 0.2
    assert profile["symbols"] == ["TQQQ"]
