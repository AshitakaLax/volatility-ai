# Algorithm research ledger

Every algorithm considered for volatility-ai's market-correction work, in
one place: what it is, where it came from, whether it fits the
constraints, what was built, what was measured, and what is still open.
Entries are recorded **regardless of merit** — a rejected idea with its
reason is worth as much as a promising one, because it stops the same
idea being re-researched.

*Compiled 2026-10-02. Covers patches 0001–0004 on top of `7961b1b`.*

---

## 1. How to read this ledger

### Objective and constraints (stated by the owner)

| | |
|---|---|
| **Objective** | Better return/drawdown during market corrections, judged on both. |
| **Instruments** | Buying and selling standard stocks and ETFs only. Leveraged long ETFs (TQQQ) are in. |
| **Out of scope** | Inverse ETFs, short selling, options, volatility ETFs (VIXY/UVXY), managed-futures ETFs (DBMF/KMLM). |
| **Loss policy** | A lot may be sold below cost **only** through a regime exit (`lots_to_liquidate` + `execution.allow_signal_exit`). No price stops, no end-of-day flatten. |

### Status legend

| Mark | Meaning |
|---|---|
| ✅ | Implemented in volatility-ai before this work |
| 🆕 | Implemented in patches 0001–0004 |
| 🔬 | Has a recorded measurement (read the caveats) |
| 🧪 | Implemented, not yet measured on real data |
| ⏳ | Candidate — fits the constraints, not implemented |
| ⛔ | Out of scope under the constraints above |
| ❌ | Rejected on evidence or mechanism |

### Two measurement caveats that apply to many entries

1. **Same-session regime flags (one-day lookahead).** The engine-stage
   harnesses behind `plan.md` (`tools/stage1_grid.py`, `stage2_grid.py`,
   `stage3_grid.py`, `stage4_leverage.py`, `probe_stage3_engine.py`) key
   each daily flag by the session it was computed from, and
   `IndicatorRegime` applies it at that same session's first bar. A
   session's own high, low and close were therefore known at its open.
   Verified directly (an alternating map is applied same-day). Every
   engine-stage regime number in `plan.md` carries this. **Patch 0004
   adds `--lag` to all five tools; 1 (causal) is now the default.**
2. **Intrabar booking and within-bar trigger.** Under
   `fill_model="intrabar"` the engine (a) booked fills at the order price
   even when the whole bar traded beyond it — 125 of 183 champion buys on
   a synthetic test were booked above their bar's high — and (b) let the
   champion's trigger level include the current bar's close before
   comparing it with that bar's low. Every recorded intrabar result
   carries both. **Patches 0003/0004 add `execution.intrabar_fill`:
   `level` (default, as recorded) → `open_or_level` (fixes a) → `causal`
   (fixes a and b).**

---

## 2. Summary

