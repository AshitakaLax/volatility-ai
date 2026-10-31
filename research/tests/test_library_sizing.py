"""The single-symbol algorithm library: research/strategies/signal_library.py
components and LibrarySizing, one strategy id per algorithm.

  1. signal="off" IS hf_entry_gated, under both fill models.
  2. Every algorithm has its own registered id, constructible from its
     committed defaults (or failing, naming the data file it needs), and
     runs end to end through the real controller.
  3. Each component does what its source says on data built to show it,
     reading only completed sessions or bars.
  4. Nothing here can sell.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.optimization.optimization_controller import OptimizationController
from research.strategies import signal_library as sl
from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing
from research.strategies.library_sizing import SIGNAL_NAMES, LibrarySizing, library_strategy_ids
from research.strategies.param_schema import (
    _PARAM_ENUMS,
    LIBRARY_SIGNALS,
    STRATEGY_DEFAULTS,
    describe_params,
)
from research.strategies.strategy_registry import STRATEGIES, resolve_strategy

FIXTURE = "tests/fixtures/regression_ohlcv.csv"
HF = {"per_lot_pct": 0.001, "lookback_days": 0.05, "bars_per_day": 120}
OUTCOMES = ("Final Equity", "Realized PnL", "Trade Count", "Closed Trade Count", "Max Drawdown %")
NEEDS_DATA = {
    "vix_term",
    "lead_lag",
    "breadth_thrust",
    "causal_impact",
    "transfer_entropy",
    "sentiment",
    "event_sentiment",
}


def ctx(day, minute, close, high=None, low=None, open_=None, volume=1000.0, lots=0):
    ts = datetime(2023, 1, 2, 14, 30) + timedelta(days=day, minutes=minute)
    return MarketContext(
        timestamp=ts,
        open=open_ if open_ is not None else close,
        high=high if high is not None else close,
        low=low if low is not None else close,
        close=close,
        cash=1e5,
        equity=1e5,
        peak_equity=1e5,
        drawdown=0.0,
        open_lot_count=lots,
        bar_index=day * 1000 + minute,
        time_of_day_flag=minute,
        volume=volume,
    )


def feed_daily(component, closes, bars=2, highs=None, lows=None):
    for d, c in enumerate(closes):
        for m in range(bars):
            h = highs[d] if highs is not None else c
            lo = lows[d] if lows is not None else c
            component.observe(ctx(d, m, c, h, lo))
    c = closes[-1]
    component.observe(ctx(len(closes), 0, c))


def _fixture():
    return pd.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")


def _sessions(days=260, bars=30, seed=0):
    rng = np.random.default_rng(seed)
    frames, p = [], 100.0
    for d in range(days):
        start = pd.Timestamp("2022-01-03 14:30", tz="UTC") + pd.offsets.BDay(d)
        idx = pd.date_range(start, periods=bars, freq="13min")
        r = rng.normal(0.0002, 0.004, bars)
        c = p * np.exp(np.cumsum(r))
        o = np.r_[p, c[:-1]]
        frames.append(
            pd.DataFrame(
                {
                    "open": o,
                    "high": np.maximum(o, c) * 1.001,
                    "low": np.minimum(o, c) * 0.999,
                    "close": c,
                    "volume": rng.integers(500, 1500, bars),
                },
                index=idx,
            )
        )
        p = c[-1]
    return pd.concat(frames)


def _run(df, cls, extra=None, fill_model="close", bars_per_day=120):
    return (
        OptimizationController(historical_data=df)
        .run_sweep(
            grid_steps=[0.003],
            profit_targets=[0.004],
            strategy_class=cls,
            strategy_params_grid=[{**HF, "bars_per_day": bars_per_day, **(extra or {})}],
            fill_model=fill_model,
        )
        .iloc[0]
    )


# --------------------------------------------------------------- 1. off is hf_entry_gated


@pytest.mark.parametrize("fill_model", ["close", "intrabar"])
def test_signal_off_is_hf_entry_gated_exactly(fill_model):
    df = _fixture()
    gated = _run(df, GatedLocalReferenceSizing, fill_model=fill_model)
    lib = _run(df, LibrarySizing, fill_model=fill_model)
    assert gated["Trade Count"] > 0
    for col in OUTCOMES:
        assert lib[col] == gated[col], col


def test_signature_mirrors_the_parent():
    parent = list(inspect.signature(GatedLocalReferenceSizing.__init__).parameters.values())
    child = list(inspect.signature(LibrarySizing.__init__).parameters.values())
    assert [(p.name, p.default, p.annotation, p.kind) for p in parent] == [
        (p.name, p.default, p.annotation, p.kind) for p in child[: len(parent)]
    ]
    assert [p.name for p in child[len(parent) :]] == ["signal", "signal_params"]


# --------------------------------------------------------------- 2. one id per algorithm


def test_every_algorithm_has_its_own_registered_id():
    ids = library_strategy_ids()
    assert ids == LIBRARY_SIGNALS
    assert len(ids) == len(sl.SIGNALS) == 50
    for sid, name in ids.items():
        assert resolve_strategy(sid) is LibrarySizing
        assert STRATEGY_DEFAULTS[sid]["signal"] == name
        assert sid == f"{sl.SIGNALS[name].ledger.lower()}_{name}"
    assert _PARAM_ENUMS["signal"] == list(SIGNAL_NAMES)


def test_the_form_seeds_the_algorithm_and_its_parameters():
    specs = {s["name"]: s for s in describe_params("rk44_supertrend", LibrarySizing)}
    assert specs["signal"]["suggested"] == "supertrend"
    assert "locked" not in specs["signal"] and "locked" not in specs["signal_params"]


@pytest.mark.parametrize("sid", sorted(LIBRARY_SIGNALS))
def test_constructible_from_its_committed_defaults(sid):
    name = LIBRARY_SIGNALS[sid]
    s = LibrarySizing(**STRATEGY_DEFAULTS[sid])
    assert s.component is not None and s.component.kind in ("gate", "sizer", "level")
    assert s.live_history_sessions() >= 2
    if name in NEEDS_DATA:
        # built, so the form can describe it -- but a run stops on its first
        # bar naming the file to supply, never a silent no-op
        with pytest.raises(ConfigurationError, match="signal_params"):
            s.record_tick(ctx(0, 0, 100))


FAST = sorted(
    n for n in sl.SIGNALS if n not in NEEDS_DATA | {"tda_level", "tda_variance", "tda_rips"}
)


@pytest.mark.parametrize("name", FAST)
def test_every_algorithm_runs_end_to_end(name):
    row = _run(_sessions(days=120), LibrarySizing, {"signal": name}, bars_per_day=30)
    assert "error" not in row.index or pd.isna(row.get("error")), row.get("error")
    assert row["Trade Count"] >= 0


def test_signal_params_parse_and_reject():
    assert sl.parse_signal_params("supertrend", "n=7, mult=2.5") == {"n": 7, "mult": 2.5}
    assert sl.parse_signal_params("rf_seqboot", "span=3") == {"span": 3}
    with pytest.raises(ConfigurationError, match="no parameter"):
        sl.parse_signal_params("supertrend", "window=3")
    with pytest.raises(ConfigurationError, match="key=value"):
        sl.parse_signal_params("supertrend", "7")
    assert sl.parse_signal_params("trend_scan", "spans=5,10,t_min=2") == {
        "spans": "5,10",
        "t_min": 2.0,
    }
    with pytest.raises(ConfigurationError):
        LibrarySizing(**HF, signal="nope")
    # a fixed setting is not tunable: the algorithm is the id
    assert "sequential_bootstrap" not in sl.signal_parameters("rf_seqboot")


# --------------------------------------------------------------- 3. components


def test_supertrend_and_ma_cross_block_downtrends_only():
    for name in ("supertrend", "ma_cross"):
        down = sl.build_signal(name, "fast=5,slow=20" if name == "ma_cross" else "n=5")
        closes = [100 * 0.99**i for i in range(80)]
        feed_daily(
            down, closes, highs=[c * 1.005 for c in closes], lows=[c * 0.995 for c in closes]
        )
        assert down.suppressed, name
        up = sl.build_signal(name, "fast=5,slow=20" if name == "ma_cross" else "n=5")
        closes = [100 * 1.01**i for i in range(80)]
        feed_daily(up, closes, highs=[c * 1.005 for c in closes], lows=[c * 0.995 for c in closes])
        assert not up.suppressed, name


def test_mtf_trend_needs_every_horizon_up():
    g = sl.build_signal("mtf_trend", "horizons=5,10")
    feed_daily(g, [100 + i for i in range(20)])
    assert not g.suppressed
    feed_daily(g, [120 + i for i in range(15)] + [100])
    assert g.suppressed


def test_hmm_blocks_in_the_volatile_state():
    rng = np.random.default_rng(0)
    calm = np.cumsum(rng.normal(0, 0.003, 300))
    wild = calm[-1] + np.cumsum(rng.normal(0, 0.04, 40))
    closes = list(100 * np.exp(np.r_[calm, wild]))
    g = sl.build_signal("hmm", "window=300,refit=5")
    feed_daily(g, closes)
    assert g.suppressed and g.prob_high > 0.6
    h = sl.build_signal("hhmm", "window=300,refit=5")  # trend level: 100 sessions
    feed_daily(h, [*closes[:-1], closes[-101] * 1.2])  # volatile but above its level
    assert not h.suppressed


def test_hurst_regime_blocks_a_trending_fall():
    """Persistent (positively autocorrelated) falling returns trend; white
    noise around a level does not."""
    rng = np.random.default_rng(1)
    r = [0.0]
    for _ in range(300):
        r.append(-0.002 + 0.6 * r[-1] + rng.normal(0, 0.005))
    g = sl.build_signal("hurst_regime", "window=200,max_lag=20")
    feed_daily(g, list(100 * np.exp(np.cumsum(r))))
    assert g.suppressed
    noise = 100 * np.exp(rng.normal(0, 0.01, 300))
    g = sl.build_signal("hurst_regime", "window=200,max_lag=20")
    feed_daily(g, list(noise))
    assert not g.suppressed


def test_trend_scan_reads_only_the_past():
    g = sl.build_signal("trend_scan", "spans=5,10,t_min=2")
    feed_daily(g, [100 - i for i in range(15)])
    assert g.suppressed and g.t_value < -2


def test_orb_breakout_waits_for_a_close_above_the_range():
    g = sl.build_signal("orb", "minutes=3")
    for m, p in enumerate([100, 101, 100.5]):  # the opening range: high 101
        g.observe(ctx(0, m, p, high=p))
    assert g.suppressed
    g.observe(ctx(0, 3, 101.5, high=101.6))
    assert g.suppressed  # not yet history
    g.observe(ctx(0, 4, 101.4))
    assert not g.suppressed
    g.observe(ctx(1, 0, 100))
    assert g.suppressed  # a new session resets


def test_overnight_allows_only_the_close():
    g = sl.build_signal("overnight", "minutes=30")
    g.observe(ctx(0, 100, 1))
    assert g.suppressed
    g.observe(ctx(0, 370, 1))
    assert not g.suppressed


def test_ema_pullback_is_a_permission_in_an_uptrend():
    g = sl.build_signal("ema_pullback", "fast=3,slow=10")
    for d in range(30):
        c = 100 + d
        g.observe(ctx(d, 0, c))
        g.observe(ctx(d, 1, c))
    g.observe(ctx(30, 0, 120))
    g.observe(ctx(30, 1, 120))  # the previous bar closed below the fast EMA (~128)
    assert not g.suppressed
    g.observe(ctx(30, 2, 140))
    g.observe(ctx(30, 3, 140))
    assert g.suppressed


def test_sizers_scale_with_their_inputs():
    atr = sl.build_signal("atr_sizing", "n=5,target=0.02")
    closes = [100.0] * 20
    feed_daily(atr, closes, highs=[101.0] * 20, lows=[99.0] * 20)  # NATR 2%
    assert atr.multiplier == pytest.approx(1.0, rel=0.05)
    kelly = sl.build_signal("kelly", "window=50,fraction=0.5")
    rng = np.random.default_rng(3)
    feed_daily(kelly, list(100 * np.exp(np.cumsum(0.002 + rng.normal(0, 0.01, 80)))))
    assert kelly.multiplier > 0
    falling = sl.build_signal("kelly", "window=50")
    feed_daily(falling, list(100 * np.exp(np.cumsum(-0.003 + rng.normal(0, 0.01, 80)))))
    assert falling.multiplier == 0.0


def test_garch_sizes_down_after_a_volatility_burst():
    rng = np.random.default_rng(4)
    r, s2 = [], 1e-4
    for _ in range(400):  # a GARCH(1,1) path, so the fit has clustering to find
        x = rng.normal(0, np.sqrt(s2))
        r.append(x)
        s2 = 2e-6 + 0.1 * x * x + 0.88 * s2
    r += list(rng.normal(0, 0.06, 5))
    g = sl.build_signal("garch", "window=300,refit=50")
    feed_daily(g, list(100 * np.exp(np.cumsum(r))))
    assert g.multiplier < 0.8


def test_evt_and_conformal_sizers():
    rng = np.random.default_rng(5)
    calm = sl.build_signal("evt", "window=200,es_budget=0.5")
    feed_daily(calm, list(100 * np.exp(np.cumsum(rng.normal(0, 0.005, 250)))))
    assert calm.multiplier == 1.0
    wild = sl.build_signal("evt", "window=200,es_budget=0.01")
    feed_daily(wild, list(100 * np.exp(np.cumsum(rng.standard_t(3, 250) * 0.02))))
    assert wild.multiplier < 1.0
    for name in ("conformal", "conformal_stack"):
        up = sl.build_signal(name, "train=60,calibration=40,alpha=0.5,floor=0.25")
        feed_daily(up, list(100 * np.exp(np.cumsum(0.01 + rng.normal(0, 0.001, 150)))))
        assert up.multiplier == 1.0, name
        flat = sl.build_signal(name, "train=60,calibration=40,alpha=0.2,floor=0.25")
        feed_daily(flat, list(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 150)))))
        assert flat.multiplier == 0.25, name


@pytest.mark.parametrize("name", ["rl_ppo", "rl_ddpg", "rl_sac", "emv"])
def test_learning_sizers_stay_in_bounds(name):
    rng = np.random.default_rng(6)
    params = "window=100,refit=50" if name != "emv" else "window=100,horizon=10,refit=50"
    s = sl.build_signal(name, params)
    feed_daily(s, list(100 * np.exp(np.cumsum(0.001 + rng.normal(0, 0.01, 160)))))
    assert 0.0 <= s.multiplier <= 2.0


def test_random_forest_learns_a_planted_pattern():
    rng = np.random.default_rng(7)
    r = [0.0]
    for _ in range(400):
        r.append(-0.8 * r[-1] + rng.normal(0, 0.01))
    closes = list(100 * np.exp(np.cumsum(r)))
    for name in ("random_forest", "rf_seqboot"):
        g = sl.build_signal(name, "train=200,refit=40")
        after_up, after_down = [], []
        for d, c in enumerate(closes):
            g.observe(ctx(d, 0, c))
            g.observe(ctx(d, 1, c))
            if g.probability is not None and d > 2:
                (after_up if closes[d - 1] > closes[d - 2] else after_down).append(g.suppressed)
        assert np.mean(after_up) > np.mean(after_down), name


def test_level_components_only_lower_the_level():
    skew = sl.build_signal("inventory_skew", "skew=1.0,max_depth=0.5")
    assert skew.adjust_level(99.0, ctx(0, 0, 100, lots=0), 0.01) == pytest.approx(99.0)
    assert skew.adjust_level(99.0, ctx(0, 0, 100, lots=3), 0.01) < 99.0
    s = LibrarySizing(**HF, signal="avellaneda_stoikov", signal_params="gamma=1000")
    for m in range(30):
        s.record_tick(ctx(0, m, 100 + (m % 3)))
    base = GatedLocalReferenceSizing(**HF)
    for m in range(30):
        base.record_tick(ctx(0, m, 100 + (m % 3)))
    c = ctx(0, 30, 100, lots=5)
    assert s._grid_trigger_level(c, 101.0, 0.01) < base._grid_trigger_level(c, 101.0, 0.01)


def test_vwap_vpin_anomaly_and_tda_components_observe_without_error():
    rng = np.random.default_rng(8)
    for name, params in (
        ("vwap", ""),
        ("vpin", "n_buckets=5"),
        ("fracdiff", "window=30"),
        ("hawkes_jumps", "window=100"),
        ("tda_level", "window=15,lookback=20,every=1"),
        ("tda_variance", "window=15,lookback=20,every=1"),
        ("tda_rips", "windows=10,15,lookback=25,every=2"),
    ):
        comp = sl.build_signal(name, params)
        p = 100.0
        for d in range(140):
            for m in range(0, 390, 30):
                p *= np.exp(rng.normal(0, 0.003))
                comp.observe(ctx(d, m, p, volume=float(rng.integers(100, 1000))))
        assert isinstance(comp.suppressed, bool), name


def test_external_series_gates_read_only_earlier_dates(tmp_path):
    days = [datetime(2023, 1, 2) + timedelta(days=d) for d in range(80)]
    leader = tmp_path / "leader.csv"
    leader.write_text(
        "date,close\n"
        + "".join(f"{d.date()},{100 * 1.001**i if i < 79 else 90}\n" for i, d in enumerate(days))
    )
    g = sl.build_signal("lead_lag", f"path={leader},window=20,min_corr=-1")
    # the leader's 10% drop is dated day 79: the session ON day 79 cannot see it
    for d in range(80):
        g.observe(ctx(d, 0, 100 * 1.001**d))
        g.observe(ctx(d, 1, 100 * 1.001**d))
    assert not g.suppressed
    g.observe(ctx(80, 0, 108))
    assert g.suppressed

    events = tmp_path / "news.csv"
    events.write_text("date,score\n2023-01-10,-0.9\n")
    e = sl.build_signal("event_sentiment", f"path={events},hold=3")
    e.observe(ctx(8, 0, 1))  # 2023-01-10 itself: not yet
    assert not e.suppressed
    e.observe(ctx(9, 0, 1))
    assert e.suppressed

    pess = tmp_path / "pess.csv"
    vals = [0.1] * 40 + [0.9]
    pess.write_text(
        "date,pessimism\n"
        + "".join(
            f"{(datetime(2023, 1, 2) + timedelta(days=i)).date()},{v}\n" for i, v in enumerate(vals)
        )
    )
    s = sl.build_signal("sentiment", f"path={pess},window=20,wait=2")
    s.observe(ctx(41, 0, 1))
    assert s.suppressed

    breadth = tmp_path / "breadth.csv"
    rows = [(0.3, 0.7)] * 15 + [(0.9, 0.1)] * 10
    breadth.write_text(
        "date,advances,declines\n"
        + "".join(
            f"{(datetime(2023, 1, 2) + timedelta(days=i)).date()},{a},{b}\n"
            for i, (a, b) in enumerate(rows)
        )
    )
    b = sl.build_signal("breadth_thrust", f"path={breadth},boost=1.5,hold=20")
    b.observe(ctx(30, 0, 1))
    assert b.multiplier == 1.5


def test_a_missing_file_stops_the_run_naming_it():
    comp = sl.build_signal("causal_impact", "pre=30")
    assert isinstance(comp, sl.MissingDataComponent)
    with pytest.raises(ConfigurationError, match="events_path=FILE"):
        comp.observe(ctx(0, 0, 1))


# --------------------------------------------------------------- 4. no sales


def test_no_exit_hook_is_overridden():
    for hook in ("lots_to_liquidate", "adjust_profit_target", "resume"):
        assert hook not in LibrarySizing.__dict__


def test_a_sizer_never_makes_a_negative_lot():
    s = LibrarySizing(**HF, signal="kelly")
    s.component.multiplier = -3.0
    s.record_tick(ctx(0, 0, 100))
    assert s.calculate_trade_value(ctx(0, 1, 100)) == 0.0


def test_class_names_stay_unique_for_analyze_annual():
    by_name: dict[str, set] = {}
    for cls in STRATEGIES.values():
        by_name.setdefault(cls.__name__, set()).add(cls)
    assert all(len(v) == 1 for v in by_name.values())
