# Information-Driven Volume Clock Imbalance Momentum

**Ledger ID RK253** · rank 253 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market microstructure / Volume timing |
| Potential effectiveness rank | 253 (1 = strongest) |
| AI implementability rank | 340 (1 = easiest) |
| Retail advantage rank | 6,476 (1 = strongest) |
| Fit with this project | 🧪 information-driven bars (C-ML5) · ⏳ a momentum rule on them |
| Implemented in volatility-ai | **Partial.** Volume and tick-imbalance bars (`ml.info_bars.volume_bars`, `tick_imbalance_bars`; ledger C-ML5); no momentum rule. |
| Related ledger entries | C-ML5, RK300, RK247 |

## In one paragraph

Sample prices every fixed amount of traded volume (or when order-flow
imbalance exceeds its expectation) instead of every minute, so each bar
carries a similar amount of information, then trade the imbalance.
Easley, López de Prado and O'Hara argued high-frequency markets run on a
volume clock; López de Prado shows volume and dollar bars have better
statistical properties than time bars. Evidence for a momentum rule on
such bars is not established.

## Evidence

* **Easley, López de Prado & O'Hara (2012), "The Volume Clock: Insights
  into the High-Frequency Paradigm," *Journal of Portfolio Management*
  39(1).** (Standard reference; not re-checked here.)
* **López de Prado (2018), *Advances in Financial Machine Learning*, ch.
  2:** volume, dollar and imbalance bars; returns sampled this way are
  closer to normal and less serially dependent. (Standard reference; not
  re-opened.)
* No study found of a momentum rule on imbalance bars.

## Against, and failure modes

* Bar arrival varies with activity; the backtest engine must index by
  event, not clock (the CSV's caveat).

## Fit with volatility-ai

Activity bars raise resolution exactly during selloffs, which is where
the grid's lot accumulation happens. The engine runs on minute bars;
minute bars with volume approximate a volume clock. The bars are built;
a rule is not.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* López de Prado, M. (2018). *Advances in Financial Machine Learning*.
  Wiley. Not re-opened.
* Easley, D., López de Prado, M., O'Hara, M. (2012). *Journal of
  Portfolio Management* 39(1). Not re-checked.
* This repository: `research/ml/info_bars.py`, ledger C-ML5.
