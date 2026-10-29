# Empirical Mode Decomposition (EMD) Hilbert-Huang Intraday Scalper

**Ledger ID RK315** · rank 315 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Signal Processing / Technical Analysis |
| Potential effectiveness rank | 315 (1 = strongest) |
| AI implementability rank | 71 (1 = easiest) |
| Retail advantage rank | 75 (1 = strongest) |
| Fit with this project | ⛔ (no evidence for a trading rule; end effects leak the future) |
| Implemented in volatility-ai | **Research code** in `research.catalog.technical_ml`: `emd`, `instantaneous_phase`, `emd_scalper_positions`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK75, C-MR4 |

## In one paragraph

Empirical mode decomposition splits a series into intrinsic mode
functions, oscillations of decreasing frequency, by repeatedly
subtracting the mean of its upper and lower envelopes; the Hilbert
transform then gives each mode's instantaneous frequency and amplitude
(the Hilbert-Huang transform). A scalper would trade the phase of the
dominant short mode. EMD is adaptive and suits non-stationary data, but
its envelopes at the end of a window depend on how the series continues,
so causal use needs care. The finance evidence is for denoising and
features, not a rule.

## Evidence

* **Huang et al. (1998), "The empirical mode decomposition and the
  Hilbert spectrum for nonlinear and non-stationary time series
  analysis," *Proc. R. Soc. A* 454 (the CSV's reference):** the method.
  (Standard reference.)
* **EMD denoising for portfolio selection (*Computational Economics*,
  SSE 50 constituents):** out of sample under mean-variance, the
  proposed EMD denoising beat EMD, EEMD and wavelet denoising on
  return-risk ratio. Not a trading rule. (Abstract.)
* **Leung & Zhao (arXiv 2105.10871):** Hilbert-Huang features as inputs
  to tree ensembles, SVMs and LSTMs; trading metrics not read.
  (Abstract.)

## Against, and failure modes

* End effects: the last modes change as new bars arrive, a silent
  look-ahead in back-tests.
* Mode mixing and sifting choices are free parameters.

## Fit with volatility-ai

No study supports an EMD trading rule, and recomputing the decomposition
each bar violates the causal-transform rule unless the end effect is
handled. Not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Huang, N. E., et al. (1998). *Proc. R. Soc. Lond. A* 454, 903–995.
  <https://royalsocietypublishing.org/doi/10.1098/rspa.1998.0193>.
* EMD denoising for portfolio selection. *Computational Economics*.
  doi:10.1007/s10614-022-10345-4. Abstract.
* Leung, T., Zhao, T. <https://arxiv.org/abs/2105.10871>. Abstract.
