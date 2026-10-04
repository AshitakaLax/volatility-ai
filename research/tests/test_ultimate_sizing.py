"""research/strategies/ultimate_sizing.py -- calm is the champion sleeve
exactly, turbulent buys only capitulation closes, the flip liquidates calm
lots only, the internal regime equals the injected causal map, warm_up
seeds that regime like the bars it replaces, and the explicit constructor
mirrors GatedLocalReferenceSizing's so the server's run form sees it all."""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.optimization.optimization_controller import OptimizationController
from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing
from research.strategies.natr_regime import calm_by_date, daily_bars, debounce
from research.strategies.regime_sleeve_sizing import RegimeSleeveSizing
from research.strategies.strategy_registry import resolve_strategy
from research.strategies.ultimate_sizing import CALM, TURBULENT, TURBULENT_MODES, UltimateSizing

HF = {"per_lot_pct": 0.001, "lookback_days": 0.05, "bars_per_day": 20}
OUTCOMES = ("Final Equity", "Realized PnL", "Trade Count", "Closed Trade Count", "Max Drawdown %")


def _sessions(n: int = 300, seed: int = 1) -> pd.DataFrame:
    """n sessions of 20 one-minute bars (minutes 0-9 and 380-389, so the
    closing window exists); volatility regimes switch every 30 sessions
    and the turbulent ones trend down with big down days."""
    rng = np.random.default_rng(seed)
    rows, price = [], 100.0
    for k, day in enumerate(pd.bdate_range("2020-01-02", periods=n)):
        turbulent = (k // 30) % 2 == 1
        vol = 0.012 if turbulent else 0.002
        drift = -0.004 if turbulent else 0.0015
        for minute in [*range(10), *range(380, 390)]:
            ts = pd.Timestamp(day).tz_localize("UTC") + pd.Timedelta(hours=14, minutes=30 + minute)
            o = price
            price = price * np.exp(drift / 20 + vol * rng.standard_normal())
            rows.append((ts, o, max(o, price) * 1.0005, min(o, price) * 0.9995, price, 10_000))
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).set_index(
        "ts"
    )


def _run(df, cls, params, target=0.01, full=False, **sweep):
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[{**HF, **params}],
        fill_model="intrabar",
        intrabar_fill="causal",
        allow_signal_exit=True,
        return_full_results=full,
        **sweep,
    )


def test_all_calm_is_the_calm_regime_sleeve_exactly():
    df = _sessions(60)
    days = sorted({t.date() for t in df.index})
    calm = dict.fromkeys(days, True)
    a = _run(df, RegimeSleeveSizing, {"sleeve": "calm", "regime_by_date": calm}).iloc[0]
    b = _run(df, UltimateSizing, {"regime_by_date": calm}).iloc[0]
    assert a["Trade Count"] > 0
    for col in OUTCOMES:
        assert b[col] == a[col], col


def test_internal_regime_equals_the_injected_causal_map():
    df = _sessions(300)
    reg = debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)
    injected = _run(df, UltimateSizing, {"regime_by_date": reg, "reversal_threshold": -0.02}).iloc[
        0
    ]
    internal = _run(
        df,
        UltimateSizing,
        {
            "natr_period": 5,
            "natr_lookback": 20,
            "regime_min_hold": 3,
            "bear_dd": None,  # the injected map is the unfiltered regime
            "reversal_threshold": -0.02,
        },
    ).iloc[0]
    for col in OUTCOMES:
        assert internal[col] == injected[col], col


