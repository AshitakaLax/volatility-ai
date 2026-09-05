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
