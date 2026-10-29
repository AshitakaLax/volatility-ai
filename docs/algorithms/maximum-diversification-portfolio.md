# Maximum-Diversification Portfolio

**Ledger ID RK66** · rank 66 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio optimization |
| Potential effectiveness rank | 66 (1 = strongest) |
| AI implementability rank | 60 (1 = easiest) |
| Retail advantage rank | 42 (1 = strongest) |
| Fit with this project | ⏳ long-only weights for a multi-ETF book |
| Implemented in volatility-ai | **Research code** in `research.catalog.allocation`: `max_diversification_weights`, `diversification_ratio`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | A5, RK56, RK60, RK61 |

## In one paragraph

Choose weights that maximise the diversification ratio: the
weighted-average volatility of the assets divided by the portfolio's
volatility. The ratio is high when the book holds assets whose risks
cancel. Choueifaty and Coignard introduced it as an alternative to
cap-weighting that, like minimum variance and risk parity, needs no
return forecasts. Its distinctive property is that every asset it holds
has the same correlation with the portfolio.

## The rule

```
DR(w) = (w . sigma) / sqrt(w' Sigma w)
maximise DR(w) subject to sum w = 1, w >= 0
```

## Evidence

* **Choueifaty & Coignard (2008), *Journal of Portfolio Management*
  35(1), 40–51:** introduces the diversification ratio and the
  Most-Diversified Portfolio and compares it with cap-weighted,
  equal-weighted and minimum-variance portfolios. (Abstract.)
* **Choueifaty, Froidure & Reynier (2013), *Journal of Investment
  Strategies*:** properties of the portfolio, including that every held
  asset has the same positive correlation with it, equal to the inverse
  of its diversification ratio. (Abstract and a secondary summary.)

## Against, and failure modes

* Depends on covariance estimates and constraints (the CSV's caveat);
  diversification disappears when correlations spike in a crisis.
* The authors' firm (TOBAM) markets the approach; independent
  out-of-sample evidence is thinner than for minimum variance.

## Fit with volatility-ai

Long-only ETF weights fit; same allocator caveat as RK60/RK61. With
four or five sleeves, maximum diversification, ERC and HRP give similar
weights; testing all three is a robustness check rather than three
strategies.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Choueifaty, Y., Coignard, Y. (2008). "Toward Maximum Diversification."
  *Journal of Portfolio Management* 35(1), 40–51. Abstract.
* Choueifaty, Y., Froidure, T., Reynier, J. (2013). "Properties of the
  Most Diversified Portfolio." *Journal of Investment Strategies*.
  <https://ideas.repec.org/a/rsk/journ6/2255764.html>. Abstract.
* The CSV's own references: <https://github.com/skfolio/skfolio>,
  <https://github.com/dcajasn/Riskfolio-Lib>.
