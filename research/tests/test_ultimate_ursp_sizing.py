"""research/strategies/ultimate_ursp_sizing.py -- the gated target equals an
independent vectorised computation session for session, the gate is the
documented linear ramp, warm-up carries the gate's history too, the engine
trades the internal target exactly like the injected map, and the
registration, server wiring and pinned config agree."""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import talib

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from research.optimization.optimization_controller import OptimizationController
from research.strategies.natr_regime import daily_bars
from research.strategies.strategy_registry import resolve_strategy
from research.strategies.ultimate_ursp_sizing import BearGatedTimingSignal, UltimateUrspSizing

SMALL = {
    "pd_periods": "5,8",
    "pd_lookbacks": "20,30",
    "ad_params": "3/10",
    "ad_lookbacks": "20",
    "bear_window": 40,
    "bear_dd_start": 0.05,
    "bear_dd_full": 0.15,
}
OUTCOMES = ("Final Equity", "Realized PnL", "Trade Count", "Closed Trade Count", "Max Drawdown %")


def _sessions(n: int = 180, seed: int = 5) -> pd.DataFrame:
    """Minute bars (minutes 0-6 and 60-66) with a crash in the middle, so
    the bear gate closes and reopens."""
    rng = np.random.default_rng(seed)
    rows, price = [], 100.0
    for k, day in enumerate(pd.bdate_range("2022-01-03", periods=n)):
        drift = -0.012 if 70 <= k < 95 else 0.0012
        vol = 0.012 if 60 <= k < 110 else 0.004
        for minute in [*range(7), *range(60, 67)]:
            ts = pd.Timestamp(day).tz_localize("America/New_York") + pd.Timedelta(
                hours=9, minutes=30 + minute
            )
            o = price
            price *= np.exp(drift / 14 + vol * rng.standard_normal())
            rows.append(
                (
                    ts.tz_convert("UTC"),
                    o,
                    max(o, price) * 1.001,
                    min(o, price) * 0.999,
                    price,
                    float(rng.integers(1_000, 40_000)),
                )
            )
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).set_index(
        "ts"
    )


def _daily(minutes: pd.DataFrame) -> pd.DataFrame:
    et = minutes.index.tz_convert("America/New_York")
    g = minutes.groupby(et.normalize().tz_localize(None))
    return pd.DataFrame(
        {
            "high": g["high"].max(),
            "low": g["low"].min(),
            "close": g["close"].last(),
            "volume": g["volume"].sum(),
        }
    )


def _reference(daily: pd.DataFrame) -> tuple[dict, dict]:
    """{session: target} and {session: gate}, vectorised, each keyed by the
    session it applies to."""
    H, L, C, V = (daily[k].to_numpy(float) for k in ("high", "low", "close", "volume"))

    def below(x, lb):
        s = pd.Series(x, index=daily.index)
        return (s < s.rolling(lb, min_periods=lb).median()).fillna(False).astype(float)

    pdv = [below(talib.PLUS_DM(H, L, timeperiod=p), lb) for p in (5, 8) for lb in (20, 30)]
    adv = [below(talib.ADOSC(H, L, C, V, fastperiod=3, slowperiod=10), 20)]
    ens = 0.5 * sum(pdv) / 4 + 0.5 * sum(adv) / 1
    dd = 1 - daily["close"] / daily["close"].rolling(40, min_periods=1).max()
    gate = ((0.15 - dd) / 0.10).clip(0, 1)
    days = [t.date() for t in daily.index]
    tgt = ens * gate
    return (
        {days[i + 1]: float(tgt.iloc[i]) for i in range(len(days) - 1)},
        {days[i + 1]: float(gate.iloc[i]) for i in range(len(days) - 1)},
    )


def _signal() -> BearGatedTimingSignal:
    return BearGatedTimingSignal(
        bear_window=40,
        bear_dd_start=0.05,
        bear_dd_full=0.15,
        pd_periods=(5, 8),
        pd_lookbacks=(20, 30),
        ad_params=((3, 10),),
        ad_lookbacks=(20,),
    )


def test_the_gated_target_equals_the_vectorised_reference():
    minutes = _sessions()
    ref_target, ref_gate = _reference(_daily(minutes))
    sig, got_t, got_g, day = _signal(), {}, {}, None
    for ts, row in minutes.iterrows():
        sig.observe(ts, row["high"], row["low"], row["close"], row["volume"])
        d = ts.tz_convert("America/New_York").date()
        if d != day:
            day = d
            if sig.target is not None:
                got_t[d], got_g[d] = sig.target, sig.gate
    assert got_t == pytest.approx(ref_target)
    assert got_g == pytest.approx(ref_gate)
    assert min(got_g.values()) == 0.0 and max(got_g.values()) == 1.0  # the crash shut the gate
    assert any(0 < g < 1 for g in got_g.values())  # and it ramps, not flips


