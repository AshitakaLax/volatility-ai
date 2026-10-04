# Algorithm research ledger

Every algorithm considered for volatility-ai's market-correction work, in
one place: what it is, where it came from, whether it fits the
constraints, what was built, what was measured, and what is still open.
Entries are recorded **regardless of merit** — a rejected idea with its
reason is worth as much as a promising one, because it stops the same
idea being re-researched.

*Compiled 2026-10-02. Covers patches 0001–0006 on top of `7961b1b`. Section 8A (2026-10-03) adds the
records of `docs/research/correction-strategies.md`; 🧪 entries there
were built the same day. Section 8B (2026-10-03) adds `research/catalog/`,
code for every remaining entry, in-scope or not.*

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

The marks describe fit with the platform. Since section 8B, ⛔ and ❌
entries also have reference code in `research/catalog/`, unwired.

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
| Q1 | MACD oscillator | quant-trading #1 | Momentum | 🆕🧪 (regime) | Low |
| Q2 | Pair trading (long/short) | quant-trading #2 | Stat-arb | ⛔ | — |
| Q3 | Heikin-Ashi | quant-trading #3 | Trend | 🆕🧪 (regime) | Medium |
| Q4 | London Breakout (as a trade) | quant-trading #4 | Breakout | ⛔ (gate built) | — |
| Q5 | Awesome oscillator | quant-trading #5 | Momentum | 🆕🧪 (regime) | Low |
| Q6 | Oil Money | quant-trading #6 | FX/commodity | ❌ | None |
| Q7 | Dual Thrust (as a trade) | quant-trading #7 | Breakout | ⛔ (gate built) | — |
| Q8 | Parabolic SAR | quant-trading #8 | Trend | 🆕🧪 (regime) | Medium |
| Q9 | Bollinger W-bottom | quant-trading #9 | Mean reversion | 🆕🧪 (entry rule) | Medium |
| Q10 | RSI pattern recognition | quant-trading #10 | Reversal | 🆕🧪 (gate) | Low |
| Q11 | Monte Carlo project | quant-trading #11 | Simulation | ❌ (as signal) | None |
| Q12 | Options straddle | quant-trading #12 | Long vol | ⛔ | — |
| Q13 | Portfolio optimization project | quant-trading #13 | Allocation | 🆕🧪 (HRP) | Medium |
| Q14 | Smart Farmers | quant-trading #14 | Commodity | ❌ | None |
| Q15 | VIX calculator | quant-trading #15 | Vol index | 🆕 (data tool) | Medium |
| Q16 | Wisdom of Crowds | quant-trading #16 | Sentiment | ❌ | Low |
| Q17 | Shooting star (as a trade) | quant-trading #17 | Reversal | ⛔ (gate built) | — |
| A1 | Deep RL agents (FinRL, DQN, PPO, DDQN, gyms) | awesome-ai-in-finance | RL | ❌ (for now) | Unknown |
| A2 | FinRL ensemble turbulence index | awesome-ai-in-finance (paper) | Regime exit | 🆕🧪 | **High** |
| A3 | LPPLS / Dragon-Kings crash hazard | awesome-ai-in-finance (paper) | Crash forecast | 🆕🧪 (research) | Medium |
| A4 | DL portfolio management (PGPortfolio, DeepDow, qtrader) | awesome-ai-in-finance | Allocation | ❌ (for now) | Low |
| A5 | skfolio / HRP allocation | awesome-ai-in-finance | Allocation | 🆕🧪 | Medium |
| A6 | HFT pairs with IB | awesome-ai-in-finance | Stat-arb | ⛔ | — |
| A7 | Crypto bots / arbitrage / blackbird | awesome-ai-in-finance | Crypto | ❌ | None |
| A8 | Pattern / forecasting libraries (mlforecast, patternity) | awesome-ai-in-finance | Forecasting | ❌ (for now) | Low |
| S1 | ThetaGang (wheel) | awesome-systematic-trading | Short options | ⛔❌ | Negative |
| S2 | PyTrendFollow | awesome-systematic-trading | Futures trend | ⛔ (idea → V16/Q8) | — |
| S3 | volest (Sinclair estimators, Yang-Zhang) | awesome-systematic-trading | Vol estimation | 🆕 | **High** |
| S4 | pysystemtrade (Carver vol targeting) | awesome-systematic-trading | Exposure scaling | 🆕🧪 | **High** |
| S5 | czsc (Chan theory) | awesome-systematic-trading | Technical | ❌ (unvetted) | Unknown |
| X1 | Intraday momentum gate (Gao et al. 2018) | outside the lists | Entry gate | 🆕🧪 | **High** |
| X2 | Defensive rotation (T-bills, XLP, XLU, USMV, SPLV) | this work | Rotation | 🆕🧪 | Medium |
| X3 | Long-only relative-strength rotation | quant-trading #2, adapted | Rotation | 🆕🧪 | Medium |
| X4 | Capitulation-bounce entries | quant-trading #9, adapted | Entry rule | 🆕🧪 | Medium |
| X5 | Long Treasuries (TLT) as the hedge | this work | Rotation | ❌ | Failed 2022 |
| X6 | Inverse-ETF regime sleeve | this work | Inverse | ⛔ | — |
| X7 | Managed-futures ETF sleeve | this work | Crisis alpha | ⛔ | — |
| X8 | Long-volatility ETF sleeve (VIXY) | this work | Long vol | ⛔ | — |
| X9 | Gold (GLD) | this work | Rotation | 🆕🧪 | Low–medium |
| C-MR1 | Short-term reversal as paid liquidity provision (VIX-conditioned) | Nagel 2012; Collin-Dufresne & Daniel | Mean reversion | 🧪 | Medium |
| C-MR2 | ETF-residual Ornstein-Uhlenbeck stat arb (s-score) | Avellaneda & Lee 2010 | Stat arb | 🧪 | Low–medium |
| C-MR4 | Mean-reversion diagnostics: ADF, Hurst exponent, variance ratio, OU half-life | letianzj/QuantResearch | Regime filter | 🧪 | Medium |
| C-MR7 | R-Breaker pivot reversal and breakout | letianzj/QuantResearch (R-Breaker) | Reversal / breakout | 🧪 | Low–medium |
| C-M1 | Noise-Area intraday momentum ("Beat the Market", Concretum Bands) | Zarattini, Aziz & Barbon 2024 | Intraday momentum | 🧪 | High |
| C-M2 | Five-minute opening range breakout (ORB) on QQQ/TQQQ and "Stocks in Play" | Zarattini & Aziz 2023; Zarattini, Barbon & Aziz 2024 | Breakout | ⛔ (as published) | Low–medium |
| C-G2 | Inventory-skewed grid (Avellaneda-Stoikov reservation price) | hftbacktest; Avellaneda & Stoikov 2008 | Grid | 🧪 | High |
| C-G3 | Volatility-scaled grid ("simplified GLFT") | hftbacktest (simplified GLFT) | Grid | 🧪 | High |
| C-G4 | Dynamic grid reset (DGT) | Chen, Chen & Jang 2025 | Grid lifecycle | 🧪 | Low–medium |
| C-G5 | Turtle ATR-unit pyramiding (scale in on strength) | letianzj/QuantResearch; huseinzol05 | Scale-in sizing | 🧪 (scale-in) · ⛔ (stop) | Medium |
| C-G6 | Grid ruin analysis with absorbing barriers | Taranto & Khan 2020 | Risk analysis | 🧪 | Medium–high |
| C-MM1 | Avellaneda-Stoikov optimal quotes | Avellaneda & Stoikov 2008 | Market making | 🧪 (buy side) | Medium–high |
| C-MM2 | Guéant-Lehalle-Fernandez-Tapia (GLFT) closed-form quotes | Guéant 2017 via hftbacktest | Market making | 🧪 (needs L1) | Medium |
| C-MM3 | Alpha-shifted quoting (fair value = mid + a × forecast) | hftbacktest | Market making | 🧪 | Medium–high |
| C-MM4 | VPIN flow-toxicity filter | Easley, López de Prado & O'Hara 2012 | Microstructure regime | 🧪 (needs trades) | Medium |
| C-MM5 | Probabilistic queue-position fill models | hftbacktest | Execution model | 🧪 (needs L2) | Measurement |
| C-R3 | Hidden Markov, Gaussian-mixture and Markov-switching volatility regimes | letianzj/QuantResearch | Regime | 🧪 | Medium–high |
| C-ML1 | Triple-barrier and trend-scanning labels | ML4T ch. 7; Advanced-Deep-Trading | ML labelling | 🧪 | Medium |
| C-ML3 | Purged k-fold, embargo and combinatorial purged CV (CPCV) | eslazarev/purged-cross-validation | Validation | 🧪 | Validation |
| C-ML4 | Deflated Sharpe ratio and probability of backtest overfitting | Bailey & López de Prado 2014; Bailey et al. | Validation | 🧪 | Validation |
| C-ML5 | Information-driven bars and fractional differentiation | Advanced-Deep-Trading; ML4T ch. 3 | Data preparation | 🧪 | Low–medium |
| C-RL4 | Deep recurrent Q-network with action augmentation | Huang 2018 | Reinforcement learning | ❌ (for now) | Low |
| C-RL5 | Direct reinforcement with a risk-adjusted online reward | Moody & Saffell 2001 | Reinforcement learning | ❌ (for now) | Low–medium |
| C-S2 | Kelly and fractional Kelly | deltaray-io/kelly-criterion; riskkit; ML4T ch. 17 | Position sizing | 🧪 | Medium |
| C-S4 | Inventory-capped inverse-exposure sizing | hftbacktest; riskkit | Position sizing | 🧪 | High |
| C-X2 | Time-limit and end-of-day exits | charlieyanhx/exitkit; M1/M2 papers | Exit | ⛔ (loss-realizing) · 🧪 (profit-only) | Low |
| C-X4 | Session caps and cooldowns on new lots | riskkit (SessionManager) | Risk throttle | 🧪 | Medium–high |
| C-MS1 | Order-flow imbalance (OFI) at the best bid and ask | Cont, Kukanov & Stoikov 2014 | Microstructure | 🧪 (needs L1) | Medium |
| C-MS2 | Order-book imbalance and micro-price | hftbacktest | Microstructure | 🧪 (needs L2) | Medium |
| C-MS3 | VWAP-relative gating | Zarattini, Aziz & Barbon 2024 (VWAP) | Intraday gate | 🧪 | High |
| C-MS5 | Bar-only microstructure proxies | twowaymind/orderflow-metrics | Microstructure | 🧪 | Measurement |
| C-MS6 | Leveraged-ETF end-of-day rebalancing flow | Cheng & Madhavan 2009; Ivanov & Lenkey 2018 | Hypothesis | 🧪 | Low |
| C-MS7 | Market profile and volume profile | letianzj/QuantResearch | Rung placement | 🧪 | Low–medium |
| C-E2 | Tactical asset allocation with moving-average filters | letianzj/QuantResearch (Faber TAA) | Rotation / parking | 🧪 | Low–medium |
| C-E4 | Regime-aware risk for concentrated mega-cap exposure | paperswithbacktest/awesome-systematic-trading | Regime | ⏳ (unverified) | Unknown |
| C-RJ1 | Dealer gamma-imbalance signals | Baltussen et al. 2021, cited in M1 | Rejected in catalog | ⛔ | — |
| C-RJ2 | Funding-rate arbitrage; perpetual-futures scanners | ML4T crypto-perps case study; crypto entries in awesome-quant and awesome-ai-in-finance | Rejected in catalog | ❌ | — |
| C-RJ3 | Martingale / averaging-down sizing | binary-martingale in awesome-quant | Rejected in catalog | ❌ | — |
| C-RJ4 | 18 deep sequence forecasters and stacked ensembles | huseinzol05/Stock-Prediction-Models | Rejected in catalog | ❌ | — |
| C-RJ5 | Ghost Trader | letianzj/QuantResearch | Rejected in catalog | ❌ | — |
| C-RJ6 | Index/ETF creation-redemption arbitrage | the research brief | Rejected in catalog | ⛔ | — |
| C-RJ7 | LLM agent frameworks (TradingAgents, FinRobot and similar) | curated lists | Rejected in catalog | ❌ | — |
| C-RJ8 | Novelty strategies (tweet-driven trading, lottery prediction) | awesome-ai-in-finance | Rejected in catalog | ❌ | — |

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


