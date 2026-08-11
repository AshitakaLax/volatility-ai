# Changelog

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
