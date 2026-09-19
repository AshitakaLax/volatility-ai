# research/

Algorithm development: the sizing strategies themselves, the machinery
that searches their parameter space, and the metrics that judge the
result. Open a session **here** for strategy work and you get the
algorithms without the order state machine, the broker adapters, the
live loop, the queue, or the web stack.

| Package | Key modules | Owns |
|---|---|---|
| `strategies/` | `size_calculators.py`, `high_frequency_sizing.py`, `bayesian_sizing_calculators.py`, `sizing_indicators.py`, `indicator_library.py`, `strategy_registry.py` | every concrete `SizingStrategy`, plus the registry mapping `strategy_id` → class |
| `optimization/` | `optimization_controller.py`, `search_strategies.py`, `walk_forward.py`, `monte_carlo.py`, `intraday_validation.py`, `trailing_target.py` | sweep orchestration (`_simulate_single` runs one combo), grid/Bayesian/random search, out-of-sample validation |
| `analysis/` | `performance_analyzer.py`, `analyze_annual.py` | result metrics, annualized vs. buy-and-hold |
| `ml/` | `features.py`, `labels.py`, `rolling.py`, `live_features.py`, `reachability_sizing.py`, `regime_scaled_sizing.py`, `qlib_regime.py`, `sources.py` | the learned-sizing research line — read-only research, not a trading input by default |
| `run_hf_sweep.py` | | the parallel sweep driver (`--n-jobs`, per-combination progress, checkpointed CSV) |

## The one direction that matters

`research/` imports `engine/`. **`engine/` never imports `research/`** —
that edge was removed deliberately and the split depends on it holding.
The engine calls a strategy only through `engine.core.sizing.SizingStrategy`
(the port); every class here is an adapter behind it, and
`strategies/strategy_registry.py` is the single place that knows the
concrete set exists.

If you find yourself needing an engine module to import something here,
that is the signal to move the shared thing down into `engine/core/`
(as `market_context.py` and the `SizingStrategy` ABC both were), not to
add the import.

## Adding a strategy

Subclass `SizingStrategy` (import it from `strategies.size_calculators`,
which re-exports the port) and register it in
`strategies/strategy_registry.py`. `BacktestConfig` stores `strategy_id`
as an opaque string and never resolves one itself, so nothing else needs
editing — `resolve_strategy` is the single mapping.

## Two rules the engine enforces on you

- **Never reimplement the no-loss comparison.** `engine/trading/no_loss_guard.py`
  is the only place a sell is checked against cost basis, and a test
  scans both `engine/` and `research/` for a reintroduced duplicate.
- **`record_tick` fires every bar; `calculate_trade_value` does not.**
  A stateful strategy must accumulate rolling state in `record_tick` —
  using `calculate_trade_value` for that gives a sparse, downward-biased
  sample, because it only runs on a confirmed trigger. See
  `engine/CLAUDE.md`'s decision-cycle section.

## Causal-transform rule, everywhere in `ml/`

Every rolling statistic is computed on a trailing window and then
shifted, so the value at bar D uses only bars < D. This is the easiest
way to leak the future into a backtest and it fails silently — don't add
a feature that violates it. `ml/rolling.py`'s `IncrementalBarFeatures`
exists specifically because a `SizingStrategy` sees the run bar-by-bar
with no "whole DataFrame" hook: it must agree with `features.py`'s
offline computation by construction, not by two implementations kept in
sync by hand.

## Where the rest of the research lives

Not everything research-shaped is in this directory, on purpose:

- `tools/` — the one-off probes and measurements (`probe_*`, `measure_*`,
  `stage*`). Left where they are because ~130 command lines across
  `README.md`, `plan.md` and `docs/` name those paths; see
  `tools/README.md`.
- `config/` — the sweep YAMLs each experiment was run from, and the
  reproduction index in `README.md`'s "Simulations run to date".
