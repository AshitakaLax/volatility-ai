# Anchored VWAP Reclaim / Rejection

**Ledger ID RK208** · rank 208 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Intraday price/volume |
| Potential effectiveness rank | 208 (1 = strongest) |
| AI implementability rank | 159 (1 = easiest) |
| Retail advantage rank | 248 (1 = strongest) |
| Fit with this project | 🧪 session VWAP as a buy gate (C-MS3) · ⏳ event anchors |
| Implemented in volatility-ai | **Partial.** Session-anchored VWAP is research code and a buy gate (`intraday_gates.session_vwap`, `intraday_gates.VwapGate`, C-MS3); no event anchors. |
| Related ledger entries | C-MS3, C-M1, RK79 |

## In one paragraph

VWAP anchored at an event (an earnings release, a swing low, the open)
is the average price paid by everyone who traded since. Price reclaiming
it says the buyers since the event are back in profit; rejection says
the opposite. The practice comes from discretionary traders. I found no
academic test of anchored VWAP as a signal; the academic VWAP literature
is about execution benchmarks.

## The rule

```text
AVWAP_t = sum(typical price x volume, anchor..t) / sum(volume, anchor..t)
long after a close back above AVWAP (reclaim); exit or avoid on a rejection from below
```

## Evidence

* Practitioner sources only; the method is associated with Brian
  Shannon's teaching. (Not opened.)
* **No academic test found.**
* In this repository the session-anchored form exists as C-MS3's VWAP
  gate and is unmeasured.

## Against, and failure modes

* Anchor choice is easy to fit in hindsight (the CSV's caveat);
  predefine event anchors.
* A volume-weighted moving average carries the same lag and whipsaw as
  any other.

## Fit with volatility-ai

As a gate on grid buys it fits (it never sells), and the session form is
built. An event-anchored variant (anchored at the last FOMC or
earnings-reaction session, which V6 already identifies) would be a small
extension of `VwapGate`. Low priority until the session gate is
measured.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Practitioner descriptions of anchored VWAP found by search. No
  academic source.
* This repository: `research/strategies/intraday_gates.py`
  (`session_vwap`, `VwapGate`), ledger C-MS3.
