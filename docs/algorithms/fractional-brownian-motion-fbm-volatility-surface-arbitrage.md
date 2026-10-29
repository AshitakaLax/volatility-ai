# Fractional Brownian Motion (fBm) Volatility Surface Arbitrage

**Ledger ID RK379** · rank 379 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Fractional calculus / Derivatives pricing |
| Potential effectiveness rank | 379 (1 = strongest) |
| AI implementability rank | 238 (1 = easiest) |
| Retail advantage rank | 2,121 (1 = strongest) |
| Fit with this project | ⛔ (options) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK303, RK297 |

## In one paragraph

Price the volatility surface with a fractional (rough) volatility model
and trade where market quotes deviate from it. Rough volatility is well
supported as a description of volatility; deviations from a model
surface are relative value, not arbitrage. The CSV's reference, arXiv
1801.03456, looks like a placeholder ID (sequential digits, like arXiv
1908.01234 on RK97) and could not be identified.

## Evidence

* **Gatheral, Jaisson & Rosenbaum (2018), "Volatility is rough,"
  *Quantitative Finance* 18(6):** log realised volatility behaves like
  fractional Brownian motion with Hurst exponent near 0.1, at all time
  scales tested. (Standard reference.)
* **Bayer, Friz & Gatheral (2016), "Pricing under rough volatility,"
  *Quantitative Finance* 16(6):** the rough Bergomi model fits SPX
  smiles with few parameters. (Standard reference; not re-checked here.)

## Against, and failure modes

* Model-relative mispricing is model risk.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gatheral, J., Jaisson, T., Rosenbaum, M. (2018). "Volatility is
  rough." *Quantitative Finance* 18(6).
  <https://arxiv.org/abs/1410.3394>.
* Bayer, C., Friz, P., Gatheral, J. (2016). *Quantitative Finance*
  16(6). Not re-checked.
