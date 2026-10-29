# Black–Litterman Allocation

**Ledger ID RK63** · rank 63 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio construction |
| Potential effectiveness rank | 63 (1 = strongest) |
| AI implementability rank | 43 (1 = easiest) |
| Retail advantage rank | 67 (1 = strongest) |
| Fit with this project | ⏳ (an allocation framework; needs explicit views) |
| Implemented in volatility-ai | **Research code** in `research.catalog.allocation`: `black_litterman`, `black_litterman_weights`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | Q13, RK60 |

## In one paragraph

Start from the expected returns implied by market-cap weights (the
returns that would make the market portfolio optimal), blend in the
investor's own views with stated confidence, and optimise. It was
designed at Goldman Sachs to stop mean-variance optimisers from
producing extreme, unstable weights from noisy return forecasts. It is a
way to express views, not a source of them: without good views it simply
returns the market portfolio.

## The rule

```
prior:      Pi = delta x Sigma x w_mkt                          # implied equilibrium returns
views:      P mu = Q + e,  e ~ N(0, Omega)                       # e.g. "QQQ beats RSP by 2% a year"
posterior:  mu_BL = [(tau Sigma)^-1 + P' Omega^-1 P]^-1 [(tau Sigma)^-1 Pi + P' Omega^-1 Q]
then mean-variance optimise with mu_BL (long-only, budget constraint)
```

## Evidence

* **Black & Litterman (1992), *Financial Analysts Journal* 48(5),
  28–43**, developed at Goldman Sachs from 1990. (Index records.)
* **He & Litterman (1999), "The Intuition Behind Black-Litterman Model
  Portfolios":** the model starts from CAPM equilibrium returns as the
  neutral reference and tilts only toward expressed views. (Summary.)

## Against, and failure modes

* Outputs depend on the prior, the view matrix, tau and Omega (the CSV's
  caveat); confidence numbers are rarely calibrated.
* An allocation framework, not a timing signal.

## Fit with volatility-ai

Long-only weights fit, but the project has no calibrated return views to
feed it; its signals are regimes (on/off), which map more naturally to
the rotation harness than to a Bayesian return blend. Low priority.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Black, F., Litterman, R. (1992). "Global Portfolio Optimization."
  *Financial Analysts Journal* 48(5), 28–43. Index records.
* He, G., Litterman, R. (1999). "The Intuition Behind Black-Litterman
  Model Portfolios." Goldman Sachs Investment Management Research; SSRN
  334304. Summary.
* The CSV's own references: PyPortfolioOpt's Black-Litterman
  documentation, <https://github.com/PyPortfolio/PyPortfolioOpt>.
