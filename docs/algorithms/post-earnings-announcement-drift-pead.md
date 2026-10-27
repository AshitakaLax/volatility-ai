# Post-Earnings Announcement Drift (PEAD)

**Ledger ID RK45** · rank 45 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Event-driven / earnings |
| Potential effectiveness rank | 45 (1 = strongest) |
| AI implementability rank | 5 (1 = easiest) |
| Retail advantage rank | 18 (1 = strongest) |
| Fit with this project | ⏳ (long-only after positive surprises, small caps) · ⛔ (short side) |
| Implemented in volatility-ai | **No.** The champion's earnings-day lot boost (V6) uses the same calendar of mega-cap earnings reactions, but it sizes lots on volatility, not on the surprise. |
| Related ledger entries | V6, RK40 |

## In one paragraph

After an earnings surprise, prices keep moving in the surprise's
direction for weeks. Buy after large positive standardised surprises and
sell (or short) after negative ones. It was one of the most robust
anomalies for decades (Ball and Brown in 1968, Bernard and Thomas in
1989). A 2022 study argues it has disappeared: since 2006 in large
stocks, and more recently in microcaps, prices absorb the surprise on
the announcement day. Others answer that the result depends on the
research design, or that an overnight version persists.

## The rule

```
SUE = (EPS - expected EPS) / std of past surprises (or the consensus surprise, or the announcement return)
buy the top decile after the announcement, hold ~60 trading days; short the bottom decile in the academic form
```

## Evidence

* **Bernard & Thomas (1989), *Journal of Accounting Research*:** the
  drift is a delayed price response, not a risk premium. (Standard
  reference; not re-checked here.)
* **Martineau (2022), "Rest in Peace Post-Earnings Announcement Drift,"
  *Critical Finance Review* 11(3–4), 613–646:** prices now fully absorb
  surprises on the announcement day; no drift in large stocks since 2006
  and only recently gone in microcaps. (Abstract.)
* **Pushback:** a 2025 working paper (Subrahmanyam) attributes the
  disagreement to research design; another argues an overnight drift
  ("OPEAD") persists. (Summaries.)
* **Fink (2021), *Journal of Behavioral and Experimental Finance* 29,
  100446 (the CSV's reference):** a survey of the drift literature;
  explanations fall into risk, trading frictions and behavioural causes,
  and no single one accounts for the drift. (Abstract.)

## Against, and failure modes

* Evidence is sample-dependent and decaying; executing right after the
  announcement is costly (the CSV's caveat).
* What survives is in small, illiquid names.

## Fit with volatility-ai

A long-only small-cap event basket would pass the instrument rule but is
unrelated to the grid. For the Nasdaq-100 mega-caps that move this book,
the evidence says the drift is gone, so a surprise-conditioned version
of V6 is not worth building.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Martineau, C. (2022). *Critical Finance Review* 11(3–4), 613–646.
  <https://ideas.repec.org/a/now/jnlcfr/104.00000122.html>. Abstract.
* Bernard, V. L., Thomas, J. K. (1989). "Post-Earnings-Announcement
  Drift: Delayed Price Response or Risk Premium?" *Journal of Accounting
  Research* 27. Not re-checked.
* UCLA Anderson Review, "Is Post-Earnings Announcement Drift a Thing
  Again?" Summary.
* Fink, J. (2021). "A review of the post-earnings-announcement drift."
  *Journal of Behavioral and Experimental Finance* 29, 100446.
  <https://doi.org/10.1016/j.jbef.2020.100446> (the CSV's reference).
  Abstract and publisher listing.
