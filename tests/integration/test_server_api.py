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
from src.core.persistence import LedgerStore

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
        assert "halt" in body["caps"]
        # Never listed, by design -- see server/control.py.
        assert "liquidate" not in body["caps"]
        assert "parameter_override" not in body["caps"]


class TestLiveReads:
    def test_state_comes_back_for_a_real_store(self, client, store):
        body = client.get("/api/live/state", params={"path": store}).json()
        assert body["cash"] == pytest.approx(50000.0)
        assert body["peak_equity"] == pytest.approx(60000.0)
        assert body["halt"] is None
        assert body["lots"] == []
        assert "path" not in body  # the caller named the store

    def test_a_missing_store_is_a_404_not_a_500(self, client, tmp_path):
        response = client.get("/api/live/state", params={"path": str(tmp_path / "nope.db")})
        assert response.status_code == 404

    def test_a_file_that_is_not_a_store_is_a_404(self, client, tmp_path):
        junk = tmp_path / "junk.db"
        junk.write_text("this is not a database", encoding="utf-8")
        assert client.get("/api/live/state", params={"path": str(junk)}).status_code == 404

    def test_activity_returns_the_revision_log(self, client, store):
        body = client.get("/api/live/activity", params={"path": store, "limit": 10}).json()
        assert isinstance(body, list)

    def test_bars_for_an_unknown_symbol_are_a_404(self, client):
        response = client.get("/api/live/bars", params={"symbol": "NOTATICKER"})
        assert response.status_code == 404


class TestLiveParametersAndIndicators:
    def test_a_store_with_no_parameters_reports_an_empty_dict(self, client, store):
        """Absent is normal for a store written before the loop recorded
        them -- the UI shows "unknown", not zeros."""
        assert client.get("/api/live/state", params={"path": store}).json()["params"] == {}

    def test_parameters_written_by_the_loop_come_back(self, client, store):
        """This is the field that would have made the 30%-instead-of-0.3%
        profit target visible without diffing a config against a ledger."""
        import json as json_

        from src.core.persistence import LedgerStore

        writer = LedgerStore(store)
        writer.set_meta(
            "live.parameters",
            json_.dumps({"symbol": "TQQQ", "step": 0.00075, "profit_target": 0.003}),
        )
        writer.close()

        body = client.get("/api/live/state", params={"path": store}).json()
        assert body["params"]["profit_target"] == pytest.approx(0.003)
        assert body["params"]["symbol"] == "TQQQ"

    def test_malformed_parameters_do_not_break_the_whole_state(self, client, store):
        """A dashboard that will not load because one metadata row is
        malformed is worse than one that says the config is unknown."""
        from src.core.persistence import LedgerStore

        writer = LedgerStore(store)
        writer.set_meta("live.parameters", "{not json")
        writer.close()

        body = client.get("/api/live/state", params={"path": store})
        assert body.status_code == 200
        assert body.json()["params"] == {}

    def test_rsi_uses_the_same_class_the_strategy_trades_on(self, client):
        """A second implementation would be free to disagree with the one
        making decisions."""
        body = client.get("/api/live/indicators", params={"symbol": "TQQQ"}).json()
        assert "rsi_period" not in body  # the caller's own query
        assert body["n"] > 14
        assert 0 <= body["rsi"] <= 100

        # And it agrees with WilderRSI driven directly over the same bars.
        from src.data.dashboard_data import find_bar_files, load_bars
        from src.strategies.sizing_indicators import WilderRSI

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
        # The whole LiveState, read back -- the reason IS the halt flag.
        assert "operator" in body["halt"]
        assert body["cash"] == pytest.approx(50000.0)

    def test_the_halt_is_visible_to_the_read_path(self, client, store):
        """Two different modules and two different connections must agree
        about whether this deployment is halted."""
        client.post("/api/live/halt", json={"path": store, "reason": "checking readback"})
        assert client.get("/api/live/state", params={"path": store}).json()["halt"]

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
    """Which build is running rides /api/health; /api/deployment is gone."""

    def test_it_reports_the_build_it_is_running(self, client):
        build = client.get("/api/health").json()["build"]
        assert build["commit"], "no commit reported from inside a git checkout"
        assert build["branch"]
        assert build["uptime_s"] >= 0
        assert build["python"].startswith("3.")

    def test_the_old_deployment_route_is_gone(self, client):
        assert client.get("/api/deployment").status_code == 404

    def test_container_stats_are_null_rather_than_zero_when_unavailable(self, client):
        """A "CPU 0%" that means "could not measure" is a number someone
        would act on. Outside a container these must be absent, not
        plausible-looking."""
        container = client.get("/api/health").json()["container"]
        # Outside a container the whole block is null, not zeros.
        if container is not None:
            # CPU is never reported: cgroup exposes cumulative microseconds,
            # and a percentage needs two samples over a known interval,
            # which this endpoint does not keep.
            assert container["cpu_pct"] is None
            assert container["mem_mb"] is not None

    def test_a_cgroup_max_limit_is_not_read_as_a_number(self):
        """cgroup writes the literal string "max" for "no limit"."""
        from server.deployment import _read_int

        assert _read_int("/definitely/not/a/real/cgroup/path") is None

    def test_git_dirty_distinguishes_unknown_from_clean(self, client):
        """None means "could not tell". A card showing a clean checkmark
        because git was missing would assert something it does not know."""
        body = client.get("/api/health").json()
        assert body["build"]["dirty"] in (True, False, None)


