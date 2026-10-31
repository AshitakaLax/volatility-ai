# Buy × Sell Composition: Mix-and-Match Trading Algorithms, with Partial-Lot Selling

Oct 31, 2026 · Plan, not yet implemented

## Goal

Choose a **buy algorithm** (when to buy, how much) and a **sell algorithm**
(when to sell, how much) independently, run every pairing through the same
backtest, and answer three questions with numbers rather than intuition:

1. Which buy algorithm is best **on average across sell algorithms** (its main effect)?
2. Which sell algorithm is best **on average across buy algorithms**?
3. **Do they interact?** That is, is the best sell algorithm different depending on the buy algorithm?
   If they do, "the optimal buy" and "the optimal sell" do not exist separately and the
   answer is the best *pair*. The plan measures this rather than assuming either way.

Selling **part of a lot** (scale-out tranches, sell half and trail the rest)
is in scope and is the largest engine change here.

## Where the code stands today (verified by reading, Oct 31 2026)

| Piece | Today | What that means for this plan |
| --- | --- | --- |
| Strategy port | `engine/core/sizing.py` `SizingStrategy`: buy hooks (`_grid_trigger_level`, `calculate_trade_value`, `record_tick`) **and** sell hooks (`adjust_profit_target`, `lots_to_liquidate`, `wants_lot_retargeting`, `retain_lots`) on one class | Buy and sell logic are fused per class. Nothing lets you pair class A's buys with class B's sells |
| Sell hook users | Trailing target (`research/optimization/trailing_target.py`, via `trail_pct` on the HF family, Bayesian, ML regime); target age-decay and fractional regime liquidation (`harvest_sleeve_sizing.py`); regime exit (`ultimate*`, `regime_sleeve_sizing.py`); exposure-target exits (`ultimate_rsp_sizing.py`) | Several sell algorithms already exist but are trapped inside particular buy classes |
| Buy catalogue | `fixed`, `rsi`, `bell_curve`, `bayesian_dual_scale`, `hf_local_reference` (champion), `hf_entry_gated`, `hf_signal_gated`, ~51 `rk*` library ids (`LibrarySizing` + one `signal_library` component), 15 ML ids, the Ultimate family | Large and already selectable by `strategy_id` |
| Sell selection | The only sell knobs in config are `grid.profit_targets`, `trail_pct`, and per-class parameters | No way to name a sell algorithm |
| Ledger partial close | `engine/core/ledger.py` `close_lot(lot, sell_qty=...)` reduces `lot.shares`, keeps `buy_price` and target, and removes the lot at `<= SHARE_EPSILON` | **Already works**, and the live loop uses it for partial *fills* (`live_trading_loop.py` `_apply_sell_fill`) |
| No-loss guard on partials | `no_loss_guard.compute_sell_economics` allocates basis as `buy_price * quantity` | **Already correct** for any quantity. No guard change needed |
| Backtest sell sites | `optimization_controller._simulate_single` and `intraday_validation.simulate_single_intraday` both call `oms.execute_sell(lot.symbol, lot.shares, …)` and then `ledger.close_lot(lot)` (full) | Both must learn to sell a quantity |
| Live sell sites | `_harvest` submits `lot.shares` at `lot.target_sell_price`; `_submit_exit` sums whole lots into one order and allocates the fill oldest-first | Both must accept a quantity per lot |
| Persistence | `ledger_lots` has `shares` but **no original size**; `load_ledger` asserts `target_sell_price == buy_price*(1+profit_target)` | A restart cannot tell "half sold" from "bought small". Needs an `original_shares` column |
| Per-lot metrics | `performance_analyzer.py:117-124` takes a lot's **last** sell `bar_index` as its close; `server/fills.py:102-103` marks a lot closed if it has **any** sell | Both are wrong once a lot can have several sells and still be open |
| Sweep params | `config.expand_strategy_params` sweeps top-level list values only | Nested `buy:`/`sell:` variants need expansion |
| Hash / warehouse | `parameter_hash` hashes `strategy_params` canonically; `queries.py` already reads `parameters_json -> '$.profit_target'` | Nested params hash correctly with no change; buy/sell ids are queryable by JSON path |
| Overfitting tools | `research/optimization/overfitting.py` (deflated Sharpe, PBO/CSCV), `walk_forward.py`, `purged_cv.py` | Already there for the selection-bias problem a big matrix creates |

