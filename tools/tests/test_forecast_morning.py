"""The morning risk report (tools/forecast_morning.py) through the real
routers: it keeps a report where the Live page's Check does and applies it
where the page's Apply does, to paper traders that are up and never to real
money; a retry finishes only what did not finish; and the schedule runs on
session mornings, retrying until the last try.

The generator is faked -- research/tests/test_forecast_generator.py covers
it -- so the report here is a real one (tests/fixtures/risk_reports/),
restamped as made that morning.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from engine.core.persistence import LedgerStore
from engine.core.trading_calendar import EASTERN
from engine.trading.control_inbox import ControlInbox
from engine.trading.operator_control import SupervisorControl
from research.forecast_generator import generator
from research.risk_overlay import inputs as inputs_module
from research.risk_overlay.baselines import Baseline
from research.risk_overlay.live import handlers
from server import live, live_control
from server.app import app
from tools import forecast_morning as fm

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/risk_reports/tqqq_2026-11-20.json"
SESSION = date(2026, 11, 20)  # a Friday
MORNING = datetime(2026, 11, 20, 12, 45, tzinfo=UTC)  # 07:45 ET


def fixture_report(as_of: str = "2026-11-20T12:44:00Z") -> dict:
    report = json.loads(FIXTURE.read_text(encoding="utf-8"))
    report["as_of"] = as_of
    return report


class FakeMake:
    """generate() as the tool calls it: counted, and failing on demand."""

    def __init__(self, report: dict | None = None, fail: Exception | None = None) -> None:
        self.report = report or fixture_report()
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def __call__(self, symbol, engine, *, now, progress):
        self.calls.append((symbol, engine))
        progress("Simulating 2,000 scenarios")
        if self.fail is not None:
            raise self.fail
        return generator.Generated(
            report=self.report,
            audit={},
            snapshot={"symbol": symbol, "target_session": "2026-11-20", "prev_close": 48.99},
            sources=[{"name": "Yahoo Finance chart API"}],
            diagnostics={"engine": engine},
        )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def deployments(tmp_path, monkeypatch):
    """`paper` takes reports and is up; `idle` takes them and is down;
    `bare` is up with no overlay; `money` is real money, up, taking them."""

    def config(path: str, name: str, *, overlay: bool) -> str:
        data = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
        if overlay:
            data.setdefault("risk", {})["overlay"] = {"mode": "advisory"}
            data["live"].setdefault("control", {})["risk_reports"] = True
        else:
            (data.get("risk") or {}).pop("overlay", None)
            (data["live"].get("control") or {}).pop("risk_reports", None)
        out = tmp_path / f"{name}.yaml"
        out.write_text(yaml.safe_dump(data), encoding="utf-8")
        return str(out)

    entries = {}
    for deployment_id, path, overlay, up in (
        ("paper", "config/paper_aggressive.yaml", True, True),
        ("idle", "config/paper_aggressive.yaml", True, False),
        ("bare", "config/paper_aggressive.yaml", False, True),
        ("money", "config/production.yaml", True, True),
    ):
        ledger = tmp_path / f"{deployment_id}.db"
        LedgerStore(str(ledger)).close()
        control = tmp_path / f"control-{deployment_id}"
        if up:
            # On the real clock: the deployment list judges a trader's
            # report by it (server/live.py).
            ControlInbox(control).write_status(state="waiting_for_open", heartbeat_seconds=15.0)
        entries[deployment_id] = {
            "label": deployment_id,
            "config": config(path, deployment_id, overlay=overlay),
            "state_db": str(ledger),
            "control_dir": str(control),
        }
    registry = tmp_path / "deployments.yaml"
    registry.write_text(yaml.safe_dump({"deployments": entries}), encoding="utf-8")
    monkeypatch.setenv("VAI_DEPLOYMENTS", str(registry))
    monkeypatch.setenv("VAI_EXTERNAL_DIR", str(tmp_path / "no-outside-data"))
    monkeypatch.setenv("VAI_FORECAST_DB", str(tmp_path / "forecasts" / "risk_reports.db"))
    monkeypatch.setattr(live_control, "_now", lambda: MORNING)
    monkeypatch.setattr(live, "_now", lambda: MORNING)
    monkeypatch.setattr(
        inputs_module, "baseline_for", lambda symbol: Baseline(symbol, 4.2, {"next_month": -30.0})
    )
    return entries


def through(client, fail=None):
    """The tool's transport, onto the app itself. `fail(method, path)` may
    answer for the server instead (a status and a body), once each time it
    returns one."""

    def send(method, path, body):
        if fail is not None:
            answer = fail(method, path)
            if answer is not None:
                return answer
        response = client.request(method, path, json=body)
        return response.status_code, response.json() if response.content else None

    return fm.Web(send)


def morning_run(web, make, *, morning=None, lines=None, **kwargs):
    morning = morning or fm.Morning(SESSION)
    finished = fm.run_fund(
        morning,
        "TQQQ",
        web,
        engine="chronos",
        now=MORNING,
        make=make,
        report=(lines.append if lines is not None else lambda _line: None),
        **kwargs,
    )
    return finished, morning


def queued(entry) -> list[dict]:
    return ControlInbox(entry["control_dir"], clock=MORNING.timestamp).history(limit=50)


def kept(client) -> list[dict]:
    return client.get("/api/live/risk-forecasts?symbol=TQQQ").json()["sessions"]


# --------------------------------------------------------------------
# One morning


def test_a_morning_makes_keeps_and_applies_to_the_paper_trader_that_is_up(client, deployments):
    make, lines = FakeMake(), []
    finished, morning = morning_run(through(client), make, lines=lines)
    assert finished and make.calls == [("TQQQ", "chronos")]
    (row,) = kept(client)
    assert row["session"] == "2026-11-20" and row["sha256"] == morning.fund("TQQQ").sha256
    (command,) = queued(deployments["paper"])
    assert command["type"] == "apply_risk_report" and command["operator"] == fm.OPERATOR
    assert command["timing"] == "now" and "This morning's risk report" in command["reason"]
    assert any("applied to paper" in line for line in lines), lines


def test_real_money_traders_that_are_down_and_bare_configs_get_nothing(client, deployments):
    morning_run(through(client), FakeMake())
    for name in ("money", "idle", "bare"):
        assert queued(deployments[name]) == [], name


def test_the_trader_applies_it_before_the_open(client, deployments):
    morning_run(through(client), FakeMake())
    entry = deployments["paper"]
    from engine.core.config import BacktestConfig

    config = BacktestConfig.from_yaml(entry["config"])
    inbox = ControlInbox(entry["control_dir"], clock=MORNING.timestamp)
    extra = handlers(config, entry["control_dir"], inbox=inbox, clock=MORNING.timestamp)
    control = SupervisorControl(
        inbox, state_db=entry["state_db"], extra=extra, clock=MORNING.timestamp
    )
    (result,) = control.poll()
    assert result["status"] == "applied", result
    shown = client.get("/api/live/deployments/paper/risk-reports").json()
    (entry,) = shown["sessions"]
    assert entry["session"] == "2026-11-20" and entry["operator"] == fm.OPERATOR
    assert shown["next"]["session"] == "2026-11-20"


def test_it_travels_in_the_pages_form_so_every_copy_is_one_report(client, deployments):
    report = fixture_report()
    report["horizons"]["tomorrow"]["summary"]["mean_pct"] = -1.0  # a float the page writes as -1
    _, morning = morning_run(through(client), FakeMake(report))
    (row,) = kept(client)
    (command,) = queued(deployments["paper"])
    sent = command["args"]["report"]
    assert sent["horizons"]["tomorrow"]["summary"]["mean_pct"] == -1
    assert isinstance(sent["horizons"]["tomorrow"]["summary"]["mean_pct"], int)
    assert row["sha256"] == morning.fund("TQQQ").sha256


def test_what_it_read_is_kept_beside_the_report(client, deployments):
    _, morning = morning_run(through(client), FakeMake())
    sha = morning.fund("TQQQ").sha256
    found = client.get(f"/api/live/risk-forecasts/report?sha256={sha}").json()
    assert found["inputs"]["snapshot"]["prev_close"] == 48.99
    assert found["inputs"]["diagnostics"] == {"engine": "chronos"}
    assert found["receipts"][0]["operator"] == fm.OPERATOR


def test_inputs_the_server_refuses_do_not_cost_the_report(client, deployments):
    class Elsewhere(FakeMake):
        def __call__(self, symbol, engine, *, now, progress):
            made = super().__call__(symbol, engine, now=now, progress=progress)
            return generator.Generated(
                report=made.report,
                audit={},
                snapshot={"symbol": symbol, "target_session": "2026-11-23"},
                sources=[],
            )

    lines: list[str] = []
    finished, morning = morning_run(through(client), Elsewhere(), lines=lines)
    assert finished and len(kept(client)) == 1
    assert any("inputs were refused" in line for line in lines), lines
    sha = morning.fund("TQQQ").sha256
    assert client.get(f"/api/live/risk-forecasts/report?sha256={sha}").json()["inputs"] is None
    assert len(queued(deployments["paper"])) == 1, "and it is still applied"


def test_a_dry_run_keeps_and_applies_nothing(client, deployments):
    finished, _ = morning_run(through(client), FakeMake(), dry_run=True)
    assert finished and kept(client) == [] and queued(deployments["paper"]) == []


def test_keep_only_applies_nowhere(client, deployments):
    finished, _ = morning_run(through(client), FakeMake(), apply=False)
    assert finished and len(kept(client)) == 1 and queued(deployments["paper"]) == []


# --------------------------------------------------------------------
# Trying again


def test_a_refused_run_is_tried_again_and_nothing_is_kept(client, deployments):
    make = FakeMake(fail=generator.ForecastRefused("the source has not posted it yet"))
    finished, morning = morning_run(through(client), make)
    assert not finished and kept(client) == []
    make.fail = None
    finished, _ = morning_run(through(client), make, morning=morning)
    assert finished and len(make.calls) == 2 and len(kept(client)) == 1


def test_a_keep_that_failed_is_finished_later_without_a_second_report(client, deployments):
    down = {"left": 1}

    def fail(method, path):
        if method == "POST" and path == "/api/live/risk-forecasts" and down["left"]:
            down["left"] -= 1
            return 503, {"detail": "starting"}
        return None

    make = FakeMake()
    finished, morning = morning_run(through(client, fail), make)
    assert not finished and kept(client) == [] and queued(deployments["paper"]) == []
    finished, _ = morning_run(through(client, fail), make, morning=morning)
    assert finished and len(make.calls) == 1, "a made report is never made again"
    assert len(kept(client)) == 1 and len(queued(deployments["paper"])) == 1


def test_an_apply_that_failed_is_sent_again_and_only_there(client, deployments):
    down = {"left": 1}

    def fail(method, path):
        if path.endswith("/commands") and down["left"]:
            down["left"] -= 1
            return 502, "bad gateway"
        return None

    finished, morning = morning_run(through(client, fail), FakeMake())
    assert not finished and queued(deployments["paper"]) == []
    finished, _ = morning_run(through(client, fail), FakeMake(), morning=morning)
    assert finished and len(queued(deployments["paper"])) == 1


def test_the_same_report_is_never_queued_twice(client, deployments):
    """A fresh morning sending the same report (a restart with the morning's
    check turned off) reaches the server's idempotency key."""
    for _ in range(2):
        morning_run(through(client), FakeMake(), skip_made=False)
    assert len(queued(deployments["paper"])) == 1


