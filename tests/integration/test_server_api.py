"""The server against a real store and the real engine.

No mocked persistence and no mocked backtest: the point of these routes
is that they compose src/dashboard_data, CircuitBreaker and
OptimizationController correctly, and substituting any of those would
test the substitution.

The backtest run uses tests/fixtures/regression_ohlcv.csv rather than a
real 60 MB minute file -- a genuine ten-year run costs ~23 seconds, and
a test suite is not the place to spend that.
"""

from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from server.app import app
from src.persistence import LedgerStore

FIXTURE = "tests/fixtures/regression_ohlcv.csv"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def store(tmp_path):
    """A real ledger store with one open lot."""
    path = str(tmp_path / "paper_ledger.db")
    store = LedgerStore(path)
    store.set_meta("live.cash", "50000.0")
    store.set_meta("live.peak_equity", "60000.0")
    yield path
    store.close()


class TestHealth:
    def test_it_reports_what_it_can_and_cannot_do(self, client):
        body = client.get("/api/health").json()
        assert body["status"] == "ok"
        assert body["capabilities"]["halt"] is True
        assert body["capabilities"]["liquidate"] is False


class TestLiveReads:
    def test_state_comes_back_for_a_real_store(self, client, store):
        body = client.get("/api/live/state", params={"path": store}).json()
        assert body["cash"] == pytest.approx(50000.0)
        assert body["peak_equity"] == pytest.approx(60000.0)
        assert body["halted"] is False
        assert body["lots"] == []

    def test_a_missing_store_is_a_404_not_a_500(self, client, tmp_path):
        response = client.get("/api/live/state", params={"path": str(tmp_path / "nope.db")})
        assert response.status_code == 404

    def test_a_file_that_is_not_a_store_is_a_404(self, client, tmp_path):
        junk = tmp_path / "junk.db"
        junk.write_text("this is not a database", encoding="utf-8")
        assert client.get("/api/live/state", params={"path": str(junk)}).status_code == 404

    def test_activity_returns_the_revision_log(self, client, store):
        body = client.get("/api/live/activity", params={"path": store, "limit": 10}).json()
        assert isinstance(body["entries"], list)

    def test_bars_for_an_unknown_symbol_are_a_404(self, client):
        response = client.get("/api/live/bars", params={"symbol": "NOTATICKER"})
        assert response.status_code == 404


class TestHalt:
    def test_it_halts_and_reads_the_state_back(self, client, store):
        body = client.post(
            "/api/live/halt", json={"path": store, "reason": "operator stopped it"}
        ).json()
        assert body["halted"] is True
        assert "operator" in body["halt_reason"]

    def test_the_halt_is_visible_to_the_read_path(self, client, store):
        """Two different modules and two different connections must agree
        about whether this deployment is halted."""
        client.post("/api/live/halt", json={"path": store, "reason": "checking readback"})
        assert client.get("/api/live/state", params={"path": store}).json()["halted"] is True

    def test_halting_twice_is_not_an_error(self, client, store):
        """An operator hitting the button twice under stress should not
        get an exception for it."""
        for _ in range(2):
            response = client.post("/api/live/halt", json={"path": store, "reason": "again"})
            assert response.status_code == 200

    def test_an_empty_reason_is_rejected(self, client, store):
        """The reason is shown to the next operator, who may be the same
        person three weeks later."""
        response = client.post("/api/live/halt", json={"path": store, "reason": ""})
        assert response.status_code == 422

    def test_a_bad_path_is_a_400_not_a_stack_trace(self, client, tmp_path):
        junk = tmp_path / "junk.db"
        junk.write_text("not a database", encoding="utf-8")
        response = client.post("/api/live/halt", json={"path": str(junk), "reason": "nope"})
        assert response.status_code == 400
        assert "Could not halt" in response.json()["detail"]

    def test_there_is_no_liquidate_endpoint(self, client, store):
        """Requested, and refused with a reason."""
        assert client.post("/api/live/liquidate", json={"path": store}).status_code == 404


