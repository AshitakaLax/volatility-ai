# Generative Diffusion Model Trajectory Generator (TabDDPM)

**Ledger ID RK378** · rank 378 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Generative machine learning / Scenario generation |
| Potential effectiveness rank | 378 (1 = strongest) |
| AI implementability rank | 371 (1 = easiest) |
| Retail advantage rank | 10,225 (1 = strongest) |
| Fit with this project | ⛔ (tabular, not sequential) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK200, RK349 |

## In one paragraph

TabDDPM is a denoising diffusion model for tables with mixed numeric and
categorical columns, built for synthetic data and privacy. It beats GAN
and VAE baselines on tabular benchmarks. Rows are generated
independently, so it does not produce trajectories; a market path
generator needs a sequence model (RK200, RK349).

## Evidence

* **Kotelnikov, Baranchuk, Rubachev & Babenko (2023), "TabDDPM:
  Modelling Tabular Data with Diffusion Models," ICML (arXiv 2209.15421,
  the CSV's reference):** outperforms GAN and VAE baselines across
  tabular benchmarks. (Abstract.)

## Against, and failure modes

* No temporal dependence: the volatility clustering that matters for a
  grid is lost.

## Fit with volatility-ai

Not a trajectory generator. A sequence model (RK200) is the relevant
tool.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Kotelnikov, A., et al. (2023). ICML.
  <https://arxiv.org/abs/2209.15421>. Abstract.