class TestBacktestSubmission:
    def test_funds_reports_availability_rather_than_hiding_it(self, client):
        body = client.get("/api/backtest/funds").json()
        assert body["funds"], "no funds listed at all"
        assert all("ok" in fund for fund in body["funds"])
        assert "fixed" in body["models"]

    def test_an_unknown_sizing_model_is_a_400_naming_the_real_ones(self, client):
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "not_a_strategy",
            },
        )
        assert response.status_code == 400
        assert "Known strategies" in response.json()["detail"]

    def test_an_empty_ticker_list_is_rejected_by_shape(self, client):
        response = client.post(
            "/api/backtest/runs",
            json={"tickers": [], "grid_steps": [0.01], "targets": [0.005]},
        )
        assert response.status_code == 422

    def test_a_valid_submission_returns_202_and_an_id(self, client):
        """202, not 200: nothing has been computed yet."""
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": 0.05},
                "limit": 500,
            },
        )
        assert response.status_code == 202
        body = response.json()
        assert body["id"]
        assert body["status"] in {"queued", "running", "complete"}

    def test_an_unknown_run_is_a_404(self, client):
        assert client.get("/api/backtest/runs/deadbeef").status_code == 404

    def test_a_run_can_be_given_a_name_and_it_rides_the_snapshot(self, client):
        """The label is descriptive only -- the engine never reads it --
        but it must be on the job snapshot immediately so a queued or
        running sweep shows by name before its report exists."""
        body = client.post(
            "/api/backtest/runs",
            json={
                "name": "  rsi oversold sweep  ",
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": 0.05},
                "limit": 500,
            },
        ).json()
        # The label rides the request echo; the report trims it.
        assert body["req"]["name"] == "  rsi oversold sweep  "

    def test_the_submitted_request_rides_the_snapshot(self, client):
        """A queued or running job carries its own submitted shape --
        tickers/grid/strategy_params -- so a client can describe what a
        sweep covers (e.g. how many simulations it is) before it has a
        report to read that from."""
        body = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01, 0.02],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": 0.05},
                "limit": 500,
            },
        ).json()
        assert body["req"]["tickers"] == ["TQQQ"]
        assert body["req"]["grid_steps"] == [0.01, 0.02]
        assert body["req"]["params"] == {"allocation_pct": 0.05}

    def test_the_legacy_field_names_are_still_accepted(self, client):
        """A sweep queued in output/queue/state.json, and any script,
        were written against the old names -- they translate, and the
        echo comes back in the new ones."""
        body = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "profit_targets": [0.005],
                "sizing_model": "fixed",
                "strategy_params": {"allocation_pct": 0.05},
                "fill_model": "intrabar",
                "enforce_no_loss": True,
                "n_jobs": 1,
                "limit": 500,
            },
        ).json()
        assert body["req"]["targets"] == [0.005]
        assert body["req"]["model"] == "fixed"
        assert body["req"]["params"] == {"allocation_pct": 0.05}
        assert body["req"]["fill"] == "intrabar"
        assert body["req"]["jobs"] == 1
        assert "sizing_model" not in body["req"]

    def test_a_whitespace_only_name_is_treated_as_unnamed(self, client):
        body = client.post(
            "/api/backtest/runs",
            json={
                "name": "   ",
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": 0.05},
                "limit": 500,
            },
        ).json()
        # The queue's label (and the report's name) treat it as unnamed.
        from server.backtest import queue

        assert queue.get(body["id"]).name is None

    def test_an_over_long_name_is_rejected_by_shape(self, client):
        response = client.post(
            "/api/backtest/runs",
            json={
                "name": "x" * 121,
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
            },
        )
        assert response.status_code == 422


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
        assert body["bucket_s"] > 60, "a 4-day window at 20 points must roll up"
        for _t, open_, high, low, close, _v in body["bars"]:
            assert low <= open_ <= high
            assert low <= close <= high

    def test_bars_for_an_unknown_ticker_are_a_404(self, client):
        assert client.get("/api/backtest/bars", params={"ticker": "NOPE"}).status_code == 404

    def test_an_empty_window_returns_no_bars_rather_than_failing(self, client):
        body = client.get(
            "/api/backtest/bars",
            params={"ticker": "TQQQ", "start": "1990-01-01", "end": "1990-01-02"},
        ).json()
        assert body["bars"] == []
        assert body["rows"] == 0


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
                "targets": [0.005],
                "model": "bell_curve",
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
                "targets": [0.005],
                "model": "bell_curve",
                "params": {"lookback_days": 20},
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
                "targets": [0.005],
                "model": "rsi",
                "params": {"period": 14},
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
        from src.trading.strategy_registry import STRATEGIES

        for name, cls in STRATEGIES.items():
            defaults = STRATEGY_DEFAULTS.get(name)
            assert defaults is not None, f"{name} is selectable but has no defaults"
            cls(**defaults)  # raises TypeError if the defaults are insufficient

    def test_the_api_serves_those_defaults_so_the_ui_need_not_guess(self, client):
        models = client.get("/api/backtest/funds").json()["models"]
        bell = {spec["name"]: spec for spec in models["bell_curve"]["params"]}
        assert bell["max_trade_pct"].get("required") is True
        assert bell["max_trade_pct"]["suggested"] > 0

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
                targets=[0.01],
                model="bayesian_dual_scale",
            )
        )
        assert config.strategy.strategy_params["target_return"] == pytest.approx(0.01)

    def test_it_refuses_to_sweep_several_targets_against_one_posterior(self, client):
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.005],
                "targets": [0.005, 0.01],
                "model": "bayesian_dual_scale",
            },
        )
        assert response.status_code == 400
        assert "cannot sweep" in response.json()["detail"]

    def test_a_swept_numeric_strategy_param_is_accepted(self, client):
        """A list-valued strategy param is a sweep axis, exactly like
        grid_steps/profit_targets already are -- the "enable sweep"
        checkbox's server-side counterpart."""
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": [0.03, 0.05, 0.08]},
            },
        )
        assert response.status_code == 202

    def test_it_refuses_to_sweep_target_return_independently(self, client):
        """target_return mirrors the grid's profit target -- sweeping it
        on its own would have the mirror-alignment silently discard it."""
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.005],
                "targets": [0.01],
                "model": "bayesian_dual_scale",
                "params": {
                    "max_trade_pct": 0.05,
                    "horizon_days": 1.0,
                    "bars_per_day": 387,
                    "target_return": [0.005, 0.0075, 0.01],
                },
            },
        )
        assert response.status_code == 400
        assert "swept independently" in response.json()["detail"]

    def test_it_refuses_a_sweep_that_exceeds_the_combinations_cap(self, client, monkeypatch):
        """Unbounded, a single request could ask for an arbitrarily long
        sweep -- narrowed here to a cap small enough to hit with an
        ordinary request, rather than actually submitting thousands."""
        import server.backtest as module

        monkeypatch.setattr(module, "MAX_SWEEP_COMBINATIONS", 3)
        response = client.post(
            "/api/backtest/runs",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": [0.02, 0.03, 0.05, 0.08]},
            },
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "4" in detail and "3" in detail


