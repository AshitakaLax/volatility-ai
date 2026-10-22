"""UltimateSizing as a live process runs it: a fresh process every session,
history replayed before the first tick, the durable book handed back, and
an exit that a bounded number of orders per tick must still finish.

The failure these pin was silent: a process started each morning with no
mode, so the flip to turbulent -- the only trigger of the regime exit --
was never seen, and the calm book rode every downturn."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from itertools import pairwise
from types import SimpleNamespace

import pandas as pd
import pytest

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from engine.core.ledger import AssetLotLedger
from engine.core.market_context import MarketContext
from engine.core.persistence import LedgerStore
from engine.data.alpaca_market_data import LiveBar
from engine.tests.test_live_trading_loop import FakeBroker, FakeMarketData
from engine.trading.live_trading_loop import LiveTradingLoop
from research.strategies.live_algorithm import build_strategy
from research.strategies.natr_regime import daily_bars
from research.strategies.strategy_registry import STRATEGIES
from research.strategies.ultimate_sizing import CALM, TURBULENT, UltimateSizing
from research.tests.test_ultimate_sizing import HF, _sessions

REGIME = {"natr_period": 5, "natr_lookback": 20, "regime_min_hold": 3, "bear_dd": None}
CALM_LOT = SimpleNamespace(order_id="calm-1", profit_target=0.3)


def _context(ts, row, i, *, equity=100_000.0, lots=0) -> MarketContext:
    return MarketContext(
        timestamp=ts,
        open=row["open"],
        high=row["high"],
        low=row["low"],
        close=row["close"],
        cash=equity,
        equity=equity,
        peak_equity=equity,
        drawdown=0.0,
        open_lot_count=lots,
        bar_index=i,
        time_of_day_flag=ts.hour * 60 + ts.minute - (14 * 60 + 30),
        volume=row["volume"],
    )


def _feed(strategy, df, *, equity=100_000.0, lots=1):
    """record_tick every bar; after each, ask the exit about one calm lot.
    Returns [(timestamp, mode, condemned?)]."""
    out = []
    for i, (ts, row) in enumerate(df.iterrows()):
        context = _context(ts, row, i, equity=equity, lots=lots)
        strategy.record_tick(context)
        out.append((ts, strategy.mode, bool(strategy.lots_to_liquidate([CALM_LOT], context))))
    return out


def _flip_day(df) -> object:
    """The first calm-to-turbulent session late enough for any warm-up."""
    days = sorted({t.date() for t in df.index})
    modes = {}
    for ts, mode, _ in _feed(UltimateSizing(**HF, **REGIME), df):
        modes[ts.date()] = mode
    pairs = pairwise(days[260:])
    return next(d for prev, d in pairs if modes[prev] == CALM and modes[d] == TURBULENT)


def test_a_restarted_process_sees_the_flip_and_exits_like_a_continuous_run():
    df = _sessions(300)
    flip = _flip_day(df)
    history, today = df[df.index.date < flip], df[df.index.date == flip]

    continuous = _feed(UltimateSizing(**HF, **REGIME), df[df.index.date <= flip])[-len(today) :]

    restarted = UltimateSizing(**HF, **REGIME)
    _feed(restarted, history, equity=0.0)  # the loop's neutral replay
    restarted.resume([CALM_LOT])
    after_restart = _feed(restarted, today)

    assert after_restart == continuous
    condemned = [c for _, _, c in after_restart]
    # This fixture's sessions have bars at minutes 0-9 and 380-389, so the
    # first at or after liquidate_minute (60) is 380.
    assert condemned == [False] * 10 + [True] * 10

    # What every live session did before: seed the regime, start with no mode.
    cold = UltimateSizing(**HF, **REGIME)
    cold.warm_up(daily_bars(history))
    assert not any(condemned for _, _, condemned in _feed(cold, today))


def test_calm_lots_left_after_the_exit_are_offered_until_the_spell_ends():
    """A live loop sends max_sells_per_tick orders a tick and a limit at the
    market can go unfilled; the exit asked for one bar only, so the rest of
    the book was never offered again."""
    df = _sessions(400)  # long enough for the spell after the flip to end
    flip = _flip_day(df)
    by_day: dict = {}
    for ts, mode, condemned in _feed(UltimateSizing(**HF, **REGIME), df):
        by_day.setdefault(ts.date(), []).append((ts, mode, condemned))

    flip_bars = by_day[flip]
    assert [c for _, _, c in flip_bars] == [False] * 10 + [True] * 10, "minutes 380-389"
    later = [d for d in sorted(by_day) if d > flip]
    turbulent = [d for d in later if by_day[d][0][1] == TURBULENT]
    calm = [d for d in later if by_day[d][0][1] == CALM]
    assert turbulent and calm
    for day in turbulent[:3]:
        assert [c for _, _, c in by_day[day]] == [False] * 10 + [True] * 10
    assert not any(c for d in calm for _, _, c in by_day[d])


def test_resume_tells_reversal_lots_from_calm_ones_by_their_target():
    strategy = UltimateSizing(**HF, **REGIME, reversal_target=0.06)
    reversal = SimpleNamespace(order_id="rev-1", profit_target=0.06)
    strategy.resume([CALM_LOT, reversal])
    strategy._exit_due = True
    assert strategy.lots_to_liquidate([CALM_LOT, reversal], None) == [CALM_LOT]
    assert strategy.reversal_open(SimpleNamespace(open_lot_count=2)) == 1


def test_it_asks_for_the_regimes_history_and_the_champions_windows():
    assert UltimateSizing(**HF).live_history_sessions() == 250 + 150
    defaults = {**HF, "vol_scale_exponent": -1.5, "vol_slow_days": 10.0}
    injected = UltimateSizing(**defaults, regime_by_date={DAY1.date(): True})
    assert injected.live_history_sessions() == 15, "an injected map needs no regime history"


# -- what build_strategy refuses for a live deployment ------------------------


def _config(**overrides) -> BacktestConfig:
    data = {
        "strategy": {"strategy_id": "ultimate", "strategy_params": dict(HF)},
        "grid": {"steps": [0.001], "profit_targets": [0.3]},
        "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
        "execution": {"allow_signal_exit": True},
        "live": {"enabled": True, "step": 0.001, "profit_target": 0.3},
    }
    for section, values in overrides.items():
        data[section] = {**data.get(section, {}), **values}
    return BacktestConfig.from_dict(data)


def test_a_live_ultimate_is_built_with_its_exit_on():
    assert isinstance(build_strategy(_config(), STRATEGIES), UltimateSizing)


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"execution": {"allow_signal_exit": False}}, "allow_signal_exit"),
        ({"live": {"extended_hours": True}}, "extended_hours"),
        ({"live": {"profit_target": 0.06}}, "reversal_target"),
    ],
)
def test_a_live_deployment_that_is_not_the_researched_strategy_is_refused(overrides, match):
    with pytest.raises(ConfigurationError, match=match):
        build_strategy(_config(**overrides), STRATEGIES)


def test_a_strategy_whose_history_the_loop_cannot_rebuild_is_refused():
    """Session state (warm_up) with no live replay (live_history_sessions)
    would start every session blind."""
    from research.strategies.live_algorithm import check_live_support

    class SessionStateOnly:
        def warm_up(self, daily) -> int:
            return 0

    with pytest.raises(ConfigurationError, match="backtest-only"):
        check_live_support(_config(), SessionStateOnly())


def test_the_paper_deployment_config_builds():
    from pathlib import Path

    config = BacktestConfig.from_yaml(
        Path(__file__).resolve().parents[2] / "config" / "ultimate_paper.yaml"
    )
    config.validate()
    assert config.live.enabled and config.live.paper_trading
    assert isinstance(build_strategy(config, STRATEGIES), UltimateSizing)


# -- through the real loop ----------------------------------------------------

DAY1 = datetime(2026, 3, 2, tzinfo=UTC)  # a Monday, EST: 09:30 ET is 14:30Z


def _at(day, minute) -> datetime:
    return day + timedelta(hours=14, minutes=30 + minute)


def test_the_live_loop_exits_the_whole_calm_book_in_one_order(tmp_path):
    day2 = DAY1 + timedelta(days=1)
    store = LedgerStore(str(tmp_path / "ledger.db"))
    ledger = AssetLotLedger()
    for i in range(3):
        store.record_open_lot(ledger.register_buy(f"calm-{i}", "TQQQ", 100.0, 1.0, 0.3))
    store.record_open_lot(ledger.register_buy("rev-0", "TQQQ", 90.0, 2.0, 0.06))

    config = _config(live={"max_sells_per_tick": 1})
    strategy = UltimateSizing(
        **HF, regime_by_date={DAY1.date(): True, day2.date(): False}, reversal_target=0.06
    )
    broker, market = FakeBroker(), FakeMarketData()
    loop = LiveTradingLoop(
        config=config,
        strategy=strategy,
        broker=broker,
        market_data=market,
        store=store,
        sleep=lambda _: None,
        history_provider=lambda symbol, sessions: pd.DataFrame(),
    )

    def tick(day, minute):
        market._bars.append(LiveBar(_at(day, minute), 95.0, 95.0, 95.0, 95.0, 0.0))
        loop.run_once()

    tick(DAY1, 200)
    tick(day2, 1)
    assert broker.sells == [], "the exit waits for liquidate_minute"
    tick(day2, 60)
    assert len(broker.sells) == 1, "one order, though max_sells_per_tick is 1"
    _symbol, qty, _price, cid = broker.sells[0]
    assert qty == pytest.approx(3.0)
    assert loop.state.open_orders[cid].exit_lot_ids == ("calm-0", "calm-1", "calm-2"), (
        "the reversal lot is kept"
    )
    store.close()


def test_its_diagnostics_say_why_it_is_not_grid_buying_and_until_when():
    """The Live page's "why is it not buying": the mode, since when, the
    readings behind it, and the first session it may change."""
    from engine.core.trading_calendar import next_session

    df = _sessions(300)
    flip = _flip_day(df)
    strategy = UltimateSizing(**HF, **REGIME)
    _feed(strategy, df[df.index.date <= flip])
    diag = strategy.diagnostics()
    assert diag["ultimate_mode"] == TURBULENT
    assert diag["regime_since"] == flip.isoformat()
    assert diag["regime_held"] == 1 and diag["regime_min_hold"] == 3
    assert diag["regime_reading"] == TURBULENT
    assert diag["regime_natr"] > diag["regime_median"]
    # Held one session of a minimum three: the third session after this one.
    assert diag["regime_earliest_change"] == next_session(flip, 3).isoformat()
    assert diag["ultimate_exit_active"] is True


def test_an_injected_regime_reports_no_readings_it_does_not_have():
    from datetime import date

    strategy = UltimateSizing(**HF, regime_by_date={date(2026, 1, 2): True})
    assert "regime_since" not in strategy.diagnostics()


# -- ultimate_rsp: a daily exposure book, live ----------------------------------

# config/fidelity_live.yaml's ultimate_rsp (2026-10-22): the campaign's best
# Calmar on RSP.
DEPLOYED_RSP = {
    "pd_periods": "21,42,63",
    "pd_lookbacks": "50,100",
    "ad_params": "3/10,5/20,10/40",
    "ad_lookbacks": "100,250",
    "pd_weight": 0.75,
    "execute_minute": 60,
    "rebalance_band": 0.1,
}


def _rsp_config(**overrides) -> BacktestConfig:
    data = {
        "strategy": {"strategy_id": "ultimate_rsp", "strategy_params": dict(DEPLOYED_RSP)},
        "grid": {"steps": [0.001], "profit_targets": [10.0]},
        "backtest": {"symbol": "RSP", "initial_cash": 25_000.0},
        "execution": {"allow_signal_exit": True, "settlement_days": 1},
        "live": {"enabled": True, "step": 0.001, "profit_target": 10.0},
    }
    for section, values in overrides.items():
        data[section] = {**data.get(section, {}), **values}
    return BacktestConfig.from_dict(data)


def test_a_live_ultimate_rsp_is_built_with_its_exit_on():
    from research.strategies.ultimate_rsp_sizing import UltimateRspSizing

    strategy = build_strategy(_rsp_config(), STRATEGIES)
    assert isinstance(strategy, UltimateRspSizing)
    assert strategy.live_history_sessions() == (40 - 1 + 250) + 150


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"execution": {"allow_signal_exit": False}}, "allow_signal_exit"),
        ({"live": {"extended_hours": True}}, "extended_hours"),
    ],
)
def test_a_live_ultimate_rsp_without_what_it_was_researched_with_is_refused(overrides, match):
    with pytest.raises(ConfigurationError, match=match):
        build_strategy(_rsp_config(**overrides), STRATEGIES)


def test_the_live_loop_replays_its_history_then_moves_to_the_target_once(tmp_path):
    """Through the real loop: the history replayed with no replayed bar
    trading, nothing before execute_minute, then ONE buy of target x equity
    -- and no second rebalance that session."""
    from research.strategies.ultimate_rsp_sizing import UltimateRspSizing
    from research.tests.test_ultimate_rsp_sizing import SMALL as RSP_SMALL
    from research.tests.test_ultimate_rsp_sizing import _daily as rsp_daily
    from research.tests.test_ultimate_rsp_sizing import _sessions as rsp_sessions

    config = _rsp_config(strategy={"strategy_params": dict(RSP_SMALL)})
    strategy = build_strategy(config, STRATEGIES)
    history = rsp_sessions(strategy.live_history_sessions())
    live_day = pd.bdate_range(history.index[-1].date(), periods=2)[-1].date()
    open_ = pd.Timestamp(f"{live_day} 09:31", tz="America/New_York").tz_convert("UTC")
    # The target the first live session trades: every replayed session's votes.
    reference = UltimateRspSizing(**RSP_SMALL)._signal
    reference.warm_up(rsp_daily(history))
    reference.observe(open_, 100.0, 100.0, 100.0, 0.0)
    want = reference.target
    assert want > strategy.rebalance_band, "this history must call for a rebalance"

    store = LedgerStore(str(tmp_path / "ledger.db"))
    broker, market = FakeBroker(), FakeMarketData()
    loop = LiveTradingLoop(
        config=config,
        strategy=strategy,
        broker=broker,
        market_data=market,
        store=store,
        sleep=lambda _: None,
        history_provider=lambda symbol, sessions: history,
    )
    assert loop.replayed_bars == len(history)
    assert broker.buys == [] and broker.sells == [], "no replayed bar trades"

    def tick(at):
        market._bars.append(LiveBar(at.to_pydatetime(), 100.0, 100.0, 100.0, 100.0, 1_000.0))
        loop.run_once()

    tick(open_)
    assert broker.buys == [], "it waits for execute_minute"
    tick(open_ + pd.Timedelta(minutes=59))  # 10:30 ET, minute 60
    assert len(broker.buys) == 1
    _symbol, value, _cid = broker.buys[0]
    assert value == pytest.approx(min(want, 1.0 - strategy.cash_buffer) * 25_000.0)
    tick(open_ + pd.Timedelta(minutes=60))
    assert len(broker.buys) == 1, "once a session"
    store.close()
