"""One risk report schedule through the backtest and the live loop gives the
same buys and steps; an advisory schedule gives exactly the buys no overlay
does (docs/daily_risk_report_plan.md, Phase 1's "done when").

Two sessions of minute bars falling then recovering; Friday's enforced
overlay widens the grid step x2 and halves each buy (tier 2). The backtest
is OptimizationController._simulate_single, the live side LiveTradingLoop
with a broker that fills every buy at its price before the next tick.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pandas as pd
import pytest

from engine.core.config import CostConfig
from engine.core.persistence import LedgerStore
from engine.core.risk_overlay import OverlaySchedule, SessionOverlay
from engine.core.trading_calendar import EASTERN
from engine.tests.test_live_trading_loop import FakeBroker, FakeMarketData, make_config
from engine.trading.live_trading_loop import LiveTradingLoop
from engine.trading.risk_manager import RiskManager
from research.optimization.optimization_controller import OptimizationController
from research.strategies.size_calculators import FixedPortfolioPercentage

THURSDAY, FRIDAY = date(2026, 11, 19), date(2026, 11, 20)
STEP, TARGET = 0.01, 0.5  # a target never reached: these sessions only buy


def session_bars(day: date, start: float) -> list[tuple[datetime, float]]:
    opens = datetime.combine(day, datetime.min.time().replace(hour=9, minute=30), tzinfo=EASTERN)
    out, price = [], start
    for minute in range(60):
        price *= 0.996 if minute < 40 else 1.003
        out.append((opens.astimezone(UTC) + timedelta(minutes=minute), round(price, 4)))
    return out


BARS = session_bars(THURSDAY, 100.0) + session_bars(FRIDAY, 95.0)


def schedule(mode: str) -> OverlaySchedule:
    return OverlaySchedule(
        [
            SessionOverlay(
                session=FRIDAY,
                mode=mode,
                tier=2,
                buy_multiplier=0.5,
                step_multiplier=2.0,
                supersedes=frozenset({"event_boosts"}),
            )
        ]
    )


def backtest(overlay: OverlaySchedule | None) -> tuple[list[tuple[datetime, float]], dict]:
    frame = pd.DataFrame(
        {
            "open": [p for _t, p in BARS],
            "high": [p for _t, p in BARS],
            "low": [p for _t, p in BARS],
            "close": [p for _t, p in BARS],
            "volume": [1000.0] * len(BARS),
        },
        index=pd.DatetimeIndex([t for t, _p in BARS], name="timestamp"),
    )
    result = OptimizationController(historical_data=frame)._simulate_single(
        step=STEP,
        target=TARGET,
        strategy_instance=FixedPortfolioPercentage(allocation_pct=0.05),
        symbol="TQQQ",
        initial_cash=100_000.0,
        cost_model=CostConfig().build(),
        risk_manager=RiskManager(overlay=overlay),
        fill_model="close",
    )
    blotter = result.trade_blotter
    buys = blotter[blotter["side"] == "buy"]
    return [
        (pd.Timestamp(t).to_pydatetime(), round(float(p) * float(q), 2))
        for t, p, q in zip(buys["timestamp"], buys["price"], buys["qty"], strict=True)
    ], result.metrics


def live(overlay: OverlaySchedule | None, tmp_path) -> list[tuple[datetime, float]]:
    store = LedgerStore(str(tmp_path / f"ledger-{id(overlay)}.db"))
    broker, market = FakeBroker(), FakeMarketData()
    loop = LiveTradingLoop(
        config=make_config(step=STEP, profit_target=TARGET),
        strategy=FixedPortfolioPercentage(allocation_pct=0.05),
        broker=broker,
        market_data=market,
        store=store,
        sleep=lambda _: None,
        risk_manager=RiskManager(overlay=overlay),
    )
    bought = []
    try:
        for stamp, price in BARS:
            market.push(price, ts=stamp)
            seen = len(broker.buys)
            loop.run_once()
            for _symbol, value, cid in broker.buys[seen:]:
                broker.fill(cid, qty=value / price, price=price)
                bought.append((stamp, round(value, 2)))
        loop.run_once()  # book the last fill
    finally:
        store.close()
    return bought


class TestParity:
    def test_the_same_schedule_buys_the_same_in_both(self, tmp_path):
        back, metrics = backtest(schedule("enforce"))
        forward = live(schedule("enforce"), tmp_path)
        assert [t for t, _v in back] == [t for t, _v in forward]
        for (_t, a), (_t2, b) in zip(back, forward, strict=True):
            assert a == pytest.approx(b, rel=1e-6)
        assert metrics["Overlay Sessions"] == 1 and metrics["Overlay Mean Step Multiplier"] == 2.0

    def test_friday_buys_fewer_and_smaller(self, tmp_path):
        plain, _ = backtest(None)
        governed, _ = backtest(schedule("enforce"))
        fri = lambda rows: [v for t, v in rows if t.astimezone(EASTERN).date() == FRIDAY]  # noqa: E731
        thu = lambda rows: [v for t, v in rows if t.astimezone(EASTERN).date() == THURSDAY]  # noqa: E731
        assert thu(plain) == thu(governed), "Thursday had no report: untouched"
        assert 0 < len(fri(governed)) < len(fri(plain))
        assert max(fri(governed)) < min(fri(plain))

    def test_advisory_trades_exactly_what_no_overlay_does(self, tmp_path):
        plain, _plain_metrics = backtest(None)
        advisory, advisory_metrics = backtest(schedule("advisory"))
        assert advisory == plain
        assert "Overlay Sessions" not in advisory_metrics
        assert live(schedule("advisory"), tmp_path) == live(None, tmp_path)
