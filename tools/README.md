# tools/

Scripts that are **not** part of the trading or backtesting path —
nothing in `src/` imports anything here, and a live run never calls one.

They live here rather than in the repository root because the root is
for what you run routinely (`cli.py`, `run_hf_sweep.py`,
`analyze_annual.py`, `resample_uniform.py`, `analyze_har.py`,
`fidelity_recon.py`, `dashboard.py`). These you run once, occasionally,
or only when a specific question comes up.

> This file previously described the directory as "one-off
> data-preparation scripts" and tabled three of them. There are now
> thirty-six, in three quite different categories with different risk
> profiles — the **operations** group touches live trading, the rest
> cannot. The directory was fine; its map was wrong, which is the more
> misleading of the two.

They are deliberately kept flat rather than split into subdirectories:
roughly 130 command lines across `README.md`, `plan.md` and `docs/`
name these paths, and several scripts import each other
(`stage2_grid.py` ← `indicator_sweep`, `probe_stage3_engine`,
`probe_regime_integrated`). A tidier tree is not worth invalidating the
documentation that makes them findable.

---

## Operations — these touch a live or paper deployment

| Script | Does |
|---|---|
| `preflight.py` | Verify a machine can actually run the live loop, **before** it trades. |
| `market_hours_supervisor.py` | Run the live loop for one trading session, then exit. |
| `adopt_broker_position.py` | Write an existing broker position into the local ledger so startup can reconcile. |
| `install_paper_service.ps1` | Register the paper supervisor as a daily Windows scheduled task. |
| `run_paper_session.cmd` | The task's entry point on Windows. |
| `docker_session_loop.sh` | The same session loop inside the Raspberry Pi container. |
| `backup_databases.py` | Snapshot every local database (SQLite ledger + `warehouse/*.duckdb`), archive it under `backups/`, and scp it to the Pi. `--install-daily` schedules it. See below. |

### Database backups

`backup_databases.py` is one file doing snapshot → archive → push → prune.
Each engine gets the right method: SQLite via `sqlite3`'s online
`.backup()` (safe while the live loop writes every tick), DuckDB by
copying the file while holding a read-only handle open (which blocks a
sweep from starting mid-copy; if one already holds it, that DB is
skipped with a non-zero exit rather than a torn copy).

    python tools/backup_databases.py --local-only            # just the archive
    python tools/backup_databases.py --remote-host pi@172.16.0.137
    python tools/backup_databases.py --install-daily --at 03:30

The push is `scp` (Git ships it; `rsync` it does not) over
`BatchMode=yes` SSH, so key auth must be non-interactive. Set the target
once with `$VAI_BACKUP_REMOTE` / `$VAI_BACKUP_REMOTE_DIR` or pass
`--remote-host` / `--remote-dir`; `--install-daily` bakes the resolved
values into a Windows Scheduled Task (`VolatilityAI-DbBackup`) or a cron
line. `--keep N` (default 14) trims old archives at both ends. The
Parquet lakes are left out by default as regenerable — `--include
warehouse/executions` folds the non-regenerable trade blotters back in.

## Data preparation — produces inputs the rest of the project consumes

| Script | Produces |
|---|---|
| `build_earnings_calendar.py` | `data/earnings_releases_derived.csv`. **Load-bearing for a fresh checkout** — `data/` is git-ignored, so this is absent after a clone and `src/event_calendar.py` needs it. Makes network requests; slow. |
| `pull_extended_history.py` | Extended-hours minute datasets under `data/`, year by year. |
| `export_strategy_curves.py` | One JSON blob of every strategy measured here, for the dashboard and the artifact. |
| `build_warehouse.py` | `warehouse/` — two DuckDB catalogs plus ZSTD Parquet lakes for bars (`ticker/year`), macro series (`provider/series_key`) and trade executions (`simulation_id`). Needs `requirements-warehouse.txt`; prints an install hint and exits 2 without it, so a core-only checkout is unaffected. See below. |

### The warehouse

`build_warehouse.py --ingest-all` turns the CSVs in `data/` into a
queryable store: ~7.4M bars compress to ~87 MB of Parquet plus ~0.7M
`data/external/` macro rows to ~6 MB, and the `.duckdb` files stay ~2 MB
because they are catalogs, not data stores.

    python tools/build_warehouse.py --ingest-all --events   # bars + events + external
    python tools/build_warehouse.py --external              # just data/external/
    python cli.py backtest --config C --data D --warehouse
    python tools/build_warehouse.py --top 20
    python tools/build_warehouse.py --explain-execution <simulation_id>
    python tools/build_warehouse.py --explain-series fred_DGS10 TQQQ

