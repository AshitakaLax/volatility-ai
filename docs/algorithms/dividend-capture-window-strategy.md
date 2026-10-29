# Dividend Capture Window Strategy

**Ledger ID RK308** · rank 308 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Equity event / income |
| Potential effectiveness rank | 308 (1 = strongest) |
| AI implementability rank | 96 (1 = easiest) |
| Retail advantage rank | 95 (1 = strongest) |
| Fit with this project | ⛔ (TQQQ's dividend is negligible; the anomaly is small and tax-bound) |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `dividend_capture`; tested on synthetic data, not wired into the engine. Dividends are recorded in the warehouse and live history, not traded. |
| Related ledger entries | RK52 |

## In one paragraph

Buy a stock just before its ex-dividend date and sell just after,
collecting the dividend. It works only if the price falls by less than
the dividend. On average it does fall by less (around 90% of the
dividend in older US data), which is usually read as a tax effect:
abnormal volume around ex-days shows short-term traders, largely
tax-exempt or corporate, capturing the gap. For a taxable retail trader,
costs, taxes and holding-period rules on qualified dividends absorb it.

## Evidence

* **Lakonishok & Vermaelen (1986), "Tax-induced trading around
  ex-dividend days," *Journal of Financial Economics* 16(3):** abnormal
  volume around ex-days, evidence of short-term dividend-capture
  traders. (Secondary sources.)
* **Kalay (1982), *Journal of Finance* 37(4):** the ex-day price drop is
  below the dividend, but transaction costs bound the arbitrage.
  (Standard reference; not re-checked here.)
* **Naranjo, Nimalendran & Ryngaert (2000):** ex-day returns of
  high-yield stocks are strongly affected by corporate dividend capture.
  (Secondary source.)

## Against, and failure modes

* Taxes, costs and the qualified-dividend holding period; the ex-day
  drop often matches the dividend in practice.

## Fit with volatility-ai

TQQQ's yield is a fraction of a percent, paid quarterly, so there is
nothing to capture, and the strategy is a single-stock calendar trade.
Not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lakonishok, J., Vermaelen, T. (1986). *Journal of Financial Economics*
  16(3). Secondary sources.
* Kalay, A. (1982). "The Ex-Dividend Day Behavior of Stock Prices."
  *Journal of Finance* 37(4). Not re-checked.
