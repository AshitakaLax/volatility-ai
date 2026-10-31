"""The ranked list's single-symbol signal gates (research/strategies/
signal_gates.py) and their strategy, hf_signal_gated.

Three claims, as for hf_entry_gated:

  1. Every gate off IS hf_entry_gated (and so the champion) -- identical
     metrics under both fill models.
  2. Each gate shuts on the condition its source names, and only then,
     without reading the bar it decides.
  3. Nothing here can sell: no exit hook is overridden, and the traded
     strategies' classes and defaults are unchanged.
"""

from __future__ import annotations

import inspect
import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.optimization.optimization_controller import OptimizationController
from research.strategies import signal_gates as sg
from research.strategies.gated_local_reference_sizing import (
    NO_BUY_LEVEL,
    GatedLocalReferenceSizing,
)
from research.strategies.param_schema import _PARAM_ENUMS, STRATEGY_DEFAULTS
from research.strategies.signal_gated_sizing import SignalGatedSizing
from research.strategies.strategy_registry import STRATEGIES, resolve_strategy

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


def ctx(day: int, minute: int, o, h, lo, c, volume=1000.0) -> MarketContext:
    ts = datetime(2024, 1, 1, 14, 30) + timedelta(days=day, minutes=minute)
    return MarketContext(
        timestamp=ts,
        open=o,
        high=h,
        low=lo,
        close=c,
        cash=1e5,
        equity=1e5,
        peak_equity=1e5,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=day * 1000 + minute,
        time_of_day_flag=minute,
        volume=volume,
    )


def daily(gate, closes, highs=None, lows=None, bars=2):
    """Feed one session per close: `bars` flat bars at that close (or the
    given high/low), then one bar of the next session so the last session
    completes. Returns the suppressed flag after each session opens."""
    seen = []
    for d, c in enumerate(closes):
        h = highs[d] if highs is not None else c
        lo = lows[d] if lows is not None else c
        for m in range(bars):
            gate.observe(ctx(d, m, c, h, lo, c))
            if m == 0:
                seen.append(gate.suppressed)
    gate.observe(ctx(len(closes), 0, closes[-1], closes[-1], closes[-1], closes[-1]))
    seen.append(gate.suppressed)
    return seen


# --------------------------------------------------------------------
# 1. Off is hf_entry_gated


def _fixture() -> pd.DataFrame:
    return pd.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")


def _run(df, cls, fill_model, extra=None):
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.004],
        strategy_class=cls,
        strategy_params_grid=[{**HF_PARAMS, **(extra or {})}],
        fill_model=fill_model,
    )


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_all_signal_gates_off_reproduces_hf_entry_gated_exactly(fill_model):
    df = _fixture()
    gated = _run(df, GatedLocalReferenceSizing, fill_model).iloc[0]
    signal = _run(df, SignalGatedSizing, fill_model).iloc[0]
    assert gated["Trade Count"] > 0
    for column in OUTCOMES:
        assert signal[column] == gated[column], column


def test_signature_mirrors_the_parent():
    parent = list(inspect.signature(GatedLocalReferenceSizing.__init__).parameters.values())
    child = list(inspect.signature(SignalGatedSizing.__init__).parameters.values())
    assert [(p.name, p.default, p.annotation, p.kind) for p in parent] == [
        (p.name, p.default, p.annotation, p.kind) for p in child[: len(parent)]
    ]
    assert all(p.default is not inspect.Parameter.empty for p in child[len(parent) :])


