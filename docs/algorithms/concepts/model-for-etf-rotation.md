# Model for ETF rotation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,435) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Unspecified model |
| Fit with this project | 🧪 worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** Long-only ETF rotation with a defensive asset is documented (Faber; Antonacci) and built here (X3, RK3); what is missing is the measurement. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Optimal Scholarly ETF
Rotation Engine Ver-53") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The title names
no method beyond "model", so this page judges the task itself. Rotation
with an absolute-momentum or moving-average filter is the practitioner
standard, with long published track records of lower drawdowns at
similar returns.

## The CSV's description

Proposed model for ETF rotation: Rank a defined ETF universe using a
specified momentum, trend, or risk signal and rotate exposure on a fixed
schedule, with a defined defensive allocation and trading-cost model.
This is a concept-level interpretation of the title, not a complete
trading specification: the exact model inputs/target, calibration,
entry/exit or rebalance rules, and position sizing are not fully defined
here.

## Evidence

* **Faber (2007), "A Quantitative Approach to Tactical Asset
  Allocation":** a 10-month moving-average filter across asset classes
  gave comparable returns with much lower volatility and drawdown (see
  RK17). (Summaries.)
* **Antonacci (2012, published 2017), "Risk Premia Harvesting Through
  Dual Momentum":** relative strength picks the asset, absolute momentum
  against T-bills decides whether to hold it (see RK3). (Paper summary.)

## Against, and failure modes

* Rotation results depend heavily on the universe and the rebalance day;
  many published variants are fitted on the same few decades.
* Momentum-based rotation lags turning points and whipsaws in sideways
  markets.

## Fit with volatility-ai

Built as X3 (relative-strength rotation), X2 (defensive rotation), RK3
(dual momentum) and C-E2 (Faber TAA), none yet measured. A rotation
sleeve sits beside the TQQQ grid.

## How to test it here

Run X3 and RK3 on a fixed universe (QQQ, SPY, sector ETFs, T-bills) with
monthly rebalances and costs, and compare with buy-and-hold QQQ and with
the grid alone.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Faber, M. T. (2007). "A Quantitative Approach to Tactical Asset
  Allocation." *Journal of Wealth Management*. Summaries; see RK17.
* Antonacci, G. (2017). "Risk Premia Harvesting Through Dual Momentum."
  See RK3.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8435 | Optimal Scholarly ETF Rotation Engine Ver-53 | Quantum computing / Adiabatic evolution / Stock index rebalancing | 13750 | 12781 | No |
| 8440 | Ensemble Scholarly ETF Rotation Engine Ver-73 | Quantum computing / Adiabatic evolution / Stock index rebalancing | 7758 | 5935 | No |
| 8464 | Optimal Scholarly ETF Rotation Engine Ver-153 | Quantum computing / Adiabatic evolution / Stock index rebalancing | 7761 | 7569 | No |
| 8469 | Ensemble Scholarly ETF Rotation Engine Ver-173 | Quantum computing / Adiabatic evolution / Stock index rebalancing | 13752 | 12783 | No |
| 13834 | Generative Scholarly ETF Rotation Engine MK-56 | Koopman operator / Model predictive control / ETF execution | 13167 | 13686 | No |
