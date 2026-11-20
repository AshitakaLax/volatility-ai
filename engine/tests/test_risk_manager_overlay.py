"""The RiskManager's risk report overlay (engine/trading/risk_manager.py):
0 <= approved <= proposed always, no overlay (or an advisory one, or no `at`)
is today's clamp exactly, and the levers apply in the plan's order."""

from __future__ import annotations

import random
from datetime import UTC, date, datetime, timedelta

import pytest

from engine.core.market_context import MarketContext
from engine.core.risk_overlay import OverlaySchedule, SessionOverlay
from engine.trading import decision_cycle
from engine.trading.risk_manager import RiskManager

FRIDAY = date(2026, 11, 20)
AT = datetime(2026, 11, 20, 15, 0, tzinfo=UTC)  # 10:00 ET Friday


def manager(overlay: SessionOverlay | None = None, **limits) -> RiskManager:
    schedule = OverlaySchedule([overlay]) if overlay is not None else None
    return RiskManager(overlay=schedule, **limits)


def enforced(**fields) -> SessionOverlay:
    return SessionOverlay(session=FRIDAY, mode="enforce", **fields)


class TestNoOverlayIsToday:
    def test_bit_for_bit(self):
        rng = random.Random(5)
        plain = RiskManager(max_concurrent_lots=40, dd_exposure_start=0.05, dd_exposure_full=0.2)
        for _ in range(500):
            args = (
                rng.uniform(0, 5000),
                rng.uniform(5_000, 100_000),
                rng.uniform(0, 100_000),
                rng.randrange(0, 50),
                rng.uniform(0, 0.3),
            )
            expected = plain.clamp_trade_value(*args)
            with_none = RiskManager(
                max_concurrent_lots=40, dd_exposure_start=0.05, dd_exposure_full=0.2, overlay=None
            )
            assert with_none.clamp_trade_value(*args, at=AT) == expected
            advisory = manager(
                SessionOverlay(session=FRIDAY, mode="advisory", pause=True),
                max_concurrent_lots=40,
                dd_exposure_start=0.05,
                dd_exposure_full=0.2,
            )
            assert advisory.clamp_trade_value(*args, at=AT) == expected, "advisory trades the YAML"
            paused = manager(
                enforced(pause=True),
                max_concurrent_lots=40,
                dd_exposure_start=0.05,
                dd_exposure_full=0.2,
            )
            assert paused.clamp_trade_value(*args) == expected, "no `at`: an exempt buy"

    def test_another_session_is_neutral(self):
        paused = manager(enforced(pause=True))
        assert (
            paused.clamp_trade_value(1000, 100_000, 100_000, 0, at=AT + timedelta(days=3)) == 1000
        )


