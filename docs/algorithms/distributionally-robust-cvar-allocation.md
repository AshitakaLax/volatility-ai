# Distributionally Robust CVaR Allocation

**Ledger ID RK88** · rank 88 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio optimization / tail risk |
| Potential effectiveness rank | 88 (1 = strongest) |
| AI implementability rank | 211 (1 = easiest) |
| Retail advantage rank | 59 (1 = strongest) |
| Fit with this project | ⏳ (an allocator; long-only weights) |
| Implemented in volatility-ai | **Research code** in `research.catalog.allocation`: `cvar_weights`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK53, RK97 |

## In one paragraph

CVaR optimisation (RK53) trusts the historical scenarios. The
distributionally robust version instead minimises the *worst-case* CVaR
over every distribution within a Wasserstein distance ε of the empirical
one, a hedge against the sample missing the next crisis. Mohajerin
Esfahani and Kuhn showed these problems reduce to tractable convex (often
linear) programmes with finite-sample guarantees. The radius ε is the
whole design: ε = 0 is ordinary CVaR, and large ε drives the book toward
the least risky asset.

## The rule

```
minimise over w:  sup over Q with W(Q, P_hat) <= epsilon of  CVaR_alpha,Q(-w . r)
P_hat = empirical distribution of the scenarios; W = 1-Wasserstein distance
long-only, fully invested; epsilon chosen by cross-validation or a target confidence
```

## Evidence

* **Mohajerin Esfahani & Kuhn (2018), *Mathematical Programming* 171,
  115–166:** Wasserstein-ball ambiguity sets around the empirical
  distribution give finite convex (often linear) reformulations and
  finite-sample guarantees; illustrated on mean-risk portfolio
  optimisation. (Abstract; open-access.)

## Against, and failure modes

* Results depend on scenario coverage and the uncertainty set (the
  CSV's caveat); robust allocations can be very conservative.
* Choosing ε with a decade of data and a handful of crashes is itself
  an estimation problem.

## Fit with volatility-ai

An allocator for a multi-ETF book; same caveat as RK53. Of interest only
after an allocator exists (ledger §11 item 11), and then as a robustness
variant of CVaR, not a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mohajerin Esfahani, P., Kuhn, D. (2018). "Data-Driven Distributionally
  Robust Optimization Using the Wasserstein Metric: Performance
  Guarantees and Tractable Reformulations." *Mathematical Programming*
  171, 115–166. <https://arxiv.org/abs/1505.05116>. Abstract.
* The CSV's own references: <https://github.com/skfolio/skfolio> (which
  offers a distributionally robust CVaR optimiser),
  <https://github.com/dcajasn/Riskfolio-Lib>.
