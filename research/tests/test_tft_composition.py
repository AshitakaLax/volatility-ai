"""The TFT in buy x sell compositions, without torch (a stub forecaster
stands in for the model, as in test_tft_sizing.py):

  1. ml_tft is a buy policy, and tft_take_profit a sell policy, that any
     other policy pairs with.
  2. tft_take_profit sells on the TURN to a forecast fall, only lots up at
     least min_gain, never below cost, reading the model every check_bars
     bars and only while lots are open.
  3. Both run through the real controller, together and with other policies.
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from typing import ClassVar

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.composition import entries, exits
from research.composition.composed_strategy import ComposedStrategy
from research.composition.exit_library import TftFallGate, TftTakeProfit
from research.ml.tft_sizing import TemporalFusionTransformerSizer
from research.optimization.optimization_controller import OptimizationController
from research.tests.test_tft_sizing import BARS, N, ctx


class ScriptedForecaster:
    """Quantiles of log price `mu` above the last encoder close. The test
    sets `mu`; the bars' own moves are 0.3% a bar, so +-5% reads clearly."""

    levels = (0.1, 0.5, 0.9)
    encoder_length = 20
    prediction_length = 4
    bars_per_day = 26
    valid_from = None
    sources: ClassVar[dict] = {"s_macro": None, "s_earnings": None, "s_news": None}

    def __init__(self, mu=0.05, sigma=0.02):
        self.mu, self.sigma, self.calls = mu, sigma, 0

    def forecast(self, encoder, decoder_known):
        self.calls += 1
        base = encoder[-1, 0] + self.mu
        return np.tile([base + self.sigma * N.inv_cdf(p) for p in self.levels], (4, 1))


@pytest.fixture
def scripted(monkeypatch):
    """Every TFT built in the test answers from one ScriptedForecaster."""
    holder = SimpleNamespace(stub=ScriptedForecaster())
    monkeypatch.setattr(
        TemporalFusionTransformerSizer, "_load_forecaster", lambda self: holder.stub
    )
    return holder


def lots_ctx(t, lots=1, **kw):
    c = ctx(t, **kw)
    return c.__class__(**{**c.__dict__, "open_lot_count": lots})


def lot(order_id, buy_price, target=0.05):
    return SimpleNamespace(
        order_id=order_id, buy_price=buy_price, profit_target=target, shares=10.0
    )


HF = {"bars_per_day": 26, "per_lot_pct": 0.01, "lookback_days": 0.5}

# ------------------------------------------------------------ 1. the registry


def test_the_tft_is_a_buy_policy_and_a_sell_policy():
    assert "ml_tft" in entries.entry_ids()
    assert entries.entry_class("ml_tft") is TemporalFusionTransformerSizer
    assert exits.resolve_exit("tft_take_profit") is TftTakeProfit
    assert TftTakeProfit.can_realize_loss is False  # the no-loss track
    TftTakeProfit(**exits.EXIT_DEFAULTS["tft_take_profit"])  # loads no model


def test_any_buy_pairs_with_the_tft_sell_and_the_tft_buy_with_any_sell():
    ComposedStrategy(
        {"id": "hf_local_reference", "params": HF},
        {"id": "tft_take_profit", "params": {"model": "stub", "bars_per_day": 26}},
    )
    ComposedStrategy(
        {
            "id": "ml_tft",
            "params": {"max_trade_pct": 0.05, "bars_per_day": 26, "model": "stub"},
        },
        {"id": "trailing", "params": {"trail_pct": 0.01}},
    )


# ------------------------------------------------------ 2. the take-profit


def test_the_gate_reads_every_check_bars_and_only_with_lots_open(scripted):
    gate = TftFallGate(
        TemporalFusionTransformerSizer(1.0, 26, model="stub"), min_drop=0.0, check_bars=5
    )
    for t in range(40):
        gate.observe(lots_ctx(t, lots=0))
    assert gate.reads == 0 and not gate.suppressed
    for t in range(40, 60):
        gate.observe(lots_ctx(t, lots=1))
    assert gate.reads == 4  # bars 40, 45, 50, 55
    with pytest.raises(ConfigurationError):
        TftFallGate(None, min_drop=-0.1, check_bars=5)