| ID | Algorithm | Source | Family | Status | Correction relevance |
|---|---|---|---|---|---|
| V1 | Fixed portfolio % sizing | volatility-ai | Grid sizing | ✅ | Baseline only |
| V2 | Bell-curve sizing | volatility-ai | Grid sizing | ✅ | Low |
| V3 | RSI momentum sizing | volatility-ai | Grid sizing | ✅ | Low |
| V4 | Bayesian dual-scale sizing | volatility-ai | Grid sizing | ✅ | Low |
| V5 | HF local-reference grid (champion) | volatility-ai | Grid | ✅🔬 | The book being protected |
| V6 | Event-day / earnings / weighted-event boosts | volatility-ai | Sizing lever | ✅ | Low |
| V7 | Vol-ratio scaling (fast/slow realized vol) | volatility-ai | Sizing lever | ✅🔬 | Medium |
| V8 | Volume scaling | volatility-ai | Sizing lever | ✅ | Low |
| V9 | Time-of-day scaling | volatility-ai | Sizing lever | ✅ | Low |
| V10 | Trailing profit target | volatility-ai | Exit | ✅ | Low |
| V11 | Drawdown throttle (`dd_throttle_*`) | volatility-ai | Sizing lever | ✅🧪 | **High** |
| V12 | Implied-vol scaling (VIXY as VXN proxy) | volatility-ai | Sizing lever | ✅🧪 | Medium |
| V13 | ML reachability sizing | volatility-ai | ML sizing | ✅🧪 | Medium |
| V14 | ML regime sizing (qlib) | volatility-ai | ML regime | ✅🧪 | Medium |
| V15 | TA-Lib indicator regime sweep | volatility-ai `plan.md` | Regime filter | ✅🔬⚠️ | **High** (needs causal re-run) |
| V16 | SMA200 / trend-line (LINEARREG) regime | volatility-ai `plan.md` | Regime filter | ✅🔬⚠️ | Medium |
| V17 | NATR-below regime, liquidate on flip | volatility-ai `plan.md` | Regime exit | ✅🔬⚠️ | **High** (lookahead) |
| V18 | Volatility targeting (RSP) | volatility-ai `plan.md` | Exposure scaling | ✅🔬 | **High** |
| V19 | Random-regime null control | volatility-ai `plan.md` | Validation | ✅🔬⚠️ | Validation |
| V20 | SQQQ grid | volatility-ai | Inverse grid | ❌⛔ | Rejected twice |
| N1 | Dual Thrust breakdown gate | quant-trading #7 | Entry gate | 🆕🧪 | Medium |
| N2 | Opening-range breakdown gate | quant-trading #4 | Entry gate | 🆕🧪 | Medium |
| N3 | Prior-session-low gap gate | London Breakout idea | Entry gate | 🆕🧪 | Medium–high |
| N4 | Shooting-star gate (causal) | quant-trading #17 | Entry gate | 🆕🧪 | Low–medium |
| N5 | Causal daily NATR regime | `plan.md` V17, fixed | Regime | 🆕 | **High** |
| N6 | Regime sleeves | this work | Book structure | 🆕🧪 | **High** |
| N7 | Leverage step-down (TQQQ calm / QQQ turbulent) | this work | Rotation | 🆕🧪 | **High** |
| N8 | `intrabar_fill` booking modes | this work | Engine | 🆕 | Measurement |
| N9 | Causal stage re-screen (`--lag`) | this work | Research tooling | 🆕 | **High** |
| Q1 | MACD oscillator | quant-trading #1 | Momentum | ⏳ (as regime) | Low |
| Q2 | Pair trading (long/short) | quant-trading #2 | Stat-arb | ⛔ | — |
| Q3 | Heikin-Ashi | quant-trading #3 | Trend | ⏳ (as regime) | Medium |
| Q4 | London Breakout (as a trade) | quant-trading #4 | Breakout | ⛔ (gate built) | — |
| Q5 | Awesome oscillator | quant-trading #5 | Momentum | ⏳ (as regime) | Low |
| Q6 | Oil Money | quant-trading #6 | FX/commodity | ❌ | None |
| Q7 | Dual Thrust (as a trade) | quant-trading #7 | Breakout | ⛔ (gate built) | — |
| Q8 | Parabolic SAR | quant-trading #8 | Trend | ⏳ (as regime) | Medium |
| Q9 | Bollinger W-bottom | quant-trading #9 | Mean reversion | ⏳ | Medium |
| Q10 | RSI pattern recognition | quant-trading #10 | Reversal | ⏳ (gate) | Low |
| Q11 | Monte Carlo project | quant-trading #11 | Simulation | ❌ (as signal) | None |
| Q12 | Options straddle | quant-trading #12 | Long vol | ⛔ | — |
| Q13 | Portfolio optimization project | quant-trading #13 | Allocation | ⏳ (later) | Medium |
| Q14 | Smart Farmers | quant-trading #14 | Commodity | ❌ | None |
| Q15 | VIX calculator | quant-trading #15 | Vol index | ⏳ (data tool) | Medium |
| Q16 | Wisdom of Crowds | quant-trading #16 | Sentiment | ❌ | Low |
| Q17 | Shooting star (as a trade) | quant-trading #17 | Reversal | ⛔ (gate built) | — |
| A1 | Deep RL agents (FinRL, DQN, PPO, DDQN, gyms) | awesome-ai-in-finance | RL | ❌ (for now) | Unknown |
| A2 | FinRL ensemble turbulence index | awesome-ai-in-finance (paper) | Regime exit | ⏳ | **High** |
| A3 | LPPLS / Dragon-Kings crash hazard | awesome-ai-in-finance (paper) | Crash forecast | ⏳ (research) | Medium |
| A4 | DL portfolio management (PGPortfolio, DeepDow, qtrader) | awesome-ai-in-finance | Allocation | ❌ (for now) | Low |
| A5 | skfolio / HRP allocation | awesome-ai-in-finance | Allocation | ⏳ (later) | Medium |
| A6 | HFT pairs with IB | awesome-ai-in-finance | Stat-arb | ⛔ | — |
| A7 | Crypto bots / arbitrage / blackbird | awesome-ai-in-finance | Crypto | ❌ | None |
| A8 | Pattern / forecasting libraries (mlforecast, patternity) | awesome-ai-in-finance | Forecasting | ❌ (for now) | Low |
| S1 | ThetaGang (wheel) | awesome-systematic-trading | Short options | ⛔❌ | Negative |
| S2 | PyTrendFollow | awesome-systematic-trading | Futures trend | ⛔ (idea → V16/Q8) | — |
| S3 | volest (Sinclair estimators, Yang-Zhang) | awesome-systematic-trading | Vol estimation | ⏳ | **High** |
| S4 | pysystemtrade (Carver vol targeting) | awesome-systematic-trading | Exposure scaling | ⏳ | **High** |
| S5 | czsc (Chan theory) | awesome-systematic-trading | Technical | ❌ (unvetted) | Unknown |
| X1 | Intraday momentum gate (Gao et al. 2018) | outside the lists | Entry gate | ⏳ | **High** |
| X2 | Defensive rotation (T-bills, XLP, XLU, USMV, SPLV) | this work | Rotation | ⏳ | Medium |
| X3 | Long-only relative-strength rotation | quant-trading #2, adapted | Rotation | ⏳ | Medium |
| X4 | Capitulation-bounce entries | quant-trading #9, adapted | Entry rule | ⏳ | Medium |
| X5 | Long Treasuries (TLT) as the hedge | this work | Rotation | ❌ | Failed 2022 |
| X6 | Inverse-ETF regime sleeve | this work | Inverse | ⛔ | — |
| X7 | Managed-futures ETF sleeve | this work | Crisis alpha | ⛔ | — |
| X8 | Long-volatility ETF sleeve (VIXY) | this work | Long vol | ⛔ | — |
| X9 | Gold (GLD) | this work | Rotation | ⏳ (low) | Low–medium |

