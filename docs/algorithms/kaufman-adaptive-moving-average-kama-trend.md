# Kaufman Adaptive Moving Average (KAMA) Trend

**Ledger ID RK112** · rank 112 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Adaptive trend |
| Potential effectiveness rank | 112 (1 = strongest) |
| AI implementability rank | 51 (1 = easiest) |
| Retail advantage rank | 92 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** Available as an indicator (V15) and research code; no evidence it beats a plain moving average. |
| Implemented in volatility-ai | **Yes.** Tradeable as an entry gate on the `hf_signal_gated` strategy: `kama_gate=below_falling` (`research/strategies/signal_gates.py`, `KamaTrendGate`). Off by default; unmeasured. Before this change: **Partly.** `research.strategies.indicator_library`. |
| Related ledger entries | V15, RK17 |

## In one paragraph

KAMA speeds up when price moves efficiently in one direction and slows
in noise, using Kaufman's efficiency ratio. It is a sensible smoother,
but the one comparison found says adaptive and simple averages win in
different market conditions, and no reliable published hit rate exists.

## Evidence

* **Ellis & Parbery (2005), "Is smarter better?":** adaptive versus
  simple moving averages on the S&P 500, DJIA and NASDAQ; relative
  effectiveness depended on market conditions. (Secondary summary.)
* **This repository:** the indicator library (V15) exposes TA-Lib's
  KAMA, and `concepts.kama` implements it.

## Against, and failure modes

* The efficiency ratio's window and the fast/slow constants are three
  more parameters.

## Fit with volatility-ai

Usable as a trend input wherever a moving average is used; nothing
suggests it would change a result.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ellis, C. A., Parbery, S. A. (2005). Is smarter better? A comparison
  of adaptive, and simple moving average trading strategies. *Research
  in International Business and Finance* 19(3). Secondary summary.
* Kaufman, P. J. (1995). *Smarter Trading*. Standard reference.
