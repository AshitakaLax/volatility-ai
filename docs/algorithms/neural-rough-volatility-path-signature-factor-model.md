# Neural Rough Volatility Path Signature Factor Model

**Ledger ID RK328** · rank 328 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Rough path theory / Signature methods / Quantitative equity |
| Potential effectiveness rank | 328 (1 = strongest) |
| AI implementability rank | 309 (1 = easiest) |
| Retail advantage rank | 961 (1 = strongest) |
| Fit with this project | ⏳ in principle (path-signature strategies have a framework) · ⛔ as a factor model here |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK342, RK391, RK330 |

## In one paragraph

Describe each asset's recent path, including its volatility's roughness,
by its signature (the iterated integrals of rough path theory) and use
those features as factors. The firmest result in this direction is
signature trading: a strategy linear in the signature of the joint
signal-price path, with an explicit dynamic mean-variance solution that
can include drawdown control, tested on synthetic and market data. The
CSV's reference, arXiv 2102.05678, looks like a placeholder ID
(sequential digits, like arXiv 1908.01234 on RK97) and could not be
identified.

## Evidence

* **Futter, Horvath & Wiese (2023), "Signature Trading: A Path-Dependent
  Extension of the Mean-Variance Framework with Exogenous Signals"
  (arXiv 2308.15135):** strategies as linear functionals of path
  signatures; explicit dynamic mean-variance solution with
  finite-horizon drawdown control; momentum and pairs examples on
  synthetic and market data. (Abstract.)
* **Futter, Muca Cirone & Horvath (2025, "Kernel Learning for
  Mean-Variance Trading Strategies"):** both the kernel and signature
  approaches beat classical Markovian methods when asset dynamics or
  signals are path-dependent. (Abstract.)
* **Gatheral, Jaisson & Rosenbaum (2018), "Volatility is rough,"
  *Quantitative Finance* 18(6):** log realised volatility behaves like
  fractional Brownian motion with Hurst exponent near 0.1, at all time
  scales tested. (Standard reference.)

## Against, and failure modes

* Signature dimension grows with truncation depth; estimates need long
  samples.

## Fit with volatility-ai

As a cross-sectional factor model it needs a stock universe. As a
single-asset tool, a signature of TQQQ's recent path could in principle
inform sizing, but that would be a new ML input with the same
weak-signal problem as V13.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Futter, O., Horvath, B., Wiese, M. (2023).
  <https://arxiv.org/abs/2308.15135>. Abstract.
* Futter, O., Muca Cirone, N., Horvath, B. (2025). "Kernel Learning for
  Mean-Variance Trading Strategies." Abstract.
* Gatheral, J., Jaisson, T., Rosenbaum, M. (2018). "Volatility is
  rough." *Quantitative Finance* 18(6).
  <https://arxiv.org/abs/1410.3394>.
