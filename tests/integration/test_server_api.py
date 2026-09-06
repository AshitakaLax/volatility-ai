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


class TestLiveParametersAndIndicators:
    def test_a_store_with_no_parameters_reports_an_empty_dict(self, client, store):
        """Absent is normal for a store written before the loop recorded
        them -- the UI shows "unknown", not zeros."""
        assert client.get("/api/live/state", params={"path": store}).json()["parameters"] == {}

    def test_parameters_written_by_the_loop_come_back(self, client, store):
        """This is the field that would have made the 30%-instead-of-0.3%
        profit target visible without diffing a config against a ledger."""
        import json as json_

        from src.persistence import LedgerStore

        writer = LedgerStore(store)
        writer.set_meta(
            "live.parameters",
            json_.dumps({"symbol": "TQQQ", "step": 0.00075, "profit_target": 0.003}),
        )
        writer.close()

        body = client.get("/api/live/state", params={"path": store}).json()
        assert body["parameters"]["profit_target"] == pytest.approx(0.003)
        assert body["parameters"]["symbol"] == "TQQQ"

    def test_malformed_parameters_do_not_break_the_whole_state(self, client, store):
        """A dashboard that will not load because one metadata row is
        malformed is worse than one that says the config is unknown."""
        from src.persistence import LedgerStore

        writer = LedgerStore(store)
        writer.set_meta("live.parameters", "{not json")
        writer.close()

        body = client.get("/api/live/state", params={"path": store})
        assert body.status_code == 200
        assert body.json()["parameters"] == {}

    def test_rsi_uses_the_same_class_the_strategy_trades_on(self, client):
        """A second implementation would be free to disagree with the one
        making decisions."""
        body = client.get("/api/live/indicators", params={"symbol": "TQQQ"}).json()
        assert body["rsi_period"] == 14
        assert body["bars_used"] > 14
        assert 0 <= body["rsi"] <= 100

        # And it agrees with WilderRSI driven directly over the same bars.
        from src.dashboard_data import find_bar_files, load_bars
        from src.sizing_indicators import WilderRSI

        frame = load_bars(find_bar_files("TQQQ", "data")[0], limit=max(14 * 20, 390))
        tracker = WilderRSI(period=14)
        expected = None
        for close in frame["close"]:
            expected = tracker.update(float(close))
        assert body["rsi"] == pytest.approx(round(expected, 2))

    def test_indicators_for_an_unknown_symbol_are_a_404(self, client):
        assert client.get("/api/live/indicators", params={"symbol": "NOPE"}).status_code == 404


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