---

## 3. Algorithms already in volatility-ai

### V1–V4. The original grid sizers

`fixed` (`FixedPortfolioPercentage`), `bell_curve`, `rsi`
(`RsiMomentumSizing`) and `bayesian_dual_scale` are the pre-champion
sizers in `research/strategies/size_calculators.py` and
`bayesian_sizing_calculators.py`. All buy on a pullback from a reference
and exit each lot at a fixed profit target under the no-loss guard;
they differ in how big each lot is. **Correction relevance: low** —
none changes exposure in response to a regime, so in a sustained
decline they keep accumulating lots that can only exit after recovery.
`fixed` is the regression-baseline strategy
(`tests/fixtures/regression_baseline.py`).

### V5. HF local-reference grid — the champion 🔬

`hf_local_reference`, `research/strategies/high_frequency_sizing.py`.
The reference a pullback is measured from is
`max(last_buy_price, rolling high over lookback_days)`, which lets a buy
retrigger on intraday chop instead of only at fresh multi-day lows.
Lots are a fixed dollar amount (`per_lot_pct` × starting capital), not a
fraction of current equity.

* **Best known:** `config/best_known_2026-08-24.yaml` — 25.38% CAGR,
  45.57% max drawdown, 86,087 trades (README). A retune reached 38.61%
  CAGR at 82.4% max drawdown; HF sweeps sit at 73–82% max drawdown
  across sweeps (module docstring).
* **Caveats:** measured under `intrabar_fill="level"` (both booking
  issues above apply), and through `run_hf_sweep.py`, which has never
  passed a YAML's `cash_yield_pct`, `allow_signal_exit` or
  `settlement_days` to the engine — so idle cash earned nothing in every
  recorded run.
* **Correction relevance:** it is the book a correction strategy
  protects. Its drawdown is the binding problem.

### V6–V12. Champion levers

| Lever | What it does | State |
|---|---|---|
| V6 event/earnings/weighted-event boosts | Larger lots on FOMC days, earnings days of top holdings, weighted event intensity | ✅ in champion config (2.5× / 1.5×) |
| V7 vol-ratio scaling | Lot × (fast/slow realized vol)^exponent, clamped | ✅ in champion (−1.5 exponent: smaller lots when vol spikes) |
| V8 volume scaling | Lot scaled by relative volume | ✅ in champion (−1.0) |
| V9 time-of-day | Lot scaled by the intraday volatility profile | ✅ available |
| V10 trailing target | Ratchets a lot's target behind a peak | ✅ available |
| V11 `dd_throttle_*` | Shrinks new lots as portfolio drawdown deepens, to a floor | ✅ **unmeasured** |
| V12 implied-vol scaling | Lot scaled by an implied-vol series; VXN unreachable, VIXY used as proxy | ✅ unmeasured |