class TestTheLevers:
    def test_never_grows_a_buy(self):
        rng = random.Random(9)
        for _ in range(500):
            overlay = enforced(
                pause=rng.random() < 0.2,
                buy_multiplier=rng.choice([1.0, 0.75, 0.5, 0.25]),
                exposure_ceiling=rng.choice([None, 0.5, 0.3, 0.1]),
            )
            rm = manager(
                overlay, dd_exposure_start=0.05, dd_exposure_full=0.2, dd_exposure_floor_pct=0.1
            )
            proposed = rng.uniform(0, 10_000)
            equity = rng.uniform(10_000, 200_000)
            approved = rm.clamp_trade_value(
                proposed,
                equity,
                rng.uniform(0, equity),
                rng.randrange(0, 30),
                rng.uniform(0, 0.3),
                at=AT,
            )
            assert 0.0 <= approved <= proposed + 1e-9

    def test_a_pause_stops_the_buy(self):
        assert (
            manager(enforced(pause=True)).clamp_trade_value(1000, 100_000, 100_000, 0, at=AT) == 0.0
        )

    def test_the_multiplier(self):
        assert (
            manager(enforced(buy_multiplier=0.5)).clamp_trade_value(
                1000, 100_000, 100_000, 0, at=AT
            )
            == 500.0
        )

    def test_a_blackouts_edges(self):
        window = (AT - timedelta(minutes=15), AT + timedelta(minutes=15))
        rm = manager(enforced(blackouts=(window,)))
        assert rm.clamp_trade_value(1000, 100_000, 100_000, 0, at=window[0]) == 0.0
        assert (
            rm.clamp_trade_value(1000, 100_000, 100_000, 0, at=window[1] - timedelta(seconds=1))
            == 0.0
        )
        assert rm.clamp_trade_value(1000, 100_000, 100_000, 0, at=window[1]) == 1000.0
        assert (
            rm.clamp_trade_value(1000, 100_000, 100_000, 0, at=window[0] - timedelta(seconds=1))
            == 1000.0
        )

    def test_the_ceiling_is_the_min_of_the_ramp_and_the_report(self):
        rm = manager(
            enforced(exposure_ceiling=0.6),
            dd_exposure_start=0.05,
            dd_exposure_full=0.2,
            dd_exposure_floor_pct=0.1,
        )
        # No drawdown: the report's 60% binds -- $60k of $100k, $50k deployed.
        assert rm.exposure_ceiling(0.0, at=AT) == 0.6
        assert rm.clamp_trade_value(20_000, 100_000, 50_000, 0, 0.0, at=AT) == pytest.approx(10_000)
        # Deep drawdown: the ramp's 10% floor binds, tighter than the report's.
        assert rm.exposure_ceiling(0.25, at=AT) == pytest.approx(0.1)
        assert rm.exposure_ceiling(0.0) is None, "without `at`, the YAML's ceiling alone"

    def test_the_lot_cap_comes_first(self):
        rm = manager(enforced(buy_multiplier=0.5), max_concurrent_lots=3)
        assert rm.clamp_trade_value(1000, 100_000, 100_000, 3, at=AT) == 0.0

    def test_the_schedule_swaps_in_place(self):
        rm = manager(None)
        assert rm.clamp_trade_value(1000, 100_000, 100_000, 0, at=AT) == 1000
        rm.set_overlay(OverlaySchedule([enforced(pause=True)]))
        assert rm.clamp_trade_value(1000, 100_000, 100_000, 0, at=AT) == 0.0


class _Strategy:
    def __init__(self, exempt: bool) -> None:
        self.exempt = exempt

    def risk_overlay_exempt(self) -> bool:
        return self.exempt

    def _check_grid_trigger(self, context, last_buy_price, step):
        return True

    def calculate_trade_value(self, context):
        return 1000.0


def context() -> MarketContext:
    return MarketContext(
        timestamp=AT,
        open=50,
        high=50,
        low=50,
        close=50,
        cash=100_000,
        equity=100_000,
        peak_equity=100_000,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
    )


class TestExemptBuys:
    def test_a_reversal_buy_escapes_the_pause(self):
        rm = manager(enforced(pause=True))
        grid = decision_cycle.evaluate_grid_decision(
            _Strategy(False), rm, context(), 51.0, 0.01, 100_000
        )
        reversal = decision_cycle.evaluate_grid_decision(
            _Strategy(True), rm, context(), 51.0, 0.01, 100_000
        )
        assert grid.clamped_trade_value == 0.0
        assert reversal.clamped_trade_value == 1000.0

    def test_not_when_the_deployment_does_not_exempt_reversals(self):
        rm = manager(enforced(pause=True, exempt=()))
        reversal = decision_cycle.evaluate_grid_decision(
            _Strategy(True), rm, context(), 51.0, 0.01, 100_000
        )
        assert reversal.clamped_trade_value == 0.0

    def test_a_strategy_without_the_hook_is_governed(self):
        class Plain(_Strategy):
            risk_overlay_exempt = None

        assert not decision_cycle.overlay_exempt(Plain(False), enforced(pause=True))
