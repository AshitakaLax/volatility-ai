# Fractional Hurst-Driven Adaptive Bandwidth Mean Reversion

**Ledger ID RK297** · rank 297 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Fractional time-series / Mean reversion |
| Potential effectiveness rank | 297 (1 = strongest) |
| AI implementability rank | 156 (1 = easiest) |
| Retail advantage rank | 2,760 (1 = strongest) |
| Fit with this project | 🧪 the Hurst diagnostic (C-MR4) · ⏳ as an adaptive band width |
| Implemented in volatility-ai | **Partial.** A Hurst-exponent estimator exists (`mean_reversion.hurst_exponent`, ledger C-MR4); no wavelet estimator and no adaptive bands. |
| Related ledger entries | C-MR4, RK202, RK75 |

## In one paragraph

Scale Bollinger or Keltner band widths by a rolling Hurst exponent,
estimated with wavelets: narrow bands (trade reversion more eagerly)
when H is below 0.5 (anti-persistent), wide bands when H is above 0.5
(trending). It is intuitive for a mean-reversion book, but rolling Hurst
estimates are noisy, and the evidence for long memory in returns is
weak. I found no study of the rule.

## The rule

```text
H_t = Hurst estimate on a trailing window (wavelet or lagged-difference estimator)
band width_t = k x sigma_t x f(H_t), with f increasing in H (e.g. f = 2H)
```

## Evidence

* **Lo (1991):** little evidence of long memory in stock returns once
  short-range dependence is accounted for. (Standard reference.)
* **No study found** of Hurst-adaptive bands.

## Against, and failure modes

* Rolling Hurst estimates on short windows are dominated by estimation
  noise.

## Fit with volatility-ai

The grid's step is a fixed band, so this maps onto a step that widens
when TQQQ is persistent and narrows when it is anti-persistent. The
estimator exists; the C-MR4 diagnostics should first show that rolling H
varies meaningfully on TQQQ before any lever is built.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lo, A. W. (1991). *Econometrica* 59(5). Not re-checked.
* This repository: `research/strategies/mean_reversion.py`
  (`hurst_exponent`), ledger C-MR4.
