# Dividend Yield / Dividend Growth

**Ledger ID RK52** · rank 52 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity (income) |
| Potential effectiveness rank | 52 (1 = strongest) |
| AI implementability rank | 136 (1 = easiest) |
| Retail advantage rank | 52 (1 = strongest) |
| Fit with this project | 🧪 as an instrument (SPYD); ⏳ as a selection rule |
| Implemented in volatility-ai | **Partial.** SPYD (the S&P 500 High Dividend ETF) is one of the funds the grid and ML strategies are researched on (`ml_regime_spyd`, `ml_reachability_spyd`, the SPYD sweeps); there is no dividend selection rule. |
| Related ledger entries | RK27, V13, V14 |

## In one paragraph

Select stocks by dividend yield, dividend growth or payout
sustainability, usually with quality screens. It is the most popular
retail factor and one of the weakest on the evidence: counting buybacks
(payout yield, RK27) predicts returns much better than dividends alone,
and Hartzmark and Solomon show investors treat dividends as free income
separate from price, a bias that makes dividend stocks more expensive
when rates are low or markets have fallen. In this repository the idea
appears only as an instrument: SPYD, a high-dividend index fund, is
traded by the grid.

## The rule

```
yield screen:  highest trailing 12-month dividend yield (e.g. top 80 of the S&P 500: SPYD's index)
growth screen: N consecutive years of dividend increases (aristocrat-style)
sustainability: payout ratio and free-cash-flow cover below thresholds; exclude yield spikes from price falls
```

## Evidence

* **Boudoukh et al. (2007):** dividend yield's predictive power has
  faded; total and net payout yields predict returns where dividends do
  not. (Abstract.)
* **Hartzmark & Solomon (2019), *Journal of Finance* 74(5), 2153–2199:**
  investors and analysts treat dividends as separate from price changes
  ("free dividends"); demand for dividends rises when rates are low or
  markets have done badly, and is followed by lower returns for dividend
  payers. (Abstract and CFA Digest summary.)

## Against, and failure modes

* High yield often signals distress (the CSV's caveat); cuts follow.
* Sector concentration (utilities, energy, REITs, financials) and
  interest-rate sensitivity.
* Taxable investors pay for the dividend form of the same cash.

## Fit with volatility-ai

As a holding, it fits and already exists (the SPYD grid, ML sizing on
SPYD). As a stock-selection rule it needs dividend histories for a
universe. The repository's interest in SPYD is as a lower-volatility
grid instrument, not as a dividend strategy.

## How to test it here

The useful comparison for this project is instrument-level: SPYD's grid
results against RSP's and COWZ's under the same causal fill, to see
whether the dividend screen changes what the grid harvests. That is a
reading of existing sweeps, not a new strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Hartzmark, S. M., Solomon, D. H. (2019). "The Dividend Disconnect."
  *Journal of Finance* 74(5), 2153–2199.
  <https://econpapers.repec.org/RePEc:bla:jfinan:v:74:y:2019:i:5:p:2153-2199>.
  Abstract and summary.
* Boudoukh, J., Michaely, R., Richardson, M., Roberts, M. R. (2007). *Journal
  of Finance* 62(2), 877–915. Abstract.
* This repository: `research/strategies/strategy_registry.py`
  (`ml_regime_spyd`, `ml_reachability_spyd`), `config/sweep_spyd_hf_intrabar_broad.yaml`.
