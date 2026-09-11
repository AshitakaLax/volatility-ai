# Changelog

## Sweep summary + per-configuration selection (Backtest result, web UI)

The result page used to show one fund's top-ranked configuration
implicitly and silently: the metrics cards, chart and trade log were
always that configuration's, with no on-screen indication a sweep had
produced any others, and the only way to look at another was
`SweepMatrix`'s heatmap (metrics-only) or clicking a cell, which jumped
to the *other* tab to stage a brand-new sweep rather than showing that
cell's own detail. Now: a **Sweep details** overview at the top (which
arguments actually varied, and by how much), a **Simulations** list of
every configuration the sweep ran, and selecting one populates the
metrics/chart/trade log below for exactly that configuration.

- Per-cell trade-level data (chart, trade log) doesn't exist on the wire
  for any configuration except the winner — an explicit, deliberate prior
  decision (`server/backtest.py`: "carrying each one's executions...
  would multiply the payload by the size of the grid"), not reopened by
  this feature. Selecting a non-winning configuration shows its
  **metrics instantly** (already shipped for every cell); the chart/trade
  log offer a **"View full detail"** button that re-runs just that one
  configuration (~23s, the existing `POST /api/backtest/runs`, no new
  backend surface) and shows its real data once that completes, cached
  per configuration for the page's lifetime. **No backend changes at
  all** — confirmed each `SweepConfiguration.strategy_params` cell
  already carries its full resolved combo (`server/backtest.py`'s
  `strategy_param_keys` covers the whole run, not just the swept subset),
  so the re-run request needs no merging.
- `lib/sweepSummary.ts` (new, pure, tested): `configurationKey()` — a
  stable per-cell identity (grid_step + profit_target + resolved
  strategy_params together) — fixes a real bug in `SweepMatrix`'s own
  narrower, pre-existing combo key (strategy_params alone), which would
  have collided two cells sharing a strategy-params combo but differing
  in grid_step/profit_target. `describeSweepAxes()` reports only the axes
  that actually varied.
- `SweepMatrix`'s cell click now selects in place (no tab navigation) —
  a strictly better version of "see this configuration's detail" than
  jumping tabs. The old capability (stage a cell into the form to launch
  a broader new sweep) is preserved, not dropped: a small per-cell "load
  into form" icon does that explicitly.

## Click-to-sort Run History columns (web UI)

Every column header in "Run history" is now clickable and cycles
ascending -> descending -> off, the same convention a spreadsheet or
data grid uses. "Off" is not a third sort of its own -- it falls back to
exactly today's "Rank by" behavior (a fixed direction per metric,
`higherIsBetter`), so a column click *overrides* that default only while
it is active, rather than replacing the concept.

