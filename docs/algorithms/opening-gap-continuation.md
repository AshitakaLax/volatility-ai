# Opening Gap Continuation

**Ledger ID RK79** · rank 79 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Intraday momentum / event |
| Potential effectiveness rank | 79 (1 = strongest) |
| AI implementability rank | 94 (1 = easiest) |
| Retail advantage rank | 56 (1 = strongest) |
| Fit with this project | 🧪 its downside as a buy gate (N3, X1) · ⛔ as a day trade (flat at close, stops) |
| Implemented in volatility-ai | **Yes.** Tradeable as an entry gate on the `hf_signal_gated` strategy: `gap_gate=gap_down` (`research/strategies/signal_gates.py`, `GapGate`). Off by default; unmeasured. Before this change: **Partial.** The gap-down side is the N3 `prior_low` gate; the first-half-hour version is the X1 intraday-momentum gate; the noise-band form is C-M1. No gap-continuation trade. |
| Related ledger entries | N3, X1, C-M1, C-M2, RK69 |

## In one paragraph

When the market opens with a large gap and the first minutes confirm it
(volume, breadth, price holding beyond the prior close), trade in the
gap's direction for the rest of the session. The best evidence is for
the index-level version: the return from the previous close to the end
of the first half hour predicts the last half hour's return in SPY
(Gao, Han, Li & Zhou 2018), more strongly on volatile and news days. A
long sample of US indices also finds prices tend to keep moving in the
gap's direction on gap days. This project uses the downside half as a
"do not buy into this" gate.

## The rule

```
gap = open / prior close - 1; act only if |gap| > threshold
confirmation: first-N-minute return in the gap's direction, opening volume above normal
trade in the gap's direction from the end of the confirmation window; flat at the close
gates (this project): N3 blocks buys after a gap below the prior session's low;
X1 blocks late-session buys when the first 30 minutes closed below the prior close by more than a threshold
```

## Evidence

* **Gao, Han, Li & Zhou (2018), "Market Intraday Momentum," *Journal of
  Financial Economics* 129(2), 394–414:** SPY 1993–2013; the first
  half-hour return, measured from the previous close, predicts the last
  half-hour return; stronger on volatile, high-volume, recession and
  macro-news days; also in ten other heavily traded ETFs. (Abstract.)
* **Plastun, Sibande, Gupta & Wohar (2020), "Price gap anomaly in the
  US stock market: the whole story," *North American Journal of
  Economics and Finance*:** Dow, S&P 500 and NASDAQ 1928–2018; on gap
  days prices tend to move in the gap's direction; the effect is
  temporary and gaps are not usually filled. (Abstract.)
* **Caporale & Plastun (2017), *Investment Analysts Journal*:** gaps in
  stocks, FX and commodities, 2000–2015. (Summary.)
* Weekend-gap work on 5-minute data reports mixed directions. (Summary.)

## Against, and failure modes

* Opening-auction slippage and pre-market data quality (the CSV's
  caveat); the edge is a fraction of a session's move and costs bite.
* Individual-stock gaps around earnings behave differently from index
  gaps.

## Fit with volatility-ai

As a day trade, out. The downside half is built twice (N3, X1), and both
are in the entry-gate probes but unmeasured. Measuring them is the next
step, not new code.

## How to test it here

Run the existing probes: `config/probe_entry_gate_prior_low.yaml` and
`config/probe_entry_gate_intraday_momentum.yaml` through
`FILL=causal bash tools/experiments/run_entry_gate_chain.sh`, and report the gated buys'
outcomes on gap-down days separately.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gao, L., Han, Y., Li, S. Z., Zhou, G. (2018). "Market Intraday
  Momentum." *Journal of Financial Economics* 129(2), 394–414.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414>.
  Abstract.
* Plastun, A., Sibande, X., Gupta, R., Wohar, M. E. (2020). "Price gap
  anomaly in the US stock market: the whole story." *North American
  Journal of Economics and Finance*.
  <https://repository.up.ac.za/handle/2263/78336>. Abstract.
* Caporale, G. M., Plastun, A. (2017). Price gaps, *Investment Analysts
  Journal*. Summary.
* This repository: ledger N3, X1, C-M1; `research/strategies/entry_gates.py`.
