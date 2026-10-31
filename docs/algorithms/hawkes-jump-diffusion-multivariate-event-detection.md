# Hawkes-Jump Diffusion Multivariate Event Detection

**Ledger ID RK314** · rank 314 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Point process / Event-driven microstructure |
| Potential effectiveness rank | 314 (1 = strongest) |
| AI implementability rank | 344 (1 = easiest) |
| Retail advantage rank | 7,557 (1 = strongest) |
| Fit with this project | ⏳ as a daily stress gauge (jump intensity) · ⛔ at event frequency |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk314_hawkes_jumps`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=hawkes_jumps`, component `JumpIntensityGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** in `research.catalog.point_processes`: `detect_jumps`, `mutually_exciting_jump_intensity`, `fit_jump_excitation`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK248, RK277, RK333 |

## In one paragraph

Model returns as diffusion plus jumps whose arrival rate is a Hawkes
process: each jump raises the chance of more, in the same market and in
others. Fitted to daily index returns, the model finds self-excitation
in the US and elsewhere and an asymmetric cross-excitation in which US
jumps raise foreign jump intensity more than the reverse. The authors
propose the filtered intensity as a stress gauge.

## The rule

```text
dX_i = mu_i dt + sigma_i dW_i + Z_i dN_i
lambda_i(t) = lambda_inf_i + sum_j beta_ij * integral exp(-alpha_i (t - s)) dN_j(s)   # mutual excitation
```

## Evidence

* **Aït-Sahalia, Cacho-Diaz & Laeven (2015), "Modeling financial
  contagion using mutually exciting jump processes," *Journal of
  Financial Economics* 117(3), 585–606:** Hawkes jumps in daily index
  returns; self-excitation in the US and other markets, cross-excitation
  asymmetric (the US moves others more than the reverse); filtered jump
  intensities proposed as a stress gauge and tested out of sample.
  (Abstract.)
* **Bacry, Mastromatteo & Muzy (2015), "Hawkes processes in finance"
  (arXiv 1502.04592):** review of Hawkes models for volatility, market
  stability, contagion, execution and order-book dynamics (see RK248).

## Against, and failure modes

* Moment-based estimation on daily data has few jumps to fit;
  intensities lag in a fast crash.

## Fit with volatility-ai

At daily frequency the filtered jump intensity is a candidate regime
input alongside the NATR regime, in the same role as RK255's topological
measure. It would need to lead NATR's turbulent flag to add anything;
the paper's out-of-sample forecasts are the starting point.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Aït-Sahalia, Y., Cacho-Diaz, J., Laeven, R. J. A. (2015). *Journal of
  Financial Economics* 117(3), 585–606.
  doi:10.1016/j.jfineco.2015.03.002. Abstract.
* Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015). "Hawkes processes in
  finance." *Market Microstructure and Liquidity*.
  <https://arxiv.org/abs/1502.04592>. Abstract.
