# Algorithm pages

One page per algorithm in the ranked list of
[`docs/algorithm_ledger.md` §8C](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import),
the 14,225-row CSV import of 2026-10-27. The ledger's tables say, for
every row, whether volatility-ai implements it and link here.

| Path | What it is | Written by |
|---|---|---|
| `<slug>.md` without a `generated` first line | A **researched** page: the rule, evidence for and against, fit with the project's constraints, what the repository already has, and how to test it here. Ledger IDs RK1–RK100 and RK200–RK300 (the same ranks). | hand |
| `<slug>.md` with a `generated` first line | A **card** for one of the 425 specific algorithms (ranks 1–425): the CSV's own text plus the implementation status. | `tools/build_algorithm_ledger.py` |
| `concepts/<slug>.md` | One page per description shared by the 13,800 title-reconstructed rows (ranks 426–14,225): the description, every variant of the other fields its members carry, and the members. [Index](concepts/README.md). | the build |
| `ranked/ranks-*.md` | The title-reconstructed rows by rank, 1,000 per page, each linked to its concept page. | the build |
| `implementation_status.csv` | Which algorithms have code here: status, ledger IDs, code references, a note. Not listed means not implemented. | hand |
| `source/*.csv.xz` | The import itself, every field of every row (`xz -dk` to read it). | the import |

## Researched so far

Ranks 1–100 and 200–300, one page each (101–199 are not yet researched). Each page says what its sources are and how far
they could be checked (full texts could not be opened from the research environment).

