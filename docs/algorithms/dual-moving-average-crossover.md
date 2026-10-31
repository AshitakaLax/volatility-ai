# Dual Moving Average Crossover

**Ledger ID RK62** · rank 62 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / momentum |
| Potential effectiveness rank | 62 (1 = strongest) |
| AI implementability rank | 9 (1 = easiest) |
| Retail advantage rank | 27 (1 = strongest) |
| Fit with this project | 🧪 as a long-or-cash regime · ⛔ as a long/short trade |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk62_ma_cross`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=ma_cross`, component `MovingAverageCrossGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code.** quant-trading's "MACD oscillator" is a short/long SMA crossover (`je_suis_tm.macd_crossover`, Q1 as a trade); Faber's 20/200 targets (`tactical_allocation.faber_targets`, C-E2). The wired regimes are EMA-MACD (`--regime macd`) and price-above-SMA (`--regime sma`), not a two-SMA crossover. |
| Related ledger entries | Q1, C-E2, V16, RK17, RK46, RK64 |

## In one paragraph

Long while a short moving average is above a long one (50/200 is the
"golden cross"), flat or short below. It is the oldest systematic trend
rule and, in general form, the same family as time-series momentum
(Levine & Pedersen 2016: moving-average crossovers and TSMOM are
equivalent representations). The early academic support (Brock,
Lakonishok & LeBaron 1992) did not survive a full correction for data
snooping in later decades. On this project's data, direction regimes
gating the grid measured poorly against the volatility regime.

## The rule

```
fast = SMA(close, n_fast); slow = SMA(close, n_slow)      # e.g. 50 / 200, or 20 / 200
risk-on while fast > slow; act at the next session
```

## Evidence

* **Brock, Lakonishok & LeBaron (1992):** 26 simple rules, moving
  averages and range breaks, on about 90 years of daily Dow Jones data,
  all beat holding cash. (As described by Sullivan et al.)
* **Sullivan, Timmermann & White (1999):** re-tested the universe of
  rules with White's Reality Check bootstrap on 100 years of the Dow to
  quantify data snooping. (Abstract. Whether the original rules'
  significance survives the adjustment out of sample is not stated in
  the abstract; read the paper before relying on either result.)
* **Levine & Pedersen (2016):** crossovers, TSMOM and other linear
  filters are equivalent in their general forms. (Abstract.)

## Against, and failure modes

* Lag at turns and whipsaw around the crossing; the CSV's caveat that
  the Zipline example is "instructional rather than a finished edge".
* Window choice is a free parameter set with hindsight.
* **In this repository:** MACD (an EMA crossover) gating the TQQQ grid,
  causal: CAGR/max DD 0.12–0.26 against 1.30–1.40 for NATR
  (ultimate-algorithm.md L1).

## Fit with volatility-ai

As a regime (long or cash) it fits; as a reversing trade it needs a
short side. A two-SMA regime would be a one-function addition to
`trend_regimes.py` alongside `sma_risk_on`.

## How to test it here

Add `dual_sma_risk_on(daily, fast=50, slow=200)` to `TREND_METHODS`,
then run the step-down with and without `--min-hold 5` beside `sma`,
`macd` and `natr`. Expect it to sit with the other direction regimes;
the test is cheap and closes the question.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Brock, W., Lakonishok, J., LeBaron, B. (1992). "Simple Technical
  Trading Rules and the Stochastic Properties of Stock Returns."
  *Journal of Finance* 47(5), 1731–1764. As summarised by Sullivan et al.
* Sullivan, R., Timmermann, A., White, H. (1999). "Data-Snooping,
  Technical Trading Rule Performance, and the Bootstrap." *Journal of
  Finance* 54(5), 1647–1691.
  <https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1647-1691>.
  Abstract.
* Levine, A., Pedersen, L. H. (2016). "Which Trend Is Your Friend?"
  *Financial Analysts Journal* 72(3), 51–66. Abstract.
* The CSV's own references: <https://github.com/quantopian/zipline>,
  <https://github.com/polakowo/vectorbt>.
