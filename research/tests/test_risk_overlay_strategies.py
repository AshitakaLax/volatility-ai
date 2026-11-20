"""The two strategies that read MarketContext.report_supersedes: with it
empty nothing changes; with `event_boosts` the event-day boosts size at x1;
with `governor` a session the governor would pause is not paused."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from research.strategies.daily_ultimate_sizing import DailyUltimateSizing
from research.strategies.ultimate_sizing import TURBULENT
from research.tests.test_daily_ultimate import UNIT
from research.tests.test_high_frequency_sizing import INITIAL_CASH, ctx, feed, hf


def test_event_boosts_stand_down_only_when_a_report_supersedes_them():
    s = hf(per_lot_pct=0.01, event_day_boost_multiplier=3.0, earnings_day_boost_multiplier=2.0)
    feed(s, [100.0])
    boosted = s.calculate_trade_value(ctx(100.0, is_macro_event_day=True))
    reported = s.calculate_trade_value(
        replace(ctx(100.0, is_macro_event_day=True), report_supersedes=frozenset({"event_boosts"}))
    )
    governor_only = s.calculate_trade_value(
        replace(ctx(100.0, is_macro_event_day=True), report_supersedes=frozenset({"governor"}))
    )
    assert boosted == pytest.approx(INITIAL_CASH * 0.01 * 3.0)
    assert reported == pytest.approx(INITIAL_CASH * 0.01)
    assert governor_only == boosted


def test_a_report_stands_in_for_the_governor_on_its_session():
    day = datetime(2026, 11, 20, 15, 0, tzinfo=UTC)
    plain = DailyUltimateSizing(**UNIT, caution_by_date={day.date(): True})
    superseded = DailyUltimateSizing(**UNIT, caution_by_date={day.date(): True})
    plain.record_tick(replace(ctx(100.0), timestamp=day, time_of_day_flag=30))
    superseded.record_tick(
        replace(
            ctx(100.0),
            timestamp=day,
            time_of_day_flag=30,
            report_supersedes=frozenset({"governor"}),
        )
    )
    assert plain.cautious is True
    assert superseded.cautious is False and superseded.superseded_sessions == 1


def test_ultimate_exempts_its_turbulent_reversal_buys():
    strategy = DailyUltimateSizing(**UNIT)
    assert strategy.risk_overlay_exempt() is False
    strategy.mode = TURBULENT
    assert strategy.risk_overlay_exempt() is True
