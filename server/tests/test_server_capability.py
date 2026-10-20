"""The server's capability split, enforced instead of documented.

The API is deliberately not uniform. Live state is read-only because a
UI bug there could touch a real position; a backtest is bidirectional
because it is a simulation over a CSV. That boundary is only worth
anything if something checks it, so these walk each module's AST.

Modelled on engine/tests/test_dashboard_data.py's
`test_no_broker_or_session_is_reachable_from_the_dashboard`, which
established the pattern here: assert against the SOURCE, not against
behaviour, because behaviour tests only cover the paths someone thought
to exercise and a new import is exactly the thing nobody thinks to
exercise.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parents[2] / "server"

# Anything that could reach a venue, a credential, or an order. Matched
# against imported MODULE names, so `src.alpaca_broker` and
# `from engine.brokers.alpaca_broker import X` are both caught.
FORBIDDEN_MODULES = (
    "alpaca",
    "alpaca_broker",
    "fidelity_broker",
    "fidelity_session",
    "fidelity_placing_broker",
    "fidelity_capture",
    "live_execution",
    "live_trading_loop",
    "broker_selection",
    "order_management_system",
    "secrets",
)

# Names that would mean this module can decide to sell something.
FORBIDDEN_NAMES = (
    "submit_sell",
    "submit_buy",
    "execute_sell",
    "close_lot",
    "lots_to_liquidate",
    "collect_liquidations",
)


def module_ast(name: str) -> ast.Module:
    return ast.parse((SERVER / name).read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> set[str]:
    """Every module named by an import, flattened to its parts."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.update(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.update(node.module.split("."))
            found.update(alias.name for alias in node.names)
    return found


def called_names(tree: ast.Module) -> set[str]:
    """Every attribute and bare name that appears in a call position."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute):
                found.add(target.attr)
            elif isinstance(target, ast.Name):
                found.add(target.id)
    return found


ALL_MODULES = (
    "live.py",
    "live_control.py",
    "live_registry.py",
    "backtest.py",
    "jobs.py",
    "app.py",
    "deployment.py",
    "ml_insights.py",
    "ml_upstream.py",
    "shards.py",
    "shard_client.py",
    "warehouse_status.py",
)


@pytest.mark.parametrize("name", ALL_MODULES)
def test_no_server_module_can_reach_a_broker(name: str):
    """Not one of them. The process has no credentials by design."""
    offenders = imported_modules(module_ast(name)) & set(FORBIDDEN_MODULES)
    assert not offenders, f"server/{name} imports {sorted(offenders)}"


@pytest.mark.parametrize("name", ALL_MODULES)
def test_no_server_module_can_sell_anything(name: str):
    """There is no forced-liquidation path, and none may appear here."""
    offenders = called_names(module_ast(name)) & set(FORBIDDEN_NAMES)
    assert not offenders, f"server/{name} calls {sorted(offenders)}"


class TestLiveIsReadOnly:
    """server/live.py's central claim."""

    def test_it_opens_no_writable_store(self):
        """Every read goes through src.dashboard_data, which opens the
        database `mode=ro` -- the DRIVER refuses writes, not this code.
        Constructing a LedgerStore here would bypass that entirely."""
        tree = module_ast("live.py")
        assert "LedgerStore" not in imported_modules(tree)
        assert "LedgerStore" not in called_names(tree)

    def test_it_cannot_reach_the_circuit_breaker(self):
        """The halt lives in control.py. If it were reachable from here,
        live.py's docstring would be false and a reader who trusted it
        would be wrong."""
        tree = module_ast("live.py")
        assert "CircuitBreaker" not in imported_modules(tree)
        assert "halt_for_reconciliation" not in called_names(tree)

    def test_it_reads_only_through_the_read_only_layer(self):
        """A direct sqlite3 connection would sidestep mode=ro."""
        assert "sqlite3" not in imported_modules(module_ast("live.py"))

    @pytest.mark.parametrize("name", ["live.py", "live_registry.py"])
    def test_it_reads_the_control_directory_and_never_writes_it(self, name: str):
        """It shows what the trader reports and what was asked of it; the
        queueing is live_control.py's, the rest the trader's."""
        called = called_names(module_ast(name))
        assert not called & (QUEUE_CALLS | WRITE_CALLS), (
            f"server/{name} calls {sorted(called & (QUEUE_CALLS | WRITE_CALLS))}"
        )