**V11 is the most correction-relevant lever that already exists and has
never been measured.** Its docstring states the mechanism this whole
ledger is about: under the no-loss guard, every lot bought deep in a
decline needs a larger recovery to exit.

### V13. ML reachability sizing 🧪

`ml_reachability_{cowz,rsp,spyd}`. A model estimates whether a lot's
profit target is reachable and scales size accordingly. Unmeasured for
corrections; the per-ticker models do not include TQQQ.

### V14. ML regime sizing (qlib) 🧪

`ml_regime_{tqqq,qqq,rsp,soxl,sqqq,spyd,xbi,cowz,ursp}`,
`research/ml/regime_scaled_sizing.py`. Scales lot size by a learned
crash-risk regime. Its own docstring records the key lesson: ranking
crash risk only pays when the grid is actually trading into the crash,
and a ratchet-down trigger in a bull market never is. Unmeasured.

### V15. TA-Lib indicator regime sweep 🔬⚠️

`research/strategies/indicator_library.py` + `plan.md` Stages 1–4. Every
TA-Lib indicator turned into above/below-median regime flags, screened
for flip count, then run through the grid engine as in/out filters with
"liquidate" and "hold" exit policies.

* **Recorded headline:** nothing beats TQQQ buy-and-hold on raw return
  (39.15% CAGR, −81.68% max DD, ret/dd 0.479); liquidating on the flip
  is worse for return in 146 of 147 paired runs.
* **⚠️ Every engine-stage number here carries the same-session
  lookahead (caveat 1).** Re-run with `--lag 1` before drawing any
  conclusion — see N9.

### V16. SMA200 / trend-line regimes 🔬⚠️

From `plan.md`: SMA200 flips ~27 times over the sample; the TQQQ
trend-line (LINEARREG) family recorded 28.87% CAGR / −54.85% max DD
against buy-and-hold's 39.15% / −81.68% (Stage 3, reproduced to the
third decimal by a second implementation). Faster regime signals made
2022 worse (RSI(14) −65.7%). **⚠️ Same lookahead.** Correction
relevance medium: trend filters have the best long-horizon record in
sustained declines, but the grid pays for every flip in realized losses.

### V17. NATR-below regime, liquidate on flip 🔬⚠️

`plan.md`'s strongest result: NATR(10) below its 100-day median →
in-market; liquidate on the flip to "above".

| | CAGR | Max DD |
|---|---|---|
| NATR below, liquidate | 38.64% | 26.68% |
| Same signal, hold through | 38.38% | 69.38% |
| TQQQ buy-and-hold | 39.15% | 81.68% |

In market 54% of the time, 138 flips, ret/dd 1.448 against a 0.479 bar,
z = +11.99 over 30 random regimes. **⚠️ Measured with the one-day
lookahead:** a range-based signal that knows today's range at the open
liquidates on the morning of the crash day. A random regime has no such
foresight, which is one way a lookahead would surface as exactly this
z-score. **How much survives is the single most important open
measurement.** Causal version: N5.

### V18. Volatility targeting (RSP) 🔬

`plan.md`: volatility targeting on RSP cut drawdown 54%, where a trend
filter cost 5.7pp of CAGR to cut it 14pp — "direction is hard; magnitude
persists." Not yet applied to the TQQQ grid. See S4.

### V19. Random-regime null control 🔬⚠️

Markov regimes matched on in-market share and flip count, used to ask
whether a signal beats chance. Sound as a design; the comparison is
invalid while the real signal has foresight the null cannot have.
Re-run under `--lag 1`.

### V20. SQQQ grid ❌⛔

`ml_regime_sqqq` exists. `server/backtest.py` records that the SQQQ
sweep lost money in every one of 80 trials, with 9–28 stuck lots.
Excluded twice over: by evidence and by the no-inverse constraint.

---

## 4. Added in this work (patches 0001–0004)

### N1–N4. Entry-suppression gates 🆕🧪 (0001)

