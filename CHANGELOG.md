# Changelog

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
