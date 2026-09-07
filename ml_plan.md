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