`research/strategies/entry_gates.py`, strategy `hf_entry_gated`
(`GatedLocalReferenceSizing`). A gate blocks **new** buys only; it never
sells, so it cannot realize a loss. Blocking is done through the trigger
*level*, because the intrabar fill path never calls
`_check_grid_trigger`. Decisions for bar t use bars before t plus bar
t's open.

| Gate | Level | Release |
|---|---|---|
| N1 `dual_thrust` | session open − k × max(HH−LC, HC−LL) over N sessions | `reclaim` (open back above) or `session` |
| N2 `opening_range` | low of the first N minutes | same |
| N3 `prior_low` | previous session's low — can fire on the first bar of a gap-down | same |
| N4 `shooting_star` | confirmed star on N-minute candles | after N candles, or an open above the star's high |

* **N4 fixes two lookaheads in the source script**: confirmation via
  `shift(-1)`, and body size against a full-sample signed mean.
* **Probes:** `config/probe_entry_gate_*.yaml` (control + 29 combos),
  `run_entry_gate_chain.sh` (`FILL=causal` for the corrected booking).
* **Known issue:** when a gate releases after a long block, the
  reference can be stale; read gate probes under `intrabar_fill=causal`.

### N5. Causal daily NATR regime 🆕 (0002)

`research/strategies/natr_regime.py`. The V17 signal with the flag from
the close of session D applied to D+1. NATR matches TA-Lib to 1e-10;
`lag=0` reproduces the stage harness map date for date, so `lag=1` is
provably the same signal shifted one session.

### N6. Regime sleeves 🆕🧪 (0002)

`research/strategies/regime_sleeve_sizing.py`. The gated champion,
active only in its regime (`calm` / `turbulent` / `always`), liquidating
its whole book on the bar the regime turns it off (edge-latched; needs
`allow_signal_exit`). Re-entry measures the first pullback from the
recent rolling high, not a stale pre-crash fill — without that, a
re-entering sleeve booked buys up to 734% above market on synthetic data.
Deliberately not registered: half of a two-instrument book.

### N7. Leverage step-down 🆕🧪 (0002)

`tools/leverage_stepdown.py`. TQQQ sleeve while calm + QQQ sleeve while
turbulent (step and target ÷ 3, same dollar lots: the same Nasdaq-100
moves at a third of the exposure), compared with TQQQ-calm-then-cash and
the champion. Each sleeve runs through the real engine; P&L is added —
exact for fixed-dollar lots, except where a sleeve was cash-constrained.
Defaults to `intrabar_fill=causal`. **Correction relevance high, but its
value depends on N5 surviving the causal re-measure.**

### N8. `execution.intrabar_fill` 🆕 (0003, 0004)

| Mode | Buy booked at | Sell booked at | Trigger level uses |
|---|---|---|---|
| `level` (default) | level | target | the current bar's close |
| `open_or_level` | min(level, open) | max(target, open) | the current bar's close |
| `causal` | min(level, open) | max(target, open) | bars before the current one |

Part of the result-cache identity and every result row;
`run_hf_sweep --intrabar-fill`, `analyze_annual` honors each row's mode.
`level → open_or_level` isolates the booking effect;
`open_or_level → causal` isolates the within-bar lookahead.

### N9. Causal re-screen tooling 🆕 (0004)

`--lag {0,1}` on `tools/stage1_grid.py`, `stage2_grid.py`,
`stage3_grid.py`, `stage4_leverage.py`, `probe_stage3_engine.py`;
default 1 (causal). `--lag 0` reproduces `plan.md`. Every regime family
in V15–V19 can now be re-measured without lookahead.

---

## 5. je-suis-tm/quant-trading (17 strategies)

### Q1. MACD oscillator ⏳ (as a regime only)
Long when a short moving average is above a long one. Momentum
crossover; whipsaws in range-bound markets. Already in the V15 sweep as
an in/out filter. As a trade it needs a short side for corrections. Next
step: causal re-screen (N9).

### Q2. Pair trading ⛔ (long/short) · see X3
Engle-Granger two-step cointegration on a rolling window, trading the
residual at ±1σ, exiting when cointegration breaks. The README itself
warns that cointegration breaks; correlations converge in sell-offs.
Requires a short leg — out of scope. Its relative-value logic survives
long-only as X3.

### Q3. Heikin-Ashi candlestick ⏳ (as a regime)
Smoothed candles; long on strong bullish candles with no lower shadow,
exit on reversal. Trend-following. Usable as a daily regime builder for
N6 sleeves. Weak prior from the trend family (V16), but that prior
carries the lookahead.