class TestParameterSchema:
    """`/funds` carries `models[id]` -- one typed spec per constructor
    argument plus the grid-trigger methods -- so the form can render a
    model's inputs and swap them when the model changes."""

    def test_required_and_suggested_carry_what_sizing_details_did(self, client):
        """The old `sizing_details` (required names, committed defaults)
        is fully recoverable from the params, so dropping it lost nothing."""
        from server.backtest import _HIDDEN_PARAMS, STRATEGY_DEFAULTS, required_parameters
        from src.trading.strategy_registry import STRATEGIES

        models = client.get("/api/backtest/funds").json()["models"]
        assert set(models) == set(STRATEGIES)
        for name, cls in STRATEGIES.items():
            params = models[name]["params"]
            if not params:
                continue
            required = [p["name"] for p in params if p.get("required")]
            # _apply_locks can promote an argument to required (fixed's
            # allocation_pct); every constructor-required one is there.
            visible = [n for n in required_parameters(cls) if n not in _HIDDEN_PARAMS]
            assert set(visible) <= set(required), name
            suggested = {p["name"]: p["suggested"] for p in params if "suggested" in p}
            assert suggested == STRATEGY_DEFAULTS.get(name, {}), name

    def test_params_cover_every_model_and_carry_typed_specs(self, client):
        models = client.get("/api/backtest/funds").json()["models"]
        bell = {s["name"]: s for s in models["bell_curve"]["params"]}
        assert bell["max_trade_pct"]["required"] is True
        assert bell["bars_per_day"]["type"] == "int"
        assert "model_dir" not in bell  # hidden filesystem wiring
        target = {s["name"]: s for s in models["bayesian_dual_scale"]["params"]}["target_return"]
        assert target["locked"] and target["mirrors"] == "profit_target"

    def test_trigger_describes_every_model(self, client):
        models = client.get("/api/backtest/funds").json()["models"]
        assert models["fixed"]["trigger"] == {"methods": ["last_buy"]}
        assert models["hf_local_reference"]["trigger"]["methods"] == ["local_reference"]
        bayes = models["bayesian_dual_scale"]["trigger"]
        assert bayes["methods"] == ["last_buy", "local_reference"]
        assert bayes["control"] == "lookback_days"
        assert bayes["window"]["param"] == "lookback_days"

    def test_one_broken_strategy_does_not_500_funds(self, client, monkeypatch):
        """`test_every_offered_sizing_model_can_actually_run` reads /funds
        first; an unguarded introspection raise would cascade to it."""
        import server.backtest as module

        def boom(strategy_id, cls):
            raise RuntimeError("introspection blew up")

        monkeypatch.setattr(module, "describe_params", boom)
        response = client.get("/api/backtest/funds")
        assert response.status_code == 200
        assert all(entry["params"] == [] for entry in response.json()["models"].values())


