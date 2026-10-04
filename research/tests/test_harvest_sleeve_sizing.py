"""research/strategies/harvest_sleeve_sizing.py -- off is RegimeSleeveSizing
exactly; each lever does what its docstring says; nothing sells below cost."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.optimization.optimization_controller import OptimizationController
from research.strategies.gated_local_reference_sizing import NO_BUY_LEVEL
from research.strategies.harvest_sleeve_sizing import HarvestSleeveSizing
from research.strategies.regime_sleeve_sizing import RegimeSleeveSizing

FIXTURE = "tests/fixtures/regression_ohlcv.csv"
FILL_MODELS = ("close", "intrabar")
OUTCOMES = (
    "Final Equity",
    "Total Return %",
    "Realized PnL",
    "Trade Count",
    "Closed Trade Count",
    "Open Trade Count",
    "Max Drawdown %",
    "CAGR %",
)
HF_PARAMS = {"per_lot_pct": 0.001, "lookback_days": 0.05, "bars_per_day": 120}


def _fixture() -> pd.DataFrame:
    return pd.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")


def _sessions(days: int = 6, drift: float = 0.0) -> pd.DataFrame:
    """`days` sessions of 120 one-minute bars oscillating +/-0.6% on a
    12-minute cycle, each session's level moved by `drift`."""
    frames, level = [], 100.0
    for day in range(days):
        start = pd.Timestamp("2024-01-02 14:30", tz="UTC") + pd.offsets.BDay(day)
        index = pd.date_range(start, periods=120, freq="1min")
        wave = level * (1 + 0.006 * np.sin(np.arange(120) * 2 * math.pi / 12))
        opens = np.r_[level, wave[:-1]]
        frames.append(
            pd.DataFrame(
                {
                    "open": opens,
                    "high": np.maximum(opens, wave) * 1.001,
                    "low": np.minimum(opens, wave) * 0.999,
                    "close": wave,
                    "volume": 10_000,
                },
                index=index,
            )
        )
        level *= 1 + drift
    return pd.concat(frames)


def _run(df, cls, fill_model="intrabar", extra=None, full=False, target=0.004):
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[{**HF_PARAMS, **(extra or {})}],
        fill_model=fill_model,
        return_full_results=full,
    )


def _ctx(minute: int = 0, price: float = 100.0, lots: int = 0, day: int = 0) -> MarketContext:
    ts = datetime(2024, 1, 2 + day, 14, 30, tzinfo=UTC) + timedelta(minutes=minute)
    return MarketContext(
        timestamp=ts,
        open=price,
        high=price,
        low=price,
        close=price,
        cash=1e5,
        equity=1e5,
        peak_equity=1e5,
        drawdown=0.0,
        open_lot_count=lots,
        bar_index=minute,
        time_of_day_flag=minute,
    )


# ---------------------------------------------------------------- off == parent


@pytest.mark.parametrize("fill_model", FILL_MODELS)
@pytest.mark.parametrize("data", ["fixture", "sessions"])
def test_defaults_reproduce_the_regime_sleeve_exactly(fill_model, data):
    df = _fixture() if data == "fixture" else _sessions()
    parent = _run(df, RegimeSleeveSizing, fill_model).iloc[0]
    harvest = _run(df, HarvestSleeveSizing, fill_model).iloc[0]
    assert parent["Trade Count"] > 0
    for column in OUTCOMES:
        assert harvest[column] == parent[column], column


def test_defaults_do_not_ask_for_retargeting():
    assert HarvestSleeveSizing(**HF_PARAMS).wants_lot_retargeting() is False


# ---------------------------------------------------------------- inventory


def test_inventory_decay_halves_each_successive_lot():
    _, full = _run(
        _sessions(drift=-0.01), HarvestSleeveSizing, extra={"inventory_decay": 0.5}, full=True
    )
    blot = full[0].trade_blotter
    buys = blot[blot["side"] == "buy"]
    notional = (buys["price"] * buys["qty"]).to_numpy()
    base = 100_000 * HF_PARAMS["per_lot_pct"]
    ks = np.log2(base / notional)
    assert np.allclose(ks, np.round(ks), atol=0.05)  # every lot is base / 2^k
    assert len(set(np.round(ks))) >= 2


