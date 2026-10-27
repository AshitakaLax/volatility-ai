# 10-Month Moving-Average Risk Filter

**Ledger ID RK17** · rank 17 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / risk filter |
| Potential effectiveness rank | 17 (1 = strongest) |
| AI implementability rank | 27 (1 = easiest) |
| Retail advantage rank | 15 (1 = strongest) |
| Fit with this project | 🧪 fits; built as the SMA regime (daily) and as Faber TAA (monthly) |
| Implemented in volatility-ai | **Yes.** `--regime sma` (200-day) on `tools/leverage_stepdown.py` and `tools/rotation.py` (`trend_regimes.sma_risk_on`); the monthly 10-month rule is research code (`tactical_allocation.faber_targets`, C-E2). |
| Related ledger entries | V16, C-E2, RK1, RK62 |

## In one paragraph

Hold an asset while its month-end price is above its 10-month moving
average; hold cash otherwise. Mebane Faber's version of this rule gave
"equity-like returns with bond-like volatility and drawdown" over a
century of US stocks and from 1973 across asset classes. It is the
simplest trend filter there is and the one most likely to be already
known to anyone reading this ledger. The repository has it, daily and
monthly, and has measured its relatives: they cut drawdowns on TQQQ but
pay for every flip, and this project's direction regimes have measured
poorly next to its volatility regime.

## The rule

```
at each month end t:
    in  if close(t) > mean(month-end closes t-9 .. t)
    out (cash / T-bills) otherwise
act at the next session; Faber equal-weights several asset classes, each filtered independently
```

## Evidence

* **Faber (2007, updated):** a 10-month SMA timing model on US equities
  since 1900 and on other asset classes since 1973 produced comparable
  returns with much lower volatility and drawdown. In the multi-asset
  version, returns of about 4.9% against 3.5% with volatility 6.6%
  against 12.8% are reported in a secondary summary (attribution to the
  2007 paper or the 2018 update unconfirmed). The 2018 update reports a
  Sharpe ratio on US stocks up from 0.45 to 0.80, but also that after
  beating the market in 2008–09 the system underperformed stocks in six
  of the next eight years. (Abstract and summaries.)
* **Gayed & Bilello (2016):** the same idea applied to leverage: hold a
  leveraged index while above its 200-day average (repository: catalog
  R1, `sma_risk_on`).

## Against, and failure modes

* **Whipsaw in sideways markets** and late exits in fast crashes; the
  CSV's own caveat is that it "does not make a leveraged ETF safe".
* **Rebalance-date sensitivity:** the result depends on the day of the
  month it trades (a blog test cited in the summary).
* **In this repository:** plan.md's SMA200 regime flipped about 27 times;
  the trend-line family cut TQQQ's maximum drawdown from 81.68% to
  54.85% at a return cost (28.87% CAGR against 39.15%), but those runs carry the same-session lookahead (V16);
  causal direction regimes on the TQQQ grid measured CAGR/max DD
  0.06–0.63 against 1.30–1.40 for NATR (ultimate-algorithm.md L1).

## Fit with volatility-ai

Fits as a regime (long or cash), and the cash leg earns the engine's
historical cash yield. On the grid every flip to "out" liquidates lots
through the regime exit, so the flip count is the cost to watch (N10's
`--min-hold` exists for this).

## How to test it here

```bash
python -m tools.leverage_stepdown --regime sma              # daily 200-session SMA, lag 1
python -m tools.leverage_stepdown --regime sma --min-hold 5
python -m tools.rotation --mode defensive --regime sma
```

The monthly 10-month form needs a month-end sampling option on the
regime builders (`tactical_allocation.month_end_days` already exists);
compare it with the daily form, because the monthly check is what keeps
Faber's flip count low.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Faber, M. T. (2007). "A Quantitative Approach to Tactical Asset
  Allocation." *Journal of Wealth Management* 9(4); updated 2009 and
  2013/2018. SSRN 962461. Abstract and secondary summaries.
* Gayed, M., Bilello, C. (2016). "Leverage for the Long Run." Charles H.
  Dow Award paper. Summary.
* This repository: `plan.md` (V16), `docs/research/ultimate-algorithm.md`
  (L1), `research/strategies/trend_regimes.py`,
  `research/strategies/tactical_allocation.py`.