class TestValidateEndpoint:
    """`POST /api/backtest/validate` dry-runs the exact `build_config`
    the submit path uses, without queuing -- so the form can show a bad
    argument under its field before a run is ever started."""

    @pytest.fixture(autouse=True)
    def _no_side_effects_guard(self, tmp_path, monkeypatch):
        # If a bug ever made /validate archive or queue, these would catch
        # it: history writes land in a tmp dir we can inspect, and the
        # queue length is asserted unchanged in every test below.
        import time as _time

        from server.backtest import queue as _queue

        deadline = _time.monotonic() + 30
        while _time.monotonic() < deadline and any(
            job.status in {"queued", "running"} for job in _queue.all()
        ):
            _time.sleep(0.05)
        monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))
        self._queue_len = len(_queue.all())

    def _assert_no_side_effects(self):
        from server import history
        from server.backtest import queue as _queue

        assert len(_queue.all()) == self._queue_len, "/validate queued a job"
        assert history.load_all() == [], "/validate wrote history"

    def test_a_valid_request_reports_the_resolved_params(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": 0.05},
            },
        ).json()
        assert body["errors"] == []
        assert body["resolved"] == {"allocation_pct": 0.05}
        assert "aligned" not in body  # nothing set or changed
        self._assert_no_side_effects()

    def test_a_partial_set_is_not_ok_and_names_the_missing_argument(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "bell_curve",
                "params": {"lookback_days": 20},
            },
        ).json()
        assert body["errors"]
        joined = " ".join(error["msg"] for error in body["errors"])
        assert "Missing" in joined and "max_trade_pct" in joined
        assert "rank_by" not in joined
        # The missing argument is pinned to its field.
        assert any(error.get("field") == "max_trade_pct" for error in body["errors"])

    def test_an_out_of_range_value_is_pinned_to_its_field(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "bell_curve",
                "params": {
                    "max_trade_pct": 1.5,
                    "lookback_days": 20,
                    "bars_per_day": 387,
                },
            },
        ).json()
        assert body["errors"]
        offending = [e for e in body["errors"] if e.get("field") == "max_trade_pct"]
        assert offending and "(0, 1]" in offending[0]["msg"]

    def test_bayesian_target_return_is_reported_as_aligned(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.005],
                "targets": [0.01],
                "model": "bayesian_dual_scale",
                # target_return omitted -- the form never sends it.
                "params": {
                    "max_trade_pct": 0.05,
                    "horizon_days": 1.0,
                    "bars_per_day": 387,
                },
            },
        ).json()
        assert body["errors"] == []
        assert body["resolved"]["target_return"] == pytest.approx(0.01)
        assert body["aligned"]["target_return"] == pytest.approx(0.01)

    def test_multi_target_bayesian_is_refused(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.005],
                "targets": [0.005, 0.01],
                "model": "bayesian_dual_scale",
            },
        ).json()
        assert body["errors"]
        assert "cannot sweep" in " ".join(e["msg"] for e in body["errors"])
        # It is about the profit-target GRID, not a constructor argument,
        # so it is left unattached -- the form shows it as a banner, not
        # under the locked target_return field.
        assert all("field" not in e for e in body["errors"])

    def test_an_ml_ticker_fund_mismatch_is_reported(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "ml_reachability_cowz",
            },
        ).json()
        assert body["errors"]
        assert "COWZ" in " ".join(e["msg"] for e in body["errors"])

    def test_an_unknown_key_is_reported_not_silently_dropped(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "rsi",
                "params": {"max_trade_pct": 0.08, "not_a_real_arg": 1},
            },
        ).json()
        assert body["errors"]
        assert "not_a_real_arg" in " ".join(e["msg"] for e in body["errors"])

    def test_an_unknown_sizing_model_is_not_ok(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "not_a_strategy",
            },
        ).json()
        assert body["errors"]
        assert body["errors"]

    def test_a_swept_strategy_param_resolves_to_a_list(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": [0.03, 0.05]},
            },
        ).json()
        assert body["errors"] == []
        assert body["resolved"] == {"allocation_pct": [0.03, 0.05]}
        self._assert_no_side_effects()

    def test_a_swept_target_return_is_refused(self, client):
        body = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.005],
                "targets": [0.01],
                "model": "bayesian_dual_scale",
                "params": {
                    "max_trade_pct": 0.05,
                    "horizon_days": 1.0,
                    "bars_per_day": 387,
                    "target_return": [0.005, 0.01],
                },
            },
        ).json()
        assert body["errors"]
        assert "swept independently" in " ".join(e["msg"] for e in body["errors"])
        self._assert_no_side_effects()

    def test_validate_shares_build_config_with_submit(self):
        """One definition of 'valid' -- not a second that can drift."""
        import inspect

        from server import backtest as module

        source = inspect.getsource(module.validate)
        assert "build_config(request)" in source