def test_inventory_skew_deepens_the_rung_and_respects_the_cap():
    s = HarvestSleeveSizing(**HF_PARAMS, inventory_skew=0.5, skew_max_depth=0.02)
    assert s._effective_step(_ctx(lots=0), 0.004) == pytest.approx(0.004)
    assert s._effective_step(_ctx(lots=2), 0.004) == pytest.approx(0.004 * 2.0)
    assert s._effective_step(_ctx(lots=20), 0.004) == pytest.approx(0.02)


def test_volatility_step_reads_the_previous_bar_under_the_causal_fill():
    s = HarvestSleeveSizing(
        **HF_PARAMS, vol_step_window=3, vol_step_multiple=2.0, vol_step_min=0.0001
    )
    for i, p in enumerate([100, 101, 100, 101, 100]):
        s.record_tick(_ctx(minute=i, price=p))
    prev, now = s._step_prev, s._step_now
    assert prev is not None and now is not None
    assert s._effective_step(_ctx(minute=5), 0.01) == pytest.approx(now)
    s.use_prior_bar_trigger(True)
    assert s._effective_step(_ctx(minute=5), 0.01) == pytest.approx(prev)


# ---------------------------------------------------------------- target decay


def test_target_decays_linearly_to_the_floor_after_the_delay():
    s = HarvestSleeveSizing(
        **HF_PARAMS,
        target_decay_after_bars=10,
        target_decay_span_bars=20,
        target_floor=0.001,
        target_decay_check_bars=1,
    )
    lot = SimpleNamespace(order_id="L1", profit_target=0.021)
    s.record_tick(_ctx(minute=0, lots=1))
    assert s.adjust_profit_target(lot, _ctx()) is None  # first sight: age 0
    for m in range(1, 11):
        s.record_tick(_ctx(minute=m, lots=1))
    assert s.adjust_profit_target(lot, _ctx()) is None  # age 10: not yet
    for m in range(11, 21):
        s.record_tick(_ctx(minute=m, lots=1))
    halfway = s.adjust_profit_target(lot, _ctx())
    assert halfway == pytest.approx(0.021 - 0.020 * 0.5)
    lot.profit_target = halfway
    for m in range(21, 60):
        s.record_tick(_ctx(minute=m, lots=1))
    assert s.adjust_profit_target(lot, _ctx()) == pytest.approx(0.001)
    s.retain_lots(set())
    assert s._births == {}


def test_retargeting_is_requested_only_when_it_can_matter():
    s = HarvestSleeveSizing(**HF_PARAMS, target_decay_after_bars=5, target_decay_check_bars=10)
    s.record_tick(_ctx(minute=0, lots=0))  # bar 0: a check bar
    assert s.wants_lot_retargeting()
    s.record_tick(_ctx(minute=1, lots=0))
    assert not s.wants_lot_retargeting()
    s.record_tick(_ctx(minute=2, lots=1))  # a new lot appeared
    assert s.wants_lot_retargeting()


def test_target_decay_frees_stuck_lots_without_a_single_losing_sale():
    df = _sessions(days=8, drift=-0.01)
    _, base = _run(df, HarvestSleeveSizing, full=True, target=0.02)
    _, full = _run(
        df,
        HarvestSleeveSizing,
        full=True,
        target=0.02,
        extra={"target_decay_after_bars": 30, "target_decay_span_bars": 60, "target_floor": 0.0005},
    )
    sells = full[0].trade_blotter.query("side == 'sell'")
    base_sells = base[0].trade_blotter.query("side == 'sell'")
    assert len(sells) > len(base_sells)
    assert (sells["profit_realized"] >= -1e-8).all()


# ---------------------------------------------------------------- gates and validation


