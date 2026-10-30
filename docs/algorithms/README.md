# Algorithm pages

One page per algorithm in the ranked list of
[`docs/algorithm_ledger.md` §8C](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import),
the 14,225-row CSV import of 2026-10-27. The ledger's tables say, for
every row, whether volatility-ai implements it and link here.

| Path | What it is | Written by |
|---|---|---|
| `<slug>.md` without a `generated` first line | A **researched** page: the rule, evidence for and against, fit with the project's constraints, what the repository already has, and how to test it here. Ledger IDs RK1–RK425 (the same ranks). Pages for ranks 101–199 add a "Useful for volatility-ai" verdict. | hand |
| `<slug>.md` with a `generated` first line | A **card** for one of the 425 specific algorithms (ranks 1–425): the CSV's own text plus the implementation status. | `tools/build_algorithm_ledger.py` |
| `concepts/<slug>.md` | One page per description shared by the 13,800 title-reconstructed rows (ranks 426–14,225): the description, every variant of the other fields its members carry, and the members. [Index](concepts/README.md). A concept page without a `generated` first line is **researched**: the 34 concepts of ranks 426–700 are. | the build; researched ones by hand |
| `ranked/ranks-*.md` | The title-reconstructed rows by rank, 1,000 per page, each linked to its concept page. | the build |
| `implementation_status.csv` | Which algorithms have code here: status, ledger IDs, code references, a note. Not listed means not implemented. | hand |
| `source/*.csv.xz` | The import itself, every field of every row (`xz -dk` to read it). | the import |

## Researched so far

Ranks 1–425, one page each; ranks 101–199 were researched on 2026-10-30 as a usefulness triage (see "Usefulness triage" below). Each page says what its sources are and how far
they could be checked (full texts could not be opened from the research environment).

Every researched algorithm now has code: entries the platform did not
already cover are standalone research code in `research/catalog/`
(tested on synthetic data in `research/tests/test_catalog_*.py`, not
wired into the engine or live trading), and the Implemented column says
"Research code" for them. That code is a reference implementation of
each rule, not evidence that it works: the verdicts on the pages stand.
Toy-scale stand-ins are named in each module's docstring (simulated
annealing and statevector simulation for quantum hardware, a lexicon or
naive-Bayes scorer for FinBERT, LightGBM for XGBoost, finite-difference
residuals for physics-informed networks).