def test_every_parent_argument_is_passed_through():
    kwargs = {**HF_PARAMS, "vol_scale_exponent": -1.5, "breakdown_gate": "prior_low"}
    child, parent = SignalGatedSizing(**kwargs), GatedLocalReferenceSizing(**kwargs)
    for name in inspect.signature(GatedLocalReferenceSizing.__init__).parameters:
        if name != "self" and hasattr(parent, name):
            assert getattr(child, name) == getattr(parent, name), name
    assert child.breakdown.mode == "prior_low"


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_a_signal_gate_changes_the_run(fill_model):
    """End to end: a gate that is shut most of the time trades less."""
    df = _fixture()
    base = _run(df, SignalGatedSizing, fill_model).iloc[0]
    gated = _run(df, SignalGatedSizing, fill_model, {"zscore_gate": "oversold"}).iloc[0]
    assert gated["Trade Count"] < base["Trade Count"]


def test_a_shut_signal_gate_returns_the_unreachable_level():
    s = SignalGatedSizing(**HF_PARAMS, gap_gate="gap_down", gap_threshold=0.01)
    s.record_tick(ctx(0, 0, 100, 100, 100, 100))
    s.record_tick(ctx(0, 1, 100, 100, 100, 100))
    s.record_tick(ctx(1, 0, 95, 95, 95, 95))
    assert s.entry_suppressed
    assert s._grid_trigger_level(ctx(1, 0, 95, 95, 95, 95), 100.0, 0.01) == NO_BUY_LEVEL


# --------------------------------------------------------------------
# 2. Each gate


def test_session_book_completes_a_session_only_when_the_next_one_starts():
    book = sg.SessionBook(10)
    assert not book.push(ctx(0, 0, 10, 11, 9, 10))
    assert not book.push(ctx(0, 1, 10, 12, 8, 11, volume=5))
    assert book.push(ctx(1, 0, 11, 11, 11, 11))
    assert list(book.highs) == [12] and list(book.lows) == [8] and list(book.closes) == [11]
    assert list(book.volumes) == [1005.0]


def test_52_week_high_gate():
    gate = sg.FiftyTwoWeekHighGate("near_high", window=5, threshold=0.9)
    seen = daily(gate, [100, 100, 100, 100, 100, 85, 84])
    assert not any(seen[:6]) and seen[-1]
    assert gate.ratio == pytest.approx(84 / 100)


def test_adx_gate_shuts_in_a_strong_downtrend_only():
    down = sg.AdxTrendGate("strong_downtrend", period=5, threshold=20)
    closes = [100 * 0.98**i for i in range(30)]
    daily(down, closes, [c * 1.005 for c in closes], [c * 0.995 for c in closes])
    assert down.suppressed and down.minus_di > down.plus_di
    up = sg.AdxTrendGate("strong_downtrend", period=5, threshold=20)
    closes = [100 * 1.02**i for i in range(30)]
    daily(up, closes, [c * 1.005 for c in closes], [c * 0.995 for c in closes])
    assert not up.suppressed and up.adx > 20


@pytest.mark.parametrize("ma", ["ema", "tema"])
def test_ribbon_gate(ma):
    """An accelerating fall (TEMA has no lag on a straight line, so a
    linear trend would leave its ribbon unordered)."""
    gate = sg.RibbonGate("bearish", spans="2,4,8", ma=ma)
    daily(gate, [100 - 0.1 * i * i for i in range(20)])
    assert gate.suppressed
    gate = sg.RibbonGate("bearish", spans="2,4,8", ma=ma)
    daily(gate, [100 + 0.1 * i * i for i in range(20)])
    assert not gate.suppressed


def test_gap_gate_blocks_a_gap_down_until_it_fills():
    gate = sg.GapGate("gap_down", threshold=0.01)
    gate.observe(ctx(0, 0, 100, 100, 100, 100))
    gate.observe(ctx(1, 0, 97, 97.5, 96, 97))
    assert gate.suppressed and gate.gap == pytest.approx(-0.03)
    gate.observe(ctx(1, 1, 97, 100.5, 97, 100))  # this bar reaches the prior close ...
    assert gate.suppressed  # ... but is not history yet
    gate.observe(ctx(1, 2, 100, 100, 100, 100))
    assert not gate.suppressed
    session = sg.GapGate("gap_down", threshold=0.01, release="session")
    for m, bar in enumerate([(100,) * 4]):
        session.observe(ctx(0, m, *bar))
    session.observe(ctx(1, 0, 97, 97, 97, 97))
    session.observe(ctx(1, 1, 101, 101, 101, 101))
    session.observe(ctx(1, 2, 101, 101, 101, 101))
    assert session.suppressed
    session.observe(ctx(2, 0, 101, 101, 101, 101))
    assert not session.suppressed


