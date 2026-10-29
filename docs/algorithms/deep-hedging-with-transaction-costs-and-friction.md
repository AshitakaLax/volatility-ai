# Deep Hedging with Transaction Costs and Friction

**Ledger ID RK352** · rank 352 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Deep reinforcement learning / Derivatives hedging |
| Potential effectiveness rank | 352 (1 = strongest) |
| AI implementability rank | 357 (1 = easiest) |
| Retail advantage rank | 282 (1 = strongest) |
| Fit with this project | ⛔ (options hedging) |
| Implemented in volatility-ai | **Research code** in `research.catalog.derivatives`: `DeepHedger`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK309, RK391, RK324 |

## In one paragraph

Learn a hedging strategy for a derivatives book with a neural network
that picks hedge positions to minimise a convex risk measure of the
final P&L, with transaction costs, liquidity limits and risk limits in
the simulation. In a Heston market with costs it beats the frictionless
complete-market hedge. It is the most established of the deep-learning
derivatives methods in this list.

## Evidence

* **Buehler, Gonon, Teichmann & Wood (2019), "Deep hedging,"
  *Quantitative Finance* 19(8), 1271–1291 (arXiv 1802.03042):** a
  network chooses hedge positions to minimise a convex risk measure of
  terminal P&L under transaction costs, liquidity limits and risk
  limits; in a Heston market with costs it beats the complete-market
  hedge that ignores frictions; also run on S&P 500 data. (Abstract.)
* **Horvath, Teichmann & Žurič (2021), "Deep Hedging under Rough
  Volatility," *Risks* 9(7), 138 (arXiv 2102.01962):** the deep-hedging
  network trained on non-Markovian rough volatility paths; architectures
  for path dependence; P&L compared with jump-diffusion models under
  infrequent rebalancing. (Abstract.)

## Against, and failure modes

* Only as good as the simulated market it trains on.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Buehler, H., Gonon, L., Teichmann, J., Wood, B. (2019). "Deep
  hedging." *Quantitative Finance* 19(8), 1271–1291.
  <https://arxiv.org/abs/1802.03042>. Abstract.
* Horvath, B., Teichmann, J., Žurič, Ž. (2021). *Risks* 9(7), 138.
  doi:10.3390/risks9070138. Abstract.
