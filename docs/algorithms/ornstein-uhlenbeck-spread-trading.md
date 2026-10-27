# Ornstein–Uhlenbeck Spread Trading

**Ledger ID RK75** · rank 75 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage |
| Potential effectiveness rank | 75 (1 = strongest) |
| AI implementability rank | 32 (1 = easiest) |
| Retail advantage rank | 117 (1 = strongest) |
| Fit with this project | ⛔ (spreads need a short leg) · 🧪 OU diagnostics and the long-only s-score |
| Implemented in volatility-ai | **Research code.** The OU s-score (`mean_reversion.s_score`, C-MR2) and the OU half-life diagnostic (`mean_reversion.half_life`, C-MR4). |
| Related ledger entries | C-MR2, C-MR4, RK33, RK73 |

## In one paragraph

Model a spread as an Ornstein–Uhlenbeck process (it is pulled back
toward a long-run mean at speed κ, with noise σ). Estimate the
parameters, then set entry and exit bands from them: as a z-score of
the equilibrium spread (Avellaneda–Lee's s-score), or as the band
that maximises expected return or Sharpe per unit time
(Bertram's first-passage solution). The OU model is the engine inside
most pairs strategies; on its own it is a way of setting thresholds,
not a source of return.

## The rule

```
dX = kappa (theta - X) dt + sigma dW; estimate by AR(1) regression on the spread
half-life = ln 2 / kappa; equilibrium std = sigma / sqrt(2 kappa)
enter at theta - a, exit at theta + m (Bertram: choose a, m to maximise expected return or Sharpe per unit time)
```

## Evidence

* **Bertram (2010), "Analytic solutions for optimal statistical
  arbitrage trading," *Physica A* 389(11), 2234–2243:** closed-form mean
  and variance of trade length and return for an OU price; exact optimum
  for expected return; Sharpe-optimal bands. (Abstract.) Applied to crude
  oil and refined products 2003–2010 by Cummins & Bucca (2012).
  (Summary.)
* **Avellaneda & Lee (2010):** OU s-score thresholds on stock residuals
  (RK33). (Abstract.)
* **Elliott, van der Hoek & Malcolm (2005):** OU spread observed in
  noise (RK73). (Summaries.)

## Against, and failure modes

* Thresholds are only as good as κ and σ; both drift, and a spread that
  stops mean-reverting turns the bands into averaging down (the CSV's
  caveat).

## Fit with volatility-ai

Spreads are out of scope. The model has one use here. The grid is
already a mean-reversion bet on a single price, and C-MR4's half-life
and Hurst diagnostics test whether that bet is holding. Bertram-style
bands could inform the grid's step and target, but TQQQ is not an OU
process, so treat that as a question for the diagnostics, not a rule.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bertram, W. K. (2010). "Analytic solutions for optimal statistical
  arbitrage trading." *Physica A* 389(11), 2234–2243.
  <https://econpapers.repec.org/RePEc:eee:phsmap:v:389:y:2010:i:11:p:2234-2243>.
  Abstract.
* Avellaneda, M., Lee, J.-H. (2010). *Quantitative Finance* 10(7),
  761–782. Abstract.
* This repository: `research/strategies/mean_reversion.py`, ledger
  C-MR2, C-MR4.
