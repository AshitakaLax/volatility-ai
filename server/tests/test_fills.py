"""server/fills.py: the result page's execution filters, server-side.

These cases are the ones web/src/lib/filters.test.ts pinned for
filterExecutions / openLotIds / buildCycles before that logic moved
here -- each is a case where the wrong answer looks entirely plausible
on screen (a lot counted open that closed, a warmup fill passing an RSI
bound, a whole day missing from a range).
"""

from __future__ import annotations

from server.fills import CSV_HEADER, FundFills, strip_report


def buy(lot: str, bar: int, ts: str = "2026-03-01T14:30:00+00:00", **extra) -> dict:
    return {"lot": lot, "side": "BUY", "i": bar, "px": 100.0, "qty": 1.0, "ts": ts, **extra}


def sell(lot: str, bar: int, ts: str = "2026-03-02T14:30:00+00:00", **extra) -> dict:
    return {
        "lot": lot,
        "side": "SELL",
        "i": bar,
        "px": 101.0,
        "qty": 1.0,
        "ts": ts,
        "pnl": 1.0,
        **extra,
    }


def keys(rows: list[dict]) -> list[str]:
    return [f"{r['lot']}-{r['side'].lower()}-{r['i']}" for r in rows]


def query(fills: list[dict], **kwargs) -> dict:
    return FundFills.from_fills(fills).query(limit=5000, **kwargs)


class TestRoundTrip:
    def test_a_page_reads_back_exactly_as_recorded(self, tmp_path):
        fills = [buy("A", 1, rsi=25.0), sell("A", 9, why="signal_exit", pnl=-0.5)]
        path = tmp_path / "f.npz"
        FundFills.from_fills(fills).save(path)
        assert FundFills.load(path).query(limit=10)["rows"] == fills

    def test_absent_rsi_pnl_and_why_stay_absent_rather_than_zero(self):
        row = query([buy("A", 1)])["rows"][0]
        assert "rsi" not in row and "pnl" not in row and "why" not in row


class TestFilters:
    def test_excludes_executions_with_no_rsi_when_a_bound_is_set(self):
        rows = query([buy("A", 1), buy("B", 2, rsi=25.0)], rsi_max=30)["rows"]
        assert keys(rows) == ["B-buy-2"]

    def test_keeps_unknown_rsi_executions_when_no_bound_is_set(self):
        assert query([buy("A", 1)])["total"] == 1

    def test_treats_rsi_bounds_as_inclusive(self):
        at30 = [buy("A", 1, rsi=30.0)]
        assert query(at30, rsi_max=30)["total"] == 1
        assert query(at30, rsi_min=30)["total"] == 1

    def test_includes_the_whole_of_the_end_day(self):
        # A picker gives "2026-03-02"; someone choosing that day means
        # all of it, not the instant midnight begins it.
        out = query([sell("A", 9)], start="2026-03-02", end="2026-03-02")
        assert out["total"] == 1

    def test_a_full_timestamp_end_still_keeps_the_whole_day(self):
        # The chart's window ends on the data's last bar, a timestamp.
        late = [buy("A", 1, ts="2026-03-02T19:59:00+00:00")]
        assert query(late, end="2026-03-02T10:00:00+00:00")["total"] == 1
        assert query(late, end="2026-03-01T23:00:00+00:00")["total"] == 0

    def test_a_start_date_begins_at_its_midnight(self):
        fills = [
            buy("A", 1, ts="2026-03-01T23:59:00+00:00"),
            buy("B", 2, ts="2026-03-02T00:00:00+00:00"),
        ]
        assert keys(query(fills, start="2026-03-02")["rows"]) == ["B-buy-2"]

    def test_splits_open_from_closed_lots_by_status(self):
        fills = [buy("A", 1), sell("A", 2), buy("B", 3)]
        assert keys(query(fills, status="stuck")["rows"]) == ["B-buy-3"]
        assert keys(query(fills, status="closed")["rows"]) == ["A-buy-1", "A-sell-2"]

    def test_open_is_decided_over_all_fills_not_the_filtered_window(self):
        # A's sell falls outside the range, but A is still not open.
        fills = [
            buy("A", 1, ts="2026-03-01T14:30:00+00:00"),
            sell("A", 2, ts="2026-03-05T14:30:00+00:00"),
        ]
        assert query(fills, status="stuck", end="2026-03-02")["total"] == 0


