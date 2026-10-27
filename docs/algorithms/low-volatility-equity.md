# Low-Volatility Equity

**Ledger ID RK18** · rank 18 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 18 (1 = strongest) |
| AI implementability rank | 13 (1 = easiest) |
| Retail advantage rank | 35 (1 = strongest) |
| Fit with this project | 🧪 via low-volatility ETFs in the defensive rotation (X2) |
| Implemented in volatility-ai | **Partial.** USMV (and SPLV) are candidate holdings in X2's defensive rotation (`tools/rotation.py --mode defensive`); there is no low-volatility stock selection. |
| Related ledger entries | X2, RK49, RK60, RK22 |

## In one paragraph

Hold the least volatile (or lowest-beta) stocks. They have historically
earned about as much as the market, sometimes more, with much smaller
drawdowns, which contradicts the textbook link between risk and return.
The most cited explanation is that benchmarked managers cannot exploit
it: buying low-beta stocks raises tracking error without raising the
benchmark-relative return they are paid on. For this project the
relevant form is the minimum-volatility ETF as a defensive place to
park capital, which X2 already does, with a guard learned from March
2020.

## The rule

```
monthly or quarterly: rank by trailing 1–3-year volatility (or beta)
hold the lowest quintile, equal- or inverse-volatility-weighted
ETF forms: USMV (minimum-variance optimisation), SPLV (100 lowest-volatility S&P 500 names)
```

## Evidence

* **Ang, Hodrick, Xing & Zhang (2006), *Journal of Finance* 61(1),
  259–299:** stocks with high idiosyncratic volatility earn very low
  average returns. (As described in a review.)
* **Baker, Bradley & Wurgler (2011), *Financial Analysts Journal* 67(1),
  40–54:** high-beta and high-volatility stocks have long underperformed
  low-beta and low-volatility stocks; 1968–2008, low-volatility and
  low-beta portfolios combined high average returns with small
  drawdowns; benchmark mandates discourage the arbitrage. (Abstract.)
* **Frazzini & Pedersen (2014):** leverage constraints flatten the
  security market line (RK49).

## Against, and failure modes

* **Sector concentration** (utilities, staples) and **interest-rate
  sensitivity**: low-volatility stocks behave partly like bonds.
* **Lags speculative rallies**, the CSV's caveat.
* **Not a crash hedge in every crash:** in March 2020 defensives fell
  with the market, which is why X2 holds a defensive only while its
  *own* NATR regime is calm (ledger X2).

## Fit with volatility-ai

Fits as an ETF holding. X2 already rotates the TQQQ book into the best
calm defensive (default XLP, XLU, USMV, GLD) when the regime is off.
Unmeasured.

## How to test it here

```bash
python -m tools.rotation --mode defensive --defensive USMV SPLV XLP
python -m tools.rotation --mode defensive --defensive USMV SPLV XLP --regime sma
```

Score 2020 and 2022 separately: one was a fast crash where defensives
fell, the other a rate shock that hit bond-like equities.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ang, A., Hodrick, R., Xing, Y., Zhang, X. (2006). "The Cross-Section
  of Volatility and Expected Returns." *Journal of Finance* 61(1),
  259–299. Described in a review; not opened.
* Baker, M., Bradley, B., Wurgler, J. (2011). "Benchmarks as Limits to
  Arbitrage: Understanding the Low-Volatility Anomaly." *Financial
  Analysts Journal* 67(1), 40–54. <https://papers.ssrn.com/abstract=1745108>.
  Abstract.
* Frazzini, A., Pedersen, L. H. (2014). "Betting Against Beta." *Journal
  of Financial Economics* 111(1), 1–25. Abstract.
* The CSV's own references: QuantConnect strategy library;
  <https://github.com/PyPortfolio/PyPortfolioOpt>.