def test_session_throttle_shuts_the_level_after_the_session_cap():
    s = HarvestSleeveSizing(**HF_PARAMS, session_throttle="on", throttle_max_lots=1)
    s.record_tick(_ctx(minute=0, lots=0))
    assert s._grid_trigger_level(_ctx(minute=0), 100.0, 0.01) > 0
    s.record_tick(_ctx(minute=1, lots=1))  # one buy recorded
    assert s._grid_trigger_level(_ctx(minute=1, lots=1), 100.0, 0.01) == NO_BUY_LEVEL
    s.record_tick(_ctx(minute=0, lots=1, day=1))  # new session resets the cap
    assert s._grid_trigger_level(_ctx(minute=0, lots=1, day=1), 100.0, 0.01) > 0


@pytest.mark.parametrize(
    "bad",
    [
        {"inventory_decay": 0.0},
        {"inventory_skew": -1.0},
        {"skew_max_depth": 1.5},
        {"target_decay_after_bars": 5, "target_floor": 0.0},
        {"target_decay_after_bars": -1},
        {"noise_gate": "sideways"},
    ],
)
def test_bad_parameters_fail_at_construction(bad):
    with pytest.raises(ConfigurationError):
        HarvestSleeveSizing(**HF_PARAMS, **bad)


# ---------------------------------------------------------------- close reversal


def _bar(day: int, minute: int, price: float, lots: int = 0) -> MarketContext:
    return _ctx(minute=minute, price=price, lots=lots, day=day)


def _feed_session(s, day, prices, lots=0):
    """One session of bars at minutes 0..len-1, but the last 12 bars are
    placed at minutes 378..389 so the closing window is exercised."""
    n = len(prices)
    minutes = list(range(n - 12)) + list(range(378, 390))
    for m, p in zip(minutes, prices, strict=True):
        s.record_tick(_bar(day, m, p, lots))
    return minutes


def test_reversal_signal_opens_only_in_the_closing_window_of_a_down_session():
    s = HarvestSleeveSizing(
        **HF_PARAMS, reversal_gate="close", reversal_threshold=-0.02, reversal_minutes=10
    )
    _feed_session(s, 0, [100.0] * 20)  # prior close 100
    for m in range(0, 8):  # session 2 falls 3% early -- far from the close
        s.record_tick(_bar(1, m, 97.0))
        assert s._grid_trigger_level(_bar(1, m, 97.0), 100.0, 0.01) == NO_BUY_LEVEL
    s.record_tick(_bar(1, 379, 97.0))  # minute 379 < 390 - 10: still shut
    assert s._grid_trigger_level(_bar(1, 379, 97.0), 100.0, 0.01) == NO_BUY_LEVEL
    s.record_tick(_bar(1, 381, 96.9))  # inside the window, down 3.1%
    assert s._grid_trigger_level(_bar(1, 381, 96.9), 100.0, 0.01) == pytest.approx(96.9)
    s.record_tick(_bar(1, 382, 99.0))  # recovered to -1%: shut again
    assert s._grid_trigger_level(_bar(1, 382, 99.0), 100.0, 0.01) == NO_BUY_LEVEL


def test_reversal_causal_level_reads_the_previous_bar_and_never_crosses_sessions():
    s = HarvestSleeveSizing(
        **HF_PARAMS, reversal_gate="close", reversal_threshold=-0.02, reversal_minutes=10
    )
    s.use_prior_bar_trigger(True)
    _feed_session(s, 0, [100.0] * 20)
    s.record_tick(_bar(1, 385, 97.0))  # decided at the end of this bar ...
    assert s._grid_trigger_level(_bar(1, 385, 97.0), 100.0, 0.01) == NO_BUY_LEVEL
    s.record_tick(_bar(1, 386, 96.5))  # ... applied to the next, at that bar's level
    assert s._grid_trigger_level(_bar(1, 386, 96.5), 100.0, 0.01) == pytest.approx(97.0)
    s.record_tick(_bar(1, 389, 96.0))
    s.record_tick(_bar(2, 0, 95.0))  # next morning: the last decision does not carry
    assert s._grid_trigger_level(_bar(2, 0, 95.0), 100.0, 0.01) == NO_BUY_LEVEL