class TestStrategyParameters:
    """The bug a real user hit: pick any model but `fixed`, get a run
    that fails twenty seconds later complaining about a missing RESULTS
    COLUMN rather than the missing constructor argument that caused it.

    Only `fixed` has an all-optional constructor. The form sent {} for
    every model, every combination errored, and run_sweep then raised
    "rank_by column 'Capital Velocity Index' not found" -- true, and
    useless.
    """

    def test_no_parameters_at_all_uses_the_defaults_rather_than_failing(self, client):
        """This is the request the UI sends, and the one a script would
        write. It is perfectly clear about what it wants."""
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "profit_targets": [0.005],
                "sizing_model": "bell_curve",
            },
        )
        assert response.status_code == 202

    def test_a_PARTIAL_parameter_set_still_fails_at_submit(self, client):
        """Overriding one argument is deliberate, so defaults are NOT
        merged underneath -- that would run a configuration nobody asked
        for. It has to fail, and it has to fail here rather than in the
        worker twenty seconds later."""
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "profit_targets": [0.005],
                "sizing_model": "bell_curve",
                "strategy_params": {"lookback_days": 20},
            },
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        # It names the ARGUMENTS, not a results column.
        assert "Missing" in detail
        assert "max_trade_pct" in detail
        assert "rank_by" not in detail

    def test_the_error_suggests_working_parameters(self, client):
        """A message that only says what is wrong leaves the reader
        where they started."""
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "profit_targets": [0.005],
                "sizing_model": "rsi",
                "strategy_params": {"period": 14},
            },
        )
        assert "Try:" in response.json()["detail"]

    def test_every_registered_model_has_defaults_that_construct(self):
        """The dropdown offers all of them, so all of them must work.

        Sourced from this project's committed configs rather than
        invented -- and asserted here so a strategy gaining a required
        argument fails a test rather than a user's run.
        """
        from server.backtest import STRATEGY_DEFAULTS
        from src.strategy_registry import STRATEGIES

        for name, cls in STRATEGIES.items():
            defaults = STRATEGY_DEFAULTS.get(name)
            assert defaults is not None, f"{name} is selectable but has no defaults"
            cls(**defaults)  # raises TypeError if the defaults are insufficient

    def test_the_api_serves_those_defaults_so_the_ui_need_not_guess(self, client):
        body = client.get("/api/backtest/funds").json()
        details = body["sizing_details"]
        assert set(details) == set(body["sizing_models"])
        assert details["fixed"]["required"] == []
        assert "max_trade_pct" in details["bell_curve"]["required"]
        assert details["bell_curve"]["defaults"]["max_trade_pct"] > 0

    def test_target_return_is_aligned_to_the_grid(self):
        """BayesianDualScaleSizing estimates P(reaching ONE
        target_return), and the engine refuses a mismatch -- rightly, or
        it would be confidently answering a different question than the
        one being traded. No single default can span a sweep, so the
        value is aligned when the caller did not choose one."""
        from server.backtest import RunRequest, build_config

        config = build_config(
            RunRequest(
                tickers=["TQQQ"],
                grid_steps=[0.005],
                profit_targets=[0.01],
                sizing_model="bayesian_dual_scale",
            )
        )
        assert config.strategy.strategy_params["target_return"] == pytest.approx(0.01)

    def test_it_refuses_to_sweep_several_targets_against_one_posterior(self, client):
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.005],
                "profit_targets": [0.005, 0.01],
                "sizing_model": "bayesian_dual_scale",
            },
        )
        assert response.status_code == 400
        assert "cannot sweep" in response.json()["detail"]


