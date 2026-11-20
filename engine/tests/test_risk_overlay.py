"""The overlay one session may be told (engine/core/risk_overlay.py): it can
only take risk away, NEUTRAL is "no report", and advisory changes nothing."""

from __future__ import annotations

import random
from datetime import UTC, date, datetime

import pytest

from engine.core.risk_overlay import (
    NEUTRAL,
    OverlaySchedule,
    SessionOverlay,
    neutral_for,
    session_step,
    session_target,
)

FRIDAY = date(2026, 11, 20)


class TestBounds:
    @pytest.mark.parametrize(
        "fields",
        [
            {"buy_multiplier": 1.2},
            {"buy_multiplier": -0.1},
            {"exposure_ceiling": 1.5},
            {"step_multiplier": 0.9},
            {"target_multiplier": 0.5},
            {"mode": "yolo"},
            {"supersedes": frozenset({"regime"})},
            {"exempt": ("everything",)},
        ],
    )
    def test_it_cannot_add_risk(self, fields):
        with pytest.raises(ValueError):
            SessionOverlay(**fields)

    def test_neutral_changes_nothing_and_supersedes_nothing(self):
        assert not NEUTRAL.changes_trading
        assert NEUTRAL.supersedes == frozenset()
        assert not neutral_for(FRIDAY).changes_trading


class TestTheStep:
    def test_never_below_the_yaml_and_advisory_is_the_yaml(self):
        rng = random.Random(7)
        for _ in range(200):
            multiplier = 1 + rng.random() * 3
            enforced = SessionOverlay(step_multiplier=multiplier, mode="enforce")
            advisory = SessionOverlay(step_multiplier=multiplier, mode="advisory")
            assert session_step(0.00075, enforced) >= 0.00075
            assert session_step(0.00075, enforced) == pytest.approx(0.00075 * multiplier)
            assert session_step(0.00075, advisory) == 0.00075
        assert session_step(0.00075, None) == 0.00075

    def test_the_target_follows_only_when_set(self):
        assert session_target(0.0045, SessionOverlay(step_multiplier=2, mode="enforce")) == 0.0045
        following = SessionOverlay(step_multiplier=2, target_multiplier=2, mode="enforce")
        assert session_target(0.0045, following) == pytest.approx(0.009)


class TestTightening:
    def test_tightest_is_lever_by_lever(self):
        a = SessionOverlay(buy_multiplier=0.75, step_multiplier=2.0, tier=1)
        b = SessionOverlay(buy_multiplier=0.5, exposure_ceiling=0.5, step_multiplier=1.5, tier=2)
        both = a.tightest(b)
        assert both.buy_multiplier == 0.5
        assert both.exposure_ceiling == 0.5
        assert both.step_multiplier == 2.0
        assert both.tier == 2
        assert both.no_looser_than(a) and both.no_looser_than(b)

    def test_a_looser_one_changes_nothing(self):
        tight = SessionOverlay(pause=True, tier=3)
        loose = SessionOverlay(buy_multiplier=0.75, tier=1)
        both = tight.tightest(loose)
        assert both.pause and both.no_looser_than(tight) and tight.no_looser_than(both)
        assert not loose.no_looser_than(tight)


class TestSchedule:
    def test_an_unnamed_session_is_neutral(self):
        schedule = OverlaySchedule([SessionOverlay(session=FRIDAY, pause=True)])
        assert schedule.get(FRIDAY).pause
        assert schedule.get(date(2026, 11, 23)) is NEUTRAL
        # 15:00 UTC Friday is Friday in New York; 03:00 UTC Saturday is still Friday.
        assert schedule.at(datetime(2026, 11, 21, 3, 0, tzinfo=UTC)).pause

    def test_its_hash_is_its_content(self):
        one = OverlaySchedule([SessionOverlay(session=FRIDAY, pause=True)])
        same = OverlaySchedule({FRIDAY: SessionOverlay(pause=True)})
        other = OverlaySchedule([SessionOverlay(session=FRIDAY, buy_multiplier=0.5)])
        assert one.content_hash() == same.content_hash() != other.content_hash()

    def test_a_round_trip(self):
        overlay = SessionOverlay(
            session=FRIDAY,
            pause=True,
            exposure_ceiling=0.6,
            step_multiplier=2.1,
            blackouts=(
                (
                    datetime(2026, 11, 20, 14, 45, tzinfo=UTC),
                    datetime(2026, 11, 20, 15, 15, tzinfo=UTC),
                ),
            ),
            supersedes=frozenset({"governor"}),
            mode="enforce",
            tier=3,
            reasons=("S 0.98",),
            mapping_id="v1",
        )
        assert SessionOverlay.from_dict(overlay.to_dict()) == overlay
        assert overlay.in_blackout(datetime(2026, 11, 20, 15, 0, tzinfo=UTC))
        assert "no new grid buys" in overlay.describe()
