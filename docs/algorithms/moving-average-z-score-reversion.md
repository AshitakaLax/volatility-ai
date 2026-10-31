# Moving-Average Z-Score Reversion

**Ledger ID RK147** · rank 147 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion |
| Potential effectiveness rank | 147 (1 = strongest) |
| AI implementability rank | 30 (1 = easiest) |
| Retail advantage rank | 156 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** The grid's band gates already use this signal (Q9 Bollinger, X4). |
| Implemented in volatility-ai | **Yes.** Tradeable as an entry gate on the `hf_signal_gated` strategy: `zscore_gate=oversold` (`research/strategies/signal_gates.py`, `BandReversionGate`). Off by default; unmeasured. Before this change: **Partly.** `research.catalog.je_suis_tm`: `bollinger_bands`. |
| Related ledger entries | Q9, X4, RK161 |

## In one paragraph

Standardise the distance from a rolling mean and fade extreme z-scores.
It is Bollinger-band reversion with the band width written as a z-score;
the evidence is Bollinger's (RK161): the plain rule fails after costs,
the contrarian form does better.

## Evidence

* **Lento, Gradojevic & Wright (2007), *Applied Financial Economics
  Letters* 3(4):** Bollinger rules did not beat buy-and-hold after
  costs; contrarian versions improved. (Abstract.)
* **This repository:** `bollinger_bands` (Q9) and the Bollinger W gate
  (X4).

## Against, and failure modes

* Fading 3x ETF extremes without a regime filter buys falling knives.

## Fit with volatility-ai

Covered: a z-score gate on grid buys is what the Bollinger gates already
test.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lento, C., Gradojevic, N., Wright, C. S. (2007). Investment
  information content in Bollinger Bands? *Applied Financial Economics
  Letters* 3(4), 263–267. Abstract.