### Q4. London Breakout ⛔ (as a trade) · gate built (N2/N3)
Tokyo's last pre-open hour sets the range; trade the break in the first
minutes after London opens; skip abnormally large breaks; 50bp
stop/target; flat at session end. Needs stops and a short side. Mapped
onto US hours as the N2 and N3 gates.

### Q5. Awesome oscillator ⏳ (as a regime)
SMA(5) − SMA(34) of the median price, with "saucer" entries. MACD-like
momentum. Same treatment as Q1.

### Q6. Oil Money project ❌
Regression of the Norwegian krone on Brent crude — an FX/commodity
relationship. Not applicable to Nasdaq-100 ETFs.

### Q7. Dual Thrust ⛔ (as a trade) · gate built (N1)
Range = max(HH − LC, HC − LL) over N days; long above open + k₁·range,
short below open − k₂·range; reverse on cross; flat at the close. As a
trade it needs a short side and end-of-day flattening. The lower band is
the N1 gate.

### Q8. Parabolic SAR ⏳ (as a regime)
Stop-and-reverse trailing level with an accelerating factor. As a
TQQQ↔cash or TQQQ↔QQQ switch it fits N6 sleeves. Intraday whipsaw is
the main risk. In the V15 sweep as a filter only.

### Q9. Bollinger Bands pattern recognition ⏳ · see X4
Detects a W-bottom against the lower band, then a breakout. Mean
reversion after capitulation — the shape corrections produce. Candidate
entry rule for the turbulent sleeve (X4).

### Q10. RSI pattern recognition ⏳ (as a gate)
Overbought/oversold plus head-and-shoulders on the RSI line. As an
entry-suppression gate (no new buys after a bearish RSI pattern) it fits
the N1–N4 framework. Weak alone.

### Q11. Monte Carlo project ❌ (as a signal)
Simulated price paths (geometric Brownian motion) — a simulation study,
not a trading rule. Its role here would be validation, which
volatility-ai already covers with the random-regime null (V19).

### Q12. Options straddle ⛔
Long at-the-money call and put; pays on large moves either way.
Excluded (options). Would also need option chain data.

### Q13. Portfolio optimization project ⏳ (later) · see A5
Efficient-frontier allocation. Only meaningful once there is a
portfolio-level allocator over several sleeves.

### Q14. Smart Farmers project ❌
Agricultural/commodity quantamental study. Not applicable.

### Q15. VIX calculator ⏳ (as a data tool)
CBOE's VIX methodology from an option chain. Could compute the VXN
series V12 could not source, from Nasdaq-100 option quotes. A data tool,
not a strategy.

### Q16. Wisdom of Crowds project ❌
Aggregating crowd/analyst forecasts. Sentiment data pipelines are
explicitly ruled out by the repo's macro-signal tests.

### Q17. Shooting star ⛔ (as a trade) · gate built (N4)
Bearish reversal candle (small bearish body, long upper shadow, no lower
shadow, after a rise), confirmed by the next bar. As a short trigger it
is out of scope; as a no-buy gate it is N4. **The source script has two
lookaheads** (next-bar confirmation and a full-sample mean); N4 fixes
both.

---

## 6. georgezouq/awesome-ai-in-finance

### A1. Deep reinforcement-learning agents ❌ (for now)
FinRL, AutomatedStockTrading-DeepQ-Learning, tf_deep_rl_trader (PPO),
deep_rl_trader (DDQN), trading-rl (price trailing), trading-gym,
gym-trading, stock_market_reinforcement_learning, Deep-Reinforcement-
Stock-Trading. Policies learned from reward signals. Rejected for now:
far more free parameters than the repo's multiple-comparison discipline
can support, and few correction episodes in 10.6 years to learn from.
Revisit only after the simple regime work is settled.

### A2. Turbulence index (FinRL ensemble paper) ⏳ — high priority
"Deep Reinforcement Learning for Automated Stock Trading: An Ensemble
Strategy" (2020) stops trading when market turbulence — the Mahalanobis
distance of today's multi-asset returns from their history — exceeds a
threshold. Catches correlation breaks (stocks and bonds falling
together) that single-asset NATR cannot. **Fit:** builds a
`regime_by_date` map for N6 sleeves from daily closes of a basket
(QQQ, RSP, TLT, GLD) used as data only. **Next step:** a
`turbulence_regime.py` beside `natr_regime.py`, run through
`leverage_stepdown.py`.

