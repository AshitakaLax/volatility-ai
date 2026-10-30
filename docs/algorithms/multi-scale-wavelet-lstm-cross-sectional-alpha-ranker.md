# Multi-Scale Wavelet LSTM Cross-Sectional Alpha Ranker

**Ledger ID RK145** · rank 145 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Signal processing / Recurrent neural networks / Equity factor modeling |
| Potential effectiveness rank | 145 (1 = strongest) |
| AI implementability rank | 297 (1 = easiest) |
| Retail advantage rank | 240 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A stock-ranking model; the project has no stock universe. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK272, RK316, RK214 |

## In one paragraph

Split each stock's return history into wavelet sub-bands, run an LSTM
per band and rank stocks on the combined output. I found no study of
this architecture, and the CSV's reference, arXiv 1903.09876, could not
be identified; whole-series wavelet transforms also leak the future
(RK272).

## Evidence

* **No study found** of a wavelet-LSTM stock ranker.
* **Deep stock-ranking models** trail LightGBM in Qlib's benchmark (see
  RK316).

## Against, and failure modes

* Non-causal wavelet bands leak future data; causal ones are lagged
  averages.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* The CSV's reference, arXiv 1903.09876 (not identified).
