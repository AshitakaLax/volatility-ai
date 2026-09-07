# Incorporating a learned model, and the environment to train it

## Context

Every sizing strategy in this project is hand-specified: a fixed
percentage, a bell curve, an RSI response, a Bayesian posterior with
hand-chosen half-lives. The question is whether a model *learned* from
the tape does better, and what it would take to find out honestly.

The honest part is most of the work. This project has already produced a
result that survived 18 of 18 parameter settings, a 12-sigma control
against matched-random regimes, both chronological halves and COVID
removal — and then **failed** the moment it was asked to predict
something it had not been fitted to (`plan.md`, Stage 4). A model with
millions of parameters will find that kind of result faster and hide it
better.

So this plan is organised around the evaluation, not the model. The
model is the easy part.

---

## What the bar actually is

Before any of this: **the grid loses to buy-and-hold on most
instruments this project has measured.**

| instrument | grid best ret/dd | buy-and-hold ret/dd |
|---|---|---|
| RSP | — | wins, monotonically |
| COWZ | 0.252 | **0.343** |
| SPYD | 0.177 | **0.210** |
| TQQQ | 3.03x its benchmark (selected max) | — |

A learned sizing model **cannot fix a strategy that is structurally
behind holding the instrument**. It can only allocate better within the
grid's own logic. So the bar is stated up front and does not move:

* **Primary:** beat the best hand-specified strategy (`hf_local_reference`
  at its champion parameters) on the same instrument, out of sample.
* **Secondary, and the one that matters for deployment:** beat
  buy-and-hold on return/drawdown for that instrument.
* A model that clears the first and not the second is a better grid, not
  a reason to trade the grid.

---

## What a model is even allowed to decide

The engine's invariants bound the action space, and they are not
negotiable — they are what the system is. From `src/no_loss_guard.py`
and `src/live_trading_loop.py`:

| the model CAN | the model CANNOT |
|---|---|
| size each buy (`calculate_trade_value`) | sell below cost basis — `no_loss_guard` refuses it |
| move the buy trigger (`_grid_trigger_level`) | force-liquidate — no code path exists |
| retarget open lots (`adjust_profit_target`) | bypass the cost model, settlement, or fill rules |
| request a signal exit (`lots_to_liquidate`) — **only** with `execution.allow_signal_exit=true`, the one path permitted to realise a loss | trade anything but the configured symbol |

**This is a sizing-and-timing model, not a free-form trader**, and that
constraint is worth more than it costs: the action space is small enough
that a modest model can fill it, and every catastrophic outcome an RL
agent would need to be taught to avoid is already unreachable.

Note the trigger override specifically. `hf_local_reference` avoids the
stranding failure — where the buy reference is left behind by a rising
market and the book never reopens — *because* it overrides
`_grid_trigger_level` to measure from a rolling high rather than the
last buy. **Any learned model must do the same or it inherits the bug**,
which four of five existing strategies demonstrably have.

---

## The integration point is two methods

`SizingStrategy` (`src/size_calculators.py:51`) has exactly two abstract
methods:

```python
def record_tick(self, context: MarketContext) -> None: ...
def calculate_trade_value(self, context: MarketContext) -> float: ...
```

So a learned model is a `SizingStrategy` that holds a loaded model and
returns a dollar figure. Register it in
`src/strategy_registry.STRATEGIES` and it works **everywhere at once**
— `cli.py backtest`, `run_sweep`, `WalkForwardRunner`, `MonteCarloRunner`,
the live loop, the web UI's dropdown, the sweep matrix, run history —
with no changes to any of them.

That is the whole integration. Everything else in this plan is about
being allowed to believe the result.

### The one hard constraint on inference

`calculate_trade_value` is called **per bar**, inside the engine loop,
about a million times per backtest. At 5 ms per call a single run takes
90 minutes instead of 15 seconds.

* **Budget: < 50 µs per call.** A gradient-boosted tree on ~50 features
  meets this comfortably; a per-bar neural network forward pass in
  Python does not.
