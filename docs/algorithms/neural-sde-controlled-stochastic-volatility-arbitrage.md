# Neural SDE Controlled Stochastic Volatility Arbitrage

**Ledger ID RK377** · rank 377 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Stochastic differential equations / Deep learning |
| Potential effectiveness rank | 377 (1 = strongest) |
| AI implementability rank | 359 (1 = easiest) |
| Retail advantage rank | 425 (1 = strongest) |
| Fit with this project | ⛔ (options; robust bounds, not an arbitrage) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK324, RK329, RK303 |

## In one paragraph

Fit a stochastic volatility model whose drift and diffusion are neural
networks to option prices, then trade where market prices sit outside
the model's robust bounds. Neural SDEs do give robust price bounds and
hedges, calibrated to both measures; they bound prices rather than
identifying arbitrage. The CSV's reference, arXiv 2009.08295, is Morrill
et al.'s *Neural Rough Differential Equations for Long Time Series*, a
sequence-modelling paper, not a pricing or hedging one.

## Evidence

* **Gierjatowicz, Sabate-Vidales, Šiška, Szpruch & Žurič, "Robust
  pricing and hedging via neural SDEs," *Journal of Computational
  Finance* (arXiv 2007.04154):** drift and diffusion learned by
  over-parameterised networks, calibrated under risk-neutral and
  real-world measures; gives robust price bounds and hedges and
  simulates scenarios. Tested on local and stochastic volatility models,
  the journal version on market data. (Abstract.)

## Against, and failure modes

* Bounds are wide when the model class is rich; mispricing relative to a
  model is model risk, not arbitrage.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gierjatowicz, P., Sabate-Vidales, M., Šiška, D., Szpruch, L., Žurič,
  Ž. *Journal of Computational Finance*.
  <https://arxiv.org/abs/2007.04154>. Abstract.
