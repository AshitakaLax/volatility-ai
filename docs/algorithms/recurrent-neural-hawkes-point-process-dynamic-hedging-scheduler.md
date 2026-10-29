# Recurrent Neural Hawkes Point Process Dynamic Hedging Scheduler

**Ledger ID RK411** · rank 411 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Point processes / Recurrent neural networks / Derivatives hedging |
| Potential effectiveness rank | 411 (1 = strongest) |
| AI implementability rank | 1,881 (1 = easiest) |
| Retail advantage rank | 10,497 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK280, RK352, RK412 |

## In one paragraph

Schedule option delta-hedge rebalances by neural Hawkes forecasts of
order-flow bursts and volatility jumps. The neural Hawkes model exists
(Mei and Eisner); I found no hedging study using it, and the CSV's
reference, arXiv 2104.09876, is a heat-pump health-monitoring paper,
unrelated to trading.

## Evidence

* **Mei & Eisner (2017), "The Neural Hawkes Process," NeurIPS:**
  continuous-time LSTM intensities for event streams, none of them
  markets (see RK304).
* **No hedging study found.**

## Against, and failure modes

* Needs event data; hedging schedules have established cost-aware
  answers (deep hedging, RK352).

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mei, H., Eisner, J. (2017). NeurIPS 30.
  <https://arxiv.org/abs/1612.09328>. Abstract.
