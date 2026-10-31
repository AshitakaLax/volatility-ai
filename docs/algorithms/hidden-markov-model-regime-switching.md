# Hidden Markov Model Regime Switching

**Ledger ID RK102** · rank 102 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Regime / machine learning |
| Potential effectiveness rank | 102 (1 = strongest) |
| AI implementability rank | 290 (1 = easiest) |
| Retail advantage rank | 127 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** A regime input to compare against the NATR regime; the Gaussian HMM is already built (C-R3). |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk102_hmm`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=hmm`, component `HmmRegimeGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.strategies.regime_models`: `GaussianHMM`, `GaussianMixture`. |
| Related ledger entries | C-R3, V17, N5, RK10 |

## In one paragraph

Infer hidden market states (calm, trending, volatile) from returns or
volatility with a hidden Markov model and switch exposure by state.
Regime switching has the best out-of-sample support of the regime
methods: Kritzman, Page and Turkington forecast regimes out of sample
and beat static allocations. For this project it competes with the
volatility regime (NATR) that already gates the grid, and the causal
Gaussian HMM is built.

## Evidence

* **Kritzman, Page & Turkington (2012), *Financial Analysts Journal*
  68(3):** Markov-switching models of turbulence, inflation and growth
  find persistent "normal" and "event" regimes; regimes forecast out of
  sample and used to tilt risk premia and a stock/bond/cash mix beat
  static allocation, most for investors avoiding large losses.
  (Abstract.)
* **This repository:** `regime_models.GaussianHMM` (C-R3) fits and
  filters causally; no harness run has compared its filtered state with
  the NATR regime as the exit trigger.

## Against, and failure modes

* HMM states are re-labelled when refit and the filtered probability
  lags turning points; with two states it largely rediscovers a
  volatility threshold.

## Fit with volatility-ai

Long-only and single-instrument: the filtered high-volatility
probability can drive the same regime exit the NATR regime drives
(V17/N5). The test is whether it exits earlier or with fewer whipsaws
than NATR on TQQQ, walk-forward.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Kritzman, M., Page, S., Turkington, D. (2012). Regime Shifts:
  Implications for Dynamic Strategies. *Financial Analysts Journal*
  68(3), 22–39. Abstract.
* The CSV's reference is QuantConnect's research repository.