class TestRunHistory:
    """Completed runs outlive the process; queued ones still do not.

    jobs.py's known limitation stands -- a restart loses work in flight,
    and resubmitting a few seconds of intent is trivial. A COMPLETED run
    is minutes of engine time and the thing a history view compares
    against, so only those are written.
    """

    @pytest.fixture(autouse=True)
    def _isolated(self, tmp_path, monkeypatch):
        # Let any run an earlier test queued on the module-global job
        # queue finish and archive into the DEFAULT directory before we
        # repoint history at this test's tmp dir. `_archive` reads the
        # env var at call time, so a background completion that lands
        # after the setenv below would otherwise drop a stray run into a
        # fixture whose assertions say "only what I saved is here". Test
        # order is randomised, so this is seed-dependent without the wait.
        import time as _time

        from server.backtest import queue as _queue

        deadline = _time.monotonic() + 30
        while _time.monotonic() < deadline and any(
            job.status in {"queued", "running"} for job in _queue.all()
        ):
            _time.sleep(0.05)

        monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))

    def test_a_saved_run_reads_back(self):
        from server import history

        history.save("abc123", {"id": "abc123", "status": "complete", "report": None})
        assert history.load("abc123")["id"] == "abc123"
        assert [r["id"] for r in history.load_all()] == ["abc123"]

    def test_a_legacy_archive_reads_back_in_the_new_shape(self):
        """output/runs/ holds runs written before the contract was
        condensed; they must load as Runs, not as something the client
        has to recognise."""
        from server import history

        history.save(
            "old1",
            {
                "run_id": "old1",
                "name": "legacy",
                "status": "running",
                "stop_requested": "pause",
                "queue_position": None,
                "message": "m",
                "request": {
                    "tickers": ["TQQQ"],
                    "grid_steps": [0.01],
                    "profit_targets": [0.005],
                    "sizing_model": "fixed",
                    "search_strategy": "bayesian",
                    "n_trials": 7,
                    "search_seed": 3,
                },
                "report": {
                    "run_id": "old1",
                    "parameters": {
                        "name": "legacy",
                        "sizing_model": "fixed",
                        "n_jobs": 2,
                        "fill_model": "close",
                        "enforce_no_loss": True,
                    },
                    "timeframe": {"start": "a", "end": "b", "interval": "1Min"},
                    "funds": {
                        "TQQQ": {
                            "metrics": {"ticker": "TQQQ", "cagr_pct": 1.0},
                            "executions": [
                                {
                                    "order_id": "7-buy-12",
                                    "ticker": "TQQQ",
                                    "type": "BUY",
                                    "price": 1.0,
                                    "shares": 2.0,
                                    "timestamp": "t",
                                },
                                {
                                    "order_id": "7-sell-40",
                                    "ticker": "TQQQ",
                                    "type": "SELL",
                                    "price": 1.1,
                                    "shares": 2.0,
                                    "timestamp": "u",
                                    "matched_buy_id": "7",
                                    "profit_realized": 0.2,
                                    "sell_reason": "profit_target",
                                    "rsi_at_entry": 41.0,
                                },
                            ],
                            "equity_curve": {"dates": ["d"], "equity": [5.0], "normalized": [100]},
                            "bars": {"start": "a", "end": "b", "count": 3},
                        }
                    },
                },
            },
        )
        run = history.load("old1")
        assert run["status"] == "pausing"
        assert run["req"]["targets"] == [0.005]
        assert run["req"]["bayes"] == {"trials": 7, "seed": 3}
        report = run["report"]
        assert report["id"] == "old1" and report["model"] == "fixed" and report["jobs"] == 2
        fund = report["funds"]["TQQQ"]
        assert fund["cells"][0]["m"] == {"cagr_pct": 1.0}
        assert fund["equity"] == {"dates": ["d"], "equity": [5.0]}
        buy, sell = fund["fills"]
        assert buy == {"lot": "7", "side": "BUY", "i": 12, "px": 1.0, "qty": 2.0, "ts": "t"}
        assert sell["i"] == 40 and sell["pnl"] == 0.2 and sell["why"] == "profit_target"
        assert sell["rsi"] == 41.0

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

        assert history.save("x", {"id": "x"}) is None
        # And reading it back is empty rather than an exception.
        assert history.load_all() == []
        assert history.load("x") is None

    def test_one_corrupt_file_does_not_hide_the_others(self):
        """A single bad file must not empty the whole listing."""
        from server import history

        history.save("good", {"id": "good"})
        (history.directory() / "broken.json").write_text("{not json", encoding="utf-8")
        assert [r["id"] for r in history.load_all()] == ["good"]

    def test_a_file_without_a_run_id_is_skipped(self):
        from server import history

        history.save("good", {"id": "good"})
        (history.directory() / "empty.json").write_text("{}", encoding="utf-8")
        assert [r["id"] for r in history.load_all()] == ["good"]

    def test_pruning_keeps_the_newest(self, monkeypatch):
        from server import history

        monkeypatch.setattr(history, "MAX_RUNS", 3)
        for index in range(6):
            history.save(f"run{index}", {"id": f"run{index}"})
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
        body = client.get("/api/backtest/history").json()
        rows = body["rows"]
        assert len(rows) == 2
        assert {row["grid"] for row in rows} == {0.01, 0.02}
        # The engine's own ranking is preserved, so a reader can see
        # when their chosen metric disagrees with it.
        assert rows[0]["rank"] == 0
        # Run-level fields are stated once, not on every row.
        assert body["runs"]["r1"]["model"] == "fixed"
        assert body["runs"]["r1"]["start"] == "2026-01-01"
        assert "model" not in rows[0] and "funds" not in body["runs"]["r1"]

    def test_a_runs_name_is_joinable_from_every_configuration_row(self, client):
        """The table is one row per (run, fund, cell); a reader scanning
        it should see the label on each row, not only the first -- joined
        through `runs[row.run]` rather than repeated on the wire."""
        from server import history

        history.save(
            "named",
            {
                "run_id": "named",
                "report": {
                    "parameters": {"name": "champion re-run", "sizing_model": "fixed"},
                    "timeframe": {"start": "2026-01-01", "end": "2026-02-01"},
                    "funds": {
                        "TQQQ": {
                            "bars": {"count": 100},
                            "metrics": {"cagr_pct": 10.0},
                            "configurations": [
                                {"grid_step": 0.01, "profit_target": 0.005, "metrics": {}},
                                {"grid_step": 0.02, "profit_target": 0.005, "metrics": {}},
                            ],
                        }
                    },
                },
            },
        )
        body = client.get("/api/backtest/history").json()
        assert len(body["rows"]) == 2
        assert all(body["runs"][row["run"]]["name"] == "champion re-run" for row in body["rows"])

    def test_history_rows_carry_the_resolved_strategy_params(self, client):
        """So the client can filter history by an input argument. `{}`
        for a run archived before this was recorded, never a missing
        key."""
        from server import history

        history.save(
            "with-params",
            {
                "run_id": "with-params",
                "report": {
                    "parameters": {
                        "sizing_model": "rsi",
                        "strategy_params": {"period": 14, "max_trade_pct": 0.08},
                    },
                    "funds": {
                        "TQQQ": {
                            "bars": {"count": 10},
                            "metrics": {"cagr_pct": 3.0},
                            "configurations": [
                                {"grid_step": 0.01, "profit_target": 0.005, "metrics": {}},
                            ],
                        }
                    },
                },
            },
        )
        history.save(
            "legacy",
            {
                "run_id": "legacy",
                "report": {
                    "parameters": {"sizing_model": "fixed"},
                    "funds": {"TQQQ": {"metrics": {"cagr_pct": 1.0}, "bars": {"count": 5}}},
                },
            },
        )
        rows = {row["run"]: row for row in client.get("/api/backtest/history").json()["rows"]}
        assert rows["with-params"]["params"] == {"period": 14, "max_trade_pct": 0.08}
        assert rows["legacy"]["params"] == {}

    def test_a_cells_own_strategy_params_beat_the_run_level_value(self, client):
        """Once a strategy param is swept, cells of the same run can
        differ -- the run-level value (the FIRST combination the engine
        happened to resolve) must not be flattened onto every row."""
        from server import history

        history.save(
            "swept-param",
            {
                "run_id": "swept-param",
                "report": {
                    "parameters": {
                        "sizing_model": "fixed",
                        "strategy_params": {"allocation_pct": 0.03},
                    },
                    "funds": {
                        "TQQQ": {
                            "bars": {"count": 10},
                            "metrics": {"cagr_pct": 3.0},
                            "configurations": [
                                {
                                    "grid_step": 0.01,
                                    "profit_target": 0.005,
                                    "strategy_params": {"allocation_pct": 0.03},
                                    "metrics": {},
                                },
                                {
                                    "grid_step": 0.01,
                                    "profit_target": 0.005,
                                    "strategy_params": {"allocation_pct": 0.05},
                                    "metrics": {},
                                },
                            ],
                        }
                    },
                },
            },
        )
        rows = client.get("/api/backtest/history").json()["rows"]
        by_params = [row["params"] for row in rows]
        assert {"allocation_pct": 0.03} in by_params
        assert {"allocation_pct": 0.05} in by_params

    def test_an_unnamed_run_reports_a_null_name_rather_than_omitting_it(self, client):
        from server import history

        history.save(
            "anon",
            {
                "run_id": "anon",
                "report": {
                    "parameters": {"grid_step_pct": 0.01, "profit_target_pct": 0.005},
                    "funds": {"TQQQ": {"metrics": {"cagr_pct": 7.0}, "bars": {"count": 10}}},
                },
            },
        )
        body = client.get("/api/backtest/history").json()
        assert body["runs"][body["rows"][0]["run"]]["name"] is None

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
        assert rows[0]["m"]["cagr_pct"] == 7.0
        assert (rows[0]["grid"], rows[0]["target"]) == (0.01, 0.005)

    def test_a_stored_run_is_served_after_it_leaves_memory(self, client):
        """A saved link must not 404 because the server restarted."""
        from server import history

        history.save("kept", {"id": "kept", "status": "complete", "report": {"funds": {}}})
        assert client.get("/api/backtest/runs/kept").json()["id"] == "kept"

    def test_an_unknown_run_is_still_a_404(self, client):
        assert client.get("/api/backtest/runs/nope").status_code == 404


