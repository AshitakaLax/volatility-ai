# Persistent Homology Betti-1 Loop Topological Momentum Strategy

**Ledger ID RK180** · rank 180 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Topological data analysis / Momentum / Cycle detection |
| Potential effectiveness rank | 180 (1 = strongest) |
| AI implementability rank | 118 (1 = easiest) |
| Retail advantage rank | 33 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** No study of loop counts as a momentum signal; topology's evidence is as a crash warning (RK255). |
| Implemented in volatility-ai | **Research code** `research.catalog.topology`: `betti_curve`. |
| Related ledger entries | RK255, RK401 |

## In one paragraph

Track one-dimensional loops (Betti-1) in correlation point clouds as a
sign of cyclical structure before trend reversals. Gidea and Katz's
landscape norms warned before two crashes in sample; I found nothing on
loops as a momentum signal, and the CSV's reference, arXiv 1904.04044,
is a set of pure-mathematics lecture notes on persistence ("Topological
Persistence in Geometry and Analysis"), not a finance study.

## Evidence

* **Gidea & Katz (2018), *Physica A* 491:** persistence-landscape norms
  of four US indices rose before the 2000 and 2008 crashes, in sample
  (see RK255).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Betti-1 counts in small rolling clouds are dominated by noise.

## Fit with volatility-ai

If topology is tested, test RK255's landscape-norm warning as a regime
input; a Betti-1 momentum rule has nothing behind it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834.
  <https://arxiv.org/abs/1703.04385>. Abstract.
* The CSV's reference, arXiv 1904.04044 (persistence lecture notes; not
  finance).
