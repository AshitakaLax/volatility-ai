# Implementation Task Specs

*Companion file: `architecture_overview.md` — read that first. Each task below is intended to be independently implementable when paired with it: give an agent the overview file plus exactly one task section to implement, test, and validate that task in isolation. Shared interfaces are canonical in the overview and must not be re-invented here.*

> **Revision v6 — AI-agent implementation precision.** This revision strengthens task independence by adding a mandatory implementation contract, explicit invariants, exact accounting rules where money/state are affected, deterministic sequencing requirements, concrete failure/recovery scenarios, and additional production-hardening tasks. The task document is deliberately more detailed than the overview; the overview remains the broad architectural context.

> **v6 focus:** remove remaining implementation-choice ambiguity around interfaces, persistence, event identity, fills, time/precision, search algorithms, configuration, reconciliation, shutdown, audit schemas, and the no-loss exit API. The architecture overview is the canonical source for shared policies; this file is the task-specific implementation authority.

## Task Independence Contract

A task is independently implementable only when an agent receiving **`architecture_overview.md` + this task subsection + the repository source** can implement and test it without relying on another task's prose or prior conversation context. Dependencies on code produced by another task are allowed only when listed under **Preconditions**.

Every task implementation MUST answer these questions, either explicitly in the task or by direct reference to a canonical contract in `architecture_overview.md`:

1. **Objective** — what changes and why.
2. **Scope / non-goals** — what is deliberately not changed.
3. **Inputs and outputs** — exact data entering/leaving the component.
4. **Public API** — exact class/function/config names and signatures when applicable.
5. **State ownership** — what state is read/written and who owns it.
6. **Sequencing** — where the behavior occurs relative to other operations.
7. **Side effects** — orders, cash/ledger mutations, persistence, logging, metrics, etc.
8. **Error behavior** — exceptions, rejection, retry, halt, or recovery semantics.
9. **Determinism** — ordering, random seeds, idempotency, and reproducibility requirements.
10. **Tests** — positive, negative, boundary, and recovery cases required for completion.
11. **Acceptance criteria** — observable, machine-testable completion conditions.
12. **Non-negotiable invariants** — especially the no-loss sell rule below.

If a task changes a shared interface, the task MUST say **"implement exactly as specified in `architecture_overview.md` §X.Y"** and must not create a competing interface.

### Mandatory repository-inspection procedure

Before editing any task's files, the implementing agent MUST:

1. Read every file listed under **Files touched / Files to inspect**.
2. Search the repository for every public symbol named by the task.
3. Identify all callers, subclasses, adapters, and tests of each changed public API.
4. Compare the repository signatures to the task/architecture signatures.
5. Record discrepancies before changing code. A discrepancy that changes the public contract is a **stop-and-report** condition unless the task explicitly provides an adaptation rule.
6. Never resolve an ambiguity by inventing a second interface, silently changing a caller, or implementing behavior belonging to another task.

### Mandatory task completion evidence

Every task implementation must provide or leave behind:

- Production files changed.
- Tests/fixtures changed or added.
- Exact verification command(s) executed.
- Any public API changed, with caller compatibility verified.
- State mutations and their authoritative owner.
- Evidence for positive, negative, boundary, and recovery cases applicable to the task.
- Determinism evidence where randomness, parallelism, search, or event replay is involved.
- Money/order evidence that accounting is based only on confirmed fills and preserves Rule One.

### Standard task structure

When a task section omits a field below, the agent must explicitly verify that the field is not applicable rather than infer that it was forgotten:

```text
Objective
Preconditions
Files to inspect
Files to modify
Public API
Inputs / Outputs
State ownership
Execution position
Behavior to preserve
Behavior to add/change
Error semantics
Determinism requirements
Forbidden behavior
Implementation steps
Required tests
Verification commands
Acceptance criteria
Definition of Done
```

### Definition of Done

A task is not complete merely because its happy-path acceptance test passes. Unless explicitly waived by the task, completion requires production implementation, focused tests, negative/boundary tests, regression tests for preserved behavior, type/lint checks used by the repository, and the task's exact verification commands.

## Expanded task map (v4)

The original 35 tasks remain intact. The following tasks were added because they close gaps that otherwise require an AI agent to infer architecture from unrelated tasks:

| Task | Purpose | Why independent agents need it |
|---|---|---|
| 4.8 | Domain exception hierarchy | Makes failure behavior machine-testable and composable. |
| 4.9 | Configuration/domain validation | Prevents invalid runs from reaching the simulation/live boundary. |
| 4.10 | Idempotent event processing | Prevents duplicate callbacks from corrupting accounting. |
| 6.3 | Immutable experiment/deployment artifacts | Ties live parameters to code/data/config provenance. |
| 6.4 | Secret/config separation | Prevents credentials from entering reproducible artifacts/logs. |
| 7.10 | Order lifecycle/state machine | Gives agents exact status/transition semantics. |
| 7.11 | Broker/account reconciliation | Defines restart/manual-intervention behavior. |
| 7.12 | Startup/shutdown lifecycle | Prevents unsafe half-started or forced-liquidation behavior. |
| 7.13 | Broker retry/rate limits | Makes ambiguous submission outcomes safe. |
| 7.14 | Durable audit/event schema | Makes every decision/fill/accounting transition reconstructable. |
| 7.15 | No-loss exit enforcement | Makes Rule One a hard execution invariant rather than a strategy convention. |

> **Synchronization note:** the companion `architecture_overview.md` task index should be synchronized with these additions when that file is next revised. The task sections themselves remain the implementation authority for task-specific behavior.

## Canonical implementation policies

Tasks inherit the following from `architecture_overview.md` and must not redefine them locally:

- **Time:** timezone-aware UTC internally; historical indexes are UTC and sorted.
- **Precision:** `MONEY_EPSILON = 1e-8`; `SHARE_EPSILON = 1e-6`; do not repeatedly round internal accounting.
- **Fill semantics:** broker `filled_qty` and `filled_avg_price` are cumulative order values; accounting applies only the delta since the last processed fill. Incremental notional is `current_qty * current_avg_price - previous_qty * previous_avg_price`, and incremental average price is incremental notional divided by incremental quantity.
- **Event identity:** one SHA-256 canonical event/decision ID scheme shared by Tasks 4.10, 7.4, and 7.14.
- **Persistence:** SQLite is the canonical live durable store; do not substitute JSONL/pickle/ad-hoc files.
- **Reconciliation:** mismatches are surfaced and resolved through reconciliation; no component silently chooses a side.
- **Determinism:** explicit seeds, stable ordering, and sequential/parallel equivalence are required where applicable.
- **Historical data:** required OHLCV columns are `open`, `high`, `low`, `close`, `volume`; UTC `DatetimeIndex`; sorted ascending; no duplicate timestamps; finite numeric values.

## Non-negotiable trading invariants

These apply to every task that can affect trading state, order generation, execution, or risk:

- **Never intentionally sell a lot at a realized loss.** No risk control, shutdown path, circuit breaker, reconnect handler, or broker error handler may submit or force a sell that violates the no-loss rule.
- A sell is permitted only when the **net proceeds for the quantity being sold are at least the allocated cost basis for that quantity**, after sell-side fees and modeled execution costs.
- Partial fills update only the filled quantity. Unfilled quantity remains open and retains its cost basis.
- A risk halt means **stop opening additional exposure**; it does not imply forced liquidation at a loss.
- Accounting is fill-driven: cash, positions, lots, and realized P&L change only from confirmed fills/reconciliation events.
- Duplicate events/orders must be idempotent: processing the same event twice must not double-count cash, shares, lots, or orders.
- Backtest and live paths must use the same strategy-facing contracts and the same decision ordering unless a task explicitly documents a simulation-only difference.

## Canonical money/accounting formulas

For tasks involving lots, fills, costs, or sells, use these definitions unless the architecture overview explicitly supersedes them:

```text
allocated_cost_basis = acquisition_notional + allocated_buy_costs + other attributable acquisition costs
net_sell_proceeds    = filled_quantity * effective_sell_price - sell_costs
realized_pnl         = net_sell_proceeds - allocated_cost_basis

sell_permitted iff net_sell_proceeds >= allocated_cost_basis
```

For a partial lot fill, allocate cost basis proportionally to the quantity sold unless the task explicitly defines another accounting method. The remaining quantity retains the remaining allocated basis.

## Canonical execution sequence

Where a task participates in a market-data decision cycle, preserve this ordering unless the task explicitly changes it:

```text
receive/validate market event
→ update market/account state
→ update peak equity/drawdown
→ construct immutable MarketContext
→ strategy.record_tick(context)
→ evaluate sell/harvest opportunities
→ evaluate buy/grid trigger
→ calculate proposed buy value
→ apply risk controls
→ create OrderIntent
→ submit through OMS/broker adapter
→ process confirmed fill events
→ update ledger/accounting
→ persist durable state
→ emit audit/observability event
```

A task may implement only one stage, but it must not silently reorder another stage.


---

## Phase 0 — Safety net

Prerequisite work before any code changes. Establishes a known-good baseline so Phase 1's intentional behavior changes can be verified against it instead of discovered by surprise.

### Task 0.1 — Add a regression fixture pinning current behavior

**Addresses:** Safety net (enables verification of Phase 1)
**Preconditions:** None
**Files touched:** new test fixture (e.g. `tests/fixtures/regression_baseline.py` + a small fixed CSV)

**Context**
Phase 1 intentionally changes runtime behavior — drawdown will start reaching sizing strategies, `record_tick` will start firing every bar. Before touching `optimization_controller.py`, capture what it currently outputs on a small, fixed dataset so any change afterward can be diffed against a known "before" state.

**Implementation**
1. Create a small synthetic OHLCV fixture (30-60 rows) with a known shape — a decline, then a recovery — small enough to run in milliseconds, large enough to exercise a few grid triggers and at least one profit-target harvest.
2. Instantiate `OptimizationController` with that fixture.
3. Run `run_sweep` with one `grid_step`, one `profit_target`, `FixedPortfolioPercentage`, one params dict.
4. Serialize the resulting single-row DataFrame (CSV or dict literal) as the "baseline" fixture output.
5. Write a test that re-runs the same call and asserts current output matches the saved baseline exactly. This test should pass right now, against the unmodified code.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Test passes against the current, unmodified `optimization_controller.py`.
- Baseline captures at minimum: final equity, trade count, Max Drawdown %, and the sweep's primary ranking metric.

### Task 0.2 — Branch/copy before editing

**Addresses:** Safety net (process)
**Preconditions:** None
**Files touched:** none (process step)

**Context**
The files this review was based on are read-only copies. Before applying any Phase 1+ change, confirm you're editing a working copy/branch of the real repository.

**Implementation**
1. Create a feature branch (e.g. `arch/phase-1-bugfixes`) off the working repository.
2. Confirm Task 0.1's regression test runs green on that branch before starting any Phase 1 edits.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Branch exists; Task 0.1's regression test passes on it before any Phase 1 code changes are made.

---

## Phase 1 — Fix the confirmed bugs (B1-B5)

No architecture change yet — these are minimal, targeted patches to the existing loop, chosen to fix real defects with the lowest possible risk. Sizing strategies get a small interim signature extension here (loose keyword args); Task 4.1 later consolidates everything onto a shared `MarketContext` object.

### Task 1.1 — Fix the Run Instructions example

**Addresses:** B1 (Critical)
**Preconditions:** None
**Files touched:** `Run_Instructions`

**Context**
The documented example calls `run_sweep(grid_steps=..., profit_targets=..., allocations=[0.01, 0.02])`. The real signature is `run_sweep(self, grid_steps: list, profit_targets: list, strategy_class, strategy_params_grid: list[dict])` — there is no `allocations` parameter, and both `strategy_class` and `strategy_params_grid` are required. Run as documented, this raises `TypeError` before a single bar is processed.

**Implementation**
1. Open `Run_Instructions`.
2. Replace the example script's call with one matching the real signature. If `allocations` was meant to sweep `FixedPortfolioPercentage`'s allocation percentage:
```python
from src.size_calculators import FixedPortfolioPercentage

strategy_params_grid = [{"allocation_pct": a} for a in [0.01, 0.02]]

results_df = controller.run_sweep(
    grid_steps=[0.005, 0.01, 0.015],
    profit_targets=[0.003, 0.005, 0.01],
    strategy_class=FixedPortfolioPercentage,
    strategy_params_grid=strategy_params_grid,
)
```
3. Confirm the exact constructor kwarg name against `src/size_calculators.py` — `allocation_pct` is a guess (see overview §8).
4. Run the corrected script against real or fixture data to confirm it executes without error.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- The example script in `Run_Instructions`, copy-pasted verbatim, runs to completion without raising.
- The parameter name used for `FixedPortfolioPercentage` matches the real constructor.

### Task 1.2 — Track peak equity / drawdown every bar

**Addresses:** B3 (High)
**Preconditions:** Task 0.1 (recommended)
**Files touched:** `optimization_controller.py`

**Context**
Peak-equity and drawdown are currently only recalculated inside `if current_price <= state.last_buy_price * (1.0 - step):` — so `state.max_drawdown` only samples drawdown on bars where a grid trigger is being evaluated, not every bar. This under-reports true drawdown, and would feed sizing strategies a stale/sparse drawdown value once Task 1.4 threads it through.