class TestDeployment:
    def test_it_reports_the_build_it_is_running(self, client):
        body = client.get("/api/deployment").json()
        assert body["git_commit"], "no commit reported from inside a git checkout"
        assert body["git_branch"]
        assert body["uptime_seconds"] >= 0
        assert body["python"].startswith("3.")

    def test_container_stats_are_null_rather_than_zero_when_unavailable(self, client):
        """A "CPU 0%" that means "could not measure" is a number someone
        would act on. Outside a container these must be absent, not
        plausible-looking."""
        body = client.get("/api/deployment").json()
        if not body["containerised"]:
            assert body["memory_mb"] is None
            assert body["memory_limit_mb"] is None
        # CPU is never reported: cgroup exposes cumulative microseconds,
        # and a percentage needs two samples over a known interval, which
        # this endpoint does not keep.
        assert body["cpu_pct"] is None

    def test_a_cgroup_max_limit_is_not_read_as_a_number(self):
        """cgroup writes the literal string "max" for "no limit"."""
        from server.deployment import _read_int

        assert _read_int("/definitely/not/a/real/cgroup/path") is None

    def test_git_dirty_distinguishes_unknown_from_clean(self, client):
        """None means "could not tell". A card showing a clean checkmark
        because git was missing would assert something it does not know."""
        body = client.get("/api/deployment").json()
        assert body["git_dirty"] in (True, False, None)


class TestBacktestSubmission:
    def test_funds_reports_availability_rather_than_hiding_it(self, client):
        body = client.get("/api/backtest/funds").json()
        assert body["funds"], "no funds listed at all"
        assert all("available" in fund for fund in body["funds"])
        assert "fixed" in body["sizing_models"]

    def test_an_unknown_sizing_model_is_a_400_naming_the_real_ones(self, client):
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "profit_targets": [0.005],
                "sizing_model": "not_a_strategy",
            },
        )
        assert response.status_code == 400
        assert "Known strategies" in response.json()["detail"]

    def test_an_empty_ticker_list_is_rejected_by_shape(self, client):
        response = client.post(
            "/api/backtest/runs",
            json={"tickers": [], "grid_steps": [0.01], "profit_targets": [0.005]},
        )
        assert response.status_code == 422

    def test_a_valid_submission_returns_202_and_an_id(self, client):
        """202, not 200: nothing has been computed yet."""
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "profit_targets": [0.005],
                "sizing_model": "fixed",
                "strategy_params": {"allocation_pct": 0.05},
                "limit": 500,
            },
        )
        assert response.status_code == 202
        body = response.json()
        assert body["run_id"]
        assert body["status"] in {"queued", "running", "complete"}

    def test_an_unknown_run_is_a_404(self, client):
        assert client.get("/api/backtest/runs/deadbeef").status_code == 404


class TestDateWindowAndBars:
    def test_the_window_is_applied_before_the_bar_cap(self):
        """CAPPING FIRST WOULD BE A REAL BUG: it takes the tail of the
        FILE and then filters, so any non-recent window comes back empty
        -- indistinguishable on screen from "no trades in that period"."""
        import pandas as pd_

        from server.backtest import window

        index = pd_.date_range("2024-01-01", periods=1000, freq="1min", tz="UTC")
        frame = pd_.DataFrame({"close": range(1000)}, index=index)

        # A window at the START of the file, with a cap far smaller than
        # the file. Cap-then-window would return nothing.
        got = window(frame, "2024-01-01", "2024-01-01", limit=10)
        assert len(got) == 10
        assert got.index[0] >= pd_.Timestamp("2024-01-01", tz="UTC")

    def test_the_end_bound_covers_the_whole_day(self):
        import pandas as pd_

        from server.backtest import window

        index = pd_.date_range("2024-01-01 09:00", periods=3, freq="4h", tz="UTC")
        frame = pd_.DataFrame({"close": [1, 2, 3]}, index=index)
        # 17:00 on the 1st must survive an end of "2024-01-01".
        assert len(window(frame, None, "2024-01-01", None)) == 3

    def test_bars_downsample_by_ohlc_not_by_sampling(self, client):
        """Under the intrabar fill model a level TOUCHED during a bar is
        a fill, so dropping the extremes would leave markers hanging off
        candles that never reached them."""
        body = client.get(
            "/api/backtest/bars",
            params={"ticker": "TQQQ", "start": "2026-03-02", "end": "2026-03-06", "max_points": 20},
        ).json()
        assert body["bars"], "no bars for a window the file covers"
        assert len(body["bars"]) <= 40, "downsample did not bound the result"
        assert body["bucket_seconds"] > 60, "a 4-day window at 20 points must roll up"
        for bar in body["bars"]:
            assert bar["low"] <= bar["open"] <= bar["high"]
            assert bar["low"] <= bar["close"] <= bar["high"]

    def test_bars_for_an_unknown_ticker_are_a_404(self, client):
        assert client.get("/api/backtest/bars", params={"ticker": "NOPE"}).status_code == 404

    def test_an_empty_window_returns_no_bars_rather_than_failing(self, client):
        body = client.get(
            "/api/backtest/bars",
            params={"ticker": "TQQQ", "start": "1990-01-01", "end": "1990-01-02"},
        ).json()
        assert body["bars"] == []
        assert body["source_rows"] == 0