The `--warehouse` flag on `cli.py backtest` / `cli.py search` records
every combination *and its trade blotter* — the blotter that
`cli.py:150` used to say it had no writer for. `--explain-execution`
runs an `ASOF JOIN` matching each fill to the market bar in force at
that instant, which is what makes recorded slippage checkable against
`src/analysis/cost_models.py`'s assumptions. `--explain-series` does the
same for a macro series, but **lag-aware**: `external_series.lag_days`
(from `data/external/manifest.json`) shifts each observation to its
publication time before the match, so a bar never joins a FRED print
that did not exist yet.

Unlike every other script here, this one has a library behind it
(`src/warehouse/`) because `cli.py` imports the sink too. The
`tools/`-scripts-are-never-imported-by-`src/` rule still holds: nothing
in `src/` imports *this file*.

## Research — measurements and probes. Read-only; they answer questions

Shared plumbing: `harness.py` (probe scaffolding) and `session_bars.py`
(session aggregation). `check_syntax.py` asserts every `.py` in the repo
parses.

**Use `harness.py` rather than re-typing what is in it.** It holds the
dataset paths and `load_bars()` (parquet-cached, ~12x faster than a bare
`read_csv` of the 1M-row TQQQ file), the `Escalating` strategy, the
`escalation()` formula, and `DrawdownEscalation` -- a mixin for probes
that are a *different* strategy but embed the same escalate-into-drawdown
mechanism. Two tests in
`tests/unit/test_tools_are_importable.py` enforce this: one pins that
`Escalating` has a single definition, the other scans every script's
executable code (docstrings stripped, since several legitimately
describe the formula in prose) and fails if the formula or the
trailing-peak update is written anywhere but `harness.py`.

**The staged indicator sweep** — see `plan.md`, which records each
stage's result and the prediction it was read against:

| Script | Question |
|---|---|
| `indicator_sweep.py` | Stages 1–2 in a long/cash shell: brute-force every TA-Lib indicator over two instruments. |
| `indicator_exit_study.py` | What each indicator says about *selling* — when, and for how much. |
| `probe_stage3_engine.py` | The shell's survivors through the real engine on minute bars. Found the shell was answering a different question. |
| `stage1_grid.py` | Stage 1 redone inside the grid engine, where the strategy actually lives. |
| `stage2_grid.py` | Are the grid-native leaders ridges, or single lucky cells? |
| `stage3_grid.py` | Is the leader about the signal, or about the exit policy? (Matched-random control.) |
| `stage4_leverage.py` | Does the effect track leverage? A falsifiable prediction, recorded before the run. |

**Instrument and regime selection:**

| Script | Question |
|---|---|
| `screen_instruments.py` | Which candidates suit this strategy's real constraints? |
| `screen_daily_fitness.py` | Which instruments suit a volatility-harvesting grid, on daily bars? |
| `probe_rsp_alternatives.py` | RSP: is there anything that beats simply holding it? |
| `probe_regime_signals.py` | Which regime indicator actually gets you out of 2022, and at what cost? |
| `probe_regime_integrated.py` | The regime strategy as ONE simulation rather than two spliced return streams. |
| `probe_regime_combo.py` | Trend-follow in bull, deep-dip escalate in bear. |
| `probe_vol_filtered_regime.py` | Hold the trend only when trend and volatility agree. |
| `probe_bull_capture.py` | Why the regime book captures ~1/3 of the benchmark in every bull year. |
| `probe_downturn_tactics.py` | TQQQ: which tactic actually makes money *through* a drawdown? |
| `probe_escalating_risk.py` | Lot size scaling with the underlying's drawdown. |
| `probe_sqqq_stop.py` | Does a stoppable SQQQ hedge work now that a loss can be realised? (No.) |

**Costs and signals the backtest does not model:**

| Script | Question |
|---|---|
| `measure_cash_drag.py` | What is the 0%-cash assumption costing the measurement? |
| `probe_settlement_drag.py` | What does T+1 settlement cost the strategies under consideration? |
| `measure_hedge_conditions.py` | Under what conditions can a hedge leg be bought and later sold at a profit? |
| `measure_event_effects.py` | Does a candidate event class actually move volatility? |
| `measure_vol_signal.py` | Does forward-looking implied vol beat the backward-looking measure? |
| `measure_regime_filter.py` | Can a strategy be positive in every calendar year, including the worst? |

`experiments/` holds the shell wrappers that drove earlier sweep
batches; see its own README.

---

## Running them

Both forms work:

    python tools/build_earnings_calendar.py
    python -m tools.pull_extended_history

Scripts that import from `src/` need the repo root on `sys.path`, and
Python puts the *script's* directory on `sys.path[0]` rather than the
working directory — so `python tools/x.py` would fail on `from src...`
while `python -m tools.x` succeeded. Each carries a small repo-root
bootstrap so neither invocation surprises anyone.
