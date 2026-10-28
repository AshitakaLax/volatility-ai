# Information-Theoretic Causality Flow Macro Asset Allocator

**Ledger ID RK257** · rank 257 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Information theory / Causal inference / Macro allocation |
| Potential effectiveness rank | 257 (1 = strongest) |
| AI implementability rank | 240 (1 = easiest) |
| Retail advantage rank | 78 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK221, RK264, RK41 |

## In one paragraph

Weight asset classes by the transfer entropy and directed information
flowing to them from macro indicators. Transfer entropy is an
established measurement of directional information flow between markets
(RK221); I found no study using it this way.

## Evidence

* **Dimpfl & Peter (2013), "Using transfer entropy to measure
  information flows between financial markets," *Studies in Nonlinear
  Dynamics & Econometrics* 17(1), 85–102:** model-free information flow
  between CDS and bond markets and between VIX and iTraxx, before,
  during and after the 2008 crisis. A measurement study, not a trading
  test. (Abstract.)
* **No study found** of this use.

## Against, and failure modes

* Transfer-entropy estimates are noisy and sample-hungry; stacking a
  model on them compounds the noise.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Schreiber, T. (2000). "Measuring Information Transfer." *Physical
  Review Letters* 85(2). Standard reference.
* Dimpfl, T., Peter, F. J. (2013). *Studies in Nonlinear Dynamics &
  Econometrics* 17(1), 85–102. Abstract.