def test_kama_gate():
    gate = sg.KamaTrendGate("below_falling", period=3, fast=2, slow=10)
    daily(gate, [100 * 0.98**i for i in range(15)])
    assert gate.suppressed
    gate = sg.KamaTrendGate("below_falling", period=3, fast=2, slow=10)
    daily(gate, [100 * 1.02**i for i in range(15)])
    assert not gate.suppressed


def _candles(gate, closes, minutes=1):
    for i, c in enumerate(closes):
        gate.observe(ctx(0, i * minutes, c, c, c, c))


def test_zscore_gate_permits_only_on_the_oversold_candle():
    gate = sg.BandReversionGate("oversold", candle_minutes=1, window=5, k=1.0)
    _candles(gate, [100, 101, 100, 101, 100, 101])
    assert gate.suppressed  # permission gate: shut by default
    _candles(gate, [95, 101])  # the 95 candle completes when 101 arrives
    assert not gate.suppressed
    gate.observe(ctx(0, 50, 101, 101, 101, 101))
    assert gate.suppressed


def test_bollinger_gate_latches_until_the_middle_band():
    gate = sg.BandReversionGate(
        "lower_band",
        name="band_gate",
        modes=("off", "lower_band"),
        candle_minutes=1,
        window=5,
        k=1.0,
    )
    for i, c in enumerate([100, 101, 100, 101, 100, 95, 96, 96.5]):
        gate.observe(ctx(0, i, c, c, c, c))
    assert not gate.suppressed  # 95 opened it; 96 is still below the mean
    for i, c in enumerate([102, 102]):
        gate.observe(ctx(0, 20 + i, c, c, c, c))
    assert gate.suppressed
    with pytest.raises(ConfigurationError):
        sg.BandReversionGate("oversold", name="band_gate", modes=("off", "lower_band"))


def test_term_structure_gate_reads_the_prior_day(tmp_path):
    path = tmp_path / "vix.csv"
    path.write_text("date,vix,vix3m\n2024-01-01,15,18\n2024-01-02,25,20\n2024-01-03,15,18\n")
    gate = sg.TermStructureGate("backwardation", path=str(path), threshold=1.0)
    gate.observe(ctx(1, 0, 1, 1, 1, 1))  # 2024-01-02: reads 01-01, contango
    assert not gate.suppressed
    gate.observe(ctx(2, 0, 1, 1, 1, 1))  # 2024-01-03: reads 01-02, backwardation
    assert gate.suppressed and gate.ratio == pytest.approx(1.25)
    gate.observe(ctx(0, 0, 1, 1, 1, 1))  # no prior row: not blocked
    assert not gate.suppressed
    with pytest.raises(ConfigurationError):
        sg.TermStructureGate("backwardation")


def test_anchored_vwap_gate():
    gate = sg.AnchoredVwapGate("swing_high", sessions=5)
    for d, level in enumerate([100, 110, 105, 100]):
        for m in range(3):
            gate.observe(ctx(d, m, level, level, level, level, volume=100))
    gate.observe(ctx(4, 0, 100, 100, 100, 100, volume=100))
    assert gate.vwap == pytest.approx((110 + 105 + 100) / 3)
    gate.observe(ctx(4, 1, 100, 100, 100, 100, volume=100))
    assert gate.suppressed  # 100 < the VWAP anchored at the 110 top
    low = sg.AnchoredVwapGate("swing_low", sessions=5)
    for d, level in enumerate([100, 90, 95, 100]):
        for m in range(3):
            low.observe(ctx(d, m, level, level, level, level, volume=100))
    low.observe(ctx(4, 0, 100, 100, 100, 100))
    low.observe(ctx(4, 1, 100, 100, 100, 100))
    assert not low.suppressed


