# Grid / Price-Ladder Trading

**Ledger ID RK164** · rank 164 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion / inventory |
| Potential effectiveness rank | 164 (1 = strongest) |
| AI implementability rank | 33 (1 = easiest) |
| Retail advantage rank | 64 (1 = strongest) |
| Fit with this project | ✅ in use |
| Useful for volatility-ai | **In use.** This is the project: the champion is a volatility-scaled grid on TQQQ (V5). |
| Implemented in volatility-ai | **Yes.** `research.strategies.high_frequency_sizing`: `HighFrequencyLocalReferenceSizing`. |
| Related ledger entries | V1, V2, V3, V4, V5, C-G2, C-G3, C-G4 |

## In one paragraph

Place staggered buys and sells at fixed or volatility-scaled intervals
and recycle inventory. Under a random walk a plain grid has zero
expected profit before costs (Chen, Chen and Jang); its returns come
from mean reversion within the range and its losses from one-way
markets. This project's grid adds the pieces that address that: per-lot
profit targets, the no-loss rule, volatility-scaled steps and a regime
exit.

## Evidence

* **Chen, Chen & Jang (2025, arXiv 2506.11921):** a traditional grid has
  zero expected return under simple assumptions; a dynamic grid that
  resets beat it and buy-and-hold on minute crypto data, 2021–2024, in
  the authors' backtests (preprint).
* **This repository:** the champion `HighFrequencyLocalReferenceSizing`
  (V5) with its grid variants (C-G2–C-G4); see README.md's simulations
  and the regression baseline.

## Against, and failure modes

* One-way declines strand lots; on a 3x ETF the regime exit is what
  bounds that.

## Fit with volatility-ai

In use: it is the core strategy. The literature adds one useful point: a
grid's edge is the asset's mean reversion within the grid range, which
is what the regime gate protects.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chen, K.-Y., Chen, K.-H., Jang, J.-S. R. (2025). Dynamic Grid Trading
  Strategy: From Zero Expectation to Market Outperformance.
  <https://arxiv.org/abs/2506.11921>. Abstract.