def test_reversal_sleeve_buys_only_on_qualifying_closes_and_never_sells_at_a_loss():
    frames, level = [], 100.0
    for day, session_ret in enumerate([0.0, -0.03, 0.02, -0.01, -0.04, 0.03, 0.01]):
        start = pd.Timestamp("2024-01-02 14:30", tz="UTC") + pd.offsets.BDay(day)
        index = pd.date_range(start, periods=390, freq="1min")
        path = (
            level
            * (1 + session_ret * np.linspace(0, 1, 390))
            * (1 + 0.001 * np.sin(np.arange(390)))
        )
        opens = np.r_[level, path[:-1]]
        frames.append(
            pd.DataFrame(
                {
                    "open": opens,
                    "high": np.maximum(opens, path) * 1.0005,
                    "low": np.minimum(opens, path) * 0.9995,
                    "close": path,
                    "volume": 10_000,
                },
                index=index,
            )
        )
        level = path[-1]
    df = pd.concat(frames)
    _, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.01],
        strategy_class=HarvestSleeveSizing,
        strategy_params_grid=[
            {
                "per_lot_pct": 0.05,
                "lookback_days": 0.05,
                "bars_per_day": 390,
                "reversal_gate": "close",
                "reversal_threshold": -0.02,
                "reversal_minutes": 10,
            }
        ],
        fill_model="intrabar",
        intrabar_fill="causal",
        return_full_results=True,
    )
    blot = full[0].trade_blotter
    buys = blot[blot["side"] == "buy"]
    assert len(buys) == 2  # the -3% and -4% sessions, one each
    minutes = buys["timestamp"].dt.hour * 60 + buys["timestamp"].dt.minute - (14 * 60 + 30)
    assert (minutes >= 380).all()
    sells = blot[blot["side"] == "sell"]
    assert (sells["profit_realized"] >= -1e-8).all()


@pytest.mark.parametrize(
    "bad", [{"reversal_gate": "open"}, {"reversal_threshold": 0.01}, {"reversal_minutes": 0}]
)
def test_bad_reversal_parameters(bad):
    with pytest.raises(ConfigurationError):
        HarvestSleeveSizing(**HF_PARAMS, **bad)


# ---------------------------------------------------------------- regime-exit timing and fraction


def _flip_sessions():
    """Three calm sessions of choppy decline (lots accumulate), then two
    turbulent ones: the calm sleeve must exit on the fourth session."""
    df = _sessions(days=5, drift=-0.004)
    days = sorted({t.date() for t in df.index})
    reg = {d: i < 3 for i, d in enumerate(days)}
    return df, reg, days


def _exits(extra):
    df, reg, days = _flip_sessions()
    _, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.05],
        strategy_class=HarvestSleeveSizing,
        strategy_params_grid=[{**HF_PARAMS, "sleeve": "calm", "regime_by_date": reg, **extra}],
        fill_model="intrabar",
        allow_signal_exit=True,
        return_full_results=True,
    )
    blot = full[0].trade_blotter
    sells = blot[(blot["side"] == "sell") & blot["sell_reason"].str.lower().str.contains("signal")]
    buys = blot[blot["side"] == "buy"].set_index("lot_id")
    return sells, buys, days


def test_delayed_regime_exit_happens_at_the_chosen_minute():
    sells, _, days = _exits({"liquidate_minute": 60})
    assert len(sells) > 0
    assert set(sells["timestamp"].dt.date) == {days[3]}
    minute = sells["timestamp"].dt.hour * 60 + sells["timestamp"].dt.minute - (14 * 60 + 30)
    assert (minute == 60).all()


def test_partial_regime_exit_sells_the_highest_cost_fraction():
    full_sells, _, _ = _exits({})
    part_sells, buys2, _ = _exits({"liquidate_fraction": 0.5})
    n = len(full_sells)
    assert n > 2 and len(part_sells) == math.ceil(0.5 * n)
    held_costs = buys2.loc[part_sells["lot_id"], "price"]
    open_at_flip = buys2.loc[full_sells["lot_id"], "price"]
    assert held_costs.min() >= open_at_flip.median() - 1e-9  # the dearer half went


@pytest.mark.parametrize("bad", [{"liquidate_minute": 390}, {"liquidate_fraction": 0.0}])
def test_bad_liquidation_parameters(bad):
    with pytest.raises(ConfigurationError):
        HarvestSleeveSizing(**HF_PARAMS, **bad)
