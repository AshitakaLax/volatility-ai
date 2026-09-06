"""The server's capability split, enforced instead of documented.

The API is deliberately not uniform. Live state is read-only because a
UI bug there could touch a real position; a backtest is bidirectional
because it is a simulation over a CSV. That boundary is only worth
anything if something checks it, so these walk each module's AST.

Modelled on tests/unit/test_dashboard_data.py's
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
# `from src.alpaca_broker import X` are both caught.
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


ALL_MODULES = ("live.py", "control.py", "backtest.py", "jobs.py", "app.py", "deployment.py")


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


class TestControlIsNarrow:
    """server/control.py is the ONE write, and only that one."""

    def test_it_reaches_the_circuit_breaker(self):
        """A negative test suite that never checks the positive case
        would pass on an empty file."""
        tree = module_ast("control.py")
        assert "CircuitBreaker" in imported_modules(tree)
        assert "halt_for_reconciliation" in called_names(tree)

    def test_it_exposes_exactly_one_route(self):
        """A second endpoint here is a second write, and would need its
        own justification. Counting them makes that a decision rather
        than a drift."""
        routes = [
            node
            for node in ast.walk(module_ast("control.py"))
            for decorator in getattr(node, "decorator_list", [])
            if isinstance(node, ast.FunctionDef)
            and isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "router"
        ]
        assert len(routes) == 1, f"control.py exposes {[r.name for r in routes]}"

    def test_it_names_no_liquidation_endpoint(self):
        """`liquidate_all` was requested and refused: the trading loop
        has no code path that sells for any reason but a met profit
        target, and adding one would mean forced selling at a loss."""
        source = (SERVER / "control.py").read_text(encoding="utf-8")
        assert "def liquidate" not in source
        assert '"/liquidate' not in source


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
        assert health.json()["status"] == "ok"

        # An API route that needs arguments still reaches its own
        # validation rather than being handed HTML.
        assert client.get("/api/live/state").status_code == 422

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

        capabilities = health()["capabilities"]
        assert capabilities["halt"] is True
        assert capabilities["liquidate"] is False
        assert capabilities["parameter_override"] is False
