# Persistent Homology Betti-2 Persistence Landscape Macro Contagion

**Ledger ID RK398** · rank 398 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Topological data analysis / Persistence landscapes / Macro risk |
| Potential effectiveness rank | 398 (1 = strongest) |
| AI implementability rank | 126 (1 = easiest) |
| Retail advantage rank | 209 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.topology`: `landscape_norm_series`, `betti2_macro_stress`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK265, RK255, RK268 |

## In one paragraph

Track two-dimensional holes (Betti-2) in persistence landscapes of
multi-asset point clouds as a macro contagion warning. It combines RK265
(Betti-2) and RK255 (landscapes). The landscape evidence covers two
crashes in sample; I found nothing for Betti-2, and the CSV's reference,
arXiv 2004.01234, could not be identified.

## Evidence

* **Gidea & Katz (2018), *Physica A* 491, 820–834:**
  persistence-landscape norms of four US indices grew before the 2000
  and 2008 crashes, in sample (see RK255).
* **No Betti-2 study found.**

## Against, and failure modes

* Higher Betti numbers are rare and noisy in small point clouds.

## Fit with volatility-ai

Test RK255's landscape norms first; Betti-2 adds nothing with evidence.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834.
  <https://arxiv.org/abs/1703.04385>. Abstract.