| ID | Algorithm | Rank | Implemented |
|---|---|---|---|
| RK1 | [Time-Series Momentum (TSMOM)](time-series-momentum-tsmom.md) | 1 | Research code (as published) |
| RK2 | [Volatility-Scaled Trend Following](volatility-scaled-trend-following.md) | 2 | Research code; the scaling half is wired (S4) |
| RK3 | [Dual Momentum (Absolute + Relative)](dual-momentum-absolute-relative.md) | 3 | Yes, as `tools/rotation.py --mode relative_strength` (X3) |
| RK4 | [Cross-Asset Carry Composite](cross-asset-carry-composite.md) | 4 | Research code |
| RK5 | [Value-Momentum Composite](value-momentum-composite.md) | 5 | Research code |
| RK6 | [12–1 Momentum (Skip-Month)](12-1-momentum-skip-month.md) | 6 | Research code |
| RK7 | [Cross-Sectional Momentum](cross-sectional-momentum.md) | 7 | Partial (X3) |
| RK8 | [Commodity Momentum + Term Structure](commodity-momentum-term-structure.md) | 8 | Research code |
| RK9 | [Fama–French Five-Factor Model Portfolio](fama-french-five-factor-model-portfolio.md) | 9 | Research code |
| RK10 | [State-Filtered Momentum](state-filtered-momentum.md) | 10 | Partial |
| RK11 | [Quality Minus Junk (QMJ)](quality-minus-junk-qmj.md) | 11 | Research code |
| RK12 | [Quality / Profitability Factor](quality-profitability-factor.md) | 12 | Research code |
| RK13 | [Gross Profitability Factor](gross-profitability-factor.md) | 13 | Research code |
| RK14 | [52-Week High Momentum](52-week-high-momentum.md) | 14 | Partial |
| RK15 | [Conservative Investment Factor](conservative-investment-factor.md) | 15 | Research code |
| RK16 | [Residual Momentum](residual-momentum.md) | 16 | Research code |
| RK17 | [10-Month Moving-Average Risk Filter](10-month-moving-average-risk-filter.md) | 17 | Yes (V16, C-E2) |
| RK18 | [Low-Volatility Equity](low-volatility-equity.md) | 18 | Partial (X2) |
| RK19 | [Sector Momentum Rotation](sector-momentum-rotation.md) | 19 | Partial (X3) |
| RK20 | [Bond Duration Momentum](bond-duration-momentum.md) | 20 | Research code |
| RK21 | [VIX-Regime Conditional Equity Exposure](vix-regime-conditional-equity-exposure.md) | 21 | Yes (V12) |
| RK22 | [Volatility Targeting / Risk Scaling](volatility-targeting-risk-scaling.md) | 22 | Yes (S4, V18, S3) |
| RK23 | [Drawdown-Aware De-Risking Governor](drawdown-aware-de-risking-governor.md) | 23 | Yes (V11) |
| RK24 | [ETF NAV / Creation-Redemption Arbitrage](etf-nav-creation-redemption-arbitrage.md) | 24 | Research code (C-RJ6) |
| RK25 | [Index Futures vs Cash Basis Arbitrage](index-futures-vs-cash-basis-arbitrage.md) | 25 | Research code |
| RK26 | [Futures Cash-and-Carry Basis Trading](futures-cash-and-carry-basis-trading.md) | 26 | Partial |
| RK27 | [Shareholder Yield Factor](shareholder-yield-factor.md) | 27 | Research code |
| RK28 | [Fixed-Income Carry and Roll-Down](fixed-income-carry-and-roll-down.md) | 28 | Research code |
| RK29 | [Price + Earnings Momentum](price-earnings-momentum.md) | 29 | Research code |
| RK30 | [FX Carry Trade](fx-carry-trade.md) | 30 | Research code |
| RK31 | [Intangibles-Adjusted Value and Profitability Factor](intangibles-adjusted-value-and-profitability-factor.md) | 31 | Research code |
| RK32 | [Commodity Futures Roll Yield](commodity-futures-roll-yield.md) | 32 | Research code |
| RK33 | [Market-Neutral Residual Mean Reversion](market-neutral-residual-mean-reversion.md) | 33 | Research code (C-MR2) |
| RK34 | [Futures Calendar-Spread Mean Reversion](futures-calendar-spread-mean-reversion.md) | 34 | Research code |
| RK35 | [Net Stock Issuance Anomaly](net-stock-issuance-anomaly.md) | 35 | Research code |
| RK36 | [Johansen Cointegration Basket Trading](johansen-cointegration-basket-trading.md) | 36 | Research code |
| RK37 | [Cointegration-Based Pairs Trading](cointegration-based-pairs-trading.md) | 37 | Research code (Q2) |
| RK38 | [Chandelier Exit Trend Following](chandelier-exit-trend-following.md) | 38 | Partial (V10, Q8) |
| RK39 | [Merger Arbitrage](merger-arbitrage.md) | 39 | Research code |
| RK40 | [Earnings Estimate Revision Momentum](earnings-estimate-revision-momentum.md) | 40 | Research code |
| RK41 | [Inflation-Regime Asset Rotation](inflation-regime-asset-rotation.md) | 41 | Research code |
| RK42 | [Cross-Asset Commodity Futures Term-Structure Carry & Roll Yield](cross-asset-commodity-futures-term-structure-carry-roll-yield.md) | 42 | Research code |
| RK43 | [Donchian / Turtle Channel Breakout](donchian-turtle-channel-breakout.md) | 43 | Research code (C-G5) |
| RK44 | [Supertrend ATR-Band Trend Following](supertrend-atr-band-trend-following.md) | 44 | Research code |
| RK45 | [Post-Earnings Announcement Drift (PEAD)](post-earnings-announcement-drift-pead.md) | 45 | Research code |
| RK46 | [MACD Signal-Line Crossover](macd-signal-line-crossover.md) | 46 | Yes (Q1) |
| RK47 | [Public Activist-Filing Event Strategy](public-activist-filing-event-strategy.md) | 47 | Research code |
| RK48 | [Book-to-Market Value](book-to-market-value.md) | 48 | Research code |
| RK49 | [Betting Against Beta (BAB)](betting-against-beta-bab.md) | 49 | Research code |
| RK50 | [Accrual Anomaly](accrual-anomaly.md) | 50 | Research code |
| RK51 | [Asset-Growth Anomaly](asset-growth-anomaly.md) | 51 | Research code |
| RK52 | [Dividend Yield / Dividend Growth](dividend-yield-dividend-growth.md) | 52 | Partial |
| RK53 | [CVaR / Expected-Shortfall Optimization](cvar-expected-shortfall-optimization.md) | 53 | Research code |
| RK54 | [Volatility-Managed Factor Portfolio](volatility-managed-factor-portfolio.md) | 54 | Partial (S4) |
| RK55 | [ADX-Filtered Trend Following](adx-filtered-trend-following.md) | 55 | Partial (V15) |
| RK56 | [Hierarchical Risk Parity (HRP)](hierarchical-risk-parity-hrp.md) | 56 | Yes (A5, Q13) |
| RK57 | [Low P/E Value Screen](low-p-e-value-screen.md) | 57 | Research code |
| RK58 | [Small-Cap Size Premium](small-cap-size-premium.md) | 58 | Research code |
| RK59 | [Liquidity Factor](liquidity-factor.md) | 59 | Partial |
| RK60 | [Global Minimum-Variance Portfolio](global-minimum-variance-portfolio.md) | 60 | Research code (Q13) |
| RK61 | [Risk Parity / Equal Risk Contribution](risk-parity-equal-risk-contribution.md) | 61 | Partial (A5) |
| RK62 | [Dual Moving Average Crossover](dual-moving-average-crossover.md) | 62 | Research code (Q1, C-E2) |
| RK63 | [Black–Litterman Allocation](black-litterman-allocation.md) | 63 | Research code |
| RK64 | [Triple EMA / Moving-Average Ribbon](triple-ema-moving-average-ribbon.md) | 64 | Partial (V15) |
| RK65 | [Cross-Sectional Factor Momentum Rotation](cross-sectional-factor-momentum-rotation.md) | 65 | Research code |
| RK66 | [Maximum-Diversification Portfolio](maximum-diversification-portfolio.md) | 66 | Research code |
| RK67 | [ATR-Based Position Sizing](atr-based-position-sizing.md) | 67 | Research code (C-G5) |
| RK68 | [Dual Thrust Breakout](dual-thrust-breakout.md) | 68 | Research code (Q7, N1) |
| RK69 | [London Session Breakout](london-session-breakout.md) | 69 | Research code (Q4, N2, N3) |
| RK70 | [Parabolic SAR Trend / Stop](parabolic-sar-trend-stop.md) | 70 | Yes (Q8) |
| RK71 | [Heikin-Ashi Trend Filter](heikin-ashi-trend-filter.md) | 71 | Yes (Q3) |
| RK72 | [Distance-Based Pairs Trading](distance-based-pairs-trading.md) | 72 | Research code |
| RK73 | [Kalman-Filter Dynamic-Hedge Pairs](kalman-filter-dynamic-hedge-pairs.md) | 73 | Research code (Q2) |
| RK74 | [Copula-Based Pairs Trading](copula-based-pairs-trading.md) | 74 | Research code |
| RK75 | [Ornstein–Uhlenbeck Spread Trading](ornstein-uhlenbeck-spread-trading.md) | 75 | Research code (C-MR2, C-MR4) |
| RK76 | [PCA Residual Statistical Arbitrage](pca-residual-statistical-arbitrage.md) | 76 | Partial (C-MR2) |
| RK77 | [ATR Volatility-Expansion Breakout](atr-volatility-expansion-breakout.md) | 77 | Research code |
| RK78 | [Multi-Timeframe Trend Agreement](multi-timeframe-trend-agreement.md) | 78 | Research code |
| RK79 | [Opening Gap Continuation](opening-gap-continuation.md) | 79 | Partial (N3, X1) |
| RK80 | [Convertible Bond Arbitrage](convertible-bond-arbitrage.md) | 80 | Research code |
| RK81 | [Capital Structure Arbitrage](capital-structure-arbitrage.md) | 81 | Research code |
| RK82 | [Closed-End Fund Discount Reversion](closed-end-fund-discount-reversion.md) | 82 | Research code |
| RK83 | [Triangular FX Arbitrage](triangular-fx-arbitrage.md) | 83 | Research code (A7) |
| RK84 | [Crypto Perpetual Funding-Rate Capture](crypto-perpetual-funding-rate-capture.md) | 84 | Research code (C-RJ2) |
| RK85 | [Spot-Perpetual Basis Arbitrage](spot-perpetual-basis-arbitrage.md) | 85 | Partial (C-RJ2) |
| RK86 | [Yield Curve Steepener / Flattener](yield-curve-steepener-flattener.md) | 86 | Research code |
| RK87 | [Option Dispersion Trading](option-dispersion-trading.md) | 87 | Research code |
| RK88 | [Distributionally Robust CVaR Allocation](distributionally-robust-cvar-allocation.md) | 88 | Research code |
| RK89 | [Autoencoder Latent-Factor Statistical Arbitrage](autoencoder-latent-factor-statistical-arbitrage.md) | 89 | Research code |
| RK90 | [Long-Term Industry Reversal with Valuation Confirmation](long-term-industry-reversal-with-valuation-confirmation.md) | 90 | Research code |
| RK91 | [iNAV Dislocation ETF Arbitrage](inav-dislocation-etf-arbitrage.md) | 91 | Partial (C-RJ6) |
| RK92 | [FED OTC Liquidity Sweep & Reverse Repo Arbitrage](fed-otc-liquidity-sweep-reverse-repo-arbitrage.md) | 92 | Research code |
| RK93 | [Cointegrated Triplet Basket Statistical Arbitrage](cointegrated-triplet-basket-statistical-arbitrage.md) | 93 | Research code |
| RK94 | [Dynamic Copula-GARCH Multivariate Pair Trading](dynamic-copula-garch-multivariate-pair-trading.md) | 94 | Research code |
| RK95 | [Asymmetric Tail-Risk Parity Allocation](asymmetric-tail-risk-parity-allocation.md) | 95 | Research code |
| RK96 | [Principal Component Analysis (PCA) Eigenportfolios Statistical Arbitrage](principal-component-analysis-pca-eigenportfolios-statistical-arbitrage.md) | 96 | Partial (C-MR2) |
| RK97 | [Wasserstein Distributionally Robust Statistical Arbitrage](wasserstein-distributionally-robust-statistical-arbitrage.md) | 97 | Research code |
| RK98 | [Adversarial Domain Generalization Cross-Market Momentum](adversarial-domain-generalization-cross-market-momentum.md) | 98 | Research code |
| RK99 | [Conformally Constrained Risk Parity Portfolio](conformally-constrained-risk-parity-portfolio.md) | 99 | Partial |
| RK100 | [Causal Discovery Directed Acyclic Graph (DAG) Pair Selection](causal-discovery-directed-acyclic-graph-dag-pair-selection.md) | 100 | Research code |
| RK101 | [Dynamic Copula-EVT Tail Risk Relative Value Arbitrage](dynamic-copula-evt-tail-risk-relative-value-arbitrage.md) | 101 | Research code |
| RK102 | [Hidden Markov Model Regime Switching](hidden-markov-model-regime-switching.md) | 102 | Research code (C-R3) |
| RK103 | [Hurst-Exponent Trend / Mean-Reversion Regime Gate](hurst-exponent-trend-mean-reversion-regime-gate.md) | 103 | Research code (C-MR4) |
| RK104 | [Bayesian Online Changepoint Regime Gate](bayesian-online-changepoint-regime-gate.md) | 104 | No |
| RK105 | [Adaptive Range-Breakout with Volatility Filter](adaptive-range-breakout-with-volatility-filter.md) | 105 | Research code |
| RK106 | [Hierarchical Hidden Markov Model (HHMM) Regime Switcher](hierarchical-hidden-markov-model-hhmm-regime-switcher.md) | 106 | Research code |
| RK107 | [Entropy-Based Portfolio Diversification Optimization](entropy-based-portfolio-diversification-optimization.md) | 107 | Research code |
| RK108 | [Intraday ETF Relative-Value Arbitrage](intraday-etf-relative-value-arbitrage.md) | 108 | Research code (A6) |
| RK109 | [Sparse Graphical Lasso Cross-Asset Spillover Predictor](sparse-graphical-lasso-cross-asset-spillover-predictor.md) | 109 | No |
| RK110 | [Opening Range Breakout (ORB)](opening-range-breakout-orb.md) | 110 | Research code (C-M2, N2) |
| RK111 | [Ichimoku Cloud Trend Filter](ichimoku-cloud-trend-filter.md) | 111 | No |
| RK112 | [Kaufman Adaptive Moving Average (KAMA) Trend](kaufman-adaptive-moving-average-kama-trend.md) | 112 | Partial (V15) |
| RK113 | [Wavelet Transform Denoised Breakout System](wavelet-transform-denoised-breakout-system.md) | 113 | Research code |
| RK114 | [Volatility Risk Premium (Short Vol + Tail Hedge)](volatility-risk-premium-short-vol-tail-hedge.md) | 114 | Research code (S1) |
| RK115 | [EMA Pullback Continuation](ema-pullback-continuation.md) | 115 | Research code |
| RK116 | [Markowitz Mean-Variance Optimization](markowitz-mean-variance-optimization.md) | 116 | Research code (Q13) |
| RK117 | [Equal-Weight Rebalancing](equal-weight-rebalancing.md) | 117 | Partial (X5) |
| RK118 | [Minimum-Correlation Portfolio](minimum-correlation-portfolio.md) | 118 | No |
| RK119 | [Hierarchical Equal Risk Contribution (HERC)](hierarchical-equal-risk-contribution-herc.md) | 119 | No |
| RK120 | [Nested Cluster Optimization (NCO)](nested-cluster-optimization-nco.md) | 120 | No |
| RK121 | [Benchmark-Tracking Enhanced Indexing](benchmark-tracking-enhanced-indexing.md) | 121 | No |
| RK122 | [Robust Wasserstein Distributionally Robust Portfolio Optimization](robust-wasserstein-distributionally-robust-portfolio-optimization.md) | 122 | Research code |
| RK123 | [Adversarial Robust Wasserstein Portfolio Optimization](adversarial-robust-wasserstein-portfolio-optimization.md) | 123 | Research code |
| RK124 | [Optimal Transport Wasserstein Barycenter Asset Allocation](optimal-transport-wasserstein-barycenter-asset-allocation.md) | 124 | No |
| RK125 | [Continuous-Time Mean-Field Portfolio Game with Competition](continuous-time-mean-field-portfolio-game-with-competition.md) | 125 | No |
| RK126 | [Entropic Risk Measure Portfolio Optimization](entropic-risk-measure-portfolio-optimization.md) | 126 | Research code |
| RK127 | [Conformal Prediction Risk-Bounded Alpha Stacking](conformal-prediction-risk-bounded-alpha-stacking.md) | 127 | Research code |
| RK128 | [Fractional Order Cointegration Residual Mean-Reversion](fractional-order-cointegration-residual-mean-reversion.md) | 128 | Research code |
| RK129 | [Inverse-Volatility Allocation](inverse-volatility-allocation.md) | 129 | Partial (A5) |
| RK130 | [Extreme Value Theory (EVT) Dynamic Tail-Risk Hedge](extreme-value-theory-evt-dynamic-tail-risk-hedge.md) | 130 | Research code |
| RK131 | [Markov-Switching Vector Error Correction Model (MS-VECM) Arbitrage](markov-switching-vector-error-correction-model-ms-vecm-arbitrage.md) | 131 | Research code |
| RK132 | [Conformal Risk-Bounded Dynamic Portfolio Allocation](conformal-risk-bounded-dynamic-portfolio-allocation.md) | 132 | Partial (V13) |
| RK133 | [Protective Put / Collar](protective-put-collar.md) | 133 | Research code (S1) |
| RK134 | [Fractional Kelly Position Sizing](fractional-kelly-position-sizing.md) | 134 | Research code (C-S2) |
| RK135 | [Fractional Order Cointegration Vector AutoRegressive (VAR) Strategy](fractional-order-cointegration-vector-autoregressive-var-strategy.md) | 135 | Research code |
| RK136 | [Graph Attention Network Dynamic Cointegration Basket Selection](graph-attention-network-dynamic-cointegration-basket-selection.md) | 136 | Research code |
| RK137 | [Fractional Cointegration Hawkes Process Lead-Lag Arbitrage](fractional-cointegration-hawkes-process-lead-lag-arbitrage.md) | 137 | Research code |
| RK138 | [Fractional Order Vector Error Correction Model (VECM) Cointegration Strategy](fractional-order-vector-error-correction-model-vecm-cointegration-strategy.md) | 138 | Research code |
| RK139 | [Fractional Order Cointegration Dynamic Copula Trading System](fractional-order-cointegration-dynamic-copula-trading-system.md) | 139 | Research code |
| RK140 | [Neural Rough Path Signature Delay-Differential Cointegration Spread Model](neural-rough-path-signature-delay-differential-cointegration-spread-model.md) | 140 | Research code |
| RK141 | [Fractional Order Cointegration Hawkes Point Process Statistical Arbitrage](fractional-order-cointegration-hawkes-point-process-statistical-arbitrage.md) | 141 | Research code |
| RK142 | [Fractional Order Cointegration Vector Error Correction Hawkes Strategy](fractional-order-cointegration-vector-error-correction-hawkes-strategy.md) | 142 | Research code |
| RK143 | [Fractional Order Cointegration Hawkes Jump-Diffusion Arbitrage](fractional-order-cointegration-hawkes-jump-diffusion-arbitrage.md) | 143 | Research code |
| RK144 | [Alpha Stacking / Ensemble Portfolio Optimizer](alpha-stacking-ensemble-portfolio-optimizer.md) | 144 | Partial (C-RJ4) |
| RK145 | [Multi-Scale Wavelet LSTM Cross-Sectional Alpha Ranker](multi-scale-wavelet-lstm-cross-sectional-alpha-ranker.md) | 145 | No |
| RK146 | [Connors RSI-2 Mean Reversion](connors-rsi-2-mean-reversion.md) | 146 | No |
| RK147 | [Moving-Average Z-Score Reversion](moving-average-z-score-reversion.md) | 147 | Partial (Q9) |
| RK148 | [Williams %R Reversal](williams-r-reversal.md) | 148 | Partial (V15) |
| RK149 | [Gap-Fade Strategy](gap-fade-strategy.md) | 149 | No |
| RK150 | [VWAP Reversion](vwap-reversion.md) | 150 | Research code (C-MS3) |
| RK151 | [Short-Term Stock Reversal](short-term-stock-reversal.md) | 151 | Research code (C-MR1) |
| RK152 | [Same-Calendar-Month Seasonality](same-calendar-month-seasonality.md) | 152 | No |
| RK153 | [Turn-of-the-Month Effect](turn-of-the-month-effect.md) | 153 | No |
| RK154 | [Overnight Equity Anomaly](overnight-equity-anomaly.md) | 154 | Research code |
| RK155 | [Wasserstein Distributionally Robust Neural Operator Portfolio Optimization](wasserstein-distributionally-robust-neural-operator-portfolio-optimization.md) | 155 | Research code |
| RK156 | [Neural Operator Delay-Differential Stochastic Control Portfolio Optimization](neural-operator-delay-differential-stochastic-control-portfolio-optimization.md) | 156 | Research code |
| RK157 | [Wasserstein Distributionally Robust Neural Operator Optimal Portfolio](wasserstein-distributionally-robust-neural-operator-optimal-portfolio.md) | 157 | Research code |
| RK158 | [Fractional Cointegration Multiscale Wavelet Arbitrage](fractional-cointegration-multiscale-wavelet-arbitrage.md) | 158 | Research code |
| RK159 | [Koopman Operator Non-Linear Cointegration Spread Strategy](koopman-operator-non-linear-cointegration-spread-strategy.md) | 159 | Research code |
| RK160 | [RSI Oversold/Overbought Reversion](rsi-oversold-overbought-reversion.md) | 160 | Yes (Q10, V3) |
| RK161 | [Bollinger Band Mean Reversion](bollinger-band-mean-reversion.md) | 161 | Partial (Q9, X4) |
| RK162 | [Stochastic Oscillator Reversal](stochastic-oscillator-reversal.md) | 162 | Partial (V15) |
| RK163 | [FX Mean-Reversion / Momentum Hybrid](fx-mean-reversion-momentum-hybrid.md) | 163 | No |
| RK164 | [Grid / Price-Ladder Trading](grid-price-ladder-trading.md) | 164 | Yes (V1, V2, V3, V4, V5, C-G2, C-G3, C-G4) |
| RK165 | [Fractional Order Cointegration Dynamic Copula Portfolio Optimizer](fractional-order-cointegration-dynamic-copula-portfolio-optimizer.md) | 165 | Research code |
| RK166 | [Calendar / Diagonal Spread](calendar-diagonal-spread.md) | 166 | Research code |
| RK167 | [Delta-Hedged Volatility Arbitrage](delta-hedged-volatility-arbitrage.md) | 167 | Research code |
| RK168 | [VIX Futures Term-Structure Strategy](vix-futures-term-structure-strategy.md) | 168 | Partial |
| RK169 | [Volatility Skew Risk Premium](volatility-skew-risk-premium.md) | 169 | Research code |
| RK170 | [Earnings Volatility Crush / Delta-Hedged Event Options](earnings-volatility-crush-delta-hedged-event-options.md) | 170 | Research code |
| RK171 | [Put-Call Parity Conversion / Reversal Arbitrage](put-call-parity-conversion-reversal-arbitrage.md) | 171 | Research code |
| RK172 | [Box-Spread Financing Arbitrage](box-spread-financing-arbitrage.md) | 172 | Research code |
| RK173 | [Broken-Wing Butterfly](broken-wing-butterfly.md) | 173 | Research code |
| RK174 | [Put Debit Spread Momentum](put-debit-spread-momentum.md) | 174 | Research code |
| RK175 | [Quantum Approximate Optimization Algorithm (QAOA) Allocation](quantum-approximate-optimization-algorithm-qaoa-allocation.md) | 175 | Research code |
| RK176 | [Rough Heston Stochastic Volatility Calibration](rough-heston-stochastic-volatility-calibration.md) | 176 | Research code |
| RK177 | [Variational Autoencoder (VAE) Latent Yield Curve Arbitrage](variational-autoencoder-vae-latent-yield-curve-arbitrage.md) | 177 | Research code |
| RK178 | [Manifold Learning Diffusion Map Statistical Arbitrage](manifold-learning-diffusion-map-statistical-arbitrage.md) | 178 | No |
| RK179 | [Fractional Order Kalman Filter Dynamic Hedging](fractional-order-kalman-filter-dynamic-hedging.md) | 179 | Research code |
| RK180 | [Persistent Homology Betti-1 Loop Topological Momentum Strategy](persistent-homology-betti-1-loop-topological-momentum-strategy.md) | 180 | Research code |
| RK181 | [Wasserstein Distributionally Robust Mean-CVaR Dynamic Allocation](wasserstein-distributionally-robust-mean-cvar-dynamic-allocation.md) | 181 | Research code |
| RK182 | [Quantum Annealing Graph Partitioning Statistical Arbitrage](quantum-annealing-graph-partitioning-statistical-arbitrage.md) | 182 | Research code |
| RK183 | [Persistent Homology Betti-0 Multiscale Clustering Arbitrage](persistent-homology-betti-0-multiscale-clustering-arbitrage.md) | 183 | Research code |
| RK184 | [Quantum Approximate Optimization Algorithm (QAOA) Max-Cut Statistical Arbitrage](quantum-approximate-optimization-algorithm-qaoa-max-cut-statistical-arbitrage.md) | 184 | Research code |
| RK185 | [Riemannian Manifold Metric Hierarchical Risk Parity](riemannian-manifold-metric-hierarchical-risk-parity.md) | 185 | Research code |
| RK186 | [Quantum Annealing Binary Matrix Factorization Statistical Arbitrage](quantum-annealing-binary-matrix-factorization-statistical-arbitrage.md) | 186 | Research code |
| RK187 | [Persistent Homology Betti-0 Connected Component Risk Parity](persistent-homology-betti-0-connected-component-risk-parity.md) | 187 | Research code |
| RK188 | [Riemannian Manifold Metric Persistent Homology Risk Parity](riemannian-manifold-metric-persistent-homology-risk-parity.md) | 188 | Research code |
| RK189 | [Persistent Homology Betti-1 Cyclical Persistence Landscape Arbitrage](persistent-homology-betti-1-cyclical-persistence-landscape-arbitrage.md) | 189 | Research code |
| RK190 | [Neural Rough Path Signature Hawkes Jump-Diffusion Spread Arbitrage](neural-rough-path-signature-hawkes-jump-diffusion-spread-arbitrage.md) | 190 | Research code |
| RK191 | [Graph Attention Network Riemannian Manifold Dynamic Risk Parity](graph-attention-network-riemannian-manifold-dynamic-risk-parity.md) | 191 | Research code |
| RK192 | [Quantum Annealing Maximum Independent Set Statistical Arbitrage](quantum-annealing-maximum-independent-set-statistical-arbitrage.md) | 192 | Research code |
| RK193 | [Persistent Homology Betti-0 Persistence Landscape Clustering Arbitrage](persistent-homology-betti-0-persistence-landscape-clustering-arbitrage.md) | 193 | Research code |
| RK194 | [Fixed Fractional / Fixed Dollar Risk](fixed-fractional-fixed-dollar-risk.md) | 194 | Yes |
| RK195 | [GARCH Volatility Forecasting with Mean-Reversion Channel](garch-volatility-forecasting-with-mean-reversion-channel.md) | 195 | Research code |
| RK196 | [Randomized Matrix Pencil Lead-Lag Cross-Asset Predictor](randomized-matrix-pencil-lead-lag-cross-asset-predictor.md) | 196 | Research code |
| RK197 | [Topological Persistent Betti Curve Macro Regime Switcher](topological-persistent-betti-curve-macro-regime-switcher.md) | 197 | Research code |
| RK198 | [Wasserstein Generative Adversarial Network Multi-Asset Allocation (WGAN-MA)](wasserstein-generative-adversarial-network-multi-asset-allocation-wgan-ma.md) | 198 | Research code |
| RK199 | [Persistent Homology Betti-1 Persistence Landscape Arbitrage](persistent-homology-betti-1-persistence-landscape-arbitrage.md) | 199 | Research code |
| RK200 | [Generative Score-Based Diffusion Multi-Asset Scenario Synthesizer](generative-score-based-diffusion-multi-asset-scenario-synthesizer.md) | 200 | Research code |
| RK201 | [Koopman Operator Predictive Control Statistical Arbitrage](koopman-operator-predictive-control-statistical-arbitrage.md) | 201 | Research code |
| RK202 | [Fractional Brownian Motion Multi-Scale Trend Scanning Strategy](fractional-brownian-motion-multi-scale-trend-scanning-strategy.md) | 202 | Research code |
| RK203 | [Koopman Operator Model Predictive Control Spread Equilibrium](koopman-operator-model-predictive-control-spread-equilibrium.md) | 203 | Research code |
| RK204 | [Lead-Lag Cross-Asset Predictive Trading](lead-lag-cross-asset-predictive-trading.md) | 204 | Research code |
| RK205 | [Dynamic Tensor Decomposition Multi-Asset Factor Rotation](dynamic-tensor-decomposition-multi-asset-factor-rotation.md) | 205 | Research code |
| RK206 | [Koopman Operator Model Predictive Control Multi-Asset Allocation](koopman-operator-model-predictive-control-multi-asset-allocation.md) | 206 | Research code |
| RK207 | [Standardized Unexpected Earnings (SUE)](standardized-unexpected-earnings-sue.md) | 207 | Research code |
| RK208 | [Anchored VWAP Reclaim / Rejection](anchored-vwap-reclaim-rejection.md) | 208 | Partial (C-MS3) |
| RK209 | [Corporate Buyback Announcement Drift](corporate-buyback-announcement-drift.md) | 209 | Research code |
| RK210 | [Index Reconstitution / Rebalance Event Trading](index-reconstitution-rebalance-event-trading.md) | 210 | Research code |
| RK211 | [Macro Surprise / Economic Release Strategy](macro-surprise-economic-release-strategy.md) | 211 | Partial (V6) |
| RK212 | [Market Breadth Thrust](market-breadth-thrust.md) | 212 | Research code |
| RK213 | [Trend-Scanning Label Model](trend-scanning-label-model.md) | 213 | Research code (C-ML1) |
| RK214 | [XGBoost Cross-Sectional Ranking](xgboost-cross-sectional-ranking.md) | 214 | Research code |
| RK215 | [Cross-Sectional Reversal with Risk Neutralization](cross-sectional-reversal-with-risk-neutralization.md) | 215 | Partial (C-MR1) |
| RK216 | [Top-K with Dropout Portfolio Rotation](top-k-with-dropout-portfolio-rotation.md) | 216 | Research code |
| RK217 | [Bayesian Structural Time Series (BSTS) Causal Impact Macro Strategy](bayesian-structural-time-series-bsts-causal-impact-macro-strategy.md) | 217 | Research code |
| RK218 | [Sparse Bayesian Learning Dynamic Factor Model](sparse-bayesian-learning-dynamic-factor-model.md) | 218 | Research code |
| RK219 | [Dynamic Mode Decomposition (DMD) Market Mode Predictor](dynamic-mode-decomposition-dmd-market-mode-predictor.md) | 219 | Research code |
| RK220 | [Continuous-Time Mean-Variance Reinforcement Learning Agent](continuous-time-mean-variance-reinforcement-learning-agent.md) | 220 | Research code |
| RK221 | [Information-Theoretic Transfer Entropy Lead-Lag Strategy](information-theoretic-transfer-entropy-lead-lag-strategy.md) | 221 | Research code |
| RK222 | [Maximum Entropy Production Rate Macro Allocator](maximum-entropy-production-rate-macro-allocator.md) | 222 | Research code |
| RK223 | [Quantum Tensor Network Portfolio Optimization](quantum-tensor-network-portfolio-optimization.md) | 223 | Research code |
| RK224 | [Deep Latent Force Model (LFM) Interest Rate Forecaster](deep-latent-force-model-lfm-interest-rate-forecaster.md) | 224 | Research code |
| RK225 | [Wasserstein Distributionally Robust Mean-Variance Allocation](wasserstein-distributionally-robust-mean-variance-allocation.md) | 225 | Research code |
| RK226 | [Functional Principal Component Analysis (FPCA) Yield Curve Forecaster](functional-principal-component-analysis-fpca-yield-curve-forecaster.md) | 226 | Research code |
| RK227 | [Multi-Agent Evolutionary Reinforcement Learning Portfolio Optimizer](multi-agent-evolutionary-reinforcement-learning-portfolio-optimizer.md) | 227 | Research code |
| RK228 | [Deep Generative Flow Matching Portfolio Generator](deep-generative-flow-matching-portfolio-generator.md) | 228 | Research code |
| RK229 | [Quantum Adiabatic Optimal Portfolio Rebalancing](quantum-adiabatic-optimal-portfolio-rebalancing.md) | 229 | Research code |
| RK230 | [Riemannian Manifold Metric Optimization Portfolio](riemannian-manifold-metric-optimization-portfolio.md) | 230 | Research code |
| RK231 | [Riemannian Manifold Metric Diffusion Portfolio Allocation](riemannian-manifold-metric-diffusion-portfolio-allocation.md) | 231 | Research code |
| RK232 | [Graph Attention Network Covariance Shrinkage Estimator](graph-attention-network-covariance-shrinkage-estimator.md) | 232 | Research code |
| RK233 | [Riemannian Manifold Metric Wasserstein Robust Allocation](riemannian-manifold-metric-wasserstein-robust-allocation.md) | 233 | Research code |
| RK234 | [Wasserstein Distributionally Robust Reinforcement Learning Portfolio Agent](wasserstein-distributionally-robust-reinforcement-learning-portfolio-agent.md) | 234 | Research code |
| RK235 | [Graph Attention Network Covariance Matrix Shrinkage Dynamic Allocation](graph-attention-network-covariance-matrix-shrinkage-dynamic-allocation.md) | 235 | Research code |
| RK236 | [Quantum Adiabatic Graph Neural Network Portfolio Optimization](quantum-adiabatic-graph-neural-network-portfolio-optimization.md) | 236 | Research code |
| RK237 | [Riemannian Manifold Metric Graph Attention Portfolio Allocation](riemannian-manifold-metric-graph-attention-portfolio-allocation.md) | 237 | Research code |
| RK238 | [Quantum Adiabatic Tensor Network Portfolio Optimization](quantum-adiabatic-tensor-network-portfolio-optimization.md) | 238 | Research code |
| RK239 | [Fractional Order Vector Error Correction Neural Network Portfolio Allocator](fractional-order-vector-error-correction-neural-network-portfolio-allocator.md) | 239 | Research code |
| RK240 | [Neural Operator Delay-Differential Stochastic Volatility Calibrator](neural-operator-delay-differential-stochastic-volatility-calibrator.md) | 240 | Research code |
| RK241 | [Koopman Operator Multi-Factor Equity Risk Factor Tracking](koopman-operator-multi-factor-equity-risk-factor-tracking.md) | 241 | Research code |
| RK242 | [Long-Volatility Breakout (Options)](long-volatility-breakout-options.md) | 242 | Research code (Q12) |
| RK243 | [Price/Volume Anomaly Detection](price-volume-anomaly-detection.md) | 243 | Partial (A8) |
| RK244 | [Liquidity-Aware Adaptive Execution](liquidity-aware-adaptive-execution.md) | 244 | Partial |
| RK245 | [Pure Passive Market Making](pure-passive-market-making.md) | 245 | Research code (C-MM1, C-MM2) |
| RK246 | [Inventory-Skewed Market Making](inventory-skewed-market-making.md) | 246 | Research code (C-G2, C-MM1) |
| RK247 | [VPIN Flow-Toxicity Filter](vpin-flow-toxicity-filter.md) | 247 | Research code (C-MM4) |
| RK248 | [Hawkes-Process Order-Flow Forecast](hawkes-process-order-flow-forecast.md) | 248 | Research code |
| RK249 | [Iceberg / Reserve-Order Execution](iceberg-reserve-order-execution.md) | 249 | Research code |
| RK250 | [Arrival-Price Adaptive Limit-vs-Market Execution](arrival-price-adaptive-limit-vs-market-execution.md) | 250 | Partial |
| RK251 | [Intraday Volume-Profile Execution](intraday-volume-profile-execution.md) | 251 | Research code |
| RK252 | [Order-Flow Imbalance (OFI) Cross-Sectional Alpha Predictor](order-flow-imbalance-ofi-cross-sectional-alpha-predictor.md) | 252 | Partial (C-MS1) |
| RK253 | [Information-Driven Volume Clock Imbalance Momentum](information-driven-volume-clock-imbalance-momentum.md) | 253 | Partial (C-ML5) |
| RK254 | [Persistent Homology Topological Data Analysis (TDA) Crash Predictor](persistent-homology-topological-data-analysis-tda-crash-predictor.md) | 254 | Research code |
| RK255 | [Persistent Homology Topological Landscape Crisis Predictor](persistent-homology-topological-landscape-crisis-predictor.md) | 255 | Research code |
| RK256 | [Deep Markov State-Space Intraday Volume Profile Predictor](deep-markov-state-space-intraday-volume-profile-predictor.md) | 256 | Research code |
| RK257 | [Information-Theoretic Causality Flow Macro Asset Allocator](information-theoretic-causality-flow-macro-asset-allocator.md) | 257 | Research code |
| RK258 | [Spiking Graph Convolutional Network (SGCN) Contagion Predictor](spiking-graph-convolutional-network-sgcn-contagion-predictor.md) | 258 | Research code |
| RK259 | [Hawkes-Driven Non-Parametric Order Flow Toxicity Filter](hawkes-driven-non-parametric-order-flow-toxicity-filter.md) | 259 | Research code |
| RK260 | [Quantum Approximate State Preparation Risk Mapping](quantum-approximate-state-preparation-risk-mapping.md) | 260 | Research code |
| RK261 | [Koopman Operator Model Predictive Control Risk Mitigation](koopman-operator-model-predictive-control-risk-mitigation.md) | 261 | Research code |
| RK262 | [Persistent Homology Betti-0 Connected Component Contagion Detector](persistent-homology-betti-0-connected-component-contagion-detector.md) | 262 | Research code |
| RK263 | [Topological Persistence Diagram Clustering Crisis Detector](topological-persistence-diagram-clustering-crisis-detector.md) | 263 | Research code |
| RK264 | [Information-Theoretic Directed GNN Contagion Model](information-theoretic-directed-gnn-contagion-model.md) | 264 | Research code |
| RK265 | [Persistent Homology Betti-2 3D Void Macro Stress Predictor](persistent-homology-betti-2-3d-void-macro-stress-predictor.md) | 265 | Research code |
| RK266 | [Riemannian Manifold Metric Entropic Risk Portfolio](riemannian-manifold-metric-entropic-risk-portfolio.md) | 266 | Research code |
| RK267 | [Graph Attention Network Covariance Matrix Spectral Regularization](graph-attention-network-covariance-matrix-spectral-regularization.md) | 267 | Research code |
| RK268 | [Persistent Homology Multi-Scale Vietoris-Rips Filtration Risk Scoring](persistent-homology-multi-scale-vietoris-rips-filtration-risk-scoring.md) | 268 | Research code |
| RK269 | [Persistent Homology Betti-0 Multiscale Filtration Contagion Clustering](persistent-homology-betti-0-multiscale-filtration-contagion-clustering.md) | 269 | Partial (A5) |
| RK270 | [Quantum Annealing Binary Matrix Factorization Portfolio Risk Model](quantum-annealing-binary-matrix-factorization-portfolio-risk-model.md) | 270 | Research code |
| RK271 | [Sequential Bootstrapping Sample Weights](sequential-bootstrapping-sample-weights.md) | 271 | Research code |
| RK272 | [Wavelet-Neural Network Hybrid Intraday Trend Scalper](wavelet-neural-network-hybrid-intraday-trend-scalper.md) | 272 | Research code |
| RK273 | [Deep Koopman-Inspired Spectral Asset Allocation](deep-koopman-inspired-spectral-asset-allocation.md) | 273 | Research code |
| RK274 | [Avellaneda–Stoikov Market Making](avellaneda-stoikov-market-making.md) | 274 | Research code (C-MM1) |
| RK275 | [DeepLOB-Style Order-Book Forecasting](deeplob-style-order-book-forecasting.md) | 275 | Research code |
| RK276 | [Queue-Reactive Market Making](queue-reactive-market-making.md) | 276 | Partial (C-MM5) |
| RK277 | [Hawkes Process Multi-Dimensional Order Flow Intensity Model](hawkes-process-multi-dimensional-order-flow-intensity-model.md) | 277 | Research code |
| RK278 | [Cross-Venue Crypto Triangular Arbitrage](cross-venue-crypto-triangular-arbitrage.md) | 278 | Research code (A7) |
| RK279 | [Asynchronous Multi-Exchange Spatial Arbitrage Graph](asynchronous-multi-exchange-spatial-arbitrage-graph.md) | 279 | Research code (A7) |
| RK280 | [Recurrent Neural Hawkes Point Process Toxic Flow Hedging Trigger](recurrent-neural-hawkes-point-process-toxic-flow-hedging-trigger.md) | 280 | Research code |
| RK281 | [Covered Call / Buy-Write](covered-call-buy-write.md) | 281 | Research code (S1) |
| RK282 | [Put-Write / Cash-Secured Put](put-write-cash-secured-put.md) | 282 | Research code (S1) |
| RK283 | [Wasserstein Distributionally Robust Neural Stochastic Control Hedging](wasserstein-distributionally-robust-neural-stochastic-control-hedging.md) | 283 | Research code |
| RK284 | [Options Wheel](options-wheel.md) | 284 | Research code (S1) |
| RK285 | [Iron Condor / Short Premium Range Strategy](iron-condor-short-premium-range-strategy.md) | 285 | Research code |
| RK286 | [Iron Butterfly Credit Strategy](iron-butterfly-credit-strategy.md) | 286 | Research code |
| RK287 | [Neural Operator Delay Differential Equation (Delay-ODE) Term Structure Predictor](neural-operator-delay-differential-equation-delay-ode-term-structure-predictor.md) | 287 | Research code |
| RK288 | [Neural Controlled Differential Equation (Neural CDE) Point Process Execution](neural-controlled-differential-equation-neural-cde-point-process-execution.md) | 288 | Research code |
| RK289 | [Neural Operator Delay-Differential Hawkes Microstructure Predictor](neural-operator-delay-differential-hawkes-microstructure-predictor.md) | 289 | Research code |
| RK290 | [Random Forest Return Classification](random-forest-return-classification.md) | 290 | Research code |
| RK291 | [Gradient-Boosted Trees Return Prediction](gradient-boosted-trees-return-prediction.md) | 291 | Yes (V13, V14) |
| RK292 | [LSTM Sequence Forecasting](lstm-sequence-forecasting.md) | 292 | Research code (C-RJ4) |
| RK293 | [News / Financial Sentiment NLP](news-financial-sentiment-nlp.md) | 293 | Research code |
| RK294 | [Triple-Barrier Labeled ML Strategy](triple-barrier-labeled-ml-strategy.md) | 294 | Partial (C-ML1) |
| RK295 | [Conformal Prediction Uncertainty Wrapper (CP-MAPIE)](conformal-prediction-uncertainty-wrapper-cp-mapie.md) | 295 | Research code (V13) |
| RK296 | [Dynamic Copula-Vine Regularized Factor Allocation](dynamic-copula-vine-regularized-factor-allocation.md) | 296 | Research code |
| RK297 | [Fractional Hurst-Driven Adaptive Bandwidth Mean Reversion](fractional-hurst-driven-adaptive-bandwidth-mean-reversion.md) | 297 | Partial (C-MR4) |
| RK298 | [AMM / CLOB Cross-Venue Arbitrage](amm-clob-cross-venue-arbitrage.md) | 298 | Research code |
| RK299 | [Dynamic AMM Liquidity Provision / Liquidity Mining](dynamic-amm-liquidity-provision-liquidity-mining.md) | 299 | Research code |
| RK300 | [Fractional Differentiation Feature Pipeline](fractional-differentiation-feature-pipeline.md) | 300 | Research code (C-ML5) |
| RK301 | [Temporal Fusion Transformer Forecasting](temporal-fusion-transformer-forecasting.md) | 301 | Research code |
| RK302 | [Physics-Informed Deep Galerkin Method (DGM) Option Solver](physics-informed-deep-galerkin-method-dgm-option-solver.md) | 302 | Research code |
| RK303 | [Neural Jump-Diffusion Rough Heston Smile Predictor](neural-jump-diffusion-rough-heston-smile-predictor.md) | 303 | Research code |
| RK304 | [Recurrent Neural Hawkes Point Process Volatility Jump Forecaster](recurrent-neural-hawkes-point-process-volatility-jump-forecaster.md) | 304 | Research code |
| RK305 | [Quantum Annealing Binary Quadratic Portfolio Rebalancing](quantum-annealing-binary-quadratic-portfolio-rebalancing.md) | 305 | Research code |
| RK306 | [Microprice / Queue-Imbalance Signal](microprice-queue-imbalance-signal.md) | 306 | Research code (C-MS2) |
| RK307 | [Cross-Exchange Market Making (XEMM)](cross-exchange-market-making-xemm.md) | 307 | Research code |
| RK308 | [Dividend Capture Window Strategy](dividend-capture-window-strategy.md) | 308 | Research code |
| RK309 | [Gamma Scalping / Long-Gamma Rebalancing](gamma-scalping-long-gamma-rebalancing.md) | 309 | Research code |
| RK310 | [Multi-Agent RL Execution / Liquidation](multi-agent-rl-execution-liquidation.md) | 310 | Research code |
| RK311 | [FinBERT Sentiment-Driven Event Arbitrage](finbert-sentiment-driven-event-arbitrage.md) | 311 | Research code |
| RK312 | [Deep Q-Network (DQN) Liquidation Agent](deep-q-network-dqn-liquidation-agent.md) | 312 | Research code |
| RK313 | [Adaptive Mesh Reinforcement Learning Market Maker (RL-MM)](adaptive-mesh-reinforcement-learning-market-maker-rl-mm.md) | 313 | Research code |
| RK314 | [Hawkes-Jump Diffusion Multivariate Event Detection](hawkes-jump-diffusion-multivariate-event-detection.md) | 314 | Research code |
| RK315 | [Empirical Mode Decomposition (EMD) Hilbert-Huang Intraday Scalper](empirical-mode-decomposition-emd-hilbert-huang-intraday-scalper.md) | 315 | Research code |
| RK316 | [Temporal CNN / TCN Forecasting](temporal-cnn-tcn-forecasting.md) | 316 | Research code |
| RK317 | [Meta-Labeling Primary Signals](meta-labeling-primary-signals.md) | 317 | Yes (V13, C-ML1) |
| RK318 | [Graph Convolutional Network (GCN) Cross-Sectional Stock Ranking](graph-convolutional-network-gcn-cross-sectional-stock-ranking.md) | 318 | Research code |
| RK319 | [Vol-Harvesting Dynamic Asymmetric Grid](vol-harvesting-dynamic-asymmetric-grid.md) | 319 | Yes (V3, V5, C-G3) |
| RK320 | [Koopman Operator Non-Linear Volatility Surface Interpolator](koopman-operator-non-linear-volatility-surface-interpolator.md) | 320 | Research code |
| RK321 | [Koopman Operator Non-Linear Volatility Surface Pricing Model](koopman-operator-non-linear-volatility-surface-pricing-model.md) | 321 | Research code |
| RK322 | [Order-Book Imbalance Signal](order-book-imbalance-signal.md) | 322 | Research code (C-MS2) |
| RK323 | [Physics-Informed Neural Operator (FNO) Yield Curve Dynamics](physics-informed-neural-operator-fno-yield-curve-dynamics.md) | 323 | Research code |
| RK324 | [Wasserstein Distributionally Robust Neural SDE Hedging](wasserstein-distributionally-robust-neural-sde-hedging.md) | 324 | Research code |
| RK325 | [Neural Operator Controlled Portfolio Dynamic Hedging](neural-operator-controlled-portfolio-dynamic-hedging.md) | 325 | Research code |
| RK326 | [Neural Operator Functional Gradient Boosting Cross-Sectional Alpha](neural-operator-functional-gradient-boosting-cross-sectional-alpha.md) | 326 | Research code |
| RK327 | [Domain-Adversarial Neural Network (DANN) Cross-Market Alpha Transfer](domain-adversarial-neural-network-dann-cross-market-alpha-transfer.md) | 327 | Research code |
| RK328 | [Neural Rough Volatility Path Signature Factor Model](neural-rough-volatility-path-signature-factor-model.md) | 328 | Research code |
| RK329 | [Wasserstein Distributionally Robust Neural Rough Volatility Hedging](wasserstein-distributionally-robust-neural-rough-volatility-hedging.md) | 329 | Research code |
| RK330 | [Neural Rough Path Signature Delay-Differential Portfolio Control](neural-rough-path-signature-delay-differential-portfolio-control.md) | 330 | Research code |
| RK331 | [Neural Rough Differential Equation (Neural RDE) LOB Forecaster](neural-rough-differential-equation-neural-rde-lob-forecaster.md) | 331 | Research code |
| RK332 | [Generative Score-Based Flow Matching Order Flow Generator](generative-score-based-flow-matching-order-flow-generator.md) | 332 | Research code |
| RK333 | [Neural Jump-Diffusion Hawkes Point Process Shock Detector](neural-jump-diffusion-hawkes-point-process-shock-detector.md) | 333 | Research code |
| RK334 | [Neural Controlled Differential Equation LOB Trend Anticipator](neural-controlled-differential-equation-lob-trend-anticipator.md) | 334 | Research code |
| RK335 | [Wasserstein Distributionally Robust RL Market Making](wasserstein-distributionally-robust-rl-market-making.md) | 335 | Research code |
| RK336 | [Score-Based Generative Diffusion Limit Order Book Simulator](score-based-generative-diffusion-limit-order-book-simulator.md) | 336 | Research code |
| RK337 | [Neural Controlled Jump Diffusion Order Book Pricing Model](neural-controlled-jump-diffusion-order-book-pricing-model.md) | 337 | Research code |
| RK338 | [Recurrent Neural Hawkes Point Process Liquidity Shock Detector](recurrent-neural-hawkes-point-process-liquidity-shock-detector.md) | 338 | Research code |
| RK339 | [Multi-Agent Reinforcement Learning Nash Market Maker](multi-agent-reinforcement-learning-nash-market-maker.md) | 339 | Research code |
| RK340 | [Fractional Order Cointegration Vector Error Correction Neural Network](fractional-order-cointegration-vector-error-correction-neural-network.md) | 340 | Research code |
| RK341 | [Multi-Agent Reinforcement Learning Stackelberg Market Maker](multi-agent-reinforcement-learning-stackelberg-market-maker.md) | 341 | Research code |
| RK342 | [Neural Rough Path Signature Hawkes Point Process Forecaster](neural-rough-path-signature-hawkes-point-process-forecaster.md) | 342 | Research code |
| RK343 | [Generative Score-Based Diffusion Limit Order Book Flow Synthesizer](generative-score-based-diffusion-limit-order-book-flow-synthesizer.md) | 343 | Research code |
| RK344 | [Multi-Agent Reinforcement Learning Stackelberg Market Maker Equilibrium](multi-agent-reinforcement-learning-stackelberg-market-maker-equilibrium.md) | 344 | Research code |
| RK345 | [Multi-Agent Reinforcement Learning Stackelberg Spread Capture](multi-agent-reinforcement-learning-stackelberg-spread-capture.md) | 345 | Research code |
| RK346 | [SAC Continuous-Action Trading Agent](sac-continuous-action-trading-agent.md) | 346 | Research code (A1) |
| RK347 | [DDPG / TD3 Continuous-Control Trader](ddpg-td3-continuous-control-trader.md) | 347 | Research code (A1) |
| RK348 | [Phase Space Reconstructed Neural ODE (PSR-NODE)](phase-space-reconstructed-neural-ode-psr-node.md) | 348 | Research code |
| RK349 | [Time-Series Generative Adversarial Network (TimeGAN)](time-series-generative-adversarial-network-timegan.md) | 349 | Research code |
| RK350 | [Physics-Informed Deep Learning Schrödinger Volatility Solver](physics-informed-deep-learning-schrodinger-volatility-solver.md) | 350 | Research code |
| RK351 | [Multi-Agent Deep Deterministic Policy Gradient (MADDPG) Portfolio Allocation](multi-agent-deep-deterministic-policy-gradient-maddpg-portfolio-allocation.md) | 351 | Research code |
| RK352 | [Deep Hedging with Transaction Costs and Friction](deep-hedging-with-transaction-costs-and-friction.md) | 352 | Research code |
| RK353 | [Recurrent Neural Hawkes Point Process Execution Timing](recurrent-neural-hawkes-point-process-execution-timing.md) | 353 | Research code |
| RK354 | [Multi-Agent Reinforcement Learning Evolutionary Market Maker](multi-agent-reinforcement-learning-evolutionary-market-maker.md) | 354 | Research code |
| RK355 | [Recurrent Neural Hawkes Point Process Toxic Flow Execution](recurrent-neural-hawkes-point-process-toxic-flow-execution.md) | 355 | Research code |
| RK356 | [Recurrent Neural Hawkes Point Process Dynamic Inventory Market Maker](recurrent-neural-hawkes-point-process-dynamic-inventory-market-maker.md) | 356 | Research code |
| RK357 | [Recurrent Neural Hawkes Point Process Toxic Flow Execution Pauser](recurrent-neural-hawkes-point-process-toxic-flow-execution-pauser.md) | 357 | Research code |
| RK358 | [Multi-Agent Reinforcement Learning Evolutionary Execution Routing](multi-agent-reinforcement-learning-evolutionary-execution-routing.md) | 358 | Research code |
| RK359 | [Multi-Agent Reinforcement Learning Evolutionary Market Making Equilibrium](multi-agent-reinforcement-learning-evolutionary-market-making-equilibrium.md) | 359 | Research code |
| RK360 | [Multi-Agent Reinforcement Learning Evolutionary Execution Allocator](multi-agent-reinforcement-learning-evolutionary-execution-allocator.md) | 360 | Research code |
| RK361 | [Deep Reinforcement Learning Order Book Market Maker (Marl-MM)](deep-reinforcement-learning-order-book-market-maker-marl-mm.md) | 361 | Research code |
| RK362 | [Koopman Operator Model Predictive Control Execution](koopman-operator-model-predictive-control-execution.md) | 362 | Research code |
| RK363 | [TWAP Execution](twap-execution.md) | 363 | Research code |
| RK364 | [VWAP Execution](vwap-execution.md) | 364 | Research code |
| RK365 | [POV / Percent-of-Volume Execution](pov-percent-of-volume-execution.md) | 365 | Research code |
| RK366 | [Implementation-Shortfall / Almgren–Chriss](implementation-shortfall-almgren-chriss.md) | 366 | Research code |
| RK367 | [Hawkes-Driven Optimal Execution with Transitory Price Impact](hawkes-driven-optimal-execution-with-transitory-price-impact.md) | 367 | Research code |
| RK368 | [Continuous-Time Mean-Field Control Execution](continuous-time-mean-field-control-execution.md) | 368 | Research code |
| RK369 | [Multi-Agent Mean-Field Game Optimal Execution Routing](multi-agent-mean-field-game-optimal-execution-routing.md) | 369 | Research code |
| RK370 | [Wasserstein Distributionally Robust Optimal Execution Trajectory](wasserstein-distributionally-robust-optimal-execution-trajectory.md) | 370 | Research code |
| RK371 | [Wasserstein Distributionally Robust Hawkes Point Process Execution](wasserstein-distributionally-robust-hawkes-point-process-execution.md) | 371 | Research code |
| RK372 | [PPO Reinforcement-Learning Trader](ppo-reinforcement-learning-trader.md) | 372 | Research code (A1) |
| RK373 | [Generative Moment Matching Network (GMMN) Portfolio Simulator](generative-moment-matching-network-gmmn-portfolio-simulator.md) | 373 | Research code |
| RK374 | [Physics-Informed Neural Network (PINN) Burgers Volatility Model](physics-informed-neural-network-pinn-burgers-volatility-model.md) | 374 | Research code |
| RK375 | [Quantum Support Vector Regression (QSVR) Return Predictor](quantum-support-vector-regression-qsvr-return-predictor.md) | 375 | Research code |
| RK376 | [Deep Koopman Operator Market Dynamics Predictor](deep-koopman-operator-market-dynamics-predictor.md) | 376 | Research code |
| RK377 | [Neural SDE Controlled Stochastic Volatility Arbitrage](neural-sde-controlled-stochastic-volatility-arbitrage.md) | 377 | Research code |
| RK378 | [Generative Diffusion Model Trajectory Generator (TabDDPM)](generative-diffusion-model-trajectory-generator-tabddpm.md) | 378 | Research code |
| RK379 | [Fractional Brownian Motion (fBm) Volatility Surface Arbitrage](fractional-brownian-motion-fbm-volatility-surface-arbitrage.md) | 379 | Research code |
| RK380 | [Dynamic Latent Factor Graph Neural Network (FactorGNN)](dynamic-latent-factor-graph-neural-network-factorgnn.md) | 380 | Research code |
| RK381 | [Hyperbolic Graph Neural Networks for Stock Pricing](hyperbolic-graph-neural-networks-for-stock-pricing.md) | 381 | Research code |
| RK382 | [Contractive Autoencoder Latent Factor Anomaly Detection](contractive-autoencoder-latent-factor-anomaly-detection.md) | 382 | Research code |
| RK383 | [Conditional Wasserstein GAN-GP Yield Curve Synthesizer](conditional-wasserstein-gan-gp-yield-curve-synthesizer.md) | 383 | Research code |
| RK384 | [Geometric Deep Learning Non-Euclidean Alpha Predictor](geometric-deep-learning-non-euclidean-alpha-predictor.md) | 384 | Research code |
| RK385 | [Graph Attention Network (GAT) Supply Chain Contagion Stock Predictor](graph-attention-network-gat-supply-chain-contagion-stock-predictor.md) | 385 | Research code |
| RK386 | [Information-Theoretic Transfer Entropy Graph Neural Network Alpha Model](information-theoretic-transfer-entropy-graph-neural-network-alpha-model.md) | 386 | Research code |
| RK387 | [Quantum Kernel-Based SVM Cross-Sectional Alpha Predictor](quantum-kernel-based-svm-cross-sectional-alpha-predictor.md) | 387 | Research code |
| RK388 | [Dynamic Copula-Quantile Regression Neural Network Alpha Model](dynamic-copula-quantile-regression-neural-network-alpha-model.md) | 388 | Research code |
| RK389 | [Quantum Annealing Entropic Value-at-Risk Portfolio Optimization](quantum-annealing-entropic-value-at-risk-portfolio-optimization.md) | 389 | Research code |
| RK390 | [Neural Operator Flow-Matching Cross-Sectional Alpha Forecaster](neural-operator-flow-matching-cross-sectional-alpha-forecaster.md) | 390 | Research code |
| RK391 | [Neural Rough Volatility Fractional signature Deep Hedging](neural-rough-volatility-fractional-signature-deep-hedging.md) | 391 | Research code |
| RK392 | [Fractional Order Vector AutoRegressive (VAR) Macro Allocator](fractional-order-vector-autoregressive-var-macro-allocator.md) | 392 | Research code |
| RK393 | [Quantum Neural Network (QNN) Volatility Surface Forecaster](quantum-neural-network-qnn-volatility-surface-forecaster.md) | 393 | Research code |
| RK394 | [Graph Diffusion Convolutional Network Cross-Sectional Alpha](graph-diffusion-convolutional-network-cross-sectional-alpha.md) | 394 | Research code |
| RK395 | [Generative Score-Based Diffusion Macro Factor Synthesizer](generative-score-based-diffusion-macro-factor-synthesizer.md) | 395 | Research code |
| RK396 | [Riemannian Manifold Metric Graph Diffusion Covariance Estimator](riemannian-manifold-metric-graph-diffusion-covariance-estimator.md) | 396 | Research code |
| RK397 | [Quantum Annealing Graph Neural Network Covariance Shrinkage](quantum-annealing-graph-neural-network-covariance-shrinkage.md) | 397 | Research code |
| RK398 | [Persistent Homology Betti-2 Persistence Landscape Macro Contagion](persistent-homology-betti-2-persistence-landscape-macro-contagion.md) | 398 | Research code |
| RK399 | [Generative Score-Based Diffusion Cross-Sectional Factor Synthesizer](generative-score-based-diffusion-cross-sectional-factor-synthesizer.md) | 399 | Research code |
| RK400 | [Graph Attention Network Riemannian Manifold Covariance Shrinkage](graph-attention-network-riemannian-manifold-covariance-shrinkage.md) | 400 | Research code |
| RK401 | [Persistent Homology Betti-1 Cyclical Persistence Landscape Contagion](persistent-homology-betti-1-cyclical-persistence-landscape-contagion.md) | 401 | Research code |
| RK402 | [Generative Score-Based Diffusion Cross-Sectional Alpha Synthesizer](generative-score-based-diffusion-cross-sectional-alpha-synthesizer.md) | 402 | Research code |
| RK403 | [Persistent Homology Betti-2 Persistence Landscape Macro Fragility](persistent-homology-betti-2-persistence-landscape-macro-fragility.md) | 403 | Research code |
| RK404 | [Graph Attention Network Riemannian Manifold Covariance Diffusion](graph-attention-network-riemannian-manifold-covariance-diffusion.md) | 404 | Research code |
| RK405 | [Generative Score-Based Diffusion Cross-Sectional Ranking Synthesizer](generative-score-based-diffusion-cross-sectional-ranking-synthesizer.md) | 405 | Research code |
| RK406 | [Graph Attention Network Riemannian Manifold Covariance Regularization](graph-attention-network-riemannian-manifold-covariance-regularization.md) | 406 | Research code |
| RK407 | [Spiking Neural Network (SNN) Event-Driven Microstructure Scalper](spiking-neural-network-snn-event-driven-microstructure-scalper.md) | 407 | Research code |
| RK408 | [Neural Jump ODE (NJ-ODE) High-Frequency Price Predictor](neural-jump-ode-nj-ode-high-frequency-price-predictor.md) | 408 | Research code |
| RK409 | [Wasserstein Distributionally Robust Koopman Model Predictive Control](wasserstein-distributionally-robust-koopman-model-predictive-control.md) | 409 | Research code |
| RK410 | [Wasserstein Distributionally Robust Neural Operator Optimal Execution](wasserstein-distributionally-robust-neural-operator-optimal-execution.md) | 410 | Research code |
| RK411 | [Recurrent Neural Hawkes Point Process Dynamic Hedging Scheduler](recurrent-neural-hawkes-point-process-dynamic-hedging-scheduler.md) | 411 | Research code |
| RK412 | [Recurrent Neural Hawkes Point Process Toxic Flow Hedging Allocator](recurrent-neural-hawkes-point-process-toxic-flow-hedging-allocator.md) | 412 | Research code |
| RK413 | [Temporal Fusion Transformer (TFT) Multi-Horizon Price Forecaster](temporal-fusion-transformer-tft-multi-horizon-price-forecaster.md) | 413 | Research code |
| RK414 | [Attention-Based Recurrent Neural Hawkes Point Process Alpha](attention-based-recurrent-neural-hawkes-point-process-alpha.md) | 414 | Research code |
| RK415 | [Koopman Operator Model Predictive Control Portfolio Rebalancing](koopman-operator-model-predictive-control-portfolio-rebalancing.md) | 415 | Research code |
| RK416 | [Koopman Operator Model Predictive Control Dynamic Hedging](koopman-operator-model-predictive-control-dynamic-hedging.md) | 416 | Research code |
| RK417 | [Koopman Operator Model Predictive Control Yield Curve Control](koopman-operator-model-predictive-control-yield-curve-control.md) | 417 | Research code |
| RK418 | [Koopman Operator Model Predictive Control Spread Hedging](koopman-operator-model-predictive-control-spread-hedging.md) | 418 | Research code |
| RK419 | [Reinforcement Learning with Expert Guidance (RLEG) Execution](reinforcement-learning-with-expert-guidance-rleg-execution.md) | 419 | Research code |
| RK420 | [Quantum Annealing Optimal Execution Trajectory Solver](quantum-annealing-optimal-execution-trajectory-solver.md) | 420 | Research code |
| RK421 | [Wasserstein Distributionally Robust RL Execution](wasserstein-distributionally-robust-rl-execution.md) | 421 | Research code |
| RK422 | [Multi-Agent Deep Deterministic Reinforcement Learning Cross-Venue Execution](multi-agent-deep-deterministic-reinforcement-learning-cross-venue-execution.md) | 422 | Research code |
| RK423 | [Multi-Agent Reinforcement Learning Stackelberg Execution Broker](multi-agent-reinforcement-learning-stackelberg-execution-broker.md) | 423 | Research code |
| RK424 | [Wasserstein Distributionally Robust Hawkes Jump-Diffusion Optimal Execution](wasserstein-distributionally-robust-hawkes-jump-diffusion-optimal-execution.md) | 424 | Research code |
| RK425 | [Deep Recurrent Attentive Execution Agent (DR-Attn-Exec)](deep-recurrent-attentive-execution-agent-dr-attn-exec.md) | 425 | Research code |

