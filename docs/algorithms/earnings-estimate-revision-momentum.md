# Earnings Estimate Revision Momentum

**Ledger ID RK40** · rank 40 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Fundamental / event momentum |
| Potential effectiveness rank | 40 (1 = strongest) |
| AI implementability rank | 74 (1 = easiest) |
| Retail advantage rank | 21 (1 = strongest) |
| Fit with this project | ⏳ (long-only basket, licensed data) |
| Implemented in volatility-ai | **No.** No analyst-estimate data. |
| Related ledger entries | RK45, RK6 |

## In one paragraph

Rank companies by the direction and size of recent revisions to
analysts' earnings estimates and hold the improvers. Analysts update
slowly, especially after bad news, so revisions trend and prices follow.
In Chan, Jegadeesh and Lakonishok's study, earnings surprises measured
by forecast revisions, standardised unexpected earnings or announcement
returns each predicted drifts that price momentum did not explain. The
obstacle for this project is data: point-in-time estimate histories are
licensed.

## The rule

```
revision_i = (consensus FY1 EPS now - 3 months ago) / price (or the up-minus-down count of revisions)
rank monthly; hold the top decile (long-only); skip around announcements if desired
```

## Evidence

* **Chan, Jegadeesh & Lakonishok (1996), "Momentum Strategies," *Journal
  of Finance* 51(5), 1681–1713:** past returns and past earnings
  surprises (including forecast revisions) each predict drifts after
  controlling for the other; analysts respond sluggishly, especially for
  past losers; not explained by market, size or book-to-market.
  (Abstract.)
* The CSV's reference (*Journal of Behavioral and Experimental Finance*,
  article 100446, 2020) could not be identified.

## Against, and failure modes

* Analyst datasets are licensed and revised after the fact; without
  point-in-time snapshots a backtest has lookahead (the CSV's caveat).
* Overlaps with price and earnings momentum.

## Fit with volatility-ai

A long-only stock basket would pass the instrument rule; it needs data
the project does not have and is unrelated to the TQQQ grid.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chan, L. K. C., Jegadeesh, N., Lakonishok, J. (1996). *Journal of
  Finance* 51(5), 1681–1713.
  <https://ideas.repec.org/a/bla/jfinan/v51y1996i5p1681-1713.html>.
  Abstract.
* The CSV's reference: <https://doi.org/10.1016/j.jbef.2020.100446>
  (not identified).
