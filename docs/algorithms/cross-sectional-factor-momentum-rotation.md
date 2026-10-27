# Cross-Sectional Factor Momentum Rotation

**Ledger ID RK65** · rank 65 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor investing / cross-sectional momentum / allocation |
| Potential effectiveness rank | 65 (1 = strongest) |
| AI implementability rank | 31 (1 = easiest) |
| Retail advantage rank | 125 (1 = strongest) |
| Fit with this project | ⏳ long-only over factor ETFs (X3's harness) |
| Implemented in volatility-ai | **No** as a factor rotation; X3's harness would run it given factor ETFs as `--universe`. |
| Related ledger entries | X3, RK7, RK19 |

## In one paragraph

Rank a fixed set of factor portfolios (value, momentum, quality, low
volatility, size…) by trailing return and tilt toward the leaders. The
evidence is genuinely mixed: several studies find factor returns
positively autocorrelated and factor momentum subsuming industry
momentum; another finds the effect concentrated in a quarter of factors
and no better than holding the factors long-only. With investable factor
ETFs it is easy to run; whether it adds anything over equal-weighting
them is the open question, and it is one of the five rows the CSV added
with research references and no backtest.

## The rule

```
universe: K long-only factor ETFs (e.g. MTUM, QUAL, VLUE, USMV, SIZE) or factor-return series (research only)
monthly: rank by trailing 1-, 6- or 12-month return; hold the top k equal-weight (or inverse-vol)
benchmarks: equal-weight all K; the static mix; the market
```

## Evidence

* **For (time series):** Ehsani & Linnainmaa (2022): most factors are
  positively autocorrelated, about 6 bp a month after a losing year and
  51 bp after a winning one; factor momentum concentrates in the
  highest-eigenvalue factors and subsumes most forms of stock momentum.
  Gupta & Kelly (2019): across 65 factors, time-series factor momentum
  earns a combined Sharpe ratio of about 0.84. (Abstracts.)
* **For (cross-section):** Arnott, Kalesnik & Linnainmaa (2023): factors
  show cross-sectional momentum that subsumes industry momentum; it is
  distinct from time-series factor momentum. (Abstract.)
* **Against:** Fan, Li, Liao & Liu (2022): weak at the individual-factor
  level; only 22–27% of factors show strong continuation; factor
  momentum strategies do not beat the corresponding long-only strategies.
  (Abstract.)

## Against, and failure modes

* **Academic factors are long/short; ETFs are long-only.** A long-only
  factor ETF is mostly market beta plus a modest tilt, so ranking them
  is largely ranking the market several times; the spread between ETFs
  is much smaller than between academic factors.
* **Choice of factors and lookback** drives results (the CSV's caveat).

## Fit with volatility-ai

Long-only ETFs, fits the constraints, and the X3 harness can run it. It
does not interact with the TQQQ grid; it is a separate allocation book
whose value would be as a parking place for capital outside the grid.

## How to test it here

Ingest five factor ETFs with long enough history and run:

```bash
python -m tools.rotation --mode relative_strength --universe MTUM QUAL VLUE USMV SIZE --rs-days 21
python -m tools.rotation --mode relative_strength --universe MTUM QUAL VLUE USMV SIZE --rs-days 252
```

Compare against HRP over the same universe (`--mode hrp`) as the
"no-momentum" baseline, and deflate the family (C-ML4).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ehsani, S., Linnainmaa, J. T. (2022). "Factor Momentum and the Momentum
  Factor." *Journal of Finance* 77(3), 1877–1919.
  <https://www.nber.org/papers/w25551>. Abstract.
* Gupta, T., Kelly, B. (2019). "Factor Momentum Everywhere." *Journal of
  Portfolio Management* 45(3), 13–36. Abstract and summaries.
* Arnott, R. D., Kalesnik, V., Linnainmaa, J. T. (2023). "Factor
  Momentum." *Review of Financial Studies* 36(8), 3034–3070.
  <https://academic.oup.com/rfs/article-abstract/36/8/3034/6988043>.
  Abstract (the CSV's reference).
* Fan, M., Li, Y., Liao, M., Liu, J. (2022). "A Reexamination of Factor
  Momentum: How Strong Is It?" *Financial Review* 57(3), 585–615.
  <https://onlinelibrary.wiley.com/doi/10.1111/fire.12300>. Abstract (the
  CSV's reference).
* The CSV's third reference (Journal of Banking & Finance 2024, S0378426624002462,
  an international study) was not opened.
