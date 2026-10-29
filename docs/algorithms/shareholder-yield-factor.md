# Shareholder Yield Factor

**Ledger ID RK27** · rank 27 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity factor / capital return |
| Potential effectiveness rank | 27 (1 = strongest) |
| AI implementability rank | 75 (1 = easiest) |
| Retail advantage rank | 58 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket or shareholder-yield ETF |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `shareholder_yield`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK35, RK52 |

## In one paragraph

Rank firms by everything they return to shareholders (dividends plus net
buybacks, and in some versions debt paydown) relative to market value,
and buy the highest. The case rests on one paper's finding: once
buybacks are counted and issuance netted out, payout yield predicts
returns far better than dividend yield, both over time and across
stocks. It is RK52's dividend screen corrected for the fact that US
firms return much of their cash through buybacks, which a dividend
yield does not see.

## The rule

```
net payout yield = (dividends + repurchases - equity issuance) / market cap      # trailing 12 months
shareholder yield (practitioner form) adds net debt paydown / market cap
annual or quarterly: long the top quintile (with liquidity and quality screens)
```

## Evidence

* **Boudoukh, Michaely, Richardson & Roberts (2007), *Journal of
  Finance* 62(2), 877–915:** payout (dividends plus repurchases) and net
  payout (minus issuance) yields give statistically and economically
  significant return predictability where dividend yield does not; they
  carry more cross-sectional information than dividend yield, and the
  high-minus-low payout portfolio is a priced factor. The decline in
  dividends' predictive power is "vastly overstated" once repurchases
  are counted. (Abstract and working paper.)
* The net-issuance half is RK35 (Pontiff & Woodgate 2008).

## Against, and failure modes

* **Measurement:** buybacks must be net of issuance and option dilution;
  announced programmes are not completed repurchases (the CSV's caveat).
* High yield can come from a falling price; quality screens are part of
  every practical version.

## Fit with volatility-ai

Long-only and simple, but a stock-selection book; data on repurchases
and issuance is not in the repository. A shareholder-yield ETF is the
in-scope vehicle, in a separate allocation book.

## What it would take

Point-in-time cash-flow statements (repurchases, issuance, dividends)
for a stock universe; reference entry until then.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Boudoukh, J., Michaely, R., Richardson, M., Roberts, M. R. (2007). "On
  the Importance of Measuring Payout Yield: Implications for Empirical
  Asset Pricing." *Journal of Finance* 62(2), 877–915.
  <https://econpapers.repec.org/RePEc:bla:jfinan:v:62:y:2007:i:2:p:877-915>.
  Abstract.
* Pontiff, J., Woodgate, A. (2008). "Share Issuance and Cross-sectional
  Returns." *Journal of Finance* 63(2), 921–945. Abstract.