# What could change a ledger, a breaker or a file. The control module may
# only QUEUE commands (ControlInbox.enqueue / cancel); the trader applies them.
WRITE_CALLS = {
    "open",
    "write_text",
    "write_bytes",
    "unlink",
    "rename",
    "replace",
    "set_meta",
    "halt_by_operator",
    "manual_reset",
    "halt_for_reconciliation",
}
# The inbox's own writers. Reading modules may not call them at all.
QUEUE_CALLS = {"enqueue", "cancel", "claim", "record", "set_desired", "write_status"}


class TestLiveControlOnlyQueues:
    """server/live_control.py changes nothing itself: it queues commands that
    the deployment's trader -- the only writer of its ledger -- applies."""

    def test_it_reaches_no_ledger_breaker_or_shell(self):
        imported = imported_modules(module_ast("live_control.py"))
        assert not imported & {"LedgerStore", "CircuitBreaker", "sqlite3", "subprocess"}, imported

    def test_it_writes_only_through_the_inbox(self):
        called = called_names(module_ast("live_control.py"))
        assert not called & WRITE_CALLS, f"live_control.py calls {sorted(called & WRITE_CALLS)}"
        # The positive case: a negative test alone would pass on an empty file.
        assert {"enqueue", "cancel"} <= called

    def test_it_never_changes_an_algorithm_itself(self):
        """It reads the algorithm and dry-runs a change (AlgorithmControl.
        check); writing the override is the trader's, when it applies the
        command."""
        attribute_calls = {
            node.func.attr
            for node in ast.walk(module_ast("live_control.py"))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert not attribute_calls & {"set", "reset", "mark_live"}, attribute_calls

    def test_there_is_no_liquidation_command(self):
        """`liquidate_all` was requested once and refused: the loop sells a
        lot only at its target under the no-loss guard (or by the Ultimate
        regime exit), and a forced, loss-realising sell is not a button."""
        import typing

        from engine.trading.control_inbox import COMMAND_TYPES
        from server.live_control import CommandRequest

        accepted = typing.get_args(CommandRequest.model_fields["type"].annotation)
        for name in (*accepted, *COMMAND_TYPES):
            assert "liquidat" not in name and "sell" not in name, name

    def test_every_post_route_has_the_cross_site_guard(self):
        from server.live_control import router, same_origin

        for route in router.routes:
            if "POST" in getattr(route, "methods", ()):
                guards = [dependency.call for dependency in route.dependant.dependencies]
                assert same_origin in guards, route.path


class TestBacktestTouchesNoLiveState:
    """The bidirectional router may accept input precisely because it
    cannot reach anything live."""

    def test_it_opens_no_ledger_store(self):
        tree = module_ast("backtest.py")
        assert "LedgerStore" not in imported_modules(tree)
        assert "CircuitBreaker" not in imported_modules(tree)

    def test_it_validates_through_the_real_config(self):
        """Not through a second schema that could drift from the one the
        engine enforces."""
        tree = module_ast("backtest.py")
        assert "BacktestConfig" in imported_modules(tree)
        assert "validate" in called_names(tree)

    def test_it_reuses_the_exporter_serialisers(self):
        """A static export and the API disagreeing about the shape of a
        BacktestExecution is a bug the UI would find at runtime."""
        imported = imported_modules(module_ast("backtest.py"))
        assert {"executions", "fund_metrics", "equity_series"} <= imported

    def test_a_submitted_config_cannot_carry_a_live_section(self):
        """Live settings from a browser would be live settings from
        anyone who can reach the port."""
        source = (SERVER / "backtest.py").read_text(encoding="utf-8")
        assert '"live"' not in source


class TestDeploymentIsNarrow:
    """deployment.py is the only module that runs a subprocess."""

    def test_it_opens_no_store_and_reaches_no_breaker(self):
        tree = module_ast("deployment.py")
        assert "LedgerStore" not in imported_modules(tree)
        assert "CircuitBreaker" not in imported_modules(tree)

    def test_no_shell_and_no_interpolated_command(self):
        """The argv is a fixed constant list. A formatted command string
        here would be a path from an HTTP request to a shell."""
        source = (SERVER / "deployment.py").read_text(encoding="utf-8")
        assert "shell=True" not in source
        assert 'subprocess.run(f"' not in source
        assert "os.system" not in source

    def test_only_deployment_runs_a_subprocess(self):
        """If another module grows one, it needs its own justification
        rather than inheriting this one's."""
        for name in ALL_MODULES:
            if name == "deployment.py":
                continue
            assert "subprocess" not in imported_modules(module_ast(name)), (
                f"server/{name} imports subprocess"
            )


class TestMlInsightsIsReadOnly:
    """server/ml_insights.py formats artifacts already written to disk.

    It is not on the path from a bar to an order, and it cannot become
    one by accident: these assertions hold it to that the same way
    live.py is held to reading through the read-only layer.
    """

    def test_it_opens_no_writable_store_and_reaches_no_breaker(self):
        tree = module_ast("ml_insights.py")
        assert "LedgerStore" not in imported_modules(tree)
        assert "CircuitBreaker" not in imported_modules(tree)
        assert "sqlite3" not in imported_modules(tree)

    def test_it_imports_no_ml_training_code(self):
        """It reads JSON that tools/*.py already wrote. Importing
        research.ml.sources or .features would pull in network calls and
        pandas transforms an HTTP GET has no business triggering;
        importing lightgbm or sklearn would pull in a dependency this
        project deliberately keeps off the Raspberry Pi image (see
        requirements-ml.txt and this module's own docstring)."""
        tree = module_ast("ml_insights.py")
        imported = imported_modules(tree)
        assert not imported & {"sources", "features", "labels", "lightgbm", "sklearn"}, (
            f"ml_insights.py imports {sorted(imported & {'sources', 'features', 'labels', 'lightgbm', 'sklearn'})}"
        )

    def test_it_exposes_only_get_routes(self):
        """A research view has nothing to submit. A POST/PUT/DELETE
        route here would be a second, undocumented write surface."""
        source = (SERVER / "ml_insights.py").read_text(encoding="utf-8")
        for verb in ("router.post", "router.put", "router.delete", "router.patch"):
            assert verb not in source, f"ml_insights.py defines a {verb} route"


class TestMlUpstreamIsReadOnly:
    """server/ml_upstream.py relays to the workstation -- GET only."""

    def test_it_forwards_get_only(self):
        """Unlike server/upstream.py, there is no job to submit here --
        only JSON someone already generated. A wider method list would
        be relaying writes to a route the workstation never exposes as
        writable in the first place."""
        source = (SERVER / "ml_upstream.py").read_text(encoding="utf-8")
        assert 'methods=["GET"]' in source
        for verb in ("POST", "PUT", "DELETE", "PATCH"):
            assert f'"{verb}"' not in source

    def test_it_reuses_the_backtest_upstream_decision_rather_than_a_second_env_var(self):
        """One "is a research/engine host configured" decision, not two
        that could disagree about whether forwarding is on."""
        tree = module_ast("ml_upstream.py")
        assert "upstream" in imported_modules(tree)
        source = (SERVER / "ml_upstream.py").read_text(encoding="utf-8")
        assert "os.environ" not in source and "getenv" not in source


class TestAppDefaults:
    def test_cors_is_not_a_wildcard(self):
        """There is no authentication. A wildcard origin plus no auth
        means any page the operator visits can read their positions."""
        source = (SERVER / "app.py").read_text(encoding="utf-8")
        assert 'allow_origins=["*"]' not in source
        assert '"*"' not in source.split("allow_origins")[1].split("]")[0]

    def test_the_spa_catch_all_never_shadows_the_api(self):
        """Asked of the app's BEHAVIOUR, not its route list.

        The first version of this compared positions in app.routes. That
        worked until FastAPI began representing an included router as a
        single entry with no path, at which point the check silently saw
        only /api/health and stopped covering the routers it existed to
        protect. Driving real requests cannot rot that way.

        The bug it guards is real and was made twice: a catch-all
        registered before the API swallowed all of it, and a GET-only
        catch-all answered 405 to a POST on a route that does not exist.
        """
        from fastapi.testclient import TestClient

        from server.app import app

        client = TestClient(app)

        # A real API route answers as itself, not with the app shell.
        health = client.get("/api/health")
        assert health.status_code == 200
        assert "caps" in health.json()

        # An API route that needs arguments still reaches its own
        # validation rather than being handed HTML.
        assert client.get("/api/live/indicators").status_code == 422

        # And an API path that does not exist is a JSON 404 on every
        # method -- never 405, and never the HTML shell.
        for method in ("get", "post"):
            missing = getattr(client, method)("/api/live/liquidate")
            assert missing.status_code == 404, f"{method} gave {missing.status_code}"
            assert "text/html" not in missing.headers.get("content-type", "")

    def test_the_worker_ceiling_is_host_configurable(self):
        """The Pi runs the trading loop and this server on four cores, so
        the 'parallelism is safe' premise is a property of the HOST. It
        has to be a setting, and the compose file that puts this next to
        a live loop is what says so."""
        source = (SERVER / "backtest.py").read_text(encoding="utf-8")
        assert "VAI_MAX_JOBS" in source

    def test_it_reports_which_commands_it_supports(self):
        """The UI renders the Command Center from what the SERVER says,
        not from a constant baked into the bundle that could disagree
        with the deployment it is talking to."""
        from server.app import health

        caps = health()["caps"]
        assert "control" in caps
        assert "liquidate" not in caps
        assert "parameter_override" not in caps


class TestWarehouseStatusIsReadOnly:
    """server/warehouse_status.py reports on the warehouse, the machine and
    the queue; it changes none of them."""

    def test_it_exposes_only_get_routes(self):
        source = (SERVER / "warehouse_status.py").read_text(encoding="utf-8")
        for verb in ("router.post", "router.put", "router.delete", "router.patch", "api_route"):
            assert verb not in source, f"warehouse_status.py defines a {verb} route"

    def test_it_cannot_open_the_warehouse_for_writing(self):
        """Reads go through engine/warehouse/inventory.py's read-only open.
        Anything that opens or writes the warehouse itself would sidestep it."""
        tree = module_ast("warehouse_status.py")
        reached = imported_modules(tree) | called_names(tree)
        assert not reached & {
            "duckdb",
            "open_warehouse",
            "BatchedResultWriter",
            "DuckDBResultSink",
            "ingest",
            "initialize",
        }, f"warehouse_status.py reaches {sorted(reached)}"

    def test_it_reaches_no_store_breaker_or_shell(self):
        imported = imported_modules(module_ast("warehouse_status.py"))
        assert not imported & {"LedgerStore", "CircuitBreaker", "sqlite3", "subprocess"}

    def test_it_changes_nothing_in_the_queue(self):
        """It reads the queue's runs and shards -- never a control."""
        called = called_names(module_ast("warehouse_status.py"))
        assert not called & {
            "submit",
            "pause",
            "resume",
            "cancel",
            "move",
            "run_next",
            "pause_all",
            "resume_all",
            "pause_shard",
            "resume_shard",
            "forget_shard",
            "set_shard_schedule",
            "set_shards_paused",
        }
