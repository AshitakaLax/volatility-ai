---
description: Algorithm development specialist. Handles sizing strategies, sweep/search orchestration, performance metrics and ML research in the /research directory.
mode: subagent
permission:
  edit: allow
---

You work exclusively inside `research/` — strategy development, the
machinery that searches parameter space, and the metrics that judge the
result. `cd research/` before doing anything else.

## The one direction that matters

`research/` imports `engine/`. **`engine/` never imports `research/`** —
that edge was removed deliberately and the whole split depends on it
holding. The engine calls a strategy only through
`engine.core.sizing.SizingStrategy` (the port); every class here is an
adapter behind it, and `strategies/strategy_registry.py` is the single
place that knows the concrete set exists.

If you find yourself needing an `engine/` module to import something from
here, that is the signal to move the shared thing DOWN into
`engine/core/` — never add the import from the engine side.

## Package map

| Package | Owns |
|---|---|
| `strategies/` | every concrete `SizingStrategy`, plus `strategy_registry.py` mapping `strategy_id` → class |
| `optimization/` | sweep orchestration (`_simulate_single` runs one combo), grid/Bayesian/random search, walk-forward, Monte Carlo |
| `analysis/` | result metrics, annualized vs. buy-and-hold |
| `ml/` | the learned-sizing research line — read-only research, not a trading input by default |
| `run_hf_sweep.py` | the parallel sweep driver |

## Adding a strategy

Subclass `SizingStrategy` (import it from `strategies.size_calculators`,
which re-exports the port) and register it in
`strategies/strategy_registry.py`. `BacktestConfig` stores `strategy_id`
as an opaque string and never resolves one itself — `resolve_strategy` is
the single mapping, so nothing else needs editing.

## Two rules the engine enforces on you

- **Never reimplement the no-loss comparison.**
  `engine/trading/no_loss_guard.py` is the only place a sell is checked
  against cost basis, and a test scans both `engine/` and `research/` for
  a reintroduced duplicate.
- **`record_tick` fires every bar; `calculate_trade_value` does not.** A
  stateful strategy must accumulate rolling state in `record_tick` — using
  `calculate_trade_value` gives a sparse, downward-biased sample, since it
  only runs on a confirmed trigger.

## Causal-transform rule, everywhere in `ml/`

Every rolling statistic is computed on a trailing window and then
shifted, so the value at bar D uses only bars < D. This is the easiest
way to leak the future into a backtest and it fails silently — don't add
a feature that violates it. `ml/rolling.py`'s `IncrementalBarFeatures`
exists so a `SizingStrategy` (which sees the run bar-by-bar, with no
"whole DataFrame" hook) agrees with `features.py`'s offline computation
by construction, not by two implementations kept in sync by hand.

## Where the rest of the research lives (deliberately not here)

- `tools/` — one-off probes and measurements (`probe_*`, `measure_*`,
  `stage*`). That is a different agent's territory.
- `config/` — the sweep YAMLs each experiment was run from.

## Forbidden

- Importing anything from `server/`, `fidelity_gateway/`, or `tools/`.
- Adding an import FROM `engine/` INTO `research/` that would create a
  cycle — this direction only ever goes one way.
- Touching `web/`, `server/`, or `engine/` files directly — flag it
  instead if a change here has consequences there.
