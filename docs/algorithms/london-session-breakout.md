# London Session Breakout

**Ledger ID RK69** · rank 69 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / breakout (intraday FX) |
| Potential effectiveness rank | 69 (1 = strongest) |
| AI implementability rank | 132 (1 = easiest) |
| Retail advantage rank | 219 (1 = strongest) |
| Fit with this project | ⛔ as a trade (FX, stops, short side) · 🧪 its US-hours analogue as a buy gate (N2) |
| Implemented in volatility-ai | **Research code** for the trade (`je_suis_tm.london_breakout_trades`, Q4); the idea is wired, mapped onto US hours, as the N2 opening-range gate on `hf_entry_gated`. |
| Related ledger entries | Q4, N2, N3, C-M2, RK68 |

## In one paragraph

Mark the high and low of the quiet Asian session; when London opens,
trade a break of that box in either direction, with a stop (often the
box midpoint or a fixed distance) and a target, flat by the session
end. It is an FX practitioner staple. I found no academic test of it;
its closest relative with published evidence is the equity
opening-range breakout (C-M2), whose headline results do not survive a
third-party replication with spread and slippage. The project already
uses the downside half of the idea as a "stop buying" gate.

## The rule

```
box = high and low of the pre-London window (e.g. 00:00-06:55 UTC; quant-trading: the last Tokyo hour)
in the first minutes after the London open: long above the box high, short below the box low
skip a break that overshoots the box by more than a set distance; stop and target fixed; flat at session end
N2 gate (this project): block new lots while price is below the low of the first N minutes of the US session
```

## Evidence

* **No academic study found.** Every source located is practitioner
  material (EA vendors, blogs, code templates such as StockSharp's) with
  no out-of-sample or cost-adjusted results. The owner-supplied Gemini
  answer cites Chaboud et al. (2014, *Journal of Finance*), which studies
  how algorithmic trading changed FX price efficiency, not session
  breakouts (it is cited on RK83 instead).
* **Nearest published evidence, equity ORB:** Zarattini & Aziz (SSRN
  4416622, 2023) report a 5-minute ORB on QQQ, 2016–2023, with a 33%
  annualised alpha net of commissions; a third-party replication on five
  index futures reproduced the gross result and found nothing
  distinguishable from zero after spread and slippage. (Summaries.)

## Against, and failure modes

* Daylight-saving and broker-server-time handling is the CSV's own
  caveat; the session boundaries move twice a year.
* Stops and end-of-day flattening realise losses; the trade needs a
  short side; spot FX is not an instrument this project trades.

## Fit with volatility-ai

The trade is ⛔. The gate (N2) is built and in the entry-gate probes
(`config/probe_entry_gate_opening_range.yaml`); N3 (`prior_low`) is the
gap variant. Neither is measured yet.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Practitioner descriptions found by search (DailyForex, StockSharp's
  "London BreakOut Classic" example). No primary or academic source.
* Zarattini, C., Aziz, A. (2023). "Can Day Trading Really Be
  Profitable?" SSRN 4416622 (<https://papers.ssrn.com/abstract=4416622>).
  Abstract and summaries, plus an MQL5 blog replication (not peer
  reviewed).
* This repository: ledger Q4, N2, N3, C-M2; `research/catalog/je_suis_tm.py`;
  `research/strategies/entry_gates.py`.
