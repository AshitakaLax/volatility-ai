"""Daily Ultimate (research/strategies/daily_ultimate_sizing.py): every
switch off is Ultimate exactly; its buy and sell halves compose back into
it; the daily goal, the compounded lots and the take-profits do what the
module docstring says; and nothing it adds can sell below cost."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.composition import entries
from research.composition.composed_strategy import ComposedStrategy
from research.optimization.optimization_controller import OptimizationController
from research.strategies.daily_ultimate_sizing import DailyGoal, DailyUltimateSizing
from research.strategies.gated_local_reference_sizing import NO_BUY_LEVEL
from research.strategies.live_algorithm import build_strategy
from research.strategies.strategy_registry import STRATEGIES, may_realize_loss
from research.strategies.ultimate_sizing import CALM, UltimateSizing
from tests.fixtures import composition_baseline as fixture

SIGNAL = {"fill_model": "intrabar", "intrabar_fill": "causal", "allow_signal_exit": True}
# Every switch on, at a goal this fixture's $100 lots reach before its closing
# window (24 of 300 sessions), so the pause and the lock both act.
DAILY = {
    "compound_lots": True,
    "daily_goal": 0.00005,
    "goal_pause_buys": True,
    "goal_lock": True,
    "eod_harvest_minute": 380,
    "harvest_min_gain": 0.001,
}
SELLING = {"goal_lock", "eod_harvest_minute", "harvest_min_gain", "reversal_target"}


@pytest.fixture(scope="module")
def ohlcv():
    return fixture.load_ohlcv()


@pytest.fixture(scope="module")
def ultimate_params(ohlcv):
    case = next(c for c in fixture.CASES if c.name == "ultimate")
    return case.params(ohlcv)


def _run(df, cls, params, target=0.05):
    summary, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[params],
        return_full_results=True,
        **SIGNAL,
    )
    assert full[0] is not None, summary.to_dict("records")
    return summary.iloc[0], full[0].trade_blotter


def _minute(blotter):
    ts = pd.to_datetime(blotter["timestamp"], utc=True).dt.tz_convert("America/New_York")
    return (ts.dt.hour * 60 + ts.dt.minute) - (9 * 60 + 30)


# -- identities ----------------------------------------------------------------


def test_every_switch_off_is_ultimate(ohlcv, ultimate_params):
    row_a, blot_a = _run(ohlcv, UltimateSizing, ultimate_params)
    row_b, blot_b = _run(ohlcv, DailyUltimateSizing, ultimate_params)
    assert fixture.blotter_digest(blot_a) == fixture.blotter_digest(blot_b)
    for column in ("Final Equity", "Trade Count", "Signal Exit Count"):
        assert row_a[column] == row_b[column], column


def test_daily_ultimate_is_its_buying_and_its_daily_exit(ohlcv, ultimate_params):
    params = {**ultimate_params, **DAILY}
    buy = {k: v for k, v in params.items() if k not in SELLING}
    sell = {
        "regime_by_date": params["regime_by_date"],
        "reversal_target": params["reversal_target"],
        **{k: v for k, v in DAILY.items() if k in SELLING | {"daily_goal"}},
    }
    row_a, blot_a = _run(ohlcv, DailyUltimateSizing, params)
    row_b, blot_b = _run(
        ohlcv,
        ComposedStrategy,
        {
            "buy": {"id": "daily_ultimate", "params": buy},
            "sell": {"id": "daily_ultimate_exit", "params": sell},
        },
    )
    assert fixture.blotter_digest(blot_a) == fixture.blotter_digest(blot_b)
    for column in ("Final Equity", "Trade Count", "Signal Exit Count"):
        assert row_a[column] == row_b[column], column
    # ...and the switches act, so the identity covers them.
    row_off, _ = _run(ohlcv, DailyUltimateSizing, ultimate_params)
    harvest_only = {k: DAILY[k] for k in ("eod_harvest_minute", "harvest_min_gain")}
    row_eod, _ = _run(ohlcv, DailyUltimateSizing, {**ultimate_params, **harvest_only})
    assert row_a["Trade Count"] < row_eod["Trade Count"], "the goal paused some buying"
    assert row_a["Final Equity"] != row_off["Final Equity"]


# -- the take-profits ------------------------------------------------------------


def test_the_closing_harvest_sells_in_profit_only_and_from_its_minute(ohlcv, ultimate_params):
    _, off = _run(ohlcv, DailyUltimateSizing, ultimate_params)
    _, on = _run(
        ohlcv,
        DailyUltimateSizing,
        {**ultimate_params, "eod_harvest_minute": 380, "harvest_min_gain": 0.001},
    )
    sells_off, sells_on = off[off["side"] == "sell"], on[on["side"] == "sell"]
    late = lambda s: s[_minute(s) >= 380]  # noqa: E731
    assert len(late(sells_on)) > len(late(sells_off))
    targets = sells_on[sells_on["sell_reason"].str.contains("profit_target")]
    assert (targets["profit_realized"] >= -1e-8).all()
    losing = sells_on[sells_on["profit_realized"] < -1e-8]
    assert losing["sell_reason"].str.contains("signal_exit").all()


def test_the_daily_harvest_sell_pairs_with_any_buyer(ohlcv):
    buy = {"id": "hf_local_reference", "params": dict(fixture.HF)}
    _, fixed = _run(ohlcv, ComposedStrategy, {"buy": buy, "sell": {"id": "fixed_target"}}, 0.01)
    _, daily = _run(
        ohlcv,
        ComposedStrategy,
        {"buy": buy, "sell": {"id": "daily_harvest", "params": {"harvest_min_gain": 0.001}}},
        0.01,
    )
    assert not daily.equals(fixed)
    sells = daily[daily["side"] == "sell"]
    assert (sells["profit_realized"] >= -1e-8).all()
    assert not sells["sell_reason"].str.contains("signal_exit").any()


# -- DailyGoal -------------------------------------------------------------------


def _ctx(day: int, minute: int, equity: float, price: float = 100.0) -> MarketContext:
    ts = pd.Timestamp(f"2024-01-{day:02d} 14:30", tz="UTC") + pd.Timedelta(minutes=max(minute, 0))
    return MarketContext(
        timestamp=ts,
        open=price,
        high=price,
        low=price,
        close=price,
        cash=equity,
        equity=equity,
        peak_equity=equity,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
        time_of_day_flag=minute,
    )


def _lot(buy_price=100.0, target=0.05, order_id="a"):
    return SimpleNamespace(buy_price=buy_price, profit_target=target, order_id=order_id)


def test_the_goal_is_measured_from_the_first_bar_with_equity():
    goal = DailyGoal(daily_goal=0.001, goal_lock=True)
    goal.observe(_ctx(2, 0, 0.0))  # a live replay's bar: equity 0, not an anchor
    assert goal.open_equity is None
    goal.observe(_ctx(2, 5, 100_000.0))
    assert goal.open_equity == 100_000.0 and not goal.reached
    goal.observe(_ctx(2, 6, 100_099.0))
    assert not goal.reached and not goal.harvest_now
    goal.observe(_ctx(2, 7, 100_100.0))
    assert goal.reached and goal.harvest_now, "the lock fires on the bar the goal is met"
    goal.observe(_ctx(2, 8, 100_200.0))
    assert goal.reached and not goal.harvest_now, "and only on that bar"
    goal.observe(_ctx(3, 0, 100_200.0))
    assert goal.open_equity == 100_200.0 and not goal.reached, "each session starts again"
    assert (goal.sessions, goal.goal_sessions) == (2, 1)


def test_the_closing_window_and_the_regular_session_only():
    goal = DailyGoal(eod_harvest_minute=380)
    goal.observe(_ctx(2, 379, 1.0))
    assert not goal.harvest_now
    goal.observe(_ctx(2, 380, 1.0))
    assert goal.harvest_now
    goal.observe(_ctx(2, -1, 1.0))
    assert not goal.harvest_now, "no harvest outside the regular session"


def test_a_take_profit_needs_the_minimum_gain_and_never_raises_a_target():
    goal = DailyGoal(eod_harvest_minute=0, harvest_min_gain=0.002)
    goal.observe(_ctx(2, 0, 1.0, price=100.1))
    assert goal.take_profit(_lot(), _ctx(2, 0, 1.0, price=100.1)) is None, "under the minimum"
    gain = goal.take_profit(_lot(), _ctx(2, 0, 1.0, price=101.0))
    assert gain == pytest.approx(0.01, abs=1e-6) and gain < 0.01, "at the market, never above"
    assert goal.take_profit(_lot(target=0.005), _ctx(2, 0, 1.0, price=101.0)) is None


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"daily_goal": 0.0}, "daily_goal"),
        ({"goal_lock": True}, "daily_goal"),
        ({"eod_harvest_minute": 390}, "eod_harvest_minute"),
        ({"eod_harvest_minute": 1.5}, "eod_harvest_minute"),
        ({"harvest_min_gain": 0.0}, "harvest_min_gain"),
    ],
)
def test_a_goal_that_cannot_mean_anything_is_refused(kwargs, match):
    with pytest.raises(ConfigurationError, match=match):
        DailyGoal(**kwargs)


# -- the buy side ----------------------------------------------------------------

UNIT = {"per_lot_pct": 0.01, "lookback_days": 1.0, "bars_per_day": 390}


def test_compounded_lots_follow_each_sessions_opening_equity():
    fixed = DailyUltimateSizing(**UNIT)
    compounded = DailyUltimateSizing(**UNIT, compound_lots=True)
    for day, minute, equity in [(2, 0, 100_000.0), (2, 200, 120_000.0)]:
        for strategy in (fixed, compounded):
            strategy.record_tick(_ctx(day, minute, equity))
    assert compounded.calculate_trade_value(_ctx(2, 200, 120_000.0)) == pytest.approx(1_000.0)
    for strategy in (fixed, compounded):
        strategy.record_tick(_ctx(3, 0, 150_000.0))
    assert compounded.calculate_trade_value(_ctx(3, 0, 150_000.0)) == pytest.approx(1_500.0)
    assert fixed.calculate_trade_value(_ctx(3, 0, 150_000.0)) == pytest.approx(1_000.0)


def test_the_goal_pauses_the_calm_grid_for_the_rest_of_the_session():
    calm = {date(2024, 1, 2): True, date(2024, 1, 3): True}
    strategy = DailyUltimateSizing(
        **UNIT, regime_by_date=calm, daily_goal=0.001, goal_pause_buys=True
    )
    strategy.record_tick(_ctx(2, 0, 100_000.0))
    assert strategy.mode == CALM
    assert strategy._grid_trigger_level(_ctx(2, 0, 100_000.0), 100.0, 0.002) > 0
    strategy.record_tick(_ctx(2, 1, 100_150.0))
    assert strategy._grid_trigger_level(_ctx(2, 1, 100_150.0), 100.0, 0.002) == NO_BUY_LEVEL
    strategy.record_tick(_ctx(3, 0, 100_150.0))
    assert strategy._grid_trigger_level(_ctx(3, 0, 100_150.0), 100.0, 0.002) > 0


def test_the_buy_policy_refuses_what_sells():
    with pytest.raises(ConfigurationError, match="eod_harvest_minute"):
        entries.build_entry("daily_ultimate", {**UNIT, "eod_harvest_minute": 380})
    with pytest.raises(ConfigurationError, match="daily_goal"):
        DailyUltimateSizing(**UNIT, goal_pause_buys=True)


# -- registry and live -----------------------------------------------------------


def _config(**overrides) -> BacktestConfig:
    data = {
        "strategy": {"strategy_id": "daily_ultimate", "strategy_params": dict(UNIT)},
        "grid": {"steps": [0.002], "profit_targets": [0.04]},
        "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
        "execution": {"allow_signal_exit": True},
        "live": {"enabled": True, "step": 0.002, "profit_target": 0.04},
    }
    for section, values in overrides.items():
        data[section] = {**data.get(section, {}), **values}
    return BacktestConfig.from_dict(data)


def test_it_is_registered_with_ultimates_regime_exit():
    assert STRATEGIES["daily_ultimate"] is DailyUltimateSizing
    assert may_realize_loss("daily_ultimate")
    assert isinstance(build_strategy(_config(), STRATEGIES), DailyUltimateSizing)


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"execution": {"allow_signal_exit": False}}, "allow_signal_exit"),
        ({"live": {"extended_hours": True}}, "extended_hours"),
        ({"live": {"profit_target": 0.06}}, "reversal_target"),
    ],
)
def test_a_live_deployment_that_is_not_the_researched_strategy_is_refused(overrides, match):
    with pytest.raises(ConfigurationError, match=match):
        build_strategy(_config(**overrides), STRATEGIES)


def test_it_asks_live_for_the_history_ultimate_asks_for():
    assert (
        DailyUltimateSizing(**UNIT, compound_lots=True).live_history_sessions()
        == UltimateSizing(**UNIT).live_history_sessions()
    )


def test_the_pinned_config_is_the_committed_default_with_the_signal_exit_on():
    from pathlib import Path

    from research.composition.book_exits import DAILY_ULTIMATE_EXIT_DEFAULTS
    from research.strategies.param_schema import STRATEGY_DEFAULTS

    path = Path(__file__).resolve().parents[2] / "config" / "daily_ultimate_tqqq.yaml"
    config = BacktestConfig.from_yaml(path)
    config.validate()
    assert config.strategy.strategy_id == "daily_ultimate"
    assert dict(config.strategy.strategy_params) == STRATEGY_DEFAULTS["daily_ultimate"]
    kwargs = config.to_run_sweep_kwargs(DailyUltimateSizing)
    assert kwargs["allow_signal_exit"] is True  # the regime exit reaches the engine
    assert kwargs["intrabar_fill"] == "causal"
    # The sell policy's seed reads the same regime and goal as the buy.
    params = STRATEGY_DEFAULTS["daily_ultimate"]
    for name, value in DAILY_ULTIMATE_EXIT_DEFAULTS.items():
        assert params[name] == value, name
