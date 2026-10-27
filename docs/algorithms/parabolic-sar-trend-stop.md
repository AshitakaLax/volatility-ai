# Parabolic SAR Trend / Stop

**Ledger ID RK70** · rank 70 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / breakout (trailing stop) |
| Potential effectiveness rank | 70 (1 = strongest) |
| AI implementability rank | 83 (1 = easiest) |
| Retail advantage rank | 13 (1 = strongest) |
| Fit with this project | 🔬 as a regime (built, measured, weak) · 🧪 as a profit-only exit · ⛔ as a stop-and-reverse |
| Implemented in volatility-ai | **Yes.** `--regime psar` on `tools/leverage_stepdown.py` and `tools/rotation.py` (`trend_regimes.psar_risk_on`, Q8), and the profit-only exit `grid_lifecycle.psar_profit_exits` (catalog M6). |
| Related ledger entries | Q8, RK38, RK44, RK55, L1 |

## In one paragraph

Wilder's Parabolic Stop-and-Reverse places a trailing level below price
in an uptrend that accelerates toward price as the trend extends (the
acceleration factor rises by 0.02 at each new extreme, capped at 0.20);
when price crosses it, the system reverses. It is one of the most
popular retail indicators (#13 retail advantage), and this project has
built both a regime and an exit from it. As a regime gating the TQQQ
grid it was the second-worst of the six measured.

## The rule

```
in an uptrend: SAR(t+1) = SAR(t) + AF x (EP - SAR(t)); EP = highest high of the trend
AF starts at 0.02, +0.02 at each new EP, max 0.20; SAR may not exceed the prior two lows
when low < SAR: reverse (SAR = EP, AF reset); mirror for a downtrend
regime (this project): risk-on in the rising phase, applied next session
exit (this project): when the latest session flips to falling, sell only lots the no-loss guard permits
```

## Evidence

* **Wilder (1978), *New Concepts in Technical Trading Systems*:**
  origin and parameters. (Secondary sources.)
* **No academic study found** of PSAR specifically; Park & Irwin (2007)
  applies to technical rules generally.
* **In this repository:** as a causal regime gating the TQQQ grid,
  CAGR/max DD 0.06–0.17 against NATR's 1.30–1.40 (ultimate-algorithm.md
  L1). The implementation agrees with TA-Lib's SAR on the trend side on
  more than 95% of sessions (tested; ledger Q8).

## Against, and failure modes

* Reverses too often in ranges (the CSV's caveat), and the acceleration
  makes it exit early in a volatile but intact trend.
* Stop levels are not fills: a gap through the SAR fills lower.

## Fit with volatility-ai

Built twice. The regime lost (L1: trend switches liquidate near lows and
re-enter near highs). The profit-only exit is in scope by construction
(it never sells a lot at a loss) and is the only form worth measuring
further.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*.
  Trend Research. Secondary descriptions.
* Park, C.-H., Irwin, S. H. (2007). *Journal of Economic Surveys* 21(4),
  786–826. Abstract.
* This repository: `research/strategies/trend_regimes.py`,
  `research/strategies/grid_lifecycle.py`, `research/catalog/je_suis_tm.py`,
  `docs/research/ultimate-algorithm.md` (L1).