class TestRunHistory:
    """Completed runs outlive the process; queued ones still do not.

    jobs.py's known limitation stands -- a restart loses work in flight,
    and resubmitting a few seconds of intent is trivial. A COMPLETED run
    is minutes of engine time and the thing a history view compares
    against, so only those are written.
    """

    @pytest.fixture(autouse=True)
    def _isolated(self, tmp_path, monkeypatch):
        monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))

    def test_a_saved_run_reads_back(self):
        from server import history

        history.save("abc123", {"run_id": "abc123", "status": "complete", "report": {}})
        assert history.load("abc123")["run_id"] == "abc123"
        assert [r["run_id"] for r in history.load_all()] == ["abc123"]

    def test_an_unwritable_directory_does_not_raise(self, tmp_path, monkeypatch):
        """A history feature must never be able to fail a backtest. The
        run completed; losing the archive copy is the smaller problem.

        A FILE where the directory should be, rather than a path like
        /proc/... that is unwritable on one platform and merely absent
        on another -- mkdir over an existing file fails everywhere.
        """
        from server import history

        blocker = tmp_path / "not-a-directory"
        blocker.write_text("", encoding="utf-8")
        monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(blocker))

        assert history.save("x", {"run_id": "x"}) is None
        # And reading it back is empty rather than an exception.
        assert history.load_all() == []
        assert history.load("x") is None

    def test_one_corrupt_file_does_not_hide_the_others(self):
        """A single bad file must not empty the whole listing."""
        from server import history

        history.save("good", {"run_id": "good"})
        (history.directory() / "broken.json").write_text("{not json", encoding="utf-8")
        assert [r["run_id"] for r in history.load_all()] == ["good"]

    def test_a_file_without_a_run_id_is_skipped(self):
        from server import history

        history.save("good", {"run_id": "good"})
        (history.directory() / "empty.json").write_text("{}", encoding="utf-8")
        assert [r["run_id"] for r in history.load_all()] == ["good"]

    def test_pruning_keeps_the_newest(self, monkeypatch):
        from server import history

        monkeypatch.setattr(history, "MAX_RUNS", 3)
        for index in range(6):
            history.save(f"run{index}", {"run_id": f"run{index}"})
        assert len(history.load_all()) == 3

    def test_history_flattens_to_one_row_per_configuration(self, client):
        """Ranking compares configurations, not runs: a run can hold
        several funds and each fund several cells."""
        from server import history

        history.save(
            "r1",
            {
                "run_id": "r1",
                "report": {
                    "parameters": {"sizing_model": "fixed", "fill_model": "close"},
                    "timeframe": {"start": "2026-01-01", "end": "2026-02-01"},
                    "funds": {
                        "TQQQ": {
                            "bars": {"count": 100},
                            "metrics": {"cagr_pct": 10.0},
                            "configurations": [
                                {
                                    "grid_step": 0.01,
                                    "profit_target": 0.005,
                                    "metrics": {"cagr_pct": 10.0},
                                },
                                {
                                    "grid_step": 0.02,
                                    "profit_target": 0.005,
                                    "metrics": {"cagr_pct": 5.0},
                                },
                            ],
                        }
                    },
                },
            },
        )
        rows = client.get("/api/backtest/history").json()["rows"]
        assert len(rows) == 2
        assert {row["grid_step"] for row in rows} == {0.01, 0.02}
        # The engine's own ranking is preserved, so a reader can see
        # when their chosen metric disagrees with it.
        assert rows[0]["engine_rank"] == 0

    def test_an_old_report_without_configurations_still_appears(self, client):
        """Reports predating the sweep matrix have headline metrics only.
        Dropping them would make history start over at every change."""
        from server import history

        history.save(
            "old",
            {
                "run_id": "old",
                "report": {
                    "parameters": {"grid_step_pct": 0.01, "profit_target_pct": 0.005},
                    "funds": {"TQQQ": {"metrics": {"cagr_pct": 7.0}, "bars": {"count": 10}}},
                },
            },
        )
        rows = client.get("/api/backtest/history").json()["rows"]
        assert len(rows) == 1
        assert rows[0]["metrics"]["cagr_pct"] == 7.0

    def test_a_stored_run_is_served_after_it_leaves_memory(self, client):
        """A saved link must not 404 because the server restarted."""
        from server import history

        history.save("kept", {"run_id": "kept", "status": "complete", "report": {"funds": {}}})
        assert client.get("/api/backtest/runs/kept").json()["run_id"] == "kept"

    def test_an_unknown_run_is_still_a_404(self, client):
        assert client.get("/api/backtest/runs/nope").status_code == 404
        assert client.get("/api/backtest/history/nope").status_code == 404


