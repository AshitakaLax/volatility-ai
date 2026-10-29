# Johansen Cointegration Basket Trading

**Ledger ID RK36** · rank 36 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage |
| Potential effectiveness rank | 36 (1 = strongest) |
| AI implementability rank | 203 (1 = easiest) |
| Retail advantage rank | 266 (1 = strongest) |
| Fit with this project | ⛔ (short legs) |
| Implemented in volatility-ai | **Research code** in `research.catalog.stat_arb`: `johansen_basket`, `band_positions`; tested on synthetic data, not wired into the engine. `pairs.engle_granger` covers the two-asset case. |
| Related ledger entries | Q2, RK37, RK93, C-MR4 |

## In one paragraph

Johansen's test estimates how many cointegrating relationships tie a
set of non-stationary prices together and gives the weights of each;
the resulting basket is stationary and is traded like a pair's spread.
It generalises Engle–Granger pairs to three or more assets, and can find
a relationship among three assets when no pair is cointegrated. The
risk is the number of tests: across a universe, some baskets will look
cointegrated by chance.

## The rule

```
VECM on log prices of k assets; Johansen trace/max-eigenvalue tests -> rank r
basket = first cointegrating vector' x prices; z = (basket - rolling mean) / rolling std
long the basket at z < -2, short at z > 2, exit near 0; re-test on a rolling window
```

## Evidence

* **Johansen (1991), *Econometrica* 59(6), 1551–1580:** the estimator
  and tests. (Standard reference.)
* **Krauss (2017), *Journal of Economic Surveys* 31(2), 513–545 (the
  CSV's reference):** survey of pairs trading in five families
  (distance, cointegration, time series, stochastic control, other).
  (Abstract.)
* **Three crude-oil futures (arXiv 2309.00875):** cointegrated as a
  triple where pairwise cointegration was not detected; profitable under
  conservative costs. (Summary.)

## Against, and failure modes

* Multiple testing across baskets; relationships break after index
  changes, mergers and regime shifts (the CSV's caveat).
* Every basket has short weights.

## Fit with volatility-ai

Out of scope. A Johansen test as one more diagnostic beside C-MR4's ADF
and Hurst tests would be cheap, but nothing here trades a basket.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Johansen, S. (1991). "Estimation and Hypothesis Testing of
  Cointegration Vectors in Gaussian Vector Autoregressive Models."
  *Econometrica* 59(6), 1551–1580.
* Krauss, C. (2017). "Statistical arbitrage pairs trading strategies:
  review and outlook." *Journal of Economic Surveys* 31(2), 513–545.
  <https://doi.org/10.1111/joes.12153>. Abstract.
* "A hidden Markov model for statistical arbitrage," arXiv 2309.00875.
  Summary.
* statsmodels `coint_johansen` (the CSV's reference).