| ID | Algorithm | Rank | Implemented |
|---|---|---|---|
| RK1 | [Time-Series Momentum (TSMOM)](time-series-momentum-tsmom.md) | 1 | Research code (as published) |
| RK2 | [Volatility-Scaled Trend Following](volatility-scaled-trend-following.md) | 2 | Research code; the scaling half is wired (S4) |
| RK3 | [Dual Momentum (Absolute + Relative)](dual-momentum-absolute-relative.md) | 3 | Yes, as `tools/rotation.py --mode relative_strength` (X3) |
| RK4 | [Cross-Asset Carry Composite](cross-asset-carry-composite.md) | 4 | No |
| RK5 | [Value-Momentum Composite](value-momentum-composite.md) | 5 | No |
| RK6 | [12–1 Momentum (Skip-Month)](12-1-momentum-skip-month.md) | 6 | No |
| RK7 | [Cross-Sectional Momentum](cross-sectional-momentum.md) | 7 | Partial (X3) |
| RK8 | [Commodity Momentum + Term Structure](commodity-momentum-term-structure.md) | 8 | No |
| RK9 | [Fama–French Five-Factor Model Portfolio](fama-french-five-factor-model-portfolio.md) | 9 | No |
| RK10 | [State-Filtered Momentum](state-filtered-momentum.md) | 10 | Partial |
| RK11 | [Quality Minus Junk (QMJ)](quality-minus-junk-qmj.md) | 11 | No |
| RK12 | [Quality / Profitability Factor](quality-profitability-factor.md) | 12 | No |
| RK13 | [Gross Profitability Factor](gross-profitability-factor.md) | 13 | No |
| RK14 | [52-Week High Momentum](52-week-high-momentum.md) | 14 | Partial |
| RK15 | [Conservative Investment Factor](conservative-investment-factor.md) | 15 | No |
| RK16 | [Residual Momentum](residual-momentum.md) | 16 | No |
| RK17 | [10-Month Moving-Average Risk Filter](10-month-moving-average-risk-filter.md) | 17 | Yes (V16, C-E2) |
| RK18 | [Low-Volatility Equity](low-volatility-equity.md) | 18 | Partial (X2) |
| RK19 | [Sector Momentum Rotation](sector-momentum-rotation.md) | 19 | Partial (X3) |
| RK20 | [Bond Duration Momentum](bond-duration-momentum.md) | 20 | No |
| RK21 | [VIX-Regime Conditional Equity Exposure](vix-regime-conditional-equity-exposure.md) | 21 | Yes (V12) |
| RK22 | [Volatility Targeting / Risk Scaling](volatility-targeting-risk-scaling.md) | 22 | Yes (S4, V18, S3) |
| RK23 | [Drawdown-Aware De-Risking Governor](drawdown-aware-de-risking-governor.md) | 23 | Yes (V11) |
| RK24 | [ETF NAV / Creation-Redemption Arbitrage](etf-nav-creation-redemption-arbitrage.md) | 24 | Research code (C-RJ6) |
| RK25 | [Index Futures vs Cash Basis Arbitrage](index-futures-vs-cash-basis-arbitrage.md) | 25 | No |
| RK26 | [Futures Cash-and-Carry Basis Trading](futures-cash-and-carry-basis-trading.md) | 26 | Partial |
| RK27 | [Shareholder Yield Factor](shareholder-yield-factor.md) | 27 | No |
| RK28 | [Fixed-Income Carry and Roll-Down](fixed-income-carry-and-roll-down.md) | 28 | No |
| RK29 | [Price + Earnings Momentum](price-earnings-momentum.md) | 29 | No |
| RK30 | [FX Carry Trade](fx-carry-trade.md) | 30 | No |
| RK31 | [Intangibles-Adjusted Value and Profitability Factor](intangibles-adjusted-value-and-profitability-factor.md) | 31 | No |
| RK32 | [Commodity Futures Roll Yield](commodity-futures-roll-yield.md) | 32 | No |
| RK33 | [Market-Neutral Residual Mean Reversion](market-neutral-residual-mean-reversion.md) | 33 | Research code (C-MR2) |
| RK34 | [Futures Calendar-Spread Mean Reversion](futures-calendar-spread-mean-reversion.md) | 34 | No |
| RK35 | [Net Stock Issuance Anomaly](net-stock-issuance-anomaly.md) | 35 | No |
| RK36 | [Johansen Cointegration Basket Trading](johansen-cointegration-basket-trading.md) | 36 | No |
| RK37 | [Cointegration-Based Pairs Trading](cointegration-based-pairs-trading.md) | 37 | Research code (Q2) |
| RK38 | [Chandelier Exit Trend Following](chandelier-exit-trend-following.md) | 38 | Partial (V10, Q8) |
| RK39 | [Merger Arbitrage](merger-arbitrage.md) | 39 | No |
| RK40 | [Earnings Estimate Revision Momentum](earnings-estimate-revision-momentum.md) | 40 | No |
| RK41 | [Inflation-Regime Asset Rotation](inflation-regime-asset-rotation.md) | 41 | No |
| RK42 | [Cross-Asset Commodity Futures Term-Structure Carry & Roll Yield](cross-asset-commodity-futures-term-structure-carry-roll-yield.md) | 42 | No |
| RK43 | [Donchian / Turtle Channel Breakout](donchian-turtle-channel-breakout.md) | 43 | Research code (C-G5) |
| RK44 | [Supertrend ATR-Band Trend Following](supertrend-atr-band-trend-following.md) | 44 | No |
| RK45 | [Post-Earnings Announcement Drift (PEAD)](post-earnings-announcement-drift-pead.md) | 45 | No |
| RK46 | [MACD Signal-Line Crossover](macd-signal-line-crossover.md) | 46 | Yes (Q1) |
| RK47 | [Public Activist-Filing Event Strategy](public-activist-filing-event-strategy.md) | 47 | No |
| RK48 | [Book-to-Market Value](book-to-market-value.md) | 48 | No |
| RK49 | [Betting Against Beta (BAB)](betting-against-beta-bab.md) | 49 | No |
| RK50 | [Accrual Anomaly](accrual-anomaly.md) | 50 | No |
| RK51 | [Asset-Growth Anomaly](asset-growth-anomaly.md) | 51 | No |
| RK52 | [Dividend Yield / Dividend Growth](dividend-yield-dividend-growth.md) | 52 | Partial |
| RK53 | [CVaR / Expected-Shortfall Optimization](cvar-expected-shortfall-optimization.md) | 53 | No |
| RK54 | [Volatility-Managed Factor Portfolio](volatility-managed-factor-portfolio.md) | 54 | Partial (S4) |
| RK55 | [ADX-Filtered Trend Following](adx-filtered-trend-following.md) | 55 | Partial (V15) |
| RK56 | [Hierarchical Risk Parity (HRP)](hierarchical-risk-parity-hrp.md) | 56 | Yes (A5, Q13) |
| RK57 | [Low P/E Value Screen](low-p-e-value-screen.md) | 57 | No |
| RK58 | [Small-Cap Size Premium](small-cap-size-premium.md) | 58 | No |
| RK59 | [Liquidity Factor](liquidity-factor.md) | 59 | Partial |
| RK60 | [Global Minimum-Variance Portfolio](global-minimum-variance-portfolio.md) | 60 | Research code (Q13) |
| RK61 | [Risk Parity / Equal Risk Contribution](risk-parity-equal-risk-contribution.md) | 61 | Partial (A5) |
| RK62 | [Dual Moving Average Crossover](dual-moving-average-crossover.md) | 62 | Research code (Q1, C-E2) |
| RK63 | [Black–Litterman Allocation](black-litterman-allocation.md) | 63 | No |
| RK64 | [Triple EMA / Moving-Average Ribbon](triple-ema-moving-average-ribbon.md) | 64 | Partial (V15) |
| RK65 | [Cross-Sectional Factor Momentum Rotation](cross-sectional-factor-momentum-rotation.md) | 65 | No |
| RK66 | [Maximum-Diversification Portfolio](maximum-diversification-portfolio.md) | 66 | No |
| RK67 | [ATR-Based Position Sizing](atr-based-position-sizing.md) | 67 | Research code (C-G5) |
| RK68 | [Dual Thrust Breakout](dual-thrust-breakout.md) | 68 | Research code (Q7, N1) |
| RK69 | [London Session Breakout](london-session-breakout.md) | 69 | Research code (Q4, N2, N3) |
| RK70 | [Parabolic SAR Trend / Stop](parabolic-sar-trend-stop.md) | 70 | Yes (Q8) |
| RK71 | [Heikin-Ashi Trend Filter](heikin-ashi-trend-filter.md) | 71 | Yes (Q3) |
| RK72 | [Distance-Based Pairs Trading](distance-based-pairs-trading.md) | 72 | No |
| RK73 | [Kalman-Filter Dynamic-Hedge Pairs](kalman-filter-dynamic-hedge-pairs.md) | 73 | Research code (Q2) |
| RK74 | [Copula-Based Pairs Trading](copula-based-pairs-trading.md) | 74 | No |
| RK75 | [Ornstein–Uhlenbeck Spread Trading](ornstein-uhlenbeck-spread-trading.md) | 75 | Research code (C-MR2, C-MR4) |
| RK76 | [PCA Residual Statistical Arbitrage](pca-residual-statistical-arbitrage.md) | 76 | Partial (C-MR2) |
| RK77 | [ATR Volatility-Expansion Breakout](atr-volatility-expansion-breakout.md) | 77 | No |
| RK78 | [Multi-Timeframe Trend Agreement](multi-timeframe-trend-agreement.md) | 78 | No |
| RK79 | [Opening Gap Continuation](opening-gap-continuation.md) | 79 | Partial (N3, X1) |
| RK80 | [Convertible Bond Arbitrage](convertible-bond-arbitrage.md) | 80 | No |
| RK81 | [Capital Structure Arbitrage](capital-structure-arbitrage.md) | 81 | No |
| RK82 | [Closed-End Fund Discount Reversion](closed-end-fund-discount-reversion.md) | 82 | No |
| RK83 | [Triangular FX Arbitrage](triangular-fx-arbitrage.md) | 83 | Research code (A7) |
| RK84 | [Crypto Perpetual Funding-Rate Capture](crypto-perpetual-funding-rate-capture.md) | 84 | Research code (C-RJ2) |
| RK85 | [Spot-Perpetual Basis Arbitrage](spot-perpetual-basis-arbitrage.md) | 85 | Partial (C-RJ2) |
| RK86 | [Yield Curve Steepener / Flattener](yield-curve-steepener-flattener.md) | 86 | No |
| RK87 | [Option Dispersion Trading](option-dispersion-trading.md) | 87 | No |
| RK88 | [Distributionally Robust CVaR Allocation](distributionally-robust-cvar-allocation.md) | 88 | No |
| RK89 | [Autoencoder Latent-Factor Statistical Arbitrage](autoencoder-latent-factor-statistical-arbitrage.md) | 89 | No |
| RK90 | [Long-Term Industry Reversal with Valuation Confirmation](long-term-industry-reversal-with-valuation-confirmation.md) | 90 | No |
| RK91 | [iNAV Dislocation ETF Arbitrage](inav-dislocation-etf-arbitrage.md) | 91 | Partial (C-RJ6) |
| RK92 | [FED OTC Liquidity Sweep & Reverse Repo Arbitrage](fed-otc-liquidity-sweep-reverse-repo-arbitrage.md) | 92 | No |
| RK93 | [Cointegrated Triplet Basket Statistical Arbitrage](cointegrated-triplet-basket-statistical-arbitrage.md) | 93 | No |
| RK94 | [Dynamic Copula-GARCH Multivariate Pair Trading](dynamic-copula-garch-multivariate-pair-trading.md) | 94 | No |
| RK95 | [Asymmetric Tail-Risk Parity Allocation](asymmetric-tail-risk-parity-allocation.md) | 95 | No |
| RK96 | [Principal Component Analysis (PCA) Eigenportfolios Statistical Arbitrage](principal-component-analysis-pca-eigenportfolios-statistical-arbitrage.md) | 96 | Partial (C-MR2) |
| RK97 | [Wasserstein Distributionally Robust Statistical Arbitrage](wasserstein-distributionally-robust-statistical-arbitrage.md) | 97 | No |
| RK98 | [Adversarial Domain Generalization Cross-Market Momentum](adversarial-domain-generalization-cross-market-momentum.md) | 98 | No |
| RK99 | [Conformally Constrained Risk Parity Portfolio](conformally-constrained-risk-parity-portfolio.md) | 99 | Partial |
| RK100 | [Causal Discovery Directed Acyclic Graph (DAG) Pair Selection](causal-discovery-directed-acyclic-graph-dag-pair-selection.md) | 100 | No |
| RK200 | [Generative Score-Based Diffusion Multi-Asset Scenario Synthesizer](generative-score-based-diffusion-multi-asset-scenario-synthesizer.md) | 200 | No |
| RK201 | [Koopman Operator Predictive Control Statistical Arbitrage](koopman-operator-predictive-control-statistical-arbitrage.md) | 201 | No |
| RK202 | [Fractional Brownian Motion Multi-Scale Trend Scanning Strategy](fractional-brownian-motion-multi-scale-trend-scanning-strategy.md) | 202 | No |
| RK203 | [Koopman Operator Model Predictive Control Spread Equilibrium](koopman-operator-model-predictive-control-spread-equilibrium.md) | 203 | No |
| RK204 | [Lead-Lag Cross-Asset Predictive Trading](lead-lag-cross-asset-predictive-trading.md) | 204 | Research code |
| RK205 | [Dynamic Tensor Decomposition Multi-Asset Factor Rotation](dynamic-tensor-decomposition-multi-asset-factor-rotation.md) | 205 | No |
| RK206 | [Koopman Operator Model Predictive Control Multi-Asset Allocation](koopman-operator-model-predictive-control-multi-asset-allocation.md) | 206 | No |
| RK207 | [Standardized Unexpected Earnings (SUE)](standardized-unexpected-earnings-sue.md) | 207 | No |
| RK208 | [Anchored VWAP Reclaim / Rejection](anchored-vwap-reclaim-rejection.md) | 208 | Partial (C-MS3) |
| RK209 | [Corporate Buyback Announcement Drift](corporate-buyback-announcement-drift.md) | 209 | No |
| RK210 | [Index Reconstitution / Rebalance Event Trading](index-reconstitution-rebalance-event-trading.md) | 210 | No |
| RK211 | [Macro Surprise / Economic Release Strategy](macro-surprise-economic-release-strategy.md) | 211 | Partial (V6) |
| RK212 | [Market Breadth Thrust](market-breadth-thrust.md) | 212 | No |
| RK213 | [Trend-Scanning Label Model](trend-scanning-label-model.md) | 213 | Research code (C-ML1) |
| RK214 | [XGBoost Cross-Sectional Ranking](xgboost-cross-sectional-ranking.md) | 214 | No |
| RK215 | [Cross-Sectional Reversal with Risk Neutralization](cross-sectional-reversal-with-risk-neutralization.md) | 215 | Partial (C-MR1) |
| RK216 | [Top-K with Dropout Portfolio Rotation](top-k-with-dropout-portfolio-rotation.md) | 216 | No |
| RK217 | [Bayesian Structural Time Series (BSTS) Causal Impact Macro Strategy](bayesian-structural-time-series-bsts-causal-impact-macro-strategy.md) | 217 | No |
| RK218 | [Sparse Bayesian Learning Dynamic Factor Model](sparse-bayesian-learning-dynamic-factor-model.md) | 218 | No |
| RK219 | [Dynamic Mode Decomposition (DMD) Market Mode Predictor](dynamic-mode-decomposition-dmd-market-mode-predictor.md) | 219 | No |
| RK220 | [Continuous-Time Mean-Variance Reinforcement Learning Agent](continuous-time-mean-variance-reinforcement-learning-agent.md) | 220 | No |
| RK221 | [Information-Theoretic Transfer Entropy Lead-Lag Strategy](information-theoretic-transfer-entropy-lead-lag-strategy.md) | 221 | No |
| RK222 | [Maximum Entropy Production Rate Macro Allocator](maximum-entropy-production-rate-macro-allocator.md) | 222 | No |
| RK223 | [Quantum Tensor Network Portfolio Optimization](quantum-tensor-network-portfolio-optimization.md) | 223 | No |
| RK224 | [Deep Latent Force Model (LFM) Interest Rate Forecaster](deep-latent-force-model-lfm-interest-rate-forecaster.md) | 224 | No |
| RK225 | [Wasserstein Distributionally Robust Mean-Variance Allocation](wasserstein-distributionally-robust-mean-variance-allocation.md) | 225 | No |
| RK226 | [Functional Principal Component Analysis (FPCA) Yield Curve Forecaster](functional-principal-component-analysis-fpca-yield-curve-forecaster.md) | 226 | No |
| RK227 | [Multi-Agent Evolutionary Reinforcement Learning Portfolio Optimizer](multi-agent-evolutionary-reinforcement-learning-portfolio-optimizer.md) | 227 | No |
| RK228 | [Deep Generative Flow Matching Portfolio Generator](deep-generative-flow-matching-portfolio-generator.md) | 228 | No |
| RK229 | [Quantum Adiabatic Optimal Portfolio Rebalancing](quantum-adiabatic-optimal-portfolio-rebalancing.md) | 229 | No |
| RK230 | [Riemannian Manifold Metric Optimization Portfolio](riemannian-manifold-metric-optimization-portfolio.md) | 230 | No |
| RK231 | [Riemannian Manifold Metric Diffusion Portfolio Allocation](riemannian-manifold-metric-diffusion-portfolio-allocation.md) | 231 | No |
| RK232 | [Graph Attention Network Covariance Shrinkage Estimator](graph-attention-network-covariance-shrinkage-estimator.md) | 232 | No |
| RK233 | [Riemannian Manifold Metric Wasserstein Robust Allocation](riemannian-manifold-metric-wasserstein-robust-allocation.md) | 233 | No |
| RK234 | [Wasserstein Distributionally Robust Reinforcement Learning Portfolio Agent](wasserstein-distributionally-robust-reinforcement-learning-portfolio-agent.md) | 234 | No |
| RK235 | [Graph Attention Network Covariance Matrix Shrinkage Dynamic Allocation](graph-attention-network-covariance-matrix-shrinkage-dynamic-allocation.md) | 235 | No |
| RK236 | [Quantum Adiabatic Graph Neural Network Portfolio Optimization](quantum-adiabatic-graph-neural-network-portfolio-optimization.md) | 236 | No |
| RK237 | [Riemannian Manifold Metric Graph Attention Portfolio Allocation](riemannian-manifold-metric-graph-attention-portfolio-allocation.md) | 237 | No |
| RK238 | [Quantum Adiabatic Tensor Network Portfolio Optimization](quantum-adiabatic-tensor-network-portfolio-optimization.md) | 238 | No |
| RK239 | [Fractional Order Vector Error Correction Neural Network Portfolio Allocator](fractional-order-vector-error-correction-neural-network-portfolio-allocator.md) | 239 | No |
| RK240 | [Neural Operator Delay-Differential Stochastic Volatility Calibrator](neural-operator-delay-differential-stochastic-volatility-calibrator.md) | 240 | No |
| RK241 | [Koopman Operator Multi-Factor Equity Risk Factor Tracking](koopman-operator-multi-factor-equity-risk-factor-tracking.md) | 241 | No |
| RK242 | [Long-Volatility Breakout (Options)](long-volatility-breakout-options.md) | 242 | Research code (Q12) |
| RK243 | [Price/Volume Anomaly Detection](price-volume-anomaly-detection.md) | 243 | Partial (A8) |
| RK244 | [Liquidity-Aware Adaptive Execution](liquidity-aware-adaptive-execution.md) | 244 | Partial |
| RK245 | [Pure Passive Market Making](pure-passive-market-making.md) | 245 | Research code (C-MM1, C-MM2) |
| RK246 | [Inventory-Skewed Market Making](inventory-skewed-market-making.md) | 246 | Research code (C-G2, C-MM1) |
| RK247 | [VPIN Flow-Toxicity Filter](vpin-flow-toxicity-filter.md) | 247 | Research code (C-MM4) |
| RK248 | [Hawkes-Process Order-Flow Forecast](hawkes-process-order-flow-forecast.md) | 248 | No |
| RK249 | [Iceberg / Reserve-Order Execution](iceberg-reserve-order-execution.md) | 249 | No |
| RK250 | [Arrival-Price Adaptive Limit-vs-Market Execution](arrival-price-adaptive-limit-vs-market-execution.md) | 250 | Partial |
| RK251 | [Intraday Volume-Profile Execution](intraday-volume-profile-execution.md) | 251 | No |
| RK252 | [Order-Flow Imbalance (OFI) Cross-Sectional Alpha Predictor](order-flow-imbalance-ofi-cross-sectional-alpha-predictor.md) | 252 | Partial (C-MS1) |
| RK253 | [Information-Driven Volume Clock Imbalance Momentum](information-driven-volume-clock-imbalance-momentum.md) | 253 | Partial (C-ML5) |
| RK254 | [Persistent Homology Topological Data Analysis (TDA) Crash Predictor](persistent-homology-topological-data-analysis-tda-crash-predictor.md) | 254 | No |
| RK255 | [Persistent Homology Topological Landscape Crisis Predictor](persistent-homology-topological-landscape-crisis-predictor.md) | 255 | No |
| RK256 | [Deep Markov State-Space Intraday Volume Profile Predictor](deep-markov-state-space-intraday-volume-profile-predictor.md) | 256 | No |
| RK257 | [Information-Theoretic Causality Flow Macro Asset Allocator](information-theoretic-causality-flow-macro-asset-allocator.md) | 257 | No |
| RK258 | [Spiking Graph Convolutional Network (SGCN) Contagion Predictor](spiking-graph-convolutional-network-sgcn-contagion-predictor.md) | 258 | No |
| RK259 | [Hawkes-Driven Non-Parametric Order Flow Toxicity Filter](hawkes-driven-non-parametric-order-flow-toxicity-filter.md) | 259 | No |
| RK260 | [Quantum Approximate State Preparation Risk Mapping](quantum-approximate-state-preparation-risk-mapping.md) | 260 | No |
| RK261 | [Koopman Operator Model Predictive Control Risk Mitigation](koopman-operator-model-predictive-control-risk-mitigation.md) | 261 | No |
| RK262 | [Persistent Homology Betti-0 Connected Component Contagion Detector](persistent-homology-betti-0-connected-component-contagion-detector.md) | 262 | No |
| RK263 | [Topological Persistence Diagram Clustering Crisis Detector](topological-persistence-diagram-clustering-crisis-detector.md) | 263 | No |
| RK264 | [Information-Theoretic Directed GNN Contagion Model](information-theoretic-directed-gnn-contagion-model.md) | 264 | No |
| RK265 | [Persistent Homology Betti-2 3D Void Macro Stress Predictor](persistent-homology-betti-2-3d-void-macro-stress-predictor.md) | 265 | No |
| RK266 | [Riemannian Manifold Metric Entropic Risk Portfolio](riemannian-manifold-metric-entropic-risk-portfolio.md) | 266 | No |
| RK267 | [Graph Attention Network Covariance Matrix Spectral Regularization](graph-attention-network-covariance-matrix-spectral-regularization.md) | 267 | No |
| RK268 | [Persistent Homology Multi-Scale Vietoris-Rips Filtration Risk Scoring](persistent-homology-multi-scale-vietoris-rips-filtration-risk-scoring.md) | 268 | No |
| RK269 | [Persistent Homology Betti-0 Multiscale Filtration Contagion Clustering](persistent-homology-betti-0-multiscale-filtration-contagion-clustering.md) | 269 | Partial (A5) |
| RK270 | [Quantum Annealing Binary Matrix Factorization Portfolio Risk Model](quantum-annealing-binary-matrix-factorization-portfolio-risk-model.md) | 270 | No |
| RK271 | [Sequential Bootstrapping Sample Weights](sequential-bootstrapping-sample-weights.md) | 271 | No |
| RK272 | [Wavelet-Neural Network Hybrid Intraday Trend Scalper](wavelet-neural-network-hybrid-intraday-trend-scalper.md) | 272 | No |
| RK273 | [Deep Koopman-Inspired Spectral Asset Allocation](deep-koopman-inspired-spectral-asset-allocation.md) | 273 | No |
| RK274 | [Avellaneda–Stoikov Market Making](avellaneda-stoikov-market-making.md) | 274 | Research code (C-MM1) |
| RK275 | [DeepLOB-Style Order-Book Forecasting](deeplob-style-order-book-forecasting.md) | 275 | No |
| RK276 | [Queue-Reactive Market Making](queue-reactive-market-making.md) | 276 | Partial (C-MM5) |
| RK277 | [Hawkes Process Multi-Dimensional Order Flow Intensity Model](hawkes-process-multi-dimensional-order-flow-intensity-model.md) | 277 | No |
| RK278 | [Cross-Venue Crypto Triangular Arbitrage](cross-venue-crypto-triangular-arbitrage.md) | 278 | Research code (A7) |
| RK279 | [Asynchronous Multi-Exchange Spatial Arbitrage Graph](asynchronous-multi-exchange-spatial-arbitrage-graph.md) | 279 | Research code (A7) |
| RK280 | [Recurrent Neural Hawkes Point Process Toxic Flow Hedging Trigger](recurrent-neural-hawkes-point-process-toxic-flow-hedging-trigger.md) | 280 | No |
| RK281 | [Covered Call / Buy-Write](covered-call-buy-write.md) | 281 | Research code (S1) |
| RK282 | [Put-Write / Cash-Secured Put](put-write-cash-secured-put.md) | 282 | Research code (S1) |
| RK283 | [Wasserstein Distributionally Robust Neural Stochastic Control Hedging](wasserstein-distributionally-robust-neural-stochastic-control-hedging.md) | 283 | No |
| RK284 | [Options Wheel](options-wheel.md) | 284 | Research code (S1) |
| RK285 | [Iron Condor / Short Premium Range Strategy](iron-condor-short-premium-range-strategy.md) | 285 | No |
| RK286 | [Iron Butterfly Credit Strategy](iron-butterfly-credit-strategy.md) | 286 | No |
| RK287 | [Neural Operator Delay Differential Equation (Delay-ODE) Term Structure Predictor](neural-operator-delay-differential-equation-delay-ode-term-structure-predictor.md) | 287 | No |
| RK288 | [Neural Controlled Differential Equation (Neural CDE) Point Process Execution](neural-controlled-differential-equation-neural-cde-point-process-execution.md) | 288 | No |
| RK289 | [Neural Operator Delay-Differential Hawkes Microstructure Predictor](neural-operator-delay-differential-hawkes-microstructure-predictor.md) | 289 | No |
| RK290 | [Random Forest Return Classification](random-forest-return-classification.md) | 290 | No |
| RK291 | [Gradient-Boosted Trees Return Prediction](gradient-boosted-trees-return-prediction.md) | 291 | Yes (V13, V14) |
| RK292 | [LSTM Sequence Forecasting](lstm-sequence-forecasting.md) | 292 | Research code (C-RJ4) |
| RK293 | [News / Financial Sentiment NLP](news-financial-sentiment-nlp.md) | 293 | No |
| RK294 | [Triple-Barrier Labeled ML Strategy](triple-barrier-labeled-ml-strategy.md) | 294 | Partial (C-ML1) |
| RK295 | [Conformal Prediction Uncertainty Wrapper (CP-MAPIE)](conformal-prediction-uncertainty-wrapper-cp-mapie.md) | 295 | Research code (V13) |
| RK296 | [Dynamic Copula-Vine Regularized Factor Allocation](dynamic-copula-vine-regularized-factor-allocation.md) | 296 | No |
| RK297 | [Fractional Hurst-Driven Adaptive Bandwidth Mean Reversion](fractional-hurst-driven-adaptive-bandwidth-mean-reversion.md) | 297 | Partial (C-MR4) |
| RK298 | [AMM / CLOB Cross-Venue Arbitrage](amm-clob-cross-venue-arbitrage.md) | 298 | No |
| RK299 | [Dynamic AMM Liquidity Provision / Liquidity Mining](dynamic-amm-liquidity-provision-liquidity-mining.md) | 299 | No |
| RK300 | [Fractional Differentiation Feature Pipeline](fractional-differentiation-feature-pipeline.md) | 300 | Research code (C-ML5) |

### Research gaps

**Needs more info** (a reference is cited or likely exists but could not
be identified or read): RK31, RK44, RK68, RK93, RK97; RK219, RK232,
RK235, RK240, RK250, RK256, RK259, RK267, RK280, RK283, RK286.

**Unable to find more details** (no published evaluation found by two
searches): RK38, RK64, RK69, RK77, RK78, RK86, RK92, RK94, RK95, RK98,
RK99, RK100; RK201, RK202, RK203, RK205, RK206, RK208, RK212, RK216,
RK217, RK221, RK222, RK224, RK227, RK228, RK230, RK231, RK233, RK234,
RK236, RK237, RK238, RK239, RK241, RK243, RK257, RK258, RK261, RK262,
RK263, RK264, RK265, RK266, RK270, RK272, RK273, RK287, RK288, RK289,
RK297.

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
