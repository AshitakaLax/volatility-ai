# Queue-Reactive Market Making

**Ledger ID RK276** · rank 276 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market microstructure / market making |
| Potential effectiveness rank | 276 (1 = strongest) |
| AI implementability rank | 306 (1 = easiest) |
| Retail advantage rank | 10,330 (1 = strongest) |
| Fit with this project | 🧪 queue-position fill model (C-MM5) · ⛔ queue-reactive quoting |
| Implemented in volatility-ai | **Partial.** A probabilistic queue-position fill model (`microstructure.QueuePositionEstimator`, ledger C-MM5; needs L2); no quoting rule. Deferred: needs Level 2 depth from Fidelity and a market-making decision ([engine/roadmap.md](../../engine/roadmap.md) item 3). |
| Related ledger entries | C-MM5, RK274, RK275 |

## In one paragraph

Condition where and how much to quote on the current state of the
queues, using the probability that a queue empties or the price moves
against a resting order. The queue-reactive model treats the book as a
Markov queuing system in which order arrival, cancellation and execution
rates depend on queue sizes, and works as a realistic simulator and a
transaction-cost tool.

## Evidence

* **Huang, Lehalle & Rosenbaum (2015), "Simulating and analyzing order
  book data: The queue-reactive model," *Journal of the American
  Statistical Association* 110(509), 107–122:** intensities depend on
  the current book state; usable as a market simulator and for
  transaction-cost analysis of algorithms. (Abstract.)

## Against, and failure modes

* Top-of-book bars cannot simulate queue priority (the CSV's caveat).
  The warehouse holds minute bars only; no historical quotes, trades or
  depth.

## Fit with volatility-ai

Its useful role here is fill realism: a resting grid buy at its trigger
fills only if its queue clears. The backtest fills a touched level
outright (intrabar fill at the level), which is optimistic. The queue
estimator exists but needs L2 data to calibrate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Huang, W., Lehalle, C.-A., Rosenbaum, M. (2015). *JASA* 110(509),
  107–122. <https://arxiv.org/abs/1312.0563>. Abstract.
* This repository: `research/strategies/microstructure.py`
  (`QueuePositionEstimator`), ledger C-MM5.
