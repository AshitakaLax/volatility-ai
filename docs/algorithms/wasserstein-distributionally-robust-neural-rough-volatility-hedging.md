# Wasserstein Distributionally Robust Neural Rough Volatility Hedging

**Ledger ID RK329** · rank 329 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Robust statistics / Rough path theory / Derivatives hedging |
| Potential effectiveness rank | 329 (1 = strongest) |
| AI implementability rank | 288 (1 = easiest) |
| Retail advantage rank | 299 (1 = strongest) |
| Fit with this project | ⛔ (options hedging) |
| Implemented in volatility-ai | **Research code** in `research.catalog.derivatives`: `DeepHedger`, `worst_case_sampler`, `rough_bergomi_paths`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK377, RK352, RK391 |

## In one paragraph

Hedge against the worst rough-volatility model in a Wasserstein ball
around the calibrated one. Robust hedging with neural SDEs has a direct
antecedent: price bounds and hedges over the family of calibrated neural
SDEs, tied to causal optimal transport. The CSV's reference, arXiv
2009.08295, is Morrill et al.'s *Neural Rough Differential Equations for
Long Time Series*, a sequence-modelling paper, not a pricing or hedging
one.

## Evidence

* **Gierjatowicz, Sabate-Vidales, Šiška, Szpruch & Žurič, "Robust
  pricing and hedging via neural SDEs," *Journal of Computational
  Finance* (arXiv 2007.04154):** drift and diffusion learned by
  over-parameterised networks, calibrated under risk-neutral and
  real-world measures; gives robust price bounds and hedges and
  simulates scenarios. Tested on local and stochastic volatility models,
  the journal version on market data. (Abstract.)
* **Horvath, Teichmann & Žurič (2021), "Deep Hedging under Rough
  Volatility," *Risks* 9(7), 138 (arXiv 2102.01962):** the deep-hedging
  network trained on non-Markovian rough volatility paths; architectures
  for path dependence; P&L compared with jump-diffusion models under
  infrequent rebalancing. (Abstract.)

## Against, and failure modes

* The ambiguity set's size drives the hedge; robust hedges are
  expensive.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gierjatowicz, P., Sabate-Vidales, M., Šiška, D., Szpruch, L., Žurič,
  Ž. *Journal of Computational Finance*.
  <https://arxiv.org/abs/2007.04154>. Abstract.
* Horvath, B., Teichmann, J., Žurič, Ž. (2021). *Risks* 9(7), 138.
  doi:10.3390/risks9070138. Abstract.
