# Recurrent Neural Hawkes Point Process Toxic Flow Hedging Trigger

**Ledger ID RK280** · rank 280 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Point processes / Recurrent neural networks / Risk management |
| Potential effectiveness rank | 280 (1 = strongest) |
| AI implementability rank | 1,882 (1 = easiest) |
| Retail advantage rank | 10,498 (1 = strongest) |
| Fit with this project | ⛔ (options hedging; event data) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK277, RK259, RK283 |

## In one paragraph

Combine a recurrent network with a multivariate Hawkes process (a
"neural Hawkes" model) to forecast surges of toxic order flow and
trigger defensive option-hedge rebalances. The neural Hawkes model is
established in machine learning; I found no finance study of this use,
and the CSV's reference, arXiv 2104.09876, looks like a placeholder ID
(sequential digits, like the CSV's arXiv 1908.01234 on RK97) and could
not be identified.

## Evidence

* **Mei & Eisner (2017), "The Neural Hawkes Process," NeurIPS:** a
  continuous-time LSTM driving event intensities. (Standard reference;
  not re-checked here.)
* **No finance study found** of neural-Hawkes hedging triggers.

## Against, and failure modes

* Needs low-latency inference (the CSV's caveat); options hedging is out
  of scope here.

## Fit with volatility-ai

Out of scope: options and event-level data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mei, H., Eisner, J. (2017). "The Neural Hawkes Process." NeurIPS. Not
  re-checked.
* The CSV's references: hawkeslib; arXiv 2104.09876 (not identified).
