# Bayesian Online Changepoint Regime Gate

**Ledger ID RK104** · rank 104 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Regime detection / Bayesian |
| Potential effectiveness rank | 104 (1 = strongest) |
| AI implementability rank | 212 (1 = easiest) |
| Retail advantage rank | 258 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** A causal changepoint probability is a cheap alternative trigger for the regime exit; no trading study exists, so it must be tested here. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK102, C-R3, V17, N5 |

## In one paragraph

Adams and MacKay's online changepoint detector keeps a posterior over
the time since the last change in the data-generating process; a
strategy pauses or adapts when that posterior says a change is likely.
The algorithm is exact, causal and cheap, which suits a live loop. I
found no study that trades on it; the nearest finance work forecasts
trading volume and order flow.

## Evidence

* **Adams & MacKay (2007, arXiv 0710.3742):** exact online inference of
  the run-length distribution by message passing; examples include the
  Dow Jones index. (Abstract.)
* **Tsaknaki, Lillo & Mazzarisi (2024, arXiv 2407.16376):** an
  autoregressive extension applied to aggregated volume and order flow,
  not to a trading rule. (Abstract.)
* **No trading study found** of a changepoint-gated strategy.

## Against, and failure modes

* The hazard rate and the observation model are free choices that set
  how often it fires; a changepoint in variance is close to what the
  NATR regime already detects.

## Fit with volatility-ai

Long-only and single-instrument: a changepoint probability on TQQQ
returns or daily range could trigger the regime exit (V17/N5) or pause
new lots. Worth one walk-forward comparison with NATR; if it adds
nothing over the volatility threshold, drop it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Adams, R. P., MacKay, D. J. C. (2007). Bayesian Online Changepoint
  Detection. <https://arxiv.org/abs/0710.3742>. Abstract.
* Tsaknaki, I.-Y., Lillo, F., Mazzarisi, P. (2024). Bayesian
  Autoregressive Online Change-Point Detection.
  <https://arxiv.org/abs/2407.16376>. Abstract.
* The CSV's references are QuantConnect's research repository and a
  GitHub stat-arb project.
