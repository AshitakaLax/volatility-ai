"""research/composition/exit_library.py (Phase 3 of
docs/research/buy-sell-composition.md): every sell policy, end to end with
the champion buying, held to the properties that make the matrix's cells
safe to compare -- then each policy's own rule, unit by unit."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from engine.core.exit_policy import ExitOrder
from engine.core.ledger import AssetLotLedger
from engine.core.market_context import MarketContext
from research.composition import exit_library as lib
from research.composition.composed_strategy import ComposedStrategy
from research.composition.exits import EXIT_DEFAULTS, EXITS
from research.optimization.optimization_controller import OptimizationController
from research.strategies.live_algorithm import build_strategy
from research.strategies.strategy_registry import STRATEGIES, may_realize_loss
from tests.fixtures import composition_baseline as fixture

HF = dict(fixture.HF)
BUY = {"id": "hf_local_reference", "params": HF}


@pytest.fixture(scope="module")
def ohlcv():
    return fixture.load_ohlcv()


def _params_for(exit_id, df):
    params = dict(EXIT_DEFAULTS[exit_id])
    if exit_id.startswith("regime_exit"):
        # The internal regime carries no flag for 250 sessions; inject the
        # causal one this dataset was built around, as the pinned cases do.
        params["regime_by_date"] = fixture.causal_regime(df)
    if exit_id == "inventory_pressure":
        params.update(start_lots=20, full_lots=200)
    return params


def _run(df, sell, **sweep):
    summary, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.01],
        strategy_class=ComposedStrategy,
        strategy_params_grid=[{"buy": BUY, "sell": sell}],
        fill_model="intrabar",
        intrabar_fill="causal",
        allow_signal_exit=True,
        return_full_results=True,
        **sweep,
    )
    assert full[0] is not None, summary.to_dict("records")
    return summary.iloc[0], full[0].trade_blotter


@pytest.fixture(scope="module")
def runs(ohlcv):
    return {
        exit_id: _run(ohlcv, {"id": exit_id, "params": _params_for(exit_id, ohlcv)})
        for exit_id in sorted(EXITS)
    }


# --- properties every policy is held to -------------------------------------


@pytest.mark.parametrize("exit_id", sorted(EXITS))
def test_a_no_loss_policy_never_realises_a_loss(runs, exit_id):
    _, blotter = runs[exit_id]
    sells = blotter[blotter["side"] == "sell"]
    losing = sells[sells["profit_realized"] < -1e-8]
    if EXITS[exit_id].can_realize_loss:
        assert (losing["sell_reason"].str.contains("signal_exit")).all()
    else:
        assert losing.empty, f"{exit_id} realised {len(losing)} loss(es)"
        assert not sells["sell_reason"].str.contains("signal_exit").any()


@pytest.mark.parametrize("exit_id", sorted(EXITS))
def test_a_policy_never_sells_more_than_a_lot_holds(runs, exit_id):
    _, blotter = runs[exit_id]
    bought = blotter[blotter["side"] == "buy"].groupby("lot_id")["qty"].sum()
    sold = blotter[blotter["side"] == "sell"].groupby("lot_id")["qty"].sum()
    assert (sold <= bought.reindex(sold.index) * (1 + 1e-9)).all()


@pytest.mark.parametrize("exit_id", sorted(set(EXITS) - {"fixed_target"}))
def test_every_policy_changes_what_sells(runs, exit_id):
    """On this dataset each policy's rule fires: a policy that sold exactly
    like the fixed target would be a matrix row measuring nothing."""
    assert not runs[exit_id][1].equals(runs["fixed_target"][1]), exit_id


@pytest.mark.parametrize("exit_id", ["scale_out", "scale_out_trail", "regime_exit_partial"])
def test_the_partial_policies_sell_lots_in_parts(runs, exit_id):
    sells = runs[exit_id][1]
    sells = sells[sells["side"] == "sell"]
    assert sells.groupby("lot_id").size().max() >= 2


def test_only_the_regime_exits_are_on_the_loss_capable_track():
    capable = {exit_id for exit_id, cls in EXITS.items() if cls.can_realize_loss}
    assert capable == {"regime_exit", "regime_exit_partial"}
    assert may_realize_loss("composed", {"buy": BUY, "sell": {"id": "regime_exit"}})
    assert may_realize_loss(
        "composed", {"buy": BUY, "sell": [{"id": "trailing"}, {"id": "regime_exit_partial"}]}
    )
    assert not may_realize_loss("composed", {"buy": BUY, "sell": {"id": "scale_out"}})


def test_a_live_config_with_a_loss_capable_sell_needs_the_files_flag():
    data = {
        "strategy": {
            "strategy_id": "composed",
            "strategy_params": {"buy": BUY, "sell": {"id": "regime_exit"}},
        },
        "grid": {"steps": [0.001], "profit_targets": [0.01]},
        "backtest": {"symbol": "TQQQ"},
        "live": {"enabled": True, "paper_trading": True, "step": 0.001, "profit_target": 0.01},
    }
    with pytest.raises(ConfigurationError, match="allow_signal_exit"):
        build_strategy(BacktestConfig.from_dict(data), STRATEGIES)
    data["execution"] = {"allow_signal_exit": True}
    build_strategy(BacktestConfig.from_dict(data), STRATEGIES)


@pytest.mark.parametrize("exit_id", sorted(EXITS))
def test_every_policy_constructs_from_its_defaults(exit_id):
    EXITS[exit_id](**EXIT_DEFAULTS[exit_id])


# --- each policy's own rule ----------------------------------------------------

T0 = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)


def _ctx(price=100.0, lots=1, minute=0, day=0, bar=0, high=None):
    return MarketContext(
        timestamp=T0 + timedelta(days=day, minutes=minute),
        open=price,
        high=high if high is not None else price,
        low=price,
        close=price,
        cash=1e5,
        equity=1e5,
        peak_equity=1e5,
        drawdown=0.0,
        open_lot_count=lots,
        bar_index=bar,
        time_of_day_flag=minute,
    )


def _lot(shares=10.0, buy=100.0, target=0.01, oid="L"):
    return AssetLotLedger().register_buy(oid, "TQQQ", buy, shares, target)


def test_scale_out_walks_its_rungs_from_what_has_sold():
    policy = lib.ScaleOut("0.25@0.01,0.25@0.02,0.5@0.05")
    ledger = AssetLotLedger()
    lot = ledger.register_buy("L", "TQQQ", 100.0, 8.0, 0.007)
    assert policy.adjust_profit_target(lot, _ctx()) == 0.01
    assert policy.harvest_quantity(lot, _ctx()) == pytest.approx(2.0)
    ledger.close_lot(lot, sell_qty=2.0, execution_price=101.0)
    assert policy.adjust_profit_target(lot, _ctx()) == 0.02
    assert policy.harvest_quantity(lot, _ctx()) == pytest.approx(2.0)
    ledger.close_lot(lot, sell_qty=2.0, execution_price=102.0)
    assert policy.adjust_profit_target(lot, _ctx()) == 0.05
    assert policy.harvest_quantity(lot, _ctx()) == lot.shares == 4.0


def test_scale_out_sells_a_dust_tranche_whole():
    policy = lib.ScaleOut("0.5@0.01,0.5@0.03", min_tranche_notional=60.0)
    lot = _lot(shares=1.0)
    assert policy.harvest_quantity(lot, _ctx(price=101.0)) == 1.0  # $50 half < $60


@pytest.mark.parametrize(
    "rungs", ["", "0.5@0.01", "0.5@0.03,0.5@0.01", "half@0.01,0.5@0.02", "0.5@0,0.5@0.01"]
)
def test_scale_out_refuses_a_bad_ladder(rungs):
    with pytest.raises(ConfigurationError):
        lib.ScaleOut(rungs)


def test_scale_out_trail_sells_its_part_then_lifts_and_trails_the_rest():
    policy = lib.ScaleOutTrail(
        0.5, 0.01, trail_pct=0.02, min_profit_target=0.005, runner_target=0.4
    )
    ledger = AssetLotLedger()
    lot = ledger.register_buy("L", "TQQQ", 100.0, 10.0, 0.01)
    assert policy.adjust_profit_target(lot, _ctx(110.0)) is None  # already at first_target
    assert policy.harvest_quantity(lot, _ctx(110.0)) == 5.0
    ledger.close_lot(lot, sell_qty=5.0, execution_price=101.0)
    assert policy.adjust_profit_target(lot, _ctx(110.0)) == 0.4  # lifted once
    lot.retarget(0.4)
    trailed = policy.adjust_profit_target(lot, _ctx(110.0))
    assert trailed == pytest.approx(110.0 * 0.98 / 100.0 - 1)  # from the peak since entry
    lot.retarget(trailed)
    restarted = lib.ScaleOutTrail(0.5, 0.01, trail_pct=0.02, runner_target=0.4)
    restarted.resume([lot])
    assert restarted.adjust_profit_target(lot, _ctx(100.0)) != 0.4, "never lifted twice"


def test_age_decay_holds_then_decays_to_its_floor():
    policy = lib.AgeDecay(after_bars=2, span_bars=4, floor=0.002, check_bars=1)
    lot = _lot(target=0.01)
    targets = []
    for bar in range(8):
        policy.record_tick(_ctx(lots=1, bar=bar))
        new = policy.adjust_profit_target(lot, _ctx())
        if new is not None:
            lot.retarget(new)
        targets.append(round(lot.profit_target, 6))
    assert targets[:3] == [0.01, 0.01, 0.01]
    assert targets[3] == pytest.approx(0.008)
    assert targets[-1] == pytest.approx(0.002)


def test_vol_scaled_target_reads_only_the_bars_before():
    import math
    import statistics
    from itertools import pairwise

    policy = lib.VolScaledTarget(
        k=2.0, window_bars=8, horizon_bars=4, min_target=1e-4, max_target=1
    )
    prices = [100, 101, 100, 102, 101]
    for i, price in enumerate(prices):
        policy.record_tick(_ctx(price=price, lots=0, bar=i))
    policy.record_tick(_ctx(price=200.0, lots=1, bar=5))  # a huge move on the lot's own bar
    returns = [math.log(b / a) for a, b in pairwise(prices)]
    expected = statistics.stdev(returns)  # through the previous bar, without the jump
    assert policy._sigma == pytest.approx(expected)
    target = policy.adjust_profit_target(_lot(), _ctx(200.0))
    assert target == pytest.approx(2.0 * expected * 2.0)
    assert policy.adjust_profit_target(_lot(), _ctx(200.0)) is None, "set once per lot"


def test_vol_scaled_target_leaves_resumed_lots_alone():
    policy = lib.VolScaledTarget()
    lot = _lot()
    policy.resume([lot])
    policy._sigma = 0.01
    assert policy.adjust_profit_target(lot, _ctx()) is None


def test_inventory_pressure_lowers_targets_as_the_book_grows_and_never_raises():
    policy = lib.InventoryPressure(start_lots=10, full_lots=20, floor=0.002)
    lot = _lot(target=0.012)
    policy.record_tick(_ctx(lots=5))
    assert not policy.wants_lot_retargeting()
    policy.record_tick(_ctx(lots=15))
    lot.retarget(policy.adjust_profit_target(lot, _ctx()))
    assert lot.profit_target == pytest.approx(0.007)
    policy.record_tick(_ctx(lots=12))
    assert policy.adjust_profit_target(lot, _ctx()) is None, "ratchets down only"


class _Gate:
    kind = "gate"
    history_sessions = 0

    def __init__(self):
        self.suppressed = False

    def observe(self, context):
        pass


def test_signal_take_profit_sells_the_lots_in_profit_when_the_gate_shuts():
    policy = lib.SignalTakeProfit(min_gain=0.005, fraction=0.5)
    policy._component = _Gate()
    up, flat = _lot(oid="up", target=0.05), _lot(oid="flat", target=0.05)
    policy.record_tick(_ctx(price=101.0))
    assert not policy.wants_lot_retargeting()
    policy._component.suppressed = True
    policy.record_tick(_ctx(price=101.0))
    assert policy.wants_lot_retargeting()
    gain = policy.adjust_profit_target(up, _ctx(101.0))
    assert gain == pytest.approx(0.01, abs=1e-8) and up.buy_price * (1 + gain) <= 101.0
    flat_lot = AssetLotLedger().register_buy("flat2", "TQQQ", 100.6, 10.0, 0.05)
    assert policy.adjust_profit_target(flat_lot, _ctx(101.0)) is None  # under min_gain
    assert policy.adjust_profit_target(flat, _ctx(100.2)) is None
    up.retarget(gain)
    assert policy.harvest_quantity(up, _ctx(101.0)) == 5.0
    policy.record_tick(_ctx(price=101.0))  # still shut: no second signal
    assert policy.adjust_profit_target(up, _ctx(101.0)) == 0.05, "the rest gets its target back"


def test_signal_take_profit_needs_a_gate():
    with pytest.raises(ConfigurationError, match="not a gate"):
        lib.SignalTakeProfit(signal="atr_sizing")


def test_a_regime_exit_fires_at_its_minute_of_the_flip_session():
    calm = {(T0 + timedelta(days=d)).date(): d < 2 for d in range(4)}
    policy = lib.RegimeExitPartial(fraction=0.25, liquidate_minute=30, regime_by_date=calm)
    lot = _lot(shares=8.0)
    fired = []
    for day in range(4):
        for minute in (0, 15, 30, 45):
            policy.record_tick(_ctx(day=day, minute=minute))
            out = policy.lots_to_liquidate([lot], _ctx(day=day, minute=minute))
            if out:
                fired.append((day, minute, out))
    assert [(d, m) for d, m, _ in fired] == [(2, 30)], (
        "once, at minute 30 of the first turbulent day"
    )
    (order,) = fired[0][2]
    assert isinstance(order, ExitOrder) and order.quantity == 2.0
