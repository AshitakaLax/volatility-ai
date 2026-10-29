# AMM / CLOB Cross-Venue Arbitrage

**Ledger ID RK298** · rank 298 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Crypto / decentralized market structure |
| Potential effectiveness rank | 298 (1 = strongest) |
| AI implementability rank | 142 (1 = easiest) |
| Retail advantage rank | 133 (1 = strongest) |
| Fit with this project | ❌ (crypto) |
| Implemented in volatility-ai | **Research code** in `research.catalog.defi`: `optimal_arbitrage`, `simulate_arbitrage`, `lvr_rate`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK299, RK278 |

## In one paragraph

Buy on whichever of an automated market maker pool or a centralised
order book is cheaper and sell on the other, when the gap beats fees,
gas and slippage. Theory explains why the trade exists: a
constant-function market maker's price is stale between trades, and
arbitrageurs who correct it take a loss-versus- rebalancing from
liquidity providers. The edge goes to the fastest bots and to whoever
controls transaction ordering (MEV).

## Evidence

* **Milionis, Moallemi, Roughgarden & Zhang (2022), "Automated Market
  Making and Loss-Versus-Rebalancing" (arXiv 2208.06046):** LPs lose to
  arbitrageurs who pick off stale pool prices (LVR, an adverse-selection
  cost); the model matches realised losses in the Uniswap v2 WETH-USDC
  pool. (Abstract.)

## Against, and failure modes

* Failed or reordered transactions, gas, MEV, pool impact, bridge and
  custody risk (the CSV's caveat).

## Fit with volatility-ai

Rejected: crypto is outside the instrument rules.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Milionis, J., Moallemi, C. C., Roughgarden, T., Zhang, A. L. (2022).
  "Automated Market Making and Loss-Versus-Rebalancing."
  <https://arxiv.org/abs/2208.06046>. Abstract.
