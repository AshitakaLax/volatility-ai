# Triple EMA / Moving-Average Ribbon

**Ledger ID RK64** · rank 64 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / momentum |
| Potential effectiveness rank | 64 (1 = strongest) |
| AI implementability rank | 66 (1 = easiest) |
| Retail advantage rank | 9 (1 = strongest) |
| Fit with this project | ⏳ as a long-or-cash regime · ⛔ as a long/short trade |
| Implemented in volatility-ai | **Yes.** Tradeable as an entry gate on the `hf_signal_gated` strategy: `ribbon_gate=bearish` (`research/strategies/signal_gates.py`, `RibbonGate`). Off by default; unmeasured. Before this change: **Partial.** Single TA-Lib moving averages (EMA, TEMA, KAMA and others) were screened as regime flags in the V15 sweep; no ribbon-alignment rule exists. |
| Related ledger entries | V15, RK62, RK46 |

## In one paragraph

Plot several moving averages and treat the trend as confirmed only when
they are stacked in order (fast above slow, all rising). The best-known
version is Daryl Guppy's Multiple Moving Average: six short EMAs (3–15)
standing for traders and six long EMAs (30–60) for investors, with a
trend when both groups agree and separate. "Triple EMA" sometimes means a
three-average stack and sometimes TEMA, Mulloy's lag-reduced single
average; the CSV describes the stack. There is no academic evidence base
specific to ribbons; they are a filter on the crossover family (RK62)
that trades fewer, later signals.

## The rule

```
EMAs at lengths L1 < L2 < ... < Lk (Guppy: 3,5,8,10,12,15 and 30,35,40,45,50,60)
risk-on while EMA_L1 > EMA_L2 > ... > EMA_Lk  (optionally: all rising, groups separated)
risk-off when the order breaks (or when the short group falls into the long group)
```

## Evidence

* Practitioner sources only: Guppy's GMMA and its oscillator variant
  are described consistently by broker and education sites, with
  default lengths treated as conventions, not tested parameters.
* The academic statement for the whole family is Levine & Pedersen
  (2016): any combination of moving averages is a weighted sum of past
  returns, so a ribbon is a particular TSMOM weighting, not new
  information.
* Brock, Lakonishok & LeBaron (1992), offered for this family by the
  owner-supplied Gemini answer, test single and dual moving-average and
  channel rules on the Dow, not ribbons (see RK62).

## Against, and failure modes

* More averages add lag and parameters; the CSV's caveat is
  "parameter-mining risk".
* Requiring all-ordered states makes the filter mostly "off" in choppy
  markets, which is useful only if the strategy it gates loses in chop;
  the grid here *earns* in chop (volatility harvesting), so a ribbon gate
  turns it off where it is strongest.

## Fit with volatility-ai

A long-or-cash regime fits. Its likely value is low here for the reason
above: this project's book is a chop harvester and its own lesson L1 is
that direction regimes cost more than they save.

## How to test it here

If tested at all: a `ribbon_risk_on(daily, lengths=(10, 20, 50, 100, 200))`
regime beside `sma` and `macd` in `tools/leverage_stepdown.py`, causal,
with `--min-hold 5`. One fixed parameter set, decided in advance.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Guppy Multiple Moving Average (Daryl Guppy). Practitioner and broker
  descriptions found by search, e.g.
  <https://www.supermoney.com/encyclopedia/guppy-multiple-moving-average>.
* Levine, A., Pedersen, L. H. (2016). "Which Trend Is Your Friend?"
  *Financial Analysts Journal* 72(3), 51–66. Abstract.
* The CSV's own references:
  <https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators>,
  <https://github.com/je-suis-tm/quant-trading>.
