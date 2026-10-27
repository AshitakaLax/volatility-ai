# Dual Thrust Breakout

**Ledger ID RK68** · rank 68 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / breakout (intraday) |
| Potential effectiveness rank | 68 (1 = strongest) |
| AI implementability rank | 82 (1 = easiest) |
| Retail advantage rank | 217 (1 = strongest) |
| Fit with this project | ⛔ as a trade (short side, end-of-day flat) · 🧪 its lower band as a buy gate (N1) |
| Implemented in volatility-ai | **Research code** for the trade (`je_suis_tm.dual_thrust_trades`, Q7); the lower band is wired as the N1 breakdown gate on `hf_entry_gated`. |
| Related ledger entries | Q7, N1, RK69, RK77 |

## In one paragraph

Each day, compute a range from the last N days, then go long if price
breaks above the open plus k₁ × range and short if it breaks below the
open minus k₂ × range, reversing on the opposite break and flat at the
close. Attributed to Michael Chalek (1980s), it is a staple of
Chinese futures quant education and of the quant-trading repository
this ledger already covers. Here the trade is out of scope, but the
lower band is a sensible "do not buy into this breakdown" gate and is
built.

## The rule

```
range = max(HH - LC, HC - LL) over the last N days       # HH highest high, LC lowest close, HC highest close, LL lowest low
upper = open + k1 x range; lower = open - k2 x range
long above upper, short below lower; reverse on the opposite cross; flat at the close
N1 gate (this project): block new lots while price is below `lower`; release on reclaim or next session
```

## Evidence

* Attributed to Michael Chalek; dated to the 1980s by one source. No
  primary publication located. (Summaries.)
* QuantConnect's tutorial: works better in trending markets and gives
  false signals in volatile ones. (Summary.)
* **No academic study found.**

## Against, and failure modes

* Parameter-heavy (N, k₁, k₂); intraday reversals and end-of-day
  flattening realise losses.

## Fit with volatility-ai

The trade is ⛔; the N1 gate is built and in the entry-gate probes
(`config/probe_entry_gate_dual_thrust.yaml`). The Ultimate design's
review of the gates: they move CAGR by about ±0.5 points on most funds
(ultimate-algorithm.md L3).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* QuantConnect, "Dual Thrust Trading Algorithm" tutorial; practitioner
  write-ups found by search (attribution to Michael Chalek).
* This repository: ledger Q7, N1; `research/catalog/je_suis_tm.py`;
  `research/strategies/entry_gates.py`; `docs/research/ultimate-algorithm.md` (L3).
