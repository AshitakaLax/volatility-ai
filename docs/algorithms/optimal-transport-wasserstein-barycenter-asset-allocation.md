# Optimal Transport Wasserstein Barycenter Asset Allocation

**Ledger ID RK124** · rank 124 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Optimal Transport / Portfolio Construction |
| Potential effectiveness rank | 124 (1 = strongest) |
| AI implementability rank | 228 (1 = easiest) |
| Retail advantage rank | 142 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset scenario-blending tool with one preprint behind it. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK63, RK225 |

## In one paragraph

Blend competing scenario distributions of returns by their Wasserstein
barycenter and optimise against the consensus. The closest published
work (Antonov, Balasubramanian, Lipton and López de Prado 2024) uses a
generalised barycenter to merge statistics with investor views as an
alternative to Black-Litterman; the CSV's reference, arXiv 2007.08316,
could not be identified.

## Evidence

* **Antonov et al. (2024, arXiv 2406.01199):** a geometric,
  Wasserstein-barycenter approach to asset allocation with investor
  views, positioned against Black-Litterman. (Abstract.)
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* The barycenter of Gaussians is closed-form but only as good as the
  scenario inputs.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Antonov, A., Balasubramanian, K., Lipton, A., López de Prado, M.
  (2024). A Geometric Approach To Asset Allocation With Investor Views.
  <https://arxiv.org/abs/2406.01199>. Abstract.
* The CSV's reference, arXiv 2007.08316 (not identified).
