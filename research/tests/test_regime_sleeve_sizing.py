"""RegimeSleeveSizing through the real controller, both fill models.

Six synthetic sessions, Jan 2-9 2024, regime calm / calm / TURBULENT /
TURBULENT / calm / calm. The calm sleeve must buy only on calm sessions
and close its whole book on the first bar of Jan 4; the turbulent sleeve
is its mirror. With allow_signal_exit off, the hook must be inert.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.optimization.optimization_controller import OptimizationController
from research.strategies.gated_local_reference_sizing import NO_BUY_LEVEL
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from research.strategies.regime_sleeve_sizing import RegimeSleeveSizing
from research.tests.test_gated_local_reference_sizing import (
    FILL_MODELS,
    HF_PARAMS,
    OUTCOMES,
    _minute_sessions,
)

DATES = [date(2024, 1, d) for d in (2, 3, 4, 5, 8, 9)]
REGIME = dict(zip(DATES, [True, True, False, False, True, True], strict=True))
TURBULENT = {d for d, calm in REGIME.items() if not calm}


class Factory:
    def __init__(self, sleeve, regime):
        self.sleeve, self.regime = sleeve, regime
        self.__name__ = f"RegimeSleeve[{sleeve}]"

    def __call__(self, **params):
        return RegimeSleeveSizing(sleeve=self.sleeve, regime_by_date=self.regime, **params)


def _blotter(sleeve, fill_model, allow_signal_exit=True):
    controller = OptimizationController(historical_data=_minute_sessions())
    _, full = controller.run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.05],  # wide: almost nothing exits at target, so the flip does
        strategy_class=Factory(sleeve, REGIME),
        strategy_params_grid=[dict(HF_PARAMS)],
        fill_model=fill_model,
        allow_signal_exit=allow_signal_exit,
        return_full_results=True,
    )
    blotter = full[0].trade_blotter.copy()
    blotter["ts"] = pd.to_datetime(blotter["timestamp"], utc=True)
    blotter["day"] = blotter["ts"].dt.date
    return blotter


def _signal_exits(blotter) -> pd.Series:
    """Rows sold on a signal. A blotter with no sells has no sell_reason
    column at all, which means no signal exits rather than an error."""
    if "sell_reason" not in blotter.columns:
        return pd.Series(False, index=blotter.index)
    return blotter["sell_reason"].astype(str).str.contains("signal", case=False)


def _open_qty_after(blotter, ts) -> float:
    upto = blotter[blotter["ts"] <= ts]
    signed = upto["qty"].where(upto["side"] == "buy", -upto["qty"])
    return float(signed.sum())


def _first_bar(day) -> pd.Timestamp:
    return pd.Timestamp(day.isoformat() + " 14:30", tz="UTC")


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_always_is_the_champion_exactly(fill_model):
    df = _minute_sessions(gap_day=4)

    def run(cls):
        return (
            OptimizationController(historical_data=df)
            .run_sweep(
                grid_steps=[0.002],
                profit_targets=[0.004],
                strategy_class=cls,
                strategy_params_grid=[dict(HF_PARAMS)],
                fill_model=fill_model,
                allow_signal_exit=True,
            )
            .iloc[0]
        )

    champion, always = run(HighFrequencyLocalReferenceSizing), run(Factory("always", {}))
    assert champion["Trade Count"] > 0
    for column in OUTCOMES:
        assert always[column] == champion[column], column


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_calm_sleeve_buys_only_while_calm_and_closes_its_book_on_the_flip(fill_model):
    b = _blotter("calm", fill_model)
    buys = b[b["side"] == "buy"]
    assert set(buys["day"]) == set(DATES) - TURBULENT
    flip = _first_bar(date(2024, 1, 4))
    exits = b[(b["ts"] == flip) & _signal_exits(b)]
    assert len(exits) > 0, "the flip bar must carry the signal exits"
    assert _open_qty_after(b, flip) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_turbulent_sleeve_is_the_mirror(fill_model):
    b = _blotter("turbulent", fill_model)
    buys = b[b["side"] == "buy"]
    assert set(buys["day"]) == TURBULENT
    flip_back = _first_bar(date(2024, 1, 8))
    assert _open_qty_after(b, flip_back) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_without_allow_signal_exit_the_book_is_held(fill_model):
    """Half a gate, as SizingStrategy.lots_to_liquidate documents: the
    hook alone realizes nothing. Buying still stops."""
    b = _blotter("calm", fill_model, allow_signal_exit=False)
    assert not _signal_exits(b).any()
    assert set(b[b["side"] == "buy"]["day"]).isdisjoint(TURBULENT)
    assert _open_qty_after(b, _first_bar(date(2024, 1, 4))) > 0


# --------------------------------------------------------------------
# Unit-level state machine


def _ctx(day: date, minute: int = 0, flag=None, price: float = 100.0) -> MarketContext:
    ts = datetime(day.year, day.month, day.day, 14, 30, tzinfo=UTC) + timedelta(minutes=minute)
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
        open_lot_count=0,
        bar_index=0,
        time_of_day_flag=minute if flag is None else flag,
    )


def test_inactive_before_the_first_known_session():
    s = RegimeSleeveSizing(sleeve="calm", regime_by_date={DATES[2]: True}, **HF_PARAMS)
    s.record_tick(_ctx(DATES[0]))
    assert s.active is False
    assert s._grid_trigger_level(_ctx(DATES[0]), 100.0, 0.01) == NO_BUY_LEVEL
    s.record_tick(_ctx(DATES[2]))
    assert s.active is True


def test_a_missing_session_keeps_the_last_known_regime():
    s = RegimeSleeveSizing(sleeve="calm", regime_by_date={DATES[0]: True}, **HF_PARAMS)
    s.record_tick(_ctx(DATES[0]))
    s.record_tick(_ctx(DATES[1]))  # not in the map
    assert s.active is True


def test_liquidation_is_an_edge_not_a_level():
    s = RegimeSleeveSizing(sleeve="calm", regime_by_date=REGIME, **HF_PARAMS)
    lots = ["lot-a", "lot-b"]
    s.record_tick(_ctx(DATES[1]))
    assert s.lots_to_liquidate(lots, _ctx(DATES[1])) == []
    s.record_tick(_ctx(DATES[2]))  # flips to turbulent
    assert s.lots_to_liquidate(lots, _ctx(DATES[2])) == lots
    s.record_tick(_ctx(DATES[2], minute=1))
    assert s.lots_to_liquidate(lots, _ctx(DATES[2], minute=1)) == []
    assert s.flips_out == 1


def test_out_of_session_bars_neither_flip_nor_clear_state():
    s = RegimeSleeveSizing(sleeve="calm", regime_by_date=REGIME, **HF_PARAMS)
    s.record_tick(_ctx(DATES[1]))
    s.record_tick(_ctx(DATES[2], minute=-60, flag=-1))  # pre-market of the flip day
    assert s.active is True
    s.record_tick(_ctx(DATES[2]))
    assert s.active is False and s.flips_out == 1


@pytest.mark.parametrize(
    "kwargs",
    [{"sleeve": "bear"}, {"sleeve": "calm"}, {"sleeve": "turbulent", "regime_by_date": {}}],
)
def test_bad_construction(kwargs):
    with pytest.raises(ConfigurationError):
        RegimeSleeveSizing(**kwargs, **HF_PARAMS)


def test_reentry_is_measured_from_the_market_not_a_stale_fill():
    """A sleeve back from sitting out a crash must not measure its first
    pullback from a pre-crash last_buy_price."""
    s = RegimeSleeveSizing(sleeve="calm", regime_by_date=REGIME, **HF_PARAMS)
    s.record_tick(_ctx(DATES[2], price=100.0))  # turbulent: inactive
    s.record_tick(_ctx(DATES[4], price=100.0))  # calm again: fresh
    stale = 500.0
    level = s._grid_trigger_level(_ctx(DATES[4]), last_buy_price=stale, step=0.01)
    assert level == pytest.approx(100.0 * 0.99)
    # Once a lot is held, the champion's own rule applies again.
    held = MarketContext(**{**_ctx(DATES[4], minute=1).__dict__, "open_lot_count": 1})
    s.record_tick(held)
    assert s._grid_trigger_level(held, stale, 0.01) == pytest.approx(stale * 0.99)
