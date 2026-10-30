# Benchmark-Tracking Enhanced Indexing

**Ledger ID RK121** · rank 121 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio optimization / index enhancement |
| Potential effectiveness rank | 121 (1 = strongest) |
| AI implementability rank | 148 (1 = easiest) |
| Retail advantage rank | 72 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** It tilts a stock universe against an index; the project has no universe or alpha signals to tilt with. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK7, RK18 |

## In one paragraph

Tilt holdings toward predictive signals while bounding tracking error,
active weights and turnover against a benchmark. Enhanced index funds
typically run under 2% tracking error and aim for modest outperformance;
the evidence for net-of-fee alpha comes mostly from managers.

## Evidence

* **Practitioner evidence (Robeco, J.P. Morgan):** wider tracking-error
  limits go with higher expected returns; outperformance is modest and
  the figures are gross or self-reported.
* **Annals of Operations Research (2023):** capping only tracking error
  leaves total risk unmanaged; adding a total-volatility constraint
  improves the managed portfolio. (Abstract.)

## Against, and failure modes

* Needs a source of alpha; without one it is the index plus costs.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Enhanced indexing with tracking-error and total-volatility
  constraints. *Annals of Operations Research* (2023). Abstract.
* Robeco and J.P. Morgan Asset Management insights on enhanced indexing.
  Vendor research.
