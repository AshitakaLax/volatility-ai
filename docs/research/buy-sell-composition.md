# Buy × Sell Composition: Mix-and-Match Trading Algorithms, with Partial-Lot Selling

Oct 31, 2026 · Plan, not yet implemented · Revision 2 (owner's decisions recorded; web pipeline added)

## Goal

Choose a **buy algorithm** (when to buy, how much) and a **sell algorithm**
(when to sell, how much) independently, run every pairing through the same
backtest, and answer three questions with numbers rather than intuition:

1. Which buy algorithm is best **on average across sell algorithms** (its main effect)?
2. Which sell algorithm is best **on average across buy algorithms**?
3. **Do they interact?** That is, is the best sell algorithm different depending on the buy algorithm?
   If they do, "the optimal buy" and "the optimal sell" do not exist separately and the
   answer is the best *pair*. The plan measures this rather than assuming either way.

Then **take any pairing from the web**: build it on the backtest form, validate
it by backtest, keep it as a candidate, paper-trial it, promote it, and switch a
live deployment to it, through the same approval pipeline single strategies use today.

Selling **part of a lot** (scale-out tranches, sell half and trail the rest) is in
scope and is the largest engine change here.

## Owner's decisions (Oct 31, 2026)

| Question | Decision | Where it lands |
| --- | --- | --- |
| Fractional shares at Fidelity | Fidelity sells fractional shares during regular market hours, whole shares only in pre- and post-market | Design §4 (session-aware quantity rule), Phase 1b |
| Decompose the Ultimate family? | **Yes**: the goal is to find which component is best | Design §6 (lot tags), catalogues, Phase 4 |
| Run the loss-capable sell track? | **Yes**: it shows how sells behave in different market conditions | Design §5, Phase 6 (regime breakdown) |
| Which data counts | **Any symbol, long history**, with each year's effect visible (2022 especially) | Phase 5 (symbol universe), Phase 6 (year analysis) |
| The web approval pipeline | Must support **any** algorithm, composites included: mix a buy and a sell on the web, backtest, then promote to live | Design §7, Phase 7 |
| CI test for profiles with no committed home | Count a registered deployment whose config is absent, checked against its `.example` | **Done** in this PR: `research/tests/test_live_profiles.py` |

## Where the code stands today (verified by reading, Oct 31 2026)

### Trading kernel

| Piece | Today | What that means for this plan |
| --- | --- | --- |
| Strategy port | `engine/core/sizing.py` `SizingStrategy`: buy hooks (`_grid_trigger_level`, `calculate_trade_value`, `record_tick`) **and** sell hooks (`adjust_profit_target`, `lots_to_liquidate`, `wants_lot_retargeting`, `retain_lots`) on one class | Buy and sell logic are fused per class. Nothing lets you pair class A's buys with class B's sells |
| Sell hook users | Trailing target (`research/optimization/trailing_target.py`, via `trail_pct` on the HF family, Bayesian, ML regime); target age-decay and fractional regime liquidation (`harvest_sleeve_sizing.py`); regime exit and reversal target (`ultimate_sizing.py`, `regime_sleeve_sizing.py`); exposure-target exits (`ultimate_rsp_sizing.py`, `ultimate_ursp_sizing.py`, `catalog_exposure_sizing.py`) | Several sell algorithms already exist but are trapped inside particular buy classes |
| Buy catalogue | `fixed`, `rsi`, `bell_curve`, `bayesian_dual_scale`, `hf_local_reference` (champion), `hf_entry_gated`, `hf_signal_gated`, ~51 `rk*` library ids (`LibrarySizing` + one `signal_library` component), 15 ML ids, the Ultimate family, `catalog_exposure` | Large and already selectable by `strategy_id` |
| Ledger partial close | `engine/core/ledger.py` `close_lot(lot, sell_qty=...)` reduces `lot.shares`, keeps `buy_price` and target, and removes the lot at `<= SHARE_EPSILON` | **Already works**, and the live loop uses it for partial *fills* (`live_trading_loop.py` `_apply_sell_fill`) |
| No-loss guard on partials | `no_loss_guard.compute_sell_economics` allocates basis as `buy_price * quantity` | **Already correct** for any quantity. No guard change needed |
| Backtest sell sites | `optimization_controller._simulate_single` and `intraday_validation.simulate_single_intraday` both call `oms.execute_sell(lot.symbol, lot.shares, …)` and then `ledger.close_lot(lot)` (full) | Both must learn to sell a quantity |
| Live sell sites | `_harvest` submits `lot.shares` at `lot.target_sell_price`; `_submit_exit` sums whole lots into one order and allocates the fill oldest-first | Both must accept a quantity per lot |
| Legacy lots on a switch | `live_trading_loop` keeps a `_legacy` set and passes it in `skip_order_ids`, so a new algorithm never retargets or liquidates the old one's lots | A switch to a composite leaves old lots alone, as it should. Partial sells must skip them too (they sell whole, at their own targets) |
| Whole shares at Fidelity | `fidelity_gateway/broker.py` sets `whole_shares = True` unconditionally ("fractional sizing is not modelled"); `live_trading_loop` rounds a buy up to one whole share or refuses it | Fidelity's fractional trading in regular hours is not used yet. Phase 1b makes it session-dependent |
| Persistence | `ledger_lots` has `shares` but **no original size** and **no tag**; `load_ledger` asserts `target_sell_price == buy_price*(1+profit_target)` | A restart cannot tell "half sold" from "bought small", and Ultimate tells reversal lots from calm ones **by their target** (`check_live_support`). Needs `original_shares` and `entry_tag` columns |
| Per-lot metrics | `performance_analyzer.py:117-124` takes a lot's **last** sell `bar_index` as its close; `server/fills.py:102-103` marks a lot closed if it has **any** sell | Both are wrong once a lot can have several sells and still be open |
| Sweep params | `config.expand_strategy_params` sweeps top-level list values only | Nested `buy:`/`sell:` variants need expansion |
| Hash / warehouse | `parameter_hash` hashes `strategy_params` canonically; `queries.py` already reads `parameters_json -> '$.profit_target'` | Nested params hash correctly with no change; buy/sell ids are queryable by JSON path |
| Overfitting tools | `research/optimization/overfitting.py` (deflated Sharpe, PBO/CSCV), `walk_forward.py`, `purged_cv.py`; `research/analysis/analyze_annual.py` (per-year against buy-and-hold) | Already there for the selection-bias problem a big matrix creates, and for the per-year view |

### The web approval pipeline (single strategies today)

```
Backtest form ──run──> cell ──"keep"──> candidate ──trial──> paper deployment
 (ParameterForm)        (history)   POST /api/algorithms/candidates    switch_algorithm command
                                              │
                         evaluate (engine/promotion_record.py, trader's journals)
                         or owner sign-off (typed id, marked manual)
                                              │
                         publish → config/live_profiles/<id>.yaml + promotions/<id>.json
                                              │                    (operator reviews and commits)
                         real-money deployment switches to the profile (typed id, once a day)
```

| Piece | Today | Gap for composites |
| --- | --- | --- |
| Model catalogue | `server/backtest.py` serves `models: {id: {params: Param[], trigger}}` from `param_schema.describe_params`; `ParameterForm.tsx` renders one flat parameter list | No notion of two nested parameter sets, or of policies that are not whole strategies |
| Sweep expansion | `server/backtest.py` `_bisect_params`, `_combination_key`; `config.expand_strategy_params` | Flat keys only |
| Candidate | `server/algorithms.py` `add_candidate` copies the cell's `strategy_id`, `strategy_params`, step and target, and names it `<model>-<ticker>-<run>-<cell>` | Works for nested params as is; the name and label say nothing about which buy and sell |
| Trial deployments | `_wire` offers paper deployments **by symbol only** | A composite with a loss-capable sell needs `execution.allow_signal_exit`, which the page cannot set. The page would offer a deployment that then refuses the switch |
| Live validation | `research/strategies/live_algorithm.py` `AlgorithmControl._parse` checks each param against `describe_params` (flat, at most 64) | A nested `buy`/`sell` object is rejected as an unknown parameter |
| Real money | Only committed profiles; `Profile.promoted()`; typed id; once a day | No change. A composite profile is just a profile whose `strategy_id` is `composed` |

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
  `trade_value(context)`, `use_prior_bar_trigger`, `tag_for_next_lot() -> str | None` (§6), optional `warm_up`,
  `live_history_sessions`, `regular_session_only`, `diagnostics`.
- `exit_policy.py`: the `ExitPolicy` protocol: `record_tick`, `on_lot_seen(lot, context) -> target | None`,
  `adjust_target(lot, context) -> target | None`, `harvest_quantity(lot, context) -> float`,
  `exit_orders(open_lots, context) -> list[ExitOrder]`, `wants_lot_retargeting`, `retain_lots`,
  `resume(open_lots)`, `can_realize_loss: bool` (class attribute), optional `warm_up`, `live_history_sessions`.
- `composed_strategy.py`: `ComposedStrategy(SizingStrategy)` takes one of each and delegates.
  `record_tick` calls **both** (entry first, then exit, in a fixed, tested order).
  `wants_lot_retargeting` is the exit policy's answer, so the 63%-of-runtime early-out still works.
  `warm_up` / `live_history_sessions` answer the larger of the two sides; `regular_session_only` is true if either side's is.
- `entry_registry.py` / `exit_registry.py`: id → class, the same pattern as `strategy_registry.py`, each with
  committed defaults (the role `STRATEGY_DEFAULTS` plays today).
- `strategy_registry.py` gains one id, `composed`. `SIGNAL_EXIT_STRATEGIES` handling becomes
  "`composed` whose exit policy has `can_realize_loss`".

Both policies receive the same `MarketContext`. Apart from the lot tag (§6),
neither sees the other's state. That isolation is what makes the pairing results comparable.

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

**The quantity rule** is one function in `engine/core/` (`sellable_quantity(requested, lot, *, whole_shares,
min_notional, price)`), called by the backtest and live alike, so they cannot round differently:

- **Session-aware share granularity.** Fidelity trades fractional shares in the regular session and whole
  shares only in pre- and post-market (owner, Oct 31). Alpaca: fractional (to nine decimals, the live loop's
  `_floor_shares`). So `whole_shares` comes from the venue **and the session the bar is in**
  (`engine/core/venue_sessions.py` already knows the windows), not from the broker alone.
  - In a whole-share window, a requested tranche is floored to whole shares.
  - If it floors to 0, the tranche **waits** for the regular session, rather than selling the whole lot early.
  - A **fractional remainder** (a lot of 2.4 shares after whole-share tranches) can only leave in the regular
    session. The backtest models that by deferring it to the next regular bar. This also covers every
    fractional lot an extended-hours window holds today.
- `min_tranche_notional` and the broker's minimum: a tranche below it sells the whole remainder instead.
  The champion's lots are about $20 (`per_lot_pct: 0.0002` on $100k), so a 50% tranche is roughly $10.
- `commission_per_trade` is charged per tranche. That is correct, and is the main way laddering can lose to
  whole-lot exits under a per-trade cost model. The matrix must run under the realistic cost model, not `zero`.
- Legacy lots (after a live switch) are never split: they keep selling whole, at their own targets.

### 5. The two sell tracks

A sell policy either **cannot** lose money (every sale is PROFIT_TARGET; the guard
rejects anything below basis) or **may** (it emits SIGNAL_EXIT, requires
`execution.allow_signal_exit`, and is refused live without it by `check_live_support`).
Both tracks run (owner, Oct 31) and are **reported separately**: a loss-capable policy
is a different risk product, and mixing the two rankings would hide that. The loss-capable
track is also where the regime breakdown in Phase 6 is most informative, since its exits
are the ones that react to the market rather than to a price.

### 6. Lot tags: how a decomposed Ultimate still works

Ultimate's sell side treats **reversal lots** (bought in a turbulent regime) differently from calm lots: they get
`reversal_target`, and they are exempt from the calm-lot regime exit. Today it recognises them by tracking which
order ids it saw first in a turbulent bar, and after a restart **by their target** (`check_live_support` refuses
`live.profit_target == reversal_target` for that reason). Split into an entry and an exit, the exit side cannot
see the entry side's regime. So:

- An entry policy may name the lot it is about to open: `tag_for_next_lot() -> str | None` (e.g. `"reversal"`).
- `register_buy` stores it on the lot (`Lot.entry_tag`, a new `ledger_lots.entry_tag` column, null by default).
- An exit policy reads `lot.entry_tag` and may treat tags differently (Ultimate's exit: tagged lots get the
  reversal target and are kept out of the regime exit).

The tag is **persisted**, so a restart no longer relies on a target value, and that `check_live_support` rule can
be retired for `composed`. Tags are free text with an allow-list per entry policy. An exit policy that does not
know a tag ignores it, which is what makes any entry pairable with any exit.

### 7. The web pipeline for composites

The pipeline's stages do not change. Each one learns about `composed`:

1. **Catalogue endpoint.** `server/backtest.py`'s model catalogue gains two lists, `entry_policies` and
   `exit_policies`, each `{id: {params: Param[], track?: "no_loss" | "loss_capable", symbols?: [...]}}`,
   built from the two registries through `describe_params`. `composed` itself appears in `models` with its two
   slots instead of a flat parameter list.
2. **Backtest form.** `ParameterForm.tsx` gets a "Buy + Sell" mode: two pickers and two parameter panels, each
   reusing `ParamField` / `SweepableParamField` as is. **Several buys and several sells may be ticked at once**,
   which submits one run that is the matrix (each side's list becomes the nested sweep of Design §3). The form shows
   the cell count before submitting, using the existing split for oversized runs.
   Loss-capable sells are listed by default with a "may sell below cost" badge, and the form shows a warning
   while one is selected.
3. **Run result.** Each cell's `params` is the nested object, so nothing changes in storage. The result view gains a
   **buy × sell heatmap** when a run's model is `composed`: cell colour = the chosen metric (Total Return % or Calmar),
   one heatmap per track, click a cell for its existing detail view.
4. **Keep as candidate.** `add_candidate` names a composite `<buy>-x-<sell>-<ticker>-<run>-<cell>` and labels it
   "`<buy>` buying, `<sell>` selling, on `<ticker>`". The stored algorithm is the same four things as today.
5. **Paper trial.** `_wire`'s `paper_deployments` stops matching on symbol alone and runs the trader's own check,
   `AlgorithmControl.check(candidate change)`, against each paper deployment (the same check the CI test now runs).
   Deployments it refuses are listed with the refusal's text: "needs `execution.allow_signal_exit` in its file",
   "trades another fund", "regular-session strategy on an extended-hours deployment". The page still cannot set those.
6. **Live validation.** `AlgorithmControl._parse` validates `composed` recursively: `buy.id` / `sell.id` against
   the registries, each side's params against its own schema, the same locks and `mirrors` rules, and the 64-value
   limit counted across both sides. `server/live_control.py`'s `.../algorithm/check` route then works for composites
   unchanged, and so does the paper deployment's own algorithm editor (`web/src/components/live/AlgorithmPanel.tsx`),
   which gets the same two-panel editor as the backtest form.
7. **Evaluate, sign off, publish, real money.** Unchanged. A published composite is a profile with
   `strategy_id: composed`, reviewed and committed like any other. Real money still takes only committed,
   promoted profiles, with the typed id and the once-a-day limit.
8. **Contract.** Every new wire field is added to `server/contract.py`'s current shape **and**
   `web/src/types/backtest.ts` / `control.ts` together, as the root rules require.

## Catalogues

### Buy policies (Phase 2 and Phase 4 extract these; behaviour pinned identical)

| Entry id | Source | Extraction difficulty |
| --- | --- | --- |
| `fixed`, `rsi`, `bell_curve` | `size_calculators.py` | Trivial: no sell logic |
| `hf_local_reference` (champion) | `high_frequency_sizing.py` | Easy: `trail_pct` moves to the `trailing` exit policy |
| `hf_entry_gated`, `hf_signal_gated`, all `rk*` library ids | `gated_local_reference_sizing.py`, `signal_gated_sizing.py`, `library_sizing.py` | Easy: their docstrings state they override no exit hook beyond the parent |
| `bayesian_dual_scale` | `bayesian_sizing_calculators.py` | Medium: `target_return` must equal the exit target (the existing guard). This becomes a cross-check between policies |
| `ml_reachability_*`, `ml_regime_*` | `research/ml/` | Medium: same `target_return`/ticker cross-checks; `ml_regime_*` carries `trail_pct` |
| `harvest_sleeve` buys | `harvest_sleeve_sizing.py` | Medium: inventory decay is a buy behaviour; target decay and fractional liquidation move to sell policies |
| `ultimate_entry` | `ultimate_sizing.py` | **Hard.** The NATR regime with the calm-mode grid and turbulent capitulation-close buys. Tags turbulent buys `reversal` (§6). Regular-session only; ~250 sessions warm-up |
| `regime_sleeve_entry` | `regime_sleeve_sizing.py` | Medium: buys only while the sleeve's regime is active |
| `exposure_entry` | `ultimate_rsp_sizing.py`, `ultimate_ursp_sizing.py`, `catalog_exposure_sizing.py` | **Hard.** Buys whole lots up to a daily exposure target. The target signal is a parameter (the PLUS_DM/ADOSC vote, URSP's graded bear gate, or any `catalog_signal`) |

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
| `ultimate_exit` | loss-capable | no | Lifted from `ultimate_sizing.py`: calm lots sold `liquidate_minute` into the first turbulent session; `reversal`-tagged lots at `reversal_target`, optionally sold on the flip back to calm. Computes its own NATR regime, so it pairs with any entry |
| `exposure_rebalance_exit` | loss-capable | no (whole lots) | Lifted from `ultimate_rsp_sizing.py`: whole lots newest-first down to a daily exposure target from its own signal parameter. Pairs with a grid buy as a "risk cap" exit |

Pinned identities for the decomposed families: `composed(ultimate_entry, ultimate_exit)` ≡ `ultimate`, and
`composed(exposure_entry(s), exposure_rebalance_exit(s))` ≡ `ultimate_rsp` / `ultimate_ursp` / `catalog_exposure`
for the matching signal `s`. Both sides computing the same signal is duplicated work, accepted for the separation.

## Phases

Each phase lands as its own PR, keeps `cli.py test` green, and changes **no recorded result** unless the
phase says so. Phases 1 to 6 are research and engine work; Phase 7 is the web; Phase 8 is promotion.
Phase 7 can start once Phase 2 lands, in parallel with 3 to 6.

### Phase 0: Lock today's behaviour down
- Add a regression fixture: blotters and summary rows for the champion, `hf_entry_gated`, `harvest_sleeve`,
  `ultimate`, `ultimate_rsp` and `catalog_exposure` under `close` and `intrabar`, alongside
  `research/tests/test_regression_baseline.py`.
- **Done when** the fixture is committed and the suite asserts identity against it.

### Phase 1: Partial sells in the engine

**Status: done.** Three deviations from the text below, each to keep "no recorded result moves" true:
- `original_shares` / `entry_tag` live in a new `ledger_lot_details` side table (the `ledger_lot_owners`
  precedent), not new `ledger_lots` columns: no migration, no schema-version bump, and a lot with no row loads as
  unsold and untagged.
- The blotter gains **no** `remaining_shares` column and the summary row no `partial_sells` /
  `avg_tranches_per_lot`, because a new column would restate every pinned result. A partial sale is a `lot_id`
  with more than one sell row; Phase 5 derives the counts from that.
- Realized P&L now adds every partially sold share at what it fetched (`Lot.partial_sold_shares/value`), for open
  lots too. A run with no partial sale is unchanged.

- `engine/core/sizing.py`: `harvest_quantity` default; `ExitOrder` in a new `engine/core/exit_policy.py`;
  `lots_to_liquidate` accepts `ExitOrder | Lot`; `sellable_quantity` (Design §4).
- `engine/trading/decision_cycle.py`: `collect_liquidations` normalises to `ExitOrder`, checks
  `0 < quantity <= lot.shares` against this bar's book, and dedupes by lot (one exit per lot per bar).
  A new `harvest_orders(strategy, marketable, context)` applies `harvest_quantity` and `sellable_quantity`.
- `research/optimization/optimization_controller.py` and `intraday_validation.py`: sell `order.quantity` and call
  `close_lot(lot, sell_qty=filled_qty)`; the blotter row records the quantity and a `remaining_shares` column.
- `engine/trading/live_trading_loop.py`: `_harvest` submits `harvest_quantity` (legacy lots: whole); `_submit_exit`
  sums each order's quantity and `_apply_exit_fill` allocates up to each lot's requested quantity rather than its
  whole position.
- `engine/core/persistence.py`: `original_shares` and `entry_tag` columns, `schema_version` bump, a migration that
  sets `original_shares = shares` and `entry_tag = NULL` for existing rows, and `load_ledger` asserts
  `0 < shares <= original_shares`. `Lot` gains both fields (set in `register_buy`, never mutated).
- Metrics: `performance_analyzer.py` holding time counts a lot as closed only when its remaining shares reach 0;
  `server/fills.py` "closed" means fully sold. Add `partial_sells` and `avg_tranches_per_lot` to the summary row.
- Contract: the blotter or fills payload's `remaining_shares` goes into `server/contract.py` **and**
  `web/src/types/backtest.ts` together.
- **Tests**:
  - the regression fixture is unchanged;
  - a test double that sells 50% then 50% gives two guard calls, two blotter rows, one closed lot and the correct
    cash, under both fill models and in live with a fake broker;
  - a persistence round-trip of a half-sold, tagged lot;
  - partial **fills** of a partial **order** (the order's quantity, not the lot's);
  - `sellable_quantity` in a whole-share window floors, defers a zero, and defers a fractional remainder;
  - the no-loss scan test still finds one implementation.
- **Done when** all of that passes and Phase 0's fixture is identical.

### Phase 1b: Fidelity's fractional shares in the regular session
- `fidelity_gateway/broker.py` and `placing_broker.py`: replace the class-level `whole_shares = True` with a
  session-aware answer, fractional in the regular session and whole in pre- and post-market (owner, Oct 31).
  Buys gain fractional sizing in the regular session too, which today is "not modelled".
- `engine/trading/live_trading_loop.py`: the existing whole-share buy rounding (`_whole_share_refusal`) asks the
  broker per session instead of once.
- Verify against Fidelity's real order ticket (`fidelity_gateway/recon.py`) before trusting it: today every order
  is sent whole-share (`qtyTypeCode 'S'`), and the gateway says fractional sizing is not modelled.
- **Done when** a fractional sell and buy are placed on paper through the bridge in the regular session, and an
  extended-hours one is refused or floored as Design §4 says.

### Phase 2: Composition layer

**Status: done.** As built:
- `research/composition/entries.py` (buy policies), `exits.py` (`ExitPolicy`, `fixed_target`, `trailing`),
  `composed_strategy.py`. A buy policy is the registered strategy itself, constructed with its params, of which
  only the buy side is called; selling params (`trail_pct`) are refused there. Buy ids so far: `fixed`, `rsi`,
  `bell_curve`, `hf_local_reference`, `hf_entry_gated`, `hf_signal_gated` and every `rk*` library id.
- Nested sweeps live in `engine/core/config.expand_strategy_params`, generically: any `{id, params}` value is a
  component whose params' lists are swept, and a list of components sweeps over them. The engine knows nothing
  about what a component is.
- `strategy_registry.may_realize_loss(id, params)` and `regular_session_only(cls, params)` answer for a
  composition from its parts; the server's backtests, the live checks and `session_bars` ask them.
- Parameters typed `dict` are served as `"object"`, and composed's trigger as `"buy_policy"`; both are in
  `web/src/types/backtest.ts`. The composition editor itself is Phase 7.

- `research/composition/` as in Design §2, with `fixed_target` and `trailing` exits and entry adapters for
  `fixed`, `hf_local_reference`, `hf_entry_gated`, `LibrarySizing`.
- `config.expand_strategy_params` nested expansion; `param_schema.describe_params` describes `composed` as two
  nested schemas (needed by the backtest form and `live_algorithm` validation).
- `live_algorithm.check_live_support`: `composed` with a loss-capable exit requires `allow_signal_exit`; a warm-up
  need on either side requires `live_history_sessions` on that side; per-lot exit state requires `resume`; a
  regular-session side refuses extended hours.
- **Pinned identities** (the repo's existing discipline): `composed(hf_local_reference, fixed_target)` ≡
  `hf_local_reference`; `composed(hf_local_reference, trailing(p))` ≡ `hf_local_reference(trail_pct=p)`;
  `composed(rkNN, fixed_target)` ≡ `rkNN`. These are identical blotters, not "close".
- **Done when** the identities pass for both fill models and a `composed` config runs through `cli.py backtest`.

### Phase 3: Sell-policy library

**Status: done** (`research/composition/exit_library.py`). All ten sell policies are registered and each is
tested end to end with the champion buying. The shared properties hold for every policy: the no-loss track never
realises a loss, no lot is ever oversold, and every policy changes what sells on the fixture data. Each policy also
has unit tests for its own rule and for restart (`resume`). Notes:
- `scale_out` takes its ladder as a string, `"0.5@0.01,0.5@0.03"`, because a list in strategy_params is always a
  sweep axis. Its first rung replaces the grid's profit target.
- `signal_take_profit` defaults to the `zscore` gate. A mean-reversion gate shuts when price is stretched high,
  with lots in profit to sell; a trend gate (`supertrend`) shuts in downtrends, with lots underwater, and barely
  fires.
- The regime exits use the internal causal NATR regime (250 sessions of warm-up, seeded by `warm_up` in a
  backtest and `live_history_sessions` live); `regime_by_date` injects a map for research and is never offered
  on the web.
- Documentation is the module docstring and this plan. `docs/algorithms/` is the ranked-list ledger's generated
  pages, which describe whole strategies, so the sell policies are not added there.

- Implement the "New" rows of the sell table, each defaulting to inert where it has an off switch.
- One unit test per policy for its rule, plus shared property tests run against **every** registered exit policy:
  - a no-loss-track policy never produces a realized loss under `enforce_no_loss`;
  - a policy never asks for more shares than a lot holds;
  - `resume(open_lots)` after a simulated restart gives the same next decision as an uninterrupted run.
- **Done when** every policy is registered, documented in `docs/algorithms/` through
  `tools/build_algorithm_ledger.py`, and marked UNMEASURED.

### Phase 4: Extract the remaining buy policies, Ultimate and the exposure books included

**Status: done.** 74 buy policies and 14 sell policies are registered. Pinned identical, blotter for blotter, on
Phase 0's own cases:
- `harvest_sleeve` + `age_decay` ≡ the harvest sleeve's target decay, and `harvest_sleeve` (calm sleeve) +
  `regime_exit` ≡ its regime exit.
- `ultimate` + `ultimate_exit` ≡ `ultimate`, with and without `liquidate_reversal_on_calm`.
- `ultimate_rsp` + `rsp_rebalance` ≡ `ultimate_rsp`, and `catalog_exposure` + `catalog_rebalance` ≡
  `catalog_exposure`.
- `bayesian_dual_scale` + `fixed_target` ≡ itself.

How the split was made, which differs in places from the text below:
- **Book sell policies are subclasses of the original strategies** (`research/composition/book_exits.py`),
  used for their sell side only, so their sells are the original code by construction. Each keeps its own copy of
  the signal it sells on.
- **A buyer that reads its own lots** (Ultimate limits reversal buys by open reversal lots, learned in its
  `adjust_profit_target`) is marked `lot_view`. The composition shows it the lots for bookkeeping and discards
  any target it returns.
- **Lot tags are live:** `ultimate` tags each turbulent-mode buy `"reversal"`, `ultimate_exit` classes a tagged
  lot by its tag (an untagged one by mode, as Ultimate does), and both `resume`s read tags. The identity passing
  is the proof that tag and mode agree.
- **Selling parameters on a split buyer are refused unless left at their default** (`liquidate_minute` on
  `ultimate`, `target_decay_*` on `harvest_sleeve`, `trail_pct` everywhere).
- **A buyer with a `target_return` refuses a sell policy that replaces each lot's target** (`replaces_target`:
  `scale_out`, `scale_out_trail`, `vol_scaled_target`).

- Bayesian, ML, harvest-sleeve buys, each with a pinned identity against its original id combined with the exit
  policy that reproduces its old sells.
- `ultimate_entry` + `ultimate_exit` with lot tags (Design §6), and `exposure_entry` + `exposure_rebalance_exit`,
  each pinned identical to the original strategy (the identities under the sell table).
- Cross-policy checks move into `ComposedStrategy.__init__`: Bayesian/ML `target_return` must match the exit
  policy's *first* target, or the existing `allow_target_return_mismatch` escape hatch applies.
- The original ids (`ultimate`, `ultimate_rsp`, `ultimate_ursp`, `catalog_exposure`) stay registered and traded as
  they are. Their configs and profiles do not move to `composed`.

### Phase 5: The matrix runner, across any symbol

**Status: done** (`research/composition/matrix.py`, `cli.py matrix`, `config/matrix/first_8x8x4.yaml`).
- A cell is one buy id × one sell id, with all of their variants. Each cell gets `trials_per_cell` trials drawn by
  `RandomSearch` with a seed fixed per cell, so a cell sees the same parameters on every fund.
- A policy named without params takes its committed defaults.
- When a cell's sell policy replaces targets, its profit-target axis is collapsed to one value, so its budget isn't
  spent on bit-identical trials.
- The loss gate opens only for loss-capable cells.
- A fund under `min_history_years` (floor 5, default 10) is skipped. One under 10 years runs and is marked
  `short_history`. A cell whose policy was researched on another fund (an ML ticker) is skipped there with the
  reason.
- Each trial is reduced in the sink, then let go: headline metrics plus Calmar, partial-sale counts, per-year
  figures (return, drawdown, realized P&L, signal exits, year-end open lots and committed capital), monthly
  returns, stress windows, and returns by NATR regime and 200-session trend. Trials are appended to
  `trials.jsonl` as they finish.
- Not done yet: sharding over `cli.py shard` (a matrix runs on one machine with `--n-jobs`), and a warehouse
  view. Trials live in their own files.
- **The real first run has not happened.** This container's warehouse holds no bars. It is verified on synthetic
  funds (`research/tests/test_matrix.py`). Time one cell first: `cli.py matrix --config config/matrix/first_8x8x4.yaml
  --output output/matrix/first --limit-cells 1`.

- `research/composition/matrix.py`: takes buy variants × sell variants × symbols, builds the `composed` param grid,
  and calls **`OptimizationController.run_sweep`**, not `run_hf_sweep.py`, which drops `allow_signal_exit` and cash
  yield. It writes through `DuckDBResultSink`.
- **Symbol universe** (owner: any symbol, long history): every fund in the warehouse
  (`engine/warehouse/inventory.py`) with at least `min_history_years` of bars (default 10, never below 5), over its
  **full** history. A policy restricted to some funds (ML tickers, an exposure signal researched on RSP) runs only
  on those and is marked so. Simulated leveraged history (e.g. `tools/simulate_ursp.py`) may extend a fund's
  history but is reported as simulated, never pooled silently with real bars.
- **Equal tuning budget per cell.** A policy with a 50-point grid would beat one with 2 points by search luck alone.
  Each cell gets the same number of trials (Bayesian search inside the cell, fixed seed), and the trial count goes
  into the deflated Sharpe.
- **Per-year output, stored once.** Each cell stores its per-calendar-year return, max drawdown, realized and
  unrealized P&L and year-end inventory (from the equity curve and blotter the run already builds), so Phase 6 never
  re-simulates to slice by year.
- CLI: `cli.py matrix --config config/matrix_<name>.yaml`. It shards across machines through the existing
  `cli.py shard` path.
- Warehouse: a `composition_cells` view over `parameters_json -> '$.buy.id'` / `'$.sell.id'` and the symbol.
  No table change.
- **Done when** a 3 × 3 × 2-symbol smoke matrix on a one-year slice completes, dedups on re-run (hash), and the
  view returns 18 cells with per-year rows.

### Phase 6: Analysis that answers the question

**Status: tooling done** (`research/composition/analysis.py`, `cli.py matrix --analyze DIR` → `report.md`); **the
results document waits for the real run.**
- Two-way decomposition with variance shares, and the interaction F-test (a two-way ANOVA with years as
  replicates; the p-value from an in-house incomplete beta, so no scipy).
- The buy × sell × fund decomposition, the independent-or-pair decision rule, year × cell tables,
  leave-one-year-out rank correlation, stress windows, the market-condition breakdown, and PBO with the
  finalists' deflated Sharpe.
- Tests construct additive, crossed and one-year-driven matrices, and check that each is told apart.

For each track, metric (Total Return %, Calmar; **not** Capital Velocity Index, which saturates) and symbol:

1. **Cell score** = the median over the cell's trials of the metric, plus the best trial reported alongside, never
   instead. The median rewards a policy that is good across its parameters, not one lucky point.
2. **Two-way decomposition** of the cell-score matrix: `score[b,s] = μ + α_b + β_s + γ_bs`.
   - `α_b`: buy main effect. Rank buys by it.
   - `β_s`: sell main effect. Rank sells by it.
   - `γ_bs`: interaction. Report the share of variance it explains, and check significance with a permutation test
     over per-year returns (shuffle sell labels within each buy row).
3. **Across symbols**: the same decomposition with symbol as a third factor, so a component that wins only on
   TQQQ shows up as a large buy × symbol (or sell × symbol) term rather than as "best".
4. **Decision rule**:
   - If interaction is small (say under 10% of explained variance and not significant), the best buy is
     argmax `α` and the best sell is argmax `β`, and they can be chosen independently.
   - Otherwise, report the best **pair**, and for each buy, its best sell.
5. **Year effects** (owner: understand what a year like 2022 does):
   - a year × cell table of return and drawdown, per symbol;
   - **leave-one-year-out**: each cell's metric with each year removed, and the rank correlation of the whole
     matrix with that year removed. A ranking that changes when 2022 is dropped is driven by 2022;
   - named stress windows reported on their own: 2018 Q4, Feb to Mar 2020, all of 2022;
   - year-end inventory and committed capital through 2022, the measure of how much a pairing got stranded.
6. **Market-condition breakdown**: returns split by regime (the NATR calm/turbulent regime the Ultimate family
   uses, and trend up/down from a 200-day average). This is where the loss-capable track earns its place:
   it shows which sells help in which conditions.
7. **Overfitting control**: PBO by CSCV across all cells (`overfitting.probability_of_backtest_overfitting`, with
   per-month returns as the T × N matrix), deflated Sharpe for each finalist with N = total trials across the whole
   matrix, then walk-forward (`walk_forward.py`) and purged CV on the top 3 pairs only.
8. **Diagnostics per cell**: open lots and committed capital at the end (stranded inventory, the problem
   `trailing_target.py` was written for), realized versus unrealized P&L, partial-sell count, average tranches per
   lot, and turnover.

Output: `docs/research/buy-sell-matrix-results.md` with the heatmaps, the decomposition tables and the year tables.

### Phase 7: The web pipeline for composites

**Status: done**, all five steps, each with its contract on both sides:
1. **Catalogue and recursive validation.** `research/composition/catalog.py` is served as `composition` by
   `/api/backtest/funds`, by the live `/algorithm` route and by `AlgorithmControl.describe`. A composed change is
   validated component by component, so a bad value is refused by name (`buy.params.per_lot_pct`). A policy named
   with no params takes its committed defaults; one given any is used as given.
2. **Backtest form.** Choosing `composed` shows a buy column and a sell column, each filterable, with each chosen
   policy's parameters. Several on either side make the matrix one run. Loss-capable sells carry a "may sell
   below cost" badge, and choosing one shows a warning; partial sells are tagged.
3. **Result heatmap** (`CompositionMatrix`): each buy × sell pairing's best configuration on a chosen metric, with
   loss-capable columns marked.
4. **Algorithms tab.** A composed candidate is named and labelled for its halves and carries
   `composition: {buy, sell, loss}`. Trials are offered only where the paper deployment's own
   `AlgorithmControl.check` passes; `paper_refused` gives each refusal's reason (for example
   `execution.allow_signal_exit`). A composed trial queues the composed switch.
5. **Live switch form** (`AlgorithmPanel`): the same editor in single mode (one buy, one sell), seeded from the
   composition in force.

Real money is unchanged: committed, promoted profiles only. A composed profile is just `strategy_id: composed`.
Not done: the per-year table in the web result, which is the matrix report's job (`cli.py matrix`).

Design §7, in this order, each step its own PR with its contract change made on both sides:

1. Catalogue endpoint (`entry_policies`, `exit_policies`) and recursive `AlgorithmControl._parse`. Backend only;
   pinned by server tests that a composite validates, a bad nested param is refused with its name, and the 64-value
   limit counts both sides.
2. Backtest form "Buy + Sell" mode, single pair first, then multi-select (the matrix as one run).
3. Result heatmap for `composed` runs, plus the per-year table from Phase 5.
4. Candidate naming and labels; `paper_deployments` through `AlgorithmControl.check` with refusal reasons.
5. Live `AlgorithmPanel.tsx` composite editor on paper deployments.
- **Done when** a composite goes from the backtest form to a published profile entirely on the web, on a paper
  deployment, and the same profile is offered to a real-money deployment's switch only after it is committed.

### Phase 8: Promotion
The winning pair is promoted the way any strategy is, with nothing special-cased: a `config/` file with `live:`
(`strategy_id: composed`), paper trial, `engine/promotion.py` gate. Partial sells add one paper-trial check:
every partially sold lot's broker position matches `shares` after reconciliation.

## Risks

| Risk | Mitigation |
| --- | --- |
| Partial fills of a partial order double-count against the lot | `sell_qty` is already incremental (`fill_accounting.py`); add the test in Phase 1 |
| Raising a target after a partial sale leaves a resting order at the old target | In-flight lots are already skipped by `adjust_open_lot_targets`; the policy only sees the lot once the order settles |
| A restart loses the rung or a lot's tag | The rung is derived from `shares / original_shares`, and the tag is a column; both are persisted |
| A whole-share window strands a fractional lot | Design §4 defers fractional remainders to the regular session; the backtest models the same deferral |
| Fidelity's fractional order type is not modelled yet | Phase 1b verifies it against the real ticket before anything relies on it; until then Fidelity stays whole-share |
| Tiny tranches are rejected by the broker or eaten by commission | `min_tranche_notional` fallback to the whole remainder; the matrix runs with the real cost model |
| The matrix is large enough to find noise | Equal per-cell budget, median cell score, PBO, deflated Sharpe with the full trial count, walk-forward on finalists, cross-symbol and leave-one-year-out checks |
| A many-symbol, full-history matrix is expensive | Time one cell first; shard it; store per-year results so analysis never re-simulates |
| Runtime: the champion already spends most of a run walking open lots | `wants_lot_retargeting` early-out is preserved; a ladder policy returns True only on bars with a new lot or a partial sale, the pattern `harvest_sleeve` already uses |
| A composed strategy differs subtly from the original class | Phase 2 and 4 identity tests on identical blotters |
| The web offers a trial deployment that then refuses the switch | `paper_deployments` runs the trader's own check and shows the refusal |
| A browser loosens a loss gate | It cannot: `allow_signal_exit` stays in the deployment's file, and real money still takes only committed profiles |

## Decided after revision 2 (Oct 31, 2026)

1. **First real matrix**: about 8 buys × 8 sells × 4 symbols at an equal budget, sized from one timed cell.
2. **Minimum history for "any symbol"**: at least 5 years (enforced); **10 or more recommended**. The matrix
   config's default is 10, the floor is 5, and the result marks any fund under 10 years. Simulated leveraged
   history stays as Phase 5 says: allowed, reported as simulated, never pooled with real bars silently.
3. **Loss-capable sells on the web form**: shown **by default**, each clearly marked as able to sell below cost
   (a badge on the option and a warning on the form when one is selected). The run, candidate and profile carry
   the same mark, so it is never lost on the way to a deployment.

## Effort (rough)

Phase 1 is the largest and riskiest engine change, since it touches all three sell sites, persistence and metrics.
Phase 1b depends on Fidelity's real order ticket. Phases 2 to 4 are mostly adapter code plus identity tests, with
Ultimate's decomposition the hardest part. Phase 5 is plumbing over the existing sweep machinery. Phase 6's compute
is unknown until one cell is timed: run a single cell first and size the full matrix from that. Phase 7 is five
small web PRs, each with its contract change on both sides.
