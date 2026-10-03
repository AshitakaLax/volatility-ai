"""CandleStream, the Bollinger W-bottom permission gate, the RSI
head-and-shoulders gate, and their wiring into hf_entry_gated."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.entry_gates import (
    BOUNCE_MODES,
    RSI_GATE_MODES,
    BollingerWGate,
    CandleStream,
    RsiHeadShouldersGate,
)
from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing
from research.tests.test_gated_local_reference_sizing import HF_PARAMS

DAY0 = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)


def bar(i, close, low=None):
    lo = close - 0.05 if low is None else low
    return MarketContext(
        timestamp=DAY0 + timedelta(minutes=i),
        open=close,
        high=close + 0.05,
        low=lo,
        close=close,
        cash=1e5,
        equity=1e5,
        peak_equity=1e5,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=i,
        time_of_day_flag=i,
    )


def test_candle_stream_completes_a_candle_when_the_next_bucket_starts():
    s = CandleStream(2)
    out = [s.push(bar(i, 100 + i)) for i in range(5)]
    assert out[0] is out[1] is None
    assert out[2] is not None and (out[2].open, out[2].close) == (100, 101)
    assert out[3] is None and out[4].close == 103


def _w_sequence():
    closes = [100.0 + (0.05 if i % 2 else -0.05) for i in range(25)]
    lows = [c - 0.05 for c in closes]
    for c, lo in [(98.0, 97.9), (99.0, 98.9), (100.5, 100.4), (99.3, 99.2), (100.8, 100.7)]:
        closes.append(c)
        lows.append(lo)
    closes += [100.8] * 6
    lows += [100.75] * 6
    return [bar(i, c, lo) for i, (c, lo) in enumerate(zip(closes, lows, strict=True))]


class TestBollingerWGate:
    def test_permission_is_granted_only_after_a_confirmed_w(self):
        gate = BollingerWGate("w_bottom", candle_minutes=1, window=20, hold_candles=3)
        states = []
        for b in _w_sequence():
            gate.observe(b)
            states.append(gate.suppressed)
        # Candle 29 (the confirming close) completes when bar 30 starts.
        assert all(states[:30])
        assert states[30:33] == [False, False, False]
        assert states[33] is True
        assert gate.episodes == 1

    def test_a_second_dip_below_the_band_is_not_a_w(self):
        seq = _w_sequence()
        seq[28] = bar(28, 96.0, 95.9)  # the "second dip" breaks the lower band
        gate = BollingerWGate("w_bottom", candle_minutes=1, window=20, hold_candles=3)
        for b in seq:
            gate.observe(b)
        assert gate.episodes == 0

    def test_off_never_suppresses(self):
        gate = BollingerWGate("off", candle_minutes=1)
        for b in _w_sequence():
            gate.observe(b)
        assert gate.suppressed is False

    @pytest.mark.parametrize("kwargs", [{"mode": "v_bottom"}, {"k": 0}, {"window": 1}])
    def test_validation(self, kwargs):
        mode = kwargs.pop("mode", "w_bottom")
        with pytest.raises(ConfigurationError):
            BollingerWGate(mode, **kwargs)


class TestRsiHeadShouldersGate:
    def test_rsi_matches_talib(self):
        talib = pytest.importorskip("talib")
        closes = 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.01, 80)))
        gate = RsiHeadShouldersGate("head_shoulders", candle_minutes=1, period=14)
        seen = []
        for i, c in enumerate(closes):
            gate.observe(bar(i, float(c)))
            seen.append(gate.rsi)
        # Candle i's RSI is known once bar i+1 has started.
        theirs = talib.RSI(closes, timeperiod=14)
        for i in range(15, 79):
            assert seen[i + 1] == pytest.approx(theirs[i], rel=1e-9)

    def test_a_top_blocks_buys_once_the_neckline_breaks(self):
        gate = RsiHeadShouldersGate("head_shoulders", hold_candles=2)
        # shoulders 55 / 57 (troughs 45, 48), head 75; neckline 46.5
        for r in [40, 55, 50, 45, 75, 60, 48, 57, 52, 47]:
            gate._on_rsi(r)
        assert gate.suppressed is False
        gate._on_rsi(46)
        assert gate.suppressed is True and gate.episodes == 1

    def test_no_top_without_an_overbought_head(self):
        gate = RsiHeadShouldersGate("head_shoulders", overbought=80)
        for r in [40, 55, 50, 45, 75, 60, 48, 57, 52, 47, 46, 30]:
            gate._on_rsi(r)
        assert gate.episodes == 0

    def test_uneven_shoulders_are_not_a_top(self):
        gate = RsiHeadShouldersGate("head_shoulders", tolerance=1.0)
        for r in [40, 55, 50, 45, 75, 60, 48, 57, 52, 47, 46, 30]:
            gate._on_rsi(r)
        assert gate.episodes == 0


def test_strategy_wiring_and_enums():
    from server.backtest import _PARAM_ENUMS

    s = GatedLocalReferenceSizing(**HF_PARAMS, bounce_gate="w_bottom", rsi_gate="head_shoulders")
    assert s.bounce.enabled and s.rsi_top.enabled
    s.record_tick(bar(0, 100.0))
    assert s.entry_suppressed is True  # permission not yet granted
    assert _PARAM_ENUMS["bounce_gate"] == list(BOUNCE_MODES)
    assert _PARAM_ENUMS["rsi_gate"] == list(RSI_GATE_MODES)
    with pytest.raises(ConfigurationError):
        GatedLocalReferenceSizing(**HF_PARAMS, rsi_gate="double_top")