### A3. LPPLS / Dragon-Kings crash hazard ⏳ (research-grade)
Sornette, "Dragon-Kings, Black Swans and the Prediction of Crises".
Fits a log-periodic power law to detect bubble dynamics ahead of a
crash. Daily-scale; too few correction events in the sample to validate
with any confidence.

### A4. Deep-learning portfolio management ❌ (for now)
PGPortfolio, DeepDow, qtrader, ml-quant-trading. Learned allocation
weights. Same objection as A1.

### A5. skfolio / hierarchical risk parity ⏳ (later)
Portfolio optimization on scikit-learn (HRP, risk budgeting). Needs the
portfolio allocator first; then a principled way to weight sleeves.

### A6. High-Frequency-Trading-Model-with-IB ⛔
Pairs trading through Interactive Brokers. Needs a short leg.

### A7. Crypto strategies and arbitrage ❌
LSTM crypto prediction, Gekko strategies, tforce_btc_trader, bitcoin
arbitrage detectors, blackbird (long/short crypto market-neutral). Wrong
asset class; arbitrage needs multiple venues and short legs.

### A8. Forecasting and pattern libraries ❌ (for now)
mlforecast, patternity, Quantium Research, Chaos Genius (anomaly
detection). Forecasting price direction is what `plan.md` found hardest;
magnitude-based approaches (S3, S4) are the better-supported direction.

---

## 7. wangzhe3224/awesome-systematic-trading

### S1. ThetaGang (the wheel) ⛔❌
Sells cash-secured puts and covered calls for premium. Excluded
(options), and short puts are the worst position to hold in a decline.

### S2. PyTrendFollow ⛔ (idea carried into V16/Q8)
Systematic futures trend following — the classic "crisis alpha"
strategy. Futures and shorts are out of scope; its long-only trend logic
is covered by V16/Q3/Q8 regime builders.

### S3. volest (Euan Sinclair's volatility estimators) ⏳ — high priority
Parkinson, Garman-Klass, Rogers-Satchell and **Yang-Zhang**, which
accounts for overnight gaps. Corrections begin with gaps that
close-to-close and intraday-range measures understate. **Fit:** a
drop-in estimator for N5 (a Yang-Zhang regime) and for S4.

### S4. pysystemtrade (Rob Carver) — volatility targeting ⏳ — high priority
Size positions by target volatility ÷ forecast volatility. Supported by
the repo's own V18 result. Unlike V7 (a *ratio* of fast to slow vol),
this targets an *absolute* level, so exposure falls as volatility rises
regardless of history. **Fit:** a sizing change only — never realizes a
loss. **Next step:** a `vol_target` lever on the champion using an S3
estimator; probe against V11.

### S5. czsc (Chan theory) ❌ (unvetted)
A Chinese technical-analysis framework (缠论). No published evidence base
to weigh; not pursued.

---

## 8. Proposed during this research (outside the linked lists)

### X1. Intraday-momentum gate ⏳ — high priority
Gao, Han, Li & Zhou, "Market Intraday Momentum" (Journal of Financial
Economics, 2018): the first half-hour's return predicts the last
half-hour's, more strongly on volatile days. Long-only form: block
late-session buys when the first half hour was down. **Fit:** an
N1–N4-style gate.

### X2. Defensive rotation ⏳
Move capital out of TQQQ on a regime exit into something that holds up:
* **T-bills (BIL, SHV, SGOV):** the only asset class that held up in
  both the March 2020 crash and the 2022 grind. Largely modeled already
  by the engine's historical money-market yield on idle cash — once
  `run_hf_sweep` passes `cash_yield_pct` through (see §9).
* **Defensive sectors / low volatility (XLP, XLU, USMV, SPLV):** held up
  in 2022, fell nearly as hard as the market in March 2020. Only with
  their own volatility gate.

### X3. Long-only relative-strength rotation ⏳
Q2's spread logic used to *choose* among QQQ, RSP, XLP and USMV rather
than to trade a long/short pair. Needs N7's harness generalized from two
sleeves to N with mutually exclusive regimes.

### X4. Capitulation-bounce entries ⏳
Q9's W-bottom as the entry rule for the turbulent sleeve: buy only after
a reversal confirms, rather than on every step down. Failed bounces wait
for the regime exit, so size small.

