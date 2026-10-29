# Deep Koopman Operator Market Dynamics Predictor

**Ledger ID RK376** · rank 376 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Operator theory / Deep learning / Dynamical systems |
| Potential effectiveness rank | 376 (1 = strongest) |
| AI implementability rank | 698 (1 = easiest) |
| Retail advantage rank | 10,484 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.koopman`: `DeepKoopman`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK273, RK206, RK219 |

## In one paragraph

Learn Koopman coordinates in which market dynamics are linear with a
deep autoencoder and forecast in them. The method is established for
physical systems (Lusch, Kutz and Brunton); the Koopman/MPC entries in
the ranked list have no trading evidence (RK201, RK206, RK219); the
nearest finance paper tuned its DMD windows in sample (Mann & Kutz
2016). The CSV's reference, arXiv 2102.12086, could not be identified.

## Evidence

* **Lusch, Kutz & Brunton (2018), "Deep learning for universal linear
  embeddings of nonlinear dynamics," *Nature Communications* 9, 4950:**
  an autoencoder finds Koopman eigenfunctions, with an auxiliary network
  for continuous spectra; tested on the pendulum and fluid flows.
  (Abstract.)
* **A Koopman-autoencoder plus MPC poster** reports +173% on 2021–2024,
  self-reported and unreviewed (see RK206).

## Against, and failure modes

* Returns are not a low-dimensional deterministic system; the linear
  embedding fits noise.

## Fit with volatility-ai

No peer-reviewed evidence for market forecasting. Not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lusch, B., Kutz, J. N., Brunton, S. L. (2018). *Nature Communications*
  9, 4950. doi:10.1038/s41467-018-07210-0.
