# Neural Operator Delay-Differential Stochastic Volatility Calibrator

**Ledger ID RK240** · rank 240 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Neural operators / Stochastic volatility / Options pricing |
| Potential effectiveness rank | 240 (1 = strongest) |
| AI implementability rank | 701 (1 = easiest) |
| Retail advantage rank | 10,286 (1 = strongest) |
| Fit with this project | ⛔ (options pricing) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK289, RK283 |

## In one paragraph

Calibrate multi-factor stochastic volatility models to option prices
with a neural operator that also handles delay terms. Neural-network
calibration of (rough) volatility models is an established research line
that speeds calibration by orders of magnitude; the delay-differential
neural-operator variant is not something I found published, and the
CSV's reference, arXiv 2106.09876, looks like a placeholder ID (like the
CSV's arXiv 1908.01234 on RK97) and could not be identified.

## Evidence

* **Horvath, Muguruza & Tomas (2021), "Deep learning volatility,"
  *Quantitative Finance* 21(1):** neural networks learn the pricing map
  of (rough) volatility models offline and calibrate quickly. (Standard
  reference; not re-checked here.)
* **Li et al. (2021), Fourier neural operators, ICLR:** the operator
  class. (Not re-checked.)
* **No study found** of delay-differential neural operators for
  volatility calibration.

## Against, and failure modes

* GPU-heavy (the CSV's caveat); a pricing tool, not a strategy.

## Fit with volatility-ai

Options are outside this project's instrument rules (long-only stocks
and ETFs). A calibration method is in any case not a trading rule.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Horvath, B., Muguruza, A., Tomas, M. (2021). "Deep learning
  volatility." *Quantitative Finance* 21(1). Not re-checked.
* The CSV's references: neuraloperator; arXiv 2106.09876 (not
  identified).