## Design

### 1. Split the port into two roles, without breaking the old one

Add to `engine/core/` (layer 0, no research imports):

```python
# engine/core/exit_policy.py
@dataclass(frozen=True)
class ExitOrder:
    lot: Lot  # must be a lot from this bar's open book
    quantity: float  # 0 < quantity <= lot.shares
    reason: SellReason  # PROFIT_TARGET (cannot lose) or SIGNAL_EXIT (may lose)
    # Price comes from the reason: PROFIT_TARGET fills at the lot's target or better
    # (the existing harvest path), SIGNAL_EXIT at the bar's price (the existing exit path)
```

and **one new optional hook on `SizingStrategy`**, with a default that
reproduces today exactly:

```python
def harvest_quantity(self, lot, context) -> float:
    """Shares to sell when `lot` is marketable at its target. Default: all of them."""
    return lot.shares
```

plus widening `lots_to_liquidate` to accept `ExitOrder`s as well as bare lots.
A bare lot still means "all shares, SIGNAL_EXIT". That keeps every existing strategy's return value valid.

Why a quantity hook and not a new "tranche lot" type: the ledger, guard,
persistence and live fill accounting already handle a lot whose `shares`
shrinks. Splitting a buy into child lots would give one broker order
several ledger keys and touch the reconciliation path. Shrinking a lot touches
none of that.

The engine still knows **no concrete policy**. It only gets a quantity and a reason.

### 2. Buy and sell policies as separate adapters in `research/`

New package `research/composition/`:

- `entry_policy.py`: the `EntryPolicy` protocol: `record_tick`, `trigger_level(context, last_buy_price, step)`,
  `trade_value(context)`, `use_prior_bar_trigger`, optional `warm_up`, `live_history_sessions`, `diagnostics`.
- `exit_policy.py`: the `ExitPolicy` protocol: `record_tick`, `on_lot_seen(lot, context) -> target | None`,
  `adjust_target(lot, context) -> target | None`, `harvest_quantity(lot, context) -> float`,
  `exit_orders(open_lots, context) -> list[ExitOrder]`, `wants_lot_retargeting`, `retain_lots`,
  `resume(open_lots)`, `can_realize_loss: bool` (class attribute).
- `composed_strategy.py`: `ComposedStrategy(SizingStrategy)` takes one of each and delegates.
  `record_tick` calls **both** (entry first, then exit, in a fixed, tested order).
  `wants_lot_retargeting` is the exit policy's answer, so the 63%-of-runtime early-out still works.
- `entry_registry.py` / `exit_registry.py`: id → class, the same pattern as `strategy_registry.py`.
- `strategy_registry.py` gains one id, `composed`. `SIGNAL_EXIT_STRATEGIES` handling becomes
  "`composed` whose exit policy has `can_realize_loss`".

Both policies receive the same `MarketContext`. Neither sees the other's state.
That isolation is what makes the pairing results comparable.

### 3. Config shape

```yaml
strategy:
  strategy_id: composed
  strategy_params:
    buy:
      id: hf_local_reference
      params: {bars_per_day: 387, per_lot_pct: 0.0002, lookback_days: 0.02, ...}
    sell:
      id: scale_out
      params: {rungs: [[0.5, 0.01], [0.5, 0.03]], min_tranche_notional: 5.0}
grid:
  steps: [0.01]
  profit_targets: [0.02]   # the BASE target every lot is registered with; a sell policy may move it
```

