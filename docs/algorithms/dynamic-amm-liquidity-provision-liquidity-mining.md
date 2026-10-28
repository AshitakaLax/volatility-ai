# Dynamic AMM Liquidity Provision / Liquidity Mining

**Ledger ID RK299** · rank 299 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Crypto / liquidity provision |
| Potential effectiveness rank | 299 (1 = strongest) |
| AI implementability rank | 331 (1 = easiest) |
| Retail advantage rank | 959 (1 = strongest) |
| Fit with this project | ❌ (crypto) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK298 |

## In one paragraph

Provide liquidity to AMM pools, concentrating it in price ranges and
rebalancing as prices move, to earn trading fees and token rewards. The
measured outcome on Uniswap v3 was negative: across 17 large pools, fees
of $199.3 million against $260.1 million of impermanent loss, so simply
holding the tokens beat providing liquidity by about $60.8 million.

## Evidence

* **Loesch, Hindman, Richardson & Welch (2021), "Impermanent Loss in
  Uniswap v3" (arXiv 2111.09192):** 17 pools above $10 million TVL
  (stablecoin pairs excluded); for almost all pools impermanent loss
  exceeded fees; $199.3m fees against $260.1m impermanent loss.
  (Abstract.)
* **Milionis et al. (2022):** LPs' running cost is
  loss-versus-rebalancing to arbitrageurs (see RK298). (Abstract.)

## Against, and failure modes

* Fee APR is not total return; impermanent loss, emissions, contract
  risk, gas and toxic flow (the CSV's caveat).

## Fit with volatility-ai

Rejected: crypto is outside the instrument rules.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Loesch, S., Hindman, N., Richardson, M. B., Welch, N. (2021).
  "Impermanent Loss in Uniswap v3." <https://arxiv.org/abs/2111.09192>.
  Abstract.
* Milionis et al. (2022), arXiv 2208.06046. Abstract.
