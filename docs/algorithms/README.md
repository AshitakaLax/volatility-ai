# Algorithm pages

One page per algorithm in the ranked list of
[`docs/algorithm_ledger.md` §8C](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import),
the 14,225-row CSV import of 2026-10-27. The ledger's tables say, for
every row, whether volatility-ai implements it and link here.

| Path | What it is | Written by |
|---|---|---|
| `<slug>.md` without a `generated` first line | A **researched** page: the rule, evidence for and against, fit with the project's constraints, what the repository already has, and how to test it here. Ledger IDs RK1–RK100 and RK200–RK425 (the same ranks). | hand |
| `<slug>.md` with a `generated` first line | A **card** for one of the 425 specific algorithms (ranks 1–425): the CSV's own text plus the implementation status. | `tools/build_algorithm_ledger.py` |
| `concepts/<slug>.md` | One page per description shared by the 13,800 title-reconstructed rows (ranks 426–14,225): the description, every variant of the other fields its members carry, and the members. [Index](concepts/README.md). A concept page without a `generated` first line is **researched**: the 34 concepts of ranks 426–700 are. | the build; researched ones by hand |
| `ranked/ranks-*.md` | The title-reconstructed rows by rank, 1,000 per page, each linked to its concept page. | the build |
| `implementation_status.csv` | Which algorithms have code here: status, ledger IDs, code references, a note. Not listed means not implemented. | hand |
| `source/*.csv.xz` | The import itself, every field of every row (`xz -dk` to read it). | the import |

## Researched so far

Ranks 1–100 and 200–425, one page each (101–199 are not yet researched). Each page says what its sources are and how far
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
RK98, RK99, RK100; RK201, RK202, RK203, RK205, RK206, RK208, RK212,
RK216, RK217, RK221, RK222, RK224, RK227, RK228, RK230, RK231, RK233,
RK234, RK236, RK237, RK238, RK239, RK240, RK241, RK243, RK257, RK258,
RK261, RK262, RK263, RK264, RK265, RK266, RK270, RK272, RK273, RK280,
RK283, RK287, RK288, RK289, RK297; RK304, RK307, RK315, RK320, RK321,
RK323, RK325, RK326, RK330, RK332, RK333, RK334, RK335, RK337, RK338,
RK339, RK340, RK341, RK342, RK344, RK345, RK350, RK353, RK354, RK355,
RK356, RK357, RK358, RK359, RK360, RK362, RK365, RK369, RK370, RK371,
RK374, RK375, RK380, RK384, RK386, RK387, RK388, RK389, RK390, RK392,
RK393, RK394, RK396, RK397, RK398; RK401, RK403, RK404, RK409, RK410,
RK411, RK412, RK414, RK415, RK416, RK417, RK418, RK421, RK422, RK423,
RK424, RK425.

For the concepts of ranks 426–700, the Evidence column above gives the
status: 1 needs more info, 21 unable to find more details.

[The ledger's table](../algorithm_ledger.md#research-gaps) says what each
one lacks.

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
