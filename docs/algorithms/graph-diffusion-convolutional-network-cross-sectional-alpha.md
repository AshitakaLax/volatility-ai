# Graph Diffusion Convolutional Network Cross-Sectional Alpha

**Ledger ID RK394** · rank 394 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Graph neural networks / Graph diffusion / Quantitative equity |
| Potential effectiveness rank | 394 (1 = strongest) |
| AI implementability rank | 183 (1 = easiest) |
| Retail advantage rank | 275 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK318, RK386 |

## In one paragraph

Model how shocks diffuse across a stock network with diffusion
convolutions (random walks on the graph), the architecture built for
traffic forecasting, and predict the cross-section of returns. I found
no stock-return study of it, and the CSV's reference, arXiv 2103.01234,
looks like a placeholder ID (sequential digits, like arXiv 1908.01234 on
RK97) and could not be identified.

## Evidence

* **Li, Yu, Shahabi & Liu (2018), "Diffusion Convolutional Recurrent
  Neural Network," ICLR:** the architecture, for traffic. (Standard
  reference; not re-checked here.)
* **Feng, He, Wang, Luo, Liu & Chua (2019), "Temporal Relational Ranking
  for Stock Prediction," *ACM Transactions on Information Systems* 37(2)
  (arXiv 1809.09441):** ranks stocks with a temporal graph convolution
  over sector and supplier-customer relations; back-tests report average
  return ratios of 98% (NYSE) and 71% (NASDAQ) over the test period.
  Self-reported; no independent replication found. (Abstract.)

## Against, and failure modes

* Relation graphs are usually a present-day snapshot (sectors, Wikidata
  links) applied to the past, a look-ahead the papers rarely address.
* Results are self-reported back-tests on short windows; costs and
  turnover are rarely modelled.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Li, Y., Yu, R., Shahabi, C., Liu, Y. (2018). "Diffusion Convolutional
  Recurrent Neural Network: Data-Driven Traffic Forecasting." ICLR. Not
  re-checked.
* Feng, F., He, X., Wang, X., Luo, C., Liu, Y., Chua, T.-S. (2019). *ACM
  TOIS* 37(2). <https://arxiv.org/abs/1809.09441>. Abstract.
