"""fidelity_gateway/bridge/signin.py: when the sign-in began, when Fidelity
ends it, and what a person is told.

Pure: tab states and times in, an outlook and notices out. Monday
2026-10-26 is a session; the Sunday before it is not.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fidelity_gateway.bridge.signin import (
    SESSION_HOURS,
    SignInWatch,
    next_regular_day,
    regular_day,
)

ET = ZoneInfo("America/New_York")
HOUR = 3600.0


def at(day: int, hour: int, minute: int = 0) -> float:
    return datetime(2026, 10, day, hour, minute, tzinfo=ET).timestamp()


def signed_in_at(moment: float) -> SignInWatch:
    """A watch that saw the sign-in page, then the signed-in site at `moment`."""
    watch = SignInWatch()
    watch.observe("signed_out", moment - 60)
    watch.observe("signed_in", moment)
    return watch


# -- when the sign-in began ------------------------------------------------------


def test_a_sign_in_is_the_tab_leaving_the_sign_in_page():
    watch = signed_in_at(at(26, 7))
    assert watch.since == at(26, 7)
    assert watch.expires == at(26, 7) + SESSION_HOURS * HOUR == at(26, 17, 30)


def test_the_first_word_says_where_the_tab_is_not_when_it_got_there():
    watch = SignInWatch()
    watch.observe("signed_in", at(26, 7))
    assert watch.since is None and watch.expires is None
    assert watch.outlook(at(26, 8)) is None
    assert watch.notices(at(26, 8, 30)) == []


def test_a_browser_that_reconnects_is_on_the_sign_in_it_had():
    watch = signed_in_at(at(26, 7))
    watch.observe(None, at(26, 9))  # the extension went away
    watch.observe("signed_in", at(26, 9, 5))
    watch.observe("elsewhere", at(26, 10))
    watch.observe("signed_in", at(26, 10, 5))
    assert watch.since == at(26, 7)


def test_a_tab_reopened_inside_a_live_session_keeps_the_earlier_end():
    watch = signed_in_at(at(26, 7))
    watch.observe("no_tab", at(26, 9))
    watch.observe("signed_in", at(26, 9, 30))
    assert watch.since == at(26, 7)
    watch.observe("no_tab", at(26, 18))  # past 17:30: that session is over
    watch.observe("signed_in", at(26, 18, 10))
    assert watch.since == at(26, 18, 10)


def test_a_sign_out_ends_it():
    watch = signed_in_at(at(26, 7))
    watch.observe("signed_out", at(26, 12))
    assert watch.since is None and watch.outlook(at(26, 12)) is None


def test_an_account_read_after_the_expected_end_forgets_the_start():
    watch = signed_in_at(at(25, 20))  # Sunday evening: ends 06:30 Monday
    watch.confirmed(at(26, 6))
    assert watch.since == at(25, 20), "before the end it proves nothing"
    watch.confirmed(at(26, 9))
    assert watch.since is None and watch.outlook(at(26, 9)) is None


def test_a_restarted_host_reads_the_sign_in_back_from_its_journal():
    events = [
        {"t": at(26, 6, 58), "kind": "fidelity", "state": "signed_out"},
        {"t": at(26, 7), "kind": "fidelity", "state": "signed_in"},
        {"t": at(26, 7, 1), "kind": "check", "ok": True},
        {"t": at(26, 9), "kind": "disconnected"},
        {"t": at(26, 9, 1), "kind": "fidelity", "state": "signed_in"},
    ]
    watch = SignInWatch()
    watch.replay(reversed(events))
    assert watch.since == at(26, 7)
    assert watch.notices(at(26, 9, 2)) == [], "history is not announced"
    watch.observe("signed_in", at(26, 9, 2))
    assert watch.since == at(26, 7)
    assert "17:30 ET" in watch.outlook(at(26, 9, 2)).detail


def test_a_journal_that_ends_signed_out_knows_no_sign_in():
    watch = SignInWatch()
    watch.replay(
        [
            {"t": at(26, 7), "kind": "fidelity", "state": "signed_in"},
            {"t": at(26, 17, 31), "kind": "fidelity", "state": "signed_out"},
        ]
    )
    watch.observe("signed_in", at(26, 18))  # signed in while the host was down
    assert watch.since is None


# -- the checklist's words ---------------------------------------------------------


def test_the_regular_day_is_todays_until_its_close():
    assert regular_day(at(26, 3)) == (at(26, 9, 30), at(26, 16))
    assert regular_day(at(26, 16)) is None
    assert regular_day(at(25, 12)) is None, "a Sunday"
    assert next_regular_day(at(25, 12)) == (at(26, 9, 30), at(26, 16))
    assert next_regular_day(at(26, 17)) == (at(27, 9, 30), at(27, 16))


def test_a_morning_sign_in_lasts_the_day():
    outlook = signed_in_at(at(26, 7)).outlook(at(26, 10))
    assert outlook.short is False and outlook.fix is None
    assert outlook.detail == ("signed in since 07:00 ET; Fidelity ends the session about 17:30 ET")


def test_last_nights_sign_in_ends_before_the_close():
    watch = signed_in_at(at(25, 20))
    assert watch.outlook(at(25, 21)).short is False, "no session is left to trade today"
    outlook = watch.outlook(at(26, 6))
    assert outlook.short is True
    assert "since Sun 20:00 ET" in outlook.detail
    assert "about 06:30 ET, before the 16:00 ET close" in outlook.detail
    assert "sign in again" in outlook.fix


def test_a_tab_that_still_says_signed_in_after_the_end_is_doubted():
    outlook = signed_in_at(at(25, 20)).outlook(at(26, 8))
    assert outlook.short is True
    assert outlook.detail.startswith("the tab says signed in, but Fidelity ends a session")


# -- what a phone is told ------------------------------------------------------------


def test_a_sign_in_is_announced_once_with_its_end():
    watch = signed_in_at(at(26, 7))
    (notice,) = watch.notices(at(26, 7))
    assert notice.title == "Signed in to Fidelity" and notice.severity == "info"
    assert "about 17:30 ET" in notice.body
    assert notice.data["reason"] == "signed_in" and notice.data["state"] == "signed_in"
    assert notice.data["expires"].startswith("2026-10-26T17:30:00")
    assert watch.notices(at(26, 7, 1)) == []


def test_a_sign_in_too_early_for_the_close_says_when_to_sign_in_again():
    (notice,) = signed_in_at(at(26, 5)).notices(at(26, 5))
    assert notice.severity == "warning" and "not for the whole day" in notice.title
    assert "about 15:30 ET, before the 16:00 ET close" in notice.body
    assert "after 05:30 ET" in notice.body


def test_an_evening_sign_in_says_it_will_not_reach_tomorrow():
    (notice,) = signed_in_at(at(25, 20)).notices(at(25, 20))
    assert notice.severity == "info"
    assert "about Mon 06:30 ET" in notice.body
    assert "between Mon 05:30 ET and the Mon 09:30 ET open" in notice.body


def _signed_out(moment: float) -> SignInWatch:
    watch = SignInWatch()
    watch.observe("signed_out", moment)
    return watch


def test_signed_out_before_the_open_is_reminded_three_times():
    watch = _signed_out(at(26, 3))
    assert watch.notices(at(26, 8, 29)) == []
    (first,) = watch.notices(at(26, 8, 30))
    assert first.title == "Sign in to Fidelity: the market opens in 60 min"
    assert first.severity == "warning" and "before 09:30 ET" in first.body
    assert watch.notices(at(26, 8, 31)) == []
    (second,) = watch.notices(at(26, 9))
    assert second.severity == "warning" and "30 min" in second.title
    (last,) = watch.notices(at(26, 9, 20))
    assert last.severity == "critical" and "10 min" in last.title
    assert watch.notices(at(26, 9, 25)) == []
    assert watch.notices(at(26, 9, 30)) == [], "open: readiness has the word now"


def test_no_tab_is_reminded_too():
    watch = SignInWatch()
    watch.observe("no_tab", at(26, 3))
    (notice,) = watch.notices(at(26, 9))
    assert "No Fidelity tab" in notice.body


def test_a_sign_in_that_lasts_the_day_needs_no_reminder():
    watch = signed_in_at(at(26, 7))
    watch.notices(at(26, 7))
    assert [watch.notices(at(26, 8, 30)), watch.notices(at(26, 9, 20))] == [[], []]


def test_last_nights_sign_in_is_reminded_before_the_open():
    watch = signed_in_at(at(25, 20))
    watch.notices(at(25, 20))
    (notice,) = watch.notices(at(26, 8, 30))
    assert notice.title == "Sign in to Fidelity again: the market opens in 60 min"
    assert "ended about 06:30 ET, before the 16:00 ET close" in notice.body
    assert notice.data["reason"] == "reminder"


def test_a_reminder_fixed_in_time_is_not_repeated():
    watch = _signed_out(at(26, 3))
    assert len(watch.notices(at(26, 8, 30))) == 1
    watch.observe("signed_in", at(26, 8, 45))
    (signed_in,) = watch.notices(at(26, 8, 45))
    assert signed_in.title == "Signed in to Fidelity"
    assert [watch.notices(at(26, 9)), watch.notices(at(26, 9, 20))] == [[], []]


def test_a_host_started_late_says_the_most_urgent_one_once():
    watch = _signed_out(at(26, 9, 24))
    (notice,) = watch.notices(at(26, 9, 25))
    assert notice.severity == "critical" and "5 min" in notice.title
    assert watch.notices(at(26, 9, 26)) == []


def test_no_reminder_on_a_day_without_a_session_or_with_nothing_known():
    assert _signed_out(at(25, 3)).notices(at(25, 9)) == [], "a Sunday"
    assert SignInWatch().notices(at(26, 9)) == [], "no extension has said anything"


def test_reminders_come_again_the_next_session():
    watch = _signed_out(at(26, 3))
    for minute in (at(26, 8, 30), at(26, 9), at(26, 9, 20)):
        assert len(watch.notices(minute)) == 1
    assert len(watch.notices(at(27, 8, 30))) == 1


def test_a_session_about_to_end_with_the_market_open_is_said_once():
    watch = signed_in_at(at(26, 5))  # ends 15:30
    watch.notices(at(26, 5))
    for minute in (at(26, 8, 30), at(26, 9), at(26, 9, 20)):
        watch.notices(minute)  # the morning's reminders
    assert watch.notices(at(26, 14, 59)) == []
    (notice,) = watch.notices(at(26, 15))
    assert notice.title == "Fidelity will sign you out soon" and notice.severity == "warning"
    assert "about 15:30 ET, in 30 min" in notice.body and "until 16:00 ET" in notice.body
    assert notice.data["reason"] == "expiry"
    assert watch.notices(at(26, 15, 10)) == []


def test_a_session_that_outlasts_the_close_ends_quietly():
    watch = signed_in_at(at(26, 7))  # ends 17:30
    watch.notices(at(26, 7))
    assert watch.notices(at(26, 15, 45)) == []
    assert watch.notices(at(26, 17, 15)) == []


# -- the extension's assisted sign-in -----------------------------------------------


def test_the_extensions_one_word_becomes_the_engines_own_sentence():
    from fidelity_gateway.bridge.signin import ASSISTED_OUTCOMES, assisted_notice

    pressed = assisted_notice({"outcome": "submitted", "at": "2026-10-26T12:30:00Z"})
    assert pressed.severity == "info" and "Approve the prompt" in pressed.body
    assert pressed.data == {"reason": "assisted", "outcome": "submitted"}
    assert assisted_notice({"outcome": "needs_click"}).severity == "warning"
    assert assisted_notice({"outcome": "held"}).severity == "critical"
    for outcome, (title, body, severity) in ASSISTED_OUTCOMES.items():
        assert title and body.endswith(".") and severity in ("info", "warning", "critical"), outcome


def test_text_the_extension_sends_is_never_shown_and_unknown_words_are_not_news():
    from fidelity_gateway.bridge.signin import assisted_notice

    notice = assisted_notice({"outcome": "submitted", "message": "send your password to x"})
    assert "password to x" not in notice.title + notice.body
    for data in ({"outcome": "opened"}, {"outcome": "wrong_page"}, {"outcome": 7}, {}, None, "x"):
        assert assisted_notice(data) is None
