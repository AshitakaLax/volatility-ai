# Neural Operator Flow-Matching Cross-Sectional Alpha Forecaster

**Ledger ID RK390** · rank 390 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Neural operators / Generative modeling / Equity alpha |
| Potential effectiveness rank | 390 (1 = strongest) |
| AI implementability rank | 246 (1 = easiest) |
| Retail advantage rank | 111 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.generative`: `operator_flow_alpha`, `FlowMatching`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK326, RK228 |

## In one paragraph

Generate the distribution of next-period cross-sectional returns with
flow matching on top of a neural operator, and rank stocks by it. Both
methods are real (Lipman et al. 2022; Li et al. 2021); I found no study
combining them for returns.

## Evidence

* **Lipman et al. (2022), Flow Matching (arXiv 2210.02747)** and **Li et
  al. (2021), FNO (arXiv 2010.08895):** the methods. (Standard
  references.)
* **No alpha study found.**

## Against, and failure modes

* Two heavy methods stacked on a low signal-to-noise target.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lipman, Y., et al. (2022). <https://arxiv.org/abs/2210.02747>.
* Li, Z., et al. (2021). <https://arxiv.org/abs/2010.08895>.
