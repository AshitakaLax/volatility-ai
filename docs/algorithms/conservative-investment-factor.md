# Conservative Investment Factor

**Ledger ID RK15** · rank 15 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity factor / fundamental |
| Potential effectiveness rank | 15 (1 = strongest) |
| AI implementability rank | 73 (1 = easiest) |
| Retail advantage rank | 7 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket (needs fundamentals) · ⛔ long/short |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `asset_growth`, `two_by_three_factor`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK9, RK51 |

## In one paragraph

Favour firms that grow their assets slowly and avoid firms expanding
aggressively. It is the CMA factor of the five-factor model and the
investment factor of the q-factor model, both built on the asset-growth
effect (RK51). The economic story (q-theory) is that firms invest a lot
when their cost of capital is low, so heavy investment signals low
expected returns. The measure is contested: a 2024 study shows both
models' investment factor owes its power to how asset growth is
constructed.

## The rule

```
investment = (total assets_t - total assets_t-1) / total assets_t-1     # annual, lagged to publication
long the lowest-investment 30% (conservative), short the highest 30% (aggressive), within size groups
```

## Evidence

* **Fama & French (2015):** CMA is one of the five factors; with RMW it
  absorbs HML's average return in the US sample. (Abstract.)
* **Hou, Xue & Zhang (2015):** a four-factor q-model with investment and
  profitability summarizes much of the cross-section. (Abstract.)
* **Cooper, Gulen & Schill (2008):** asset growth is a strong predictor
  of abnormal returns, including among large stocks, beyond book-to-market,
  size, prior returns and accruals. (Abstract.)
* **Against: Cooper, Gulen & Ion (2024):** both models' performance
  depends crucially on the asset-growth construction; rebuilt with
  traditional or intangibles-inclusive investment measures they lose
  much of their pricing power, and most of the information sits in
  inventory and receivables growth. (Abstract.)

## Against, and failure modes

* Accounting timing and classification (the CSV's caveat); acquisitions
  inflate asset growth mechanically.
* Low turnover does not mean low drawdown: conservative firms lagged in
  growth-led markets.

## Fit with volatility-ai

A long-only stock basket fits the instrument rule; data and the
multi-stock book are missing. It points away from the high-investment
technology firms that dominate the Nasdaq-100, so as a sleeve it would
diversify this project's TQQQ exposure, but as a separate book.

## What it would take

Point-in-time balance sheets with filing dates for a stock universe;
reference entry until then. RK9's attribution would measure this
project's CMA loading for free.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Fama, E. F., French, K. R. (2015). "A Five-Factor Asset Pricing
  Model." *Journal of Financial Economics* 116(1), 1–22.
  <https://doi.org/10.1016/j.jfineco.2014.10.010> (the CSV's reference).
  Abstract.
* Hou, K., Xue, C., Zhang, L. (2015). "Digesting Anomalies: An
  Investment Approach." *Review of Financial Studies* 28(3), 650–705.
  Abstract.
* Cooper, M. J., Gulen, H., Schill, M. J. (2008). "Asset Growth and the
  Cross-Section of Stock Returns." *Journal of Finance* 63(4),
  1609–1651. Abstract.
* Cooper, M., Gulen, H., Ion, M. (2024). "The Use of Asset Growth in
  Empirical Asset Pricing Models." *Journal of Financial Economics*.
  Abstract.
