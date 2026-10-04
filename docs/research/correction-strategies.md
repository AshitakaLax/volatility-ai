# Intraday Strategies for Market Corrections — Source Mining & Algorithm Catalog

Oct 3, 2026 · @ashitakalax

## Scope and constraints

Every algorithm below is judged by one question: would it raise return/drawdown for the Volatility-ai TQQQ grid during a market correction, within the platform's standing rules. A correction here means a 10%+ peak-to-trough fall in the Nasdaq-100 (QQQ), roughly three times that in TQQQ and path-dependent (working assumption).

| Standing rule | How it changed the evaluation |
| --- | --- |
| Long-only stocks and ETFs; no shorting, inverse ETFs, options, managed-futures or volatility ETFs (DBMF, KMLM, VIXY ruled out) | Short legs of pairs and stat-arb, two-sided market making and short breakout signals are kept only in long-or-flat form; the only correction hedge is cash or a defensive long |
| Correction sleeve realizes losses only via regime exits (`lots_to_liquidate`), never price stops | Stop-loss rules are recast as regime-exit triggers; a regime filter becomes a prerequisite for any correction sleeve |
| Judged on return/drawdown | Each candidate is rated on whether it adds return or removes drawdown in corrections; sizing and regime layers rank high because they cut drawdown |
| Intraday, minute bars or finer, US stocks and ETFs | Daily-bar evidence is flagged; tick or L2 dependence is noted |
| Multi-lot dynamic grid, sizing engine queried per grid step, ledger never sells a lot at a loss | The grid-compatibility field says what must change |

Verification standard: "verified" means I opened the repo file or paper and confirmed the method or claim exists as described. I did not re-run any backtest; reported returns are the sources' claims.

## Bottom line for corrections

The evidence supports a three-layer correction design more than any single new strategy: a regime layer that decides when TQQQ lots may be liquidated, a grid that slows itself down as volatility rises, and intraday momentum used as a gate on grid buys. None of the 66 records below was tested as a long-only, no-stop intraday sleeve on TQQQ in a correction, so that backtest is yours to build.

- **Intraday momentum is the one family with direct correction evidence.** Sharpe rose with the VIX (about 3.5 above 40) and returns were positive in each of the S&P 500's ten worst quarters since 2008 (M1); first-half-hour predictability is strongest on volatile and recession days (M3). Both results include short trades.
- **Dip-buying pays more in turmoil, but not more per unit of risk** (MR1). Keep the grid, but scale rung spacing and lot size to realized volatility (G3, S1).
- **Volatility targeting is the best-evidenced drawdown reducer:** across 60+ assets since 1926 it thinned the left tail and cut maximum drawdowns (S1).
- **For a 3× product, volatility is what destroys compounding.** A 200-day-SMA leverage switch raised Sharpe from 0.30 to 0.51 over 1928–2015 (R1); a turbulence-index liquidation rule held an RL portfolio's drawdown to −9.7% against −37.1% for the DJIA through March 2020 (R2).
- **A plain grid has roughly zero expected value under a random walk** (G4). Never selling at a loss turns losses into inventory, so inventory growth is the quantity to control (G2, S4, X4).
- **After recent declines, intraday trends are stickier** (low RSI(5) predicted stronger momentum, M1). Widen rungs when oversold rather than tightening them (MR6).
- **Source quality is weak overall:** most code is frictionless, daily or crypto-based, and five priority repos are unmaintained for more than 24 months (see coverage table).

## Source coverage

I reviewed 17 repositories and lists and the brief's starting papers, then followed citations to 18 further papers; 66 algorithm records came out. Five repos have had no commits for more than 24 months. Last-commit dates come from each repo's GitHub commit feed, checked on 3 Oct 2026.

