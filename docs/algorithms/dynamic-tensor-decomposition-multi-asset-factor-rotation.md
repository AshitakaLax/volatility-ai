# Dynamic Tensor Decomposition Multi-Asset Factor Rotation

**Ledger ID RK205** · rank 205 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Tensor algebra / Factor investing |
| Potential effectiveness rank | 205 (1 = strongest) |
| AI implementability rank | 77 (1 = easiest) |
| Retail advantage rank | 32 (1 = strongest) |
| Fit with this project | ⛔ (no evidence for factor rotation) |
| Implemented in volatility-ai | **Research code** in `research.catalog.allocation`: `cp_als`, `tensor_factor_rotation`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK7, RK19 |

## In one paragraph

Arrange returns as a tensor (time × asset × factor or characteristic),
decompose it (CP/PARAFAC or Tucker), and rotate across sectors by the
time-varying loadings. Tensor factor models are established in
statistics; I found no study applying them to factor or sector rotation.
The CSV's reference, arXiv 2001.00012, is a student paper on
differentially private wavelet mechanisms, unrelated to trading.

## Evidence

* **Chen, Yang & Zhang (2022), "Factor Models for High-Dimensional
  Tensor Time Series," *JASA* 117(537), 94–116:** Tucker-type tensor
  factor models with estimation theory; applications to transport
  networks, not assets. (Abstract.)
* **No rotation study found.**

## Against, and failure modes

* Decompositions are not unique and drift; rotation turnover.

## Fit with volatility-ai

Sector rotation is X3's job here; no evidence that tensor loadings
improve it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chen, R., Yang, D., Zhang, C.-H. (2022). *JASA* 117(537), 94–116.
  <https://arxiv.org/abs/1905.07530>. Abstract.
