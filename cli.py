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

On `live`: src/alpaca_broker.py implements the LiveBroker protocol
against a real Alpaca account, so `live` now genuinely connects,
verifies credentials against an authenticated endpoint, and
reconciles persisted local state against the broker before reaching
READY. Whether it talks to the paper or the real-capital endpoint is
decided by `live.paper_trading` in the config file -- a committed,
reviewable value rather than a shell flag.

Reaching READY means startup succeeded; it does not by itself mean
the strategy is trading. Driving ticks through LiveExecutionLoop is
the caller's job, and Mode.LIVE still requires paper-trading
promotion evidence (Task 7.7) before real capital is reachable at all.
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
    """Connect to Alpaca and run the startup lifecycle to READY."""
    from src.alpaca_broker import AlpacaBroker
    from src.config import BacktestConfig
    from src.exceptions import ConfigurationError
    from src.order_management_system import Mode
    from src.persistence import LedgerStore
    from src.reconciliation import Reconciler
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
    reconciler = Reconciler(store=store, circuit_breaker=circuit_breaker)
    lifecycle = RuntimeLifecycle(
        store=store, circuit_breaker=circuit_breaker, reconciler=reconciler
    )

    # PAPER vs LIVE comes from the config, not from a CLI flag: routing
    # real capital must be a reviewable, committed decision rather than
    # something typed at a shell. Mode.LIVE additionally requires
    # promotion evidence (Task 7.7), enforced where that gate lives.
    mode = Mode.PAPER if config.live.paper_trading else Mode.LIVE

    # The broker is built INSIDE connect_broker, not before the
    # lifecycle starts. Credential loading and the connection check are
    # both failure modes the lifecycle is designed to absorb into
    # RECOVERY_REQUIRED -- constructing outside would turn a missing
    # env var into an uncaught traceback instead, losing the graceful
    # path and the persisted state that comes with it.
    connected: dict = {}

    def _connect_broker():
        broker = AlpacaBroker.from_mode(mode, load_live_credentials())
        # ping() rather than a bare construction: TradingClient does no
        # I/O in its constructor, so a bad key would otherwise pass
        # CONNECT_BROKER and only fail at the first real order.
        broker.ping()
        connected["broker"] = broker

    final_state = lifecycle.start(
        connect_broker=_connect_broker,
        broker_snapshot_provider=lambda: connected["broker"].snapshot(),
    )
    store.close()

    print(f"Runtime state: {final_state.value}")
    print(f"Mode: {mode.value}")
    if final_state.value == "READY":
        print("READY -- broker connected and local state reconciles with the broker.")
        return 0
    print(
        "Did not reach READY. The state above names the stage that stopped startup; "
        "RECONCILIATION_REQUIRED means local and broker state disagree and a human "
        "must resolve it before trading resumes."
    )
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

    p_live = sub.add_parser("live", help="Connect to Alpaca and run the startup lifecycle")
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