def test_a_refusal_from_the_server_is_not_asked_again(client, deployments):
    calls = {"commands": 0}

    def fail(method, path):
        if path.endswith("/commands"):
            calls["commands"] += 1
            return 409, {"detail": "paper takes no risk reports"}
        return None

    finished, morning = morning_run(through(client, fail), FakeMake())
    assert finished and calls["commands"] == 1
    assert morning_run(through(client, fail), FakeMake(), morning=morning)[0]
    assert calls["commands"] == 1


# --------------------------------------------------------------------
# What is already there


def test_a_report_made_this_morning_is_left_as_it_is(client, deployments):
    client.post(
        "/api/live/risk-forecasts",
        json={"report": fixture_report("2026-11-20T12:10:00Z"), "operator": "owner"},
    )
    make, lines = FakeMake(fixture_report("2026-11-20T12:44:00Z")), []
    finished, _ = morning_run(through(client), make, lines=lines)
    assert finished and make.calls == [] and queued(deployments["paper"]) == []
    assert any("already made this morning" in line for line in lines), lines


def test_an_evening_report_does_not_stop_the_morning_one(client, deployments):
    client.post(
        "/api/live/risk-forecasts",
        json={"report": fixture_report("2026-11-20T02:38:15Z"), "operator": "owner"},
    )
    make = FakeMake()
    finished, _ = morning_run(through(client), make)
    assert finished and len(make.calls) == 1 and len(queued(deployments["paper"])) == 1


