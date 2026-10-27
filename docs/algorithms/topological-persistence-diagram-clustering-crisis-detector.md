# Topological Persistence Diagram Clustering Crisis Detector

**Ledger ID RK263** · rank 263 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Topological data analysis / Risk management / Crash prediction |
| Potential effectiveness rank | 263 (1 = strongest) |
| AI implementability rank | 117 (1 = easiest) |
| Retail advantage rank | 194 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK254, RK255, RK262, RK268, RK269 |

## In one paragraph

Cluster rolling persistence diagrams by Wasserstein distance and alert
when the cluster structure changes abruptly. The core evidence is Gidea
and Katz (2018): landscape norms of four US indices' returns grew before
the dot-com and Lehman crashes. That is two events, in sample. The CSV's
reference (arXiv 1904.04044) could not be identified.

## Evidence

* **Gidea & Katz (2018), "Topological data analysis of financial time
  series: Landscapes of crashes," *Physica A* 491, 820–834:**
  sliding-window point clouds of daily log-returns of the S&P 500, DJIA,
  Nasdaq and Russell 2000; the Lp-norms of persistence landscapes grow
  before the primary peak of a crash, and their low-frequency spectral
  density rises for about 250 trading days before the March 2000 dot-com
  peak and the Lehman bankruptcy. Two crashes, in sample, no
  out-of-sample test in the abstract. (Abstract.)

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
* The CSV's references: giotto-tda; arXiv 1904.04044 (not identified).