* Features must be **incrementally updatable** from `record_tick`, not
  recomputed over history each bar. `src/sizing_indicators.py`'s
  `RollingMean` / `RollingStdev` / `WilderRSI` are the existing pattern
  and should be reused rather than reimplemented.

---

## Phase 0 — The training environment

The deliverable is a dataset builder that produces one row per bar with
features **that were knowable at that bar**, and labels that were not.

### 0.1 `src/ml/features.py` — the feature contract

One function, `features_for(context, state) -> dict[str, float]`, used by
**both** the offline dataset builder and the live strategy. That is not
tidiness: two implementations of "the features" is exactly how a model
trained on one thing gets deployed predicting another, and this project
already has the shape of that bug on record (`live_trading_loop` and the
backtest sharing `decision_cycle` precisely to prevent it).

Feature families, all already available:

| family | source | notes |
|---|---|---|
| price / return structure | `MarketContext.open/high/low/close`, `bar_index` | multi-horizon returns, realised vol |
| technical indicators | `src/indicator_library.py` | **134 TA-Lib indicators already wired**, with warmup handling |
| intraday seasonality | `context.time_of_day_flag`, `src/intraday_profile.py` | the open measured at **2.56x** the session average — the largest single effect in this repo |
| volume | `context.volume` | |
| book state | `context.open_lot_count`, `drawdown`, `peak_equity`, `cash` | what the strategy itself is carrying |
| event calendar | `context.is_macro_event_day`, `is_earnings_reaction_day`, `event_intensity`, `minutes_to_event` | `src/fomc_calendar.py`, `src/earnings_calendar.py` |
| implied vol | `context.implied_vol_change` | via `src/external_index_series.py` |

**`macro_surprise_factor` is inert** — declared at
`market_context.py:50`, populated by nothing, read by nothing. Either
populate it from a real consensus series or delete it; leaving a third
dead field is how the proliferation the Task 7.9 gate exists to prevent
begins.

**The anti-leakage rule, inherited not invented:**
`indicator_library.signals()` compares each indicator to its **trailing**
median, never a full-sample one, "because a full-sample quantile knows
the future, and on a ten-year backtest that is worth several points of
fictitious CAGR." Every normalisation in the feature set follows that
rule. No z-score against full-sample mean and standard deviation. No
`fit_transform` on the whole frame.

### 0.2 `src/ml/labels.py` — what the model predicts

The natural target is already implemented analytically in this repo, by
`BayesianDualScaleSizing`:

> **P(price reaches `+profit_target` within `horizon_days`)**

That framing earns its place three ways: it is the quantity the grid
actually needs to size a lot; there is a working analytic incumbent to
beat, which this project would otherwise lack entirely; and the
consistency check between `target_return` and `profit_target` is already
enforced by the engine.

**The label must use maximum favourable excursion, not forward return.**
A lot fills on *touch* — `target_sell_price` is a resting limit — so the
label is:

```
y = 1  if  max(high[t+1 : t+H]) >= close[t] * (1 + profit_target)
```

