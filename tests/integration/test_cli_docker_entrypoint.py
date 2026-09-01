"""
Tests for cli.py, the Docker image's ENTRYPOINT.

Run as real subprocesses (matching
tests/integration/test_task_1_1_run_instructions.py's established
pattern) rather than importing and calling functions directly, since
what actually matters is the exact invocation a `docker run` would
perform -- argument parsing, exit codes, and stdout/stderr -- not the
internal function calls.

Includes a regression test for a real bug caught during manual testing
before this was committed: `cli.py test -q` (the single most common
invocation) raised "unrecognized arguments: -q", because
argparse.REMAINDER cannot reliably capture a leading option-like token
with no preceding positional. Fixed by forwarding sys.argv directly
for the `test` subcommand rather than routing it through argparse.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "cli.py"


def _run(*args, timeout=60):
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.fixture
def config_path(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "strategy:\n"
        "  strategy_id: fixed\n"
        "  strategy_params:\n"
        "    allocation_pct: 0.05\n"
        "grid:\n"
        "  steps: [0.005, 0.01]\n"
        "  profit_targets: [0.003, 0.005]\n"
    )
    return path


@pytest.fixture
def data_path():
    return REPO_ROOT / "tests" / "fixtures" / "regression_ohlcv.csv"


def test_bare_invocation_shows_usage_and_exits_nonzero():
    result = _run()
    assert result.returncode != 0
    assert "usage" in result.stderr.lower()


def test_help_mentions_all_three_subcommands():
    result = _run("--help")
    assert result.returncode == 0
    for name in ("test", "backtest", "live"):
        assert name in result.stdout


def test_test_subcommand_with_a_leading_flag_does_not_crash_argparse():
    """Regression test for the exact bug found during manual testing:
    `cli.py test -q` (no preceding positional) previously raised
    'unrecognized arguments: -q' from the top-level parser, because
    argparse.REMAINDER only reliably captures a trailing remainder when
    a positional precedes it. Scoped to one fast, stable file so this
    stays quick rather than re-running the whole suite recursively."""
    result = _run("test", "tests/unit/test_no_loss_guard.py", "-q")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "unrecognized arguments" not in result.stderr


def test_test_subcommand_forwards_arguments_to_pytest_verbatim():
    result = _run("test", "tests/unit/test_no_loss_guard.py", "-q")
    assert "passed" in result.stdout
    assert "+ " in result.stderr  # the echoed command line


def test_test_subcommand_propagates_pytest_failure_exit_code():
    result = _run("test", "tests/unit/test_no_loss_guard.py::test_this_does_not_exist", "-q")
    assert result.returncode != 0


def test_test_subcommand_help_does_not_crash():
    result = _run("test", "--help")
    assert result.returncode == 0


def test_backtest_runs_end_to_end_against_the_regression_fixture(config_path, data_path):
    result = _run("backtest", "--config", str(config_path), "--data", str(data_path))
    assert result.returncode == 0, result.stderr
    assert "Grid Step" in result.stdout
    assert "combination(s) evaluated" in result.stdout


def test_backtest_writes_a_loadable_full_results_csv(config_path, data_path, tmp_path):
    import pandas as pd

    output = tmp_path / "results.csv"
    result = _run(
        "backtest", "--config", str(config_path), "--data", str(data_path), "--output", str(output)
    )
    assert result.returncode == 0, result.stderr
    assert output.exists()

    df = pd.read_csv(output)
    assert len(df) == 4  # 2 grid steps x 2 profit targets
    assert "Capital Velocity Index" in df.columns


def test_backtest_missing_config_file_fails_clearly(data_path):
    result = _run("backtest", "--config", "/nonexistent/config.yaml", "--data", str(data_path))
    assert result.returncode == 2
    assert "not found" in result.stderr.lower()


def test_backtest_missing_data_file_fails_clearly(config_path):
    result = _run("backtest", "--config", str(config_path), "--data", "/nonexistent/data.csv")
    assert result.returncode == 2
    assert "not found" in result.stderr.lower()


def test_backtest_invalid_config_fails_with_validation_error(tmp_path, data_path):
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text(
        "strategy:\n  strategy_id: fixed\n  strategy_params: {allocation_pct: 0.05}\n"
        "grid:\n  steps: [1.5]\n  profit_targets: [0.01]\n"
    )  # grid step >= 1.0 is invalid
    result = _run("backtest", "--config", str(bad_config), "--data", str(data_path))
    assert result.returncode == 2
    assert "invalid config" in result.stderr.lower()


def test_backtest_unknown_strategy_id_fails_clearly(tmp_path, data_path):
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text(
        "strategy:\n  strategy_id: not_a_real_strategy\ngrid:\n  steps: [0.01]\n  profit_targets: [0.005]\n"
    )
    result = _run("backtest", "--config", str(bad_config), "--data", str(data_path))
    assert result.returncode == 2
    assert "unknown strategy_id" in result.stderr.lower()


def test_backtest_missing_required_flags_fails():
    result = _run("backtest")
    assert result.returncode == 2


def test_live_with_enabled_false_refuses_cleanly(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        "strategy:\n  strategy_id: fixed\n  strategy_params: {allocation_pct: 0.05}\n"
        "grid:\n  steps: [0.01]\n  profit_targets: [0.005]\n"
    )
    result = _run("live", "--config", str(config), "--state-db", str(tmp_path / "ledger.db"))
    assert result.returncode == 2
    assert "live.enabled" in result.stderr


def test_live_with_no_credentials_fails_at_credential_loading(tmp_path):
    """No env vars at all -> fails before ever reaching the
    broker-adapter question, at credential loading itself."""
    config = tmp_path / "config.yaml"
    config.write_text(
        "strategy:\n  strategy_id: fixed\n  strategy_params: {allocation_pct: 0.05}\n"
        "grid:\n  steps: [0.01]\n  profit_targets: [0.005]\n"
        "live:\n  enabled: true\n  paper_trading: true\n"
    )
    db_path = tmp_path / "ledger.db"
    env = {"PATH": "/usr/bin:/bin"}  # explicitly no APCA_* credentials
    result = subprocess.run(
        [sys.executable, str(CLI), "live", "--config", str(config), "--state-db", str(db_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert result.returncode == 1
    assert "RECOVERY_REQUIRED" in result.stdout
    assert "Missing required live-credential environment variable" in result.stderr


def test_live_with_rejected_credentials_halts_in_recovery_required(tmp_path):
    """Credentials present but not valid at the broker -> the adapter
    connects for real, the broker rejects the key, and startup stops in
    RECOVERY_REQUIRED rather than trading against an unauthenticated
    session.

    The credentials are deliberately bogus, so this asserts the failure
    path only. It must not depend on reaching Alpaca: with network the
    connection check fails on a 401, without network it fails on a
    transport error, and RECOVERY_REQUIRED is the correct outcome for
    both -- which is exactly what makes this assertion safe in an
    offline CI environment.
    """
    config = tmp_path / "config.yaml"
    config.write_text(
        "strategy:\n  strategy_id: fixed\n  strategy_params: {allocation_pct: 0.05}\n"
        "grid:\n  steps: [0.01]\n  profit_targets: [0.005]\n"
        "live:\n  enabled: true\n  paper_trading: true\n"
    )
    db_path = tmp_path / "ledger.db"
    env = {
        "PATH": "/usr/bin:/bin",
        "APCA_API_KEY_ID": "test-key",
        "APCA_API_SECRET_KEY": "test-secret",
    }
    result = subprocess.run(
        [sys.executable, str(CLI), "live", "--config", str(config), "--state-db", str(db_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    assert result.returncode == 1
    assert "RECOVERY_REQUIRED" in result.stdout
    assert "PAPER" in result.stdout, "the mode actually used must be reported"
    # BOTH wordings, because the docstring above already says both paths
    # are correct: "with network the connection check fails on a 401,
    # without network it fails on a transport error". The assertion used
    # to accept only the online phrasing, so it contradicted the contract
    # it was written to enforce and failed offline for the one reason the
    # docstring says is fine. Widened to match the stated contract, not
    # loosened to go green -- returncode, RECOVERY_REQUIRED and PAPER are
    # all still asserted exactly.
    accepted = ("connection check failed", "broker connection failed")
    assert any(phrase in result.stderr for phrase in accepted), (
        f"stderr must name a connection failure; got: {result.stderr[:300]!r}"
    )


def test_live_honest_failure_still_persists_state(tmp_path):
    """Even though live cannot connect to a real broker, the ledger
    store it opens along the way must be real and durable -- confirmed
    by inspecting the SQLite file directly, not just trusting the exit
    message."""
    import sqlite3

    config = tmp_path / "config.yaml"
    config.write_text(
        "strategy:\n  strategy_id: fixed\n  strategy_params: {allocation_pct: 0.05}\n"
        "grid:\n  steps: [0.01]\n  profit_targets: [0.005]\n"
        "live:\n  enabled: true\n  paper_trading: true\n"
    )
    db_path = tmp_path / "ledger.db"
    _run("live", "--config", str(config), "--state-db", str(db_path))

    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    for required in ("ledger_lots", "revisions", "processed_events"):
        assert required in tables


def test_live_missing_config_file_fails_clearly(tmp_path):
    result = _run(
        "live", "--config", "/nonexistent/config.yaml", "--state-db", str(tmp_path / "l.db")
    )
    assert result.returncode == 2
    assert "not found" in result.stderr.lower()


def test_dockerfile_exists_and_uses_the_correct_entrypoint():
    content = (REPO_ROOT / "Dockerfile").read_text()
    assert 'ENTRYPOINT ["python", "cli.py"]' in content
    # Must match pyproject.toml's requires-python floor, not a rounded default.
    assert "python:3.12-slim" in content
    assert "VOLUME" in content


def test_dockerfile_python_version_matches_pyproject_floor():
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'requires-python = ">=3.12"' in pyproject
    assert "python:3.12-slim" in dockerfile


def test_dockerignore_excludes_secrets_and_state():
    content = (REPO_ROOT / ".dockerignore").read_text()
    for pattern in (".env", ".git", "state/", "*.db"):
        assert pattern in content


def test_compose_file_defines_all_three_services_and_uses_env_file_for_live():
    content = (REPO_ROOT / "docker-compose.yml").read_text()
    for service in ("test:", "backtest:", "live:"):
        assert service in content
    assert "env_file" in content, (
        "live service must source credentials from an env file, never inline"
    )
    assert (
        ".env" not in content.split("env_file")[0]
    )  # .env is not committed/baked in above the env_file line


def test_the_shipped_deployment_configs_are_valid_and_complete():
    """The staging/production configs the containers actually run must
    stay loadable and carry the live parameters the trading loop needs.

    Guards the deployment specifically: a config change that breaks
    these would otherwise only surface when a container failed to start
    in a 24/7 deployment, which is the worst place to find out.
    """
    from src.config import BacktestConfig

    for name, expected_paper in (("staging", True), ("production", False)):
        path = REPO_ROOT / "config" / f"{name}.yaml"
        assert path.exists(), f"{name}.yaml is referenced by docker-compose.yml"
        config = BacktestConfig.from_yaml(str(path))
        config.validate()
        assert config.live.enabled is True
        assert config.live.paper_trading is expected_paper
        assert config.live.step is not None, "the live loop refuses to run without live.step"
        assert config.live.profit_target is not None


def test_production_config_is_the_only_one_routing_real_capital():
    """A staging config that silently pointed at real capital is the
    single most expensive configuration mistake available here."""
    from src.config import BacktestConfig

    staging = BacktestConfig.from_yaml(str(REPO_ROOT / "config" / "staging.yaml"))
    assert staging.live.paper_trading is True, "staging must never touch real capital"


def test_run_trading_loop_drives_ticks_and_shuts_down_cleanly(tmp_path, monkeypatch):
    """Covers the cli-to-loop seam in-process.

    This wiring is not reachable by the subprocess tests above, because
    they never get past CONNECT_BROKER with bogus credentials -- and it
    is exactly where a stale import already slipped through once (the
    loop referenced load_live_credentials from the wrong scope, which
    would have crashed the moment a real container reached READY).
    """
    import importlib

    from src.persistence import LedgerStore
    from src.risk_manager import CircuitBreaker
    from src.runtime_lifecycle import RuntimeLifecycle
    from tests.integration.test_live_trading_loop import (
        FakeBroker,
        FakeMarketData,
        make_config,
    )

    cli = importlib.import_module("cli")
    monkeypatch.setenv("APCA_API_KEY_ID", "k")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "s")

    market = FakeMarketData()
    market.push(100.0)
    monkeypatch.setattr(
        "src.alpaca_market_data.AlpacaMarketData", lambda *a, **kw: market, raising=True
    )

    store = LedgerStore(str(tmp_path / "ledger.db"))
    breaker = CircuitBreaker(store=store)
    lifecycle = RuntimeLifecycle(store=store, circuit_breaker=breaker)

    class Args:
        max_ticks = 2

    broker = FakeBroker()
    broker.trading_client = object()
    rc = cli._run_trading_loop(Args(), make_config(), broker, store, breaker, lifecycle)
    assert rc == 0


def _bayesian_live_config(target_return, profit_target, **strategy_extra):
    from src.config import BacktestConfig

    return BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": "bayesian_dual_scale",
                "strategy_params": {
                    "max_trade_pct": 0.05,
                    "target_return": target_return,
                    "horizon_days": 1.0,
                    "bars_per_day": 100,
                    "fast_half_life_days": 1.0,
                    "slow_half_life_days": 5.0,
                    **strategy_extra,
                },
            },
            "grid": {"steps": [0.003], "profit_targets": [profit_target]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
            "live": {
                "enabled": True,
                "paper_trading": True,
                "step": 0.01,
                "profit_target": profit_target,
                "poll_interval_seconds": 1.0,
            },
        }
    )


def test_a_live_target_return_mismatch_is_rejected_before_the_loop_starts(monkeypatch):
    """Same cross-check as the sweep path, applied to the single
    parameter set real capital would actually trade."""
    import importlib

    from src.exceptions import ConfigurationError
    from tests.integration.test_live_trading_loop import FakeBroker, FakeMarketData

    cli = importlib.import_module("cli")
    market = FakeMarketData()
    monkeypatch.setattr(
        "src.alpaca_market_data.AlpacaMarketData", lambda *a, **kw: market, raising=True
    )

    class Args:
        max_ticks = 1

    broker = FakeBroker()
    broker.trading_client = object()
    config = _bayesian_live_config(target_return=0.02, profit_target=0.005)

    with pytest.raises(ConfigurationError, match="target_return=0.02"):
        cli._run_trading_loop(Args(), config, broker, None, None, None)


def test_a_matching_live_target_return_starts_the_loop(monkeypatch):
    import importlib

    from src.persistence import LedgerStore
    from src.risk_manager import CircuitBreaker
    from src.runtime_lifecycle import RuntimeLifecycle
    from tests.integration.test_live_trading_loop import FakeBroker, FakeMarketData

    cli = importlib.import_module("cli")
    monkeypatch.setenv("APCA_API_KEY_ID", "k")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "s")
    market = FakeMarketData()
    market.push(100.0)
    monkeypatch.setattr(
        "src.alpaca_market_data.AlpacaMarketData", lambda *a, **kw: market, raising=True
    )

    class Args:
        max_ticks = 1

    broker = FakeBroker()
    broker.trading_client = object()
    config = _bayesian_live_config(target_return=0.005, profit_target=0.005)
    store = LedgerStore(":memory:")
    breaker = CircuitBreaker(store=store)
    lifecycle = RuntimeLifecycle(store=store, circuit_breaker=breaker)

    rc = cli._run_trading_loop(Args(), config, broker, store, breaker, lifecycle)
    assert rc == 0


def test_allow_target_return_mismatch_lets_a_live_deployment_start(monkeypatch):
    import importlib

    from src.persistence import LedgerStore
    from src.risk_manager import CircuitBreaker
    from src.runtime_lifecycle import RuntimeLifecycle
    from tests.integration.test_live_trading_loop import FakeBroker, FakeMarketData

    cli = importlib.import_module("cli")
    monkeypatch.setenv("APCA_API_KEY_ID", "k")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "s")
    market = FakeMarketData()
    market.push(100.0)
    monkeypatch.setattr(
        "src.alpaca_market_data.AlpacaMarketData", lambda *a, **kw: market, raising=True
    )

    class Args:
        max_ticks = 1

    broker = FakeBroker()
    broker.trading_client = object()
    config = _bayesian_live_config(
        target_return=0.02, profit_target=0.005, allow_target_return_mismatch=True
    )
    store = LedgerStore(":memory:")
    breaker = CircuitBreaker(store=store)
    lifecycle = RuntimeLifecycle(store=store, circuit_breaker=breaker)

    rc = cli._run_trading_loop(Args(), config, broker, store, breaker, lifecycle)
    assert rc == 0

    assert rc == 0
    assert lifecycle.state.value == "STOPPED", "shutdown must complete, not abandon state"


def test_fetch_data_help_exits_zero():
    result = _run("fetch-data", "--help")
    assert result.returncode == 0
    assert "--symbol" in result.stdout


def test_fetch_data_requires_a_window():
    """--days or --start/--end: without one the window is undefined and
    the command must refuse rather than guess a default range."""
    result = _run("fetch-data", "--symbol", "TQQQ")
    assert result.returncode != 0
    assert "--days" in result.stderr


def test_fetch_data_without_credentials_fails_before_any_network(tmp_path):
    """Credential loading happens before the first request, so a
    missing key is a clean exit 2 naming the variable -- not a stack
    trace from deep inside the SDK."""
    result = subprocess.run(
        [sys.executable, str(CLI), "fetch-data", "--symbol", "TQQQ", "--days", "5"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": "/usr/bin:/bin"},  # explicitly no APCA_* credentials
    )
    assert result.returncode == 2
    assert "APCA_API_KEY_ID" in result.stderr


def test_fetch_data_rejects_an_unknown_timeframe(tmp_path):
    """Fails on the timeframe before spending a network round trip."""
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "fetch-data",
            "--symbol",
            "TQQQ",
            "--days",
            "5",
            "--timeframe",
            "1Fortnight",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": "/usr/bin:/bin", "APCA_API_KEY_ID": "k", "APCA_API_SECRET_KEY": "s"},
    )
    assert result.returncode == 2
    assert "1Day" in result.stderr, "the error should list the valid timeframes"


def test_the_data_directory_is_git_ignored():
    """Downloads are tens of MB and must never be committable.

    This guards a real gap: .gitignore's comment claimed to cover data/
    while the rule was actually missing, so the directory was
    committable and stayed untracked only by being empty.
    """
    result = subprocess.run(
        ["git", "check-ignore", "-v", "data/TQQQ_1Min_latest.csv"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "data/ must be git-ignored"
    assert ".gitignore" in result.stdout


def test_env_files_stay_out_of_the_docker_build_context():
    """.env / *.env do not match .env.staging, so the per-environment
    credential files were entering the build context and being baked
    into the image by `COPY . .`. Pin the fix.
    """
    patterns = [
        line.strip()
        for line in (REPO_ROOT / ".dockerignore").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    import fnmatch

    for name in (".env", ".env.staging", ".env.production"):
        assert any(fnmatch.fnmatch(name, p) for p in patterns), (
            f"{name} would enter the Docker build context"
        )


FIDELITY_ARTIFACTS = (
    # Playwright storage_state: cookies + localStorage for an
    # AUTHENTICATED brokerage session, plaintext. fidelity-api writes it
    # into the CWD on every close_browser() unless save_state=False.
    "Fidelity.json",
    "Fidelity_staging.json",
    # Playwright trace, written when debug=True -- records .fill()
    # arguments, i.e. the username and password in cleartext.
    "fidelity_trace.zip",
    "fidelity_tracestaging.zip",
    # Downloaded holdings/statements.
    "Portfolio_Positions_Aug-29-2026.csv",
    # fidelity_recon.py's traffic dump: captured authenticated-session
    # traffic. Written to ~/.fidelity_recon by default, but --artifact-dir
    # can point at the repo.
    "recon_20260829_153000.json",
)


def test_fidelity_session_artifacts_are_git_ignored():
    """fidelity-api writes credential-equivalent files into the working
    directory by default. The real fix is save_state=False and an
    explicit profile_path outside the repo -- this pins the defense in
    depth, so a mistake there is still not committable."""
    import subprocess

    for name in FIDELITY_ARTIFACTS:
        result = subprocess.run(
            ["git", "check-ignore", "-v", name],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{name} is NOT git-ignored -- it could be committed"


def test_fidelity_session_artifacts_stay_out_of_the_docker_build_context():
    """Same artifacts, same reasoning as the .env case above: `COPY . .`
    would otherwise bake a live brokerage session into the image."""
    patterns = [
        line.strip()
        for line in (REPO_ROOT / ".dockerignore").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    import fnmatch

    for name in FIDELITY_ARTIFACTS:
        assert any(fnmatch.fnmatch(name, p) for p in patterns), (
            f"{name} would enter the Docker build context"
        )


def test_fidelity_dependencies_are_exactly_pinned():
    """Unlike requirements.txt's floors. playwright-sm in particular is
    a single-release, solo-maintainer package that runs in-process with
    an authenticated brokerage browser context -- a floating version
    there would auto-adopt any future release unreviewed."""
    content = (REPO_ROOT / "requirements-fidelity.txt").read_text()
    pinned = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert pinned, "requirements-fidelity.txt declares no dependencies"
    for line in pinned:
        assert "==" in line, f"{line!r} is not exactly pinned"
    for package in ("fidelity-api", "playwright-sm", "playwright", "pyotp"):
        assert any(line.startswith(package + "==") for line in pinned), (
            f"{package} missing an exact pin"
        )


def test_playwright_is_not_in_the_main_requirements():
    """It would be installed into every Docker image by the Dockerfile's
    `pip install -r requirements.txt`, for containers that only run
    backtests -- and be unusable there anyway without a separate
    `playwright install` for the browser binary."""
    main_requirements = (REPO_ROOT / "requirements.txt").read_text()
    declared = [
        line.strip()
        for line in main_requirements.splitlines()
        if line.strip() and not line.startswith("#")
    ]
    for line in declared:
        assert not line.lower().startswith(("playwright", "fidelity-api", "pyotp")), (
            f"{line!r} belongs in requirements-fidelity.txt, not requirements.txt"
        )


def test_backtest_with_return_full_results_does_not_crash(config_path, data_path):
    """Regression test: output.return_full_results=True makes
    run_sweep return (summary_df, full_results) instead of a bare
    DataFrame. cmd_backtest previously called results.head(10)
    unconditionally and crashed with AttributeError on the tuple --
    caught while running a real sweep, not a synthetic case."""
    config = config_path.parent / "config_full.yaml"
    config.write_text(config_path.read_text() + "output:\n  return_full_results: true\n")
    result = _run("backtest", "--config", str(config), "--data", str(data_path))
    assert result.returncode == 0, result.stderr
    assert "combination(s) evaluated" in result.stdout
    assert "does not yet write them to disk" in result.stdout