def test_turbulent_buys_only_reversal_lots_with_their_own_target_and_flip_liquidates_calm():
    df = _sessions(300)
    reg = debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)
    _, full = _run(
        df,
        UltimateSizing,
        {
            "regime_by_date": reg,
            "reversal_threshold": -0.02,
            "reversal_target": 0.02,
            "reversal_lot_pct": 0.05,
            "reversal_max_lots": 2,
        },
        target=0.30,
        full=True,
    )
    blot = full[0].trade_blotter
    buys = blot[blot["side"] == "buy"].copy()
    buys["day"] = buys["timestamp"].dt.date
    turbulent_days = {d for d, calm in reg.items() if not calm}
    tb = buys[buys["day"].isin(turbulent_days)]
    assert len(tb) > 0
    minute = tb["timestamp"].dt.hour * 60 + tb["timestamp"].dt.minute - (14 * 60 + 30)
    assert (minute >= 380).all()  # only in the closing window
    assert tb.groupby("day").size().max() == 1  # one per session
    notional = (tb["price"] * tb["qty"]).to_numpy()
    assert np.allclose(notional, 100_000 * 0.05, rtol=0.02)
    sells = blot[blot["side"] == "sell"]
    targets = sells[sells["sell_reason"].str.lower().str.contains("profit_target")]
    signal = sells[sells["sell_reason"].str.lower().str.contains("signal_exit")]
    reversal_ids = set(tb["lot_id"])
    assert set(signal["lot_id"]).isdisjoint(reversal_ids)  # flips liquidate calm lots only
    rev_sells = targets[targets["lot_id"].isin(reversal_ids)]
    assert len(rev_sells) > 0
    paid = buys.set_index("lot_id").loc[rev_sells["lot_id"], "price"].to_numpy()
    gain = rev_sells["price"].to_numpy() / paid - 1
    assert (gain < 0.05).all()  # sold near the 2% reversal target, not the 30% grid target
    assert (targets["profit_realized"] >= -1e-8).all()


def test_cash_mode_buys_nothing_while_turbulent():
    df = _sessions(300)
    reg = debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)
    _, full = _run(df, UltimateSizing, {"regime_by_date": reg, "turbulent_mode": "cash"}, full=True)
    buys = full[0].trade_blotter.query("side == 'buy'")
    turbulent_days = {d for d, calm in reg.items() if not calm}
    assert not buys["timestamp"].dt.date.isin(turbulent_days).any()


@pytest.mark.parametrize(
    "bad",
    [
        {"turbulent_mode": "short"},
        {"reversal_lot_pct": 0.0},
        {"reversal_target": 0.0},
        {"reversal_threshold": 0.01},
    ],
)
def test_bad_parameters(bad):
    with pytest.raises(ConfigurationError):
        UltimateSizing(**HF, **bad)


def test_delayed_regime_exit_fires_at_the_chosen_minute_of_the_flip_session():
    df = _sessions(300)
    reg = debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)
    _, full = _run(
        df,
        UltimateSizing,
        {"regime_by_date": reg, "turbulent_mode": "cash", "liquidate_minute": 381},
        full=True,
    )
    blot = full[0].trade_blotter
    sig = blot[(blot["side"] == "sell") & blot["sell_reason"].str.lower().str.contains("signal")]
    assert len(sig) > 0
    minute = sig["timestamp"].dt.hour * 60 + sig["timestamp"].dt.minute - (14 * 60 + 30)
    assert (minute == 381).all()  # this fixture's sessions have bars at 0-9 and 380-389
    flip_days = {
        d for d, prev in zip(sorted(reg)[1:], sorted(reg), strict=False) if reg[prev] and not reg[d]
    }
    assert set(sig["timestamp"].dt.date) <= flip_days


def _modes(strategy: UltimateSizing, df: pd.DataFrame) -> list:
    """Feed each bar to record_tick (as the decision cycle does first, every
    bar) and collect the mode after it."""
    out = []
    for i, (ts, row) in enumerate(df.iterrows()):
        strategy.record_tick(
            MarketContext(
                timestamp=ts,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                cash=100_000.0,
                equity=100_000.0,
                peak_equity=100_000.0,
                drawdown=0.0,
                open_lot_count=0,
                bar_index=i,
                time_of_day_flag=ts.hour * 60 + ts.minute - (14 * 60 + 30),
                volume=row["volume"],
            )
        )
        out.append(strategy.mode)
    return out


def test_warm_up_gives_the_live_run_the_regime_it_would_have_had():
    df = _sessions(300)
    cut = sorted({t.date() for t in df.index})[260]
    history, live = df[df.index.date < cut], df[df.index.date >= cut]
    kw = {**HF, "natr_period": 5, "natr_lookback": 20, "regime_min_hold": 3, "bear_dd": None}
    replayed = _modes(UltimateSizing(**kw), df)[len(history) :]
    cold = _modes(UltimateSizing(**kw), live)
    warm = UltimateSizing(**kw)
    assert warm.warm_up(daily_bars(history)) == 260
    seeded = _modes(warm, live)
    assert seeded == replayed
    assert {CALM, TURBULENT} <= set(seeded)
    assert set(cold) == {None}  # without history: no flag, so no buys, for the whole run


def test_warm_up_is_a_no_op_with_an_injected_regime():
    df = _sessions(30)
    calm = dict.fromkeys({t.date() for t in df.index}, True)
    assert UltimateSizing(**HF, regime_by_date=calm).warm_up(daily_bars(df)) == 0