def test_warm_up_carries_the_gate_history():
    minutes = _sessions()
    cut = sorted({t.tz_convert("America/New_York").date() for t in minutes.index})[90]
    et_dates = minutes.index.tz_convert("America/New_York").date
    hist = minutes[et_dates < cut]
    full, seeded = _signal(), _signal()
    d = _daily(hist)
    assert seeded.warm_up(d) == 90
    for ts, row in minutes.iterrows():
        full.observe(ts, row["high"], row["low"], row["close"], row["volume"])
        if ts.tz_convert("America/New_York").date() >= cut:
            seeded.observe(ts, row["high"], row["low"], row["close"], row["volume"])
            assert seeded.target == pytest.approx(full.target)
            assert seeded.gate == pytest.approx(full.gate)


def _run(df, params, **sweep):
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.001],
        profit_targets=[10.0],
        strategy_class=UltimateUrspSizing,
        strategy_params_grid=[params],
        fill_model="intrabar",
        intrabar_fill="causal",
        allow_signal_exit=True,
        **sweep,
    )


def test_through_the_engine_the_internal_target_trades_like_the_injected_map():
    minutes = _sessions()
    ref_target, _ = _reference(_daily(minutes))
    internal = _run(minutes, {**SMALL, "rebalance_band": 0.05}).iloc[0]
    injected = _run(minutes, {"exposure_by_date": ref_target, "rebalance_band": 0.05}).iloc[0]
    assert internal["Trade Count"] > 10
    for col in OUTCOMES:
        assert internal[col] == pytest.approx(injected[col]), col


def test_a_wider_band_trades_less():
    minutes = _sessions()
    narrow = _run(minutes, {**SMALL, "rebalance_band": 0.05}).iloc[0]["Trade Count"]
    wide = _run(minutes, {**SMALL, "rebalance_band": 0.20}).iloc[0]["Trade Count"]
    assert wide < narrow


@pytest.mark.parametrize(
    "bad",
    [
        {"bear_window": 1},
        {"bear_dd_start": 0.6, "bear_dd_full": 0.5},
        {"bear_dd_full": 1.0},
        {"rebalance_band": 0.0},
        {"pd_periods": "x"},
    ],
)
def test_bad_parameters(bad):
    with pytest.raises(ConfigurationError):
        UltimateUrspSizing(**bad)


def test_every_form_parameter_is_a_plain_scalar():
    for name, p in inspect.signature(UltimateUrspSizing.__init__).parameters.items():
        if name in ("self", "exposure_by_date"):
            continue
        assert isinstance(p.default, (str, int, float)), name


def test_registered_with_server_wiring_that_matches_the_strategy():
    from server.backtest import (
        _HIDDEN_PARAMS,
        SIGNAL_EXIT_STRATEGIES,
        STRATEGY_DEFAULTS,
        describe_grid_trigger,
    )

    assert resolve_strategy("ultimate_ursp") is UltimateUrspSizing
    assert "exposure_by_date" in _HIDDEN_PARAMS
    assert "ultimate_ursp" in SIGNAL_EXIT_STRATEGIES
    assert describe_grid_trigger("ultimate_ursp") == {"methods": ["exposure_target"]}
    defaults = {
        n: p.default for n, p in inspect.signature(UltimateUrspSizing.__init__).parameters.items()
    }
    for name, value in STRATEGY_DEFAULTS["ultimate_ursp"].items():
        assert defaults[name] == value, name
    UltimateUrspSizing(**STRATEGY_DEFAULTS["ultimate_ursp"])


def test_the_pinned_config_is_the_server_default_with_the_signal_exit_on():
    from server.backtest import STRATEGY_DEFAULTS

    config = BacktestConfig.from_yaml(
        Path(__file__).resolve().parents[2] / "config" / "ultimate_ursp.yaml"
    )
    config.validate()
    assert config.strategy.strategy_id == "ultimate_ursp"
    assert dict(config.strategy.strategy_params) == STRATEGY_DEFAULTS["ultimate_ursp"]
    kwargs = config.to_run_sweep_kwargs(UltimateUrspSizing)
    assert kwargs["allow_signal_exit"] is True
    assert kwargs["profit_targets"] == [10.0]


def test_daily_bars_helper_matches_the_test_aggregation():
    """Guard for the reference above: the natr_regime helper and the local
    aggregation agree on these regular-hours sessions."""
    minutes = _sessions(30)
    a = daily_bars(minutes)
    b = _daily(minutes)
    np.testing.assert_allclose(a["close"].to_numpy(), b["close"].to_numpy())
