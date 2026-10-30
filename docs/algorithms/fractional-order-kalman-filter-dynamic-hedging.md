# Fractional Order Kalman Filter Dynamic Hedging

**Ledger ID RK179** · rank 179 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Fractional calculus / State-space models / Statistical arbitrage |
| Potential effectiveness rank | 179 (1 = strongest) |
| AI implementability rank | 325 (1 = easiest) |
| Retail advantage rank | 10,230 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A pairs hedge-ratio filter (short leg) with no study of the fractional form. |
| Implemented in volatility-ai | **Research code** `research.catalog.econometrics`: `kalman_hedge_ratio`. |
| Related ledger entries | RK34, RK36 |

## In one paragraph

Track a pair's time-varying hedge ratio with a Kalman filter driven by
fractional noise. The standard random-walk Kalman hedge ratio is a
well-known pairs tool (Chan); the fractional variant has no trading
study I could find, and the CSV's reference, arXiv 1908.02345, is a
condensed-matter physics paper on plasmons, unrelated to trading.

## Evidence

* **Chan (2013), *Algorithmic Trading*:** the Kalman random-walk hedge
  ratio for pairs.
* **This repository:** `econometrics.kalman_hedge_ratio` (standard
  form).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Fractional noise in a state-space filter has no closed-form recursion;
  approximations add parameters.

## Fit with volatility-ai

A relative-value trade between assets: it needs a short leg and a
universe of related instruments, and the engine trades one leveraged ETF
long-only. Out of scope as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chan, E. (2013). *Algorithmic Trading*. Wiley. Standard reference.
* The CSV's reference, arXiv 1908.02345 (condensed-matter physics;
  unrelated).
