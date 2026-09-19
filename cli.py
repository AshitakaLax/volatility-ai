#!/usr/bin/env python3
"""
Single entrypoint for running this project inside a container (or
locally). Ten subcommands cover everything the project can honestly
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
                                    into data/, the intake format for
                                    `tools/build_warehouse.py --ingest S`.
  cli.py backtest --config C [--output O]
                                    Run an exhaustive parameter sweep
                                    against C's `backtest.symbol` bars,
                                    read from the warehouse.
  cli.py search --config C --trials N
                                    Adaptive (Optuna TPE) search over a
                                    space too large to enumerate, logging
                                    trials in execution order.
  cli.py submit --config C          Hand C to the server's shard queue
                                    instead of running it here -- for a
                                    sweep too big for one process, or one
                                    to watch drain across shards in the
                                    browser. Needs `cli.py serve` running.
  cli.py live --config C            Connect, reconcile, then trade until
                                    signalled. --check-only runs startup
                                    and exits; --max-ticks bounds the run.
  cli.py backup                    Snapshot the DuckDB warehouse and push
                                    it to the Raspberry Pi as a tar.gz.
  cli.py restore [ARCHIVE]         Fetch a warehouse backup (local path,
                                    or from the Pi) and overwrite the
                                    current warehouse databases with it.
  cli.py serve                     Start the backend backtest engine
                                    (server/app.py, FastAPI) that web/
                                    talks to. --reload for local dev.
  cli.py shard --name N --main H   Join the backtest engine at H as an
                                    extra machine: claim queued sweeps,
                                    run them here, report each result.

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
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

# `backup`/`restore`'s default push/pull target -- the Raspberry Pi this
# project deploys to (see docs/DEPLOY_RASPBERRY_PI.md). Overridable with
# --remote-host or $VAI_BACKUP_REMOTE; tools/backup_databases.py (which
# these two commands delegate to) deliberately has no default of its own,
# but a CLI meant to be run without flags needs one.
DEFAULT_PI_REMOTE = "ashitakalax@172.16.0.137"

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
        from src.trading.strategy_registry import STRATEGIES

        STRATEGY_REGISTRY.update(STRATEGIES)
    return STRATEGY_REGISTRY


def _open_result_sink(args: argparse.Namespace, config, dataset_version: str):
    """Wire up the DuckDB warehouse for one sweep, or return None.

    Returns {"sink", "finalize"} rather than the sink alone because the
    lake VIEWs can only be (re)created once the sweep has actually
    written a Parquet file into them -- read_parquet over an empty glob
    is an error at CREATE VIEW time. finalize() runs after the sweep.

    Never fatal: a warehouse is an addition to a sweep, not a
    precondition for one. A missing dependency or an unwritable
    directory prints a warning and the sweep runs exactly as it would
    have without the flag.

    `dataset_version` identifies the BAR DATA this sweep ran against --
    now `src.warehouse.bars.fingerprint(ticker)`, since the simulation
    read path is the market-data warehouse itself, not a CSV with a
    `.meta.json` sidecar to hash.
    """
    try:
        # Probed directly: src.warehouse imports duckdb/polars lazily, so
        # importing it succeeds even where neither is installed and the
        # real failure would surface later as a traceback rather than
        # the actionable message below.
        import duckdb  # noqa: F401
        import polars  # noqa: F401

        from src.warehouse import schema
        from src.warehouse.connection import open_warehouse
        from src.warehouse.duckdb_sink import DuckDBResultSink, ensure_broker_environment
        from src.warehouse.hashing import broker_id_for
    except ImportError as e:
        print(
            f"--warehouse needs its optional dependencies ({e}); "
            "run `pip install -r requirements-warehouse.txt`. Continuing without it.",
            file=sys.stderr,
        )
        return None

    try:
        root = Path(args.warehouse)
        con = open_warehouse(root)
        schema.initialize(con, root)

        version = dataset_version
        broker_id = broker_id_for(config.costs)
        ensure_broker_environment(con, broker_id, config.costs, f"{config.costs.model_type} costs")

        sink = DuckDBResultSink(con, root, dataset_version=version)
        sink.open_sweep(
            algorithm=config.search.strategy,
            base_parameters=config.to_dict(),
            broker_id=broker_id,
            dataset_version=version,
        )
        print(f"Warehouse: {root} (dataset_version={version[:12]}, broker={broker_id})")

        def finalize() -> None:
            schema.refresh_views(con, root)
            stats = sink.stats
            print(
                f"Warehouse recorded {stats['recorded']} simulation(s), "
                f"{stats['failed']} failed, {stats['skipped_duplicate']} already present, "
                f"{stats['errors']} storage error(s)."
            )
            con.close()

        return {"sink": sink, "finalize": finalize}
    except Exception as e:
        print(
            f"Could not open the warehouse ({type(e).__name__}: {e}). Continuing without it.",
            file=sys.stderr,
        )
        return None


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


def _apply_backtest_window(df, config):
    """Slice `df` (timestamp-indexed) to `config.backtest.start_date` /
    `end_date`, or return it unchanged if neither is set.

    FOUND BY RUNNING A SWEEP, NOT BY READING THE SCHEMA: `BacktestConfig`
    parses and round-trips `start_date`/`end_date` (src/core/config.py's
    `from_dict`/`to_dict`), but until this existed NOTHING in the CLI
    path read them back. `cli.py backtest`/`search` handed
    OptimizationController the FULL CSV regardless of what a config's
    `backtest:` block said -- config/search_soxl_regime_bayesian.yaml's
    `start_date: "2024-01-01"` silently searched all 10.6 years of
    history instead of the intended held-out post-training-cutoff
    window, and every threshold candidate in that sweep produced
    IDENTICAL trade counts across wildly different values, which is what
    surfaced this: a config field that LOOKS load-bearing and is quietly
    inert should never fail silently like that again.

    server/backtest.py's `window()` already solved this correctly for
    the HTTP path (`RunRequest.start`/`.end`) and is not imported here on
    purpose -- `server/` depends on `src/` and `cli.py`, not the other
    way around, and cli.py must keep working without FastAPI installed.
    The slicing rule is duplicated rather than shared through a new
    module for two lines of logic; if a THIRD call site needs it, that
    is the point to extract one.

    `end_date` covers the WHOLE day, matching `window()`'s own
    convention: a config author writing "2024-01-01" means that day
    included, not excluded at its first instant.
    """
    start, end = config.backtest.start_date, config.backtest.end_date
    if start:
        df = df[df.index >= _to_utc_timestamp(start)]
    if end:
        import pandas as pd

        df = df[df.index < _to_utc_timestamp(end) + pd.Timedelta(days=1)]
    return df


def _to_utc_timestamp(value: str):
    import pandas as pd

    # A naive date string ("2024-01-01") localizes to UTC directly.
    # `tz="UTC"` on an ALREADY-aware string would raise rather than
    # convert, so a value that already carries an offset is converted
    # instead -- config authors here have written only naive dates so
    # far, but a future one should not fail confusingly.
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _load_warehouse_bars(ticker: str) -> tuple[object | None, str | None]:
    """A ticker's full bar history from the warehouse, or (None, None).

    The ONLY way `backtest`/`search` read historical bars -- there is no
    CSV fallback. A ticker gets into the warehouse via `cli.py fetch-data`
    (downloads bars into `data/`) followed by `tools/build_warehouse.py
    --ingest TICKER` (loads them into `warehouse/`); backtesting itself
    never touches `data/`.

    Returns the fingerprint alongside the frame because that is this
    project's dataset-identity value now (see `_open_result_sink`) --
    computing it here means every caller gets it for free instead of
    reopening the warehouse a second time.
    """
    from src.warehouse.bars import available_tickers, fingerprint, load_frame

    df = load_frame(ticker)
    if df.empty:
        known = ", ".join(sorted(available_tickers())) or "(none ingested yet)"
        print(
            f"No warehouse data for {ticker!r}. Available: {known}.\n"
            f"Fetch it with `python cli.py fetch-data --symbol {ticker} --days N`, "
            f"then ingest it with `python tools/build_warehouse.py --ingest {ticker}`.",
            file=sys.stderr,
        )
        return None, None
    return df, fingerprint(ticker)


def cmd_backtest(args: argparse.Namespace) -> int:
    """Run a parameter sweep from a YAML config against the warehouse."""
    import pandas as pd

    from src.core.config import BacktestConfig
    from src.core.exceptions import ConfigurationError

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

    registry = _load_strategy_registry()
    if config.strategy.strategy_id not in registry:
        known = ", ".join(sorted(registry))
        print(
            f"Unknown strategy_id {config.strategy.strategy_id!r}. Known: {known}",
            file=sys.stderr,
        )
        return 2
    strategy_class = registry[config.strategy.strategy_id]

    df, dataset_version = _load_warehouse_bars(config.backtest.symbol)
    if df is None:
        return 2
    df = _apply_backtest_window(df, config)

    from src.optimization.optimization_controller import OptimizationController

    controller = OptimizationController(historical_data=df)
    sweep_kwargs = config.to_run_sweep_kwargs(strategy_class)

    # Optional durable storage. Imported only when asked for: duckdb and
    # polars live in requirements-warehouse.txt, and `cli.py backtest`
    # must keep working on a machine that has never installed them.
    warehouse = (
        _open_result_sink(args, config, dataset_version)
        if getattr(args, "warehouse", None)
        else None
    )
    if warehouse is not None:
        sweep_kwargs["result_sink"] = warehouse["sink"]

    try:
        results = controller.run_sweep(**sweep_kwargs)
    finally:
        if warehouse is not None:
            warehouse["sink"].close_sweep()
            warehouse["finalize"]()

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
    """Download historical bars into data/, the warehouse's intake format.

    This is intake, not backtesting: `backtest`/`search` read bars from
    the warehouse (`src/warehouse/bars.py`) and never touch `data/`
    directly. A freshly fetched symbol becomes visible to them only
    after `tools/build_warehouse.py --ingest SYMBOL` loads this file in.

    Kept a separate command from `backtest` on purpose. Auto-fetching
    inside a backtest would put implicit network I/O behind a command
    whose whole value is reproducibility -- two runs of the same
    invocation would silently compare different data.
    """
    from src.core.exceptions import ConfigurationError, DataValidationError, TradingSystemError
    from src.core.secrets import load_live_credentials
    from src.data.historical_data import (
        AlpacaHistoricalData,
        FetchSpec,
        download,
        median_bar_interval_seconds,
        resolve_window,
        validate_timeframe,
    )

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
        f"\nLoad it into the warehouse, then run a sweep against it:\n"
        f"  python tools/build_warehouse.py --ingest {spec.symbol}\n"
        f"  python cli.py backtest --config config/staging.yaml"
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

    from src.core.config import BacktestConfig, expand_strategy_params
    from src.core.exceptions import ConfigurationError
    from src.optimization.optimization_controller import (
        OptimizationController,
        _run_one_combination,
    )
    from src.optimization.search_strategies import BayesianSearch
    from src.trading.strategy_registry import resolve_strategy

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
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

    df, dataset_version = _load_warehouse_bars(config.backtest.symbol)
    if df is None:
        return 2
    df = _apply_backtest_window(df, config)
    if config.backtest.start_date or config.backtest.end_date:
        # Printed explicitly, not left implicit -- a windowed search
        # that silently searched the whole file was exactly the bug
        # _apply_backtest_window's docstring records finding.
        print(
            f"Date window  : {config.backtest.start_date or 'file start'} -> "
            f"{config.backtest.end_date or 'file end'} ({len(df):,} bars)"
        )
    controller = OptimizationController(historical_data=df)
    cost_model = config.costs.build()
    risk_manager = config.risk.build()

    # This command drives the inner loop itself rather than calling
    # run_sweep, so it wires the sink here rather than inheriting
    # run_sweep's hook. Same contract, same parent-process guarantee.
    warehouse = (
        _open_result_sink(args, config, dataset_version)
        if getattr(args, "warehouse", None)
        else None
    )
    sink = warehouse["sink"] if warehouse else None

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
        if sink is not None:
            sink.record(row=row, sim_result=sim_result, elapsed_ms=int((time.time() - t0) * 1000))

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

    if warehouse is not None:
        sink.close_sweep()
        warehouse["finalize"]()

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
    from src.brokers.alpaca_broker import AlpacaBroker
    from src.core.config import BacktestConfig
    from src.core.exceptions import ConfigurationError
    from src.core.persistence import LedgerStore
    from src.core.secrets import load_live_credentials
    from src.execution.order_management_system import Mode
    from src.execution.reconciliation import Reconciler
    from src.trading.risk_manager import CircuitBreaker
    from src.trading.runtime_lifecycle import RuntimeLifecycle

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
    from src.core.process_lock import LockHeldError, StateStoreLock

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

    from src.core.secrets import load_live_credentials
    from src.data.alpaca_market_data import AlpacaMarketData
    from src.trading.live_trading_loop import LiveTradingLoop

    strategy_class = _load_strategy_registry()[config.strategy.strategy_id]
    strategy = strategy_class(**config.strategy.strategy_params)

    # Same cross-check optimization_controller._run_one_combination
    # applies per sweep combination -- see BayesianDualScaleSizing's
    # module docstring, "THE TARGET_RETURN / PROFIT_TARGET CROSS-CHECK".
    # Here it is target_return against the SINGLE parameter the live
    # loop actually trades (config.live.profit_target), not a sweep
    # value -- real capital confidently estimating the probability of
    # hitting the wrong number is the same silent failure, live.
    from src.core.exceptions import ConfigurationError

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


def cmd_backup(args: argparse.Namespace) -> int:
    """Snapshot the DuckDB warehouse and push it to the Raspberry Pi.

    Scoped to the two warehouse catalogs (market_data.duckdb,
    sim_results.duckdb) rather than tools/backup_databases.py's full
    default set (which also covers the SQLite live ledger) -- this
    command is `cli.py`'s entrypoint for the warehouse specifically, the
    thing a workstation actually accumulates hours of sweep compute
    into. Delegates every mechanic (online-safe snapshotting, archiving,
    scp push, pruning) to that script rather than reimplementing it.
    """
    import tempfile

    from src.warehouse.connection import MARKET_DATA_DB, SIM_RESULTS_DB
    from tools.backup_databases import build_archive, prune_local, push_to_remote, snapshot_all

    warehouse_dir = Path(args.warehouse)
    databases = [
        warehouse_dir / name
        for name in (MARKET_DATA_DB, SIM_RESULTS_DB)
        if (warehouse_dir / name).exists()
    ]
    if not databases:
        print(
            f"No warehouse databases found under {warehouse_dir} "
            f"(looked for {MARKET_DATA_DB}, {SIM_RESULTS_DB}).",
            file=sys.stderr,
        )
        return 1

    extra_paths = []
    if args.include_executions:
        executions_dir = warehouse_dir / "executions"
        if not executions_dir.exists():
            print(f"--include-executions: no such directory ({executions_dir})", file=sys.stderr)
            return 2
        extra_paths.append(executions_dir)

    print(f"Snapshotting {len(databases)} warehouse database(s) from {warehouse_dir}:")
    with tempfile.TemporaryDirectory(prefix="vai-warehouse-backup-") as tmp:
        workdir = Path(tmp)
        entries, errors = snapshot_all(databases, workdir)
        if not entries:
            print("Nothing was snapshotted successfully.", file=sys.stderr)
            return 1
        archive = build_archive(workdir, entries, extra_paths, Path(args.out_dir))

    prune_local(Path(args.out_dir), args.keep)

    pushed = False
    if args.local_only:
        print("  (--local-only: not pushing)")
    elif not args.remote_host:
        print(
            "  no --remote-host / $VAI_BACKUP_REMOTE set -- archive kept locally only",
            file=sys.stderr,
        )
    else:
        try:
            push_to_remote(
                archive, args.remote_host, args.remote_dir, args.keep, dry_run=args.dry_run
            )
            pushed = True
        except RuntimeError as e:
            print(f"  PUSH FAILED: {e}", file=sys.stderr)
            errors.append(f"push: {e}")

    if errors:
        print(f"\nCompleted with {len(errors)} problem(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    where = f"{archive}" + (" (pushed)" if pushed else " (local only)")
    print(f"\nWarehouse backup complete: {where}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    """Fetch a warehouse backup tarball (local path, or from the Pi) and
    overwrite the current warehouse databases with its contents.

    Always restores INTO --warehouse (default warehouse/), never into
    the manifest's recorded source path -- that path was captured on
    whichever machine made the backup and has no reason to exist on this
    one. A non-warehouse archive (e.g. one made by
    `tools/backup_databases.py` directly, which also backs up the live
    ledger) is filtered down to just its warehouse entries; anything else
    in it is left alone.
    """
    import tempfile

    from src.warehouse.connection import MARKET_DATA_DB, SIM_RESULTS_DB
    from tools.backup_databases import (
        extract_archive,
        pull_from_remote,
        restore_databases,
        verify_archive,
    )

    warehouse_dir = Path(args.warehouse)
    warehouse_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="vai-warehouse-restore-") as tmp:
        tmp_path = Path(tmp)
        archive_arg = args.archive
        local_candidate = Path(archive_arg).expanduser() if archive_arg else None

        if local_candidate is not None and local_candidate.exists():
            archive = local_candidate.resolve()
        else:
            if not args.remote_host:
                print(
                    "No local archive found"
                    + (f" at {archive_arg}" if archive_arg else "")
                    + " and no --remote-host / $VAI_BACKUP_REMOTE set to fetch one from.",
                    file=sys.stderr,
                )
                return 2
            name = Path(archive_arg).name if archive_arg else None
            print(
                f"Fetching {name or 'the latest archive'} from "
                f"{args.remote_host}:{args.remote_dir}..."
            )
            try:
                archive = pull_from_remote(
                    args.remote_host, args.remote_dir, tmp_path, name=name, dry_run=args.dry_run
                )
            except RuntimeError as e:
                print(f"Fetch failed: {e}", file=sys.stderr)
                return 1
            if args.dry_run:
                print("  (--dry-run: nothing was fetched or restored)")
                return 0

        print(f"Extracting {archive.name}...")
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir(exist_ok=True)
        try:
            manifest = extract_archive(archive, extract_dir)
        except RuntimeError as e:
            print(f"Invalid archive: {e}", file=sys.stderr)
            return 1

        wanted = {MARKET_DATA_DB, SIM_RESULTS_DB}
        entries = [e for e in manifest.get("databases", []) if e["name"] in wanted]
        if not entries:
            print(
                f"{archive.name} contains no warehouse databases "
                f"({MARKET_DATA_DB}, {SIM_RESULTS_DB}); nothing to restore.",
                file=sys.stderr,
            )
            return 1
        scoped_manifest = {**manifest, "databases": entries}

        problems = verify_archive(scoped_manifest, extract_dir)
        if problems:
            print("Archive failed verification:", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
            return 1

        print(
            f"Archive: {len(entries)} warehouse database(s), created "
            f"{manifest.get('created_utc', '?')} on {manifest.get('host', '?')} "
            f"(commit {(manifest.get('git_commit') or '?')[:12]})"
        )
        for entry in entries:
            print(
                f"  - {entry['name']}  ({entry['bytes']:,} bytes)  sha256={entry['sha256'][:12]}..."
            )

        if not args.yes:
            # isatty() alone is not trusted here: it has been observed to
            # misreport on a redirected-but-not-a-real-tty stdin (Git Bash
            # on Windows), which would otherwise let a non-interactive
            # caller crash on EOFError instead of failing cleanly.
            try:
                reply = input(
                    f"\nThis OVERWRITES {warehouse_dir} with the archive's contents. "
                    "Type 'restore' to continue: "
                )
            except EOFError:
                print(
                    "\nRefusing to overwrite the warehouse without --yes in a non-interactive "
                    "session.",
                    file=sys.stderr,
                )
                return 2
            if reply.strip() != "restore":
                print("Aborted -- nothing was changed.")
                return 1

        results = restore_databases(
            scoped_manifest, extract_dir, warehouse_dir, dry_run=args.dry_run
        )

        skipped = [r for r in results if r["status"] == "skipped"]
        restored = [r for r in results if r["status"] == "restored"]
        if skipped:
            print(
                f"\n{len(skipped)} database(s) skipped (open elsewhere) -- close whatever holds "
                "them (a sweep, ingest, or the dashboard) and re-run.",
                file=sys.stderr,
            )
            return 1
        print(f"\nRestore complete: {len(restored)} database(s) restored into {warehouse_dir}.")
        return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the backend backtest engine: server/app.py under uvicorn.

    This is the FastAPI process web/ talks to for /api/backtest/* (and,
    unless VAI_BACKTEST_UPSTREAM forwards them elsewhere, /api/live/* and
    /api/ml/*) -- see server/CLAUDE.md.

    RUNS UVICORN IN THIS PROCESS, NOT AS A CHILD, AND THAT IS THE FIX FOR
    A LEAK THIS COMMAND CAUSED. It first shelled out to `python -m
    uvicorn`, mirroring how cmd_test shells out to pytest. But a server
    is long-lived where pytest is not: stopping the wrapper left the
    child holding the port. On Windows terminate() is TerminateProcess,
    which runs no handler in the wrapper at all, so forwarding the signal
    could not fix it either -- five orphaned servers were found running
    after a test that did exactly this. With no child there is nothing to
    orphan: a terminate kills the server itself, and Ctrl+C reaches
    uvicorn's own handler, which drains connections and runs the lifespan
    shutdown. (`--reload` still spawns uvicorn's reloader child; that is
    uvicorn's own dev-only behavior and not something this wraps.)

    No --workers: server/jobs.py's backtest queue is a single-worker
    design whose durability (state.json, <run_id>.rows.jsonl under
    output/queue/) assumes exactly one process owns it. Multiple uvicorn
    workers would each restore and run the same queue independently --
    the same "one loop per store" hazard live trading avoids by taking a
    process lock, with no equivalent guard here.
    """
    try:
        import fastapi  # noqa: F401
        import uvicorn
    except ImportError as e:
        print(
            f"`serve` needs the web backend's dependencies ({e}); "
            "run `pip install -r requirements-web.txt`.",
            file=sys.stderr,
        )
        return 2

    print(
        f"+ uvicorn server.app:app --host {args.host} --port {args.port}"
        + (" --reload" if args.reload else ""),
        file=sys.stderr,
    )
    if args.host not in ("127.0.0.1", "localhost"):
        print(
            f"  binding {args.host}: this server has NO AUTHENTICATION and returns account "
            "balances, positions and cost bases -- only do this on a trusted network.",
            file=sys.stderr,
        )

    # The import string, not the app object: uvicorn needs one for
    # --reload, and it keeps this command's startup free of the engine
    # import until the server itself is ready to do it.
    uvicorn.run("server.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def cmd_shard(args: argparse.Namespace) -> int:
    """Join a main backtest server as a remote shard (server/shard_client.py).

    The main server must be reachable from this machine, which means it
    was started with `cli.py serve --host 0.0.0.0` (or a LAN address),
    and both machines should be on the same commit -- registration is
    refused otherwise unless --allow-version-mismatch is passed.
    """
    import re
    import signal

    try:
        import fastapi  # noqa: F401
        import httpx  # noqa: F401
    except ImportError as e:
        print(
            f"`shard` needs the web backend's dependencies ({e}); "
            "run `pip install -r requirements-web.txt`.",
            file=sys.stderr,
        )
        return 2

    from server.jobs import LOCAL_SHARD, SHARD_NAME_PATTERN

    if not re.match(SHARD_NAME_PATTERN, args.name) or args.name == LOCAL_SHARD:
        print(
            f"Invalid shard name {args.name!r}: use letters, digits, '.', '-' or '_' "
            f"(up to 64 characters, starting with a letter or digit), and not "
            f"{LOCAL_SHARD!r}, which is the main server's own worker.",
            file=sys.stderr,
        )
        return 2
    if args.max_jobs is not None:
        if args.max_jobs < 1:
            print("--max-jobs must be at least 1.", file=sys.stderr)
            return 2
        # Read by server.backtest at import, which shard_client defers
        # until the first sweep -- so setting it here is early enough.
        os.environ["VAI_MAX_JOBS"] = str(args.max_jobs)

    from server.shard_client import ShardProcess, main_url

    try:
        base = main_url(args.main, args.port)
    except ValueError as e:
        print(f"--main: {e}", file=sys.stderr)
        return 2

    cache_dir = (
        Path(args.cache_dir) if args.cache_dir else REPO_ROOT / "output" / "shard_cache" / args.name
    )
    process = ShardProcess(
        args.name,
        base,
        cache_dir=cache_dir,
        allow_version_mismatch=args.allow_version_mismatch,
    )

    # First signal: finish the configurations in flight, hand the sweep
    # back, exit. Second: exit now and let the main server's timeout
    # reassign it. SIGBREAK is Windows' graceful stop -- see cmd_live.
    signalled = {"count": 0}

    def _handle_signal(signum, _frame):
        signalled["count"] += 1
        if signalled["count"] > 1:
            print("\nSecond signal -- exiting now.", file=sys.stderr, flush=True)
            os._exit(130)
        print(
            f"\nReceived signal {signum} -- finishing in-flight configurations and handing "
            "the sweep back. Press Ctrl+C again to quit immediately.",
            file=sys.stderr,
            flush=True,
        )
        process.request_stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _handle_signal)

    print(f"Shard {args.name!r} joining {base} (instance {process.instance})", flush=True)
    return process.run_forever(max_runs=args.max_runs)


