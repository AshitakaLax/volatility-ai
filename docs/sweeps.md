# Parameter sweeps and the simulation record

How the research sweeps are run, and every sweep run to date with the
command that reproduces it. Moved out of `README.md` to keep that file an
overview; the content is unchanged apart from Linux paths.

## Running the HF parameter sweeps

Every sweep behind `CHANGELOG.md`'s `HighFrequencyLocalReferenceSizing`
research (the strategy the [Simulations run to date](#simulations-run-to-date)
table below is full of) was driven by two scripts, not `cli.py`. `cli.py
backtest` exposes neither `n_jobs` nor per-combination progress logging, and
`cli.py search` calls the internal runner without `fill_model`, so it
silently runs the CLOSE-only fill model regardless of what
`execution.fill_model` says — wrong for a strategy whose grid rests limit
orders. Older, non-HF strategies (`fixed`, `bayesian_dual_scale`) still go
through `cli.py`, since they predate that defect being found.

### `research/run_hf_sweep.py` — the sweep driver

```bash
.venv/bin/python research/run_hf_sweep.py \
  --config config/<name>.yaml \
  --search grid \
  --n-jobs 4 \
  --output output/<name>.csv
```

Reads bars from the warehouse by `config.backtest.symbol` — there is no
`--data` flag; ingest the ticker first (`tools/build_warehouse.py
--ingest TICKER`) if this is the first sweep to use it.

| Flag | Default | Meaning |
|---|---|---|
| `--config` | `config/search_hf_intrabar.yaml` | `BacktestConfig` YAML to run |
| `--output` | `output/search_hf_intrabar_2026-08-22.csv` | ranked results CSV, checkpointed periodically so a multi-hour run has partial output on failure |
| `--search {grid,bayesian,random}` | the config's `search.strategy` | overrides the YAML without editing it |
| `--trials N` | `200` | evaluation budget for `bayesian`/`random`; ignored for `grid` |
| `--n-jobs N` | `1` | worker processes. Each peaks around 1.7GB RAM at the heaviest settings (~900k trades/10y) — budget accordingly, and see `--max-drawdown` below for why a bare TPE run over a mostly-categorical space tends to collapse |
| `--max-drawdown X` | none | penalizes the search *objective* for combinations over `X`% max drawdown, gradated by how far over — a flat penalty gives the sampler nothing to walk back down. The combination is still fully measured and its true numbers land in the CSV; only what the sampler is told to chase changes |
| `--limit N` | none | run only the first `N` combinations — for smoke-testing a config before committing to the full space |

Runs sequentially by default; pass `--n-jobs 4` (or similar) for
process-level parallelism. Random search (`--search random`) samples
without replacement and is generally the better default over `bayesian` on
these mostly-categorical spaces — TPE has repeatedly been observed
re-proposing the same ~15 combinations for hundreds of trials once it
locks onto a mode, where random search covers the space proportionally to
budget. See `Add RandomSearch...` in `git log` for the measurements.

### `research/analysis/analyze_annual.py` — year-by-year vs. buy-and-hold

The whole-period CAGR of a profit-capped strategy over a decade-long bull
run is misleading in a specific, predictable direction. This reads every
CSV in `output/`, deduplicates to distinct parameter sets, takes the best
few by `Total Return %`, re-simulates each once, and reports calendar-year
returns against TQQQ buy-and-hold on the same data — so it is checking
whether the strategy actually wins the chop/correction years it is meant
for, not just its aggregate number.

```bash
.venv/bin/python research/analysis/analyze_annual.py --top 3
.venv/bin/python research/analysis/analyze_annual.py --cap 50 --top 2   # only consider maxDD <= 50%
```

| Flag | Default | Meaning |
|---|---|---|
| `--ticker` | `TQQQ` | warehouse ticker to re-simulate finalists and the benchmark on |
| `--cap` | none | only consider rows with `Max Drawdown % <= cap` |
| `--top` | `3` | how many best (deduplicated) configurations to report |

### `cli.py search` / `cli.py backtest` — for non-HF strategies

```bash
python cli.py backtest --config config/sweep_5y.yaml --output output/sweep_5y.csv
python cli.py search --config config/search_bayesian_deep.yaml --trials 500 --output output/search_bayesian_deep.csv
```

`backtest` runs the config's declared `search.strategy` (grid or bayesian)
to completion in one process. `search` drives `BayesianSearch` directly and
logs trials in the order Optuna actually proposes them (`--trial-log`), so
the explore-then-exploit progression is visible instead of hidden behind
`run_sweep`'s final sort.

### Chain scripts

`tools/experiments/run_extended_chain.sh`, `run_frontier_chain.sh`, and `run_overnight_chain.sh`
wrap a sweep plus an `research/analysis/analyze_annual.py` breakdown into one sequential run,
logging to `output/<name>_$(date +%Y%m%d_%H%M).log`. Sequential is
deliberate, not an oversight: four `n_jobs` workers already peak near
1.7GB of commit each, and an earlier 250-trial run was killed partway
through when something else ran alongside it on the same machine. Run one
at a time:

```bash
bash tools/experiments/run_frontier_chain.sh
```

`run_overnight_chain.sh` additionally takes a task-output path as `$1` and
waits (polling every 60s, capped at 6h) for that in-flight sweep to finish
before starting its own chain, so a long foreground run and an overnight
chain can be queued back to back without overlapping.

### `cli.py submit` — hand a sweep to the server's shard queue

`backtest`/`search`/`run_hf_sweep.py` all run in THIS process. `submit`
instead posts the same `BacktestConfig` YAML to `POST /api/backtest/runs`
on a running `cli.py serve`, which queues it for whatever shards are
online (`GET /api/backtest/shards`) to claim and run — watchable in the
browser (Backtesting → Run History), and unaffected by this process
exiting. No bespoke per-sweep script needed: any config works.

```bash
python cli.py submit --config config/search_hf_bayesian.yaml --search grid
python cli.py submit --config config/search_bayesian_deep.yaml --trials 500
```

| Flag | Default | Meaning |
|---|---|---|
| `--config` | required | `BacktestConfig` YAML to submit |
| `--api` | `http://127.0.0.1:8000` | the running server's base URL |
| `--search {grid,bayesian}` | the config's `search.strategy` | override without editing the file (server has no `random`) |
| `--trials N` | `500` | bayesian trials **per chunk** (max 500, the API's own ceiling) — not a total budget |
| `--limit N` | none (the whole file) | bar cap per configuration |
| `--dry-run` | off | print the plan; submit nothing |
| `--resubmit` | off | queue even runs already completed/pending on the server |

A config's declared combination space can exceed what one submission may
carry (`MAX_SWEEP_COMBINATIONS` for grid, 100x looser for bayesian, since
the whole point of choosing bayesian is a space too large to enumerate)
— `submit` splits it into as many runs as needed by recursively bisecting
the widest swept axis, the same way `tools/sweep_rsp_all.py` did by hand
before this existed. A strategy like `bayesian_dual_scale`, whose
`target_return` the server force-aligns to the grid's own profit target,
gets one submission per swept `target_return` value automatically (that
parameter is never sent — the server supplies it).

**Not the same as a local run:** `RunRequest` has no cost-model field, so
every submitted run executes at zero transaction cost regardless of what
the config's own `costs:` section says — a real gap in the web API, not
something `submit` works around.

---

## Simulations run to date

Every config in `config/` that has actually been swept, in the order it
was run, with the command that reproduces it. All use the strategy
`hf_local_reference` (`HighFrequencyLocalReferenceSizing`) against the
10-year TQQQ SIP dataset unless noted. Read each config's own header
comment for the full rationale — this table is a reproduction index, not a
replacement for it.

| Config | Question it answers | Command | Output |
|---|---|---|---|
| `search_hf_intrabar.yaml` | Foundational exhaustive sweep (192 combos) that fixed the close-vs-touch fill model, a binding lot cap, and dead sub-cost-floor targets. | `research/run_hf_sweep.py --config config/search_hf_intrabar.yaml --search grid --n-jobs 4 --output output/search_hf_intrabar.csv` | superseded, not retained |
| `search_hf_bayesian.yaml` | TPE over the same space densified to 6,272 points, uncapped. | `research/run_hf_sweep.py --config config/search_hf_bayesian.yaml --search bayesian --trials 200 --n-jobs 4 --output output/search_hf_bayesian_2026-08-22.csv` | `output/search_hf_bayesian_2026-08-22.csv` |
| `search_hf_bayesian.yaml` | Same space, drawdown capped so the sampler stops chasing the ~80%-drawdown corner. | `research/run_hf_sweep.py --config config/search_hf_bayesian.yaml --search bayesian --trials 200 --max-drawdown 55 --n-jobs 4 --output output/search_hf_bayesian_capped_2026-08-22.csv` | `output/search_hf_bayesian_capped_2026-08-22.csv` |
| `search_hf_bayesian.yaml` | Rerun of the capped search after the penalty was graded by excess instead of flattened (the flat penalty had collapsed exploration to 14 unique combos). | `research/run_hf_sweep.py --config config/search_hf_bayesian.yaml --search bayesian --trials 200 --max-drawdown 55 --n-jobs 4 --output output/search_hf_bayesian_capped_v2_2026-08-22.csv` | `output/search_hf_bayesian_capped_v2_2026-08-22.csv` |
| `probe_vol_scaling.yaml` | Controlled probe: only `vol_scale_exponent` swept, everything else pinned at the capped run's best. Sizing down into volatility (`-1.5`) beat the no-op control by +13.05pp. | `research/run_hf_sweep.py --config config/probe_vol_scaling.yaml --search grid --output output/probe_vol_scaling.csv` | recorded in commit `5ff9eb1`, CSV not retained |
| `search_hf_volscaled.yaml` | TPE over 3,240 points with continuous vol scaling as the primary axis, event boosts pinned. | `research/run_hf_sweep.py --config config/search_hf_volscaled.yaml --search bayesian --trials 200 --max-drawdown 55 --n-jobs 4 --output output/search_hf_volscaled_2026-08-23.csv` | `output/search_hf_volscaled_2026-08-23.csv` |
| `search_hf_volscaled.yaml` | Same space, random search instead of TPE (250 distinct combos, 7.7% coverage) — added after TPE was found covering up to 17x less of a categorical space than random. | `research/run_hf_sweep.py --config config/search_hf_volscaled.yaml --search random --trials 250 --max-drawdown 55 --n-jobs 4 --output output/search_hf_volscaled_random_2026-08-23.csv` | `output/search_hf_volscaled_random_2026-08-23.csv` |
| `search_hf_volscaled.yaml` | Rerun after the range-based vol measure, volume field, and extended fast/slow windows were added. | `research/run_hf_sweep.py --config config/search_hf_volscaled.yaml --search bayesian --trials 200 --max-drawdown 55 --n-jobs 4 --output output/search_hf_volscaled_v2_2026-08-23.csv` | `output/search_hf_volscaled_v2_2026-08-23.csv` |
| `probe_volume_scaling.yaml` | Controlled probe: only `volume_scale_exponent` swept, pinned at the random sweep's best. Worth +11pp cap-compliant / +35.8pp uncapped, despite scoring weakest of any candidate on the prior correlation screen. | `research/run_hf_sweep.py --config config/probe_volume_scaling.yaml --search grid --output output/probe_volume_scaling.csv` | recorded in commit `5449475`, CSV not retained |
| `search_hf_wide_targets.yaml` | Does the profit target (held ≤0.003 in every sweep above) actually cap upside? No-loss guard ON. | `research/run_hf_sweep.py --config config/search_hf_wide_targets.yaml --search grid --n-jobs 4 --output output/search_hf_wide_targets.csv` | `output/search_hf_wide_targets.csv` |
| `search_hf_wide_targets_noguard.yaml` | Same grid, no-loss guard OFF — isolates whether the guard itself costs anything at wider targets. | `research/run_hf_sweep.py --config config/search_hf_wide_targets_noguard.yaml --search grid --n-jobs 4 --output output/search_hf_wide_targets_noguard.csv` | `output/search_hf_wide_targets_noguard.csv` |
| `search_hf_volume_sweep.yaml` | Brings volume in as a real swept axis alongside vol scaling, rather than a pinned-off control. | `research/run_hf_sweep.py --config config/search_hf_volume_sweep.yaml --search random --trials 220 --max-drawdown 55 --n-jobs 4 --output output/search_hf_volume_sweep.csv` | `output/search_hf_volume_sweep.csv` |
| `search_hf_targets_extended.yaml` | Extends the target axis 0.05 → 0.30 (120 combos, exhaustive) after the wide-targets sweep's winner sat on its 0.05 ceiling. | `research/run_hf_sweep.py --config config/search_hf_targets_extended.yaml --search grid --n-jobs 4 --output output/search_hf_targets_extended.csv` | `output/search_hf_targets_extended.csv` |
| `search_hf_targets_frontier.yaml` | Extends the target axis 0.30 → 1.00 *and* re-sweeps `per_lot_pct` alongside it (64 combos), since both control how long capital stays deployed and tuning either alone would mis-attribute the effect. | `research/run_hf_sweep.py --config config/search_hf_targets_frontier.yaml --search grid --n-jobs 4 --output output/search_hf_targets_frontier.csv` | `output/search_hf_targets_frontier.csv` — launched 2026-08-24 via `bash tools/experiments/run_frontier_chain.sh`; still running as of 2026-08-25 (see note below) |
| `best_known_2026-08-24.yaml` | Not a sweep — a single-point config pinning the best result found to date (25.38% CAGR, 45.57% max drawdown, 86,087 trades over the 10.63-year dataset) so it can be reproduced without hunting through every sweep output. | `research/run_hf_sweep.py --config config/best_known_2026-08-24.yaml --search grid --output output/best_known_2026-08-24.csv` | not yet run standalone; value is the config itself |

Two older, unrelated sweep families exist from before the HF strategy work
and use `cli.py` instead of `research/run_hf_sweep.py`:

| Config | Strategy | Command |
|---|---|---|
| `sweep_5y.yaml` / `sweep_5y_boundary.yaml` / `sweep_5y_costed.yaml` | `fixed` (`FixedPortfolioPercentage`) — early minute-bar step/target tuning, zero-cost then costed | `python cli.py backtest --config config/sweep_5y.yaml --output output/sweep_5y.csv` |
| `sweep_bayesian.yaml` / `search_bayesian_deep.yaml` | `bayesian_dual_scale` (`BayesianDualScaleSizing`) — dual-timescale Beta-posterior sizing, TPE-searched | `python cli.py search --config config/search_bayesian_deep.yaml --trials 500 --output output/search_bayesian_deep.csv` |

(Both originally ran against a `--data` CSV, before `backtest`/`search`
switched to reading the warehouse by `backtest.symbol` — TQQQ for both
configs. Reproducing them today needs no flag change, only that TQQQ is
ingested: `python tools/build_warehouse.py --ingest TQQQ`.)

`staging.yaml` and `production.yaml` are not sweep configs at all — they
are `live:`-enabled deployment configs; see
[Going live](../README.md#live-trading-and-the-promotion-path).

> **On stalled ETAs from a sleeping machine.** The frontier sweep above sat
> at a ~30h ETA for most of 2026-08-24 despite each combination taking
> ~500s of actual compute (visible via the process's CPU-seconds, which
> keep counting only while a process is scheduled). Wall-clock elapsed time
> includes any interval the machine spent asleep, so the driver's own ETA —
> computed from wall time — inflates the same way. It was not stuck; system
> sleep has since been disabled so this should not recur.


## The Ultimate family (`ultimate`, `ultimate_rsp`, `ultimate_ursp`)

These strategies sell lots below cost basis through their regime exit, so a
sweep must pass `allow_signal_exit=True` (and, to match the research,
`cash_yield_pct=None` for the historical short rate) to
`OptimizationController.run_sweep`. `research/run_hf_sweep.py` hard-codes
both off and therefore cannot run them as researched; the server and
`cli.py backtest` thread them from the config. The design log, every
experiment and the recommended configuration are in
[`docs/research/ultimate-algorithm.md`](research/ultimate-algorithm.md).
