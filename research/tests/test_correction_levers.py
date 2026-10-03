"""The intraday-momentum gate and volatility targeting on hf_entry_gated.

Both default off, and test_gated_local_reference_sizing already pins
"every lever off is the champion exactly". These pin what each does
when ON, in isolation and through the real controller.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.optimization.optimization_controller import OptimizationController
from research.strategies.entry_gates import MOMENTUM_MODES, IntradayMomentumGate
from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from research.strategies.volatility_estimators import VOL_ESTIMATORS
from research.tests.test_gated_local_reference_sizing import (
    FILL_MODELS,
    HF_PARAMS,
    _minute_sessions,
)

DAY0 = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)


def ctx(day, minute, close, open_=None):
    o = close if open_ is None else open_
    return MarketContext(
        timestamp=DAY0 + timedelta(days=day, minutes=minute),
        open=o,
        high=max(o, close) + 0.01,
        low=min(o, close) - 0.01,
        close=close,
        cash=1e5,
        equity=1e5,
        peak_equity=1e5,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
        time_of_day_flag=minute,
    )


def _session(day, early_end_price, minutes=390, base=100.0):
    """Opens at `base`, slides linearly to early_end_price over the first
    30 minutes, then holds there."""
    bars = []
    for m in range(minutes):
        price = base + (early_end_price - base) * min(m + 1, 30) / 30
        bars.append(ctx(day, m, price))
    return bars


def _feed(gate, bars):
    out = []
    for bar in bars:
        gate.observe(bar)
        out.append(gate.suppressed)
    return out


# --------------------------------------------------------------------
# IntradayMomentumGate


class TestIntradayMomentumGate:
    def test_blocks_only_the_late_window_after_a_bad_start(self):
        gate = IntradayMomentumGate("early_negative")
        states = _feed(gate, _session(0, 100.0) + _session(1, 98.0))
        day1 = states[390:]
        assert not any(day1[:360])
        assert all(day1[360:])
        assert gate.early_return == pytest.approx(98.0 / 100.0 - 1)

    def test_the_early_return_is_known_only_after_the_window_closes(self):
        """It is computed at the start of minute 30 from minute 29's close
        -- never from a bar still in progress."""
        gate = IntradayMomentumGate("early_negative")
        bars = _session(0, 100.0) + _session(1, 98.0)
        for bar in bars[: 390 + 30]:
            gate.observe(bar)
        assert gate.early_return is None
        gate.observe(bars[390 + 30])
        assert gate.early_return is not None

    def test_a_good_start_or_a_small_dip_never_blocks(self):
        assert not any(
            _feed(IntradayMomentumGate("early_negative"), _session(0, 100) + _session(1, 101))
        )
        small = IntradayMomentumGate("early_negative", threshold=0.03)
        assert not any(_feed(small, _session(0, 100) + _session(1, 98)))

    def test_each_session_starts_clear_and_half_days_are_inert(self):
        gate = IntradayMomentumGate("early_negative")
        states = _feed(
            gate, _session(0, 100) + _session(1, 98) + _session(2, 98, minutes=210, base=98)
        )
        assert states[390 + 389] is True
        assert not any(states[780:])

    def test_off_is_inert(self):
        gate = IntradayMomentumGate("off")
        assert not any(_feed(gate, _session(0, 100) + _session(1, 90)))

    @pytest.mark.parametrize(
        "kwargs",
        [{"mode": "late"}, {"threshold": -0.01}, {"early_minutes": 200, "late_minutes": 200}],
    )
    def test_validation(self, kwargs):
        mode = kwargs.pop("mode", "early_negative")
        with pytest.raises(ConfigurationError):
            IntradayMomentumGate(mode, **kwargs)


def _two_long_sessions() -> pd.DataFrame:
    """Day 0 oscillates around 100; day 1 opens at 100, slides 2% in the
    first half hour, then oscillates around 98 to the close -- so the
    champion buys all day, late window included."""
    frames = []
    for day, (start, end) in enumerate([(100.0, 100.0), (100.0, 98.0)]):
        m = np.arange(390)
        level = start + (end - start) * np.minimum(m + 1, 30) / 30
        close = level * (1 + 0.004 * np.sin(m * 2 * math.pi / 12))
        open_ = np.r_[start, close[:-1]]
        idx = pd.date_range(DAY0 + timedelta(days=day), periods=390, freq="1min")
        frames.append(
            pd.DataFrame(
                {
                    "open": open_,
                    "high": np.maximum(open_, close) * 1.0005,
                    "low": np.minimum(open_, close) * 0.9995,
                    "close": close,
                    "volume": 1e4,
                },
                index=idx,
            )
        )
    return pd.concat(frames)


def _buys(df, cls, fill_model, extra=None):
    _, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.3],
        strategy_class=cls,
        strategy_params_grid=[{**HF_PARAMS, "bars_per_day": 390, **(extra or {})}],
        fill_model=fill_model,
        return_full_results=True,
    )
    b = full[0].trade_blotter
    buys = b[b["side"] == "buy"].copy()
    buys["ts"] = pd.to_datetime(buys["timestamp"], utc=True)
    return buys


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_momentum_gate_end_to_end(fill_model):
    df = _two_long_sessions()
    late = DAY0 + timedelta(days=1, minutes=360)
    champion = _buys(df, HighFrequencyLocalReferenceSizing, fill_model)
    gated = _buys(df, GatedLocalReferenceSizing, fill_model, {"momentum_gate": "early_negative"})
    assert (champion["ts"] >= late).sum() > 0, "the champion must buy late, or this proves nothing"
    assert (gated["ts"] >= late).sum() == 0
    # Before the late window the gate changes nothing at all.
    assert (
        champion[champion["ts"] < late]["ts"].tolist() == gated[gated["ts"] < late]["ts"].tolist()
    )


# --------------------------------------------------------------------
# Volatility targeting


def test_multiplier_is_neutral_until_warm_then_target_over_realized():
    s = GatedLocalReferenceSizing(**HF_PARAMS, vol_target=0.5, vol_target_days=2)
    rng = np.random.default_rng(0)
    price = 100.0
    for day in range(2):
        for m in range(3):
            price *= math.exp(rng.normal(0, 0.01))
            s.record_tick(ctx(day, m, price))
    assert s.vol_target_multiplier == 1.0  # two completed sessions are not enough
    for day in range(2, 5):
        for m in range(3):
            price *= math.exp(rng.normal(0, 0.01))
            s.record_tick(ctx(day, m, price))
    realized = s._session_vol.value
    assert realized is not None
    assert s.vol_target_multiplier == pytest.approx(min(2.0, max(0.25, 0.5 / realized)))


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_vol_target_scales_buys_only_after_its_window_fills(fill_model):
    """A target far below any realized vol clamps to the 0.25 floor once
    two sessions plus a prior close have completed (from session 3)."""
    df = _minute_sessions(days=6)
    champion = _buys(df, HighFrequencyLocalReferenceSizing, fill_model)
    target = _buys(
        df, GatedLocalReferenceSizing, fill_model, {"vol_target": 1e-6, "vol_target_days": 2}
    )
    for buys in (champion, target):
        buys["notional"] = buys["qty"] * buys["price"]
        buys["session"] = buys["ts"].dt.date.rank(method="dense").astype(int) - 1
    assert np.allclose(champion["notional"], champion["notional"].iloc[0])
    lot = champion["notional"].iloc[0]
    early, late = target[target["session"] < 3], target[target["session"] >= 3]
    assert len(early) and len(late)
    assert np.allclose(early["notional"], lot)
    assert np.allclose(late["notional"], 0.25 * lot)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"vol_target": 0.0},
        {"vol_target": 0.5, "vol_target_min": 0.0},
        {"vol_target": 0.5, "vol_target_min": 2.0, "vol_target_max": 1.0},
        {"vol_target_estimator": "garch"},
        {"momentum_gate": "on"},
    ],
)
def test_strategy_validation(kwargs):
    with pytest.raises(ConfigurationError):
        GatedLocalReferenceSizing(**HF_PARAMS, **kwargs)


def test_server_enums_match_the_guards():
    from server.backtest import _PARAM_ENUMS

    assert _PARAM_ENUMS["momentum_gate"] == list(MOMENTUM_MODES)
    assert _PARAM_ENUMS["vol_target_estimator"] == list(VOL_ESTIMATORS)
