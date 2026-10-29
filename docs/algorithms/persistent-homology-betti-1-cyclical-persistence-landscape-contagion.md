# Persistent Homology Betti-1 Cyclical Persistence Landscape Contagion

**Ledger ID RK401** · rank 401 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Topological data analysis / Persistence landscapes / Macro risk |
| Potential effectiveness rank | 401 (1 = strongest) |
| AI implementability rank | 129 (1 = easiest) |
| Retail advantage rank | 212 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.topology`: `landscape_norm_series`, `persistence_landscape`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK255, RK398, RK403 |

## In one paragraph

Track one-dimensional loops (Betti-1) in persistence landscapes of
rolling multi-asset correlation point clouds as a warning of contagion
before liquidity crunches. Gidea and Katz's landscape norms, which pool
all dimensions, rose before two crashes in sample; I found nothing
isolating this dimension, and the CSV's reference, arXiv 2004.01234,
could not be identified.

## Evidence

* **Gidea & Katz (2018), *Physica A* 491, 820–834:**
  persistence-landscape norms of four US indices grew before the 2000
  and 2008 crashes, in sample (see RK255).
* **No study found** of this Betti dimension as a warning signal.

## Against, and failure modes

* Higher Betti numbers are rare and noisy in small point clouds; window
  and embedding are free parameters.

## Fit with volatility-ai

Test RK255's landscape norms first; higher Betti numbers add nothing
with evidence.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834.
  <https://arxiv.org/abs/1703.04385>. Abstract.
