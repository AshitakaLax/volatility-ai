# Algorithm pages

One page per algorithm in the ranked list of
[`docs/algorithm_ledger.md` §8C](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import),
the 14,225-row CSV import of 2026-10-27. The ledger's tables say, for
every row, whether volatility-ai implements it and link here.

| Path | What it is | Written by |
|---|---|---|
| `<slug>.md` without a `generated` first line | A **researched** page: the rule, evidence for and against, fit with the project's constraints, what the repository already has, and how to test it here. Ledger IDs RK1–RK100 (ranks 1–100). | hand |
| `<slug>.md` with a `generated` first line | A **card** for one of the 425 specific algorithms (ranks 1–425): the CSV's own text plus the implementation status. | `tools/build_algorithm_ledger.py` |
| `concepts/<slug>.md` | One page per description shared by the 13,800 title-reconstructed rows (ranks 426–14,225): the description, every variant of the other fields its members carry, and the members. [Index](concepts/README.md). | the build |
| `ranked/ranks-*.md` | The title-reconstructed rows by rank, 1,000 per page, each linked to its concept page. | the build |
| `implementation_status.csv` | Which algorithms have code here: status, ledger IDs, code references, a note. Not listed means not implemented. | hand |
| `source/*.csv.xz` | The import itself, every field of every row (`xz -dk` to read it). | the import |

## Researched so far

Ranks 1–100, one page each. Each page says what its sources are and how far
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

### Research gaps

**Needs more info** (a reference is cited or likely exists but could not
be identified or read): RK31, RK44, RK68, RK93, RK97.

**Unable to find more details** (no published evaluation found by two
searches): RK38, RK64, RK69, RK77, RK78, RK86, RK92, RK94, RK95, RK98,
RK99, RK100.

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