### N10. Regime minimum hold (`debounce`) 🆕 (0006)
`natr_regime.debounce`: once a regime flips, it holds for at least
`min_hold` sessions. Causal. Every flip liquidates the outgoing sleeve,
and `plan.md` found liquidation costs return in 146 of 147 paired runs,
so fast regimes pay on every whipsaw. `--min-hold N` on both harnesses,
for every regime.

### N11. Rotation harness 🆕🧪 (0006)
`tools/rotation.py` — X2, X3 and A5 (with X9) through the same sleeve
machinery and additive account as N7, sharing its regime options. Writes
the session-by-session holding alongside the summary.

---

## 5. je-suis-tm/quant-trading (17 strategies)

### Q1. MACD oscillator 🆕🧪 (as a regime)
Long when a short moving average is above a long one — momentum
crossover; whipsaws in range-bound markets. As a trade it needs a short
side for corrections; as a regime it does not.
**Built (0006):** `research/strategies/trend_regimes.py`, a daily
risk-on map — `--regime macd` on `tools/leverage_stepdown.py` and
`tools/rotation.py`, lagged one session like every other regime.
MACD line (EMA 12 − EMA 26) above its 9-period signal line; pinned to that definition. Unmeasured.

### Q2. Pair trading ⛔ (long/short) · see X3
Engle-Granger two-step cointegration on a rolling window, trading the
residual at ±1σ, exiting when cointegration breaks. The README itself
warns that cointegration breaks; correlations converge in sell-offs.
Requires a short leg — out of scope. Its relative-value logic survives
long-only as X3.

### Q3. Heikin-Ashi candlestick 🆕🧪 (as a regime)
Smoothed candles; long on strong bullish candles, exit on reversal.
**Built (0006):** `research/strategies/trend_regimes.py`, a daily
risk-on map — `--regime heikin_ashi` on `tools/leverage_stepdown.py` and
`tools/rotation.py`, lagged one session like every other regime.
Risk-on after `confirm` consecutive bullish Heikin-Ashi candles, off after as many bearish; a single opposite candle is ignored at confirm > 1 (tested). Unmeasured.

### Q4. London Breakout ⛔ (as a trade) · gate built (N2/N3)
Tokyo's last pre-open hour sets the range; trade the break in the first
minutes after London opens; skip abnormally large breaks; 50bp
stop/target; flat at session end. Needs stops and a short side. Mapped
onto US hours as the N2 and N3 gates.

### Q5. Awesome oscillator 🆕🧪 (as a regime)
SMA(5) − SMA(34) of the median price (H+L)/2, MACD-like momentum. The
source's "saucer" entries need a short side; the zero line does not.
**Built (0006):** `research/strategies/trend_regimes.py`, a daily
risk-on map — `--regime awesome` on `tools/leverage_stepdown.py` and
`tools/rotation.py`, lagged one session like every other regime.
Risk-on while the oscillator is above zero; pinned to the definition. Unmeasured.

### Q6. Oil Money project ❌
Regression of the Norwegian krone on Brent crude — an FX/commodity
relationship. Not applicable to Nasdaq-100 ETFs.

### Q7. Dual Thrust ⛔ (as a trade) · gate built (N1)
Range = max(HH − LC, HC − LL) over N days; long above open + k₁·range,
short below open − k₂·range; reverse on cross; flat at the close. As a
trade it needs a short side and end-of-day flattening. The lower band is
the N1 gate.

### Q8. Parabolic SAR 🆕🧪 (as a regime)
Wilder's stop-and-reverse trailing level with an accelerating factor
(0.02 step, 0.2 cap).
**Built (0006):** `research/strategies/trend_regimes.py`, a daily
risk-on map — `--regime psar` on `tools/leverage_stepdown.py` and
`tools/rotation.py`, lagged one session like every other regime.
Risk-on in the rising phase; agrees with TA-Lib's SAR on the trend side on more than 95% of sessions (tested — the two differ only in how the first trend is seeded). Unmeasured.

### Q9. Bollinger Bands pattern recognition 🆕🧪 (entry rule) · see X4
Detects a W-bottom against the lower band, then a breakout. **Built
(0006)** as `entry_gates.BollingerWGate` — a *permission* gate (buys
only after a confirmed W) — on `hf_entry_gated` (`bounce_gate=w_bottom`)
and as `tools/leverage_stepdown.py --qqq-entry w_bottom`. Unmeasured.

