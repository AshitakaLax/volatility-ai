# Continuous-Time Mean-Variance Reinforcement Learning Agent

**Ledger ID RK220** · rank 220 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Reinforcement Learning / Portfolio Theory |
| Potential effectiveness rank | 220 (1 = strongest) |
| AI implementability rank | 174 (1 = easiest) |
| Retail advantage rank | 187 (1 = strongest) |
| Fit with this project | ⏳ for a multi-asset book · no use for the single-instrument grid |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk220_emv`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=emv`, component `EmvSizer`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** in `research.catalog.deep_rl`: `EMVAgent`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK227, RK234 |

## In one paragraph

Learn a continuous-time mean-variance policy with an actor-critic method
under entropy regularisation, which makes the optimal exploration policy
Gaussian and handles Markowitz's time inconsistency. Wang and Zhou's
framework proves a policy-improvement theorem; follow-up S&P 500 tests
report over 10% annualised returns, ahead of econometric and deep-RL
baselines, and later work finds it among the best strategies in bear
markets. These are the authors' own results.

## Evidence

* **Wang & Zhou, "Continuous-time mean-variance portfolio selection: A
  reinforcement learning framework" (arXiv 1904.11392; published in
  *Mathematical Finance*, details unconfirmed):** entropy-regularised
  exploratory control; Gaussian optimal policy; policy-improvement
  theorem; implementable algorithm (EMV). (Abstract.)
* **Wang (arXiv 1907.11718):** S&P 500 tests (monthly 2000–2010; daily
  2018); over 10% annualised, outperforming econometric and deep-RL
  methods. (Abstract.)
* **Huang, Jia & Zhou (arXiv 2412.16175):** continuous-time RL
  strategies consistently among the best on S&P 500 stocks, especially
  in a volatile bear market. (Abstract.)
* The CSV's reference, arXiv 1911.11862, was not identified.

## Against, and failure modes

* Results are from the method's authors; mean-variance inputs remain the
  weak point.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Wang, H., Zhou, X. Y. <https://arxiv.org/abs/1904.11392>. Abstract.
* Wang, H. <https://arxiv.org/abs/1907.11718>. Abstract.
* Huang, Y., Jia, Y., Zhou, X. Y. <https://arxiv.org/abs/2412.16175>.
  Abstract.
