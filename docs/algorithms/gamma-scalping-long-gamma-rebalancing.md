# Gamma Scalping / Long-Gamma Rebalancing

**Ledger ID RK309** · rank 309 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Options / delta hedging |
| Potential effectiveness rank | 309 (1 = strongest) |
| AI implementability rank | 208 (1 = easiest) |
| Retail advantage rank | 237 (1 = strongest) |
| Fit with this project | ⛔ (options; and long gamma pays the volatility risk premium) |
| Implemented in volatility-ai | **Research code** in `research.catalog.derivatives`: `gamma_scalp_pnl`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK352, Q12 |

## In one paragraph

Buy options and delta-hedge them repeatedly, so the position earns when
realised volatility exceeds the implied volatility paid. On average it
loses: delta- hedged long option positions on the S&P 500 earn negative
returns, the signature of a negative volatility risk premium, and the
loss is larger when volatility is high. Long gamma is insurance, and
insurance has a price.

## The rule

```text
long option (gamma > 0), delta-hedge with the underlying each interval
P&L ~ 1/2 gamma S^2 (realised variance - implied variance) per unit time - hedging costs
```

## Evidence

* **Bakshi & Kapadia (2003), "Delta-Hedged Gains and the Negative Market
  Volatility Risk Premium," *Review of Financial Studies* 16(2),
  527–566:** delta-hedged S&P 500 option gains are below zero, less so
  for out-of-the-money options and more when volatility is high;
  evidence of a negative market volatility risk premium. (Abstract.)

## Against, and failure modes

* Pays the volatility risk premium on average; frequent hedging costs.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing. The grid is
economically the opposite position: it is short gamma (buys falls, sells
rises), and it collects the premium that this strategy pays.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bakshi, G., Kapadia, N. (2003). *Review of Financial Studies* 16(2),
  527–566. doi:10.1093/rfs/hhg002. Abstract.
