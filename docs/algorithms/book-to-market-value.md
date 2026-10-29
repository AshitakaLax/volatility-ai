# Book-to-Market Value

**Ledger ID RK48** · rank 48 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 48 (1 = strongest) |
| AI implementability rank | 109 (1 = easiest) |
| Retail advantage rank | 158 (1 = strongest) |
| Fit with this project | ⏳ long-only (stock basket or value ETF) · ⛔ long/short |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `two_by_three_factor`, `quantile_weights`; tested on synthetic data, not wired into the engine. The repository researches COWZ, a free-cash-flow-yield ETF, but only as a grid instrument. |
| Related ledger entries | RK5, RK9, RK31, RK57 |

## In one paragraph

Buy stocks with high book equity relative to market value (cheap),
avoid or short the expensive. HML, the value factor, is one of the
founding factors of empirical finance. It is also the cautionary tale:
from 2017 to mid-2020 it suffered its worst drawdown on record, about
−55%, and in the five-factor model it becomes redundant once
profitability and investment are included. Later work blames part of
the slump on book value ignoring intangibles (RK31).

## The rule

```
B/M = book equity (last fiscal year, lagged ~6 months) / market equity
June each year: long the top 30% by B/M, short the bottom 30%, within size groups (HML)
long-only form: the top group, or a value index/ETF
```

## Evidence

* **Fama & French (1992, 1993):** size and book-to-market capture much of
  the cross-section of average returns; HML is formalised in 1993.
  (Cited by the sources below; not opened.)
* **Fama & French (2015):** HML is redundant once RMW and CMA are added,
  in the US sample. (Abstract.)
* **Asness, Moskowitz & Pedersen (2013):** value premia in eight markets,
  negatively correlated with momentum (RK5). (Abstract.)

## Against, and failure modes

* **2017–2020:** HML drawdown about −55% through June 2020, the largest
  since 1963 (Arnott et al. 2021); BlackRock calls January 2017–June 2020
  the worst on record since the 1920s. Small value returned −13% against
  small growth's +71% from January 2017 to August 2020 (Alpha Architect).
  (Summaries.)
* Value traps, sector bias (financials, energy), accounting lags (the
  CSV's caveat).

## Fit with volatility-ai

A long-only basket or a value ETF fits the instrument rule, as a
separate book. Value is close to the opposite of the Nasdaq-100's
growth tilt, so as a diversifier of TQQQ exposure it is plausible, and
as a crisis hedge it failed in 2020 (value fell more than growth).

## What it would take

Point-in-time fundamentals for the stock form; the ETF form needs only
bars and the rotation harness. RK9's attribution would give this
project's HML loading (likely strongly negative).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Fama, E. F., French, K. R. (1992). "The Cross-Section of Expected Stock
  Returns." *Journal of Finance* 47(2), 427–465. Not opened.
* Fama, E. F., French, K. R. (2015). "A Five-Factor Asset Pricing
  Model." *Journal of Financial Economics* 116(1), 1–22. Abstract.
* Arnott, R., Harvey, C. R., Kalesnik, V., Linnainmaa, J. (2021).
  "Reports of Value's Death May Be Greatly Exaggerated." *Financial
  Analysts Journal* 77(1). Summary.
* BlackRock, "The Sleeping Giant: Value's Dormant not Dead"; Alpha
  Architect, "Resurrecting the value premium". Summaries.