Sweeps: `buy` and `sell` may each be a **list** of `{id, params}` variants, and each
`params` value may itself be a list. `expand_strategy_params` gets a nested branch:
expand each side's params, then take the cartesian product of buy variants × sell variants.
The flat behaviour stays byte-identical for every existing config (regression test).

`grid.profit_targets` stays required and keeps its meaning (the target at
registration). Live keeps `live.profit_target` required, per the root rule.

### 4. Partial-lot selling: how a tranche ladder actually runs

Take the ladder "sell 50% at +1%, the rest at +3%". The rung is **derived from state the
ledger already persists**, never from policy memory, so a restart reconstructs it:

```
sold_fraction = 1 - lot.shares / lot.original_shares
rung          = first rung whose cumulative fraction > sold_fraction
```

Per bar, in the existing canonical order:

1. `record_tick`: both policies.
2. `adjust_open_lot_targets`: the exit policy returns the current rung's target. On a lot's first bar
   that sets rung 1. After a partial sale it **raises** the target to the next rung.
   `Lot.retarget` already allows any positive target, and the ledger's bound only needs to hear about
   *lowered* targets, which it already does.
3. `collect_liquidations`: `ExitOrder`s, still gated by `allow_signal_exit` for SIGNAL_EXIT.
4. Marketable lots sell `harvest_quantity(lot)` shares, not `lot.shares`.
5. The guard runs on that quantity. The ledger calls `close_lot(lot, sell_qty=q)`.

A lot sold in part on bar *t* is not offered again on bar *t*, because the exit list is
computed once per bar. On bar *t+1*, step 2 moves it to the next rung before step 4 looks.
The live loop gets the same result because in-flight lots are skipped and retargeting
precedes the marketable check. **One ordering, three sites**, which is what
`decision_cycle.py` exists to guarantee.

Guards specific to partials:

- `min_tranche_notional` and the broker's minimum: a tranche below it sells the whole remainder instead.
  The champion's lots are about $20 (`per_lot_pct: 0.0002` on $100k), so a 50% tranche of a 0.25-share lot is
  roughly $10. That is fine for Alpaca fractional shares, but **unknown for the Fidelity route** (an open question below).
- Quantities are floored with the live loop's existing `_floor_shares` (nine decimals). The backtest uses the same
  function so the two cannot round differently.
- `commission_per_trade` is charged per tranche. That is correct, and is the main way laddering can lose to
  whole-lot exits under a per-trade cost model. The matrix must run under the realistic cost model, not `zero`.

### 5. The two sell tracks

A sell policy either **cannot** lose money (every sale is PROFIT_TARGET; the guard
rejects anything below basis) or **may** (it emits SIGNAL_EXIT, requires
`execution.allow_signal_exit`, and is refused live without it by `check_live_support`).
The matrix runs these as **separate tracks**, reported separately. A loss-capable
policy is a different risk product, and mixing the two rankings would hide that.

## Catalogues

### Buy policies (phase 2 extracts these; behaviour pinned identical)

| Entry id | Source | Extraction difficulty |
| --- | --- | --- |
| `fixed`, `rsi`, `bell_curve` | `size_calculators.py` | Trivial: no sell logic |
| `hf_local_reference` (champion) | `high_frequency_sizing.py` | Easy: `trail_pct` moves to the `trailing` exit policy |
| `hf_entry_gated`, `hf_signal_gated`, all `rk*` library ids | `gated_local_reference_sizing.py`, `signal_gated_sizing.py`, `library_sizing.py` | Easy: their docstrings state they override no exit hook beyond the parent |
| `bayesian_dual_scale` | `bayesian_sizing_calculators.py` | Medium: `target_return` must equal the exit target (the existing guard). This becomes a cross-check between policies |
| `ml_reachability_*`, `ml_regime_*` | `research/ml/` | Medium: same `target_return`/ticker cross-checks; `ml_regime_*` carries `trail_pct` |
| `harvest_sleeve` buys | `harvest_sleeve_sizing.py` | Medium: inventory decay is a buy behaviour; target decay and fractional liquidation move to sell policies |
| `ultimate`, `ultimate_rsp`, `ultimate_ursp`, regime sleeve | | **Hard, and possibly wrong to split.** Ultimate tags reversal lots by their *target* and its exit only makes sense with its own regime buys. These stay **bundles**: one cell each in the matrix, labelled as such, until a separate decision says otherwise |

