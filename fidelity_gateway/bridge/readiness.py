"""
Is the Fidelity connection ready to trade -- and if not, the one thing to fix.

The bridge host (host.py) works this out from what it knows -- whether it
listens, the extension's connection (BridgeServer.connection_report), the
deployment's mode, its last read-only account check -- and writes it into its
status every few seconds. tools/market_hours_supervisor.py starts a session
only on "ready"; the Live page shows the checklist; the extension is told the
verdict. One function, so the three cannot disagree.

Each item is one link in the chain from this server to the account:

  bridge      listening for the extension on its port
  extension   connected, and heard from within HEARD_WITHIN_SECONDS (it pings
              every 20 s; a sleeping browser stops)
  version     not older than the engine expects (a warning: it still trades)
  fidelity    the extension's Fidelity tab is the signed-in site
  trading     "Allow trading" on in the extension, for a deployment that
              places real orders
  account     the last read-only check of the account, since the extension
              last connected

and has a state: "ok", "warn" (works, but look), "fail" (stops a session
starting) or "unknown" (not reported yet; never blocks on its own). The
verdict is ready when nothing fails; otherwise the first failure, with what
to do about it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

HEARD_WITHIN_SECONDS = 60.0

ITEMS = ("bridge", "extension", "version", "fidelity", "trading", "account")

_LABELS = {
    "bridge": "Bridge",
    "extension": "Extension",
    "version": "Extension version",
    "fidelity": "Fidelity tab",
    "trading": "Allow trading",
    "account": "Account check",
}


def _seconds(iso: object) -> float | None:
    if not isinstance(iso, str) or not iso:
        return None
    try:
        return datetime.fromisoformat(iso).timestamp()
    except ValueError:
        return None


def _item(id_: str, state: str, detail: str, fix: str | None = None) -> dict[str, Any]:
    return {"id": id_, "label": _LABELS[id_], "state": state, "detail": detail, "fix": fix}


def _ago(seconds: float) -> str:
    seconds = max(0.0, seconds)
    if seconds < 90:
        return f"{seconds:.0f} s ago"
    if seconds < 90 * 60:
        return f"{seconds / 60:.0f} min ago"
    return f"{seconds / 3600:.1f} h ago"


def _bridge(listening: bool, listen_error: str | None, report: dict) -> dict:
    if listening:
        return _item("bridge", "ok", f"listening on {report.get('url') or 'its port'}")
    return _item(
        "bridge",
        "fail",
        listen_error or "not listening",
        "stop the program holding the bridge's port -- a `cli.py live` or "
        "`python -m fidelity_gateway.bridge serve` started by hand -- and it binds within 30 s",
    )


def _extension(report: dict, now: float) -> dict:
    if report.get("connected"):
        heard = _seconds(report.get("last_heard"))
        if heard is not None and now - heard > HEARD_WITHIN_SECONDS:
            return _item(
                "extension",
                "fail",
                f"connected from {report.get('client')}, but silent since {_ago(now - heard)}",
                "wake the browser's computer: a sleeping browser stops answering",
            )
        return _item(
            "extension",
            "ok",
            f"connected from {report.get('client')}"
            + (f", last heard {_ago(now - heard)}" if heard is not None else ""),
        )
    refused = report.get("last_refused") or None
    disconnected = report.get("last_disconnect") or None
    refused_at = _seconds((refused or {}).get("at"))
    gone_at = _seconds((disconnected or {}).get("at"))
    if refused and (gone_at is None or (refused_at or 0) >= gone_at):
        return _item(
            "extension",
            "fail",
            f"turned away {refused.get('client')} {_ago(now - (refused_at or now))}: "
            f"{refused.get('reason')}",
            "fix what the refusal says, in the extension's settings or this deployment's "
            "live.fidelity.bridge",
        )
    detail = "not connected"
    if gone_at is not None:
        code = (disconnected or {}).get("code")
        detail += f" since {_ago(now - gone_at)}" + (f" (closed with {code})" if code else "")
    return _item(
        "extension",
        "fail",
        detail,
        "open the browser with the Fidelity Bridge extension; its engine address must be this "
        "server's and its key FIDELITY_BRIDGE_API_KEY",
    )


def _version(report: dict) -> dict:
    if not report.get("connected"):
        return _item("version", "unknown", "no extension connected")
    version = report.get("version") or "?"
    advice = report.get("advice")
    if advice:
        return _item("version", "warn", f"{version}: {advice}")
    return _item("version", "ok", version)


def _fidelity(report: dict) -> dict:
    if not report.get("connected"):
        return _item("fidelity", "unknown", "no extension connected")
    tab = report.get("fidelity_tab") or None
    if tab is None:
        return _item("fidelity", "unknown", "the extension has not said where its tab is")
    state = tab.get("state")
    if state == "signed_in":
        return _item("fidelity", "ok", "signed in")
    if state == "signed_out":
        return _item(
            "fidelity",
            "fail",
            "Fidelity signed you out",
            "sign in to Fidelity again in that browser",
        )
    if state == "no_tab":
        return _item(
            "fidelity",
            "fail",
            "no Fidelity tab is open",
            "open Fidelity in that browser and sign in",
        )
    return _item(
        "fidelity",
        "warn",
        "the Fidelity tab is not on the signed-in site; the engine goes to Trader+ itself",
    )


def _trading(report: dict, mode: str) -> dict:
    if mode != "live":
        return _item("trading", "ok", "preview only (dry_run): no orders are placed")
    if not report.get("connected"):
        return _item("trading", "unknown", "no extension connected")
    permissions = report.get("permissions")
    if not isinstance(permissions, dict):
        return _item("trading", "unknown", "the extension has not said")
    if permissions.get("place"):
        return _item("trading", "ok", "on: orders go to Fidelity")
    return _item(
        "trading",
        "fail",
        "off: every order is refused in the browser",
        'turn "Allow trading" on in the extension\'s settings',
    )


def _account(report: dict, check: dict | None) -> dict:
    since = _seconds(report.get("since")) if report.get("connected") else None
    at = _seconds((check or {}).get("at"))
    if check is None or at is None or (since is not None and at < since):
        return _item("account", "unknown", "not checked since the extension connected")
    if check.get("ok"):
        return _item("account", "ok", str(check.get("detail") or "read-only check passed"))
    return _item(
        "account",
        "fail",
        str(check.get("detail") or "the read-only check failed"),
        "check again once the cause is fixed (Check connection on the Live page)",
    )


def readiness(
    *,
    listening: bool,
    report: dict,
    mode: str,
    now: float,
    listen_error: str | None = None,
    check: dict | None = None,
) -> dict[str, Any]:
    """The checklist and its verdict:
    {"ready", "blocking" (the first failing item's id, or None), "summary",
     "fix", "items": [{"id", "label", "state", "detail", "fix"}, ...]}."""
    items = [
        _bridge(listening, listen_error, report),
        _extension(report, now),
        _version(report),
        _fidelity(report),
        _trading(report, mode),
        _account(report, check),
    ]
    failing = next((item for item in items if item["state"] == "fail"), None)
    if failing is None:
        return {
            "ready": True,
            "blocking": None,
            "summary": "ready",
            "fix": None,
            "items": items,
        }
    return {
        "ready": False,
        "blocking": failing["id"],
        "summary": f"{failing['label']}: {failing['detail']}",
        "fix": failing["fix"],
        "items": items,
    }


__all__ = ["HEARD_WITHIN_SECONDS", "ITEMS", "readiness"]
