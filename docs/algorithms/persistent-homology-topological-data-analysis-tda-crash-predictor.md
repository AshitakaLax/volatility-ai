# Persistent Homology Topological Data Analysis (TDA) Crash Predictor

**Ledger ID RK254** · rank 254 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Topological data analysis / Risk management |
| Potential effectiveness rank | 254 (1 = strongest) |
| AI implementability rank | 294 (1 = easiest) |
| Retail advantage rank | 7,422 (1 = strongest) |
| Fit with this project | ⏳ as a regime input (crash early warning) |
| Implemented in volatility-ai | **Research code** in `research.catalog.topology`: `landscape_norm_series`, `stress_alert`, `tda_exposure`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK255, RK262, RK268, RK269 |

## In one paragraph

Build Vietoris–Rips complexes from rolling multi-asset point clouds and
track persistence diagrams (Betti numbers) as a crash warning. The core
evidence is Gidea and Katz (2018): landscape norms of four US indices'
returns grew before the dot-com and Lehman crashes. That is two events,
in sample. The CSV's reference (arXiv 1904.04044) is a set of
pure-mathematics lecture notes on persistence ("Topological Persistence
in Geometry and Analysis"), not a finance study.

## Evidence

* **Gidea & Katz (2018), "Topological data analysis of financial time
  series: Landscapes of crashes," *Physica A* 491, 820–834:**
  sliding-window point clouds of daily log-returns of the S&P 500, DJIA,
  Nasdaq and Russell 2000; the Lp-norms of persistence landscapes grow
  before the primary peak of a crash, and their low-frequency spectral
  density rises for about 250 trading days before the March 2000 dot-com
  peak and the Lehman bankruptcy. Two crashes, in sample, no
  out-of-sample test in the abstract. (Abstract.)

## Against, and failure modes

* Two crashes are not a test; window, embedding and threshold choices
  are free parameters.
* Topological features of returns move with volatility and correlation,
  which simpler measures already track.

## Fit with volatility-ai

As a crash early-warning input to the regime it would fit (it never
trades by itself). The evidence is two crashes, in sample; the NATR
regime already reacts to rising volatility within days.

## How to test it here

Compute persistence-landscape Lp-norms on a trailing window of daily
QQQ, SPY, IWM and DIA returns (giotto-tda or ripser), causally, and
check whether their rise leads the NATR regime's turbulent flag in 2000,
2008, 2020 and 2022, with the threshold fixed before looking.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834.
  <https://arxiv.org/abs/1703.04385>. Abstract.
* The CSV's references: giotto-tda; arXiv 1904.04044 (persistence
  lecture notes; not finance).