def cmd_submit(args: argparse.Namespace) -> int:
    """Submit a BacktestConfig YAML to the server's shard queue.

    The config-file/local-process split this project already has
    (`backtest`/`search` run in THIS process; `submit` hands the same
    kind of config to server/jobs.py's durable queue instead, for a
    sweep too big for one process, or one you want to watch drain
    across shards in the browser) -- no bespoke script per sweep. Any
    `BacktestConfig` YAML works; nothing here is COWZ- or
    strategy-specific.

    Chunked the same way tools/sweep_rsp_all.py already did by hand:
    server/backtest.py's build_config() cannot accept a submission
    whose combination space exceeds MAX_SWEEP_COMBINATIONS (grid) or
    MAX_SWEEP_COMBINATIONS_BAYESIAN (bayesian, 100x looser -- the whole
    point of choosing bayesian is a space too large to enumerate), so a
    config whose declared grid/strategy_params space is larger than
    that arrives here as more than one queued run, each a coherent
    slice of the same space, never as a rejected request. THESE TWO
    CONSTANTS ARE COPIED FROM server/backtest.py, NOT IMPORTED: server/
    depends on src/ and cli.py, never the reverse (see
    _apply_backtest_window's docstring for the same boundary), so
    cli.py cannot import server.backtest to read them from one place.
    Keep them in sync by hand if either changes.

    BAYESIAN_DUAL_SCALE'S target_return, GENERICALLY: any strategy
    whose target_return the server force-aligns to the grid's own
    profit_target (build_config's "mirrors" handling) refuses a
    submission that both sweeps target_return AND carries more than
    one grid profit target -- the strategy is estimating P(reaching
    ONE target), so more than one target is a different question per
    combination, not one sweep. A config authored for the LOCAL engine
    (which has no such rejection -- only a per-combination mismatch
    error, so a swept target_return there just wastes most of its
    trial budget on combinations that fail) is fanned out here into one
    submission per target_return value instead, target_return itself
    dropped so the server supplies it -- the same fix this project's
    own cowz1-bayesian_dual_scale.yaml needed by hand.
    """
    import json
    import urllib.error
    import urllib.request

    from src.core.config import BacktestConfig
    from src.core.exceptions import ConfigurationError

    # Copied from server/backtest.py -- see docstring for why this
    # cannot be an import instead.
    max_grid_combos = 2000
    max_bayes_combos = max_grid_combos * 100
    bayes_trials_ceiling = 500

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

    mode = args.search or config.search.strategy
    if mode == "random":
        print(
            "search.strategy: random has no server equivalent (RunRequest supports only "
            "grid and bayesian) -- run it locally with `cli.py search`/`run_hf_sweep.py "
            "--search random`, or pass --search grid/bayesian to override.",
            file=sys.stderr,
        )
        return 2
    is_bayesian = mode == "bayesian"
    if is_bayesian and not (2 <= args.trials <= bayes_trials_ceiling):
        print(f"--trials must be between 2 and {bayes_trials_ceiling}.", file=sys.stderr)
        return 2

    def combos(values: dict) -> int:
        n = 1
        for v in values.values():
            n *= len(v) if isinstance(v, list) else 1
        return n

    def split_axis(space: dict) -> str | None:
        multi = {k: v for k, v in space.items() if isinstance(v, list) and len(v) > 1}
        return max(multi, key=lambda k: len(multi[k])) if multi else None

    def bisect(space: dict, cap: int) -> list[dict]:
        if combos(space) <= cap:
            return [space]
        axis = split_axis(space)
        if axis is None:
            return [space]
        values = space[axis]
        mid = len(values) // 2
        left, right = dict(space), dict(space)
        left[axis], right[axis] = values[:mid], values[mid:]
        return bisect(left, cap) + bisect(right, cap)

    grid_steps = list(config.grid.steps)
    params = dict(config.strategy.strategy_params)
    target_groups = [list(config.grid.profit_targets)]
    if isinstance(params.get("target_return"), list):
        target_groups = [[v] for v in params.pop("target_return")]

    cap = max_bayes_combos if is_bayesian else max_grid_combos
    batches: list[tuple[dict, int]] = []
    for targets in target_groups:
        grid_axes = len(grid_steps) * len(targets)
        chunk_cap = max(1, cap // grid_axes)
        for chunk in bisect(params, chunk_cap):
            n = combos(chunk) * grid_axes
            batches.append(({"grid_steps": grid_steps, "targets": targets, "params": chunk}, n))

    label_base = args.name or config_path.stem
    total = len(batches)
    requests = []
    for i, (chunk, n) in enumerate(batches, start=1):
        suffix = f" [{i}/{total}]" if total > 1 else ""
        tag = f" pt={chunk['targets'][0]:.4g}" if len(target_groups) > 1 else ""
        label = f"{label_base}{suffix}{tag}"
        body = {
            "name": label,
            "tickers": [config.backtest.symbol],
            "grid_steps": chunk["grid_steps"],
            "targets": chunk["targets"],
            "model": config.strategy.strategy_id,
            "params": chunk["params"],
            "fill": config.execution.fill_model,
            "no_loss": config.execution.enforce_no_loss,
            "limit": args.limit,
            "rank_by": config.search.rank_by,
            "minimize": config.search.direction == "minimize",
        }
        if is_bayesian:
            body["bayes"] = {"trials": args.trials, "seed": config.search.seed}
        requests.append((label, body, chunk["grid_steps"], chunk["targets"], n))

    grid_total = sum(n for *_r, n in requests) if not is_bayesian else 0
    print(f"{config.backtest.symbol}: {config.execution.fill_model} fills, config={config_path}")
    if is_bayesian:
        print(f"{total} run(s), {args.trials} trials each, {total * args.trials:,} trials total\n")
    else:
        print(f"{total} run(s), {grid_total:,} combinations total\n")
    for label, _body, steps, targets, n in requests:
        print(f"  {label}  ({len(steps)} steps x {len(targets)} targets x ... = {n:,} combos)")

    if args.dry_run:
        print("\n--dry-run: nothing submitted.")
        return 0

    print()
    if not args.resubmit:
        try:
            with urllib.request.urlopen(f"{args.api}/api/backtest/history", timeout=60) as resp:
                completed = {
                    run.get("name") for run in json.loads(resp.read()).get("runs", {}).values()
                }
            with urllib.request.urlopen(f"{args.api}/api/backtest/runs", timeout=60) as resp:
                pending = {
                    (run.get("req") or {}).get("name")
                    for run in json.loads(resp.read()).get("runs", [])
                    if run.get("status") in ("queued", "running", "pausing", "paused")
                }
        except urllib.error.URLError as exc:
            print(f"UNREACHABLE {args.api}: {getattr(exc, 'reason', exc)}", file=sys.stderr)
            print("Start it with: python cli.py serve", file=sys.stderr)
            return 1
        already = completed | pending
        before = len(requests)
        for label, *_ in requests:
            if label in already:
                print(f"  skip (already handled) {label}")
        requests = [r for r in requests if r[0] not in already]
        if before != len(requests):
            print(
                f"\n{before - len(requests)} of {before} already handled; {len(requests)} to queue.\n"
            )

    ok = 0
    for label, body, *_ in requests:
        req = urllib.request.Request(
            f"{args.api}/api/backtest/runs",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                job = json.loads(resp.read())
            print(f"  queued {job['id']}  {label}", flush=True)
            ok += 1
        except urllib.error.HTTPError as exc:
            print(f"  REJECTED {label}\n    {exc.code}: {exc.read().decode()[:300]}")
        except urllib.error.URLError as exc:
            print(f"UNREACHABLE {args.api}: {exc.reason}", file=sys.stderr)
            print("Start it with: python cli.py serve", file=sys.stderr)
            return 1

    print(f"\n{ok}/{len(requests)} queued. Watch: {args.api}  (Backtesting -> Run History)")
    return 0 if ok == len(requests) else 1


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
    p_backtest.add_argument(
        "--output", default=None, help="Optional path to write full results CSV"
    )
    p_backtest.add_argument(
        "--warehouse",
        nargs="?",
        const="warehouse",
        default=None,
        metavar="DIR",
        help="Also record every combination and its trade blotter into the DuckDB "
        "warehouse at DIR (default: warehouse/). Needs requirements-warehouse.txt; "
        "without the flag nothing changes and neither dependency is imported.",
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
    p_search.add_argument(
        "--warehouse",
        nargs="?",
        const="warehouse",
        default=None,
        metavar="DIR",
        help="Also record every trial and its trade blotter into the DuckDB warehouse "
        "at DIR (default: warehouse/). Needs requirements-warehouse.txt.",
    )
    p_search.set_defaults(func=cmd_search)

    p_submit = sub.add_parser(
        "submit", help="Submit a BacktestConfig sweep to the server's shard queue"
    )
    p_submit.add_argument("--config", required=True, help="Path to a BacktestConfig YAML file")
    p_submit.add_argument("--api", default="http://127.0.0.1:8000", help="Backtest server base URL")
    p_submit.add_argument(
        "--name", default=None, help="Label prefix for queued runs (default: config filename)"
    )
    p_submit.add_argument(
        "--search",
        choices=("grid", "bayesian"),
        default=None,
        help="override the config's search.strategy (server has no 'random')",
    )
    p_submit.add_argument(
        "--trials",
        type=int,
        default=500,
        help="Bayesian trials PER CHUNK, max 500 (default: 500). Ignored for grid mode.",
    )
    p_submit.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Bar cap per configuration (default: none -- the whole file)",
    )
    p_submit.add_argument("--dry-run", action="store_true", help="Print the plan. Submits nothing.")
    p_submit.add_argument(
        "--resubmit",
        action="store_true",
        help="Queue every run, including ones already completed or pending on the server.",
    )
    p_submit.set_defaults(func=cmd_submit)

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

    p_backup = sub.add_parser("backup", help="Snapshot the DuckDB warehouse and push it to the Pi")
    p_backup.add_argument(
        "--warehouse",
        default="warehouse",
        metavar="DIR",
        help="Warehouse root (default: warehouse/)",
    )
    p_backup.add_argument(
        "--include-executions",
        action="store_true",
        help="Also fold warehouse/executions (per-fill trade blotters) into the archive",
    )
    p_backup.add_argument(
        "--out-dir",
        default="backups",
        metavar="DIR",
        help="Where local archives are written (default: backups/)",
    )
    p_backup.add_argument(
        "--keep",
        type=int,
        default=14,
        help="How many archives to retain locally and remotely (default: 14; 0 = keep all)",
    )
    p_backup.add_argument(
        "--remote-host",
        default=os.environ.get("VAI_BACKUP_REMOTE", DEFAULT_PI_REMOTE),
        metavar="USER@HOST",
        help=f"SSH target for the push (default: $VAI_BACKUP_REMOTE or {DEFAULT_PI_REMOTE})",
    )
    p_backup.add_argument(
        "--remote-dir",
        default=os.environ.get("VAI_BACKUP_REMOTE_DIR", "volatility-ai-backups"),
        metavar="DIR",
        help="Directory on the remote (default: $VAI_BACKUP_REMOTE_DIR or volatility-ai-backups)",
    )
    p_backup.add_argument(
        "--local-only", action="store_true", help="Build the archive but do not push it to the Pi"
    )
    p_backup.add_argument(
        "--dry-run", action="store_true", help="Print the ssh/scp commands instead of running them"
    )
    p_backup.set_defaults(func=cmd_backup)

    p_restore = sub.add_parser("restore", help="Restore the DuckDB warehouse from a backup tarball")
    p_restore.add_argument(
        "archive",
        nargs="?",
        default=None,
        help="Local path to a backup tar.gz, or a bare filename on the remote. Omit to fetch "
        "the newest archive from --remote-host.",
    )
    p_restore.add_argument(
        "--warehouse",
        default="warehouse",
        metavar="DIR",
        help="Warehouse root to restore INTO (default: warehouse/); an existing file is saved "
        "as <name>.pre-restore-<timestamp> before being overwritten",
    )
    p_restore.add_argument(
        "--remote-host",
        default=os.environ.get("VAI_BACKUP_REMOTE", DEFAULT_PI_REMOTE),
        metavar="USER@HOST",
        help=f"Where to fetch the archive from if not found locally "
        f"(default: $VAI_BACKUP_REMOTE or {DEFAULT_PI_REMOTE})",
    )
    p_restore.add_argument(
        "--remote-dir",
        default=os.environ.get("VAI_BACKUP_REMOTE_DIR", "volatility-ai-backups"),
        metavar="DIR",
        help="Directory on the remote to fetch from (default: $VAI_BACKUP_REMOTE_DIR or "
        "volatility-ai-backups)",
    )
    p_restore.add_argument(
        "--yes", action="store_true", help="Skip the interactive confirmation prompt"
    )
    p_restore.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fetched/restored without changing anything",
    )
    p_restore.set_defaults(func=cmd_restore)

    p_serve = sub.add_parser(
        "serve", help="Start the backend backtest engine (server/app.py) that web/ talks to"
    )
    p_serve.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1). No authentication exists -- 0.0.0.0 or a LAN "
        "address exposes account balances, positions and cost bases to that network.",
    )
    p_serve.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    p_serve.add_argument(
        "--reload",
        action="store_true",
        help="Restart the server on code changes (uvicorn --reload; local dev only)",
    )
    p_serve.set_defaults(func=cmd_serve)

    p_shard = sub.add_parser(
        "shard",
        help="Join a backtest engine as an extra machine that runs queued sweeps",
    )
    p_shard.add_argument(
        "--name", required=True, help="This shard's name as shown in the UI, e.g. fast-shard"
    )
    p_shard.add_argument(
        "--main",
        required=True,
        metavar="HOST",
        help="The main server: an IP or hostname (port from --port), host:port, or a URL. "
        "It must be started with `cli.py serve --host 0.0.0.0` to be reachable.",
    )
    p_shard.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Main server port when --main does not name one (default: 8000)",
    )
    p_shard.add_argument(
        "--cache-dir",
        default=None,
        metavar="DIR",
        help="Where downloaded bars are cached (default: output/shard_cache/<name>/, which is "
        "per shard so two on one machine never share a download)",
    )
    p_shard.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Cap the worker processes each sweep uses on this machine "
        "(default: one less than its core count)",
    )
    p_shard.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Exit after completing this many sweeps (default: run until stopped)",
    )
    p_shard.add_argument(
        "--allow-version-mismatch",
        action="store_true",
        help="Join even if this checkout's commit differs from the main server's",
    )
    p_shard.set_defaults(func=cmd_shard)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