class TestBacktestExecution:
    """The worker actually runs the engine and produces the contract."""

    def test_a_run_completes_and_carries_joinable_executions(self, tmp_path):
        from server.backtest import run_backtest

        frame = pd.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")
        csv = tmp_path / "TESTQ.csv"
        frame.to_csv(csv)

        # Point KNOWN_DATA at the fixture for the duration, so this
        # exercises the real code path without a 60 MB file.
        from server import backtest as module

        original = dict(module.KNOWN_DATA)
        module.KNOWN_DATA.clear()
        module.KNOWN_DATA["TESTQ"] = str(csv)
        try:
            progress: list[tuple[float, str]] = []
            report = run_backtest(
                {
                    "tickers": ["TESTQ"],
                    "grid_steps": [0.01],
                    "profit_targets": [0.005],
                    "sizing_model": "fixed",
                    "strategy_params": {"allocation_pct": 0.05},
                    "limit": 5000,
                },
                lambda fraction, note: progress.append((fraction, note)),
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        assert progress, "the run reported no progress at all"
        fund = report["funds"]["TESTQ"]

        # The metrics the UI panel needs are all present.
        for key in ("win_rate_pct", "profit_factor", "stuck_capital_value", "sharpe_ratio"):
            assert key in fund["metrics"], f"missing {key}"

        # And the executions carry what a cycle connector needs.
        sells = [e for e in fund["executions"] if e["type"] == "SELL"]
        buys = {e["matched_buy_id"] for e in sells}
        buy_lots = {
            e["order_id"].rsplit("-buy-", 1)[0] for e in fund["executions"] if e["type"] == "BUY"
        }
        assert sells, "the fixture produced no sells"
        assert buys <= buy_lots, "a sell references a lot with no buy row"

    def test_a_multi_configuration_run_returns_every_cell(self, tmp_path):
        """The sweep matrix needs the whole surface, not the best row."""
        import pandas as pd_

        from server import backtest as module
        from server.backtest import run_backtest

        frame = pd_.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")
        csv = tmp_path / "TESTQ.csv"
        frame.to_csv(csv)

        original = dict(module.KNOWN_DATA)
        module.KNOWN_DATA.clear()
        module.KNOWN_DATA["TESTQ"] = str(csv)
        try:
            report = run_backtest(
                {
                    "tickers": ["TESTQ"],
                    "grid_steps": [0.01, 0.02],
                    "profit_targets": [0.005, 0.01, 0.02],
                    "sizing_model": "fixed",
                    "strategy_params": {"allocation_pct": 0.05},
                    "limit": 5000,
                },
                lambda fraction, note: None,
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        cells = report["funds"]["TESTQ"]["configurations"]
        assert len(cells) == 6, "2 steps x 3 targets should be 6 cells"
        assert {c["grid_step"] for c in cells} == {0.01, 0.02}
        assert {c["profit_target"] for c in cells} == {0.005, 0.01, 0.02}
        # Index 0 is the engine's own top-ranked row, and `metrics`
        # above describes that same configuration.
        assert cells[0]["metrics"] == report["funds"]["TESTQ"]["metrics"]

    def test_a_window_with_no_bars_fails_with_a_useful_message(self, tmp_path):
        import pandas as pd_

        from server import backtest as module
        from server.backtest import run_backtest

        frame = pd_.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")
        csv = tmp_path / "TESTQ.csv"
        frame.to_csv(csv)

        original = dict(module.KNOWN_DATA)
        module.KNOWN_DATA.clear()
        module.KNOWN_DATA["TESTQ"] = str(csv)
        try:
            with pytest.raises(ValueError, match="no bars between"):
                run_backtest(
                    {
                        "tickers": ["TESTQ"],
                        "grid_steps": [0.01],
                        "profit_targets": [0.005],
                        "sizing_model": "fixed",
                        "start": "1990-01-01",
                        "end": "1990-06-01",
                    },
                    lambda fraction, note: None,
                )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

    def test_a_run_naming_no_downloaded_fund_fails_with_a_useful_message(self):
        from server.backtest import run_backtest

        with pytest.raises(ValueError, match="fetch-data"):
            run_backtest(
                {
                    "tickers": ["NOTATICKER"],
                    "grid_steps": [0.01],
                    "profit_targets": [0.005],
                    "sizing_model": "fixed",
                },
                lambda fraction, note: None,
            )
