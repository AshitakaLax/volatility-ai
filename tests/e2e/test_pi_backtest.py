"""Backtesting works, end to end, against the real deployment.

--------------------------------------------------------------------
WHAT "END TO END" MEANS HERE

Every request goes to the Raspberry Pi. The Pi serves the UI and the
live routes itself and FORWARDS the backtest routes to the workstation,
so a passing test here proves the whole chain:

    browser -> Pi (static bundle) -> Pi (/api/backtest/*)
            -> workstation (job queue, engine, history) -> back again

Nothing is mocked and nothing is local. That is the point: the unit and
integration suites already cover each part in isolation, and the failure
this catches is the one they cannot -- the pieces disagreeing across a
network, a stale bundle on the Pi, a forwarding rule that drops a
websocket, an engine host that is reachable but has no data.

--------------------------------------------------------------------
IT NEVER TOUCHES THE TRADING LOOP

The Pi is running a live paper deployment. These tests submit backtests,
which are simulations on another machine, and read live state without
writing. /api/live/halt is never called, and a test below asserts this
file does not name it.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx
import pytest

# A small window and one instrument: this proves the chain, not the
# strategy. A ten-year sweep would take minutes and prove exactly the
# same thing about plumbing.
SMALL_RUN = {
    "tickers": ["TQQQ"],
    "grid_steps": [0.005, 0.01],
    "profit_targets": [0.003, 0.005],
    "sizing_model": "fixed",
    "limit": 20_000,
}


def wait_for(client: httpx.Client, run_id: str, timeout: float = 180.0) -> dict:
    """Poll a run to completion, the way a reloaded page would."""
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        response = client.get(f"/api/backtest/runs/{run_id}")
        response.raise_for_status()
        last = response.json()
        if last["status"] in {"complete", "failed"}:
            return last
        time.sleep(0.5)
    pytest.fail(f"run {run_id} did not finish within {timeout}s; last state {last}")


class TestTheDeploymentIsWhatWeThinkItIs:
    def test_the_pi_serves_the_built_ui(self, client):
        """A 200 with JSON here would mean the bundle was never copied
        into the image and the API is answering the browser's page
        request -- which looks like a blank screen, not an error."""
        page = client.get("/")
        assert page.status_code == 200
        assert "text/html" in page.headers["content-type"]
        assert '<div id="root">' in page.text

    def test_the_bundle_it_references_actually_loads(self, client):
        """A stale index.html pointing at an asset the image does not
        have renders an empty page with a 404 in the console."""
        asset = re.search(r'src="(/assets/[^"]+\.js)"', client.get("/").text)
        assert asset, "index.html references no bundle"
        response = client.get(asset.group(1))
        assert response.status_code == 200
        assert len(response.content) > 50_000, "the bundle looks truncated"

    def test_backtests_are_forwarded_not_run_on_the_pi(self, client):
        """The Pi has four cores and one of them is placing orders."""
        health = client.get("/api/health").json()
        assert health["backtest_local"] is False
        assert health["backtest_upstream"], "no engine host configured"

    def test_the_engine_host_has_data_the_pi_does_not(self, client):
        """Proof the forwarding reaches the other machine: the Pi's own
        data directory holds TQQQ alone."""
        funds = client.get("/api/backtest/funds").json()["funds"]
        available = {fund["ticker"] for fund in funds if fund["available"]}
        assert "TQQQ" in available
        assert len(available) > 1, f"only {available} — is this the Pi's own data?"


class TestARunCompletesThroughTheWholeChain:
    def test_a_submitted_run_finishes_and_carries_the_contract(self, client):
        submitted = client.post("/api/backtest/runs", json=SMALL_RUN)
        assert submitted.status_code == 202, submitted.text
        run_id = submitted.json()["run_id"]

        finished = wait_for(client, run_id)
        assert finished["status"] == "complete", finished.get("error")

        report = finished["report"]
        assert report["run_id"] == run_id, "the report was not stamped with its own id"
        fund = report["funds"]["TQQQ"]

        # Every metric the UI panel reads, including the ones added for
        # ranking. A missing key renders as "--" rather than crashing,
        # which is exactly the silent degradation worth catching here.
        for key in (
            "cagr_pct",
            "max_drawdown_pct",
            "win_rate_pct",
            "profit_factor",
            "sharpe_ratio",
            "worst_year_pct",
            "stuck_capital_value",
            "capital_velocity_index",
            "total_trades",
        ):
            assert key in fund["metrics"], f"metrics is missing {key}"

        # 2 steps x 2 targets. The sweep matrix needs all of them.
        assert len(fund["configurations"]) == 4

        # And the executions carry what the chart's cycle connectors
        # join on -- the reason the blotter was given lot identity.
        sells = [e for e in fund["executions"] if e["type"] == "SELL"]
        buys = {
            e["order_id"].rsplit("-buy-", 1)[0] for e in fund["executions"] if e["type"] == "BUY"
        }
        if sells:
            assert all("matched_buy_id" in sell for sell in sells)
            assert {sell["matched_buy_id"] for sell in sells} <= buys

    def test_progress_is_reported_between_start_and_finish(self, client):
        """A bar that only ever shows 0% then 100% is not a progress
        bar. This is the case that was broken until progress became
        per-combination rather than per-ticker."""
        run_id = client.post("/api/backtest/runs", json=SMALL_RUN).json()["run_id"]

        fractions: set[float] = set()
        deadline = time.time() + 180
        while time.time() < deadline:
            state = client.get(f"/api/backtest/runs/{run_id}").json()
            fractions.add(state["progress"])
            if state["status"] in {"complete", "failed"}:
                break
            time.sleep(0.2)

        assert 1.0 in fractions, "never reported completion"
        # At least one reading strictly between the ends. Polling can
        # miss individual updates on a fast run, so this asserts the
        # WEAK form: not that every step was seen, but that progress is
        # not binary.
        assert any(0.0 < value < 1.0 for value in fractions), (
            f"progress only ever reported {sorted(fractions)} — per-ticker again?"
        )

    def test_a_completed_run_reaches_history(self, client):
        """History is written on the workstation and read back through
        the Pi, so this covers persistence AND the forwarding of it."""
        before = client.get("/api/backtest/history").json()
        run_id = client.post("/api/backtest/runs", json=SMALL_RUN).json()["run_id"]
        wait_for(client, run_id)

        after = client.get("/api/backtest/history").json()
        assert after["runs"] > before["runs"]
        rows = [row for row in after["rows"] if row["run_id"] == run_id]
        assert len(rows) == 4, "the sweep's four cells are not all in history"
        assert all(row["ticker"] == "TQQQ" for row in rows)
        # Rankable: the fields the history table sorts on are present.
        assert all("cagr_pct" in row["metrics"] for row in rows)

    def test_a_stored_run_can_be_reopened(self, client):
        run_id = client.post("/api/backtest/runs", json=SMALL_RUN).json()["run_id"]
        wait_for(client, run_id)
        reopened = client.get(f"/api/backtest/history/{run_id}")
        assert reopened.status_code == 200
        assert reopened.json()["report"]["funds"]["TQQQ"]["metrics"]["total_trades"] >= 0


class TestFailuresSurfaceRatherThanHang:
    def test_a_bad_sizing_model_is_rejected_immediately(self, client):
        """The failure a real user hit: this used to be accepted and
        then die in the worker complaining about a results column."""
        response = client.post(
            "/api/backtest/runs",
            json={**SMALL_RUN, "sizing_model": "not_a_strategy"},
        )
        assert response.status_code == 400
        assert "Known strategies" in response.json()["detail"]

    def test_a_partial_parameter_set_is_rejected_immediately(self, client):
        response = client.post(
            "/api/backtest/runs",
            json={
                **SMALL_RUN,
                "sizing_model": "bell_curve",
                "strategy_params": {"lookback_days": 20},
            },
        )
        assert response.status_code == 400
        assert "Missing" in response.json()["detail"]

    def test_every_offered_sizing_model_can_actually_run(self, client):
        """The dropdown offers these, so every one must be submittable.
        Four of the five were not, which is the bug that started this."""
        details = client.get("/api/backtest/funds").json()["sizing_details"]
        for model in details:
            # This model estimates P(reaching ONE target), so the engine
            # refuses to sweep several against it.
            targets = [0.005] if model == "bayesian_dual_scale" else SMALL_RUN["profit_targets"]
            response = client.post(
                "/api/backtest/runs",
                json={**SMALL_RUN, "sizing_model": model, "profit_targets": targets},
            )
            assert response.status_code == 202, (
                f"{model}: {response.status_code} {response.text[:160]}"
            )


class TestItCannotTouchTheTradingLoop:
    def test_this_suite_never_calls_the_halt_endpoint(self):
        """The Pi is running a live paper deployment. A test suite able
        to halt it is a worse problem than no suite at all.

        Checked against the AST rather than the text: a substring search
        flags this file's own docstring explaining the rule, which is
        how the first version of this test failed. Only strings passed
        to a CALL count -- prose about the endpoint is not a request to
        it.
        """
        import ast

        for path in Path(__file__).parent.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                for literal in ast.walk(node):
                    if (
                        isinstance(literal, ast.Constant)
                        and isinstance(literal.value, str)
                        and "/api/live/halt" in literal.value
                    ):
                        pytest.fail(
                            f"{path.name}:{literal.lineno} passes the halt endpoint to a call"
                        )

    def test_live_state_is_readable_without_being_written(self, client):
        """Read-only by construction on the server; asserted here as the
        behaviour a reader depends on."""
        stores = client.get("/api/live/stores").json()["stores"]
        assert stores, "the Pi reports no ledger stores"
        state = client.get("/api/live/state", params={"path": stores[0]["path"]})
        assert state.status_code == 200
        assert "lots" in state.json()


class TestTheBrowserActuallyRendersIt:
    """The part no HTTP check covers: the bundle runs, and the page it
    draws is fed by these same endpoints."""

    @pytest.fixture(scope="class")
    def page(self, base_url):
        playwright = pytest.importorskip("playwright.sync_api")
        with playwright.sync_playwright() as driver:
            try:
                browser = driver.firefox.launch()
            except Exception as exc:
                pytest.skip(f"no browser available: {str(exc)[:120]}")
            context = browser.new_context(viewport={"width": 1600, "height": 1200})
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base_url, wait_until="networkidle", timeout=60_000)
            page.errors = errors  # type: ignore[attr-defined]
            yield page
            browser.close()

    def test_the_app_mounts_without_a_javascript_error(self, page):
        """A blank page with a console error is the classic stale-bundle
        failure, and it returns 200 to every HTTP check above.

        This is not hypothetical: the first run of this suite caught
        "Cannot parse color: oklch(...)" thrown by lightweight-charts,
        which took the whole backtesting view down. Every HTTP assertion
        above passed while the page rendered nothing.
        """
        assert page.locator("text=volatility-ai").first.is_visible()
        assert not page.errors, f"page errors: {page.errors}"  # type: ignore[attr-defined]

    def test_the_backtesting_view_is_the_default(self, page):
        """Section 1 is the priority view, per the brief."""
        assert page.locator("text=Run a backtest").first.is_visible()

    def test_the_history_table_is_visible_on_load(self, page):
        """It used to be hidden until a report was loaded -- exactly the
        load where it is most useful."""
        history = page.locator("text=Run history").first
        assert history.is_visible()
        # Seeded and completed runs mean this should not be empty.
        assert page.locator("text=/configurations? across/").first.is_visible()

    def test_the_ranking_metric_can_be_changed(self, page):
        """The selectable ranking is the feature; a fixed column would
        assert an answer the data does not settle.

        Targeted by data-testid rather than by position among the page's
        selects -- an index would silently start testing a different
        control the moment a field is added above it. (The parameter form
        renders a variable number of selects now: enum/bool sizing-model
        arguments each get one when their model is picked.)
        """
        page.get_by_test_id("rank-by").select_option(label="Lowest drawdown")
        page.wait_for_timeout(400)
        assert page.locator("text=Lowest drawdown").first.is_visible()

    def test_opening_a_run_from_history_loads_its_report_in_a_new_tab(self, page):
        """The Pi ships no static export -- output/ is git-ignored and
        excluded from the image -- so a fresh page has no report until
        one is opened. That is correct, and it is also how a person
        gets to a chart: click a row.

        A real anchor (target="_blank"), not a same-page state swap: the
        original page must be left exactly as it was, and Playwright
        surfaces the new tab as a "popup" event on the shared context.
        Stashed onto `page` itself (matching how the fixture already
        hangs `page.errors` off it) so later tests in this class -- which
        need a report already loaded -- read that tab, not this one.
        """
        with page.expect_popup() as popup_info:
            page.get_by_test_id("history-row").first.click()
        report_page = popup_info.value
        report_page.wait_for_selector("text=Execution chart", timeout=30_000)
        assert report_page.locator("text=Risk and reward").first.is_visible()

        # The tab that did the clicking never navigated. Checked via the
        # URL, not page content: a development machine can have a static
        # export (output/) the Pi deliberately excludes, which would
        # make "no report visible here" a fact about that machine's data
        # rather than about whether this tab navigated.
        assert "run=" not in page.url
        assert page.locator("text=Run a backtest").first.is_visible()

        page.report_page = report_page  # type: ignore[attr-defined]

    def test_the_trade_log_expands(self, page):
        """Collapsed by default; opening it is a deliberate act.

        Runs after a report is loaded -- in the NEW TAB the previous
        test opened, not `page` itself, which never gained one.
        """
        report_page = getattr(page, "report_page", page)
        report_page.get_by_test_id("trade-log-toggle").click()
        report_page.wait_for_timeout(500)
        assert report_page.locator("text=/one row per lot|every buy and sell/").first.is_visible()

    def test_submitting_a_run_from_the_form_shows_progress_and_results(self, page):
        """The whole feature, driven the way a person drives it."""
        page.get_by_test_id("bars").select_option(index=0)  # 20k, the fast one
        page.get_by_test_id("run").click()

        # The button becomes "Running…" while the job is in flight.
        page.wait_for_selector("text=Running…", timeout=30_000)

        # And the run settles. Generous: it crosses two machines.
        page.wait_for_selector("text=/complete/i", timeout=180_000)
        assert not page.errors, f"page errors during the run: {page.errors}"  # type: ignore[attr-defined]


def test_the_run_payload_matches_the_documented_contract(client):
    """One last check on shape, so a field renamed on the server is
    caught here rather than as a blank column in the UI."""
    run_id = client.post("/api/backtest/runs", json=SMALL_RUN).json()["run_id"]
    report = wait_for(client, run_id)["report"]

    assert set(report) >= {"run_id", "parameters", "timeframe", "funds"}
    assert set(report["parameters"]) >= {
        "grid_step_pct",
        "profit_target_pct",
        "sizing_model",
        "fill_model",
        "enforce_no_loss",
        "n_jobs",
    }
    fund = report["funds"]["TQQQ"]
    assert set(fund) >= {"metrics", "executions", "equity_curve", "configurations", "bars"}
    assert set(fund["equity_curve"]) == {"dates", "equity", "normalized"}
    # Parallel arrays, which the overlay chart indexes together.
    curve = fund["equity_curve"]
    assert len(curve["dates"]) == len(curve["equity"]) == len(curve["normalized"])
    # Rebased to 100 at the first point -- the whole basis of comparing
    # two funds on one axis.
    if curve["normalized"]:
        assert curve["normalized"][0] == pytest.approx(100.0)


def test_the_suite_points_somewhere_explicit(base_url):
    """Recorded in the output so a passing run says WHICH deployment it
    passed against."""
    assert base_url.startswith("http")
    print(f"\ne2e target: {base_url}")
    print(json.dumps({"target": base_url}, indent=None))
