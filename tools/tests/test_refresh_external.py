"""tools/refresh_external.py -- keeping the outside series current -- against
a fake fetch and temp directories. No network; no sleeping."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time

import pandas as pd
import pytest

from engine.core.trading_calendar import EASTERN, sessions_between
from research.ml import sources
from research.strategies.risk_governor import CORE_SIGNALS, SIGNALS
from tools import refresh_external as R

# 20:45 Eastern on a Thursday: the day's closes are stamped and in the past.
NOW = datetime(2026, 10, 22, 20, 45, tzinfo=EASTERN).astimezone(UTC)
SESSIONS = sessions_between(date(2025, 12, 31), date(2026, 10, 22))


def source(key: str) -> sources.Source:
    return next(s for s in sources.registry() if sources.manifest_key(s) == key)


def frame(values, sessions=SESSIONS, lag: timedelta = timedelta(0)) -> pd.DataFrame:
    stamps = pd.DatetimeIndex(pd.to_datetime(sessions)).tz_localize("UTC") + lag
    stamps += pd.Timedelta(hours=21)
    return pd.DataFrame({"timestamp": stamps, "close": list(values)})


def level(key: str, n: int = len(SESSIONS)) -> pd.DataFrame:
    """A series whose values depend on its key, `n` sessions long."""
    base = 10.0 + sum(map(ord, key)) % 50
    return frame([base + 0.01 * i for i in range(n)], SESSIONS[:n], source(key).lag)


class Feed:
    """sources.fetch over a set of series; `down` keys raise."""

    def __init__(self, keys, n: int = len(SESSIONS), down=()):
        self.keys, self.n, self.down, self.calls = set(keys), n, set(down), []

    def __call__(self, src: sources.Source) -> pd.DataFrame:
        key = sources.manifest_key(src)
        self.calls.append(key)
        if key in self.down:
            raise sources.SourceUnavailable(f"{key}: HTTP 503")
        return level(key, self.n)


CORE_KEYS = sorted({key for name in CORE_SIGNALS for key in SIGNALS[name].inputs})
WANTED = [source(key) for key in (*CORE_KEYS, "fred_DGS10")]
N = len(WANTED)
quiet: list[str] = []


# -- one series ------------------------------------------------------------------


def test_a_fetch_is_judged_against_what_is_stored():
    full = level("cboe_VXN")
    stored = R.as_csv(full.iloc[:-1])
    assert R.judge(None, full)[0] == "new"
    assert R.judge(R.as_csv(full), full)[0] == "unchanged"
    assert R.judge(stored, full) == ("updated", f"{len(full):,} rows to 2026-10-22")
    # Half the history: the stored file stays.
    status, detail = R.judge(R.as_csv(full), full.iloc[: len(full) // 2])
    assert status == "kept" and "rows against" in detail
    # Yesterday's file again after today's was stored.
    status, detail = R.judge(R.as_csv(full), full.iloc[:-1])
    assert status == "kept" and "stored to 2026-10-22" in detail
    # A revision of an old value, same span: written.
    revised = full.copy()
    revised.loc[3, "close"] += 1.0
    assert R.judge(R.as_csv(full), revised)[0] == "updated"


def test_a_bar_still_forming_is_not_stored_but_a_lagged_stamp_is():
    midday = datetime(2026, 10, 22, 12, 0, tzinfo=EASTERN).astimezone(UTC)
    same_day = R.settled(source("yahoo_QQQ"), level("yahoo_QQQ"), midday)
    assert len(same_day) == len(SESSIONS) - 1  # today's 21:00 stamp is still ahead
    assert len(R.settled(source("yahoo_QQQ"), level("yahoo_QQQ"), NOW)) == len(SESSIONS)
    lagged = R.settled(source("ofr_FSI"), level("ofr_FSI"), midday)
    assert len(lagged) == len(SESSIONS)  # stamped days ahead by design


def test_series_are_written_whole_with_their_manifest(tmp_path):
    feed = Feed(CORE_KEYS)
    outcomes = R.refresh_series(WANTED, tmp_path, fetch=feed, now=NOW, report=quiet.append)
    assert {o.key: o.status for o in outcomes} == dict.fromkeys(
        [*CORE_KEYS, "fred_DGS10"], "new"
    )
    stored = pd.read_csv(tmp_path / "cboe_VXN.csv")
    assert list(stored.columns) == ["timestamp", "close"] and len(stored) == len(SESSIONS)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert set(manifest) == {*CORE_KEYS, "fred_DGS10"}
    assert manifest["ofr_FSI"]["lag_days"] == 4.0 and manifest["ofr_FSI"]["file"] == "ofr_FSI.csv"
    assert not list(tmp_path.glob(".*.partial"))
    again = R.refresh_series(WANTED, tmp_path, fetch=feed, now=NOW, report=quiet.append)
    assert {o.status for o in again} == {"unchanged"}


def test_a_source_that_is_down_is_one_failure_and_its_file_stays(tmp_path):
    R.refresh_series(WANTED, tmp_path, fetch=Feed(CORE_KEYS, n=100), now=NOW, report=quiet.append)
    before = (tmp_path / "cboe_VXN.csv").read_text()
    lines: list[str] = []
    outcomes = R.refresh_series(
        WANTED, tmp_path, fetch=Feed(CORE_KEYS, down={"cboe_VXN"}), now=NOW, report=lines.append
    )
    by = {o.key: o.status for o in outcomes}
    assert by["cboe_VXN"] == "failed" and by["yahoo_QQQ"] == "updated"
    assert (tmp_path / "cboe_VXN.csv").read_text() == before
    assert any("cboe_VXN" in line and "failed" in line and "503" in line for line in lines)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["cboe_VXN"]["rows"] == 100  # the row of the file that is there
    assert manifest["yahoo_QQQ"]["rows"] == len(SESSIONS)


def test_a_truncated_answer_does_not_replace_the_stored_series(tmp_path):
    R.refresh_series(WANTED, tmp_path, fetch=Feed(CORE_KEYS), now=NOW, report=quiet.append)
    before = (tmp_path / "ofr_FSI.csv").read_text()
    outcomes = R.refresh_series(
        WANTED, tmp_path, fetch=Feed(CORE_KEYS, n=20), now=NOW, report=quiet.append
    )
    assert {o.status for o in outcomes} == {"kept"}
    assert (tmp_path / "ofr_FSI.csv").read_text() == before


def test_a_dry_run_writes_nothing(tmp_path):
    target = tmp_path / "not-made"
    lines: list[str] = []
    outcomes = R.refresh_series(
        WANTED, target, fetch=Feed(CORE_KEYS), dry_run=True, now=NOW, report=lines.append
    )
    assert {o.status for o in outcomes} == {"new"} and not target.exists()
    assert all("would be new" in line for line in lines)


# -- a run -----------------------------------------------------------------------


def _run(tmp_path, feed, **over):
    lines: list[str] = []
    laked: list = []

    def lake(root, directory):
        laked.append((root, directory))
        return "lake: written"

    ok = R.run_once(
        WANTED,
        tmp_path / "external",
        tmp_path / "warehouse",
        now=NOW,
        fetch=feed,
        fomc=over.pop("fomc", None),
        lake=over.pop("lake", lake),
        report=lines.append,
        **over,
    )
    return ok, lines, laked


def test_a_run_writes_the_lake_once_when_something_changed_and_reports_the_governor(tmp_path):
    ok, lines, laked = _run(tmp_path, Feed(CORE_KEYS))
    assert ok and len(laked) == 1
    assert any(f"{N} series: {N} new" in line for line in lines)
    assert any("governor for 2026-10-23" in line for line in lines)
    ok, lines, laked = _run(tmp_path, Feed(CORE_KEYS))
    assert ok and laked == []  # nothing changed: the lake is left alone
    assert any(f"{N} unchanged" in line for line in lines)


def test_a_run_fails_only_for_what_the_governor_reads(tmp_path):
    ok, _, _ = _run(tmp_path, Feed(CORE_KEYS, down={"fred_DGS10"}))
    assert ok
    ok, lines, _ = _run(tmp_path, Feed(CORE_KEYS, n=len(SESSIONS) - 1, down={"ofr_FSI"}))
    assert not ok
    assert any("ofr_FSI" in line and "failed" in line for line in lines)


def test_a_lake_that_cannot_be_written_fails_the_run_after_the_files_are_safe(tmp_path):
    def broken(root, directory):
        raise OSError("disk full")

    ok, lines, _ = _run(tmp_path, Feed(CORE_KEYS), lake=broken)
    assert not ok and (tmp_path / "external" / "cboe_VXN.csv").exists()
    assert any("lake NOT written" in line and "disk full" in line for line in lines)


def test_the_governor_line_names_what_is_raised_and_what_is_stale(tmp_path):
    R.refresh_series(WANTED, tmp_path, fetch=Feed(CORE_KEYS), now=NOW, report=quiet.append)
    line = R.governor_line(tmp_path, date(2026, 10, 23))
    assert line.startswith("governor for 2026-10-23:") and "of 5 warnings raised" in line
    assert "STALE" not in line
    late = R.governor_line(tmp_path, date(2026, 12, 1))
    assert "0 of 0 warnings" in late and "STALE, casting no vote: vxn_hi" in late
    assert "no reading" in R.governor_line(tmp_path / "empty", date(2026, 10, 23))


def test_the_lake_is_written_without_a_catalog(tmp_path):
    pytest.importorskip("duckdb")
    pytest.importorskip("polars")
    directory, root = tmp_path / "external", tmp_path / "warehouse"
    R.refresh_series(WANTED, directory, fetch=Feed(CORE_KEYS), now=NOW, report=quiet.append)
    line = R.write_lake(root, directory)
    assert line.startswith(f"lake: {N} series") and "no catalog yet" in line
    parts = sorted(p.parent.name for p in (root / "external").rglob("*.parquet"))
    assert "series_key=ofr_FSI" in parts and len(parts) == N
    assert not (root / "market_data.duckdb").exists()


# -- the FOMC calendar -----------------------------------------------------------


def test_a_meeting_the_engine_lacks_is_reported_until_it_is_added(tmp_path):
    from engine.data.fomc_calendar import FOMC_DECISION_DATES

    known = sorted(FOMC_DECISION_DATES)
    today = known[-1] + timedelta(days=100)
    passed, ahead = known[-1] + timedelta(days=49), known[-1] + timedelta(days=140)
    lines = R.fomc_lines(tmp_path, today, lambda: [*known[-3:], passed, ahead])
    assert "lacks 2 scheduled decision day(s)" in lines[0]
    assert lines[1] == f"  already passed: {passed}" and lines[2] == f"  next: {ahead}"
    stored = (tmp_path / R.FOMC_FILE).read_text().split()
    assert stored[0] == "date" and stored[-1] == str(ahead)
    current = R.fomc_lines(tmp_path, today, lambda: known[-3:])
    assert current == [f"FOMC calendar: the engine has every scheduled meeting to {known[-1]}"]


def test_a_calendar_that_cannot_be_fetched_is_one_line(tmp_path):
    def down():
        raise sources.SourceUnavailable("HTTP 503")

    assert R.fomc_lines(tmp_path, date(2026, 11, 10), down) == [
        "FOMC calendar not fetched: HTTP 503"
    ]
    assert not (tmp_path / R.FOMC_FILE).exists()


# -- when ------------------------------------------------------------------------


def test_the_session_a_process_started_now_would_trade():
    def at(text: str) -> datetime:
        return datetime.fromisoformat(text).replace(tzinfo=EASTERN)

    assert R.upcoming_session(at("2026-10-22 07:30")) == date(2026, 10, 22)
    assert R.upcoming_session(at("2026-10-22 20:45")) == date(2026, 10, 23)
    assert R.upcoming_session(at("2026-10-24 10:00")) == date(2026, 10, 26)  # a Saturday


def test_the_next_run_is_the_nearer_of_the_two_times():
    times = [clock_time(20, 45), clock_time(7, 30)]

    def at(text: str) -> datetime:
        return datetime.fromisoformat(text).replace(tzinfo=EASTERN)

    assert R.next_run(at("2026-10-22 21:00"), times) == at("2026-10-23 07:30")
    assert R.next_run(at("2026-10-23 08:00"), times) == at("2026-10-23 20:45")
    assert R.next_run(at("2026-10-23 20:45"), times) == at("2026-10-24 07:30")


def test_a_failed_run_is_tried_again_within_the_hour():
    clock = [datetime(2026, 10, 22, 21, 0, tzinfo=EASTERN)]
    results = iter([False, True, True])
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        clock[0] += timedelta(seconds=seconds)

    R.run_daily(
        [clock_time(20, 45), clock_time(7, 30)],
        lambda: next(results),
        now=lambda: clock[0],
        sleep=sleep,
        report=quiet.append,
        rounds=3,
    )
    assert slept[0] == R.RETRY_SECONDS  # failed at 21:00: again at 22:00
    assert clock[0] == datetime(2026, 10, 23, 20, 45, tzinfo=EASTERN)
    assert slept[1] == 9.5 * 3600  # 22:00 to 07:30


def test_the_command_line_accepts_what_the_compose_service_passes():
    args = R.build_parser().parse_args(["--daily", "20:45", "07:30"])
    assert args.daily == ["20:45", "07:30"]
    assert R.build_parser().parse_args(["--daily"]).daily == []
    assert R.build_parser().parse_args([]).daily is None
    assert set(CORE_KEYS) == set(R.REQUIRED)
