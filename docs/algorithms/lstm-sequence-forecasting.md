# LSTM Sequence Forecasting

**Ledger ID RK292** · rank 292 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Machine learning |
| Potential effectiveness rank | 292 (1 = strongest) |
| AI implementability rank | 313 (1 = easiest) |
| Retail advantage rank | 104 (1 = strongest) |
| Fit with this project | ❌ (rejected in the catalog, C-RJ4) |
| Implemented in volatility-ai | **Research code.** `forecasting.LSTMForecaster` (ledger C-RJ4, rejected: no trading evidence for the forecasters it came with). |
| Related ledger entries | C-RJ4, RK290, RK291 |

## In one paragraph

Recurrent networks learn from sequences of prices or features. The best
known positive result: an LSTM on S&P 500 constituents earned 0.46% a
day with a Sharpe ratio of 5.8 before costs (1992–2015), beating a
random forest and a deep net. But the stocks it picked were
high-volatility short-term reversal names, and a simple rules-based
reversal strategy explained part of its returns; profits had largely
gone by the end of the sample.

## Evidence

* **Fischer & Krauss (2018), *European Journal of Operational Research*
  270(2), 654–669:** LSTM on S&P 500 constituents, 1992–2015: 0.46% a
  day and Sharpe 5.8 before costs; beats random forest, deep net and
  logistic regression; the selected stocks share high volatility and a
  short-term reversal profile, and a rules-based reversal strategy
  explains part of the returns. (Abstract.)
* The catalog's rejection (C-RJ4) covers 18 deep sequence forecasters
  with no trading evidence. (Ledger.)

## Against, and failure modes

* Fragile on financial data; evaluate calibration and net trading
  utility, not prediction loss (the CSV's caveat).
* Much of the published edge is a known anomaly (short-term reversal) in
  a costlier form.

## Fit with volatility-ai

Rejected for this project, and the best evidence explains why: what the
network found was a short-term reversal, which the grid already harvests
on one instrument without a model.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Fischer, T., Krauss, C. (2018). "Deep learning with long short-term
  memory networks for financial market predictions." *European Journal
  of Operational Research* 270(2), 654–669.
  <https://doi.org/10.1016/j.ejor.2017.11.054>. Abstract.
* This repository: `research/catalog/forecasting.py` (`LSTMForecaster`),
  ledger C-RJ4.