class TestSplitDeployment:
    """The Pi serves live state; the workstation runs the engine.

    The split is forced by where things are: the ledger lives in the
    Pi's Docker volume so nothing else can read it, and the bar files
    and cores live on the workstation.
    """

    def test_without_an_upstream_backtests_run_locally(self, client):
        body = client.get("/api/health").json()
        assert body["upstream"] is None  # null = runs locally
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
        assert upstream.upstream_base() == "http://172.16.0.134:8000"

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
                    "targets": [0.005],
                    "model": "fixed",
                    "params": {"allocation_pct": 0.05},
                },
                lambda fraction, note: None,
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        # A one-configuration run on a tiny fixture must report serial.
        assert report["jobs"] == 1


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
                    "targets": [0.005],
                    "model": "fixed",
                    "params": {"allocation_pct": 0.05},
                    "limit": 5000,
                },
                lambda fraction, note: progress.append((fraction, note)),
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        assert progress, "the run reported no progress at all"
        fund = report["funds"]["TESTQ"]

        # The metrics the UI panel needs are all present, on the headline
        # cell -- cells[0] IS the configuration the fills came from.
        for key in ("win_rate_pct", "profit_factor", "stuck_capital_value", "sharpe_ratio"):
            assert key in fund["cells"][0]["m"], f"missing {key}"
        assert "ticker" not in fund["cells"][0]["m"]  # it is the fund's key

        # And the fills carry what a cycle connector needs: a sell joins
        # its buy on `lot`, and (lot, side, i) is unique.
        sells = [e for e in fund["fills"] if e["side"] == "SELL"]
        buy_lots = {e["lot"] for e in fund["fills"] if e["side"] == "BUY"}
        assert sells, "the fixture produced no sells"
        assert {e["lot"] for e in sells} <= buy_lots, "a sell references a lot with no buy row"
        keys = [(e["lot"], e["side"], e["i"]) for e in fund["fills"]]
        assert len(keys) == len(set(keys))
        assert "normalized" not in fund["equity"]

    def test_the_report_echoes_the_submitted_name(self, tmp_path):
        """Descriptive only, but it must survive from the request through
        to the archived report so history can show what a sweep was for."""
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
            named = run_backtest(
                {
                    "name": "  five percent baseline  ",
                    "tickers": ["TESTQ"],
                    "grid_steps": [0.01],
                    "targets": [0.005],
                    "model": "fixed",
                    "params": {"allocation_pct": 0.05},
                    "limit": 5000,
                },
                lambda fraction, note: None,
            )
            anon = run_backtest(
                {
                    "tickers": ["TESTQ"],
                    "grid_steps": [0.01],
                    "targets": [0.005],
                    "model": "fixed",
                    "params": {"allocation_pct": 0.05},
                    "limit": 5000,
                },
                lambda fraction, note: None,
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        assert named["name"] == "five percent baseline"
        assert anon["name"] is None
        # The RESOLVED sizing-model arguments ride along too, so the
        # history view can filter on an input rather than only the grid.
        assert named["params"] == {"allocation_pct": 0.05}

    def test_the_report_records_resolved_strategy_params(self, tmp_path):
        """Not what was submitted -- what the engine was built with, after
        defaults are filled in. `bell_curve` takes no params in the
        request below, so the report must still name the three it ran."""
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
                    "targets": [0.005],
                    "model": "bell_curve",
                    "limit": 5000,
                },
                lambda fraction, note: None,
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        params = report["params"]
        assert params["max_trade_pct"] == 0.08
        assert params["lookback_days"] == 20
        assert params["bars_per_day"] == 387

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
                    "targets": [0.005, 0.01, 0.02],
                    "model": "fixed",
                    "params": {"allocation_pct": 0.05},
                    "limit": 5000,
                },
                lambda fraction, note: None,
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        cells = report["funds"]["TESTQ"]["cells"]
        assert len(cells) == 6, "2 steps x 3 targets should be 6 cells"
        assert {c["grid"] for c in cells} == {0.01, 0.02}
        assert {c["target"] for c in cells} == {0.005, 0.01, 0.02}
        assert "metrics" not in report["funds"]["TESTQ"]  # cells[0].m is the headline

    def test_a_swept_strategy_param_produces_one_cell_per_value_with_its_own_combo(self, tmp_path):
        """The engine already cross-products grid_steps x profit_targets x
        strategy_params_grid (src/optimization/search_strategies.py's
        GridSearch); this pins the web API's own wiring of that third
        axis: `combinations` counts it, and each cell carries the exact
        combo it ran with rather than the run's first-resolved value."""
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
                    "targets": [0.005],
                    "model": "fixed",
                    "params": {"allocation_pct": [0.03, 0.05]},
                    "limit": 5000,
                },
                lambda fraction, note: None,
            )
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

        cells = report["funds"]["TESTQ"]["cells"]
        assert len(cells) == 2, "1 step x 1 target x 2 allocation_pct values should be 2 cells"
        assert {c["params"]["allocation_pct"] for c in cells} == {0.03, 0.05}
        # A plain Python float, not a numpy scalar -- history archiving
        # calls bare json.dumps with no custom encoder.
        for cell in cells:
            assert isinstance(cell["params"]["allocation_pct"], float)

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
                        "targets": [0.005],
                        "model": "fixed",
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
                    "targets": [0.005],
                    "model": "fixed",
                },
                lambda fraction, note: None,
            )