### Q10. RSI pattern recognition 🆕🧪 (as a gate)
Overbought/oversold plus head-and-shoulders on the RSI line. **Built
(0006)** as `entry_gates.RsiHeadShouldersGate` on `hf_entry_gated`
(`rsi_gate=head_shoulders`): Wilder RSI on N-minute candles (matches
TA-Lib's RSI to 1e-9); three swing highs with an overbought head and
shoulders within `rsi_tolerance` points; buys stop for
`rsi_hold_candles` once the RSI closes below the neckline. Probe:
`config/probe_entry_gate_rsi_head_shoulders.yaml` (4 combinations), in
the gate chain. Unmeasured.

### Q11. Monte Carlo project ❌ (as a signal)
Simulated price paths (geometric Brownian motion) — a simulation study,
not a trading rule. Its role here would be validation, which
volatility-ai already covers with the random-regime null (V19).

### Q12. Options straddle ⛔
Long at-the-money call and put; pays on large moves either way.
Excluded (options). Would also need option chain data.

### Q13. Portfolio optimization project 🆕🧪 (as HRP) · see A5
Efficient-frontier allocation in the source. Built as hierarchical risk
parity instead (A5), which needs no expected-return estimates — the
weakest input of a mean-variance optimiser.

### Q14. Smart Farmers project ❌
Agricultural/commodity quantamental study. Not applicable.

### Q15. VIX calculator 🆕 (as a data tool)
**Built (0006):** `research/strategies/vix_calculator.py` — the CBOE
methodology (forward from put-call parity, out-of-the-money strip, the
two-zero-bid cutoff, 30-day interpolation). Returns 25.0 ± 0.4 on a
flat-25%-volatility Black-Scholes chain (tested). With Nasdaq-100 or QQQ
option quotes it can supply the VXN series V12 could not source.
Ingesting option quotes is not built.

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

### A2. Turbulence index (FinRL ensemble paper) 🆕🧪 (0005)
"Deep Reinforcement Learning for Automated Stock Trading: An Ensemble
Strategy" (2020) stops trading when market turbulence crosses a
threshold. The index (Kritzman & Li) is the Mahalanobis distance of a
day's basket returns from the mean and covariance of the previous
`lookback` days. It catches correlation breaks that single-asset NATR
cannot: in the tests, two negatively correlated assets both falling
1.5% score more than three times a same-sized move in their usual
pattern.

* **Built:** `research/strategies/turbulence_regime.py`. Calm while the
  index is below its trailing `quantile` (default 0.9 over 252
  sessions), applied to the next session (lag 1, via `apply_lag`). The
  basket is data only; nothing in it is traded.
* **Use:** `python -m tools.leverage_stepdown --regime turbulence
  --basket QQQ RSP TLT GLD` — every basket member must be ingested.
* **Shape:** ~90% of sessions are calm by construction, so the QQQ
  sleeve runs only in the turbulent tail — a different book from the
  NATR regime, which is calm 54% of the time.
* **Unmeasured.**

### A3. LPPLS / Dragon-Kings crash hazard 🆕🧪 (research-grade)
Sornette, "Dragon-Kings, Black Swans and the Prediction of Crises".
**Built (0006):** `research/strategies/lppls.py`. Filimonov–Sornette
linearisation with a (tc, m, ω) grid — NumPy only. A window is a
positive bubble when B < 0, 0.1 ≤ m ≤ 0.9, 6 ≤ ω ≤ 13, tc within 40
sessions and damping ≥ 0.5; confidence is the share of windows (60–250
sessions) that are. Recovers a planted bubble exactly and scores random
walks low (tested). `--regime lppls` (risk-on below `--lppls-threshold`,
re-fitted every `--lppls-step` sessions). Still research-grade: too few
correction episodes in 10.6 years to validate.

### A4. Deep-learning portfolio management ❌ (for now)
PGPortfolio, DeepDow, qtrader, ml-quant-trading. Learned allocation
weights. Same objection as A1.

### A5. skfolio / hierarchical risk parity 🆕🧪
**Built (0006):** `research/strategies/hrp.py` — López de Prado's HRP,
NumPy only, allocating along the dendrogram so a duplicated asset cannot
double its weight (tested), and inverse-variance for two independent
assets (tested). Used by `tools/rotation.py --mode hrp` to size
concurrent sleeves from weights fitted on the warm-up only. Concurrent
sleeves stretch the additive-account approximation: total deployed
capital can exceed one account's. Unmeasured.

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

### S3. volest (Euan Sinclair's volatility estimators) 🆕 (0005)
`research/strategies/volatility_estimators.py`: close-to-close,
Parkinson, Garman-Klass, Rogers-Satchell and Yang-Zhang, each pinned to
its textbook formula. Yang-Zhang is the default because corrections
arrive overnight: in a market whose every move is an overnight gap, the
three range estimators read exactly zero, while Yang-Zhang reads what
close-to-close does (pinned in the tests). `SessionVolatility` estimates
from completed sessions only and equals the vectorized reference one
session late. Used by S4; also a candidate replacement for NATR in a
regime builder.

### S4. pysystemtrade (Rob Carver) — volatility targeting 🆕🧪 (0005)
On `hf_entry_gated`: lot × clamp(`vol_target` / realized vol,
`vol_target_min`, `vol_target_max`), realized vol over the last
`vol_target_days` completed sessions (S3; Yang-Zhang by default).
Neutral (×1) until the window fills — no estimate is not a low one.
Supported by the repo's V18 result. Unlike V7 (a fast/slow *ratio*,
which drifts back to 1 during a sustained high-volatility correction),
this targets an absolute level. A sizing change only, so it cannot
realize a loss. Through the real controller it scales buys only after
its window fills (tested under both fill models).

* **Probe:** `config/probe_vol_target.yaml` — targets 0.45/0.60/0.75 ×
  10/20 sessions × Yang-Zhang vs close-to-close (12 combinations).
* **Unmeasured.** Compare with V11 `dd_throttle`, the other exposure
  lever.

### S5. czsc (Chan theory) ❌ (unvetted)
A Chinese technical-analysis framework (缠论). No published evidence base
to weigh; not pursued.

---

## 8. Proposed during this research (outside the linked lists)

### X1. Intraday-momentum gate 🆕🧪 (0005)
Gao, Han, Li & Zhou, "Market Intraday Momentum" (Journal of Financial
Economics, 2018): the return from the previous close to the end of the
first half hour predicts the last half hour's, more strongly on volatile
days. `momentum_gate="early_negative"` on `hf_entry_gated`
(`entry_gates.IntradayMomentumGate`) blocks buys in the last
`momentum_late_minutes` of a session whose first `momentum_early_minutes`
closed below the previous close by more than `momentum_threshold`.

* Known at the start of the first bar after the early window, from that
  window's last close; clears at the session end; inert on half-days.
* Through the real controller it removes exactly the late-window buys
  and changes nothing before them (tested under both fill models).
* **Probe:** `config/probe_entry_gate_intraday_momentum.yaml` (4
  combinations), included in `run_entry_gate_chain.sh`.
* **Unmeasured.**

### X2. Defensive rotation 🆕🧪
**Built (0006):** `tools/rotation.py --mode defensive`. The lead (TQQQ)
while any regime is risk-on; otherwise the `--defensive` ETF (default
XLP, XLU, USMV, GLD) with the best trailing return **among those whose
own NATR regime is calm** — the guard against March 2020, when
defensives fell with the market; none calm → cash at the configured
cash yield (T-bills, in effect). Grid step and target are scaled by each
instrument's warm-up daily range. Unmeasured.

### X3. Long-only relative-strength rotation 🆕🧪
**Built (0006):** `tools/rotation.py --mode relative_strength` — dual
momentum over `--universe` (default QQQ, RSP, XLP, USMV): best trailing
`--rs-days` return, cash when even the best is negative. Every choice
uses closes through the previous session (pinned against mutation).
Unmeasured.

### X4. Capitulation-bounce entries 🆕🧪
**Built (0006)** as Q9's W-bottom permission gate; for the turbulent
QQQ sleeve: `tools/leverage_stepdown.py --qqq-entry w_bottom`. Failed
bounces still wait for the regime exit, so lots stay small. Unmeasured.

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

### X9. Gold (GLD) 🆕🧪 (as a defensive candidate)
Roughly flat in 2022; no hedge in a fast crash. Included in X2's default
`--defensive` list, where its own NATR regime must be calm before it is
held. Low expected value.

---

## 8A. Research catalog additions (`docs/research/correction-strategies.md`)

