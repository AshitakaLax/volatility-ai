"""Run History queries, run summaries and paged fills, through the HTTP API.

The filter rules mirror web/src/lib/filters.ts as it stood (see
server/history_query.py); these cases are the ones its tests pinned,
now asserted against the endpoint that replaced it.
"""

from __future__ import annotations

import json
import os
import time

import pytest
from fastapi.testclient import TestClient

from server import history
from server.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))
    return TestClient(app)


def fill(lot, side, bar, ts, **extra):
    return {"lot": lot, "side": side, "i": bar, "px": 10.0, "qty": 1.0, "ts": ts, **extra}


def save_run(
    run_id,
    *,
    ticker="TQQQ",
    name=None,
    model="fixed",
    fill_model="close",
    start="2026-01-01T14:30:00+00:00",
    end="2026-02-01T20:00:00+00:00",
    cells=None,
    fills=None,
    bars=1000,
):
    cells = (
        cells
        if cells is not None
        else [{"grid": 0.01, "target": 0.005, "params": {}, "m": {"cagr_pct": 1.0}}]
    )
    history.save(
        run_id,
        {
            "id": run_id,
            "status": "complete",
            "report": {
                "name": name,
                "model": model,
                "fill": fill_model,
                "no_loss": True,
                "start": start,
                "end": end,
                "interval": "1Min",
                "funds": {
                    ticker: {
                        "cells": cells,
                        "fills": fills or [],
                        "equity": {"dates": ["2026-01-02"], "equity": [100000.0]},
                        "bars": {"start": start, "end": end, "count": bars},
                    }
                },
            },
        },
    )


def cell(grid=0.01, target=0.005, params=None, **metrics):
    return {"grid": grid, "target": target, "params": params or {}, "m": metrics}


def page(client, **body):
    body.setdefault("ticker", "TQQQ")
    response = client.post("/api/backtest/history/query", json=body)
    assert response.status_code == 200, response.text
    return response.json()