- `lib/filters.ts` gains `nextRunHistorySort()` (the 3-state cycle, pure)
  and `sortHistoryRows()` (one column's sort, `null` returns the rows
  unchanged so the caller's default applies) -- both unit-tested in
  `filters.test.ts`, following this codebase's pure-function-first
  pattern rather than living inline in the component.
- The dynamic "Rank by" metric column keeps its existing default arrow
  (up when higher is better, down otherwise) until clicked; clicking it
  sorts by whichever metric is currently selected and shows the real
  direction instead.
- A `null` value (a metric absent from an older report, an unset grid
  axis) sorts LAST regardless of direction, matching the existing
  Rank-by ranking's own rule.

## Per-argument "enable sweep" + Sweep Strategy (web UI + backtest API)

Generalizes the Fixed | Sweep toggle below into a per-argument "enable
sweep" checkbox, usable on grid step, profit target, *and* any numeric
strategy param (`ParamSpec.sweepable`), each revealing a **Sweep
Strategy** dropdown: Linear, Logarithmic, Random / Monte Carlo, and two
disabled "(coming soon)" entries -- Multi-Resolution/coarse-to-fine and
Adaptive/Heuristic, which imply a coarse pass inspecting its own results
before refining, i.e. genuine multi-round orchestration nothing reachable
from the web submit path does today. Faking either as a static list
would have claimed behavior that doesn't exist, so both are stubs
(`sweepStrategies.ts`) that error rather than silently do the wrong
thing.

- `web/src/lib/sweepStrategies.ts` (new, pure, tested) holds the three
  working generators (`buildLinearSweep`/`buildLogarithmicSweep`/
  `buildRandomSweep`) plus the two stubs, unit-agnostic so grid step,
  profit target, and a strategy param all share one implementation
  instead of three copies. `gridSteps.ts`'s existing Sweep-mode math
  became a thin percent-domain wrapper over it -- `buildGridSteps` is
  byte-identical for `strategy: "linear"` (the default), so nothing
  built earlier this session regressed.
- The engine turned out to already be wired for a 3-axis sweep:
  `BacktestConfig.to_run_sweep_kwargs()` already calls
  `expand_strategy_params()` to build a `strategy_params_grid`, and
  `GridSearch` already cross-products `grid_steps × profit_targets ×
  strategy_params_grid` -- confirmed by reading the code, not assumed.
  So `server/backtest.py` needed wiring, not new engine surface:
  `RunRequest.strategy_params` already accepted a list value per key
  (`dict[str, Any]`); `build_config()` now expands it, guards against a
  swept `target_return` (would otherwise be silently discarded by the
  existing mirror-alignment code), and caps the resulting combination
  count at `MAX_SWEEP_COMBINATIONS` (2000, `VAI_MAX_SWEEP_COMBINATIONS`
  overridable); `run_backtest()`'s `combinations` count gained the third
  factor and each result cell now carries the exact `strategy_params`
  combo it ran with (`_native()` coerces the numpy scalars `summary.iterrows()`
  yields, since `history.save()` calls bare `json.dumps`); `history_rows()`
  prefers a cell's own combo over the run-level snapshot, fixing a real
  bug this feature would otherwise have introduced (every row of a swept
  run showing the same first-resolved combo).
- `describe_params()` gains `sweepable` per param
  (`type in ("int","float") and editable and mirrors is None`) --
  server-computed, matching this project's "server describes capability"
  pattern (`_apply_locks`, `describe_grid_trigger`), so `target_return`
  (mirrors the grid) and every locked/non-numeric field never render the
  checkbox.
- `SweepMatrix.tsx`'s heatmap was hard-keyed to `(grid_step, profit_target)`
  -- once a strategy param is also swept, several cells share that key.
  A "Params" selector (reusing the existing Fund-selector idiom) now
  picks which combo's 2D slice to render when more than one is present,
  rather than the old `Map` construction silently keeping only the last.

A no-edit, no-sweep submit is still byte-identical to before.

## Grid-step method + Fixed/Sweep (web UI + backtest API)

The lone "Grid step %" input in "Run a Backtest" becomes a small panel
with two orthogonal controls:

- **Fixed | Sweep** for the step *value*. Fixed is one % (as today);
  Sweep takes min / max / count and submits a sorted, de-duped
  `grid_steps` list so the engine tries them all and the Sweep Matrix /
  Run history fill in — with a live "N configurations · ~23s each"
  readout. No server change: `RunRequest.grid_steps` was already a
  1–12 `list[float]` and the sweep path already flattens per cell.
  `web/src/lib/gridSteps.ts` (pure, tested) maps the inputs to the list
  with hard client validation (0 < step < 100 %, count an integer 1–12,
  min < max, no oversized array even mid-paste).

- **Trigger method**, where the strategy has a choice: "Last buy price"
  (`last_buy_price × (1 − step)`) vs "Local reference (rolling high)"
  (`max(last_buy, N-day high) × (1 − step)` — re-fires on local dips).
  `GET /funds` gains a `grid_trigger[id]` descriptor
  (`{methods, default, controlled_by, window_param, window_default}`)
  from an explicit `_GRID_TRIGGER` map in `server/backtest.py` — this
  is *presentation* over the existing `_grid_trigger_level` override
  point, not a new engine param. `hf_local_reference` is locked to
  local-reference; `bayesian_dual_scale` is the one model that switches
  (via its optional `lookback_days`); everything else is locked to
  last-buy. A `test_backtest_grid_trigger.py` anti-rot check ties the
  descriptor to whether the class actually overrides the trigger, and a
  behavioural check confirms the advertised strategies build a rolling
  high. The window param (`lookback_days` for hf *and* bayesian, never
  bell_curve's Gaussian-sizing `lookback_days`) moves out of the param
  grid into one "reference window (days)" input in the panel.

A no-edit submit of any model is byte-identical to before.

## Execution-chart zoom: 1D / 1H / 1m (web UI)

The Execution chart's candle resolution used to be a dropdown on the
filter panel (1Min…1Day) that only *re-aggregated* a fixed ~3000-point
server payload -- so "1Min" over a ten-year run was a rollup of a
rollup, never actual minute bars. It is now a **1D / 1H / 1m** toggle on
the chart itself, and each level bounds the window it pulls so the
resolution is real:

- **1D** — daily candles over the whole backtest.
- **1H** — hourly candles, at most a 10-day window.
- **1m** — minute candles, at most a 2-day window.

Each level fetches `/api/backtest/bars` for its capped window with a high
`max_points`, anchored to the end of the filter range (or the run's data
end when the range is open) and never starting before the range does --
so narrowing the filter panel's dates first, then zooming, works as
expected. The window math is `chartWindow()` in `lib/filters.ts`, pure
and unit-tested. `ExecutionFilters.timeframe` becomes `chartResolution`
(`"1d" | "1h" | "1m"`); the filter panel's Timeframe control is removed.
No server change -- `/bars` already took `max_points` and an arbitrary
window.

## Dynamic sizing-model parameters (web UI + backtest API)

"Run a backtest" now renders one input per sizing-model constructor
argument and swaps the whole set when the Sizing Model changes -- so
picking `rsi` shows `period` / `oversold_threshold`, picking
`bell_curve` shows `lookback_days` / `bars_per_day` / `mu` / `sigma`,
and so on. Fields are pre-filled from this project's committed configs,
grouped Primary vs a collapsed **Advanced** block, and each carries a
reset-to-suggested control; a readout says which values differ from the
committed defaults.

**Server (`server/backtest.py`).** `describe_params()` introspects each
strategy's `__init__` (`inspect.signature` + `typing.get_type_hints`,
which is needed because the strategy modules use
`from __future__ import annotations`) into a typed spec per argument:
`type` (float/int/bool/str), `nullable`, `required`, `default`,
`suggested`, `enum`, `group`, `editable`, `mirrors`, `step`. Three
things `inspect` cannot see are named once: `_PARAM_ENUMS`
(`vol_measure` -> stdev/range), `_HIDDEN_PARAMS` (`model_dir` /
`external_dir` -- never shown or sent), `_DERIVED_PARAMS`
(`baseline_price` -- shown locked). `bayesian_dual_scale.target_return`
is surfaced locked with `mirrors: "profit_target"` (the form tracks the
Profit target field and never sends it -- `build_config` already
aligns it to the grid); `ml_reachability_*` `ticker` is locked to the
id's fund. `GET /funds` gains a `sizing_params` key; `sizing_details`
(`required` / `defaults`) is byte-for-byte unchanged for its existing
consumers.

**"More than read-only": `POST /api/backtest/validate`.** Dry-runs the
*same* `build_config(request)` the submit path uses -- one definition of
"valid", no second to drift -- queues nothing, writes no history, opens
no store, and returns `{ ok, resolved_strategy_params, aligned, errors:
[{field, message}] }` always as HTTP 200. The form debounces a call to
it and renders a bad argument as a red line under its field, so
`max_trade_pct = 1.5` or a partial parameter set is caught before the
run is ever queued instead of as a 400 on click or a job that dies
twenty seconds in. A 404 (a deployment whose backtest half predates the
route) degrades silently to submit-time validation.

**Client.** `strategyParams.ts` holds the pure schema->form->wire logic
(covered in `strategyParams.test.ts`): a blank field is omitted (never
sent as `null`); a `mirrors` field and the `percentage` alias are never
sent; an `editable:false` field is never sent except `ticker`; ints go
out as integers and bools as JSON booleans (the server does no
coercion). A no-edit submit of any model therefore sends exactly that
model's committed defaults -- byte-identical to the old blind
`sizing_details.defaults` splat. The e2e hooks (`sizing-model` /
`bars` / `run` test-ids, the `bars` option order, the `Run a backtest`
title) are untouched; the Advanced block is collapsed on load so no new
`<select>` shifts.

## "Backtest result" nav tab (web UI)

Opening a run (from Run history or Active runs) already opened `?run=<id>`
in a new browser tab. That tab now lands on a **fourth nav tab**,
"Backtest result", instead of rendering the report inline under
Backtesting. The report — summary metrics, OHLC chart, trade log, sweep
surface, fund comparison — moved into `web/src/components/backtest/
BacktestResult.tsx`; the Backtesting tab is now just the instrument
(ParameterForm, ActiveRuns, RunHistory).

- A deep link (`?run=`) selects the result tab on load and attaches.
- A run submitted from the form finishes on the Backtesting tab (the Run
  button and status badge report it there), and a "Run complete → Backtest
  result" card offers the jump. It deliberately does **not** force-navigate
  on completion — that races the "complete" state a reader and the e2e
  suite both watch for.
- A sweep-matrix cell click on the result tab still stages the
  configuration onto the form and switches back to Backtesting, so the
  prefilled form is in view rather than changed on a hidden tab.
- The execution filter (its date range doubles as the submitted run's
  window) stays lifted in `App`; `BacktestResult` derives the chart data
  from it.

## Run-history filtering (web UI)

The **Run history** table can now be narrowed before it is ranked.

- **Categorical**, as multi-select chips: fund, algorithm (`sizing_model`),
  fill model. Empty = no restriction; picking several is OR-within,
  AND-between.
- **Name**, as a case-insensitive substring. A row with no name drops
  out once the box is non-empty.
- **Input arguments**: `grid_step` and `profit_target` are always shown
  (in percent, matching the table); every numeric sizing-model argument
  seen across the loaded rows is offered through an "add filter"
  dropdown. Each takes a set of exact values (chips, when the distinct
  count is 2–12) **and** a min/max band — a row passes on either, so
  "1% or 1.5%" and "0.5%–2%" both work.
- **Results**: every `FundPerformanceMetrics` field (CAGR, worst year,
  max drawdown, Sharpe, return/drawdown, trade count, …) can be added as
  a min/max band from the same dropdown.

A row missing a gated field — an old report with no `worst_year_pct`, a
model that never took `period` — is **excluded**, not passed through, the
same rule `filterExecutions` already follows for an execution with no
RSI. The filtering itself is `filterHistoryRows` and friends in
`web/src/lib/filters.ts`, pure and covered in `filters.test.ts`; the
panel only edits the filter object.

To make an input argument filterable at all, the resolved
`strategy_params` (what the engine was built with, after defaults and
`target_return` alignment) now ride on the report's `parameters` and on
every flattened history row — `{}` for a run archived before this.

## Named backtest runs (web UI)

"Run a backtest" now has an optional **Name** field. It is descriptive
only — the engine never reads it — and deliberately stops at the server
boundary rather than entering `BacktestConfig`: it is a UI/history
concern, so it is carried on the `Job` snapshot (`server/jobs.py`) and
the archived report's `parameters.name` (`server/backtest.py`), never
handed to `from_dict()`.

Because it rides the job snapshot, a queued or running sweep shows by
name in **Active runs** before its report exists; once complete it labels
the header strip and gets its own column in **Run history**, repeated on
every configuration row since that table is flattened one row per cell.
Blank and whitespace-only names normalise to unnamed at both the queue
and the report, so the history table never shows a row labelled `"   "`.

## Analytical warehouse (DuckDB + Polars)

Sweep output previously landed in four stores that could not be joined:
flat CSVs (`cli.py`, `run_hf_sweep.py`), per-run JSON (`server/history.py`),
JSONL probe journals (`tools/stage*_grid.py`), and SQLite for live state
only (`src/core/persistence.py`, which deliberately refuses backtest
results). Three consequences drove this change:

1. **Trade blotters were computed and discarded.** `_simulate_single`
   builds the blotter unconditionally because `trade_metrics` needs it,
   then `run_sweep` drops it unless `return_full_results` is set.
   `cli.py:150` said so outright: *"cli.py does not yet write them to
   disk."*
2. **No dedup survived a process.** The only one was an in-process dict
   in `run_hf_sweep.py`, which measured 140 of 200 TPE trials as
   re-measurements of 60 unique combinations.
3. **No lineage.** A results CSV recorded parameters and metrics but not
   *which data file* produced them.

`warehouse/` now holds `market_data.duckdb` (assets, market_events,
external_series) and `sim_results.duckdb` (broker_environments, sweeps,
simulations), linked by `ATTACH`, over ZSTD Parquet lakes partitioned
`ticker/year`, `provider/series_key` and `simulation_id`. Build it with
`tools/build_warehouse.py --ingest-all`; record into it with
`cli.py backtest --warehouse`. On this repo's data, 7.36M bars compress
to 87 MB and 0.69M macro rows to 6 MB, with the catalogs at ~2 MB.

### Decisions worth keeping

**The sweep engine does not import duckdb.** `run_sweep` gained one
keyword, `result_sink=None`, typed against a stdlib `Protocol` in
`src/optimization/result_sink.py`. `src/optimization` is reachable from
the live path, and the Pi must not need an analytics library to boot.
`DuckDBResultSink` satisfies the Protocol structurally and never imports
it.

**`parameter_hash` includes `dataset_version` and `broker_id`.** It
carries the `UNIQUE` constraint that *is* the dedup, so it must cover
everything that changes what a run means. A hash that is "purely about
parameters" reads cleaner and silently makes the warehouse refuse to
re-measure a strategy on newer data. `rank_by` is excluded: ranking
chooses which row you look at, not what was computed. It builds on
`core/artifacts.canonical_hash` rather than adding a third hashing
scheme to a project that already had two.

**Sorting at write time replaces the index that a view cannot have.**
DuckDB refuses `CREATE INDEX` on a view ("can only create an index on a
base table"), so the OHLCV lake is written `ORDER BY ticker, timestamp`.
Partition pruning plus row-group zonemaps do the work — but zonemaps
only prune if the data was sorted. Dropping the `ORDER BY` fails no
query; it just silently makes every `ASOF JOIN` a full scan.

**`TimeZone` is pinned to UTC.** Measured: DuckDB defaults to the system
zone (America/Denver on this machine), and it changes what
`TIMESTAMPTZ::TIMESTAMP` yields — the same instant read back as 14:30
under UTC and 07:30 under America/Denver. A casting mistake in an ASOF
join does **not** raise; it shifts the instant and joins anyway.

**Blotter columns are cast explicitly.** Polars types an all-null column
as `String`. A combination that closes no trades has an all-null
`profit_realized`, whose Parquet file would then disagree about that
column's type with every other run's and break the view. `BLOTTER_SCHEMA`
pins all twelve columns.

**Cross-database foreign keys do not exist**, so `dataset_version` is a
plain `VARCHAR`. Lineage is recorded, not enforced — the alternative was
collapsing both catalogs into one file.

**A sink may not raise, and may not retain its `SimulationResult`.**
Both come from incidents already recorded in `optimization_controller.py`:
losing hours of engine time to a storage fault, and the 1,260-combination
run whose RAM was exhausted by holding results. Writing the blotter costs
nothing extra because it already exists; only *keeping* it does.

**`/warehouse/` is anchored in `.gitignore`.** A bare `warehouse/` also
matches `src/warehouse/`, which would leave the package's own source
untracked and missing from every clone — precisely what the bare `data/`
rule still does to `src/data/`.

### External-series lake — `data/external/` (FRED / CBOE / Yahoo)

`build_warehouse.py --external` (also folded into `--ingest-all`) ingests
the 118 macro series in `data/external/` — 56 FRED, 52 Yahoo, 10 CBOE,
~0.69M rows → 6 MB — into a Parquet lake partitioned `provider/series_key`
with an `external` view and an `external_series` dimension table.

**Manifest-driven, not glob-driven.** `data/external/manifest.json`
(written by `tools/fetch_market_inputs.py`) is the list of series and the
only source of each one's provider, category and — critically —
`lag_days`. A CSV with no manifest entry is skipped rather than guessed
at: its publication lag would be unknown, and lag is not optional.

**The join is lag-aware.** 55 of 56 FRED series carry a real publication
lag (CPI +45d, GDP +90d, ...). `queries.EXTERNAL_SERIES_AT_BARS` shifts
every observation forward by `lag_days` to a `known_at` and does the
`ASOF` match on that, so a March backtest bar sees the January CPI print,
not the March one that wasn't released until mid-April. Verified against
real data: 0 of 1,035,332 TQQQ bars joined a CPI value dated less than
45 days before them. `EXTERNAL_VALUE_AT` is the raw
`ExternalIndexSeries.scalar()` equivalent for non-backtest lookups.

**Heterogeneous shapes, one view.** FRED is `timestamp,close`; some CBOE
series add `high,low`; Yahoo adds `volume`. Every series is projected
onto a fixed 8-column superset with NULLs, and `union_by_name` binds the
differing per-partition files.

## Tooling — Docker

The project runs in a container via `cli.py`, a single entrypoint with
three subcommands. Build once, run any of them:

```
docker build -t volatility-ai .
docker run --rm volatility-ai --help
```

Or via compose, which also wires up the right volumes:

```
docker compose run --rm test
docker compose run --rm backtest --config /app/config/config.yaml --data /app/data/TQQQ_historical.csv
docker compose run --rm live --config /app/config/config.yaml
```

**`test`** — runs pytest inside the image. Arguments forward straight
through: `docker compose run --rm test -k my_test -v`.

**`backtest`** — loads a `BacktestConfig` YAML and a historical CSV,
runs the sweep, prints a summary, and optionally writes full results
with `--output`. Mount `./data` and `./config` read-only, `./output`
read-write.

**`live`** — validates config and credentials and runs the Task 7.12
startup sequence against a persistent SQLite store. **It cannot place
a real order.** No class in this codebase implements the `LiveBroker`
protocol against an actual Alpaca connection — confirmed by search
before writing this, not assumed — so `live` correctly and honestly
lands in `RECOVERY_REQUIRED` rather than pretending to connect. What
it does verify for real: config validation, credential presence
(`APCA_API_KEY_ID` / `APCA_API_SECRET_KEY`, sourced only from the
environment — see the secret policy above), and that ledger/audit
state persists to `/app/state` across the run.

Credentials for `live` come from an uncommitted `.env` file passed via
`env_file:` in `docker-compose.yml` — never baked into the image, and
excluded from the build context by `.dockerignore` even if one existed
locally.

State persistence: `/app/state` is a named volume (`state:` in
compose), not a bind mount, so the SQLite ledger and audit log survive
`docker compose run` invocations across separate container instances
— the point of Task 7.3/7.12's design, now actually exercised by the
container lifecycle rather than only by tests.

**A real bug was caught before this was committed.** The `test`
subcommand originally routed pytest arguments through
`argparse.REMAINDER`, which cannot reliably capture a leading
option-like token with no preceding positional — `cli.py test -q`
(the single most common invocation) raised `unrecognized arguments:
-q`, while `cli.py test some/path.py -q` worked fine. Fixed by
forwarding `sys.argv` directly for that subcommand instead of routing
it through argparse. Regression-tested in
`tests/integration/test_cli_docker_entrypoint.py`.

The full build was also simulated without Docker itself (unavailable
in the authoring sandbox): a clean virtualenv installing only
`requirements.txt`, against a build context mirrored through the exact
`.dockerignore` exclusions, running the exact entrypoint commands.
All 677 tests passed in that simulated environment before any of this
was committed.


## Tooling — ruff (formatter + linter)

Formatting and linting are both handled by [ruff](https://docs.astral.sh/ruff/),
configured in `pyproject.toml`.

```
ruff format .           # apply formatting
ruff format --check .   # verify only, for CI
ruff check .            # lint
ruff check --fix .      # lint and apply safe fixes
```

**Configuration choices, and why:**

- **`line-length = 100`**, not ruff's default 88. Measured against the
  existing code: p95 of line lengths is 87 and p99 is 106, so 88 would
  have rewrapped ~4.5% of all lines while 100 touches ~1.6%. This keeps
  formatting churn off code that was already readable.
- **`E501` (line-too-long) is ignored** at lint level. Operator-facing
  error strings — reconciliation diagnostics, no-loss rejections —
  deliberately name the specific delta so someone paged at 3am can act
  without reading source. The *formatter* still enforces line length on
  code; this only exempts strings it cannot split.
- **`C408` is exempted in `tests/` only.** Test helpers build kwargs
  dicts that are immediately splatted (`base = dict(...)` →
  `Model(**base)`), where the call form mirrors the keywords it becomes.
  `src/` and `optimization_controller.py` are held to the rule and are
  C408-clean.
- **`docstring-code-format = false`.** Several docstrings contain spec
  excerpts and illustrative pseudo-code that are not valid Python and
  must not be rewritten.

Two `noqa` comments exist, both in `tests/unit/test_secret_policy.py`,
both with stated reasons: that test verifies credentials stay redacted
through *every* string-conversion path, so the `%`-format and
`.format()` call sites are the code paths under test — modernizing them
would silently drop coverage.


## Phase 1 — Fix the confirmed bugs (B1–B5)

Tasks 1.1–1.5 fixed. Task 1.6 (this entry) re-runs the Task 0.1
regression fixture and documents deltas, per
`implementation_task_specs.md`.

### FixedPortfolioPercentage: unchanged, value-for-value

`FixedPortfolioPercentage` doesn't use drawdown or ticks in its
sizing, so its output should be identical to the pre-Phase-1 baseline
captured in Task 0.1 — confirmed by
`tests/integration/test_task_1_6_regression_verification.py`, which
re-runs the exact Task 0.1 fixture/parameters post-Phase-1 and asserts
every column matches the frozen `BASELINE` in
`tests/fixtures/regression_baseline.py` exactly:

| Metric | Value |
|---|---|
| Final Equity | 100099.81489816227 |
| Trade Count | 4 |
| Closed Trade Count | 4 |
| Capital Velocity Index | 1.0 |
| Max Drawdown % | 0.4430668810465577 |

Unchanged despite: drawdown now being tracked every bar instead of
only trigger bars (Task 1.2), `record_tick` now firing every bar
(Task 1.3), `current_dd` now being threaded into
`calculate_trade_value` (Task 1.4), and fill-status/no-loss validation
now gating cash and ledger mutation (Task 1.5) — all expected, since
none of those changes touch a code path `FixedPortfolioPercentage`
reads from.

### Drawdown/tick-consuming strategies: not applicable yet

Task 1.6 also asks to re-run and record an updated baseline for "any
drawdown/tick-consuming strategy available." None exists in this repo
yet — `BellCurveProbabilitySizing`, `RsiMomentumSizing`, and
`BayesianDualScaleSizing` were out of scope for the from-scratch
`src/size_calculators.py` implementation (see that file's docstring:
no sizing formula was specified anywhere to implement them against).
B2/B3/B4's underlying mechanism is fixed at the controller level
regardless (Tasks 1.2–1.4), so whenever a drawdown- or
tick-consuming strategy is added, it will receive real per-bar ticks
and real drawdown from day one rather than needing its own fix.

### No collision between the controller's and analyzer's drawdown figures

`PerformanceAnalyzer.calculate_metrics()` deliberately never produces
a `"Max Drawdown %"` key (see that file's docstring) — the value in
every `run_sweep()` result row is exactly
`optimization_controller.py`'s own `state.max_drawdown * 100.0`
assignment, with nothing else able to write or silently overwrite it.
Confirmed by
`test_no_collision_between_controller_and_analyzer_drawdown_figures`.

### Bugs fixed this phase

| Task | Bug | Fix |
|---|---|---|
| 1.1 | B1 | `Run_Instructions` example used a non-existent `allocations=` param and a wrong import path; both fixed |
| 1.2 | B3 | Peak equity / drawdown now computed every bar, not only on grid-trigger bars |
| 1.3 | B4 | `sizing_engine.record_tick(current_price)` now called every bar (previously never called) |
| 1.4 | B2 | `current_dd` now threaded into `calculate_trade_value` (previously always defaulted to 0.0) |
| 1.5 | B5 | Fill status (`OrderStatus.FILLED`) and the no-loss invariant now validated before cash/ledger mutation on both buy and sell paths |

## Phase 6 — Config & docs

### Task 6.2: integration-test coverage for scenarios 1–6

Task 6.2 lists 13 integration-test scenarios; scenarios 7–13 need
Phase 7 tasks that don't exist in this repo yet and were explicitly
not attempted, per that task's own instruction not to build ahead of
the tasks they depend on. Scenarios 1–6 were each already covered by
a dedicated, traceably-named test written when its source task was
originally implemented — re-verified together (not assumed still
passing) before this entry was written, rather than duplicated into
new tests that would just re-check the same behavior a second time:

| # | Scenario | Test |
|---|---|---|
| 1 | `record_tick` called exactly once per bar regardless of trigger state (Task 1.3) | `tests/integration/test_task_1_3_record_tick.py::test_record_tick_called_exactly_once_per_bar_including_non_trigger_bars` |
| 2 | `calculate_trade_value` receives a non-zero drawdown during a scripted drawdown (Task 1.4) | `tests/integration/test_task_1_4_drawdown_threading.py::test_calculate_trade_value_receives_real_drawdown_not_default_zero` |
| 3 | Each `RiskManager` cap clamps rather than silently over-allocating (Tasks 3.1/3.2) | `tests/unit/test_risk_manager.py::test_max_concurrent_lots_clamps_to_zero_once_at_cap`, `::test_max_total_exposure_pct_clamps_to_zero_when_already_at_or_over_cap`, and `tests/integration/test_task_3_2_risk_manager_wiring.py::test_max_concurrent_lots_caps_trade_count` |
| 4 | A single raised exception inside one combination doesn't abort the sweep (Task 4.4) | `tests/integration/test_task_4_4_error_isolation.py::test_one_bad_combination_does_not_abort_the_others` |
| 5 | `n_jobs>1` output matches `n_jobs=1` output (Task 4.5) | `tests/integration/test_task_4_5_parallel_execution.py::test_n_jobs_greater_than_1_produces_the_same_result_set_as_sequential` |
| 6 | Walk-forward out-of-sample metrics are computed on data never used for that fold's selection (Task 5.1) | `tests/unit/test_walk_forward.py::test_no_test_slice_overlaps_its_own_train_slice` |

### Tasks 6.3 / 6.4: deployment artifacts and secret policy

**Backtest artifacts are safe to persist without credentials.** A
`DeploymentArtifact` (`src/artifacts.py`) contains only provenance
identifiers and hashes — no credential fields exist on it, and
`canonical_hash()` actively *rejects* any content carrying a
secret-looking key (`secret`, `password`, `api_key`, `token`,
`credential`, `private_key`, checked case-insensitively through
nested structures) rather than silently hashing it. The same is true
of `BacktestConfig`: it has no credential fields by design, so a
serialized config is safe to commit to source control.

**Credentials come only from the environment**, never from YAML/JSON
config, command-line arguments, or source control:

| Variable | Purpose |
|---|---|
| `APCA_API_KEY_ID` | Alpaca API key ID |
| `APCA_API_SECRET_KEY` | Alpaca API secret key |

`load_live_credentials()` (`src/secrets.py`) raises
`ConfigurationError` naming exactly which variables are missing —
it never falls back to simulation mode, and never echoes a value
(even partially) into the error message.

**Redaction is structural, not conventional.** `LiveCredentials`
overrides `__repr__`/`__str__`, so credentials cannot reach a log
line, f-string, `%`-format, `.format()` call, or traceback frame even
when the object is logged directly. `redact_secrets(payload)` is
available for masking secret-bearing values inside arbitrary
structured-logging payloads (non-mutating — the caller's live values
are untouched).

## Phase 7 — Live execution parity

### Task 7.7: promotion runbook (backtest → paper → live capital)

**No code path goes from a backtest result directly to live capital.**
This is enforced structurally, not by convention: constructing a
`Mode.LIVE` `OrderManagementSystem` requires a passing
`PromotionEvaluation`, which requires a real `PaperTradingRecord` that
met every threshold. There is deliberately no `enable_live=True`
boolean shortcut.

**The three stages, in required order:**

| Stage | Mode | What it proves |
|---|---|---|
| 1. Backtest | `Mode.SIMULATION` | The parameter set survives historical data (and ideally Task 5.1 walk-forward validation) |
| 2. Paper | `Mode.PAPER` | It survives real-time execution against Alpaca's paper endpoint, risk-free |
| 3. Live | `Mode.LIVE` | Only reachable with recorded evidence that stage 2 passed |

`Mode.PAPER` is a first-class mode rather than a flag on `LIVE`,
so reaching real capital is an explicit, auditable step.

**Promotion criteria** (`src/promotion.py::PromotionCriteria`) — all
machine-checkable, all recorded in the promotion artifact rather than
left to operator judgment:

| Criterion | Default |
|---|---|
| Minimum paper-trading duration | 5 days |
| Minimum strategy decisions | 20 |
| Minimum fills | 5 |
| Accounting discrepancies | 0 allowed |
| Duplicate-order incidents | 0 allowed |
| No-loss guard violations | 0 allowed |
| Unresolved reconciliation state | 0 allowed |
| Unhandled runtime exceptions | 0 allowed |

**Operator procedure:**

1. Run the backtest sweep; select a parameter set.
2. Build a `BacktestConfig` with `live.paper_trading: true` and run it.
   `LiveExecutionLoop` builds a `Mode.PAPER` OMS — real capital is
   unreachable at this stage regardless of what else is configured.
3. Collect results into a `PaperTradingRecord`. Its `metrics` field
   mirrors `SimulationResult.metrics` (Task 4.6), so paper and
   backtest results are directly comparable rather than living in two
   incompatible report formats.
4. Call `assert_promotable_to_live(artifact, record)`. It reports
   *every* unmet criterion at once, not just the first.
5. Only on success, pass the returned evaluation as
   `live_capital_promotion` to enable `Mode.LIVE`. Record
   `evaluation.criteria` in the deployment artifact — that is the
   auditable record of which bar was cleared.

**Gap closed during this task:** `LiveExecutionLoop` previously
constructed `Mode.LIVE` unconditionally, ignoring
`config.live.paper_trading` entirely — a config asking for paper
trading still got a real-capital OMS. It now honors the flag.

### Task 7.9: macro/seasonality signals — **Not required / deferred**

Discovery gate outcome. **No confirmed consumer exists**, so per the
task's own step 2 no ingestion pipeline was built and no production
behavior was changed.

Evidence from a repository-wide search of all three field names
(`time_of_day_flag`, `is_macro_event_day`, `macro_surprise_factor`):

| Location | Role |
|---|---|
| `src/market_context.py` | **Defines** the fields with safe defaults (`0`, `False`, `0.0`) — a definition, not a consumer |
| `src/live_execution.py` | `build_context()` **forwards** them. Pure pass-through plumbing; it type-coerces and hands them to the constructor, never reading a value to make a decision |
| `src/size_calculators.py` | The only real strategy, `FixedPortfolioPercentage`, reads exactly `context.price` and `context.equity` — neither of the three fields |

Also confirmed: no conditional logic anywhere branches on these
fields; no call site supplies a non-default value; and no FinBERT /
sentiment / transformers / CPI / Federal Reserve / FOMC reference
exists anywhere in the repository.

**On the external claim that prompted this task** — that FinBERT NLP
sentiment and Fed/CPI macro-event awareness were already integrated
into this system's Bayesian sizing — nothing here supports it.
`BayesianDualScaleSizing` is not implemented in this repository at all
(`FixedPortfolioPercentage` is the only sizing strategy that exists),
and "macro" in that class's name refers to a **long-window Bayesian
posterior** — a lookback-length distinction — not to macroeconomic
events. The two senses of "macro" appear to be the source of the
confusion.

The fields are deliberately **left in place**: they are optional,
defaulted, and already part of overview §5.1's `MarketContext`
contract. Removing them would be a breaking change for no benefit;
populating them would be the speculative scope this gate exists to
prevent.

This finding is **executable, not just documented** —
`tests/unit/test_task_7_9_macro_signals_discovery.py` fails if a
consumer, a branch, an ingestion dependency, or a new sizing strategy
appears, at which point the gate must be re-run and step 3 (consuming
strategy, source dataset, timestamp-join semantics, defaults, and a
follow-up implementation task) becomes live.
