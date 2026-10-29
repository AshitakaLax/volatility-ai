# Domain-Adversarial Neural Network (DANN) Cross-Market Alpha Transfer

**Ledger ID RK327** · rank 327 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Domain adaptation / Transfer learning / Quantitative equity |
| Potential effectiveness rank | 327 (1 = strongest) |
| AI implementability rank | 282 (1 = easiest) |
| Retail advantage rank | 26 (1 = strongest) |
| Fit with this project | ⛔ (cross-market stock alpha; accuracy-only evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK98 |

## In one paragraph

Train a forecaster on a data-rich market while a domain classifier,
reversed through a gradient-reversal layer, forces features that cannot
tell the markets apart, so the model transfers to a thin target market.
Domain-adversarial training is an established method (the CSV's
reference is the original paper). Stock studies report accuracy gains of
a few points, not trading results.

## Evidence

* **Ganin et al. (2016), "Domain-Adversarial Training of Neural
  Networks," *JMLR* 17 (arXiv 1505.07818, the CSV's reference):** the
  method. (Standard reference.)
* **Li, Dai & Zheng, "Selective transfer learning with adversarial
  training for stock movement prediction" (STLAT):** accuracy gains of
  3.8–4.9 points on the ACL18, KDD17 and CN50 datasets. (Abstract.)
* **ADA-FTSF (2023, *Neural Computing and Applications*):** adversarial
  domain adaptation across financial indexes, energy and agricultural
  futures. Forecast error only. (Abstract.)

## Against, and failure modes

* Domain-invariant features can discard exactly the market-specific
  signal; accuracy gains do not imply profit.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ganin, Y., et al. (2016). "Domain-Adversarial Training of Neural
  Networks." *JMLR* 17. <https://arxiv.org/abs/1505.07818>.
* Li, Dai, Zheng. STLAT. Abstract.
* ADA-FTSF (2023). *Neural Computing and Applications*.
  doi:10.1007/s00521-023-09047-1. Abstract.
