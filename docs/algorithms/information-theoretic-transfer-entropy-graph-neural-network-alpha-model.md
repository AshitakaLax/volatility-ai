# Information-Theoretic Transfer Entropy Graph Neural Network Alpha Model

**Ledger ID RK386** · rank 386 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Information theory / Graph neural networks / Alpha generation |
| Potential effectiveness rank | 386 (1 = strongest) |
| AI implementability rank | 335 (1 = easiest) |
| Retail advantage rank | 7,559 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK221, RK264, RK394 |

## In one paragraph

Build a directed stock graph from pairwise transfer entropy and forecast
returns with a graph neural network over it. Transfer entropy measures
information flow between markets (RK221); I found no study feeding it to
a GNN for alpha.

## Evidence

* **Dimpfl & Peter (2013), *Studies in Nonlinear Dynamics &
  Econometrics* 17(1):** transfer entropy as a measure of information
  flow between markets (see RK221).
* **No study found** of transfer-entropy graphs for return prediction.

## Against, and failure modes

* Pairwise transfer entropy across many stocks is noisy and
  sample-hungry; the graph inherits the noise.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Dimpfl, T., Peter, F. J. (2013). *Studies in Nonlinear Dynamics &
  Econometrics* 17(1), 85–102. Abstract.
