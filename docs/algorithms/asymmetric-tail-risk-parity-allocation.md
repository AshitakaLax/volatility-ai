# Asymmetric Tail-Risk Parity Allocation

**Ledger ID RK95** · rank 95 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio construction / risk parity |
| Potential effectiveness rank | 95 (1 = strongest) |
| AI implementability rank | 8 (1 = easiest) |
| Retail advantage rank | 141 (1 = strongest) |
| Fit with this project | ⏳ (an allocator; long-only weights) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK61, RK53, A5 |

## In one paragraph

Risk parity (RK61) equalises each asset's contribution to portfolio
*variance*, which treats upside and downside moves alike. This variant
equalises contributions to a downside measure instead: semivariance
(only below-mean returns) or expected shortfall. The expected-shortfall
version has a clear source, CVaR risk budgets (Boudt, Carl & Peterson
2013); a recent paper builds a CVaR-based risk parity with machine-learning
forecasts. I found no study specific to the semivariance form, and
nothing that shows either beats ordinary risk parity out of sample.

## The rule

```
ES contribution:  ES_i = w_i x dES(w)/dw_i        # Euler decomposition, sums to portfolio ES
solve for w >= 0, sum w = 1 with ES_i equal (or each ES_i <= a budget)
semivariance form: replace Sigma with the downside semicovariance matrix in the ERC problem
```

## Evidence

* **Boudt, Carl & Peterson (2013), "Asset Allocation with Conditional
  Value-at-Risk Budgets," *Journal of Risk* 15(3), 39–68:** two
  strategies, minimising the largest ES risk contribution and bounding
  each contribution. (As described by a citing paper.)
* **Boudt, Peterson & Croux:** a modified ES estimator for non-normal
  returns and a per-holding decomposition of VaR and ES. (Abstract.)
* **Sheng et al. (2025), *Pacific-Basin Finance Journal* 93:** a
  CVaR-based risk parity model that spreads tail risk evenly, with
  machine-learning forecasts for rebalancing. (Abstract.)
* **Gap:** no source found for semivariance-based risk parity, and no
  out-of-sample comparison with variance-based risk parity. The
  owner-supplied Gemini answer cites Roncalli (2013), *Introduction to
  Risk Parity and Budgeting*, and Qian (2011), "Risk Parity and
  Diversification" (*Journal of Investing*), both about risk budgeting
  in general, and states drawdown results without naming a study.

## Against, and failure modes

* Tail estimates need long samples (the CSV's caveat); with a decade of
  daily data the ES of each asset rests on a few crises.
* Equalising tail contributions in a sample without a bond crash
  overweights bonds, the 2022 problem again.

## Fit with volatility-ai

An allocator; same status as RK53 and RK61. Worth testing only as a
variant once ERC is built.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Boudt, K., Carl, P., Peterson, B. G. (2013). "Asset Allocation with
  Conditional Value-at-Risk Budgets." *Journal of Risk* 15(3), 39–68.
  <https://ideas.repec.org/a/rsk/journ4/2160992.html>. Index record and a
  citing description.
* Sheng et al. (2025). CVaR-based risk parity with machine-learning
  forecasts. *Pacific-Basin Finance Journal* 93.
  <https://ideas.repec.org/a/eee/pacfin/v93y2025ics0927538x25001945.html>.
  Abstract.
* The CSV's own references: Riskfolio-Lib, PyPortfolioOpt (both support
  ES and semivariance risk measures).