def _parent_parameters() -> dict:
    sig = inspect.signature(GatedLocalReferenceSizing.__init__)
    return {name: p for name, p in sig.parameters.items() if name != "self"}


def test_constructor_mirrors_every_gated_parameter_without_a_catch_all():
    ours = inspect.signature(UltimateSizing.__init__).parameters
    assert not any(p.kind is inspect.Parameter.VAR_KEYWORD for p in ours.values())
    parents = _parent_parameters()
    assert [name for name in ours if name != "self"][: len(parents)] == list(parents)
    for name, parent in parents.items():
        assert ours[name].default == parent.default, name
        assert ours[name].kind is parent.kind, name


def test_every_gated_parameter_is_passed_through(monkeypatch):
    sentinels = {name: object() for name in _parent_parameters()}  # before the patch
    seen: dict = {}
    monkeypatch.setattr(GatedLocalReferenceSizing, "__init__", lambda self, **kw: seen.update(kw))
    UltimateSizing(**sentinels)
    assert seen.keys() == sentinels.keys()
    assert all(seen[name] is value for name, value in sentinels.items())


def test_a_sweep_handed_the_history_runs_the_window_on_the_full_history_regime():
    """run_sweep(warm_up_daily=...) -- the server's path. A window too short
    to warm the regime itself trades exactly as if the full-history causal
    map had been injected, and records how many sessions warmed it; the
    same window cold buys nothing."""
    df = _sessions(300)
    cut = sorted({t.date() for t in df.index})[260]
    history, live = df[df.index.date < cut], df[df.index.date >= cut]
    reg = debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)
    regime = {"natr_period": 5, "natr_lookback": 20, "regime_min_hold": 3, "bear_dd": None}
    injected = _run(live, UltimateSizing, {"regime_by_date": reg}).iloc[0]
    warmed = _run(live, UltimateSizing, regime, warm_up_daily=daily_bars(history)).iloc[0]
    cold = _run(live, UltimateSizing, regime).iloc[0]
    assert injected["Trade Count"] > 0
    for col in OUTCOMES:
        assert warmed[col] == injected[col], col
    assert warmed["warm_up_sessions"] == 260
    assert cold["Trade Count"] == 0 and "warm_up_sessions" not in cold


def test_a_sweep_refuses_warm_up_history_that_overlaps_the_run():
    df = _sessions(30)
    with pytest.raises(ConfigurationError):
        _run(df, UltimateSizing, {}, warm_up_daily=daily_bars(df))


def test_registered_with_server_defaults_and_choices_that_match_the_strategy():
    from server.backtest import (
        _HIDDEN_PARAMS,
        _PARAM_ENUMS,
        SIGNAL_EXIT_STRATEGIES,
        STRATEGY_DEFAULTS,
    )

    assert resolve_strategy("ultimate") is UltimateSizing
    assert _PARAM_ENUMS["turbulent_mode"] == list(TURBULENT_MODES)
    assert "regime_by_date" in _HIDDEN_PARAMS
    assert "ultimate" in SIGNAL_EXIT_STRATEGIES  # the regime exit is the design
    committed = STRATEGY_DEFAULTS["ultimate"]
    defaults = {
        name: p.default
        for name, p in inspect.signature(UltimateSizing.__init__).parameters.items()
        if name in committed and p.default is not inspect.Parameter.empty
    }
    ultimate_layer = set(inspect.signature(UltimateSizing.__init__).parameters) - set(
        _parent_parameters()
    )
    for name in ultimate_layer & set(committed):
        assert committed[name] == defaults[name], name  # one recommended configuration
    UltimateSizing(**committed)


def test_the_pinned_config_is_the_server_default_with_the_signal_exit_on():
    config = BacktestConfig.from_yaml(
        Path(__file__).resolve().parents[2] / "config" / "ultimate_tqqq.yaml"
    )
    config.validate()
    from server.backtest import STRATEGY_DEFAULTS

    assert config.strategy.strategy_id == "ultimate"
    assert dict(config.strategy.strategy_params) == STRATEGY_DEFAULTS["ultimate"]
    kwargs = config.to_run_sweep_kwargs(UltimateSizing)
    assert kwargs["allow_signal_exit"] is True  # the regime exit reaches the engine
    assert kwargs["intrabar_fill"] == "causal"
