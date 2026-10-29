# Persistent Homology Betti-0 Connected Component Contagion Detector

**Ledger ID RK262** · rank 262 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Topological data analysis / Risk management / Contagion |
| Potential effectiveness rank | 262 (1 = strongest) |
| AI implementability rank | 116 (1 = easiest) |
| Retail advantage rank | 193 (1 = strongest) |
| Fit with this project | ⛔ (simpler correlation measures do the same job) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK254, RK255, RK268, RK269 |

## In one paragraph

Track the number of connected components (Betti-0) of a rolling
correlation-threshold graph; a sudden merging of clusters signals
contagion. Fewer components at a fixed threshold is the same information
as rising average correlation, which simpler systemic-risk measures (the
absorption ratio) track directly. The core evidence is Gidea and Katz
(2018): landscape norms of four US indices' returns grew before the
dot-com and Lehman crashes. That is two events, in sample. The CSV's
reference (arXiv 1904.04044) is a set of pure-mathematics lecture notes
on persistence ("Topological Persistence in Geometry and Analysis"), not
a finance study.

## Evidence

* **Gidea & Katz (2018), "Topological data analysis of financial time
  series: Landscapes of crashes," *Physica A* 491, 820–834:**
  sliding-window point clouds of daily log-returns of the S&P 500, DJIA,
  Nasdaq and Russell 2000; the Lp-norms of persistence landscapes grow
  before the primary peak of a crash, and their low-frequency spectral
  density rises for about 250 trading days before the March 2000 dot-com
  peak and the Lehman bankruptcy. Two crashes, in sample, no
  out-of-sample test in the abstract. (Abstract.)
* **Kritzman, Li, Page & Rigobon (2011), "Principal components as a
  measure of systemic risk" (*Journal of Portfolio Management*):** the
  absorption ratio, the variance share of the top eigenvectors, rises
  with market fragility. (Standard reference; not re-checked here.)

## Against, and failure modes

* Two crashes are not a test; window, embedding and threshold choices
  are free parameters.
* Topological features of returns move with volatility and correlation,
  which simpler measures already track.

## Fit with volatility-ai

No evidence beyond Gidea & Katz's two in-sample crashes; not a candidate
before RK255 is tested.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834.
  <https://arxiv.org/abs/1703.04385>. Abstract.
* The CSV's references: giotto-tda; arXiv 1904.04044 (persistence
  lecture notes; not finance).
