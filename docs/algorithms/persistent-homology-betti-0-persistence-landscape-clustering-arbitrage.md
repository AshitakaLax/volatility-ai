# Persistent Homology Betti-0 Persistence Landscape Clustering Arbitrage

**Ledger ID RK193** · rank 193 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Topological data analysis / Persistence landscapes / Statistical arbitrage |
| Potential effectiveness rank | 193 (1 = strongest) |
| AI implementability rank | 130 (1 = easiest) |
| Retail advantage rank | 216 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A short-leg relative-value trade; topology has crash-warning evidence only. |
| Implemented in volatility-ai | **Research code** `research.catalog.topology`: `landscape_norm_series`, `rips_persistence`. |
| Related ledger entries | RK255, RK401, RK263 |

## In one paragraph

Trade relative value when Betti-0 persistence-landscape cluster norms of
sliding correlation spaces deviate. Topological summaries have been
studied as crash warnings (Gidea and Katz) and as portfolio risk
measures (Goel and co-authors); I found no study trading relative value
on them, and the CSV's reference, arXiv 2004.01234, could not be
identified.

## Evidence

* **Gidea & Katz (2018), *Physica A* 491:** persistence-landscape norms
  of four US indices rose before the 2000 and 2008 crashes, in sample
  (see RK255).
* **Goel, Pasricha & Mehra (2020), *Expert Systems with Applications*;
  Goel, Sharma & Kanniainen (2026, arXiv 2601.03974):**
  persistence-landscape risk measures used for enhanced indexing and
  portfolio selection beat several benchmarks in the authors' tests; the
  2026 paper is a preprint. (Abstracts.)
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Landscape norms of small rolling point clouds are noisy, with window,
  embedding and dimension all free choices.

## Fit with volatility-ai

A relative-value trade across assets with a short leg; the one
topological measure with evidence (landscape norms before crashes,
RK255) is a risk warning, not a spread signal.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834.
  <https://arxiv.org/abs/1703.04385>. Abstract.
* Goel, A., Pasricha, P., Mehra, A. (2020). Topological data analysis in
  investment decisions. *Expert Systems with Applications*. Abstract;
  Goel, A., Sharma, Kanniainen, J. (2026).
  <https://arxiv.org/abs/2601.03974>. Abstract.
* The CSV's reference, arXiv 2004.01234 (not identified).
