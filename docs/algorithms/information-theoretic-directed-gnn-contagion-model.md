# Information-Theoretic Directed GNN Contagion Model

**Ledger ID RK264** · rank 264 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Information theory / Graph neural networks / Risk management |
| Potential effectiveness rank | 264 (1 = strongest) |
| AI implementability rank | 218 (1 = easiest) |
| Retail advantage rank | 149 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.information`: `TEContagionModel`, `te_matrix`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK221, RK258 |

## In one paragraph

Build a directed graph of transfer-entropy flows between assets and feed
it to a graph neural network that forecasts shock contagion. Transfer
entropy is an established measurement of directional information flow
between markets (RK221); I found no study using it this way.

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

A contagion forecaster for a multi-asset risk book; no evidence and no
use here.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Schreiber, T. (2000). "Measuring Information Transfer." *Physical
  Review Letters* 85(2). Standard reference.
* Dimpfl, T., Peter, F. J. (2013). *Studies in Nonlinear Dynamics &
  Econometrics* 17(1), 85–102. Abstract.
