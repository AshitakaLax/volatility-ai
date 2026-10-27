# Volatility-Managed Factor Portfolio

**Ledger ID RK54** · rank 54 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity factor / risk management |
| Potential effectiveness rank | 54 (1 = strongest) |
| AI implementability rank | 61 (1 = easiest) |
| Retail advantage rank | 31 (1 = strongest) |
| Fit with this project | ⛔ as long/short factor scaling · the scaling itself is S4 (🧪) |
| Implemented in volatility-ai | **Partial.** The scaling exists for grid lots (S4); no factor portfolios. |
| Related ledger entries | S4, RK22, RK2 |

## In one paragraph

Scale a factor portfolio (market, value, momentum…) by the inverse of
its recent variance. Moreira and Muir found this raises Sharpe ratios
for most factors because volatility rises without a matching rise in
expected return; for momentum, scaling by its own volatility nearly
doubles the Sharpe ratio and removes most crashes (Barroso & Santa-Clara).
The out-of-sample critique is serious: implemented in real time across
103 strategies, it generally did not beat the unmanaged versions. The
CSV's own reference could not be identified.

## The rule

```
w_t = c / sigma^2_{t-1}           # previous month's realized variance of the factor (Moreira-Muir)
managed return = w_t x factor return_t; c chosen so the managed and unmanaged volatilities match
variants: scale by volatility (not variance); by downside volatility; cap the leverage
```

## Evidence

* **Moreira & Muir (2017), *Journal of Finance* 72(4), 1611–1644:**
  volatility-managed market, value, momentum, profitability, ROE,
  investment, BAB and FX carry portfolios produce large alphas.
  (Abstract.)
* **Barroso & Santa-Clara (2015), *JFE* 116(1), 111–120:** risk-managed
  momentum nearly doubles the Sharpe ratio and practically eliminates
  crashes. (Abstract.)
* **Wang & Yan (2021), *Journal of Banking & Finance* 131:** scaling by
  *downside* volatility beats scaling by total volatility. (Abstract.)

## Against, and failure modes

* **Cederburg, O'Doherty, Wang & Yan (2020), *JFE* 138(1), 95–117:**
  across 103 equity strategies, real-time versions generally earn lower
  certainty equivalents and Sharpe ratios than the unmanaged portfolios;
  the spanning regressions are structurally unstable. (Abstract.)
* Lower exposure after a spike misses the rebound (the CSV's caveat).

## Fit with volatility-ai

Long/short factor portfolios are out. The mechanism is the same as S4
and RK22 on this project's own book; Wang & Yan's downside-volatility
variant is a cheap extension of S3's estimators worth recording.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moreira, A., Muir, T. (2017). "Volatility-Managed Portfolios." *Journal
  of Finance* 72(4), 1611–1644. NBER w22208. Abstract.
* Barroso, P., Santa-Clara, P. (2015). "Momentum Has Its Moments."
  *Journal of Financial Economics* 116(1), 111–120. Abstract.
* Wang, F., Yan, X. (2021). Downside-volatility-managed portfolios.
  *Journal of Banking & Finance* 131, 106198. Abstract.
* Cederburg, S., O'Doherty, M. S., Wang, F., Yan, X. (2020). "On the
  Performance of Volatility-Managed Portfolios." *Journal of Financial
  Economics* 138(1), 95–117. Abstract.
* The CSV's reference
  <https://www.sciencedirect.com/science/article/pii/S0378426622002928>
  (a 2022 *Journal of Banking & Finance* article) could not be identified
  from search.