### X5. Long Treasuries (TLT) as the hedge ❌
Fell alongside stocks in 2022 — the longest correction in the dataset.
Usable as turbulence-index *data* (A2), not as a holding.

### X6. Inverse-ETF regime sleeve ⛔
Proposed early (the SQQQ grid run while the TQQQ grid is out). Excluded
by the no-inverse constraint, and V20 recorded losses in all 80 SQQQ
trials.

### X7. Managed-futures ETF sleeve ⛔
DBMF / KMLM hold trend positions internally, including shorts, and rose
in 2022. Excluded by the owner as not "standard" ETFs.

### X8. Long-volatility ETF sleeve ⛔
VIXY spike capture. Most convex payoff in fast crashes, heavy bleed
otherwise. Excluded by the owner. VIXY remains in use as V12's *data*.

### X9. Gold (GLD) ⏳ (low priority)
Roughly flat in 2022; no hedge in a fast crash. Low expected value as a
rotation target.

---

## 9. Engine and methodology findings

Problems found while researching the algorithms above. Each affects how
some recorded number should be read.

| Finding | Effect | State |
|---|---|---|
| Stage harnesses apply regime flags on their own session | One-day lookahead in V15–V19 | `--lag` added (0004), default causal; **re-measure needed** |
| Intrabar fills booked at the order price outside the bar's range | Mis-booked fills in every intrabar result | `intrabar_fill=open_or_level` (0003) |
| Champion's level includes the current bar's close | Within-bar lookahead under intrabar | `intrabar_fill=causal` (0004) |
| `run_hf_sweep` ignores YAML `cash_yield_pct`, `allow_signal_exit`, `settlement_days` | No interest on idle cash in any recorded run; YAML signal exits silently off | Made explicit, unchanged (0003); **decision open** |
| `analyze_annual` hardcoded the strategy class | Gated rows would re-simulate as the champion | Fixed (0001) |
| `analyze_annual` hardcoded the booking | Year-by-year in a different booking from the headline | Fixed (0003) |
| `intraday_validation.py` computes the trigger inline | Legacy finalist re-check ignores every strategy's level | Flagged, not changed |
| Shooting-star reference script lookahead | Next-bar confirm + full-sample mean | Fixed in N4 |
| README runs scripts by path | Fails without the repo root on `PYTHONPATH`; `python -m` works | Flagged |
| `run_hf_sweep` leaderboard hid swept columns | Rows differing only in an unlisted parameter printed as identical | Fixed (0001) |

---

## 10. Run book

```bash
# Bookings: recorded -> booking fixed -> booking + within-bar fixed
for f in level open_or_level causal; do
  python -m research.run_hf_sweep --config config/best_known_2026-08-24.yaml \
      --search grid --intrabar-fill $f --output output/champion_$f.csv
done                                    # 'level' should reproduce 25.38%

# Causal re-screen of plan.md (lag 1 is the default; lag 0 reproduces it)
python -m tools.probe_stage3_engine --lag 0 --out output/stage3_engine_lag0.csv
python -m tools.probe_stage3_engine --lag 1 --out output/stage3_engine_lag1.csv
python -m tools.stage1_grid --lag 1 --out output/stage1_grid_lag1.jsonl

# Leverage step-down, and the size of the NATR lookahead
python -m tools.leverage_stepdown                # causal booking, lag 1
python -m tools.leverage_stepdown --lag 0        # same-session reading

# Entry gates under the corrected booking
FILL=causal bash run_entry_gate_chain.sh
```

---

## 11. Next actions, in order

1. **Re-measure V17 causally** (`probe_stage3_engine --lag 1`,
   `leverage_stepdown` at lag 0 vs 1). Everything in N5–N7 depends on it.
2. **Champion under all three bookings** — sizes the two intrabar
   issues on real data.
3. **Causal re-screen of V15** with `stage1_grid --lag 1` onward — a
   trustworthy list of regime builders.
4. **Measure V11 `dd_throttle`** — the existing, unmeasured
   correction lever.
5. **Build S4 + S3** (volatility targeting with a Yang-Zhang estimator).
6. **Build A2** (turbulence regime) as a second regime source for N6.
7. **Build X1** (intraday-momentum gate).
8. **Decide the `run_hf_sweep` cash-yield threading** — changes every
   result, so do it once, deliberately, with a re-baselined champion.
9. Then X3/X4, and only after a portfolio allocator exists, Q13/A5.
