#!/usr/bin/env python3
"""
Single entrypoint for running this project inside a container (or
locally). Five subcommands cover everything the project can honestly
do today:

  cli.py test [pytest args...]     Run the test suite. Extra arguments
                                    pass straight to pytest (e.g.
                                    `cli.py test -k my_test -v`) -- do
                                    not prefix them with `--`, which
                                    pytest itself treats as "everything
                                    after this is a file path", not as
                                    a separator to strip.
  cli.py fetch-data --symbol S --days N
                                    Download historical bars from Alpaca
                                    into a backtest-ready CSV in data/.
  cli.py backtest --config C --data D [--output O]
                                    Run an exhaustive parameter sweep.
  cli.py search --config C --data D --trials N
                                    Adaptive (Optuna TPE) search over a
                                    space too large to enumerate, logging
                                    trials in execution order.
  cli.py live --config C            Connect, reconcile, then trade until
                                    signalled. --check-only runs startup
                                    and exits; --max-ticks bounds the run.

Kept as one file rather than three, so the Dockerfile has exactly one
ENTRYPOINT and "run everything" is genuinely one image.

On `live`: src/alpaca_broker.py implements the LiveBroker protocol
against a real Alpaca account, so `live` now genuinely connects,
verifies credentials against an authenticated endpoint, and
reconciles persisted local state against the broker before reaching
READY. Whether it talks to the paper or the real-capital endpoint is
decided by `live.paper_trading` in the config file -- a committed,
reviewable value rather than a shell flag.

Once READY, `live` enters src/live_trading_loop.py's tick loop and
runs until SIGTERM/SIGINT, then shuts down through the Task 7.12
sequence -- settling in-flight orders and persisting state rather than
dying mid-fill. That signal handling is what makes a container with
restart:unless-stopped safe to `docker stop`.

Mode.LIVE still requires paper-trading promotion evidence (Task 7.7)
before real capital is reachable at all.
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
    """Delegates to src/strategy_registry.py.

    Kept as a function so the import stays lazy (the CLI's startup
    cost matters for `cli.py test`), but the table itself now lives in
    src/ where the library, not just this entrypoint, can reach it.
    """
    if not STRATEGY_REGISTRY:
        from src.strategy_registry import STRATEGIES

        STRATEGY_REGISTRY.update(STRATEGIES)
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

    # output.return_full_results=True makes run_sweep return
    # (summary_df, full_results) instead of summary_df alone -- a real
    # config option, not something specific to any one config file.
    # Unpacking it here (rather than only in the summary-only branch)
    # is what makes that flag usable from this entrypoint at all; before
    # this, any config setting it crashed on results.head(10) because
    # results was the tuple, not the DataFrame.
    full_results = None
    if isinstance(results, tuple):
        results, full_results = results

    pd.set_option("display.width", 200)
    print(results.head(10).to_string())
    print(f"\n{len(results)} combination(s) evaluated.")
    if full_results is not None:
        # Per-combination blotters/equity curves exist only in memory
        # here -- cli.py has no writer for them yet. Said plainly rather
        # than silently discarding what the config asked for.
        print(
            f"output.return_full_results is set: {len(full_results)} per-combination result "
            "object(s) were produced but cli.py does not yet write them to disk. Use the "
            "Python API (OptimizationController.run_sweep) directly to access them."
        )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(out_path, index=False)
        print(f"Full results written to {out_path}")
    return 0


def cmd_fetch_data(args: argparse.Namespace) -> int:
    """Download historical bars into a CSV the backtest can consume.

    Kept a separate command from `backtest` on purpose. Auto-fetching
    inside a backtest would put implicit network I/O behind a command
    whose whole value is reproducibility -- two runs of the same
    invocation would silently compare different data.
    """
    from src.exceptions import ConfigurationError, DataValidationError, TradingSystemError
    from src.historical_data import (
        AlpacaHistoricalData,
        FetchSpec,
        download,
        median_bar_interval_seconds,
        resolve_window,
        validate_timeframe,
    )
    from src.secrets import load_live_credentials

    try:
        start, end = resolve_window(days=args.days, start=args.start, end=args.end)
        # Validated HERE, not left to download(). parse_timeframe is
        # otherwise first reached inside fetch_bars
        # (src/historical_data.py), which runs AFTER the network client is
        # built and the first request is in flight -- so a bad
        # --timeframe was diagnosed only if the network happened to work,
        # and surfaced as whatever transport error came first if it did
        # not. That made an argument error's exit code depend on
        # connectivity.
        validate_timeframe(args.timeframe)
        credentials = load_live_credentials()
    except ConfigurationError as e:
        print(f"{e}", file=sys.stderr)
        return 2

    spec = FetchSpec(
        symbol=args.symbol.upper(),
        start=start,
        end=end,
        timeframe=args.timeframe,
        feed=args.feed,
        adjustment=args.adjustment,
        regular_hours_only=not args.include_extended_hours,
    )
    print(
        f"Fetching {spec.symbol} {spec.timeframe} bars "
        f"{start.date()} -> {end.date()} (feed={spec.feed}, adjustment={spec.adjustment}, "
        f"{'regular hours only' if spec.regular_hours_only else 'including extended hours'})..."
    )

    try:
        report = download(
            spec,
            out_path=Path(args.output) if args.output else None,
            market_data=AlpacaHistoricalData(credentials=credentials),
            data_dir=Path(args.output_dir),
            force=args.force,
        )
    except DataValidationError as e:
        print(f"No usable data: {e}", file=sys.stderr)
        return 2
    except ConfigurationError as e:
        print(f"{e}", file=sys.stderr)
        return 2
    except TradingSystemError as e:
        print(f"Download failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        # The two failures most likely to land here are worth naming
        # explicitly rather than leaving the user to decode an APIError.
        text = str(e)
        if "subscription" in text.lower():
            print(
                f"Market-data subscription error: {e}\n"
                "The 'sip' feed needs a paid subscription, and free accounts also cannot read "
                "SIP data from the last 15 minutes. Use --feed iex (the default), which every "
                "account has -- and which is what the live loop reads anyway.",
                file=sys.stderr,
            )
            return 2
        if "unauthorized" in text.lower() or "forbidden" in text.lower():
            print(
                f"Alpaca rejected the credentials: {e}\n"
                "Check APCA_API_KEY_ID / APCA_API_SECRET_KEY.",
                file=sys.stderr,
            )
            return 2
        print(f"Download failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    import pandas as pd

    df = pd.read_csv(report.path, parse_dates=["timestamp"]).set_index("timestamp")
    interval = median_bar_interval_seconds(df)

    print(f"\nWrote {report.path}  ({report.path.stat().st_size / 1e6:.1f} MB)")
    print(f"  rows            : {report.rows:,}")
    print(f"  range           : {report.first_timestamp}  ->  {report.last_timestamp}")
    print(f"  trading days    : {report.trading_days}")
    if interval is not None:
        print(f"  median interval : {interval:.0f}s")
    if report.dropped_extended_hours:
        print(f"  dropped (ext hrs): {report.dropped_extended_hours:,}")
    if report.dropped_duplicates:
        print(f"  dropped (dupes) : {report.dropped_duplicates:,}")
    print(f"  sha256          : {report.sha256[:16]}...")
    print(
        f"\nRun a sweep against it:\n"
        f"  python cli.py backtest --config config/staging.yaml --data {report.path}"
    )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Adaptive parameter search, logging trials in the order they run.

    Separate from `backtest` for a concrete reason: run_sweep sorts
    both summary_df and full_results by rank_by before returning, so
    its output is in RANKED order and the explore-then-exploit
    progression of an adaptive search is invisible in it. This drives
    BayesianSearch.suggest()/report() directly -- the same inner loop
    run_sweep(n_jobs=1) uses -- and records each trial as it happens,
    before any sorting.

    It also constructs BayesianSearch itself rather than passing
    search_strategy="bayesian", which is the documented way to set a
    trial budget: the string form defaults n_trials to the FULL
    combination count, which is meaningless for a space of millions.
    """
    import time

    import pandas as pd

    from optimization_controller import OptimizationController, _run_one_combination
    from src.config import BacktestConfig, expand_strategy_params
    from src.exceptions import ConfigurationError
    from src.search_strategies import BayesianSearch
    from src.strategy_registry import resolve_strategy

    config_path = Path(args.config)
    data_path = Path(args.data)
    for label, path in (("Config", config_path), ("Data", data_path)):
        if not path.exists():
            print(f"{label} file not found: {path}", file=sys.stderr)
            return 2

    config = BacktestConfig.from_yaml(str(config_path))
    try:
        config.validate()
        strategy_class = resolve_strategy(config.strategy.strategy_id)
    except ConfigurationError as e:
        print(f"Invalid config: {e}", file=sys.stderr)
        return 2

    params_grid = expand_strategy_params(config.strategy.strategy_params)
    grid_steps = list(config.grid.steps)
    profit_targets = list(config.grid.profit_targets)
    total_space = len(grid_steps) * len(profit_targets) * len(params_grid)

    search = BayesianSearch(
        grid_steps,
        profit_targets,
        params_grid,
        rank_by=config.search.rank_by,
        direction=config.search.direction,
        n_trials=args.trials,
        seed=config.search.seed,
    )

    print(f"Search space : {total_space:,} combinations")
    print(f"Trial budget : {args.trials} ({100 * args.trials / total_space:.4f}% of the space)")
    print(f"Objective    : {config.search.rank_by} ({config.search.direction})")
    print(f"Strategy     : {config.strategy.strategy_id} -> {strategy_class.__name__}")
    if search.decomposed:
        print(f"Search axes  : grid_step, profit_target, {', '.join(search.search_axis_names)}")
    else:
        # Worth saying loudly: the index fallback cannot converge on
        # strategy params, so a search that looks like it is not
        # narrowing is explained by this line rather than by the data.
        print("Search axes  : grid_step, profit_target, strategy_params (OPAQUE INDEX --")
        print("               params grid is not a cartesian product, so per-key")
        print("               search is unavailable and strategy params cannot converge)")
    print()

    df = pd.read_csv(data_path, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=df)
    cost_model = config.costs.build()
    risk_manager = config.risk.build()

    rows, trial_log = [], []
    started = time.time()
    trial_number = 0
    while True:
        suggestion = search.suggest()
        if suggestion is None:
            break
        trial_number += 1
        t0 = time.time()
        row, sim_result = _run_one_combination(
            controller,
            suggestion["grid_step"],
            suggestion["profit_target"],
            strategy_class,
            suggestion["strategy_params"],
            config.backtest.symbol,
            config.backtest.initial_cash,
            cost_model,
            risk_manager,
            config.execution.on_flat_reentry,
        )
        search.report(suggestion, sim_result)
        rows.append(row)

        objective = None if "error" in row else row.get(config.search.rank_by)
        trial_log.append(
            {
                "trial": trial_number,
                "objective": objective,
                "grid_step": suggestion["grid_step"],
                "profit_target": suggestion["profit_target"],
                **suggestion["strategy_params"],
                "elapsed_s": round(time.time() - t0, 3),
            }
        )
        if trial_number % args.log_every == 0 or trial_number <= 10:
            shown = f"{objective:9.3f}" if objective is not None else "   FAILED"
            best = max(
                (t["objective"] for t in trial_log if t["objective"] is not None), default=None
            )
            best_str = f"{best:9.3f}" if best is not None else "     n/a"
            phase = "random" if trial_number <= 10 else "TPE   "
            print(
                f"[{trial_number:4d}/{args.trials}] {phase} obj={shown}  best={best_str}  "
                f"step={suggestion['grid_step']:.4f} target={suggestion['profit_target']:.4f}  "
                f"({time.time() - started:.0f}s elapsed)"
            )

    elapsed = time.time() - started
    print(
        f"\n{trial_number} trials in {elapsed:.0f}s ({elapsed / max(1, trial_number):.2f}s/trial)"
    )

    results = pd.DataFrame(rows)
    ascending = config.search.direction == "minimize"
    if config.search.rank_by in results.columns:
        results = results.sort_values(
            config.search.rank_by, ascending=ascending, na_position="last"
        ).reset_index(drop=True)
    pd.set_option("display.width", 250)
    print(f"\nTop 10 by {config.search.rank_by}:")
    print(results.head(10).to_string())

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(out, index=False)
        print(f"\nRanked results -> {out}")
    if args.trial_log:
        log_path = Path(args.trial_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(trial_log).to_csv(log_path, index=False)
        print(f"Trial-order log -> {log_path}")
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

    # ONE LOOP PER STORE. Two live loops against the same state store
    # submit duplicate orders, and DuplicateOrderGuard cannot catch it:
    # its decision_id is derived from symbol, side and bar timestamp, so
    # both loops compute the SAME id on the same bar and each believes
    # it is the one submitting it. Acquired before the store is opened,
    # so a refusal costs nothing and leaves no partial state.
    from src.process_lock import LockHeldError, StateStoreLock

    lock = StateStoreLock(db_path)
    try:
        lock.acquire()
    except LockHeldError as exc:
        print(f"\n{exc}\n", file=sys.stderr)
        return 2

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

    print(f"Runtime state: {final_state.value}")
    print(f"Mode: {mode.value}")
    if final_state.value != "READY":
        store.close()
        lock.release()
        print(
            "Did not reach READY. The state above names the stage that stopped startup; "
            "RECONCILIATION_REQUIRED means local and broker state disagree and a human "
            "must resolve it before trading resumes."
        )
        return 1

    print("READY -- broker connected and local state reconciles with the broker.")
    if args.check_only:
        store.close()
        lock.release()
        return 0

    try:
        return _run_trading_loop(
            args, config, connected["broker"], store, circuit_breaker, lifecycle
        )
    finally:
        # finally, not after the return: a loop that raises must not
        # leave a lock naming a live PID that is about to not exist.
        lock.release()


def _run_trading_loop(args, config, broker, store, circuit_breaker, lifecycle) -> int:
    """Run the tick loop until a signal stops it, then shut down cleanly.

    Split from cmd_live so the startup path stays readable: everything
    above this point is "can we safely trade at all", everything below
    is "trade until told to stop".
    """
    import signal

    from src.alpaca_market_data import AlpacaMarketData
    from src.live_trading_loop import LiveTradingLoop
    from src.secrets import load_live_credentials

    strategy_class = _load_strategy_registry()[config.strategy.strategy_id]
    strategy = strategy_class(**config.strategy.strategy_params)

    # Same cross-check optimization_controller._run_one_combination
    # applies per sweep combination -- see BayesianDualScaleSizing's
    # module docstring, "THE TARGET_RETURN / PROFIT_TARGET CROSS-CHECK".
    # Here it is target_return against the SINGLE parameter the live
    # loop actually trades (config.live.profit_target), not a sweep
    # value -- real capital confidently estimating the probability of
    # hitting the wrong number is the same silent failure, live.
    from src.exceptions import ConfigurationError

    # live.profit_target can still be None here -- BacktestConfig.validate()
    # deliberately does not require it (a config may set live.enabled
    # without running the daemon), and LiveTradingLoop.__init__ below is
    # what raises the clearer "both required" error for that case. Guard
    # against it here so a missing value isn't misreported as a
    # "mismatch" against None.
    declared_target = getattr(strategy, "target_return", None)
    mismatch_allowed = getattr(strategy, "allow_target_return_mismatch", False)
    if (
        declared_target is not None
        and config.live.profit_target is not None
        and declared_target != config.live.profit_target
        and not mismatch_allowed
    ):
        raise ConfigurationError(
            f"{config.strategy.strategy_id}'s target_return={declared_target} does not match "
            f"live.profit_target={config.live.profit_target} -- the posterior would be "
            "confidently estimating the probability of hitting a different price than the one "
            "this deployment actually trades. Set target_return to match live.profit_target, "
            "or pass allow_target_return_mismatch=True in strategy_params to confirm the "
            "mismatch is deliberate."
        )

    market_data = AlpacaMarketData(
        feed=config.live.feed,
        # The clock is a trading-API endpoint, so it comes from the
        # connection the broker already authenticated rather than a
        # second one.
        trading_client=broker.trading_client,
        credentials=load_live_credentials(),
    )

    loop = LiveTradingLoop(
        config=config,
        strategy=strategy,
        broker=broker,
        market_data=market_data,
        store=store,
        circuit_breaker=circuit_breaker,
    )

    # SIGTERM is how `docker stop` asks a container to exit, so handling
    # it is what makes restart:unless-stopped safe: the loop finishes
    # the tick it is in, settles in-flight orders, and persists -- rather
    # than being killed midway through applying a confirmed fill.
    def _handle_signal(signum, _frame):
        print(f"\nReceived signal {signum} -- finishing the current tick.", file=sys.stderr)
        loop.request_stop()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    # SIGBREAK is the ONLY graceful stop Windows can deliver to a
    # detached process: taskkill without /F does not reach a console
    # application, and Process.terminate() is a hard kill that would
    # land mid-tick. A supervisor there sends CTRL_BREAK_EVENT to the
    # process group, which arrives here as SIGBREAK. Without this the
    # Windows path had no way to stop the loop cleanly at all.
    if hasattr(signal, "SIGBREAK"):  # Windows only
        signal.signal(signal.SIGBREAK, _handle_signal)

    print(
        f"Trading loop started: symbol={config.backtest.symbol} step={config.live.step} "
        f"profit_target={config.live.profit_target} feed={config.live.feed} "
        f"interval={config.live.poll_interval_seconds}s"
    )
    exit_code = 0
    try:
        ticks = loop.run_forever(max_ticks=args.max_ticks)
        print(f"Trading loop stopped after {ticks} tick(s).")
    except Exception as e:
        # Never exit silently on a trading error -- the shutdown
        # sequence below still runs so in-flight state is settled and
        # persisted rather than abandoned.
        print(f"Trading loop aborted: {type(e).__name__}: {e}", file=sys.stderr)
        exit_code = 1

    final = lifecycle.shutdown(
        in_flight_settled=loop.in_flight_settled,
        persist_state=loop.persist_state,
        close_connections=store.close,
    )
    print(f"Shutdown state: {final.value}")
    if final.value != "STOPPED":
        # RECONCILIATION_REQUIRED here means in-flight orders did not
        # settle in the bounded window; the next startup must reconcile.
        return 1
    return exit_code


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

    p_fetch = sub.add_parser("fetch-data", help="Download historical bars for backtesting")
    p_fetch.add_argument("--symbol", required=True, help="Ticker to download, e.g. TQQQ")
    window = p_fetch.add_mutually_exclusive_group(required=True)
    window.add_argument("--days", type=int, help="Look back this many days from now")
    window.add_argument("--start", help="Window start (ISO 8601); requires --end")
    p_fetch.add_argument("--end", help="Window end (ISO 8601); used with --start")
    p_fetch.add_argument(
        "--timeframe",
        default="1Min",
        help="Bar size: 1Min, 5Min, 15Min, 30Min, 1Hour, 1Day (default: 1Min). "
        "Match this to live.poll_interval_seconds -- grid steps tuned on daily bars "
        "produce almost no trades on minute bars.",
    )
    p_fetch.add_argument(
        "--feed",
        default="iex",
        help="Data feed (default: iex). Use iex unless you hold a paid SIP subscription: "
        "the live loop can only read iex, so backtesting on sip tunes parameters against "
        "a tape production cannot see.",
    )
    p_fetch.add_argument(
        "--adjustment",
        default="all",
        choices=("raw", "split", "dividend", "all"),
        help="Corporate-action adjustment (default: all). Anything less than split "
        "adjustment makes a split look like a ~66%% single-bar crash.",
    )
    p_fetch.add_argument(
        "--include-extended-hours",
        action="store_true",
        help="Keep pre/post-market bars. Off by default: the live loop only trades the "
        "regular session, so those bars are ones it can never act on.",
    )
    p_fetch.add_argument("--output", default=None, help="Explicit output CSV path")
    p_fetch.add_argument(
        "--output-dir", default="data", help="Directory for output (default: data)"
    )
    p_fetch.add_argument(
        "--force", action="store_true", help="Overwrite an existing file of the same name"
    )
    p_fetch.set_defaults(func=cmd_fetch_data)

    p_search = sub.add_parser(
        "search", help="Adaptive (Bayesian/TPE) parameter search with trial-order logging"
    )
    p_search.add_argument("--config", required=True, help="Path to a BacktestConfig YAML file")
    p_search.add_argument("--data", required=True, help="Path to historical OHLCV CSV")
    p_search.add_argument(
        "--trials",
        type=int,
        default=200,
        help="Trial budget (default: 200). The first 10 are TPE's random startup phase.",
    )
    p_search.add_argument("--output", default=None, help="Path for ranked results CSV")
    p_search.add_argument(
        "--trial-log",
        default=None,
        help="Path for a CSV of trials in EXECUTION order (shows explore->exploit)",
    )
    p_search.add_argument(
        "--log-every", type=int, default=10, help="Print progress every N trials (default: 10)"
    )
    p_search.set_defaults(func=cmd_search)

    p_live = sub.add_parser("live", help="Connect to Alpaca and run the startup lifecycle")
    p_live.add_argument("--config", required=True, help="Path to a BacktestConfig YAML file")
    p_live.add_argument(
        "--state-db",
        default="/app/state/ledger.db",
        help="Path to the persistent SQLite ledger store",
    )
    p_live.add_argument(
        "--check-only",
        action="store_true",
        help="Run startup and reconciliation, then exit without trading (health check)",
    )
    p_live.add_argument(
        "--max-ticks",
        type=int,
        default=None,
        help="Stop after N ticks instead of running until signalled",
    )
    p_live.set_defaults(func=cmd_live)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