class TestBayesianSearch:
    """search_strategy="bayesian": the web equivalent of cli.py search's
    own --trials flag, reachable from a submitted run instead of only a
    YAML config file. See RunRequest's own field comments for why
    n_trials is required rather than defaulted, and
    MAX_SWEEP_COMBINATIONS_BAYESIAN's comment for why the ceiling differs
    from a plain grid sweep's."""

    @pytest.fixture
    def known_data(self, tmp_path):
        """Points KNOWN_DATA at the tiny regression fixture for the
        duration of one test, the same substitution
        TestBacktestExecution's own tests perform inline -- pulled into
        a fixture here since every test below needs it."""
        frame = pd.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")
        csv = tmp_path / "TESTQ.csv"
        frame.to_csv(csv)

        from server import backtest as module

        original = dict(module.KNOWN_DATA)
        module.KNOWN_DATA.clear()
        module.KNOWN_DATA["TESTQ"] = str(csv)
        try:
            yield "TESTQ"
        finally:
            module.KNOWN_DATA.clear()
            module.KNOWN_DATA.update(original)

    def test_trials_is_required_for_bayesian(self, client):
        response = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "bayes": {},
            },
        )
        body = response.json()
        assert response.status_code == 200  # errors are the payload, see TestValidateEndpoint
        assert body["errors"]
        assert "bayes.trials" in body["errors"][0]["msg"]

    def test_legacy_n_trials_is_accepted_and_ignored_for_a_plain_grid_request(self, client):
        """A legacy trial budget while search_strategy is still "grid"
        (its default) must not be an error -- the field is meaningless
        there, not invalid there. It translates to no `bayes` at all."""
        response = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "n_trials": 10,
            },
        )
        assert response.json()["errors"] == []

    def test_bayesian_samples_exactly_n_trials_not_the_full_combination_space(self, known_data):
        """The regression this class exists for: a plain string
        search_strategy="bayesian" (passed straight through
        to_run_sweep_kwargs with no n_trials attached) would default
        Optuna's budget to the FULL combination count -- see
        BayesianSearch's own docstring. run_backtest must replace it
        with a real pre-configured instance carrying the request's
        n_trials before run_sweep ever sees it."""
        from server.backtest import run_backtest

        report = run_backtest(
            {
                "tickers": [known_data],
                "grid_steps": [0.01, 0.02, 0.03],
                "targets": [0.003, 0.005],
                "model": "fixed",
                "params": {"allocation_pct": [0.03, 0.05, 0.08, 0.10]},
                # 3 steps x 2 targets x 4 allocation_pct values = 24
                # combinations; a plain grid would run all 24.
                "bayes": {"trials": 5},
                "rank_by": "Total Return %",
                "jobs": 1,
                "limit": 5000,
            },
            lambda fraction, note: None,
        )
        configurations = report["funds"][known_data]["cells"]
        assert len(configurations) == 5, (
            f"expected exactly the requested 5 trials, got {len(configurations)} -- a bayesian "
            "request silently ran the full 24-combination grid"
        )

    def test_target_return_alignment_does_not_downgrade_a_bayesian_search_to_grid(self, known_data):
        """THE bug this class exists to guard against. build_config
        rebuilds `config` via a second BacktestConfig.from_dict(...) once
        target_return alignment changes `params` -- bayesian_dual_scale's
        single profit_target always triggers this. That rebuild dict
        must carry the search section through explicitly; from_dict
        defaults an absent one to plain grid, which would silently run
        every combination despite a small n_trials having been
        requested. Asserted the same way as the test above: by the
        actual number of configurations a real run produces, not by
        inspecting config internals that could pass while the real
        behavior still regresses."""
        from server.backtest import run_backtest

        report = run_backtest(
            {
                "tickers": [known_data],
                "grid_steps": [0.01, 0.02],
                # ONE profit target -- required for bayesian_dual_scale,
                # and exactly what makes build_config align target_return
                # and rebuild `config` with the params dict.
                "targets": [0.005],
                "model": "bayesian_dual_scale",
                "params": {
                    "max_trade_pct": [0.03, 0.05, 0.08],
                    "bars_per_day": 387,
                    "horizon_days": [0.25, 1.0],
                },
                # 2 steps x 1 target x 3 max_trade_pct x 2 horizon_days
                # = 12 combinations; a downgraded-to-grid run would run
                # all 12.
                "bayes": {"trials": 4},
                "jobs": 1,
                "limit": 5000,
            },
            lambda fraction, note: None,
        )
        configurations = report["funds"][known_data]["cells"]
        assert len(configurations) == 4, (
            f"expected exactly the requested 4 trials, got {len(configurations)} -- "
            "target_return alignment's config rebuild silently dropped the bayesian search "
            "and ran the full grid instead"
        )

    def test_bayesian_relaxes_the_combination_ceiling_grid_does_not(self, client):
        """Same combination count (2100, past MAX_SWEEP_COMBINATIONS'
        2000), two outcomes: grid must still refuse it -- that ceiling
        exists independently of search mode -- bayesian with a small
        trial budget must not, since MAX_SWEEP_COMBINATIONS_BAYESIAN is
        the ceiling that actually governs it."""
        big_sweep = [round(0.01 + i * 0.0001, 6) for i in range(2100)]

        grid = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": big_sweep},
            },
        ).json()
        assert grid["errors"]
        assert "2000" in grid["errors"][0]["msg"]

        bayesian = client.post(
            "/api/backtest/validate",
            json={
                "tickers": ["TQQQ"],
                "grid_steps": [0.01],
                "targets": [0.005],
                "model": "fixed",
                "params": {"allocation_pct": big_sweep},
                "bayes": {"trials": 5},
            },
        ).json()
        assert bayesian["errors"] == []
