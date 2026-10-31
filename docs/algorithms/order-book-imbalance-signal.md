# Order-Book Imbalance Signal

**Ledger ID RK322** · rank 322 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Market microstructure / alpha |
| Potential effectiveness rank | 322 (1 = strongest) |
| AI implementability rank | 330 (1 = easiest) |
| Retail advantage rank | 9,811 (1 = strongest) |
| Fit with this project | 🧪 research code (C-MS2) · ⛔ as a trade (needs depth and tick data) |
| Implemented in volatility-ai | **Research code.** `microstructure.depth_imbalance` and `standardized` (ledger C-MS2); no depth data to feed them. Deferred: needs Level 2 depth from Fidelity ([engine/roadmap.md](../../engine/roadmap.md) item 3). |
| Related ledger entries | RK306, C-MS2, C-MS1 |

## In one paragraph

Order-book imbalance compares resting buy and sell volume near the mid,
often over several levels and standardised against its own recent
history; a positive imbalance predicts an upward mid move over the next
ticks. It is the same family as the micro-price (RK306), with depth
beyond the best quotes. Order-flow imbalance (the change in queues,
C-MS1) explains short-horizon price changes better than a static
snapshot.

## Evidence

* **Gould & Bonart (2016):** best-queue imbalance predicts the next mid
  move on Nasdaq stocks, most for large-tick stocks (see RK306).
* **Cont, Kukanov & Stoikov (2014), "The price impact of order book
  events," *Journal of Financial Econometrics* 12(1):** order-flow
  imbalance explains short-interval price changes linearly (see C-MS1).
  (Standard reference.)

## Against, and failure modes

* Depth is easily spoofed and cancelled; the horizon is ticks.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. Alpaca's equity feed gives the best quotes, not depth, so the
multi-level form cannot even be logged live.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gould, M. D., Bonart, J. (2016). <https://arxiv.org/abs/1512.03492>.
  Abstract.
* Cont, R., Kukanov, A., Stoikov, S. (2014). *Journal of Financial
  Econometrics* 12(1). Standard reference.
* This repository: `research/strategies/microstructure.py` (C-MS2).