class TestQuery:
    def test_a_fund_is_required(self, client):
        assert client.post("/api/backtest/history/query", json={}).status_code == 422

    def test_only_the_named_funds_cells_are_returned(self, client):
        save_run("a", ticker="TQQQ")
        save_run("b", ticker="RSP")
        body = page(client)
        assert [row["ticker"] for row in body["rows"]] == ["TQQQ"]
        assert body["total"] == body["total_unfiltered"] == 1

    def test_the_name_filter_is_a_case_insensitive_substring_and_drops_unnamed_runs(self, client):
        save_run("a", name="RSI oversold sweep")
        save_run("b", name="bell curve")
        save_run("c")
        rows = page(client, filters={"name": "OVERSOLD"})["rows"]
        assert [row["name"] for row in rows] == ["RSI oversold sweep"]
        assert page(client, filters={"name": "x"})["total"] == 0

    def test_categorical_lists_are_or_within_and_between(self, client):
        save_run("a", model="fixed", fill_model="close")
        save_run("b", model="rsi", fill_model="close")
        save_run("c", model="fixed", fill_model="intrabar")
        body = page(client, filters={"models": ["fixed"], "fillModels": ["close", "intrabar"]})
        assert sorted(row["run"] for row in body["rows"]) == ["a", "c"]

    def test_a_swept_dimension_filters_in_the_percent_the_table_shows(self, client):
        save_run("a", cells=[cell(grid=0.005), cell(grid=0.01), cell(grid=0.02)])
        assert [
            r["grid"]
            for r in page(client, filters={"ranges": {"grid_step": {"min": 0.75, "max": 1.5}}})[
                "rows"
            ]
        ] == [0.01]
        picked = page(client, filters={"values": {"grid_step": [0.5, 2]}})["rows"]
        assert sorted(r["grid"] for r in picked) == [0.005, 0.02]

    def test_a_value_set_or_a_band_on_the_same_field_either_passes(self, client):
        save_run("a", cells=[cell(grid=0.005), cell(grid=0.03)])
        body = page(
            client,
            filters={
                "values": {"grid_step": [3]},
                "ranges": {"grid_step": {"min": None, "max": 0.6}},
            },
        )
        assert body["total"] == 2

    def test_a_row_missing_a_gated_field_is_excluded(self, client):
        save_run("a", cells=[cell(cagr_pct=10, worst_year_pct=-5), cell(cagr_pct=10)])
        body = page(client, filters={"ranges": {"metric:worst_year_pct": {"min": -10, "max": 0}}})
        assert body["total"] == 1
        save_run("p", cells=[cell(params={"period": 14}), cell(params={})])
        assert (
            page(client, filters={"ranges": {"param:period": {"min": 10, "max": 20}}})["total"] == 1
        )

    def test_a_simulation_window_matches_by_overlap_inclusive(self, client):
        save_run("q1", start="2026-01-01", end="2026-03-31")
        save_run("q2", start="2026-04-01", end="2026-06-30")
        assert (
            page(client, filters={"window": {"start": "2026-02-01", "end": "2026-05-01"}})["total"]
            == 2
        )
        assert page(client, filters={"window": {"start": "2026-04-01", "end": None}})["total"] == 1
        assert page(client, filters={"window": {"start": None, "end": "2026-01-01"}})["total"] == 1
        assert page(client, filters={"window": {"start": "2027-01-01", "end": None}})["total"] == 0

    def test_window_days_is_inclusive_calendar_days(self, client):
        save_run("d30", start="2026-01-01", end="2026-01-30")
        save_run("d365", start="2026-01-01", end="2026-12-31")
        body = page(client, filters={"ranges": {"window_days": {"min": 100, "max": None}}})
        assert [row["run"] for row in body["rows"]] == ["d365"]

    def test_default_order_is_the_rank_metric_best_first_with_missing_last(self, client):
        save_run("a", cells=[cell(cagr_pct=5), cell(grid=0.02), cell(grid=0.03, cagr_pct=20)])
        rows = page(client, rank_by="cagr_pct", sort={"column": "metric", "direction": "desc"})[
            "rows"
        ]
        assert [r["m"].get("cagr_pct") for r in rows] == [20, 5, None]
        rows = page(client, rank_by="cagr_pct", sort={"column": "metric", "direction": "asc"})[
            "rows"
        ]
        assert [r["m"].get("cagr_pct") for r in rows] == [5, 20, None]

    def test_a_string_column_sorts_both_ways_with_null_last(self, client):
        save_run("b", name="beta")
        save_run("n")
        save_run("a", name="alpha")
        asc = [r["name"] for r in page(client, sort={"column": "name", "direction": "asc"})["rows"]]
        desc = [
            r["name"] for r in page(client, sort={"column": "name", "direction": "desc"})["rows"]
        ]
        assert asc == ["alpha", "beta", None] and desc == ["beta", "alpha", None]

    def test_pages_slice_the_sorted_result_and_count_matched_runs(self, client):
        save_run("a", cells=[cell(grid=g / 100, cagr_pct=g) for g in range(1, 8)])
        save_run("b", cells=[cell(cagr_pct=0.5)])
        body = page(client, offset=2, limit=3, sort={"column": "metric", "direction": "desc"})
        assert [r["m"]["cagr_pct"] for r in body["rows"]] == [5, 4, 3]
        assert body["total"] == 8 and body["runs_matched"] == 2

    def test_rows_carry_only_the_metrics_history_uses(self, client):
        save_run("a", cells=[cell(cagr_pct=1.0, final_equity=123.0, closed_trades=7)])
        (row,) = page(client)["rows"]
        assert row["m"] == {"cagr_pct": 1.0}


class TestFacetsFundsRuns:
    def test_facets_list_one_funds_options(self, client):
        save_run(
            "a",
            model="fixed",
            cells=[cell(grid=0.02, params={"period": 14, "ticker": "X"}), cell(grid=0.005)],
        )
        save_run("b", model="rsi", fill_model="intrabar")
        save_run("c", ticker="RSP", model="bell_curve")
        facets = client.get("/api/backtest/history/facets", params={"ticker": "TQQQ"}).json()
        assert facets["models"] == ["fixed", "rsi"] and facets["fills"] == ["close", "intrabar"]
        fields = {f["key"]: f for f in facets["fields"]}
        assert fields["grid_step"]["values"] == [0.5, 1.0, 2.0]
        assert "param:period" in fields and "param:ticker" not in fields
        assert facets["rows"] == 3 and facets["runs"] == 2

    def test_funds_count_cells_and_runs(self, client):
        save_run("a", ticker="TQQQ", cells=[cell(), cell(grid=0.02)])
        save_run("b", ticker="RSP")
        funds = {f["ticker"]: f for f in client.get("/api/backtest/history/funds").json()}
        assert (funds["TQQQ"]["rows"], funds["TQQQ"]["runs"]) == (2, 1)
        assert funds["RSP"]["last_saved"] is not None

    def test_runs_lists_run_level_fields_without_cells(self, client):
        save_run("a", name="named")
        runs = client.get("/api/backtest/history/runs").json()["runs"]
        assert runs["a"]["name"] == "named" and "funds" not in runs["a"]