**Implementation**
1. In the `for timestamp, row in self.data.iterrows():` loop, compute `open_assets_val` / `total_equity` unconditionally at the top of every bar's iteration, not just inside the trigger `if`.
2. Move this block to run every bar:
```python
if total_equity > state.peak_equity:
    state.peak_equity = total_equity
current_dd = (state.peak_equity - total_equity) / state.peak_equity
if current_dd > state.max_drawdown:
    state.max_drawdown = current_dd
```
3. Keep the grid-trigger `if` block for the buy-decision logic only — it no longer needs to compute `total_equity`/`current_dd` itself, since both are now available from the per-bar computation above.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- `state.max_drawdown` reflects the true maximum peak-to-trough drawdown across the entire bar series, not just trigger bars — verify with a fixture where the deepest drawdown bar is *not* a trigger bar, and confirm `Max Drawdown %` still captures it.
- Existing trigger/buy behavior is otherwise unchanged.

### Task 1.3 — Call record_tick every bar (minimal fix)

**Addresses:** B4 (Critical)
**Preconditions:** Task 0.1 (recommended)
**Files touched:** `optimization_controller.py`

**Context**
`sizing_engine.record_tick(...)` is never called anywhere in the current file — only `calculate_trade_value` is invoked. Any strategy maintaining an internal rolling window (RSI, Bayesian macro/micro posteriors) expecting continuous ticks currently receives none.

**Implementation**
1. Inside the main bar loop, before the harvest/trigger logic, call `sizing_engine.record_tick(current_price)` unconditionally, every bar. (Confirm the real method signature against `src/size_calculators.py` and `src/bayesian_sizing_calculators.py` — it may take more than price.)
2. This is the Phase 1 interim form — a loose parameter, not the `MarketContext` object. Task 4.1 migrates this call to `record_tick(context)` per overview §5.2.
3. Check whether `calculate_trade_value` was already internally doing something equivalent to `record_tick` (undocumented) — if so, verify this change doesn't double-count once both are checked against source.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- A test strategy with an instrumented `record_tick` (e.g. a stub that counts calls) shows exactly one call per bar of historical data, regardless of whether that bar triggers a grid buy.
- Existing `calculate_trade_value`-driven behavior is unchanged for strategies that don't rely on `record_tick`.

### Task 1.4 — Thread drawdown into calculate_trade_value

**Addresses:** B2 (Critical)
**Preconditions:** Task 1.2 (drawdown must be computed every bar first), Task 0.1 (recommended)
**Files touched:** `optimization_controller.py`, `src/size_calculators.py`, `src/bayesian_sizing_calculators.py`

**Context**
`current_dd` is computed locally in `run_sweep` but the only call to the sizing engine — `sizing_engine.calculate_trade_value(total_equity, current_price)` — never passes it. This is very likely the exact mechanism behind `BellCurveProbabilitySizing` always seeing zero drawdown.

