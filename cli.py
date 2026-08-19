#!/usr/bin/env python3
"""
Single entrypoint for running this project inside a container (or
locally). Three subcommands cover everything the project can honestly
do today:

  cli.py test [pytest args...]     Run the test suite. Extra arguments
                                    pass straight to pytest (e.g.
                                    `cli.py test -k my_test -v`) -- do
                                    not prefix them with `--`, which
                                    pytest itself treats as "everything
                                    after this is a file path", not as
                                    a separator to strip.
  cli.py backtest --config C --data D [--output O]
                                    Run a parameter sweep.
  cli.py live --config C            Validate config/credentials and run
                                    the startup sequence against
                                    persisted state.

Kept as one file rather than three, so the Dockerfile has exactly one
ENTRYPOINT and "run everything" is genuinely one image.

On `live`: this project has no concrete broker adapter (no class
implements the LiveBroker protocol anywhere in src/ -- confirmed by
grep before writing this, not assumed). `live` therefore cannot place
a real order. What it CAN do, honestly, is the part that exists:
validate the config, verify credentials are present, open persistent
ledger/audit storage, and run the startup lifecycle (Task 7.12)
through to its real, correct outcome -- which is RECOVERY_REQUIRED,
because connecting to a broker is a step this codebase does not
implement. Reporting that plainly is preferable to stubbing a fake
connection that would misrepresent what the system can do.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

# strategy_id -> class. BacktestConfig only stores the id as a string
# (Task 6.1); this is the same manual mapping Run_Instructions
# documents, since the codebase has no id-to-class registry.
STRATEGY_REGISTRY = {}


def _load_strategy_registry() -> dict:
    if not STRATEGY_REGISTRY:
        from src.size_calculators import FixedPortfolioPercentage

        STRATEGY_REGISTRY["fixed"] = FixedPortfolioPercentage
    return STRATEGY_REGISTRY


def cmd_test(pytest_args: list[str]) -> int:
    """Run pytest, forwarding arguments verbatim.

    Deliberately NOT parsed through argparse's subparsers: nargs=REMAINDER
    fails to capture a leading option-like token when no positional
    precedes it (a known argparse limitation) -- verified directly,
    `cli.py test -q` raised "unrecognized arguments: -q" while
    `cli.py test some/path.py -q` worked, which is exactly backwards
    from what a user expects for `cli.py test [pytest args...]`, and
    `-q` is the single most common invocation. sys.argv is read
    directly instead, which has no such failure mode.
    """
    cmd = [sys.executable, "-m", "pytest", *pytest_args]
    print(f"+ {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode


def cmd_backtest(args: argparse.Namespace) -> int:
    """Run a parameter sweep from a YAML config against a CSV."""
    import pandas as pd

    from src.config import BacktestConfig
    from src.exceptions import ConfigurationError

    config_path = Path(args.config)
    data_path = Path(args.data)
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 2
    if not data_path.exists():
        print(f"Data file not found: {data_path}", file=sys.stderr)
        return 2

    config = BacktestConfig.from_yaml(str(config_path))
    try:
        config.validate()
    except ConfigurationError as e:
        print(f"Invalid config: {e}", file=sys.stderr)
        return 2

    registry = _load_strategy_registry()
    if config.strategy.strategy_id not in registry:
        known = ", ".join(sorted(registry))
        print(
            f"Unknown strategy_id {config.strategy.strategy_id!r}. Known: {known}",
            file=sys.stderr,
        )
        return 2
    strategy_class = registry[config.strategy.strategy_id]

    df = pd.read_csv(data_path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)

    from optimization_controller import OptimizationController

    controller = OptimizationController(historical_data=df)
    results = controller.run_sweep(**config.to_run_sweep_kwargs(strategy_class))

    pd.set_option("display.width", 200)
    print(results.head(10).to_string())
    print(f"\n{len(results)} combination(s) evaluated.")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(out_path, index=False)
        print(f"Full results written to {out_path}")
    return 0


def cmd_live(args: argparse.Namespace) -> int:
    """Validate config/credentials and run the startup lifecycle.

    Does not and cannot submit a real order -- see module docstring.
    """
    from src.config import BacktestConfig
    from src.exceptions import ConfigurationError
    from src.persistence import LedgerStore
    from src.risk_manager import CircuitBreaker
    from src.runtime_lifecycle import RuntimeLifecycle
    from src.secrets import load_live_credentials

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 2

    config = BacktestConfig.from_yaml(str(config_path))
    try:
        config.validate()
    except ConfigurationError as e:
        print(f"Invalid config: {e}", file=sys.stderr)
        return 2
    if not config.live.enabled:
        print("Config has live.enabled: false -- nothing to start.", file=sys.stderr)
        return 2

    registry = _load_strategy_registry()
    if config.strategy.strategy_id not in registry:
        known = ", ".join(sorted(registry))
        print(
            f"Unknown strategy_id {config.strategy.strategy_id!r}. Known: {known}", file=sys.stderr
        )
        return 2

    db_path = args.state_db
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    store = LedgerStore(db_path)
    circuit_breaker = CircuitBreaker(store=store)
    lifecycle = RuntimeLifecycle(store=store, circuit_breaker=circuit_breaker)

    def _connect_broker():
        # Credential presence IS checked here -- that much is real and
        # required before anything else. What is not implemented is an
        # actual network connection: no class in this codebase
        # implements the LiveBroker protocol against a real Alpaca
        # account. Raising, rather than silently returning, is what
        # sends the lifecycle honestly into RECOVERY_REQUIRED.
        load_live_credentials()
        raise RuntimeError(
            "Credentials are valid, but no broker adapter is implemented in this "
            "codebase (no class implements src.live_execution.LiveBroker against a "
            "real account) -- see CHANGELOG.md. Startup correctly stops here rather "
            "than pretending to connect."
        )

    final_state = lifecycle.start(connect_broker=_connect_broker)
    store.close()

    print(f"Runtime state: {final_state.value}")
    if final_state.value == "READY":
        print("READY, but no order can actually be submitted (see above).")
        return 0
    print("Did not reach READY -- this is the expected, honest outcome today.")
    return 1


def main() -> int:
    # `test` is special-cased ahead of argparse -- see cmd_test's
    # docstring for why. Every other invocation (including bare
    # `cli.py`, `cli.py --help`, `cli.py test --help`) falls through
    # to the normal parser below unchanged.
    if len(sys.argv) >= 2 and sys.argv[1] == "test" and "--help" not in sys.argv[2:3]:
        return cmd_test(sys.argv[2:])

    parser = argparse.ArgumentParser(prog="cli.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_test = sub.add_parser("test", help="Run the test suite (see: cli.py test --help)")
    p_test.set_defaults(func=lambda args: cmd_test([]))

    p_backtest = sub.add_parser("backtest", help="Run a parameter sweep")
    p_backtest.add_argument("--config", required=True, help="Path to a BacktestConfig YAML file")
    p_backtest.add_argument("--data", required=True, help="Path to historical OHLCV CSV")
    p_backtest.add_argument(
        "--output", default=None, help="Optional path to write full results CSV"
    )
    p_backtest.set_defaults(func=cmd_backtest)

    p_live = sub.add_parser(
        "live", help="Validate config/credentials and run startup (no real orders)"
    )
    p_live.add_argument("--config", required=True, help="Path to a BacktestConfig YAML file")
    p_live.add_argument(
        "--state-db",
        default="/app/state/ledger.db",
        help="Path to the persistent SQLite ledger store",
    )
    p_live.set_defaults(func=cmd_live)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