def test_anomaly_gate_holds_after_a_crash_bar():
    gate = sg.AnomalyGate("price", span=10, z=3.0, hold_bars=3)
    rng = np.random.default_rng(0)
    price = 100.0
    for m in range(40):
        price *= 1 + rng.normal(0, 0.001)
        gate.observe(ctx(0, m, price, price, price, price))
    assert not gate.suppressed
    gate.observe(ctx(0, 40, price * 0.95, price, price * 0.95, price * 0.95))
    gate.observe(ctx(0, 41, price * 0.95, price * 0.95, price * 0.95, price * 0.95))
    assert gate.suppressed
    for m in range(42, 46):
        gate.observe(ctx(0, m, price * 0.95, price * 0.95, price * 0.95, price * 0.95))
    assert not gate.suppressed


def test_volume_imbalance_gate_shuts_under_persistent_selling():
    gate = sg.VolumeImbalanceGate(
        "sell_imbalance", bars_per_session=10, window=3, threshold=0.5, sessions=1
    )
    for m in range(10):  # a flat first session sets the volume clock
        gate.observe(ctx(0, m, 100, 100, 100, 100, volume=100))
    price = 100.0
    for m in range(20):
        price -= 0.1
        gate.observe(ctx(1, m, price, price, price, price, volume=100))
    assert gate.suppressed and gate.imbalance <= -0.5


def test_triple_barrier_gate_learns_a_planted_pattern():
    """Sessions after a fall rise and sessions after a rise fall, so the
    classifier must learn to block after rises."""
    rng = np.random.default_rng(1)
    closes = [100.0]
    for _ in range(420):
        prev = closes[-1] / closes[-2] - 1 if len(closes) > 1 else 0
        closes.append(closes[-1] * (1 + (-0.8 * prev) + rng.normal(0, 0.01)))
    gate = sg.TripleBarrierGate(
        "classifier", horizon=1, profit=0.002, loss=0.002, min_samples=100, retrain=10
    )
    blocked_after = {"up": [], "down": []}
    for d, c in enumerate(closes):
        gate.observe(ctx(d, 0, c, c, c, c))
        gate.observe(ctx(d, 1, c, c, c, c))
        if gate.probability is not None and d >= 2:
            move = "up" if closes[d - 1] > closes[d - 2] else "down"
            blocked_after[move].append(gate.suppressed)
    assert np.mean(blocked_after["up"]) > np.mean(blocked_after["down"]) + 0.3


def test_triple_barrier_labels_are_causal():
    gate = sg.TripleBarrierGate("classifier", horizon=3, min_samples=20)
    for d, c in enumerate([100, 101, 102, 103]):
        gate.observe(ctx(d, 0, c, c, c, c))
    gate._label_ready()
    # session 0's outcome needs session 3's bar, which has not completed
    assert 0 not in gate._labels


def test_hurst_gate_blocks_reversion_buys_in_a_trend():
    rng = np.random.default_rng(2)
    gate = sg.HurstBandGate("adaptive_band", candle_minutes=1, window=40, max_lag=10, k=1.0)
    trend = 100 + np.cumsum(np.cumsum(rng.normal(0, 0.01, 80)))  # persistent: H > 1
    _candles(gate, list(trend))
    assert gate.hurst > 0.65 and gate.suppressed
    rev = sg.HurstBandGate("adaptive_band", candle_minutes=1, window=40, max_lag=10, k=1.0)
    path = 100 + rng.normal(0, 0.5, 80)  # white noise around a level: H near 0
    _candles(rev, [*list(path), path.mean() - 5, path.mean()])
    assert rev.hurst < 0.5 and not rev.suppressed


