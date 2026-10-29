# Hyperbolic Graph Neural Networks for Stock Pricing

**Ledger ID RK381** · rank 381 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Graph machine learning / Hyperbolic geometry / Quantitative equity |
| Potential effectiveness rank | 381 (1 = strongest) |
| AI implementability rank | 333 (1 = easiest) |
| Retail advantage rank | 272 (1 = strongest) |
| Fit with this project | ⛔ (stock selection; no stock universe here) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK318, RK384, RK230 |

## In one paragraph

Embed the stock-relation graph in hyperbolic space, whose geometry suits
the scale-free, hub-dominated networks that stock correlations form, and
run graph attention there for stock selection. The one study found
reports gains over Euclidean graph models on four markets. The CSV's
reference, arXiv 2205.01234, could not be identified.

## Evidence

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

* Sawhney, R., Agarwal, S., Wadhwa, A., Shah, R. R. (2021). WWW '21,
  11–22. doi:10.1145/3442381.3450095. Abstract.
