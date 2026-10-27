# FED OTC Liquidity Sweep & Reverse Repo Arbitrage

**Ledger ID RK92** · rank 92 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Macro / fixed-income relative value |
| Potential effectiveness rank | 92 (1 = strongest) |
| AI implementability rank | 170 (1 = easiest) |
| Retail advantage rank | 227 (1 = strongest) |
| Fit with this project | ⛔ (repo leverage, institutional access) · the cash-yield question it raises is in scope |
| Implemented in volatility-ai | **No** as a trade. SOFR and ON RRP volume (`RRPONTSYD`) are registered FRED inputs (`research/ml/sources.py`), and idle cash accrues a money-market yield in backtests (`research/optimization/money_market_yield.py`). |
| Related ledger entries | RK28 |

## In one paragraph

Trade short Treasury bill yields against the Federal Reserve's
overnight reverse repo (ON RRP) rate and SOFR. The ON RRP rate is meant
to be a floor for money-market rates, yet bills and private repo traded
below it in 2021 as the facility took in about $2 trillion. I found no
published study of this as a trading strategy. The sources describe how
the floor works, not a tested trade. The CSV notes it is
capital-intensive and needs repo leverage. The title's "OTC liquidity
sweep" is not a term I could find in Fed or academic sources.

## The rule

```
(as described in the CSV) spread = T-bill yield - ON RRP rate (or - SOFR)
bills well below the floor: ... (no rule given beyond "trade the dislocation"); positions financed in repo
```

## Evidence

* **Federal Reserve FEDS Note (December 2023), "Money market fund repo
  and the ON RRP facility":** from January 2021 to June 2022 money
  funds' ON RRP investment rose by about $2 trillion while their private
  repo lending fell by almost $500 billion; the facility is designed as
  a floor for repo rates. (Summary.)
* **Market reports (2021):** bills and repo traded below the ON RRP
  offering rate (0.05% after June 2021) as bill supply fell. (Summaries.)
* **No study of a trading strategy found.**

## Against, and failure modes

* Basis-point spreads need leverage; access to the facility is limited
  to eligible counterparties.

## Fit with volatility-ai

Out of scope as a trade. The useful question for this project is where
idle cash should sit (bills, a bill ETF or a money fund) when the
regime exit holds cash. That is a cash-yield choice the backtests
already model with a money-market rate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Board of Governors of the Federal Reserve System, FEDS Notes, "Money
  Market Fund Repo and the ON RRP Facility" (2023-12-15).
  <https://www.federalreserve.gov/econres/notes/feds-notes/money-market-fund-repo-and-the-on-rrp-facility-20231215.html>.
  Summary.
* Federal Reserve Bank of Kansas City, *Economic Bulletin* (December
  2022), on continued ON RRP use. Summary.
* FRED series SOFR and RRPONTSYD (the CSV's reference).
* This repository: `research/ml/sources.py`,
  `research/optimization/money_market_yield.py`.