### Sell policies

| Exit id | Track | Partial? | Source / note |
| --- | --- | --- | --- |
| `fixed_target` | no-loss | no | Today's default. With the champion it must equal the champion exactly |
| `trailing` | no-loss | no | Wraps `TrailingTargetPolicy` (`trail_pct`, `min_profit_target`) as is |
| `age_decay` | no-loss | no | Lifted from `harvest_sleeve_sizing`'s `target_decay_*` |
| `vol_scaled_target` | no-loss | no | **New**: target = k × trailing realized vol at entry, floored; reuses `volatility_estimators.py` |
| `inventory_pressure` | no-loss | no | **New**: lowers the targets of the oldest lots as open-lot count or committed capital grows (the "inventory is the quantity to control" finding in `correction-strategies.md`) |
| `scale_out` | no-loss | **yes** | **New**: N rungs of (fraction, target) |
| `scale_out_trail` | no-loss | **yes** | **New**: first tranche at a fixed target, remainder trails from the peak |
| `signal_take_profit` | no-loss | yes (optional fraction) | **New**: when a `signal_library` component flips bearish, sell lots already above `basis*(1+floor)` at market. A sale below basis is impossible because the reason is PROFIT_TARGET and the guard rejects it |
| `regime_exit` | loss-capable | no | Lifted from `regime_sleeve_sizing.lots_to_liquidate` |
| `regime_exit_partial` | loss-capable | **yes** | **New**: sells `fraction` of every lot's *shares* on the flip, unlike `harvest_sleeve`'s fraction of *lots* (highest cost first). Both stay available so they can be compared |

## Phases

Each phase lands as its own PR, keeps `cli.py test` green, and changes **no
recorded result** unless the phase says so.

### Phase 0: Lock today's behaviour down
- Add a regression fixture: blotters and summary rows for the champion, `hf_entry_gated`, `harvest_sleeve`
  and `ultimate` under `close` and `intrabar`, alongside `research/tests/test_regression_baseline.py`.
- **Done when** the fixture is committed and the suite asserts identity against it.

### Phase 1: Partial sells in the engine
- `engine/core/sizing.py`: `harvest_quantity` default; `ExitOrder` in a new `engine/core/exit_policy.py`;
  `lots_to_liquidate` accepts `ExitOrder | Lot`.
- `engine/trading/decision_cycle.py`: `collect_liquidations` normalises to `ExitOrder`, checks
  `0 < quantity <= lot.shares` against this bar's book, and dedupes by lot (one exit per lot per bar).
  A new `harvest_orders(strategy, marketable, context)` applies `harvest_quantity` and the minimum-tranche fallback.
- `research/optimization/optimization_controller.py` and `intraday_validation.py`: sell `order.quantity` and call
  `close_lot(lot, sell_qty=filled_qty)`; the blotter row records the quantity and a `remaining_shares` column.
- `engine/trading/live_trading_loop.py`: `_harvest` submits `harvest_quantity`; `_submit_exit` sums each order's
  quantity and `_apply_exit_fill` allocates up to each lot's requested quantity rather than its whole position.
- `engine/core/persistence.py`: `original_shares` column, `schema_version` bump, migration that sets
  `original_shares = shares` for existing rows, and `load_ledger` asserts `0 < shares <= original_shares`.
  `Lot` gains `original_shares` (set in `register_buy`, never mutated).
- Metrics: `performance_analyzer.py` holding time counts a lot as closed only when its remaining shares reach 0;
  `server/fills.py` "closed" means fully sold. Add `partial_sells` and `avg_tranches_per_lot` to the summary row.