@pytest.mark.parametrize(
    "cls,kwargs",
    [
        (sg.FiftyTwoWeekHighGate, {"threshold": 1.5}),
        (sg.AdxTrendGate, {"period": 1}),
        (sg.RibbonGate, {"spans": "20,10"}),
        (sg.GapGate, {"release": "never"}),
        (sg.KamaTrendGate, {"fast": 30, "slow": 2}),
        (sg.AnomalyGate, {"z": 0}),
        (sg.VolumeImbalanceGate, {"threshold": 2}),
        (sg.TripleBarrierGate, {"threshold": 1.0}),
        (sg.HurstBandGate, {"max_lag": 200}),
    ],
)
def test_bad_parameters_fail_even_when_off(cls, kwargs):
    with pytest.raises(ConfigurationError):
        cls("off", **kwargs)


def test_off_gates_are_inert():
    for gate in (
        sg.FiftyTwoWeekHighGate(),
        sg.AdxTrendGate(),
        sg.RibbonGate(),
        sg.GapGate(),
        sg.KamaTrendGate(),
        sg.BandReversionGate(),
        sg.TermStructureGate(),
        sg.AnchoredVwapGate(),
        sg.AnomalyGate(),
        sg.VolumeImbalanceGate(),
        sg.TripleBarrierGate(),
        sg.HurstBandGate(),
    ):
        gate.observe(ctx(0, 0, 1, 1, 1, 1))
        assert not gate.enabled and not gate.suppressed and gate.suppressed_bars == 0


def test_live_history_covers_the_longest_enabled_gate():
    base = SignalGatedSizing(**HF_PARAMS).live_history_sessions()
    long = SignalGatedSizing(**HF_PARAMS, high52_gate="near_high").live_history_sessions()
    assert base < long and long >= 254


# --------------------------------------------------------------------
# 3. Registered; the traded strategies untouched


def test_registered_with_the_champion_defaults():
    assert resolve_strategy("hf_signal_gated") is SignalGatedSizing
    assert STRATEGY_DEFAULTS["hf_signal_gated"] == STRATEGY_DEFAULTS["hf_local_reference"]
    assert STRATEGY_DEFAULTS["hf_entry_gated"] == STRATEGY_DEFAULTS["hf_local_reference"]
    assert STRATEGIES["hf_entry_gated"] is GatedLocalReferenceSizing
    strategy = SignalGatedSizing(**STRATEGY_DEFAULTS["hf_signal_gated"])
    assert strategy.diagnostics()["entry_suppressed"] is False


def test_no_exit_hook_is_overridden():
    for hook in ("lots_to_liquidate", "adjust_profit_target", "resume"):
        assert hook not in SignalGatedSizing.__dict__


def test_server_enums_match_the_guards():
    pairs = {
        "high52_gate": sg.FiftyTwoWeekHighGate,
        "adx_gate": sg.AdxTrendGate,
        "ribbon_gate": sg.RibbonGate,
        "gap_gate": sg.GapGate,
        "kama_gate": sg.KamaTrendGate,
        "term_gate": sg.TermStructureGate,
        "avwap_gate": sg.AnchoredVwapGate,
        "anomaly_gate": sg.AnomalyGate,
        "imbalance_gate": sg.VolumeImbalanceGate,
        "barrier_gate": sg.TripleBarrierGate,
        "hurst_gate": sg.HurstBandGate,
    }
    for param, cls in pairs.items():
        assert _PARAM_ENUMS[param] == list(cls.modes), param
    strategy = SignalGatedSizing(**HF_PARAMS)
    assert _PARAM_ENUMS["zscore_gate"] == list(strategy.zscore.modes)
    assert _PARAM_ENUMS["band_gate"] == list(strategy.band.modes)
    assert math.isfinite(len(_PARAM_ENUMS["ribbon_ma"]))