class TestDerivedFiles:
    def test_an_archive_written_directly_is_indexed_on_first_read(self, client):
        # tools/ write archives without going through history.save.
        directory = history.directory()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "tool.json").write_text(
            json.dumps(
                {
                    "id": "tool",
                    "status": "complete",
                    "report": {
                        "model": "fixed",
                        "funds": {"TQQQ": {"cells": [cell()], "fills": [], "bars": {"count": 3}}},
                    },
                }
            ),
            encoding="utf-8",
        )
        assert [r["run"] for r in page(client)["rows"]] == ["tool"]

    def test_a_rewritten_archive_rebuilds_its_derived_files(self, client):
        save_run("a", cells=[cell(cagr_pct=1.0)])
        assert page(client)["rows"][0]["m"]["cagr_pct"] == 1.0
        time.sleep(0.02)
        save_run("a", cells=[cell(cagr_pct=9.0)])
        archive = history.directory() / "a.json"
        os.utime(archive, (time.time() + 5, time.time() + 5))
        assert page(client)["rows"][0]["m"]["cagr_pct"] == 9.0

    def test_a_run_is_served_without_fills_and_with_a_count(self, client):
        save_run("a", fills=[fill("L1", "BUY", 1, "2026-01-02T14:30:00+00:00")] * 2)
        fund = client.get("/api/backtest/runs/a").json()["report"]["funds"]["TQQQ"]
        assert fund["fills_count"] == 2 and "fills" not in fund
        assert fund["equity"]["equity"] == [100000.0]


class TestFillsApi:
    @pytest.fixture
    def run(self, client):
        save_run(
            "f",
            fills=[
                fill("L1", "BUY", 1, "2026-01-02T14:30:00+00:00", rsi=25.0),
                fill("L1", "SELL", 5, "2026-01-05T15:00:00+00:00", pnl=1.5, why="profit_target"),
                fill("L2", "BUY", 7, "2026-01-06T14:30:00+00:00"),
            ],
        )
        return "f"

    def test_pages_fills_with_a_summary_over_the_filtered_set(self, client, run):
        body = client.get(
            f"/api/backtest/runs/{run}/fills", params={"ticker": "TQQQ", "limit": 2}
        ).json()
        assert body["total"] == 3 and len(body["rows"]) == 2
        assert body["summary"] == {
            "fills": 3,
            "fills_unfiltered": 3,
            "closed": 1,
            "open": 1,
            "realized": 1.5,
        }

    def test_filters_and_cycles_through_the_endpoint(self, client, run):
        stuck = client.get(
            f"/api/backtest/runs/{run}/fills", params={"ticker": "TQQQ", "status": "stuck"}
        ).json()
        assert [r["lot"] for r in stuck["rows"]] == ["L2"]
        cycles = client.get(
            f"/api/backtest/runs/{run}/fills",
            params={"ticker": "TQQQ", "view": "cycles", "cycles": "closed"},
        ).json()
        assert [c["lot"] for c in cycles["rows"]] == ["L1"] and cycles["rows"][0]["realized"] == 1.5

    def test_csv_downloads_the_filtered_fills(self, client, run):
        response = client.get(
            f"/api/backtest/runs/{run}/fills.csv", params={"ticker": "TQQQ", "end": "2026-01-05"}
        )
        assert response.headers["content-type"].startswith("text/csv")
        lines = response.text.strip().splitlines()
        assert lines[0].startswith("timestamp,type,lot_id") and len(lines) == 3

    def test_unknown_runs_funds_and_bad_dates_are_errors_not_empty_pages(self, client, run):
        assert (
            client.get("/api/backtest/runs/nope/fills", params={"ticker": "TQQQ"}).status_code
            == 404
        )
        assert (
            client.get(f"/api/backtest/runs/{run}/fills", params={"ticker": "RSP"}).status_code
            == 404
        )
        assert (
            client.get(
                f"/api/backtest/runs/{run}/fills", params={"ticker": "TQQQ", "start": "garbage"}
            ).status_code
            == 400
        )