- Contract: if the blotter or fills payload gains `remaining_shares`, update `server/contract.py` **and**
  `web/src/types/backtest.ts` together.
- **Tests**: the regression fixture is unchanged; a test double that sells 50% then 50% gives two guard calls,
  two blotter rows, one closed lot and the correct cash, under both fill models and in live with a fake broker;
  a persistence round-trip of a half-sold lot; partial **fills** of a partial **order** (the order's quantity, not the lot's);
  the no-loss scan test still finds one implementation.
- **Done when** all of that passes and Phase 0's fixture is identical.

### Phase 2: Composition layer
- `research/composition/` as in Design §2, with `fixed_target` and `trailing` exits and entry adapters for
  `fixed`, `hf_local_reference`, `hf_entry_gated`, `LibrarySizing`.
- `config.expand_strategy_params` nested expansion; `param_schema.describe_params` learns to describe
  `composed` as two nested schemas (needed by the backtest form and `live_algorithm` validation).
- `live_algorithm.check_live_support`: `composed` with a loss-capable exit requires `allow_signal_exit`; a
  warm-up need on either side requires `live_history_sessions` on that side; per-lot exit state requires `resume`.
- **Pinned identities** (the repo's existing discipline): `composed(hf_local_reference, fixed_target)` ≡
  `hf_local_reference`; `composed(hf_local_reference, trailing(p))` ≡ `hf_local_reference(trail_pct=p)`;
  `composed(rkNN, fixed_target)` ≡ `rkNN`. These are identical blotters, not "close".
- **Done when** the identities pass for both fill models and a `composed` config runs through `cli.py backtest`.

### Phase 3: Sell-policy library
- Implement the "New" rows of the sell table, each defaulting to inert where it has an off switch.
- One unit test per policy for its rule, plus three shared property tests run against **every** registered exit
  policy: a no-loss-track policy never produces a realized loss under `enforce_no_loss`; a policy never asks for
  more shares than a lot holds; `resume(open_lots)` after a simulated restart gives the same next decision as an
  uninterrupted run.
- **Done when** every policy is registered, documented in `docs/algorithms/` through
  `tools/build_algorithm_ledger.py`, and marked UNMEASURED.

### Phase 4: Extract the remaining buy policies
- Bayesian, ML, harvest-sleeve buys, each with a pinned identity against its original id combined with the exit
  policy that reproduces its old sells.
- Cross-policy checks move into `ComposedStrategy.__init__`: Bayesian/ML `target_return` must match the exit
  policy's *first* target, or the existing `allow_target_return_mismatch` escape hatch applies.
- The Ultimate family stays a bundle (see Open questions).

### Phase 5: The matrix runner
- `research/composition/matrix.py`: takes buy variants × sell variants, builds the `composed` param grid, and
  calls **`OptimizationController.run_sweep`**, not `run_hf_sweep.py`, which drops `allow_signal_exit` and cash yield.
  It writes through `DuckDBResultSink`.
- **Equal tuning budget per cell.** A policy with a 50-point grid would beat one with 2 points by search luck alone.
  Each cell gets the same number of trials (Bayesian search inside the cell, fixed seed), and the trial count goes
  into the deflated Sharpe.
- CLI: `cli.py matrix --config config/matrix_<name>.yaml`. It shards across machines through the existing
  `cli.py shard` path.
- Warehouse: a `composition_cells` view over `parameters_json -> '$.buy.id'` / `'$.sell.id'`. No table change.
- **Done when** a 3 × 3 smoke matrix on a one-year TQQQ slice completes, dedups on re-run (hash), and the view returns 9 cells.

### Phase 6: Analysis that answers the question
For each track, metric (Total Return %, Calmar; **not** Capital Velocity Index, which saturates) and dataset:

1. **Cell score** = the median over the cell's trials of the metric, plus the best trial reported alongside, never instead.
   The median rewards a policy that is good across its parameters, not one lucky point.
2. **Two-way decomposition** of the cell-score matrix: `score[b,s] = μ + α_b + β_s + γ_bs`.
   - `α_b`: buy main effect. Rank buys by it.
   - `β_s`: sell main effect. Rank sells by it.
   - `γ_bs`: interaction. Report the share of variance it explains, and check significance with a permutation test
     over per-year returns (shuffle sell labels within each buy row).
3. **Decision rule**:
   - If interaction is small (say under 10% of explained variance and not significant), the best buy is
     argmax `α` and the best sell is argmax `β`, and they can be chosen independently.
   - Otherwise, report the best **pair** and, for each buy, its best sell.
4. **Overfitting control**: PBO by CSCV across all cells (`overfitting.probability_of_backtest_overfitting`, with
   per-month returns as the T × N matrix), deflated Sharpe for each finalist with N = total trials across the whole
   matrix, then walk-forward (`walk_forward.py`) and purged CV on the top 3 pairs only.
5. **Robustness**: rerun the top 5 pairs on at least one more symbol (QQQ or SOXL) and on the 2022 correction alone.
   A pair that wins only on full-period TQQQ is reported as such.
6. **Diagnostics per cell**: open lots and committed capital at the end (stranded inventory, the problem
   `trailing_target.py` was written for), realized versus unrealized P&L, partial-sell count, average tranches per lot, and turnover.

Output: `docs/research/buy-sell-matrix-results.md` with heatmaps (buy × sell, per track) and the decomposition table.
A UI heatmap on the Warehouse tab is optional and a separate PR, because the contract is hand-mirrored.

### Phase 7: Promotion
The winning pair is promoted the way any strategy is, with nothing special-cased: a `config/` file with `live:`
(`strategy_id: composed`), paper trial, `engine/promotion.py` gate. Partial sells add one paper-trial check:
every partially sold lot's broker position matches `shares` after reconciliation.

## Risks

| Risk | Mitigation |
| --- | --- |
| Partial fills of a partial order double-count against the lot | `sell_qty` is already incremental (`fill_accounting.py`); add the test in Phase 1 |
| Raising a target after a partial sale leaves a resting order at the old target | In-flight lots are already skipped by `adjust_open_lot_targets`; the policy only sees the lot once the order settles |
| A restart loses the rung | The rung is derived from `shares / original_shares`, which is persisted |
| Tiny tranches are rejected by the broker or eaten by commission | `min_tranche_notional` fallback to the whole remainder; the matrix runs with the real cost model |
| The matrix is large enough to find noise | Equal per-cell budget, median cell score, PBO, deflated Sharpe with the full trial count, walk-forward on finalists |
| Runtime: the champion already spends most of a run walking open lots | `wants_lot_retargeting` early-out is preserved; a ladder policy returns True only on bars with a new lot or a partial sale, the pattern `harvest_sleeve` already uses |
| A composed strategy differs subtly from the original class | Phase 2 and 4 identity tests on identical blotters |

## Open questions (owner decisions)

1. **Fractional shares on the Fidelity route.** Partial selling of the champion's ~$20 lots needs fractional sell orders.
   If the Fidelity gateway cannot place them, the ladder is backtest and Alpaca only, or lots must be larger. This needs checking in `fidelity_gateway/`.
2. **Should the Ultimate family be decomposed?** Its exit is designed around its own regime buys. The plan keeps it as a bundle; splitting it would create unresearched variants.
3. **Is the loss-capable track wanted at all** beyond the existing regime exits? It is kept separate so it can simply be skipped.
4. **Which datasets count** for "best": full-period TQQQ only, or TQQQ plus a second symbol and the 2022 correction (as recommended)?

## Effort (rough)

Phase 1 is the largest and riskiest, since it touches all three sell sites, persistence and metrics.
Phases 2 to 4 are mostly adapter code plus identity tests. Phase 5 is plumbing over existing sweep machinery.
Phase 6's compute is unknown until one cell is timed: run a single cell first and size the full matrix from that.
