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
code for every remaining entry, in-scope or not. Section 8C (2026-10-27)
adds a ranked list of 14,225 algorithms from a CSV import, each with
whether it is implemented here and a link to its documentation in
[`docs/algorithms/`](algorithms/README.md); ranks 1–100 (RK1–RK100) and
200–400 (RK200–RK400) are researched, and §8C lists the research gaps that remain.*

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
| RK1 | Time-series momentum (TSMOM) | ranked list #1; Moskowitz, Ooi & Pedersen 2012 | Trend | ⛔ (as published) · ⏳ (long-or-cash) | Medium |
| RK2 | Volatility-scaled trend following | ranked list #2; Kim, Tse & Wald 2016 | Trend / risk scaling | ⛔ (as published) · ⏳ (long-or-cash) | **High** (the scaling half) |
| RK3 | Dual momentum (absolute + relative) | ranked list #3; Antonacci 2012 | Rotation | 🧪 | Medium |
| RK4 | Cross-asset carry composite | ranked list #4; Koijen, Moskowitz, Pedersen & Vrugt 2018 | Carry | ⛔ | None |
| RK5 | Value-momentum composite | ranked list #5; Asness, Moskowitz & Pedersen 2013 | Multi-factor equity | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK6 | 12–1 momentum (skip-month) | ranked list #6; Jegadeesh & Titman 1993 | Cross-sectional momentum | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK7 | Cross-sectional momentum | ranked list #7; Jegadeesh & Titman 1993; Asness, Moskowitz & Pedersen 2013 | Momentum / rotation | 🧪 (long-only ETF rotation, X3) · ⛔ (long/short) | Low–medium |
| RK8 | Commodity momentum + term structure | ranked list #8; Fuertes, Miffre & Rallis 2010 | Commodity trend / carry | ⛔ | None |
| RK9 | Fama–French five-factor portfolio | ranked list #9; Fama & French 2015 | Factor model | ⛔ (as a portfolio) · ⏳ (as an attribution tool) | Measurement |
| RK10 | State-filtered momentum | ranked list #10; Cooper, Gutierrez & Hameed 2004 | Regime-aware momentum | ⏳ | Medium |
| RK11 | Quality minus junk (QMJ) | ranked list #11; Asness, Frazzini & Pedersen 2019 | Quality factor | ⛔ (as published) · ⏳ (long-only) | Low |
| RK12 | Quality / profitability factor | ranked list #12; Novy-Marx 2013; Fama & French 2015 | Quality factor | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK13 | Gross profitability factor | ranked list #13; Novy-Marx 2013 | Quality factor | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK14 | 52-week-high momentum | ranked list #14; George & Hwang 2004 | Cross-sectional momentum | ⏳ (long-only basket) · ⛔ (long/short) | Medium (as a single-asset filter) |
| RK15 | Conservative investment factor | ranked list #15; Fama & French 2015; Cooper, Gulen & Schill 2008 | Investment factor | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK16 | Residual momentum | ranked list #16; Blitz, Huij & Martens 2011 | Cross-sectional momentum | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK17 | 10-month moving-average risk filter | ranked list #17; Faber 2007 | Trend regime | 🧪 | Medium |
| RK18 | Low-volatility equity | ranked list #18; Baker, Bradley & Wurgler 2011; Ang et al. 2006 | Defensive equity | 🧪 (via defensive ETFs, X2) | Medium |
| RK19 | Sector momentum rotation | ranked list #19; Moskowitz & Grinblatt 1999 | Rotation | 🧪 | Low–medium |
| RK20 | Bond duration momentum | ranked list #20; Durham (NY Fed SR 657, FAJ 2015) | Fixed-income trend | ⛔ (as published) · ⏳ (long-or-cash Treasury ETF) | Low–medium |
| RK21 | VIX-regime conditional equity exposure | ranked list #21; Copeland & Copeland 1999; Bansal & Stivers 2023 | Volatility regime | 🧪 | Medium |
| RK22 | Volatility targeting / risk scaling | ranked list #22; Harvey et al. 2018; Moreira & Muir 2017 | Exposure scaling | 🧪 | **High** |
| RK23 | Drawdown-aware de-risking governor | ranked list #23; Grossman & Zhou 1993 | Exposure scaling | 🔬 (V11) · 🧪 (halt tiers) | Medium |
| RK24 | ETF NAV / creation-redemption arbitrage | ranked list #24; Petajisto 2017 | ETF relative value | ⛔ | None |
| RK25 | Index futures vs cash basis arbitrage | ranked list #25; MacKinlay & Ramaswamy 1988 | Index arbitrage | ⛔ | None |
| RK26 | Futures cash-and-carry basis trading | ranked list #26; MacKinlay & Ramaswamy 1988 | Basis arbitrage | ⛔ | None |
| RK27 | Shareholder yield factor | ranked list #27; Boudoukh, Michaely, Richardson & Roberts 2007 | Payout factor | ⏳ | Low |
| RK28 | Fixed-income carry and roll-down | ranked list #28; Koijen et al. 2018 | Fixed-income carry | ⛔ (levered curve trade) · ⏳ (long-only ETF maturity choice) | Low |
| RK29 | Price + earnings momentum | ranked list #29; Chan, Jegadeesh & Lakonishok 1996 | Cross-sectional momentum / earnings | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK30 | FX carry trade | ranked list #30; Lustig, Roussanov & Verdelhan 2011; Brunnermeier, Nagel & Pedersen 2008 | Currency carry | ⛔ | None |
| RK31 | Intangibles-adjusted value and profitability | ranked list #31; Peters & Taylor 2017; Financial Management 2025 | Value factor | ⏳ | Low |
| RK32 | Commodity futures roll yield | ranked list #32; Erb & Harvey 2006; Szymanowska et al. 2014 | Commodity carry | ⛔ (futures) · ⏳ (long-only ETF) | Low |
| RK33 | Market-neutral residual mean reversion | ranked list #33; Avellaneda & Lee 2010 | Statistical arbitrage | ⛔ (market-neutral) · 🧪 (long-only s-score, C-MR2) | Low |
| RK34 | Futures calendar-spread mean reversion | ranked list #34; Lubnau & Todorova 2015; Shang, Serra & Garcia 2023 | Futures relative value | ⛔ | None |
| RK35 | Net stock issuance anomaly | ranked list #35; Pontiff & Woodgate 2008 | Corporate-actions factor | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK36 | Johansen cointegration basket trading | ranked list #36; Johansen 1991; Krauss 2017 | Statistical arbitrage | ⛔ | None |
| RK37 | Cointegration-based pairs trading | ranked list #37; Engle & Granger 1987; Rad, Low & Faff 2016 | Statistical arbitrage | ⛔ (long/short) · 🧪 (long-only spread signal) | Low |
| RK38 | Chandelier exit | ranked list #38; LeBeau (via Elder) | Exit rule | ⛔ (stop) · ⏳ (profit-only trail) | Low |
| RK39 | Merger arbitrage | ranked list #39; Mitchell & Pulvino 2001 | Event-driven | ⏳ (long the target, cash deals) · ⛔ (short acquirer hedge) | Low |
| RK40 | Earnings estimate revision momentum | ranked list #40; Chan, Jegadeesh & Lakonishok 1996 | Earnings momentum | ⏳ (long-only basket) | Low |
| RK41 | Inflation-regime asset rotation | ranked list #41; Neville, Draaisma, Funnell, Harvey & Van Hemert 2021 | Macro rotation | ⏳ | Medium |
| RK42 | Cross-asset commodity term-structure carry | ranked list #42; Szymanowska et al. 2014 | Commodity carry | ⛔ | None |
| RK43 | Donchian / Turtle channel breakout | ranked list #43; Szakmary, Shen & Sharma 2010; Faith 2003 | Trend / breakout | ⛔ (as published) · 🧪 (scale-in pyramid, C-G5) | Low |
| RK44 | Supertrend ATR-band trend following | ranked list #44; attributed to Olivier Seban | Trend / technical | ⏳ (long-or-cash regime) · ⛔ (stop-and-reverse) | Low |
| RK45 | Post-earnings announcement drift (PEAD) | ranked list #45; Bernard & Thomas 1989; Martineau 2022 | Event-driven / earnings | ⏳ (long-only, small caps) · ⛔ (short side) | Low |
| RK46 | MACD signal-line crossover | ranked list #46; Appel (1970s) | Trend / momentum | 🔬 (regime, measured) · ⛔ (long/short) | Low |
| RK47 | Public activist-filing (13D) event strategy | ranked list #47; Brav, Jiang, Partnoy & Thomas 2008 | Event-driven / activism | ⏳ (long-only event basket) | Low |
| RK48 | Book-to-market value | ranked list #48; Fama & French 1992 | Value factor | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK49 | Betting against beta (BAB) | ranked list #49; Frazzini & Pedersen 2014 | Low-risk factor | ⛔ | None |
| RK50 | Accrual anomaly | ranked list #50; Sloan 1996 | Accounting factor | ⏳ (long-only basket) · ⛔ (long/short) | None |
| RK51 | Asset-growth anomaly | ranked list #51; Cooper, Gulen & Schill 2008 | Investment factor | ⏳ (long-only basket) · ⛔ (long/short) | Low |
| RK52 | Dividend yield / dividend growth | ranked list #52; Hartzmark & Solomon 2019 | Income factor | 🧪 (as an instrument, SPYD) · ⏳ (as a selection rule) | Low |
| RK53 | CVaR / expected-shortfall optimization | ranked list #53; Rockafellar & Uryasev 2000 | Portfolio construction | ⏳ | Low |
| RK54 | Volatility-managed factor portfolio | ranked list #54; Moreira & Muir 2017; Hanauer & Windmüller 2023 | Exposure scaling | ⛔ (factor portfolios) · 🧪 (the scaling, S4) | Low |
| RK55 | ADX-filtered trend following | ranked list #55; Wilder 1978 | Trend strength | ⏳ (harvest gate) · ⛔ (long/short trend trade) | Medium |
| RK56 | Hierarchical risk parity (HRP) | ranked list #56; López de Prado 2016 | Portfolio construction | 🧪 | Medium |
| RK57 | Low P/E value screen | ranked list #57; Basu 1977 | Value factor | ⏳ | Low |
| RK58 | Small-cap size premium | ranked list #58; Banz 1981; Asness et al. 2018 | Size factor | ⏳ | Low |
| RK59 | Liquidity factor | ranked list #59; Amihud 2002; Pástor & Stambaugh 2003 | Liquidity | ⛔ (illiquidity premium) · 🧪 (the measures, as data) | Measurement |
| RK60 | Global minimum-variance portfolio | ranked list #60; Clarke, de Silva & Thorley 2006 | Portfolio construction | ⏳ | Low |
| RK61 | Risk parity / equal risk contribution | ranked list #61; Maillard, Roncalli & Teiletche 2010; Asness, Frazzini & Pedersen 2012 | Portfolio construction | ⏳ (unlevered) · ⛔ (levered) | Low |
| RK62 | Dual moving-average crossover | ranked list #62; Brock, Lakonishok & LeBaron 1992 | Trend regime | 🧪 (as a regime) · ⛔ (as a long/short trade) | Low |
| RK63 | Black–Litterman allocation | ranked list #63; Black & Litterman 1992 | Portfolio construction | ⏳ | Low |
| RK64 | Triple EMA / moving-average ribbon | ranked list #64; Guppy (practitioner) | Trend regime | ⏳ (as a regime) · ⛔ (as a long/short trade) | Low |
| RK65 | Cross-sectional factor momentum rotation | ranked list #65; Ehsani & Linnainmaa 2022; Fan et al. 2022 | Factor rotation | ⏳ | Low |
| RK66 | Maximum-diversification portfolio | ranked list #66; Choueifaty & Coignard 2008 | Portfolio construction | ⏳ | Low |
| RK67 | ATR-based position sizing | ranked list #67; Faith 2003 (Turtle rules) | Position sizing | 🧪 (volatility-normalised lots) · ⛔ (stop-distance form) | Low |
| RK68 | Dual Thrust breakout | ranked list #68; attributed to Michael Chalek | Intraday breakout | ⛔ (trade) · 🧪 (lower band as a buy gate, N1) | Low |
| RK69 | London session breakout | ranked list #69; practitioner sources only | Intraday breakout (FX) | ⛔ (trade) · 🧪 (US-hours gate, N2) | Low |
| RK70 | Parabolic SAR trend / stop | ranked list #70; Wilder 1978 | Trend / trailing stop | 🔬 (regime, measured) · 🧪 (profit-only exit) · ⛔ (stop-and-reverse) | Low |
| RK71 | Heikin-Ashi trend filter | ranked list #71; Valcu 2004 | Trend / smoothed candles | 🔬 (regime, measured) | None |
| RK72 | Distance-based pairs trading | ranked list #72; Gatev, Goetzmann & Rouwenhorst 2006; Do & Faff 2010 | Statistical arbitrage | ⛔ | None |
| RK73 | Kalman-filter dynamic-hedge pairs | ranked list #73; Elliott, van der Hoek & Malcolm 2005 | Statistical arbitrage | ⛔ (long/short) · 🧪 (long-only spread signal) | Low |
| RK74 | Copula-based pairs trading | ranked list #74; Liew & Wu 2013; Stübinger, Mangold & Krauss 2018 | Statistical arbitrage | ⛔ | None |
| RK75 | Ornstein–Uhlenbeck spread trading | ranked list #75; Bertram 2010 | Statistical arbitrage | ⛔ (spread) · 🧪 (OU diagnostics) | Low |
| RK76 | PCA residual statistical arbitrage | ranked list #76; Avellaneda & Lee 2010 | Statistical arbitrage | ⛔ | None |
| RK77 | ATR volatility-expansion breakout | ranked list #77; Williams 1999 | Volatility breakout | ⛔ (breakout trade) | Low |
| RK78 | Multi-timeframe trend agreement | ranked list #78; Hurst, Ooi & Pedersen 2017; Elder 1993 | Signal confirmation | ⏳ (long-or-cash) · ⛔ (with a short side) | Low |
| RK79 | Opening gap continuation | ranked list #79; Gao, Han, Li & Zhou 2018; Plastun et al. 2020 | Intraday momentum | 🧪 (downside as buy gates, N3/X1) · ⛔ (day trade) | Medium |
| RK80 | Convertible bond arbitrage | ranked list #80; Agarwal, Fung, Loon & Naik 2011 | Capital structure | ⛔ | None |
| RK81 | Capital structure arbitrage | ranked list #81; Yu 2006 | Credit-equity relative value | ⛔ | None |
| RK82 | Closed-end fund discount reversion | ranked list #82; Pontiff 1995; Lee, Shleifer & Thaler 1991 | Fund discounts | ⏳ | Low |
| RK83 | Triangular FX arbitrage | ranked list #83; Fenn et al. 2009 | Cross-market arbitrage | ⛔ | None |
| RK84 | Crypto perpetual funding-rate capture | ranked list #84; Schmeling, Schrimpf & Todorov 2023 | Crypto carry | ❌ | None |
| RK85 | Spot-perpetual basis arbitrage | ranked list #85; He, Manela, Ross & von Wachter | Crypto basis | ❌ | None |
| RK86 | Yield-curve steepener / flattener | ranked list #86; Litterman & Scheinkman 1991 | Rates relative value | ⛔ | None |
| RK87 | Option dispersion trading | ranked list #87; Driessen, Maenhout & Vilkov 2009 | Options volatility | ⛔ | None |
| RK88 | Distributionally robust CVaR allocation | ranked list #88; Mohajerin Esfahani & Kuhn 2018 | Portfolio construction | ⏳ | Low |
| RK89 | Autoencoder latent-factor stat arb | ranked list #89; Gu, Kelly & Xiu 2021; Guijarro-Ordonez, Pelger & Zanotti | ML statistical arbitrage | ⛔ | None |
| RK90 | Long-term industry reversal with valuation confirmation | ranked list #90; Bornholt, Gharaibeh & Malin 2015 | Long-horizon contrarian rotation | ⏳ (long-only sector ETFs) | Low |
| RK91 | iNAV dislocation ETF arbitrage | ranked list #91; Petajisto 2017 | ETF arbitrage | ⛔ | None |
| RK92 | Fed ON RRP / T-bill liquidity arbitrage | ranked list #92; FEDS Notes 2023 | Money markets | ⛔ | None |
| RK93 | Cointegrated triplet basket stat arb | ranked list #93; Johansen 1991 | Statistical arbitrage | ⛔ | None |
| RK94 | Dynamic copula-GARCH pair trading | ranked list #94; Stübinger, Mangold & Krauss 2018 | Statistical arbitrage | ⛔ | None |
| RK95 | Asymmetric tail-risk parity | ranked list #95; Boudt, Carl & Peterson 2013 | Portfolio construction | ⏳ | Low |
| RK96 | PCA eigenportfolios stat arb | ranked list #96; Avellaneda & Lee 2010 | Statistical arbitrage | ⛔ | None |
| RK97 | Wasserstein distributionally robust stat arb | ranked list #97 | Robust statistical arbitrage | ⛔ | None |
| RK98 | Adversarial domain-generalisation cross-market momentum | ranked list #98; Arjovsky et al. 2019; Gulrajani & Lopez-Paz 2021 | ML momentum | ⏳ (in principle) · not a priority | None |
| RK99 | Conformally constrained risk parity | ranked list #99; Kato 2024; Schmitt 2026 | Portfolio construction | ⏳ | Low |
| RK100 | Causal-discovery (DAG) pair selection | ranked list #100; Stübinger 2019 | Causal inference | ⛔ | None |
| RK200 | Score-based diffusion multi-asset scenario synthesizer | ranked list #200; Takahashi & Mizuno 2024 | Generative scenarios | ⏳ (stress-test tool) | Low |
| RK201 | Koopman-operator MPC statistical arbitrage | ranked list #201; Mann & Kutz 2016 | Koopman / MPC | ⛔ | None |
| RK202 | Fractional Brownian motion multi-scale trend scanning | ranked list #202; Lo 1991 | Fractional trend detection | ⛔ | None |
| RK203 | Koopman-operator MPC spread equilibrium | ranked list #203; Mann & Kutz 2016 | Koopman / MPC | ⛔ | None |
| RK204 | Lead-lag cross-asset predictive trading | ranked list #204; Huth & Abergel | Cross-asset lead-lag | 🧪 (estimator) · ⏳ (entry timing) · ⛔ (latency trade) | Low |
| RK205 | Dynamic tensor decomposition multi-asset factor rotation | ranked list #205; Chen, Yang & Zhang 2022 | Tensor factor models | ⛔ | None |
| RK206 | Koopman-operator MPC multi-asset allocation | ranked list #206; Mann & Kutz 2016 | Koopman / MPC | ⛔ | None |
| RK207 | Standardized unexpected earnings (SUE) | ranked list #207; Foster, Olsen & Shevlin 1984 | Earnings event | ⏳ (long-only basket) · ⛔ (short side) | Low |
| RK208 | Anchored VWAP reclaim / rejection | ranked list #208; practitioner sources | Intraday price/volume | 🧪 (session VWAP gate) · ⏳ (event anchors) | Low |
| RK209 | Corporate buyback announcement drift | ranked list #209; Ikenberry, Lakonishok & Vermaelen 1995 | Corporate-action event | ⏳ (long-only event basket) | None |
| RK210 | Index reconstitution / rebalance event trading | ranked list #210; Greenwood & Sammon 2025 | Index flow event | ⛔ | None |
| RK211 | Macro surprise / economic release strategy | ranked list #211; Savor & Wilson 2013; Lucca & Moench 2015 | Macro event | ⛔ (release trade) · ✅ (event-day sizing, V6) | Low |
| RK212 | Market breadth thrust | ranked list #212; Zweig 1986 | Market internals | ⏳ | Low |
| RK213 | Trend-scanning label model | ranked list #213; López de Prado 2020 | ML labelling | 🧪 (labelling tool) | Low |
| RK214 | XGBoost cross-sectional ranking | ranked list #214; Gu, Kelly & Xiu 2020 | ML stock selection | ⏳ (long-only top-k) · ⛔ (long-short) | Low |
| RK215 | Cross-sectional reversal with risk neutralization | ranked list #215; Da, Liu & Schaumburg 2014 | Short-horizon reversal | 🧪 (long-only contrarian weights) · ⛔ (market-neutral) | Low |
| RK216 | Top-K with dropout portfolio rotation | ranked list #216; Qlib | Signal deployment | ⏳ (turnover rule) | Low |
| RK217 | BSTS causal-impact macro strategy | ranked list #217; Brodersen et al. 2015 | Bayesian event study | ⏳ (event-study tool) | None |
| RK218 | Sparse Bayesian learning dynamic factor model | ranked list #218; Bryzgalova, Huang & Julliard 2023 | Bayesian factor selection | ⏳ | None |
| RK219 | Dynamic mode decomposition (DMD) market mode predictor | ranked list #219; Mann & Kutz 2016 | Dynamical systems | ⛔ | None |
| RK220 | Continuous-time mean-variance RL agent | ranked list #220; Wang & Zhou | RL allocation | ⏳ | Low |
| RK221 | Transfer-entropy lead-lag strategy | ranked list #221; Schreiber 2000; Dimpfl & Peter 2013 | Information theory | ⏳ (measurement) · ⛔ (trade) | Low |
| RK222 | Maximum entropy production rate macro allocator | ranked list #222 | Thermodynamic allocation | ⛔ | None |
| RK223 | Quantum tensor-network portfolio optimization | ranked list #223; Mugel et al. 2022 | Quantum-inspired optimisation | ⛔ | None |
| RK224 | Deep latent force model interest-rate forecaster | ranked list #224; Álvarez, Luengo & Lawrence 2009 | Gaussian-process rates model | ⛔ | None |
| RK225 | Wasserstein distributionally robust mean-variance allocation | ranked list #225; Blanchet, Chen & Zhou 2022 | Robust allocation | ⏳ | Low |
| RK226 | Functional PCA (FPCA) yield-curve forecaster | ranked list #226; Hays, Shen & Huang 2012 | Functional data analysis | ⛔ | None |
| RK227 | Multi-agent evolutionary RL portfolio optimizer | ranked list #227 | Evolutionary RL | ⛔ | None |
| RK228 | Deep generative flow-matching portfolio generator | ranked list #228; Lipman et al. 2022 | Generative allocation | ⛔ | None |
| RK229 | Quantum adiabatic optimal portfolio rebalancing | ranked list #229; Mugel et al. 2022; Rosenberg et al. 2016 | Quantum optimisation | ⛔ | None |
| RK230 | Riemannian SPD-manifold portfolio optimization | ranked list #230 | Riemannian portfolio | ⛔ | None |
| RK231 | Riemannian SPD metric-diffusion risk parity | ranked list #231 | Riemannian portfolio | ⛔ | None |
| RK232 | Graph-attention covariance shrinkage estimator | ranked list #232; Ledoit & Wolf | Covariance estimation | ⛔ | None |
| RK233 | Riemannian SPD Wasserstein-robust allocation | ranked list #233 | Riemannian portfolio | ⛔ | None |
| RK234 | Wasserstein distributionally robust RL portfolio agent | ranked list #234 | Robust RL allocation | ⛔ | None |
| RK235 | Graph-attention covariance shrinkage dynamic allocation | ranked list #235; Ledoit & Wolf | Covariance estimation | ⛔ | None |
| RK236 | Quantum adiabatic GNN portfolio optimization | ranked list #236 | Quantum optimisation | ⛔ | None |
| RK237 | Riemannian SPD graph-attention allocation | ranked list #237 | Riemannian portfolio | ⛔ | None |
| RK238 | Quantum adiabatic tensor-network portfolio optimization | ranked list #238 | Quantum optimisation | ⛔ | None |
| RK239 | Fractional-order VECM neural network allocator | ranked list #239; Johansen & Nielsen 2012 | Fractional cointegration | ⛔ | None |
| RK240 | Neural-operator delay-differential stochastic volatility calibrator | ranked list #240; Horvath, Muguruza & Tomas 2021 | Option pricing / calibration | ⛔ | None |
| RK241 | Koopman-operator factor risk tracking | ranked list #241; Mann & Kutz 2016 | Koopman / MPC | ⛔ | None |
| RK242 | Long-volatility breakout (options) | ranked list #242; Coval & Shumway 2001 | Options volatility | ⛔ | None |
| RK243 | Price/volume anomaly detection | ranked list #243 | Anomaly detection | 🧪 (data-quality flag) · ❌ (alpha) | Low |
| RK244 | Liquidity-aware adaptive execution | ranked list #244; Almgren & Chriss 2001; BIS 2020 | Execution | 🧪 (spread gate) · ⛔ (slicing not needed) | Low |
| RK245 | Pure passive market making | ranked list #245; Menkveld 2013 | Market making | ⛔ (two-sided) · grid is the buy-side relative | Low |
| RK246 | Inventory-skewed market making | ranked list #246; Avellaneda & Stoikov 2008 | Market making | ✅ (buy-side skew, C-G2) · ⛔ (sell side below cost) | Medium |
| RK247 | VPIN flow-toxicity filter | ranked list #247; Easley, López de Prado & O'Hara 2012; Andersen & Bondarenko 2014 | Flow toxicity | 🧪 (buy gate) · disputed evidence | Low |
| RK248 | Hawkes-process order-flow forecast | ranked list #248; Bacry, Mastromatteo & Muzy 2015 | Point-process microstructure | ⛔ | None |
| RK249 | Iceberg / reserve-order execution | ranked list #249; Bessembinder, Panayides & Venkataraman 2009 | Execution | ⛔ (not needed) | None |
| RK250 | Arrival-price adaptive limit-vs-market execution | ranked list #250; Perold 1988 | Execution | 🧪 (purpose-based pricing) · ⏳ (shortfall check) | Low |
| RK251 | Intraday volume-profile execution | ranked list #251; Białkowski, Darolles & Le Fol 2008 | Execution | ⛔ (not applicable) | None |
| RK252 | Order-flow imbalance (OFI) cross-sectional alpha predictor | ranked list #252; Cont, Kukanov & Stoikov 2014 | Order-flow alpha | 🧪 (single-instrument OFI) · ⛔ (cross-sectional) | Low |
| RK253 | Information-driven volume-clock imbalance momentum | ranked list #253; Easley, López de Prado & O'Hara 2012 | Volume-clock sampling | 🧪 (bars) · ⏳ (rule) | Low |
| RK254 | Persistent-homology (TDA) crash predictor | ranked list #254; Gidea & Katz 2018 | Topological data analysis | ⏳ as a regime input | Low |
| RK255 | Persistent-homology landscape crisis predictor | ranked list #255; Gidea & Katz 2018 | Topological data analysis | ⏳ as a regime input | Low |
| RK256 | Deep Markov state-space intraday volume predictor | ranked list #256 | Deep state-space volume | ⛔ | None |
| RK257 | Transfer-entropy causality-flow macro allocator | ranked list #257 | Information theory | ⛔ | None |
| RK258 | Spiking graph convolutional network contagion predictor | ranked list #258 | Neuromorphic AI | ⛔ | None |
| RK259 | Hawkes-driven non-parametric order-flow toxicity filter | ranked list #259 | Flow toxicity | ⛔ | None |
| RK260 | Quantum approximate state-preparation risk mapping | ranked list #260; Woerner & Egger 2019 | Quantum risk | ⛔ | None |
| RK261 | Koopman-operator MPC risk mitigation | ranked list #261; Mann & Kutz 2016 | Koopman / MPC | ⛔ | None |
| RK262 | Persistent-homology Betti-0 contagion detector | ranked list #262; Gidea & Katz 2018 | Topological data analysis | ⛔ | None |
| RK263 | Persistence-diagram clustering crisis detector | ranked list #263; Gidea & Katz 2018 | Topological data analysis | ⛔ | None |
| RK264 | Transfer-entropy directed GNN contagion model | ranked list #264 | Information theory | ⛔ | None |
| RK265 | Persistent-homology Betti-2 macro stress predictor | ranked list #265; Gidea & Katz 2018 | Topological data analysis | ⛔ | None |
| RK266 | Riemannian SPD entropic-risk portfolio | ranked list #266 | Riemannian portfolio | ⛔ | None |
| RK267 | Graph-attention covariance spectral regularization | ranked list #267; Ledoit & Wolf | Covariance estimation | ⛔ | None |
| RK268 | Persistent-homology multi-scale Vietoris–Rips risk score | ranked list #268; Gidea & Katz 2018 | Topological data analysis | ⏳ as a regime input | Low |
| RK269 | Persistent-homology Betti-0 multiscale contagion clustering | ranked list #269; Gidea & Katz 2018 | Topological data analysis | 🧪 (dendrogram in HRP) · ⏳ (contagion signal) | Low |
| RK270 | Quantum annealing binary matrix factorization risk model | ranked list #270 | Quantum risk | ⛔ | None |
| RK271 | Sequential bootstrapping sample weights | ranked list #271; López de Prado 2018 | ML training | ⏳ (training hygiene) | Low |
| RK272 | Wavelet-neural network intraday trend scalper | ranked list #272 | Signal processing + ML | ⛔ (scalper) | None |
| RK273 | Deep Koopman spectral asset allocation | ranked list #273; Mann & Kutz 2016 | Koopman / MPC | ⛔ | None |
| RK274 | Avellaneda–Stoikov market making | ranked list #274; Avellaneda & Stoikov 2008 | Market making | ✅ (bid-side reservation price) · ⛔ (two-sided) | Low |
| RK275 | DeepLOB-style order-book forecasting | ranked list #275; Zhang, Zohren & Roberts 2019 | Deep learning microstructure | ⛔ | None |
| RK276 | Queue-reactive market making | ranked list #276; Huang, Lehalle & Rosenbaum 2015 | Market making | 🧪 (fill model) · ⛔ (quoting) | Low |
| RK277 | Hawkes multi-dimensional order-flow intensity model | ranked list #277; Bacry & Muzy 2014 | Point-process microstructure | ⛔ | None |
| RK278 | Cross-venue crypto triangular arbitrage | ranked list #278; Makarov & Schoar 2020 | Crypto arbitrage | ❌ | None |
| RK279 | Asynchronous multi-exchange spatial arbitrage graph | ranked list #279; Makarov & Schoar 2020 | Crypto arbitrage | ❌ | None |
| RK280 | Recurrent neural Hawkes toxic-flow hedging trigger | ranked list #280; Mei & Eisner 2017 | Neural point processes | ⛔ | None |
| RK281 | Covered call / buy-write | ranked list #281; Whaley 2002; Israelov & Nielsen 2015 | Options income | ⛔ | Low |
| RK282 | Put-write / cash-secured put | ranked list #282; Ungar & Moran 2009 | Options income | ⛔ | Low |
| RK283 | Wasserstein distributionally robust neural stochastic-control hedging | ranked list #283; Buehler et al. 2019 | Derivatives hedging | ⛔ | None |
| RK284 | Options wheel | ranked list #284; ThetaGang | Options income | ⛔ | Low |
| RK285 | Iron condor / short premium range strategy | ranked list #285; Cboe CNDR | Options income | ⛔ | None |
| RK286 | Iron butterfly credit strategy | ranked list #286; Cboe BFLY | Options income | ⛔ | None |
| RK287 | Neural-operator delay-ODE term-structure predictor | ranked list #287 | Neural operators | ⛔ | None |
| RK288 | Neural CDE point-process execution | ranked list #288; Kidger et al. 2020 | Neural differential equations | ⛔ | None |
| RK289 | Neural-operator delay-differential Hawkes microstructure predictor | ranked list #289 | Neural operators | ⛔ | None |
| RK290 | Random forest return classification | ranked list #290; Krauss, Do & Huck 2017 | ML classification | ⏳ (as a learner) · ⛔ (long-short) | Low |
| RK291 | Gradient-boosted trees return prediction | ranked list #291; Gu, Kelly & Xiu 2020 | ML prediction | ✅ (lot sizing, V13/V14) · ⛔ (direction trade) | Medium |
| RK292 | LSTM sequence forecasting | ranked list #292; Fischer & Krauss 2018 | Deep learning forecast | ❌ | None |
| RK293 | News / financial sentiment NLP | ranked list #293; Tetlock 2007 | Text sentiment | ⏳ (market-level input) · ⛔ (stock-level news trade) | Low |
| RK294 | Triple-barrier labeled ML strategy | ranked list #294; López de Prado 2018 | ML labelling | 🧪 (labels) | Medium |
| RK295 | Conformal prediction uncertainty wrapper (CP-MAPIE) | ranked list #295; Vovk, Gammerman & Shafer 2005 | Uncertainty quantification | 🧪 (conformal sizing) | Low |
| RK296 | Dynamic copula-vine regularized factor allocation | ranked list #296; Low, Alcock, Faff & Brailsford 2013 | Copula allocation | ⏳ | Low |
| RK297 | Fractional Hurst-driven adaptive-bandwidth mean reversion | ranked list #297; Lo 1991 | Adaptive mean reversion | 🧪 (Hurst diagnostic) · ⏳ (adaptive bands) | Low |
| RK298 | AMM / CLOB cross-venue arbitrage | ranked list #298; Milionis et al. 2022 | DeFi arbitrage | ❌ | None |
| RK299 | Dynamic AMM liquidity provision / liquidity mining | ranked list #299; Loesch et al. 2021 | DeFi liquidity provision | ❌ | None |
| RK300 | Fractional differentiation feature pipeline | ranked list #300; López de Prado 2018; Hosking 1981 | ML preprocessing | 🧪 (feature transform) | Low |
| RK301 | Temporal Fusion Transformer forecasting | ranked list #301; Lim et al. 2021 | Deep forecasting | ⛔ | None |
| RK302 | Deep Galerkin Method (DGM) option solver | ranked list #302; Sirignano & Spiliopoulos 2018 | Physics-informed ML | ⛔ | None |
| RK303 | Neural jump-diffusion rough Heston smile predictor | ranked list #303; Gatheral, Jaisson & Rosenbaum 2018 | Derivatives pricing | ⛔ | None |
| RK304 | Recurrent neural Hawkes volatility-jump forecaster | ranked list #304 | Point processes | ⛔ | None |
| RK305 | Quantum annealing binary-quadratic rebalancing | ranked list #305; Mugel et al. 2022 | Quantum optimisation | ⛔ | None |
| RK306 | Micro-price / queue-imbalance signal | ranked list #306; Stoikov 2018; Gould & Bonart 2016 | Microstructure | 🧪 (C-MS2) · ⏳ (fair-value check) | Low |
| RK307 | Cross-exchange market making (XEMM) | ranked list #307; Hummingbot | Market making | ⛔ | None |
| RK308 | Dividend capture window | ranked list #308; Lakonishok & Vermaelen 1986 | Event / income | ⛔ | None |
| RK309 | Gamma scalping / long-gamma rebalancing | ranked list #309; Bakshi & Kapadia 2003 | Options | ⛔ | None |
| RK310 | Multi-agent RL execution / liquidation | ranked list #310; Karpe et al. 2020 | RL execution | ⛔ | None |
| RK311 | FinBERT sentiment event arbitrage | ranked list #311; Huang, Wang & Yang 2023; Lopez-Lira & Tang | NLP / event-driven | ⏳ (market-level input) · ⛔ (stock-level trade) | Low |
| RK312 | Deep Q-network (DQN) liquidation agent | ranked list #312; Ning, Lin & Jaimungal 2021 | RL execution | ⛔ | None |
| RK313 | Adaptive-mesh RL market maker | ranked list #313; Spooner et al. 2018 | RL market making | ⛔ | None |
| RK314 | Hawkes jump-diffusion multivariate event detection | ranked list #314; Aït-Sahalia, Cacho-Diaz & Laeven 2015 | Point processes | ⏳ (daily stress gauge) | Low |
| RK315 | Empirical mode decomposition (Hilbert-Huang) intraday scalper | ranked list #315; Huang et al. 1998 | Signal processing | ⛔ | None |
| RK316 | Temporal convolutional network (TCN) forecasting | ranked list #316; Bai, Kolter & Koltun 2018 | Deep forecasting | ⛔ | None |
| RK317 | Meta-labelling primary signals | ranked list #317; López de Prado 2018; Joubert 2022 | ML sizing | ✅ (V13) | Medium |
| RK318 | Graph convolutional network (GCN) stock ranking | ranked list #318; Feng et al. 2019 | Graph ML | ⛔ | None |
| RK319 | Volatility-harvesting dynamic asymmetric grid | ranked list #319; this repository; Chen, Chen & Jang 2025 | Grid trading | ✅ (V5, the champion) | High |
| RK320 | Koopman-operator volatility-surface interpolator | ranked list #320 | Koopman / derivatives | ⛔ | None |
| RK321 | Koopman-operator volatility-surface pricing model | ranked list #321 | Koopman / derivatives | ⛔ | None |
| RK322 | Order-book imbalance signal | ranked list #322; Gould & Bonart 2016 | Microstructure | 🧪 (C-MS2) · ⛔ (needs depth) | None |
| RK323 | Physics-informed neural operator yield-curve dynamics | ranked list #323 | Neural operators | ⛔ | None |
| RK324 | Wasserstein distributionally robust neural SDE hedging | ranked list #324; Gierjatowicz et al. | Derivatives hedging | ⛔ | None |
| RK325 | Neural-operator controlled portfolio dynamic hedging | ranked list #325 | Neural operators | ⛔ | None |
| RK326 | Neural-operator functional gradient boosting alpha | ranked list #326 | Neural operators | ⛔ | None |
| RK327 | Domain-adversarial (DANN) cross-market alpha transfer | ranked list #327; Ganin et al. 2016 | Transfer learning | ⛔ | None |
| RK328 | Neural rough-volatility path-signature factor model | ranked list #328; Futter, Horvath & Wiese 2023 | Rough paths | ⛔ | None |
| RK329 | Wasserstein distributionally robust rough-volatility hedging | ranked list #329; Gierjatowicz et al. | Derivatives hedging | ⛔ | None |
| RK330 | Rough-path signature delay-differential portfolio control | ranked list #330 | Rough paths / control | ⛔ | None |
| RK331 | Neural rough differential equation (neural RDE) order-book forecaster | ranked list #331 | Rough paths / deep learning | ⛔ | None |
| RK332 | Flow-matching order-flow generator | ranked list #332 | Generative market simulation | ⛔ | None |
| RK333 | Neural jump-diffusion Hawkes shock detector | ranked list #333 | Point processes / neural SDEs | ⛔ | None |
| RK334 | Neural controlled differential equation order-book trend anticipator | ranked list #334 | Rough paths / deep learning | ⛔ | None |
| RK335 | Wasserstein distributionally robust RL market making | ranked list #335 | RL market making / robust | ⛔ | None |
| RK336 | Score-based diffusion order-book simulator | ranked list #336; Berti, Prenkaj & Velardi 2025 | Generative market simulation | ⛔ | None |
| RK337 | Neural controlled jump-diffusion order-book pricing model | ranked list #337 | Rough paths / deep learning | ⛔ | None |
| RK338 | Recurrent neural Hawkes liquidity-shock detector | ranked list #338 | Point processes | ⛔ | None |
| RK339 | Multi-agent RL Nash market maker | ranked list #339 | RL market making | ⛔ | None |
| RK340 | Fractional-order cointegration VECM neural network | ranked list #340; Johansen & Nielsen 2012 | Fractional cointegration | ⛔ | None |
| RK341 | Multi-agent RL Stackelberg market maker | ranked list #341 | RL market making / game theory | ⛔ | None |
| RK342 | Rough-path signature Hawkes point-process forecaster | ranked list #342 | Rough paths / point processes | ⛔ | None |
| RK343 | Score-based diffusion order-book flow synthesizer | ranked list #343; Berti, Prenkaj & Velardi 2025 | Generative market simulation | ⛔ | None |
| RK344 | Multi-agent RL Stackelberg market-maker equilibrium | ranked list #344 | RL market making / game theory | ⛔ | None |
| RK345 | Multi-agent RL Stackelberg spread capture | ranked list #345 | RL market making / game theory | ⛔ | None |
| RK346 | Soft actor-critic (SAC) continuous-action trader | ranked list #346; Yang et al. 2020; Gort et al. 2022 | Deep RL | 🧪 (A1) · ❌ (as a trader) | None |
| RK347 | DDPG / TD3 continuous-control trader | ranked list #347; Yang et al. 2020; Gort et al. 2022 | Deep RL | 🧪 (A1) · ❌ (as a trader) | None |
| RK348 | Phase-space-reconstructed neural ODE (PSR-NODE) | ranked list #348 | Dynamical systems / deep learning | ⛔ | None |
| RK349 | Time-series GAN (TimeGAN) scenario generation | ranked list #349; Yoon et al. 2019 | Generative scenarios | ⏳ (stress-test tool) | Low |
| RK350 | Physics-informed Schrödinger volatility solver | ranked list #350 | Physics-informed ML | ⛔ | None |
| RK351 | MADDPG portfolio allocation | ranked list #351; Lowe et al. 2017 | Deep RL allocation | ⛔ | None |
| RK352 | Deep hedging with transaction costs | ranked list #352; Buehler et al. 2019 | Derivatives hedging | ⛔ | None |
| RK353 | Recurrent neural Hawkes execution timing | ranked list #353 | Execution / point processes | ⛔ | None |
| RK354 | Multi-agent RL evolutionary market maker | ranked list #354 | RL market making / evolutionary | ⛔ | None |
| RK355 | Recurrent neural Hawkes toxic-flow execution | ranked list #355 | Execution / point processes | ⛔ | None |
| RK356 | Recurrent neural Hawkes dynamic-inventory market maker | ranked list #356 | Market making / point processes | ⛔ | None |
| RK357 | Recurrent neural Hawkes toxic-flow execution pauser | ranked list #357 | Execution / point processes | ⛔ | None |
| RK358 | Multi-agent RL evolutionary execution routing | ranked list #358 | RL execution / evolutionary | ⛔ | None |
| RK359 | Multi-agent RL evolutionary market-making equilibrium | ranked list #359 | RL market making / evolutionary | ⛔ | None |
| RK360 | Multi-agent RL evolutionary execution allocator | ranked list #360 | RL execution / evolutionary | ⛔ | None |
| RK361 | Multi-agent deep RL order-book market maker | ranked list #361; Ganesh et al. 2019 | RL market making | ⛔ | None |
| RK362 | Koopman-operator MPC execution | ranked list #362 | Execution / Koopman | ⛔ | None |
| RK363 | TWAP execution | ranked list #363; Almgren & Chriss 2001 | Execution | 🧪 (AC lead, λ = 0) · ⛔ (not needed) | None |
| RK364 | VWAP execution | ranked list #364; Berkowitz, Logue & Noser 1988 | Execution | ⛔ | None |
| RK365 | Percent-of-volume (POV) execution | ranked list #365; BIS 2020 | Execution | ⛔ | None |
| RK366 | Implementation shortfall / Almgren-Chriss | ranked list #366; Perold 1988; Almgren & Chriss 2001 | Execution | 🧪 (AC lead) · ⏳ (shortfall measurement) | Low |
| RK367 | Hawkes-driven optimal execution with transient impact | ranked list #367; Alfonsi & Blanc 2016 | Execution | ⛔ | None |
| RK368 | Continuous-time mean-field control execution | ranked list #368; Cardaliaguet & Lehalle 2018 | Execution / mean-field games | ⛔ | None |
| RK369 | Multi-agent mean-field game execution routing | ranked list #369 | Execution / mean-field games | ⛔ | None |
| RK370 | Wasserstein distributionally robust optimal execution trajectory | ranked list #370 | Execution / robust optimisation | ⛔ | None |
| RK371 | Wasserstein distributionally robust Hawkes execution | ranked list #371 | Execution / robust optimisation | ⛔ | None |
| RK372 | PPO reinforcement-learning trader | ranked list #372; Yang et al. 2020; Gort et al. 2022 | Deep RL | 🧪 (A1) · ❌ (as a trader) | None |
| RK373 | Generative moment matching network (GMMN) portfolio simulator | ranked list #373; Hofert, Prasad & Zhu 2021 | Generative scenarios | ⏳ (stress-test tool) | Low |
| RK374 | Physics-informed (PINN) Burgers volatility model | ranked list #374 | Physics-informed ML | ⛔ | None |
| RK375 | Quantum support vector regression return predictor | ranked list #375 | Quantum machine learning | ⛔ | None |
| RK376 | Deep Koopman market-dynamics predictor | ranked list #376 | Koopman / deep learning | ⛔ | None |
| RK377 | Neural SDE stochastic-volatility arbitrage | ranked list #377; Gierjatowicz et al. | Derivatives pricing | ⛔ | None |
| RK378 | Tabular diffusion (TabDDPM) trajectory generator | ranked list #378; Kotelnikov et al. 2023 | Generative scenarios | ⛔ | None |
| RK379 | Fractional Brownian motion volatility-surface arbitrage | ranked list #379; Gatheral, Jaisson & Rosenbaum 2018 | Derivatives pricing | ⛔ | None |
| RK380 | Dynamic latent factor graph neural network (FactorGNN) | ranked list #380 | Graph ML / factor models | ⛔ | None |
| RK381 | Hyperbolic graph neural network stock selection | ranked list #381; Sawhney et al. 2021 | Graph ML | ⛔ | None |
| RK382 | Contractive autoencoder latent-factor anomaly detection | ranked list #382 | Anomaly detection | ⛔ | None |
| RK383 | Conditional WGAN-GP yield-curve synthesizer | ranked list #383; Guo 2024 | Generative scenarios | ⛔ | None |
| RK384 | Geometric deep learning non-Euclidean alpha predictor | ranked list #384 | Geometric deep learning | ⛔ | None |
| RK385 | Graph-attention supply-chain contagion stock predictor | ranked list #385; Cohen & Frazzini 2008 | Graph ML / economic links | ⛔ | None |
| RK386 | Transfer-entropy graph neural network alpha model | ranked list #386 | Information theory / graph ML | ⛔ | None |
| RK387 | Quantum-kernel SVM cross-sectional alpha | ranked list #387 | Quantum machine learning | ⛔ | None |
| RK388 | Dynamic copula-quantile regression neural network alpha | ranked list #388; Baruník, Hronec & Tobek | Distributional forecasting | ⛔ | None |
| RK389 | Quantum annealing entropic value-at-risk optimisation | ranked list #389 | Quantum optimisation | ⛔ | None |
| RK390 | Neural-operator flow-matching alpha forecaster | ranked list #390 | Neural operators / generative | ⛔ | None |
| RK391 | Rough-volatility signature deep hedging | ranked list #391; Horvath, Teichmann & Žurič 2021 | Derivatives hedging | ⛔ | None |
| RK392 | Fractional-order VAR macro allocator | ranked list #392 | Fractional time series | ⛔ | None |
| RK393 | Quantum neural network volatility-surface forecaster | ranked list #393 | Quantum machine learning | ⛔ | None |
| RK394 | Graph diffusion convolutional network stock alpha | ranked list #394 | Graph ML | ⛔ | None |
| RK395 | Score-based diffusion macro-factor synthesizer | ranked list #395; Chen et al. 2025 | Generative scenarios | ⏳ (stress-test tool) | None |
| RK396 | Riemannian graph-diffusion covariance estimator | ranked list #396 | Covariance estimation | ⛔ | None |
| RK397 | Quantum-annealing GNN covariance shrinkage | ranked list #397 | Covariance estimation | ⛔ | None |
| RK398 | Persistent-homology Betti-2 landscape macro contagion | ranked list #398 | Topological data analysis | ⛔ | None |
| RK399 | Score-based diffusion cross-sectional factor synthesizer | ranked list #399; Chen et al. 2025 | Generative scenarios | ⛔ | None |
| RK400 | Graph-attention Riemannian covariance shrinkage | ranked list #400 | Covariance estimation | ⛔ | None |

The remaining 13,924 rows of the ranked list are tabled in §8C, not here. Ranks 1–100 and 200–400 are researched (ranks 101–199 are not yet); the ones whose sources could not be found or checked are listed in §8C under "Research gaps".

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
## 8C. The ranked algorithm list (CSV import)

*Added 2026-10-27.* A list of 14,225 trading algorithms, each ranked
three ways by its compiler
(`trading_algorithms_ranked_ai_retail_described_plus_5.csv`), imported
whole: every row is in the tables below or on the pages they link to,
with whether volatility-ai implements it and a link to its
documentation. The ranks are the CSV's judgments, not measurements made
here: **potential effectiveness** (1 = strongest), **AI
implementability** (1 = easiest) and **retail advantage over
institutions** (1 = strongest). The import is committed with every field
of every row in
[`docs/algorithms/source/`](algorithms/source/);
[`docs/algorithms/README.md`](algorithms/README.md) explains the pages.

The list holds two kinds of row, and the CSV says which is which in its
own "Description Basis / Confidence" column:

* **Specific algorithms (ranks 1–425).** Named methods with their own
  descriptions: TSMOM, pairs trading, HRP, the options wheel, VWAP
  execution. 420 keep the list's original descriptions, which the CSV
  says it did not re-audit; five (ranks 31, 35, 47, 65 and 90) were
  added with research references and no backtest. Each has its own
  page: a card of the CSV's text until it is researched.
* **Title-reconstructed algorithms (ranks 426–14,225).** 13,800
  combinatorial names ("Hierarchical Scholarly Cointegrated Stock Pair
  MK-1") over only 378 distinct descriptions. The CSV rates every one
  *low confidence: reconstructed from the algorithm title; executable
  rules and source support are not established*, and its reference
  review calls the cited paper unrelated to trading in 8,872 of them (a
  condensed-matter physics paper on plasmon emission, for one). They are
  listed by rank on fourteen index pages and documented by concept, one
  page per shared description: a page per name would be ~30 MB of
  near-duplicates.

**The Implemented column** records code, separately from the fit marks
of §1:

| Value | Meaning |
|---|---|
| Yes | Runs on the platform: a registered strategy, a strategy option, an engine feature or a harness mode (`tools/rotation.py`, `tools/leverage_stepdown.py`). |
| Research code | The algorithm as described is tested standalone code in `research/` but is not wired into a strategy or a harness. §8B's transcriptions of ⛔ and ❌ entries count here. |
| Partial | A component, a long-only adaptation or a close variant exists; the algorithm as described does not. |
| No | Nothing in the repository. |

The values come from
[`docs/algorithms/implementation_status.csv`](algorithms/implementation_status.csv):
one row per algorithm that has code, with its ledger entries, code
references and a note. An algorithm not listed there is not
implemented. Every specific algorithm was checked against the entries
above and the code; none of the title-reconstructed ones has code.
`tools/tests/test_build_algorithm_ledger.py` fails if a code reference
stops resolving or the tables drift from those files.

**Ledger IDs.** A ranked algorithm gets an ID when it is researched:
`RK` and its rank in this import (RK1 is rank 1), kept even if a later
import re-ranks the list. Until then a row is keyed by its rank and
name.

**Keeping it current.** Edit `implementation_status.csv` (or put a new
export in `docs/algorithms/source/` and pass it with `--source`), then
run `python tools/build_algorithm_ledger.py`; `--check` reports stale
output. To research an algorithm, replace its generated page with a
written one (deleting the page's first, `generated` line), add an `RK`
entry below and in `research/catalog/registry.py`. The build then links
the page as researched and leaves it alone.

### RK1. Time-series momentum (TSMOM) ⛔ (as published) · ⏳ (long-or-cash)

Long an asset while its own trailing 12-month excess return is positive,
short while it is negative, each position sized to 40% volatility over
an ex-ante EWMA estimate (Moskowitz, Ooi & Pedersen 2012); positive for
every one of 58 futures markets, and since 1880 in every decade (Hurst,
Ooi & Pedersen 2017).

* **Fit:** The published form needs shorts and futures, and is what the
  excluded managed-futures ETFs run (X7). The long-or-cash form
  ("absolute momentum") fits and is not built.
* **Against:** Without the volatility scaling, TSMOM's alpha is
  statistically indistinguishable from buy-and-hold (Kim, Tse & Wald
  2016); asset-by-asset predictability is weak (Huang et al. 2020); the
  crisis alpha comes from the short side. Here, direction regimes gating
  the TQQQ grid measured poorly (ultimate-algorithm.md L1) and TSMOM
  filters on RSP/QQQ reached Calmar 0.23–0.47 (ultimate-rsp.md A1). A
  slow trend condition on calm *re-entry* is the form that has helped
  (L12).
* **Built:** `research/catalog/trend_following.py` — tsmom_weights (as
  published, X7). Next: a `tsmom` trend regime and the Ultimate bear
  filter with it.
* **Details:** [docs/algorithms/time-series-momentum-tsmom.md](algorithms/time-series-momentum-tsmom.md)

### RK2. Volatility-scaled trend following ⛔ (as published) · ⏳ (long-or-cash)

A trend signal sized by target volatility over forecast volatility. The
scaling carries most of TSMOM's published alpha (Kim, Tse & Wald 2016),
improves Sharpe ratios for equities through the leverage effect and
thins the left tail in every asset class (Harvey et al. 2018), and on a
3× daily-reset fund it addresses a drag of about 3σ² a year (Avellaneda
& Zhang 2010).

* **Fit:** The scaling half fits as a sizing change and is built (S4,
  `vol_target` on `hf_entry_gated`, unmeasured on TQQQ); the trend half
  is RK1's long-or-cash regime. A combined exposure target fits the
  `UltimateRspSizing` book.
* **Against:** Real-time volatility-managed portfolios generally fail to
  beat the unmanaged ones (Cederburg et al. 2020, 103 strategies);
  forecasts lag jumps. On RSP here, volatility targeting cut drawdown
  (V18) but lowered Calmar on top of the Ultimate-RSP votes (A4).
* **Built:** `research/catalog/trend_following.py` — tsmom_weights,
  pytrendfollow_position (X7, S2); `research/strategies/gated_local_reference_sizing.py`
  — the S4 scaling.
* **Details:** [docs/algorithms/volatility-scaled-trend-following.md](algorithms/volatility-scaled-trend-following.md)

### RK3. Dual momentum (absolute + relative) 🧪

Monthly, hold the asset with the best trailing 12-month return if it
also beats T-bills, otherwise the safe asset (Antonacci 2012; GEM: S&P
500 vs ACWI ex-US, else aggregate bonds). Absolute momentum is what cuts
drawdown.

* **Fit:** Long-only as published. X3 is a version of it: daily,
  63 sessions, a zero hurdle, cash as the safe asset, and the champion
  grid held in the chosen ETF, liquidated when rotated out.
* **Against:** Post-publication decay in an ETF replication; the choice
  among lookbacks and universes is statistically arbitrary and an
  unrewarded risk (ReSolve 2019); whipsaw and rebound crashes (Daniel &
  Moskowitz 2016).
* **Built:** `tools/rotation.py` — `--mode relative_strength` (X3).
  Unmeasured. A monthly rebalance and a T-bill hurdle would make GEM
  expressible.
* **Details:** [docs/algorithms/dual-momentum-absolute-relative.md](algorithms/dual-momentum-absolute-relative.md)

### RK4. Cross-asset carry composite ⛔

Hold high-carry markets (rate differentials, roll yield, yield plus roll-down) and short low-carry ones across asset classes; carry predicts returns in every asset class studied (Koijen et al. 2018).

* **Fit:** Out of scope: futures, forwards and short legs. The long-only shadows are RK28 and RK32.
* **Against:** Carry strategies fail together in global recessions, when this book also falls; currency carry is crash-prone.
* **Built:** Nothing.
* **Details:** [docs/algorithms/cross-asset-carry-composite.md](algorithms/cross-asset-carry-composite.md)

### RK5. Value-momentum composite ⏳ (long-only basket) · ⛔ (long/short)

Rank stocks on a fixed blend of value and momentum. Both are rewarded in eight markets and asset classes and are negatively correlated with each other, so the blend is steadier than either (Asness, Moskowitz & Pedersen 2013).

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Both legs can lag for years (value's 2017–2020 drawdown was about −55%); the negative correlation is a long/short property.
* **Built:** Nothing.
* **Details:** [docs/algorithms/value-momentum-composite.md](algorithms/value-momentum-composite.md)

### RK6. 12–1 momentum (skip-month) ⏳ (long-only basket) · ⛔ (long/short)

Rank stocks on the return from t−12 to t−2, buy the top decile (short the bottom in the academic form), hold a month. Novy-Marx (2012): the 12–7-month window carries most of the effect.

* **Fit:** Long-only fits the instrument rule but is a stock book; the warehouse has no stock universe. Momentum ETFs are the practical route.
* **Against:** Crashes in panic-state rebounds (Daniel & Moskowitz 2016: past losers +163% vs winners +8%, March–May 2009), mostly through the short leg.
* **Built:** Nothing; X3 ranks ETFs on 63 sessions with no skip month.
* **Details:** [docs/algorithms/12-1-momentum-skip-month.md](algorithms/12-1-momentum-skip-month.md)

### RK7. Cross-sectional momentum 🧪 (long-only ETF rotation, X3) · ⛔ (long/short)

Hold the leaders of a universe by trailing return. The general form of RK6, RK19 and RK65; the premium documented in eight markets comes from breadth and a short leg.

* **Fit:** Long-only over ETFs is X3. Each switch liquidates a grid sleeve, so switches are a cost here.
* **Against:** Few-asset rotations are specification bets; crashes after panics.
* **Built:** `tools/rotation.py` — `--mode relative_strength` (X3), top-1 only.
* **Details:** [docs/algorithms/cross-sectional-momentum.md](algorithms/cross-sectional-momentum.md)

### RK8. Commodity momentum + term structure ⛔

Long rising, backwardated commodity futures and short falling, contangoed ones: alphas of 10.14% (momentum) and 12.66% (term structure) alone, 21.02% double-sorted (Fuertes, Miffre & Rallis 2010); premia track inventories (Gorton et al. 2013).

* **Fit:** Out of scope: commodity futures and shorts. GLD as a gated defensive (X9) is the only commodity holding considered.
* **Against:** Roll and contract construction change backtests materially; thin, event-driven markets.
* **Built:** Nothing.
* **Details:** [docs/algorithms/commodity-momentum-term-structure.md](algorithms/commodity-momentum-term-structure.md)

### RK9. Fama–French five-factor portfolio ⛔ (as a portfolio) · ⏳ (as an attribution tool)

Market, size, value, profitability (RMW) and investment (CMA) factors; with RMW and CMA, HML is redundant in the US sample (Fama & French 2015). Rivals: the q-factor model; critique: the investment factor's construction (Cooper, Gulen & Ion 2024).

* **Fit:** Out of scope as a portfolio; useful as attribution: regress the champion's and Ultimate's daily returns on the five factors to separate alpha from leveraged beta.
* **Against:** Long/short factor portfolios and leverage.
* **Built:** Nothing.
* **Details:** [docs/algorithms/fama-french-five-factor-model-portfolio.md](algorithms/fama-french-five-factor-model-portfolio.md)

### RK10. State-filtered momentum ⏳

Run momentum only in favourable market states: about 0.93% a month after up markets vs −0.37% after down markets, 1929–1995 (Cooper et al.); crashes cluster in high-volatility panic states (Daniel & Moskowitz).

* **Fit:** The state filter is a causal regime map the repository already builds (N5, `--regime sma`); the momentum book must be long-only (X3 or a momentum ETF).
* **Against:** Few states and many thresholds: data-mining risk; contradicting evidence exists.
* **Built:** Pieces only: regimes (N5, trend regimes) and X3; X3 cannot yet be gated by a regime.
* **Details:** [docs/algorithms/state-filtered-momentum.md](algorithms/state-filtered-momentum.md)

### RK11. Quality minus junk (QMJ) ⛔ (as published) · ⏳ (long-only)

Long high-quality (profitable, growing, safe, high-payout) stocks, short junk. Quality trades at only a modest premium yet earns high risk-adjusted returns in the US and 24 countries (Asness, Frazzini & Pedersen 2019).

* **Fit:** Long/short is out; a quality ETF fits as a separate book. AQR's daily QMJ returns could serve as data for a risk regime.
* **Against:** Long/short; definitions vary by vintage; lags junk-led rebounds.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quality-minus-junk-qmj.md](algorithms/quality-minus-junk-qmj.md)

### RK12. Quality / profitability factor ⏳ (long-only basket) · ⛔ (long/short)

Favour profitable, strong-balance-sheet firms; profitable firms earn more despite higher valuations (Novy-Marx 2013) and RMW is one of the five factors (Fama & French 2015).

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Restatements and industry comparability; lags speculative markets.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quality-profitability-factor.md](algorithms/quality-profitability-factor.md)

### RK13. Gross profitability factor ⏳ (long-only basket) · ⛔ (long/short)

Rank on gross profits / total assets: predicts returns about as well as book-to-market, and controlling for it sharply improves value, especially in large liquid stocks (Novy-Marx 2013, 1962–2010).

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Needs release-date-aware statements and industry controls; overlaps what a Nasdaq-100 holder already owns.
* **Built:** Nothing.
* **Details:** [docs/algorithms/gross-profitability-factor.md](algorithms/gross-profitability-factor.md)

### RK14. 52-week-high momentum ⏳ (long-only basket) · ⛔ (long/short)

Buy stocks nearest their 52-week high. Nearness beats past returns as a forecaster and, unlike momentum, does not reverse (George & Hwang 2004).

* **Fit:** The ranking needs a stock universe. The same nearness measure is already the Ultimate strategy's bear filter (`bear_dd`, `bear_window=250`, L12).
* **Against:** Sample sensitivity; momentum-style crashes.
* **Built:** As a single-asset condition only: `UltimateSizing` bear filter.
* **Details:** [docs/algorithms/52-week-high-momentum.md](algorithms/52-week-high-momentum.md)

### RK15. Conservative investment factor ⏳ (long-only basket) · ⛔ (long/short)

Favour slow asset growers over aggressive investors: the CMA factor (Fama & French 2015) and the q-model's investment factor (Hou, Xue & Zhang 2015), both built on asset growth (Cooper, Gulen & Schill 2008).

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** The factors' power depends on how asset growth is constructed (Cooper, Gulen & Ion 2024).
* **Built:** Nothing.
* **Details:** [docs/algorithms/conservative-investment-factor.md](algorithms/conservative-investment-factor.md)

### RK16. Residual momentum ⏳ (long-only basket) · ⛔ (long/short)

Rank stocks on the trailing return of their Fama-French residuals (36-month regressions, months t−12..t−2): about twice the risk-adjusted profit of total-return momentum and more consistent.

* **Fit:** Stock book; needs a stock universe and factor returns.
* **Against:** Depends on the factor model and window; still exposed to rebounds.
* **Built:** Nothing.
* **Details:** [docs/algorithms/residual-momentum.md](algorithms/residual-momentum.md)

### RK17. 10-month moving-average risk filter 🧪

Hold while the month-end price is above its 10-month average, cash otherwise: equity-like returns with much lower volatility and drawdown since 1900 (Faber), but it lagged stocks in six of eight years after 2009.

* **Fit:** Built daily as `--regime sma` (200 sessions) and monthly as Faber TAA research code (C-E2). Every flip liquidates grid lots.
* **Against:** Whipsaw and late exits; direction regimes measured poorly on the TQQQ grid here (L1); plan.md's SMA results carry the lookahead (V16).
* **Built:** `research/strategies/trend_regimes.py` — sma_risk_on; `research/strategies/tactical_allocation.py` — faber_targets.
* **Details:** [docs/algorithms/10-month-moving-average-risk-filter.md](algorithms/10-month-moving-average-risk-filter.md)

### RK18. Low-volatility equity 🧪 (via defensive ETFs, X2)

Hold the least volatile or lowest-beta stocks: high-volatility stocks have long underperformed, and low-volatility portfolios had high returns with small drawdowns 1968–2008; benchmark mandates block the arbitrage (Baker, Bradley & Wurgler 2011).

* **Fit:** Low-volatility ETFs (USMV, SPLV) are candidate holdings in X2's defensive rotation, held only while their own NATR regime is calm.
* **Against:** Sector and rate concentration; lags speculative rallies; defensives fell with the market in March 2020.
* **Built:** `tools/rotation.py` — `--mode defensive` (X2) with USMV among the candidates.
* **Details:** [docs/algorithms/low-volatility-equity.md](algorithms/low-volatility-equity.md)

### RK19. Sector momentum rotation 🧪

Hold the strongest sector ETFs by trailing return. Industry momentum survives controls for size, value and stock momentum (Moskowitz & Grinblatt); factor momentum may explain it (Arnott et al. 2023). The CSV's #1 for retail advantage.

* **Fit:** Long-only ETFs; X3's harness runs it with a sector universe (each held ETF runs the grid).
* **Against:** Concentration and tracking error; XLC and XLRE are recent; short lookbacks whipsaw.
* **Built:** `tools/rotation.py` — `--mode relative_strength` with a sector `--universe` (never run).
* **Details:** [docs/algorithms/sector-momentum-rotation.md](algorithms/sector-momentum-rotation.md)

### RK20. Bond duration momentum ⛔ (as published) · ⏳ (long-or-cash Treasury ETF)

Long duration while bonds' own trailing return is positive. On the Treasury curve, duration-neutral long-only momentum earned up to ~120 bp a year (IR up to 0.79), 1996–2013 (Durham).

* **Fit:** Short duration and futures are out; a Treasury ETF gated by absolute momentum fits as an X2 defensive candidate.
* **Against:** Policy turns; small edges; TLT fell with stocks in 2022 (X5).
* **Built:** Nothing; X5 rejected TLT as an ungated hedge.
* **Details:** [docs/algorithms/bond-duration-momentum.md](algorithms/bond-duration-momentum.md)

### RK21. VIX-regime conditional equity exposure 🧪

Change exposure at VIX percentiles. The contrarian direction has the support: much higher excess returns follow implied volatility above its ~80th–85th percentile, 1990–2022 (Bansal & Stivers 2023), matching this project's capitulation-reversal result (L11).

* **Fit:** VIX as data fits and is partly built: V12 scales lots by implied volatility (VIXY proxy); VIX bands are research code (catalog R4).
* **Against:** High VIX follows falls, so part of the premium is the rebound; VIX is S&P, not Nasdaq (VXN).
* **Built:** V12 in the champion; `research/strategies/vix_bands.py`; `leads.vix_term_structure_regime`.
* **Details:** [docs/algorithms/vix-regime-conditional-equity-exposure.md](algorithms/vix-regime-conditional-equity-exposure.md)

### RK22. Volatility targeting / risk scaling 🧪

Scale exposure to a target volatility. Helps equities through the leverage effect and thins tails everywhere (Harvey et al. 2018); real-time versions often fail to beat the unmanaged book (Cederburg et al. 2020). The scaling half of RK2.

* **Fit:** Built as S4 (`vol_target` on `hf_entry_gated`, Yang-Zhang realized vol); measured on RSP (V18: drawdown −54%, edge in Feb–Jun 2020), not on TQQQ.
* **Against:** De-risks after falls, re-risks after calm; no gap protection; lowered Calmar on top of the Ultimate-RSP votes (A4).
* **Built:** `research/strategies/gated_local_reference_sizing.py` (S4); `config/probe_vol_target.yaml` unrun.
* **Details:** [docs/algorithms/volatility-targeting-risk-scaling.md](algorithms/volatility-targeting-risk-scaling.md)

### RK23. Drawdown-aware de-risking governor 🔬 (V11) · 🧪 (halt tiers)

Cut risk as drawdown deepens; Grossman & Zhou's optimum holds risky assets in proportion to the cushion above a drawdown floor. Measured here: V11's throttle on TQQQ cost 10.6 points of CAGR for 12.3 of drawdown, changing size, not shape (L4).

* **Fit:** Built: V11 throttle (wired), `DrawdownLadder` with halt and liquidation tiers, CPPI and Grossman-Zhou (research code). The unmeasured halt tier is the part that could change shape.
* **Against:** Acts after the damage; locks in losses and re-enters late; Grossman-Zhou loses optimality in discrete time.
* **Built:** V11 `dd_throttle_*`; `research/strategies/position_sizing.py` — DrawdownLadder; `research/catalog/leads.py` — cppi_path, grossman_zhou_multiplier.
* **Details:** [docs/algorithms/drawdown-aware-de-risking-governor.md](algorithms/drawdown-aware-de-risking-governor.md)

### RK24. ETF NAV / creation-redemption arbitrage ⛔

Create or redeem ETF units against the basket when the ETF trades away from NAV. Price-NAV bands are about 100 bp after removing stale pricing (US ETFs 2007–2014), and trading them earned abnormal returns before costs (Petajisto 2017).

* **Fit:** Needs authorized-participant access and short legs. The useful fact here is the reverse: a leveraged ETF's premium to NAV is an execution cost.
* **Against:** Creation units, AP agreements, basket execution and borrow are institutional.
* **Built:** `excluded.creation_redemption_action` (C-RJ6).
* **Details:** [docs/algorithms/etf-nav-creation-redemption-arbitrage.md](algorithms/etf-nav-creation-redemption-arbitrage.md)

### RK25. Index futures vs cash basis arbitrage ⛔

Trade index futures against the cash basket outside a cost band around fair value (spot carried at financing minus dividends). S&P 500 futures mispricing grows with maturity and is path-dependent (MacKinlay & Ramaswamy 1988).

* **Fit:** Futures and short legs; no long-only form.
* **Against:** Basket replication cost, dividend forecast error, funding and latency set the band.
* **Built:** Nothing.
* **Details:** [docs/algorithms/index-futures-vs-cash-basis-arbitrage.md](algorithms/index-futures-vs-cash-basis-arbitrage.md)

### RK26. Futures cash-and-carry basis trading ⛔

Buy spot and sell a rich future (or the reverse) when the basis departs from the cost of carry; deviations grow with maturity and are path-dependent (MacKinlay & Ramaswamy 1988).

* **Fit:** Out of scope: one leg is a short future or short underlying. The crypto version is research code and rejected (C-RJ2).
* **Against:** Financing, margin and delivery risk; retail cannot finance at institutional rates.
* **Built:** `research/catalog/crypto.py` — funding_carry_positions (C-RJ2, crypto only), timed on funding thresholds, not on the basis.
* **Details:** [docs/algorithms/futures-cash-and-carry-basis-trading.md](algorithms/futures-cash-and-carry-basis-trading.md)

### RK27. Shareholder yield factor ⏳

Rank on dividends plus net buybacks (and debt paydown) over market value. Payout and net payout yields predict returns where dividend yield does not, over time and across stocks (Boudoukh et al. 2007).

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Buybacks must be net of issuance and dilution; high yield can be a falling price.
* **Built:** Nothing.
* **Details:** [docs/algorithms/shareholder-yield-factor.md](algorithms/shareholder-yield-factor.md)

### RK28. Fixed-income carry and roll-down ⛔ (levered curve trade) · ⏳ (long-only ETF maturity choice)

Hold the bonds or maturities with the best yield plus roll-down net of financing; bond carry predicts returns (Koijen et al. 2018).

* **Fit:** The levered curve trade is out; choosing a Treasury ETF maturity by carry is in scope but competes with cash at the engine's money-market yield, which has no duration risk.
* **Against:** Rate shocks erase years of carry (2022; ledger X5).
* **Built:** Nothing.
* **Details:** [docs/algorithms/fixed-income-carry-and-roll-down.md](algorithms/fixed-income-carry-and-roll-down.md)

### RK29. Price + earnings momentum ⏳ (long-only basket) · ⛔ (long/short)

Buy stocks strong on both price momentum and earnings surprises or revisions; each predicts returns after controlling for the other, with little reversal (Chan, Jegadeesh & Lakonishok 1996).

* **Fit:** Stock book; needs point-in-time earnings and estimate data.
* **Against:** Data timing and restatements; crowding and valuation risk.
* **Built:** Nothing; the earnings calendar only sizes grid lots (V6).
* **Details:** [docs/algorithms/price-earnings-momentum.md](algorithms/price-earnings-momentum.md)

### RK30. FX carry trade ⛔

Long high-rate currencies, short low-rate ones: a >5-point annual spread, Sharpe ~0.6, 1983–2007, explained by a global slope factor (Lustig et al.); returns are negatively skewed and crash when funding dries up (Brunnermeier et al.).

* **Fit:** Out of scope: currencies and a short funding leg; it bets on calm, funded markets like the grid does.
* **Against:** Crash risk (2008, the 2015 franc de-peg).
* **Built:** Nothing.
* **Details:** [docs/algorithms/fx-carry-trade.md](algorithms/fx-carry-trade.md)

### RK31. Intangibles-adjusted value and profitability ⏳

Capitalise R&D (and optionally SG&A) into intangible capital, adjust book and profits, rank on adjusted value and profitability. Motivated by value's intangibles problem; an intangibles-intensity factor adds explanatory power (Financial Management 2025), but this hybrid itself is untested.

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Many free capitalisation choices; the CSV's second reference could not be identified.
* **Built:** Nothing.
* **Details:** [docs/algorithms/intangibles-adjusted-value-and-profitability-factor.md](algorithms/intangibles-adjusted-value-and-profitability-factor.md)

### RK32. Commodity futures roll yield ⛔ (futures) · ⏳ (long-only ETF)

Hold backwardated commodity futures, avoid contangoed ones. The average single commodity earned about zero (Erb & Harvey 2006); basis-sorted spot premia are 5–14% a year (Szymanowska et al. 2014).

* **Fit:** Futures and shorts are out; a roll-optimised long-only commodity ETF is an in-scope holding, as an inflation hedge (RK41), not a crash hedge.
* **Against:** Curve definitions and roll schedules vary; long-only commodities lagged for most of 2011–2020.
* **Built:** Nothing.
* **Details:** [docs/algorithms/commodity-futures-roll-yield.md](algorithms/commodity-futures-roll-yield.md)

### RK33. Market-neutral residual mean reversion ⛔ (market-neutral) · 🧪 (long-only s-score, C-MR2)

Trade the OU s-score of stock residuals on factor returns. PCA factors: Sharpe 1.44 after costs 1997–2007, 0.9 in 2003–2007; sector-ETF factors 1.1 with similar decay (Avellaneda & Lee 2010).

* **Fit:** The long-only half (C-MR2) buys single stocks that fell against their sector; net long, not this book.
* **Against:** Factor misspecification; crowding (August 2007); decayed through the 2000s.
* **Built:** `mean_reversion.s_score`, `s_score_long_signal` (C-MR2).
* **Details:** [docs/algorithms/market-neutral-residual-mean-reversion.md](algorithms/market-neutral-residual-mean-reversion.md)

### RK34. Futures calendar-spread mean reversion ⛔

Trade the near/far spread of one future back toward a carry or seasonal range. Mixed evidence: seasonal processing-spread rules failed out of sample (Cole et al. 1999); dynamic-hedge spreads in energy futures reported Sharpe above 2 (Lubnau & Todorova 2015); calendar-spread momentum adds nothing once unrealisable roll yield is removed (Shang, Serra & Garcia 2023).

* **Fit:** Futures with a short leg by construction.
* **Against:** Roll, delivery and margin effects; seasonal patterns are thin after costs.
* **Built:** Nothing.
* **Details:** [docs/algorithms/futures-calendar-spread-mean-reversion.md](algorithms/futures-calendar-spread-mean-reversion.md)

### RK35. Net stock issuance anomaly ⏳ (long-only basket) · ⛔ (long/short)

Tilt toward firms that shrink their share count. Post-1970, issuance predicts returns more significantly than size, value or momentum (Pontiff & Woodgate 2008), and in 41 countries (McLean, Pontiff & Watanabe 2009).

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Messy corporate actions; mostly insignificant before 1970; overlaps shareholder yield and asset growth.
* **Built:** Nothing.
* **Details:** [docs/algorithms/net-stock-issuance-anomaly.md](algorithms/net-stock-issuance-anomaly.md)

### RK36. Johansen cointegration basket trading ⛔

Trade the stationary basket from a Johansen cointegrating vector across three or more assets; a triple can cointegrate where no pair does (crude-oil futures, arXiv 2309.00875). Krauss (2017) surveys the family.

* **Fit:** Short weights in every basket. A Johansen test could join C-MR4's diagnostics, but nothing here trades baskets.
* **Against:** Multiple testing; breaks after index changes, mergers and regime shifts.
* **Built:** Nothing.
* **Details:** [docs/algorithms/johansen-cointegration-basket-trading.md](algorithms/johansen-cointegration-basket-trading.md)

### RK37. Cointegration-based pairs trading ⛔ (long/short) · 🧪 (long-only spread signal)

Trade an Engle–Granger stationary spread. US equities 1962–2014: 85 bp a month before costs, 33 bp after; best in turbulent markets (Rad, Low & Faff 2016).

* **Fit:** Short leg out; the long-only spread signal and X3's rotation are what remain.
* **Against:** Cointegration breaks; correlations converge in sell-offs; thin net returns.
* **Built:** `je_suis_tm.pair_trading_signals` (Q2), `pairs.engle_granger`, `pairs.spread_long_signal`.
* **Details:** [docs/algorithms/cointegration-based-pairs-trading.md](algorithms/cointegration-based-pairs-trading.md)

### RK38. Chandelier exit ⛔ (stop) · ⏳ (profit-only trail)

Exit a long when price falls k × ATR (commonly 3 × ATR(22)) below the highest high since entry. Credited to Chuck LeBeau, popularised by Alexander Elder; no published performance study.

* **Fit:** As a stop it realises losses (excluded). Applied only to lots already past their target it is a profit-only exit, which the project has in two forms (V10, the PSAR exit).
* **Against:** Gaps through the level; the ATR multiple is the whole design.
* **Built:** Profit-only relatives: V10 `TrailingTargetPolicy`, `grid_lifecycle.psar_profit_exits`. No ATR chandelier.
* **Details:** [docs/algorithms/chandelier-exit-trend-following.md](algorithms/chandelier-exit-trend-following.md)

### RK39. Merger arbitrage ⏳ (long the target, cash deals) · ⛔ (short acquirer hedge)

Buy announced targets below the offer and collect the spread on completion. 4,750 US deals 1963–1998: about 4% a year excess return after costs, with a payoff like writing index puts: losses cluster in sharp market declines (Mitchell & Pulvino 2001).

* **Fit:** Cash-deal targets are long-only stocks, but it is a separate event book needing deal data, and its losses coincide with this book's worst periods.
* **Against:** Deal breaks lose many times the spread; correlated breaks in crises; stock deals need a short leg.
* **Built:** Nothing.
* **Details:** [docs/algorithms/merger-arbitrage.md](algorithms/merger-arbitrage.md)

### RK40. Earnings estimate revision momentum ⏳ (long-only basket)

Hold stocks with rising analyst estimates. Forecast revisions, SUE and announcement returns each predict drifts beyond price momentum; analysts adjust sluggishly, especially after bad news (Chan, Jegadeesh & Lakonishok 1996).

* **Fit:** Long-only stocks pass the instrument rule; point-in-time estimate histories are licensed and not in the warehouse.
* **Against:** Revised analyst datasets create lookahead; overlaps with price momentum.
* **Built:** Nothing.
* **Details:** [docs/algorithms/earnings-estimate-revision-momentum.md](algorithms/earnings-estimate-revision-momentum.md)

### RK41. Inflation-regime asset rotation ⏳

Rotate among equities, bonds, TIPS and commodities by the inflation state. Over 95 years, unexpected inflation hurt stocks and bonds, commodities helped unevenly, and trend following protected most reliably (Neville et al. 2021).

* **Fit:** Long-only ETFs fit. FRED fetchers and the warehouse's lag-aware macro join make a causal monthly inflation regime buildable; 2022 (TQQQ −79%) was an inflation shock.
* **Against:** Release lags and revisions (lookahead if ignored); few inflation episodes to fit.
* **Built:** Pieces only: `research/ml/sources.py` (FRED), `engine/warehouse/queries.py` (lagged ASOF join), `tools/rotation.py`.
* **Details:** [docs/algorithms/inflation-regime-asset-rotation.md](algorithms/inflation-regime-asset-rotation.md)

### RK42. Cross-asset commodity term-structure carry ⛔

Market-neutral roll yield: long the most backwardated futures, short the most contangoed; the basis factor explains commodity spot premia (Szymanowska et al. 2014).

* **Fit:** Out of scope: commodity futures and a short leg. RK32's long-only ETF form is the in-scope one.
* **Against:** Delivery and notice-date liquidity; dollar-neutral is not volatility-neutral. One CSV reference (Pynecone) is unrelated.
* **Built:** Nothing.
* **Details:** [docs/algorithms/cross-asset-commodity-futures-term-structure-carry-roll-yield.md](algorithms/cross-asset-commodity-futures-term-structure-carry-roll-yield.md)

### RK43. Donchian / Turtle channel breakout ⛔ (as published) · 🧪 (scale-in pyramid, C-G5)

Buy an N-day high, exit an M-day low (Turtles: 20/10 and 55/20, ATR units, pyramiding). Channel and dual-MA rules earned positive mean excess returns net of costs in at least 22 of 28 commodity futures over 48 years (Szakmary et al. 2010).

* **Fit:** Stops and the short side are out. C-G5 keeps the scale-in: rebuild inventory on strength after a regime exit.
* **Against:** Long flat periods and whipsaw; the Turtles' edge has faded since the 1980s; weaker in equity indices.
* **Built:** `research/catalog/trend_following.py` (Turtle trades), `position_sizing.TurtlePyramid` (C-G5).
* **Details:** [docs/algorithms/donchian-turtle-channel-breakout.md](algorithms/donchian-turtle-channel-breakout.md)

### RK44. Supertrend ATR-band trend following ⏳ (long-or-cash regime) · ⛔ (stop-and-reverse)

A trailing band at the bar midpoint ± k × ATR (commonly 3 × ATR(10)) that ratchets with price; the trend flips when the close crosses it. No peer-reviewed evaluation found.

* **Fit:** A long-or-cash regime fits; expect it to behave like PSAR, which measured 0.06–0.17 CAGR/max DD as a regime here (L1).
* **Against:** Whipsaw in ranges; ATR widening delays re-entry after a crash bottom.
* **Built:** Nothing.
* **Details:** [docs/algorithms/supertrend-atr-band-trend-following.md](algorithms/supertrend-atr-band-trend-following.md)

### RK45. Post-earnings announcement drift (PEAD) ⏳ (long-only, small caps) · ⛔ (short side)

Buy after large positive earnings surprises as prices keep drifting. Long robust, but Martineau (2022) finds prices now absorb surprises on the day: no drift in large stocks since 2006, recently none in microcaps; others dispute the design or find an overnight version. The CSV's reference is Fink's (2021) survey of the literature.

* **Fit:** For the mega-caps that move this book the drift appears gone, so a surprise-conditioned V6 is not worth building.
* **Against:** Decaying, sample-dependent; costly immediate execution; survives, if at all, in illiquid names.
* **Built:** Nothing; V6 boosts lots on mega-cap earnings days (volatility, not surprise).
* **Details:** [docs/algorithms/post-earnings-announcement-drift-pead.md](algorithms/post-earnings-announcement-drift-pead.md)

### RK46. MACD signal-line crossover 🔬 (regime, measured) · ⛔ (long/short)

Long while the 12/26 EMA difference is above its 9-period EMA. Academic tests are parameter- and market-dependent. As a causal regime gating the TQQQ grid it measured 0.12–0.26 CAGR/max DD against NATR's 1.30–1.40 (L1).

* **Fit:** Built as a regime and measured; it lost to the volatility regime.
* **Against:** A transformation of price; lags at turns; whipsaws in ranges.
* **Built:** `trend_regimes.macd_risk_on` (`--regime macd`, Q1); quant-trading's crossover as research code.
* **Details:** [docs/algorithms/macd-signal-line-crossover.md](algorithms/macd-signal-line-crossover.md)

### RK47. Public activist-filing (13D) event strategy ⏳ (long-only event basket)

Parse new Schedule 13D filings and buy liquid targets that have not repriced. Activism announcements carried about a 7% abnormal return with no reversal over a year (Brav et al. 2008), but much of it comes at or before disclosure, so the post-filing return is unmeasured.

* **Fit:** Long-only stocks pass the instrument rule and EDGAR is free; a separate event book unrelated to the grid.
* **Against:** Announcement returns are not post-filing returns; lumpy event flow; thin targets.
* **Built:** Nothing.
* **Details:** [docs/algorithms/public-activist-filing-event-strategy.md](algorithms/public-activist-filing-event-strategy.md)

### RK48. Book-to-market value ⏳ (long-only basket) · ⛔ (long/short)

Buy cheap stocks by book-to-market (HML). A founding factor, redundant in the five-factor model (2015), and through its worst drawdown on record, about −55% to mid-2020.

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Value traps, sector bias, long drawdowns; fell more than growth in 2020.
* **Built:** Nothing.
* **Details:** [docs/algorithms/book-to-market-value.md](algorithms/book-to-market-value.md)

### RK49. Betting against beta (BAB) ⛔

Long low-beta assets levered to beta 1, short high-beta assets delevered to beta 1; leverage-constrained investors bid up high-beta assets (Frazzini & Pedersen 2014).

* **Fit:** Out of scope: the short leg and leverage are the strategy. Its long-only shadow is RK18.
* **Against:** Effectively equal-weighted and micro-cap heavy; costs cut profits by more than half (Novy-Marx & Velikov 2022).
* **Built:** Nothing.
* **Details:** [docs/algorithms/betting-against-beta-bab.md](algorithms/betting-against-beta-bab.md)

### RK50. Accrual anomaly ⏳ (long-only basket) · ⛔ (long/short)

Low-accrual (cash-backed) earners beat high-accrual ones (Sloan 1996), but hedge returns have decayed and are no longer reliably positive (Green, Hand & Soliman 2011).

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Arbitraged away after publication; accounting schema changes.
* **Built:** Nothing.
* **Details:** [docs/algorithms/accrual-anomaly.md](algorithms/accrual-anomaly.md)

### RK51. Asset-growth anomaly ⏳ (long-only basket) · ⛔ (long/short)

Low asset growers beat high growers, beyond value, size, momentum and accruals, including large caps; ~20% a year spread in the working paper (Cooper, Gulen & Schill 2008).

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** May be external financing rather than growth; the information sits in inventory and receivables (Cooper, Gulen & Ion 2024).
* **Built:** Nothing.
* **Details:** [docs/algorithms/asset-growth-anomaly.md](algorithms/asset-growth-anomaly.md)

### RK52. Dividend yield / dividend growth 🧪 (as an instrument, SPYD) · ⏳ (as a selection rule)

Select by dividend yield or growth. Weak on the evidence: payout yield beats dividend yield (Boudoukh et al. 2007), and investors treat dividends as free income, bidding payers up when rates are low (Hartzmark & Solomon 2019).

* **Fit:** SPYD (the S&P 500 High Dividend ETF) is already a grid and ML-sizing instrument here; a selection rule would need dividend histories.
* **Against:** High yield signals distress; sector and rate concentration.
* **Built:** SPYD as an instrument: `ml_regime_spyd`, `ml_reachability_spyd`, the SPYD sweeps.
* **Details:** [docs/algorithms/dividend-yield-dividend-growth.md](algorithms/dividend-yield-dividend-growth.md)

### RK53. CVaR / expected-shortfall optimization ⏳

Minimise the average loss beyond VaR; a linear programme over scenarios (Rockafellar & Uryasev 2000).

* **Fit:** Long-only ETF weights fit; it needs a multi-instrument book, which today exists only as the rotation harness's additive account.
* **Against:** Tail estimates are data-hungry and unstable; the sample's crises decide the weights.
* **Built:** Nothing.
* **Details:** [docs/algorithms/cvar-expected-shortfall-optimization.md](algorithms/cvar-expected-shortfall-optimization.md)

### RK54. Volatility-managed factor portfolio ⛔ (factor portfolios) · 🧪 (the scaling, S4)

Scale factor portfolios by inverse recent variance: large alphas in-sample (Moreira & Muir 2017), crash-free momentum (Barroso & Santa-Clara 2015), downside-volatility scaling better still (Wang & Yan 2021); real-time versions generally lose to the unmanaged factors (Cederburg et al. 2020). The CSV's reference, Hanauer & Windmüller (2023), finds volatility-scaled and dynamically scaled momentum roughly double plain momentum's Sharpe ratio.

* **Fit:** Long/short factors are out; the mechanism is S4/RK22 on this book. The CSV's reference could not be identified.
* **Against:** Out-of-sample instability; misses rebounds.
* **Built:** The scaling only: S4.
* **Details:** [docs/algorithms/volatility-managed-factor-portfolio.md](algorithms/volatility-managed-factor-portfolio.md)

### RK55. ADX-filtered trend following ⏳ (harvest gate) · ⛔ (long/short trend trade)

Trade a trend only when Wilder's ADX shows a strong trend. ADX measures strength, not direction, which makes it a candidate harvest gate (pause new lots in strong trends), as plan.md proposes. No academic study of ADX filtering found.

* **Fit:** A gate that pauses new grid lots never sells and is direction-agnostic, the kind of regime L1 favours. Ultimate-RSP already votes on Wilder's +DM.
* **Against:** Double smoothing makes it slow; V15's ADX flags carried the same-session lookahead (caveat 1).
* **Built:** ADX screened in V15; +DM is Ultimate-RSP's core vote. No ADX gate.
* **Details:** [docs/algorithms/adx-filtered-trend-following.md](algorithms/adx-filtered-trend-following.md)

### RK56. Hierarchical risk parity (HRP) 🧪

Cluster assets by correlation and allocate by recursive bisection in inverse variance; lower out-of-sample variance than the critical-line optimiser in Monte Carlo tests (López de Prado 2016).

* **Fit:** Built (A5); concurrent sleeves stretch the additive-account approximation.
* **Against:** Window and distance-metric sensitivity; no guarantee in correlated crashes; equal weight is the null (DeMiguel et al. 2009).
* **Built:** `research/strategies/hrp.py` — hrp_weights; `tools/rotation.py --mode hrp` (A5).
* **Details:** [docs/algorithms/hierarchical-risk-parity-hrp.md](algorithms/hierarchical-risk-parity-hrp.md)

### RK57. Low P/E value screen ⏳

Buy low-P/E stocks: low-P/E NYSE portfolios beat high-P/E ones by about 6–7% a year, ~1957–1971 (Basu 1977); later replications are mixed.

* **Fit:** A long-only stock basket fits the instrument rule, but the warehouse has no stock universe or fundamentals; an ETF is the practical vehicle, as a separate book from the grid.
* **Against:** Noisy, manageable earnings; value's long drawdowns.
* **Built:** Nothing.
* **Details:** [docs/algorithms/low-p-e-value-screen.md](algorithms/low-p-e-value-screen.md)

### RK58. Small-cap size premium ⏳

Tilt to small caps. The premium weakened after its discovery, but controlling for junk revives a stable one, not confined to micro-caps (Asness et al. 2018).

* **Fit:** A small-cap ETF fits as a separate holding; RSP's equal weighting is only a mild size tilt.
* **Against:** Capacity and costs; long stretches without a premium; recession sensitivity.
* **Built:** Nothing.
* **Details:** [docs/algorithms/small-cap-size-premium.md](algorithms/small-cap-size-premium.md)

### RK59. Liquidity factor ⛔ (illiquidity premium) · 🧪 (the measures, as data)

Illiquid stocks earn a premium (Amihud 2002); stocks sensitive to aggregate liquidity earned 7.5% a year more, 1966–1999 (Pástor & Stambaugh 2003).

* **Fit:** Harvesting an illiquidity premium is a capacity strategy, out of character here. The measures exist as research code (C-MS5) and are useful as fill-cost data for the grid.
* **Against:** Costs eat the illiquidity premium; liquidity-risk premia fail in liquidity crises.
* **Built:** `research/strategies/microstructure.py` — amihud_illiquidity, kyle_lambda, roll_spread (C-MS5).
* **Details:** [docs/algorithms/liquidity-factor.md](algorithms/liquidity-factor.md)

### RK60. Global minimum-variance portfolio ⏳

Lowest-variance long-only weights need no return forecasts; US stocks since 1968: about three-quarters of the market's risk with higher returns (Clarke et al. 2006).

* **Fit:** Long-only ETF weights fit; it needs a multi-instrument book, which today exists only as the rotation harness's additive account.
* **Against:** Concentrates in low-volatility or correlated assets (long bonds before 2022).
* **Built:** `research/catalog/je_suis_tm_projects.py` — markowitz_weights (min_variance, Q13).
* **Details:** [docs/algorithms/global-minimum-variance-portfolio.md](algorithms/global-minimum-variance-portfolio.md)

### RK61. Risk parity / equal risk contribution ⏳ (unlevered) · ⛔ (levered)

Equalise each asset's risk contribution (ERC lies between minimum variance and equal weight), classically levered to a target volatility; leverage aversion makes safe assets earn more per unit of risk (Asness et al. 2012).

* **Fit:** Long-only ETF weights fit; it needs a multi-instrument book, which today exists only as the rotation harness's additive account.
* **Against:** Levered bonds are out of scope and failed in 2022; contributions jump with correlations.
* **Built:** HRP only (A5); ERC is not built.
* **Details:** [docs/algorithms/risk-parity-equal-risk-contribution.md](algorithms/risk-parity-equal-risk-contribution.md)

### RK62. Dual moving-average crossover 🧪 (as a regime) · ⛔ (as a long/short trade)

Long while a short moving average is above a long one. Early support (Brock et al. 1992) was re-tested for data snooping (Sullivan, Timmermann & White 1999); equivalent in general form to TSMOM (Levine & Pedersen 2016).

* **Fit:** A regime fits; a two-SMA regime is a one-function addition beside `sma_risk_on`.
* **Against:** Lag and whipsaw; MACD (an EMA crossover) gating the TQQQ grid measured 0.12–0.26 CAGR/max DD vs 1.30–1.40 for NATR (L1).
* **Built:** `research/catalog/je_suis_tm.py` — macd_crossover (an SMA crossover, Q1); `tactical_allocation.faber_targets` (20/200).
* **Details:** [docs/algorithms/dual-moving-average-crossover.md](algorithms/dual-moving-average-crossover.md)

### RK63. Black–Litterman allocation ⏳

Blend market-implied equilibrium returns with explicit views and confidences, then optimise (Black & Litterman 1992; He & Litterman 1999).

* **Fit:** Long-only ETF weights fit; it needs a multi-instrument book, which today exists only as the rotation harness's additive account.
* **Against:** Needs calibrated views; outputs depend on the prior, tau and Omega; not a timing signal.
* **Built:** Nothing.
* **Details:** [docs/algorithms/black-litterman-allocation.md](algorithms/black-litterman-allocation.md)

### RK64. Triple EMA / moving-average ribbon ⏳ (as a regime) · ⛔ (as a long/short trade)

Trend confirmed only while several moving averages are stacked in order (Guppy's 6 short + 6 long EMAs). No academic evidence specific to ribbons; a lagged member of the crossover family.

* **Fit:** A regime fits, but a ribbon is mostly off in chop, where this grid earns most.
* **Against:** More lag and more parameters.
* **Built:** Single TA-Lib averages were screened in V15; no ribbon rule.
* **Details:** [docs/algorithms/triple-ema-moving-average-ribbon.md](algorithms/triple-ema-moving-average-ribbon.md)

### RK65. Cross-sectional factor momentum rotation ⏳

Tilt toward the factors with the best trailing returns. Mixed evidence: factor returns are autocorrelated (Ehsani & Linnainmaa; Gupta & Kelly, 65 factors), but only 22–27% of factors show strong continuation and the strategies do not beat long-only factors (Fan et al. 2022).

* **Fit:** Long-only factor ETFs fit and X3's harness can run them; a separate allocation book from the grid.
* **Against:** Long-only factor ETFs are mostly market beta, so the spread to rotate is small.
* **Built:** Nothing as a factor rotation; X3 with factor ETFs as `--universe`.
* **Details:** [docs/algorithms/cross-sectional-factor-momentum-rotation.md](algorithms/cross-sectional-factor-momentum-rotation.md)

### RK66. Maximum-diversification portfolio ⏳

Maximise the diversification ratio (average asset volatility over portfolio volatility); every held asset ends up with the same correlation to the portfolio (Choueifaty & Coignard 2008; Choueifaty et al. 2013).

* **Fit:** Long-only ETF weights fit; it needs a multi-instrument book, which today exists only as the rotation harness's additive account.
* **Against:** Covariance-dependent; diversification vanishes in correlation spikes; thinner independent evidence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/maximum-diversification-portfolio.md](algorithms/maximum-diversification-portfolio.md)

### RK67. ATR-based position sizing 🧪 (volatility-normalised lots) · ⛔ (stop-distance form)

Size each position so one ATR (or the stop distance) risks a fixed fraction of equity; the Turtle unit is 1% of equity over the 20-day ATR (Faith 2003).

* **Fit:** Stops are out of scope; volatility-normalised lots are already V7 (ratio) and S4 (target), and the Turtle units are research code (C-G5).
* **Against:** Gaps exceed planned risk; per-trade sizing does not cap total open exposure.
* **Built:** `research/strategies/position_sizing.py` — turtle_unit_shares, turtle_atr, TurtlePyramid (C-G5).
* **Details:** [docs/algorithms/atr-based-position-sizing.md](algorithms/atr-based-position-sizing.md)

### RK68. Dual Thrust breakout ⛔ (trade) · 🧪 (lower band as a buy gate, N1)

Range = max(HH−LC, HC−LL) over N days; long above open + k₁ × range, short below open − k₂ × range, flat at the close. No primary or academic source found.

* **Fit:** The trade is out; the lower band is the N1 buy gate on `hf_entry_gated`.
* **Against:** Parameter-heavy; stops and end-of-day flattening realise losses.
* **Built:** `je_suis_tm.dual_thrust_trades` (Q7); `entry_gates.BreakdownGate` mode `dual_thrust` (N1).
* **Details:** [docs/algorithms/dual-thrust-breakout.md](algorithms/dual-thrust-breakout.md)

### RK69. London session breakout ⛔ (trade) · 🧪 (US-hours gate, N2)

Trade a break of the Asian-session range after the London open, with a stop and target, flat by session end. No academic test found; the nearest published evidence (equity ORB) does not survive a third-party replication with spread and slippage.

* **Fit:** FX and stops are out; the idea mapped onto US hours is the N2 opening-range gate, and N3 is its gap variant.
* **Against:** Daylight-saving and server-time handling; stops realise losses.
* **Built:** `je_suis_tm.london_breakout_trades` (Q4); `entry_gates.BreakdownGate` modes `opening_range`/`prior_low` (N2, N3).
* **Details:** [docs/algorithms/london-session-breakout.md](algorithms/london-session-breakout.md)

### RK70. Parabolic SAR trend / stop 🔬 (regime, measured) · 🧪 (profit-only exit) · ⛔ (stop-and-reverse)

Wilder's accelerating trailing level (AF 0.02 step, 0.20 cap) that reverses on a cross. As a causal regime gating the TQQQ grid it measured 0.06–0.17 CAGR/max DD (L1).

* **Fit:** Built as a regime (lost) and as a profit-only exit (in scope by construction, unmeasured).
* **Against:** Reverses too often in ranges; gaps fill below the stop.
* **Built:** `trend_regimes.psar_risk_on` (`--regime psar`, Q8); `grid_lifecycle.psar_profit_exits` (catalog M6).
* **Details:** [docs/algorithms/parabolic-sar-trend-stop.md](algorithms/parabolic-sar-trend-stop.md)

### RK71. Heikin-Ashi trend filter 🔬 (regime, measured)

Synthetic smoothed candles (close = OHLC average, open = midpoint of the previous synthetic candle); runs of one colour mark a trend. As a causal regime gating the TQQQ grid it measured −0.09–0.11 CAGR/max DD, the worst of six (L1).

* **Fit:** Built and measured; it lost. Nothing further to build.
* **Against:** HA prices are not fill prices; smoothing adds lag.
* **Built:** `trend_regimes.heikin_ashi_risk_on` (`--regime heikin_ashi`, Q3); quant-trading's trade script as research code.
* **Details:** [docs/algorithms/heikin-ashi-trend-filter.md](algorithms/heikin-ashi-trend-filter.md)

### RK72. Distance-based pairs trading ⛔

Pair stocks with the closest normalised price paths and trade 2-sigma divergences. Top-20 pairs earned 0.86% a month in 1962–1988, 0.37% in 1989–2002 and 0.24% in 2003–2009 before costs (Do & Faff 2010); 38 bp after costs over 1962–2014 (Rad et al. 2016).

* **Fit:** Short leg; X3's rotation is the long-only remainder.
* **Against:** Correlation is not convergence; decay; costs.
* **Built:** Nothing.
* **Details:** [docs/algorithms/distance-based-pairs-trading.md](algorithms/distance-based-pairs-trading.md)

### RK73. Kalman-filter dynamic-hedge pairs ⛔ (long/short) · 🧪 (long-only spread signal)

Estimate a drifting hedge ratio with a Kalman filter and trade the forecast error; the state-space view of pairs goes back to Elliott, van der Hoek & Malcolm (2005).

* **Fit:** Short leg out; the filter and a long-only spread signal exist as research code.
* **Against:** The noise ratio decides whether it tracks drift or noise.
* **Built:** `pairs.KalmanHedgeRatio`, `pairs.spread_long_signal`.
* **Details:** [docs/algorithms/kalman-filter-dynamic-hedge-pairs.md](algorithms/kalman-filter-dynamic-hedge-pairs.md)

### RK74. Copula-based pairs trading ⛔

Trade extreme conditional probabilities from a fitted copula. Bivariate copula pairs: 43 bp a month before costs, 5 bp after, 1962–2014 (Rad et al. 2016); vine copulas on the S&P 500: 9.25% a year after costs, Sharpe 1.12, 1992–2015 (Stübinger et al. 2018).

* **Fit:** Short leg.
* **Against:** Data-hungry tail estimation; dependence changes in crises.
* **Built:** Nothing.
* **Details:** [docs/algorithms/copula-based-pairs-trading.md](algorithms/copula-based-pairs-trading.md)

### RK75. Ornstein–Uhlenbeck spread trading ⛔ (spread) · 🧪 (OU diagnostics)

Fit an OU process to a spread and set bands from its parameters: Avellaneda–Lee s-scores, or Bertram's (2010) closed-form bands maximising expected return or Sharpe per unit time.

* **Fit:** Spreads are out. OU half-life and Hurst diagnostics (C-MR4) already test whether the grid's single-price mean-reversion bet holds.
* **Against:** Thresholds are fragile when kappa and sigma drift.
* **Built:** `mean_reversion.s_score` (C-MR2), `mean_reversion.half_life` (C-MR4).
* **Details:** [docs/algorithms/ornstein-uhlenbeck-spread-trading.md](algorithms/ornstein-uhlenbeck-spread-trading.md)

### RK76. PCA residual statistical arbitrage ⛔

RK33 with principal-component factors: Sharpe 1.44 after costs over 1997–2007, 0.9 over 2003–2007 (Avellaneda & Lee 2010).

* **Fit:** A market-neutral stock book; the warehouse has no stock universe.
* **Against:** Universe, windows, costs and crowding; eigenvectors rotate in crises.
* **Built:** The s-score on ETF residuals only (C-MR2).
* **Details:** [docs/algorithms/pca-residual-statistical-arbitrage.md](algorithms/pca-residual-statistical-arbitrage.md)

### RK77. ATR volatility-expansion breakout ⛔ (breakout trade)

Enter on a range break while ATR or realised volatility expands (Larry Williams' volatility breakout is the best-known form). No academic test found. This project's evidence runs the other way: a NATR spike is its signal to step out of leveraged lots (L1, L6).

* **Fit:** As a breakout trade, out. Its parts exist with the signs the evidence supports: the downside break is the N1 gate, volatility expansion is the turbulent regime.
* **Against:** False breaks at news and overnight gaps; the stop realises losses; expansion often follows the break.
* **Built:** Nothing as a trade; relatives: N1 (`BreakdownGate`), the NATR regime.
* **Details:** [docs/algorithms/atr-volatility-expansion-breakout.md](algorithms/atr-volatility-expansion-breakout.md)

### RK78. Multi-timeframe trend agreement ⏳ (long-or-cash) · ⛔ (with a short side)

Hold only when short-, medium- and long-horizon trend signals agree (Elder's Triple Screen). The literature usually averages horizons instead (1-, 3- and 12-month TSMOM over a century: Hurst, Ooi & Pedersen 2017); no study of the all-must-agree form found.

* **Fit:** A long-or-cash variant of RK1/RK2. Direction regimes lose to the volatility regime here (L1), and agreement makes them slower.
* **Against:** Higher-timeframe leakage; each confirmation adds lag.
* **Built:** Nothing; daily regimes and intraday gates exist but nothing requires agreement.
* **Details:** [docs/algorithms/multi-timeframe-trend-agreement.md](algorithms/multi-timeframe-trend-agreement.md)

### RK79. Opening gap continuation 🧪 (downside as buy gates, N3/X1) · ⛔ (day trade)

Trade in a large gap's direction once the open confirms it. The first half-hour return from the prior close predicts the last half-hour in SPY 1993–2013 (Gao et al. 2018), and US index prices tend to move in the gap's direction on gap days, 1928–2018 (Plastun et al. 2020).

* **Fit:** The day trade is out. The downside half is built twice as buy gates (N3 prior-low gap, X1 intraday momentum); both unmeasured.
* **Against:** Opening-auction slippage; the edge is small against costs; stock gaps around earnings differ.
* **Built:** `entry_gates.BreakdownGate` mode `prior_low` (N3); `entry_gates.IntradayMomentumGate` (X1).
* **Details:** [docs/algorithms/opening-gap-continuation.md](algorithms/opening-gap-continuation.md)

### RK80. Convertible bond arbitrage ⛔

Long convertibles, short the stock's delta. A buy-and-hedge factor explains much of convertible-arbitrage fund returns; market-wide extremes and convertible supply matter (Agarwal et al. 2011).

* **Fit:** Convertibles and short stock.
* **Against:** Borrow recalls, credit deterioration, jumps, forced deleveraging (2005, 2008).
* **Built:** Nothing.
* **Details:** [docs/algorithms/convertible-bond-arbitrage.md](algorithms/convertible-bond-arbitrage.md)

### RK81. Capital structure arbitrage ⛔

Trade CDS against equity when a structural model (CreditGrades) disagrees with the market. 261 obligors: single trades can lose heavily; an equal-weighted portfolio had Sharpe ratios like other fixed-income arbitrage (Yu 2006).

* **Fit:** CDS, bonds and short legs.
* **Against:** Model, recovery and basis risk; legs may never converge.
* **Built:** Nothing.
* **Details:** [docs/algorithms/capital-structure-arbitrage.md](algorithms/capital-structure-arbitrage.md)

### RK82. Closed-end fund discount reversion ⏳

Buy closed-end funds at unusually wide discounts to NAV and hold for the narrowing. A 20% discount predicted a 12-month return about 6 points higher than no discount, from discount mean reversion (Pontiff 1995, confirming Thompson 1978).

* **Fit:** Long-only listed funds fit the instrument rule, but it is a separate income book; daily NAVs and distributions are not in the warehouse.
* **Against:** Discounts persist or widen; stale NAVs; leverage, fees, return-of-capital distributions; thin trading.
* **Built:** Nothing.
* **Details:** [docs/algorithms/closed-end-fund-discount-reversion.md](algorithms/closed-end-fund-discount-reversion.md)

### RK83. Triangular FX arbitrage ⛔

Trade the three legs when executable cross rates violate the triangle identity. Opportunities exist but are small, brief and declining; profiting needs an unfeasibly large share of them (Fenn et al. 2009); exploitable on EBS before the mid-2000s (Ito et al. 2020).

* **Fit:** FX and a latency race.
* **Against:** Legging, rejects, credit limits; gone before execution.
* **Built:** `crypto.find_arbitrage_cycle`, `conversion_rates` (A7, crypto venues).
* **Details:** [docs/algorithms/triangular-fx-arbitrage.md](algorithms/triangular-fx-arbitrage.md)

### RK84. Crypto perpetual funding-rate capture ❌

Long spot, short the perpetual to collect funding. Crypto futures carry reached about 60% a year, varies strongly and is crash-prone through margin spikes and liquidations (BIS WP 1087).

* **Fit:** Crypto is outside the instrument rules.
* **Against:** Variable funding; liquidation, exchange and custody risk.
* **Built:** `crypto.funding_carry_positions`, `funding_carry_pnl` (C-RJ2).
* **Details:** [docs/algorithms/crypto-perpetual-funding-rate-capture.md](algorithms/crypto-perpetual-funding-rate-capture.md)

### RK85. Spot-perpetual basis arbitrage ❌

Open long spot / short perpetual when basis plus expected funding beats costs. Perpetual deviations from no-arbitrage prices are large, co-move and shrink over time; an implied arbitrage strategy earns high Sharpe ratios (He et al., arXiv 2212.06888).

* **Fit:** Crypto is outside the instrument rules.
* **Against:** Basis widens, funding flips, venues fail.
* **Built:** `crypto.funding_carry_positions` (C-RJ2), which enters and exits on funding thresholds and never reads the basis; the basis rule is not built.
* **Details:** [docs/algorithms/spot-perpetual-basis-arbitrage.md](algorithms/spot-perpetual-basis-arbitrage.md)

### RK86. Yield-curve steepener / flattener ⛔

DV01-matched long/short across two maturities to bet on the slope; slope is the second of three factors behind >95% of yield variation (Litterman & Scheinkman 1991). Forward rates forecast bond excess returns in sample (Fama & Bliss 1987; Cochrane & Piazzesi 2005) but add no consistent value out of sample (Thornton & Valente 2012); no study found that a rules-based slope trade earns a premium.

* **Fit:** Out of scope as a trade; the 10y–2y slope is usable as data for a slow recession regime.
* **Against:** Convexity, carry and basis risk; a policy-timing bet.
* **Built:** Nothing.
* **Details:** [docs/algorithms/yield-curve-steepener-flattener.md](algorithms/yield-curve-steepener-flattener.md)

### RK87. Option dispersion trading ⛔

Short index volatility against long component volatility to collect the correlation risk premium. Correlation risk is priced in S&P 100 options, but the strategy's high alpha does not survive realistic trading frictions (Driessen, Maenhout & Vilkov 2009).

* **Fit:** Options are out of scope.
* **Against:** Correlation spikes in crashes; jumps and earnings; costs across dozens of option legs.
* **Built:** Nothing.
* **Details:** [docs/algorithms/option-dispersion-trading.md](algorithms/option-dispersion-trading.md)

### RK88. Distributionally robust CVaR allocation ⏳

Minimise worst-case CVaR over a Wasserstein ball around the empirical distribution; tractable convex programmes with finite-sample guarantees (Mohajerin Esfahani & Kuhn 2018).

* **Fit:** Long-only ETF weights fit; it needs a multi-instrument book, which today exists only as the rotation harness's additive account.
* **Against:** The radius is the whole design; can be very conservative.
* **Built:** Nothing.
* **Details:** [docs/algorithms/distributionally-robust-cvar-allocation.md](algorithms/distributionally-robust-cvar-allocation.md)

### RK89. Autoencoder latent-factor stat arb ⛔

Trade residuals against an autoencoder factor model. Conditional autoencoders price the cross-section with small out-of-sample errors (Gu, Kelly & Xiu 2021); a deep-learning stat-arb pipeline reports about 20% a year at under 6% volatility after costs (arXiv 2106.04028).

* **Fit:** A market-neutral stock book with a short leg.
* **Against:** Residuals may be model error; overfitting; needs walk-forward refits.
* **Built:** Nothing.
* **Details:** [docs/algorithms/autoencoder-latent-factor-statistical-arbitrage.md](algorithms/autoencoder-latent-factor-statistical-arbitrage.md)

### RK90. Long-term industry reversal with valuation confirmation ⏳ (long-only sector ETFs)

Buy industries that lagged for years when they are cheap and stabilising. 48 US industries 1963–2013 show long-term reversals lasting years (Bornholt et al. 2015); UK losing industries beat winners over five years (Wu & Mazouz 2016). The valuation filter is the CSV's proposal.

* **Fit:** Long-only sector ETFs pass the instrument rule; a slow separate book on the rotation harness with a reversed ranking; valuations are not in the warehouse.
* **Against:** Structural decline looks like a cheap loser; value traps; multi-year waits; few independent periods for sector ETFs.
* **Built:** Nothing; X3 ranks the other way (trailing strength).
* **Details:** [docs/algorithms/long-term-industry-reversal-with-valuation-confirmation.md](algorithms/long-term-industry-reversal-with-valuation-confirmation.md)

### RK91. iNAV dislocation ETF arbitrage ⛔

Rebuild intraday NAV from live holdings quotes and post passive orders against ETF dislocations, hedged, flat by the close; the premise (about 100 bp bands, short-term mean reversion; Petajisto 2017) is documented, this exact form is not.

* **Fit:** Market making with a hedge leg and forced end-of-day exits.
* **Against:** Adverse selection on passive fills; Level 2 data on every holding.
* **Built:** Only the AP decision (C-RJ6).
* **Details:** [docs/algorithms/inav-dislocation-etf-arbitrage.md](algorithms/inav-dislocation-etf-arbitrage.md)

### RK92. Fed ON RRP / T-bill liquidity arbitrage ⛔

Trade T-bill yields against the ON RRP rate and SOFR. The ON RRP is a floor for money-market rates, yet bills and repo traded below it in 2021 as facility use rose about $2 trillion (FEDS Notes 2023); no study of a trading strategy found.

* **Fit:** Repo leverage and facility access are institutional. The in-scope question is where regime-exit cash sits (bills, a bill ETF, a money fund), which backtests already model with a money-market yield.
* **Against:** Basis-point spreads need leverage; facility access is restricted.
* **Built:** Data only: SOFR and RRPONTSYD are registered FRED inputs; idle cash accrues a money-market yield.
* **Details:** [docs/algorithms/fed-otc-liquidity-sweep-reverse-repo-arbitrage.md](algorithms/fed-otc-liquidity-sweep-reverse-repo-arbitrage.md)

### RK93. Cointegrated triplet basket stat arb ⛔

RK36 with three assets (A − αB − βC). A triple can cointegrate where no pair does (three crude-oil futures, arXiv 2309.00875); Galenko, Popova & Popova (2012) give a trading method for three or more cointegrated assets; no equity-triplet study found.

* **Fit:** Short legs.
* **Against:** Fundamental shifts leave permanent divergence; more search, more false discoveries.
* **Built:** Nothing.
* **Details:** [docs/algorithms/cointegrated-triplet-basket-statistical-arbitrage.md](algorithms/cointegrated-triplet-basket-statistical-arbitrage.md)

### RK94. Dynamic copula-GARCH pair trading ⛔

RK74 with GARCH marginals and a time-varying copula. Vine copulas with time-varying dependence: 9.25% a year after costs on the S&P 500, 1992–2015 (Stübinger et al. 2018); no copula-GARCH pairs study verified.

* **Fit:** Short leg.
* **Against:** Two layers of estimation; window and family sensitivity.
* **Built:** Nothing.
* **Details:** [docs/algorithms/dynamic-copula-garch-multivariate-pair-trading.md](algorithms/dynamic-copula-garch-multivariate-pair-trading.md)

### RK95. Asymmetric tail-risk parity ⏳

Equalise contributions to expected shortfall (or semivariance) instead of variance: CVaR risk budgets (Boudt, Carl & Peterson 2013); CVaR-based risk parity with ML forecasts (Sheng et al. 2025).

* **Fit:** Long-only ETF weights fit; it needs a multi-instrument book, which today exists only as the rotation harness's additive account.
* **Against:** Tail estimates need long samples; no source found for the semivariance form or an out-of-sample comparison.
* **Built:** Nothing.
* **Details:** [docs/algorithms/asymmetric-tail-risk-parity-allocation.md](algorithms/asymmetric-tail-risk-parity-allocation.md)

### RK96. PCA eigenportfolios stat arb ⛔

RK76 described through its eigenportfolios (eigenvector weights over stock volatilities); Sharpe 1.44 after costs over 1997–2007, 0.9 over 2003–2007 (Avellaneda & Lee 2010).

* **Fit:** A market-neutral stock book.
* **Against:** Loadings drift and rotate in crises.
* **Built:** The s-score on ETF residuals only (C-MR2).
* **Details:** [docs/algorithms/principal-component-analysis-pca-eigenportfolios-statistical-arbitrage.md](algorithms/principal-component-analysis-pca-eigenportfolios-statistical-arbitrage.md)

### RK97. Wasserstein distributionally robust stat arb ⛔

Choose pair thresholds that are best under the worst distribution in a Wasserstein ball. The DRO machinery exists (RK88); no paper applying it to stat-arb thresholds found; the CSV's arXiv reference is an unrelated biomedical-engineering paper.

* **Fit:** Short leg.
* **Against:** The radius decides everything; slow over many pairs.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-statistical-arbitrage.md](algorithms/wasserstein-distributionally-robust-statistical-arbitrage.md)

### RK98. Adversarial domain-generalisation cross-market momentum ⏳ (in principle) · not a priority

Train a momentum model with an adversary that penalises market-specific features, so the rule generalises across markets. No momentum study found; DomainBed found tuned ordinary training matched domain-generalisation methods.

* **Fit:** A long-only ranking would pass the instrument rule; no evidence justifies the machinery.
* **Against:** Unstable adversarial training; few independent regimes to learn from.
* **Built:** Nothing.
* **Details:** [docs/algorithms/adversarial-domain-generalization-cross-market-momentum.md](algorithms/adversarial-domain-generalization-cross-market-momentum.md)

### RK99. Conformally constrained risk parity ⏳

ERC weights plus a conformal bound on portfolio loss. Conformal portfolio selection (Kato 2024) and conformal VaR under nonstationarity (Schmitt 2026) exist separately; no published method combines them with ERC.

* **Fit:** Conformal intervals and conformal sizing exist as research code (catalog S5); ERC does not. A conformal check on the single grid's total exposure is the more practical use.
* **Against:** Exchangeability fails for returns; needs adaptive conformal inference; two layers of estimation.
* **Built:** Pieces: `position_sizing.split_conformal_interval`, `conformal_long_size`; HRP.
* **Details:** [docs/algorithms/conformally-constrained-risk-parity-portfolio.md](algorithms/conformally-constrained-risk-parity-portfolio.md)

### RK100. Causal-discovery (DAG) pair selection ⛔

Select pairs or leader–follower trades from a causal graph (PC, NOTEARS, PCMCI) instead of correlation. No PC/NOTEARS pair-selection study found; nearest: lead-lag optimal causal paths on minute S&P 500 data (Stübinger 2019).

* **Fit:** Pairs need a short leg.
* **Against:** Confounders and sampling frequency change the graph; low power.
* **Built:** Nothing.
* **Details:** [docs/algorithms/causal-discovery-directed-acyclic-graph-dag-pair-selection.md](algorithms/causal-discovery-directed-acyclic-graph-dag-pair-selection.md)

### RK200. Score-based diffusion multi-asset scenario synthesizer ⏳ (stress-test tool)

Generate joint market scenarios with diffusion models for stress testing; recent work reports reproducing stylized facts (Takahashi & Mizuno 2024). A risk tool, not a strategy.

* **Fit:** Could stress-test the grid on synthetic crash paths; a block bootstrap is the cheaper first step.
* **Against:** Inherits training regimes; hard to validate.
* **Built:** Nothing.
* **Details:** [docs/algorithms/generative-score-based-diffusion-multi-asset-scenario-synthesizer.md](algorithms/generative-score-based-diffusion-multi-asset-scenario-synthesizer.md)

### RK201. Koopman-operator MPC statistical arbitrage ⛔

Lift nonlinear multi-asset cointegration dynamics into a dictionary of observables so they evolve linearly, then run MPC to choose the mean-reversion trades. No peer-reviewed out-of-sample study found; the nearest is DMD trading with in-sample window tuning (Mann & Kutz 2016).

* **Fit:** Spread trading needs a short leg, and there is no evidence the method works out of sample.
* **Against:** Approximate linearisation; MPC on weak forecasts.
* **Built:** Nothing.
* **Details:** [docs/algorithms/koopman-operator-predictive-control-statistical-arbitrage.md](algorithms/koopman-operator-predictive-control-statistical-arbitrage.md)

### RK202. Fractional Brownian motion multi-scale trend scanning ⛔

Combine variance-ratio/Hurst tests with multi-horizon trend scanning. Little long memory in stock returns (Lo 1991); no study of the combination found.

* **Fit:** Both diagnostics exist; as a direction regime it falls under L1.
* **Against:** Multiple testing; noisy Hurst estimates.
* **Built:** Nothing combined; the diagnostics exist separately.
* **Details:** [docs/algorithms/fractional-brownian-motion-multi-scale-trend-scanning-strategy.md](algorithms/fractional-brownian-motion-multi-scale-trend-scanning-strategy.md)

### RK203. Koopman-operator MPC spread equilibrium ⛔

The same construction as RK201 applied to a single cointegrated spread: a Koopman dictionary linearises the spread's nonlinear dynamics and MPC plans the multi-period mean-reversion path. No peer-reviewed out-of-sample study found; the nearest is DMD trading with in-sample window tuning (Mann & Kutz 2016).

* **Fit:** Spread trading needs a short leg; the single-asset grid already trades mean reversion with no model.
* **Against:** Approximate linearisation; MPC on weak forecasts.
* **Built:** Nothing.
* **Details:** [docs/algorithms/koopman-operator-model-predictive-control-spread-equilibrium.md](algorithms/koopman-operator-model-predictive-control-spread-equilibrium.md)

### RK204. Lead-lag cross-asset predictive trading 🧪 (estimator) · ⏳ (entry timing) · ⛔ (latency trade)

Trade the follower on the leader's last move. At tick level liquid assets and futures lead, and the lagger's next mid-quote move is predictable about 60% of the time, but not by enough to pay the spread (Huth & Abergel).

* **Fit:** A latency trade is out; Nasdaq-100 futures leading TQQQ could time grid entries. The estimator exists.
* **Against:** Leakage, latency, stale quotes; the lead sits inside one bar at minute frequency.
* **Built:** `leads.lagged_cross_correlation`, `leads.hy_lead_lag` (gap-analysis lead).
* **Details:** [docs/algorithms/lead-lag-cross-asset-predictive-trading.md](algorithms/lead-lag-cross-asset-predictive-trading.md)

### RK205. Dynamic tensor decomposition multi-asset factor rotation ⛔

Rotate sectors by time-varying CP/Tucker tensor loadings. Tensor factor models exist (Chen, Yang & Zhang 2022); no rotation study found.

* **Fit:** No evidence it improves X3's rotation.
* **Against:** Non-unique, drifting decompositions.
* **Built:** Nothing.
* **Details:** [docs/algorithms/dynamic-tensor-decomposition-multi-asset-factor-rotation.md](algorithms/dynamic-tensor-decomposition-multi-asset-factor-rotation.md)

### RK206. Koopman-operator MPC multi-asset allocation ⛔

Lift macro and return dynamics into a linear space with a Koopman dictionary and use MPC to set tactical asset weights. No peer-reviewed out-of-sample study found; the nearest is DMD trading with in-sample window tuning (Mann & Kutz 2016).

* **Fit:** A long-only tactical allocator would pass the instrument rule, but the engine trades one symbol and the only reported result is an unreviewed poster.
* **Against:** Approximate linearisation; MPC on weak forecasts.
* **Built:** Nothing.
* **Details:** [docs/algorithms/koopman-operator-model-predictive-control-multi-asset-allocation.md](algorithms/koopman-operator-model-predictive-control-multi-asset-allocation.md)

### RK207. Standardized unexpected earnings (SUE) ⏳ (long-only basket) · ⛔ (short side)

Rank announcements by earnings surprise over the dispersion of past surprises and buy the top decile; the measurement behind PEAD (RK45), strong historically and largely gone in large stocks since 2006 (Martineau 2022).

* **Fit:** A long-only stock basket; no earnings data here, and the drift appears gone in the Nasdaq-100 names.
* **Against:** Point-in-time data; decay; survives in illiquid names only.
* **Built:** Nothing; V6 sizes on earnings-reaction volatility, not surprise.
* **Details:** [docs/algorithms/standardized-unexpected-earnings-sue.md](algorithms/standardized-unexpected-earnings-sue.md)

### RK208. Anchored VWAP reclaim / rejection 🧪 (session VWAP gate) · ⏳ (event anchors)

Trade a reclaim or rejection of VWAP anchored at an event. No academic test found; the session-anchored form is C-MS3's buy gate.

* **Fit:** As a buy gate it fits; the session form is built, an event-anchored one would extend VwapGate.
* **Against:** Hindsight anchor choice; moving-average lag.
* **Built:** `intraday_gates.session_vwap`, `VwapGate` (C-MS3).
* **Details:** [docs/algorithms/anchored-vwap-reclaim-rejection.md](algorithms/anchored-vwap-reclaim-rejection.md)

### RK209. Corporate buyback announcement drift ⏳ (long-only event basket)

Buy after open-market repurchase announcements: 12.1% four-year abnormal return in 1980–1990, 45.3% for value stocks (Ikenberry et al. 1995); much smaller after 2001 (Lee, Park & Pearson 2019), though Peyer & Vermaelen (2009) reject its disappearance.

* **Fit:** A long-only stock book with its own filing data; unrelated to the grid.
* **Against:** Authorisation is not purchase; benchmark-dependent long-run returns; decay.
* **Built:** Nothing.
* **Details:** [docs/algorithms/corporate-buyback-announcement-drift.md](algorithms/corporate-buyback-announcement-drift.md)

### RK210. Index reconstitution / rebalance event trading ⛔

Front-run forced index-fund buying. The S&P 500 inclusion effect fell from 7.4% in the 1990s to under 1% in the last decade, deletions to about 0.1% (Greenwood & Sammon 2025).

* **Fit:** Single-stock front-running; for this book index events are only flow days.
* **Against:** Crowding and anticipation; the effect has largely disappeared.
* **Built:** Nothing.
* **Details:** [docs/algorithms/index-reconstitution-rebalance-event-trading.md](algorithms/index-reconstitution-rebalance-event-trading.md)

### RK211. Macro surprise / economic release strategy ⛔ (release trade) · ✅ (event-day sizing, V6)

Trade the reaction to macro surprises. For a long-only holder the documented effect is the announcement-day premium (11.4 bp against 1.1 bp, 1958–2009; Savor & Wilson 2013) and the pre-FOMC drift (Lucca & Moench 2015).

* **Fit:** The release trade is out; FOMC-day sizing is already V6, and a pre-FOMC-session boost is a cheap variant to test.
* **Against:** Point-in-time consensus; sub-second execution for the reaction trade.
* **Built:** V6 FOMC-day lot boost on the champion; no surprise measure.
* **Details:** [docs/algorithms/macro-surprise-economic-release-strategy.md](algorithms/macro-surprise-economic-release-strategy.md)

### RK212. Market breadth thrust ⏳

Zweig's thrust (10-day EMA of advance share from below 0.40 to above 0.615 within 10 sessions): about 18 signals since 1945, every past one followed by a higher S&P 500 a year later per vendor counts; no peer-reviewed test.

* **Fit:** A calm re-entry input like the Ultimate bear filter; the breadth data is not in the warehouse.
* **Against:** About 18 events; universe- and threshold-dependent; NYSE breadth is a poor Nasdaq-100 proxy.
* **Built:** Nothing.
* **Details:** [docs/algorithms/market-breadth-thrust.md](algorithms/market-breadth-thrust.md)

### RK213. Trend-scanning label model 🧪 (labelling tool)

Label each bar with the sign of the most significant forward trend over several windows (López de Prado 2020); a training target, not a strategy.

* **Fit:** Built (C-ML1); useful for labelling regimes for V14 or validating the NATR regime.
* **Against:** Future-derived; needs purging and embargo.
* **Built:** `ml.barrier_labels.trend_scanning_labels` (C-ML1).
* **Details:** [docs/algorithms/trend-scanning-label-model.md](algorithms/trend-scanning-label-model.md)

### RK214. XGBoost cross-sectional ranking ⏳ (long-only top-k) · ⛔ (long-short)

Rank assets with boosted trees and hold the top. Trees and neural nets forecast the cross-section best (Gu, Kelly & Xiu 2020); an S&P 500 ensemble earned 0.45% a day before costs, 1992–2015, declining (Krauss, Do & Huck 2017).

* **Fit:** X3 with a learned score; X3 itself is unmeasured.
* **Against:** Long-short, pre-cost evidence; turnover; overfitting.
* **Built:** Nothing; the LightGBM models here size lots, not rank assets.
* **Details:** [docs/algorithms/xgboost-cross-sectional-ranking.md](algorithms/xgboost-cross-sectional-ranking.md)

### RK215. Cross-sectional reversal with risk neutralization 🧪 (long-only contrarian weights) · ⛔ (market-neutral)

Buy recent losers net of market, industry and news components. The residual reversal earns about four times the standard strategy's risk-adjusted return (Da, Liu & Schaumburg 2014); reversal pays for liquidity provision (Nagel 2012).

* **Fit:** Needs a stock universe; the grid is already a single-asset reversal bet. Contrarian weights exist as research code.
* **Against:** Turnover; profits concentrated in illiquid names and the short leg.
* **Built:** `mean_reversion.contrarian_weights`, `decayed_reversal_scores` (C-MR1).
* **Details:** [docs/algorithms/cross-sectional-reversal-with-risk-neutralization.md](algorithms/cross-sectional-reversal-with-risk-neutralization.md)

### RK216. Top-K with dropout portfolio rotation ⏳ (turnover rule)

Hold the top K by score but replace at most N per rebalance (Qlib's TopkDropoutStrategy); a turnover limiter, not a signal. No independent study found.

* **Fit:** A switching cap for a multi-ETF X3; not needed while X3 holds one name.
* **Against:** Value depends on the signal, K, N and costs.
* **Built:** Nothing.
* **Details:** [docs/algorithms/top-k-with-dropout-portfolio-rotation.md](algorithms/top-k-with-dropout-portfolio-rotation.md)

### RK217. BSTS causal-impact macro strategy ⏳ (event-study tool)

Measure an event's effect against a Bayesian structural time-series counterfactual (Brodersen et al. 2015) and trade it. A measurement tool; no trading study found.

* **Fit:** A research tool for event effects on TQQQ, not a trading rule.
* **Against:** Controls rarely unaffected by market shocks; ex-post measurement.
* **Built:** Nothing.
* **Details:** [docs/algorithms/bayesian-structural-time-series-bsts-causal-impact-macro-strategy.md](algorithms/bayesian-structural-time-series-bsts-causal-impact-macro-strategy.md)

### RK218. Sparse Bayesian learning dynamic factor model ⏳

Sparsity (ARD) priors select active factors in a dynamic factor model; Bayesian averaging over 2.25 quadrillion factor models beat existing models in and out of sample (Bryzgalova, Huang & Julliard 2023).

* **Fit:** A stock-book tool; no stock universe here.
* **Against:** Cross-sectional only; tuning.
* **Built:** Nothing.
* **Details:** [docs/algorithms/sparse-bayesian-learning-dynamic-factor-model.md](algorithms/sparse-bayesian-learning-dynamic-factor-model.md)

### RK219. Dynamic mode decomposition (DMD) market mode predictor ⛔

Extract and extrapolate DMD modes from a price matrix. One trading study exists, with windows tuned in sample (Mann & Kutz 2016).

* **Fit:** No out-of-sample trading evidence.
* **Against:** In-sample window tuning; unstable modes.
* **Built:** Nothing.
* **Details:** [docs/algorithms/dynamic-mode-decomposition-dmd-market-mode-predictor.md](algorithms/dynamic-mode-decomposition-dmd-market-mode-predictor.md)

### RK220. Continuous-time mean-variance RL agent ⏳

Entropy-regularised continuous-time mean-variance RL (Wang & Zhou); the authors' S&P 500 tests report over 10% a year, ahead of econometric and deep-RL baselines.

* **Fit:** A multi-asset allocator; evidence is the authors' own.
* **Against:** Author-only evidence; MV inputs.
* **Built:** Nothing.
* **Details:** [docs/algorithms/continuous-time-mean-variance-reinforcement-learning-agent.md](algorithms/continuous-time-mean-variance-reinforcement-learning-agent.md)

### RK221. Transfer-entropy lead-lag strategy ⏳ (measurement) · ⛔ (trade)

Trade nonlinear, directional lead-lag measured by transfer entropy (Schreiber 2000); used to measure market information flows (Dimpfl & Peter 2013), not tested as a trade.

* **Fit:** A measurement after RK204's linear lead-lag; no trade.
* **Against:** Sample-hungry; spread problem.
* **Built:** Nothing; linear lead-lag estimators are on RK204.
* **Details:** [docs/algorithms/information-theoretic-transfer-entropy-lead-lag-strategy.md](algorithms/information-theoretic-transfer-entropy-lead-lag-strategy.md)

### RK222. Maximum entropy production rate macro allocator ⛔

Allocate to maximise entropy production of macro asset flows. No finance study found; no link to expected returns.

* **Fit:** No evidence; not a candidate.
* **Against:** No link to returns.
* **Built:** Nothing.
* **Details:** [docs/algorithms/maximum-entropy-production-rate-macro-allocator.md](algorithms/maximum-entropy-production-rate-macro-allocator.md)

### RK223. Quantum tensor-network portfolio optimization ⛔

Solve portfolio optimisation with matrix-product-state tensor networks; tested beside annealers and VQE on 52 assets (Mugel et al. 2022), with no shown advantage over classical solvers.

* **Fit:** No combinatorial portfolio problem here.
* **Against:** No demonstrated advantage; irrelevant scale.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-tensor-network-portfolio-optimization.md](algorithms/quantum-tensor-network-portfolio-optimization.md)

### RK224. Deep latent force model interest-rate forecaster ⛔

Gaussian-process latent forces drive a term-structure model. The method exists (Álvarez et al. 2009); no rates application found.

* **Fit:** No use for this book.
* **Against:** Extra assumptions; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deep-latent-force-model-lfm-interest-rate-forecaster.md](algorithms/deep-latent-force-model-lfm-interest-rate-forecaster.md)

### RK225. Wasserstein distributionally robust mean-variance allocation ⏳

Minimise worst-case variance over a Wasserstein ball; equivalent to regularised empirical variance minimisation with a data-driven radius (Blanchet, Chen & Zhou 2022).

* **Fit:** A sound allocator for a future multi-ETF book, beside HRP.
* **Against:** Radius-dependent; close to shrinkage.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-mean-variance-allocation.md](algorithms/wasserstein-distributionally-robust-mean-variance-allocation.md)

### RK226. Functional PCA (FPCA) yield-curve forecaster ⛔

Forecast yield curves as functions via functional principal components; a functional dynamic factor model forecast yields well, especially in a trading exercise (Hays, Shen & Huang 2012).

* **Fit:** No direct use for this book.
* **Against:** Bond construction; out-of-sample decay.
* **Built:** Nothing.
* **Details:** [docs/algorithms/functional-principal-component-analysis-fpca-yield-curve-forecaster.md](algorithms/functional-principal-component-analysis-fpca-yield-curve-forecaster.md)

### RK227. Multi-agent evolutionary RL portfolio optimizer ⛔

Evolve multi-agent RL allocation policies with genetic algorithms. No out-of-sample study found.

* **Fit:** An untested multi-asset allocator.
* **Against:** Maximal data-snooping risk.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-evolutionary-reinforcement-learning-portfolio-optimizer.md](algorithms/multi-agent-evolutionary-reinforcement-learning-portfolio-optimizer.md)

### RK228. Deep generative flow-matching portfolio generator ⛔

Optimise weights over flow-matching-generated scenarios. The method (Lipman et al. 2022) is established; no portfolio study found.

* **Fit:** A multi-asset allocator with no evidence; not a candidate.
* **Against:** Inherits generator error; misses true shifts.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deep-generative-flow-matching-portfolio-generator.md](algorithms/deep-generative-flow-matching-portfolio-generator.md)

### RK229. Quantum adiabatic optimal portfolio rebalancing ⛔

Solve rebalancing with costs as a QUBO on a quantum annealer; done on real data (Mugel et al. 2022) without a claimed classical advantage.

* **Fit:** No combinatorial portfolio problem here.
* **Against:** Penalty tuning, noise; no advantage shown.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-adiabatic-optimal-portfolio-rebalancing.md](algorithms/quantum-adiabatic-optimal-portfolio-rebalancing.md)

### RK230. Riemannian SPD-manifold portfolio optimization ⛔

Optimise a portfolio by gradient descent on the manifold of symmetric positive definite (covariance) matrices, respecting its non-Euclidean geometry. No portfolio study found; shrinkage estimators are the baseline to beat.

* **Fit:** A multi-asset allocator with no evidence.
* **Against:** Must beat Ledoit-Wolf shrinkage; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/riemannian-manifold-metric-optimization-portfolio.md](algorithms/riemannian-manifold-metric-optimization-portfolio.md)

### RK231. Riemannian SPD metric-diffusion risk parity ⛔

Diffuse covariance estimates along the SPD manifold's geometry so risk-parity weights evolve smoothly through the cycle. No portfolio study found; shrinkage estimators are the baseline to beat.

* **Fit:** A multi-asset allocator with no evidence.
* **Against:** Must beat Ledoit-Wolf shrinkage; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/riemannian-manifold-metric-diffusion-portfolio-allocation.md](algorithms/riemannian-manifold-metric-diffusion-portfolio-allocation.md)

### RK232. Graph-attention covariance shrinkage estimator ⛔

Run a graph attention network over the asset correlation graph to produce a nonlinearly shrunk covariance matrix for Markowitz optimisation. Only a thesis and an arXiv comparison (not read) apply GNNs to covariance estimation; shrinkage is the baseline.

* **Fit:** A multi-asset allocation input; the engine trades one symbol.
* **Against:** Must beat shrinkage; thin evidence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/graph-attention-network-covariance-shrinkage-estimator.md](algorithms/graph-attention-network-covariance-shrinkage-estimator.md)

### RK233. Riemannian SPD Wasserstein-robust allocation ⛔

Combine a Wasserstein ambiguity set with Riemannian descent on the covariance manifold for distributionally robust allocation. No portfolio study found; shrinkage estimators are the baseline to beat.

* **Fit:** A multi-asset allocator with no evidence.
* **Against:** Must beat Ledoit-Wolf shrinkage; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/riemannian-manifold-metric-wasserstein-robust-allocation.md](algorithms/riemannian-manifold-metric-wasserstein-robust-allocation.md)

### RK234. Wasserstein distributionally robust RL portfolio agent ⛔

Deep RL portfolio agent trained against a Wasserstein ball of transition models. No portfolio study found.

* **Fit:** A multi-asset allocator with no evidence.
* **Against:** Unstable training; arbitrary radius.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-reinforcement-learning-portfolio-agent.md](algorithms/wasserstein-distributionally-robust-reinforcement-learning-portfolio-agent.md)

### RK235. Graph-attention covariance shrinkage dynamic allocation ⛔

The RK232 estimator re-estimated on a rolling window and fed into dynamic mean-variance allocation. Only a thesis and an arXiv comparison (not read) apply GNNs to covariance estimation; shrinkage is the baseline.

* **Fit:** A multi-asset allocation input; the engine trades one symbol.
* **Against:** Must beat shrinkage; thin evidence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/graph-attention-network-covariance-matrix-shrinkage-dynamic-allocation.md](algorithms/graph-attention-network-covariance-matrix-shrinkage-dynamic-allocation.md)

### RK236. Quantum adiabatic GNN portfolio optimization ⛔

GNN asset embeddings fed into quantum-annealing portfolio Hamiltonians. Each part exists; no study of the combination found.

* **Fit:** No evidence; no portfolio problem here.
* **Against:** Untested combination.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-adiabatic-graph-neural-network-portfolio-optimization.md](algorithms/quantum-adiabatic-graph-neural-network-portfolio-optimization.md)

### RK237. Riemannian SPD graph-attention allocation ⛔

Use graph attention over asset relations to produce weights on the SPD manifold of covariance matrices. No portfolio study found; shrinkage estimators are the baseline to beat.

* **Fit:** A multi-asset allocator with no evidence.
* **Against:** Must beat Ledoit-Wolf shrinkage; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/riemannian-manifold-metric-graph-attention-portfolio-allocation.md](algorithms/riemannian-manifold-metric-graph-attention-portfolio-allocation.md)

### RK238. Quantum adiabatic tensor-network portfolio optimization ⛔

Tensor networks combined with adiabatic evolution for allocation; tested only separately (Mugel et al. 2022).

* **Fit:** No evidence; no portfolio problem here.
* **Against:** Untested combination.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-adiabatic-tensor-network-portfolio-optimization.md](algorithms/quantum-adiabatic-tensor-network-portfolio-optimization.md)

### RK239. Fractional-order VECM neural network allocator ⛔

FCVAR with a neural error-correction term for basket allocation. FCVAR is established (Johansen & Nielsen 2012); no study of the neural variant.

* **Fit:** Basket trading with short weights; out of scope.
* **Against:** Overfitting; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/fractional-order-vector-error-correction-neural-network-portfolio-allocator.md](algorithms/fractional-order-vector-error-correction-neural-network-portfolio-allocator.md)

### RK240. Neural-operator delay-differential stochastic volatility calibrator ⛔

Calibrate stochastic volatility models with delay-aware neural operators. Deep calibration of (rough) volatility exists (Horvath et al. 2021); the delay variant was not found, and the CSV's arXiv 2106.09876 is a general graph anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance one.

* **Fit:** Options pricing; out of scope and not a trading rule.
* **Against:** GPU-heavy; a pricing tool.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-operator-delay-differential-stochastic-volatility-calibrator.md](algorithms/neural-operator-delay-differential-stochastic-volatility-calibrator.md)

### RK241. Koopman-operator factor risk tracking ⛔

Model the drift of a portfolio's factor exposures with a Koopman linearisation to track style rotation and factor risk over time. No peer-reviewed out-of-sample study found; the nearest is DMD trading with in-sample window tuning (Mann & Kutz 2016).

* **Fit:** A risk-monitoring tool for a multi-factor stock book, which this project does not run.
* **Against:** Approximate linearisation; MPC on weak forecasts.
* **Built:** Nothing.
* **Details:** [docs/algorithms/koopman-operator-multi-factor-equity-risk-factor-tracking.md](algorithms/koopman-operator-multi-factor-equity-risk-factor-tracking.md)

### RK242. Long-volatility breakout (options) ⛔

Buy straddles before catalysts. Zero-beta ATM straddles lose about 3% a week on average (Coval & Shumway 2001): buyers pay the volatility risk premium.

* **Fit:** Options are out; the grid is on the other, paid side of the volatility premium.
* **Against:** Theta; IV crush; negative average returns.
* **Built:** `options.straddle_entry`, `straddle_pnl_at_expiry` (Q12).
* **Details:** [docs/algorithms/long-volatility-breakout-options.md](algorithms/long-volatility-breakout-options.md)

### RK243. Price/volume anomaly detection 🧪 (data-quality flag) · ❌ (alpha)

Flag unusual price, volume or spread observations and filter trades. No study found that this improves returns; most flags are bad ticks or scheduled events.

* **Fit:** A data-quality check fits; as a trade filter it removes the volatile sessions the grid harvests.
* **Against:** Anomalies are not predictions; filters cut volatile sessions.
* **Built:** `forecasting.ewm_anomalies` (A8).
* **Details:** [docs/algorithms/price-volume-anomaly-detection.md](algorithms/price-volume-anomaly-detection.md)

### RK244. Liquidity-aware adaptive execution 🧪 (spread gate) · ⛔ (slicing not needed)

Adapt aggressiveness and child-order timing to spreads, depth and urgency (Almgren & Chriss 2001); execution algorithms help market functioning but shift execution risk to users (BIS 2020).

* **Fit:** Orders here are small; the live loop already skips grid buys when the spread is too wide.
* **Against:** Objective trade-offs; vendor-specific methods.
* **Built:** Spread gate and premium cap in `engine/execution/limit_pricing.py`.
* **Details:** [docs/algorithms/liquidity-aware-adaptive-execution.md](algorithms/liquidity-aware-adaptive-execution.md)

### RK245. Pure passive market making ⛔ (two-sided) · grid is the buy-side relative

Rest symmetric quotes around mid and refresh. Spread profits are given back on positions without inventory and toxicity control (Menkveld 2013: €1.55 earned on the spread, €0.68 lost on positions per trade).

* **Fit:** Two-sided quoting is out; the grid is its long-only buy side.
* **Against:** Adverse selection; queue priority; needs quote data.
* **Built:** `inventory_control.as_quotes`, `glft_quotes` (C-MM1, C-MM2).
* **Details:** [docs/algorithms/pure-passive-market-making.md](algorithms/pure-passive-market-making.md)

### RK246. Inventory-skewed market making ✅ (buy-side skew, C-G2) · ⛔ (sell side below cost)

Skew quotes against inventory via a reservation price (Avellaneda & Stoikov 2008; GLFT 2013). The buy-side half (lower the next buy as lots accumulate) is the grid's own inventory question.

* **Fit:** The buy-side skew is built (C-G2); the sell side cannot go below cost.
* **Against:** Model-dependent; adverse selection; queue position.
* **Built:** `inventory_control.inventory_skewed_level`, `as_reservation_price` (C-G2, C-MM1).
* **Details:** [docs/algorithms/inventory-skewed-market-making.md](algorithms/inventory-skewed-market-making.md)

### RK247. VPIN flow-toxicity filter 🧪 (buy gate) · disputed evidence

Volume-synchronised order imbalance as a toxicity warning (Easley et al. 2012); critics find no predictive power beyond volume and volatility and a peak after the flash crash (Andersen & Bondarenko 2014).

* **Fit:** Built as a possible buy gate; its content duplicates the volume and volatility levers already in the champion.
* **Against:** Disputed; trade-classification dependent.
* **Built:** `microstructure.vpin` (C-MM4).
* **Details:** [docs/algorithms/vpin-flow-toxicity-filter.md](algorithms/vpin-flow-toxicity-filter.md)

### RK248. Hawkes-process order-flow forecast ⛔

Forecast order-flow intensity with self- and cross-exciting Hawkes processes (review: Bacry, Mastromatteo & Muzy 2015); established as a model, no evidence of trading value at retail latency.

* **Fit:** Needs event-level order data the warehouse does not have.
* **Against:** Parameter instability; event data; latency.
* **Built:** Nothing.
* **Details:** [docs/algorithms/hawkes-process-order-flow-forecast.md](algorithms/hawkes-process-order-flow-forecast.md)

### RK249. Iceberg / reserve-order execution ⛔ (not needed)

Hide most of a large order and refill the displayed part. Hidden orders fill less and slower but lower execution costs on Euronext Paris (Bessembinder et al. 2009).

* **Fit:** Orders here are too small to need hiding.
* **Against:** Venue rules; queue priority; impact remains.
* **Built:** Nothing.
* **Details:** [docs/algorithms/iceberg-reserve-order-execution.md](algorithms/iceberg-reserve-order-execution.md)

### RK250. Arrival-price adaptive limit-vs-market execution 🧪 (purpose-based pricing) · ⏳ (shortfall check)

Choose limit or marketable orders by drift from arrival and urgency; judge by implementation shortfall (Perold 1988). The engine already prices orders by purpose; the CSV's reference could not be identified.

* **Fit:** Built in a purpose-based form; measuring live shortfall against trigger prices is the useful addition.
* **Against:** Non-fill versus impact; must be benchmarked on real fills.
* **Built:** `engine/execution/limit_pricing.py` (grid_buy, marketable_buy, marketable_sell).
* **Details:** [docs/algorithms/arrival-price-adaptive-limit-vs-market-execution.md](algorithms/arrival-price-adaptive-limit-vs-market-execution.md)

### RK251. Intraday volume-profile execution ⛔ (not applicable)

Schedule child orders along a forecast volume curve to track VWAP; dynamic market-plus-stock volume models improve tracking (Białkowski et al. 2008).

* **Fit:** The grid's orders are price-triggered and small; nothing to schedule.
* **Against:** Curves shift on news, auctions, half-days.
* **Built:** Nothing; the intraday volatility profile (V9) is the nearest.
* **Details:** [docs/algorithms/intraday-volume-profile-execution.md](algorithms/intraday-volume-profile-execution.md)

### RK252. Order-flow imbalance (OFI) cross-sectional alpha predictor 🧪 (single-instrument OFI) · ⛔ (cross-sectional)

Net changes in best-quote queue sizes explain short-interval price changes linearly, scaled by depth (Cont, Kukanov & Stoikov 2014); seconds-horizon alpha needing L1/L2.

* **Fit:** A possible buy gate on live quotes, but no historical quotes to test it.
* **Against:** Data and compute heavy; seconds horizon.
* **Built:** `microstructure.ofi`, `ofi_events` (C-MS1).
* **Details:** [docs/algorithms/order-flow-imbalance-ofi-cross-sectional-alpha-predictor.md](algorithms/order-flow-imbalance-ofi-cross-sectional-alpha-predictor.md)

### RK253. Information-driven volume-clock imbalance momentum 🧪 (bars) · ⏳ (rule)

Sample by volume or order imbalance rather than time and trade the imbalance (Easley, López de Prado & O'Hara 2012); the bars are better behaved statistically, a momentum rule on them is untested.

* **Fit:** Bars built (C-ML5); the engine runs on minute bars.
* **Against:** Event-indexed backtests required.
* **Built:** `ml.info_bars.volume_bars`, `tick_imbalance_bars` (C-ML5).
* **Details:** [docs/algorithms/information-driven-volume-clock-imbalance-momentum.md](algorithms/information-driven-volume-clock-imbalance-momentum.md)

### RK254. Persistent-homology (TDA) crash predictor ⏳ as a regime input

Build Vietoris–Rips complexes from rolling multi-asset point clouds and track persistence diagrams (Betti numbers) as a crash warning. Evidence: persistence-landscape norms rose before the 2000 and 2008 crashes, in sample (Gidea & Katz 2018).

* **Fit:** As a crash early-warning input to the regime it would fit (it never trades by
    itself).
* **Against:** Two events; free parameters; overlaps with volatility measures.
* **Built:** Nothing.
* **Details:** [docs/algorithms/persistent-homology-topological-data-analysis-tda-crash-predictor.md](algorithms/persistent-homology-topological-data-analysis-tda-crash-predictor.md)

### RK255. Persistent-homology landscape crisis predictor ⏳ as a regime input

Track persistence landscapes and Betti curves of sliding multi-asset point clouds; growing landscape norms signal fragility before a crash. Evidence: persistence-landscape norms rose before the 2000 and 2008 crashes, in sample (Gidea & Katz 2018).

* **Fit:** As a crash early-warning input to the regime it would fit (it never trades by
    itself).
* **Against:** Two events; free parameters; overlaps with volatility measures.
* **Built:** Nothing.
* **Details:** [docs/algorithms/persistent-homology-topological-landscape-crisis-predictor.md](algorithms/persistent-homology-topological-landscape-crisis-predictor.md)

### RK256. Deep Markov state-space intraday volume predictor ⛔

Forecast intraday volume curves with a deep Markov model. No finance study found; the CSV's arXiv 2006.12345 could not be identified.

* **Fit:** Not applicable: orders here are not volume-scheduled.
* **Against:** Unstable variational training; no evidence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deep-markov-state-space-intraday-volume-profile-predictor.md](algorithms/deep-markov-state-space-intraday-volume-profile-predictor.md)

### RK257. Transfer-entropy causality-flow macro allocator ⛔

Weight asset classes by the transfer entropy and directed information flowing to them from macro indicators. No study found.

* **Fit:** No evidence; not a candidate.
* **Against:** Noisy estimates; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/information-theoretic-causality-flow-macro-asset-allocator.md](algorithms/information-theoretic-causality-flow-macro-asset-allocator.md)

### RK258. Spiking graph convolutional network contagion predictor ⛔

Spiking neural networks fused with graph convolutions to model shock contagion. No finance study found.

* **Fit:** No evidence; no use here.
* **Against:** Hard to train; no benchmarks.
* **Built:** Nothing.
* **Details:** [docs/algorithms/spiking-graph-convolutional-network-sgcn-contagion-predictor.md](algorithms/spiking-graph-convolutional-network-sgcn-contagion-predictor.md)

### RK259. Hawkes-driven non-parametric order-flow toxicity filter ⛔

Halt market making when a non-parametric Hawkes toxicity score is high. No study of the combination found; the CSV's arXiv 2002.09876 could not be identified.

* **Fit:** Market making on event data; out of scope.
* **Against:** Stale kernels; toxicity scores may duplicate volume and volatility.
* **Built:** Nothing.
* **Details:** [docs/algorithms/hawkes-driven-non-parametric-order-flow-toxicity-filter.md](algorithms/hawkes-driven-non-parametric-order-flow-toxicity-filter.md)

### RK260. Quantum approximate state-preparation risk mapping ⛔

Quantum amplitude estimation for VaR/CVaR, near-quadratically faster than Monte Carlo in principle; toy demonstrations only (Woerner & Egger 2019).

* **Fit:** Risk numbers here are cheap and exact classically.
* **Against:** State preparation and noise erase the speed-up.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-approximate-state-preparation-risk-mapping.md](algorithms/quantum-approximate-state-preparation-risk-mapping.md)

### RK261. Koopman-operator MPC risk mitigation ⛔

Linearise macro state dynamics with a Koopman dictionary and use MPC to raise or cut portfolio risk exposure ahead of predicted stress. No peer-reviewed out-of-sample study found; the nearest is DMD trading with in-sample window tuning (Mann & Kutz 2016).

* **Fit:** It would play the role the NATR regime and drawdown throttle already play, with a model in place of a measured rule; no evidence it does better.
* **Against:** Approximate linearisation; MPC on weak forecasts.
* **Built:** Nothing.
* **Details:** [docs/algorithms/koopman-operator-model-predictive-control-risk-mitigation.md](algorithms/koopman-operator-model-predictive-control-risk-mitigation.md)

### RK262. Persistent-homology Betti-0 contagion detector ⛔

Track the number of connected components (Betti-0) of a rolling correlation-threshold graph; a sudden merging of clusters signals contagion. Evidence: persistence-landscape norms rose before the 2000 and 2008 crashes, in sample (Gidea & Katz 2018).

* **Fit:** No evidence beyond two in-sample crashes.
* **Against:** Two events; free parameters; overlaps with volatility measures.
* **Built:** Nothing.
* **Details:** [docs/algorithms/persistent-homology-betti-0-connected-component-contagion-detector.md](algorithms/persistent-homology-betti-0-connected-component-contagion-detector.md)

### RK263. Persistence-diagram clustering crisis detector ⛔

Cluster rolling persistence diagrams by Wasserstein distance and alert when the cluster structure changes abruptly. Evidence: persistence-landscape norms rose before the 2000 and 2008 crashes, in sample (Gidea & Katz 2018).

* **Fit:** No evidence beyond two in-sample crashes.
* **Against:** Two events; free parameters; overlaps with volatility measures.
* **Built:** Nothing.
* **Details:** [docs/algorithms/topological-persistence-diagram-clustering-crisis-detector.md](algorithms/topological-persistence-diagram-clustering-crisis-detector.md)

### RK264. Transfer-entropy directed GNN contagion model ⛔

Build a directed graph of transfer-entropy flows between assets and feed it to a graph neural network that forecasts shock contagion. No study found.

* **Fit:** No evidence; not a candidate.
* **Against:** Noisy estimates; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/information-theoretic-directed-gnn-contagion-model.md](algorithms/information-theoretic-directed-gnn-contagion-model.md)

### RK265. Persistent-homology Betti-2 macro stress predictor ⛔

Track two-dimensional voids (Betti-2) in multi-asset correlation point clouds as a sign of higher-order dependence collapse before crises. Evidence: persistence-landscape norms rose before the 2000 and 2008 crashes, in sample (Gidea & Katz 2018).

* **Fit:** No evidence beyond two in-sample crashes.
* **Against:** Two events; free parameters; overlaps with volatility measures.
* **Built:** Nothing.
* **Details:** [docs/algorithms/persistent-homology-betti-2-3d-void-macro-stress-predictor.md](algorithms/persistent-homology-betti-2-3d-void-macro-stress-predictor.md)

### RK266. Riemannian SPD entropic-risk portfolio ⛔

Minimise an entropic risk measure while optimising over the SPD manifold of covariance matrices. No portfolio study found; shrinkage estimators are the baseline to beat.

* **Fit:** A multi-asset allocator with no evidence.
* **Against:** Must beat Ledoit-Wolf shrinkage; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/riemannian-manifold-metric-entropic-risk-portfolio.md](algorithms/riemannian-manifold-metric-entropic-risk-portfolio.md)

### RK267. Graph-attention covariance spectral regularization ⛔

Use a graph attention network to clip and condition the eigenvalues of rolling covariance matrices (the job random-matrix-theory cleaning does). Only a thesis and an arXiv comparison (not read) apply GNNs to covariance estimation; shrinkage is the baseline.

* **Fit:** A multi-asset allocation input; the engine trades one symbol.
* **Against:** Must beat shrinkage; thin evidence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/graph-attention-network-covariance-matrix-spectral-regularization.md](algorithms/graph-attention-network-covariance-matrix-spectral-regularization.md)

### RK268. Persistent-homology multi-scale Vietoris–Rips risk score ⏳ as a regime input

Turn multi-scale Vietoris–Rips filtrations of rolling correlation matrices into a single fragility score. Evidence: persistence-landscape norms rose before the 2000 and 2008 crashes, in sample (Gidea & Katz 2018).

* **Fit:** As a crash early-warning input to the regime it would fit (it never trades by
    itself).
* **Against:** Two events; free parameters; overlaps with volatility measures.
* **Built:** Nothing.
* **Details:** [docs/algorithms/persistent-homology-multi-scale-vietoris-rips-filtration-risk-scoring.md](algorithms/persistent-homology-multi-scale-vietoris-rips-filtration-risk-scoring.md)

### RK269. Persistent-homology Betti-0 multiscale contagion clustering 🧪 (dendrogram in HRP) · ⏳ (contagion signal)

Watch Betti-0 persistence (single-linkage merge heights) for sudden cluster fusion as a contagion signal; the dendrogram is already built inside HRP.

* **Fit:** The dendrogram exists (A5); as a signal it mostly restates rising correlation.
* **Against:** Restates rising correlation.
* **Built:** Single-linkage clustering inside `hrp.hrp_weights` (A5).
* **Details:** [docs/algorithms/persistent-homology-betti-0-multiscale-filtration-contagion-clustering.md](algorithms/persistent-homology-betti-0-multiscale-filtration-contagion-clustering.md)

### RK270. Quantum annealing binary matrix factorization risk model ⛔

Factorise risk covariances into binary matrices on a quantum annealer. No finance study found.

* **Fit:** No evidence; no use here.
* **Against:** Binary restriction; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-annealing-binary-matrix-factorization-portfolio-risk-model.md](algorithms/quantum-annealing-binary-matrix-factorization-portfolio-risk-model.md)

### RK271. Sequential bootstrapping sample weights ⏳ (training hygiene)

Bootstrap overlapping financial labels in proportion to their average uniqueness (López de Prado 2018, ch. 4); a training step, not a strategy.

* **Fit:** A cheap addition to the V13/V14 training; purged CV (C-ML3) already exists.
* **Against:** Does not fix leakage or overfitting.
* **Built:** Nothing; purged CV is C-ML3.
* **Details:** [docs/algorithms/sequential-bootstrapping-sample-weights.md](algorithms/sequential-bootstrapping-sample-weights.md)

### RK272. Wavelet-neural network intraday trend scalper ⛔ (scalper)

Denoise intraday prices with wavelets and trade a neural net's trend call. Full-sample transforms leak the future; denoising generally does not improve forecasts (Bašta 2018); no causal, cost-inclusive test found.

* **Fit:** An intraday scalper is out; the NATR regime already measures volatility causally.
* **Against:** Look-ahead from non-causal transforms; boundary effects; costs.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wavelet-neural-network-hybrid-intraday-trend-scalper.md](algorithms/wavelet-neural-network-hybrid-intraday-trend-scalper.md)

### RK273. Deep Koopman spectral asset allocation ⛔

Learn the Koopman observables with a neural network (a deep Koopman autoencoder) so that macro and return dynamics become linear, then allocate by linear optimal control. No peer-reviewed out-of-sample study found; the nearest is DMD trading with in-sample window tuning (Mann & Kutz 2016).

* **Fit:** As RK206: an allocator for a multi-asset book, with only an unreviewed poster as evidence.
* **Against:** Approximate linearisation; MPC on weak forecasts.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deep-koopman-inspired-spectral-asset-allocation.md](algorithms/deep-koopman-inspired-spectral-asset-allocation.md)

### RK274. Avellaneda–Stoikov market making ✅ (bid-side reservation price) · ⛔ (two-sided)

Quote around an inventory-adjusted reservation price with a risk- and intensity-based spread (Avellaneda & Stoikov 2008); a model reference, not a production strategy.

* **Fit:** The bid-side reservation price is the grid's inventory skew (C-G2); the ask side is out.
* **Against:** Latency, adverse selection, fees decide results.
* **Built:** `inventory_control.as_reservation_price`, `as_optimal_spread`, `as_quotes` (C-MM1).
* **Details:** [docs/algorithms/avellaneda-stoikov-market-making.md](algorithms/avellaneda-stoikov-market-making.md)

### RK275. DeepLOB-style order-book forecasting ⛔

CNN+LSTM on order-book snapshots predicts short-horizon mid-price moves, with stable out-of-sample accuracy on LSE data (Zhang, Zohren & Roberts 2019); accuracy is not net edge.

* **Fit:** Needs depth history; seconds horizon.
* **Against:** Licensed data; latency and fees.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deeplob-style-order-book-forecasting.md](algorithms/deeplob-style-order-book-forecasting.md)

### RK276. Queue-reactive market making 🧪 (fill model) · ⛔ (quoting)

Quote according to queue state, modelling the book as a Markov queuing system (Huang, Lehalle & Rosenbaum 2015); here its value is fill realism for resting grid buys.

* **Fit:** The queue estimator would make level fills more realistic; needs L2 to calibrate.
* **Against:** Bars cannot simulate queue priority.
* **Built:** `microstructure.QueuePositionEstimator` (C-MM5).
* **Details:** [docs/algorithms/queue-reactive-market-making.md](algorithms/queue-reactive-market-making.md)

### RK277. Hawkes multi-dimensional order-flow intensity model ⛔

Multivariate mutually exciting Hawkes model of order-book events for seconds-ahead forecasts (Bacry & Muzy 2014; review: Bacry, Mastromatteo & Muzy 2015).

* **Fit:** Needs event-level data the warehouse does not have.
* **Against:** Low latency; heavy estimation.
* **Built:** Nothing.
* **Details:** [docs/algorithms/hawkes-process-multi-dimensional-order-flow-intensity-model.md](algorithms/hawkes-process-multi-dimensional-order-flow-intensity-model.md)

### RK278. Cross-venue crypto triangular arbitrage ❌

Trade three-pair cycles across or within crypto venues. Cross-exchange bitcoin gaps were large and persistent, mostly across countries with capital controls (Makarov & Schoar 2020).

* **Fit:** Crypto; rejected.
* **Against:** Fees, withdrawals, latency.
* **Built:** `crypto.find_arbitrage_cycle` (A7).
* **Details:** [docs/algorithms/cross-venue-crypto-triangular-arbitrage.md](algorithms/cross-venue-crypto-triangular-arbitrage.md)

### RK279. Asynchronous multi-exchange spatial arbitrage graph ❌

Route multi-hop cross-venue arbitrage by minimum-cost flow. The gaps it targets are real in crypto, mostly across countries with capital controls (Makarov & Schoar 2020).

* **Fit:** Crypto; rejected.
* **Against:** Withdrawal freezes, latency, rate limits.
* **Built:** `crypto.depth_arbitrage`, `find_arbitrage_cycle` (A7).
* **Details:** [docs/algorithms/asynchronous-multi-exchange-spatial-arbitrage-graph.md](algorithms/asynchronous-multi-exchange-spatial-arbitrage-graph.md)

### RK280. Recurrent neural Hawkes toxic-flow hedging trigger ⛔

A neural Hawkes model forecasting toxic-flow surges to trigger option-hedge rebalances. No finance study found; the CSV's arXiv 2104.09876 is a heat-pump health-monitoring paper, unrelated to trading.

* **Fit:** Options and event data; out of scope.
* **Against:** Latency; no evidence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/recurrent-neural-hawkes-point-process-toxic-flow-hedging-trigger.md](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-hedging-trigger.md)

### RK281. Covered call / buy-write ⛔

Hold the stock and sell calls. BXM matched the index with less volatility (Whaley 2002); a covered call is equity plus well-paid short volatility plus a poorly paid reversal bet (Israelov & Nielsen 2015).

* **Fit:** Options are out; the decomposition describes the grid's own risk (per-lot target caps upside, no premium).
* **Against:** Capped upside in rallies; the reversal exposure.
* **Built:** `options.wheel_calls_to_write` (S1).
* **Details:** [docs/algorithms/covered-call-buy-write.md](algorithms/covered-call-buy-write.md)

### RK282. Put-write / cash-secured put ⛔

Sell cash-secured puts for the volatility risk premium. The Cboe PUT index returned 10.32% against 8.77% for the S&P 500 with 9.91% against 15.39% volatility, 1986–2008 (gross, partly back-filled).

* **Fit:** Options are out; the grid's resting buys are a premium-free relative.
* **Against:** Crash losses; back-filled index history; gross returns.
* **Built:** `options.wheel_should_write`, `wheel_select_contract` (S1).
* **Details:** [docs/algorithms/put-write-cash-secured-put.md](algorithms/put-write-cash-secured-put.md)

### RK283. Wasserstein distributionally robust neural stochastic-control hedging ⛔

Learn option hedges robust to a Wasserstein ball of volatility paths. Deep hedging is established (Buehler et al. 2019); the robust variant was not found, and the CSV's arXiv 2009.08295 is Morrill et al.'s neural rough differential equations paper, a general time-series method.

* **Fit:** Derivatives hedging; out of scope.
* **Against:** Heavy training; no evidence for the variant.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-neural-stochastic-control-hedging.md](algorithms/wasserstein-distributionally-robust-neural-stochastic-control-hedging.md)

### RK284. Options wheel ⛔

Alternate cash-secured puts and covered calls. The legs are documented (PUT, BXM); no study of the combined rule found. It keeps owning a falling stock.

* **Fit:** Options are out; the grid is the premium-free, many-lot analogue with a regime exit.
* **Against:** Concentration in falling assets; rolling extends losses.
* **Built:** `options.wheel_select_contract`, `wheel_should_roll` (S1).
* **Details:** [docs/algorithms/options-wheel.md](algorithms/options-wheel.md)

### RK285. Iron condor / short premium range strategy ⛔

Sell OTM put and call spreads for a credit. Cboe's CNDR index matched the S&P 500's return with lower volatility and drawdowns, 1986–2015, in a sponsor-commissioned study.

* **Fit:** Options; out of scope.
* **Against:** Gap losses; four-leg slippage; sponsor study.
* **Built:** Nothing.
* **Details:** [docs/algorithms/iron-condor-short-premium-range-strategy.md](algorithms/iron-condor-short-premium-range-strategy.md)

### RK286. Iron butterfly credit strategy ⛔

Sell an ATM straddle with OTM wings. Cboe's BFLY index exists; its performance figures were not found.

* **Fit:** Options; out of scope.
* **Against:** Short gamma around jumps; large defined loss.
* **Built:** Nothing.
* **Details:** [docs/algorithms/iron-butterfly-credit-strategy.md](algorithms/iron-butterfly-credit-strategy.md)

### RK287. Neural-operator delay-ODE term-structure predictor ⛔

Neural delay-differential operators for term-structure dynamics. No study found.

* **Fit:** No use for this book.
* **Against:** Over-parameterised; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-operator-delay-differential-equation-delay-ode-term-structure-predictor.md](algorithms/neural-operator-delay-differential-equation-delay-ode-term-structure-predictor.md)

### RK288. Neural CDE point-process execution ⛔

Neural CDEs (Kidger et al. 2020) with point processes to time execution on irregular tick data. The model class is established; no execution study found.

* **Fit:** Execution timing on event data; not applicable here.
* **Against:** GPU, solvers; no finance evidence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-controlled-differential-equation-neural-cde-point-process-execution.md](algorithms/neural-controlled-differential-equation-neural-cde-point-process-execution.md)

### RK289. Neural-operator delay-differential Hawkes microstructure predictor ⛔

Fourier neural operators with delay-differential Hawkes intensities for order arrivals. Each part exists; no study combines them.

* **Fit:** Event data, no evidence; out of scope.
* **Against:** Heavy compute; no evidence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-operator-delay-differential-hawkes-microstructure-predictor.md](algorithms/neural-operator-delay-differential-hawkes-microstructure-predictor.md)

### RK290. Random forest return classification ⏳ (as a learner) · ⛔ (long-short)

Classify next-period returns with a random forest. On S&P 500 constituents RF was the strongest single model (about 0.43% a day before costs, 1992–2015), fading after the early 2000s (Krauss, Do & Huck 2017).

* **Fit:** Interchangeable with the LightGBM learners here, whose measured AUCs are weak.
* **Against:** Leakage, nonstationarity, turnover; pre-cost evidence.
* **Built:** Nothing; LightGBM is used instead.
* **Details:** [docs/algorithms/random-forest-return-classification.md](algorithms/random-forest-return-classification.md)

### RK291. Gradient-boosted trees return prediction ✅ (lot sizing, V13/V14) · ⛔ (direction trade)

Boosted trees predict returns or probabilities; among the best cross-sectional forecasters (Gu, Kelly & Xiu 2020). Here LightGBM sizes grid lots (V13, V14); measured AUCs are 0.52–0.63, with one macro lift in six comparisons.

* **Fit:** Built as sizing levers; next is the pre-registered held-out test in ml_plan.md.
* **Against:** Accuracy is not P&L; weak AUCs; selection bias.
* **Built:** `ml.reachability_sizing.MLReachabilitySizing` (V13), `ml.regime_scaled_sizing.MLRegimeScaledSizing` (V14).
* **Details:** [docs/algorithms/gradient-boosted-trees-return-prediction.md](algorithms/gradient-boosted-trees-return-prediction.md)

### RK292. LSTM sequence forecasting ❌

An LSTM on S&P 500 stocks earned 0.46% a day before costs (1992–2015), but its picks were short-term reversal names and a rules-based reversal explained part of it (Fischer & Krauss 2018). Rejected in the catalog (C-RJ4).

* **Fit:** Rejected; what the network learned is the reversal the grid already harvests.
* **Against:** Fragile; pre-cost; a known anomaly in costlier form.
* **Built:** `forecasting.LSTMForecaster` (C-RJ4).
* **Details:** [docs/algorithms/lstm-sequence-forecasting.md](algorithms/lstm-sequence-forecasting.md)

### RK293. News / financial sentiment NLP ⏳ (market-level input) · ⛔ (stock-level news trade)

Trade on sentiment extracted from text. Market-level media pessimism predicts price pressure followed by reversal (Tetlock 2007), i.e. noise rather than news.

* **Fit:** Market-level pessimism-then-reversal matches the grid's premise; needs a licensed, timestamped archive.
* **Against:** Timestamp and duplication look-ahead; licensed data; fast decay.
* **Built:** Nothing; only the Michigan consumer-sentiment survey is a registered input.
* **Details:** [docs/algorithms/news-financial-sentiment-nlp.md](algorithms/news-financial-sentiment-nlp.md)

### RK294. Triple-barrier labeled ML strategy 🧪 (labels)

Label trades by the first of profit target, stop and time limit, then train a (meta-)classifier (López de Prado 2018, ch. 3). The barriers map onto a grid lot; V13's reachability label is a two-barrier form.

* **Fit:** Labels built (C-ML1); the meta-model on top is the missing step.
* **Against:** A labelling method; overlapping labels need purged validation.
* **Built:** `ml.barrier_labels.triple_barrier_labels` (C-ML1).
* **Details:** [docs/algorithms/triple-barrier-labeled-ml-strategy.md](algorithms/triple-barrier-labeled-ml-strategy.md)

### RK295. Conformal prediction uncertainty wrapper (CP-MAPIE) 🧪 (conformal sizing)

Turn model predictions into intervals with finite-sample coverage under exchangeability (Vovk et al. 2005) and trade only when the interval clears costs. Split-conformal sizing exists as research code.

* **Fit:** Pairs naturally with the V13 reachability model; inherits its weakness.
* **Against:** Exchangeability fails in markets; only as good as the inner model.
* **Built:** `position_sizing.split_conformal_interval`, `conformal_long_size` (S5).
* **Details:** [docs/algorithms/conformal-prediction-uncertainty-wrapper-cp-mapie.md](algorithms/conformal-prediction-uncertainty-wrapper-cp-mapie.md)

### RK296. Dynamic copula-vine regularized factor allocation ⏳

Allocate on regularised vine-copula dependence models; a Clayton canonical vine was best for min-CVaR portfolios of 3–12 assets (Low et al. 2013).

* **Fit:** Published support for a future multi-ETF CVaR allocator.
* **Against:** Estimation grows with dimension; tuning.
* **Built:** Nothing.
* **Details:** [docs/algorithms/dynamic-copula-vine-regularized-factor-allocation.md](algorithms/dynamic-copula-vine-regularized-factor-allocation.md)

### RK297. Fractional Hurst-driven adaptive-bandwidth mean reversion 🧪 (Hurst diagnostic) · ⏳ (adaptive bands)

Widen or narrow mean-reversion bands by a rolling Hurst exponent. Intuitive for a grid, but Hurst estimates are noisy and long memory is weak (Lo 1991); no study of the rule.

* **Fit:** Maps onto an adaptive grid step; check rolling H on TQQQ first.
* **Against:** Noisy rolling estimates; weak long memory.
* **Built:** `mean_reversion.hurst_exponent` (C-MR4).
* **Details:** [docs/algorithms/fractional-hurst-driven-adaptive-bandwidth-mean-reversion.md](algorithms/fractional-hurst-driven-adaptive-bandwidth-mean-reversion.md)

### RK298. AMM / CLOB cross-venue arbitrage ❌

Arbitrage AMM pool prices against order books. Arbitrageurs profit from stale pool prices at LPs' expense (loss-versus-rebalancing; Milionis et al. 2022); the edge goes to the fastest and to MEV.

* **Fit:** Crypto; rejected.
* **Against:** Gas, MEV, failed transactions, custody.
* **Built:** Nothing.
* **Details:** [docs/algorithms/amm-clob-cross-venue-arbitrage.md](algorithms/amm-clob-cross-venue-arbitrage.md)

### RK299. Dynamic AMM liquidity provision / liquidity mining ❌

Provide concentrated AMM liquidity for fees. Across 17 Uniswap v3 pools impermanent loss ($260.1m) exceeded fees ($199.3m) (Loesch et al. 2021).

* **Fit:** Crypto; rejected.
* **Against:** Impermanent loss exceeds fees; contract and MEV risk.
* **Built:** Nothing.
* **Details:** [docs/algorithms/dynamic-amm-liquidity-provision-liquidity-mining.md](algorithms/dynamic-amm-liquidity-provision-liquidity-mining.md)

### RK300. Fractional differentiation feature pipeline 🧪 (feature transform)

Fractionally difference prices to the smallest order that is stationary, keeping memory (López de Prado 2018, ch. 5; Hosking 1981). Preprocessing, not alpha; built as C-ML5.

* **Fit:** A candidate transform for the ML features, after the held-out ML test exists.
* **Against:** Choosing d on the full sample leaks.
* **Built:** `ml.info_bars.frac_diff_ffd` (C-ML5).
* **Details:** [docs/algorithms/fractional-differentiation-feature-pipeline.md](algorithms/fractional-differentiation-feature-pipeline.md)

### RK301. Temporal Fusion Transformer forecasting ⛔

Multi-horizon attention-based forecaster (Lim et al. 2021). In Qlib's own equity benchmark it ranks below LightGBM; trading studies found are single-stock and pre-cost.

* **Fit:** The ML pipeline's problem is signal, not model capacity (as RK292, C-RJ4).
* **Against:** Accuracy is not profit; tuning; leakage.
* **Built:** Nothing; the rejected deep-forecaster catalog (C-RJ4) has an LSTM, no TFT.
* **Details:** [docs/algorithms/temporal-fusion-transformer-forecasting.md](algorithms/temporal-fusion-transformer-forecasting.md)

### RK302. Deep Galerkin Method (DGM) option solver ⛔

Mesh-free deep-learning PDE solver; prices American options in up to 200 dimensions (Sirignano & Spiliopoulos 2018). A pricing method, not a strategy.

* **Fit:** Options excluded.
* **Against:** Hard-to-certify accuracy.
* **Built:** Nothing.
* **Details:** [docs/algorithms/physics-informed-deep-galerkin-method-dgm-option-solver.md](algorithms/physics-informed-deep-galerkin-method-dgm-option-solver.md)

### RK303. Neural jump-diffusion rough Heston smile predictor ⛔

Rough Heston volatility (Hurst near 0.1) with jumps and neural parts to predict the smile; volatility is rough (Gatheral et al. 2018).

* **Fit:** Options excluded.
* **Against:** Slow calibration; surrogate error.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-jump-diffusion-rough-heston-smile-predictor.md](algorithms/neural-jump-diffusion-rough-heston-smile-predictor.md)

### RK304. Recurrent neural Hawkes volatility-jump forecaster ⛔

Forecast volatility jumps with a neural Hawkes process, a continuous-time LSTM setting the intensity of each event type. The neural Hawkes model exists (Mei & Eisner 2017); no market application found.

* **Fit:** Needs event data the warehouse does not have.
* **Against:** Tick data; drifting parameters.
* **Built:** Nothing.
* **Details:** [docs/algorithms/recurrent-neural-hawkes-point-process-volatility-jump-forecaster.md](algorithms/recurrent-neural-hawkes-point-process-volatility-jump-forecaster.md)

### RK305. Quantum annealing binary-quadratic rebalancing ⛔

QUBO rebalancing on a quantum annealer, as RK229; done on real data without a classical advantage (Mugel et al. 2022).

* **Fit:** No portfolio problem here.
* **Against:** No demonstrated advantage.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-annealing-binary-quadratic-portfolio-rebalancing.md](algorithms/quantum-annealing-binary-quadratic-portfolio-rebalancing.md)

### RK306. Micro-price / queue-imbalance signal 🧪 (C-MS2) · ⏳ (fair-value check)

Shift the mid toward the thinner queue. Stoikov's estimated micro-price beats the mid and weighted mid (2018); queue imbalance predicts the next tick for large-tick stocks (Gould & Bonart 2016); a DAX replication failed.

* **Fit:** The weighted mid is research code; no historical quotes, but live triggers could log it.
* **Against:** Tick-to-second horizon; needs queue simulation; mixed replication.
* **Built:** `microstructure.micro_price` (weighted mid), `depth_imbalance` (C-MS2).
* **Details:** [docs/algorithms/microprice-queue-imbalance-signal.md](algorithms/microprice-queue-imbalance-signal.md)

### RK307. Cross-exchange market making (XEMM) ⛔

Quote on an illiquid venue and hedge fills on a liquid one; a crypto bot strategy (Hummingbot) with no performance study.

* **Fit:** One venue; crypto excluded; two-sided quoting.
* **Against:** Hedge-leg slippage and failures.
* **Built:** Nothing.
* **Details:** [docs/algorithms/cross-exchange-market-making-xemm.md](algorithms/cross-exchange-market-making-xemm.md)

### RK308. Dividend capture window ⛔

Buy before the ex-date, sell after. The price drops by less than the dividend on average, a tax effect captured mainly by tax-exempt and corporate traders (Lakonishok & Vermaelen 1986).

* **Fit:** TQQQ's dividend is negligible; out of scope.
* **Against:** Taxes and costs absorb the gap.
* **Built:** Nothing; dividends are only recorded.
* **Details:** [docs/algorithms/dividend-capture-window-strategy.md](algorithms/dividend-capture-window-strategy.md)

### RK309. Gamma scalping / long-gamma rebalancing ⛔

Delta-hedge long options to earn when realised beats implied volatility; on average delta-hedged long options lose (Bakshi & Kapadia 2003).

* **Fit:** Options excluded; the grid is the short-gamma side.
* **Against:** Pays the volatility risk premium.
* **Built:** Nothing.
* **Details:** [docs/algorithms/gamma-scalping-long-gamma-rebalancing.md](algorithms/gamma-scalping-long-gamma-rebalancing.md)

### RK310. Multi-agent RL execution / liquidation ⛔

Execution agents trained among other agents in a simulated book; a double-DQN agent converged toward TWAP (Karpe et al. 2020).

* **Fit:** No large orders here; RL rejected for now (A1).
* **Against:** Simulator-bound; collapses toward TWAP.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-rl-execution-liquidation.md](algorithms/multi-agent-rl-execution-liquidation.md)

### RK311. FinBERT sentiment event arbitrage ⏳ (market-level input) · ⛔ (stock-level trade)

Trade on FinBERT sentiment of news and filings. FinBERT beats dictionaries at classification (Huang et al. 2023); LLM headline scores predict next-day returns, mostly small stocks, decaying with adoption (Lopez-Lira & Tang).

* **Fit:** A market-level series could feed the regime (as RK293); no news archive here.
* **Against:** Timestamp leakage; licensed data; small-stock, decaying edge.
* **Built:** Nothing; event calendars without text (V6).
* **Details:** [docs/algorithms/finbert-sentiment-driven-event-arbitrage.md](algorithms/finbert-sentiment-driven-event-arbitrage.md)

### RK312. Deep Q-network (DQN) liquidation agent ⛔

Deep Q-learning for liquidation; one of RL's better-supported finance uses (Nevmyvaka et al. 2006; Ning, Lin & Jaimungal 2021).

* **Fit:** No large parent orders here; RL rejected for now (A1).
* **Against:** Replay ignores own impact; gains are a fraction of the spread.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deep-q-network-dqn-liquidation-agent.md](algorithms/deep-q-network-dqn-liquidation-agent.md)

### RK313. Adaptive-mesh RL market maker ⛔

RL quoting policies rewarded for spread capture net of inventory risk; in simulators they beat simple benchmarks and learn inventory skew (Spooner et al. 2018; Ganesh et al. 2019).

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Simulator-only; short-capable inventory.
* **Built:** Nothing; closed-form quotes (C-MM1, C-MM2).
* **Details:** [docs/algorithms/adaptive-mesh-reinforcement-learning-market-maker-rl-mm.md](algorithms/adaptive-mesh-reinforcement-learning-market-maker-rl-mm.md)

### RK314. Hawkes jump-diffusion multivariate event detection ⏳ (daily stress gauge)

Jumps with Hawkes intensities that excite each other across markets; US jumps raise foreign intensity more than the reverse, and the filtered intensity works as a stress gauge (Aït-Sahalia et al. 2015).

* **Fit:** A daily jump intensity could join the regime if it leads NATR.
* **Against:** Few jumps to fit; lags in fast crashes.
* **Built:** Nothing.
* **Details:** [docs/algorithms/hawkes-jump-diffusion-multivariate-event-detection.md](algorithms/hawkes-jump-diffusion-multivariate-event-detection.md)

### RK315. Empirical mode decomposition (Hilbert-Huang) intraday scalper ⛔

Trade the phase of empirical-mode-decomposition oscillations (Huang et al. 1998). Finance evidence covers denoising and features, not a rule; end effects leak the future.

* **Fit:** No evidence for a rule; causal use is hard.
* **Against:** End-effect look-ahead; free parameters.
* **Built:** Nothing.
* **Details:** [docs/algorithms/empirical-mode-decomposition-emd-hilbert-huang-intraday-scalper.md](algorithms/empirical-mode-decomposition-emd-hilbert-huang-intraday-scalper.md)

### RK316. Temporal convolutional network (TCN) forecasting ⛔

Causal dilated convolutions for sequence forecasting (Bai et al. 2018). Stock comparisons with LSTMs are mixed and accuracy-only; it trails LightGBM in Qlib's benchmark.

* **Fit:** The ML pipeline's problem is signal, not model capacity.
* **Against:** Accuracy-only evidence; mixed results.
* **Built:** Nothing.
* **Details:** [docs/algorithms/temporal-cnn-tcn-forecasting.md](algorithms/temporal-cnn-tcn-forecasting.md)

### RK317. Meta-labelling primary signals ✅ (V13)

A secondary model predicts whether the primary signal's trade reaches its target and sizes or filters it (López de Prado 2018; Joubert 2022). Built as V13: grid buys scaled by P(target reached).

* **Fit:** Built (V13) in the only form that respects the grid's rules; needs a TQQQ model.
* **Against:** Bounded by a weak secondary model; costs size on good trades.
* **Built:** `reachability_sizing.MLReachabilitySizing` (V13); triple-barrier labels (C-ML1).
* **Details:** [docs/algorithms/meta-labeling-primary-signals.md](algorithms/meta-labeling-primary-signals.md)

### RK318. Graph convolutional network (GCN) stock ranking ⛔

Rank stocks with graph convolutions over relation networks; self-reported back-tests show large gains (Feng et al. 2019).

* **Fit:** Stock selection; no stock universe here.
* **Against:** Snapshot relation look-ahead; self-reported.
* **Built:** Nothing.
* **Details:** [docs/algorithms/graph-convolutional-network-gcn-cross-sectional-stock-ranking.md](algorithms/graph-convolutional-network-gcn-cross-sectional-stock-ranking.md)

### RK319. Volatility-harvesting dynamic asymmetric grid ✅ (V5, the champion)

Independent lots bought on fixed drops from a rolling reference and sold at their own targets, never below cost. This is volatility-ai (V5): 25.38% CAGR at 45.57% drawdown in the best known configuration; a static grid has near-zero expectation without mean reversion (Chen, Chen & Jang 2025).

* **Fit:** It is the project; drawdown in long declines is the binding problem.
* **Against:** Fills every rung in a long decline; fill-model sensitivity.
* **Built:** `HighFrequencyLocalReferenceSizing` (V5), `HarvestSleeveSizing`, C-G3, V3.
* **Details:** [docs/algorithms/vol-harvesting-dynamic-asymmetric-grid.md](algorithms/vol-harvesting-dynamic-asymmetric-grid.md)

### RK320. Koopman-operator volatility-surface interpolator ⛔

Interpolate the implied-volatility surface with Koopman-linearised dynamics. No study found.

* **Fit:** Options excluded.
* **Against:** Untested; no arbitrage constraints.
* **Built:** Nothing.
* **Details:** [docs/algorithms/koopman-operator-non-linear-volatility-surface-interpolator.md](algorithms/koopman-operator-non-linear-volatility-surface-interpolator.md)

### RK321. Koopman-operator volatility-surface pricing model ⛔

Price options from a volatility surface whose dynamics are linearised with a Koopman dictionary. No study found.

* **Fit:** Options excluded.
* **Against:** Untested; no arbitrage constraints.
* **Built:** Nothing.
* **Details:** [docs/algorithms/koopman-operator-non-linear-volatility-surface-pricing-model.md](algorithms/koopman-operator-non-linear-volatility-surface-pricing-model.md)

### RK322. Order-book imbalance signal 🧪 (C-MS2) · ⛔ (needs depth)

Resting buy versus sell volume near the mid predicts the next ticks (Gould & Bonart 2016); order-flow changes explain price changes better (Cont, Kukanov & Stoikov 2014).

* **Fit:** Research code exists; no depth data, live or historical.
* **Against:** Spoofable depth; tick horizon.
* **Built:** `microstructure.depth_imbalance`, `standardized` (C-MS2).
* **Details:** [docs/algorithms/order-book-imbalance-signal.md](algorithms/order-book-imbalance-signal.md)

### RK323. Physics-informed neural operator yield-curve dynamics ⛔

Learn yield-curve dynamics with a Fourier neural operator constrained by a term-structure PDE. No study found.

* **Fit:** No use here.
* **Against:** Untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/physics-informed-neural-operator-fno-yield-curve-dynamics.md](algorithms/physics-informed-neural-operator-fno-yield-curve-dynamics.md)

### RK324. Wasserstein distributionally robust neural SDE hedging ⛔

Hedge against the worst neural-SDE market within a Wasserstein ball around the calibrated one. Neural-SDE robust bounds and hedges are the antecedent (Gierjatowicz et al.).

* **Fit:** Options excluded.
* **Against:** Ambiguity-set choice; costly hedges.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-neural-sde-hedging.md](algorithms/wasserstein-distributionally-robust-neural-sde-hedging.md)

### RK325. Neural-operator controlled portfolio dynamic hedging ⛔

Learn the map from market-state paths to hedge ratios with a neural operator. No study found.

* **Fit:** No use here.
* **Against:** Untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-operator-controlled-portfolio-dynamic-hedging.md](algorithms/neural-operator-controlled-portfolio-dynamic-hedging.md)

### RK326. Neural-operator functional gradient boosting alpha ⛔

Neural operators combined by gradient boosting to forecast the cross-section. The operator class is for PDEs (Li et al. 2021); no alpha study found.

* **Fit:** Stock selection; no stock universe here.
* **Against:** No physics in returns; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-operator-functional-gradient-boosting-cross-sectional-alpha.md](algorithms/neural-operator-functional-gradient-boosting-cross-sectional-alpha.md)

### RK327. Domain-adversarial (DANN) cross-market alpha transfer ⛔

Transfer a forecaster across markets with domain-adversarial training (Ganin et al. 2016); stock studies report accuracy gains of a few points, no trading results.

* **Fit:** Cross-market stock alpha; out of scope.
* **Against:** Invariance can discard signal; accuracy-only.
* **Built:** Nothing.
* **Details:** [docs/algorithms/domain-adversarial-neural-network-dann-cross-market-alpha-transfer.md](algorithms/domain-adversarial-neural-network-dann-cross-market-alpha-transfer.md)

### RK328. Neural rough-volatility path-signature factor model ⛔

Path signatures as factors. Signature trading gives an explicit path-dependent mean-variance solution with drawdown control (Futter, Horvath & Wiese 2023).

* **Fit:** A factor model needs a stock universe; a single-asset signature input would be weak ML.
* **Against:** Feature blow-up; long samples.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-rough-volatility-path-signature-factor-model.md](algorithms/neural-rough-volatility-path-signature-factor-model.md)

### RK329. Wasserstein distributionally robust rough-volatility hedging ⛔

Hedge against the worst rough-volatility model in a Wasserstein ball around the calibrated one. Neural-SDE robust bounds and hedges are the antecedent (Gierjatowicz et al.).

* **Fit:** Options excluded.
* **Against:** Ambiguity-set choice; costly hedges.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-neural-rough-volatility-hedging.md](algorithms/wasserstein-distributionally-robust-neural-rough-volatility-hedging.md)

### RK330. Rough-path signature delay-differential portfolio control ⛔

Portfolio control by delay-differential equations on path signatures. No study found; signature trading (RK328) covers the idea.

* **Fit:** A multi-asset allocator with no evidence.
* **Against:** Untested; redundant.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-rough-path-signature-delay-differential-portfolio-control.md](algorithms/neural-rough-path-signature-delay-differential-portfolio-control.md)

### RK331. Neural rough differential equation (neural RDE) order-book forecaster ⛔

Neural RDE (Morrill et al. 2021) on order-book data. Signatures help order-book forecasts (Sidogi et al. 2023); no neural-RDE order-book study.

* **Fit:** Needs order-book data the warehouse does not have.
* **Against:** Tick-horizon; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-rough-differential-equation-neural-rde-lob-forecaster.md](algorithms/neural-rough-differential-equation-neural-rde-lob-forecaster.md)

### RK332. Flow-matching order-flow generator ⛔

Order-flow generation by flow matching (Lipman et al. 2022); no order-flow application found.

* **Fit:** Needs order-book data.
* **Against:** Untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/generative-score-based-flow-matching-order-flow-generator.md](algorithms/generative-score-based-flow-matching-order-flow-generator.md)

### RK333. Neural jump-diffusion Hawkes shock detector ⛔

Neural jump SDE whose intensity spikes flag shocks (Jia & Benson 2019); no market application found. RK314's classical version has evidence.

* **Fit:** RK314's classical gauge comes first.
* **Against:** Untested; data-hungry.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-jump-diffusion-hawkes-point-process-shock-detector.md](algorithms/neural-jump-diffusion-hawkes-point-process-shock-detector.md)

### RK334. Neural controlled differential equation order-book trend anticipator ⛔

Drive a neural CDE with the order-book path, which handles irregular event times natively, to anticipate short-term trends. The model class exists (Kidger et al. 2020); no order-book study found.

* **Fit:** Needs order-book data the warehouse does not have.
* **Against:** Untested; tick horizon.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-controlled-differential-equation-lob-trend-anticipator.md](algorithms/neural-controlled-differential-equation-lob-trend-anticipator.md)

### RK335. Wasserstein distributionally robust RL market making ⛔

RL market maker trained against a Wasserstein ball of order-flow models. No study found.

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Arbitrary radius; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-rl-market-making.md](algorithms/wasserstein-distributionally-robust-rl-market-making.md)

### RK336. Score-based diffusion order-book simulator ⛔

Generate reactive order flow with a diffusion model as a market simulator; TRADES (2025) does this and is open source.

* **Fit:** Needs order-book data; the grid trades minute bars.
* **Against:** Immature realism metrics.
* **Built:** Nothing.
* **Details:** [docs/algorithms/score-based-generative-diffusion-limit-order-book-simulator.md](algorithms/score-based-generative-diffusion-limit-order-book-simulator.md)

### RK337. Neural controlled jump-diffusion order-book pricing model ⛔

Combine a neural CDE driven by the order book with jump terms to price the next mid-quote. The model class exists (Kidger et al. 2020); no order-book study found.

* **Fit:** Needs order-book data the warehouse does not have.
* **Against:** Untested; tick horizon.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-controlled-jump-diffusion-order-book-pricing-model.md](algorithms/neural-controlled-jump-diffusion-order-book-pricing-model.md)

### RK338. Recurrent neural Hawkes liquidity-shock detector ⛔

Detect liquidity shocks (spread blow-outs, depth withdrawals) from the intensity of a neural Hawkes process over order-book events. The neural Hawkes model exists (Mei & Eisner 2017); no market application found.

* **Fit:** Needs event data the warehouse does not have.
* **Against:** Tick data; drifting parameters.
* **Built:** Nothing.
* **Details:** [docs/algorithms/recurrent-neural-hawkes-point-process-liquidity-shock-detector.md](algorithms/recurrent-neural-hawkes-point-process-liquidity-shock-detector.md)

### RK339. Multi-agent RL Nash market maker ⛔

Market makers trained jointly to a Nash equilibrium. Multi-agent simulators exist (Ganesh et al. 2019); no performance study of the equilibrium learner.

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Non-convergence; simulator-dependent.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-reinforcement-learning-nash-market-maker.md](algorithms/multi-agent-reinforcement-learning-nash-market-maker.md)

### RK340. Fractional-order cointegration VECM neural network ⛔

FCVAR with a neural error-correction term, as RK239. FCVAR is established (Johansen & Nielsen 2012); the neural variant is untested.

* **Fit:** Basket trading with short weights; out of scope.
* **Against:** Overfitting; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/fractional-order-cointegration-vector-error-correction-neural-network.md](algorithms/fractional-order-cointegration-vector-error-correction-neural-network.md)

### RK341. Multi-agent RL Stackelberg market maker ⛔

Treat the market maker as a Stackelberg leader that quotes first and the other traders as followers that best-respond, and learn the leader's quotes with RL. Stackelberg RL methods exist; no market-making performance study found.

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Untested; simulator-dependent.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-reinforcement-learning-stackelberg-market-maker.md](algorithms/multi-agent-reinforcement-learning-stackelberg-market-maker.md)

### RK342. Rough-path signature Hawkes point-process forecaster ⛔

Signature features of the order-flow path to forecast Hawkes intensities. Signatures helped order-book forecasts once (Sidogi et al. 2023); no signature-Hawkes study.

* **Fit:** Needs event data the warehouse does not have.
* **Against:** Feature blow-up; event data.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-rough-path-signature-hawkes-point-process-forecaster.md](algorithms/neural-rough-path-signature-hawkes-point-process-forecaster.md)

### RK343. Score-based diffusion order-book flow synthesizer ⛔

Diffusion-generated order flow for data augmentation; TRADES (2025) is the nearest system (see RK336).

* **Fit:** Needs order-book data.
* **Against:** Inherits the training regime.
* **Built:** Nothing.
* **Details:** [docs/algorithms/generative-score-based-diffusion-limit-order-book-flow-synthesizer.md](algorithms/generative-score-based-diffusion-limit-order-book-flow-synthesizer.md)

### RK344. Multi-agent RL Stackelberg market-maker equilibrium ⛔

Solve for the Stackelberg equilibrium between a leading market maker and following traders with multi-agent RL, as a model of how quotes should be set. Stackelberg RL methods exist; no market-making performance study found.

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Untested; simulator-dependent.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-reinforcement-learning-stackelberg-market-maker-equilibrium.md](algorithms/multi-agent-reinforcement-learning-stackelberg-market-maker-equilibrium.md)

### RK345. Multi-agent RL Stackelberg spread capture ⛔

Use a Stackelberg leader-follower formulation to learn quotes that maximise spread captured from following traders. Stackelberg RL methods exist; no market-making performance study found.

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Untested; simulator-dependent.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-reinforcement-learning-stackelberg-spread-capture.md](algorithms/multi-agent-reinforcement-learning-stackelberg-spread-capture.md)

### RK346. Soft actor-critic (SAC) continuous-action trader 🧪 (A1) · ❌ (as a trader)

Soft actor-critic maximises reward plus the policy's entropy, which keeps exploring and is stable with continuous actions such as a position size. FinRL's ensemble beat the Dow in its authors' back-test (Yang et al. 2020); many DRL profits are back-test overfitting (Gort et al. 2022).

* **Fit:** Rejected for now (A1); V13 already makes the size decision with fewer parameters.
* **Against:** Back-test overfitting; seed and reward sensitivity.
* **Built:** `rl_agents.sac_target` (A1).
* **Details:** [docs/algorithms/sac-continuous-action-trading-agent.md](algorithms/sac-continuous-action-trading-agent.md)

### RK347. DDPG / TD3 continuous-control trader 🧪 (A1) · ❌ (as a trader)

DDPG learns a deterministic policy for continuous actions with an off-policy critic; TD3 adds twin critics, delayed policy updates and target smoothing to curb DDPG's overestimation. FinRL's ensemble beat the Dow in its authors' back-test (Yang et al. 2020); many DRL profits are back-test overfitting (Gort et al. 2022).

* **Fit:** Rejected for now (A1); V13 already makes the size decision with fewer parameters.
* **Against:** Back-test overfitting; seed and reward sensitivity.
* **Built:** `rl_agents.ddpg_target`, `td3_target` (A1).
* **Details:** [docs/algorithms/ddpg-td3-continuous-control-trader.md](algorithms/ddpg-td3-continuous-control-trader.md)

### RK348. Phase-space-reconstructed neural ODE (PSR-NODE) ⛔

Neural ODE on a delay-embedded phase space. Returns show no low-dimensional attractor; no finance study found.

* **Fit:** No mechanism or evidence.
* **Against:** Free embedding parameters; noise.
* **Built:** Nothing.
* **Details:** [docs/algorithms/phase-space-reconstructed-neural-ode-psr-node.md](algorithms/phase-space-reconstructed-neural-ode-psr-node.md)

### RK349. Time-series GAN (TimeGAN) scenario generation ⏳ (stress-test tool)

Adversarial plus supervised latent training for realistic time series (Yoon et al. 2019). A scenario generator; diffusion models now claim better stylized facts.

* **Fit:** A stress-test tool; a block bootstrap comes first.
* **Against:** Unstable training; mode collapse drops crashes.
* **Built:** Nothing.
* **Details:** [docs/algorithms/time-series-generative-adversarial-network-timegan.md](algorithms/time-series-generative-adversarial-network-timegan.md)

### RK350. Physics-informed Schrödinger volatility solver ⛔

Fit volatility with a PINN for the Schrödinger equation. PINNs exist (Raissi et al. 2019); no volatility study or mechanism.

* **Fit:** No mechanism or evidence.
* **Against:** No mechanism.
* **Built:** Nothing.
* **Details:** [docs/algorithms/physics-informed-deep-learning-schrodinger-volatility-solver.md](algorithms/physics-informed-deep-learning-schrodinger-volatility-solver.md)

### RK351. MADDPG portfolio allocation ⛔

Multi-agent DDPG for joint allocation; in one study it trailed a genetic algorithm badly (Sharpe 1.28 against 3.15).

* **Fit:** A multi-asset allocator with weak evidence.
* **Against:** Overfitting; weak comparative results.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-deep-deterministic-policy-gradient-maddpg-portfolio-allocation.md](algorithms/multi-agent-deep-deterministic-policy-gradient-maddpg-portfolio-allocation.md)

### RK352. Deep hedging with transaction costs ⛔

A network hedges a derivatives book to minimise a risk measure under costs and limits; beats the frictionless hedge in a Heston market (Buehler et al. 2019).

* **Fit:** Options excluded.
* **Against:** Simulator-dependent.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deep-hedging-with-transaction-costs-and-friction.md](algorithms/deep-hedging-with-transaction-costs-and-friction.md)

### RK353. Recurrent neural Hawkes execution timing ⛔

Time child orders by a neural Hawkes forecast of when liquidity will arrive. No execution study of the neural Hawkes form found.

* **Fit:** Small orders; no event data.
* **Against:** Event data; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/recurrent-neural-hawkes-point-process-execution-timing.md](algorithms/recurrent-neural-hawkes-point-process-execution-timing.md)

### RK354. Multi-agent RL evolutionary market maker ⛔

Evolve a population of RL market makers with genetic operators, keeping the most profitable quoting policies. No study found.

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Untested; data snooping.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-reinforcement-learning-evolutionary-market-maker.md](algorithms/multi-agent-reinforcement-learning-evolutionary-market-maker.md)

### RK355. Recurrent neural Hawkes toxic-flow execution ⛔

Slow or reroute execution when a neural Hawkes model forecasts a burst of informed (toxic) order flow. No execution study of the neural Hawkes form found.

* **Fit:** Small orders; no event data.
* **Against:** Event data; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/recurrent-neural-hawkes-point-process-toxic-flow-execution.md](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-execution.md)

### RK356. Recurrent neural Hawkes dynamic-inventory market maker ⛔

Neural Hawkes forecasts of order arrivals drive inventory-skewed quotes. No market-making study of the neural version found.

* **Fit:** Two-sided quoting on event data; out of scope.
* **Against:** Event data; closed-form alternatives.
* **Built:** Nothing.
* **Details:** [docs/algorithms/recurrent-neural-hawkes-point-process-dynamic-inventory-market-maker.md](algorithms/recurrent-neural-hawkes-point-process-dynamic-inventory-market-maker.md)

### RK357. Recurrent neural Hawkes toxic-flow execution pauser ⛔

Pause execution outright while a neural Hawkes model's toxic-flow intensity is high. No execution study of the neural Hawkes form found.

* **Fit:** Small orders; no event data.
* **Against:** Event data; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/recurrent-neural-hawkes-point-process-toxic-flow-execution-pauser.md](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-execution-pauser.md)

### RK358. Multi-agent RL evolutionary execution routing ⛔

Evolve a population of RL routing agents that split child orders across venues. No study found.

* **Fit:** No large orders or venue choice here.
* **Against:** Untested; data snooping.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-reinforcement-learning-evolutionary-execution-routing.md](algorithms/multi-agent-reinforcement-learning-evolutionary-execution-routing.md)

### RK359. Multi-agent RL evolutionary market-making equilibrium ⛔

Let an evolving population of market-making agents settle into an evolutionarily stable quoting equilibrium. No study found.

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Untested; data snooping.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-reinforcement-learning-evolutionary-market-making-equilibrium.md](algorithms/multi-agent-reinforcement-learning-evolutionary-market-making-equilibrium.md)

### RK360. Multi-agent RL evolutionary execution allocator ⛔

Evolve a population of RL agents that allocate a parent order over time and venues. No study found.

* **Fit:** No large orders or venue choice here.
* **Against:** Untested; data snooping.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-reinforcement-learning-evolutionary-execution-allocator.md](algorithms/multi-agent-reinforcement-learning-evolutionary-execution-allocator.md)

### RK361. Multi-agent deep RL order-book market maker ⛔

Deep RL market maker among learning competitors; in a dealer simulator it learns competitor-aware inventory skew (Ganesh et al. 2019).

* **Fit:** Two-sided quoting; RL rejected for now (A1).
* **Against:** Simulator-only.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deep-reinforcement-learning-order-book-market-maker-marl-mm.md](algorithms/deep-reinforcement-learning-order-book-market-maker-marl-mm.md)

### RK362. Koopman-operator MPC execution ⛔

Koopman-linearised dynamics with MPC to schedule execution. No study found.

* **Fit:** Small orders; nothing to schedule.
* **Against:** Untested; model-dependent.
* **Built:** Nothing.
* **Details:** [docs/algorithms/koopman-operator-model-predictive-control-execution.md](algorithms/koopman-operator-model-predictive-control-execution.md)

### RK363. TWAP execution 🧪 (AC lead, λ = 0) · ⛔ (not needed)

Equal slices over time to track the time-weighted average price; the Almgren-Chriss path at zero risk aversion. A double-DQN agent converged to it in simulation (Karpe et al. 2020).

* **Fit:** Orders here are small; nothing to slice.
* **Against:** Predictable; ignores volume profile.
* **Built:** `leads.almgren_chriss` (risk_aversion = 0 gives TWAP).
* **Details:** [docs/algorithms/twap-execution.md](algorithms/twap-execution.md)

### RK364. VWAP execution ⛔

Slice along the intraday volume curve to track VWAP, the standard institutional benchmark (Berkowitz, Logue & Noser 1988).

* **Fit:** Orders here are small; VWAP is used as a gate (C-MS3), not a schedule.
* **Against:** A benchmark, not alpha.
* **Built:** Nothing for execution; `session_vwap` as a gate (C-MS3).
* **Details:** [docs/algorithms/vwap-execution.md](algorithms/vwap-execution.md)

### RK365. Percent-of-volume (POV) execution ⛔

Trade a fixed share of realised volume until done; adaptive speed, uncertain completion.

* **Fit:** Orders here are small; nothing to schedule.
* **Against:** Uncertain completion; pro-cyclical.
* **Built:** Nothing.
* **Details:** [docs/algorithms/pov-percent-of-volume-execution.md](algorithms/pov-percent-of-volume-execution.md)

### RK366. Implementation shortfall / Almgren-Chriss 🧪 (AC lead) · ⏳ (shortfall measurement)

Measure execution against the decision price (Perold 1988) and minimise expected shortfall plus its variance (Almgren & Chriss 2001).

* **Fit:** The trajectory is research code; logging each fill's shortfall (RK250) is the useful part.
* **Against:** Linear-impact assumptions; hard-to-estimate parameters.
* **Built:** `leads.almgren_chriss`, `almgren_chriss_objective`.
* **Details:** [docs/algorithms/implementation-shortfall-almgren-chriss.md](algorithms/implementation-shortfall-almgren-chriss.md)

### RK367. Hawkes-driven optimal execution with transient impact ⛔

Optimal execution when other traders' orders are Hawkes-driven; explicit optimum, and conditions that rule out price manipulation (Alfonsi & Blanc 2016).

* **Fit:** Large-order execution on event data; not applicable.
* **Against:** Order-level calibration.
* **Built:** Nothing.
* **Details:** [docs/algorithms/hawkes-driven-optimal-execution-with-transitory-price-impact.md](algorithms/hawkes-driven-optimal-execution-with-transitory-price-impact.md)

### RK368. Continuous-time mean-field control execution ⛔

Liquidation among a crowd of similar traders as a mean-field game; closed form, follow the crowd but not too fast (Cardaliaguet & Lehalle 2018).

* **Fit:** Large-order execution theory; not applicable.
* **Against:** Stylised crowd; estimation.
* **Built:** Nothing.
* **Details:** [docs/algorithms/continuous-time-mean-field-control-execution.md](algorithms/continuous-time-mean-field-control-execution.md)

### RK369. Multi-agent mean-field game execution routing ⛔

Mean-field game for routing child orders across venues. No routing study found.

* **Fit:** One broker; no venue choice.
* **Against:** Untested; ignores venue details.
* **Built:** Nothing.
* **Details:** [docs/algorithms/multi-agent-mean-field-game-optimal-execution-routing.md](algorithms/multi-agent-mean-field-game-optimal-execution-routing.md)

### RK370. Wasserstein distributionally robust optimal execution trajectory ⛔

Choose the liquidation path that minimises cost under the worst price-impact and volatility model in a Wasserstein ball around the estimated one. No study found.

* **Fit:** Small orders; nothing to schedule.
* **Against:** Arbitrary radius; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-optimal-execution-trajectory.md](algorithms/wasserstein-distributionally-robust-optimal-execution-trajectory.md)

### RK371. Wasserstein distributionally robust Hawkes execution ⛔

Optimise execution against the worst Hawkes order-flow model within a Wasserstein ball. No study found.

* **Fit:** Small orders; nothing to schedule.
* **Against:** Arbitrary radius; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/wasserstein-distributionally-robust-hawkes-point-process-execution.md](algorithms/wasserstein-distributionally-robust-hawkes-point-process-execution.md)

### RK372. PPO reinforcement-learning trader 🧪 (A1) · ❌ (as a trader)

Proximal policy optimisation clips each policy update to stay near the previous policy, with advantages from generalised advantage estimation; it is the default on-policy algorithm in most RL libraries. FinRL's ensemble beat the Dow in its authors' back-test (Yang et al. 2020); many DRL profits are back-test overfitting (Gort et al. 2022).

* **Fit:** Rejected for now (A1); V13 already makes the size decision with fewer parameters.
* **Against:** Back-test overfitting; seed and reward sensitivity.
* **Built:** `rl_agents.ppo_clip_loss`, `gae` (A1).
* **Details:** [docs/algorithms/ppo-reinforcement-learning-trader.md](algorithms/ppo-reinforcement-learning-trader.md)

### RK373. Generative moment matching network (GMMN) portfolio simulator ⏳ (stress-test tool)

MMD-trained generators sample dependent risks; with quasi-random inputs they cut the variance of tail estimates such as expected shortfall (Hofert, Prasad & Zhu 2021).

* **Fit:** A risk-sampling tool; this book's risk is one instrument.
* **Against:** Cannot exceed the sample's dependence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/generative-moment-matching-network-gmmn-portfolio-simulator.md](algorithms/generative-moment-matching-network-gmmn-portfolio-simulator.md)

### RK374. Physics-informed (PINN) Burgers volatility model ⛔

Fit volatility with a PINN for the Burgers equation. PINNs exist (Raissi et al. 2019); no volatility study or mechanism.

* **Fit:** No mechanism or evidence.
* **Against:** No mechanism.
* **Built:** Nothing.
* **Details:** [docs/algorithms/physics-informed-neural-network-pinn-burgers-volatility-model.md](algorithms/physics-informed-neural-network-pinn-burgers-volatility-model.md)

### RK375. Quantum support vector regression return predictor ⛔

Predict returns with support vector regression on a quantum kernel. Demonstrated only on toy problems; no finance study found.

* **Fit:** Hardware not ready; no evidence.
* **Against:** Toy demonstrations only.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-support-vector-regression-qsvr-return-predictor.md](algorithms/quantum-support-vector-regression-qsvr-return-predictor.md)

### RK376. Deep Koopman market-dynamics predictor ⛔

Deep-autoencoder Koopman coordinates to forecast markets. Established for physical systems (Lusch et al. 2018); no peer-reviewed market study.

* **Fit:** No evidence for market forecasting.
* **Against:** Fits noise; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/deep-koopman-operator-market-dynamics-predictor.md](algorithms/deep-koopman-operator-market-dynamics-predictor.md)

### RK377. Neural SDE stochastic-volatility arbitrage ⛔

Neural-network SDEs calibrated to options give robust price bounds and hedges (Gierjatowicz et al.); trading outside the bounds is model risk, not arbitrage.

* **Fit:** Options excluded.
* **Against:** Wide bounds; model risk.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-sde-controlled-stochastic-volatility-arbitrage.md](algorithms/neural-sde-controlled-stochastic-volatility-arbitrage.md)

### RK378. Tabular diffusion (TabDDPM) trajectory generator ⛔

Diffusion model for mixed-type tables (Kotelnikov et al. 2023); generates rows, not paths, so it cannot produce market trajectories.

* **Fit:** Not a trajectory generator.
* **Against:** No temporal dependence.
* **Built:** Nothing.
* **Details:** [docs/algorithms/generative-diffusion-model-trajectory-generator-tabddpm.md](algorithms/generative-diffusion-model-trajectory-generator-tabddpm.md)

### RK379. Fractional Brownian motion volatility-surface arbitrage ⛔

Trade option quotes against a rough-volatility surface; rough volatility is well supported (Gatheral et al. 2018), but deviations are model risk.

* **Fit:** Options excluded.
* **Against:** Model risk, not arbitrage.
* **Built:** Nothing.
* **Details:** [docs/algorithms/fractional-brownian-motion-fbm-volatility-surface-arbitrage.md](algorithms/fractional-brownian-motion-fbm-volatility-surface-arbitrage.md)

### RK380. Dynamic latent factor graph neural network (FactorGNN) ⛔

Joint latent factors and stock graph for return forecasts. No paper of this name; nearest is FactorVAE (Duan et al. 2022).

* **Fit:** Stock selection; no stock universe here.
* **Against:** Unidentified latent structure; self-reported.
* **Built:** Nothing.
* **Details:** [docs/algorithms/dynamic-latent-factor-graph-neural-network-factorgnn.md](algorithms/dynamic-latent-factor-graph-neural-network-factorgnn.md)

### RK381. Hyperbolic graph neural network stock selection ⛔

Graph attention in hyperbolic space for stock selection; HyperStockGAT reports higher profit and Sharpe than Euclidean models on four markets (Sawhney et al. 2021, self-reported).

* **Fit:** Stock selection; no stock universe here.
* **Against:** Self-reported; snapshot relations.
* **Built:** Nothing.
* **Details:** [docs/algorithms/hyperbolic-graph-neural-networks-for-stock-pricing.md](algorithms/hyperbolic-graph-neural-networks-for-stock-pricing.md)

### RK382. Contractive autoencoder latent-factor anomaly detection ⛔

Flag returns a contractive autoencoder cannot reconstruct. Plain autoencoders found biased moves after abnormal prices (Gotou & Suzuki 2016); no contractive version in finance found.

* **Fit:** A stock-level method; a simpler data-quality check suffices.
* **Against:** Flags volatility; refits.
* **Built:** Nothing.
* **Details:** [docs/algorithms/contractive-autoencoder-latent-factor-anomaly-detection.md](algorithms/contractive-autoencoder-latent-factor-anomaly-detection.md)

### RK383. Conditional WGAN-GP yield-curve synthesizer ⛔

Conditional WGAN-GP for yield-curve scenarios; on US curves it ties historical simulation and GARCH rather than beating them (Guo 2024).

* **Fit:** No use for this book.
* **Against:** Ties simpler methods.
* **Built:** Nothing.
* **Details:** [docs/algorithms/conditional-wasserstein-gan-gp-yield-curve-synthesizer.md](algorithms/conditional-wasserstein-gan-gp-yield-curve-synthesizer.md)

### RK384. Geometric deep learning non-Euclidean alpha predictor ⛔

Non-Euclidean networks for cross-sectional alpha; the only study found is hyperbolic graph attention (RK381).

* **Fit:** Stock selection; no stock universe here.
* **Against:** Self-reported; ungrounded geometry.
* **Built:** Nothing.
* **Details:** [docs/algorithms/geometric-deep-learning-non-euclidean-alpha-predictor.md](algorithms/geometric-deep-learning-non-euclidean-alpha-predictor.md)

### RK385. Graph-attention supply-chain contagion stock predictor ⛔

Predict returns from supplier and customer moves with a graph attention network. The effect is documented: customer momentum earned about 1.55% a month (Cohen & Frazzini 2008); no evidence the GNN adds to it.

* **Fit:** Single-stock long-short; out of scope for an index ETF.
* **Against:** Licensed supply-chain data; short leg.
* **Built:** Nothing.
* **Details:** [docs/algorithms/graph-attention-network-gat-supply-chain-contagion-stock-predictor.md](algorithms/graph-attention-network-gat-supply-chain-contagion-stock-predictor.md)

### RK386. Transfer-entropy graph neural network alpha model ⛔

A GNN over a transfer-entropy graph of stocks. No study found.

* **Fit:** Stock selection; no stock universe here.
* **Against:** Noisy graph; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/information-theoretic-transfer-entropy-graph-neural-network-alpha-model.md](algorithms/information-theoretic-transfer-entropy-graph-neural-network-alpha-model.md)

### RK387. Quantum-kernel SVM cross-sectional alpha ⛔

Classify stocks' next-period returns with a support vector machine on a quantum kernel. Demonstrated only on toy problems; no finance study found.

* **Fit:** Hardware not ready; no evidence.
* **Against:** Toy demonstrations only.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-kernel-based-svm-cross-sectional-alpha-predictor.md](algorithms/quantum-kernel-based-svm-cross-sectional-alpha-predictor.md)

### RK388. Dynamic copula-quantile regression neural network alpha ⛔

Quantile neural networks for return distributions, joined by a copula, to rank stocks. Quantile networks beat standard models out of sample (Baruník et al.); the copula combination is untested.

* **Fit:** Stock-level alpha; no stock universe here.
* **Against:** Extra estimation error; untested combination.
* **Built:** Nothing.
* **Details:** [docs/algorithms/dynamic-copula-quantile-regression-neural-network-alpha-model.md](algorithms/dynamic-copula-quantile-regression-neural-network-alpha-model.md)

### RK389. Quantum annealing entropic value-at-risk optimisation ⛔

EVaR portfolio minimisation on a quantum annealer. No study found; EVaR is convex and solves classically.

* **Fit:** No portfolio problem here.
* **Against:** Classically solvable; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-annealing-entropic-value-at-risk-portfolio-optimization.md](algorithms/quantum-annealing-entropic-value-at-risk-portfolio-optimization.md)

### RK390. Neural-operator flow-matching alpha forecaster ⛔

Flow matching on a neural operator to forecast the cross-section. No study found.

* **Fit:** Stock selection; no stock universe here.
* **Against:** Untested; low signal-to-noise.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-operator-flow-matching-cross-sectional-alpha-forecaster.md](algorithms/neural-operator-flow-matching-cross-sectional-alpha-forecaster.md)

### RK391. Rough-volatility signature deep hedging ⛔

Deep hedging under rough volatility with signature inputs; studied by Horvath, Teichmann & Žurič (2021).

* **Fit:** Options excluded.
* **Against:** Feature blow-up; simulator-dependent.
* **Built:** Nothing.
* **Details:** [docs/algorithms/neural-rough-volatility-fractional-signature-deep-hedging.md](algorithms/neural-rough-volatility-fractional-signature-deep-hedging.md)

### RK392. Fractional-order VAR macro allocator ⛔

Asset allocation from a fractionally integrated macro VAR. No allocation study found.

* **Fit:** A multi-asset allocator with no evidence.
* **Against:** Imprecise long-memory estimates.
* **Built:** Nothing.
* **Details:** [docs/algorithms/fractional-order-vector-autoregressive-var-macro-allocator.md](algorithms/fractional-order-vector-autoregressive-var-macro-allocator.md)

### RK393. Quantum neural network volatility-surface forecaster ⛔

Forecast implied-volatility surfaces with a parameterised quantum circuit. Demonstrated only on toy problems; no finance study found.

* **Fit:** Hardware not ready; no evidence.
* **Against:** Toy demonstrations only.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-neural-network-qnn-volatility-surface-forecaster.md](algorithms/quantum-neural-network-qnn-volatility-surface-forecaster.md)

### RK394. Graph diffusion convolutional network stock alpha ⛔

Diffusion convolutions over a stock graph to forecast returns. The architecture comes from traffic forecasting; no stock study found.

* **Fit:** Stock selection; no stock universe here.
* **Against:** Untested; snapshot relations.
* **Built:** Nothing.
* **Details:** [docs/algorithms/graph-diffusion-convolutional-network-cross-sectional-alpha.md](algorithms/graph-diffusion-convolutional-network-cross-sectional-alpha.md)

### RK395. Score-based diffusion macro-factor synthesizer ⏳ (stress-test tool)

Diffusion-generated macro-factor scenarios for stress tests; factor-structured diffusion has recent theory (Chen et al. 2025), no macro application found.

* **Fit:** RK200's tool on a different panel.
* **Against:** Short macro samples.
* **Built:** Nothing.
* **Details:** [docs/algorithms/generative-score-based-diffusion-macro-factor-synthesizer.md](algorithms/generative-score-based-diffusion-macro-factor-synthesizer.md)

### RK396. Riemannian graph-diffusion covariance estimator ⛔

Smooth covariance estimates by diffusing them over an asset graph while respecting the geometry of positive-definite matrices. Untested; shrinkage is the baseline.

* **Fit:** A multi-asset input; the engine trades one symbol.
* **Against:** Must beat shrinkage; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/riemannian-manifold-metric-graph-diffusion-covariance-estimator.md](algorithms/riemannian-manifold-metric-graph-diffusion-covariance-estimator.md)

### RK397. Quantum-annealing GNN covariance shrinkage ⛔

Choose covariance shrinkage targets with a graph neural network and optimise them on a quantum annealer. Untested; shrinkage is the baseline.

* **Fit:** A multi-asset input; the engine trades one symbol.
* **Against:** Must beat shrinkage; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/quantum-annealing-graph-neural-network-covariance-shrinkage.md](algorithms/quantum-annealing-graph-neural-network-covariance-shrinkage.md)

### RK398. Persistent-homology Betti-2 landscape macro contagion ⛔

Betti-2 persistence landscapes as a contagion warning. Landscape norms rose before two crashes (Gidea & Katz 2018); nothing for Betti-2.

* **Fit:** RK255 first.
* **Against:** Rare, noisy features.
* **Built:** Nothing.
* **Details:** [docs/algorithms/persistent-homology-betti-2-persistence-landscape-macro-contagion.md](algorithms/persistent-homology-betti-2-persistence-landscape-macro-contagion.md)

### RK399. Score-based diffusion cross-sectional factor synthesizer ⛔

Factor-structured diffusion for synthetic cross-sections of returns (Chen, Xu, Xu & Zhang 2025).

* **Fit:** Cross-sectional; no stock universe here.
* **Against:** Hard to validate.
* **Built:** Nothing.
* **Details:** [docs/algorithms/generative-score-based-diffusion-cross-sectional-factor-synthesizer.md](algorithms/generative-score-based-diffusion-cross-sectional-factor-synthesizer.md)

### RK400. Graph-attention Riemannian covariance shrinkage ⛔

Shrink covariance matrices with graph attention while keeping them on the positive-definite manifold. Untested; shrinkage is the baseline.

* **Fit:** A multi-asset input; the engine trades one symbol.
* **Against:** Must beat shrinkage; untested.
* **Built:** Nothing.
* **Details:** [docs/algorithms/graph-attention-network-riemannian-manifold-covariance-shrinkage.md](algorithms/graph-attention-network-riemannian-manifold-covariance-shrinkage.md)

### Research gaps

Ranks 4–100 were researched from what web search could reach (full texts
could not be opened; each page says what was checked). On 2026-10-27 the
remaining gaps were checked again against a Gemini answer the owner
supplied. Its citations were verified before use, which resolved RK34,
RK40/RK45 and RK54 and added sources to several other pages; its
performance claims that named no study, and citations that turned out to
be about something else, were not used.

Ranks 200–300 were researched the same way on 2026-10-27, and ranks
301–400 on 2026-10-28. Many entries in these ranges cite an arXiv ID with
a sequential-digit pattern (2103.01234, 2106.09876, 1908.01234 and
similar). The pages first called these placeholders. A title search on
2026-10-29, prompted by the CSV's own review column, showed that the ones
it could resolve are real papers on unrelated subjects: black-hole physics
(2103.01234), a heat pump (2104.09876), an electromagnetic bioreactor
(1908.01234), sterile neutrinos (2110.09876), crystalline measures
(2004.05678), supernova dust (2102.05678) and graph anomaly detection
(2106.09876). The pages now name them; the rest could not be identified.
Several real IDs are attached to the wrong entry: arXiv 2009.08295,
Morrill et al.'s neural rough differential equations, is cited for four
pricing and hedging entries. What remains:

| Status | Meaning |
|---|---|
| Needs more info | A specific reference is cited or likely exists, but it could not be identified or read. |
| Unable to find more details | Neither search found a published evaluation; the algorithm is probably untested. |

| ID | Algorithm | Status | What is missing |
|---|---|---|---|
| RK31 | [Intangibles-Adjusted Value and Profitability Factor](algorithms/intangibles-adjusted-value-and-profitability-factor.md) | Needs more info | The CSV's second reference, doi 10.1111/fima.12505. Gemini attributes it to Ozdagli & Ryfe, "Asset Manager Commonality and Portfolio Similarity"; a Dallas Fed working paper of that title exists, but the DOI match is unconfirmed, and if right it is unrelated to intangibles. |
| RK38 | [Chandelier Exit Trend Following](algorithms/chandelier-exit-trend-following.md) | Unable to find more details | A performance study. LeBeau's original Traders Club write-up is not online. |
| RK44 | [Supertrend ATR-Band Trend Following](algorithms/supertrend-atr-band-trend-following.md) | Needs more info | A primary source by Olivier Seban. His book *Tout le monde mérite d'être riche* exists, but nothing confirms it describes Supertrend. |
| RK64 | [Triple EMA / Moving-Average Ribbon](algorithms/triple-ema-moving-average-ribbon.md) | Unable to find more details | A test of ribbon or alignment rules. Brock, Lakonishok & LeBaron (1992) test single and dual moving averages, not ribbons. |
| RK68 | [Dual Thrust Breakout](algorithms/dual-thrust-breakout.md) | Needs more info | Michael Chalek's original publication, and any academic test. |
| RK69 | [London Session Breakout](algorithms/london-session-breakout.md) | Unable to find more details | A test of the Asian-range breakout. Gemini's citation (Chaboud et al. 2014) is about algorithmic trading and FX efficiency. |
| RK77 | [ATR Volatility-Expansion Breakout](algorithms/atr-volatility-expansion-breakout.md) | Unable to find more details | A test of Williams' volatility breakout or an ATR-confirmed breakout. |
| RK78 | [Multi-Timeframe Trend Agreement](algorithms/multi-timeframe-trend-agreement.md) | Unable to find more details | A test of the all-horizons-must-agree form (Elder's Triple Screen, *Futures*, 1986). |
| RK86 | [Yield Curve Steepener / Flattener](algorithms/yield-curve-steepener-flattener.md) | Unable to find more details | A direct test of a DV01-neutral slope rule; forward-rate predictability is documented in sample only (Thornton & Valente 2012). |
| RK92 | [FED OTC Liquidity Sweep & Reverse Repo Arbitrage](algorithms/fed-otc-liquidity-sweep-reverse-repo-arbitrage.md) | Unable to find more details | Any strategy study; "OTC liquidity sweep" appears to be informal wording, so the rule is undefined. |
| RK93 | [Cointegrated Triplet Basket Statistical Arbitrage](algorithms/cointegrated-triplet-basket-statistical-arbitrage.md) | Needs more info | The results of Galenko, Popova & Popova (2012), *Journal of Alternative Investments* 15(1), 85–97, which could not be read; no equity-triplet study found. |
| RK94 | [Dynamic Copula-GARCH Multivariate Pair Trading](algorithms/dynamic-copula-garch-multivariate-pair-trading.md) | Unable to find more details | A copula-GARCH pairs study with reported returns. |
| RK95 | [Asymmetric Tail-Risk Parity Allocation](algorithms/asymmetric-tail-risk-parity-allocation.md) | Unable to find more details | Semivariance risk parity, or an out-of-sample comparison of tail-risk with variance risk parity. |
| RK97 | [Wasserstein Distributionally Robust Statistical Arbitrage](algorithms/wasserstein-distributionally-robust-statistical-arbitrage.md) | Unable to find more details | No Wasserstein-DRO stat-arb paper found. The CSV's arXiv 1908.01234 is a biomedical-engineering paper on an electromagnetic bioreactor and cell tensegrity, unrelated to trading (confirming the owner's Gemini answer). |
| RK98 | [Adversarial Domain Generalization Cross-Market Momentum](algorithms/adversarial-domain-generalization-cross-market-momentum.md) | Unable to find more details | Any application of adversarial domain generalisation to momentum. |
| RK99 | [Conformally Constrained Risk Parity Portfolio](algorithms/conformally-constrained-risk-parity-portfolio.md) | Unable to find more details | Any method combining equal risk contribution with conformal bounds. |
| RK100 | [Causal Discovery Directed Acyclic Graph (DAG) Pair Selection](algorithms/causal-discovery-directed-acyclic-graph-dag-pair-selection.md) | Unable to find more details | Any study using PC or NOTEARS causal discovery for pair selection. |
| RK201 | [Koopman Operator Predictive Control Statistical Arbitrage](algorithms/koopman-operator-predictive-control-statistical-arbitrage.md) | Unable to find more details | No peer-reviewed out-of-sample study of Koopman/MPC trading found; the CSV's reference, arXiv 2004.05678, is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK202 | [Fractional Brownian Motion Multi-Scale Trend Scanning Strategy](algorithms/fractional-brownian-motion-multi-scale-trend-scanning-strategy.md) | Unable to find more details | No study of combining fractional-Brownian-motion tests with multi-horizon trend scanning as a strategy found. |
| RK203 | [Koopman Operator Model Predictive Control Spread Equilibrium](algorithms/koopman-operator-model-predictive-control-spread-equilibrium.md) | Unable to find more details | No peer-reviewed out-of-sample study of Koopman/MPC trading found; the CSV's reference, arXiv 2004.05678, is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK205 | [Dynamic Tensor Decomposition Multi-Asset Factor Rotation](algorithms/dynamic-tensor-decomposition-multi-asset-factor-rotation.md) | Unable to find more details | No study applying tensor decomposition to factor or sector rotation found; the CSV's arXiv 2001.00012 is a student paper on differentially private wavelet mechanisms, unrelated to trading. |
| RK206 | [Koopman Operator Model Predictive Control Multi-Asset Allocation](algorithms/koopman-operator-model-predictive-control-multi-asset-allocation.md) | Unable to find more details | No peer-reviewed out-of-sample study of Koopman/MPC trading found; the CSV's reference, arXiv 2004.05678, is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK208 | [Anchored VWAP Reclaim / Rejection](algorithms/anchored-vwap-reclaim-rejection.md) | Unable to find more details | No academic test of anchored-VWAP signals; practitioner sources only. |
| RK212 | [Market Breadth Thrust](algorithms/market-breadth-thrust.md) | Unable to find more details | No peer-reviewed test of breadth thrusts; only vendor event counts (about 18 signals since 1945). |
| RK216 | [Top-K with Dropout Portfolio Rotation](algorithms/top-k-with-dropout-portfolio-rotation.md) | Unable to find more details | No study of top-K-with-dropout beyond Qlib's own documentation and benchmarks. |
| RK217 | [Bayesian Structural Time Series (BSTS) Causal Impact Macro Strategy](algorithms/bayesian-structural-time-series-bsts-causal-impact-macro-strategy.md) | Unable to find more details | No study using BSTS / CausalImpact as a trading rule; the method measures events after the fact. |
| RK219 | [Dynamic Mode Decomposition (DMD) Market Mode Predictor](algorithms/dynamic-mode-decomposition-dmd-market-mode-predictor.md) | Needs more info | Mann & Kutz (2016)'s backtest results could not be read; their windows were tuned in sample, and no out-of-sample DMD trading study was found. |
| RK221 | [Information-Theoretic Transfer Entropy Lead-Lag Strategy](algorithms/information-theoretic-transfer-entropy-lead-lag-strategy.md) | Unable to find more details | No study of trading on transfer-entropy lead-lag signals found; only measurement studies. |
| RK222 | [Maximum Entropy Production Rate Macro Allocator](algorithms/maximum-entropy-production-rate-macro-allocator.md) | Unable to find more details | No finance study applying maximum entropy production to allocation found; the CSV's arXiv 1709.08765 could not be identified. |
| RK224 | [Deep Latent Force Model (LFM) Interest Rate Forecaster](algorithms/deep-latent-force-model-lfm-interest-rate-forecaster.md) | Unable to find more details | No interest-rate application of latent force models found; the CSV's arXiv 1802.04321 could not be identified. |
| RK227 | [Multi-Agent Evolutionary Reinforcement Learning Portfolio Optimizer](algorithms/multi-agent-evolutionary-reinforcement-learning-portfolio-optimizer.md) | Unable to find more details | No out-of-sample study of evolutionary multi-agent RL allocation found; the CSV's arXiv 2006.09876 could not be identified. |
| RK228 | [Deep Generative Flow Matching Portfolio Generator](algorithms/deep-generative-flow-matching-portfolio-generator.md) | Unable to find more details | No study applying flow matching to portfolio allocation found. |
| RK230 | [Riemannian Manifold Metric Optimization Portfolio](algorithms/riemannian-manifold-metric-optimization-portfolio.md) | Unable to find more details | No study applying Riemannian SPD-manifold optimisation to portfolio construction found; the CSV's arXiv 2106.09876 is a general graph anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance one. |
| RK231 | [Riemannian Manifold Metric Diffusion Portfolio Allocation](algorithms/riemannian-manifold-metric-diffusion-portfolio-allocation.md) | Unable to find more details | No study applying Riemannian SPD-manifold optimisation to portfolio construction found; the CSV's arXiv 2106.09876 is a general graph anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance one. |
| RK232 | [Graph Attention Network Covariance Shrinkage Estimator](algorithms/graph-attention-network-covariance-shrinkage-estimator.md) | Needs more info | GNN covariance estimators appear only in an arXiv comparison (2604.24486) and a 2026 Politecnico di Torino thesis, neither read; the CSV's arXiv 2103.01234 is a black-hole physics paper ("Hidden Symmetry of Vanishing Love"), unrelated to trading. |
| RK233 | [Riemannian Manifold Metric Wasserstein Robust Allocation](algorithms/riemannian-manifold-metric-wasserstein-robust-allocation.md) | Unable to find more details | No study applying Riemannian SPD-manifold optimisation to portfolio construction found; the CSV's arXiv 2106.09876 is a general graph anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance one. |
| RK234 | [Wasserstein Distributionally Robust Reinforcement Learning Portfolio Agent](algorithms/wasserstein-distributionally-robust-reinforcement-learning-portfolio-agent.md) | Unable to find more details | No portfolio study of Wasserstein-robust deep RL found; the CSV's arXiv 2110.09876 is a particle-physics review ("Light Sterile Neutrinos"), unrelated to trading. |
| RK235 | [Graph Attention Network Covariance Matrix Shrinkage Dynamic Allocation](algorithms/graph-attention-network-covariance-matrix-shrinkage-dynamic-allocation.md) | Needs more info | GNN covariance estimators appear only in an arXiv comparison (2604.24486) and a 2026 Politecnico di Torino thesis, neither read; the CSV's arXiv 2103.01234 is a black-hole physics paper ("Hidden Symmetry of Vanishing Love"), unrelated to trading. |
| RK236 | [Quantum Adiabatic Graph Neural Network Portfolio Optimization](algorithms/quantum-adiabatic-graph-neural-network-portfolio-optimization.md) | Unable to find more details | No study combining graph-neural-network embeddings with quantum annealing for portfolios found. |
| RK237 | [Riemannian Manifold Metric Graph Attention Portfolio Allocation](algorithms/riemannian-manifold-metric-graph-attention-portfolio-allocation.md) | Unable to find more details | No study applying Riemannian SPD-manifold optimisation to portfolio construction found. |
| RK238 | [Quantum Adiabatic Tensor Network Portfolio Optimization](algorithms/quantum-adiabatic-tensor-network-portfolio-optimization.md) | Unable to find more details | No study combining tensor networks with adiabatic quantum evolution for portfolios found; the CSV's arXiv 2103.02345 could not be identified. |
| RK239 | [Fractional Order Vector Error Correction Neural Network Portfolio Allocator](algorithms/fractional-order-vector-error-correction-neural-network-portfolio-allocator.md) | Unable to find more details | No study of a neural-network fractionally cointegrated VECM found; the CSV's arXiv 1809.02345 could not be identified. |
| RK240 | [Neural Operator Delay-Differential Stochastic Volatility Calibrator](algorithms/neural-operator-delay-differential-stochastic-volatility-calibrator.md) | Unable to find more details | No study of delay-differential neural operators for volatility calibration found; the CSV's reference, arXiv 2106.09876, is a general graph anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance one. |
| RK241 | [Koopman Operator Multi-Factor Equity Risk Factor Tracking](algorithms/koopman-operator-multi-factor-equity-risk-factor-tracking.md) | Unable to find more details | No peer-reviewed out-of-sample study of Koopman/MPC trading found; the CSV's reference, arXiv 2004.05678, is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK243 | [Price/Volume Anomaly Detection](algorithms/price-volume-anomaly-detection.md) | Unable to find more details | No study showing that anomaly filtering improves trading-strategy returns. |
| RK250 | [Arrival-Price Adaptive Limit-vs-Market Execution](algorithms/arrival-price-adaptive-limit-vs-market-execution.md) | Needs more info | The CSV's reference (Quantitative Finance, doi 10.1080/14697688.2015.1032543) could not be identified. |
| RK256 | [Deep Markov State-Space Intraday Volume Profile Predictor](algorithms/deep-markov-state-space-intraday-volume-profile-predictor.md) | Needs more info | No study of deep Markov volume forecasting found; the CSV's reference, arXiv 2006.12345, could not be identified. |
| RK257 | [Information-Theoretic Causality Flow Macro Asset Allocator](algorithms/information-theoretic-causality-flow-macro-asset-allocator.md) | Unable to find more details | No study of allocation by transfer-entropy information flow found; the CSV's arXiv 1904.08765 could not be identified. |
| RK258 | [Spiking Graph Convolutional Network (SGCN) Contagion Predictor](algorithms/spiking-graph-convolutional-network-sgcn-contagion-predictor.md) | Unable to find more details | No finance study of spiking graph networks found; the CSV's arXiv 2111.05678 could not be identified. |
| RK259 | [Hawkes-Driven Non-Parametric Order Flow Toxicity Filter](algorithms/hawkes-driven-non-parametric-order-flow-toxicity-filter.md) | Needs more info | No study found; the CSV's reference, arXiv 2002.09876, could not be identified. |
| RK261 | [Koopman Operator Model Predictive Control Risk Mitigation](algorithms/koopman-operator-model-predictive-control-risk-mitigation.md) | Unable to find more details | No peer-reviewed out-of-sample study of Koopman/MPC trading found; the CSV's reference, arXiv 2004.05678, is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK262 | [Persistent Homology Betti-0 Connected Component Contagion Detector](algorithms/persistent-homology-betti-0-connected-component-contagion-detector.md) | Unable to find more details | No study of Betti-0 contagion detection beyond what average-correlation and absorption-ratio measures already capture. |
| RK263 | [Topological Persistence Diagram Clustering Crisis Detector](algorithms/topological-persistence-diagram-clustering-crisis-detector.md) | Unable to find more details | No study of clustering persistence diagrams for crisis detection found. |
| RK264 | [Information-Theoretic Directed GNN Contagion Model](algorithms/information-theoretic-directed-gnn-contagion-model.md) | Unable to find more details | No study combining transfer-entropy graphs with graph neural networks for contagion found. |
| RK265 | [Persistent Homology Betti-2 3D Void Macro Stress Predictor](algorithms/persistent-homology-betti-2-3d-void-macro-stress-predictor.md) | Unable to find more details | No study using Betti-2 features for macro stress prediction found. |
| RK266 | [Riemannian Manifold Metric Entropic Risk Portfolio](algorithms/riemannian-manifold-metric-entropic-risk-portfolio.md) | Unable to find more details | No study applying Riemannian SPD-manifold optimisation to portfolio construction found; the CSV's arXiv 2106.09876 is a general graph anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance one. |
| RK267 | [Graph Attention Network Covariance Matrix Spectral Regularization](algorithms/graph-attention-network-covariance-matrix-spectral-regularization.md) | Needs more info | GNN covariance estimators appear only in an arXiv comparison (2604.24486) and a 2026 Politecnico di Torino thesis, neither read; the CSV's arXiv 2103.01234 is a black-hole physics paper ("Hidden Symmetry of Vanishing Love"), unrelated to trading. |
| RK270 | [Quantum Annealing Binary Matrix Factorization Portfolio Risk Model](algorithms/quantum-annealing-binary-matrix-factorization-portfolio-risk-model.md) | Unable to find more details | No finance study of annealer-based binary matrix factorisation found; the CSV's arXiv 2103.01234 is a black-hole physics paper ("Hidden Symmetry of Vanishing Love"), unrelated to trading. |
| RK272 | [Wavelet-Neural Network Hybrid Intraday Trend Scalper](algorithms/wavelet-neural-network-hybrid-intraday-trend-scalper.md) | Unable to find more details | No causal (trailing-window), cost-inclusive test of a wavelet-plus-neural-network trading strategy found. |
| RK273 | [Deep Koopman-Inspired Spectral Asset Allocation](algorithms/deep-koopman-inspired-spectral-asset-allocation.md) | Unable to find more details | No peer-reviewed out-of-sample study of Koopman/MPC trading found; the CSV's reference, arXiv 2004.05678, is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK280 | [Recurrent Neural Hawkes Point Process Toxic Flow Hedging Trigger](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-hedging-trigger.md) | Unable to find more details | No finance study found; the CSV's reference, arXiv 2104.09876, is a heat-pump health-monitoring paper, unrelated to trading. |
| RK283 | [Wasserstein Distributionally Robust Neural Stochastic Control Hedging](algorithms/wasserstein-distributionally-robust-neural-stochastic-control-hedging.md) | Unable to find more details | No study of Wasserstein-robust deep hedging found; the CSV's reference, arXiv 2009.08295, is Morrill et al.'s neural rough differential equations paper, a general time-series method. |
| RK286 | [Iron Butterfly Credit Strategy](algorithms/iron-butterfly-credit-strategy.md) | Needs more info | Performance statistics for Cboe's BFLY iron-butterfly index (or any study of the strategy) were not found. |
| RK287 | [Neural Operator Delay Differential Equation (Delay-ODE) Term Structure Predictor](algorithms/neural-operator-delay-differential-equation-delay-ode-term-structure-predictor.md) | Unable to find more details | No term-structure study using neural delay-differential operators found; the CSV's arXiv 2106.09876 is a general graph anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance one. |
| RK288 | [Neural Controlled Differential Equation (Neural CDE) Point Process Execution](algorithms/neural-controlled-differential-equation-neural-cde-point-process-execution.md) | Unable to find more details | No study applying neural controlled differential equations to order execution found. |
| RK289 | [Neural Operator Delay-Differential Hawkes Microstructure Predictor](algorithms/neural-operator-delay-differential-hawkes-microstructure-predictor.md) | Unable to find more details | No study combining neural operators with delay-differential Hawkes processes for microstructure found. |
| RK297 | [Fractional Hurst-Driven Adaptive Bandwidth Mean Reversion](algorithms/fractional-hurst-driven-adaptive-bandwidth-mean-reversion.md) | Unable to find more details | No study of Hurst-adaptive band widths found. |
| RK304 | [Recurrent Neural Hawkes Point Process Volatility Jump Forecaster](algorithms/recurrent-neural-hawkes-point-process-volatility-jump-forecaster.md) | Unable to find more details | No study applying neural Hawkes processes to volatility jumps found; the CSV's arXiv 2104.09876 is a heat-pump health-monitoring paper, unrelated to trading. |
| RK307 | [Cross-Exchange Market Making (XEMM)](algorithms/cross-exchange-market-making-xemm.md) | Unable to find more details | No performance study of cross-exchange market making found; only the Hummingbot documentation. |
| RK315 | [Empirical Mode Decomposition (EMD) Hilbert-Huang Intraday Scalper](algorithms/empirical-mode-decomposition-emd-hilbert-huang-intraday-scalper.md) | Unable to find more details | No out-of-sample test of an EMD or Hilbert-Huang trading rule found; studies use EMD for denoising or as ML features. |
| RK320 | [Koopman Operator Non-Linear Volatility Surface Interpolator](algorithms/koopman-operator-non-linear-volatility-surface-interpolator.md) | Unable to find more details | No volatility-surface application of Koopman operators found; the CSV's arXiv 2004.05678 is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK321 | [Koopman Operator Non-Linear Volatility Surface Pricing Model](algorithms/koopman-operator-non-linear-volatility-surface-pricing-model.md) | Unable to find more details | No volatility-surface application of Koopman operators found; the CSV's arXiv 2004.05678 is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK323 | [Physics-Informed Neural Operator (FNO) Yield Curve Dynamics](algorithms/physics-informed-neural-operator-fno-yield-curve-dynamics.md) | Unable to find more details | No yield-curve application of neural operators found. |
| RK325 | [Neural Operator Controlled Portfolio Dynamic Hedging](algorithms/neural-operator-controlled-portfolio-dynamic-hedging.md) | Unable to find more details | No hedging application of neural operators found. |
| RK326 | [Neural Operator Functional Gradient Boosting Cross-Sectional Alpha](algorithms/neural-operator-functional-gradient-boosting-cross-sectional-alpha.md) | Unable to find more details | No cross-sectional alpha study using neural operators found. |
| RK330 | [Neural Rough Path Signature Delay-Differential Portfolio Control](algorithms/neural-rough-path-signature-delay-differential-portfolio-control.md) | Unable to find more details | No study of signature-driven delay-differential portfolio control found. |
| RK331 | [Neural Rough Differential Equation (Neural RDE) LOB Forecaster](algorithms/neural-rough-differential-equation-neural-rde-lob-forecaster.md) | Needs more info | No neural-RDE order-book study found; the CSV's arXiv 2005.08320 could not be identified. |
| RK332 | [Generative Score-Based Flow Matching Order Flow Generator](algorithms/generative-score-based-flow-matching-order-flow-generator.md) | Unable to find more details | No order-flow application of flow matching found. |
| RK333 | [Neural Jump-Diffusion Hawkes Point Process Shock Detector](algorithms/neural-jump-diffusion-hawkes-point-process-shock-detector.md) | Unable to find more details | No market application of neural jump SDEs found; the CSV's arXiv 2104.09876 is a heat-pump health-monitoring paper, unrelated to trading. |
| RK334 | [Neural Controlled Differential Equation LOB Trend Anticipator](algorithms/neural-controlled-differential-equation-lob-trend-anticipator.md) | Unable to find more details | No order-book study using neural controlled differential equations found. |
| RK335 | [Wasserstein Distributionally Robust RL Market Making](algorithms/wasserstein-distributionally-robust-rl-market-making.md) | Unable to find more details | No Wasserstein-robust RL market-making study found; the CSV's arXiv 2110.09876 is a particle-physics review ("Light Sterile Neutrinos"), unrelated to trading. |
| RK337 | [Neural Controlled Jump Diffusion Order Book Pricing Model](algorithms/neural-controlled-jump-diffusion-order-book-pricing-model.md) | Unable to find more details | No order-book study using neural controlled differential equations found. |
| RK338 | [Recurrent Neural Hawkes Point Process Liquidity Shock Detector](algorithms/recurrent-neural-hawkes-point-process-liquidity-shock-detector.md) | Unable to find more details | No study applying neural Hawkes processes to liquidity shocks found; the CSV's arXiv 2104.09876 is a heat-pump health-monitoring paper, unrelated to trading. |
| RK339 | [Multi-Agent Reinforcement Learning Nash Market Maker](algorithms/multi-agent-reinforcement-learning-nash-market-maker.md) | Unable to find more details | No performance study of Nash-equilibrium multi-agent market makers found. |
| RK340 | [Fractional Order Cointegration Vector Error Correction Neural Network](algorithms/fractional-order-cointegration-vector-error-correction-neural-network.md) | Unable to find more details | No study of a neural fractionally cointegrated VECM found (as RK239); the CSV's arXiv 1809.02345 could not be identified. |
| RK341 | [Multi-Agent Reinforcement Learning Stackelberg Market Maker](algorithms/multi-agent-reinforcement-learning-stackelberg-market-maker.md) | Unable to find more details | No market-making performance study using Stackelberg multi-agent RL found. |
| RK342 | [Neural Rough Path Signature Hawkes Point Process Forecaster](algorithms/neural-rough-path-signature-hawkes-point-process-forecaster.md) | Unable to find more details | No study combining path signatures with Hawkes intensity forecasting found; the CSV's arXiv 2102.05678 is an astrophysics paper on supernova dust laws, unrelated to trading. |
| RK344 | [Multi-Agent Reinforcement Learning Stackelberg Market Maker Equilibrium](algorithms/multi-agent-reinforcement-learning-stackelberg-market-maker-equilibrium.md) | Unable to find more details | No market-making performance study using Stackelberg multi-agent RL found. |
| RK345 | [Multi-Agent Reinforcement Learning Stackelberg Spread Capture](algorithms/multi-agent-reinforcement-learning-stackelberg-spread-capture.md) | Unable to find more details | No market-making performance study using Stackelberg multi-agent RL found. |
| RK348 | [Phase Space Reconstructed Neural ODE (PSR-NODE)](algorithms/phase-space-reconstructed-neural-ode-psr-node.md) | Needs more info | No finance study of phase-space-reconstructed neural ODEs found; the CSV's NeurIPS proceedings reference (doi 10.5555/3540261.3546083) could not be identified. |
| RK350 | [Physics-Informed Deep Learning Schrödinger Volatility Solver](algorithms/physics-informed-deep-learning-schrodinger-volatility-solver.md) | Unable to find more details | No study modelling volatility with the Schrödinger equation found. |
| RK353 | [Recurrent Neural Hawkes Point Process Execution Timing](algorithms/recurrent-neural-hawkes-point-process-execution-timing.md) | Unable to find more details | No execution study using neural Hawkes processes found; the CSV's arXiv 2104.09876 is a heat-pump health-monitoring paper, unrelated to trading. |
| RK354 | [Multi-Agent Reinforcement Learning Evolutionary Market Maker](algorithms/multi-agent-reinforcement-learning-evolutionary-market-maker.md) | Unable to find more details | No study of evolutionary multi-agent market makers found. |
| RK355 | [Recurrent Neural Hawkes Point Process Toxic Flow Execution](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-execution.md) | Unable to find more details | No execution study using neural Hawkes processes found; the CSV's arXiv 2104.09876 is a heat-pump health-monitoring paper, unrelated to trading. |
| RK356 | [Recurrent Neural Hawkes Point Process Dynamic Inventory Market Maker](algorithms/recurrent-neural-hawkes-point-process-dynamic-inventory-market-maker.md) | Unable to find more details | No market-making study using neural Hawkes order-flow forecasts found; the CSV's arXiv 2104.09876 is a heat-pump health-monitoring paper, unrelated to trading. |
| RK357 | [Recurrent Neural Hawkes Point Process Toxic Flow Execution Pauser](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-execution-pauser.md) | Unable to find more details | No execution study using neural Hawkes processes found; the CSV's arXiv 2104.09876 is a heat-pump health-monitoring paper, unrelated to trading. |
| RK358 | [Multi-Agent Reinforcement Learning Evolutionary Execution Routing](algorithms/multi-agent-reinforcement-learning-evolutionary-execution-routing.md) | Unable to find more details | No study of evolutionary multi-agent RL execution found. |
| RK359 | [Multi-Agent Reinforcement Learning Evolutionary Market Making Equilibrium](algorithms/multi-agent-reinforcement-learning-evolutionary-market-making-equilibrium.md) | Unable to find more details | No study of evolutionary multi-agent market makers found. |
| RK360 | [Multi-Agent Reinforcement Learning Evolutionary Execution Allocator](algorithms/multi-agent-reinforcement-learning-evolutionary-execution-allocator.md) | Unable to find more details | No study of evolutionary multi-agent RL execution found. |
| RK362 | [Koopman Operator Model Predictive Control Execution](algorithms/koopman-operator-model-predictive-control-execution.md) | Unable to find more details | No study of Koopman-operator MPC execution found; the CSV's arXiv 2004.05678 is a mathematical-physics paper ("Stable polynomials and crystalline measures"), unrelated to trading. |
| RK365 | [POV / Percent-of-Volume Execution](algorithms/pov-percent-of-volume-execution.md) | Unable to find more details | No academic performance study of percent-of-volume execution found; it appears in practitioner and BIS descriptions only. |
| RK369 | [Multi-Agent Mean-Field Game Optimal Execution Routing](algorithms/multi-agent-mean-field-game-optimal-execution-routing.md) | Unable to find more details | No study applying mean-field games to order routing found; the CSV's arXiv 2005.02345 could not be identified. |
| RK370 | [Wasserstein Distributionally Robust Optimal Execution Trajectory](algorithms/wasserstein-distributionally-robust-optimal-execution-trajectory.md) | Unable to find more details | No Wasserstein distributionally robust execution study found; the CSV's arXiv 1908.01234 is a biomedical-engineering paper on an electromagnetic bioreactor, unrelated to trading. |
| RK371 | [Wasserstein Distributionally Robust Hawkes Point Process Execution](algorithms/wasserstein-distributionally-robust-hawkes-point-process-execution.md) | Unable to find more details | No Wasserstein distributionally robust execution study found; the CSV's arXiv 1908.01234 is a biomedical-engineering paper on an electromagnetic bioreactor, unrelated to trading. |
| RK374 | [Physics-Informed Neural Network (PINN) Burgers Volatility Model](algorithms/physics-informed-neural-network-pinn-burgers-volatility-model.md) | Unable to find more details | No study modelling volatility with the Burgers equation found. |
| RK375 | [Quantum Support Vector Regression (QSVR) Return Predictor](algorithms/quantum-support-vector-regression-qsvr-return-predictor.md) | Unable to find more details | No study showing quantum support vector regression predicting returns found. |
| RK376 | [Deep Koopman Operator Market Dynamics Predictor](algorithms/deep-koopman-operator-market-dynamics-predictor.md) | Needs more info | No peer-reviewed market-forecasting study using deep Koopman models found; the CSV's arXiv 2102.12086 could not be identified. |
| RK380 | [Dynamic Latent Factor Graph Neural Network (FactorGNN)](algorithms/dynamic-latent-factor-graph-neural-network-factorgnn.md) | Unable to find more details | No paper describing a FactorGNN for stocks found (nearest: FactorVAE); the CSV's arXiv 2206.01234 could not be identified. |
| RK382 | [Contractive Autoencoder Latent Factor Anomaly Detection](algorithms/contractive-autoencoder-latent-factor-anomaly-detection.md) | Needs more info | No finance study using contractive autoencoders found; the CSV's arXiv 1105.3911 could not be identified. |
| RK384 | [Geometric Deep Learning Non-Euclidean Alpha Predictor](algorithms/geometric-deep-learning-non-euclidean-alpha-predictor.md) | Unable to find more details | Beyond HyperStockGAT (RK381), no non-Euclidean alpha study found; the CSV's arXiv 2106.09876 is a general graph anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance one. |
| RK386 | [Information-Theoretic Transfer Entropy Graph Neural Network Alpha Model](algorithms/information-theoretic-transfer-entropy-graph-neural-network-alpha-model.md) | Unable to find more details | No study using transfer-entropy graphs in a graph neural network for alpha found. |
| RK387 | [Quantum Kernel-Based SVM Cross-Sectional Alpha Predictor](algorithms/quantum-kernel-based-svm-cross-sectional-alpha-predictor.md) | Unable to find more details | No cross-sectional alpha study using quantum-kernel SVMs found. |
| RK388 | [Dynamic Copula-Quantile Regression Neural Network Alpha Model](algorithms/dynamic-copula-quantile-regression-neural-network-alpha-model.md) | Unable to find more details | No study combining quantile neural networks with a dynamic copula for alpha found; the CSV's arXiv 2001.05432 could not be identified. |
| RK389 | [Quantum Annealing Entropic Value-at-Risk Portfolio Optimization](algorithms/quantum-annealing-entropic-value-at-risk-portfolio-optimization.md) | Unable to find more details | No quantum-annealing EVaR study found; the CSV's arXiv 2103.01234 is a black-hole physics paper ("Hidden Symmetry of Vanishing Love"), unrelated to trading. |
| RK390 | [Neural Operator Flow-Matching Cross-Sectional Alpha Forecaster](algorithms/neural-operator-flow-matching-cross-sectional-alpha-forecaster.md) | Unable to find more details | No study combining neural operators and flow matching for return forecasting found. |
| RK392 | [Fractional Order Vector AutoRegressive (VAR) Macro Allocator](algorithms/fractional-order-vector-autoregressive-var-macro-allocator.md) | Unable to find more details | No allocation study using a fractional VAR found; the CSV's arXiv 1809.02345 could not be identified. |
| RK393 | [Quantum Neural Network (QNN) Volatility Surface Forecaster](algorithms/quantum-neural-network-qnn-volatility-surface-forecaster.md) | Unable to find more details | No volatility-surface study using quantum neural networks found; the CSV's arXiv 2103.01234 is a black-hole physics paper ("Hidden Symmetry of Vanishing Love"), unrelated to trading. |
| RK394 | [Graph Diffusion Convolutional Network Cross-Sectional Alpha](algorithms/graph-diffusion-convolutional-network-cross-sectional-alpha.md) | Unable to find more details | No stock-return study using diffusion convolutional networks found; the CSV's arXiv 2103.01234 is a black-hole physics paper ("Hidden Symmetry of Vanishing Love"), unrelated to trading. |
| RK396 | [Riemannian Manifold Metric Graph Diffusion Covariance Estimator](algorithms/riemannian-manifold-metric-graph-diffusion-covariance-estimator.md) | Unable to find more details | No study of this combination found. |
| RK397 | [Quantum Annealing Graph Neural Network Covariance Shrinkage](algorithms/quantum-annealing-graph-neural-network-covariance-shrinkage.md) | Unable to find more details | No study of this combination found. |
| RK398 | [Persistent Homology Betti-2 Persistence Landscape Macro Contagion](algorithms/persistent-homology-betti-2-persistence-landscape-macro-contagion.md) | Unable to find more details | No study using Betti-2 persistence landscapes for contagion found; the CSV's arXiv 2004.01234 could not be identified. |
| RK400 | [Graph Attention Network Riemannian Manifold Covariance Shrinkage](algorithms/graph-attention-network-riemannian-manifold-covariance-shrinkage.md) | Needs more info | No study of this combination found; the GNN covariance leads (arXiv 2604.24486 and a 2026 Politecnico di Torino thesis) were not read. |

### The list

<!-- BEGIN ranked list: generated by tools/build_algorithm_ledger.py -->

*Generated from `docs/algorithms/source/trading_algorithms_ranked_2026-10-27.csv.xz` and `docs/algorithms/implementation_status.csv` by `python tools/build_algorithm_ledger.py`. Edit those two files, not this block.*

| Rows | Algorithms | Yes | Research code | Partial | No |
|---|---|---|---|---|---|
| Specific (ranks 1–425) | 425 | 13 | 49 | 41 | 322 |
| Title-reconstructed (ranks 426–14,225) | 13,800 | 0 | 0 | 0 | 13,800 |
| All | 14,225 | 13 | 49 | 41 | 14,122 |

#### Specific algorithms

| Rank | Algorithm | Family | AI | Retail | Implemented | Ledger | Documentation |
|---|---|---|---|---|---|---|---|
| 1 | Time-Series Momentum (TSMOM) | Trend / momentum | 10 | 28 | Research code | RK1, X7, X3 | [**researched**](algorithms/time-series-momentum-tsmom.md) |
| 2 | Volatility-Scaled Trend Following | Trend / risk scaling | 26 | 6 | Research code | RK2, S2, X7, S4 | [**researched**](algorithms/volatility-scaled-trend-following.md) |
| 3 | Dual Momentum (Absolute + Relative) | Trend / allocation | 24 | 2 | Yes | RK3, X3 | [**researched**](algorithms/dual-momentum-absolute-relative.md) |
| 4 | Cross-Asset Carry Composite | Macro / carry | 68 | 131 | No | RK4 | [**researched**](algorithms/cross-asset-carry-composite.md) |
| 5 | Value-Momentum Composite | Equity factor / multi-factor | 57 | 8 | No | RK5 | [**researched**](algorithms/value-momentum-composite.md) |
| 6 | 12–1 Momentum (Skip-Month) | Trend / momentum | 19 | 11 | No | RK6 | [**researched**](algorithms/12-1-momentum-skip-month.md) |
| 7 | Cross-Sectional Momentum | Trend / momentum | 81 | 51 | Partial | RK7, X3 | [**researched**](algorithms/cross-sectional-momentum.md) |
| 8 | Commodity Momentum + Term Structure | Trend / carry | 25 | 14 | No | RK8 | [**researched**](algorithms/commodity-momentum-term-structure.md) |
| 9 | Fama–French Five-Factor Model Portfolio | Factor / systematic equity | 88 | 252 | No | RK9 | [**researched**](algorithms/fama-french-five-factor-model-portfolio.md) |
| 10 | State-Filtered Momentum | Factor / regime-aware | 35 | 17 | Partial | RK10 | [**researched**](algorithms/state-filtered-momentum.md) |
| 11 | Quality Minus Junk (QMJ) | Equity factor / quality | 234 | 301 | No | RK11 | [**researched**](algorithms/quality-minus-junk-qmj.md) |
| 12 | Quality / Profitability Factor | Factor / systematic equity | 110 | 245 | No | RK12 | [**researched**](algorithms/quality-profitability-factor.md) |
| 13 | Gross Profitability Factor | Equity factor / fundamental | 167 | 106 | No | RK13 | [**researched**](algorithms/gross-profitability-factor.md) |
| 14 | 52-Week High Momentum | Cross-sectional momentum | 15 | 5 | Partial | RK14 | [**researched**](algorithms/52-week-high-momentum.md) |
| 15 | Conservative Investment Factor | Equity factor / fundamental | 73 | 7 | No | RK15 | [**researched**](algorithms/conservative-investment-factor.md) |
| 16 | Residual Momentum | Factor / systematic equity | 34 | 29 | No | RK16 | [**researched**](algorithms/residual-momentum.md) |
| 17 | 10-Month Moving-Average Risk Filter | Trend / risk filter | 27 | 15 | Yes | RK17, V16, C-E2 | [**researched**](algorithms/10-month-moving-average-risk-filter.md) |
| 18 | Low-Volatility Equity | Factor / systematic equity | 13 | 35 | Partial | RK18, X2 | [**researched**](algorithms/low-volatility-equity.md) |
| 19 | Sector Momentum Rotation | Trend / allocation | 23 | 1 | Partial | RK19, X3 | [**researched**](algorithms/sector-momentum-rotation.md) |
| 20 | Bond Duration Momentum | Fixed income / trend | 69 | 84 | No | RK20 | [**researched**](algorithms/bond-duration-momentum.md) |
| 21 | VIX-Regime Conditional Equity Exposure | Regime / volatility | 196 | 100 | Yes | RK21, V12 | [**researched**](algorithms/vix-regime-conditional-equity-exposure.md) |
| 22 | Volatility Targeting / Risk Scaling | Risk management | 137 | 123 | Yes | RK22, S4, V18, S3 | [**researched**](algorithms/volatility-targeting-risk-scaling.md) |
| 23 | Drawdown-Aware De-Risking Governor | Risk management | 138 | 126 | Yes | RK23, V11 | [**researched**](algorithms/drawdown-aware-de-risking-governor.md) |
| 24 | ETF NAV / Creation-Redemption Arbitrage | Index / ETF relative value | 206 | 182 | Research code | RK24, C-RJ6 | [**researched**](algorithms/etf-nav-creation-redemption-arbitrage.md) |
| 25 | Index Futures vs Cash Basis Arbitrage | Index arbitrage / basis | 141 | 2759 | No | RK25 | [**researched**](algorithms/index-futures-vs-cash-basis-arbitrage.md) |
| 26 | Futures Cash-and-Carry Basis Trading | Basis / carry | 95 | 163 | Partial | RK26 | [**researched**](algorithms/futures-cash-and-carry-basis-trading.md) |
| 27 | Shareholder Yield Factor | Equity factor / capital return | 75 | 58 | No | RK27 | [**researched**](algorithms/shareholder-yield-factor.md) |
| 28 | Fixed-Income Carry and Roll-Down | Fixed income / relative value | 168 | 30 | No | RK28 | [**researched**](algorithms/fixed-income-carry-and-roll-down.md) |
| 29 | Price + Earnings Momentum | Factor / event-driven | 112 | 20 | No | RK29 | [**researched**](algorithms/price-earnings-momentum.md) |
| 30 | FX Carry Trade | Carry / macro | 38 | 101 | No | RK30 | [**researched**](algorithms/fx-carry-trade.md) |
| 31 | Intangibles-Adjusted Value and Profitability Factor | Equity factor / fundamental valuation / intangible capital | 46 | 60 | No | RK31 | [**researched**](algorithms/intangibles-adjusted-value-and-profitability-factor.md) |
| 32 | Commodity Futures Roll Yield | Carry / macro | 67 | 120 | No | RK32 | [**researched**](algorithms/commodity-futures-roll-yield.md) |
| 33 | Market-Neutral Residual Mean Reversion | Statistical arbitrage | 53 | 129 | Research code | RK33, C-MR2 | [**researched**](algorithms/market-neutral-residual-mean-reversion.md) |
| 34 | Futures Calendar-Spread Mean Reversion | Relative value / futures | 54 | 83 | No | RK34 | [**researched**](algorithms/futures-calendar-spread-mean-reversion.md) |
| 35 | Net Stock Issuance Anomaly | Equity factor / corporate actions / issuance anomaly | 22 | 68 | No | RK35 | [**researched**](algorithms/net-stock-issuance-anomaly.md) |
| 36 | Johansen Cointegration Basket Trading | Statistical arbitrage | 203 | 266 | No | RK36 | [**researched**](algorithms/johansen-cointegration-basket-trading.md) |
| 37 | Cointegration-Based Pairs Trading | Statistical arbitrage | 191 | 262 | Research code | RK37, Q2 | [**researched**](algorithms/cointegration-based-pairs-trading.md) |
| 38 | Chandelier Exit Trend Following | Trend / risk management | 50 | 55 | Partial | RK38, V10, Q8 | [**researched**](algorithms/chandelier-exit-trend-following.md) |
| 39 | Merger Arbitrage | Event-driven / relative value | 140 | 235 | No | RK39 | [**researched**](algorithms/merger-arbitrage.md) |
| 40 | Earnings Estimate Revision Momentum | Fundamental / event momentum | 74 | 21 | No | RK40 | [**researched**](algorithms/earnings-estimate-revision-momentum.md) |
| 41 | Inflation-Regime Asset Rotation | Macro / tactical allocation | 144 | 37 | No | RK41 | [**researched**](algorithms/inflation-regime-asset-rotation.md) |
| 42 | Cross-Asset Commodity Futures Term-Structure Carry & Roll Yield | Macro / Commodity carry | 160 | 139 | No | RK42 | [**researched**](algorithms/cross-asset-commodity-futures-term-structure-carry-roll-yield.md) |
| 43 | Donchian / Turtle Channel Breakout | Trend / breakout | 107 | 261 | Research code | RK43, C-G5 | [**researched**](algorithms/donchian-turtle-channel-breakout.md) |
| 44 | Supertrend ATR-Band Trend Following | Trend / technical | 49 | 4 | No | RK44 | [**researched**](algorithms/supertrend-atr-band-trend-following.md) |
| 45 | Post-Earnings Announcement Drift (PEAD) | Event-driven / earnings | 5 | 18 | No | RK45, V6 | [**researched**](algorithms/post-earnings-announcement-drift-pead.md) |
| 46 | MACD Signal-Line Crossover | Trend / momentum | 80 | 10 | Yes | RK46, Q1 | [**researched**](algorithms/macd-signal-line-crossover.md) |
| 47 | Public Activist-Filing Event Strategy | Event-driven / public regulatory filings / shareholder activism | 62 | 90 | No | RK47 | [**researched**](algorithms/public-activist-filing-event-strategy.md) |
| 48 | Book-to-Market Value | Factor / systematic equity | 109 | 158 | No | RK48 | [**researched**](algorithms/book-to-market-value.md) |
| 49 | Betting Against Beta (BAB) | Factor / systematic equity | 90 | 233 | No | RK49 | [**researched**](algorithms/betting-against-beta-bab.md) |
| 50 | Accrual Anomaly | Factor / systematic equity | 135 | 180 | No | RK50 | [**researched**](algorithms/accrual-anomaly.md) |
| 51 | Asset-Growth Anomaly | Factor / systematic equity | 165 | 159 | No | RK51 | [**researched**](algorithms/asset-growth-anomaly.md) |
| 52 | Dividend Yield / Dividend Growth | Factor / systematic equity | 136 | 52 | Partial | RK52 | [**researched**](algorithms/dividend-yield-dividend-growth.md) |
| 53 | CVaR / Expected-Shortfall Optimization | Portfolio construction | 202 | 162 | No | RK53 | [**researched**](algorithms/cvar-expected-shortfall-optimization.md) |
| 54 | Volatility-Managed Factor Portfolio | Equity factor / risk management | 61 | 31 | Partial | RK54, S4 | [**researched**](algorithms/volatility-managed-factor-portfolio.md) |
| 55 | ADX-Filtered Trend Following | Trend / breakout | 20 | 12 | Partial | RK55, V15 | [**researched**](algorithms/adx-filtered-trend-following.md) |
| 56 | Hierarchical Risk Parity (HRP) | Portfolio construction | 3 | 36 | Yes | RK56, A5, Q13 | [**researched**](algorithms/hierarchical-risk-parity-hrp.md) |
| 57 | Low P/E Value Screen | Factor / systematic equity | 72 | 244 | No | RK57 | [**researched**](algorithms/low-p-e-value-screen.md) |
| 58 | Small-Cap Size Premium | Factor / systematic equity | 89 | 81 | No | RK58 | [**researched**](algorithms/small-cap-size-premium.md) |
| 59 | Liquidity Factor | Factor / systematic equity | 2 | 82 | Partial | RK59 | [**researched**](algorithms/liquidity-factor.md) |
| 60 | Global Minimum-Variance Portfolio | Portfolio construction | 44 | 69 | Research code | RK60, Q13 | [**researched**](algorithms/global-minimum-variance-portfolio.md) |
| 61 | Risk Parity / Equal Risk Contribution | Portfolio construction | 45 | 122 | Partial | RK61, A5 | [**researched**](algorithms/risk-parity-equal-risk-contribution.md) |
| 62 | Dual Moving Average Crossover | Trend / momentum | 9 | 27 | Research code | RK62, Q1, C-E2 | [**researched**](algorithms/dual-moving-average-crossover.md) |
| 63 | Black–Litterman Allocation | Portfolio construction | 43 | 67 | No | RK63 | [**researched**](algorithms/black-litterman-allocation.md) |
| 64 | Triple EMA / Moving-Average Ribbon | Trend / momentum | 66 | 9 | Partial | RK64, V15 | [**researched**](algorithms/triple-ema-moving-average-ribbon.md) |
| 65 | Cross-Sectional Factor Momentum Rotation | Factor investing / cross-sectional momentum / allocation | 31 | 125 | No | RK65 | [**researched**](algorithms/cross-sectional-factor-momentum-rotation.md) |
| 66 | Maximum-Diversification Portfolio | Portfolio optimization | 60 | 42 | No | RK66 | [**researched**](algorithms/maximum-diversification-portfolio.md) |
| 67 | ATR-Based Position Sizing | Position sizing | 48 | 124 | Research code | RK67, C-G5 | [**researched**](algorithms/atr-based-position-sizing.md) |
| 68 | Dual Thrust Breakout | Trend / breakout | 82 | 217 | Research code | RK68, Q7, N1 | [**researched**](algorithms/dual-thrust-breakout.md) |
| 69 | London Session Breakout | Trend / breakout | 132 | 219 | Research code | RK69, Q4, N2, N3 | [**researched**](algorithms/london-session-breakout.md) |
| 70 | Parabolic SAR Trend / Stop | Trend / breakout | 83 | 13 | Yes | RK70, Q8 | [**researched**](algorithms/parabolic-sar-trend-stop.md) |
| 71 | Heikin-Ashi Trend Filter | Trend / breakout | 84 | 3 | Yes | RK71, Q3 | [**researched**](algorithms/heikin-ashi-trend-filter.md) |
| 72 | Distance-Based Pairs Trading | Statistical arbitrage | 134 | 220 | No | RK72 | [**researched**](algorithms/distance-based-pairs-trading.md) |
| 73 | Kalman-Filter Dynamic-Hedge Pairs | Statistical arbitrage | 192 | 263 | Research code | RK73, Q2 | [**researched**](algorithms/kalman-filter-dynamic-hedge-pairs.md) |
| 74 | Copula-Based Pairs Trading | Statistical arbitrage | 193 | 427 | No | RK74 | [**researched**](algorithms/copula-based-pairs-trading.md) |
| 75 | Ornstein–Uhlenbeck Spread Trading | Statistical arbitrage | 32 | 117 | Research code | RK75, C-MR2, C-MR4 | [**researched**](algorithms/ornstein-uhlenbeck-spread-trading.md) |
| 76 | PCA Residual Statistical Arbitrage | Statistical arbitrage | 194 | 264 | Partial | RK76, C-MR2 | [**researched**](algorithms/pca-residual-statistical-arbitrage.md) |
| 77 | ATR Volatility-Expansion Breakout | Trend / volatility breakout | 14 | 91 | No | RK77, N1, N5 | [**researched**](algorithms/atr-volatility-expansion-breakout.md) |
| 78 | Multi-Timeframe Trend Agreement | Trend / signal confirmation | 16 | 181 | No | RK78 | [**researched**](algorithms/multi-timeframe-trend-agreement.md) |
| 79 | Opening Gap Continuation | Intraday momentum / event | 94 | 56 | Partial | RK79, N3, X1 | [**researched**](algorithms/opening-gap-continuation.md) |
| 80 | Convertible Bond Arbitrage | Capital structure / relative value | 204 | 281 | No | RK80 | [**researched**](algorithms/convertible-bond-arbitrage.md) |
| 81 | Capital Structure Arbitrage | Relative value / credit-equity | 205 | 130 | No | RK81 | [**researched**](algorithms/capital-structure-arbitrage.md) |
| 82 | Closed-End Fund Discount Reversion | Relative value / fund discounts | 4 | 57 | No | RK82 | [**researched**](algorithms/closed-end-fund-discount-reversion.md) |
| 83 | Triangular FX Arbitrage | Cross-market arbitrage | 55 | 94 | Research code | RK83, A7 | [**researched**](algorithms/triangular-fx-arbitrage.md) |
| 84 | Crypto Perpetual Funding-Rate Capture | Crypto derivatives / carry | 225 | 7420 | Research code | RK84, C-RJ2 | [**researched**](algorithms/crypto-perpetual-funding-rate-capture.md) |
| 85 | Spot-Perpetual Basis Arbitrage | Crypto / basis | 56 | 132 | Partial | RK85, C-RJ2 | [**researched**](algorithms/spot-perpetual-basis-arbitrage.md) |
| 86 | Yield Curve Steepener / Flattener | Fixed income / macro relative value | 235 | 236 | No | RK86 | [**researched**](algorithms/yield-curve-steepener-flattener.md) |
| 87 | Option Dispersion Trading | Options volatility relative value | 98 | 257 | No | RK87 | [**researched**](algorithms/option-dispersion-trading.md) |
| 88 | Distributionally Robust CVaR Allocation | Portfolio optimization / tail risk | 211 | 59 | No | RK88 | [**researched**](algorithms/distributionally-robust-cvar-allocation.md) |
| 89 | Autoencoder Latent-Factor Statistical Arbitrage | ML / statistical arbitrage | 254 | 226 | No | RK89 | [**researched**](algorithms/autoencoder-latent-factor-statistical-arbitrage.md) |
| 90 | Long-Term Industry Reversal with Valuation Confirmation | Industry / sector rotation / long-horizon contrarian | 39 | 50 | No | RK90 | [**researched**](algorithms/long-term-industry-reversal-with-valuation-confirmation.md) |
| 91 | iNAV Dislocation ETF Arbitrage | Relative value / ETF arbitrage | 262 | 2827 | Partial | RK91, C-RJ6 | [**researched**](algorithms/inav-dislocation-etf-arbitrage.md) |
| 92 | FED OTC Liquidity Sweep & Reverse Repo Arbitrage | Macro / Fixed Income relative value | 170 | 227 | No | RK92 | [**researched**](algorithms/fed-otc-liquidity-sweep-reverse-repo-arbitrage.md) |
| 93 | Cointegrated Triplet Basket Statistical Arbitrage | Statistical arbitrage / Quantitative equity | 158 | 251 | No | RK93 | [**researched**](algorithms/cointegrated-triplet-basket-statistical-arbitrage.md) |
| 94 | Dynamic Copula-GARCH Multivariate Pair Trading | Statistical arbitrage / Econometrics | 291 | 9358 | No | RK94 | [**researched**](algorithms/dynamic-copula-garch-multivariate-pair-trading.md) |
| 95 | Asymmetric Tail-Risk Parity Allocation | Portfolio construction / Risk parity | 8 | 141 | No | RK95 | [**researched**](algorithms/asymmetric-tail-risk-parity-allocation.md) |
| 96 | Principal Component Analysis (PCA) Eigenportfolios Statistical Arbitrage | Statistical arbitrage / Factor modeling | 105 | 269 | Partial | RK96, C-MR2 | [**researched**](algorithms/principal-component-analysis-pca-eigenportfolios-statistical-arbitrage.md) |
| 97 | Wasserstein Distributionally Robust Statistical Arbitrage | Robust statistics / Statistical arbitrage | 278 | 960 | No | RK97 | [**researched**](algorithms/wasserstein-distributionally-robust-statistical-arbitrage.md) |
| 98 | Adversarial Domain Generalization Cross-Market Momentum | Domain adaptation / Machine learning momentum | 175 | 25 | No | RK98 | [**researched**](algorithms/adversarial-domain-generalization-cross-market-momentum.md) |
| 99 | Conformally Constrained Risk Parity Portfolio | Conformal prediction / Portfolio construction | 18 | 47 | Partial | RK99 | [**researched**](algorithms/conformally-constrained-risk-parity-portfolio.md) |
| 100 | Causal Discovery Directed Acyclic Graph (DAG) Pair Selection | Causal inference / Statistical arbitrage | 324 | 6478 | No | RK100 | [**researched**](algorithms/causal-discovery-directed-acyclic-graph-dag-pair-selection.md) |
| 101 | Dynamic Copula-EVT Tail Risk Relative Value Arbitrage | Extreme value theory / Copulas / Relative value | 355 | 10445 | No | — | [card](algorithms/dynamic-copula-evt-tail-risk-relative-value-arbitrage.md) |
| 102 | Hidden Markov Model Regime Switching | Regime / machine learning | 290 | 127 | Research code | C-R3 | [card](algorithms/hidden-markov-model-regime-switching.md) |
| 103 | Hurst-Exponent Trend / Mean-Reversion Regime Gate | Regime filter | 52 | 93 | Research code | C-MR4 | [card](algorithms/hurst-exponent-trend-mean-reversion-regime-gate.md) |
| 104 | Bayesian Online Changepoint Regime Gate | Regime detection / Bayesian | 212 | 258 | No | — | [card](algorithms/bayesian-online-changepoint-regime-gate.md) |
| 105 | Adaptive Range-Breakout with Volatility Filter | Trend / breakout | 17 | 85 | No | — | [card](algorithms/adaptive-range-breakout-with-volatility-filter.md) |
| 106 | Hierarchical Hidden Markov Model (HHMM) Regime Switcher | Probabilistic regime / Hidden Markov Model | 106 | 259 | No | — | [card](algorithms/hierarchical-hidden-markov-model-hhmm-regime-switcher.md) |
| 107 | Entropy-Based Portfolio Diversification Optimization | Information Theory / Portfolio Construction | 63 | 76 | No | — | [card](algorithms/entropy-based-portfolio-diversification-optimization.md) |
| 108 | Intraday ETF Relative-Value Arbitrage | Statistical arbitrage / intraday | 195 | 279 | Research code | A6 | [card](algorithms/intraday-etf-relative-value-arbitrage.md) |
| 109 | Sparse Graphical Lasso Cross-Asset Spillover Predictor | Graphical models / Econometrics / Risk management | 64 | 145 | No | — | [card](algorithms/sparse-graphical-lasso-cross-asset-spillover-predictor.md) |
| 110 | Opening Range Breakout (ORB) | Trend / breakout | 131 | 218 | Research code | C-M2, N2 | [card](algorithms/opening-range-breakout-orb.md) |
| 111 | Ichimoku Cloud Trend Filter | Trend / breakout | 21 | 88 | No | — | [card](algorithms/ichimoku-cloud-trend-filter.md) |
| 112 | Kaufman Adaptive Moving Average (KAMA) Trend | Adaptive trend | 51 | 92 | Partial | V15 | [card](algorithms/kaufman-adaptive-moving-average-kama-trend.md) |
| 113 | Wavelet Transform Denoised Breakout System | Signal processing / Technical trend | 255 | 7556 | No | — | [card](algorithms/wavelet-transform-denoised-breakout-system.md) |
| 114 | Volatility Risk Premium (Short Vol + Tail Hedge) | Options / volatility | 40 | 246 | Research code | S1 | [card](algorithms/volatility-risk-premium-short-vol-tail-hedge.md) |
| 115 | EMA Pullback Continuation | Trend / pullback | 1 | 234 | No | — | [card](algorithms/ema-pullback-continuation.md) |
| 116 | Markowitz Mean-Variance Optimization | Portfolio construction | 42 | 66 | Research code | Q13 | [card](algorithms/markowitz-mean-variance-optimization.md) |
| 117 | Equal-Weight Rebalancing | Portfolio construction | 59 | 22 | Partial | X5 | [card](algorithms/equal-weight-rebalancing.md) |
| 118 | Minimum-Correlation Portfolio | Portfolio optimization | 6 | 43 | No | — | [card](algorithms/minimum-correlation-portfolio.md) |
| 119 | Hierarchical Equal Risk Contribution (HERC) | Portfolio optimization / clustering | 7 | 44 | No | — | [card](algorithms/hierarchical-equal-risk-contribution-herc.md) |
| 120 | Nested Cluster Optimization (NCO) | Portfolio optimization / clustering | 147 | 45 | No | — | [card](algorithms/nested-cluster-optimization-nco.md) |
| 121 | Benchmark-Tracking Enhanced Indexing | Portfolio optimization / index enhancement | 148 | 72 | No | — | [card](algorithms/benchmark-tracking-enhanced-indexing.md) |
| 122 | Robust Wasserstein Distributionally Robust Portfolio Optimization | Portfolio optimization / Robust statistics | 114 | 184 | No | — | [card](algorithms/robust-wasserstein-distributionally-robust-portfolio-optimization.md) |
| 123 | Adversarial Robust Wasserstein Portfolio Optimization | Portfolio optimization / Robust statistics | 115 | 185 | No | — | [card](algorithms/adversarial-robust-wasserstein-portfolio-optimization.md) |
| 124 | Optimal Transport Wasserstein Barycenter Asset Allocation | Optimal Transport / Portfolio Construction | 228 | 142 | No | — | [card](algorithms/optimal-transport-wasserstein-barycenter-asset-allocation.md) |
| 125 | Continuous-Time Mean-Field Portfolio Game with Competition | Game Theory / Mean-field games / Portfolio theory | 176 | 77 | No | — | [card](algorithms/continuous-time-mean-field-portfolio-game-with-competition.md) |
| 126 | Entropic Risk Measure Portfolio Optimization | Risk-sensitive optimization / Portfolio construction | 65 | 79 | No | — | [card](algorithms/entropic-risk-measure-portfolio-optimization.md) |
| 127 | Conformal Prediction Risk-Bounded Alpha Stacking | Conformal prediction / Ensemble modeling / Portfolio construction | 217 | 49 | No | — | [card](algorithms/conformal-prediction-risk-bounded-alpha-stacking.md) |
| 128 | Fractional Order Cointegration Residual Mean-Reversion | Statistical arbitrage / Fractional time series | 171 | 228 | No | — | [card](algorithms/fractional-order-cointegration-residual-mean-reversion.md) |
| 129 | Inverse-Volatility Allocation | Portfolio construction / risk scaling | 146 | 41 | Partial | A5 | [card](algorithms/inverse-volatility-allocation.md) |
| 130 | Extreme Value Theory (EVT) Dynamic Tail-Risk Hedge | Quantitative risk management / Tail risk | 214 | 260 | No | — | [card](algorithms/extreme-value-theory-evt-dynamic-tail-risk-hedge.md) |
| 131 | Markov-Switching Vector Error Correction Model (MS-VECM) Arbitrage | Econometric / Regime-switching cointegration | 172 | 19 | No | — | [card](algorithms/markov-switching-vector-error-correction-model-ms-vecm-arbitrage.md) |
| 132 | Conformal Risk-Bounded Dynamic Portfolio Allocation | Conformal prediction / Risk management | 157 | 143 | Partial | V13 | [card](algorithms/conformal-risk-bounded-dynamic-portfolio-allocation.md) |
| 133 | Protective Put / Collar | Options / hedging | 252 | 121 | Research code | S1 | [card](algorithms/protective-put-collar.md) |
| 134 | Fractional Kelly Position Sizing | Position sizing | 47 | 70 | Research code | C-S2 | [card](algorithms/fractional-kelly-position-sizing.md) |
| 135 | Fractional Order Cointegration Vector AutoRegressive (VAR) Strategy | Statistical arbitrage / Fractional time series / Econometrics | 178 | 285 | No | — | [card](algorithms/fractional-order-cointegration-vector-autoregressive-var-strategy.md) |
| 136 | Graph Attention Network Dynamic Cointegration Basket Selection | Graph neural networks / Cointegration / Statistical arbitrage | 292 | 305 | No | — | [card](algorithms/graph-attention-network-dynamic-cointegration-basket-selection.md) |
| 137 | Fractional Cointegration Hawkes Process Lead-Lag Arbitrage | Fractional time series / Point processes / Statistical arbitrage | 311 | 9361 | No | — | [card](algorithms/fractional-cointegration-hawkes-process-lead-lag-arbitrage.md) |
| 138 | Fractional Order Vector Error Correction Model (VECM) Cointegration Strategy | Fractional time series / Cointegration / Statistical arbitrage | 184 | 291 | No | — | [card](algorithms/fractional-order-vector-error-correction-model-vecm-cointegration-strategy.md) |
| 139 | Fractional Order Cointegration Dynamic Copula Trading System | Fractional time series / Copulas / Statistical arbitrage | 187 | 293 | No | — | [card](algorithms/fractional-order-cointegration-dynamic-copula-trading-system.md) |
| 140 | Neural Rough Path Signature Delay-Differential Cointegration Spread Model | Rough path theory / Delay differential equations / Statistical arbitrage | 351 | 6479 | No | — | [card](algorithms/neural-rough-path-signature-delay-differential-cointegration-spread-model.md) |
| 141 | Fractional Order Cointegration Hawkes Point Process Statistical Arbitrage | Fractional time series / Point processes / Statistical arbitrage | 360 | 10658 | No | — | [card](algorithms/fractional-order-cointegration-hawkes-point-process-statistical-arbitrage.md) |
| 142 | Fractional Order Cointegration Vector Error Correction Hawkes Strategy | Fractional time series / Point processes / Statistical arbitrage | 361 | 10659 | No | — | [card](algorithms/fractional-order-cointegration-vector-error-correction-hawkes-strategy.md) |
| 143 | Fractional Order Cointegration Hawkes Jump-Diffusion Arbitrage | Fractional time series / Point processes / Statistical arbitrage | 299 | 10165 | No | — | [card](algorithms/fractional-order-cointegration-hawkes-jump-diffusion-arbitrage.md) |
| 144 | Alpha Stacking / Ensemble Portfolio Optimizer | Portfolio construction / ensemble | 149 | 73 | Partial | C-RJ4 | [card](algorithms/alpha-stacking-ensemble-portfolio-optimizer.md) |
| 145 | Multi-Scale Wavelet LSTM Cross-Sectional Alpha Ranker | Signal processing / Recurrent neural networks / Equity factor modeling | 297 | 240 | No | — | [card](algorithms/multi-scale-wavelet-lstm-cross-sectional-alpha-ranker.md) |
| 146 | Connors RSI-2 Mean Reversion | Mean reversion | 11 | 116 | No | — | [card](algorithms/connors-rsi-2-mean-reversion.md) |
| 147 | Moving-Average Z-Score Reversion | Mean reversion | 30 | 156 | Partial | Q9 | [card](algorithms/moving-average-z-score-reversion.md) |
| 148 | Williams %R Reversal | Mean reversion | 86 | 16 | Partial | V15 | [card](algorithms/williams-r-reversal.md) |
| 149 | Gap-Fade Strategy | Mean reversion / intraday | 133 | 157 | No | — | [card](algorithms/gap-fade-strategy.md) |
| 150 | VWAP Reversion | Mean reversion / intraday | 222 | 424 | Research code | C-MS3 | [card](algorithms/vwap-reversion.md) |
| 151 | Short-Term Stock Reversal | Mean reversion / cross-sectional | 12 | 62 | Research code | C-MR1 | [card](algorithms/short-term-stock-reversal.md) |
| 152 | Same-Calendar-Month Seasonality | Seasonality / event | 36 | 119 | No | — | [card](algorithms/same-calendar-month-seasonality.md) |
| 153 | Turn-of-the-Month Effect | Seasonality / event | 37 | 65 | No | — | [card](algorithms/turn-of-the-month-effect.md) |
| 154 | Overnight Equity Anomaly | Seasonality / intraday | 91 | 160 | Research code | — | [card](algorithms/overnight-equity-anomaly.md) |
| 155 | Wasserstein Distributionally Robust Neural Operator Portfolio Optimization | Robust statistics / Neural operators / Portfolio optimization | 336 | 198 | No | — | [card](algorithms/wasserstein-distributionally-robust-neural-operator-portfolio-optimization.md) |
| 156 | Neural Operator Delay-Differential Stochastic Control Portfolio Optimization | Neural operators / Stochastic control / Portfolio optimization | 318 | 276 | No | — | [card](algorithms/neural-operator-delay-differential-stochastic-control-portfolio-optimization.md) |
| 157 | Wasserstein Distributionally Robust Neural Operator Optimal Portfolio | Robust statistics / Neural operators / Portfolio optimization | 337 | 215 | No | — | [card](algorithms/wasserstein-distributionally-robust-neural-operator-optimal-portfolio.md) |
| 158 | Fractional Cointegration Multiscale Wavelet Arbitrage | Fractional calculus / Wavelets / Statistical arbitrage | 316 | 10283 | No | — | [card](algorithms/fractional-cointegration-multiscale-wavelet-arbitrage.md) |
| 159 | Koopman Operator Non-Linear Cointegration Spread Strategy | Operator theory / Cointegration / Statistical arbitrage | 180 | 288 | No | — | [card](algorithms/koopman-operator-non-linear-cointegration-spread-strategy.md) |
| 160 | RSI Oversold/Overbought Reversion | Mean reversion | 28 | 61 | Research code | Q10, V3 | [card](algorithms/rsi-oversold-overbought-reversion.md) |
| 161 | Bollinger Band Mean Reversion | Mean reversion | 29 | 89 | Partial | Q9, X4 | [card](algorithms/bollinger-band-mean-reversion.md) |
| 162 | Stochastic Oscillator Reversal | Mean reversion | 85 | 80 | Partial | V15 | [card](algorithms/stochastic-oscillator-reversal.md) |
| 163 | FX Mean-Reversion / Momentum Hybrid | Mean reversion / FX | 87 | 63 | No | — | [card](algorithms/fx-mean-reversion-momentum-hybrid.md) |
| 164 | Grid / Price-Ladder Trading | Mean reversion / inventory | 33 | 64 | Yes | V1, V2, V3, V4, V5, C-G2, C-G3, C-G4 | [card](algorithms/grid-price-ladder-trading.md) |
| 165 | Fractional Order Cointegration Dynamic Copula Portfolio Optimizer | Fractional time series / Copulas / Portfolio construction | 250 | 155 | No | — | [card](algorithms/fractional-order-cointegration-dynamic-copula-portfolio-optimizer.md) |
| 166 | Calendar / Diagonal Spread | Options / volatility | 201 | 253 | No | — | [card](algorithms/calendar-diagonal-spread.md) |
| 167 | Delta-Hedged Volatility Arbitrage | Options / volatility | 328 | 6473 | No | — | [card](algorithms/delta-hedged-volatility-arbitrage.md) |
| 168 | VIX Futures Term-Structure Strategy | Options / volatility | 92 | 265 | Partial | — | [card](algorithms/vix-futures-term-structure-strategy.md) |
| 169 | Volatility Skew Risk Premium | Options / volatility risk premium | 99 | 39 | No | — | [card](algorithms/volatility-skew-risk-premium.md) |
| 170 | Earnings Volatility Crush / Delta-Hedged Event Options | Options / event volatility | 169 | 165 | No | — | [card](algorithms/earnings-volatility-crush-delta-hedged-event-options.md) |
| 171 | Put-Call Parity Conversion / Reversal Arbitrage | Options / no-arbitrage | 100 | 224 | No | — | [card](algorithms/put-call-parity-conversion-reversal-arbitrage.md) |
| 172 | Box-Spread Financing Arbitrage | Options / synthetic lending | 209 | 134 | No | — | [card](algorithms/box-spread-financing-arbitrage.md) |
| 173 | Broken-Wing Butterfly | Options / asymmetric convexity | 210 | 225 | No | — | [card](algorithms/broken-wing-butterfly.md) |
| 174 | Put Debit Spread Momentum | Options / directional risk-defined | 101 | 40 | No | — | [card](algorithms/put-debit-spread-momentum.md) |
| 175 | Quantum Approximate Optimization Algorithm (QAOA) Allocation | Quantum computing / Portfolio optimization | 219 | 183 | No | — | [card](algorithms/quantum-approximate-optimization-algorithm-qaoa-allocation.md) |
| 176 | Rough Heston Stochastic Volatility Calibration | Econometric volatility / Mathematical finance | 358 | 2119 | No | — | [card](algorithms/rough-heston-stochastic-volatility-calibration.md) |
| 177 | Variational Autoencoder (VAE) Latent Yield Curve Arbitrage | Deep Learning / Fixed Income Relative Value | 264 | 110 | No | — | [card](algorithms/variational-autoencoder-vae-latent-yield-curve-arbitrage.md) |
| 178 | Manifold Learning Diffusion Map Statistical Arbitrage | Manifold learning / Statistical arbitrage | 295 | 10219 | No | — | [card](algorithms/manifold-learning-diffusion-map-statistical-arbitrage.md) |
| 179 | Fractional Order Kalman Filter Dynamic Hedging | Fractional calculus / State-space models / Statistical arbitrage | 325 | 10230 | No | — | [card](algorithms/fractional-order-kalman-filter-dynamic-hedging.md) |
| 180 | Persistent Homology Betti-1 Loop Topological Momentum Strategy | Topological data analysis / Momentum / Cycle detection | 118 | 33 | No | — | [card](algorithms/persistent-homology-betti-1-loop-topological-momentum-strategy.md) |
| 181 | Wasserstein Distributionally Robust Mean-CVaR Dynamic Allocation | Robust statistics / Tail risk allocation | 283 | 169 | No | — | [card](algorithms/wasserstein-distributionally-robust-mean-cvar-dynamic-allocation.md) |
| 182 | Quantum Annealing Graph Partitioning Statistical Arbitrage | Quantum computing / Graph partitioning / Statistical arbitrage | 326 | 1809 | No | — | [card](algorithms/quantum-annealing-graph-partitioning-statistical-arbitrage.md) |
| 183 | Persistent Homology Betti-0 Multiscale Clustering Arbitrage | Topological data analysis / Clustering / Statistical arbitrage | 120 | 199 | No | — | [card](algorithms/persistent-homology-betti-0-multiscale-clustering-arbitrage.md) |
| 184 | Quantum Approximate Optimization Algorithm (QAOA) Max-Cut Statistical Arbitrage | Quantum computing / Max-Cut / Statistical arbitrage | 327 | 1707 | No | — | [card](algorithms/quantum-approximate-optimization-algorithm-qaoa-max-cut-statistical-arbitrage.md) |
| 185 | Riemannian Manifold Metric Hierarchical Risk Parity | Geometric deep learning / Riemannian geometry / Portfolio construction | 249 | 205 | No | — | [card](algorithms/riemannian-manifold-metric-hierarchical-risk-parity.md) |
| 186 | Quantum Annealing Binary Matrix Factorization Statistical Arbitrage | Quantum computing / Matrix factorization / Statistical arbitrage | 323 | 290 | No | — | [card](algorithms/quantum-annealing-binary-matrix-factorization-statistical-arbitrage.md) |
| 187 | Persistent Homology Betti-0 Connected Component Risk Parity | Topological data analysis / Risk parity / Portfolio construction | 124 | 207 | No | — | [card](algorithms/persistent-homology-betti-0-connected-component-risk-parity.md) |
| 188 | Riemannian Manifold Metric Persistent Homology Risk Parity | Geometric deep learning / Riemannian geometry / Topological risk parity | 186 | 151 | No | — | [card](algorithms/riemannian-manifold-metric-persistent-homology-risk-parity.md) |
| 189 | Persistent Homology Betti-1 Cyclical Persistence Landscape Arbitrage | Topological data analysis / Statistical arbitrage / Persistence landscapes | 125 | 208 | No | — | [card](algorithms/persistent-homology-betti-1-cyclical-persistence-landscape-arbitrage.md) |
| 190 | Neural Rough Path Signature Hawkes Jump-Diffusion Spread Arbitrage | Rough path theory / Point processes / Statistical arbitrage | 352 | 6480 | No | — | [card](algorithms/neural-rough-path-signature-hawkes-jump-diffusion-spread-arbitrage.md) |
| 191 | Graph Attention Network Riemannian Manifold Dynamic Risk Parity | Graph neural networks / Riemannian geometry / Risk parity | 271 | 115 | No | — | [card](algorithms/graph-attention-network-riemannian-manifold-dynamic-risk-parity.md) |
| 192 | Quantum Annealing Maximum Independent Set Statistical Arbitrage | Quantum computing / Maximum independent set / Statistical arbitrage | 298 | 277 | No | — | [card](algorithms/quantum-annealing-maximum-independent-set-statistical-arbitrage.md) |
| 193 | Persistent Homology Betti-0 Persistence Landscape Clustering Arbitrage | Topological data analysis / Persistence landscapes / Statistical arbitrage | 130 | 216 | No | — | [card](algorithms/persistent-homology-betti-0-persistence-landscape-clustering-arbitrage.md) |
| 194 | Fixed Fractional / Fixed Dollar Risk | Position sizing | 93 | 254 | No | — | [card](algorithms/fixed-fractional-fixed-dollar-risk.md) |
| 195 | GARCH Volatility Forecasting with Mean-Reversion Channel | Econometric / Volatility modeling | 263 | 6475 | No | — | [card](algorithms/garch-volatility-forecasting-with-mean-reversion-channel.md) |
| 196 | Randomized Matrix Pencil Lead-Lag Cross-Asset Predictor | Signal processing / Matrix pencil / Lead-lag arbitrage | 229 | 2829 | No | — | [card](algorithms/randomized-matrix-pencil-lead-lag-cross-asset-predictor.md) |
| 197 | Topological Persistent Betti Curve Macro Regime Switcher | Topological data analysis / Regime switching / Macro strategy | 177 | 190 | No | — | [card](algorithms/topological-persistent-betti-curve-macro-regime-switcher.md) |
| 198 | Wasserstein Generative Adversarial Network Multi-Asset Allocation (WGAN-MA) | Generative machine learning / Robust portfolio allocation | 315 | 191 | No | — | [card](algorithms/wasserstein-generative-adversarial-network-multi-asset-allocation-wgan-ma.md) |
| 199 | Persistent Homology Betti-1 Persistence Landscape Arbitrage | Topological data analysis / Persistence landscapes / Statistical arbitrage | 121 | 201 | No | — | [card](algorithms/persistent-homology-betti-1-persistence-landscape-arbitrage.md) |
| 200 | Generative Score-Based Diffusion Multi-Asset Scenario Synthesizer | Generative AI / Diffusion models / Risk management | 320 | 298 | No | RK200 | [**researched**](algorithms/generative-score-based-diffusion-multi-asset-scenario-synthesizer.md) |
| 201 | Koopman Operator Predictive Control Statistical Arbitrage | Operator theory / Model predictive control / Statistical arbitrage | 220 | 426 | No | RK201 | [**researched**](algorithms/koopman-operator-predictive-control-statistical-arbitrage.md) |
| 202 | Fractional Brownian Motion Multi-Scale Trend Scanning Strategy | Fractional calculus / Trend scanning / Technical alpha | 317 | 304 | No | RK202 | [**researched**](algorithms/fractional-brownian-motion-multi-scale-trend-scanning-strategy.md) |
| 203 | Koopman Operator Model Predictive Control Spread Equilibrium | Operator theory / Model predictive control / Statistical arbitrage | 128 | 297 | No | RK203 | [**researched**](algorithms/koopman-operator-model-predictive-control-spread-equilibrium.md) |
| 204 | Lead-Lag Cross-Asset Predictive Trading | Cross-asset / statistical | 139 | 105 | Research code | RK204 | [**researched**](algorithms/lead-lag-cross-asset-predictive-trading.md) |
| 205 | Dynamic Tensor Decomposition Multi-Asset Factor Rotation | Tensor algebra / Factor investing | 77 | 32 | No | RK205 | [**researched**](algorithms/dynamic-tensor-decomposition-multi-asset-factor-rotation.md) |
| 206 | Koopman Operator Model Predictive Control Multi-Asset Allocation | Operator theory / Model predictive control / Portfolio allocation | 233 | 154 | No | RK206 | [**researched**](algorithms/koopman-operator-model-predictive-control-multi-asset-allocation.md) |
| 207 | Standardized Unexpected Earnings (SUE) | Factor / event-driven | 111 | 118 | No | RK207 | [**researched**](algorithms/standardized-unexpected-earnings-sue.md) |
| 208 | Anchored VWAP Reclaim / Rejection | Intraday price/volume | 159 | 248 | Partial | RK208, C-MS3 | [**researched**](algorithms/anchored-vwap-reclaim-rejection.md) |
| 209 | Corporate Buyback Announcement Drift | Event-driven / corporate actions | 143 | 71 | No | RK209 | [**researched**](algorithms/corporate-buyback-announcement-drift.md) |
| 210 | Index Reconstitution / Rebalance Event Trading | Event-driven / flow prediction | 97 | 96 | No | RK210 | [**researched**](algorithms/index-reconstitution-rebalance-event-trading.md) |
| 211 | Macro Surprise / Economic Release Strategy | Macro / event-driven | 207 | 164 | Partial | RK211, V6 | [**researched**](algorithms/macro-surprise-economic-release-strategy.md) |
| 212 | Market Breadth Thrust | Market internals / timing | 58 | 38 | No | RK212 | [**researched**](algorithms/market-breadth-thrust.md) |
| 213 | Trend-Scanning Label Model | ML / event labeling | 152 | 137 | Research code | RK213, C-ML1 | [**researched**](algorithms/trend-scanning-label-model.md) |
| 214 | XGBoost Cross-Sectional Ranking | ML / cross-sectional selection | 113 | 23 | No | RK214 | [**researched**](algorithms/xgboost-cross-sectional-ranking.md) |
| 215 | Cross-Sectional Reversal with Risk Neutralization | Equity / short-horizon reversal | 103 | 97 | Partial | RK215, C-MR1 | [**researched**](algorithms/cross-sectional-reversal-with-risk-neutralization.md) |
| 216 | Top-K with Dropout Portfolio Rotation | Portfolio strategy / ML signal deployment | 104 | 24 | No | RK216 | [**researched**](algorithms/top-k-with-dropout-portfolio-rotation.md) |
| 217 | Bayesian Structural Time Series (BSTS) Causal Impact Macro Strategy | Bayesian econometrics / Macro event trading | 236 | 186 | No | RK217 | [**researched**](algorithms/bayesian-structural-time-series-bsts-causal-impact-macro-strategy.md) |
| 218 | Sparse Bayesian Learning Dynamic Factor Model | Bayesian statistics / Systematic equity | 76 | 109 | No | RK218 | [**researched**](algorithms/sparse-bayesian-learning-dynamic-factor-model.md) |
| 219 | Dynamic Mode Decomposition (DMD) Market Mode Predictor | Signal Processing / Dynamical Systems | 227 | 303 | No | RK219 | [**researched**](algorithms/dynamic-mode-decomposition-dmd-market-mode-predictor.md) |
| 220 | Continuous-Time Mean-Variance Reinforcement Learning Agent | Reinforcement Learning / Portfolio Theory | 174 | 187 | No | RK220 | [**researched**](algorithms/continuous-time-mean-variance-reinforcement-learning-agent.md) |
| 221 | Information-Theoretic Transfer Entropy Lead-Lag Strategy | Information theory / Cross-asset lead-lag | 374 | 6477 | No | RK221 | [**researched**](algorithms/information-theoretic-transfer-entropy-lead-lag-strategy.md) |
| 222 | Maximum Entropy Production Rate Macro Allocator | Thermodynamic finance / Macro allocation | 239 | 144 | No | RK222 | [**researched**](algorithms/maximum-entropy-production-rate-macro-allocator.md) |
| 223 | Quantum Tensor Network Portfolio Optimization | Quantum computing / Tensor networks / Portfolio optimization | 257 | 239 | No | RK223 | [**researched**](algorithms/quantum-tensor-network-portfolio-optimization.md) |
| 224 | Deep Latent Force Model (LFM) Interest Rate Forecaster | Gaussian processes / Differential equations / Fixed income | 161 | 86 | No | RK224 | [**researched**](algorithms/deep-latent-force-model-lfm-interest-rate-forecaster.md) |
| 225 | Wasserstein Distributionally Robust Mean-Variance Allocation | Robust statistics / Mean-variance optimization | 78 | 147 | No | RK225 | [**researched**](algorithms/wasserstein-distributionally-robust-mean-variance-allocation.md) |
| 226 | Functional Principal Component Analysis (FPCA) Yield Curve Forecaster | Functional data analysis / Fixed income | 79 | 48 | No | RK226 | [**researched**](algorithms/functional-principal-component-analysis-fpca-yield-curve-forecaster.md) |
| 227 | Multi-Agent Evolutionary Reinforcement Learning Portfolio Optimizer | Evolutionary algorithms / Reinforcement learning / Portfolio construction | 265 | 99 | No | RK227 | [**researched**](algorithms/multi-agent-evolutionary-reinforcement-learning-portfolio-optimizer.md) |
| 228 | Deep Generative Flow Matching Portfolio Generator | Generative AI / Continuous normalizing flows / Portfolio allocation | 356 | 286 | No | RK228 | [**researched**](algorithms/deep-generative-flow-matching-portfolio-generator.md) |
| 229 | Quantum Adiabatic Optimal Portfolio Rebalancing | Quantum computing / Adiabatic evolution / Portfolio optimization | 259 | 241 | No | RK229 | [**researched**](algorithms/quantum-adiabatic-optimal-portfolio-rebalancing.md) |
| 230 | Riemannian Manifold Metric Optimization Portfolio | Geometric deep learning / Riemannian optimization / Portfolio construction | 245 | 195 | No | RK230 | [**researched**](algorithms/riemannian-manifold-metric-optimization-portfolio.md) |
| 231 | Riemannian Manifold Metric Diffusion Portfolio Allocation | Geometric deep learning / Riemannian geometry / Portfolio allocation | 266 | 197 | No | RK231 | [**researched**](algorithms/riemannian-manifold-metric-diffusion-portfolio-allocation.md) |
| 232 | Graph Attention Network Covariance Shrinkage Estimator | Graph neural networks / Covariance estimation / Portfolio construction | 181 | 170 | No | RK232 | [**researched**](algorithms/graph-attention-network-covariance-shrinkage-estimator.md) |
| 233 | Riemannian Manifold Metric Wasserstein Robust Allocation | Geometric deep learning / Riemannian geometry / Robust portfolio allocation | 248 | 203 | No | RK233 | [**researched**](algorithms/riemannian-manifold-metric-wasserstein-robust-allocation.md) |
| 234 | Wasserstein Distributionally Robust Reinforcement Learning Portfolio Agent | Robust reinforcement learning / Portfolio allocation | 349 | 150 | No | RK234 | [**researched**](algorithms/wasserstein-distributionally-robust-reinforcement-learning-portfolio-agent.md) |
| 235 | Graph Attention Network Covariance Matrix Shrinkage Dynamic Allocation | Graph neural networks / Covariance shrinkage / Portfolio allocation | 185 | 113 | No | RK235 | [**researched**](algorithms/graph-attention-network-covariance-matrix-shrinkage-dynamic-allocation.md) |
| 236 | Quantum Adiabatic Graph Neural Network Portfolio Optimization | Quantum computing / Graph neural networks / Portfolio optimization | 342 | 292 | No | RK236 | [**researched**](algorithms/quantum-adiabatic-graph-neural-network-portfolio-optimization.md) |
| 237 | Riemannian Manifold Metric Graph Attention Portfolio Allocation | Geometric deep learning / Graph attention networks / Portfolio allocation | 268 | 114 | No | RK237 | [**researched**](algorithms/riemannian-manifold-metric-graph-attention-portfolio-allocation.md) |
| 238 | Quantum Adiabatic Tensor Network Portfolio Optimization | Quantum computing / Tensor networks / Portfolio optimization | 221 | 210 | No | RK238 | [**researched**](algorithms/quantum-adiabatic-tensor-network-portfolio-optimization.md) |
| 239 | Fractional Order Vector Error Correction Neural Network Portfolio Allocator | Fractional time series / Neural networks / Portfolio allocation | 269 | 153 | No | RK239 | [**researched**](algorithms/fractional-order-vector-error-correction-neural-network-portfolio-allocator.md) |
| 240 | Neural Operator Delay-Differential Stochastic Volatility Calibrator | Neural operators / Stochastic volatility / Options pricing | 701 | 10286 | No | RK240 | [**researched**](algorithms/neural-operator-delay-differential-stochastic-volatility-calibrator.md) |
| 241 | Koopman Operator Multi-Factor Equity Risk Factor Tracking | Operator theory / Factor modeling / Risk management | 163 | 112 | No | RK241 | [**researched**](algorithms/koopman-operator-multi-factor-equity-risk-factor-tracking.md) |
| 242 | Long-Volatility Breakout (Options) | Options / volatility | 41 | 102 | Research code | RK242, Q12 | [**researched**](algorithms/long-volatility-breakout-options.md) |
| 243 | Price/Volume Anomaly Detection | Machine learning / microstructure | 223 | 54 | Partial | RK243, A8 | [**researched**](algorithms/price-volume-anomaly-detection.md) |
| 244 | Liquidity-Aware Adaptive Execution | Execution / market microstructure | 362 | 9357 | Partial | RK244 | [**researched**](algorithms/liquidity-aware-adaptive-execution.md) |
| 245 | Pure Passive Market Making | Market microstructure / market making | 304 | 2118 | Research code | RK245, C-MM1, C-MM2 | [**researched**](algorithms/pure-passive-market-making.md) |
| 246 | Inventory-Skewed Market Making | Market microstructure / market making | 305 | 1815 | Research code | RK246, C-G2, C-MM1 | [**researched**](algorithms/inventory-skewed-market-making.md) |
| 247 | VPIN Flow-Toxicity Filter | Market microstructure / risk filter | 363 | 10495 | Research code | RK247, C-MM4 | [**researched**](algorithms/vpin-flow-toxicity-filter.md) |
| 248 | Hawkes-Process Order-Flow Forecast | Market microstructure / point process | 332 | 10217 | No | RK248 | [**researched**](algorithms/hawkes-process-order-flow-forecast.md) |
| 249 | Iceberg / Reserve-Order Execution | Execution / market impact | 307 | 6474 | No | RK249 | [**researched**](algorithms/iceberg-reserve-order-execution.md) |
| 250 | Arrival-Price Adaptive Limit-vs-Market Execution | Execution / transaction-cost optimization | 154 | 302 | Partial | RK250 | [**researched**](algorithms/arrival-price-adaptive-limit-vs-market-execution.md) |
| 251 | Intraday Volume-Profile Execution | Execution / volume forecasting | 102 | 250 | No | RK251 | [**researched**](algorithms/intraday-volume-profile-execution.md) |
| 252 | Order-Flow Imbalance (OFI) Cross-Sectional Alpha Predictor | Market microstructure / Alpha generation | 321 | 10483 | Partial | RK252, C-MS1 | [**researched**](algorithms/order-flow-imbalance-ofi-cross-sectional-alpha-predictor.md) |
| 253 | Information-Driven Volume Clock Imbalance Momentum | Market microstructure / Volume timing | 340 | 6476 | Partial | RK253, C-ML5 | [**researched**](algorithms/information-driven-volume-clock-imbalance-momentum.md) |
| 254 | Persistent Homology Topological Data Analysis (TDA) Crash Predictor | Topological data analysis / Risk management | 294 | 7422 | No | RK254 | [**researched**](algorithms/persistent-homology-topological-data-analysis-tda-crash-predictor.md) |
| 255 | Persistent Homology Topological Landscape Crisis Predictor | Topological data analysis / Risk management / Crash prediction | 296 | 7424 | No | RK255 | [**researched**](algorithms/persistent-homology-topological-landscape-crisis-predictor.md) |
| 256 | Deep Markov State-Space Intraday Volume Profile Predictor | Deep state-space models / Market microstructure | 1877 | 10496 | No | RK256 | [**researched**](algorithms/deep-markov-state-space-intraday-volume-profile-predictor.md) |
| 257 | Information-Theoretic Causality Flow Macro Asset Allocator | Information theory / Causal inference / Macro allocation | 240 | 78 | No | RK257 | [**researched**](algorithms/information-theoretic-causality-flow-macro-asset-allocator.md) |
| 258 | Spiking Graph Convolutional Network (SGCN) Contagion Predictor | Neuromorphic AI / Graph neural networks / Risk management | 241 | 146 | No | RK258 | [**researched**](algorithms/spiking-graph-convolutional-network-sgcn-contagion-predictor.md) |
| 259 | Hawkes-Driven Non-Parametric Order Flow Toxicity Filter | Point process / Market microstructure / Risk filter | 378 | 10227 | No | RK259 | [**researched**](algorithms/hawkes-driven-non-parametric-order-flow-toxicity-filter.md) |
| 260 | Quantum Approximate State Preparation Risk Mapping | Quantum computing / Risk management / Monte Carlo | 258 | 284 | No | RK260 | [**researched**](algorithms/quantum-approximate-state-preparation-risk-mapping.md) |
| 261 | Koopman Operator Model Predictive Control Risk Mitigation | Operator theory / Model predictive control / Risk management | 230 | 192 | No | RK261 | [**researched**](algorithms/koopman-operator-model-predictive-control-risk-mitigation.md) |
| 262 | Persistent Homology Betti-0 Connected Component Contagion Detector | Topological data analysis / Risk management / Contagion | 116 | 193 | No | RK262 | [**researched**](algorithms/persistent-homology-betti-0-connected-component-contagion-detector.md) |
| 263 | Topological Persistence Diagram Clustering Crisis Detector | Topological data analysis / Risk management / Crash prediction | 117 | 194 | No | RK263 | [**researched**](algorithms/topological-persistence-diagram-clustering-crisis-detector.md) |
| 264 | Information-Theoretic Directed GNN Contagion Model | Information theory / Graph neural networks / Risk management | 218 | 149 | No | RK264 | [**researched**](algorithms/information-theoretic-directed-gnn-contagion-model.md) |
| 265 | Persistent Homology Betti-2 3D Void Macro Stress Predictor | Topological data analysis / Macro risk management | 119 | 196 | No | RK265 | [**researched**](algorithms/persistent-homology-betti-2-3d-void-macro-stress-predictor.md) |
| 266 | Riemannian Manifold Metric Entropic Risk Portfolio | Geometric deep learning / Riemannian optimization / Risk management | 247 | 200 | No | RK266 | [**researched**](algorithms/riemannian-manifold-metric-entropic-risk-portfolio.md) |
| 267 | Graph Attention Network Covariance Matrix Spectral Regularization | Graph neural networks / Covariance estimation / Risk management | 182 | 171 | No | RK267 | [**researched**](algorithms/graph-attention-network-covariance-matrix-spectral-regularization.md) |
| 268 | Persistent Homology Multi-Scale Vietoris-Rips Filtration Risk Scoring | Topological data analysis / Risk management | 123 | 204 | No | RK268 | [**researched**](algorithms/persistent-homology-multi-scale-vietoris-rips-filtration-risk-scoring.md) |
| 269 | Persistent Homology Betti-0 Multiscale Filtration Contagion Clustering | Topological data analysis / Clustering / Risk management | 127 | 211 | Partial | RK269, A5 | [**researched**](algorithms/persistent-homology-betti-0-multiscale-filtration-contagion-clustering.md) |
| 270 | Quantum Annealing Binary Matrix Factorization Portfolio Risk Model | Quantum computing / Matrix factorization / Risk management | 261 | 243 | No | RK270 | [**researched**](algorithms/quantum-annealing-binary-matrix-factorization-portfolio-risk-model.md) |
| 271 | Sequential Bootstrapping Sample Weights | ML / training data sampling | 153 | 138 | No | RK271 | [**researched**](algorithms/sequential-bootstrapping-sample-weights.md) |
| 272 | Wavelet-Neural Network Hybrid Intraday Trend Scalper | Signal processing / Machine learning trend | 322 | 2828 | No | RK272 | [**researched**](algorithms/wavelet-neural-network-hybrid-intraday-trend-scalper.md) |
| 273 | Deep Koopman-Inspired Spectral Asset Allocation | Operator theory / Dynamical systems / Portfolio allocation | 162 | 148 | No | RK273 | [**researched**](algorithms/deep-koopman-inspired-spectral-asset-allocation.md) |
| 274 | Avellaneda–Stoikov Market Making | Market making | 302 | 5930 | Research code | RK274, C-MM1 | [**researched**](algorithms/avellaneda-stoikov-market-making.md) |
| 275 | DeepLOB-Style Order-Book Forecasting | ML / market microstructure | 353 | 10329 | No | RK275 | [**researched**](algorithms/deeplob-style-order-book-forecasting.md) |
| 276 | Queue-Reactive Market Making | Market microstructure / market making | 306 | 10330 | Partial | RK276, C-MM5 | [**researched**](algorithms/queue-reactive-market-making.md) |
| 277 | Hawkes Process Multi-Dimensional Order Flow Intensity Model | Point process / Market microstructure | 364 | 10556 | No | RK277 | [**researched**](algorithms/hawkes-process-multi-dimensional-order-flow-intensity-model.md) |
| 278 | Cross-Venue Crypto Triangular Arbitrage | Arbitrage / Crypto microstructure | 365 | 1807 | Research code | RK278, A7 | [**researched**](algorithms/cross-venue-crypto-triangular-arbitrage.md) |
| 279 | Asynchronous Multi-Exchange Spatial Arbitrage Graph | Arbitrage / Market microstructure | 366 | 1808 | Research code | RK279, A7 | [**researched**](algorithms/asynchronous-multi-exchange-spatial-arbitrage-graph.md) |
| 280 | Recurrent Neural Hawkes Point Process Toxic Flow Hedging Trigger | Point processes / Recurrent neural networks / Risk management | 1882 | 10498 | No | RK280 | [**researched**](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-hedging-trigger.md) |
| 281 | Covered Call / Buy-Write | Options / income | 197 | 161 | Research code | RK281, S1 | [**researched**](algorithms/covered-call-buy-write.md) |
| 282 | Put-Write / Cash-Secured Put | Options / income | 198 | 221 | Research code | RK282, S1 | [**researched**](algorithms/put-write-cash-secured-put.md) |
| 283 | Wasserstein Distributionally Robust Neural Stochastic Control Hedging | Robust statistics / Stochastic control / Derivatives hedging | 287 | 296 | No | RK283 | [**researched**](algorithms/wasserstein-distributionally-robust-neural-stochastic-control-hedging.md) |
| 284 | Options Wheel | Options / income | 199 | 222 | Research code | RK284, S1 | [**researched**](algorithms/options-wheel.md) |
| 285 | Iron Condor / Short Premium Range Strategy | Options / income | 200 | 280 | No | RK285 | [**researched**](algorithms/iron-condor-short-premium-range-strategy.md) |
| 286 | Iron Butterfly Credit Strategy | Options / short premium | 145 | 267 | No | RK286 | [**researched**](algorithms/iron-butterfly-credit-strategy.md) |
| 287 | Neural Operator Delay Differential Equation (Delay-ODE) Term Structure Predictor | Neural operators / Delay differential equations / Fixed income | 310 | 87 | No | RK287 | [**researched**](algorithms/neural-operator-delay-differential-equation-delay-ode-term-structure-predictor.md) |
| 288 | Neural Controlled Differential Equation (Neural CDE) Point Process Execution | Neural CDEs / Point processes / Execution | 5372 | 9360 | No | RK288 | [**researched**](algorithms/neural-controlled-differential-equation-neural-cde-point-process-execution.md) |
| 289 | Neural Operator Delay-Differential Hawkes Microstructure Predictor | Neural operators / Point processes / Microstructure | 696 | 10285 | No | RK289 | [**researched**](algorithms/neural-operator-delay-differential-hawkes-microstructure-predictor.md) |
| 290 | Random Forest Return Classification | Machine learning | 312 | 53 | No | RK290 | [**researched**](algorithms/random-forest-return-classification.md) |
| 291 | Gradient-Boosted Trees Return Prediction | Machine learning | 275 | 103 | Yes | RK291, V13, V14 | [**researched**](algorithms/gradient-boosted-trees-return-prediction.md) |
| 292 | LSTM Sequence Forecasting | Machine learning | 313 | 104 | Research code | RK292, C-RJ4 | [**researched**](algorithms/lstm-sequence-forecasting.md) |
| 293 | News / Financial Sentiment NLP | Machine learning / alternative data | 300 | 223 | No | RK293 | [**researched**](algorithms/news-financial-sentiment-nlp.md) |
| 294 | Triple-Barrier Labeled ML Strategy | Machine learning / event-based labels | 150 | 135 | Partial | RK294, C-ML1 | [**researched**](algorithms/triple-barrier-labeled-ml-strategy.md) |
| 295 | Conformal Prediction Uncertainty Wrapper (CP-MAPIE) | Uncertainty quantification / Machine learning filter | 155 | 74 | Research code | RK295, V13 | [**researched**](algorithms/conformal-prediction-uncertainty-wrapper-cp-mapie.md) |
| 296 | Dynamic Copula-Vine Regularized Factor Allocation | Vine copulas / Regularization / Multi-factor allocation | 244 | 168 | No | RK296 | [**researched**](algorithms/dynamic-copula-vine-regularized-factor-allocation.md) |
| 297 | Fractional Hurst-Driven Adaptive Bandwidth Mean Reversion | Fractional time-series / Mean reversion | 156 | 2760 | Partial | RK297, C-MR4 | [**researched**](algorithms/fractional-hurst-driven-adaptive-bandwidth-mean-reversion.md) |
| 298 | AMM / CLOB Cross-Venue Arbitrage | Crypto / decentralized market structure | 142 | 133 | No | RK298 | [**researched**](algorithms/amm-clob-cross-venue-arbitrage.md) |
| 299 | Dynamic AMM Liquidity Provision / Liquidity Mining | Crypto / liquidity provision | 331 | 959 | No | RK299 | [**researched**](algorithms/dynamic-amm-liquidity-provision-liquidity-mining.md) |
| 300 | Fractional Differentiation Feature Pipeline | ML / time-series preprocessing | 151 | 136 | Research code | RK300, C-ML5 | [**researched**](algorithms/fractional-differentiation-feature-pipeline.md) |
| 301 | Temporal Fusion Transformer Forecasting | ML / time-series forecasting | 277 | 249 | No | RK301 | [**researched**](algorithms/temporal-fusion-transformer-forecasting.md) |
| 302 | Physics-Informed Deep Galerkin Method (DGM) Option Solver | Physics-informed neural networks / Options pricing | 281 | 283 | No | RK302 | [**researched**](algorithms/physics-informed-deep-galerkin-method-dgm-option-solver.md) |
| 303 | Neural Jump-Diffusion Rough Heston Smile Predictor | Stochastic volatility / Deep learning / Derivatives pricing | 379 | 10661 | No | RK303 | [**researched**](algorithms/neural-jump-diffusion-rough-heston-smile-predictor.md) |
| 304 | Recurrent Neural Hawkes Point Process Volatility Jump Forecaster | Point processes / Recurrent neural networks / Volatility forecasting | 5371 | 10657 | No | RK304 | [**researched**](algorithms/recurrent-neural-hawkes-point-process-volatility-jump-forecaster.md) |
| 305 | Quantum Annealing Binary Quadratic Portfolio Rebalancing | Quantum computing / Quadratic programming / Portfolio optimization | 260 | 242 | No | RK305 | [**researched**](algorithms/quantum-annealing-binary-quadratic-portfolio-rebalancing.md) |
| 306 | Microprice / Queue-Imbalance Signal | Market microstructure / alpha | 303 | 9812 | Research code | RK306, C-MS2 | [**researched**](algorithms/microprice-queue-imbalance-signal.md) |
| 307 | Cross-Exchange Market Making (XEMM) | Market microstructure / market making | 226 | 2117 | No | RK307 | [**researched**](algorithms/cross-exchange-market-making-xemm.md) |
| 308 | Dividend Capture Window Strategy | Equity event / income | 96 | 95 | No | RK308 | [**researched**](algorithms/dividend-capture-window-strategy.md) |
| 309 | Gamma Scalping / Long-Gamma Rebalancing | Options / delta hedging | 208 | 237 | No | RK309 | [**researched**](algorithms/gamma-scalping-long-gamma-rebalancing.md) |
| 310 | Multi-Agent RL Execution / Liquidation | Reinforcement learning / execution | 368 | 7421 | No | RK310 | [**researched**](algorithms/multi-agent-rl-execution-liquidation.md) |
| 311 | FinBERT Sentiment-Driven Event Arbitrage | NLP / Machine learning / Event-driven | 213 | 98 | No | RK311 | [**researched**](algorithms/finbert-sentiment-driven-event-arbitrage.md) |
| 312 | Deep Q-Network (DQN) Liquidation Agent | Reinforcement learning / Execution | 376 | 10163 | No | RK312 | [**researched**](algorithms/deep-q-network-dqn-liquidation-agent.md) |
| 313 | Adaptive Mesh Reinforcement Learning Market Maker (RL-MM) | Reinforcement learning / Market making | 5368 | 11671 | No | RK313 | [**researched**](algorithms/adaptive-mesh-reinforcement-learning-market-maker-rl-mm.md) |
| 314 | Hawkes-Jump Diffusion Multivariate Event Detection | Point process / Event-driven microstructure | 344 | 7557 | No | RK314 | [**researched**](algorithms/hawkes-jump-diffusion-multivariate-event-detection.md) |
| 315 | Empirical Mode Decomposition (EMD) Hilbert-Huang Intraday Scalper | Signal Processing / Technical Analysis | 71 | 75 | No | RK315 | [**researched**](algorithms/empirical-mode-decomposition-emd-hilbert-huang-intraday-scalper.md) |
| 316 | Temporal CNN / TCN Forecasting | Machine learning | 108 | 128 | No | RK316 | [**researched**](algorithms/temporal-cnn-tcn-forecasting.md) |
| 317 | Meta-Labeling Primary Signals | Machine learning / signal filtering | 253 | 107 | Yes | RK317, V13, C-ML1 | [**researched**](algorithms/meta-labeling-primary-signals.md) |
| 318 | Graph Convolutional Network (GCN) Cross-Sectional Stock Ranking | Graph machine learning / Quantitative equity | 173 | 108 | No | RK318 | [**researched**](algorithms/graph-convolutional-network-gcn-cross-sectional-stock-ranking.md) |
| 319 | Vol-Harvesting Dynamic Asymmetric Grid | Grid trading / Inventory management / Volatility harvesting | 70 | 46 | Yes | RK319, V3, V5, C-G3 | [**researched**](algorithms/vol-harvesting-dynamic-asymmetric-grid.md) |
| 320 | Koopman Operator Non-Linear Volatility Surface Interpolator | Operator theory / Volatility derivatives | 347 | 10446 | No | RK320 | [**researched**](algorithms/koopman-operator-non-linear-volatility-surface-interpolator.md) |
| 321 | Koopman Operator Non-Linear Volatility Surface Pricing Model | Operator theory / Volatility derivatives / Options pricing | 350 | 10447 | No | RK321 | [**researched**](algorithms/koopman-operator-non-linear-volatility-surface-pricing-model.md) |
| 322 | Order-Book Imbalance Signal | Market microstructure / alpha | 330 | 9811 | Research code | RK322, C-MS2 | [**researched**](algorithms/order-book-imbalance-signal.md) |
| 323 | Physics-Informed Neural Operator (FNO) Yield Curve Dynamics | Physics-informed ML / Fourier Neural Operators / Fixed income | 280 | 188 | No | RK323 | [**researched**](algorithms/physics-informed-neural-operator-fno-yield-curve-dynamics.md) |
| 324 | Wasserstein Distributionally Robust Neural SDE Hedging | Robust statistics / Neural SDEs / Derivatives hedging | 338 | 287 | No | RK324 | [**researched**](algorithms/wasserstein-distributionally-robust-neural-sde-hedging.md) |
| 325 | Neural Operator Controlled Portfolio Dynamic Hedging | Neural operators / Stochastic control / Derivatives hedging | 293 | 289 | No | RK325 | [**researched**](algorithms/neural-operator-controlled-portfolio-dynamic-hedging.md) |
| 326 | Neural Operator Functional Gradient Boosting Cross-Sectional Alpha | Neural operators / Functional data analysis / Quantitative equity | 319 | 172 | No | RK326 | [**researched**](algorithms/neural-operator-functional-gradient-boosting-cross-sectional-alpha.md) |
| 327 | Domain-Adversarial Neural Network (DANN) Cross-Market Alpha Transfer | Domain adaptation / Transfer learning / Quantitative equity | 282 | 26 | No | RK327 | [**researched**](algorithms/domain-adversarial-neural-network-dann-cross-market-alpha-transfer.md) |
| 328 | Neural Rough Volatility Path Signature Factor Model | Rough path theory / Signature methods / Quantitative equity | 309 | 961 | No | RK328 | [**researched**](algorithms/neural-rough-volatility-path-signature-factor-model.md) |
| 329 | Wasserstein Distributionally Robust Neural Rough Volatility Hedging | Robust statistics / Rough path theory / Derivatives hedging | 288 | 299 | No | RK329 | [**researched**](algorithms/wasserstein-distributionally-robust-neural-rough-volatility-hedging.md) |
| 330 | Neural Rough Path Signature Delay-Differential Portfolio Control | Rough path theory / Delay differential equations / Portfolio control | 251 | 278 | No | RK330 | [**researched**](algorithms/neural-rough-path-signature-delay-differential-portfolio-control.md) |
| 331 | Neural Rough Differential Equation (Neural RDE) LOB Forecaster | Rough path theory / Deep learning / Microstructure | 986 | 10282 | No | RK331 | [**researched**](algorithms/neural-rough-differential-equation-neural-rde-lob-forecaster.md) |
| 332 | Generative Score-Based Flow Matching Order Flow Generator | Generative machine learning / Flow matching / Microstructure | 9256 | 10333 | No | RK332 | [**researched**](algorithms/generative-score-based-flow-matching-order-flow-generator.md) |
| 333 | Neural Jump-Diffusion Hawkes Point Process Shock Detector | Point process / Neural SDEs / Market microstructure | 1876 | 7558 | No | RK333 | [**researched**](algorithms/neural-jump-diffusion-hawkes-point-process-shock-detector.md) |
| 334 | Neural Controlled Differential Equation LOB Trend Anticipator | Rough path theory / Neural CDEs / Microstructure | 382 | 10444 | No | RK334 | [**researched**](algorithms/neural-controlled-differential-equation-lob-trend-anticipator.md) |
| 335 | Wasserstein Distributionally Robust RL Market Making | Reinforcement learning / Robust statistics / Market making | 2038 | 10229 | No | RK335 | [**researched**](algorithms/wasserstein-distributionally-robust-rl-market-making.md) |
| 336 | Score-Based Generative Diffusion Limit Order Book Simulator | Generative AI / Diffusion models / Market microstructure | 5370 | 10335 | No | RK336 | [**researched**](algorithms/score-based-generative-diffusion-limit-order-book-simulator.md) |
| 337 | Neural Controlled Jump Diffusion Order Book Pricing Model | Neural CDEs / Jump diffusion / Microstructure | 3189 | 9359 | No | RK337 | [**researched**](algorithms/neural-controlled-jump-diffusion-order-book-pricing-model.md) |
| 338 | Recurrent Neural Hawkes Point Process Liquidity Shock Detector | Point processes / Recurrent neural networks / Microstructure | 693 | 10231 | No | RK338 | [**researched**](algorithms/recurrent-neural-hawkes-point-process-liquidity-shock-detector.md) |
| 339 | Multi-Agent Reinforcement Learning Nash Market Maker | Multi-agent reinforcement learning / Game theory / Market making | 987 | 10336 | No | RK339 | [**researched**](algorithms/multi-agent-reinforcement-learning-nash-market-maker.md) |
| 340 | Fractional Order Cointegration Vector Error Correction Neural Network | Fractional time series / Neural networks / Cointegration | 284 | 232 | No | RK340 | [**researched**](algorithms/fractional-order-cointegration-vector-error-correction-neural-network.md) |
| 341 | Multi-Agent Reinforcement Learning Stackelberg Market Maker | Multi-agent reinforcement learning / Game theory / Market making | 988 | 10338 | No | RK341 | [**researched**](algorithms/multi-agent-reinforcement-learning-stackelberg-market-maker.md) |
| 342 | Neural Rough Path Signature Hawkes Point Process Forecaster | Rough path theory / Point processes / Microstructure | 990 | 10448 | No | RK342 | [**researched**](algorithms/neural-rough-path-signature-hawkes-point-process-forecaster.md) |
| 343 | Generative Score-Based Diffusion Limit Order Book Flow Synthesizer | Generative AI / Diffusion models / Microstructure | 700 | 7429 | No | RK343 | [**researched**](algorithms/generative-score-based-diffusion-limit-order-book-flow-synthesizer.md) |
| 344 | Multi-Agent Reinforcement Learning Stackelberg Market Maker Equilibrium | Multi-agent reinforcement learning / Game theory / Market making | 991 | 10341 | No | RK344 | [**researched**](algorithms/multi-agent-reinforcement-learning-stackelberg-market-maker-equilibrium.md) |
| 345 | Multi-Agent Reinforcement Learning Stackelberg Spread Capture | Multi-agent reinforcement learning / Game theory / Market making | 993 | 10343 | No | RK345 | [**researched**](algorithms/multi-agent-reinforcement-learning-stackelberg-spread-capture.md) |
| 346 | SAC Continuous-Action Trading Agent | Reinforcement learning | 166 | 256 | Research code | RK346, A1 | [**researched**](algorithms/sac-continuous-action-trading-agent.md) |
| 347 | DDPG / TD3 Continuous-Control Trader | Reinforcement learning | 256 | 247 | Research code | RK347, A1 | [**researched**](algorithms/ddpg-td3-continuous-control-trader.md) |
| 348 | Phase Space Reconstructed Neural ODE (PSR-NODE) | Continuous-time deep learning / Physics-informed ML | 375 | 10218 | No | RK348 | [**researched**](algorithms/phase-space-reconstructed-neural-ode-psr-node.md) |
| 349 | Time-Series Generative Adversarial Network (TimeGAN) | Generative machine learning / Data augmentation | 314 | 268 | No | RK349 | [**researched**](algorithms/time-series-generative-adversarial-network-timegan.md) |
| 350 | Physics-Informed Deep Learning Schrödinger Volatility Solver | Physics-informed neural networks (PINN) / Derivatives pricing | 697 | 10223 | No | RK350 | [**researched**](algorithms/physics-informed-deep-learning-schrodinger-volatility-solver.md) |
| 351 | Multi-Agent Deep Deterministic Policy Gradient (MADDPG) Portfolio Allocation | Reinforcement learning / Multi-agent allocation | 308 | 140 | No | RK351 | [**researched**](algorithms/multi-agent-deep-deterministic-policy-gradient-maddpg-portfolio-allocation.md) |
| 352 | Deep Hedging with Transaction Costs and Friction | Deep reinforcement learning / Derivatives hedging | 357 | 282 | No | RK352 | [**researched**](algorithms/deep-hedging-with-transaction-costs-and-friction.md) |
| 353 | Recurrent Neural Hawkes Point Process Execution Timing | Point processes / Recurrent neural networks / Execution | 1879 | 10337 | No | RK353 | [**researched**](algorithms/recurrent-neural-hawkes-point-process-execution-timing.md) |
| 354 | Multi-Agent Reinforcement Learning Evolutionary Market Maker | Multi-agent reinforcement learning / Evolutionary algorithms / Market making | 384 | 10232 | No | RK354 | [**researched**](algorithms/multi-agent-reinforcement-learning-evolutionary-market-maker.md) |
| 355 | Recurrent Neural Hawkes Point Process Toxic Flow Execution | Point processes / Recurrent neural networks / Execution | 694 | 10233 | No | RK355 | [**researched**](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-execution.md) |
| 356 | Recurrent Neural Hawkes Point Process Dynamic Inventory Market Maker | Point processes / Recurrent neural networks / Market making | 1880 | 10340 | No | RK356 | [**researched**](algorithms/recurrent-neural-hawkes-point-process-dynamic-inventory-market-maker.md) |
| 357 | Recurrent Neural Hawkes Point Process Toxic Flow Execution Pauser | Point processes / Recurrent neural networks / Execution | 695 | 10234 | No | RK357 | [**researched**](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-execution-pauser.md) |
| 358 | Multi-Agent Reinforcement Learning Evolutionary Execution Routing | Multi-agent reinforcement learning / Evolutionary algorithms / Execution | 385 | 10235 | No | RK358 | [**researched**](algorithms/multi-agent-reinforcement-learning-evolutionary-execution-routing.md) |
| 359 | Multi-Agent Reinforcement Learning Evolutionary Market Making Equilibrium | Multi-agent reinforcement learning / Evolutionary algorithms / Market making | 386 | 10236 | No | RK359 | [**researched**](algorithms/multi-agent-reinforcement-learning-evolutionary-market-making-equilibrium.md) |
| 360 | Multi-Agent Reinforcement Learning Evolutionary Execution Allocator | Multi-agent reinforcement learning / Evolutionary algorithms / Execution | 387 | 10237 | No | RK360 | [**researched**](algorithms/multi-agent-reinforcement-learning-evolutionary-execution-allocator.md) |
| 361 | Deep Reinforcement Learning Order Book Market Maker (Marl-MM) | Multi-agent reinforcement learning / Market making | 381 | 10226 | No | RK361 | [**researched**](algorithms/deep-reinforcement-learning-order-book-market-maker-marl-mm.md) |
| 362 | Koopman Operator Model Predictive Control Execution | Operator theory / Model predictive control / Execution | 345 | 7426 | No | RK362 | [**researched**](algorithms/koopman-operator-model-predictive-control-execution.md) |
| 363 | TWAP Execution | Execution / market microstructure | 301 | 5928 | Research code | RK363 | [**researched**](algorithms/twap-execution.md) |
| 364 | VWAP Execution | Execution / market microstructure | 329 | 10281 | No | RK364 | [**researched**](algorithms/vwap-execution.md) |
| 365 | POV / Percent-of-Volume Execution | Execution / market microstructure | 339 | 5929 | No | RK365 | [**researched**](algorithms/pov-percent-of-volume-execution.md) |
| 366 | Implementation-Shortfall / Almgren–Chriss | Execution / market microstructure | 224 | 9810 | Research code | RK366 | [**researched**](algorithms/implementation-shortfall-almgren-chriss.md) |
| 367 | Hawkes-Driven Optimal Execution with Transitory Price Impact | Market microstructure / Optimal execution | 372 | 10331 | No | RK367 | [**researched**](algorithms/hawkes-driven-optimal-execution-with-transitory-price-impact.md) |
| 368 | Continuous-Time Mean-Field Control Execution | Optimal execution / Mean-field games | 690 | 2120 | No | RK368 | [**researched**](algorithms/continuous-time-mean-field-control-execution.md) |
| 369 | Multi-Agent Mean-Field Game Optimal Execution Routing | Mean-field games / Execution routing / Optimal execution | 692 | 7427 | No | RK369 | [**researched**](algorithms/multi-agent-mean-field-game-optimal-execution-routing.md) |
| 370 | Wasserstein Distributionally Robust Optimal Execution Trajectory | Robust statistics / Optimal execution / Institutional execution | 348 | 10164 | No | RK370 | [**researched**](algorithms/wasserstein-distributionally-robust-optimal-execution-trajectory.md) |
| 371 | Wasserstein Distributionally Robust Hawkes Point Process Execution | Robust statistics / Point processes / Optimal execution | 989 | 10339 | No | RK371 | [**researched**](algorithms/wasserstein-distributionally-robust-hawkes-point-process-execution.md) |
| 372 | PPO Reinforcement-Learning Trader | Reinforcement learning | 276 | 255 | Research code | RK372, A1 | [**researched**](algorithms/ppo-reinforcement-learning-trader.md) |
| 373 | Generative Moment Matching Network (GMMN) Portfolio Simulator | Generative Machine Learning / Portfolio Stress Testing | 215 | 166 | No | RK373 | [**researched**](algorithms/generative-moment-matching-network-gmmn-portfolio-simulator.md) |
| 374 | Physics-Informed Neural Network (PINN) Burgers Volatility Model | Physics-Informed Deep Learning / Derivatives | 216 | 270 | No | RK374 | [**researched**](algorithms/physics-informed-neural-network-pinn-burgers-volatility-model.md) |
| 375 | Quantum Support Vector Regression (QSVR) Return Predictor | Quantum Machine Learning / Predictive Alpha | 341 | 229 | No | RK375 | [**researched**](algorithms/quantum-support-vector-regression-qsvr-return-predictor.md) |
| 376 | Deep Koopman Operator Market Dynamics Predictor | Operator theory / Deep learning / Dynamical systems | 698 | 10484 | No | RK376 | [**researched**](algorithms/deep-koopman-operator-market-dynamics-predictor.md) |
| 377 | Neural SDE Controlled Stochastic Volatility Arbitrage | Stochastic differential equations / Deep learning | 359 | 425 | No | RK377 | [**researched**](algorithms/neural-sde-controlled-stochastic-volatility-arbitrage.md) |
| 378 | Generative Diffusion Model Trajectory Generator (TabDDPM) | Generative machine learning / Scenario generation | 371 | 10225 | No | RK378 | [**researched**](algorithms/generative-diffusion-model-trajectory-generator-tabddpm.md) |
| 379 | Fractional Brownian Motion (fBm) Volatility Surface Arbitrage | Fractional calculus / Derivatives pricing | 238 | 2121 | No | RK379 | [**researched**](algorithms/fractional-brownian-motion-fbm-volatility-surface-arbitrage.md) |
| 380 | Dynamic Latent Factor Graph Neural Network (FactorGNN) | Graph neural networks / Quantitative equity | 279 | 271 | No | RK380 | [**researched**](algorithms/dynamic-latent-factor-graph-neural-network-factorgnn.md) |
| 381 | Hyperbolic Graph Neural Networks for Stock Pricing | Graph machine learning / Hyperbolic geometry / Quantitative equity | 333 | 272 | No | RK381 | [**researched**](algorithms/hyperbolic-graph-neural-networks-for-stock-pricing.md) |
| 382 | Contractive Autoencoder Latent Factor Anomaly Detection | Deep learning / Contractive autoencoders / Anomaly detection | 354 | 7425 | No | RK382 | [**researched**](algorithms/contractive-autoencoder-latent-factor-anomaly-detection.md) |
| 383 | Conditional Wasserstein GAN-GP Yield Curve Synthesizer | Generative Machine Learning / Fixed Income | 334 | 273 | No | RK383 | [**researched**](algorithms/conditional-wasserstein-gan-gp-yield-curve-synthesizer.md) |
| 384 | Geometric Deep Learning Non-Euclidean Alpha Predictor | Geometric deep learning / Riemannian manifolds / Quantitative equity | 242 | 189 | No | RK384 | [**researched**](algorithms/geometric-deep-learning-non-euclidean-alpha-predictor.md) |
| 385 | Graph Attention Network (GAT) Supply Chain Contagion Stock Predictor | Graph neural networks / Attention mechanisms / Quantitative equity | 179 | 274 | No | RK385 | [**researched**](algorithms/graph-attention-network-gat-supply-chain-contagion-stock-predictor.md) |
| 386 | Information-Theoretic Transfer Entropy Graph Neural Network Alpha Model | Information theory / Graph neural networks / Alpha generation | 335 | 7559 | No | RK386 | [**researched**](algorithms/information-theoretic-transfer-entropy-graph-neural-network-alpha-model.md) |
| 387 | Quantum Kernel-Based SVM Cross-Sectional Alpha Predictor | Quantum machine learning / Support vector machines / Alpha generation | 367 | 230 | No | RK387 | [**researched**](algorithms/quantum-kernel-based-svm-cross-sectional-alpha-predictor.md) |
| 388 | Dynamic Copula-Quantile Regression Neural Network Alpha Model | Econometric copulas / Quantile regression / Deep learning | 243 | 167 | No | RK388 | [**researched**](algorithms/dynamic-copula-quantile-regression-neural-network-alpha-model.md) |
| 389 | Quantum Annealing Entropic Value-at-Risk Portfolio Optimization | Quantum computing / Tail risk optimization | 346 | 231 | No | RK389 | [**researched**](algorithms/quantum-annealing-entropic-value-at-risk-portfolio-optimization.md) |
| 390 | Neural Operator Flow-Matching Cross-Sectional Alpha Forecaster | Neural operators / Generative modeling / Equity alpha | 246 | 111 | No | RK390 | [**researched**](algorithms/neural-operator-flow-matching-cross-sectional-alpha-forecaster.md) |
| 391 | Neural Rough Volatility Fractional signature Deep Hedging | Rough path theory / Neural SDEs / Derivatives hedging | 699 | 10284 | No | RK391 | [**researched**](algorithms/neural-rough-volatility-fractional-signature-deep-hedging.md) |
| 392 | Fractional Order Vector AutoRegressive (VAR) Macro Allocator | Fractional time series / Vector autoregression / Macro strategy | 231 | 34 | No | RK392 | [**researched**](algorithms/fractional-order-vector-autoregressive-var-macro-allocator.md) |
| 393 | Quantum Neural Network (QNN) Volatility Surface Forecaster | Quantum machine learning / Derivatives forecasting | 3190 | 10700 | No | RK393 | [**researched**](algorithms/quantum-neural-network-qnn-volatility-surface-forecaster.md) |
| 394 | Graph Diffusion Convolutional Network Cross-Sectional Alpha | Graph neural networks / Graph diffusion / Quantitative equity | 183 | 275 | No | RK394 | [**researched**](algorithms/graph-diffusion-convolutional-network-cross-sectional-alpha.md) |
| 395 | Generative Score-Based Diffusion Macro Factor Synthesizer | Generative AI / Diffusion models / Macroeconomic factor modeling | 285 | 206 | No | RK395 | [**researched**](algorithms/generative-score-based-diffusion-macro-factor-synthesizer.md) |
| 396 | Riemannian Manifold Metric Graph Diffusion Covariance Estimator | Geometric deep learning / Graph diffusion / Covariance estimation | 267 | 173 | No | RK396 | [**researched**](algorithms/riemannian-manifold-metric-graph-diffusion-covariance-estimator.md) |
| 397 | Quantum Annealing Graph Neural Network Covariance Shrinkage | Quantum computing / Graph neural networks / Covariance estimation | 343 | 294 | No | RK397 | [**researched**](algorithms/quantum-annealing-graph-neural-network-covariance-shrinkage.md) |
| 398 | Persistent Homology Betti-2 Persistence Landscape Macro Contagion | Topological data analysis / Persistence landscapes / Macro risk | 126 | 209 | No | RK398 | [**researched**](algorithms/persistent-homology-betti-2-persistence-landscape-macro-contagion.md) |
| 399 | Generative Score-Based Diffusion Cross-Sectional Factor Synthesizer | Generative AI / Diffusion models / Quantitative equity | 188 | 174 | No | RK399 | [**researched**](algorithms/generative-score-based-diffusion-cross-sectional-factor-synthesizer.md) |
| 400 | Graph Attention Network Riemannian Manifold Covariance Shrinkage | Graph neural networks / Riemannian geometry / Covariance estimation | 270 | 175 | No | RK400 | [**researched**](algorithms/graph-attention-network-riemannian-manifold-covariance-shrinkage.md) |
| 401 | Persistent Homology Betti-1 Cyclical Persistence Landscape Contagion | Topological data analysis / Persistence landscapes / Macro risk | 129 | 212 | No | — | [card](algorithms/persistent-homology-betti-1-cyclical-persistence-landscape-contagion.md) |
| 402 | Generative Score-Based Diffusion Cross-Sectional Alpha Synthesizer | Generative AI / Diffusion models / Quantitative equity | 189 | 176 | No | — | [card](algorithms/generative-score-based-diffusion-cross-sectional-alpha-synthesizer.md) |
| 403 | Persistent Homology Betti-2 Persistence Landscape Macro Fragility | Topological data analysis / Persistence landscapes / Macro risk | 164 | 213 | No | — | [card](algorithms/persistent-homology-betti-2-persistence-landscape-macro-fragility.md) |
| 404 | Graph Attention Network Riemannian Manifold Covariance Diffusion | Graph neural networks / Riemannian geometry / Covariance estimation | 273 | 177 | No | — | [card](algorithms/graph-attention-network-riemannian-manifold-covariance-diffusion.md) |
| 405 | Generative Score-Based Diffusion Cross-Sectional Ranking Synthesizer | Generative AI / Diffusion models / Quantitative equity | 190 | 178 | No | — | [card](algorithms/generative-score-based-diffusion-cross-sectional-ranking-synthesizer.md) |
| 406 | Graph Attention Network Riemannian Manifold Covariance Regularization | Graph neural networks / Riemannian geometry / Covariance estimation | 274 | 179 | No | — | [card](algorithms/graph-attention-network-riemannian-manifold-covariance-regularization.md) |
| 407 | Spiking Neural Network (SNN) Event-Driven Microstructure Scalper | Neuromorphic AI / Event-based trading | 3188 | 10332 | No | — | [card](algorithms/spiking-neural-network-snn-event-driven-microstructure-scalper.md) |
| 408 | Neural Jump ODE (NJ-ODE) High-Frequency Price Predictor | Continuous-Time Deep Learning / Microstructure | 373 | 10224 | No | — | [card](algorithms/neural-jump-ode-nj-ode-high-frequency-price-predictor.md) |
| 409 | Wasserstein Distributionally Robust Koopman Model Predictive Control | Robust statistics / Operator theory / Model predictive control | 232 | 152 | No | — | [card](algorithms/wasserstein-distributionally-robust-koopman-model-predictive-control.md) |
| 410 | Wasserstein Distributionally Robust Neural Operator Optimal Execution | Robust statistics / Neural operators / Optimal execution | 377 | 7430 | No | — | [card](algorithms/wasserstein-distributionally-robust-neural-operator-optimal-execution.md) |
| 411 | Recurrent Neural Hawkes Point Process Dynamic Hedging Scheduler | Point processes / Recurrent neural networks / Derivatives hedging | 1881 | 10497 | No | — | [card](algorithms/recurrent-neural-hawkes-point-process-dynamic-hedging-scheduler.md) |
| 412 | Recurrent Neural Hawkes Point Process Toxic Flow Hedging Allocator | Point processes / Recurrent neural networks / Derivatives hedging | 1883 | 10499 | No | — | [card](algorithms/recurrent-neural-hawkes-point-process-toxic-flow-hedging-allocator.md) |
| 413 | Temporal Fusion Transformer (TFT) Multi-Horizon Price Forecaster | Deep learning / Time-series forecasting | 237 | 238 | No | — | [card](algorithms/temporal-fusion-transformer-tft-multi-horizon-price-forecaster.md) |
| 414 | Attention-Based Recurrent Neural Hawkes Point Process Alpha | Recurrent neural networks / Attention / Point processes | 1878 | 10662 | No | — | [card](algorithms/attention-based-recurrent-neural-hawkes-point-process-alpha.md) |
| 415 | Koopman Operator Model Predictive Control Portfolio Rebalancing | Operator theory / Model predictive control / Portfolio rebalancing | 122 | 202 | No | — | [card](algorithms/koopman-operator-model-predictive-control-portfolio-rebalancing.md) |
| 416 | Koopman Operator Model Predictive Control Dynamic Hedging | Operator theory / Model predictive control / Derivatives hedging | 286 | 295 | No | — | [card](algorithms/koopman-operator-model-predictive-control-dynamic-hedging.md) |
| 417 | Koopman Operator Model Predictive Control Yield Curve Control | Operator theory / Model predictive control / Fixed income | 272 | 214 | No | — | [card](algorithms/koopman-operator-model-predictive-control-yield-curve-control.md) |
| 418 | Koopman Operator Model Predictive Control Spread Hedging | Operator theory / Model predictive control / Derivatives hedging | 289 | 300 | No | — | [card](algorithms/koopman-operator-model-predictive-control-spread-hedging.md) |
| 419 | Reinforcement Learning with Expert Guidance (RLEG) Execution | Reinforcement learning / Optimal execution | 369 | 8378 | No | — | [card](algorithms/reinforcement-learning-with-expert-guidance-rleg-execution.md) |
| 420 | Quantum Annealing Optimal Execution Trajectory Solver | Quantum optimization / Execution | 380 | 8379 | No | — | [card](algorithms/quantum-annealing-optimal-execution-trajectory-solver.md) |
| 421 | Wasserstein Distributionally Robust RL Execution | Reinforcement learning / Robust statistics / Optimal execution | 691 | 7423 | No | — | [card](algorithms/wasserstein-distributionally-robust-rl-execution.md) |
| 422 | Multi-Agent Deep Deterministic Reinforcement Learning Cross-Venue Execution | Reinforcement learning / Multi-agent systems / Optimal execution | 383 | 10228 | No | — | [card](algorithms/multi-agent-deep-deterministic-reinforcement-learning-cross-venue-execution.md) |
| 423 | Multi-Agent Reinforcement Learning Stackelberg Execution Broker | Reinforcement learning / Game theory / Optimal execution | 370 | 7428 | No | — | [card](algorithms/multi-agent-reinforcement-learning-stackelberg-execution-broker.md) |
| 424 | Wasserstein Distributionally Robust Hawkes Jump-Diffusion Optimal Execution | Robust statistics / Point processes / Optimal execution | 992 | 10342 | No | — | [card](algorithms/wasserstein-distributionally-robust-hawkes-jump-diffusion-optimal-execution.md) |
| 425 | Deep Recurrent Attentive Execution Agent (DR-Attn-Exec) | Reinforcement learning / Attention mechanisms / Optimal execution | 5369 | 10334 | No | — | [card](algorithms/deep-recurrent-attentive-execution-agent-dr-attn-exec.md) |

#### Title-reconstructed algorithms

Listed by rank on the pages below; each row links to one of 378 [concept pages](algorithms/concepts/README.md).

| Ranks | Algorithms | Page |
|---|---|---|
| 426–1,425 | 1,000 | [ranks 426–1,425](algorithms/ranked/ranks-00426-01425.md) |
| 1,426–2,425 | 1,000 | [ranks 1,426–2,425](algorithms/ranked/ranks-01426-02425.md) |
| 2,426–3,425 | 1,000 | [ranks 2,426–3,425](algorithms/ranked/ranks-02426-03425.md) |
| 3,426–4,425 | 1,000 | [ranks 3,426–4,425](algorithms/ranked/ranks-03426-04425.md) |
| 4,426–5,425 | 1,000 | [ranks 4,426–5,425](algorithms/ranked/ranks-04426-05425.md) |
| 5,426–6,425 | 1,000 | [ranks 5,426–6,425](algorithms/ranked/ranks-05426-06425.md) |
| 6,426–7,425 | 1,000 | [ranks 6,426–7,425](algorithms/ranked/ranks-06426-07425.md) |
| 7,426–8,425 | 1,000 | [ranks 7,426–8,425](algorithms/ranked/ranks-07426-08425.md) |
| 8,426–9,425 | 1,000 | [ranks 8,426–9,425](algorithms/ranked/ranks-08426-09425.md) |
| 9,426–10,425 | 1,000 | [ranks 9,426–10,425](algorithms/ranked/ranks-09426-10425.md) |
| 10,426–11,425 | 1,000 | [ranks 10,426–11,425](algorithms/ranked/ranks-10426-11425.md) |
| 11,426–12,425 | 1,000 | [ranks 11,426–12,425](algorithms/ranked/ranks-11426-12425.md) |
| 12,426–13,425 | 1,000 | [ranks 12,426–13,425](algorithms/ranked/ranks-12426-13425.md) |
| 13,426–14,225 | 800 | [ranks 13,426–14,225](algorithms/ranked/ranks-13426-14225.md) |

<!-- END ranked list -->

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
