# Bayesian Structural Time Series (BSTS) Causal Impact Macro Strategy

**Ledger ID RK217** · rank 217 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Bayesian econometrics / Macro event trading |
| Potential effectiveness rank | 217 (1 = strongest) |
| AI implementability rank | 236 (1 = easiest) |
| Retail advantage rank | 186 (1 = strongest) |
| Fit with this project | ⏳ as an event-study tool · not a trading rule |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK211 |

## In one paragraph

CausalImpact (Brodersen et al., Google) builds a counterfactual for a
series from control series with a Bayesian structural time-series model
and measures an event's effect as actual minus counterfactual, with
credible intervals. It was built for marketing analytics. As a trading
strategy it would trade the estimated abnormal move after an event; I
found no study of that use.

## The rule

```text
fit y_t = local level + trend + seasonal + beta' x_t (controls unaffected by the event) on the pre-event window
counterfactual after the event = posterior predictive; effect = y - counterfactual (with intervals)
```

## Evidence

* **Brodersen, Gallusser, Koehler, Remy & Scott (2015), "Inferring
  causal impact using Bayesian structural time-series models," *Annals
  of Applied Statistics* 9(1), 247–274:** the method, applied to an
  advertising campaign. (Abstract.)
* **No trading study found.**

## Against, and failure modes

* The controls must be unaffected by the event (the CSV's caveat); in
  markets almost everything reacts to a macro shock.
* An effect measured after the fact is not a forecast.

## Fit with volatility-ai

Useful here as a research tool rather than a rule: for example, to
measure how a rule change, an index event or a fund launch moved TQQQ's
volatility against controls. Not a trading strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Brodersen, K. H., Gallusser, F., Koehler, J., Remy, N., Scott, S. L.
  (2015). *Annals of Applied Statistics* 9(1), 247–274.
  <https://doi.org/10.1214/14-AOAS788>. Abstract.
* The CSV's references: Google's CausalImpact; PyMC.