def test_it_sells_lots_in_profit_on_the_turn_to_a_forecast_fall(scripted):
    policy = TftTakeProfit(model="stub", bars_per_day=26, min_gain=0.002, check_bars=1)
    for t in range(30):
        policy.record_tick(lots_ctx(t))  # the ring fills at bar 20; every read is bullish
    assert scripted.stub.calls > 0 and policy.fires == 0
    scripted.stub.mu = -0.05
    policy.record_tick(lots_ctx(30))  # the forecast turns to a fall
    assert policy._fire and policy.fires == 1 and policy.wants_lot_retargeting()
    price = float(BARS.close.iloc[30])
    up, flat, under = (
        lot("up", price / 1.01),
        lot("flat", price / 1.001),
        lot("under", price * 1.02),
    )
    new_target = policy.adjust_profit_target(up, lots_ctx(30))
    assert new_target == pytest.approx(price * (1 - 1e-9) / up.buy_price - 1)
    assert policy.adjust_profit_target(flat, lots_ctx(30)) is None  # below min_gain
    assert policy.adjust_profit_target(under, lots_ctx(30)) is None  # never below cost
    assert policy.harvest_quantity(up, lots_ctx(30)) == up.shares
    policy.record_tick(lots_ctx(31))  # still bearish: no second fire
    assert not policy._fire and policy.fires == 1


def test_a_partial_take_profit_restores_the_rest_to_its_target(scripted):
    policy = TftTakeProfit(model="stub", bars_per_day=26, fraction=0.5, check_bars=1)
    for t in range(30):
        policy.record_tick(lots_ctx(t))
    scripted.stub.mu = -0.05
    policy.record_tick(lots_ctx(30))
    up = lot("up", float(BARS.close.iloc[30]) / 1.01, target=0.05)
    policy.adjust_profit_target(up, lots_ctx(30))
    assert policy.harvest_quantity(up, lots_ctx(30)) == pytest.approx(5.0)
    policy.record_tick(lots_ctx(31))
    assert policy.adjust_profit_target(up, lots_ctx(31)) == pytest.approx(0.05)


def test_min_drop_ignores_a_shallow_forecast_fall(scripted):
    scripted.stub.mu = -0.02
    policy = TftTakeProfit(model="stub", bars_per_day=26, min_drop=0.05, check_bars=1)
    for t in range(40):
        policy.record_tick(lots_ctx(t))
    assert policy.fires == 0 and policy._component.last_mu < 0
    scripted.stub.mu = -0.1
    policy.record_tick(lots_ctx(40))
    assert policy.fires == 1


def test_it_refuses_in_sample_bars_like_the_sizer(scripted):
    scripted.stub = ScriptedForecaster()
    scripted.stub.valid_from = BARS.index[100]
    policy = TftTakeProfit(model="stub", bars_per_day=26, check_bars=1)
    with pytest.raises(ConfigurationError, match="training data"):
        for t in range(31):
            policy.record_tick(lots_ctx(t))


# ---------------------------------------------- 3. through the real controller


class AlternatingForecaster(ScriptedForecaster):
    """Up, then down, on alternate forecasts: buys and take-profits both."""

    def forecast(self, encoder, decoder_known):
        self.mu = abs(self.mu) * (1 if self.calls % 2 == 0 else -1)
        return super().forecast(encoder, decoder_known)


def _run(buy, sell):
    return (
        OptimizationController(historical_data=BARS)
        .run_sweep(
            grid_steps=[0.003],
            profit_targets=[0.02],
            strategy_class=ComposedStrategy,
            strategy_params_grid=[{"buy": buy, "sell": sell}],
            fill_model="intrabar",
            intrabar_fill="causal",
        )
        .iloc[0]
    )


@pytest.mark.parametrize(
    ("buy", "sell"),
    [
        (
            {"id": "ml_tft", "params": {"max_trade_pct": 0.05, "bars_per_day": 26, "model": "s"}},
            {"id": "tft_take_profit", "params": {"model": "s", "bars_per_day": 26}},
        ),
        (
            {"id": "hf_local_reference", "params": HF},
            {
                "id": "tft_take_profit",
                "params": {"model": "s", "bars_per_day": 26, "check_bars": 2},
            },
        ),
        (
            {"id": "ml_tft", "params": {"max_trade_pct": 0.05, "bars_per_day": 26, "model": "s"}},
            {"id": "age_decay", "params": {"after_bars": 26, "span_bars": 26}},
        ),
    ],
)
def test_tft_compositions_trade_through_the_controller(scripted, buy, sell):
    scripted.stub = AlternatingForecaster(mu=0.004, sigma=0.01)
    result = _run(buy, sell)
    assert not isinstance(result.get("error"), str), result.get("error")
    assert result["Trade Count"] > 0
    assert math.isfinite(result["Total Return %"])