## Researched concepts (ranks 426–700)

The 275 title-reconstructed rows in ranks 426–700 share 34 descriptions,
researched one page per concept (the ledger's §8C "Researched concepts"
explains why). Members of the same concepts further down the list link
to the same pages. Each concept's methods are research code in
`research/catalog/concepts.py`, indexed by page slug in its `CONCEPTS` table.

| Concept | Task | Members in 426–700 / all | Verdict | Evidence |
|---|---|---|---|---|
| [Model for tail-risk hedging and allocation](concepts/model-for-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 6 / 142 | 🔬 the project's equivalent is the regime exit (V17, N5) | Evidence found |
| [Robust approach to factor risk-parity allocation](concepts/robust-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 3 / 18 | ⏳ for a multi-ETF book · no method-specific evidence | Unable to find more details |
| [Attention-weighted approach to factor risk-parity allocation](concepts/attention-weighted-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 2 / 10 | ⛔ (no evidence) | Unable to find more details |
| [Stochastic-process-based approach to momentum/trend forecasting](concepts/stochastic-process-based-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 28 / 72 | ⏳ as a long-or-cash overlay (as RK1) · ⛔ for stock members | Evidence found |
| [Adaptive approach to momentum/trend forecasting](concepts/adaptive-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 30 / 73 | ⏳ as a long-or-cash overlay (as RK1) · ⛔ for stock members | Evidence found |
| [Dynamical-systems/geometric approach to factor risk-parity allocation](concepts/dynamical-systems-geometric-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 2 / 11 | ⛔ (no evidence) | Unable to find more details |
| [Markov-state-based approach to momentum/trend forecasting](concepts/markov-state-based-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 30 / 74 | 🧪 the regime models exist (C-R3) · ⏳ as a regime input | Evidence found |
| [Dynamical-systems/geometric approach to covariance estimation for portfolio risk](concepts/dynamical-systems-geometric-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 5 / 63 | ⛔ (no evidence) | Unable to find more details |
| [Conformal-prediction-based approach to momentum/trend forecasting](concepts/conformal-prediction-based-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 25 / 62 | 🧪 conformal sizing exists · ⏳ as an uncertainty wrapper | Evidence found |
| [Robust approach to covariance estimation for portfolio risk](concepts/robust-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 4 / 68 | ⏳ for a multi-ETF book | Evidence found |
| [Spectral approach to momentum/trend forecasting](concepts/spectral-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 25 / 66 | ⛔ (no evidence over plain momentum) | Unable to find more details |
| [Attention-weighted approach to covariance estimation for portfolio risk](concepts/attention-weighted-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 4 / 63 | ⛔ (thin evidence) | Needs more info |
| [Copula-based approach to factor risk-parity allocation](concepts/copula-based-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 9 / 69 | ⏳ for a multi-ETF book (CVaR budgets) | Evidence found |
| [Nonlinear approach to factor risk-parity allocation](concepts/nonlinear-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 8 / 62 | ⛔ (no evidence) | Unable to find more details |
| [Variational approach to factor risk-parity allocation](concepts/variational-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 8 / 62 | ⛔ (no evidence) | Unable to find more details |
| [Geometry-aware approach to factor risk-parity allocation](concepts/geometry-aware-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 8 / 63 | ⛔ (no evidence) | Unable to find more details |
| [Path-signature-based approach to factor risk-parity allocation](concepts/path-signature-based-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 13 / 63 | ⛔ (no evidence) | Unable to find more details |
| [Kernel-based approach to factor risk-parity allocation](concepts/kernel-based-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 12 / 62 | ⛔ (no evidence) | Unable to find more details |
| [Evolutionary-optimization-based approach to factor risk-parity allocation](concepts/evolutionary-optimization-based-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 12 / 62 | ⛔ (risk parity is convex; nothing to search) | Unable to find more details |
| [Model for sector allocation](concepts/model-for-sector-allocation.md) | Sector allocation | 2 / 13 | 🧪 relative-strength rotation is built (X3) · unmeasured | Evidence found |
| [Model for regime-aware allocation](concepts/model-for-regime-aware-allocation.md) | Regime-aware allocation | 1 / 12 | 🔬 this is the project's own regime work (V17, N5, N6, C-R3) | Evidence found |
| [Bayesian approach to momentum/trend forecasting](concepts/bayesian-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 5 / 5 | ⏳ via the trend-filter literature · no method-specific evidence | Unable to find more details |
| [Robust approach to momentum/trend forecasting](concepts/robust-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 5 / 7 | ⏳ in principle · no method-specific evidence | Unable to find more details |
| [Copula-based approach to momentum/trend forecasting](concepts/copula-based-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 5 / 7 | ⛔ (no evidence) | Unable to find more details |
| [Nonlinear approach to momentum/trend forecasting](concepts/nonlinear-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 2 / 4 | ⏳ via the trend-filter literature · ⛔ for ML variants | Evidence found |
| [Model for covariance estimation for portfolio risk](concepts/model-for-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 2 / 6 | ⏳ for a multi-ETF book (use shrinkage) | Evidence found |
| [Wavelet-based approach to tail-risk hedging and allocation](concepts/wavelet-based-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 4 / 135 | ⛔ (no evidence) | Unable to find more details |
| [Fractional-order approach to momentum/trend forecasting](concepts/fractional-order-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 2 / 78 | 🧪 the Hurst diagnostic exists (C-MR4) · ⛔ as a forecast | Unable to find more details |
| [Koopman-operator-based approach to factor risk-parity allocation](concepts/koopman-operator-based-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 2 / 10 | ⛔ (no evidence) | Unable to find more details |
| [Dynamical-systems/geometric approach to tail-risk hedging and allocation](concepts/dynamical-systems-geometric-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 4 / 136 | ⛔ (no evidence) | Unable to find more details |
| [Recursive approach to tail-risk hedging and allocation](concepts/recursive-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 3 / 139 | ⏳ as an alternative exit trigger · test against N5 | Evidence found |
| [Diffusion-model-based approach to momentum/trend forecasting](concepts/diffusion-model-based-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 2 / 62 | ⛔ (no evidence) | Unable to find more details |
| [Koopman-operator-based approach to covariance estimation for portfolio risk](concepts/koopman-operator-based-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 1 / 62 | ⛔ (no evidence) | Unable to find more details |
| [Topology-aware approach to momentum/trend forecasting](concepts/topology-aware-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 1 / 62 | ⛔ (no evidence) | Unable to find more details |

### Research gaps

**Needs more info** (a reference is cited or likely exists but could not
be identified or read): RK31, RK44, RK68, RK93; RK219, RK232, RK235,
RK250, RK256, RK259, RK267, RK286; RK331, RK348, RK376, RK382, RK400;
RK406, RK408.

**Unable to find more details** (no published evaluation found by two
searches): RK38, RK64, RK69, RK77, RK78, RK86, RK92, RK94, RK95, RK97,
RK98, RK99, RK100; RK101, RK103, RK104, RK105, RK109, RK113, RK115,
RK118, RK119, RK124, RK126, RK128, RK131, RK135, RK136, RK137, RK138,
RK139, RK140, RK141, RK142, RK143, RK145, RK146, RK148, RK150, RK155,
RK156, RK157, RK158, RK159, RK162, RK165, RK173, RK174, RK177, RK178,
RK179, RK180, RK182, RK183, RK184, RK185, RK186, RK188, RK189, RK190,
RK191, RK192, RK193, RK196, RK197, RK198, RK199; RK201, RK202, RK203,
RK205, RK206, RK208, RK212, RK216, RK217, RK221, RK222, RK224, RK227,
RK228, RK230, RK231, RK233, RK234, RK236, RK237, RK238, RK239, RK240,
RK241, RK243, RK257, RK258, RK261, RK262, RK263, RK264, RK265, RK266,
RK270, RK272, RK273, RK280, RK283, RK287, RK288, RK289, RK297; RK304,
RK307, RK315, RK320, RK321, RK323, RK325, RK326, RK330, RK332, RK333,
RK334, RK335, RK337, RK338, RK339, RK340, RK341, RK342, RK344, RK345,
RK350, RK353, RK354, RK355, RK356, RK357, RK358, RK359, RK360, RK362,
RK365, RK369, RK370, RK371, RK374, RK375, RK380, RK384, RK386, RK387,
RK388, RK389, RK390, RK392, RK393, RK394, RK396, RK397, RK398; RK401,
RK403, RK404, RK409, RK410, RK411, RK412, RK414, RK415, RK416, RK417,
RK418, RK421, RK422, RK423, RK424, RK425.

For the concepts of ranks 426–700, the Evidence column above gives the
status: 1 needs more info, 21 unable to find more details.

[The ledger's table](../algorithm_ledger.md#research-gaps) says what each
one lacks.

## Usefulness triage (ranks 101–199 and 701–14,225)

The 344 concepts not researched with ranks 426–700 hold 11,897 of the
13,800 title-reconstructed rows, all ranked beyond 700; the 34
researched concepts hold the other 1,903, so every row of the ranked
list now has a researched page. The 344 were researched on 2026-10-30 as
a usefulness triage, one page each: each page names the task (from the
shared description) and the method (from the title), gives the evidence
for the task and for the method on it, and adds a "Useful for
volatility-ai" verdict. A task that cannot run under the owner's rules
or on this book (short legs, options, a stock universe, execution at
size, quantum hardware) is Not useful whatever the method. On a task
that fits, a method with published evidence on that task is Worth
testing, or In use when the project already does it; an established
method without such evidence is Reference only; and a method with no
evidence in finance (quantum, topological, Koopman, diffusion,
path-signature, attention and other exotic methods) is Not useful. The
verdicts: 2 in use, 11 worth testing, 80 reference only and 251 not
useful; the in-use and worth-testing concepts hold 310 rows, the
reference-only ones 2,406 and the not-useful ones 9,181. Ranks 101–199
got the same verdicts on their own pages (4 in use, 11 worth testing, 10
reference only, 74 not useful). No code was added for the triage; the
Implemented row of each page names what already exists.

The entries to act on, In use first, then Worth testing:

| Entry | Verdict | Why |
|---|---|---|
| RK129 [Inverse-volatility allocation](inverse-volatility-allocation.md) | ✅ In use | For one instrument it is volatility targeting, which the grid already applies (S4 vol_target). |
| RK160 [RSI oversold/overbought reversion](rsi-oversold-overbought-reversion.md) | ✅ In use | RSI already sizes the grid's lots (V3, a registered strategy) and is researched as a gate (Q10). |
| RK164 [Grid / price-ladder trading](grid-price-ladder-trading.md) | ✅ In use | This is the project: the champion is a volatility-scaled grid on TQQQ (V5). |
| RK194 [Fixed fractional / fixed dollar risk](fixed-fractional-fixed-dollar-risk.md) | ✅ In use | Fixed-fraction sizing is the grid's base sizing (V1); stop-distance sizing does not apply, since the grid uses no stops. |
| [Adaptive approach to regime-aware allocation](concepts/adaptive-approach-to-regime-aware-allocation.md) (concept, 2 rows) | ✅ In use | The project's regime exit already is one: NATR measured against its own trailing median, an adaptive threshold (V17, causal N5). |
| [Adaptive approach to tail-risk hedging and allocation](concepts/adaptive-approach-to-tail-risk-hedging-and-allocation.md) (concept, 1 row) | ✅ In use | Volatility targeting is the adaptive form, and the project already runs it (V18, RK22); Harvey et al. (2018) find it shrinks equities' left tail. |
| RK102 [Hidden Markov model regime switching](hidden-markov-model-regime-switching.md) | ⏳ Worth testing | A regime input to compare against the NATR regime; the Gaussian HMM is already built (C-R3). |
| RK104 [Bayesian online changepoint regime gate](bayesian-online-changepoint-regime-gate.md) | ⏳ Worth testing | A causal changepoint probability is a cheap alternative trigger for the regime exit; no trading study exists, so it must be tested here. |
| RK106 [Hierarchical hidden Markov model regime switcher](hierarchical-hidden-markov-model-hhmm-regime-switcher.md) | ⏳ Worth testing | A two-level bull/bear and volatility regime is plausible, but test it only after the plain HMM (RK102) earns its place. |
| RK127 [Conformal-prediction risk-bounded alpha stacking](conformal-prediction-risk-bounded-alpha-stacking.md) | ⏳ Worth testing | Conformal sizing is already researched for grid lots (V13); stacking needs several alpha sources the project does not have. |
| RK130 [Extreme value theory dynamic tail-risk hedge](extreme-value-theory-evt-dynamic-tail-risk-hedge.md) | ⏳ Worth testing | The put-buying hedge is excluded, but an EVT expected-shortfall forecast is a candidate exposure governor next to the NATR regime. |
| RK132 [Conformal risk-bounded dynamic portfolio allocation](conformal-risk-bounded-dynamic-portfolio-allocation.md) | ⏳ Worth testing | Conformal lot sizing is already researched (V13); this is its leverage-control form, worth a walk-forward test. |
| RK134 [Fractional Kelly position sizing](fractional-kelly-position-sizing.md) | ⏳ Worth testing | A principled cap on lot size or total exposure; the research code exists (C-S2). |
| RK146 [Connors RSI-2 mean reversion](connors-rsi-2-mean-reversion.md) | ⏳ Worth testing | A long-only, single-index dip-buying rule, aligned with the grid; cheap to test as a buy gate, but its evidence is in-sample only. |
| RK153 [Turn-of-the-month effect](turn-of-the-month-effect.md) | ⏳ Worth testing | An index-level, long-only calendar effect with long-run evidence; a cheap test as a lot-size boost or buy gate on TQQQ. |
| RK168 [VIX futures term-structure strategy](vix-futures-term-structure-strategy.md) | ⏳ Worth testing | Trading VIX futures is excluded, but the term structure itself is a candidate regime input; the research code exists. |
| RK195 [GARCH volatility forecast for mean-reversion bands](garch-volatility-forecasting-with-mean-reversion-channel.md) | ⏳ Worth testing | The grid's step already scales with volatility; GARCH is a candidate forecaster for that step, and it is hard to beat. |
| [Model for momentum/trend forecasting](concepts/model-for-momentum-trend-forecasting.md) (concept, 13 rows) | ⏳ Worth testing | Time-series momentum as a long-or-cash overlay on TQQQ (RK1) is the documented form; test it as a regime input against the NATR exit. |
| [Multi-scale approach to momentum/trend forecasting](concepts/multi-scale-approach-to-momentum-trend-forecasting.md) (concept, 2 rows) | ⏳ Worth testing | Blending lookbacks (as Goulding et al. and Keller's 13612W momentum do) is the documented fix for single-lookback lag, and cheap to test. |
| [Multi-scale approach to sector allocation](concepts/multi-scale-approach-to-sector-allocation.md) (concept, 64 rows) | ⏳ Worth testing | Multi-lookback industry momentum is the documented signal in a form X3 can already run; measure it there. |
| [High-frequency approach to momentum/trend forecasting](concepts/high-frequency-approach-to-momentum-trend-forecasting.md) (concept, 4 rows) | ⏳ Worth testing | The first half-hour return predicts the last half-hour on SPY (Gao et al. 2018); built here as an intraday gate (X1), not yet measured. |
| [Multi-scale approach to tail-risk hedging and allocation](concepts/multi-scale-approach-to-tail-risk-hedging-and-allocation.md) (concept, 2 rows) | ⏳ Worth testing | HAR-RV, a daily-weekly-monthly volatility model, is a well-tested forecaster (Corsi 2009); test it as the volatility input to the existing targeting and regime rules. |
| [Bayesian approach to regime-aware allocation](concepts/bayesian-approach-to-regime-aware-allocation.md) (concept, 136 rows) | ⏳ Worth testing | Bayesian online changepoint detection (RK104) is a cheap, causal regime gate to test against the NATR regime. |
| [Multi-scale approach to ETF rotation](concepts/multi-scale-approach-to-etf-rotation.md) (concept, 67 rows) | ⏳ Worth testing | 13612W-style multi-lookback momentum (Keller and Keuning) is the documented refinement of single-lookback rotation; X3 can run it. |
| [Model for leveraged-ETF exposure rebalancing](concepts/model-for-leveraged-etf-exposure-rebalancing.md) (concept, 4 rows) | ⏳ Worth testing | The task is the project's own: a target-exposure rule for TQQQ is a sizing lever to measure beside V18 and N7. |
| [Model for ETF rotation](concepts/model-for-etf-rotation.md) (concept, 5 rows) | ⏳ Worth testing | Long-only ETF rotation with a defensive asset is documented (Faber; Antonacci) and built here (X3, RK3); what is missing is the measurement. |
| [Markov-state-based approach to regime-aware allocation](concepts/markov-state-based-approach-to-regime-aware-allocation.md) (concept, 5 rows) | ⏳ Worth testing | HMM regimes forecast out of sample in the literature (Kritzman et al. 2012) and are built here (C-R3, RK102); test them against the NATR regime. |
| [Adaptive approach to leveraged-ETF exposure rebalancing](concepts/adaptive-approach-to-leveraged-etf-exposure-rebalancing.md) (concept, 5 rows) | ⏳ Worth testing | Scale leverage with recent volatility, which the decay result and the volatility-targeting literature both support and N7 and V18 already implement; measure it on the grid. |

Verdicts by task, for the 344 concepts:

| Task | In use | Worth testing | Reference only | Not useful | Rows |
|---|---|---|---|---|---|
| Regime-aware allocation | 1 | 2 | 5 | 4 | 572 |
| Momentum / trend forecasting |  | 3 | 2 | 1 | 28 |
| ETF rotation |  | 2 | 8 | 8 | 582 |
| Leveraged-ETF exposure rebalancing |  | 2 | 5 | 12 | 577 |
| Tail-risk hedging and allocation | 1 | 1 | 4 | 3 | 32 |
| Sector allocation |  | 1 | 9 | 9 | 569 |
| Macro-driven index allocation |  |  | 13 | 8 | 577 |
| Covariance estimation for portfolio risk |  |  | 8 | 5 | 322 |
| Delay-aware portfolio allocation |  |  | 7 | 8 | 567 |
| Liquidity-shock detection and response |  |  | 7 | 8 | 583 |
| Factor risk-parity allocation |  |  | 5 | 2 | 90 |
| Cross-asset / sector contagion analysis |  |  | 3 | 1 | 542 |
| Index portfolio rebalancing |  |  | 3 | 1 | 16 |
| Robust portfolio optimisation |  |  | 1 |  | 2 |
| Benchmark index tracking |  |  |  | 11 | 576 |
| Candidate alpha-signal generation |  |  |  | 16 | 567 |
| Cointegration / pairs trading |  |  |  | 7 | 17 |
| Cross-sectional stock ranking |  |  |  | 26 | 585 |
| Dependence-aware cointegration / relative-value analysis |  |  |  | 8 | 568 |
| Index / ETF constituent arbitrage |  |  |  | 14 | 582 |
| Neural-operator forecasting |  |  |  | 12 | 542 |
| Path-signature time-series forecasting |  |  |  | 11 | 567 |
| Quantum-circuit or quantum-inspired optimisation |  |  |  | 12 | 542 |
| Statistical-arbitrage basket construction |  |  |  | 15 | 583 |
| Topological-feature portfolio allocation |  |  |  | 8 | 542 |
| Trade-execution optimisation |  |  |  | 19 | 584 |
| Volatility-surface forecasting |  |  |  | 22 | 583 |
| **All 344** | **2** | **11** | **80** | **251** | **11,897** |

### Triaged concepts (ranks 701–14,225)

| Concept | Task | Rows | Best rank | Useful | Evidence |
|---|---|---|---|---|---|
| [Neural-network-based approach to factor risk-parity allocation](concepts/neural-network-based-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 68 | 769 | ⛔ Not useful | Unable to find more details |
| [Model for momentum/trend forecasting](concepts/model-for-momentum-trend-forecasting.md) | Momentum / trend forecasting | 13 | 844 | ⏳ Worth testing | Evidence found |
| [Model for statistical-arbitrage basket construction](concepts/model-for-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 6 | 846 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to statistical-arbitrage basket construction](concepts/attention-weighted-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 7 | 848 | ⛔ Not useful | Unable to find more details |
| [Spectral approach to statistical-arbitrage basket construction](concepts/spectral-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 78 | 849 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to statistical-arbitrage basket construction](concepts/multi-scale-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 5 | 850 | ⛔ Not useful | Unable to find more details |
| [Neural-network-based approach to momentum/trend forecasting](concepts/neural-network-based-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 5 | 851 | ⛔ Not useful | Evidence found |
| [Geometry-aware approach to statistical-arbitrage basket construction](concepts/geometry-aware-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 5 | 852 | ⛔ Not useful | Unable to find more details |
| [Hawkes-process-based approach to statistical-arbitrage basket construction](concepts/hawkes-process-based-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 5 | 854 | ⛔ Not useful | Unable to find more details |
| [Hawkes-process-based approach to dependence-aware cointegration / relative-value analysis](concepts/hawkes-process-based-approach-to-dependence-aware-cointegration-relative-value-a.md) | Dependence-aware cointegration / relative-value analysis | 142 | 883 | ⛔ Not useful | Unable to find more details |
| [Quantum/quantum-inspired approach to dependence-aware cointegration / relative-value analysis](concepts/quantum-quantum-inspired-approach-to-dependence-aware-cointegration-relative-val.md) | Dependence-aware cointegration / relative-value analysis | 136 | 885 | ⛔ Not useful | Unable to find more details |
| [Conformal-prediction-based approach to statistical-arbitrage basket construction](concepts/conformal-prediction-based-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 73 | 886 | ⛔ Not useful | Unable to find more details |
| [Integrated approach to dependence-aware cointegration / relative-value analysis](concepts/integrated-approach-to-dependence-aware-cointegration-relative-value-analysis.md) | Dependence-aware cointegration / relative-value analysis | 135 | 889 | ⛔ Not useful | Unable to find more details |
| [Bayesian approach to dependence-aware cointegration / relative-value analysis](concepts/bayesian-approach-to-dependence-aware-cointegration-relative-value-analysis.md) | Dependence-aware cointegration / relative-value analysis | 135 | 892 | ⛔ Not useful | Unable to find more details |
| [Stochastic-process-based approach to statistical-arbitrage basket construction](concepts/stochastic-process-based-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 64 | 906 | ⛔ Not useful | Unable to find more details |
| [Adaptive approach to statistical-arbitrage basket construction](concepts/adaptive-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 64 | 910 | ⛔ Not useful | Unable to find more details |
| [Markov-state-based approach to statistical-arbitrage basket construction](concepts/markov-state-based-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 63 | 913 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to momentum/trend forecasting](concepts/multi-scale-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 2 | 1,188 | ⏳ Worth testing | Evidence found |
| [Hierarchical approach to momentum/trend forecasting](concepts/hierarchical-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 2 | 1,191 | ⏳ Reference only | Unable to find more details |
| [Kernel-based approach to sector allocation](concepts/kernel-based-approach-to-sector-allocation.md) | Sector allocation | 10 | 1,199 | ⏳ Reference only | Unable to find more details |
| [Evolutionary-optimization-based approach to sector allocation](concepts/evolutionary-optimization-based-approach-to-sector-allocation.md) | Sector allocation | 10 | 1,200 | ⛔ Not useful | Unable to find more details |
| [Kernel-based approach to delay-aware portfolio allocation](concepts/kernel-based-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 11 | 1,201 | ⏳ Reference only | Unable to find more details |
| [Path-signature-based approach to sector allocation](concepts/path-signature-based-approach-to-sector-allocation.md) | Sector allocation | 15 | 1,203 | ⛔ Not useful | Unable to find more details |
| [Evolutionary-optimization-based approach to delay-aware portfolio allocation](concepts/evolutionary-optimization-based-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 16 | 1,204 | ⛔ Not useful | Unable to find more details |
| [Path-signature-based approach to delay-aware portfolio allocation](concepts/path-signature-based-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 10 | 1,207 | ⛔ Not useful | Unable to find more details |
| [Kernel-based approach to cross-sectional stock ranking](concepts/kernel-based-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 63 | 1,221 | ⛔ Not useful | Unable to find more details |
| [Path-signature-based approach to volatility-surface forecasting](concepts/path-signature-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 61 | 1,223 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to leveraged-ETF exposure rebalancing](concepts/attention-weighted-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 65 | 1,224 | ⛔ Not useful | Unable to find more details |
| [Evolutionary-optimization-based approach to cross-sectional stock ranking](concepts/evolutionary-optimization-based-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 62 | 1,225 | ⛔ Not useful | Unable to find more details |
| [Dynamical-systems/geometric approach to ETF rotation](concepts/dynamical-systems-geometric-approach-to-etf-rotation.md) | ETF rotation | 62 | 1,227 | ⛔ Not useful | Unable to find more details |
| [Path-signature-based approach to cross-sectional stock ranking](concepts/path-signature-based-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 68 | 1,228 | ⛔ Not useful | Unable to find more details |
| [Robust approach to ETF rotation](concepts/robust-approach-to-etf-rotation.md) | ETF rotation | 64 | 1,231 | ⏳ Reference only | Unable to find more details |
| [Kernel-based approach to volatility-surface forecasting](concepts/kernel-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 63 | 1,232 | ⛔ Not useful | Unable to find more details |
| [Dynamical-systems/geometric approach to leveraged-ETF exposure rebalancing](concepts/dynamical-systems-geometric-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 62 | 1,233 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to ETF rotation](concepts/attention-weighted-approach-to-etf-rotation.md) | ETF rotation | 69 | 1,235 | ⛔ Not useful | Unable to find more details |
| [Evolutionary-optimization-based approach to volatility-surface forecasting](concepts/evolutionary-optimization-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 63 | 1,236 | ⛔ Not useful | Unable to find more details |
| [Robust approach to leveraged-ETF exposure rebalancing](concepts/robust-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 62 | 1,237 | ⏳ Reference only | Unable to find more details |
| [Multi-scale approach to delay-aware portfolio allocation](concepts/multi-scale-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 63 | 1,291 | ⏳ Reference only | Unable to find more details |
| [Adversarially robust approach to sector allocation](concepts/adversarially-robust-approach-to-sector-allocation.md) | Sector allocation | 63 | 1,292 | ⛔ Not useful | Unable to find more details |
| [Entropy-regularized approach to delay-aware portfolio allocation](concepts/entropy-regularized-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 62 | 1,294 | ⏳ Reference only | Unable to find more details |
| [Multi-scale approach to sector allocation](concepts/multi-scale-approach-to-sector-allocation.md) | Sector allocation | 64 | 1,295 | ⏳ Worth testing | Evidence found |
| [Graph-based approach to delay-aware portfolio allocation](concepts/graph-based-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 68 | 1,298 | ⏳ Reference only | Unable to find more details |
| [Entropy-regularized approach to sector allocation](concepts/entropy-regularized-approach-to-sector-allocation.md) | Sector allocation | 62 | 1,299 | ⏳ Reference only | Unable to find more details |
| [Adversarially robust approach to delay-aware portfolio allocation](concepts/adversarially-robust-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 62 | 1,301 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to sector allocation](concepts/graph-based-approach-to-sector-allocation.md) | Sector allocation | 63 | 1,302 | ⏳ Reference only | Unable to find more details |
| [Robust approach to delay-aware portfolio allocation](concepts/robust-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 62 | 1,399 | ⏳ Reference only | Unable to find more details |
| [Dynamical-systems/geometric approach to sector allocation](concepts/dynamical-systems-geometric-approach-to-sector-allocation.md) | Sector allocation | 63 | 1,400 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to delay-aware portfolio allocation](concepts/attention-weighted-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 62 | 1,403 | ⛔ Not useful | Unable to find more details |
| [Robust approach to sector allocation](concepts/robust-approach-to-sector-allocation.md) | Sector allocation | 63 | 1,404 | ⏳ Reference only | Unable to find more details |
| [Attention-weighted approach to sector allocation](concepts/attention-weighted-approach-to-sector-allocation.md) | Sector allocation | 62 | 1,406 | ⛔ Not useful | Unable to find more details |
| [Dynamical-systems/geometric approach to delay-aware portfolio allocation](concepts/dynamical-systems-geometric-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 63 | 1,408 | ⛔ Not useful | Unable to find more details |
| [Model for factor risk-parity allocation](concepts/model-for-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 7 | 1,538 | ⏳ Reference only | Evidence found |
| [Topology-aware approach to statistical-arbitrage basket construction](concepts/topology-aware-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 74 | 1,539 | ⛔ Not useful | Unable to find more details |
| [Diffusion-model-based approach to statistical-arbitrage basket construction](concepts/diffusion-model-based-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 73 | 1,540 | ⛔ Not useful | Unable to find more details |
| [Fractional-order approach to statistical-arbitrage basket construction](concepts/fractional-order-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 63 | 1,546 | ⛔ Not useful | Unable to find more details |
| [High-frequency approach to momentum/trend forecasting](concepts/high-frequency-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 4 | 1,598 | ⏳ Worth testing | Evidence found |
| [Distributionally robust approach to momentum/trend forecasting](concepts/distributionally-robust-approach-to-momentum-trend-forecasting.md) | Momentum / trend forecasting | 2 | 1,601 | ⏳ Reference only | Unable to find more details |
| [Multi-scale approach to factor risk-parity allocation](concepts/multi-scale-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 1 | 1,604 | ⏳ Reference only | Unable to find more details |
| [Model for index portfolio rebalancing](concepts/model-for-index-portfolio-rebalancing.md) | Index portfolio rebalancing | 5 | 1,605 | ⏳ Reference only | Evidence found |
| [Spectral approach to index portfolio rebalancing](concepts/spectral-approach-to-index-portfolio-rebalancing.md) | Index portfolio rebalancing | 4 | 1,613 | ⏳ Reference only | Unable to find more details |
| [Distributionally robust approach to tail-risk hedging and allocation](concepts/distributionally-robust-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 2 | 1,614 | ⏳ Reference only | Unable to find more details |
| [Spectral approach to covariance estimation for portfolio risk](concepts/spectral-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 4 | 1,619 | ⏳ Reference only | Unable to find more details |
| [Nonlinear approach to index portfolio rebalancing](concepts/nonlinear-approach-to-index-portfolio-rebalancing.md) | Index portfolio rebalancing | 4 | 1,621 | ⏳ Reference only | Unable to find more details |
| [Model for cross-sectional stock ranking](concepts/model-for-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 9 | 1,622 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to tail-risk hedging and allocation](concepts/multi-scale-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 2 | 1,623 | ⏳ Worth testing | Evidence found |
| [Hierarchical approach to factor risk-parity allocation](concepts/hierarchical-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 2 | 1,624 | ⏳ Reference only | Evidence found |
| [Nonlinear approach to covariance estimation for portfolio risk](concepts/nonlinear-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 13 | 1,629 | ⏳ Reference only | Unable to find more details |
| [Model for index/ETF constituent arbitrage](concepts/model-for-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 6 | 1,630 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to candidate alpha-signal generation](concepts/recursive-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 5 | 1,658 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to covariance estimation for portfolio risk](concepts/copula-based-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 15 | 1,659 | ⏳ Reference only | Unable to find more details |
| [Koopman-operator-based approach to index/ETF constituent arbitrage](concepts/koopman-operator-based-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 5 | 1,660 | ⛔ Not useful | Unable to find more details |
| [Quantum/quantum-inspired approach to candidate alpha-signal generation](concepts/quantum-quantum-inspired-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 5 | 1,661 | ⛔ Not useful | Unable to find more details |
| [Bayesian approach to covariance estimation for portfolio risk](concepts/bayesian-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 5 | 1,662 | ⏳ Reference only | Unable to find more details |
| [Diffusion-model-based approach to index/ETF constituent arbitrage](concepts/diffusion-model-based-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 5 | 1,663 | ⛔ Not useful | Unable to find more details |
| [Koopman-operator-based approach to candidate alpha-signal generation](concepts/koopman-operator-based-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 16 | 1,664 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to index/ETF constituent arbitrage](concepts/adversarially-robust-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 5 | 1,666 | ⛔ Not useful | Unable to find more details |
| [Diffusion-model-based approach to candidate alpha-signal generation](concepts/diffusion-model-based-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 5 | 1,667 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to index/ETF constituent arbitrage](concepts/recursive-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 7 | 1,668 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to candidate alpha-signal generation](concepts/adversarially-robust-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 5 | 1,669 | ⛔ Not useful | Unable to find more details |
| [Quantum/quantum-inspired approach to index/ETF constituent arbitrage](concepts/quantum-quantum-inspired-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 138 | 1,670 | ⛔ Not useful | Unable to find more details |
| [Conformal-prediction-based approach to macro-driven index allocation](concepts/conformal-prediction-based-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 73 | 1,724 | ⏳ Reference only | Unable to find more details |
| [Evolutionary-optimization-based approach to trade-execution optimization](concepts/evolutionary-optimization-based-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 11 | 1,725 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to cross-asset/sector contagion analysis](concepts/graph-based-approach-to-cross-asset-sector-contagion-analysis.md) | Cross-asset / sector contagion analysis | 135 | 1,726 | ⏳ Reference only | Unable to find more details |
| [Stochastic-process-based approach to liquidity-shock detection and response](concepts/stochastic-process-based-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 76 | 1,727 | ⏳ Reference only | Unable to find more details |
| [Dynamical-systems/geometric approach to quantum-circuit or quantum-inspired optimization](concepts/dynamical-systems-geometric-approach-to-quantum-circuit-or-quantum-inspired-opti.md) | Quantum-circuit or quantum-inspired optimisation | 10 | 1,728 | ⛔ Not useful | Unable to find more details |
| [Bayesian approach to regime-aware allocation](concepts/bayesian-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 136 | 1,729 | ⏳ Worth testing | Evidence found |
| [Neural-network-based approach to delay-aware portfolio allocation](concepts/neural-network-based-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 10 | 1,730 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to benchmark index tracking](concepts/recursive-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 135 | 1,732 | ⛔ Not useful | Unable to find more details |
| [Markov-state-based approach to path-signature time-series forecasting](concepts/markov-state-based-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 78 | 1,733 | ⛔ Not useful | Unable to find more details |
| [Variational approach to covariance estimation for portfolio risk](concepts/variational-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 11 | 1,737 | ⛔ Not useful | Unable to find more details |
| [Integrated approach to index/ETF constituent arbitrage](concepts/integrated-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 136 | 1,738 | ⛔ Not useful | Unable to find more details |
| [Spectral approach to macro-driven index allocation](concepts/spectral-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 74 | 1,740 | ⏳ Reference only | Unable to find more details |
| [Path-signature-based approach to trade-execution optimization](concepts/path-signature-based-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 11 | 1,741 | ⛔ Not useful | Unable to find more details |
| [Dynamical-systems/geometric approach to cross-asset/sector contagion analysis](concepts/dynamical-systems-geometric-approach-to-cross-asset-sector-contagion-analysis.md) | Cross-asset / sector contagion analysis | 135 | 1,742 | ⛔ Not useful | Unable to find more details |
| [Adaptive approach to liquidity-shock detection and response](concepts/adaptive-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 74 | 1,743 | ⏳ Reference only | Unable to find more details |
| [Robust approach to quantum-circuit or quantum-inspired optimization](concepts/robust-approach-to-quantum-circuit-or-quantum-inspired-optimization.md) | Quantum-circuit or quantum-inspired optimisation | 10 | 1,745 | ⛔ Not useful | Unable to find more details |
| [Hawkes-process-based approach to regime-aware allocation](concepts/hawkes-process-based-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 136 | 1,746 | ⛔ Not useful | Unable to find more details |
| [Wavelet-based approach to benchmark index tracking](concepts/wavelet-based-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 139 | 1,748 | ⛔ Not useful | Unable to find more details |
| [Dynamical-systems/geometric approach to candidate alpha-signal generation](concepts/dynamical-systems-geometric-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 11 | 1,749 | ⛔ Not useful | Unable to find more details |
| [Bayesian approach to index/ETF constituent arbitrage](concepts/bayesian-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 136 | 1,753 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to cross-asset/sector contagion analysis](concepts/recursive-approach-to-cross-asset-sector-contagion-analysis.md) | Cross-asset / sector contagion analysis | 136 | 1,755 | ⏳ Reference only | Unable to find more details |
| [Markov-state-based approach to liquidity-shock detection and response](concepts/markov-state-based-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 72 | 1,756 | ⏳ Reference only | Unable to find more details |
| [Attention-weighted approach to quantum-circuit or quantum-inspired optimization](concepts/attention-weighted-approach-to-quantum-circuit-or-quantum-inspired-optimization.md) | Quantum-circuit or quantum-inspired optimisation | 11 | 1,757 | ⛔ Not useful | Unable to find more details |
| [Quantum/quantum-inspired approach to regime-aware allocation](concepts/quantum-quantum-inspired-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 136 | 1,758 | ⛔ Not useful | Unable to find more details |
| [Model for benchmark index tracking](concepts/model-for-benchmark-index-tracking.md) | Benchmark index tracking | 140 | 1,760 | ⛔ Not useful | Unable to find more details |
| [Stochastic-process-based approach to path-signature time-series forecasting](concepts/stochastic-process-based-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 73 | 1,761 | ⛔ Not useful | Unable to find more details |
| [Robust approach to candidate alpha-signal generation](concepts/robust-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 10 | 1,762 | ⛔ Not useful | Unable to find more details |
| [Hawkes-process-based approach to index/ETF constituent arbitrage](concepts/hawkes-process-based-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 135 | 1,765 | ⛔ Not useful | Unable to find more details |
| [Kernel-based approach to trade-execution optimization](concepts/kernel-based-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 10 | 1,766 | ⛔ Not useful | Unable to find more details |
| [Wavelet-based approach to cross-asset/sector contagion analysis](concepts/wavelet-based-approach-to-cross-asset-sector-contagion-analysis.md) | Cross-asset / sector contagion analysis | 136 | 1,767 | ⏳ Reference only | Unable to find more details |
| [Neural-network-based approach to sector allocation](concepts/neural-network-based-approach-to-sector-allocation.md) | Sector allocation | 11 | 1,768 | ⛔ Not useful | Unable to find more details |
| [Koopman-operator-based approach to quantum-circuit or quantum-inspired optimization](concepts/koopman-operator-based-approach-to-quantum-circuit-or-quantum-inspired-optimizat.md) | Quantum-circuit or quantum-inspired optimisation | 10 | 1,769 | ⛔ Not useful | Unable to find more details |
| [Integrated approach to regime-aware allocation](concepts/integrated-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 139 | 1,770 | ⏳ Reference only | Unable to find more details |
| [Dynamical-systems/geometric approach to benchmark index tracking](concepts/dynamical-systems-geometric-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 136 | 1,772 | ⛔ Not useful | Unable to find more details |
| [Adaptive approach to path-signature time-series forecasting](concepts/adaptive-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 73 | 1,773 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to candidate alpha-signal generation](concepts/attention-weighted-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 10 | 1,774 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to covariance estimation for portfolio risk](concepts/geometry-aware-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 10 | 1,776 | ⛔ Not useful | Unable to find more details |
| [Markov-state-based approach to macro-driven index allocation](concepts/markov-state-based-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 63 | 1,840 | ⏳ Reference only | Unable to find more details |
| [Spectral approach to path-signature time-series forecasting](concepts/spectral-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 63 | 1,842 | ⛔ Not useful | Unable to find more details |
| [Neural-network-based approach to neural-operator forecasting](concepts/neural-network-based-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 63 | 1,843 | ⛔ Not useful | Unable to find more details |
| [Koopman-operator-based approach to ETF rotation](concepts/koopman-operator-based-approach-to-etf-rotation.md) | ETF rotation | 63 | 1,845 | ⛔ Not useful | Unable to find more details |
| [Kernel-based approach to neural-operator forecasting](concepts/kernel-based-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 62 | 1,854 | ⛔ Not useful | Unable to find more details |
| [Neural-network-based approach to volatility-surface forecasting](concepts/neural-network-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 62 | 1,856 | ⛔ Not useful | Unable to find more details |
| [Koopman-operator-based approach to leveraged-ETF exposure rebalancing](concepts/koopman-operator-based-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 63 | 1,858 | ⛔ Not useful | Unable to find more details |
| [Conformal-prediction-based approach to liquidity-shock detection and response](concepts/conformal-prediction-based-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 63 | 1,863 | ⏳ Reference only | Unable to find more details |
| [Stochastic-process-based approach to macro-driven index allocation](concepts/stochastic-process-based-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 63 | 1,866 | ⏳ Reference only | Unable to find more details |
| [Evolutionary-optimization-based approach to neural-operator forecasting](concepts/evolutionary-optimization-based-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 62 | 1,868 | ⛔ Not useful | Unable to find more details |
| [Spectral approach to liquidity-shock detection and response](concepts/spectral-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 62 | 1,874 | ⏳ Reference only | Unable to find more details |
| [Neural-network-based approach to cross-sectional stock ranking](concepts/neural-network-based-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 63 | 1,875 | ⛔ Not useful | Unable to find more details |
| [Adaptive approach to macro-driven index allocation](concepts/adaptive-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 67 | 1,878 | ⏳ Reference only | Unable to find more details |
| [Conformal-prediction-based approach to path-signature time-series forecasting](concepts/conformal-prediction-based-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 62 | 1,880 | ⛔ Not useful | Unable to find more details |
| [Path-signature-based approach to neural-operator forecasting](concepts/path-signature-based-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 63 | 1,881 | ⛔ Not useful | Unable to find more details |
| [Nonlinear approach to quantum-circuit or quantum-inspired optimization](concepts/nonlinear-approach-to-quantum-circuit-or-quantum-inspired-optimization.md) | Quantum-circuit or quantum-inspired optimisation | 63 | 2,043 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to trade-execution optimization](concepts/graph-based-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 61 | 2,048 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to candidate alpha-signal generation](concepts/geometry-aware-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 63 | 2,050 | ⛔ Not useful | Unable to find more details |
| [Variational approach to quantum-circuit or quantum-inspired optimization](concepts/variational-approach-to-quantum-circuit-or-quantum-inspired-optimization.md) | Quantum-circuit or quantum-inspired optimisation | 63 | 2,054 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to trade-execution optimization](concepts/adversarially-robust-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 63 | 2,062 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to candidate alpha-signal generation](concepts/copula-based-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 63 | 2,064 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to quantum-circuit or quantum-inspired optimization](concepts/geometry-aware-approach-to-quantum-circuit-or-quantum-inspired-optimization.md) | Quantum-circuit or quantum-inspired optimisation | 62 | 2,067 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to trade-execution optimization](concepts/multi-scale-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 70 | 2,075 | ⛔ Not useful | Unable to find more details |
| [Nonlinear approach to candidate alpha-signal generation](concepts/nonlinear-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 62 | 2,078 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to quantum-circuit or quantum-inspired optimization](concepts/copula-based-approach-to-quantum-circuit-or-quantum-inspired-optimization.md) | Quantum-circuit or quantum-inspired optimisation | 63 | 2,082 | ⛔ Not useful | Unable to find more details |
| [Entropy-regularized approach to trade-execution optimization](concepts/entropy-regularized-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 63 | 2,089 | ⛔ Not useful | Unable to find more details |
| [Variational approach to candidate alpha-signal generation](concepts/variational-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 62 | 2,092 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to covariance estimation for portfolio risk](concepts/adversarially-robust-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 63 | 2,480 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to trade-execution optimization](concepts/attention-weighted-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 68 | 2,482 | ⛔ Not useful | Unable to find more details |
| [Evolutionary-optimization-based approach to candidate alpha-signal generation](concepts/evolutionary-optimization-based-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 63 | 2,484 | ⛔ Not useful | Unable to find more details |
| [Kernel-based approach to quantum-circuit or quantum-inspired optimization](concepts/kernel-based-approach-to-quantum-circuit-or-quantum-inspired-optimization.md) | Quantum-circuit or quantum-inspired optimisation | 62 | 2,489 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to covariance estimation for portfolio risk](concepts/graph-based-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 63 | 2,494 | ⏳ Reference only | Unable to find more details |
| [Path-signature-based approach to candidate alpha-signal generation](concepts/path-signature-based-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 62 | 2,497 | ⛔ Not useful | Unable to find more details |
| [Evolutionary-optimization-based approach to quantum-circuit or quantum-inspired optimization](concepts/evolutionary-optimization-based-approach-to-quantum-circuit-or-quantum-inspired.md) | Quantum-circuit or quantum-inspired optimisation | 63 | 2,502 | ⛔ Not useful | Unable to find more details |
| [Entropy-regularized approach to covariance estimation for portfolio risk](concepts/entropy-regularized-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 62 | 2,507 | ⏳ Reference only | Unable to find more details |
| [Dynamical-systems/geometric approach to trade-execution optimization](concepts/dynamical-systems-geometric-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 62 | 2,509 | ⛔ Not useful | Unable to find more details |
| [Neural-network-based approach to candidate alpha-signal generation](concepts/neural-network-based-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 62 | 2,511 | ⛔ Not useful | Unable to find more details |
| [Koopman-operator-based approach to delay-aware portfolio allocation](concepts/koopman-operator-based-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 63 | 2,513 | ⛔ Not useful | Unable to find more details |
| [Path-signature-based approach to quantum-circuit or quantum-inspired optimization](concepts/path-signature-based-approach-to-quantum-circuit-or-quantum-inspired-optimizatio.md) | Quantum-circuit or quantum-inspired optimisation | 63 | 2,515 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to covariance estimation for portfolio risk](concepts/multi-scale-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 62 | 2,521 | ⏳ Reference only | Unable to find more details |
| [Robust approach to trade-execution optimization](concepts/robust-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 65 | 2,523 | ⛔ Not useful | Unable to find more details |
| [Kernel-based approach to candidate alpha-signal generation](concepts/kernel-based-approach-to-candidate-alpha-signal-generation.md) | Candidate alpha-signal generation | 63 | 2,525 | ⛔ Not useful | Unable to find more details |
| [Neural-network-based approach to quantum-circuit or quantum-inspired optimization](concepts/neural-network-based-approach-to-quantum-circuit-or-quantum-inspired-optimizatio.md) | Quantum-circuit or quantum-inspired optimisation | 62 | 2,529 | ⛔ Not useful | Unable to find more details |
| [Koopman-operator-based approach to sector allocation](concepts/koopman-operator-based-approach-to-sector-allocation.md) | Sector allocation | 62 | 2,532 | ⛔ Not useful | Unable to find more details |
| [Hierarchical approach to hierarchical macro-driven etf allocator ver-14](concepts/hierarchical-approach-to-hierarchical-macro-driven-etf-allocator-ver-14.md) | Macro-driven ETF allocation (one generated name) | 1 | 3,169 | ⏳ Reference only | Unable to find more details |
| [Copula-based approach to copula-based macro-driven etf allocator ver-34](concepts/copula-based-approach-to-copula-based-macro-driven-etf-allocator-ver-34.md) | Macro-driven ETF allocation (one generated name) | 1 | 3,170 | ⏳ Reference only | Unable to find more details |
| [Robust approach to robust macro-driven etf allocator ver-54](concepts/robust-approach-to-robust-macro-driven-etf-allocator-ver-54.md) | Macro-driven ETF allocation (one generated name) | 1 | 3,171 | ⏳ Reference only | Unable to find more details |
| [Model for transformer-based macro-driven etf allocator ver-94](concepts/model-for-transformer-based-macro-driven-etf-allocator-ver-94.md) | Macro-driven ETF allocation (one generated name) | 1 | 3,172 | ⛔ Not useful | Unable to find more details |
| [Hierarchical approach to hierarchical macro-driven etf allocator ver-114](concepts/hierarchical-approach-to-hierarchical-macro-driven-etf-allocator-ver-114.md) | Macro-driven ETF allocation (one generated name) | 1 | 3,173 | ⏳ Reference only | Unable to find more details |
| [Copula-based approach to copula-based macro-driven etf allocator ver-134](concepts/copula-based-approach-to-copula-based-macro-driven-etf-allocator-ver-134.md) | Macro-driven ETF allocation (one generated name) | 1 | 3,174 | ⏳ Reference only | Unable to find more details |
| [Robust approach to robust macro-driven etf allocator ver-154](concepts/robust-approach-to-robust-macro-driven-etf-allocator-ver-154.md) | Macro-driven ETF allocation (one generated name) | 1 | 3,175 | ⏳ Reference only | Unable to find more details |
| [Model for transformer-based macro-driven etf allocator ver-194](concepts/model-for-transformer-based-macro-driven-etf-allocator-ver-194.md) | Macro-driven ETF allocation (one generated name) | 1 | 3,176 | ⛔ Not useful | Unable to find more details |
| [Topology-aware approach to tail-risk hedging and allocation](concepts/topology-aware-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 2 | 3,651 | ⛔ Not useful | Evidence found |
| [Adaptive approach to regime-aware allocation](concepts/adaptive-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 2 | 3,652 | ✅ In use | Evidence found |
| [Distributionally robust approach to factor risk-parity allocation](concepts/distributionally-robust-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 2 | 3,654 | ⏳ Reference only | Unable to find more details |
| [High-frequency approach to covariance estimation for portfolio risk](concepts/high-frequency-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 4 | 3,656 | ⏳ Reference only | Evidence found |
| [Adaptive approach to sector allocation](concepts/adaptive-approach-to-sector-allocation.md) | Sector allocation | 2 | 3,658 | ⏳ Reference only | Unable to find more details |
| [Adaptive approach to tail-risk hedging and allocation](concepts/adaptive-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 1 | 3,659 | ✅ In use | Evidence found |
| [Nonlinear approach to benchmark index tracking](concepts/nonlinear-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 2 | 3,673 | ⛔ Not useful | Unable to find more details |
| [Model for liquidity-shock detection and response](concepts/model-for-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 5 | 3,674 | ⏳ Reference only | Evidence found |
| [High-frequency approach to index portfolio rebalancing](concepts/high-frequency-approach-to-index-portfolio-rebalancing.md) | Index portfolio rebalancing | 3 | 3,676 | ⛔ Not useful | Unable to find more details |
| [Spectral approach to benchmark index tracking](concepts/spectral-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 2 | 3,677 | ⛔ Not useful | Unable to find more details |
| [Neural-network-based approach to tail-risk hedging and allocation](concepts/neural-network-based-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 5 | 3,687 | ⛔ Not useful | Unable to find more details |
| [Diffusion-model-based approach to volatility-surface forecasting](concepts/diffusion-model-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 5 | 3,689 | ⛔ Not useful | Unable to find more details |
| [Fractional-order approach to tail-risk hedging and allocation](concepts/fractional-order-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 5 | 3,690 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to volatility-surface forecasting](concepts/adversarially-robust-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 15 | 3,692 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to tail-risk hedging and allocation](concepts/copula-based-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 5 | 3,693 | ⏳ Reference only | Unable to find more details |
| [Fractional-order approach to factor risk-parity allocation](concepts/fractional-order-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 5 | 3,694 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to volatility-surface forecasting](concepts/recursive-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 5 | 3,695 | ⛔ Not useful | Unable to find more details |
| [Bayesian approach to tail-risk hedging and allocation](concepts/bayesian-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 5 | 3,696 | ⏳ Reference only | Unable to find more details |
| [Quantum/quantum-inspired approach to volatility-surface forecasting](concepts/quantum-quantum-inspired-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 5 | 3,698 | ⛔ Not useful | Unable to find more details |
| [Neural-network-based approach to covariance estimation for portfolio risk](concepts/neural-network-based-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 5 | 3,699 | ⛔ Not useful | Unable to find more details |
| [Robust approach to tail-risk hedging and allocation](concepts/robust-approach-to-tail-risk-hedging-and-allocation.md) | Tail-risk hedging and allocation | 5 | 3,700 | ⏳ Reference only | Unable to find more details |
| [Bayesian approach to factor risk-parity allocation](concepts/bayesian-approach-to-factor-risk-parity-allocation.md) | Factor risk-parity allocation | 5 | 3,701 | ⏳ Reference only | Unable to find more details |
| [Koopman-operator-based approach to volatility-surface forecasting](concepts/koopman-operator-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 5 | 3,702 | ⛔ Not useful | Unable to find more details |
| [Fractional-order approach to covariance estimation for portfolio risk](concepts/fractional-order-approach-to-covariance-estimation-for-portfolio-risk.md) | Covariance estimation for portfolio risk | 5 | 3,703 | ⛔ Not useful | Unable to find more details |
| [Nonlinear approach to leveraged-ETF exposure rebalancing](concepts/nonlinear-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 11 | 3,774 | ⏳ Reference only | Unable to find more details |
| [Multi-scale approach to volatility-surface forecasting](concepts/multi-scale-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 11 | 3,776 | ⛔ Not useful | Unable to find more details |
| [Variational approach to ETF rotation](concepts/variational-approach-to-etf-rotation.md) | ETF rotation | 10 | 3,780 | ⛔ Not useful | Unable to find more details |
| [Entropy-regularized approach to neural-operator forecasting](concepts/entropy-regularized-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 10 | 3,784 | ⛔ Not useful | Unable to find more details |
| [Diffusion-model-based approach to topological-feature portfolio allocation](concepts/diffusion-model-based-approach-to-topological-feature-portfolio-allocation.md) | Topological-feature portfolio allocation | 73 | 3,785 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to cross-sectional stock ranking](concepts/graph-based-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 11 | 3,791 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to leveraged-ETF exposure rebalancing](concepts/copula-based-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 11 | 3,794 | ⛔ Not useful | Unable to find more details |
| [Nonlinear approach to ETF rotation](concepts/nonlinear-approach-to-etf-rotation.md) | ETF rotation | 10 | 3,800 | ⏳ Reference only | Unable to find more details |
| [Multi-scale approach to neural-operator forecasting](concepts/multi-scale-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 11 | 3,804 | ⛔ Not useful | Unable to find more details |
| [Topology-aware approach to topological-feature portfolio allocation](concepts/topology-aware-approach-to-topological-feature-portfolio-allocation.md) | Topological-feature portfolio allocation | 74 | 3,805 | ⛔ Not useful | Unable to find more details |
| [Fractional-order approach to path-signature time-series forecasting](concepts/fractional-order-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 73 | 3,809 | ⛔ Not useful | Unable to find more details |
| [Entropy-regularized approach to cross-sectional stock ranking](concepts/entropy-regularized-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 10 | 3,812 | ⛔ Not useful | Unable to find more details |
| [Diffusion-model-based approach to macro-driven index allocation](concepts/diffusion-model-based-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 73 | 3,813 | ⛔ Not useful | Unable to find more details |
| [Neural-network-based approach to trade-execution optimization](concepts/neural-network-based-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 10 | 3,814 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to leveraged-ETF exposure rebalancing](concepts/geometry-aware-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 10 | 3,817 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to volatility-surface forecasting](concepts/graph-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 10 | 3,819 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to ETF rotation](concepts/copula-based-approach-to-etf-rotation.md) | ETF rotation | 13 | 3,823 | ⏳ Reference only | Unable to find more details |
| [Adversarially robust approach to neural-operator forecasting](concepts/adversarially-robust-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 11 | 3,827 | ⛔ Not useful | Unable to find more details |
| [Conformal-prediction-based approach to topological-feature portfolio allocation](concepts/conformal-prediction-based-approach-to-topological-feature-portfolio-allocation.md) | Topological-feature portfolio allocation | 73 | 3,828 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to cross-sectional stock ranking](concepts/multi-scale-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 10 | 3,834 | ⛔ Not useful | Unable to find more details |
| [Topology-aware approach to macro-driven index allocation](concepts/topology-aware-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 77 | 3,836 | ⛔ Not useful | Unable to find more details |
| [Variational approach to leveraged-ETF exposure rebalancing](concepts/variational-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 10 | 3,839 | ⛔ Not useful | Unable to find more details |
| [Fractional-order approach to liquidity-shock detection and response](concepts/fractional-order-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 73 | 3,840 | ⛔ Not useful | Unable to find more details |
| [Entropy-regularized approach to volatility-surface forecasting](concepts/entropy-regularized-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 11 | 3,842 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to ETF rotation](concepts/geometry-aware-approach-to-etf-rotation.md) | ETF rotation | 16 | 3,846 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to neural-operator forecasting](concepts/graph-based-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 10 | 3,850 | ⛔ Not useful | Unable to find more details |
| [Spectral approach to topological-feature portfolio allocation](concepts/spectral-approach-to-topological-feature-portfolio-allocation.md) | Topological-feature portfolio allocation | 72 | 3,851 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to cross-sectional stock ranking](concepts/adversarially-robust-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 10 | 3,857 | ⛔ Not useful | Unable to find more details |
| [Diffusion-model-based approach to liquidity-shock detection and response](concepts/diffusion-model-based-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 68 | 3,951 | ⛔ Not useful | Unable to find more details |
| [Adaptive approach to topological-feature portfolio allocation](concepts/adaptive-approach-to-topological-feature-portfolio-allocation.md) | Topological-feature portfolio allocation | 63 | 3,962 | ⛔ Not useful | Unable to find more details |
| [Topology-aware approach to liquidity-shock detection and response](concepts/topology-aware-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 65 | 3,972 | ⛔ Not useful | Unable to find more details |
| [Fractional-order approach to macro-driven index allocation](concepts/fractional-order-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 62 | 3,976 | ⛔ Not useful | Unable to find more details |
| [Diffusion-model-based approach to path-signature time-series forecasting](concepts/diffusion-model-based-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 63 | 3,981 | ⛔ Not useful | Unable to find more details |
| [Markov-state-based approach to topological-feature portfolio allocation](concepts/markov-state-based-approach-to-topological-feature-portfolio-allocation.md) | Topological-feature portfolio allocation | 61 | 3,985 | ⛔ Not useful | Unable to find more details |
| [Topology-aware approach to path-signature time-series forecasting](concepts/topology-aware-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 62 | 4,002 | ⛔ Not useful | Unable to find more details |
| [Fractional-order approach to topological-feature portfolio allocation](concepts/fractional-order-approach-to-topological-feature-portfolio-allocation.md) | Topological-feature portfolio allocation | 63 | 4,006 | ⛔ Not useful | Unable to find more details |
| [Stochastic-process-based approach to topological-feature portfolio allocation](concepts/stochastic-process-based-approach-to-topological-feature-portfolio-allocation.md) | Topological-feature portfolio allocation | 63 | 4,026 | ⛔ Not useful | Unable to find more details |
| [Variational approach to neural-operator forecasting](concepts/variational-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 63 | 5,027 | ⛔ Not useful | Unable to find more details |
| [Entropy-regularized approach to ETF rotation](concepts/entropy-regularized-approach-to-etf-rotation.md) | ETF rotation | 63 | 5,029 | ⏳ Reference only | Unable to find more details |
| [Geometry-aware approach to volatility-surface forecasting](concepts/geometry-aware-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 62 | 5,033 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to leveraged-ETF exposure rebalancing](concepts/graph-based-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 67 | 5,036 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to cross-sectional stock ranking](concepts/copula-based-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 62 | 5,040 | ⛔ Not useful | Unable to find more details |
| [Nonlinear approach to neural-operator forecasting](concepts/nonlinear-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 63 | 5,047 | ⛔ Not useful | Unable to find more details |
| [Koopman-operator-based approach to trade-execution optimization](concepts/koopman-operator-based-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 62 | 5,048 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to ETF rotation](concepts/multi-scale-approach-to-etf-rotation.md) | ETF rotation | 67 | 5,050 | ⏳ Worth testing | Evidence found |
| [Variational approach to volatility-surface forecasting](concepts/variational-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 62 | 5,054 | ⛔ Not useful | Unable to find more details |
| [Entropy-regularized approach to leveraged-ETF exposure rebalancing](concepts/entropy-regularized-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 63 | 5,057 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to cross-sectional stock ranking](concepts/geometry-aware-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 63 | 5,061 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to neural-operator forecasting](concepts/copula-based-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 62 | 5,069 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to ETF rotation](concepts/adversarially-robust-approach-to-etf-rotation.md) | ETF rotation | 62 | 5,071 | ⛔ Not useful | Unable to find more details |
| [Nonlinear approach to volatility-surface forecasting](concepts/nonlinear-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 63 | 5,075 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to leveraged-ETF exposure rebalancing](concepts/multi-scale-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 63 | 5,079 | ⏳ Reference only | Unable to find more details |
| [Variational approach to cross-sectional stock ranking](concepts/variational-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 63 | 5,084 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to neural-operator forecasting](concepts/geometry-aware-approach-to-neural-operator-forecasting.md) | Neural-operator forecasting | 62 | 5,091 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to ETF rotation](concepts/graph-based-approach-to-etf-rotation.md) | ETF rotation | 63 | 5,093 | ⏳ Reference only | Unable to find more details |
| [Copula-based approach to volatility-surface forecasting](concepts/copula-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 64 | 5,097 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to leveraged-ETF exposure rebalancing](concepts/adversarially-robust-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 62 | 5,100 | ⛔ Not useful | Unable to find more details |
| [Nonlinear approach to cross-sectional stock ranking](concepts/nonlinear-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 67 | 5,105 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to index/ETF constituent arbitrage](concepts/attention-weighted-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 2 | 6,100 | ⛔ Not useful | Unable to find more details |
| [Quantum-inspired approach to statistical-arbitrage basket construction](concepts/quantum-inspired-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 1 | 6,101 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to liquidity-shock detection and response](concepts/attention-weighted-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 1 | 6,102 | ⛔ Not useful | Unable to find more details |
| [Model for cointegration/pairs trading](concepts/model-for-cointegration-pairs-trading.md) | Cointegration / pairs trading | 6 | 6,106 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to regime-aware allocation](concepts/multi-scale-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 2 | 6,110 | ⏳ Reference only | Unable to find more details |
| [Quantum-inspired approach to cointegration/pairs trading](concepts/quantum-inspired-approach-to-cointegration-pairs-trading.md) | Cointegration / pairs trading | 2 | 6,111 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to statistical-arbitrage basket construction](concepts/recursive-approach-to-statistical-arbitrage-basket-construction.md) | Statistical-arbitrage basket construction | 2 | 6,112 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to cointegration/pairs trading](concepts/attention-weighted-approach-to-cointegration-pairs-trading.md) | Cointegration / pairs trading | 2 | 6,114 | ⛔ Not useful | Unable to find more details |
| [Model for generative macro-driven etf allocator ver-74](concepts/model-for-generative-macro-driven-etf-allocator-ver-74.md) | Macro-driven ETF allocation (one generated name) | 1 | 6,116 | ⛔ Not useful | Unable to find more details |
| [Stochastic-process-based approach to cointegration/pairs trading](concepts/stochastic-process-based-approach-to-cointegration-pairs-trading.md) | Cointegration / pairs trading | 2 | 6,118 | ⛔ Not useful | Unable to find more details |
| [Distributionally robust approach to regime-aware allocation](concepts/distributionally-robust-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 2 | 6,120 | ⏳ Reference only | Unable to find more details |
| [Model for generative macro-driven etf allocator ver-174](concepts/model-for-generative-macro-driven-etf-allocator-ver-174.md) | Macro-driven ETF allocation (one generated name) | 1 | 6,131 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to dependence-aware cointegration / relative-value analysis](concepts/geometry-aware-approach-to-dependence-aware-cointegration-relative-value-analysi.md) | Dependence-aware cointegration / relative-value analysis | 5 | 6,136 | ⛔ Not useful | Unable to find more details |
| [Geometry-aware approach to trade-execution optimization](concepts/geometry-aware-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 5 | 6,139 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to dependence-aware cointegration / relative-value analysis](concepts/attention-weighted-approach-to-dependence-aware-cointegration-relative-value-ana.md) | Dependence-aware cointegration / relative-value analysis | 5 | 6,140 | ⛔ Not useful | Unable to find more details |
| [Hawkes-process-based approach to trade-execution optimization](concepts/hawkes-process-based-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 5 | 6,141 | ⛔ Not useful | Unable to find more details |
| [Spectral approach to dependence-aware cointegration / relative-value analysis](concepts/spectral-approach-to-dependence-aware-cointegration-relative-value-analysis.md) | Dependence-aware cointegration / relative-value analysis | 5 | 6,142 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to dependence-aware cointegration / relative-value analysis](concepts/multi-scale-approach-to-dependence-aware-cointegration-relative-value-analysis.md) | Dependence-aware cointegration / relative-value analysis | 5 | 6,144 | ⛔ Not useful | Unable to find more details |
| [Spectral approach to trade-execution optimization](concepts/spectral-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 5 | 6,145 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to regime-aware allocation](concepts/recursive-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 2 | 7,406 | ⏳ Reference only | Unable to find more details |
| [Recursive approach to sector allocation](concepts/recursive-approach-to-sector-allocation.md) | Sector allocation | 1 | 7,408 | ⏳ Reference only | Unable to find more details |
| [Copula-based approach to trade-execution optimization](concepts/copula-based-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 2 | 7,411 | ⛔ Not useful | Unable to find more details |
| [Attention-weighted approach to volatility-surface forecasting](concepts/attention-weighted-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 2 | 7,413 | ⛔ Not useful | Unable to find more details |
| [Model for trade-execution optimization](concepts/model-for-trade-execution-optimization.md) | Trade-execution optimisation | 8 | 7,414 | ⛔ Not useful | Unable to find more details |
| [High-frequency approach to benchmark index tracking](concepts/high-frequency-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 2 | 7,415 | ⛔ Not useful | Unable to find more details |
| [Stochastic-process-based approach to volatility-surface forecasting](concepts/stochastic-process-based-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 2 | 7,416 | ⛔ Not useful | Unable to find more details |
| [Model for volatility-surface forecasting](concepts/model-for-volatility-surface-forecasting.md) | Volatility-surface forecasting | 6 | 7,418 | ⛔ Not useful | Unable to find more details |
| [Hierarchical approach to trade-execution optimization](concepts/hierarchical-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 2 | 7,419 | ⛔ Not useful | Unable to find more details |
| [Evolutionary-optimization-based approach to macro-driven index allocation](concepts/evolutionary-optimization-based-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 5 | 7,431 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to macro-driven index allocation](concepts/graph-based-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 5 | 7,433 | ⏳ Reference only | Unable to find more details |
| [Wavelet-based approach to macro-driven index allocation](concepts/wavelet-based-approach-to-macro-driven-index-allocation.md) | Macro-driven index allocation | 5 | 7,434 | ⏳ Reference only | Unable to find more details |
| [Hierarchical approach to cointegration/pairs trading](concepts/hierarchical-approach-to-cointegration-pairs-trading.md) | Cointegration / pairs trading | 2 | 8,387 | ⛔ Not useful | Unable to find more details |
| [Robust approach to volatility-surface forecasting](concepts/robust-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 2 | 8,388 | ⛔ Not useful | Unable to find more details |
| [Quantum-inspired approach to index/ETF constituent arbitrage](concepts/quantum-inspired-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 2 | 8,389 | ⛔ Not useful | Unable to find more details |
| [Hierarchical approach to volatility-surface forecasting](concepts/hierarchical-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 2 | 8,392 | ⛔ Not useful | Unable to find more details |
| [Topology-aware approach to regime-aware allocation](concepts/topology-aware-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 2 | 8,393 | ⛔ Not useful | Unable to find more details |
| [Quantum-inspired approach to liquidity-shock detection and response](concepts/quantum-inspired-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 2 | 8,395 | ⛔ Not useful | Unable to find more details |
| [Copula-based approach to cointegration/pairs trading](concepts/copula-based-approach-to-cointegration-pairs-trading.md) | Cointegration / pairs trading | 2 | 8,397 | ⛔ Not useful | Unable to find more details |
| [Hierarchical approach to ETF rotation](concepts/hierarchical-approach-to-etf-rotation.md) | ETF rotation | 1 | 8,399 | ⏳ Reference only | Evidence found |
| [Topology-aware approach to sector allocation](concepts/topology-aware-approach-to-sector-allocation.md) | Sector allocation | 1 | 8,400 | ⛔ Not useful | Unable to find more details |
| [Robust approach to cointegration/pairs trading](concepts/robust-approach-to-cointegration-pairs-trading.md) | Cointegration / pairs trading | 1 | 8,402 | ⛔ Not useful | Unable to find more details |
| [Stochastic-process-based approach to index/ETF constituent arbitrage](concepts/stochastic-process-based-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 1 | 8,404 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to cross-sectional stock ranking](concepts/recursive-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 2 | 8,417 | ⛔ Not useful | Unable to find more details |
| [Adaptive approach to index/ETF constituent arbitrage](concepts/adaptive-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 2 | 8,418 | ⛔ Not useful | Unable to find more details |
| [Model for cross-sectional quantitative stock selector ver-7](concepts/model-for-cross-sectional-quantitative-stock-selector-ver-7.md) | Quantitative stock selection (one generated name) | 1 | 8,419 | ⛔ Not useful | Unable to find more details |
| [Stochastic-process-based approach to leveraged-ETF exposure rebalancing](concepts/stochastic-process-based-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 2 | 8,420 | ⏳ Reference only | Evidence found |
| [Quantum-inspired approach to volatility-surface forecasting](concepts/quantum-inspired-approach-to-volatility-surface-forecasting.md) | Volatility-surface forecasting | 2 | 8,423 | ⛔ Not useful | Unable to find more details |
| [Model for dynamic quantitative stock selector ver-27](concepts/model-for-dynamic-quantitative-stock-selector-ver-27.md) | Quantitative stock selection (one generated name) | 1 | 8,426 | ⛔ Not useful | Unable to find more details |
| [Model for leveraged-ETF exposure rebalancing](concepts/model-for-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 4 | 8,427 | ⏳ Worth testing | Evidence found |
| [Stochastic-process-based approach to ETF rotation](concepts/stochastic-process-based-approach-to-etf-rotation.md) | ETF rotation | 2 | 8,429 | ⏳ Reference only | Unable to find more details |
| [Topology-aware approach to cross-sectional stock ranking](concepts/topology-aware-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 2 | 8,430 | ⛔ Not useful | Unable to find more details |
| [Distributionally robust approach to robust portfolio optimization](concepts/distributionally-robust-approach-to-robust-portfolio-optimization.md) | Robust portfolio optimisation | 2 | 8,432 | ⏳ Reference only | Evidence found |
| [Model for ETF rotation](concepts/model-for-etf-rotation.md) | ETF rotation | 5 | 8,435 | ⏳ Worth testing | Evidence found |
| [Topology-aware approach to index/ETF constituent arbitrage](concepts/topology-aware-approach-to-index-etf-constituent-arbitrage.md) | Index / ETF constituent arbitrage | 2 | 8,436 | ⛔ Not useful | Unable to find more details |
| [Model for convolutional quantitative stock selector ver-67](concepts/model-for-convolutional-quantitative-stock-selector-ver-67.md) | Quantitative stock selection (one generated name) | 1 | 8,437 | ⛔ Not useful | Unable to find more details |
| [Quantum-inspired approach to leveraged-ETF exposure rebalancing](concepts/quantum-inspired-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 2 | 8,438 | ⛔ Not useful | Unable to find more details |
| [Distributionally robust approach to sector allocation](concepts/distributionally-robust-approach-to-sector-allocation.md) | Sector allocation | 2 | 8,439 | ⏳ Reference only | Unable to find more details |
| [Adaptive approach to cross-sectional stock ranking](concepts/adaptive-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 2 | 8,441 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to multi-scale quantitative stock selector ver-87](concepts/multi-scale-approach-to-multi-scale-quantitative-stock-selector-ver-87.md) | Quantitative stock selection (one generated name) | 1 | 8,442 | ⛔ Not useful | Unable to find more details |
| [Quantum-inspired approach to ETF rotation](concepts/quantum-inspired-approach-to-etf-rotation.md) | ETF rotation | 2 | 8,445 | ⛔ Not useful | Unable to find more details |
| [Model for cross-sectional quantitative stock selector ver-107](concepts/model-for-cross-sectional-quantitative-stock-selector-ver-107.md) | Quantitative stock selection (one generated name) | 1 | 8,448 | ⛔ Not useful | Unable to find more details |
| [Model for dynamic quantitative stock selector ver-127](concepts/model-for-dynamic-quantitative-stock-selector-ver-127.md) | Quantitative stock selection (one generated name) | 1 | 8,455 | ⛔ Not useful | Unable to find more details |
| [Model for convolutional quantitative stock selector ver-167](concepts/model-for-convolutional-quantitative-stock-selector-ver-167.md) | Quantitative stock selection (one generated name) | 1 | 8,466 | ⛔ Not useful | Unable to find more details |
| [Multi-scale approach to multi-scale quantitative stock selector ver-187](concepts/multi-scale-approach-to-multi-scale-quantitative-stock-selector-ver-187.md) | Quantitative stock selection (one generated name) | 1 | 8,471 | ⛔ Not useful | Unable to find more details |
| [Nonlinear approach to sector allocation](concepts/nonlinear-approach-to-sector-allocation.md) | Sector allocation | 5 | 8,475 | ⏳ Reference only | Unable to find more details |
| [Hawkes-process-based approach to ETF rotation](concepts/hawkes-process-based-approach-to-etf-rotation.md) | ETF rotation | 5 | 8,478 | ⛔ Not useful | Unable to find more details |
| [Adversarially robust approach to liquidity-shock detection and response](concepts/adversarially-robust-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 5 | 8,479 | ⛔ Not useful | Unable to find more details |
| [Adaptive approach to delay-aware portfolio allocation](concepts/adaptive-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 5 | 8,480 | ⏳ Reference only | Unable to find more details |
| [Integrated approach to sector allocation](concepts/integrated-approach-to-sector-allocation.md) | Sector allocation | 5 | 8,482 | ⏳ Reference only | Unable to find more details |
| [Wavelet-based approach to leveraged-ETF exposure rebalancing](concepts/wavelet-based-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 5 | 8,483 | ⏳ Reference only | Unable to find more details |
| [Nonlinear approach to path-signature time-series forecasting](concepts/nonlinear-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 5 | 8,484 | ⛔ Not useful | Unable to find more details |
| [Graph-based approach to benchmark index tracking](concepts/graph-based-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 5 | 8,486 | ⛔ Not useful | Unable to find more details |
| [Recursive approach to liquidity-shock detection and response](concepts/recursive-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 7 | 8,487 | ⏳ Reference only | Unable to find more details |
| [Topology-aware approach to delay-aware portfolio allocation](concepts/topology-aware-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 5 | 8,488 | ⛔ Not useful | Unable to find more details |
| [Path-signature-based approach to regime-aware allocation](concepts/path-signature-based-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 5 | 8,489 | ⛔ Not useful | Unable to find more details |
| [Evolutionary-optimization-based approach to leveraged-ETF exposure rebalancing](concepts/evolutionary-optimization-based-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 5 | 8,491 | ⛔ Not useful | Unable to find more details |
| [Integrated approach to path-signature time-series forecasting](concepts/integrated-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 5 | 8,492 | ⛔ Not useful | Unable to find more details |
| [Spectral approach to ETF rotation](concepts/spectral-approach-to-etf-rotation.md) | ETF rotation | 5 | 8,493 | ⏳ Reference only | Unable to find more details |
| [Quantum/quantum-inspired approach to liquidity-shock detection and response](concepts/quantum-quantum-inspired-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 5 | 8,495 | ⛔ Not useful | Unable to find more details |
| [Markov-state-based approach to regime-aware allocation](concepts/markov-state-based-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 5 | 8,497 | ⏳ Worth testing | Evidence found |
| [Adaptive approach to leveraged-ETF exposure rebalancing](concepts/adaptive-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 5 | 8,500 | ⏳ Worth testing | Evidence found |
| [Path-signature-based approach to path-signature time-series forecasting](concepts/path-signature-based-approach-to-path-signature-time-series-forecasting.md) | Path-signature time-series forecasting | 10 | 8,501 | ⛔ Not useful | Unable to find more details |
| [Evolutionary-optimization-based approach to benchmark index tracking](concepts/evolutionary-optimization-based-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 5 | 8,503 | ⛔ Not useful | Unable to find more details |
| [Koopman-operator-based approach to liquidity-shock detection and response](concepts/koopman-operator-based-approach-to-liquidity-shock-detection-and-response.md) | Liquidity-shock detection and response | 5 | 8,504 | ⛔ Not useful | Unable to find more details |
| [Wavelet-based approach to delay-aware portfolio allocation](concepts/wavelet-based-approach-to-delay-aware-portfolio-allocation.md) | Delay-aware portfolio allocation | 5 | 8,505 | ⏳ Reference only | Unable to find more details |
| [Nonlinear approach to regime-aware allocation](concepts/nonlinear-approach-to-regime-aware-allocation.md) | Regime-aware allocation | 5 | 8,506 | ⏳ Reference only | Unable to find more details |
| [Markov-state-based approach to sector allocation](concepts/markov-state-based-approach-to-sector-allocation.md) | Sector allocation | 5 | 8,507 | ⛔ Not useful | Evidence found |
| [Topology-aware approach to leveraged-ETF exposure rebalancing](concepts/topology-aware-approach-to-leveraged-etf-exposure-rebalancing.md) | Leveraged-ETF exposure rebalancing | 5 | 8,508 | ⛔ Not useful | Unable to find more details |
| [Adaptive approach to benchmark index tracking](concepts/adaptive-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 5 | 8,511 | ⛔ Not useful | Unable to find more details |
| [Distributionally robust approach to trade-execution optimization](concepts/distributionally-robust-approach-to-trade-execution-optimization.md) | Trade-execution optimisation | 1 | 13,833 | ⛔ Not useful | Unable to find more details |
| [Topology-aware approach to benchmark index tracking](concepts/topology-aware-approach-to-benchmark-index-tracking.md) | Benchmark index tracking | 5 | 13,846 | ⛔ Not useful | Unable to find more details |
| [Markov-state-based approach to cross-sectional stock ranking](concepts/markov-state-based-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 5 | 13,848 | ⛔ Not useful | Unable to find more details |
| [Integrated approach to cross-sectional stock ranking](concepts/integrated-approach-to-cross-sectional-stock-ranking.md) | Cross-sectional stock ranking | 5 | 13,850 | ⛔ Not useful | Unable to find more details |

## Implementation status values

| Value | Meaning |
|---|---|
| `yes` | Runs on the platform: a registered strategy, a strategy option, an engine feature or a harness mode. |
| `research` | The algorithm as described is tested standalone code in `research/`, not wired into a strategy or harness. |
| `partial` | A component, a long-only adaptation or a close variant exists; the algorithm as described does not. |
| `no` | Nothing in the repository (a row with `no` is there to carry a ledger ID or a note). |

In `implementation_status.csv`, `ledger` and `code` take several values
separated by `;`. A code reference is `package.module:qualname`,
`package.module` or a path such as `tools/rotation.py`; the tests import
or find every one.

## Changing anything here

```bash
# after editing implementation_status.csv, or researching a page
python tools/build_algorithm_ledger.py
python tools/build_algorithm_ledger.py --check     # what the test runs: exit 1 if stale
# a new export of the list
python tools/build_algorithm_ledger.py --source docs/algorithms/source/<new>.csv.xz
```

Generated pages are overwritten and, when the import stops producing
them, deleted. A page whose first line is not the `generated` comment is
never touched. To research an algorithm: write its page over the card
(keep the file name, drop the comment line), add an `RK<rank>` entry to
the ledger's §8C and to `research/catalog/registry.py`, put the RK ID in
its `implementation_status.csv` row, and re-run the build.