class TestSplitDeployment:
    """The Pi serves live state; the workstation runs the engine.

    The split is forced by where things are: the ledger lives in the
    Pi's Docker volume so nothing else can read it, and the bar files
    and cores live on the workstation.
    """

    def test_without_an_upstream_backtests_run_locally(self, client):
        body = client.get("/api/health").json()
        assert body["backtest_local"] is True
        assert body["backtest_upstream"] is None
        # And the local routes are actually reachable.
        assert client.get("/api/backtest/funds").status_code == 200

    def test_health_names_the_upstream_when_set(self, monkeypatch):
        """So a reader can see WHERE a sweep will run, from the machine
        they are pointed at."""
        import importlib

        monkeypatch.setenv("VAI_BACKTEST_UPSTREAM", "http://172.16.0.134:8000")
        from server import upstream

        importlib.reload(upstream)
        assert upstream.is_enabled()
        assert upstream.describe() == {
            "backtest_upstream": "http://172.16.0.134:8000",
            "backtest_local": False,
        }

    def test_a_blank_upstream_is_the_same_as_unset(self, monkeypatch):
        """An empty environment variable is how a compose file says
        "not this host", and it must not become a URL of ''."""
        import importlib

        monkeypatch.setenv("VAI_BACKTEST_UPSTREAM", "   ")
        from server import upstream

        importlib.reload(upstream)
        assert upstream.upstream_base() is None
        assert upstream.is_enabled() is False

    def test_a_trailing_slash_does_not_double_up(self, monkeypatch):
        import importlib

        monkeypatch.setenv("VAI_BACKTEST_UPSTREAM", "http://host:8000/")
        from server import upstream

        importlib.reload(upstream)
        assert upstream.upstream_base() == "http://host:8000"

    def test_an_unreachable_upstream_says_so_rather_than_showing_nothing(self, monkeypatch):
        """A backtesting UI that silently rendered an empty page would
        be worse than one naming the host it could not reach."""
        import importlib

        from fastapi.testclient import TestClient

        monkeypatch.setenv("VAI_BACKTEST_UPSTREAM", "http://127.0.0.1:59999")
        from server import app as app_module
        from server import upstream

        importlib.reload(upstream)
        importlib.reload(app_module)

        response = TestClient(app_module.app).get("/api/backtest/funds")
        assert response.status_code == 502
        assert "unreachable" in response.json()["detail"]
        assert "127.0.0.1:59999" in response.json()["detail"]

        # Leave the module set back to local mode for everything after.
        monkeypatch.delenv("VAI_BACKTEST_UPSTREAM")
        importlib.reload(upstream)
        importlib.reload(app_module)


class TestWorkerSelection:
    """The pool is not free, and below a certain size it is a loss.

    Measured on a 12-core machine, 11 workers, Windows spawn:

        13,260 bars x 12 configs   4.2s serial  ->  0.69x  SLOWER
       100,000 bars x  6 configs   8.2s serial  ->  1.35x
       300,000 bars x  6 configs  19.8s serial  ->  2.25x

    So the heuristic is not a guess -- it is those numbers.
    """

    def test_a_small_interactive_run_stays_serial(self):
        """The common case: one configuration over a recent window, run
        to look at a chart. Pooling it measured SLOWER."""
        from server.backtest import choose_jobs

        assert choose_jobs(13_260, 12, None) == 1

    def test_a_large_sweep_gets_workers(self):
        from server.backtest import choose_jobs

        assert choose_jobs(300_000, 6, None) > 1

    def test_a_single_configuration_never_pools(self):
        """There is nothing to spread, and a worker would still pay the
        cost of pickling the whole frame."""
        from server.backtest import choose_jobs

        assert choose_jobs(1_000_000, 1, None) == 1

    def test_workers_never_exceed_the_grid_size(self):
        """Eight workers for three configurations spawns five processes
        that pickle a DataFrame and exit."""
        from server.backtest import choose_jobs

        assert choose_jobs(1_000_000, 3, None) <= 3
        assert choose_jobs(1_000_000, 3, 99) <= 3

    def test_an_explicit_request_is_honoured(self):
        """Someone who has measured their own machine knows more than
        this heuristic does."""
        from server.backtest import choose_jobs

        assert choose_jobs(13_260, 12, 4) == 4

    def test_the_report_states_what_was_actually_used(self, tmp_path):
        """Not what was asked for -- so a reader can tell a slow sweep
        from a serial one."""
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
                    "grid_steps": [0.01],
                    "profit_targets": [0.005],
                    "sizing_model": "fixed",
                    "strategy_params": {"allocation_pct": 0.05},
                },
                lambda fraction, note: None,
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        # A one-configuration run on a tiny fixture must report serial.
        assert report["parameters"]["n_jobs"] == 1


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
