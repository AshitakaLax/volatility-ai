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

## Data preparation — produces inputs the rest of the project consumes

| Script | Produces |
|---|---|
| `build_earnings_calendar.py` | `data/earnings_releases_derived.csv`. **Load-bearing for a fresh checkout** — `data/` is git-ignored, so this is absent after a clone and `src/event_calendar.py` needs it. Makes network requests; slow. |
| `pull_extended_history.py` | Extended-hours minute datasets under `data/`, year by year. |
| `export_strategy_curves.py` | One JSON blob of every strategy measured here, for the dashboard and the artifact. |

## Research — measurements and probes. Read-only; they answer questions

Shared plumbing: `harness.py` (probe scaffolding) and `session_bars.py`
(session aggregation). `check_syntax.py` asserts every `.py` in the repo
parses.

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