[`docs/research/correction-strategies.md`](research/correction-strategies.md)
(Oct 3, 2026) catalogs 66 algorithm records mined from 17 repositories
and lists plus 18 papers, judged against the same constraints as this
ledger. Records already covered by an entry above are mapped in the
cross-reference table below; the rest are recorded here. Their IDs are
the catalog's own with a `C-` prefix, because the catalog reuses S and
X numbers that mean other things in this ledger (its S4 is
inventory-capped sizing, this ledger's S4 is volatility targeting).

Each entry gives the source and links to the full record in the
catalog (role, parameters, data, evidence quality, failure modes).
Statuses apply this ledger's constraints. Entries marked 🧪 were
built on 2026-10-03 as standalone research modules, each with unit
tests pinned to its source's definitions (the Built line names them);
none is wired into a strategy, the engine host or a harness yet, and
none has been run on market data. The catalog's own
[ranked shortlist](research/correction-strategies.md#ranked-shortlist-and-implementation-order)
proposes a build order (sizing and regime exits first); it is not
merged into section 11.

### C-MR1. Short-term reversal as paid liquidity provision (VIX-conditioned) 🧪
Buying recent losers earns a liquidity-provision premium that rises with the VIX; the counter-study finds the Sharpe ratio no better once the strategy's own volatility is controlled.

* **Fit:** Long-only basket form only. The grid is already a liquidity provider, so the transferable lesson is to widen spacing and shrink lots with realized volatility (C-G3, S4) rather than switch off. Daily, long-short evidence.
* **Built:** `research/strategies/mean_reversion.py` — contrarian_weights, decayed_reversal_scores.
* **Source:** Nagel, "Evaporating Liquidity", Review of Financial Studies 25(7), 2012 ([NBER w17653](https://nber.org/papers/w17653)); Collin-Dufresne & Daniel, "Liquidity and Return Reversals", working paper, 2014 ([PDF](https://business.columbia.edu/sites/default/files-efs/pubfiles/11568/str1.pdf)).
* **Details:** [catalog MR1](research/correction-strategies.md#mr1-short-term-reversal-as-paid-liquidity-provision-vix-conditioned)

### C-MR2. ETF-residual Ornstein-Uhlenbeck stat arb (s-score) 🧪
Ornstein-Uhlenbeck model of a stock's cumulative residual against its sector ETF; long below s = −1.25, exit above −0.50.

* **Fit:** Short side dropped (⛔). The long-only form is net long and needs a regime gate; it picks single stocks, not the TQQQ book. Daily evidence.
* **Built:** `research/strategies/mean_reversion.py` — s_score, s_score_long_signal.
* **Source:** Avellaneda & Lee, "Statistical Arbitrage in the US Equities Market", Quantitative Finance 10(7), 2010 ([PDF](https://traders.berkeley.edu/papers/Statistical%20arbitrage%20in%20the%20US%20equities%20market.pdf), [abstract](https://cims.nyu.edu/ams/abstracts/avellaneda.html)); thresholds confirmed in [Avellaneda's lecture slides](https://math.nyu.edu/inmemoriam/avellaneda/Lecture8Risk2011.pdf).
* **Details:** [catalog MR2](research/correction-strategies.md#mr2-etf-residual-ornstein-uhlenbeck-stat-arb-s-score)

### C-MR4. Mean-reversion diagnostics: ADF, Hurst exponent, variance ratio, OU half-life 🧪
Rolling ADF, Hurst exponent, variance ratio and OU half-life classify the tape as mean-reverting or trending; run the grid dense in the first state and wide or paused in the second.

* **Fit:** Fits: changes spacing and pausing only, never sells. No trading backtest in the source.
* **Built:** `research/strategies/mean_reversion.py` — adf, hurst_exponent, variance_ratio, half_life.
* **Source:** [letianzj/QuantResearch, notebooks/mean\_reversion.py](https://github.com/letianzj/QuantResearch/blob/master/notebooks/mean_reversion.py).
* **Details:** [catalog MR4](research/correction-strategies.md#mr4-mean-reversion-diagnostics-adf-hurst-exponent-variance-ratio-ou-half-life)

### C-MR7. R-Breaker pivot reversal and breakout 🧪
Prior-day pivots P, R1–R3, S1–S3; a reversal buy when the day's low pierces S2 and price recovers above S1.

* **Fit:** Usable as the condition for re-opening grid buys on a correction day; the breakout and short legs are not needed. Code only, no results.
* **Built:** `research/strategies/intraday_gates.py` — RBreakerGate, r_breaker_levels.
* **Source:** [letianzj/QuantResearch, backtest/r\_breaker.py](https://github.com/letianzj/QuantResearch) (credits Richard Saidenberg, 1994).
* **Details:** [catalog MR7](research/correction-strategies.md#mr7-r-breaker-pivot-reversal-and-breakout)

### C-M1. Noise-Area intraday momentum ("Beat the Market", Concretum Bands) 🧪
Minute-of-day noise bands from the last 14 sessions; long above the upper band, exit below max(band, VWAP), flat at the close, volatility-scaled shares. Sharpe rose with the VIX and returns were positive in each of the ten worst S&P 500 quarters since 2008.

* **Fit:** As a gate on grid buys (pause while below the band) it fits the rules (catalog rank 7). As a sleeve, its band/VWAP exit and end-of-day flatten can realize losses, which the loss policy forbids unless reclassified — an open question in the catalog. Reported results include short trades.
* **Built:** `research/strategies/intraday_gates.py` — NoiseAreaGate, noise_bounds (gate form).
* **Source:** Zarattini, Aziz, Barbon, "Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)", SFI Research Paper 24-97, 2024 ([paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content), [IDEAS](https://ideas.repec.org/p/chf/rpseri/rp2497.html)).
* **Details:** [catalog M1](research/correction-strategies.md#m1-noise-area-intraday-momentum-beat-the-market-concretum-bands)

### C-M2. Five-minute opening range breakout (ORB) on QQQ/TQQQ and "Stocks in Play" ⛔ (as published)
Buy if the first 5-minute bar closes up, exit at the close or an ATR stop; the Stocks-in-Play variant trades the highest relative-volume names.

* **Fit:** The published form needs a price stop, a short side and an end-of-day exit, all out of scope; a long-only, no-stop version is untested. The breakdown side already exists as the N2 gate.
* **Source:** Zarattini & Aziz, "Can Day Trading Really Be Profitable?", 2023 ([SSRN 4416622](https://papers.ssrn.com/abstract=4416622)); Zarattini, Barbon & Aziz, "A Profitable Day Trading Strategy for the U.S. Equity Market", 2024 ([SSRN 4729284](https://ssrn.com/abstract=4729284)); rule summary by [CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy).
* **Details:** [catalog M2](research/correction-strategies.md#m2-five-minute-opening-range-breakout-orb-on-qqqtqqq-and-stocks-in-play)

### C-G2. Inventory-skewed grid (Avellaneda-Stoikov reservation price) 🧪
Centre the grid on a reservation price, mid − skew × position, so buy rungs move lower and thin out as inventory grows.

* **Fit:** Fits on the buy side only: sell rungs cannot move below each lot's cost. Catalog rank 2, with C-S4.
* **Built:** `research/strategies/inventory_control.py` — skewed_depths, inventory_skewed_level.
* **Source:** [hftbacktest tutorial (skew section)](https://hftbacktest.readthedocs.io/en/latest/tutorials/High-Frequency%20Grid%20Trading.html); model from [Avellaneda & Stoikov 2008](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf) as linked in the tutorial code.
* **Details:** [catalog G2](research/correction-strategies.md#g2-inventory-skewed-grid-avellaneda-stoikov-reservation-price)

### C-G3. Volatility-scaled grid ("simplified GLFT") 🧪
Grid step, half-spread and skew proportional to short-term volatility, with a minimum step; centred on the micro-price.

* **Fit:** Fits directly, and is distinct from V7 and S4, which scale lot size: the champion's step is fixed. Catalog rank 1, with S1/S4. The volatility part works on minute bars; micro-price centring needs L1 sizes.
* **Built:** `research/strategies/grid_spacing.py` — VolatilityScaledStep, step_series, volatility_scaled_step.
* **Source:** [hftbacktest tutorial: Grid Trading — Simplified from GLFT](https://hftbacktest.readthedocs.io/en/latest/tutorials/High-Frequency%20Grid%20Trading%20-%20Simplified%20from%20GLFT.html).
* **Details:** [catalog G3](research/correction-strategies.md#g3-volatility-scaled-grid-simplified-glft)

### C-G4. Dynamic grid reset (DGT) 🧪
Re-centre the whole grid on the current price whenever price leaves its range, instead of stopping; the paper argues a static finite grid has roughly zero expected value.

* **Fit:** Compatible with the no-loss ledger, but a downside reset adds rungs below held lots, which is averaging down; pair it with C-G2/C-G3 and a regime exit. Crypto-only evidence.
* **Built:** `research/strategies/grid_lifecycle.py` — DynamicGrid, geometric_levels.
* **Source:** Chen, Chen & Jang, "Dynamic Grid Trading Strategy: From Zero Expectation to Market Outperformance", 2025 ([arXiv 2506.11921](https://arxiv.org/abs/2506.11921v1), [IDEAS](https://ideas.repec.org/p/arx/papers/2506.11921.html)).
* **Details:** [catalog G4](research/correction-strategies.md#g4-dynamic-grid-reset-dgt)

### C-G5. Turtle ATR-unit pyramiding (scale in on strength) 🧪 (scale-in) · ⛔ (stop)
Turtle units: one ATR-sized unit per +0.5 ATR, up to three adds, after a 20-day high.

* **Fit:** Useful as a recovery-mode rebuild of TQQQ inventory after a regime exit, buying confirmation rather than the low. Its 2-ATR price stop is out of scope. Code only.
* **Built:** `research/strategies/position_sizing.py` — TurtlePyramid, turtle_atr, turtle_unit_shares (scale-in only).
* **Source:** [letianzj/QuantResearch, backtest/turtle.py](https://github.com/letianzj/QuantResearch); turtle agent in [huseinzol05/Stock-Prediction-Models](https://github.com/huseinzol05/Stock-Prediction-Models).
* **Details:** [catalog G5](research/correction-strategies.md#g5-turtle-atr-unit-pyramiding-scale-in-on-strength)

### C-G6. Grid ruin analysis with absorbing barriers 🧪
The grid as a random walk between two absorbing barriers, capital exhaustion and a profit target, giving the probability of hitting each for a chosen depth and spacing.

* **Fit:** An analysis tool rather than a rule: size a correction sleeve so a −30% TQQQ leg cannot exhaust capital before a regime exit fires. Theoretical; abstract only.
* **Built:** `research/strategies/grid_lifecycle.py` — target_first_probability, ruin_probability, expected_steps, rungs_for_decline.
* **Source:** Taranto & Khan, "Bi-directional grid absorption barrier constrained stochastic processes with applications in finance and investment", 2020 ([USQ repository listing](https://research.usq.edu.au/item/q5x8w/bi-directional-grid-absorption-barrier-constrained-stochastic-processes-with-applications-in-finance-and-investment)); I saw only the listing and abstract.
* **Details:** [catalog G6](research/correction-strategies.md#g6-grid-ruin-analysis-with-absorbing-barriers)

### C-MM1. Avellaneda-Stoikov optimal quotes 🧪 (buy side)
Reservation price r = mid − q·γ·σ²·(T−t) and an optimal spread that widens with volatility and with lower order-arrival intensity.

* **Fit:** Long-only, buy-side use: lower and thin buy rungs as lots accumulate; asks stay at or above cost. Calibrating arrival intensity needs L1 quotes and trades.
* **Built:** `research/strategies/inventory_control.py` — as_reservation_price, as_optimal_spread, as_quotes.
* **Source:** [Avellaneda & Stoikov paper](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf) as linked in the hftbacktest grid code.
* **Details:** [catalog MM1](research/correction-strategies.md#mm1-avellaneda-stoikov-optimal-quotes)

### C-MM2. Guéant-Lehalle-Fernandez-Tapia (GLFT) closed-form quotes 🧪 (needs L1)
Closed-form bid and ask depths from risk aversion, volatility and a fitted arrival intensity λ = A·exp(−k·δ), with no terminal time.

* **Fit:** The most principled spacing model (catalog rank 14), but minute bars cannot calibrate A and k: it needs trade prints and L1 quotes.
* **Built:** `research/strategies/inventory_control.py` — glft_coefficients, glft_quotes, fit_arrival_intensity.
* **Source:** [hftbacktest tutorial: GLFT Market Making Model and Grid Trading](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html), implementing equations 4.6–4.7 of Guéant, "Optimal market making" ([arXiv 1605.01862](https://arxiv.org/abs/1605.01862)).
* **Details:** [catalog MM2](research/correction-strategies.md#mm2-guéant-lehalle-fernandez-tapia-glft-closed-form-quotes)

### C-MM3. Alpha-shifted quoting (fair value = mid + a × forecast) 🧪
Fair value = mid + a × forecast − an inventory-risk term; a negative forecast lowers bids instead of switching the grid off.

* **Fit:** The cleanest way to merge a momentum signal (X1, C-M1) into the grid without a hard gate. Crypto tutorials only.
* **Built:** `research/strategies/inventory_control.py` — alpha_shifted_quotes.
* **Source:** [hftbacktest README quick example](https://github.com/nkaz001/hftbacktest); [Market Making with Alpha — Order Book Imbalance](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html).
* **Details:** [catalog MM3](research/correction-strategies.md#mm3-alpha-shifted-quoting-fair-value--mid--a--forecast)

### C-MM4. VPIN flow-toxicity filter 🧪 (needs trades)
VPIN: volume-bucketed order-flow imbalance; high readings mean liquidity providers are being adversely selected.

* **Fit:** A bid-side gate only. Disputed: Andersen & Bondarenko find the bar-level (bulk-classified) version adds nothing beyond volume and volatility, and that is the only version minute bars allow.
* **Built:** `research/strategies/microstructure.py` — vpin, volume_buckets.
* **Source:** Easley, López de Prado & O'Hara, "Flow Toxicity and Liquidity in a High Frequency World", Review of Financial Studies 25(5), 2012 ([SSRN 1695596](https://papers.ssrn.com/abstract=1695596)); critique by Andersen & Bondarenko ([CREATES paper](https://repec.econ.au.dk/repec/creates/rp/13/rp13_43.pdf)); rejoinder in Journal of Financial Markets 17, 2014 ([record](https://opus.lib.uts.edu.au/citation/handle/10453/118180)).
* **Details:** [catalog MM4](research/correction-strategies.md#mm4-vpin-flow-toxicity-filter)

### C-MM5. Probabilistic queue-position fill models 🧪 (needs L2)
Probabilistic queue-position models: a resting order fills only after the queue ahead of it clears, so backtests stop assuming every touch fills.

* **Fit:** Bears on N8's booking question: touch fills overstate grid profits, most of all in fast selloffs. Not possible with minute bars.
* **Built:** `research/strategies/microstructure.py` — QueuePositionEstimator.
* **Source:** [hftbacktest tutorial: Probability Queue Models](https://github.com/nkaz001/hftbacktest/blob/master/examples/Probability%20Queue%20Models.ipynb).
* **Details:** [catalog MM5](research/correction-strategies.md#mm5-probabilistic-queue-position-fill-models)

### C-R3. Hidden Markov, Gaussian-mixture and Markov-switching volatility regimes 🧪
Two or three hidden states fitted to returns (HMM, Gaussian mixture, Markov switching); trade the grid fully in the calm state and thin it in the turbulent one.

* **Fit:** Good as a sizing input; as an exit it needs hysteresis (compare N10). The source notebooks fit and decode on the full sample (lookahead) and invert their return formula, so they cannot be reused as they stand.
* **Built:** `research/strategies/regime_models.py` — GaussianHMM, GaussianMixture, causal_turbulence.
* **Source:** [letianzj/QuantResearch notebooks #12 (hidden\_markov\_chain.py) and #18 (gaussian\_mixture\_markov\_switching.ipynb)](https://github.com/letianzj/QuantResearch).
* **Details:** [catalog R3](research/correction-strategies.md#r3-hidden-markov-gaussian-mixture-and-markov-switching-volatility-regimes)

### C-ML1. Triple-barrier and trend-scanning labels 🧪
Triple-barrier labels: each entry labelled by the first barrier hit — profit target, lower barrier or time limit — plus trend-scanning labels.

* **Fit:** Maps one-to-one onto lots: upper barrier = take-profit, lower = regime-exit level, vertical = maximum hold. Training input for meta-label sizing (catalog rank 10; compare V13).
* **Built:** `research/ml/barrier_labels.py` — triple_barrier_labels, trend_scanning_labels.
* **Source:** [stefan-jansen/machine-learning-for-trading, chapter 7](https://github.com/stefan-jansen/machine-learning-for-trading) (forward-return, triple-barrier and trend-scanning labels); [Rachnog/Advanced-Deep-Trading, bars-labels-diff/Labeling.ipynb](https://github.com/Rachnog/Advanced-Deep-Trading).
* **Details:** [catalog ML1](research/correction-strategies.md#ml1-triple-barrier-and-trend-scanning-labels)

### C-ML3. Purged k-fold, embargo and combinatorial purged CV (CPCV) 🧪
Purged k-fold, embargo and combinatorial purged cross-validation: drop training rows whose label horizons overlap the test fold, skip a buffer after it, and recombine folds into many backtest paths.

* **Fit:** For every parameter of a correction sleeve, especially regime thresholds. Complements the walk-forward runner and the random-regime null (V19).
* **Built:** `research/optimization/purged_cv.py` — purged_kfold, combinatorial_purged_splits, n_backtest_paths.
* **Source:** [eslazarev/purged-cross-validation](https://github.com/eslazarev/purged-cross-validation) (pip `purgedcv`, scikit-learn compatible, active as of Oct 2026); [Advanced-Deep-Trading, proba\_backtest/Combinatorial Cross Validation.ipynb](https://github.com/Rachnog/Advanced-Deep-Trading).
* **Details:** [catalog ML3](research/correction-strategies.md#ml3-purged-k-fold-embargo-and-combinatorial-purged-cv-cpcv)

### C-ML4. Deflated Sharpe ratio and probability of backtest overfitting 🧪
Deflated Sharpe ratio (corrects a Sharpe for the number of trials, skew and kurtosis) and probability of backtest overfitting (how often the in-sample winner ranks below median out of sample).

* **Fit:** The catalog asks for DSR/PBO scoring of every sweep before its rank 1, and the sweeps recorded in this ledger (V15, the HF retunes) are exactly the many-trial case it corrects.
* **Built:** `research/optimization/overfitting.py` — probabilistic_sharpe, deflated_sharpe, probability_of_backtest_overfitting.
* **Source:** Bailey & López de Prado, "The Deflated Sharpe Ratio", Journal of Portfolio Management 40(5), 2014 ([SSRN 2460551](https://papers.ssrn.com/abstract=2460551)); Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting", Journal of Computational Finance 20(4) ([SSRN 2326253](https://papers.ssrn.com/abstract=2326253)); [Advanced-Deep-Trading, backtest\_veroft/Overfit Probability.ipynb](https://github.com/Rachnog/Advanced-Deep-Trading).
* **Details:** [catalog ML4](research/correction-strategies.md#ml4-deflated-sharpe-ratio-and-probability-of-backtest-overfitting)

### C-ML5. Information-driven bars and fractional differentiation 🧪
Information-driven bars (volume, dollar or imbalance sampling instead of clock time) and fractional differentiation (stationary prices that keep memory).

* **Fit:** Activity-based bars raise resolution exactly during selloffs; minute bars with volume approximate them.
* **Built:** `research/ml/info_bars.py` — tick/volume/dollar/tick-imbalance bars, frac_diff_ffd.
* **Source:** [Advanced-Deep-Trading, bars-labels-diff](https://github.com/Rachnog/Advanced-Deep-Trading); [ML4T chapter 3](https://github.com/stefan-jansen/machine-learning-for-trading) (bar-sampling comparison); [twowaymind/orderflow-metrics](https://github.com/twowaymind/orderflow-metrics).
* **Details:** [catalog ML5](research/correction-strategies.md#ml5-information-driven-bars-and-fractional-differentiation)

### C-RL4. Deep recurrent Q-network with action augmentation ❌ (for now)
Deep recurrent Q-network with action augmentation: a small trader does not move prices, so every action's reward is computable at each step and random exploration is unnecessary.

* **Fit:** Not pursued, for A1's reason. If RL is revisited, the augmentation idea could score every candidate lot size at historical grid triggers. FX-only preprint.
* **Source:** Huang, "Financial Trading as a Game: A Deep Reinforcement Learning Approach", 2018 ([arXiv 1807.02787](https://arxiv.org/abs/1807.02787v1)).
* **Details:** [catalog RL4](research/correction-strategies.md#rl4-deep-recurrent-q-network-with-action-augmentation)

### C-RL5. Direct reinforcement with a risk-adjusted online reward ❌ (for now)
Direct reinforcement: optimise trading decisions directly against an incrementally updated risk-adjusted measure instead of forecasting prices.

* **Fit:** Not pursued, for A1's reason, but the reward idea carries over: any learned sizing policy should optimise return/drawdown, this ledger's objective.
* **Source:** Moody & Saffell, "Learning to trade via direct reinforcement", IEEE Transactions on Neural Networks 12, 2001 (cited in the RL1 paper); "Reinforcement Learning for Trading" ([NIPS paper link](http://papers.nips.cc/paper/1551-reinforcement-learning-for-trading.pdf)) and Ritter, "Machine Learning for Trading" ([PDF](https://cims.nyu.edu/~ritter/ritter2017machine.pdf)), both listed in awesome-ai-in-finance. I did not open these.
* **Details:** [catalog RL5](research/correction-strategies.md#rl5-direct-reinforcement-with-a-risk-adjusted-online-reward)

### C-S2. Kelly and fractional Kelly 🧪
Kelly leverage f = mean excess return / variance; fractional Kelly trades growth for much lower drawdown; long-only clips negative f to zero.

* **Fit:** As a ceiling on total sleeve exposure, not per lot; TQQQ's 3× can exceed what a full-Kelly estimate on QQQ supports.
* **Built:** `research/strategies/position_sizing.py` — kelly_leverage, kelly_portfolio, kelly_growth_rate.
* **Source:** [deltaray-io/kelly-criterion](https://github.com/deltaray-io/kelly-criterion) (Python 2.7; no commits since Feb 2019, unmaintained); half-Kelly ceiling in [riskkit](https://github.com/HasibVortex369/riskkit); Kelly and conformal sizing in [ML4T chapter 17](https://github.com/stefan-jansen/machine-learning-for-trading).
* **Details:** [catalog S2](research/correction-strategies.md#s2-kelly-and-fractional-kelly)

### C-S4. Inventory-capped inverse-exposure sizing 🧪
Inventory-capped inverse-exposure sizing: lot size decays as open lots or open notional rise, under hard caps on total open notional and heat.

* **Fit:** The sizing-engine form of C-G2 (catalog rank 2) and the cheapest way to make a correction consume capital slowly. The engine's RiskManager already has hard caps (`max_concurrent_lots`, `max_total_exposure`); the decaying lot size is the new part.
* **Built:** `research/strategies/inventory_control.py` — inventory_decay_multiplier, inventory_capped_lot.
* **Source:** Skew mechanism in the [hftbacktest grid tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/High-Frequency%20Grid%20Trading.html); portfolio caps (open notional, heat, sector) in [riskkit](https://github.com/HasibVortex369/riskkit).
* **Details:** [catalog S4](research/correction-strategies.md#s4-inventory-capped-inverse-exposure-sizing)

### C-X2. Time-limit and end-of-day exits ⛔ (loss-realizing) · 🧪 (profit-only)
Time-limit and end-of-day exits: close after a fixed holding period or at the session close, regardless of P&L.

* **Fit:** Conflicts with the loss policy (no end-of-day flatten; losses only through regime exits) unless reclassified, an open question in the catalog. A profit-only variant fits. Anecdotal evidence.
* **Built:** `research/strategies/grid_lifecycle.py` — profit_only_time_exits (profit-only variant, through the no-loss guard).
* **Source:** [charlieyanhx/exitkit](https://github.com/charlieyanhx/exitkit) (27 exit models in 6 families; last commit Sep 2026); M1 and M2 papers for end-of-day flattening.
* **Details:** [catalog X2](research/correction-strategies.md#x2-time-limit-and-end-of-day-exits)

### C-X4. Session caps and cooldowns on new lots 🧪
Session caps and cooldowns: cap new lots per day, enforce minimum time between fills, and escalate cooldowns after runs of adverse fills.

* **Fit:** Throttles buys only (catalog rank 9, with V9). Pairs with X1: defer buys on strongly negative mornings.
* **Built:** `research/strategies/intraday_gates.py` — SessionLotThrottle.
* **Source:** SessionManager in [riskkit](https://github.com/HasibVortex369/riskkit).
* **Details:** [catalog X4](research/correction-strategies.md#x4-session-caps-and-cooldowns-on-new-lots)

### C-MS1. Order-flow imbalance (OFI) at the best bid and ask 🧪 (needs L1)
Order-flow imbalance at the touch: signed bid/ask size and price changes; short-interval price changes are roughly linear in OFI.

* **Fit:** Hold back a grid bid while OFI is strongly negative. Needs quote updates, and the relation is contemporaneous, so forecasting value must be tested separately.
* **Built:** `research/strategies/microstructure.py` — ofi, ofi_events.
* **Source:** Cont, Kukanov & Stoikov, "The Price Impact of Order Book Events", Journal of Financial Econometrics 12(1), 2014 ([arXiv 1011.6402](https://arxiv.org/abs/1011.6402)); implementation in [twowaymind/orderflow-metrics](https://github.com/twowaymind/orderflow-metrics).
* **Details:** [catalog MS1](research/correction-strategies.md#ms1-order-flow-imbalance-ofi-at-the-best-bid-and-ask)

### C-MS2. Order-book imbalance and micro-price 🧪 (needs L2)
Standardised order-book imbalance near the mid, and the micro-price (each side weighted by the other's size).

* **Fit:** A fair-value shift for grid quotes (feeds C-MM3). L1 sizes suffice for the micro-price; the imbalance needs depth.
* **Built:** `research/strategies/microstructure.py` — micro_price, depth_imbalance, standardized.
* **Source:** [hftbacktest tutorial: Market Making with Alpha — Order Book Imbalance](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html).
* **Details:** [catalog MS2](research/correction-strategies.md#ms2-order-book-imbalance-and-micro-price)

### C-MS3. VWAP-relative gating 🧪
VWAP-relative gating: add lots only when price is below VWAP by k·σ, and pause when it is far below and still falling.

* **Fit:** Catalog rank 7, with C-M1. Minute bars with volume suffice, and as a gate it needs no price stop.
* **Built:** `research/strategies/intraday_gates.py` — VwapGate, session_vwap.
* **Source:** M1 paper ([PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)), which cites Zarattini & Aziz, "Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems", SSRN 2023 (not opened).
* **Details:** [catalog MS3](research/correction-strategies.md#ms3-vwap-relative-gating)

### C-MS5. Bar-only microstructure proxies 🧪
Bar-only proxies: effective-spread, volatility and jump estimators from OHLC, and bar-volume buy/sell classification.

* **Fit:** Mainly realistic cost and fill assumptions for grid backtests when only minute bars exist.
* **Built:** `research/strategies/microstructure.py` — roll_spread, corwin_schultz, abdi_ranaldo, amihud_illiquidity, kyle_lambda, bvc_buy_fraction.
* **Source:** [twowaymind/orderflow-metrics](https://github.com/twowaymind/orderflow-metrics) (Python and TypeScript; last commit Sep 2026).
* **Details:** [catalog MS5](research/correction-strategies.md#ms5-bar-only-microstructure-proxies)

### C-MS6. Leveraged-ETF end-of-day rebalancing flow 🧪
Daily-reset leveraged ETFs must trade with the day's move near the close.

* **Fit:** Contested: Ivanov & Lenkey find fund flows offset most of it. At most a reason to avoid buying in the last 30 minutes of large down days, which X1 already covers.
* **Built:** `research/strategies/microstructure.py` — letf_rebalance_demand.
* **Source:** Cheng & Madhavan, "The Dynamics of Leveraged and Inverse ETFs", Journal of Investment Management 2009 ([PDF](https://joim.com/wp-content/uploads/emember/downloads/p0283.pdf)); Ivanov & Lenkey, "Do leveraged ETFs really amplify late-day returns and volatility?", Journal of Financial Markets 41, 2018 ([record](https://pure.psu.edu/en/publications/do-leveraged-etfs-really-amplify-late-day-returns-and-volatility/)); Lenkey's [literature survey](https://www.aimspress.com/article/id/676a38d5ba35de0ad141c3c3).
* **Details:** [catalog MS6](research/correction-strategies.md#ms6-leveraged-etf-end-of-day-rebalancing-flow)

### C-MS7. Market profile and volume profile 🧪
Market and volume profile: the volume-at-price histogram, whose point of control and value-area edges act as reaction levels.

* **Fit:** Snap grid rungs to high-volume nodes instead of a uniform ladder. Code and blog only.
* **Built:** `research/strategies/microstructure.py` — volume_profile, tpo_profile, point_of_control, value_area.
* **Source:** [letianzj/QuantResearch, market/market\_profile.ipynb (#25)](https://github.com/letianzj/QuantResearch).
* **Details:** [catalog MS7](research/correction-strategies.md#ms7-market-profile-and-volume-profile)

### C-E2. Tactical asset allocation with moving-average filters 🧪
Tactical asset allocation: hold each asset-class ETF only while it is above its long moving average, otherwise cash.

* **Fit:** A parking rule for idle correction-sleeve capital; compare X2, which gates each defensive ETF on its own NATR regime. Code only.
* **Built:** `research/strategies/tactical_allocation.py` — faber_targets, held_weights.
* **Source:** [letianzj/QuantResearch, backtest/mebane\_faber\_taa.py](https://github.com/letianzj/QuantResearch); the original Faber paper was not opened.
* **Details:** [catalog E2](research/correction-strategies.md#e2-tactical-asset-allocation-with-moving-average-filters)

### C-E4. Regime-aware risk for concentrated mega-cap exposure ⏳ (unverified)
A listed replication on regime-aware risk management in portfolios concentrated in the Magnificent Seven.

* **Fit:** Only the title and summary statistics were seen; kept for follow-up because the Nasdaq-100 is concentrated in a few mega-caps.
* **Source:** [paperswithbacktest/awesome-systematic-trading, Multi-asset table](https://github.com/paperswithbacktest/awesome-systematic-trading) (Sharpe 1.11, t-stat 6.4, 33 years, gross of costs).
* **Details:** [catalog E4](research/correction-strategies.md#e4-regime-aware-risk-for-concentrated-mega-cap-exposure)

### Catalog records already in this ledger

| Catalog record | Ledger entry | Note |
|---|---|---|
| [MR3. Cointegration pairs (Engle-Granger) and Kalman-filter hedge ratio](research/correction-strategies.md#mr3-cointegration-pairs-engle-granger-and-kalman-filter-hedge-ratio) | Q2, X3 | Pair trading is Q2 (short leg ⛔); its long-only rotation form is X3. The Kalman-filter hedge ratio is not built. **Built:** Engle-Granger test and the notebook's Kalman hedge ratio, long-only signal (`research/strategies/pairs.py`). |
| [MR5. Bollinger Band reversion and W-bottom](research/correction-strategies.md#mr5-bollinger-band-reversion-and-w-bottom) | Q9, X4 | The W-bottom permission gate is built; using band width as rung spacing is C-G3's idea. |
| [MR6. RSI oversold/overbought and RSI head-and-shoulders](research/correction-strategies.md#mr6-rsi-oversoldoverbought-and-rsi-head-and-shoulders) | V3, Q10 | RSI sizing (V3) and the RSI head-and-shoulders gate (Q10). The catalog adds that a low prior-day RSI(5) predicts stickier intraday trends (C-M1): widen rungs when oversold. |
| [MR8. Beta and volatility-ratio pairs (IB high-frequency model)](research/correction-strategies.md#mr8-beta-and-volatility-ratio-pairs-ib-high-frequency-model) | A6 | Same source. The catalog's long-only form (buy A only when cheap to β × B) is not built. |
| [M3. Market intraday momentum (first half-hour predicts last half-hour)](research/correction-strategies.md#m3-market-intraday-momentum-first-half-hour-predicts-last-half-hour) | X1 | Same paper (Gao, Han, Li & Zhou 2018). Catalog rank 6. |
| [M4. Dual Thrust](research/correction-strategies.md#m4-dual-thrust) | Q7, N1 | The lower band is the N1 gate; the trade itself is ⛔. |
| [M5. London Breakout (pre-open range breakout)](research/correction-strategies.md#m5-london-breakout-pre-open-range-breakout) | Q4, N2, N3 | Mapped onto US hours as the N2/N3 gates; the trade is ⛔. |
| [M6. Parabolic SAR](research/correction-strategies.md#m6-parabolic-sar) | Q8 | Built as a regime. The catalog's use, a profit-only trailing exit for lots past target, is not built (compare V10). **Built:** profit-only PSAR exit through the no-loss guard (`grid_lifecycle.psar_profit_exits`). |
| [M7. Heikin-Ashi trend filter](research/correction-strategies.md#m7-heikin-ashi-trend-filter) | Q3 |  |
| [M8. MACD and Awesome Oscillator crossovers](research/correction-strategies.md#m8-macd-and-awesome-oscillator-crossovers) | Q1, Q5 |  |
| [G1. Plain high-frequency grid](research/correction-strategies.md#g1-plain-high-frequency-grid) | V5 | The champion is the plain HF grid, with sell rungs only for lots whose target is above cost. |
| [R1. Moving-average leverage regime ("Leverage for the Long Run")](research/correction-strategies.md#r1-moving-average-leverage-regime-leverage-for-the-long-run) | V16 | Same idea (SMA200 leverage switch); the catalog's source is Gayed & Bilello, "Leverage for the Long Run". plan.md's measurement carries the same-session lookahead, and SMA is not yet a `--regime` option on N7/N11. Catalog rank 3. **Built:** `--regime sma` on N7/N11 (`trend_regimes.sma_risk_on`, 200-day default). |
| [R2. Financial turbulence index liquidation rule](research/correction-strategies.md#r2-financial-turbulence-index-liquidation-rule) | A2 | Catalog rank 4; also RL1's turbulence override. |
| [R4. Realized-volatility, ATR and VIX-level gates](research/correction-strategies.md#r4-realized-volatility-atr-and-vix-level-gates) | V17/N5, V7, V12 | NATR (ATR) regime and realized/implied-vol scaling exist. A VIX-level gate is not built: the VIX is not ingested. **Built:** VIX bands (`research/strategies/vix_bands.py`); the VIX series is in data/external/ after the ML input fetch. |
| [R5. Drawdown-state regimes](research/correction-strategies.md#r5-drawdown-state-regimes) | V11 | The throttle exists (unmeasured). The catalog's final tier, halting new lots or liquidating as a regime exit, is not built. Catalog rank 5, with S3 below. **Built:** tiered ladder with a halt tier, hysteresis and a liquidation request (`position_sizing.DrawdownLadder`). |
| [R6. LPPLS bubble and critical-time detection](research/correction-strategies.md#r6-lppls-bubble-and-critical-time-detection) | A3 |  |
| [ML2. Meta-labeling the grid's own triggers](research/correction-strategies.md#ml2-meta-labeling-the-grids-own-triggers) | V13 | V13's model scores whether a lot's target is reachable and scales its size, which is meta-labelling the grid's own triggers. The catalog's version adds triple-barrier labels (C-ML1) and DSR/PBO validation (C-ML4). |
| [ML6. Gradient boosting on intraday microstructure features](research/correction-strategies.md#ml6-gradient-boosting-on-intraday-microstructure-features) | V13, V14 | Both are LightGBM on bar-local and volatility features. |
| [RL1. Turbulence-gated actor-critic ensemble (FinRL, ICAIF 2020)](research/correction-strategies.md#rl1-turbulence-gated-actor-critic-ensemble-finrl-icaif-2020) | A1, A2 | The agents are A1 (❌ for now); the turbulence override is A2. |
| [RL2. FinRL library agents (A2C, DDPG, PPO, SAC, TD3)](research/correction-strategies.md#rl2-finrl-library-agents-a2c-ddpg-ppo-sac-td3) | A1 |  |
| [RL3. EIIE portfolio policy ("Deep Portfolio Management")](research/correction-strategies.md#rl3-eiie-portfolio-policy-deep-portfolio-management) | A4 | EIIE is the PGPortfolio policy. |
| [RL6. Single-asset DQN/DDPG and evolution-strategy agents](research/correction-strategies.md#rl6-single-asset-dqnddpg-and-evolution-strategy-agents) | A1 | huseinzol05's and Albert-Z-Guo's agents fall under A1's reasoning. |
| [S1. Volatility targeting](research/correction-strategies.md#s1-volatility-targeting) | S4, V18 | Same mechanism. Catalog rank 1. |
| [S3. Volatility-adjusted fixed-fractional sizing with a drawdown ladder](research/correction-strategies.md#s3-volatility-adjusted-fixed-fractional-sizing-with-a-drawdown-ladder) | V11, S4 | riskkit's tiered drawdown ladder is a stepped form of V11 on top of volatility sizing; tiers that halt new lots are not built. |
| [S5. Probability-scaled (meta-label or conformal) sizing](research/correction-strategies.md#s5-probability-scaled-meta-label-or-conformal-sizing) | V13 | Probability-scaled sizing is V13's mechanism; conformal calibration is not built. **Built:** AFML bet-size curve and split-conformal sizing (`position_sizing.bet_size_from_probability`, `conformal_long_size`). |
| [S6. Inverse-volatility weights across a small ETF set](research/correction-strategies.md#s6-inverse-volatility-weights-across-a-small-etf-set) | A5 | Inverse-volatility weights are HRP's limit for independent assets. |
| [X1. Composite regime-exit policy (`lots_to_liquidate`)](research/correction-strategies.md#x1-composite-regime-exit-policy-lots_to_liquidate) | §1 loss policy, N6 | `lots_to_liquidate` + `allow_signal_exit` is the only loss-realizing path. The catalog's open question on liquidation order (highest-cost first, all lots, or a fraction) is still open. |
| [X3. Profit-only trailing exits](research/correction-strategies.md#x3-profit-only-trailing-exits) | V10 | Catalog rank 8. |
| [MS4. Time-of-day-normalized volatility](research/correction-strategies.md#ms4-time-of-day-normalized-volatility) | V9 | V9 scales lot size by the intraday profile; using the profile for spacing belongs with C-G3. |
| [E1. Regime-based leverage stepping (TQQQ → QQQ → T-bills)](research/correction-strategies.md#e1-regime-based-leverage-stepping-tqqq--qqq--t-bills) | N7, X2 | N7 steps TQQQ → QQQ; X2's no-calm-defensive fallback is cash at the T-bill yield. Catalog rank 11. |
| [E3. Cross-asset ETF momentum and mean reversion](research/correction-strategies.md#e3-cross-asset-etf-momentum-and-mean-reversion) | X3 | Dual momentum over a small ETF universe. |

One disagreement: the catalog rejects the VIX calculator with the
options straddle (options pricing); this ledger built it as a
data-only tool (Q15) and still trades no options.

### Rejected in the catalog ([rejected list](research/correction-strategies.md#rejected-list))

Items not already recorded above (the straddle, VIX calculator, crypto
bots, Monte Carlo, Oil Money, Smart Farmers, Wisdom of Crowds, short
legs and inverse/volatility/managed-futures ETFs are Q12, Q15, A7, Q11,
Q6, Q14, Q16 and X6–X8).

| ID | Item | Source | Status | Reason |
|---|---|---|---|---|
| C-RJ1 | Dealer gamma-imbalance signals | Baltussen et al. 2021, cited in M1 | ⛔ | Needs options positioning data; M1's RSI(5) proxy is kept instead. |
| C-RJ2 | Funding-rate arbitrage; perpetual-futures scanners | ML4T crypto-perps case study; crypto entries in awesome-quant and awesome-ai-in-finance | ❌ | Crypto-specific mechanics (compare A7). |
| C-RJ3 | Martingale / averaging-down sizing | binary-martingale in awesome-quant | ❌ | Ruin-prone sizing that works against the drawdown goal. |
| C-RJ4 | 18 deep sequence forecasters and stacked ensembles | huseinzol05/Stock-Prediction-Models | ❌ | Daily, no costs, no trading evidence, unmaintained since Jan 2021 (compare A8). |
| C-RJ5 | Ghost Trader | letianzj/QuantResearch | ❌ | Daily MA/RSI/new-high entry with a Donchian price stop; redundant with Q1/Q5 and V3, and stop-dependent. |
| C-RJ6 | Index/ETF creation-redemption arbitrage | the research brief | ⛔ | Requires authorized-participant access. |
| C-RJ7 | LLM agent frameworks (TradingAgents, FinRobot and similar) | curated lists | ❌ | Frameworks rather than algorithms; no verifiable trading results. |
| C-RJ8 | Novelty strategies (tweet-driven trading, lottery prediction) | awesome-ai-in-finance | ❌ | No credible evidence. |

### Leads from the catalog's [gap analysis](research/correction-strategies.md#gap-analysis) (not catalogued)

Named as searches to run next; the catalog did not verify them.

| Lead | Gap it addresses | Standing |
|---|---|---|
| HAR-type realized-volatility forecasting | Intraday regime detection | suggested search |
| VIX term structure as a data-only regime input | Intraday regime detection | suggested search |
| Drawdown-constrained investing and CPPI (e.g. Grossman & Zhou) | Drawdown-constrained sizing theory | suggested search |
| Nasdaq-100 futures → ETF lead-lag as a data-only leading signal | ETF-specific intraday ideas | suggested search |
| Online mean-reversion portfolios (OLMAR/PAMR, Marigold/universal-portfolios) | Mean-reverting ETF rotation sleeve | listed in awesome-quant, not opened |
| MacroHFT (KDD'24), IMM (IJCAI'24), LLM crash detection (arXiv 2410.17266) | Regime-aware RL and market making | listed in ihobbang250/Awesome-AI-in-Finance, not opened |
| Cartea, Jaimungal & Penalva; Guéant market-liquidity books | Grid trading on equities | listed in awesome-systematic-trading |
| Intraday periodicity (Heston, Korajczyk & Sadka); overnight-vs-intraday returns | Intraday mean reversion in stress | suggested search |

---
## 8B. The algorithm database (`research/catalog/`)

Every entry above now has code (or a recorded reason for none), including
the ⛔ and ❌ ones: `research/catalog/` holds the algorithms as their
sources define them, shorts, stops, options and all. Nothing there is
wired into the engine, the engine host or a harness, and nothing trades;
the status marks in this ledger still describe **platform fit**, not
whether code exists. Code that fits the platform stays where it was
(`research/strategies/`, `research/ml/`, `research/optimization/`).

`research/catalog/registry.py` maps every ledger ID to its
implementations; `research/tests/test_catalog_registry.py` fails if a
ledger ID is missing or duplicated, if a reference does not import, or if
an entry has neither code nor a note. Tests are pinned to the sources:
values printed in the source notebooks, the sources' own unit tests
(czsc), textbook closed forms, brute force, or finite-difference gradient
checks for every hand-written backward pass.

| Module | Ledger entries | Sources transcribed |
|---|---|---|
| `je_suis_tm` | Q1–Q5, Q7–Q10, Q17 (as trades), Q2 | the quant-trading scripts |
| `je_suis_tm_projects` | Q6, Q11, Q13, Q14, Q16 | Oil Money, Monte Carlo, Smart Farmers, Wisdom of Crowds notebooks; graph-theory portfolio notebook |
| `options` | Q12, S1, C-RJ1 | Options Straddle script; ThetaGang `thetagang.toml`; Black-Scholes; GEX |
| `trend_following` | S2, C-G5 (with stops), X7, C-RJ5, C-M2 | PyTrendFollow rules/utility; letianzj `turtle.py`, `ghost_trader.py`; Faith's Turtle rules; Moskowitz-Ooi-Pedersen; Zarattini & Aziz |
| `czsc` | S5 | waditu/czsc Rust core (`analyze/utils.rs`, `mod.rs`, `bi.rs`, `zs.rs`) and its tests |
| `crypto` | A7, C-RJ2 | blackbird `check_entry_exit.cpp`/`result.cpp`; maxme/bitcoin-arbitrage `arbitrer.py`; Bellman-Ford arbitrage |
| `rl_agents` | A1, RL1/RL2, RL6, A2 (threshold) | huseinzol05 agents 5, 6, 7; FinRL `env_stocktrading.py`, `models.py`; GAE, PPO, TD3, SAC, DDPG rules |
| `rl_papers` | C-RL5, C-RL4, A4/RL3 | Moody & Saffell 2001; Huang 2018; Jiang, Xu & Liang 2017 (EIIE) |
| `forecasting` | C-RJ4, A8 | huseinzol05 `1.lstm.ipynb` and stacking; mlforecast-style lags; analogues; EW anomaly bands |
| `leads` | the gap-analysis leads | OLMAR, PAMR, CPPI, Grossman-Zhou, HAR-RV, VIX/VIX3M, Hayashi-Yoshida lead-lag, intraday periodicity, Almgren-Chriss |
| `excluded` | A6, X5, X6, X8, C-RJ3, C-RJ6 | jamesmawm IB `hft_model_1.py`; stock/bond mix; daily-reset inverse ETFs; martingale; creation/redemption |

**Source quirks kept, with a switch to the corrected form where one is
obvious** (each documented at its function):

* letianzj `turtle.py` computes its "10-day low" exit as the **max of the
  highs** (`textbook_exit=True` fixes it); `ghost_trader.py`'s long exit
  can fire only when the close is the bar's low.
* jamesmawm's IB model has `is_overbought`/`is_oversold` swapped against
  their comments, so its BUY signal buys the spread when A is rich
  (`fixed_labels=True`).
* FinRL's validation Sharpe annualises with √4, and its adaptive
  turbulence threshold is overwritten by the in-sample 99th percentile
  (`adaptive=True` keeps the discarded branch).
* PyTrendFollow normalises with full-sample statistics (its own
  "lookahead bias" warning; `causal=True` uses its commented-out
  expanding window). The huseinzol05 agents reward cash only, and the
  LSTM notebook leaves dropout on at inference.
* Smart Farmers' `compute_price` raises price with production, against
  its own demand fit (`consistent=True`); Platt-Burges' per-item
  variances collapse toward zero, so only the relative-change stop ends
  EM.

**Simplifications, stated in the modules:** the DRQN uses an Elman layer
(position at the output) instead of an LSTM; EIIE's evaluator is linear,
not a CNN; FinRL's SB3 networks are represented by their update rules and
a linear A2C; the LSTM forecaster stands for its 17 sibling notebooks,
which vary the cell, not the procedure.

**No code, by design:** C-E4 (the catalog could not verify the method),
C-RJ7 (LLM frameworks, not algorithms), C-RJ8 (no verifiable definition),
and the MacroHFT/IMM/LLM-crash lead (never opened; its RL building blocks
are in `rl_agents`/`rl_papers`). V20 maps to the V5 grid plus the
inverse-ETF drag in `excluded.daily_reset_path`.

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

# Entry gates, now including the intraday-momentum gate (X1)
FILL=causal bash run_entry_gate_chain.sh

# Volatility targeting (S4 with S3)
python -m research.run_hf_sweep --config config/probe_vol_target.yaml \
    --search grid --intrabar-fill causal --output output/probe_vol_target_causal.csv

# Turbulence regime (A2) for the step-down -- ingest QQQ, RSP, TLT, GLD first
python -m tools.leverage_stepdown --regime turbulence

# Every regime side by side (0006), with and without a minimum hold
for r in natr turbulence macd awesome psar heikin_ashi lppls; do
  python -m tools.leverage_stepdown --regime $r
  python -m tools.leverage_stepdown --regime $r --min-hold 5
done
python -m tools.leverage_stepdown --qqq-entry w_bottom     # X4 for the QQQ sleeve

# Rotations (0006) -- ingest XLP, XLU, USMV, GLD, RSP, QQQ first
python -m tools.rotation --mode defensive
python -m tools.rotation --mode relative_strength
python -m tools.rotation --mode hrp
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
5. **Measure S4** (`probe_vol_target.yaml`) alongside V11 `dd_throttle`
   — the two exposure levers.
6. **Measure A2** — `leverage_stepdown --regime turbulence` against
   `--regime natr`, both at lag 1.
7. **Measure X1** through the gate chain (`FILL=causal`).
8. **Decide the `run_hf_sweep` cash-yield threading** — changes every
   result, so do it once, deliberately, with a re-baselined champion.
9. **Measure the regime family side by side** — every `--regime` at
   lag 1, with and without `--min-hold 5`.
10. **Measure the rotations** — `tools.rotation --mode defensive`,
    `relative_strength` and `hrp`.
11. **Build a portfolio-level allocator** in the engine if any
    multi-instrument book earns it. It removes the additive-account
    approximation that N7, N11 and A5 all rest on.
