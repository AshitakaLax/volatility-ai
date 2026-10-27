# Corporate Buyback Announcement Drift

**Ledger ID RK209** · rank 209 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Event-driven / corporate actions |
| Potential effectiveness rank | 209 (1 = strongest) |
| AI implementability rank | 143 (1 = easiest) |
| Retail advantage rank | 71 (1 = strongest) |
| Fit with this project | ⏳ long-only event basket |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK27, RK35 |

## In one paragraph

Buy after a company announces an open-market repurchase programme. The
classic study found a 12.1% four-year abnormal return after
announcements in 1980–1990, 45.3% for value stocks and nothing for
glamour stocks. Later work disagrees on whether it survives: one study
rejects its disappearance; another finds much smaller returns after 2001
announcements; a third finds the abnormal returns come at later
authorisations and completions, not in between.

## The rule

```text
event: open-market repurchase authorisation (8-K / press release)
long at the next open; screen for value (high book-to-market) and liquidity; hold 1-4 years
```

## Evidence

* **Ikenberry, Lakonishok & Vermaelen (1995), *Journal of Financial
  Economics* 39:** 1980–1990; average four-year buy-and-hold abnormal
  return of 12.1% after announcements; 45.3% for value stocks; no drift
  for glamour stocks. (Abstract.)
* **Peyer & Vermaelen (2009), "The Nature and Persistence of Buyback
  Anomalies":** reject the hypothesis that the anomalies have
  disappeared. (Abstract.)
* **Lee, Park & Pearson (2019):** long-horizon abnormal returns after
  post-2001 announcements are much smaller; many recent buybacks are not
  about undervaluation. (Working paper.)
* **Bargeron, Bonaime & Thomas (2017), *JFQA*:** returns between
  authorisation and completion are indistinguishable from zero; long-run
  returns come from later authorisation announcements and takeover
  attempts. (Abstract.)

## Against, and failure modes

* An authorisation is not a purchase (the CSV's caveat).
* Long-horizon abnormal returns depend on the benchmark model; the
  effect may have decayed.

## Fit with volatility-ai

A long-only stock basket passes the instrument rule but is a separate
book with its own data (EDGAR filings, completion data), unrelated to
the grid. The related capital-return factors are RK27 (shareholder
yield) and RK35 (net issuance).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ikenberry, D., Lakonishok, J., Vermaelen, T. (1995). "Market
  Underreaction to Open Market Share Repurchases." *Journal of Financial
  Economics* 39. Abstract.
* Peyer, U., Vermaelen, T. (2009). "The Nature and Persistence of
  Buyback Anomalies." *Review of Financial Studies* 22(4). Abstract.
* Lee, I., Park, Y. J., Pearson, N. D. (2019). "Repurchases Have
  Changed." Working paper. Abstract.
* Bargeron, L., Bonaime, A., Thomas, S. (2017). "The Timing and Source
  of Long-Run Returns Following Repurchases." *JFQA* 52(2). Abstract.
