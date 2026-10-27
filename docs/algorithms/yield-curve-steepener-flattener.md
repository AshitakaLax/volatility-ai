# Yield Curve Steepener / Flattener

**Ledger ID RK86** · rank 86 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Fixed income / macro relative value |
| Potential effectiveness rank | 86 (1 = strongest) |
| AI implementability rank | 235 (1 = easiest) |
| Retail advantage rank | 236 (1 = strongest) |
| Fit with this project | ⛔ (one leg is always short duration) · the curve slope is usable as data |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK28, RK20 |

## In one paragraph

Bet on the slope of the yield curve, not its level: a steepener is long
short-maturity and short long-maturity bonds, DV01-matched, so it gains
if long yields rise relative to short ones; a flattener is the reverse.
It is a discretionary macro trade around central-bank cycles rather
than a systematic strategy with a published edge; there is no academic
study that a rules-based steepener/flattener earns a premium, so the
evidence here is the structure of the curve itself. For this project
the slope is interesting only as data.

## The rule

```
steepener: long N_2y of the 2-year, short N_10y of the 10-year, with N_2y x DV01_2y = N_10y x DV01_10y
signal (systematic variants): slope momentum, slope mean reversion, or a policy-cycle view
```

## Evidence

* **Litterman & Scheinkman (1991):** three factors (level, slope or
  "steepness", curvature) explain well over 95% of Treasury yield
  variation; level dominates. A DV01-neutral steepener isolates the
  slope factor. (Summaries.)
* **Forward rates forecast bond excess returns, in sample:** Fama &
  Bliss (1987, *American Economic Review* 77(4), 680–692) and Cochrane &
  Piazzesi (2005, *American Economic Review* 95(1), 138–160). (Standard
  references, offered by the owner-supplied Gemini answer.)
* **Not out of sample:** Thornton & Valente (2012, *Review of Financial
  Studies* 25(10), 3141–3168) find these forecasts add no consistent
  economic value in a dynamic asset allocation and get worse over time.
  (Abstract.) That contradicts the Gemini answer's claim of robust
  out-of-sample returns.
* These forecast duration (level) returns; no source found that tests a
  DV01-neutral steepener/flattener rule. Curve-momentum work (Durham;
  Sihvonen, see RK20) is the nearest.

## Against, and failure modes

* DV01 matching leaves convexity, carry, futures basis and
  cheapest-to-deliver risk (the CSV's caveat).
* Slope trades are policy bets; they are right on the cycle and wrong on
  the timing as often as not.

## Fit with volatility-ai

Out of scope as a trade. As data, the 10-year minus 2-year slope (FRED)
is a classic recession indicator; inverted curves preceded the 2001,
2008 and 2020 recessions. A causal "curve inverted" flag is a candidate
input to a slow regime, and should be tested like any other: lagged,
with its few episodes counted honestly.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Litterman, R., Scheinkman, J. (1991). "Common Factors Affecting Bond
  Returns." *Journal of Fixed Income* 1(1), 54–61. Summaries.
* Durham, J. B. (2015), FAJ 71(5); Sihvonen, M., "Yield Curve Momentum".
  See RK20.
* Fama, E. F., Bliss, R. R. (1987). "The Information in Long-Maturity
  Forward Rates." *American Economic Review* 77(4), 680–692.
* Cochrane, J. H., Piazzesi, M. (2005). "Bond Risk Premia." *American
  Economic Review* 95(1), 138–160.
* Thornton, D. L., Valente, G. (2012). "Out-of-Sample Predictions of Bond
  Excess Returns and Forward Rates: An Asset Allocation Perspective."
  *Review of Financial Studies* 25(10), 3141–3168.
  <https://ideas.repec.org/a/oup/rfinst/v25y2012i10p3141-3168.html>.
  Abstract.
* The CSV's own references: CME, "Introduction to Treasury Futures";
  QuantConnect strategy library.
