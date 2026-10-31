# ADX-Filtered Trend Following

**Ledger ID RK55** · rank 55 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / breakout (trend-strength filter) |
| Potential effectiveness rank | 55 (1 = strongest) |
| AI implementability rank | 20 (1 = easiest) |
| Retail advantage rank | 12 (1 = strongest) |
| Fit with this project | ⏳ as a direction-agnostic harvest gate (plan.md's proposal) · ⛔ as a long/short trend trade |
| Implemented in volatility-ai | **Yes.** Tradeable as an entry gate on the `hf_signal_gated` strategy: `adx_gate=strong_downtrend` (`research/strategies/signal_gates.py`, `AdxTrendGate`). Off by default; unmeasured. Before this change: **Partial.** ADX was screened as an above/below-median regime flag in the V15 TA-Lib sweep; Wilder's +DM, a component of the same system, is the core vote of the registered `ultimate_rsp` strategy. No ADX-gated trade. |
| Related ledger entries | V15, Ultimate-RSP, RK46, RK70 |

## In one paragraph

Trade a trend signal only when the trend is strong, measured by Wilder's
ADX (above 20 or 25). ADX measures trend *strength*, not direction:
it rises in strong moves either way and falls in ranges. That makes it
the most interesting indicator in this family for this project, which
plan.md already noticed: the grid earns in choppy markets and loses in
rallies (where its lots exit early) and in crashes (where they pile up),
and ADX is the standard measure of choppy versus trending.

## The rule

```
+DM, -DM = Wilder's directional movements; TR = true range
+DI = 100 x smoothed(+DM) / ATR; -DI = 100 x smoothed(-DM) / ATR      # Wilder smoothing, n = 14
DX = 100 x |+DI - -DI| / (+DI + -DI); ADX = smoothed(DX)
trend trade: long when +DI > -DI and ADX > 25; flat when ADX < 20
harvest gate (this project): run the grid while ADX < threshold; pause new lots while ADX is high
```

## Evidence

* **Wilder (1978), *New Concepts in Technical Trading Systems*:**
  introduced ADX/DMI, ATR, Parabolic SAR and RSI. (Secondary sources.)
* **No academic study found** of ADX filtering specifically; the general
  technical-analysis record (Park & Irwin 2007) applies.
* **In this repository:** plan.md proposes ADX as a harvest gate;
  Ultimate-RSP's core vote is PLUS_DM (Wilder's +DM) below its trailing
  median, which plan.md's sweep found to be one of two robust ridges on
  RSP and which works as an upside-volatility measure
  (ultimate-rsp.md).

## Against, and failure modes

* ADX is slow (double smoothing) and peaks after the move.
* V15's ADX flags were measured with the same-session lookahead (ledger
  caveat 1); nothing about ADX is established here yet.

## Fit with volatility-ai

As a trend-following trade with a short side, out. As a gate that pauses
new grid lots in strong trends, it fits (a gate never sells), and it is
a direction-agnostic regime, the kind lesson L1 favours.

## How to test it here

Add an ADX gate to `hf_entry_gated` (block new lots while daily ADX(14)
on QQQ exceeds a threshold fixed in advance, say 30), causal, and run it
through the gate chain (`FILL=causal bash tools/experiments/run_entry_gate_chain.sh`).
Report 2020 and 2022 separately: the gate should cut lot accumulation in
crashes, and must not cost much in 2023–2024's trend.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*.
  Trend Research. Secondary descriptions.
* Park, C.-H., Irwin, S. H. (2007). *Journal of Economic Surveys* 21(4),
  786–826. Abstract.
* This repository: `plan.md` (trend-strength table),
  `research/strategies/indicator_library.py`,
  `research/strategies/ultimate_rsp_sizing.py`, `docs/research/ultimate-rsp.md`.
