"""bridge/notifications.py -- what the bridge tells apps.

No sockets: the hub on its own, with an injected clock. What it pins:
only enabled kinds are sent, ids count within a stream, a reconnecting
app is sent exactly what it missed, and each thing the bridge sees reads
as a notification someone glancing at a phone can act on.
"""

from __future__ import annotations

import pytest

from engine.core.config import FIDELITY_NOTIFICATION_EVENTS, FidelityNotificationsConfig
from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.notifications import (
    DEFAULT_EVENTS,
    EVENT_KINDS,
    Notifications,
)
from fidelity_gateway.bridge.order_reports import OrderReport

# 2026-10-24T14:00:00Z
STARTED = 1_792_850_400.0


def _hub(events=tuple(EVENT_KINDS), **kwargs) -> Notifications:
    clock = kwargs.pop("clock", lambda: STARTED)
    return Notifications(events, clock=clock, stream="s1", **kwargs)


def _report(**overrides) -> OrderReport:
    fields = {
        "id": "r1",
        "conf_num": "2C50H6WV",
        "symbol": "TQQQ",
        "side": "buy",
        "qty": 3.0,
        "limit_price": 70.1,
        "state": "submitted",
        "filled_qty": 0.0,
        "avg_price": 0.0,
        "attempts": 1,
        "placed_at": "2026-10-24T14:00:05.000Z",
        "updated_at": "2026-10-24T14:00:05.000Z",
        "detail": "",
    }
    fields.update(overrides)
    return OrderReport(**fields)


# -- the kinds ----------------------------------------------------------------


def test_the_config_names_the_same_kinds_as_the_bridge():
    """engine/core/config.py validates live.fidelity.bridge.notifications
    without importing this package, so it keeps its own list."""
    assert tuple(EVENT_KINDS) == FIDELITY_NOTIFICATION_EVENTS
    assert FidelityNotificationsConfig().events == DEFAULT_EVENTS


def test_routine_order_updates_are_off_by_default():
    assert "order_update" not in DEFAULT_EVENTS
    assert set(DEFAULT_EVENTS) == set(EVENT_KINDS) - {"order_update"}


def test_an_unknown_kind_is_refused_up_front():
    with pytest.raises(ConfigurationError, match="sold"):
        Notifications(["buy", "sold"])


def test_a_kind_not_enabled_is_not_sent_or_kept():
    hub = _hub(events=["sell"])
    assert hub.publish("buy", "Bought", "x") is None
    assert hub.publish("sell", "Sold", "x") is not None
    assert [n.kind for n in hub.recent()] == ["sell"]


def test_publishing_something_that_is_not_a_kind_is_a_bug():
    with pytest.raises(ValueError):
        _hub().publish("bought", "x", "y")
    with pytest.raises(ValueError):
        _hub().publish("buy", "x", "y", severity="loud")


# -- numbering, catching up, status ---------------------------------------------


def test_ids_count_up_within_the_stream():
    hub = _hub()
    first, second = hub.publish("buy", "a", "b"), hub.publish("sell", "c", "d")
    assert (first.id, second.id) == (1, 2)
    assert first.stream == second.stream == hub.stream == "s1"
    assert first.at == "2026-10-24T14:00:00+00:00"


def test_each_bridge_run_is_its_own_stream():
    assert Notifications().stream != Notifications().stream


def test_a_reconnecting_app_is_sent_only_what_it_missed():
    hub = _hub()
    for n in range(5):
        hub.publish("buy", f"n{n}", "")
    subscription = hub.subscribe(lambda *_: None, since=("s1", 3))
    assert [n.id for n in subscription.backlog] == [4, 5]


def test_an_app_from_another_run_or_none_is_sent_everything_kept():
    hub = _hub(keep=3)
    for n in range(5):
        hub.publish("buy", f"n{n}", "")
    assert [n.id for n in hub.subscribe(lambda *_: None).backlog] == [3, 4, 5]
    other = hub.subscribe(lambda *_: None, since=("an-old-run", 99))
    assert [n.id for n in other.backlog] == [3, 4, 5]


def test_subscribers_hear_notifications_and_status_in_order_until_they_close():
    hub = _hub()
    heard: list = []
    subscription = hub.subscribe(lambda kind, payload: heard.append((kind, payload)))
    hub.publish("buy", "a", "")
    hub.set_status({"engine": {"state": "running"}})
    subscription.close()
    hub.publish("sell", "b", "")
    assert [kind for kind, _ in heard] == ["notification", "status"]
    assert heard[0][1].title == "a"


def test_the_status_is_sent_only_when_it_changes_and_is_handed_to_new_subscribers():
    hub = _hub()
    heard: list = []
    hub.subscribe(lambda kind, payload: heard.append(kind))
    hub.set_status({"engine": None})
    hub.set_status({"engine": None})
    assert heard == ["status"]
    assert hub.subscribe(lambda *_: None).status == {"engine": None}


def test_a_failing_listener_is_logged_and_the_others_still_hear():
    lines: list[str] = []
    hub = _hub(log=lines.append)
    heard: list = []

    def broken(*_):
        raise RuntimeError("boom")

    hub.subscribe(broken)
    hub.subscribe(lambda kind, payload: heard.append(kind))
    assert hub.publish("buy", "a", "") is not None
    assert heard == ["notification"]
    assert any("RuntimeError: boom" in line for line in lines)


# -- the extension, its switch, the engine ----------------------------------------


