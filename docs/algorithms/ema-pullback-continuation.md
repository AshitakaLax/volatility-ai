# EMA Pullback Continuation

**Ledger ID RK115** · rank 115 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Trend / pullback |
| Potential effectiveness rank | 115 (1 = strongest) |
| AI implementability rank | 1 (1 = easiest) |
| Retail advantage rank | 234 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** The grid already buys pullbacks; a trend-confirmed pullback is at most a gate on it, and no study supports one. |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk115_ema_pullback`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=ema_pullback`, component `EmaPullbackGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.strategies.entry_gates`. |
| Related ledger entries | V5, X1, RK17 |

## In one paragraph

In an established uptrend, buy a pullback toward a short or medium
exponential moving average once price resumes upward. It is a
practitioner rule with no academic test found. Its long side is what the
grid does mechanically: buy declines, sell recoveries.

## Evidence

* **No study found** of EMA pullback entries.
* **This repository:** the grid buys every configured step down; entry
  gates (`entry_gates.py`, X1, N-series) already condition buys on trend
  and band position.

## Against, and failure modes

* "Evidence of price resuming upward" waits for the bounce, so it buys
  higher than the grid's resting order would.

## Fit with volatility-ai

Already covered: the grid's rungs are pullback entries, and a trend gate
is the "in an uptrend" half. A separate EMA-pullback rule adds nothing
new.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* The CSV's references are je-suis-tm/quant-trading and QuantConnect's
  strategy library.
