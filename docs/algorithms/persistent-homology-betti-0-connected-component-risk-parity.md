# Persistent Homology Betti-0 Connected Component Risk Parity

**Ledger ID RK187** · rank 187 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Topological data analysis / Risk parity / Portfolio construction |
| Potential effectiveness rank | 187 (1 = strongest) |
| AI implementability rank | 124 (1 = easiest) |
| Retail advantage rank | 207 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset allocator; TDA portfolio results are the authors' own and none is risk parity. |
| Implemented in volatility-ai | **Research code** `research.catalog.topology`: `betti0_contagion`; `research.strategies.hrp`: `hrp_weights`. |
| Related ledger entries | A5, RK262 |

## In one paragraph

Cluster assets by connected-component persistence and allocate risk
parity across the clusters. Betti-0 persistence of a correlation
distance is single-linkage clustering, the same tree HRP uses; TDA
portfolio studies (Goel and co-authors) use landscape risk measures, not
risk parity, and the CSV's reference, arXiv 1904.04044, is a set of
pure-mathematics lecture notes on persistence ("Topological Persistence
in Geometry and Analysis"), not a finance study.

## Evidence

* **Goel, Pasricha & Mehra (2020), *Expert Systems with Applications*;
  Goel, Sharma & Kanniainen (2026, arXiv 2601.03974):**
  persistence-landscape risk measures used for enhanced indexing and
  portfolio selection beat several benchmarks in the authors' tests; the
  2026 paper is a preprint. (Abstracts.)
* **Betti-0 persistence equals single linkage**, the clustering inside
  HRP (A5).

## Against, and failure modes

* Adds a name to HRP's clustering rather than new information.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Goel, A., Pasricha, P., Mehra, A. (2020). Topological data analysis in
  investment decisions. *Expert Systems with Applications*. Abstract;
  Goel, A., Sharma, Kanniainen, J. (2026).
  <https://arxiv.org/abs/2601.03974>. Abstract.
* The CSV's reference, arXiv 1904.04044 (persistence lecture notes; not
  finance).
