# Microprice / Queue-Imbalance Signal

**Ledger ID RK306** · rank 306 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Market microstructure / alpha |
| Potential effectiveness rank | 306 (1 = strongest) |
| AI implementability rank | 303 (1 = easiest) |
| Retail advantage rank | 9,812 (1 = strongest) |
| Fit with this project | 🧪 research code (C-MS2; L1 quotes only) · ⏳ as a fair-value check at a live trigger |
| Implemented in volatility-ai | **Research code.** `microstructure.micro_price` is the size-weighted mid ((bid × ask size + ask × bid size) / total size) and `depth_imbalance` the queue imbalance (ledger C-MS2). Stoikov's micro-price, an estimated martingale adjustment, is not built. Deferred: needs Level 1 quotes from Fidelity ([engine/roadmap.md](../../engine/roadmap.md) item 3). |
| Related ledger entries | RK322, C-MS2, C-MS1, C-MM3 |

## In one paragraph

The micro-price adjusts the mid-price toward the side with less queued
size, because a thin queue is more likely to be depleted next. Its
simplest form weights each quote by the opposite side's size. Stoikov's
version is the expected mid-price in the near future, estimated from
data as a function of imbalance and spread, and built to be a
martingale; he finds it predicts short-term prices better than either
the mid or the weighted mid. A replication on DAX stocks did not find
that.

## The rule

```text
imbalance I = Q_bid / (Q_bid + Q_ask)                      # L1 queue sizes
weighted mid = I * ask + (1 - I) * bid                        # the repo's micro_price
Stoikov: P_micro = mid + g(I, spread), g estimated so that P_micro is a martingale
```

## Evidence

* **Stoikov (2018), "The micro-price: a high-frequency estimator of
  future prices," *Quantitative Finance* 18(12), 1959–1966:**
  empirically a better short-term predictor than the mid or the weighted
  mid. (Abstract.)
* **Gould & Bonart (2016), "Queue imbalance as a one-tick-ahead price
  predictor in a limit order book" (arXiv 1512.03492):** logistic
  regressions on 10 liquid Nasdaq stocks; queue imbalance improves
  prediction of the next mid-price move considerably for large-tick
  stocks, moderately for small-tick stocks. (Abstract.)
* **A Frankfurt master's thesis replicating Stoikov on DAX 40 stocks**
  found the micro-price no better than the mid or weighted mid for most
  horizons. (Summary.)

## Against, and failure modes

* The horizon is ticks to seconds; on minute bars the signal has already
  been priced.
* Backtests need queue and fill simulation (the CSV's caveat).

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. Live, the loop does see L1 quotes with sizes, so a weighted mid
could be logged at each trigger and compared with the fill afterwards.
TQQQ is a large-tick stock (a one-cent tick on a price in the tens of
dollars), the case where Gould and Bonart found imbalance most
informative. That is a logging exercise, not a trading change.

## What to log

At every live grid trigger, record bid, ask, both sizes and the weighted
mid, and the mid one and five seconds later; after a few hundred
triggers, check whether buys placed when the imbalance leaned to the ask
side filled at worse prices.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Stoikov, S. (2018). "The micro-price: a high-frequency estimator of
  future prices." *Quantitative Finance* 18(12), 1959–1966.
  <https://ideas.repec.org/a/taf/quantf/v18y2018i12p1959-1966.html>.
  Abstract.
* Gould, M. D., Bonart, J. (2016). <https://arxiv.org/abs/1512.03492>.
  Abstract.
* "The Time-Adjusted Micro-Price and the Relevance of Deeper Limit Order
  Book Levels." Master's thesis, Goethe University Frankfurt. Summary.
* This repository: `research/strategies/microstructure.py` (C-MS2).
