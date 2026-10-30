# RSI Oversold/Overbought Reversion

**Ledger ID RK160** · rank 160 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion |
| Potential effectiveness rank | 160 (1 = strongest) |
| AI implementability rank | 28 (1 = easiest) |
| Retail advantage rank | 61 (1 = strongest) |
| Fit with this project | ✅ in use |
| Useful for volatility-ai | **In use.** RSI already sizes the grid's lots (V3, a registered strategy) and is researched as a gate (Q10). |
| Implemented in volatility-ai | **Yes.** `research.strategies.size_calculators`: `RsiMomentumSizing`; `research.catalog.je_suis_tm`: `rsi_overbought_oversold`. |
| Related ledger entries | V3, Q10, RK146 |

## In one paragraph

Buy when RSI drops below a low threshold and recovers; sell or exit at a
high threshold. On its own the evidence is the technical-analysis
literature's: mixed in stocks and prone to data snooping (Park and
Irwin). Here RSI is not a stand-alone strategy but a sizing input to the
grid.

## Evidence

* **Park & Irwin (2007), *Journal of Economic Surveys* 21(4):**
  technical rules mixed in stocks; most tests suffer from data snooping.
  (Abstract.)
* **This repository:** `RsiMomentumSizing` (V3) is a registered sizing
  strategy; `je_suis_tm.rsi_overbought_oversold` (Q10) is research code.

## Against, and failure modes

* Thresholds (30/70, 10/90) are tuned after the fact; oversold persists
  in trends.

## Fit with volatility-ai

In use as V3's sizing input. A separate RSI reversion strategy would
duplicate it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Park, C.-H., Irwin, S. H. (2007). *Journal of Economic Surveys* 21(4),
  786–826. Abstract.
