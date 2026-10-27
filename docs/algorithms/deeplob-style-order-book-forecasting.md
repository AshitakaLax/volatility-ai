# DeepLOB-Style Order-Book Forecasting

**Ledger ID RK275** · rank 275 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | ML / market microstructure |
| Potential effectiveness rank | 275 (1 = strongest) |
| AI implementability rank | 353 (1 = easiest) |
| Retail advantage rank | 10,329 (1 = strongest) |
| Fit with this project | ⛔ (needs licensed depth history; seconds horizon) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK252, RK276 |

## In one paragraph

Feed order-book snapshots (prices and sizes at several levels) through
convolutional and LSTM layers to predict the next mid-price move.
DeepLOB beat earlier benchmarks on the FI-2010 dataset, held its
accuracy out of sample over a year of London Stock Exchange data, and
transferred to instruments outside its training set. Accuracy is not
profit, as the CSV notes: latency and fees decide whether a
seconds-ahead forecast can be traded.

## Evidence

* **Zhang, Zohren & Roberts (2019), "DeepLOB: Deep Convolutional Neural
  Networks for Limit Order Books," *IEEE Transactions on Signal
  Processing* (arXiv 1808.03668):** beats benchmarks on FI-2010; stable
  out-of-sample accuracy on one year of LSE quotes; transfers to unseen
  instruments. (Abstract.)

## Against, and failure modes

* Large licensed datasets and event-time validation; paper accuracy is
  not deployable net edge (the CSV's caveat).

## Fit with volatility-ai

Out of scope: The warehouse holds minute bars only; no historical
quotes, trades or depth. The horizon is seconds.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Zhang, Z., Zohren, S., Roberts, S. (2019). *IEEE Transactions on
  Signal Processing*. <https://arxiv.org/abs/1808.03668>. Abstract.
