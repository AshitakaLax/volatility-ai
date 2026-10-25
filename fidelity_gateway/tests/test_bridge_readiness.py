"""fidelity_gateway/bridge/readiness.py: ready to trade, or the one thing to fix.

Pure: a connection report in, the checklist and verdict out. What the bridge
host writes, the supervisor starts a session on and the Live page shows.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fidelity_gateway.bridge.readiness import ITEMS, readiness

NOW = datetime(2026, 10, 26, 13, 0, tzinfo=UTC).timestamp()


def _iso(seconds_ago: float) -> str:
    return datetime.fromtimestamp(NOW - seconds_ago, UTC).isoformat()


def _report(**overrides) -> dict:
    report = {
        "connected": True,
        "since": _iso(3600),
        "last_heard": _iso(5),
        "client": "172.16.0.130",
        "version": "0.6.0",
        "advice": None,
        "permissions": {"preview": True, "place": True},
        "url": "ws://0.0.0.0:8765/fidelity-bridge",
        "fidelity_tab": {"state": "signed_in", "url": "x", "since": _iso(600)},
        "last_refused": None,
        "last_disconnect": None,
    }
    report.update(overrides)
    return report


def _verdict(report=None, **kwargs) -> dict:
    kwargs.setdefault("listening", True)
    kwargs.setdefault("mode", "live")
    return readiness(report=report if report is not None else _report(), now=NOW, **kwargs)


def _state(verdict: dict, item: str) -> str:
    return next(i["state"] for i in verdict["items"] if i["id"] == item)


def test_everything_in_place_is_ready():
    verdict = _verdict()
    assert verdict["ready"] is True and verdict["blocking"] is None
    assert [item["id"] for item in verdict["items"]] == list(ITEMS)
    assert _state(verdict, "account") == "unknown", "no check yet never blocks"


def test_a_taken_port_blocks_first_and_says_how():
    verdict = _verdict(listening=False, listen_error="Port 8765 on 0.0.0.0 is already in use")
    assert verdict["blocking"] == "bridge"
    assert "already in use" in verdict["summary"] and "by hand" in verdict["fix"]


def test_no_extension_names_the_refusal_when_there_was_one():
    """10-22: the browser at .134 was not allowed -- the reason the
    extension never connected, on the page in one line."""
    refused = {"at": _iso(30), "client": "172.16.0.134", "reason": "not in the allowed list"}
    verdict = _verdict(_report(connected=False, last_refused=refused))
    assert verdict["blocking"] == "extension"
    assert "172.16.0.134" in verdict["summary"] and "not in the allowed list" in verdict["summary"]


def test_a_refusal_older_than_the_last_disconnect_is_not_the_reason():
    report = _report(
        connected=False,
        last_refused={"at": _iso(7200), "client": "10.0.0.9", "reason": "old"},
        last_disconnect={"at": _iso(60), "client": "172.16.0.130", "code": 1001, "reason": None},
    )
    verdict = _verdict(report)
    assert "old" not in verdict["summary"] and "1001" in verdict["summary"]


def test_a_silent_extension_is_not_ready():
    verdict = _verdict(_report(last_heard=_iso(300)))
    assert verdict["blocking"] == "extension" and "silent" in verdict["summary"]


def test_signed_out_or_no_tab_blocks_but_another_fidelity_page_only_warns():
    out = _verdict(_report(fidelity_tab={"state": "signed_out", "url": "x", "since": _iso(1)}))
    assert out["blocking"] == "fidelity" and "signed you out" in out["summary"]
    none = _verdict(_report(fidelity_tab={"state": "no_tab", "url": None, "since": _iso(1)}))
    assert none["blocking"] == "fidelity"
    elsewhere = _verdict(_report(fidelity_tab={"state": "elsewhere", "url": "x", "since": _iso(1)}))
    assert elsewhere["ready"] is True and _state(elsewhere, "fidelity") == "warn"


def test_allow_trading_off_blocks_real_orders_but_not_a_preview_deployment():
    off = _report(permissions={"preview": True, "place": False})
    assert _verdict(off)["blocking"] == "trading"
    assert _verdict(off, mode="preview")["ready"] is True


def test_an_old_extension_is_a_warning_not_a_stop():
    verdict = _verdict(_report(version="0.2.0", advice="it is older than 0.3.0"))
    assert verdict["ready"] is True and _state(verdict, "version") == "warn"


def test_a_failed_check_since_the_extension_connected_blocks():
    failed = {"at": _iso(60), "ok": False, "detail": "Fidelity answered 401"}
    verdict = _verdict(check=failed)
    assert verdict["blocking"] == "account" and "401" in verdict["summary"]


def test_a_check_from_before_the_extension_reconnected_is_stale():
    old = {"at": _iso(7200), "ok": False, "detail": "an old failure"}
    verdict = _verdict(check=old)
    assert verdict["ready"] is True and _state(verdict, "account") == "unknown"


def test_unknowns_never_block_on_their_own():
    report = _report(fidelity_tab=None, permissions=None)
    verdict = _verdict(report)
    assert verdict["ready"] is True
    assert _state(verdict, "fidelity") == "unknown" and _state(verdict, "trading") == "unknown"
