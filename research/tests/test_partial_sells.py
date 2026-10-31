"""Partial-lot selling through the backtest and the intraday replay (Phase 1
of docs/research/buy-sell-composition.md): a two-rung ladder and a partial
signal exit, run end to end, with the books checked from the blotter."""

from __future__ import annotations

import pandas as pd
import pytest

from engine.core.exit_policy import ExitOrder
from research.optimization import intraday_validation
from research.optimization.optimization_controller import OptimizationController
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from tests.fixtures import composition_baseline as fixture

HF = dict(fixture.HF)
BASE_TARGET = 0.01
SECOND_RUNG = 0.02
# A tranche is floored to nine decimals, so the fraction sold lands a hair
# under the rung it reached: compare with a tolerance far above that step.
RUNG_TOLERANCE = 1e-6


class _Ladder(HighFrequencyLocalReferenceSizing):
    """Half of each lot at the base target, the rest at SECOND_RUNG. The
    rung is read from the lot itself (sold_fraction), never remembered."""

    def wants_lot_retargeting(self) -> bool:
        return True

    def adjust_profit_target(self, lot, context):
        return SECOND_RUNG if lot.sold_fraction >= 0.5 - RUNG_TOLERANCE else None

    def harvest_quantity(self, lot, context):
        return lot.original_shares * 0.5 if lot.sold_fraction < 0.5 - RUNG_TOLERANCE else lot.shares


class _TrimsOnBigDrop(HighFrequencyLocalReferenceSizing):
    """Sells half of every open lot on any bar that falls 1% from its open."""

    def lots_to_liquidate(self, open_lots, context):
        if context.close < context.open * 0.99:
            return [ExitOrder(lot, lot.shares / 2) for lot in open_lots]
        return []


@pytest.fixture(scope="module")
def ohlcv():
    return fixture.load_ohlcv()


def _run(df, strategy, **sweep):
    summary, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[BASE_TARGET],
        strategy_class=strategy,
        strategy_params_grid=[dict(HF)],
        return_full_results=True,
        **sweep,
    )
    return summary.iloc[0], full[0].trade_blotter


def _per_lot(blotter: pd.DataFrame) -> pd.DataFrame:
    buys = blotter[blotter["side"] == "buy"].set_index("lot_id")
    sells = blotter[blotter["side"] == "sell"]
    return pd.DataFrame(
        {
            "bought": buys["qty"],
            "buy_price": buys["price"],
            "sold": sells.groupby("lot_id")["qty"].sum(),
            "sales": sells.groupby("lot_id").size(),
        }
    ).fillna({"sold": 0.0, "sales": 0})


@pytest.mark.parametrize(
    "sweep",
    [{"fill_model": "close"}, {"fill_model": "intrabar", "intrabar_fill": "causal"}],
    ids=["close", "intrabar"],
)
def test_a_ladder_sells_each_lot_in_two_halves(ohlcv, sweep):
    row, blotter = _run(ohlcv, _Ladder, **sweep)
    lots = _per_lot(blotter)
    sells = blotter[blotter["side"] == "sell"]

    assert (lots["sold"] <= lots["bought"] * (1 + 1e-9)).all(), "never more than was bought"
    two = lots[lots["sales"] == 2]
    assert len(two) > 10, "the ladder must actually fire"
    assert (lots["sales"] <= 2).all()
    for lot_id in two.index[:50]:
        first, second = sells[sells["lot_id"] == lot_id].sort_values("bar_index")["qty"]
        assert first == pytest.approx(lots.loc[lot_id, "bought"] / 2)
        assert first + second == pytest.approx(lots.loc[lot_id, "bought"])
    # The second half sold at the higher rung, never below it.
    second_sales = sells[sells.duplicated("lot_id", keep="first")]
    paid = lots.loc[second_sales["lot_id"], "buy_price"].to_numpy()
    assert (second_sales["price"].to_numpy() >= paid * (1 + SECOND_RUNG) * (1 - 1e-9)).all()

    assert (sells["profit_realized"] >= -1e-8).all(), "a ladder is still no-loss"
    fully_sold = int((lots["sold"] >= lots["bought"] * (1 - 1e-9)).sum())
    assert row["Closed Trade Count"] == fully_sold
    assert row["Open Trade Count"] == len(lots) - fully_sold
    if sweep["fill_model"] == "close":
        # Fills are exactly at target here, so the target-based realized PnL
        # and the blotter's per-sale figures must agree -- including every
        # tranche sold off a lot that is still open.
        assert row["Realized PnL"] == pytest.approx(sells["profit_realized"].sum(), abs=1e-6)


def test_the_ladder_differs_from_whole_lot_selling(ohlcv):
    whole_row, whole = _run(ohlcv, HighFrequencyLocalReferenceSizing)
    ladder_row, ladder = _run(ohlcv, _Ladder)
    assert (whole.groupby("lot_id").size() <= 2).all()
    assert len(ladder[ladder["side"] == "sell"]) > len(whole[whole["side"] == "sell"]) * 0.5
    assert ladder_row["Final Equity"] != whole_row["Final Equity"]


def test_a_partial_signal_exit_halves_every_lot_and_leaves_the_rest_to_its_target(ohlcv):
    row, blotter = _run(
        ohlcv,
        _TrimsOnBigDrop,
        fill_model="intrabar",
        intrabar_fill="causal",
        allow_signal_exit=True,
    )
    sells = blotter[blotter["side"] == "sell"]
    exits = sells[sells["sell_reason"].str.contains("signal_exit")]
    targets = sells[sells["sell_reason"].str.contains("profit_target")]
    assert len(exits) > 0 and row["Signal Exit Count"] == len(exits)
    lots = _per_lot(blotter)
    assert (lots["sold"] <= lots["bought"] * (1 + 1e-9)).all()
    trimmed_then_harvested = set(exits["lot_id"]) & set(targets["lot_id"])
    assert trimmed_then_harvested, "the half left open sells at its target later"


def test_without_the_flag_a_partial_signal_exit_sells_nothing(ohlcv):
    _, gated = _run(ohlcv, _TrimsOnBigDrop, fill_model="intrabar", intrabar_fill="causal")
    _, plain = _run(
        ohlcv, HighFrequencyLocalReferenceSizing, fill_model="intrabar", intrabar_fill="causal"
    )
    assert gated.equals(plain)


def test_the_intraday_replay_sells_the_ladder_too(ohlcv):
    whole = intraday_validation.simulate_single_intraday(
        ohlcv, 0.002, BASE_TARGET, HighFrequencyLocalReferenceSizing, dict(HF)
    )
    ladder = intraday_validation.simulate_single_intraday(
        ohlcv, 0.002, BASE_TARGET, _Ladder, dict(HF)
    )
    assert ladder["Final Equity"] != whole["Final Equity"]
    assert ladder["Realized PnL"] > 0