| Source | Last commit | Status | Reviewed | Not opened | Records |
| --- | --- | --- | --- | --- | --- |
| [georgezouq/awesome-ai-in-finance](https://github.com/georgezouq/awesome-ai-in-finance) | 2026-09-08 | Active | Full README from GitHub (the project copy stops at Strategies & Research); Papers and all Strategies & Research subsections | Most linked repos (largely crypto bots and frameworks) | RL1–RL5, R6 (via its papers) |
| [wilsonfreitas/awesome-quant](https://github.com/wilsonfreitas/awesome-quant) | 2026-09-13 | Active | All 253 entries in the five named sections; nearly all are libraries | universal-portfolios, TrendFollowingSystems, goal-based-allocation | ML3, MS1, MS5, R5, R6, X2, S3 (via listed tools) |
| [ihobbang250/Awesome-AI-in-Finance](https://github.com/ihobbang250/Awesome-AI-in-Finance) | 2025-02-27 | Slow | Every paper title (mostly LLM and deep-learning) | All papers | None |
| [brandonhimpfen/awesome-finance](https://github.com/brandonhimpfen/awesome-finance) | 2026-09-06 | Active | Quantitative Finance section (5 framework links) | — | None |
| [paperswithbacktest/awesome-systematic-trading](https://github.com/paperswithbacktest/awesome-systematic-trading) | 2026-09-28 | Active | Replication statistics, 61-strategy table, HFT and ML book lists | Individual strategy pages | E4 (listing only) |
| [stefan-jansen/machine-learning-for-trading](https://github.com/stefan-jansen/machine-learning-for-trading) | 2026-10-03 | Active | README (chapters and nine case studies) | Notebooks | ML1, ML5, ML6, S2, S5, E3 |
| [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) | 2024-04-14 | Unmaintained (29 months) | README and 10 strategy scripts | Options straddle, VIX calculator, quantamental projects | M4–M8, MR3, MR5, MR6 |
| [letianzj/QuantResearch](https://github.com/letianzj/QuantResearch) | 2023-08-26 | Unmaintained (37 months) | README, mean-reversion, HMM and Markov-switching notebooks, 13 backtest scripts | ML and RL notebooks | MR3–MR5, MR7, R3, R4, G5, E2, MS7 |
| [nkaz001/hftbacktest](https://github.com/nkaz001/hftbacktest) | 2025-12-23 | Slow | README and 5 tutorial notebooks | Rust live-trading code | G1–G3, MM1–MM3, MM5, MS2 |
| [jamesmawm/High-Frequency-Trading-Model-with-IB](https://github.com/jamesmawm/High-Frequency-Trading-Model-with-IB) | 2025-05-29 | Slow | README and model code | — | MR8 |
| [huseinzol05/Stock-Prediction-Models](https://github.com/huseinzol05/Stock-Prediction-Models) | 2021-01-05 | Unmaintained (68 months) | README (18 forecasting models, 23 agents) | Notebooks | RL6, G5 |
| [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | 2026-09-28 | Active | README and the ensemble paper | Library code | RL1, RL2, R2 |
| [Albert-Z-Guo/Deep-Reinforcement-Stock-Trading](https://github.com/Albert-Z-Guo/Deep-Reinforcement-Stock-Trading) | 2024-11-06 | Slow (23 months) | README | Code | RL6 |
| [eslazarev/purged-cross-validation](https://github.com/eslazarev/purged-cross-validation) | 2026-10-01 | Active | README | Example notebooks | ML3, ML4 |
| [Rachnog/Advanced-Deep-Trading](https://github.com/Rachnog/Advanced-Deep-Trading) | 2020-11-29 | Unmaintained (70 months) | README and file list | Notebook contents | ML1, ML3–ML5 |
| [deltaray-io/kelly-criterion](https://github.com/deltaray-io/kelly-criterion) | 2019-02-16 | Unmaintained (91 months) | README and code | — | S2 |
| [HasibVortex369/riskkit](https://github.com/HasibVortex369/riskkit) | 2026-07-02 | Active | README, sizing and drawdown code | Framework adapters | R5, S3, S4, S6, X3, X4 |

| Starting paper | What I could verify | Records |
| --- | --- | --- |
| Jiang, Xu & Liang 2017 ([arXiv 1706.10059](https://arxiv.org/abs/1706.10059)) | Abstract: 30-minute crypto backtests | RL3 |
| Huang 2018 ([arXiv 1807.02787](https://arxiv.org/abs/1807.02787v1)) | Abstract and data section: 15-minute FX | RL4 |
| Liu et al. 2020, FinRL ([arXiv 2011.09607](https://arxiv.org/abs/2011.09607)) | Not opened; library README read | RL2 |
| Yang et al. 2020, Ensemble Strategy (SSRN 3690996) | Full paper ([PDF](https://openfin.engineering.columbia.edu/sites/default/files/content/publications/ensemble.pdf)) | RL1, R2 |
| López de Prado, "Ten Financial Applications of Machine Learning" (SSRN 3197726) | Not opened (slide deck) | — |
| Avellaneda & Stoikov; Guéant–Lehalle–Fernandez-Tapia | Formulas verified through the hftbacktest tutorial; originals not opened | MM1, MM2 |
| López de Prado: triple barrier, meta-labeling, purged CV, DSR, PBO | DSR and PBO publication records verified; the book itself not opened | ML1–ML4 |

## Catalog — Mean reversion

Mean reversion is what the grid already harvests, and the evidence says its payoff per trade rises in corrections while its risk rises about as fast. Nagel finds liquidity-provision returns spike with the VIX; Collin-Dufresne and Daniel find the Sharpe ratio does not improve once the strategy's own volatility is controlled. The practical reading: keep buying dips in corrections, but size and space by realized volatility.

### MR1. Short-term reversal as paid liquidity provision (VIX-conditioned)

- **Name and category:** Short-term reversal / liquidity provision — mean reversion.
- **Role:** Sizing and regime input for dip-buying; a basket entry signal in its original form.
- **Core idea:** Buying recent losers and selling recent winners earns a premium for supplying liquidity. That premium is highly predictable with the VIX and spikes in turmoil (Nagel). A counter-study finds about 10% of idiosyncratic shocks reverse with a half-life near 2.4 days even in the 100 largest stocks, but the VIX no longer forecasts the Sharpe ratio after controlling for the strategy's own volatility.
- **Key parameters:** Formation window 1–5 days; exponential decay of past residual returns (half-life about 2.4 days); universe of the 100–500 largest stocks.
- **Data required:** Daily returns in both papers; a market-beta estimate for residuals. Works on minute bars: untested.
- **Asset fit:** Large-cap stocks; Nagel reports even industry-portfolio reversal earns high returns when the VIX is high.
- **Intraday suitability:** Medium. Flag: daily-bar evidence proposed for intraday use.
- **Grid compatibility:** High in spirit, since the grid is a liquidity provider. Use the grid's own trailing realized volatility to widen rung spacing and shrink lot size as volatility rises, rather than switching the grid off. Long-only removes the short leg, so the strategy keeps full market beta in a correction.
- **Source(s):** Nagel, "Evaporating Liquidity", Review of Financial Studies 25(7), 2012 ([NBER w17653](https://nber.org/papers/w17653)); Collin-Dufresne & Daniel, "Liquidity and Return Reversals", working paper, 2014 ([PDF](https://business.columbia.edu/sites/default/files-efs/pubfiles/11568/str1.pdf)).
- **Evidence quality:** Peer-reviewed (Nagel); preliminary working paper (Collin-Dufresne & Daniel). Both long-short and daily.
- **Known failure modes:** No reversal around earnings announcements; efficacy declined over time per literature cited by Collin-Dufresne & Daniel; the long-only leg absorbs the market's fall.
- **Implementation complexity:** Medium.

### MR2. ETF-residual Ornstein-Uhlenbeck stat arb (s-score)

- **Name and category:** Avellaneda-Lee s-score — statistical arbitrage.
- **Role:** Entry and exit signal for single-stock lots measured against their sector ETF.
- **Core idea:** Regress each stock's returns on its sector ETF, model the cumulative residual as an OU process, and standardize it into an s-score. Open long at s < −1.25 and close at s > −0.50; the short side (open at +1.25, close at +0.75) is dropped here.
- **Key parameters:** Estimation window about 60 business days; entry/exit thresholds above; optional trading-time (volume) adjustment.
- **Data required:** Daily bars in the paper. Works on minute bars: untested.
- **Asset fit:** Stocks against sector ETFs (the authors' own examples include EBAY against QQQ).
- **Intraday suitability:** Low–medium. Flag: daily-bar evidence.
- **Grid compatibility:** Could choose which Nasdaq-100 names to ladder during a correction. Long-only leaves the sleeve net long, so it needs a regime gate.
- **Source(s):** Avellaneda & Lee, "Statistical Arbitrage in the US Equities Market", Quantitative Finance 10(7), 2010 ([PDF](https://traders.berkeley.edu/papers/Statistical%20arbitrage%20in%20the%20US%20equities%20market.pdf), [abstract](https://cims.nyu.edu/ams/abstracts/avellaneda.html)); thresholds confirmed in [Avellaneda's lecture slides](https://math.nyu.edu/inmemoriam/avellaneda/Lecture8Risk2011.pdf).
- **Evidence quality:** Peer-reviewed, net of costs, long-short. PCA version Sharpe 1.44 over 1997–2007 but only 0.9 over 2003–2007; volume-adjusted ETF signals reached 1.51 over 2003–2007.
- **Known failure modes:** Performance decay after 2002; crowding; long-only form carries market beta.
- **Implementation complexity:** Medium.

### MR3. Cointegration pairs (Engle-Granger) and Kalman-filter hedge ratio

- **Name and category:** Pairs trading — statistical arbitrage.
- **Role:** Entry signal; in long-only form, a rotation rule between two related holdings.
- **Core idea:** Test two prices for cointegration, standardize the residual spread, and trade when it passes ±1σ. The Kalman version lets the hedge ratio drift over time instead of fixing it.
- **Key parameters:** Threshold 1σ (repo); calibration window; Kalman process and observation noise.
- **Data required:** Daily NVDA/AMD bars for 2013–2014 in je-suis-tm. Works on minute bars: yes, with frequent recalibration.
- **Asset fit:** Both.
- **Intraday suitability:** Medium.
- **Grid compatibility:** Long-only version holds the cheap leg and rotates when the spread flips. TQQQ against QQQ is a poor pair because leverage decay drifts the spread.
- **Source(s):** [je-suis-tm, Pair trading backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/Pair%20trading%20backtest.py); [letianzj/QuantResearch notebooks #10 and #11](https://github.com/letianzj/QuantResearch).
- **Evidence quality:** In-sample only, frictionless, two years of one pair.
- **Known failure modes:** Cointegration breaks in stress (the README itself warns to re-test often); short leg unavailable.
- **Implementation complexity:** Medium.

### MR4. Mean-reversion diagnostics: ADF, Hurst exponent, variance ratio, OU half-life

- **Name and category:** Stationarity and persistence tests — regime classification.
- **Role:** Regime filter deciding grid density.
- **Core idea:** On rolling windows, a Hurst exponent below 0.5, a variance ratio below 1 and a short OU half-life indicate mean reversion; the opposite indicates trend. Run a dense grid in the first state and widen or pause it in the second.
- **Key parameters:** Window length (for example 1–5 days of minute bars); Hurst lags; variance-ratio horizon; half-life from regressing Δprice on lagged price.
- **Data required:** Minute bars are fine.
- **Asset fit:** Both.
- **Intraday suitability:** High as a filter.
- **Grid compatibility:** Direct. Feeds the sizing engine's spacing and pause decisions without realizing losses.
- **Source(s):** [letianzj/QuantResearch, notebooks/mean\_reversion.py](https://github.com/letianzj/QuantResearch/blob/master/notebooks/mean_reversion.py).
- **Evidence quality:** Standard statistical tools; the notebook demonstrates them on daily USD/CAD and reports no trading backtest.
- **Known failure modes:** Noisy, biased estimates on short windows; lags regime changes.
- **Implementation complexity:** Low.

### MR5. Bollinger Band reversion and W-bottom

- **Name and category:** Volatility-band mean reversion — pattern recognition.
- **Role:** Entry signal; band width as a spacing input.
- **Core idea:** Mid band = 20-period moving average, outer bands = ±2 standard deviations. Buy at the lower band or on a W-bottom where the second low holds above the band; exit toward the mid or upper band.
- **Key parameters:** 20 periods, 2σ; pattern search window 75 bars; band-width contraction threshold.
- **Data required:** GBP/USD from histdata in the repo. Works on minute bars: yes.
- **Asset fit:** Both.
- **Intraday suitability:** Medium.
- **Grid compatibility:** Natural: set rung spacing at k·σ so rungs widen automatically as volatility rises.
- **Source(s):** [je-suis-tm, Bollinger Bands Pattern Recognition backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/Bollinger%20Bands%20Pattern%20Recognition%20backtest.py); [QuantResearch backtest/bollinger\_bands.py](https://github.com/letianzj/QuantResearch).
- **Evidence quality:** In-sample only, frictionless.
- **Known failure modes:** "Walking the band" in a falling market triggers repeated buys.
- **Implementation complexity:** Low.

### MR6. RSI oversold/overbought and RSI head-and-shoulders

- **Name and category:** RSI reversion — oscillator.
- **Role:** Entry signal; the basis of your existing RSI-adaptive grid.
- **Core idea:** 14-period RSI below 30 is oversold, above 70 overbought; the pattern variant finds a head-and-shoulders shape on the RSI line itself.
- **Key parameters:** RSI 14; 30/70; pattern window 25 bars; tolerance 0.2.
- **Data required:** Daily Yahoo bars (FCAU 2016–2018) in the repo. Works on minute bars: yes.
- **Asset fit:** Both.
- **Intraday suitability:** Medium. Flag: daily-bar backtest.
- **Grid compatibility:** Already in use. Cross-check from M1: a low prior-day RSI(5) predicted stronger intraday trends, so intraday dip-buying is more likely to be run over after recent declines. In low-RSI states, widen rung spacing rather than tighten it.
- **Source(s):** [je-suis-tm, RSI Pattern Recognition backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/RSI%20Pattern%20Recognition%20backtest.py).
- **Evidence quality:** In-sample only, single stock, frictionless.
- **Known failure modes:** RSI stays oversold through a trending decline.
- **Implementation complexity:** Low.

### MR7. R-Breaker pivot reversal and breakout

- **Name and category:** R-Breaker — intraday support/resistance.
- **Role:** Entry signal; a "failed breakdown" trigger for grid lots.
- **Core idea:** From yesterday's high, low and close: pivot P = (H+L+C)/3, R1 = 2P−L, R2 = P+(H−L), R3 = H+2(P−L), S1 = 2P−H, S2 = P−(H−L), S3 = L−2(H−P). Breakout buy above R3; reversal buy when the day's low has pierced S2 and price then recovers above S1.
- **Key parameters:** The seven levels; the repo hard-codes a stop of 10 price units.
- **Data required:** Prior-day OHLC plus intraday bars. Works on minute bars: yes.
- **Asset fit:** Both (originally commodity futures).
- **Intraday suitability:** High.
- **Grid compatibility:** Good. Use the S2-probe-then-S1-recovery as the condition for re-opening grid buys on a correction day.
- **Source(s):** [letianzj/QuantResearch, backtest/r\_breaker.py](https://github.com/letianzj/QuantResearch) (credits Richard Saidenberg, 1994).
- **Evidence quality:** Code only; no reported results in the repo.
- **Known failure modes:** Fixed levels ignore volatility regime; many false recoveries on trend-down days.
- **Implementation complexity:** Low.

### MR8. Beta and volatility-ratio pairs (IB high-frequency model)

- **Name and category:** Short-window pairs — statistical arbitrage.
- **Role:** Entry signal.
- **Core idea:** On 5-second IB bars resampled to 30 seconds over a 1-hour window, beta = mean(A)/mean(B) and volatility ratio = σA/σB. A ratio above 1 marks an uptrend; trade A when it deviates from beta × price of B.
- **Key parameters:** 1-hour window; 30-second resample.
- **Data required:** 5-second bars or L1 ticks.
- **Asset fit:** Both; needs a highly correlated pair.
- **Intraday suitability:** High.
- **Grid compatibility:** Long-only version buys A only when it is cheap to beta × B.
- **Source(s):** [jamesmawm/High-Frequency-Trading-Model-with-IB, models/hft\_model\_1.py](https://github.com/jamesmawm/High-Frequency-Trading-Model-with-IB).
- **Evidence quality:** Anecdotal; live-trading code with no backtest, and the README says the ported version is unlikely to work as intended.
- **Known failure modes:** Ratio of means is not a hedge ratio; no cointegration test.
- **Implementation complexity:** Medium.

## Catalog — Momentum, trend and breakout

Intraday momentum is the best-documented correction performer in this survey: its edge rises with volatility, and the strongest paper reports positive returns in each of the S&P 500's ten worst quarters since 2008. The caveat for this platform is that those results include short trades; a long-or-flat version is untested.

### M1. Noise-Area intraday momentum ("Beat the Market", Concretum Bands)

- **Name and category:** Noise-Area intraday momentum — momentum/breakout.
- **Role:** Entry signal, trailing exit and volatility sizing in one package; the band can also serve as a regime gate for grid buys.
- **Core idea:** For each minute of the day, average the absolute move from the open over the last 14 sessions (σ). Bands are max(open, prior close)×(1+σ) and min(open, prior close)×(1−σ). Go long above the upper band at HH:00/HH:30 checks, exit below max(upper band, VWAP), flat at close; shares = equity × min(4, 2% / 14-day daily vol) / open.
- **Key parameters:** Lookback 14 days (5–90 tested; 90 had the best Sharpe); volatility multiplier 1 (1.5 best Sharpe); decision interval 30 min; daily vol target 2%; leverage cap 4×.
- **Data required:** 1-minute OHLCV, regular-hours VWAP, daily closes. Works on minute bars: yes (built on them).
- **Asset fit:** Both. Paper uses SPY; the authors' FAQ shows QQQ, liquid large caps and Nasdaq futures (Sharpe 1.23). Needs deep intraday liquidity.
- **Intraday suitability:** High. Sharpe rises with the VIX at the open, to about 3.5 when VIX > 40; a low prior-day RSI(5) (recent decline) predicts higher strategy returns (β = −3.25, p = 0.001).
- **Grid compatibility:** Not a grid; run as a separate long-or-flat sleeve. Its VWAP/band exit can realize a loss, which breaks the regime-exit-only rule unless classed as a regime exit. Best grid use: pause new grid buys while price sits below the lower band (abnormal selling), resume inside the band.
- **Source(s):** Zarattini, Aziz, Barbon, "Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)", SFI Research Paper 24-97, 2024 ([paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content), [IDEAS](https://ideas.repec.org/p/chf/rpseri/rp2497.html)).
- **Evidence quality:** Working paper; in-sample backtest May 2007–Apr 2024 on IQFeed 1-minute data, net of $0.0035/share commission and $0.001 slippage. Reported 19.6% CAGR, Sharpe 1.33, max drawdown 25%; Q4 2008 +16%, Q1 2020 +7%, Q2 2022 +12% (authors' FAQ). Long-only correction results not reported.
- **Known failure modes:** Sharp intraday reversals (a 20 Jan 2022 example lost 2.19% in the base model); 7,668 trades make it cost-sensitive; classic intraday momentum weakened after 2013 outside volatile regimes ([Rosa 2022, J. Futures Markets](https://ideas.repec.org/a/wly/jfutmk/v42y2022i12p2218-2234.html) as cited by the paper).
- **Implementation complexity:** Low–medium.

### M2. Five-minute opening range breakout (ORB) on QQQ/TQQQ and "Stocks in Play"

- **Name and category:** 5-minute ORB — breakout.
- **Role:** Entry signal (plus an ATR stop in the published version).
- **Core idea:** If the first 5-minute bar closes up, buy at the start of the second bar (short if down); exit at the close unless the stop triggers. The Stocks-in-Play variant trades only the 20 highest relative-volume names (price > $5, 14-day ADV ≥ 1M shares, ATR > $0.50, opening relative volume ≥ 100%).
- **Key parameters:** Opening range 5 min (5/15/30/60 tested, 5 strongest); stop 5% of 14-day ATR (TQQQ variant) or 10% ATR (stocks); leverage cap 4×.
- **Data required:** 1- or 5-minute bars, daily ATR, opening-interval relative volume. Works on minute bars: yes.
- **Asset fit:** Both; QQQ/TQQQ directly match this platform's instrument.
- **Intraday suitability:** High. Correction-specific results were not broken out in the sources I opened.
- **Grid compatibility:** Separate sleeve. Long-only means trading only up-opening days. The tight ATR stop is a price stop, so it is not allowed in a correction sleeve; an end-of-day exit would also need to count as a regime exit.
- **Source(s):** Zarattini & Aziz, "Can Day Trading Really Be Profitable?", 2023 ([SSRN 4416622](https://papers.ssrn.com/abstract=4416622)); Zarattini, Barbon & Aziz, "A Profitable Day Trading Strategy for the U.S. Equity Market", 2024 ([SSRN 4729284](https://ssrn.com/abstract=4729284)); rule summary by [CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy).
- **Evidence quality:** In-sample backtest, Jan 2016–Feb 2023, $0.0005/share commission, no spread or slippage modeled. Claimed 1,484% (TQQQ variant) vs 169% buy-and-hold QQQ.
- **Known failure modes:** No spread/slippage; leverage magnifies gap and whipsaw losses; many small stop-outs; unknown performance in a long-only, no-stop form.
- **Implementation complexity:** Low.

### M3. Market intraday momentum (first half-hour predicts last half-hour)

- **Name and category:** Market intraday momentum — time-series momentum.
- **Role:** Entry signal, or a time-of-day gate for grid buys.
- **Core idea:** The return from the prior close to 10:00 ET predicts the 15:30–16:00 return. Long-or-cash version: hold the ETF in the last half-hour only when the first half-hour return is positive.
- **Key parameters:** First window (prior close to 10:00); optional 15:00–15:30 confirmation; optional volatility filter.
- **Data required:** 30-minute returns (aggregated minute bars). Works on minute bars: yes.
- **Asset fit:** ETFs (SPY plus ten other liquid ETFs in the paper).
- **Intraday suitability:** High. Predictability is stronger on volatile, high-volume, recession and major macro-news days.
- **Grid compatibility:** Good as a gate: when the first half-hour is strongly negative, defer new grid buys until after 15:30 to avoid buying into expected late-day continuation.
- **Source(s):** Gao, Han, Li & Zhou, "Market Intraday Momentum", Journal of Financial Economics 129(2), 2018 ([abstract record](https://academicnewsletter.sufe.edu.cn/info/356150), [SSRN 2440866](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)); long-or-cash result summarized by [CXO Advisory](https://cxoadvisory.com/?p=25481).
- **Evidence quality:** Peer-reviewed; SPY 1993–2013. The long-or-cash variant earned about 6.3% a year gross in the 2014 working-paper sample.
- **Known failure modes:** Low R² (about 2%); weaker after 2013 except in volatile regimes (Rosa 2022); one trade per day. Supporting evidence across 16 developed markets finds intraday time-series momentum stronger when volatility is high and liquidity low, in and out of sample ([Li, Sakkas & Urquhart 2022, J. Financial Markets](https://nottingham-repository.worktribe.com/output/5273197)).
- **Implementation complexity:** Low.

### M4. Dual Thrust

- **Name and category:** Dual Thrust — range breakout.
- **Role:** Entry signal; lower threshold usable as a grid-pause gate.
- **Core idea:** Range = max(highest high − lowest close, highest close − lowest low) over N prior days. Upper = open + K1×Range, lower = open − K2×Range; trade the breach, reverse on the opposite breach, flat at close.
- **Key parameters:** N = 4–5 days; K1, K2 roughly 0.2–0.7. The repo uses N = 5 and an even 0.5/0.5 split.
- **Data required:** Minute bars plus daily OHLC. Works on minute bars: yes.
- **Asset fit:** Both; the repo tests GBP/USD.
- **Intraday suitability:** Medium–high.
- **Grid compatibility:** Separate sleeve, or use a lower-threshold breach to pause grid buys for the day.
- **Source(s):** [je-suis-tm/quant-trading, Dual Thrust backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/Dual%20Thrust%20backtest.py); rules referenced to a QuantConnect tutorial linked from the README.
- **Evidence quality:** In-sample only, one FX pair, frictionless by the repo's own statement.
- **Known failure modes:** Whipsaw in choppy high-volatility tape; K values overfit easily.
- **Implementation complexity:** Low.

### M5. London Breakout (pre-open range breakout)

- **Name and category:** London Breakout — opening-range breakout across time zones.
- **Role:** Entry signal.
- **Core idea:** Set thresholds from the high/low of the hour before the London open; trade a breach in the first minutes after the open; exit at a 50 bp target/stop or the session end.
- **Key parameters:** Pre-open window 1 hour; stop/target 0.5% (repo); abnormal-gap filter 1%.
- **Data required:** 1-minute bars. Works on minute bars: yes.
- **Asset fit:** FX in the source. The US-equity analog is a pre-market range breakout, where pre-market liquidity is thin.
- **Intraday suitability:** Medium for US ETFs.
- **Grid compatibility:** Low; relies on price stops.
- **Source(s):** [je-suis-tm/quant-trading, London Breakout backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/London%20Breakout%20backtest.py).
- **Evidence quality:** In-sample, GBP/USD only, frictionless; no equity evidence found.
- **Known failure modes:** Pre-market noise; stop-dependent.
- **Implementation complexity:** Low.

### M6. Parabolic SAR

- **Name and category:** Parabolic stop-and-reverse — trend following.
- **Role:** Exit (profit-only trailing) rather than entry.
- **Core idea:** A trailing level accelerates toward price as the trend extends: SAR(t+1) = SAR(t) + AF×(extreme point − SAR(t)), with AF rising by a step on each new extreme.
- **Key parameters:** AF start 0.02, step 0.02, max 0.2.
- **Data required:** OHLC bars. Works on minute bars: yes, but the repo uses daily Yahoo data.
- **Asset fit:** Both.
- **Intraday suitability:** Medium. Flag: daily-bar backtest proposed for intraday use.
- **Grid compatibility:** Good as a profit-only trail on lots already above their take-profit, letting bear-market rally lots run; never used as a loss stop.
- **Source(s):** [je-suis-tm/quant-trading, Parabolic SAR backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/Parabolic%20SAR%20backtest.py).
- **Evidence quality:** In-sample, single ticker, frictionless.
- **Known failure modes:** Constant flips in ranges.
- **Implementation complexity:** Low.

### M7. Heikin-Ashi trend filter

- **Name and category:** Heikin-Ashi candles — trend filter.
- **Role:** Regime/trend filter.
- **Core idea:** Smoothed candles (HA close = average of OHLC; HA open = average of prior HA open and close) produce longer same-color runs; trade on color changes with body/shadow rules.
- **Key parameters:** Rule set from Quantiacs; repo caps stacked longs at 3.
- **Data required:** OHLC bars; repo uses daily Yahoo data. Works on minute bars: yes.
- **Asset fit:** Both.
- **Intraday suitability:** Low–medium. Flag: daily-bar backtest.
- **Grid compatibility:** Could throttle grid buy size during red-candle runs on 15–30-minute bars.
- **Source(s):** [je-suis-tm/quant-trading, Heikin-Ashi backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/Heikin-Ashi%20backtest.py).
- **Evidence quality:** In-sample only, frictionless.
- **Known failure modes:** Lag; the repo itself warns of slow response in flash crashes.
- **Implementation complexity:** Low.

### M8. MACD and Awesome Oscillator crossovers

- **Name and category:** Moving-average oscillators — trend following.
- **Role:** Entry signal or trend filter.
- **Core idea:** MACD is long when a short moving average of close is above a long one. The Awesome Oscillator uses 5- and 34-period simple averages of the (high+low)/2 midpoint, with a "saucer" rule for faster entries.
- **Key parameters:** User-entered MA lengths (MACD); 5/34 (AO).
- **Data required:** Daily Yahoo bars in the repo. Works on minute bars: yes.
- **Asset fit:** Both.
- **Intraday suitability:** Low. Flag: daily-bar backtest.
- **Grid compatibility:** Usable only as a slow filter on grid aggressiveness.
- **Source(s):** [MACD Oscillator backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/MACD%20Oscillator%20backtest.py), [Awesome Oscillator backtest.py](https://github.com/je-suis-tm/quant-trading/blob/master/Awesome%20Oscillator%20backtest.py).
- **Evidence quality:** In-sample only, frictionless.
- **Known failure modes:** Whipsaw in high-volatility chop, which is typical of corrections.
- **Implementation complexity:** Low.

## Catalog — Grid, scale-in and inventory-aware methods

A plain grid has roughly zero expected value when price follows a random walk, and never selling at a loss does not change that; it converts realized losses into held inventory. In a correction the outcome is decided by how much inventory accumulates before the decline ends. The levers below all attack that: volatility-scaled spacing, inventory skew, recentering rules and scale-in on strength.

### G1. Plain high-frequency grid

- **Name and category:** Fixed-interval grid around the mid — grid.
- **Role:** Execution and entry engine (the baseline your platform already runs).
- **Core idea:** Keep N post-only buy orders below and N sell orders above the mid at a fixed interval, snapped to grid prices, and refresh them on a timer; stop adding buys at a position cap.
- **Key parameters:** Tutorial values: 20 levels, 10-tick interval, 20-tick half spread, max position 5 units, refresh every 100 ms.
- **Data required:** L1 best bid/ask for realistic fills; minute bars only allow fills inferred from bar high/low.
- **Asset fit:** Both; needs tight spreads.
- **Intraday suitability:** High.
- **Grid compatibility:** Baseline. Your ledger differs in that sell rungs exist only for lots whose target is above cost.
- **Source(s):** [hftbacktest tutorial: High-Frequency Grid Trading](https://hftbacktest.readthedocs.io/en/latest/tutorials/High-Frequency%20Grid%20Trading.html) (nkaz001/hftbacktest).
- **Evidence quality:** In-sample tick backtest with latency and queue modeling. Source uses crypto data (Binance futures ETH/USDT) and a 0.005% maker rebate.
- **Known failure modes:** Profitability leans on the maker rebate, which retail US-equity accounts usually do not get; inventory piles up in trends.
- **Implementation complexity:** Medium (fill simulation is the hard part).

### G2. Inventory-skewed grid (Avellaneda-Stoikov reservation price)

- **Name and category:** Inventory skew — inventory-aware grid.
- **Role:** Sizing and spacing rule queried at each grid step.
- **Core idea:** Center the grid on a reservation price r = mid − skew × (position / lot size). As inventory grows, buy rungs move lower and sell rungs move closer, pulling inventory back toward zero.
- **Key parameters:** Skew 1 tick per lot (weak) to 10 (strong) in the tutorial.
- **Data required:** L1 quotes or minute bars.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High, with one change: sell rungs cannot move below each lot's cost, so long-only skew acts mostly on the buy side, widening spacing and shrinking lot size as open lots accumulate. This directly caps correction drawdown.
- **Source(s):** [hftbacktest tutorial (skew section)](https://hftbacktest.readthedocs.io/en/latest/tutorials/High-Frequency%20Grid%20Trading.html); model from [Avellaneda & Stoikov 2008](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf) as linked in the tutorial code.
- **Evidence quality:** Peer-reviewed model; the tutorial shows better risk-adjusted results with skew on crypto data (asset-agnostic technique).
- **Known failure modes:** Strong skew limits participation in V-shaped recoveries.
- **Implementation complexity:** Low.

### G3. Volatility-scaled grid ("simplified GLFT")

- **Name and category:** Volatility-proportional spacing — adaptive grid.
- **Role:** Spacing and sizing.
- **Core idea:** Drop the order-arrival calibration of the full GLFT model and set half-spread, grid step and skew in proportion to short-term volatility of mid-price changes, with a minimum step. Center on the micro-price (bid×askQty + ask×bidQty) / (bidQty + askQty).
- **Key parameters:** Volatility-to-half-spread multiplier, minimum grid step, number of levels, skew, max notional.
- **Data required:** Volatility from minute bars works; the micro-price needs L1 sizes.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Direct. Rungs widen automatically as a correction raises volatility, so the same capital spans a deeper decline before it is fully deployed.
- **Source(s):** [hftbacktest tutorial: Grid Trading — Simplified from GLFT](https://hftbacktest.readthedocs.io/en/latest/tutorials/High-Frequency%20Grid%20Trading%20-%20Simplified%20from%20GLFT.html).
- **Evidence quality:** In-sample tick backtests; crypto data, asset-agnostic technique.
- **Known failure modes:** Volatility estimates lag regime shifts; a calm-period calibration under-spaces the first leg of a selloff.
- **Implementation complexity:** Low.

### G4. Dynamic grid reset (DGT)

- **Name and category:** Recentering grid — adaptive grid.
- **Role:** Grid lifecycle rule.
- **Core idea:** The paper shows a finite traditional grid has essentially zero expected return under simple assumptions, then resets the whole grid around the current price whenever price leaves the grid range instead of stopping.
- **Key parameters:** Grid count, grid size, reset trigger at the range boundary.
- **Data required:** Minute bars.
- **Asset fit:** Source is crypto (BTC, ETH); the mechanism is asset-agnostic.
- **Intraday suitability:** High.
- **Grid compatibility:** Compatible with the no-loss ledger, but a downside reset adds buy rungs below held lots, which is averaging down; pair it with G2/G3 and a regime gate.
- **Source(s):** Chen, Chen & Jang, "Dynamic Grid Trading Strategy: From Zero Expectation to Market Outperformance", 2025 ([arXiv 2506.11921](https://arxiv.org/abs/2506.11921v1), [IDEAS](https://ideas.repec.org/p/arx/papers/2506.11921.html)).
- **Evidence quality:** Preprint; in-sample minute backtest Jan 2021–Jul 2024 on crypto, reporting better IRR and risk control than a static grid and buy-and-hold.
- **Known failure modes:** Crypto-specific volatility; downside resets can compound inventory in a persistent decline.
- **Implementation complexity:** Low.

### G5. Turtle ATR-unit pyramiding (scale in on strength)

- **Name and category:** Turtle breakout with pyramiding — scale-in.
- **Role:** Sizing and scale-in rule; useful as a recovery-mode rebuild after a regime exit.
- **Core idea:** Enter on a 20-day high; add one unit for each +0.5 ATR up to three adds. One unit = 1% of equity / ATR; exit at −2 ATR or a 10-day low.
- **Key parameters:** 20-day entry, 10-day exit, 0.5-ATR add step, 3 adds, 1% risk per unit.
- **Data required:** Daily bars in the repo. Works on minute bars: yes, with intraday ATR.
- **Asset fit:** Both.
- **Intraday suitability:** Low–medium. Flag: daily-bar code.
- **Grid compatibility:** The mirror image of a grid. After a correction exit, rebuild TQQQ inventory as price confirms rather than catching the low. The 2-ATR stop is a price stop and would have to become a regime exit.
- **Source(s):** [letianzj/QuantResearch, backtest/turtle.py](https://github.com/letianzj/QuantResearch); turtle agent in [huseinzol05/Stock-Prediction-Models](https://github.com/huseinzol05/Stock-Prediction-Models).
- **Evidence quality:** Code only; no reported results.
- **Known failure modes:** Whipsaw in bear-market rallies.
- **Implementation complexity:** Low.

### G6. Grid ruin analysis with absorbing barriers

- **Name and category:** Grid as a constrained random walk — risk analysis.
- **Role:** Risk overlay and capacity planning (how many rungs survive a given decline).
- **Core idea:** Treat the grid as a random walk between two absorbing barriers, capital exhaustion and a profit target, and compute the probability of hitting each for a chosen depth and spacing.
- **Key parameters:** Rung count, spacing, capital, target.
- **Data required:** None beyond volatility assumptions.
- **Asset fit:** Both (FX focus in the source).
- **Intraday suitability:** Not applicable (planning tool).
- **Grid compatibility:** High. Size the correction sleeve so that a −30% TQQQ leg cannot exhaust capital before a regime exit fires.
- **Source(s):** Taranto & Khan, "Bi-directional grid absorption barrier constrained stochastic processes with applications in finance and investment", 2020 ([USQ repository listing](https://research.usq.edu.au/item/q5x8w/bi-directional-grid-absorption-barrier-constrained-stochastic-processes-with-applications-in-finance-and-investment)); I saw only the listing and abstract.
- **Evidence quality:** Theoretical; not verified beyond the abstract.
- **Known failure modes:** Random-walk assumption ignores volatility clustering and trends.
- **Implementation complexity:** Low.

## Catalog — Market making and inventory skewing

Market-making models are the most rigorous way to set grid spacing and inventory skew, and they adapt to equities in a long-only form: bids are skewed by inventory, asks exist only for lots above cost. Their weakness in a correction is adverse selection, so they need a toxicity or regime filter on the bid side.

### MM1. Avellaneda-Stoikov optimal quotes

- **Name and category:** Avellaneda-Stoikov model — inventory-aware market making.
- **Role:** Spacing and skew for grid orders.
- **Core idea:** Quote around a reservation price that falls with inventory and risk aversion, r = mid − q·γ·σ²·(T−t), with an optimal spread that widens with volatility and with lower order-arrival intensity. Holding inventory makes the trader quote lower on both sides.
- **Key parameters:** Risk aversion γ, volatility σ, order-arrival decay k, horizon T.
- **Data required:** L1 quotes and trades to calibrate arrival intensity; σ from minute bars.
- **Asset fit:** Both; best on liquid ETFs.
- **Intraday suitability:** High (the finite horizon maps naturally to the trading day).
- **Grid compatibility:** High. Use the reservation-price shift to lower and thin buy rungs as lots accumulate; asks stay at or above each lot's cost.
- **Source(s):** [Avellaneda & Stoikov paper](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf) as linked in the hftbacktest grid code.
- **Evidence quality:** Peer-reviewed theory; empirical results here come only from crypto tutorials.
- **Known failure modes:** Assumes no drift; in a trending decline inventory still builds, only more slowly.
- **Implementation complexity:** Medium.

### MM2. Guéant-Lehalle-Fernandez-Tapia (GLFT) closed-form quotes

- **Name and category:** GLFT asymptotic model — inventory-constrained market making.
- **Role:** Spacing and skew, with no terminal time.
- **Core idea:** Bid depth = half-spread + skew·q and ask depth = half-spread − skew·q, where half-spread = c1 + (Δ/2)·σ·c2 and skew = σ·c2. The constants come from risk aversion and an arrival intensity λ = A·exp(−k·δ) fitted by regressing log arrival counts on quote depth.
- **Key parameters:** γ (the tutorial uses 0.05), Δ = 1, ξ = γ, A and k from calibration, σ from mid-price changes.
- **Data required:** Trade prints and L1 quotes (to measure how deep market orders reach). Minute bars alone cannot calibrate A and k.
- **Asset fit:** Both; the tutorial notes the model suits stocks and spot assets because it needs no terminal time.
- **Intraday suitability:** High.
- **Grid compatibility:** High; it hands the sizing engine a spacing and skew per step. The tutorial's own diagnostic is useful: at its calibrated spread only about 1.86% of market trades per step would fill the quote.
- **Source(s):** [hftbacktest tutorial: GLFT Market Making Model and Grid Trading](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html), implementing equations 4.6–4.7 of Guéant, "Optimal market making" ([arXiv 1605.01862](https://arxiv.org/abs/1605.01862)).
- **Evidence quality:** Peer-reviewed model line; tutorial backtests use crypto data with a maker rebate.
- **Known failure modes:** The exponential intensity fit is poor away from the touch; parameters drift with regime.
- **Implementation complexity:** Medium–high.

### MM3. Alpha-shifted quoting (fair value = mid + a × forecast)

- **Name and category:** Market making with a short-term forecast — market making.
- **Role:** Bid/ask placement.
- **Core idea:** Replace the mid with a fair value that adds a scaled forecast and subtracts an inventory-risk term: reservation = mid + a·forecast − b·(c + volatility)·position. Any intraday signal in this catalog (M1, M3, order-book imbalance) can serve as the forecast.
- **Key parameters:** Forecast weight a, risk weight b, volatility-scaled half-spread.
- **Data required:** Whatever the forecast needs; L1 for placement.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High. It is the cleanest way to merge a momentum gate into the grid: a negative forecast lowers bids instead of switching the grid off.
- **Source(s):** [hftbacktest README quick example](https://github.com/nkaz001/hftbacktest); [Market Making with Alpha — Order Book Imbalance](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html).
- **Evidence quality:** Tutorial backtests on crypto (BTC/ETH, May 2023); asset-agnostic.
- **Known failure modes:** Forecast decay; double-counting inventory risk if the forecast already embeds it.
- **Implementation complexity:** Medium.

### MM4. VPIN flow-toxicity filter

- **Name and category:** Volume-synchronized probability of informed trading — regime filter for liquidity providers.
- **Role:** Regime filter that widens or pauses bids when order flow is toxic.
- **Core idea:** Bucket trades by equal volume, classify buy and sell volume, and average the absolute imbalance over recent buckets. High readings mean market makers are being adversely selected.
- **Key parameters:** Volume bucket size, number of buckets in the window, trade-classification method.
- **Data required:** Trades with volume; bar-level bulk classification is possible but is the very variant critics found weakest.
- **Asset fit:** Both; original work on E-mini futures around the 6 May 2010 flash crash.
- **Intraday suitability:** High.
- **Grid compatibility:** Bid-side gate only; it never forces a sale.
- **Source(s):** Easley, López de Prado & O'Hara, "Flow Toxicity and Liquidity in a High Frequency World", Review of Financial Studies 25(5), 2012 ([SSRN 1695596](https://papers.ssrn.com/abstract=1695596)); critique by Andersen & Bondarenko ([CREATES paper](https://repec.econ.au.dk/repec/creates/rp/13/rp13_43.pdf)); rejoinder in Journal of Financial Markets 17, 2014 ([record](https://opus.lib.uts.edu.au/citation/handle/10453/118180)).
- **Evidence quality:** Peer-reviewed but disputed. Andersen & Bondarenko conclude the bulk-classified version adds no predictive power beyond trading intensity and volatility.
- **Known failure modes:** Sensitive to classification and start point; may just proxy volume and volatility.
- **Implementation complexity:** Medium.

### MM5. Probabilistic queue-position fill models

- **Name and category:** Queue-position modeling — execution and backtest realism.
- **Role:** Execution model for evaluating any limit-order grid.
- **Core idea:** A resting order fills only after the queue ahead of it is consumed. Probability models (for example a power-law weighting) estimate how much of each cancellation came from ahead of you, so backtests stop assuming every touch fills.
- **Key parameters:** Model family (power 2 in the tutorials), latency model.
- **Data required:** L2 depth and trades; not possible with minute bars.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Essential for honest grid backtests; without it, fills on bar lows overstate grid profits, most of all in fast selloffs.
- **Source(s):** [hftbacktest tutorial: Probability Queue Models](https://github.com/nkaz001/hftbacktest/blob/master/examples/Probability%20Queue%20Models.ipynb).
- **Evidence quality:** Tutorial comparisons on crypto data; the repo recommends matching the model to live fills.
- **Known failure modes:** Needs L2 history, which is costly for US equities.
- **Implementation complexity:** High.

## Catalog — Volatility and regime detection

Because losses may be realized only through regime exits, this category decides most of the correction drawdown. Two candidates have direct evidence for exactly that job: a 200-day moving-average leverage switch (volatility is the enemy of leverage) and a turbulence-index liquidation rule that carried an RL portfolio through March 2020. Both are daily signals that would gate an intraday sleeve.

### R1. Moving-average leverage regime ("Leverage for the Long Run")

- **Name and category:** SMA leverage rotation — trend/volatility regime.
- **Role:** Regime filter and the primary `lots_to_liquidate` trigger for a TQQQ sleeve.
- **Core idea:** Hold leverage when the index closes above its moving average and move to T-bills below it. Above the average, forward volatility is lower and positive streaks longer; below it, volatility rises, which is what erodes daily-reset leverage.
- **Key parameters:** 200-day SMA (10-, 20-, 50- and 100-day also tested); leverage 1.25–3×; signal on the unleveraged index (QQQ or the Nasdaq-100 for this platform).
- **Data required:** Daily closes. Works on minute bars: not intended; it gates intraday trading.
- **Asset fit:** Index ETFs and their leveraged versions; T-bill ETFs as the cash leg fit your no-volatility-ETF rule.
- **Intraday suitability:** Low as a signal, high as a gate. Flag: daily-bar evidence.
- **Grid compatibility:** High. A close below the SMA marks TQQQ lots for liquidation and switches the grid to a smaller or unleveraged sleeve; a close back above re-enables it. About five switches a year in the paper's S&P test.
- **Source(s):** Gayed & Bilello, "Leverage for the Long Run", 2016 Charles H. Dow Award paper ([PDF](https://docs.cmtassociation.org/dow-award/2016-gayed-bilello.pdf), [summary](https://cmtassociation.org/?p=47026)); results summarized by [CXO Advisory](https://www.cxoadvisory.com/volatility-effects/leveraging-the-u-s-stock-market-based-on-sma-rules/).
- **Evidence quality:** Industry award paper; long in-sample history (Oct 1928–Oct 2015). 2× above SMA200 / T-bills below gave Sharpe 0.51 against 0.30 for buy-and-hold, assuming 1% annual leverage cost and no switching costs.
- **Known failure modes:** Whipsaw around the average; late exits in fast crashes (the signal is daily); returns overstated by ignoring frictions.
- **Implementation complexity:** Low.

### R2. Financial turbulence index liquidation rule

- **Name and category:** Turbulence (Mahalanobis distance) — stress regime.
- **Role:** Regime exit: halt buys and liquidate when turbulence exceeds a threshold, resume when it falls back.
- **Core idea:** turbulence = (y − μ)ᵀ Σ⁻¹ (y − μ), where y is the current vector of asset returns and μ, Σ are their historical mean and covariance. It spikes when moves are large or break normal correlations.
- **Key parameters:** Asset basket (the paper uses the 30 Dow stocks); history window for μ and Σ; threshold (not stated numerically in the paper, which says lower thresholds mean more risk aversion).
- **Data required:** Daily returns in the paper. Works on minute bars: plausible on 30-minute returns of sector ETFs, untested.
- **Asset fit:** Any basket; for this platform, Nasdaq-100 sector or top-weight constituents.
- **Intraday suitability:** Medium as a gate.
- **Grid compatibility:** High; it is literally a `lots_to_liquidate` rule plus a buy halt.
- **Source(s):** Yang, Liu, Zhong & Walid, "Deep Reinforcement Learning for Automated Stock Trading: An Ensemble Strategy", ICAIF 2020 ([PDF](https://openfin.engineering.columbia.edu/sites/default/files/content/publications/ensemble.pdf)), which takes the index from Kritzman & Li, "Skulls, Financial Turbulence, and Risk Management", Financial Analysts Journal 2010 (cited, not opened).
- **Evidence quality:** Conference paper; daily backtest with 0.1% costs and out-of-sample trading Jan 2016–May 2020. Ensemble max drawdown −9.7% versus −37.1% for the DJIA, credited to the turbulence sell-off in March 2020.
- **Known failure modes:** Threshold is a free parameter chosen in-sample; one crash in the test window; agents kept training during the test period.
- **Implementation complexity:** Low.

### R3. Hidden Markov, Gaussian-mixture and Markov-switching volatility regimes

- **Name and category:** Latent-state models — volatility regime.
- **Role:** Regime filter scaling grid density and lot size.
- **Core idea:** Fit 2–3 hidden states to returns; states separate by volatility (and sometimes drift). Trade the grid fully in the calm state, thin it in the turbulent state.
- **Key parameters:** Number of states (2–3 chosen by AIC/BIC in the notebook); switching variance on.
- **Data required:** Daily S&P 500 returns in the notebooks. Works on minute bars: yes, with intraday seasonality removed first.
- **Asset fit:** Both.
- **Intraday suitability:** Medium.
- **Grid compatibility:** High as a sizing input. As an exit trigger it needs hysteresis to avoid flip-flopping.
- **Source(s):** [letianzj/QuantResearch notebooks #12 (hidden\_markov\_chain.py) and #18 (gaussian\_mixture\_markov\_switching.ipynb)](https://github.com/letianzj/QuantResearch).
- **Evidence quality:** Illustration only. Verified issues: the HMM is fit and decoded on the full sample (look-ahead), and the script computes returns as P(t−1)/P(t) − 1, which flips their sign.
- **Known failure modes:** Label switching between refits; smoothed states leak future information; detection lags the turn.
- **Implementation complexity:** Medium.

### R4. Realized-volatility, ATR and VIX-level gates

- **Name and category:** Volatility level — regime.
- **Role:** Regime filter and sizing input.
- **Core idea:** Trailing realized volatility or ATR sets grid spacing and lot size; the VIX at the open is used as data only (volatility ETFs remain excluded). M1 shows intraday momentum Sharpe rising with the opening VIX, so a high VIX tilts the platform from grid buying toward momentum gating.
- **Key parameters:** ATR 14; 14-day daily vol (M1 sizing); VIX bands (for example below 20, 20–30, above 30).
- **Data required:** Minute and daily bars; a VIX feed.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Direct input to the sizing engine.
- **Source(s):** M1 paper ([PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)); [QuantResearch backtest/dynamic\_breakout\_ii.py](https://github.com/letianzj/QuantResearch) for a volatility-adaptive lookback (20–60 days).
- **Evidence quality:** Indirect: VIX-conditioned results from M1; no stand-alone backtest of the gate.
- **Known failure modes:** VIX is a poor proxy for single-name volatility (see MR1); thresholds drift across eras.
- **Implementation complexity:** Low.

### R5. Drawdown-state regimes

- **Name and category:** Drawdown from high-water mark — regime.
- **Role:** Regime exit and sleeve switch.
- **Core idea:** Classify the market (or the account) by its current drawdown and trend segment: for example QQQ more than 10% below its high marks a correction state. Account-level tiers cut size, raise the entry bar, then halt.
- **Key parameters:** riskkit defaults: size ×0.75 past 3% drawdown, ×0.50 past 5%, ×0.25 past 7%, halt new entries past 10%, with a recovery ramp.
- **Data required:** Daily or intraday equity and price series.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High; this is the drawdown circuit breaker still open on your list. Tiers that only throttle new buys never force a sale; a final tier can trigger `lots_to_liquidate`.
- **Source(s):** [rafa-rod/pytrendseries](https://github.com/rafa-rod/pytrendseries) (trend segments with drawdown/max drawdown); [HasibVortex369/riskkit, drawdown.py](https://github.com/HasibVortex369/riskkit).
- **Evidence quality:** Tools only; no performance evidence.
- **Known failure modes:** Account-drawdown tiers react after losses occur; market-drawdown states lag V-shaped recoveries.
- **Implementation complexity:** Low.

### R6. LPPLS bubble and critical-time detection

- **Name and category:** Log-periodic power law singularity — crash-hazard regime.
- **Role:** Early-warning filter that shrinks lot size before a possible correction.
- **Core idea:** Fit E\[ln p(t)\] = A + B(t\_c − t)^m + C(t\_c − t)^m cos(ω ln(t\_c − t) − φ); a good fit with super-exponential growth flags a bubble and estimates its critical time t\_c.
- **Key parameters:** Fit windows; bounds on m and ω; CMA-ES optimizer settings.
- **Data required:** Daily prices. Works on minute bars: not intended.
- **Asset fit:** Indexes and large ETFs.
- **Intraday suitability:** Low. Flag: daily tool.
- **Grid compatibility:** Medium; a lot-size dampener, not an exit.
- **Source(s):** [Boulder-Investment-Technologies/lppls](https://github.com/Boulder-Investment-Technologies/lppls); Sornette, "Dragon-Kings, Black Swans and the Prediction of Crises" ([arXiv 0907.4290](https://arxiv.org/pdf/0907.4290.pdf), listed in awesome-ai-in-finance).
- **Evidence quality:** Academic method; I did not verify any out-of-sample timing record.
- **Known failure modes:** Unstable fits; many false alarms; t\_c estimates drift.
- **Implementation complexity:** High.

## Catalog — ML signal generation and validation

The most useful ML idea for this platform is not a price forecaster but a meta-model on the grid's own triggers: label each historical grid lot by whether it reached its take-profit before a regime exit, then size new lots by that probability. The validation tools here (purged CV, deflated Sharpe, PBO) matter more than any model, because correction episodes are few and easy to overfit.

### ML1. Triple-barrier and trend-scanning labels

- **Name and category:** Path-dependent labeling — ML labeling.
- **Role:** Training labels for entry or sizing models.
- **Core idea:** Label each entry by the first barrier touched: an upper profit barrier, a lower barrier, or a vertical time limit. For a no-loss grid, set the upper barrier at the lot's take-profit, the lower at the regime-exit level, and the vertical at a maximum hold.
- **Key parameters:** Barrier widths in volatility units (for example 1–3× trailing σ); max holding period.
- **Data required:** Minute bars are sufficient.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High; maps one-to-one onto lot outcomes in your ledger.
- **Source(s):** [stefan-jansen/machine-learning-for-trading, chapter 7](https://github.com/stefan-jansen/machine-learning-for-trading) (forward-return, triple-barrier and trend-scanning labels); [Rachnog/Advanced-Deep-Trading, bars-labels-diff/Labeling.ipynb](https://github.com/Rachnog/Advanced-Deep-Trading).
- **Evidence quality:** Method; no correction-specific results.
- **Known failure modes:** Overlapping labels leak information unless purged (ML3); barrier widths become hidden parameters.
- **Implementation complexity:** Low–medium.

### ML2. Meta-labeling the grid's own triggers

- **Name and category:** Meta-labeling — ML sizing.
- **Role:** Sizing; the natural thing for your sizing engine to query at each grid step.
- **Core idea:** Keep the grid as the primary signal and train a secondary classifier to predict whether a given trigger will succeed (ML1 labels). Use the predicted probability to size or skip the lot. Candidate features: R1/R2 regime states, M1 band position, realized-volatility percentile, time of day, open-lot count.
- **Key parameters:** Model class (gradient boosting is typical), probability-to-size mapping, minimum probability.
- **Data required:** The platform's own historical or simulated grid triggers plus minute features.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Very high; it changes only lot size, never forces a sale.
- **Source(s):** López de Prado, Advances in Financial Machine Learning (2018), listed in [awesome-ai-in-finance](https://github.com/georgezouq/awesome-ai-in-finance) and [awesome-systematic-trading](https://github.com/paperswithbacktest/awesome-systematic-trading); I did not open the book. Its methodology family (information bars, triple barrier, meta-labeling, purged CV, DSR, PBO) is summarized in [this survey page](https://tradingstrategy.ai/docs/learn/backtesting.html).
- **Evidence quality:** Widely used method; no published evidence for grid triggers specifically.
- **Known failure modes:** Few correction episodes means few positive and negative examples in the regime that matters; class imbalance.
- **Implementation complexity:** Medium.

### ML3. Purged k-fold, embargo and combinatorial purged CV (CPCV)

- **Name and category:** Leakage-aware cross-validation — validation.
- **Role:** Model and parameter validation.
- **Core idea:** Drop training rows whose label horizons overlap the test fold (purge), skip a buffer after it (embargo), and in CPCV recombine folds into many backtest paths instead of one.
- **Key parameters:** Number of folds and test groups; embargo length; label horizon.
- **Data required:** Any labeled series with event times.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Use for every parameter of the correction sleeve, especially regime thresholds.
- **Source(s):** [eslazarev/purged-cross-validation](https://github.com/eslazarev/purged-cross-validation) (pip `purgedcv`, scikit-learn compatible, active as of Oct 2026); [Advanced-Deep-Trading, proba\_backtest/Combinatorial Cross Validation.ipynb](https://github.com/Rachnog/Advanced-Deep-Trading).
- **Evidence quality:** Established method; the library is tested and documented.
- **Known failure modes:** CPCV still shares one market history; few corrections per path.
- **Implementation complexity:** Low (library).

### ML4. Deflated Sharpe ratio and probability of backtest overfitting

- **Name and category:** Multiple-testing corrections — validation.
- **Role:** Strategy selection gate.
- **Core idea:** DSR deflates a Sharpe ratio for the number of trials and for skew and kurtosis. PBO uses combinatorially symmetric cross-validation to estimate how often the in-sample winner ranks below median out of sample.
- **Key parameters:** Number of trials tried; CSCV partition count.
- **Data required:** Return series of every configuration tested.
- **Asset fit:** Both.
- **Intraday suitability:** Not applicable (evaluation).
- **Grid compatibility:** Use before promoting any grid parameter set to live.
- **Source(s):** Bailey & López de Prado, "The Deflated Sharpe Ratio", Journal of Portfolio Management 40(5), 2014 ([SSRN 2460551](https://papers.ssrn.com/abstract=2460551)); Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting", Journal of Computational Finance 20(4) ([SSRN 2326253](https://papers.ssrn.com/abstract=2326253)); [Advanced-Deep-Trading, backtest\_veroft/Overfit Probability.ipynb](https://github.com/Rachnog/Advanced-Deep-Trading).
- **Evidence quality:** Peer-reviewed.
- **Known failure modes:** Requires an honest count of all trials, including abandoned ones.
- **Implementation complexity:** Low.

### ML5. Information-driven bars and fractional differentiation

- **Name and category:** Sampling and stationarity transforms — feature engineering.
- **Role:** Data preparation for every intraday model.
- **Core idea:** Sample bars by volume, dollar value or order-flow imbalance instead of clock time, so a selloff with heavy volume yields more bars. Fractional differentiation makes prices stationary while keeping more memory than returns.
- **Key parameters:** Bar threshold (for example a fixed dollar value per bar); differentiation order d (roughly 0.3–0.6).
- **Data required:** Trades, or minute bars with volume as an approximation.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Medium; activity-based bars raise resolution exactly during corrections.
- **Source(s):** [Advanced-Deep-Trading, bars-labels-diff](https://github.com/Rachnog/Advanced-Deep-Trading); [ML4T chapter 3](https://github.com/stefan-jansen/machine-learning-for-trading) (bar-sampling comparison); [twowaymind/orderflow-metrics](https://github.com/twowaymind/orderflow-metrics).
- **Evidence quality:** Method; Advanced-Deep-Trading has no commits since Nov 2020 (unmaintained).
- **Known failure modes:** Dollar bars from minute data are only approximate; d chosen in-sample.
- **Implementation complexity:** Low.

### ML6. Gradient boosting on intraday microstructure features

- **Name and category:** Supervised tabular models — ML signal generation.
- **Role:** Entry signal or meta-model (ML2).
- **Core idea:** Train XGBoost/LightGBM/CatBoost on engineered intraday features with purged walk-forward CV and cost-aware evaluation. ML4T's NASDAQ-100 case study builds 15-minute signals from order flow and the limit order book.
- **Key parameters:** Feature windows; label horizon; tuning budget.
- **Data required:** 15-minute bars plus order-flow/LOB features in the case study; NASDAQ ITCH parsing in chapter 3.
- **Asset fit:** Stocks (Nasdaq-100 constituents), directly relevant to QQQ.
- **Intraday suitability:** High.
- **Grid compatibility:** Best as ML2's meta-model rather than a standalone signal.
- **Source(s):** [stefan-jansen/machine-learning-for-trading](https://github.com/stefan-jansen/machine-learning-for-trading) (chapters 3, 7, 12, 16–19; NASDAQ-100 microstructure case study). I read the README only, not the notebooks.
- **Evidence quality:** Book case study; not verified beyond the README's description.
- **Known failure modes:** Edge consumed by costs at 15-minute horizons; regime dependence.
- **Implementation complexity:** High.

## Catalog — Reinforcement learning

None of the RL sources tests US equities intraday, and the strongest correction result in this category comes from a hand-written turbulence rule rather than from the learned policy. The transferable pieces are that rule, a return/drawdown-style reward, and "action augmentation" for evaluating sizing choices without exploration.

### RL1. Turbulence-gated actor-critic ensemble (FinRL, ICAIF 2020)

- **Name and category:** PPO/A2C/DDPG ensemble with turbulence override — deep RL.
- **Role:** Allocation policy; its turbulence override is the reusable regime exit (see R2).
- **Core idea:** Retrain three agents every quarter on a growing window, pick the one with the best validation Sharpe for the next quarter, and override all agents with a sell-everything rule when turbulence exceeds a threshold.
- **Key parameters:** 3-month retrain and validation windows; 0.1% cost per trade; state of prices, holdings and MACD/RSI/CCI/ADX.
- **Data required:** Daily bars (Dow 30, 2009–May 2020). Works on minute bars: not tested.
- **Asset fit:** Stocks.
- **Intraday suitability:** Low. Flag: daily-bar evidence.
- **Grid compatibility:** Low for the agents; high for the turbulence override.
- **Source(s):** [Yang, Liu, Zhong & Walid 2020 (PDF)](https://openfin.engineering.columbia.edu/sites/default/files/content/publications/ensemble.pdf); [arXiv record](https://arxiv.org/abs/2511.12120v1).
- **Evidence quality:** Conference paper with an out-of-sample period (2016–May 2020): ensemble Sharpe 1.30 and max drawdown −9.7% versus 0.47 and −37.1% for the DJIA.
- **Known failure modes:** Model selection on 3-month Sharpe is noisy (validation Sharpes from −0.42 to 0.71); agents kept training during the test; one crash.
- **Implementation complexity:** High.

### RL2. FinRL library agents (A2C, DDPG, PPO, SAC, TD3)

- **Name and category:** DRL agent suite — deep RL.
- **Role:** Research framework for allocation and timing policies.
- **Core idea:** Gym-style environments with Stable-Baselines3 agents; the default pipeline adds technical indicators, the VIX and the turbulence index to the state.
- **Key parameters:** Agent choice, reward, train/trade split (README example trains on 2014–2025 Dow 30 data).
- **Data required:** Daily Yahoo data by default; the README lists minute-level sources (Binance) and TAQ via WRDS.
- **Asset fit:** Stocks, ETFs, crypto.
- **Intraday suitability:** Low–medium.
- **Grid compatibility:** Low; a sizing-policy experiment at most.
- **Source(s):** [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) (active, last commit Sep 2026); Liu et al., [arXiv 2011.09607](https://arxiv.org/abs/2011.09607).
- **Evidence quality:** In-sample/out-of-sample daily backtests from the authors.
- **Known failure modes:** Overfitting, seed sensitivity, daily-close fills.
- **Implementation complexity:** High.

### RL3. EIIE portfolio policy ("Deep Portfolio Management")

- **Name and category:** Ensemble of identical independent evaluators — deep RL portfolio management.
- **Role:** Rotation weights across a small ETF set.
- **Core idea:** One small network scores each asset independently from its recent price window plus last period's weight; a softmax turns the scores into portfolio weights, trained by online stochastic batch learning.
- **Key parameters:** CNN, RNN or LSTM evaluator; 30-minute rebalance; window length.
- **Data required:** 30-minute bars.
- **Asset fit:** Source uses cryptocurrency data; the technique is asset-agnostic.
- **Intraday suitability:** Medium.
- **Grid compatibility:** Low; it rebalances whole positions.
- **Source(s):** Jiang, Xu & Liang, "A Deep Reinforcement Learning Framework for the Financial Portfolio Management Problem", 2017 ([arXiv 1706.10059](https://arxiv.org/abs/1706.10059)).
- **Evidence quality:** Preprint; three crypto backtests.
- **Known failure modes:** Crypto-era momentum; turnover costs.
- **Implementation complexity:** High.

### RL4. Deep recurrent Q-network with action augmentation

- **Name and category:** DRQN — deep RL.
- **Role:** Entry/exit policy; the augmentation trick suits sizing research.
- **Core idea:** Because a small trader's orders do not move prices, the reward for every possible action can be computed at each step. Feeding all of them back removes the need for random exploration; the paper also uses a tiny replay memory and long training sequences.
- **Key parameters:** Replay memory of a few hundred transitions; sequence length; training every T steps.
- **Data required:** 15-minute bars from TrueFX tick data, 2012–2017.
- **Asset fit:** Source uses FX; technique is asset-agnostic.
- **Intraday suitability:** Medium–high.
- **Grid compatibility:** Medium. The same no-impact assumption lets you score every candidate lot size at each historical grid trigger and train a sizing policy without exploration.
- **Source(s):** Huang, "Financial Trading as a Game: A Deep Reinforcement Learning Approach", 2018 ([arXiv 1807.02787](https://arxiv.org/abs/1807.02787v1)).
- **Evidence quality:** Preprint; FX only.
- **Known failure modes:** The no-impact assumption breaks for larger lots and in thin markets.
- **Implementation complexity:** High.

### RL5. Direct reinforcement with a risk-adjusted online reward

- **Name and category:** Recurrent direct reinforcement — RL objective.
- **Role:** Objective function for any learned sizing policy.
- **Core idea:** Optimize trading decisions directly against an incrementally updated risk-adjusted performance measure, rather than forecasting prices; the risk-averse case is handled through the reward choice.
- **Key parameters:** Reward definition (for this platform, return/drawdown).
- **Data required:** Any frequency.
- **Asset fit:** Both.
- **Intraday suitability:** Medium.
- **Grid compatibility:** Medium; use a return/drawdown reward so the learner optimizes your actual metric.
- **Source(s):** Moody & Saffell, "Learning to trade via direct reinforcement", IEEE Transactions on Neural Networks 12, 2001 (cited in the RL1 paper); "Reinforcement Learning for Trading" ([NIPS paper link](http://papers.nips.cc/paper/1551-reinforcement-learning-for-trading.pdf)) and Ritter, "Machine Learning for Trading" ([PDF](https://cims.nyu.edu/~ritter/ritter2017machine.pdf)), both listed in awesome-ai-in-finance. I did not open these.
- **Evidence quality:** Peer-reviewed (Moody & Saffell); not verified here beyond citations and list descriptions.
- **Known failure modes:** Sparse correction data; reward hacking.
- **Implementation complexity:** Medium–high.

### RL6. Single-asset DQN/DDPG and evolution-strategy agents

- **Name and category:** Educational trading agents — deep RL.
- **Role:** None recommended beyond experimentation.
- **Core idea:** Buy/hold/sell agents on one daily series; Stock-Prediction-Models adds turtle, moving-average, Q-learning, policy-gradient and evolution-strategy agents.
- **Key parameters:** 10-day observation window, 10 episodes (Albert-Z-Guo defaults).
- **Data required:** Daily closes.
- **Asset fit:** Stocks.
- **Intraday suitability:** Low. Flag: daily-bar code.
- **Grid compatibility:** Low.
- **Source(s):** [Albert-Z-Guo/Deep-Reinforcement-Stock-Trading](https://github.com/Albert-Z-Guo/Deep-Reinforcement-Stock-Trading); [huseinzol05/Stock-Prediction-Models](https://github.com/huseinzol05/Stock-Prediction-Models).
- **Evidence quality:** Anecdotal. Albert-Z-Guo's README states no transaction costs, fills at the close and no short selling; Stock-Prediction-Models has had no commits since Jan 2021.
- **Known failure modes:** Overfitting, no costs, local optima noted by the author.
- **Implementation complexity:** Medium.

## Catalog — Position sizing

Volatility targeting is the best-evidenced drawdown reducer in the whole survey: across 60+ assets since 1926 it thinned the left tail and cut maximum drawdowns, because large losses cluster in high-volatility periods when a vol-targeted book is small. For a grid queried at every step, that translates into lot size scaled down by trailing volatility and by open inventory.

### S1. Volatility targeting

- **Name and category:** Inverse-volatility exposure scaling — sizing.
- **Role:** Sizing at each grid step and for every sleeve.
- **Core idea:** Exposure = target vol / forecast vol, capped. M1 uses shares = equity × min(4, 2% / trailing 14-day daily vol) / open; the cross-asset study targets 10% annualized with exponentially weighted realized vol.
- **Key parameters:** Vol target; estimator half-life; leverage cap.
- **Data required:** Daily or intraday returns (intraday measures were a robustness check in the study).
- **Asset fit:** Both; the Sharpe gain is specific to risk assets such as equities.
- **Intraday suitability:** High.
- **Grid compatibility:** Direct: lot size ∝ target / realized vol, so a correction automatically shrinks new lots. It never forces a sale.
- **Source(s):** Harvey, Hoyle, Korgaonkar, Rattray, Sargaison & Van Hemert, "The Impact of Volatility Targeting", Journal of Portfolio Management, Fall 2018 ([PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf)); Moreira & Muir, "Volatility-Managed Portfolios", Journal of Finance 2017 (cited there, not opened); M1 paper for the intraday rule.
- **Evidence quality:** Peer-reviewed, long daily history. For US equities Sharpe rose from 0.40 to 0.48–0.51 and volatility of volatility fell from 4.6% to 1.8% ([summary](https://www.bluerating.com/?p=141117)).
- **Known failure modes:** Lags sudden jumps; scales back in just before sharp rebounds; leverage cap matters for a 3× product.
- **Implementation complexity:** Low.

### S2. Kelly and fractional Kelly

- **Name and category:** Growth-optimal sizing — sizing.
- **Role:** Upper bound on sleeve leverage.
- **Core idea:** With independent strategies, leverage f\_i = m\_i / s\_i² (mean excess return over variance). Fractional Kelly (½ or less) trades growth for much lower drawdown; long-only means negative f values are clipped to zero.
- **Key parameters:** Estimation window; Kelly fraction 0.25–0.5; risk-free rate.
- **Data required:** Daily Yahoo returns in the repo.
- **Asset fit:** Both.
- **Intraday suitability:** Low as estimated; medium as a cap. Flag: daily inputs.
- **Grid compatibility:** Medium; use as a ceiling on total sleeve exposure, not per lot. Your TQQQ already embeds 3× leverage, which a full-Kelly estimate on QQQ can exceed.
- **Source(s):** [deltaray-io/kelly-criterion](https://github.com/deltaray-io/kelly-criterion) (Python 2.7; no commits since Feb 2019, unmaintained); half-Kelly ceiling in [riskkit](https://github.com/HasibVortex369/riskkit); Kelly and conformal sizing in [ML4T chapter 17](https://github.com/stefan-jansen/machine-learning-for-trading).
- **Evidence quality:** Theory (Kelly 1956; Thorp, cited by the repo); the repo's own example even returns a short SPY leverage of −2.73.
- **Known failure modes:** Mean estimates are noisy; ignoring covariance (as this repo does) overstates leverage.
- **Implementation complexity:** Low.

### S3. Volatility-adjusted fixed-fractional sizing with a drawdown ladder

- **Name and category:** Risk-budget sizing with drawdown tiers — sizing and risk overlay.
- **Role:** Sizing plus an account-level circuit breaker.
- **Core idea:** Size from a fixed fraction of equity scaled by ATR versus its baseline, cap at a half-Kelly and notional limit, then multiply by the drawdown tier: 1.0 below 3% drawdown, 0.75 to 5%, 0.5 to 7%, 0.25 to 10%, halt above 10%, with a recovery ramp and losing-streak reductions.
- **Key parameters:** Base risk 1% (example); tier thresholds 3/5/7/10%; notional cap.
- **Data required:** Equity curve and ATR.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High; the tiers throttle new lots only. This is a ready-made version of your open drawdown circuit-breaker item.
- **Source(s):** [HasibVortex369/riskkit](https://github.com/HasibVortex369/riskkit) (PositionSizer, DrawdownManager; zero dependencies; last commit Jul 2026).
- **Evidence quality:** Tooling; no performance evidence. Examples are crypto-flavored but the code is asset-agnostic.
- **Known failure modes:** Account-drawdown tiers react after the damage; recovery ramps can keep size low through the rebound.
- **Implementation complexity:** Low.

### S4. Inventory-capped inverse-exposure sizing

- **Name and category:** Lot size decreasing with open inventory — sizing.
- **Role:** Sizing at each grid step.
- **Core idea:** The sizing-engine form of G2's skew: lot size falls as open lots or open notional rise (for example geometric decay per open lot) under hard caps on total open notional and total heat.
- **Key parameters:** Decay per lot; max lots; open-notional cap.
- **Data required:** The inventory ledger.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Very high; it is the cheapest way to make a correction consume capital slowly.
- **Source(s):** Skew mechanism in the [hftbacktest grid tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/High-Frequency%20Grid%20Trading.html); portfolio caps (open notional, heat, sector) in [riskkit](https://github.com/HasibVortex369/riskkit).
- **Evidence quality:** Mechanism only; no correction-specific test found.
- **Known failure modes:** Under-buys the final capitulation leg, which is often the most profitable.
- **Implementation complexity:** Low.

### S5. Probability-scaled (meta-label or conformal) sizing

- **Name and category:** Probabilistic sizing — sizing.
- **Role:** Sizing.
- **Core idea:** Map ML2's predicted success probability, or a conformal prediction interval, to lot size, so uncertain triggers get small lots.
- **Key parameters:** Probability-to-size curve; minimum probability; interval coverage.
- **Data required:** Model outputs.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High.
- **Source(s):** [ML4T chapter 17](https://github.com/stefan-jansen/machine-learning-for-trading) (conformal position sizing, README only); ML2 above.
- **Evidence quality:** Method; not verified beyond the README.
- **Known failure modes:** Miscalibrated probabilities in unseen regimes.
- **Implementation complexity:** Medium.

### S6. Inverse-volatility weights across a small ETF set

- **Name and category:** Naive risk parity — sizing.
- **Role:** Splits a correction sleeve across several ETFs.
- **Core idea:** Weight\_i ∝ 1/σ\_i, normalized; optionally one position per correlation group.
- **Key parameters:** Volatility window; correlation-group threshold.
- **Data required:** Daily or intraday returns.
- **Asset fit:** ETFs.
- **Intraday suitability:** Medium.
- **Grid compatibility:** Medium; useful if the correction sleeve ladders QQQ, defensive sector ETFs and T-bill ETFs together.
- **Source(s):** `inverse_vol_weights` and CorrelationGuard in [riskkit](https://github.com/HasibVortex369/riskkit).
- **Evidence quality:** Tooling only.
- **Known failure modes:** Correlations converge toward 1 in crashes.
- **Implementation complexity:** Low.

## Catalog — Risk and exit logic

Under your rules, exits split cleanly into two kinds: regime exits that may realize losses, and profit-only exits that never do. The sources supply good building blocks for both; what they do not supply is evidence on which lots to liquidate first, which is an open design choice.

### X1. Composite regime-exit policy (`lots_to_liquidate`)

- **Name and category:** Regime-triggered liquidation — risk overlay (synthesis of R1, R2 and R5).
- **Role:** The only loss-realizing exit in the correction sleeve.
- **Core idea:** Liquidate TQQQ lots when any confirmed trigger fires: QQQ closes below its 200-day SMA (R1), turbulence exceeds its threshold (R2), or the account reaches the final drawdown tier (R5). Halt new buys while the trigger holds; re-arm with hysteresis.
- **Key parameters:** Trigger set; confirmation (close vs intraday); hysteresis band; liquidation order (highest-cost lots first, all lots, or a fixed fraction).
- **Data required:** Daily closes plus a daily or intraday turbulence basket.
- **Asset fit:** Both.
- **Intraday suitability:** Medium (triggers are mostly daily; execution is intraday).
- **Grid compatibility:** Native; it is the interface your ledger already exposes.
- **Source(s):** R1, R2 and R5 records above.
- **Evidence quality:** Components have evidence (R1 long-history in-sample; R2 one out-of-sample crash); the combination is untested.
- **Known failure modes:** Selling into a capitulation low, then missing a V-shaped rebound; trigger whipsaw.
- **Implementation complexity:** Medium.

### X2. Time-limit and end-of-day exits

- **Name and category:** Time-based exits — exit logic.
- **Role:** Exit for intraday sleeves (M1, M2) and an inventory-age limit for grid lots.
- **Core idea:** Close a position after a fixed holding period or at the session close regardless of P&L. In exitkit's own demo (one 10/30 SMA entry rule, five exit policies), a 30-day time limit held drawdown to 22% through 2008–09 while the other policies reached 65%.
- **Key parameters:** Max holding time; end-of-day cutoff.
- **Data required:** Any.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Conflicts with the no-loss rule unless time exits are classed as regime exits (open question). A profit-only variant (exit at time limit only if above cost) is always allowed.
- **Source(s):** [charlieyanhx/exitkit](https://github.com/charlieyanhx/exitkit) (27 exit models in 6 families; last commit Sep 2026); M1 and M2 papers for end-of-day flattening.
- **Evidence quality:** Single-asset illustration on sample data; anecdotal.
- **Known failure modes:** Cuts winners that need more time; the demo result may not generalize.
- **Implementation complexity:** Low.

### X3. Profit-only trailing exits

- **Name and category:** Trailing take-profit — exit logic.
- **Role:** Profit-taking that never realizes a loss.
- **Core idea:** Once a lot is past its take-profit, replace the fixed target with a trailing exit that only ratchets up: VWAP or noise-band trail (M1), Parabolic SAR (M6), or ATR/chandelier trail. The exit price is floored at the lot's take-profit, so it can only lock in gains.
- **Key parameters:** Trail type; ATR multiple (for example 2–3); floor at cost + target.
- **Data required:** Minute bars (VWAP needs volume).
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Very high; captures more of bear-market rallies, which are sharp, than a fixed rung.
- **Source(s):** M1 trailing-stop rule ([PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)); StopEngine (ATR/EMA trailing, chandelier, PSAR) in [riskkit](https://github.com/HasibVortex369/riskkit); [je-suis-tm Parabolic SAR](https://github.com/je-suis-tm/quant-trading/blob/master/Parabolic%20SAR%20backtest.py).
- **Evidence quality:** M1 shows a VWAP-plus-band trail raised Sharpe from 0.61 to 1.24 versus an opposite-band stop, but that was a loss-allowed exit in a momentum strategy; no evidence for the profit-only form.
- **Known failure modes:** Gives back part of each gain; frees capital later than a fixed rung.
- **Implementation complexity:** Low.

### X4. Session caps and cooldowns on new lots

- **Name and category:** Daily trade and loss limits — risk overlay.
- **Role:** Limits how fast the grid can deploy capital on a falling day.
- **Core idea:** Cap new lots per day, enforce minimum spacing in time between fills, and escalate cooldowns after runs of adverse fills; optional profit-taking stop for the day.
- **Key parameters:** Max new lots per day; minimum minutes between fills; cooldown schedule.
- **Data required:** The ledger.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High; it throttles buys only. Pairs well with M3 (defer buys on strongly negative mornings).
- **Source(s):** SessionManager in [riskkit](https://github.com/HasibVortex369/riskkit).
- **Evidence quality:** Tooling only.
- **Known failure modes:** Misses intraday capitulation reversals if the cap binds early.
- **Implementation complexity:** Low.

## Catalog — Intraday seasonality and microstructure

The signals with the strongest evidence here (order-flow imbalance, book imbalance) need quote data; with minute bars only, the usable tools are VWAP-relative gating, time-of-day-normalized volatility and OHLC-based proxies. The TQQQ-specific idea people expect to matter, leveraged-ETF rebalancing at the close, has contested evidence.

### MS1. Order-flow imbalance (OFI) at the best bid and ask

- **Name and category:** OFI — microstructure signal.
- **Role:** Execution timing and a bid-side adverse-selection filter.
- **Core idea:** OFI adds bid-size increases, ask-size decreases and price upticks at the touch, and subtracts the opposite. Short-interval price changes are roughly linear in OFI, with slope inversely proportional to market depth.
- **Key parameters:** Aggregation interval (seconds to minutes); depth normalization.
- **Data required:** L1 quote updates (NYSE TAQ in the paper). Not computable from minute bars.
- **Asset fit:** Stocks (50 US stocks in the paper); applies to ETFs.
- **Intraday suitability:** High.
- **Grid compatibility:** Medium. Hold back a grid bid while OFI is strongly negative; the authors themselves suggest OFI as a measure of adverse selection in limit-order execution.
- **Source(s):** Cont, Kukanov & Stoikov, "The Price Impact of Order Book Events", Journal of Financial Econometrics 12(1), 2014 ([arXiv 1011.6402](https://arxiv.org/abs/1011.6402)); implementation in [twowaymind/orderflow-metrics](https://github.com/twowaymind/orderflow-metrics).
- **Evidence quality:** Peer-reviewed; robust across stocks, time scales and intraday seasonality. The relation is contemporaneous, so its forecasting value must be tested separately.
- **Known failure modes:** Explains moves as they happen more than it predicts them; needs a quote feed.
- **Implementation complexity:** Medium.

### MS2. Order-book imbalance and micro-price

- **Name and category:** Static book imbalance, micro-price, VAMP — microstructure signal.
- **Role:** Fair-value shift for grid quotes (feeds MM3).
- **Core idea:** Imbalance = (bid depth − ask depth) / (bid depth + ask depth) within a band around the mid, standardized over a rolling window; micro-price weights bid and ask by the opposite side's size.
- **Key parameters:** Depth band (2.5% or 0.1% of mid in the tutorial); standardization window (10 min to 1 hour); alpha weight c1.
- **Data required:** L2 depth (L1 sizes suffice for the micro-price).
- **Asset fit:** Both; source uses crypto (BTC/ETH futures).
- **Intraday suitability:** High.
- **Grid compatibility:** Medium; lowers bids when the book leans to sellers.
- **Source(s):** [hftbacktest tutorial: Market Making with Alpha — Order Book Imbalance](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html).
- **Evidence quality:** Tutorial backtests on crypto (May 2023) with a maker rebate.
- **Known failure modes:** Spoofable; US equity books are fragmented across venues.
- **Implementation complexity:** Medium.

### MS3. VWAP-relative gating

- **Name and category:** VWAP deviation — intraday signal.
- **Role:** Regime gate and profit-only trail.
- **Core idea:** Regular-hours VWAP marks the day's average traded price; staying below it signals persistent selling. M1 exits longs on a cross below max(VWAP, upper band). For the grid: add lots only when price is below VWAP by k·σ and pause when it is far below and still falling.
- **Key parameters:** k (in intraday σ); VWAP from regular-hours data only.
- **Data required:** Minute bars with volume.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High.
- **Source(s):** M1 paper ([PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)), which cites Zarattini & Aziz, "Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems", SSRN 2023 (not opened).
- **Evidence quality:** Indirect (VWAP trail's contribution inside M1).
- **Known failure modes:** VWAP anchors to the open, so it lags late-day reversals.
- **Implementation complexity:** Low.

### MS4. Time-of-day-normalized volatility

- **Name and category:** Intraday seasonality — volatility normalization.
- **Role:** Spacing input.
- **Core idea:** Measure each minute's typical move from the open over recent days (M1's σ by time of day) and scale grid spacing by it, so rungs are wide at the open and close and tighter midday. M1's authors also report trends pausing around lunch and resuming from 14:00.
- **Key parameters:** Lookback 14–90 days; per-minute or per-half-hour buckets.
- **Data required:** Minute bars.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** High; a direct improvement to G3.
- **Source(s):** M1 paper and its FAQ (Q6, Q18); M3 (first and last half-hours).
- **Evidence quality:** Indirect.
- **Known failure modes:** Event days (FOMC, CPI) break the profile.
- **Implementation complexity:** Low.

### MS5. Bar-only microstructure proxies

- **Name and category:** OHLC spread estimators, range-based volatility, jump tests, bulk volume classification — microstructure proxies.
- **Role:** Features and cost estimates when only minute bars exist.
- **Core idea:** Estimate effective spread, volatility and jump activity from OHLC; classify bar volume into buy/sell shares; build information-driven bars.
- **Key parameters:** Estimator choice; window.
- **Data required:** Minute OHLCV.
- **Asset fit:** Both.
- **Intraday suitability:** High.
- **Grid compatibility:** Medium; mainly realistic cost and fill assumptions for grid backtests.
- **Source(s):** [twowaymind/orderflow-metrics](https://github.com/twowaymind/orderflow-metrics) (Python and TypeScript; last commit Sep 2026).
- **Evidence quality:** Library of published estimators; I did not validate implementations.
- **Known failure modes:** Bulk classification is the weak variant in the VPIN dispute (MM4).
- **Implementation complexity:** Low.

### MS6. Leveraged-ETF end-of-day rebalancing flow

- **Name and category:** LETF rebalancing pressure — intraday seasonality.
- **Role:** Hypothesis for late-day grid behavior on large-move days; not a standalone signal.
- **Core idea:** Daily-reset leveraged ETFs must buy after up days and sell after down days near the close, in the direction of the move. Capital flows can offset that demand.
- **Key parameters:** Day's index return × LETF assets; flow estimate.
- **Data required:** Intraday prices plus daily LETF assets and flows.
- **Asset fit:** TQQQ and its underlying basket specifically.
- **Intraday suitability:** Medium.
- **Grid compatibility:** Low until tested; at most a reason to avoid buying in the last 30 minutes of large down days (which M3 already suggests).
- **Source(s):** Cheng & Madhavan, "The Dynamics of Leveraged and Inverse ETFs", Journal of Investment Management 2009 ([PDF](https://joim.com/wp-content/uploads/emember/downloads/p0283.pdf)); Ivanov & Lenkey, "Do leveraged ETFs really amplify late-day returns and volatility?", Journal of Financial Markets 41, 2018 ([record](https://pure.psu.edu/en/publications/do-leveraged-etfs-really-amplify-late-day-returns-and-volatility/)); Lenkey's [literature survey](https://www.aimspress.com/article/id/676a38d5ba35de0ad141c3c3).
- **Evidence quality:** Contested. Ivanov & Lenkey find flows substantially reduce rebalancing demand even in stress and the late-day effect is economically insignificant (2006–2014).
- **Known failure modes:** Small or offset effect; crowded front-running.
- **Implementation complexity:** Medium.

### MS7. Market profile and volume profile

- **Name and category:** Price-by-volume distribution — support/resistance.
- **Role:** Rung placement.
- **Core idea:** Build the session's or recent days' volume-at-price histogram; the point of control and value-area edges act as likely reaction levels for grid rungs.
- **Key parameters:** Profile window; value-area percentage (commonly 70%).
- **Data required:** Minute bars with volume.
- **Asset fit:** Both.
- **Intraday suitability:** Medium.
- **Grid compatibility:** Medium; snap rungs to high-volume nodes instead of a uniform ladder.
- **Source(s):** [letianzj/QuantResearch, market/market\_profile.ipynb (#25)](https://github.com/letianzj/QuantResearch).
- **Evidence quality:** Code and blog only; no performance evidence.
- **Known failure modes:** Levels lose meaning in trend days.
- **Implementation complexity:** Low.

## Catalog — ETF-specific ideas

This category is thin in the sources: nothing intraday, and index/ETF arbitrage is out of reach without creation/redemption access. The one idea that fits the long-only constraint well is changing leverage by regime, stepping from TQQQ to QQQ to a T-bill ETF instead of hedging.

### E1. Regime-based leverage stepping (TQQQ → QQQ → T-bills)

- **Name and category:** Leverage rotation within one index family — ETF regime overlay.
- **Role:** Instrument selection for the correction sleeve.
- **Core idea:** Extend R1 from on/off to steps: TQQQ when QQQ is above its SMA and volatility is low, QQQ when one condition fails, a T-bill ETF when both fail. The paper tested 1.25×, 2× and 3× versions of the same rule.
- **Key parameters:** SMA length; volatility threshold; step order.
- **Data required:** Daily closes; intraday execution.
- **Asset fit:** ETFs (no inverse or volatility products needed).
- **Intraday suitability:** Low as a signal; the grid keeps running on whichever instrument is active.
- **Grid compatibility:** High. Each step-down is a regime exit for the higher-leverage lots, then the grid continues on QQQ with smaller rungs.
- **Source(s):** [Gayed & Bilello 2016](https://docs.cmtassociation.org/dow-award/2016-gayed-bilello.pdf) (R1).
- **Evidence quality:** In-sample, long history, S&P 500 rather than Nasdaq-100; the stepped version is my extension and untested.
- **Known failure modes:** Extra switching costs; QQQ still falls in a correction, only one-third as fast.
- **Implementation complexity:** Low.

### E2. Tactical asset allocation with moving-average filters

- **Name and category:** Faber-style TAA — ETF rotation.
- **Role:** Where idle correction-sleeve capital sits.
- **Core idea:** Hold each asset-class ETF only while it is above its long moving average, otherwise cash.
- **Key parameters:** Moving-average length (monthly in the original style); asset list.
- **Data required:** Daily or monthly closes.
- **Asset fit:** ETFs.
- **Intraday suitability:** Low. Flag: daily/monthly strategy.
- **Grid compatibility:** Low; a parking rule, not a grid input.
- **Source(s):** [letianzj/QuantResearch, backtest/mebane\_faber\_taa.py](https://github.com/letianzj/QuantResearch); the original Faber paper was not opened.
- **Evidence quality:** Code only in this survey.
- **Known failure modes:** Slow; whipsaw near the average.
- **Implementation complexity:** Low.

### E3. Cross-asset ETF momentum and mean reversion

- **Name and category:** Cross-sectional ETF signals — ETF rotation.
- **Role:** Selecting which defensive ETFs the sleeve may hold.
- **Core idea:** Rank about 100 ETFs on momentum and short-term reversal features inside ML4T's standard pipeline (labels, features, models, costs).
- **Key parameters:** Look-back windows; rebalance frequency.
- **Data required:** Daily bars.
- **Asset fit:** ETFs.
- **Intraday suitability:** Low. Flag: daily case study.
- **Grid compatibility:** Low.
- **Source(s):** [ML4T ETFs case study](https://github.com/stefan-jansen/machine-learning-for-trading) (README only).
- **Evidence quality:** Not verified beyond the README.
- **Known failure modes:** Correlations converge in crashes.
- **Implementation complexity:** Medium.

### E4. Regime-aware risk for concentrated mega-cap exposure

- **Name and category:** Concentration risk regime — ETF/portfolio risk overlay.
- **Role:** Candidate regime input, since the Nasdaq-100 is concentrated in a few mega-caps.
- **Core idea:** Listed replication titled "Regime-Aware Risk Management in Concentrated Equity Portfolios: Evidence from the Magnificent Seven"; I saw only the title and summary statistics.
- **Key parameters:** Unknown.
- **Data required:** Unknown (the replication catalogue is mostly daily or monthly).
- **Asset fit:** Mega-cap stocks and QQQ-like exposure.
- **Intraday suitability:** Unknown.
- **Grid compatibility:** Unknown.
- **Source(s):** [paperswithbacktest/awesome-systematic-trading, Multi-asset table](https://github.com/paperswithbacktest/awesome-systematic-trading) (Sharpe 1.11, t-stat 6.4, 33 years, gross of costs).
- **Evidence quality:** Unverifiable from what I opened; listed for follow-up.
- **Known failure modes:** Unknown.
- **Implementation complexity:** Unknown.

## Ranked shortlist and implementation order

Build drawdown control before any new signal: ranks 1–5 are low-effort changes to sizing and regime exits that act on correction drawdown directly, ranks 6–9 add intraday gates, and new return sources come last. Rank order is also the suggested build order.

Before rank 1, set up the test harness: correction episodes (at minimum Q4 2018, Feb–Mar 2020 and 2022, the stress quarters M1 reports), conservative bar-based fills (or MM5 queue models if you have L2), real commissions and slippage, and DSR/PBO scoring (ML4) for every parameter sweep.

| Rank | Record(s) | What to build | Why it helps in corrections | Complexity |
| --- | --- | --- | --- | --- |
| 1 | S1 + G3 | Lot size ∝ target vol / realized vol; rung spacing ∝ short-term σ | Best-evidenced drawdown reducer; a correction automatically shrinks and spreads new lots | Low |
| 2 | G2 + S4 | Lot size decays with open lots; open-notional cap | Limits the inventory build-up that drives correction drawdown, without forcing sales | Low |
| 3 | R1 → X1 | QQQ close below its 200-day SMA marks TQQQ lots for `lots_to_liquidate` and halts buys until reclaimed | The loss-realizing exit your rules allow; long-history evidence that leverage fails below the SMA | Low |
| 4 | R2 | Turbulence index on a Nasdaq-100 basket as a second, faster trigger | Reacts to correlation breaks before a daily SMA does; survived one out-of-sample crash | Low |
| 5 | R5 / S3 | Drawdown tier ladder: throttle, then halt new lots | Closes your open circuit-breaker item; throttles buys only | Low |
| 6 | M3 | Defer grid buys after a strongly negative prior-close-to-10:00 return until after 15:30 | Peer-reviewed; predictability is strongest on volatile days | Low |
| 7 | M1 (as a gate) + MS3 | Pause grid buys while price is below the noise band or far below VWAP | Strongest correction evidence, used in gate form so no price stop is needed | Low–medium |
| 8 | X3 | Profit-only trailing exit for lots past take-profit | Captures more of sharp bear-market rallies without realizing losses | Low |
| 9 | MS4 + X4 | Time-of-day spacing; cap on new lots per day | Cheap refinements that slow capital deployment on trend days | Low |
| 10 | ML1 + ML2 (validated with ML3, ML4) | Meta-model on historical grid triggers that sizes each lot | Sizes down the triggers most likely to be run over, learned from your own history | Medium |
| 11 | E1 | Step TQQQ → QQQ → T-bill ETF by regime instead of on/off | Keeps the grid running at 1× through moderate stress | Low |
| 12 | M1 long-or-flat sleeve | Separate intraday momentum sleeve, long side only | Return-adding in volatile regimes; needs the time-exit question settled and a long-only test | Medium |
| 13 | MR1 basket | High-volatility dip-buying across Nasdaq-100 losers, vol-scaled | Liquidity-provision returns rise in turmoil; daily evidence only | Medium |
| 14 | MM2 | GLFT-calibrated spacing and skew | Most principled spacing model; needs L1 trade and quote data | Medium–high |

Success test for each rank, per your metric: return/max-drawdown over the correction episodes must improve without lowering it over the full sample by more than you are willing to pay for protection.

## Gap analysis

The biggest gap is the one that matters most: no source tests a long-only, no-stop intraday strategy on a leveraged ETF through a correction. The suggestions below are searches to run next; I have not verified the specific papers named as suggestions.

| Category | What is thin or missing | Suggested next sources |
| --- | --- | --- |
| Intraday mean reversion in stress | Reversal evidence (MR1) is daily and long-short | Search for intraday cross-sectional return patterns (e.g. Heston, Korajczyk & Sadka on intraday periodicity) and overnight-versus-intraday return studies |
| Grid trading on equities | Only crypto (G4) and FX (G6) sources; no equity grid study with real fills | Cartea, Jaimungal & Penalva and Guéant's market-liquidity books (both listed in awesome-systematic-trading); SSRN/arXiv searches for "ladder" and "grid" strategies on equities |
| Long-only momentum in corrections | M1 and M2 report long-short results only | Run it yourself; the M1 authors publish Python code via their FAQ |
| Intraday regime detection | R1 and R2 are daily signals | Realized-volatility forecasting (HAR-type models); VIX term-structure studies as a data-only regime input |
| Drawdown-constrained sizing theory | Only tooling (riskkit tiers) | Drawdown-control and CPPI literature (e.g. Grossman & Zhou on drawdown-constrained investing) |
| Microstructure with bars only | OFI and book imbalance need quotes | ML4T chapter 3 and its NASDAQ-100 case study notebooks; TAQ data via WRDS (listed in the FinRL README) |
| ETF-specific intraday ideas | Nothing intraday; arbitrage not feasible | Futures-to-ETF price discovery and lead-lag studies (Nasdaq futures as a data-only leading signal) |
| Crash and bubble detection | LPPLS has no verified out-of-sample record here | Sornette group's crisis-observatory papers |
| Regime-aware RL and market making | Listed but unopened: MacroHFT (KDD'24, crypto), IMM (IJCAI'24), LLM crash detection (arXiv 2410.17266) | Open these from [ihobbang250/Awesome-AI-in-Finance](https://github.com/ihobbang250/Awesome-AI-in-Finance) only if RL or market making moves up the list |
| Online mean-reversion portfolios | universal-portfolios (OLMAR/PAMR-type algorithms) listed in awesome-quant, not opened | [Marigold/universal-portfolios](https://github.com/Marigold/universal-portfolios) for a mean-reverting ETF rotation sleeve |

## Rejected list

Most exclusions fall into four buckets: options-dependent, crypto-specific, incompatible with the long-only rule, or unverifiable. Asset-agnostic techniques demonstrated on crypto were kept in the catalog and flagged instead.

| Item | Source | Reason |
| --- | --- | --- |
| Options straddle; VIX calculator | [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) | Options pricing (excluded by the brief) |
| Dealer gamma-imbalance signals | Baltussen et al. 2021, cited in M1 | Needs options positioning data; M1's RSI(5) proxy is kept instead |
| Funding-rate arbitrage; perpetual-futures scanners | ML4T crypto-perps case study; awesome-quant and awesome-ai-in-finance crypto entries | Crypto-specific mechanics |
| Crypto bots and indicator packs (Gekko strategies, crypto-signal, LSTM crypto predictors, DeepAlpha) | [awesome-ai-in-finance](https://github.com/georgezouq/awesome-ai-in-finance) | Crypto-specific or no verifiable results |
| Martingale / averaging-down sizing | binary-martingale in [awesome-quant](https://github.com/wilsonfreitas/awesome-quant) | Ruin-prone sizing that works against the drawdown goal |
| 18 deep sequence forecasters and stacked ensembles | [huseinzol05/Stock-Prediction-Models](https://github.com/huseinzol05/Stock-Prediction-Models) | Daily, no costs, no trading evidence, unmaintained since Jan 2021 |
| Short legs of pairs, stat-arb and breakout rules | MR2, MR3, MR8, M2, M4 sources | Shorting not allowed; long-only variants kept |
| Inverse, volatility and managed-futures ETFs as hedges | Your standing constraints | Ruled out (DBMF, KMLM, VIXY named) |
| Monte Carlo price prediction, Oil Money, Smart Farmers, Wisdom of Crowds | [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) | Research projects on FX, commodities or forecasts, not intraday equity algorithms |
| Ghost Trader | [letianzj/QuantResearch](https://github.com/letianzj/QuantResearch) | Daily MA/RSI/new-high entry with a Donchian price stop; redundant with M8 and MR6 and stop-dependent |
| Index/ETF creation-redemption arbitrage | Brief category | Requires authorized-participant access |
| LLM agent frameworks (TradingAgents, FinRobot and similar) | Curated lists | Frameworks rather than algorithms; no verifiable trading results |
| Novelty strategies (tweet-driven trading, lottery prediction) | [awesome-ai-in-finance](https://github.com/georgezouq/awesome-ai-in-finance) | No credible evidence |
| "Ten Financial Applications of Machine Learning" | SSRN 3197726 | Not opened; nothing extracted |

## Open questions before implementation

The first two answers decide whether the momentum sleeves (M1, M2) are usable at all; the third decides which microstructure and market-making records can be built.

- [ ] Does an end-of-day flatten or a time-limit exit count as a regime exit for intraday sleeves (M1, M2, X2)?
- [ ] May a VWAP or band trailing exit close a lot below cost if classed as a regime exit, or must trailing exits stay profit-only (X3)?
- [ ] What data is available: minute bars only, L1 quotes and trades, or L2 depth (MS1, MS2, MM2, MM5)?
- [ ] May the VIX index and a Nasdaq-100 constituent basket be used as data inputs (R2, R4)?
- [ ] Which instruments are allowed as the step-down and cash legs: QQQ, T-bill ETFs, defensive sector ETFs (E1, E2, S6)?
- [ ] Liquidation order for `lots_to_liquidate`: highest-cost lots first, all lots, or a fixed fraction (X1)? Do tax lots matter?
- [ ] Is the correction sleeve a separate capital pool from the main grid, and with what share of capital?
- [ ] Is "QQQ 10% below its high" the right correction definition for test episodes, or do you want a different trigger?
- [ ] Should a long-or-flat momentum sleeve trade TQQQ or QQQ?
