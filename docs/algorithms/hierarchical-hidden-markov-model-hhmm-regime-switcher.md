# Hierarchical Hidden Markov Model (HHMM) Regime Switcher

**Ledger ID RK106** · rank 106 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Probabilistic regime / Hidden Markov Model |
| Potential effectiveness rank | 106 (1 = strongest) |
| AI implementability rank | 106 (1 = easiest) |
| Retail advantage rank | 259 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** A two-level bull/bear and volatility regime is plausible, but test it only after the plain HMM (RK102) earns its place. |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk106_hhmm`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=hhmm`, component `HmmRegimeGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.strategies.regime_models`: `GaussianHMM`. |
| Related ledger entries | RK102, C-R3 |

## In one paragraph

A two-layer HMM: the top level classifies bull and bear markets, a
sub-level high and low volatility within each. Oelschläger and Adam show
the hierarchy separates long trends from short swings on the DAX and S&P
500 better than a flat HMM; they report state detection, not trading
returns.

## Evidence

* **Oelschläger & Adam (2023), *Statistical Modelling* (arXiv
  2007.14874):** a hierarchical HMM identifies bearish and bullish
  phases of the DAX and S&P 500 as market moods with distinct return and
  volatility; implemented in the R package fHMM. (Abstract.)
* **Tayal (Waterloo thesis):** regime switching and technical trading
  with dynamic Bayesian networks on high-frequency stock data; only the
  outline was seen.

## Against, and failure modes

* Twice the parameters of a flat HMM on the same short history; the
  top-level bull/bear state changes rarely, so few out-of-sample
  switches are available to judge it.

## Fit with volatility-ai

Long-only: the top level could gate the grid's regime exit and the
sub-level its lot size. It adds estimation risk over RK102, so it is a
second step, not a first.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Oelschläger, L., Adam, T. (2023). Detecting bearish and bullish
  markets in financial time series using hierarchical hidden Markov
  models. *Statistical Modelling*. <https://arxiv.org/abs/2007.14874>.
  Abstract.
* Tayal, A. Regime Switching and Technical Trading with Dynamic Bayesian
  Networks in High-Frequency Stock Markets. University of Waterloo
  thesis. Outline only.
