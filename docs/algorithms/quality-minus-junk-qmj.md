# Quality Minus Junk (QMJ)

**Ledger ID RK11** · rank 11 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity factor / quality |
| Potential effectiveness rank | 11 (1 = strongest) |
| AI implementability rank | 234 (1 = easiest) |
| Retail advantage rank | 301 (1 = strongest) |
| Fit with this project | ⛔ as published (long/short) · ⏳ long-only quality basket or ETF |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK12, RK13, RK58 |

## In one paragraph

Score every stock on profitability, growth, safety and payout, go long
the high-quality ("quality") and short the low-quality ("junk"). Asness,
Frazzini and Pedersen find high-quality stocks trade at only modestly
higher prices yet earn high risk-adjusted returns, in the US and across
24 countries. AQR publishes the factor's daily returns, which makes it
testable as data even though the strategy itself is a long/short stock
book.

## The rule

```
quality_z = mean of z-scores for:
    profitability (gross profits/assets, ROE, ROA, cash flow, margins, low accruals)
    growth        (5-year changes in the profitability measures)
    safety        (low beta, low leverage, low bankruptcy risk, low earnings volatility)
    payout        (net equity and debt issuance, dividends)
long top 30%, short bottom 30%, within size groups; rebalance monthly
```

The component list and the size-group construction are the paper's as I
recall them; the search confirmed profitability, growth and safety, and
payout only through a secondary source.

## Evidence

* **Asness, Frazzini & Pedersen (2019), *Review of Accounting Studies*
  24(1), 34–112:** quality stocks have higher prices, but only modestly;
  QMJ earns significant risk-adjusted returns in the US and in 24
  countries. The working paper adds that the price of quality was low
  during the internet bubble and that a low price of quality predicts
  higher QMJ returns. (Abstract and working-paper abstract.)
* **Asness et al. (2018):** controlling for junk revives a stable size
  premium (RK58).

## Against, and failure modes

* Long/short and multi-signal: definitions differ by region and by
  dataset vintage (the CSV's caveat), so "QMJ" is a family.
* Quality tends to lag in junk-led rebounds and speculative manias (the
  working paper's internet-bubble observation), which are also when
  this project's leveraged book does best; it is a complement, not a
  hedge.

## Fit with volatility-ai

The long/short factor is out of scope. A long-only quality ETF is an
in-scope holding, but in a separate allocation book. A data-only use is
plausible: AQR's daily QMJ returns as an input to a risk regime (junk
rallying = risk-on), the same role VIXY plays for V12.

## How to test it here

Research-only: load AQR's daily QMJ series and test whether a causal
"QMJ trailing return" regime separates good and bad months for the TQQQ
grid, beside NATR. One fixed lookback, decided before looking.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Asness, C., Frazzini, A., Pedersen, L. H. (2019). "Quality Minus
  Junk." *Review of Accounting Studies* 24(1), 34–112.
  <https://doi.org/10.1007/s11142-018-9470-2>. Abstract.
* Asness, C., Frazzini, A., Israel, R., Moskowitz, T., Pedersen, L. H.
  (2018). "Size Matters, if You Control Your Junk." *Journal of Financial
  Economics* 129(3), 479–509. Abstract.
* AQR datasets, "Quality Minus Junk: Factors, Daily" (the CSV's
  reference): <https://www.aqr.com/Insights/Datasets/Quality-Minus-Junk-Factors-Daily>.
