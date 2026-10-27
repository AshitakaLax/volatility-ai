# Bond Duration Momentum

**Ledger ID RK20** · rank 20 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Fixed income / trend |
| Potential effectiveness rank | 20 (1 = strongest) |
| AI implementability rank | 69 (1 = easiest) |
| Retail advantage rank | 84 (1 = strongest) |
| Fit with this project | ⛔ as published (long/short bond futures) · ⏳ long-or-cash on a Treasury ETF, as a rotation leg |
| Implemented in volatility-ai | **No.** TLT as a hedge was rejected (X5: it fell with stocks in 2022). |
| Related ledger entries | X5, X2, RK1 |

## In one paragraph

Go long duration (bond futures, or a long-dated Treasury fund) when
bonds' own trailing return is positive and short or flat when it is
negative, usually volatility-scaled. It is RK1's time-series momentum
applied to the bond leg; bonds are one of the four asset classes in the
trend-following literature. A related cross-sectional form ranks
maturity buckets along one curve. For this project the question is
narrower: whether a trend rule would have kept a Treasury ETF out of the
2022 bond bear market, which is why TLT was rejected as a hedge.

## The rule

```
time-series form: position_t = sign(R_bond[t-12m, t] - R_cash) x target_vol / sigma_t
long-only form:   hold the Treasury ETF while its 12-month return beats T-bills, else T-bills
curve form (Durham): rank Treasury maturity buckets by trailing return; overweight the leaders, duration-neutral
```

## Evidence

* **Time-series momentum in bond futures** is part of Moskowitz, Ooi &
  Pedersen (2012) and of the century-long sample of Hurst, Ooi & Pedersen
  (2017), whose bond markets are 15 of 67. (Abstracts; see RK1.)
* **Durham (NY Fed Staff Report 657; FAJ 2015):** momentum across
  duration buckets on the US Treasury curve, December 1996–July 2013,
  duration-neutral and long-only, earned up to about 120 bp a year
  excess with information ratios up to 0.79; a blended-lookback version
  about 34 bp and 0.46. Durham notes behavioural explanations are lacking
  for Treasuries. (Report abstract.)
* **Yield-curve momentum** research (Sihvonen) attributes it to
  autocorrelation in yield changes rather than in carry. (Abstract.)

## Against, and failure modes

* **Policy turns**: rate trends end abruptly at central-bank pivots.
* **Small edges** in the curve form (tens of basis points) are easily
  consumed by costs at retail scale.
* **For this project, the hedge question dominates**: a bond position
  only helps a TQQQ book if it does not fall at the same time, and 2022
  is the counter-example.

## Fit with volatility-ai

Short duration and futures are out of scope. A long-or-cash Treasury ETF
(IEF or TLT) with a 12-month absolute-momentum gate fits, as a defensive
candidate in X2's rotation, and it would have been out of bonds for most
of 2022 if the signal turned early enough, which is the claim to test.

## How to test it here

Add IEF/TLT to `tools/rotation.py --mode defensive --defensive ...` with
an absolute-momentum condition (the RK1 `tsmom_risk_on` sketch applied to
the defensive candidate) instead of, or alongside, its own NATR regime.
Measure 2022 specifically, since that year is the reason X5 was rejected.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Durham, J. B. "Momentum and the Term Structure of Interest Rates."
  Federal Reserve Bank of New York Staff Report 657;
  *Financial Analysts Journal* 71(5), 57–74 (2015).
  <https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr657.html>.
  Abstract.
* Moskowitz, T., Ooi, Y. H., Pedersen, L. H. (2012); Hurst, B., Ooi,
  Y. H., Pedersen, L. H. (2017). See RK1's references.
* Sihvonen, M. "Yield Curve Momentum." Working paper (AEA 2022 program).
  Abstract.
* The CSV's own reference:
  <https://www.aqr.com/insights/research/journal-article/a-century-of-evidence-on-trend-following-investing>.
