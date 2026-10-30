# Koopman Operator Non-Linear Cointegration Spread Strategy

**Ledger ID RK159** · rank 159 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Operator theory / Cointegration / Statistical arbitrage |
| Potential effectiveness rank | 159 (1 = strongest) |
| AI implementability rank | 180 (1 = easiest) |
| Retail advantage rank | 288 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A short-leg spread trade; Koopman methods have no out-of-sample trading evidence. |
| Implemented in volatility-ai | **Research code** `research.catalog.koopman`: `koopman_spread_position`. |
| Related ledger entries | RK201, RK203, RK219 |

## In one paragraph

Lift a nonlinear cointegration relation into linear coordinates with a
Koopman dictionary and trade mean reversion there. The nearest finance
evidence is Mann and Kutz's DMD trading, tuned in sample; the CSV's
reference, arXiv 2004.05678, is a mathematical-physics paper ("Stable
polynomials and crystalline measures"), unrelated to trading.

## Evidence

* **Mann & Kutz (2016), *Quantitative Finance* 16(11):** DMD trading
  with windows tuned on in-sample "hot spots" (see RK219).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* A finite dictionary linearises only approximately; spreads are short
  histories.

## Fit with volatility-ai

A relative-value trade between assets: it needs a short leg and a
universe of related instruments, and the engine trades one leveraged ETF
long-only. Out of scope as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mann, J., Kutz, J. N. (2016). *Quantitative Finance* 16(11). Abstract.
* The CSV's reference, arXiv 2004.05678 (mathematical physics;
  unrelated).
