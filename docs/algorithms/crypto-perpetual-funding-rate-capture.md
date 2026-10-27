# Crypto Perpetual Funding-Rate Capture

**Ledger ID RK84** · rank 84 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Crypto derivatives / carry |
| Potential effectiveness rank | 84 (1 = strongest) |
| AI implementability rank | 225 (1 = easiest) |
| Retail advantage rank | 7,420 (1 = strongest) |
| Fit with this project | ❌ (crypto, perpetual futures, short leg) |
| Implemented in volatility-ai | **Research code.** `crypto.funding_carry_positions` and `funding_carry_pnl` (ledger C-RJ2, rejected in the catalog). |
| Related ledger entries | C-RJ2, RK85, RK4 |

## In one paragraph

Hold spot crypto and short the perpetual future (or the reverse when
funding is negative) to collect the periodic funding payments while
staying close to delta-neutral. Crypto futures carry has been very large
(up to about 60% a year) and highly variable. It reflects leveraged
demand from small, trend-chasing traders and too little arbitrage
capital. The trade is not riskless: margin spikes and liquidations in
drawdowns force positions closed, and the authors link this to crypto's
frequent crashes.

## The rule

```
if annualised funding > costs + buffer: long spot, short perpetual (equal notional); collect funding each interval
exit when funding falls below the buffer or turns; manage margin on the short to avoid liquidation
```

## Evidence

* **Schmeling, Schrimpf & Todorov (2023), "Crypto carry," BIS Working
  Paper 1087:** Bitcoin and Ethereum futures carry up to 60% a year and
  strongly time-varying, driven by trend-chasing small investors and
  scarce arbitrage capital; cash-and-carry is risky because of margin
  spikes and liquidations. (Abstract.)
* **He, Manela, Ross & von Wachter, "Fundamentals of Perpetual Futures"
  (arXiv 2212.06888):** no-arbitrage prices for perpetuals; deviations
  of roughly 60–100% a year mean absolute, co-moving across coins and
  shrinking over time; an implied arbitrage strategy earns high Sharpe
  ratios even at high costs. (Abstract and summaries.)

## Against, and failure modes

* Funding is variable, not guaranteed; liquidation, exchange and custody
  risk, transfer delays (the CSV's caveat).

## Fit with volatility-ai

Rejected: crypto is outside the instrument rules (ledger C-RJ2).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Schmeling, M., Schrimpf, A., Todorov, K. (2023). "Crypto carry." BIS
  Working Paper 1087. <https://www.bis.org/publ/work1087.pdf>. Abstract.
* He, S., Manela, A., Ross, O., von Wachter, V. "Fundamentals of
  Perpetual Futures." <https://arxiv.org/abs/2212.06888>. Abstract.
* This repository: `research/catalog/crypto.py`, ledger C-RJ2.
