# Graph Convolutional Network (GCN) Cross-Sectional Stock Ranking

**Ledger ID RK318** · rank 318 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Graph machine learning / Quantitative equity |
| Potential effectiveness rank | 318 (1 = strongest) |
| AI implementability rank | 173 (1 = easiest) |
| Retail advantage rank | 108 (1 = strongest) |
| Fit with this project | ⛔ (stock selection; no stock universe here) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK381, RK385, RK394 |

## In one paragraph

Represent stocks as nodes linked by sector, supplier-customer or
correlation edges, propagate features through graph convolutions, and
rank stocks by predicted return. The best-known paper ranks NYSE and
NASDAQ stocks this way and reports large back-tested return ratios; the
gains are self-reported, and the relation graphs used are typically a
present-day snapshot applied to past data.

## Evidence

* **Feng, He, Wang, Luo, Liu & Chua (2019), "Temporal Relational Ranking
  for Stock Prediction," *ACM Transactions on Information Systems* 37(2)
  (arXiv 1809.09441):** ranks stocks with a temporal graph convolution
  over sector and supplier-customer relations; back-tests report average
  return ratios of 98% (NYSE) and 71% (NASDAQ) over the test period.
  Self-reported; no independent replication found. (Abstract.)
* **Sawhney, Agarwal, Wadhwa & Shah (2021), "Exploring the Scale-Free
  Nature of Stock Markets: Hyperbolic Graph Learning for Algorithmic
  Trading," WWW '21, 11–22:** HyperStockGAT, graph attention in
  hyperbolic space over inter-stock relations, on NASDAQ, NYSE, TSE and
  Chinese exchanges over six years; reports over 12% higher
  profitability and over 4% higher Sharpe ratio than earlier models.
  Self-reported. (Abstract.)

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

* Feng, F., He, X., Wang, X., Luo, C., Liu, Y., Chua, T.-S. (2019). *ACM
  TOIS* 37(2). <https://arxiv.org/abs/1809.09441>. Abstract.
* Sawhney, R., Agarwal, S., Wadhwa, A., Shah, R. R. (2021). WWW '21,
  11–22. doi:10.1145/3442381.3450095. Abstract.