**Implementation**
1. Extend the call site:
```python
trade_value = sizing_engine.calculate_trade_value(
    total_equity, current_price, current_dd=current_dd
)
```
2. Extend `calculate_trade_value`'s signature to accept `current_dd: float = 0.0` as a new keyword argument with a safe default, on every `SizingStrategy` subclass in `src/size_calculators.py` and `src/bayesian_sizing_calculators.py` — at minimum `FixedPortfolioPercentage`, `BellCurveProbabilitySizing`, `RsiMomentumSizing`, and `BayesianDualScaleSizing` (see overview §8), plus any additional subclass found during inspection (e.g. `src/chatgpt_sizing_calculators.py`, if present — see overview §6). Strategies that don't use `current_dd` need no other change.
3. In `BellCurveProbabilitySizing` specifically, wire the new parameter into whatever internal drawdown-dependent logic previously always saw zero.
4. This is the Phase 1 interim form. Task 4.1 migrates this to `calculate_trade_value(context)` per overview §5.2.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- A test instantiating `BellCurveProbabilitySizing` and driving it through a scripted drawdown (via `run_sweep` on a fixture with a known decline) shows its size output responding to drawdown rather than staying flat at the zero-drawdown value.
- Strategies not using `current_dd` are unaffected (Task 0.1's regression fixture still matches for `FixedPortfolioPercentage`, modulo the now-correct drawdown/record_tick behavior from 1.2/1.3).

### Task 1.5 — Validate order fill status before crediting cash / closing lots

**Addresses:** B5 (High)
**Preconditions:** Task 0.1 (recommended)
**Files touched:** `optimization_controller.py`

**Context**
Both the harvest (sell) and buy paths currently trust `exec_res`/`order` unconditionally — cash is credited and lots are closed/registered without checking a fill-status field first. This is inconsistent with the live-trading path, which already reads real Alpaca order fields (`OrderStatus.FILLED`, `Order.filled_qty`, `Order.filled_avg_price`) rather than assuming instant fill.

**Implementation**
1. On the sell path:
```python
exec_res = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)
if exec_res.get("status") == OrderStatus.FILLED:  # confirm exact field/enum against src/order_management_system.py
    state.cash += (exec_res["qty"] * exec_res["filled_avg_price"])
    ledger.close_lot(lot)
else:
    logger.warning(f"Sell not filled for lot {lot.symbol}: status={exec_res.get('status')}")
```
2. Apply the equivalent check on the buy path before decrementing cash / calling `ledger.register_buy(...)`.
3. Confirm whether `OrderManagementSystem(mode="SIMULATION")` currently always returns a filled status — if so, this change should be a no-op for existing SIMULATION-mode behavior (verify with Task 0.1's fixture).


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Exact fill contract**
- Only `FILLED` (or the repository's confirmed equivalent terminal fill state) may mutate cash/ledger in the complete-fill path.
- `NEW`, `ACCEPTED`, `PENDING`, `PARTIALLY_FILLED`, `CANCELED`, `REJECTED`, and `EXPIRED` must not be treated as complete fills.
- Never use requested quantity as filled quantity; use the broker/OMS-confirmed filled quantity and average fill price.
- A non-filled order remains open/reconcilable and must not disappear from the strategy state.
- Do not close a lot until the no-loss validation for the confirmed filled quantity passes. If the order was created at a target that is no longer profitable after actual execution costs, reject/prevent that sell rather than recording a loss.

**Required negative tests**
1. Non-filled buy → no cash/lot mutation.
2. Non-filled sell → no cash/lot closure.
3. Partial sell → only filled quantity is removed and remaining cost basis remains open.
4. Confirmed fill whose effective net proceeds would realize a loss → sell is rejected and no loss is recorded.

**Acceptance criteria**
- Task 0.1's regression fixture output is unchanged, confirming SIMULATION mode still always fills today.
- A new test using a stubbed OMS that returns a non-filled status confirms cash is NOT credited and the lot is NOT closed/registered in that case.

### Task 1.6 — Re-run the regression fixture and document deltas

**Addresses:** Verification for Tasks 1.2-1.5
**Preconditions:** Tasks 1.2, 1.3, 1.4, 1.5
**Files touched:** test/fixture docs only

**Context**
Tasks 1.2-1.4 are expected to legitimately change output for indicator-based/drawdown-based strategies — that's the point, they were broken. This task confirms the change is isolated to what's expected, and also checks a related open question: whether `PerformanceAnalyzer.calculate_metrics` already computes its own drawdown figure that the controller's `metrics["Max Drawdown %"] = state.max_drawdown * 100.0` line would silently overwrite (overview §8).

**Implementation**
1. Re-run the Task 0.1 fixture test suite.
2. For `FixedPortfolioPercentage` (doesn't use drawdown or ticks in its sizing) — output should be unchanged versus the pre-Phase-1 baseline; investigate if it changed.
3. For any drawdown/tick-consuming strategy available, re-run and record the new output as an updated baseline, with a short note on what changed and why (link back to B2/B3/B4).
4. Confirm no naming collision between the controller's own `Max Drawdown %` and anything `PerformanceAnalyzer.calculate_metrics` independently produces.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- `FixedPortfolioPercentage` baseline is value-for-value identical to pre-Phase-1.
- A short changelog entry documents the expected metric shifts for drawdown/tick-consuming strategies.
- Confirmed: no silent overwrite between the controller's drawdown figure and the analyzer's own output.

---

## Phase 2 — Backtest fidelity (F1, F2, F3, F4)

### Task 2.1 — Add DataValidator

**Addresses:** F4 (High)
**Preconditions:** Phase 1 complete (recommended, for a clean baseline)
**Files touched:** new `src/data_validation.py`, `optimization_controller.py`

**Context**
`OptimizationController.__init__` currently accepts `historical_data` with no checks. A NaN in `close`, an unsorted index, missing columns, or an empty frame all currently fail silently — NaN comparisons are always `False` in Python, so a corrupted `close` column just produces a "0 trades" result instead of an error.

**Implementation**
1. Create `src/data_validation.py`:
```python
import pandas as pd

REQUIRED_COLUMNS = {"close"}  # extend to {"open","high","low","close","volume"} if/when OHLC is adopted (Task 2.3)

class DataValidationError(ValueError):
    pass

def validate(df: pd.DataFrame, *, warn_on_gap_pct: float = 0.15) -> None:
    if df.empty:
        raise DataValidationError("historical_data is empty.")
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise DataValidationError(f"historical_data missing required columns: {missing}")
    if df["close"].isna().any():
        raise DataValidationError("historical_data contains NaN values in 'close'.")
    if not df.index.is_monotonic_increasing:
        raise DataValidationError("historical_data index is not sorted ascending.")
    if df.index.duplicated().any():
        raise DataValidationError("historical_data contains duplicate timestamps.")
    pct_change = df["close"].pct_change().abs()
    big_jumps = pct_change[pct_change > warn_on_gap_pct]
    if not big_jumps.empty:
        import logging
        logging.getLogger("Optimizer").warning(
            f"{len(big_jumps)} bar(s) show a >{warn_on_gap_pct:.0%} single-bar move in 'close' "
            "- verify data is split/dividend adjusted."
        )
```
2. In `OptimizationController.__init__`, call `data_validation.validate(historical_data)` before assigning `self.data`.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Validation severity contract**
- **ERROR / reject:** empty input, missing required columns, NaN/non-finite required prices, non-positive prices, unsorted timestamps, duplicate timestamps, and invalid OHLC relationships once OHLC is required.
- **WARNING / accept:** unusually large but syntactically valid price moves or other conditions explicitly configured as warnings.
- Validation must not silently coerce bad trading data into a valid value.
- Error messages must identify the field and, when possible, the offending timestamp/index.

**Boundary fixtures**
Include at least: empty frame, missing column, NaN, `inf`, negative/zero price, duplicate timestamp, descending timestamp, valid large move, and valid normal data.

**Acceptance criteria**
- Constructing `OptimizationController` with an empty DataFrame, a DataFrame missing `close`, a NaN in `close`, an unsorted index, or duplicate timestamps each raises `DataValidationError` with a clear message.
- Constructing it with valid, already-clean fixture data succeeds silently.
- A fixture with one large single-bar jump logs a warning but does not raise.

### Task 2.2 — Add TransactionCostModel and wire into both fill paths

**Addresses:** F1 (High), F3 (Medium)
**Preconditions:** Phase 1 complete (touches the same buy/sell blocks as Task 1.5 — sequence after it)
**Files touched:** new `src/cost_models.py`, `optimization_controller.py`

**Context**
Every fill currently happens at the exact quoted price with zero commission and zero slippage — optimistic on both sides, unrealistic for a strategy that trades frequently by design.

**Implementation**
1. Create `src/cost_models.py` containing `TransactionCostModel`, `ZeroCostModel`, and `SlippageCommissionModel` exactly as specified in `architecture_overview.md` §5.3.
2. Add a `cost_model: TransactionCostModel = None` parameter to `run_sweep`, defaulting to `ZeroCostModel()` when `None` — preserves current behavior exactly.
3. At the sell fill point (after Task 1.5's status check passes), run the target price through `cost_model.apply_sell(price, qty)` before crediting cash; subtract the returned cost from proceeds.
4. At the buy fill point (after Task 1.5's status check passes), run `current_price` through `cost_model.apply_buy(price, qty)` before computing shares/decrementing cash; add the returned cost as an explicit deduction.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Cost-model contract**
- `apply_buy` / `apply_sell` calculate execution economics only; they do not mutate portfolio, ledger, or order state.
- The returned tuple is `(effective_fill_price, cost)`.
- Costs are applied exactly once. A commission must not be deducted both by the cost model and by the caller.
- `ZeroCostModel` is the exact backward-compatible default.
- Tests must verify buy and sell directionality: buy slippage increases effective price; sell slippage decreases effective price.
- Actual realized sell economics must feed the no-loss check; a target based only on quoted price is insufficient once costs are enabled.

**Acceptance criteria**
- With `cost_model=None` (or `ZeroCostModel()`), Task 1.6's regression fixture output is unchanged.
- With `SlippageCommissionModel(commission_per_trade=1.0, slippage_bps=5)`, a fixture run shows lower final equity than the zero-cost run, explainable by (trade count × commission) + slippage drag.

### Task 2.3 — Add optional intraday-replay validation pass

**Addresses:** F2 (High)
**Preconditions:** Task 2.2. **Soft dependency on Task 4.1** — can be implemented against the current inline loop (with some duplicated logic) or deferred until after 4.1 for a cleaner implementation that reuses `_simulate_single` directly. Recommend deferring if you're not implementing phases strictly in numeric order.
**Files touched:** new `src/intraday_validation.py` (per overview §6), called from `optimization_controller.py`

**Context**
Both the buy trigger and the sell-target check currently look only at daily `close`. A grid/limit-style strategy is really asking whether price touched a level at any point in the bar; the clearest failure mode is a sell target touched intrabar that reverses before the close, which the daily backtest simply never records, while a live intraday limit order would have filled it.

**Implementation**
1. Keep the existing daily-close sweep as the default, fast screening pass — no change to default behavior.
2. Add a method (e.g. `validate_finalists_intraday(finalist_params: list[dict], intraday_data: pd.DataFrame) -> pd.DataFrame`) that re-runs the single-combination simulation against minute-bar data for a short list of finalist parameter combinations, using `high`/`low` to detect any intrabar touch of a sell target the daily pass would have missed.
3. Surface a comparison: daily-close metrics vs. intraday-replay metrics per finalist, so divergence is visible rather than silent.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Intrabar ambiguity contract**
When OHLC data shows that both a buy trigger and a sell target were touched in the same bar but the order of touches cannot be established, do not assume the favorable order. The task must either require finer-grained data or apply a documented conservative ordering rule. The chosen rule must be deterministic and configurable.

**Default ordering rule:** consistent with the Canonical execution sequence (this file's front matter / overview §2.3, which evaluates sell/harvest before buy/grid-trigger), an ambiguous bar resolves the sell-target touch before the buy-trigger touch — harvest first against pre-buy lot state, then evaluate the grid trigger against the post-harvest cash/position. Expose this as a configurable parameter (e.g. `intrabar_priority: Literal["sell_first", "buy_first"] = "sell_first"`) rather than hardcoding it, so a finer-grained data source can override the default once available.

**Acceptance criteria**
- Given a fixture where a sell target is known to be touched intrabar and reversed by close, the intraday pass records that sell while a daily-close-only run does not.
- Default `run_sweep` behavior (daily-close screening) is unaffected — this is strictly additive/opt-in.

---

## Phase 3 — Risk management (R1, R2)

### Task 3.1 — Add RiskManager

**Addresses:** R1 (High)
**Preconditions:** None (additive)
**Files touched:** new `src/risk_manager.py`

**Context**
Nothing currently caps concurrent open lots or total capital deployed to the grid; on a sustained decline (realistic for 3x-leveraged TQQQ) the grid keeps buying every step down until cash is exhausted.

**Implementation**
1. Create `src/risk_manager.py` containing `RiskManager` exactly as specified in `architecture_overview.md` §5.4 — note it takes plain `equity`/`cash`/`open_lot_count` values rather than a context object, so it works unchanged before and after Task 4.1.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Risk semantics**
- RiskManager controls **new buy exposure**. It does not decide whether an existing profitable lot may be harvested.
- `max_total_exposure_pct` means gross deployed market value divided by current equity, using the exact exposure definition from the architecture overview.
- A cap produces a deterministic clamped value of `0 <= approved_value <= proposed_value`; it must never increase proposed exposure.
- `None` means unlimited for that specific control.
- Risk controls must not create a loss-making sell path.

**Acceptance criteria**
- With both limits `None` (default `RiskManager()`), `clamp_trade_value` is a no-op for any input.
- With `max_concurrent_lots=3`, a fixture that would otherwise open a 4th lot has that trade clamped to `0.0`.
- With `max_total_exposure_pct=0.5`, a fixture confirms deployed capital never exceeds 50% of equity.

### Task 3.2 — Wire clamp_trade_value into the buy path

**Addresses:** R1 (High)
**Preconditions:** Task 3.1
**Files touched:** `optimization_controller.py`

**Context**
`RiskManager` exists (Task 3.1) but isn't consulted anywhere yet.

**Implementation**
1. Add a `risk_manager: RiskManager = None` parameter to `run_sweep`, defaulting to `RiskManager()` (unlimited) when `None`.
2. Immediately after `sizing_engine.calculate_trade_value(...)` returns a proposed `trade_value`, clamp it against the loop's existing local variables:
```python
trade_value = risk_manager.clamp_trade_value(
    trade_value, total_equity, state.cash, len(ledger.open_lots)
)
```
3. No new object needed here — Task 4.1 later just changes this call site to read `context.equity`, `context.cash`, `context.open_lot_count` instead of these local variables; `RiskManager`'s own signature doesn't change.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Default `RiskManager()` produces output identical to Task 2.2's regression baseline.
- A capped `RiskManager` measurably reduces trade count / peak exposure versus the uncapped baseline on the same fixture.

### Task 3.3 — Add on_flat_reentry policy flag

**Addresses:** R2 (Medium)
**Preconditions:** None
**Files touched:** `optimization_controller.py`

**Context**
`last_buy_price` currently only updates on buys, never resetting when the portfolio goes fully flat (`len(ledger.open_lots) == 0`). After a full exit, re-entry stays gated on a further drop from a potentially stale, far-below-market reference price, which can leave the strategy sidelined for a long stretch.

**Implementation**
1. Add a parameter to `run_sweep` (or `BacktestState`): `on_flat_reentry: str = "stale_reference"`, allowed values `"stale_reference"` (current behavior) and `"reset_to_market"`.
2. Immediately after a sell that brings `len(ledger.open_lots)` to zero, if `on_flat_reentry == "reset_to_market"`, set `state.last_buy_price = current_price`.
3. Default stays `"stale_reference"` so existing behavior is unchanged unless explicitly opted in.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Default behavior (`"stale_reference"`) matches the Task 3.2 regression baseline exactly.
- `"reset_to_market"` on a fixture that goes fully flat then rallies shows the strategy re-entering sooner than the default policy would.

---

## Phase 4 — Software architecture (A1, A2, A3, A5, A6, A7, S1-S3)

Task 4.1 is the pivot point: everything after it works against the extracted `_simulate_single` and the shared `MarketContext`/`SizingStrategy` contract from `architecture_overview.md` §5.1-§5.2, instead of the inline loop and loose parameters Phases 1-3 used.

### Task 4.1 — Extract _simulate_single & Introduce MarketContext

* **Addresses / Preconditions / Files Touched:** A1 (Medium). Preconditions: Phase 1 complete. Files: `optimization_controller.py`, `src/size_calculators.py`, `src/bayesian_sizing_calculators.py`, new `src/market_context.py`.
* **Context:** The simulation loop is currently hardcoded inside `run_sweep`, making walk-forward testing impossible. Additionally, sizing strategies accept loose parameters. This task extracts the combination loop into a standalone `_simulate_single` method and unifies market state into a single, immutable `MarketContext` object.
* **Strict Type Signatures:**
    * Create in `src/market_context.py`:
        ```python
        @dataclass(frozen=True)
        class MarketContext:
            timestamp: datetime
            open: float
            high: float
            low: float
            close: float
            cash: float
            equity: float
            peak_equity: float
            drawdown: float
            open_lot_count: int
            bar_index: int
            
            @property
            def price(self) -> float:
                return self.close
        ```
    * Create in `optimization_controller.py` (`OptimizationController` class):
        ```python
        def _simulate_single(self, step: float, target: float, strategy_instance: SizingStrategy, symbol: str, initial_cash: float, cost_model: TransactionCostModel, risk_manager: RiskManager) -> SimulationResult:
        ```
      `SimulationResult` is defined once, canonically, in overview §5.6 (`src/market_context.py`) — do not redefine it here. This task only needs to populate `metrics`; leave `trade_blotter`/`equity_curve`/`params` at their defaults (Task 4.6 populates those later).
    * Update `SizingStrategy` base class:
        ```python
        @abstractmethod
        def record_tick(self, context: MarketContext) -> None: ...
        @abstractmethod
        def calculate_trade_value(self, context: MarketContext) -> float: ...
        ```
* **Permitted Imports:**
    * Allowed: `from dataclasses import dataclass`, `from datetime import datetime`, `from src.market_context import MarketContext, SimulationResult`.
    * Forbidden: Do not import specific sizing strategies directly into `optimization_controller.py`. It must rely strictly on the `SizingStrategy` abstract base class.
* **Implementation Steps:**
    1. Define the `MarketContext` dataclass exactly as specified above.
    2. Refactor every `SizingStrategy` subclass to accept `context: MarketContext` instead of loose parameters (`current_price`, `total_equity`, etc.) — at minimum `FixedPortfolioPercentage`, `BellCurveProbabilitySizing`, `RsiMomentumSizing`, `BayesianDualScaleSizing` (overview §8), plus any additional subclass found in `src/size_calculators.py` / `src/bayesian_sizing_calculators.py` during inspection.
    3. Extract the inner combination `for` loop from `run_sweep` into `_simulate_single`.
    4. Inside `_simulate_single`, instantiate `MarketContext` at the top of every bar iteration and pass it to `record_tick`, `_check_grid_trigger`, and `calculate_trade_value`.
    5. Update `run_sweep` to iteratively call `_simulate_single` for each parameter matrix.
* **State Mutation Scope:**
    * `MarketContext` must be declared with `frozen=True`. It is strictly read-only.
    * `_simulate_single` must instantiate a fresh `AssetLotLedger` and `OrderManagementSystem` for every run. It is strictly forbidden from mutating `self.data` or leaking state between combinations.
* **Mocking & Fixture Blueprint:**
    * Provide the unit test with a strict `pd.DataFrame` containing these exact columns: `["open", "high", "low", "close", "volume"]`, indexed by `pd.DatetimeIndex()`.


### Single-simulation lifecycle

`_simulate_single()` must execute one isolated combination in this order:

```text
create fresh simulation state
→ initialize cash/equity/peak/drawdown
→ initialize fresh AssetLotLedger and OrderManagementSystem
→ iterate validated OHLCV bars in timestamp order
→ update portfolio/account state
→ update peak equity and drawdown
→ construct immutable MarketContext
→ strategy.record_tick(context)
→ evaluate sells/harvests
→ evaluate grid trigger/buy
→ process simulated fills
→ update ledger/accounting
→ calculate final metrics
→ return canonical SimulationResult
```

At simulation end, open lots remain open; final portfolio/equity metrics must use the repository's canonical treatment of their value rather than silently discarding them. No strategy, ledger, OMS, RNG, or mutable cache may leak between parameter combinations.

### Verification commands

```bash
pytest -q <focused Task 4.1 tests>
pytest -q <existing optimization-controller regression tests>
```

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. This task extracts and unifies existing behavior — it does not change sizing math, cost/risk logic, or acceptance thresholds. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

* **Acceptance Criteria:**
    * Calling `_simulate_single` directly with a single parameter combination executes without throwing an error and returns a valid `SimulationResult`.
    * The `run_sweep` output matrix is mathematically identical value-for-value to the pre-Task 4.1 regression baseline.

### Task 4.2 — Swap iterrows for itertuples

**Addresses:** A3 (Medium)
**Preconditions:** Task 4.1
**Files touched:** `optimization_controller.py`

**Context**
`DataFrame.iterrows()` is one of the slower ways to iterate a DataFrame (it boxes each row as a Series, incurring dtype-coercion overhead), and this happens inside `_simulate_single`'s hot loop, once per combination in the sweep.

**Implementation**
1. Inside `_simulate_single`, replace:
```python
for timestamp, row in self.data.iterrows():
    current_price = row['close']
```
with:
```python
for row in self.data.itertuples():
    timestamp = row.Index
    current_price = row.close
```
2. Confirm column names accessed via attribute (`row.close`) match the DataFrame's actual column names — `itertuples` sanitizes non-identifier column names, so verify no column needs a `getattr(row, "...")` fallback.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Regression fixture output is unchanged.
- A simple timing comparison (e.g. `timeit` over a few hundred bars) shows a measurable speedup versus `iterrows()`.

### Task 4.3 — Parameterize hardcoded values & tighten types

**Addresses:** A4 (Low), S1 (Low), S2 (Low)
**Preconditions:** Task 4.1
**Files touched:** `optimization_controller.py`

**Context**
`"TQQQ"` and `100000.0` (duplicated in two places) are hardcoded; `mode="SIMULATION"` is a bare string rather than an enum; `strategy_class` has no type hint.

**Implementation**
1. Add `symbol: str = "TQQQ"` and `initial_cash: float = 100_000.0` parameters to `run_sweep` (defaults preserve current values); thread both through to `_simulate_single` instead of the literals.
2. Replace the two separate `100000.0` occurrences with the single `initial_cash` value.
3. If `OrderManagementSystem` exposes (or can reasonably be extended to expose) a `Mode` enum, use `Mode.SIMULATION` instead of the bare string `"SIMULATION"`; if not, note this as a follow-up dependent on `order_management_system.py`.
4. Add a `Type[SizingStrategy]` type hint to `strategy_class` (the ABC as defined in overview §5.2).


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Calling `run_sweep(...)` with no `symbol`/`initial_cash` arguments reproduces the existing regression baseline exactly.
- Calling with `symbol="SPXL"` and a matching fixture runs without hardcoded `"TQQQ"` leaking into order calls (verify via the OMS stub/mock recording what symbol it was called with).

### Task 4.4 — Per-combination error isolation

**Addresses:** A5 (High)
**Preconditions:** Task 4.1
**Files touched:** `optimization_controller.py`

**Context**
Currently, one bad parameter combination (an edge case in one strategy, a divide-by-zero, an OMS hiccup) raises an exception that aborts the entire sweep, discarding every previously computed result.

**Implementation**
1. In `run_sweep`'s combination loop, wrap the `_simulate_single` call:
```python
try:
    result = self._simulate_single(step, target, sizing_engine, symbol, initial_cash, cost_model, risk_manager)
    result_row = {"Grid Step": step, "Profit Target": target, **params, **result.metrics}
except Exception as e:
    logger.error(f"Combination failed [{idx+1}/{len(combinations)}] step={step} target={target} params={params}: {e}")
    result_row = {"Grid Step": step, "Profit Target": target, **params, "error": str(e)}
results.append(result_row)
```
2. Ensure the final `pd.DataFrame(results)` and Task 4.7's sort tolerate rows carrying an `error` key instead of the usual metrics keys.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- A fixture that deliberately makes one parameter combination raise (e.g. an invalid strategy param causing a `ZeroDivisionError`) still returns a DataFrame with all other combinations' results intact, plus one row carrying an `error` value.
- Regression fixture (no failing combinations) output is unchanged.

### Task 4.5 — Opt-in parallel execution via n_jobs

**Addresses:** A2 (Medium), S3 (Low)
**Preconditions:** Tasks 4.1, 4.4
**Files touched:** `optimization_controller.py`

**Context**
The sweep is embarrassingly parallel across `combinations` but runs strictly sequentially today.

**Implementation**
1. Add `n_jobs: int = 1` to `run_sweep` (default preserves current sequential behavior).
2. When `n_jobs == 1`, keep the existing sequential loop (with Task 4.4's try/except).
3. When `n_jobs > 1`, route combinations through `concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs)`, submitting one `_simulate_single`-wrapping task per combination and collecting results as they complete; each task keeps its own try/except (4.4) so a worker-process failure surfaces as an `error` row rather than killing the pool.
4. Confirm `self.data`, `strategy_class`, and each `params` dict are all picklable.
5. Reduce or gate `logger.debug` per-iteration logging when `n_jobs > 1` — each subprocess needs its own logging setup, and per-iteration debug logs across many processes get noisy fast.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Determinism contract**
For the same validated input, parameters, code, and random seed, `n_jobs=1` and `n_jobs>1` must produce the same set of results. Worker completion order must never determine ranking or metric values. Each worker receives isolated mutable strategy/ledger/OMS state. Any random process must receive an explicit per-combination seed derived deterministically from the parent seed and combination identity.

**Acceptance criteria**
- `n_jobs=1` regression fixture output is unchanged.
- `n_jobs=4` (or any >1) on a larger fixture produces a results DataFrame identical in content to `n_jobs=1` (row order may differ; sort or set-compare rows before asserting equality) and completes faster on a combination count large enough to show the benefit.

### Task 4.6 — Opt-in trade blotter / equity curve capture

**Addresses:** A6 (Medium)
**Preconditions:** Task 4.1
**Files touched:** `optimization_controller.py`, `src/market_context.py` (`SimulationResult` already exists there as of Task 4.1 / overview §5.6 — this task only populates fields it left at their defaults)

**Context**
Only the final aggregate metrics row survives past each combination today — there's no way to see why a given combination performed as it did.

**Implementation**
1. `SimulationResult` (overview §5.6) already has all four fields as of Task 4.1 — `trade_blotter`, `equity_curve`, and `params` simply default to empty until now. This task does not redefine the dataclass; it starts populating those three fields.
2. Inside `_simulate_single`, append a record to a blotter list on every buy and every sell (`context.timestamp`, side, price, qty, `context.equity`), and append `(context.timestamp, context.equity)` to an equity-curve list every bar.
3. Set `trade_blotter`, `equity_curve`, and `params` on the `SimulationResult` that `_simulate_single` already constructs and returns (Task 4.1) — the return type itself doesn't change.
4. Add `return_full_results: bool = False` to `run_sweep`. When `False` (default), behavior/return type is unchanged. When `True`, additionally return the list of `SimulationResult` objects (e.g. as a tuple `(summary_df, full_results)`).
5. Note: `len(trade_blotter)` per run is the "total tickets/segments evaluated" figure already planned for `backtest_runner.py` — no separate counter needed once this lands.
6. Confirm exactly which keys `PerformanceAnalyzer.calculate_metrics` returns (see overview §8 — it may include grid-specific metrics beyond the confirmed `Capital Velocity Index`) and make sure `SimulationResult.metrics` passes all of them through unmodified rather than remapping to a generic subset like Sharpe/CAGR only — a purpose-built metric set losing itself to a generic one defeats the point of having it.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- `return_full_results=False` (default) reproduces the existing regression baseline exactly, including return type (single DataFrame).
- `return_full_results=True` additionally returns one `SimulationResult` per combination, whose `trade_blotter` row count matches the combination's actual buys+sells and whose `equity_curve` has one entry per bar in the input data.
- `SimulationResult.metrics` contains every key `PerformanceAnalyzer.calculate_metrics` originally returned, unmodified.

### Task 4.7 — Harden the final ranking/sort

**Addresses:** A7 (Medium)
**Preconditions:** Task 4.1 (can be done independently, grouped here for scope)
**Files touched:** `optimization_controller.py`

**Context**
`.sort_values(by="Capital Velocity Index", ascending=False)` hardcodes a single column with no existence check, no tie-break, and no NaN/inf handling — a silent failure mode if that column is ever renamed, missing (e.g. on an `error` row from Task 4.4), or tied.

**Implementation**
1. Add `rank_by: str = "Capital Velocity Index"` and `tie_break_by: Optional[str] = None` parameters to `run_sweep`.
2. Before sorting, validate the column exists in the results DataFrame; raise a clear error naming the missing column and listing available columns if not.
3. Explicitly sink rows with no `rank_by` value (e.g. `error` rows from Task 4.4, or NaN/inf metrics) to the bottom regardless of sort direction, with a logged warning naming how many rows were excluded from ranking.
4. If `tie_break_by` is provided, use it as a secondary sort key.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Default call (`rank_by="Capital Velocity Index"`, no ties, no error rows) reproduces the existing regression baseline exactly.
- A results set containing one `error` row (from Task 4.4) sorts without raising, with the error row at the bottom.
- Passing a nonexistent `rank_by` column raises a clear error rather than a raw pandas `KeyError`.


### Task 4.8 — Define the domain exception hierarchy

**Addresses:** Reliability / predictable agent behavior
**Preconditions:** Task 4.1
**Files touched:** new `src/exceptions.py`; affected modules only where exceptions are currently generic

**Context**
Autonomous agents need predictable failure types. A generic `ValueError`/`Exception` makes it difficult for orchestration, tests, and live recovery code to distinguish invalid configuration from broker failure or state corruption.

**Implementation**
1. Define `TradingSystemError` as the root exception.
2. Add `ConfigurationError`, `DataValidationError`, `StrategyError`, `RiskError`, `ExecutionError`, `ReconciliationError`, and `PersistenceError` as stable domain exceptions.
3. Preserve the original exception as `__cause__` when wrapping lower-level exceptions.
4. Update only the modules touched by this task to raise the appropriate domain exception; do not broadly rewrite unrelated error handling.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. Do not retrofit every existing `raise` site in the codebase — only the modules this task's Files touched actually names. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Tests can distinguish configuration, data, execution, reconciliation, and persistence failures without matching error-message strings.
- Existing successful behavior is unchanged.
- Wrapped lower-level exceptions remain inspectable through exception chaining.

### Task 4.9 — Add configuration/domain validation helpers

**Addresses:** Configuration correctness
**Preconditions:** Task 4.3; Task 6.1 may consume these helpers later
**Files touched:** `src/config.py` or `src/validation.py`

**Context**
Parameter validation currently occurs implicitly or not at all. Invalid combinations should fail before a potentially expensive sweep or live startup.

**Implementation**
1. Validate numeric ranges: positive prices/steps/targets, non-negative costs, `0 <= exposure_pct <= 1`, positive lot limits, valid `n_jobs`, and valid search/ranking modes.
2. Validate cross-field relationships, such as a sell target/threshold being compatible with the strategy's configured grid semantics.
3. Raise `ConfigurationError` with the field name and offending value.
4. Keep validation pure; it must not mutate strategy or portfolio state.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. Whichever of `src/config.py` or `src/validation.py` you choose, use it consistently — Task 6.1 will import from wherever this task actually lands. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Every invalid boundary listed above has a focused test.
- Valid minimum/maximum boundary values are accepted.
- Validation runs before the first simulation or live order submission.

### Task 4.10 — Make event processing idempotent

**Addresses:** Duplicate market/fill/reconnect events
**Preconditions:** Task 4.1
**Files touched:** event/OMS/ledger handling modules as applicable

**Context**
Duplicate callbacks are possible in reconnecting or replayed systems. A handler that applies a fill twice can corrupt cash and lot state even when order submission itself is idempotent.

**Implementation**
1. Give each externally sourced event a stable identifier: for broker-sourced events (fills, order-status updates), use the broker's own order/event ID directly if the SDK guarantees it's stable and unique per event — confirm this against `alpaca-py`'s actual fields rather than assuming; for internally generated events (e.g. an order intent created before submission), generate a UUID at creation time and persist it before dispatch, not after.
2. Maintain a processed-event set appropriate to the runtime: an in-process set is sufficient for `SIMULATION` mode (bounded by the run's lifetime, no restart to survive); `LIVE` mode must persist the set so it survives restart, reusing Task 7.3's persistence layer rather than standing up a separate bespoke store.
3. Apply an event exactly once; repeated delivery returns the already-applied result without repeating side effects.
4. Retention: keep processed-event IDs at least as long as the broker/data source could plausibly redeliver them (e.g. across a reconnect or replay window) — do not expire them on a fixed short timer without confirming the broker's redelivery window first, and do not let unbounded growth become its own persistence problem. A reasonable default is to retain for the lifetime of the corresponding order/lot plus a configurable grace period.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. This task does not build the persistence layer itself (Task 7.3) or the reconnect/resubmission logic (Task 7.4) — it defines and applies the idempotency mechanism they plug into. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Idempotency scope contract**
This task, Task 7.4 (idempotent reconnect/duplicate-order protection), and Task 7.14 (durable audit/event schema) must share one event-ID scheme — the ID that gates re-application here is the same ID Task 7.14 records in the audit log and the same ID Task 7.4 checks before resubmitting an order. Do not invent three separate identifier schemes for what is functionally one problem; if this task lands before 7.4/7.14, document the scheme chosen here (in code comments and in the module's docstring) so those tasks adopt it rather than re-deriving their own.

**Acceptance criteria**
- Applying the same fill event twice changes cash/position/lot state exactly once.
- Replaying an already-processed event after restart remains a no-op.
- Event IDs are included in audit logs.
- The identifier scheme used here is documented clearly enough that Task 7.4 and Task 7.14 can reuse it without guessing.


---

## Phase 5 — Statistical robustness (M1, M2, M3)

### Task 5.1 — Implement WalkForwardRunner

**Addresses:** M1 (High)
**Preconditions:** Task 4.1 (needs `run_sweep`/`_simulate_single` as callable units); Phase 2/3 recommended for realistic evaluation but not blocking
**Files touched:** new `src/walk_forward.py`

**Context**
`run_sweep` currently picks a "best" parameter combination by scoring against the exact same historical sample it's optimizing over — a standard setup for overfitting/data-snooping bias, which matters more for a path-dependent, 3x-leveraged instrument like TQQQ.

**Implementation**
1. Create `src/walk_forward.py`:
```python
import pandas as pd

class WalkForwardRunner:
    def __init__(self, controller_factory, train_window: int, test_window: int,
                 step: int, anchored: bool = False):
        """controller_factory: callable(df_slice) -> OptimizationController,
        so each fold gets its own controller over the right data slice."""
        self.controller_factory = controller_factory
        self.train_window = train_window
        self.test_window = test_window
        self.step = step
        self.anchored = anchored

    def run(self, full_data: pd.DataFrame, grid_steps, profit_targets,
            strategy_class, strategy_params_grid, rank_by: str = "Capital Velocity Index") -> pd.DataFrame:
        folds = []
        start = 0
        while start + self.train_window + self.test_window <= len(full_data):
            train_start = 0 if self.anchored else start
            train_slice = full_data.iloc[train_start:start + self.train_window]
            test_slice = full_data.iloc[start + self.train_window:start + self.train_window + self.test_window]

            train_controller = self.controller_factory(train_slice)
            train_results = train_controller.run_sweep(grid_steps, profit_targets, strategy_class, strategy_params_grid)
            winner = train_results.sort_values(by=rank_by, ascending=False).iloc[0]

            test_controller = self.controller_factory(test_slice)
            test_results = test_controller.run_sweep(
                [winner["Grid Step"]], [winner["Profit Target"]], strategy_class,
                [{k: winner[k] for k in strategy_params_grid[0].keys()}]
            )
            folds.append({"fold_start": start, **{f"train_{k}": v for k, v in winner.items()},
                          **{f"test_{k}": v for k, v in test_results.iloc[0].items()}})
            start += self.step
        return pd.DataFrame(folds)
```
2. This is a first working version, not a final one — validate the winner-extraction / re-run logic against the actual `strategy_params_grid` dict shape once `src/size_calculators.py` is in view.


### Walk-forward fold contract

For each fold, the ordered data is split into a contiguous training window followed immediately by a test window. Parameter selection is performed using training data only. The selected parameter set is frozen before test evaluation. Strategy state is reset at the beginning of each fold unless the task explicitly tests state carry-over. Test results must never influence parameter selection for the same fold.

The configuration must explicitly define `train_bars`, `test_bars`, and `step_bars`; invalid/non-positive values are rejected. Fold boundaries are deterministic and reported in UTC.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Walk-forward isolation contract**
For every fold, parameter selection occurs only on the training window. The selected parameter set is frozen before the test window is evaluated. No test metric, test trade, or test-derived state may influence selection for that fold or later folds unless explicitly part of an anchored training policy. Indicator warm-up behavior must be deterministic and documented; do not leak test prices into training indicator state.

**Acceptance criteria**
- On a fixture long enough for at least 3 folds, `WalkForwardRunner.run(...)` returns one row per fold with both in-sample (`train_*`) and out-of-sample (`test_*`) metrics.
- Out-of-sample metrics are computed strictly on data the winning combination was never scored against during selection.

### Task 5.2 — Implement MonteCarloRunner

**Addresses:** M2 (Medium)
**Preconditions:** Task 4.1
**Files touched:** new `src/monte_carlo.py`

**Context**
There's currently no way to tell how sensitive a chosen parameter combination's results are to the specific sequence of historical returns — a single point estimate is all the sweep produces.

**Implementation**
1. Create `src/monte_carlo.py` with a block-bootstrap resampler (resample contiguous blocks of daily returns, not individual days, to preserve volatility clustering/autocorrelation) that reconstructs a synthetic price path from a chosen starting price.
2. `MonteCarloRunner.run(controller_factory, n_paths: int, block_size: int, step, target, strategy_class, strategy_params, seed: Optional[int] = None) -> pd.DataFrame`: generates `n_paths` synthetic price series, builds a fresh `OptimizationController` per path via `controller_factory`, runs `_simulate_single` (or a single-combination `run_sweep`) on each, and collects metrics.
3. Report percentiles (e.g. 5th/25th/50th/75th/95th) of CAGR, Max Drawdown %, and final equity across paths.


### Monte Carlo contract

Use a **block bootstrap of the ordered return series** as the canonical resampling method. The configuration must specify `iterations`, `block_size`, and `seed`. The original chronological sample is not modified. Each generated path is independently seeded from the configured seed using a deterministic child-seed sequence. Output ordering is iteration number ascending.

If insufficient observations exist for the configured block size, fail validation rather than silently changing the method.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Monte Carlo contract**
The task must distinguish the resampling unit from the reported uncertainty. At minimum document: return source, block construction, synthetic path reconstruction, seed handling, number of paths, and percentile calculation. Trade-order randomization, execution-cost perturbation, and parameter perturbation are separate techniques and are not silently substituted for block bootstrap.

**Acceptance criteria**
- With a fixed `seed`, two runs produce identical resampled paths and identical output.
- Percentile spread is visibly narrower for a lower-volatility fixture than a higher-volatility one, confirming the resampling is sensitive to the input data's actual volatility.

### Task 5.3 — Implement BayesianSearch as an alternate search_strategy

**Addresses:** M3 (Low)
**Preconditions:** Task 4.1
**Files touched:** new `src/search_strategies.py`, `optimization_controller.py`

**Context**
Parameter search today is pure brute-force `itertools.product`, which scales combinatorially as more strategy params are added; the codebase already has Bayesian machinery (`BayesianDualScaleSizing`) that the search process itself could borrow from in spirit.

**Implementation**
1. **Implement exactly as specified in `architecture_overview.md` §5.7. Do not redefine `SearchStrategy`.** The canonical interface is:
```python
class SearchStrategy(ABC):
    @abstractmethod
    def suggest(self) -> dict: ...

    @abstractmethod
    def report(self, params: dict, result: SimulationResult) -> None: ...
```
2. Implement `GridSearch` as the compatibility/default implementation and preserve the existing Cartesian-product ordering exactly.
3. Implement `BayesianSearch` using **Optuna** as the canonical optimizer. Do not introduce an alternative optimizer dependency for this task.
4. If batching is useful internally, add a private/internal batching mechanism; never change `suggest()` or `report()` to accept `n` or a scalar score.
5. The optimization objective is the configured ranking metric from Task 4.7. Higher-is-better/lower-is-better semantics must be explicit and ties must be deterministic.
6. The Bayesian sampler must accept an explicit seed and produce reproducible suggestions for the same study inputs.
7. Failed/invalid evaluations are reported through the canonical `SimulationResult`/error representation rather than crashing the search loop.
8. `OptimizationController.run_sweep(..., search_strategy=...)` accepts either implementation without special-casing concrete strategy classes.
9. If Optuna is unavailable, `search_strategy="bayesian"` must raise a clear configuration/dependency error rather than silently falling back to grid search.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Search objective contract**
The objective passed to Bayesian search is the configured `rank_by` metric, with its direction explicitly defined as maximize/minimize. Invalid parameter combinations must return a deterministic failed evaluation rather than crash the optimizer. Search bounds/types must be explicit for every parameter. The seed must make the search reproducible.

**Acceptance criteria**
- `search_strategy="grid"` (default) reproduces the existing regression baseline exactly, including evaluating every combination.
- `search_strategy="bayesian"` on a fixture with a known optimum reaches an objective within 5% of the known optimum while using no more than 75% of the evaluations required by the equivalent full grid, with the exact trial count recorded in the test.

---

## Phase 6 — Config & docs

### Task 6.1 — Introduce BacktestConfig & rewrite Run Instructions

**Addresses:** A4 follow-through, documentation completeness
**Preconditions:** Whichever of Phases 1-5 have actually been implemented
**Files touched:** new `src/config.py`, `Run_Instructions`

**Context**
By this point `symbol`, `initial_cash`, `cost_model`, `risk_manager`, `n_jobs`, `search_strategy`, `rank_by`, and `return_full_results` are all real parameters. Centralizing sensible defaults and documenting the current true API prevents `Run_Instructions` from going stale again (as it already had — Task 1.1).

**Implementation**
1. Create a `BacktestConfig` dataclass bundling the above with defaults matching today's values (`symbol="TQQQ"`, `initial_cash=100_000.0`, `cost_model=ZeroCostModel()`, `risk_manager=RiskManager()`, `n_jobs=1`, `search_strategy="grid"`, `rank_by="Capital Velocity Index"`, `return_full_results=False`).
2. Implement the canonical configuration schema as the source of truth. YAML loading is the required external representation for deployment/reproducible runs when a configuration file is used; it must deserialize into `BacktestConfig` and pass the same validation path as programmatic construction. Do not create a second YAML-only schema.
3. Rewrite `Run_Instructions` end to end against whatever subset of the new API actually exists in the codebase at the time this task is done — do not document parameters that haven't been implemented yet.


### Canonical BacktestConfig shape

The validated configuration must contain distinct sections for:

```text
strategy: strategy_id, strategy_params
backtest: symbol, initial_cash, date/time range, data settings
grid: steps, profit targets
costs: transaction-cost model configuration
risk: exposure/lot/drawdown limits
search: search strategy, ranking metric, direction, seed
execution: fill/intrabar/slippage settings
output: result/artifact settings
live: deployment/runtime settings (without secrets)
```

Required fields, defaults, enum values, numeric bounds, and cross-field validation must be explicit. Secrets are never fields in `BacktestConfig` and never serialized into its artifact representation.
### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Configuration schema contract**
Separate strategy parameters, backtest parameters, execution/cost parameters, risk parameters, and deployment/runtime settings. Required fields, defaults, enum values, numeric bounds, and cross-field validation must be explicit. Secrets/API credentials must never be serialized into experiment artifacts or configuration snapshots.

**Acceptance criteria**
- `Run_Instructions`'s example script, copy-pasted verbatim, runs to completion.
- Every parameter mentioned in `Run_Instructions` actually exists on `run_sweep` (or `BacktestConfig`) at doc-writing time.

### Task 6.2 — Extend the integration test suite

**Addresses:** Overall coverage for Phases 1-5, plus the Phase 7 scenarios below as those tasks land
**Preconditions:** Whichever of Phases 1-5 have actually been implemented, for scenarios 1-6 below. Scenarios 7-13 additionally require their named Phase 7 task (7.15, 7.2, 4.10, 7.11, 7.12, 7.13, 7.8 respectively) to exist first — do not attempt those before the corresponding task lands. This task is revisited incrementally across Phase 7 rather than completed in one pass.
**Files touched:** test suite

**Context**
Existing integration-test categories (cold start, uptrend, downtrend, flat, reversal, polymorphic paths, constructor guards) don't yet cover the new behaviors introduced above.

**Implementation**
Add one test per bullet, extending whichever of the corresponding tasks have landed:
1. `record_tick` called exactly once per bar regardless of trigger state (Task 1.3).
2. `calculate_trade_value` receives a non-zero drawdown during a scripted drawdown (Task 1.4).
3. Each `RiskManager` cap clamps rather than silently over-allocating (Tasks 3.1/3.2).
4. A single raised exception inside one combination doesn't abort the sweep (Task 4.4).
5. `n_jobs>1` output matches `n_jobs=1` output (Task 4.5).
6. Walk-forward out-of-sample metrics are computed on data never used for that fold's selection (Task 5.1).


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Additional required scenarios** (each requires its named Phase 7 task to already exist — add it then, not before)
7. No-loss sell guard rejects a sale when fees/slippage make net proceeds lower than allocated cost basis (Task 7.15).
8. Partial sell of 6/10 shares updates only the 6-share portion (Task 7.2).
9. Duplicate fill event is idempotent (Task 4.10).
10. Restart with local/broker mismatch enters reconciliation rather than silently trading (Task 7.11).
11. SIGTERM/graceful shutdown does not liquidate an open lot at a loss (Task 7.12).
12. Timeout after order submission reconciles before retrying (Task 7.13).
13. Live circuit breaker halts new buys but leaves profitable harvest processing intact (Task 7.8).

**Acceptance criteria**
- Each listed test exists, is named traceably to its source task, and passes against the current implementation state.


### Task 6.3 — Create immutable experiment/deployment artifacts

**Addresses:** L3 / reproducibility / promotion safety
**Preconditions:** Task 6.1; Task 5.1 recommended
**Files touched:** `src/config.py`, new artifact/provenance module, deployment output

**Context**
A winning parameter row is not sufficient to reproduce or safely deploy a strategy. The live system needs an immutable identity tying parameters to code, data, validation, and configuration.

**Implementation**
1. Create an artifact containing `deployment_id`, `strategy_id`, `strategy_version`, code commit, configuration hash, dataset identity/hash, experiment ID, validation status, creation time, and promotion status.
2. Serialize the artifact deterministically so the same inputs produce the same content/hash.
3. Make live startup reject an incomplete artifact.
4. Never include secrets in the artifact.

### Canonical artifact hash

Artifact hashes use SHA-256 over canonical UTF-8 JSON: lexical key ordering, no insignificant whitespace, explicit UTF-8 encoding, stable numeric serialization, and no secret fields. The same inputs must produce the same hash across processes and platforms.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. Do not use this task to also implement the secret-separation rules — that's Task 6.4's scope even though both touch `src/config.py`. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- Two artifacts generated from identical inputs have identical canonical hashes.
- Changing code/config/data identity changes the artifact identity.
- Live startup cannot proceed with missing required provenance fields.

### Task 6.4 — Separate secrets from configuration and experiment artifacts

**Addresses:** Operational/security hygiene
**Preconditions:** Task 6.1
**Files touched:** `src/config.py`, deployment documentation/tests

**Context**
Broker credentials and other secrets must not be mixed with reproducible strategy configuration.

**Implementation**
1. Define explicit secret inputs/environment variables or secret-provider hooks.
2. Ensure config serialization/redaction removes secret values.
3. Add a test that serializing a live configuration cannot contain API keys/secrets.
4. Document that a backtest artifact is safe to persist without credentials.

### Secret policy

For Alpaca live trading, credentials must be supplied through environment/secret-store mechanisms using the repository's configured names; when no existing names are present, use `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`. Secrets are forbidden in YAML/JSON configuration, command-line arguments, source control, artifact snapshots, audit payloads, and exception/log messages. Structured logging must redact credential values before serialization.
### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. Do not use this task to also build the provenance/hashing artifact — that's Task 6.3's scope even though both touch `src/config.py`. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- No secret value appears in serialized config, experiment artifacts, logs, or error messages.
- Live startup fails clearly when required credentials are absent rather than silently falling back to simulation.


---

## Phase 7 — Live execution parity & operational hardening (L1-L10)

Bridges the backtest/live gap identified while reviewing external feedback on this document set. Sequenced last because it depends on the rest of the system (extraction, fidelity, risk controls, config) being solid before trusting it with real capital — not because it's less important. See `architecture_overview.md` §4.2, §5.5, and §8 before starting: §8 in particular flags which of this phase's premises are confirmed vs. speculative. Task 7.9 specifically should not be started without confirming its premise first.

### Task 7.1 — Build or refactor the live execution loop around MarketContext

**Addresses:** L1 (High), L3 (Medium)
**Preconditions:** Task 4.1 (MarketContext must exist), Task 6.1 (config to load)
**Files touched:** `main.py` (if it exists) or a new live-loop entry point, Alpaca WebSocket integration code

**Context**
Live trading via Alpaca is a stated goal of this system, but nothing in this architecture represents how live ticks flow through the same `SizingStrategy` contract the backtester uses. The fix is architectural, not just documentation — the live loop and the backtest engine need to provably run the same strategy code, not just similar code. (External feedback on this document flagged this gap and proposed specific component names — `main.py`, a "State Dispatcher," a `StateBroadcaster` — that aren't confirmed against source; see overview §8. Read whatever live-execution code already exists, if any, before writing new code.)

**Implementation**
1. Confirm whether a live-execution entry point already exists in the codebase before writing anything new — if it does, read it first and adapt these steps to it rather than creating a parallel implementation.
2. On each incoming Alpaca WebSocket tick (post sanity-check, Task 7.6), construct a `MarketContext` (overview §5.1) exactly as `_simulate_single` does per bar — same field semantics, real-time values instead of historical-bar values.
3. Call `sizing_engine.record_tick(context)`, then `sizing_engine._check_grid_trigger(context, last_buy_price, step)`, then (if triggered) `risk_manager.clamp_trade_value(...)` and `sizing_engine.calculate_trade_value(context)` — the same call sequence `_simulate_single` uses, so live and backtest exercise identical strategy code paths.
4. Load the deployed parameter set (`BacktestConfig`/`config.yaml`, Task 6.1) at startup rather than hardcoding `grid_step`/`profit_target`/strategy params in the live loop.
5. Load Alpaca API credentials from environment variables or a secrets manager — never from a committed config file — and fail fast at startup with a clear error if they're missing, rather than surfacing an opaque auth failure later.
6. Route buy/sell decisions through `OrderManagementSystem` in its live mode (as opposed to `mode="SIMULATION"`).


### Shared decision-cycle contract

The live loop must invoke the same canonical decision-cycle implementation/path used by backtest after `MarketContext` construction. Do not maintain separate copies of sell/buy decision ordering. The live adapter supplies real market/account state and confirmed fills; the strategy-facing contract remains `MarketContext` + `SizingStrategy`.
### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Live/backtest parity contract**
The live loop must not contain a second implementation of strategy sizing or grid logic. It feeds the same `MarketContext`/`SizingStrategy` contract used by `_simulate_single`. Broker-specific details remain behind the OMS/broker adapter. The live loop must process confirmed fill events asynchronously and must not assume submission equals execution.

**Startup state**
Live startup must enter a non-trading/reconciliation state until configuration, persisted state, broker state, market-data validity, and time synchronization have all passed their checks.

**Acceptance criteria**
- The live loop's per-tick call sequence to `sizing_engine` is provably identical (same methods, same argument shapes) to `_simulate_single`'s per-bar sequence — e.g. via a shared helper function both call, not two independently-written copies.
- Starting the live loop with a missing/invalid Alpaca credential fails immediately with a clear error, before any WebSocket connection is attempted.
- A parameter set produced by a backtest sweep can be loaded into the live loop without manual code edits.

### Task 7.2 — Handle Partial Fills on Buy and Sell Paths

* **Addresses / Preconditions / Files Touched:** L4 (High). Preconditions: Task 1.5, Task 7.1. Files: `src/ledger.py`, `src/order_management_system.py`, Live Loop / `main.py`.
* **Context:** Alpaca broker execution routinely fills only part of a requested quantity (e.g., 4 shares out of 10). The current logic assumes requested quantity equals filled quantity. This task upgrades the accounting logic to parse Alpaca's actual `filled_qty` to prevent double-counting or phantom ledger shares.
* **Strict Type Signatures:**
    * Update in `src/ledger.py` (`AssetLotLedger` class) — **this signature is proposed, not confirmed; verify against the real method before changing it (overview §8 flags this exact question as open)**:
        ```python
        def close_lot(self, lot, sell_qty: float = None, execution_price: float = None, completed: bool = True) -> None:
        ```
      This must stay backward compatible with the existing call site (`ledger.close_lot(lot)` in `optimization_controller.py`'s `SIMULATION` path, unchanged since it was introduced and untouched by Tasks 1.5-4.x): when `sell_qty` is omitted, behavior is identical to today — full close of `lot`, `completed` honored exactly as it already is. When `sell_qty` is provided and less than the lot's remaining shares, the lot is left open regardless of the `completed` default; only an explicit `completed=True` or a `sell_qty` that exhausts `lot.shares` closes it. If the real signature already accepts fill price/qty in some other shape, adapt this proposal to match it — do not overwrite it, and do not break the existing full-close call path either way.
* **Permitted Imports:**
    * Allowed: `from alpaca.trading.models import Order`, `from alpaca.trading.enums import OrderStatus, OrderSide`.
* **Implementation Steps:**
    1. In the live sell path, intercept the Alpaca `Order` response. Extract `float(order.filled_qty)` and `float(order.filled_avg_price)`.
    2. Treat Alpaca `filled_qty` and `filled_avg_price` as **cumulative order values**. Compute:
   `new_fill_qty = current_qty - previous_qty`
   `new_fill_notional = current_qty * current_avg_price - previous_qty * previous_avg_price`
   `new_fill_avg_price = new_fill_notional / new_fill_qty` when `new_fill_qty > 0`.
   Only the incremental quantity/notional mutates cash, shares, cost basis, or realized P&L.
3. Pass the lot object being closed, the **newly filled quantity**, and the derived incremental fill price into `ledger.close_lot()` as `sell_qty` and `execution_price`.
    4. Inside `close_lot`, deduct `sell_qty` from `lot.shares` (defaulting to a full close when `sell_qty` is omitted, per the signature above).
    5. Only remove the lot from `self.open_lots` if `lot.shares <= SHARE_EPSILON` (to account for floating-point drift).
    6. In the live loop, credit the cash balance strictly by the **incremental fill notional** represented by the newly filled quantity/price, minus execution costs attributable to that incremental fill. Never use `new_fill_qty * cumulative_filled_avg_price`.
    7. Repeat the equivalent delta-fill accounting on the buy path (`register_buy`); do not register the cumulative quantity more than once.
* **State Mutation Scope:**
    * The portfolio `cash` balance is permitted to mutate ONLY by the broker-confirmed **incremental fill notional** (plus/minus explicitly attributable execution costs). The cumulative `filled_qty * filled_avg_price` value must never be applied twice. 
    * The ledger must mutate the `lot.shares` property, but it is strictly forbidden from mutating `lot.buy_price` or `lot.target_sell_price` during a partial split.
* **Mocking & Fixture Blueprint:**
    * To test, you must inject this exact Pydantic mock mimicking an Alpaca partial fill:
        ```python
        Order(id="test-123", status=OrderStatus.PARTIALLY_FILLED, qty="10.0", filled_qty="4.0", filled_avg_price="150.00", side=OrderSide.SELL)
        ```

### Cumulative-fill arithmetic fixture

Required unit test:
- update 1: `filled_qty=4`, `filled_avg_price=150` → delta qty `4`, delta notional `600`
- update 2: `filled_qty=7`, `filled_avg_price=151` → delta qty `3`, delta notional `457`
- update 3: `filled_qty=10`, `filled_avg_price=152` → delta qty `3`, delta notional `463`

The exact delta notionals above must be asserted.

### Cumulative-fill invariant

For a sequence of broker status updates `4 @ 150 → 7 @ 151 → 10 @ 152`, ledger/accounting quantity mutations must be `+4 → +3 → +3`, and notional mutations must be `+600 → +453 → +456`. Never calculate the second increment as `3 * 151` merely because 151 is the cumulative average price. If broker-reported cumulative quantity or notional decreases, enter reconciliation/error handling; never automatically reverse prior accounting.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. The durable write-through for these mutations is Task 7.3's scope, not this one's — this task only fixes the in-memory accounting. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

* **Acceptance Criteria:**
    * Submitting a mock sell `Order` that fills 4 out of 10 requested shares results in cash credited for exactly 4 shares.
    * The original `InventoryLot` remains in `ledger.open_lots` with a remaining share count of 6.
    * The backtest's simulated OMS behavior (which always fills completely) is unchanged — confirm the existing `ledger.close_lot(lot)` call site still works unmodified.
    
### Task 7.3 — Ledger persistence & crash recovery

**Addresses:** L2 (High)
**Preconditions:** Task 7.1
**Files touched:** `src/ledger.py`, new persistence layer (file/DB-backed)

**Context**
Nothing in this architecture addresses what happens to `AssetLotLedger`'s open-lot state if the live process restarts (deploy, crash, host reboot). Without durable persistence, a restart risks losing track of open lots entirely — double-buying positions the system already holds, or losing the target sell price for a real, already-owned lot.

**Implementation**
1. Confirm whether `AssetLotLedger` already persists to anything — this may already exist and simply not have been reviewed yet.
2. If persistence does not already exist, implement it using the **canonical SQLite backend** defined in `architecture_overview.md` §2.6. Do not use JSONL/pickle/ad-hoc files. The persistence layer must expose transactionally atomic operations for lot mutations, revisions, and processed-event records.
3. On live-loop startup, reload open lots from that store before processing the first tick, so `last_buy_price` and all open lots are reconstructed accurately.
4. Reconcile reloaded ledger state against Alpaca's actual account/position data at startup, and log (or halt) on any mismatch rather than silently trusting local state that might be stale.


### Minimum persistence schema

The implementation must provide, at minimum, tables equivalent to `ledger_lots`, `revisions`, and `processed_events`; if Task 7.14 is co-located, `audit_events` may share the same database. Every record has a schema version and monotonic revision/sequence. Ledger mutation plus its revision/event record must commit atomically.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Durability contract**
Persistence must be atomic enough that a crash cannot leave a half-written lot mutation. Persist a schema/version and a monotonically increasing event or revision identifier. Recovery must be idempotent. If persisted state and broker state disagree, the system must not silently choose one; it enters reconciliation/halt state according to the reconciliation policy.

**Acceptance criteria**
- The live implementation uses the canonical SQLite persistence backend and exposes the required minimum tables/records.
- Simulating a process restart mid-run (kill and relaunch the live loop against the same persistent store) reconstructs the exact same open-lot state that existed before the restart.
- A deliberately corrupted/mismatched persistent store (vs. Alpaca's real positions) is detected and surfaced rather than silently trusted.

### Task 7.4 — Idempotent reconnect / duplicate-order protection

**Addresses:** L5 (Medium)
**Preconditions:** Task 7.1, Task 7.3
**Files touched:** live loop, `src/order_management_system.py`

**Context**
If the live loop reconnects after a network blip or restart, it must not re-submit an order for a grid trigger it already acted on before the disconnect — that risks buying (or selling) the same signal twice.

**Implementation**
1. Assign each trigger decision the canonical stable `decision_id` from `architecture_overview.md` §2.5 before submitting the order to Alpaca, using the broker client-order-ID mechanism exposed by the installed `alpaca-py` SDK. Before editing, verify the installed SDK field/method names. If the installed SDK lacks a client-order-ID facility, stop and report the dependency rather than inventing a broker-side substitute; the local persisted decision ID must still prevent a duplicate submission after reconnect.
2. On startup/reconnect, check Task 7.3's persisted ledger/order log for any decision already acted on before re-evaluating triggers for the same period, to avoid double-submission.


### Idempotency-key contract

The same logical decision must reuse the same client/order identity across reconnects. A new ID may be generated only for a genuinely new decision. The identifier used here must be the same ID consumed by Task 4.10 and recorded by Task 7.14.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**Idempotency contract**
Every decision/order intent must have a stable client-side identifier. The same intent replayed after reconnect must resolve to the existing order/result rather than create a second order. Fill events also require deduplication by broker/event identifier or equivalent stable key. The implementation must test the ambiguous case where local state says `SUBMITTED` and broker state says `FILLED`.

**Acceptance criteria**
- Deliberately reconnecting the live loop mid-session (simulated) does not result in a duplicate order for a trigger already filled before the reconnect.
- The idempotency key scheme is confirmed to actually map onto a real `alpaca-py` deduplication mechanism, not assumed to exist.

### Task 7.5 — Dynamic, volatility-aware slippage model

**Addresses:** L6 (Medium)
**Preconditions:** Task 2.2, Task 4.1
**Files touched:** `src/cost_models.py`

**Context**
`SlippageCommissionModel` (overview §5.3, Task 2.2) uses a flat `slippage_bps` regardless of market conditions. Real slippage is materially wider around the open, during fast-moving/high-volatility periods, or around scheduled data prints, than during calm mid-day trading — a static model understates cost exactly when it matters most.

**Implementation**
1. `architecture_overview.md` §5.3 now has optional `context`/`prev_close` parameters on `TransactionCostModel.apply_buy`/`apply_sell` (defaulting to `None`, ignored by `ZeroCostModel`/`SlippageCommissionModel`) — if Task 2.2 was already implemented against the prior signature, add these two optional parameters now; existing call sites that don't pass them are unaffected.
2. Implement `DynamicSlippageModel` in `src/cost_models.py` exactly as specified in overview §5.5 — scales slippage by the current bar's absolute percentage move versus the previous bar's close.
3. Update `_simulate_single`'s fill call sites to pass `context` and the previous bar's close through to `cost_model.apply_buy`/`apply_sell` (a no-op for `ZeroCostModel`/`SlippageCommissionModel`, since they ignore the extra arguments).
4. Optional refinement, not required for this task: swap the single-bar-move proxy for a proper Average True Range (ATR) calculation if a smoother volatility estimate is wanted later.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- With `DynamicSlippageModel`, a fixture containing one unusually large single-bar move shows a visibly wider effective fill spread on that bar than on calmer bars.
- `ZeroCostModel` and `SlippageCommissionModel` behavior is completely unchanged by the signature extension.

### Task 7.6 — Live tick data sanity-checking

**Addresses:** L7 (Medium)
**Preconditions:** Task 7.1
**Files touched:** new validation in the live loop, reusing patterns from `src/data_validation.py` (Task 2.1)

**Context**
`DataValidator` (Task 2.1) only validates the batch `historical_data` passed once at `__init__` — it has no equivalent for live ticks arriving one at a time over a WebSocket. A single bad print (zero/negative price, an obviously erroneous spike from a feed glitch) processed as real market data could trigger a nonsensical trade.

**Implementation**
1. Add a lightweight per-tick check (not the full batch `DataValidator`, which isn't suited to streaming data): reject a tick with a non-positive price, and reject an implausibly large single-tick move versus the last known-good price. A rejected spike must not reach strategy evaluation, must not update the last-known-good price, and must not submit an order.
2. Route rejected ticks to the canonical observability/audit path when available; otherwise emit the repository-standard structured log. Never silently drop a rejected tick. Valid ticks surrounding a rejected tick continue processing normally.


### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- A synthetic tick stream containing one zero-price and one absurd-spike tick results in both being rejected/flagged rather than processed as real triggers, while surrounding valid ticks are processed normally.

### Task 7.7 — Paper-trading validation gate before live capital promotion

**Addresses:** L8 (Medium)
**Preconditions:** Task 7.1
**Files touched:** deployment process / runbook, not necessarily code

**Context**
Nothing in this architecture requires a parameter set to prove itself against real-time (but risk-free) execution before real capital is committed — Alpaca's paper-trading environment exists specifically for this and isn't currently part of the pipeline.

**Implementation**
1. Define a promotion gate: a parameter set that passes the backtest sweep (and ideally Task 5.1's walk-forward validation) must run against Alpaca's paper-trading endpoint for a minimum period/trade count before `OrderManagementSystem`'s live mode is enabled for it.
2. Track paper-trading results the same way `SimulationResult` (Task 4.6) tracks backtest results, so the two are directly comparable.
3. Make it operationally hard to skip — e.g. `OrderManagementSystem`'s live mode could require an explicit flag/confirmation rather than being a simple config toggle.


### Promotion criteria

Promotion to live requires explicit, machine-checkable thresholds in configuration. At minimum: minimum paper-trading duration, minimum number of strategy decisions/fills, zero accounting discrepancies, zero duplicate-order incidents, zero no-loss guard violations, no unresolved reconciliation state, and no unhandled runtime exceptions. Threshold values must be recorded in the promotion artifact rather than inferred from operator judgment.
### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- The documented promotion path requires a paper-trading period between "passed backtest" and "live capital enabled" — no code path exists that goes directly from a backtest result to live capital.

### Task 7.8 — Live circuit-breaker / kill-switch

**Addresses:** L9 (High)
**Preconditions:** Task 3.1, Task 7.1
**Files touched:** `src/risk_manager.py`, live loop

**Context**
The backtest `RiskManager` (overview §5.4, Task 3.1) clamps trade size when a cap is exceeded — appropriate for a sweep, but a live system arguably needs a harder stop for extreme scenarios (drawdown beyond a threshold, an unexpected string of losses, a data feed anomaly): one that halts new buys entirely and alerts a human, rather than just sizing down.

**Implementation**
1. Add a live-only `halt_new_buys_if_drawdown_exceeds: Optional[float] = None` setting, checked at the same point `clamp_trade_value` is called, distinct from the sizing clamp — this fully blocks new entries rather than reducing them, while existing sell/harvest logic continues to run so open positions can still be exited/harvested normally.
2. Wire the halt state into Task 7.1's observability layer so a human is actually notified, not just silently protected.
3. Require an explicit manual reset to resume buying after a halt — don't auto-resume once the drawdown recovers, since the point is to force a human look at what happened.


### HALTED_NEW_BUYS behavior

When halted:

| Operation | Allowed |
|---|---|
| Receive/validate market data | Yes |
| Update strategy rolling state | Yes |
| Evaluate profitable exits | Yes |
| Submit a sell that passes the no-loss guard | Yes |
| Generate new buy exposure | No |
| Submit buy orders | No |
| Apply confirmed fills | Yes |
| Persist/audit state | Yes |

The halt persists across restart until the configured/manual reset condition is satisfied.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.



**No-loss shutdown invariant**
A circuit breaker or kill switch **must never force liquidation solely because the system is halted**. Its default action is `HALT_NEW_BUYS` plus alerting. Existing lots remain eligible for normal profitable harvest. Any emergency sell mechanism would require a separate, explicitly approved policy and must still enforce the no-loss invariant.

**State contract**
Use explicit states such as `ACTIVE`, `HALTED_NEW_BUYS`, and `MANUAL_RESET_REQUIRED`; persist the halt state across restart.

**Acceptance criteria**
- A live (or live-simulating test) scenario that crosses the configured drawdown threshold stops new buy orders while continuing to process sells for existing lots.
- The halt persists across a restart (ties to Task 7.3) until manually cleared.


### Task 7.10 — Define the order lifecycle/state machine

**Addresses:** Execution correctness / L4-L5 / operational clarity
**Preconditions:** Task 7.1
**Files touched:** `src/order_management_system.py`, new order-state definitions/tests

**Context**
Order status is currently handled as ad-hoc strings/SDK values. A deterministic lifecycle prevents invalid transitions and makes partial fills, cancellation, reconnect, and reconciliation implementable independently.

**Implementation**
1. Define canonical internal states such as `CREATED`, `SUBMITTED`, `ACCEPTED`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `REJECTED`, `EXPIRED`, and `UNKNOWN`.
2. Define allowed transitions and reject/log invalid transitions.
3. Map broker-specific statuses into these internal states at the adapter boundary.
4. Keep requested quantity, filled quantity, remaining quantity, average fill price, client order ID, broker order ID, and timestamps as separate fields.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. This task defines the state machine and its transitions — it does not implement reconciliation logic (Task 7.11) or retry logic (Task 7.13), both of which consume the states defined here. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**State transition contract**
Absent a confirmed existing state machine in `src/order_management_system.py`, implement this default transition table (reject and log any transition not listed):
- `CREATED → SUBMITTED`
- `SUBMITTED → ACCEPTED | REJECTED | UNKNOWN`
- `ACCEPTED → PARTIALLY_FILLED | FILLED | CANCELED | EXPIRED`
- `PARTIALLY_FILLED → PARTIALLY_FILLED | FILLED | CANCELED`
- `FILLED | CANCELED | REJECTED | EXPIRED` — terminal; no further transitions.
- `UNKNOWN → any state` — only via an explicit reconciliation/query resolution (Task 7.11), never via inference.

**Acceptance criteria**
- Every broker status used by the implementation maps to one canonical internal state.
- Invalid transitions are rejected without mutating accounting.
- Partial-fill transitions preserve remaining quantity.
- The transition table above (or a documented, confirmed replacement) is enforced, not just described in a comment.

### Task 7.11 — Broker/account reconciliation

**Addresses:** Restart safety / execution correctness
**Preconditions:** Tasks 7.3, 7.10
**Files touched:** live reconciliation module, ledger/OMS integration

**Context**
Local state can diverge from broker state after crashes, network failures, manual broker actions, or missed callbacks. The system needs a formal reconciliation operation before it resumes trading.

**Implementation**
1. Fetch broker open orders, positions, cash/equity, and relevant fills.
2. Compare against persisted local state using stable order/lot identifiers.
3. Automatically repair only discrepancies that are unambiguously derivable from broker-confirmed events.
4. For ambiguous discrepancies, enter `RECONCILIATION_REQUIRED` / `HALTED_NEW_BUYS` and alert the operator.
5. Never manufacture a profitable or loss-making local transaction merely to make totals match.

### Reconciliation decision table

Apply the canonical precedence from `architecture_overview.md` §2.7:

| Condition | Required state/action |
|---|---|
| Local and broker agree | `READY`; continue |
| Broker has an unknown fill/order | Import/reconstruct it, then reconcile ledger/accounting |
| Local order absent at broker | Query by stable client order ID; if unresolved, `UNKNOWN`/halt |
| Position quantity mismatch | `RECONCILIATION_REQUIRED`; never invent a fill |
| Cash mismatch | `RECONCILIATION_REQUIRED`; no trading from guessed cash |
| Cumulative fill decreases | `RECONCILIATION_REQUIRED`; never reverse automatically |
| Ambiguous submission | Query/reconcile before resubmission |
| Unresolvable mismatch | Remain halted until explicit/manual resolution |

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. Do not build the persistence layer (Task 7.3) or the order-state machine (Task 7.10) here — reconciliation consumes both. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**"Unambiguously derivable" contract**
A discrepancy is **unambiguous** (auto-repair permitted) only when a broker-confirmed event trail exactly and uniquely explains the delta — e.g. the broker reports a fill for an order the local state already has as `ACCEPTED`/`PARTIALLY_FILLED` under a known client order ID, and the resulting position/cash delta matches that fill exactly. A discrepancy is **ambiguous** (must halt) whenever: no broker event/order ID explains the delta (e.g. a trade placed outside this system); more than one local order could plausibly explain the same delta; or the broker shows more shares/cash than local records with no corresponding fill in the event trail. When in doubt, treat it as ambiguous — an unnecessary halt is recoverable, an incorrect auto-repair is not.

**Acceptance criteria**
- Matching local/broker state returns `READY`.
- Known recoverable differences (per the contract above) converge to broker-confirmed state.
- Ambiguous differences halt new buys and produce an actionable diagnostic naming the specific unexplained delta.

### Task 7.12 — Startup recovery and graceful shutdown

**Addresses:** Operational lifecycle
**Preconditions:** Tasks 7.3, 7.8, 7.11
**Files touched:** live entry point/runtime lifecycle

**Context**
Container restarts and deployment signals must not leave the strategy half-active. Shutdown must preserve state and must not force a loss-making liquidation.

**Implementation**
1. Implement startup states: `STARTING → LOAD_CONFIG → LOAD_STATE → CONNECT_BROKER → RECONCILE → VALIDATE_DATA/CLOCK → READY`.
2. Do not accept new buys before `READY`.
3. On shutdown, stop generating new orders, persist state, flush audit events, and wait for a bounded period for in-flight state to settle.
4. Do not automatically liquidate open lots on shutdown.
5. If the process cannot persist/reconcile safely, exit to a state that requires explicit recovery rather than guessing.

### Shutdown sequence contract

On shutdown request:

```text
1. transition runtime to SHUTTING_DOWN
2. stop accepting new buy decisions
3. stop new market-triggered strategy evaluations
4. continue consuming broker/order/fill events
5. apply confirmed fills through the normal accounting path
6. enforce the no-loss guard for any exit that is still allowed
7. persist durable state and audit events
8. if in-flight state cannot settle within the bounded window, enter RECONCILIATION_REQUIRED
9. close external connections and exit without forced liquidation
```

Existing orders are not automatically canceled unless a separate explicit policy says so. The shutdown path must never manufacture a final state from an unconfirmed broker response.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. This task sequences startup/shutdown around Tasks 7.3, 7.8, and 7.11 — it does not reimplement their internals. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Bounded shutdown window**
Default the in-flight settle wait to 30 seconds, configurable. If in-flight orders/state haven't settled when the window elapses, do not force-liquidate and do not force-persist a guessed state — exit into the same `RECONCILIATION_REQUIRED` state Task 7.11 defines, so the next startup reconciles rather than trusts an unsettled snapshot.

**Acceptance criteria**
- Restart recovery never generates a duplicate order for an already-acted-on decision.
- SIGTERM/SIGINT or equivalent graceful shutdown persists state and does not submit new buys after shutdown begins.
- Open profitable harvest opportunities remain available after restart.
- A shutdown that hits the bounded window without settling exits into `RECONCILIATION_REQUIRED`, not a guessed clean state.

### Task 7.13 — Broker rate limits, retry, and transient-failure handling

**Addresses:** Live reliability
**Preconditions:** Task 7.1, Task 7.10
**Files touched:** broker adapter/OMS

**Context**
Network failures, timeouts, rate limits, and transient broker errors are normal. Retrying a non-idempotent order without a stable client identifier can create duplicate exposure.

**Implementation**
1. Classify broker errors into retryable, non-retryable, and unknown/ambiguous submission outcomes.
2. Use bounded exponential backoff for retryable reads/requests.
3. For an ambiguous order submission, reconcile/query by client order ID before retrying submission.
4. Enforce broker rate limits without blocking state reconciliation indefinitely.
5. Surface repeated failures to the circuit-breaker/observability layer.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. Reconciliation logic itself belongs to Task 7.11 — this task only decides when to retry, when to stop, and when to hand off to reconciliation instead. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Backoff and classification contract**
Canonical retry parameters: base delay 1s, multiplier 2x, max 5 total attempts including the initial request, cap 30s, and ±20% jitter. These values are configurable only through the canonical retry configuration and must default to these values. Classification must be confirmed against `alpaca-py`'s actual exception/status surface rather than assumed: connection errors, read/non-submitting timeouts, and 5xx responses are retryable; 4xx authentication/authorization/validation errors are non-retryable and surface immediately; any timeout or connection failure **after an order submission was sent** (i.e. it is unknown whether the broker received it) is ambiguous, not retryable, and must go through Task 7.10's `UNKNOWN` state and Task 7.11's reconciliation-by-client-order-ID before any resubmission is considered.

**Acceptance criteria**
- A timeout after order submission does not automatically submit a second order before reconciliation.
- Retryable read failures recover within the configured retry budget.
- Non-retryable errors are surfaced immediately with no blind retry.
- An ambiguous submission outcome resolves through reconciliation (Task 7.11), never through a bare retry.
- Backoff tests verify the exact default sequence is bounded by 1s, 2s, 4s, 8s, and 16s before jitter, with no more than 5 total attempts.
- Jitter remains within ±20% of each calculated delay.
- A broker-provided rate-limit retry time is honored when present and never causes an unbounded reconciliation stall.

### Task 7.14 — Durable audit/event schema

**Addresses:** Reproducibility / diagnostics / compliance-quality traceability
**Preconditions:** Tasks 4.10, 7.10
**Files touched:** new audit/event module and persistence integration

**Context**
A top-tier trading system must be able to reconstruct why an order existed, what the strategy saw, what risk decided, and what actually filled. Ordinary logs are not a sufficient canonical audit trail.

**Implementation**
1. Define an immutable event schema containing at least event ID, sequence, timestamp, event type, schema version, strategy/deployment identity, and payload.
2. Record decision, risk, order intent, broker status, fill, ledger mutation, reconciliation, and halt events.
3. Ensure event ordering is deterministic within a stream using sequence numbers rather than timestamps alone.
4. Make audit writes durable before acknowledging state transitions that require them — "durable" means flushed/fsynced (or the equivalent commit acknowledgment for a DB-backed store) before the caller proceeds, not merely written to an in-process buffer.

### Required event payload schemas

At minimum, these event types must have explicit payload fields:

```text
MARKET_CONTEXT: timestamp, symbol, OHLCV, bar/event ID
STRATEGY_DECISION: decision_id, strategy_id, proposed action, parameters
RISK_DECISION: decision_id, allowed/rejected, reason, relevant limits
ORDER_INTENT: intent_id, decision_id, symbol, side, quantity, limit_price
ORDER_STATUS: intent_id, broker_order_id, status, cumulative_filled_qty
FILL: fill_id, order_id, incremental_fill_qty, cumulative_filled_qty, price, fees, timestamp
LEDGER_MUTATION: event_id, lot_id, mutation type, quantity delta, cash delta
RECONCILIATION: correlation ID, local state summary, broker state summary, resolution
RISK_HALT: halt reason, previous state, new state
STARTUP/SHUTDOWN: deployment ID, runtime state, reconciliation result
```

`incremental_fill_qty` must be derived from cumulative broker quantity and must not be confused with requested quantity. Payloads must be JSON-serializable and versioned.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. This task records events; it does not generate the idempotency mechanism that produces their IDs (Task 4.10) or the ledger persistence they get correlated against (Task 7.3). If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Shared event-ID contract**
The event ID used in this schema must be the same identifier Task 4.10 defines for idempotency and Task 7.4 checks before resubmitting an order — one scheme across all three, not three independent ones (see Task 4.10's Idempotency scope contract). If this task lands first, define the ID scheme here and have 4.10/7.4 adopt it instead.

**Acceptance criteria**
- A test run can reconstruct the causal chain from market decision → risk decision → order → fill → ledger mutation.
- Duplicate events do not create duplicate side effects.
- Audit schema versions are explicit and forward-compatible.
- Event IDs in this schema are the same IDs used by Task 4.10's idempotency check, verifiable by cross-referencing a single event across both.

### Task 7.15 — Enforce no-loss sell economics at the exit boundary

**Addresses:** Non-negotiable trading invariant
**Preconditions:** Tasks 2.2, 4.1, 7.2, 7.10
**Files touched:** `src/ledger.py`, OMS/exit decision path, cost model integration

**Context**
The system's primary strategy invariant is that it never intentionally sells at a loss. This cannot be left as a strategy convention because transaction costs, slippage, partial fills, reconnects, risk halts, and live execution can otherwise bypass it. The invariant must be enforced at the final exit boundary.

**Implementation**
1. Track acquisition cost basis at lot/partial-lot granularity.
2. Given a proposed sell quantity and quoted price, calculate the effective sell price and all sell costs using the configured `TransactionCostModel`.
3. Calculate `net_sell_proceeds` and compare it with the allocated cost basis for exactly the proposed filled quantity.
4. If `net_sell_proceeds < allocated_cost_basis`, reject the sell intent before submission.
5. For partial fills, recompute the realized economics using the actual filled quantity and price; never mark the remaining lot as realized.
6. Risk halts, shutdown, reconciliation, and retry logic must call this same guard rather than bypassing it.

### Canonical no-loss API

Implement one canonical guard at the exit boundary. The concrete module may differ if the repository already has a suitable location, but the public behavior must be equivalent to:

```python
@dataclass(frozen=True)
class SellEconomics:
    quantity: float
    allocated_cost_basis: float
    sell_costs: float
    net_sell_proceeds: float
    realized_pnl: float

def validate_sell(
    lot: InventoryLot,
    quantity: float,
    quoted_price: float,
    cost_model: TransactionCostModel,
) -> SellEconomics:
    ...
```

If `net_sell_proceeds < allocated_cost_basis - MONEY_EPSILON`, the function rejects the sell with the canonical domain exception from Task 4.8. All exit paths call this guard; they do not duplicate the formula.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Single-guard contract**
Use exactly the `net_sell_proceeds` / `allocated_cost_basis` formulas from this file's Canonical money/accounting formulas section (identical to overview §2.1) — do not derive a second, slightly different formula here. This is the **one** place the no-loss check is evaluated; Task 1.5's fill validation and Task 7.2's partial-fill accounting feed this guard their confirmed quantities and prices, they do not each re-implement their own version of the loss check. If Task 1.5 or Task 7.2 currently contains an inline loss check, fold it into a call to this guard rather than leaving two independent implementations that could silently drift apart.

**Acceptance criteria**
- A sell at the nominal target passes only when net proceeds cover allocated cost basis.
- A sell whose nominal target is profitable but becomes a loss after modeled commission/slippage is rejected.
- A partial fill that remains profitable closes only the filled portion.
- No live circuit-breaker, shutdown, or reconciliation path can create an intentional loss-making sell.
- Only one implementation of the no-loss comparison exists in the codebase; Tasks 1.5 and 7.2 call it rather than duplicating it.

### Task 7.9 — Confirm whether macro/seasonality signals are required (Discovery Gate)

*Placed here, after 7.15, rather than immediately after 7.8: this task predates the v4 addition of 7.10-7.15 and is intentionally last in reading order because of its speculative/optional status below — not a sequencing error. Numerically it depends only on Task 4.1 and can be picked up any time after that, independent of 7.10-7.15.*

**Addresses:** L10 (Low / unconfirmed)
**Preconditions:** Task 4.1. **Discovery only. Do not implement production ingestion or MarketContext population in this task.**
**Files to inspect:** `src/market_context.py`, `src/data_validation.py`, strategy implementations. **Files to modify:** none required; documentation/contract notes only unless a follow-up implementation task is created.

**Context**
External feedback on this document asserted that FinBERT-based NLP sentiment scoring and Federal Reserve/CPI macro-event awareness were previously integrated into this system's Bayesian sizing. That doesn't match anything previously established: `BayesianDualScaleSizing` fuses "macro" (long-window) and "micro" (short-window) Bayesian posteriors over price/volatility data — a purely technical distinction about lookback length, not macroeconomic events. This task exists so the hooks are ready if the need is real, but it should be confirmed against actual source (or against what's actually intended) before building it out — otherwise this is speculative scope with no confirmed consumer.

**Discovery procedure**
1. Inspect the repository and architecture for a real consumer of `time_of_day_flag`, `is_macro_event_day`, or `macro_surprise_factor`. `time_of_day_flag`, `is_macro_event_day`, `macro_surprise_factor` have already been added to `MarketContext` (overview §5.1) with safe defaults (`0`, `False`, `0.0`) — confirm they're actually consumed by a real strategy before populating them with real data; unused optional fields are harmless, but a whole ingestion pipeline (step 2) built for nothing isn't.
2. If no confirmed consumer exists, record that outcome and stop. Do not add an ingestion dependency merely to make the task appear implemented.
3. If a real consumer exists, document the exact consuming strategy, required fields, source dataset, timestamp join semantics, default behavior, and a proposed follow-up implementation task.
4. The only production change permitted in this discovery task is documentation/contract clarification; no speculative data pipeline may be added.

### Agent implementation contract

Before coding, inspect the repository implementation named in **Files touched** and verify the current signatures rather than assuming them. Do not broaden the task into adjacent architectural work.

**Required implementation evidence**
- Identify the exact public API/state being changed and preserve unrelated callers.
- State explicitly which objects are mutated and which component owns that state.
- Add or update focused tests for success, rejection/error, and boundary behavior; use deterministic fixtures/seeds where applicable.
- For money/order changes, verify accounting is based on confirmed fills and preserves the no-loss invariant.
- For persistence/reconnect changes, test restart, duplicate-event, and mismatch behavior.
- For parallel/search changes, verify deterministic equivalence with the sequential/default path.
- Do not mark the task complete until every acceptance criterion below is executable as a test or a documented verification step.

**Non-goals**
Do not implement behavior belonging to another task merely because it is convenient while touching the same file. If a prerequisite is missing, stop at the documented boundary and report the dependency rather than inventing an incompatible substitute.

**Acceptance criteria**
- A repository/source review explicitly identifies whether a real strategy consumes these fields.
- If no consumer is found, the task is marked **Not required / deferred** with evidence and no speculative implementation.
- If a consumer is found, a follow-up implementation task is defined with exact inputs/outputs, timestamp-join semantics, data source, defaults, and tests.

---

## Specification-freeze requirements

Before an implementation task is considered ready for handoff:

1. Any repository-specific uncertainty is explicitly labeled **repository-adaptive** and has a source-inspection procedure.
2. No task uses “optional”, “choose”, or “e.g.” for behavior that changes an externally observable contract.
3. Every task has executable acceptance criteria and exact verification commands, or explicitly states why verification is documentation-only.
4. Shared interfaces are implemented exactly as defined in `architecture_overview_v6.md`; compatibility adapters are preferred over breaking changes to existing callers.
5. Any public-contract discrepancy discovered during implementation is reported before code is broadened beyond task scope.
6. Canonical no-loss, fill-delta, event-ID, persistence, reconciliation, UTC, precision, and determinism policies are not reimplemented differently by individual tasks.
7. Live implementation remains gated by startup reconciliation and Task 7.7 promotion criteria; successful tests alone do not authorize live capital.

## Document history

- **v1-v3** — Original 35-task implementation specification paired with the architecture overview.
- **v4** — Strengthened for independent AI-agent execution: added task-independence contract, no-loss invariant, canonical accounting/sequencing rules, compact completion contract on every task, explicit edge-case contracts for critical tasks, and 11 additional hardening tasks (4.8-4.10, 6.3-6.4, 7.10-7.15).
- **v6** — Added mandatory repository-inspection/completion evidence, canonical time/numeric/data policies, exact SearchStrategy compatibility, cumulative-fill semantics, SQLite persistence, canonical event IDs, reconciliation precedence, walk-forward/Monte Carlo contracts, BacktestConfig/artifact hashing/secret rules, shared live/backtest decision-cycle requirements, paper-promotion criteria, shutdown sequencing, audit payload schemas, an explicit no-loss API, and converted Task 7.9 into a discovery-only gate.
- **v6.1** — Final specification-freeze pass: classified source-specific uncertainty as repository-adaptive, made live tick rejection deterministic, standardized the canonical retry/backoff policy and tests, removed externally observable optional configuration behavior, and added final handoff/freeze requirements.
- **v5** — Closed gaps found in an independence review: Task 4.1 now returns the canonical `SimulationResult` (overview §5.6) instead of an undefined forward reference, and Task 4.6 extends it rather than re-originating it; backfilled the Agent implementation contract / Non-goals section that v4's "every task" claim missed on 4.1, 4.8-4.10, 6.3-6.4, 7.2, and 7.10-7.15, adding concrete edge-case contracts to 7.10-7.15 specifically (state-transition table, unambiguous-vs-ambiguous reconciliation rule, bounded shutdown window, backoff parameters, shared event-ID scheme, single no-loss guard); made Task 7.2's `close_lot()` signature a flagged, backward-compatible proposal instead of an unconfirmed breaking change, and reconciled Task 7.3's description of it; fixed Task 6.2's precondition line against its own Phase-7 test requirements; gave Task 2.3 a concrete default intrabar-ambiguity rule instead of an unspecified one; named all four sizing-strategy classes explicitly in Tasks 1.4 and 4.1; promoted `SearchStrategy` to a canonical §5.7 contract; and closed the missing `intraday_validation.py` module-layout entry.