class TestCycles:
    def test_pairs_a_buy_with_the_sell_that_closed_it(self):
        out = query([buy("A", 1), sell("A", 9)], view="cycles")
        (cycle,) = out["rows"]
        assert cycle["open"] is False and cycle["realized"] == 1.0
        assert out["summary"]["closed"] == 1 and out["summary"]["open"] == 0

    def test_sums_partial_sells_against_one_lot(self):
        (cycle,) = query(
            [buy("A", 1), sell("A", 5, pnl=0.4), sell("A", 9, pnl=0.6)], view="cycles"
        )["rows"]
        assert len(cycle["sells"]) == 2
        assert abs(cycle["realized"] - 1.0) < 1e-12

    def test_reports_an_unsold_lot_as_open_with_null_realised(self):
        # null, not 0: zero would read as "closed for no gain".
        (cycle,) = query([buy("A", 1)], view="cycles")["rows"]
        assert cycle["open"] is True and cycle["realized"] is None

    def test_keeps_the_first_buy_when_a_lot_id_appears_twice(self):
        (cycle,) = query([buy("A", 1), buy("A", 50), sell("A", 60)], view="cycles")["rows"]
        assert cycle["buy"]["i"] == 1

    def test_ignores_a_sell_whose_lot_has_no_buy(self):
        assert query([sell("GHOST", 5)], view="cycles")["total"] == 0

    def test_cycles_follow_the_order_their_buys_happened(self):
        fills = [buy("B", 1), buy("A", 2), sell("B", 3)]
        assert [c["lot"] for c in query(fills, view="cycles")["rows"]] == ["B", "A"]

    def test_closed_and_open_cycles_can_be_asked_for_separately(self):
        fills = [buy("A", 1), sell("A", 2), buy("B", 3)]
        assert [c["lot"] for c in query(fills, view="cycles", cycles="closed")["rows"]] == ["A"]
        assert [c["lot"] for c in query(fills, view="cycles", cycles="open")["rows"]] == ["B"]

    def test_the_summary_realised_total_counts_only_closed_cycles(self):
        fills = [
            buy("A", 1),
            sell("A", 2, pnl=2.5),
            buy("B", 3),
            buy("C", 4),
            sell("C", 5, pnl=-1.0),
        ]
        assert query(fills, view="cycles")["summary"]["realized"] == 1.5


class TestPaging:
    def test_offset_and_limit_slice_the_filtered_rows_and_report_the_total(self):
        fills = [buy(f"L{n}", n) for n in range(10)]
        out = FundFills.from_fills(fills).query(offset=3, limit=4)
        assert out["total"] == 10 and out["offset"] == 3
        assert [r["i"] for r in out["rows"]] == [3, 4, 5, 6]
        assert out["summary"]["fills"] == 10 and out["summary"]["fills_unfiltered"] == 10

    def test_the_limit_is_capped(self):
        fills = [buy(f"L{n}", n) for n in range(6000)]
        assert len(FundFills.from_fills(fills).query(limit=100_000)["rows"]) == 5000


def test_csv_streams_every_filtered_fill_with_the_export_header():
    fills = FundFills.from_fills([buy("A", 1, rsi=20.0), sell("A", 2, why="profit_target")])
    lines = "".join(fills.csv_lines("TQQQ", fills.select())).splitlines()
    assert lines[0].split(",") == CSV_HEADER
    assert lines[1].split(",")[:6] == [
        "2026-03-01T14:30:00+00:00",
        "BUY",
        "A",
        "TQQQ",
        "100.0",
        "1.0",
    ]
    assert lines[2].endswith(",profit_target") and len(lines) == 3


def test_strip_report_swaps_fills_for_a_count_without_touching_the_original():
    report = {"id": "r", "funds": {"TQQQ": {"cells": [], "fills": [buy("A", 1)] * 3}}}
    slim = strip_report(report)
    assert slim["funds"]["TQQQ"] == {"cells": [], "fills_count": 3}
    assert len(report["funds"]["TQQQ"]["fills"]) == 3
