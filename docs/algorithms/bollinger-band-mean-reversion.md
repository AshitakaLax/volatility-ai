# Bollinger Band Mean Reversion

**Ledger ID RK161** · rank 161 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion |
| Potential effectiveness rank | 161 (1 = strongest) |
| AI implementability rank | 29 (1 = easiest) |
| Retail advantage rank | 89 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** Researched as a grid buy gate (X4); the plain rule fails after costs, the contrarian one does better. |
| Implemented in volatility-ai | **Partly.** `research.strategies.entry_gates`: `BollingerWGate`; `research.catalog.je_suis_tm`: `bollinger_w_trades`. |
| Related ledger entries | Q9, X4, RK147 |

## In one paragraph

Fade excursions outside volatility bands expecting a return toward the
moving average. Lento, Gradojevic and Wright found the conventional
Bollinger rule did not beat buy and hold after costs, while the
contrarian reading (the mean-reversion form) improved results.

## Evidence

* **Lento, Gradojevic & Wright (2007), *Applied Financial Economics
  Letters* 3(4).** (Abstract.)
* **This repository:** `entry_gates.BollingerWGate` (X4) and
  `je_suis_tm.bollinger_bands` (Q9).

## Against, and failure modes

* Bands widen in crises exactly when fading them is most dangerous.

## Fit with volatility-ai

Researched as a buy gate on the grid (X4); nothing new to test.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lento, C., Gradojevic, N., Wright, C. S. (2007). *Applied Financial
  Economics Letters* 3(4), 263–267. Abstract.
