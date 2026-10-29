# Wasserstein Distributionally Robust Statistical Arbitrage

**Ledger ID RK97** · rank 97 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Robust statistics / statistical arbitrage |
| Potential effectiveness rank | 97 (1 = strongest) |
| AI implementability rank | 278 (1 = easiest) |
| Retail advantage rank | 960 (1 = strongest) |
| Fit with this project | ⛔ (short leg) |
| Implemented in volatility-ai | **Research code** in `research.catalog.stat_arb`: `wdro_threshold`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK37, RK88, RK75 |

## In one paragraph

Choose a cointegrated pair's entry and exit thresholds to do best under
the worst distribution within a Wasserstein ball around the empirical
one, rather than under the fitted model alone. The aim is thresholds
that survive parameter uncertainty and structural breaks. The robust
optimisation machinery is established (RK88), but I found no paper that
applies it to stat-arb thresholds. The CSV's reference, arXiv
1908.01234, is a biomedical-engineering paper on an electromagnetic
bioreactor and cell tensegrity, unrelated to trading.

## The rule

```
ambiguity set B = {Q : W(Q, P_hat) <= eps} around the empirical spread distribution P_hat
choose thresholds (a, m) maximising min over Q in B of E_Q[trade return] (or a risk-adjusted objective)
```

## Evidence

* **Wasserstein DRO:** Mohajerin Esfahani & Kuhn (2018) give tractable
  convex reformulations and finite-sample guarantees (see RK88).
* **Threshold literature (non-robust):** Bertram's OU-optimal bands
  (RK75); asymptotic-mean thresholds for cointegrated portfolios
  (*Computational Economics*, 2023, summary).
* **No paper found** that combines a Wasserstein ambiguity set with
  stat-arb thresholds.

## Against, and failure modes

* The ball's radius decides everything and can make the rule never
  trade; slow to solve over many pairs (the CSV's caveat).

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mohajerin Esfahani, P., Kuhn, D. (2018). "Data-driven distributionally
  robust optimization using the Wasserstein metric." *Mathematical
  Programming* 171, 115–166. (See RK88.)
* Bertram, W. K. (2010). *Physica A* 389(11), 2234–2243. Abstract.
* The CSV's references: cvxpy; arXiv 1908.01234 ("Field models and
  numerical dosimetry inside an extremely-low-frequency electromagnetic
  bioreactor", a biomedical-engineering paper; confirmed by title search
  on 2026-10-29, as the owner-supplied Gemini answer said).