def test_a_report_for_another_session_is_not_kept(client, deployments):
    finished, _ = morning_run(through(client), FakeMake(), morning=fm.Morning(date(2026, 11, 23)))
    assert finished and kept(client) == [] and queued(deployments["paper"]) == []


def test_made_this_morning_reads_eastern_time():
    rows = [{"session": "2026-11-20", "as_of": "2026-11-20T04:30:00Z"}]  # 23:30 ET the 19th
    assert fm.made_this_morning(rows, SESSION) is None
    rows = [{"session": "2026-11-20", "as_of": "2026-11-20T09:05:00+00:00"}]  # 04:05 ET
    assert fm.made_this_morning(rows, SESSION) == rows[0]
    rows = [{"session": "2026-11-20", "as_of": "2026-11-20T14:45:00Z"}]  # inside the session
    assert fm.made_this_morning(rows, SESSION) is None


# --------------------------------------------------------------------
# The schedule

AT = [clock_time(7, 45)]


def et(year, month, day, hour, minute) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=EASTERN)


def test_mornings_are_session_days_only():
    # Wednesday 25 Nov after the run: Thanksgiving is skipped.
    assert fm.next_morning(et(2026, 11, 25, 8, 0), AT) == et(2026, 11, 27, 7, 45)
    # Friday after the run: the weekend is skipped.
    assert fm.next_morning(et(2026, 11, 27, 8, 0), AT) == et(2026, 11, 30, 7, 45)
    assert fm.next_morning(et(2026, 11, 30, 7, 0), AT) == et(2026, 11, 30, 7, 45)


