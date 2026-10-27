# Persistent Homology Betti-0 Multiscale Filtration Contagion Clustering

**Ledger ID RK269** · rank 269 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Topological data analysis / Clustering / Risk management |
| Potential effectiveness rank | 269 (1 = strongest) |
| AI implementability rank | 127 (1 = easiest) |
| Retail advantage rank | 211 (1 = strongest) |
| Fit with this project | 🧪 the dendrogram exists inside HRP · ⏳ as a contagion signal |
| Implemented in volatility-ai | **Partial.** Single-linkage hierarchical clustering on correlation distance is built inside HRP (`hrp.hrp_weights`, ledger A5); no contagion detector. |
| Related ledger entries | A5, RK262, RK60 |

## In one paragraph

Track how clusters of assets merge as the correlation-distance threshold
rises (zero-dimensional persistence), and flag contagion when clusters
fuse suddenly. Betti-0 persistence of a distance filtration is exactly
the merge heights of single-linkage hierarchical clustering, so this is
a single-linkage dendrogram watched over time. HRP already builds that
dendrogram for allocation.

## Evidence

* **Gidea & Katz (2018), "Topological data analysis of financial time
  series: Landscapes of crashes," *Physica A* 491, 820–834:**
  sliding-window point clouds of daily log-returns of the S&P 500, DJIA,
  Nasdaq and Russell 2000; the Lp-norms of persistence landscapes grow
  before the primary peak of a crash, and their low-frequency spectral
  density rises for about 250 trading days before the March 2000 dot-com
  peak and the Lehman bankruptcy. Two crashes, in sample, no
  out-of-sample test in the abstract. (Abstract.)
* Betti-0 persistence of a Vietoris–Rips filtration equals the
  single-linkage dendrogram's merge heights (a standard result in
  topological data analysis).

## Against, and failure modes

* Cluster fusion in a selloff is rising correlation, which simpler
  measures track.

## Fit with volatility-ai

The dendrogram is built (HRP, A5). A contagion flag from falling merge
heights across the Nasdaq-100's sectors could feed the regime, but it
would mostly restate rising correlation; test RK255's landscape norms
first.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834.
  <https://arxiv.org/abs/1703.04385>. Abstract.
* This repository: `research/strategies/hrp.py` (single-linkage
  clustering), ledger A5.
