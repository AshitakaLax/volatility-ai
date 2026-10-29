# Recurrent Neural Hawkes Point Process Toxic Flow Hedging Allocator

**Ledger ID RK412** · rank 412 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Point processes / Recurrent neural networks / Derivatives hedging |
| Potential effectiveness rank | 412 (1 = strongest) |
| AI implementability rank | 1,883 (1 = easiest) |
| Retail advantage rank | 10,499 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.point_processes`: `hedge_budget_allocation`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK280, RK411 |

## In one paragraph

Allocate option-hedging capital by neural Hawkes forecasts of toxic
order-flow surges. The neural Hawkes model exists (Mei and Eisner); I
found no hedging study using it, and the CSV's reference, arXiv
2104.09876, is a heat-pump health-monitoring paper, unrelated to
trading.

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
