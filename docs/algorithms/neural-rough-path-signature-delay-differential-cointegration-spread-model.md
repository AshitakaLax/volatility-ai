# Neural Rough Path Signature Delay-Differential Cointegration Spread Model

**Ledger ID RK140** · rank 140 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Rough path theory / Delay differential equations / Statistical arbitrage |
| Potential effectiveness rank | 140 (1 = strongest) |
| AI implementability rank | 351 (1 = easiest) |
| Retail advantage rank | 6,479 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A short-leg spread model stacking three untested methods. |
| Implemented in volatility-ai | **Research code** `research.catalog.cross_section`: `signature_trading`. |
| Related ledger entries | RK328, RK330 |

## In one paragraph

Embed cointegrated spread paths by their signatures and model them with
neural delay differential equations. Signature trading has a clean
mean-variance theory (RK328); I found no spread-trading study combining
it with delay equations.

## Evidence

* **Futter, Horvath & Wiese (2023):** positions linear in the signature
  have an explicit mean-variance solution (see RK328).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Each layer adds parameters to a spread with a few hundred independent
  observations.

## Fit with volatility-ai

A relative-value trade between assets: it needs a short leg and a
universe of related instruments, and the engine trades one leveraged ETF
long-only. Out of scope as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* See RK328's references.
