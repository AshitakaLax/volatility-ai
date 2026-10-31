# Hurst-Exponent Trend / Mean-Reversion Regime Gate

**Ledger ID RK103** · rank 103 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Regime filter |
| Potential effectiveness rank | 103 (1 = strongest) |
| AI implementability rank | 52 (1 = easiest) |
| Retail advantage rank | 93 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** The estimator is built (C-MR4) but too noisy on short windows to gate trades, and no study supports the gate. |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk103_hurst_regime`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=hurst_regime`, component `HurstRegimeGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.strategies.mean_reversion`: `hurst_exponent`, `variance_ratio`. |
| Related ledger entries | C-MR4, RK202, RK297 |

## In one paragraph

Estimate the Hurst exponent on a rolling window and allow trend signals
when it is above 0.5 and mean-reversion signals when below. The idea is
sound in principle, but Hurst estimates on a few hundred bars have
standard errors comparable to the distance from 0.5, and the only
trading study found is a student working paper.

## Evidence

* **Chang, Lizardi & Shah (2022, arXiv 2205.11122):** switching momentum
  and mean reversion on H > or < 0.5 earned higher returns at higher
  risk; a student paper whose sample, costs and out-of-sample design are
  not stated in its abstract.
* **This repository:** `mean_reversion.hurst_exponent` and
  `variance_ratio` (C-MR4) exist as diagnostics; `information.hurst_dfa`
  adds a DFA estimator.

## Against, and failure modes

* Thresholds (0.5, 0.45, a 0.4–0.6 dead band) are arbitrary; long memory
  in returns is weak once short-range dependence is allowed for (Lo
  1991).

## Fit with volatility-ai

Useful as a diagnostic of TQQQ's persistence in a window, not as a gate:
an estimate whose error band straddles 0.5 cannot switch the grid
reliably.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chang, Lizardi, Shah (2022). Optimizing Returns Using the Hurst
  Exponent and Q Learning on Momentum and Mean Reversion Strategies.
  <https://arxiv.org/abs/2205.11122>. Abstract.
* The CSV's references are NautilusTrader's documentation and
  repository.
