# Quantum Approximate State Preparation Risk Mapping

**Ledger ID RK260** · rank 260 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Quantum computing / Risk management / Monte Carlo |
| Potential effectiveness rank | 260 (1 = strongest) |
| AI implementability rank | 258 (1 = easiest) |
| Retail advantage rank | 284 (1 = strongest) |
| Fit with this project | ⛔ (hardware not ready; risk numbers here are cheap classically) |
| Implemented in volatility-ai | **Research code** in `research.catalog.quantum`: `quantum_var`, `amplitude_estimate`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK53, RK270 |

## In one paragraph

Load a multi-asset return distribution into a quantum state and estimate
VaR and expected shortfall by amplitude estimation, which in principle
converges nearly quadratically faster than Monte Carlo. Demonstrations
so far are toy models; the speed-up needs fault-tolerant hardware and
state preparation that does not eat the gain.

## Evidence

* **Woerner & Egger (2019), "Quantum risk analysis," *npj Quantum
  Information* 5, 15:** amplitude estimation computes VaR and CVaR with
  convergence approaching O(1/M) against Monte Carlo's O(1/√M), a
  near-quadratic speed-up in principle; demonstrated on two toy models.
  (Abstract.)

## Against, and failure modes

* State preparation cost and circuit depth on noisy hardware erase the
  theoretical speed-up for realistic distributions.

## Fit with volatility-ai

This book's risk numbers (drawdown, lot exposure) are computed exactly
and quickly by the backtester. Nothing to gain.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Woerner, S., Egger, D. J. (2019). "Quantum risk analysis." *npj
  Quantum Information* 5, 15. <https://arxiv.org/abs/1806.06893>.
  Abstract.