class Clock:
    def __init__(self, start: datetime) -> None:
        self.at = start.astimezone(UTC)

    def now(self) -> datetime:
        return self.at

    def sleep(self, seconds: float) -> None:
        self.at += timedelta(seconds=seconds)


def test_an_unfinished_morning_is_tried_every_ten_minutes_until_the_last_try():
    clock, tries = Clock(et(2026, 11, 25, 6, 0)), []

    def attempt(morning):
        tries.append((morning.session, clock.now().astimezone(EASTERN).strftime("%H:%M")))
        clock.sleep(30)  # a run takes a while
        return False

    fm.run_daily(AT, attempt, now=clock.now, sleep=clock.sleep, report=lambda _: None, rounds=11)
    wednesday = [t for d, t in tries if d == date(2026, 11, 25)]
    assert wednesday == [
        "07:45",
        "07:55",
        "08:05",
        "08:15",
        "08:25",
        "08:35",
        "08:45",
        "08:55",
        "09:05",
        "09:15",
    ]
    assert tries[-1] == (date(2026, 11, 27), "07:45"), "then the next session's morning"


def test_a_finished_morning_waits_for_the_next_session():
    clock, tries = Clock(et(2026, 11, 25, 6, 0)), []

    def attempt(morning):
        tries.append(clock.now().astimezone(EASTERN))
        return True

    fm.run_daily(AT, attempt, now=clock.now, sleep=clock.sleep, report=lambda _: None, rounds=2)
    assert tries == [et(2026, 11, 25, 7, 45), et(2026, 11, 27, 7, 45)]


def test_a_start_inside_the_window_runs_at_once_and_outside_it_waits():
    for start, first in (
        (et(2026, 11, 27, 8, 20), et(2026, 11, 27, 8, 20)),  # a deploy mid-morning
        (et(2026, 11, 27, 9, 20), et(2026, 11, 30, 7, 45)),  # past the last try
        (et(2026, 11, 26, 8, 0), et(2026, 11, 27, 7, 45)),  # Thanksgiving
    ):
        clock, tries = Clock(start), []

        def attempt(morning, clock=clock, tries=tries):
            tries.append(clock.now().astimezone(EASTERN))
            return True

        fm.run_daily(AT, attempt, now=clock.now, sleep=clock.sleep, report=lambda _: None, rounds=1)
        assert tries == [first], start


def test_each_try_carries_the_mornings_work():
    clock, seen = Clock(et(2026, 11, 27, 7, 0)), []

    def attempt(morning):
        seen.append(morning)
        return len(seen) > 1

    fm.run_daily(AT, attempt, now=clock.now, sleep=clock.sleep, report=lambda _: None, rounds=2)
    assert seen[0] is seen[1]


def test_a_run_time_at_or_after_the_last_try_is_refused():
    with pytest.raises(SystemExit):
        fm.main(["--daily", "09:30"])
