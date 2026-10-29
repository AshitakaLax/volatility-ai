# Graph Attention Network (GAT) Supply Chain Contagion Stock Predictor

**Ledger ID RK385** · rank 385 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Graph neural networks / Attention mechanisms / Quantitative equity |
| Potential effectiveness rank | 385 (1 = strongest) |
| AI implementability rank | 179 (1 = easiest) |
| Retail advantage rank | 274 (1 = strongest) |
| Fit with this project | ⛔ (stock-level long-short; the economic effect is real) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK318, RK204, RK7 |

## In one paragraph

Propagate news through supplier-customer links with a graph attention
network, predicting a firm's return from its customers' and suppliers'
recent moves. The underlying effect is one of the better-documented
anomalies: investors react slowly to news about a firm's economic
partners, and a strategy long firms whose customers rose and short those
whose customers fell earned about 1.55% a month (Cohen and Frazzini). A
graph network is one way to use it; there is no evidence it adds to the
simple rule. The CSV's reference, arXiv 2103.01234, is a black-hole
physics paper ("Hidden Symmetry of Vanishing Love"), unrelated to
trading.

## Evidence

* **Cohen & Frazzini (2008), "Economic Links and Predictable Returns,"
  *Journal of Finance* 63(4), 1977–2011:** customer momentum earns
  abnormal returns of 1.55% a month (monthly alphas above 150 basis
  points), with little exposure to standard factors or the firm's own
  momentum. (Abstract and AQR summary.)
* A FactSet study propagated momentum through its supply-chain database
  for index constituents, 2003–2019. (Summary; results not read.)

## Against, and failure modes

* Supply-chain data is licensed and sparse before the 2000s; the
  long-short form needs a short leg.

## Fit with volatility-ai

TQQQ is an index product; customer momentum acts on single stocks and
needs a short leg. Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cohen, L., Frazzini, A. (2008). "Economic Links and Predictable
  Returns." *Journal of Finance* 63(4), 1977–2011.
  <https://www.aqr.com/insights/research/journal-article/economic-links-and-predictable-returns>.
  Abstract.
* FactSet Insight. "Propagating momentum information through global
  supply chain networks." Summary.