def test_the_extension_connecting_and_reconnecting():
    hub = _hub()
    first = hub.extension_connected(version="1.4.0", peer="127.0.0.1")
    assert (first.kind, first.title) == ("connected", "Extension connected")
    assert first.body == "Fidelity Bridge 1.4.0 connected from 127.0.0.1."
    again = hub.extension_connected(version=None, peer="127.0.0.1", away_seconds=200)
    assert again.title == "Extension reconnected"
    assert "after 3m 20s away" in again.body
    assert again.data["awaySeconds"] == 200


def test_the_extension_going_away_is_a_warning():
    gone = _hub().extension_disconnected(peer="192.168.1.20")
    assert (gone.kind, gone.severity) == ("disconnected", "warning")
    assert "192.168.1.20" in gone.body


def test_the_trading_switch_both_ways():
    hub = _hub()
    off = hub.trading_switch(allowed=False)
    assert (off.title, off.severity, off.data) == (
        "Trading switched OFF",
        "warning",
        {"trading": False},
    )
    on = hub.trading_switch(allowed=True)
    assert (on.title, on.severity) == ("Trading switched on", "info")


@pytest.mark.parametrize(
    "state,title,severity",
    [
        ("starting", "Engine starting", "info"),
        ("running", "Engine running", "info"),
        ("paused", "Engine paused", "warning"),
        ("halted", "Engine HALTED", "critical"),
        ("stopped", "Engine stopped", "info"),
        ("recovery_required", "Engine needs recovery", "critical"),
        ("rebooting", "Engine rebooting", "info"),
    ],
)
def test_engine_states(state, title, severity):
    status = {"state": state, "detail": "why", "symbol": "TQQQ", "mode": "live"}
    notification = _hub().engine_state(status, previous="running")
    assert (notification.kind, notification.title, notification.severity) == (
        "engine",
        title,
        severity,
    )
    assert notification.body == "TQQQ · live: why"
    assert notification.data["previous"] == "running"


# -- order reports -----------------------------------------------------------------


def test_a_filled_buy_and_a_filled_sell():
    hub = _hub()
    bought = hub.order_report(_report(state="filled", filled_qty=3, avg_price=70.05), None)
    assert (bought.kind, bought.title) == ("buy", "Bought 3 TQQQ")
    assert bought.body == "3 at $70.05 (BUY 3 TQQQ @ $70.10), order 2C50H6WV."
    assert bought.data["confNum"] == "2C50H6WV" and bought.data["state"] == "filled"
    sold = hub.order_report(
        _report(id="r2", side="sell", state="filled", filled_qty=3, avg_price=71.2), None
    )
    assert (sold.kind, sold.title) == ("sell", "Sold 3 TQQQ")


def test_a_partial_fill_is_announced_once_not_at_every_share():
    hub = _hub()
    partial = _report(state="partially_filled", filled_qty=1, avg_price=70.1)
    first = hub.order_report(partial, _report())
    assert first.title == "Buy partly filled: 1 of 3 TQQQ"
    more = _report(state="partially_filled", filled_qty=2, avg_price=70.1)
    assert hub.order_report(more, partial) is None
    done = hub.order_report(_report(state="filled", filled_qty=3, avg_price=70.1), more)
    assert done.title == "Bought 3 TQQQ"


def test_the_routine_middle_of_an_order_is_order_update_and_off_by_default():
    quiet = _hub(events=DEFAULT_EVENTS)
    for state in ("submitted", "working", "cancel_requested", "cancelled", "expired"):
        assert quiet.order_report(_report(state=state), None) is None
    loud = _hub()
    assert loud.order_report(_report(state="submitted"), None).title == "Order accepted"
    assert loud.order_report(_report(state="cancelled"), None).title == "Order cancelled"
    assert loud.order_report(_report(state="working"), None) is None


@pytest.mark.parametrize(
    "state,title,severity",
    [
        ("rejected", "Order rejected", "warning"),
        ("blocked", "Order refused by the extension", "warning"),
        ("unknown", "Order outcome unknown", "critical"),
    ],
)
def test_order_problems(state, title, severity):
    notification = _hub().order_report(_report(state=state, detail="trading is off"), None)
    assert (notification.kind, notification.title, notification.severity) == (
        "order_problem",
        title,
        severity,
    )
    assert "trading is off" in notification.body


def test_an_order_from_before_the_bridge_started_in_the_resent_log_is_history():
    """The first connect of a bridge with no reports file: the extension's
    whole log arrives, and none of it is news."""
    hub = _hub()
    old = _report(state="filled", filled_qty=3, avg_price=70, updated_at="2026-10-23T19:00:00Z")
    assert hub.order_report(old, None, resent=True) is None
    assert hub.order_report(_report(state="filled", updated_at="garbage"), None, True) is None


def test_a_resent_report_that_changed_since_the_bridge_started_is_news():
    hub = _hub()
    fresh = _report(state="filled", filled_qty=3, avg_price=70, updated_at="2026-10-24T14:05:00Z")
    assert hub.order_report(fresh, None, resent=True).title == "Bought 3 TQQQ"


def test_a_resent_report_on_an_order_already_known_is_news_whenever_it_changed():
    """Known from the reports file: the fill happened while the engine was
    down, and that is exactly what the phone should hear."""
    hub = _hub()
    filled = _report(state="filled", filled_qty=3, avg_price=70, updated_at="2026-10-23T19:00:00Z")
    assert hub.order_report(filled, _report(), resent=True).title == "Bought 3 TQQQ"
