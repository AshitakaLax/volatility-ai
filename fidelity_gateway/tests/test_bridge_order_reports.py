"""bridge/order_reports.py -- the extension's order confirmations.

What arrives is checked field by field (it is logged and written to
disk), each order's latest report is kept, only real changes are logged
or written, and the file is read back so a reconnecting extension's
resent log is not news twice.
"""

from __future__ import annotations

import json
import threading

from fidelity_gateway.bridge.order_reports import KEEP, OrderReport, OrderReports


def _wire(**overrides) -> dict:
    """One report as the extension sends it (orderReport() in order-log.js)."""
    report = {
        "id": "2026-10-07T14:00:00.000Z#1",
        "confNum": "2C50H6WV",
        "symbol": "TQQQ",
        "side": "buy",
        "qty": 3,
        "limitPrice": 70.1,
        "state": "submitted",
        "filledQty": 0,
        "avgPrice": 0,
        "attempts": 1,
        "placedAt": "2026-10-07T14:00:00.000Z",
        "updatedAt": "2026-10-07T14:00:00.000Z",
        "detail": "",
    }
    report.update(overrides)
    return report


def _reports(**kwargs) -> tuple[OrderReports, list[str]]:
    lines: list[str] = []
    return OrderReports(log=lines.append, **kwargs), lines


# -- parsing ------------------------------------------------------------------


def test_a_report_is_read_from_the_wire_names():
    report = OrderReport.parse(_wire(state="filled", filledQty=3, avgPrice=70.05))
    assert report == OrderReport(
        id="2026-10-07T14:00:00.000Z#1",
        conf_num="2C50H6WV",
        symbol="TQQQ",
        side="buy",
        qty=3.0,
        limit_price=70.1,
        state="filled",
        filled_qty=3.0,
        avg_price=70.05,
        attempts=1,
        placed_at="2026-10-07T14:00:00.000Z",
        updated_at="2026-10-07T14:00:00.000Z",
        detail="",
    )
    assert report.summary == "BUY 3 TQQQ @ $70.10"


def test_what_is_not_a_report_is_refused():
    for bad in (
        None,
        "x",
        [],
        _wire(id=""),
        _wire(id=7),
        _wire(state="exploded"),
        _wire(side="short"),
        _wire(symbol=""),
        _wire(symbol=None),
    ):
        assert OrderReport.parse(bad) is None, bad


def test_numbers_that_are_not_sensible_are_zero_and_attempts_at_least_one():
    report = OrderReport.parse(
        _wire(qty=-1, limitPrice=float("nan"), filledQty=True, avgPrice="70", attempts=0)
    )
    assert (report.qty, report.limit_price, report.filled_qty, report.avg_price) == (0, 0, 0, 0)
    assert report.attempts == 1
    assert OrderReport.parse(_wire(attempts=4)).attempts == 4


def test_text_cannot_start_a_log_line_of_its_own_and_is_bounded():
    report = OrderReport.parse(
        _wire(detail="refused\n[bridge] FAKE LINE\r\x1b[2J", symbol="tqqq\n", confNum="  ")
    )
    assert "\n" not in report.detail and "\r" not in report.detail and "\x1b" not in report.detail
    assert report.symbol == "TQQQ"
    assert report.conf_num is None, "an empty confNum is no confNum"
    assert len(OrderReport.parse(_wire(detail="x" * 5000)).detail) == 500


def test_each_state_reads_as_its_own_log_line():
    def line(state, **extra):
        return OrderReport.parse(_wire(state=state, **extra)).describe()

    assert line("filled", filledQty=3, avgPrice=70.05) == (
        "the extension confirms order 2C50H6WV FILLED: BUY 3 TQQQ @ $70.10, 3 at $70.05"
    )
    assert line("submitted") == (
        "the extension confirms Fidelity accepted order 2C50H6WV: BUY 3 TQQQ @ $70.10"
    )
    assert "partly filled: 1 of 3 at $70.00" in line("partially_filled", filledQty=1, avgPrice=70)
    assert "cancelled" in line("cancelled")
    assert "expired" in line("expired")
    assert "REJECTED" in line("rejected")
    assert line("blocked", confNum=None, detail="trading is off") == (
        "the extension refused BUY 3 TQQQ @ $70.10: trading is off"
    )
    assert "could not confirm" in line("unknown", detail="the request failed")
    assert line("working") is None
    assert line("cancel_requested") is None


# -- keeping the latest -------------------------------------------------------


def test_a_new_report_is_kept_and_logged():
    reports, lines = _reports()
    assert reports.note(_wire()) is not None
    assert reports.for_conf_num("2C50H6WV").state == "submitted"
    assert lines == [
        "[bridge] the extension confirms Fidelity accepted order 2C50H6WV: BUY 3 TQQQ @ $70.10"
    ]


def test_the_same_report_again_is_not_news():
    reports, lines = _reports()
    reports.note(_wire())
    assert reports.note(_wire()) is None
    assert len(lines) == 1


def test_a_change_of_state_is_logged_and_the_latest_wins():
    reports, lines = _reports()
    reports.note(_wire())
    reports.note(_wire(state="working"))
    reports.note(_wire(state="filled", filledQty=3, avgPrice=70.05))
    assert reports.for_conf_num("2C50H6WV").state == "filled"
    assert len(lines) == 2, "working is the routine middle, and not logged"
    assert "FILLED" in lines[-1]


def test_a_partial_fill_growing_is_news_but_logged_only_on_the_change_of_state():
    reports, lines = _reports()
    reports.note(_wire(state="partially_filled", filledQty=1, avgPrice=70))
    assert reports.note(_wire(state="partially_filled", filledQty=2, avgPrice=70)) is not None
    assert reports.for_conf_num("2C50H6WV").filled_qty == 2
    assert len(lines) == 1