Using `close[t+H]` instead would be a different and wrong question, and
this project has already recorded that distinction ("fills on touch, so
**maximum favourable excursion**, not forward return, decides
reachability").

Secondary label, for the exit side: MAE over the same horizon, which is
what a `lots_to_liquidate` decision would need.

### 0.3 `tools/build_ml_dataset.py` — the builder

Walks a minute file once, drives the real `MarketContext` construction,
emits Parquet partitioned by ticker and year. Reuses
`optimization_controller`'s own per-bar loop rather than a parallel one,
so a feature computed for training is computed the way the engine would.

Expected size: ~1.03M bars × 7 instruments × ~60 float32 columns ≈
**1.7 GB**. Fits in memory on this machine.

### 0.4 The splits, decided before any model exists

| split | period | purpose |
|---|---|---|
| train | 2016 – 2021 | fitting |
| validation | 2022 – 2023 | hyperparameters, early stopping |
| **holdout** | **2024 – 2026** | **touched once, at the end** |
| cross-instrument holdout | every ticker not trained on | the test Stage 4 failed |

2022 sits in validation deliberately: it is the only severe bear market
in the sample, and a model selected without ever seeing one would be
selected on a decade of upward drift.

**The holdout is not to be looked at.** Stage 4 in `plan.md` is the
cautionary case — 544 configurations scored against one instrument, and
the winner did not survive contact with a second one.

---

## Phase 1 — Baselines before models

A model is only interesting relative to something. Establish, on the
same splits and the same metric:

1. **Buy-and-hold** for the instrument.
2. **`hf_local_reference`** at its champion parameters — the real bar.
3. **`bayesian_dual_scale`** — the analytic posterior the model is
   trying to replace, which makes "did learning help?" answerable rather
   than rhetorical.
4. **A matched-random control** — the `tools/stage3_grid.py` pattern: a
   model whose outputs are shuffled while preserving their marginal
   distribution. This project's NATR result needed exactly this control
   to be believable, and the policy-vs-signal distinction it exposed
   applies identically here.

---

## Phase 2 — The model

**Gradient-boosted trees first, and probably last.** LightGBM or
XGBoost, ~50 features, ~7M rows, tabular, low signal-to-noise. On this
hardware (RTX 4050, 6 GB; 12 CPU cores) a GBM trains in minutes on CPU
and meets the 50 µs inference budget. A sequence model is a later
question, justified only by a GBM that works and visibly leaves
something on the table.

Add to `requirements-ml.txt`, separate from `requirements.txt` for the
same reason `requirements-web.txt` is separate: **the machine that
trades must not grow a training dependency.** The live path loads a
serialised model, not a training framework.

* `src/ml/model.py` — train / calibrate / persist. Probability
  calibration matters more than accuracy here: the output is fed to a
  sizing function, so a model that is 60% confident must be right 60% of
  the time or the sizing is systematically wrong.
* `src/ml/sizing.py` — `LearnedSizing(SizingStrategy)`. Maps calibrated
  probability to a dollar figure, clamped to the same bounds
  `hf_local_reference` uses, and overriding `_grid_trigger_level` with a
  rolling reference so it does not inherit the stranding bug.
* Registered as `"learned"` in `strategy_registry`.

---

## Phase 3 — Evaluation, which is the actual work

### 3.1 Use the harness that already exists

`src/walk_forward.py`'s `WalkForwardRunner` selects parameters on a
training window and scores them **only** on the following window. It is
fully implemented, tested — and **used by nothing outside its own
tests**. It was built for precisely this and has been waiting.

The one change needed: it currently sweeps *parameters*. For a learned
model the per-fold step is *fit the model on the training window, score
on the test window*, which is the same shape with a different inner
call.

### 3.2 The four questions, in order

1. **Does it beat its own baselines out of sample?** Walk-forward across
   2016–2023, holdout untouched.
2. **Is it the model or the policy?** Matched-random control. Stage 3's
   finding — that liquidate-on-flip applied to noise was *actively
   destructive* at −2.48% CAGR — is why this cannot be skipped: a policy
   effect and a signal effect score identically without it.
3. **Does it transfer?** Train on TQQQ, evaluate on QQQ, SOXL, RSP,
   COWZ, SPYD. **This is the test Stage 4 failed**, and it is the one
   that decides whether there is a model here or a memorised price path.
4. **Only then, once:** the 2024–2026 holdout.

### 3.3 Pre-registration

Each stage's prediction is written into the script's docstring **before
it runs**, the way `tools/stage4_leverage.py` recorded "15+ of 18 on QQQ
falsifies the drag mechanism" and was then held to it. A result read
against a prediction is evidence; the same result read afterwards is a
story.

---

## Phase 4 — Deployment, if it survives

Only reachable if Phase 3 clears. In order:

1. Model artefact versioned and hashed; the ledger records **which model
   hash** produced each decision, alongside the parameters
   `live.parameters` already persists.
2. `LearnedSizing` must be picklable — `run_sweep` uses
   `ProcessPoolExecutor` at `n_jobs > 1` and pickles the strategy per
   task.
3. Paper trading on the Pi, against `hf_local_reference` running the
   same instrument, for a full quarter.
4. **A kill switch that does not depend on the model**: the existing
   `CircuitBreaker` halt already blocks new buys while letting open lots
   exit, and requires no cooperation from the strategy.
5. Live only after the Task 7.7 promotion evidence, unchanged.

---

## File manifest

| file | purpose |
|---|---|
| `requirements-ml.txt` | training deps, kept off the trading machine |
| `src/ml/features.py` | the one feature definition, shared offline and live |
| `src/ml/labels.py` | MFE-based target within horizon |
| `src/ml/model.py` | train, calibrate, persist |
| `src/ml/sizing.py` | `LearnedSizing(SizingStrategy)` |
| `tools/build_ml_dataset.py` | bars → Parquet feature store |
| `tools/train_model.py` | fit + calibrate + report |
| `tools/eval_walk_forward.py` | drives the existing `WalkForwardRunner` |
| `tools/eval_transfer.py` | cross-instrument, the Stage 4 test |
| `tests/unit/test_ml_features.py` | leakage tests — see below |

---

## What would make this dishonest

The section this project keeps, because it keeps needing it.

* **Any full-sample statistic in a feature.** A mean, a median, a
  scaler fitted on the whole frame. Tested directly: build features on a
  truncated frame and assert every row matches the same row built on the
  full frame. A feature that changes when *future* data is appended is
  leaking, and the test names it.
* **Selecting on the holdout.** 544 configurations against one
  instrument produced a 12-sigma result that did not transfer. More
  parameters will do it faster.
* **Reporting the best fold.** Walk-forward reports every fold or none.
* **Quietly dropping the cost model, settlement, or the no-loss guard**
  to make a number look better. Any of those changes what the strategy
  *is*, and the comparison stops being a comparison.
* **Comparing against a weak baseline.** The bar is
  `hf_local_reference` at its champion parameters and buy-and-hold — not
  `fixed`, which this project has now shown stops trading entirely after
  its first flat book.

## What success and failure both look like

**Success:** the learned model beats `hf_local_reference` and the
analytic posterior on walk-forward folds, survives the matched-random
control, transfers to at least two instruments it was not trained on,
and only then clears the holdout.

**Failure is a real outcome and cheap at this stage.** If the model
matches the analytic posterior, the answer is that the posterior already
captures what is there — which is worth knowing and costs one Phase 2.
If it beats it in-sample and fails to transfer, that is Stage 4 again,
and the right response is to record it and stop, not to add features
until it passes.

---

# Phase 0 — BUILT AND MEASURED (2026-09-06)

## What exists now

| File | What it does |
|---|---|
| `src/ml/sources.py` | Registry of **118 public series**, no API key, with per-source publication lag |
| `tools/fetch_market_inputs.py` | Pulls them to `data/external/` + `manifest.json`; records failures rather than aborting |
| `src/ml/features.py` | 73 macro/cross-asset features + 22 bar-local; causal transforms, as-of join |
| `src/ml/labels.py` | MFE labels (`reached`, `time_to_hit`, `mfe`, `mae`) by binary lifting |
| `tools/build_ml_dataset.py` | Joins the three layers into parquet + schema |
| `tools/evaluate_ml_features.py` | Purged walk-forward with paired controls |
| `tests/unit/test_ml_labels.py` | 36 tests pinning labels to a brute-force reference |
| `requirements-ml.txt` | lightgbm 4.6.0 + scikit-learn 1.7.2, deliberately separate |

Sources: 51 FRED, 10 CBOE, 54 Yahoo, 3 added later — **113/113 fetched, 0 failed**.

## Publication lag, which was the main correctness risk

A FRED observation is stamped with the date it *describes*, not when it became
knowable. Joining on the observation date lets a backtest read August CPI during
August. Every source now declares its lag and is stamped at the moment it could
first have been read. Verified: July 2026 CPI becomes readable 2026-08-15, which
is when BLS actually released it.

## Two corrections to standing claims

* **`src/high_frequency_sizing.py` said FRED and BLS "refuse programmatic access".**
  False, and load-bearing — it is why macro inputs were written off rather than
  measured. Both serve series data keyless. What is genuinely unavailable is
  narrower: FRED's *release-calendar* endpoint needs a key (HTTP 400) and bls.gov's
  schedule pages return 403. Corrected in place.
* **FRED caps the ICE BofA credit series at a rolling 3 years** without a key
  (measured: 795 rows from 2023-09-05; `cosd` does not lift it). That is ~28%
  coverage over a 2016–2026 window. Moody's `BAA10Y`/`AAA10Y` reach 1986 and carry
  the signal instead — Baa-10y sits at the 100th percentile on both 2018-12-24 and
  2020-03-23, and the 13th today.

## The measured result, stated plainly

Purged expanding-window walk-forward, 5 folds, paired per fold. Label
`reached_t0.5_h390` (a 0.5% target within one session):

| Ticker | bar | macro | both | paired lift | folds + | verdict |
|---|---|---|---|---|---|---|
| RSP  | 0.628 | 0.623 | 0.626 | −0.001 ± 0.011 | 2/5 | indistinguishable |
| COWZ | 0.524 | 0.549 | 0.570 | **+0.046 ± 0.012** | 5/5 | adds |
| SPYD | 0.563 | 0.563 | 0.574 | +0.011 ± 0.011 | 3/5 | indistinguishable |

At `h1950` (five sessions) **all three are indistinguishable** — so the hypothesis
that daily macro needs a longer horizon to express itself is *not* supported; the
shorter horizon gave the cleaner read.

**The harness does not leak.** Shuffled-label control over 50 fits: 0.5011 ± 0.0047,
+0.2 SE from chance. Note that single-seed five-fold controls ranged 0.480–0.542, so
the control is now averaged over several seeds — one seed is not evidence.

### The honest reading, and why it is not "macro works"

One reproducible lift, on one fund, at one horizon — out of **six comparisons**
(3 tickers × 2 horizons). One hit at roughly p≈0.03 across six tests is close to
what chance produces. This is the same selection-bias trap Stage 2/3 already walked
into on indicator sweeps, and the matched-random control does not rescue it: the
control kills "policy alone", not "we searched a wide feature set against a few
price paths".

COWZ is therefore a **candidate to pre-register and test out of sample**, not a
finding. It is also the shortest history (2016-12-22, 102k strided rows), which is
where an accidental result is most likely.

Absolute AUCs of 0.52–0.63 are weak in any case, and none of this has yet been
connected to money: AUC is not P&L. A model must beat `hf_local_reference` on
Harvest-to-Stuck through `SizingStrategy`, not on a classification metric.

## Next, in order

1. Pre-register the COWZ claim and test it on held-out 2025–2026 data only.
2. Feature ablation by category — is the lift the credit block, the vol block, or one column?
3. Baselines from Phase 1 *before* any model is wired in.
4. Only then the `SizingStrategy` integration, against Harvest-to-Stuck.

## Ablation by block (added same day)

Which part of the 118 series carries the COWZ lift. Each block added to the bar-only
baseline, same folds, paired:

| Block | COWZ lift | folds + | SPYD lift | folds + |
|---|---|---|---|---|
| vol (15 cols) | **+0.039 ± 0.010** | 5/5 | +0.020 ± 0.013 | 3/5 |
| rotation (10) | **+0.028 ± 0.007** | 5/5 | +0.003 ± 0.007 | 3/5 |
| factor (5) | +0.026 ± 0.009 | 4/5 | −0.031 ± 0.014 | 1/5 |
| credit (12) | +0.019 ± 0.013 | 3/5 | +0.013 ± 0.012 | 3/5 |
| rates / curve / labour / fx | ≤ +0.010, inconsistent | | ≤ 0, inconsistent | |

**The volatility block alone (+0.039) accounts for nearly the whole macro lift (+0.046)
on COWZ** — the VIX term structure, VVIX and SKEW, not the macro calendar. On SPYD
nothing survives; its best block is 3/5 folds.

Two caveats that keep this from being a finding:

* **28 comparisons** (14 blocks × 2 tickers). P(5/5 by chance) ≈ 0.03 each, so ~1 spurious
  "consistent" block is expected; COWZ shows five. That is more than chance alone, but the
  blocks are **strongly correlated** with each other, so these are not 28 independent
  tests and no clean multiple-comparison correction applies.
* It remains one fund. The direction is a useful prior for what to test next — *the
  volatility complex, not the macro calendar* — and nothing more.

---

## UI hookup (2026-09-07)

**A scope decision, stated rather than assumed:** "hook up the AI trading model
with the UI" is built as a **read-only research view**, not a live-trading
integration. There is no trained, saved model to deploy as a trading input —
Phase ML-0 above ran evaluation folds to measure whether the data carries
signal, and those models are not persisted. And the one measured result
(COWZ, +0.046 AUC, one horizon) is one hit in six comparisons, which the plan
itself already flagged as "a candidate to pre-register... not a finding."
Wiring that into `SizingStrategy` on the machine that runs paper (and
eventually live) trading would contradict both the evidence and the plan's
own sequencing (Phase 1 baselines → Phase 2 model → Phase 3 pre-registered
evaluation → Phase 4 "deployment, **if it survives**").

**What was built instead:** a "Model research" tab, new third section
alongside Backtesting and Live, showing exactly what Phase ML-0 measured —
source inventory, dataset coverage, the evaluation table (bar/macro/both AUC,
paired lift, verdict), and the per-category ablation — with the same honest,
hedged framing as this document. A banner states plainly that nothing on the
tab touches trading.

* `server/ml_insights.py` — read-only, reads precomputed JSON only (no
  `lightgbm`/`sklearn` import, no `src.ml.*` import — see its own docstring).
  Follows the exact split `live.py`/`control.py` established, extended with
  new AST guards in `tests/unit/test_server_capability.py`.
* `server/ml_upstream.py` — Pi-side relay, GET-only, reusing
  `VAI_BACKTEST_UPSTREAM` rather than a second env var. `data/external/` and
  `data/ml/` are gitignored and live only on the workstation.
* `tools/ablate_ml_features.py` — new; persists the per-category breakdown
  that was previously only an ad hoc computation, as `data/ml/ablation_*.json`.
  Confirms the earlier read: **COWZ shows 5/14 categories consistent (vol
  alone: +0.039 of the +0.046 total), RSP and SPYD show 0.** Concentrated on
  the shortest-history fund is exactly where a false positive is likeliest.
* `web/src/components/ml/ModelInsights.tsx` + `web/src/types/ml.ts` — new tab.

Full suite green: `pytest tests/unit -q` → 1870 passed; `npm run build` and
`npm test` clean.

**Deploy:** pushed to `origin/main`. This session has no SSH access to the
Pi (checked; both configured hosts refused key auth) — the Pi-side
`git pull && docker compose -f docker-compose.pi.yml up -d --build` needs to
be run by the user.

---

## Phase ML-2 — Wired into the backtest engine as a selectable strategy (2026-09-07)

Answers "how do I select the AI model for simulations": it is now a real,
selectable, backtest-only `SizingStrategy` -- `ml_reachability_rsp` /
`_cowz` / `_spyd` in the same dropdown as `fixed`/`hf_local_reference`/etc.
**Still nowhere near the paper/live loop** -- see Phase ML-1's scope decision,
unchanged.

### What actually got built, and the two things that don't fit in a summary

* **21 bar-local features, computed ONE BAR AT A TIME** (`src/ml/rolling.py`),
  because `SizingStrategy` genuinely cannot see more than that: `strategy_class(**params)`
  gets no DataFrame, only per-bar `MarketContext` -- the same constraint live
  trading has. Pinned against the offline `features.bar_features()` batch
  computation in `tests/unit/test_ml_rolling.py`; this caught two real bugs
  (RSI needed re-deriving to match `ewm(adjust=False)` exactly rather than
  classic Wilder smoothing, and the true-range buffer was missing row 0's
  partial value, both invisible in isolation and both exact-zero once fixed).
* **The persisted model trains on 36 features, not the offline dataset's 95** --
  21 bar-local (`volume_ratio_390b` dropped: `MarketContext` carries no
  volume, the same gap already deferred once for RSI-at-entry) + the
  15-column volatility block, which `tools/ablate_ml_features.py` measured
  as carrying nearly all of the macro lift that survived walk-forward at
  all (+0.039 of +0.046 on COWZ). `src/ml/features.py` was refactored
  (`transformed_sources()`) so the live and offline paths share the SAME
  transform code for that block, not two copies to keep in sync by hand.
* **A held-out calendar cutoff (2024-01-01), not a walk-forward average.**
  `tools/train_ml_model.py` persists ONE model a user can then backtest
  over any date range the UI offers -- unlike every upstream evaluation
  tool, which throws its models away after each fold. Measured test AUC on
  the held-out tail: RSP 0.60, COWZ 0.57, SPYD 0.57.
* **Confidence can only shrink a position, never grow it past the base
  ceiling.** Built on `_BaselineScaledStrategy`, the same composition
  `RsiMomentumSizing`/`BellCurveProbabilitySizing` already use -- consistent
  with every other model-driven strategy here, and the conservative
  direction for three funds whose stated purpose is reducing risk.
* **Shares the grid's stranding vulnerability.** No trigger override; this
  changes only how much a confirmed buy is worth, matching every strategy
  but `hf_local_reference`. Stated in the module docstring rather than
  fixed, given the scope already spent here.
* **Measured, not assumed, to be ~25x slower per bar** (~600us vs ~23us) --
  a full-length run is minutes, not seconds. `predict(num_threads=1,
  validate_features=False)` recovered about a quarter of the model-call
  cost; rewriting the feature tracker for throughput was judged not worth
  it given how weak the signal it feeds still is. The UI's ParameterForm
  states this plainly when one of the three is selected, alongside the
  "only COWZ is measured" caveat from the scope decision.

### The bug this caught before it shipped

First pass reintroduced a variant of a failure this project already fixed
once (`server/backtest.py`'s own comment on missing-argument errors): a
ticker mismatch detected deep in `optimization_controller.py`'s
per-combination isolation surfaced to the API caller as "rank_by column
'Capital Velocity Index' not found in results" -- true, but useless. Found
by actually driving the mismatch through `server.backtest.run_backtest`
(the real path a browser takes) rather than unit-testing the deep guard
alone. Fixed by adding the SAME check `build_config()` already performs
for `target_return`, catching it immediately with the real reason;
`tests/unit/test_ml_reachability_wiring.py` pins both the fix and (via
`run_sweep` directly) that the deeper guard still fires for callers that
bypass the API layer.

Also caught: the lazy-lightgbm-import guarantee (`server/app.py` imports
`backtest` -> `strategy_registry` UNCONDITIONALLY, so a module-level
`import lightgbm` in `reachability_sizing.py` would have crashed the
Pi's ENTIRE web container on startup, not just backtesting -- lightgbm
is never installed there). Verified by actually blocking `lightgbm`/
`sklearn` at import time and re-importing `server.app` fresh
(`tests/unit/test_ml_optional_dependency.py`), not by inspection.

`pytest tests/unit -q` -> **1890 passed, 1 skipped**. `npm run build`/`npm test` clean.
