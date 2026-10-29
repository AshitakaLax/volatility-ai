# Wasserstein Distributionally Robust Neural Stochastic Control Hedging

**Ledger ID RK283** · rank 283 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Robust statistics / Stochastic control / Derivatives hedging |
| Potential effectiveness rank | 283 (1 = strongest) |
| AI implementability rank | 287 (1 = easiest) |
| Retail advantage rank | 296 (1 = strongest) |
| Fit with this project | ⛔ (derivatives hedging) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK97, RK88, RK240 |

## In one paragraph

Learn an option-hedging policy that minimises the worst-case replication
error over a Wasserstein ball of volatility paths, trained
adversarially. Deep hedging (learning hedges with neural networks under
frictions) is established; I found no study of the Wasserstein-robust
variant, and the CSV's reference, arXiv 2009.08295, is Morrill et al.'s
neural rough differential equations paper, a general time-series method.

## Evidence

* **Buehler, Gonon, Teichmann & Wood (2019), "Deep hedging,"
  *Quantitative Finance* 19(8):** neural-network hedging under
  transaction costs and other frictions. (Standard reference; not
  re-checked here.)
* **Mohajerin Esfahani & Kuhn (2018):** Wasserstein distributionally
  robust optimisation (see RK88).
* **No study found** of Wasserstein-robust deep hedging.

## Against, and failure modes

* Heavy adversarial GPU training (the CSV's caveat).

## Fit with volatility-ai

Options are outside this project's instrument rules (long-only stocks
and ETFs).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Buehler, H., Gonon, L., Teichmann, J., Wood, B. (2019). "Deep
  hedging." *Quantitative Finance* 19(8). Not re-checked.
* The CSV's references: torchsde; arXiv 2009.08295 (neural rough
  differential equations; general method).