def test_a_refusal_retried_is_not_news_but_its_count_is_kept():
    reports, lines = _reports()
    reports.note(_wire(state="blocked", confNum=None, detail="off"))
    assert reports.note(_wire(state="blocked", confNum=None, detail="off", attempts=5)) is None
    assert reports.recent()[0].attempts == 5
    assert len(lines) == 1


def test_a_malformed_report_is_ignored_and_said_so():
    reports, lines = _reports()
    assert reports.note({"state": "filled"}) is None
    assert reports.recent() == []
    assert lines == ["[bridge] ignored an order report from the extension that is not one"]


def test_lookups_find_the_latest_report_for_a_confnum():
    reports, _ = _reports()
    reports.note(_wire(id="a", confNum="C1"))
    reports.note(_wire(id="b", confNum="C2", state="working"))
    assert reports.for_conf_num("C2").id == "b"
    assert reports.for_conf_num("C9") is None


def test_recent_is_newest_first_by_last_report():
    reports, _ = _reports()
    reports.note(_wire(id="a", confNum="C1"))
    reports.note(_wire(id="b", confNum="C2"))
    reports.note(_wire(id="a", confNum="C1", state="filled", filledQty=3, avgPrice=70))
    assert [report.id for report in reports.recent()] == ["a", "b"]
    assert [report.id for report in reports.recent(1)] == ["a"]


def test_memory_is_bounded():
    reports, _ = _reports(keep=3)
    for i in range(5):
        reports.note(_wire(id=f"r{i}", confNum=f"C{i}"))
    assert [report.id for report in reports.recent()] == ["r4", "r3", "r2"]
    assert KEEP >= 100


# -- the log the extension sends on connecting --------------------------------


def test_the_whole_log_is_taken_oldest_first_and_said_to_come_from_it():
    reports, lines = _reports()
    newest_first = [
        _wire(id="b", confNum="C2", state="filled", filledQty=3, avgPrice=70),
        _wire(id="a", confNum="C1"),
    ]
    assert reports.note_all({"orders": newest_first}) == 2
    assert [report.id for report in reports.recent()] == ["b", "a"]
    assert all(line.startswith("[bridge] (from the extension's log) ") for line in lines)
    assert reports.wait_for_log(0)


def test_a_resent_log_tells_the_engine_only_what_changed():
    reports, lines = _reports()
    reports.note(_wire(id="a", confNum="C1"))
    lines.clear()
    assert reports.note_all({"orders": [_wire(id="a", confNum="C1")]}) == 0
    assert lines == []


def test_a_malformed_log_is_ignored_and_not_taken_for_one():
    reports, lines = _reports()
    assert reports.note_all({"orders": "nope"}) == 0
    assert reports.note_all(None) == 0
    assert not reports.wait_for_log(0)
    assert lines == ["[bridge] ignored an order log from the extension that is not one"] * 2


def test_an_empty_log_still_counts_as_the_log_arriving():
    reports, _ = _reports()
    assert not reports.wait_for_log(0)
    reports.note_all({"orders": []})
    assert reports.wait_for_log(0)


# -- the file -----------------------------------------------------------------


def test_each_change_is_appended_to_the_file(tmp_path):
    path = tmp_path / "reports.jsonl"
    reports, _ = _reports(path=path)
    reports.note(_wire())
    reports.note(_wire())
    reports.note(_wire(state="filled", filledQty=3, avgPrice=70.05))
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [entry["state"] for entry in entries] == ["submitted", "filled"]
    assert entries[1]["conf_num"] == "2C50H6WV" and entries[1]["avg_price"] == 70.05
    assert all(isinstance(entry["received"], float) for entry in entries)
    assert reports.path == path


def test_a_restarted_engine_reads_the_file_back_and_is_not_told_twice(tmp_path):
    path = tmp_path / "reports.jsonl"
    first, _ = _reports(path=path)
    first.note(_wire(state="filled", filledQty=3, avgPrice=70.05))

    second, lines = _reports(path=path)
    assert second.for_conf_num("2C50H6WV").state == "filled"
    assert second.note_all({"orders": [_wire(state="filled", filledQty=3, avgPrice=70.05)]}) == 0
    assert lines == []
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_damaged_lines_are_skipped_not_fatal(tmp_path):
    path = tmp_path / "reports.jsonl"
    good = json.dumps({"received": 1.0, **OrderReport.parse(_wire()).to_dict()})
    path.write_text(f"{good}\nnot json\n\n{{}}\n" + json.dumps({"state": "filled"}) + "\n")
    reports, lines = _reports(path=path)
    assert reports.for_conf_num("2C50H6WV").state == "submitted"
    assert lines == [f"[bridge] skipped 3 unreadable line(s) in {path}"]


def test_a_file_that_cannot_be_written_is_said_once_and_never_raises(tmp_path):
    path = tmp_path / "missing-dir" / "reports.jsonl"
    reports, lines = _reports(path=path)
    reports.note(_wire(id="a", confNum="C1"))
    reports.note(_wire(id="b", confNum="C2"))
    assert reports.for_conf_num("C2") is not None, "still kept in memory"
    assert sum("could not record order reports" in line for line in lines) == 1


def test_reports_from_another_thread_are_safe():
    reports, _ = _reports()
    errors: list[BaseException] = []

    def send(start: int) -> None:
        try:
            for i in range(start, start + 50):
                reports.note(_wire(id=f"r{i}", confNum=f"C{i}"))
                reports.for_conf_num(f"C{i}")
                reports.recent()
        except BaseException as exc:  # surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=send, args=(n * 50,)) for n in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert len(reports.recent()) == 200
