# Neural Jump-Diffusion Hawkes Point Process Shock Detector

**Ledger ID RK333** · rank 333 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Point process / Neural SDEs / Market microstructure |
| Potential effectiveness rank | 333 (1 = strongest) |
| AI implementability rank | 1,876 (1 = easiest) |
| Retail advantage rank | 7,558 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK314, RK338 |

## In one paragraph

Learn a latent state that evolves continuously and jumps at events whose
intensity is a neural network (a neural jump SDE), and flag shocks when
the intensity spikes. The model class is established; I found no market
application, and the CSV's reference, arXiv 2104.09876, is a heat-pump
health-monitoring paper, unrelated to trading. Classical mutually
exciting jumps in index returns are documented (RK314).

## Evidence

* **Jia & Benson (2019), "Neural Jump Stochastic Differential
  Equations," NeurIPS 32 (arXiv 1905.10403):** piecewise-continuous
  latent dynamics with neural jump intensities. (Abstract.)
* **Aït-Sahalia, Cacho-Diaz & Laeven (2015), "Modeling financial
  contagion using mutually exciting jump processes," *Journal of
  Financial Economics* 117(3), 585–606:** Hawkes jumps in daily index
  returns; self-excitation in the US and other markets, cross-excitation
  asymmetric (the US moves others more than the reverse); filtered jump
  intensities proposed as a stress gauge and tested out of sample.
  (Abstract.)

## Against, and failure modes

* Needs event-level (tick) data; parameters drift across regimes.
* Neural intensities add capacity to a problem whose limit is data, not
  model form.

## Fit with volatility-ai

The daily jump-intensity gauge of RK314 is the simpler version of this
idea and has evidence; the neural form has none.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Jia, J., Benson, A. R. (2019). NeurIPS 32.
  <https://arxiv.org/abs/1905.10403>. Abstract.
* Aït-Sahalia, Y., Cacho-Diaz, J., Laeven, R. J. A. (2015). *Journal of
  Financial Economics* 117(3), 585–606.
  doi:10.1016/j.jfineco.2015.03.002. Abstract.
