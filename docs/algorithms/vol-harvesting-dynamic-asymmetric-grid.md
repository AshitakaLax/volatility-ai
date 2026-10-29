# Vol-Harvesting Dynamic Asymmetric Grid

**Ledger ID RK319** · rank 319 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Grid trading / Inventory management / Volatility harvesting |
| Potential effectiveness rank | 319 (1 = strongest) |
| AI implementability rank | 70 (1 = easiest) |
| Retail advantage rank | 46 (1 = strongest) |
| Fit with this project | ✅ this is volatility-ai's own design (V5, the champion) |
| Implemented in volatility-ai | **Yes.** The champion `hf_local_reference` grid (`research/strategies/high_frequency_sizing.py`, ledger V5) with its levers (V6–V12); a harvest sleeve (`harvest_sleeve_sizing.py`); volatility-scaled steps (C-G3) and RSI-scaled lots (V3) as alternatives. |
| Related ledger entries | V5, C-G3, C-G4, C-G6, V3, RK246 |

## In one paragraph

Buy a fixed-dollar lot each time the price falls one step below a
reference, hold each lot independently, and sell each at its own profit
target above its cost, never below it. The steps down and the targets up
differ (the asymmetry), and both can scale with volatility. On a
leveraged ETF this harvests the oscillation that volatility decay erodes
for a buy-and-hold owner. A static grid has roughly zero expected value
on a random walk; the edge has to come from mean reversion at the step's
scale and from how the grid survives trends. The binding risk is a long
decline that fills every rung.

## The rule

```text
reference = max(last buy price, rolling high over lookback_days)      # V5
buy one lot when price <= reference x (1 - live.step)
each lot sells at cost x (1 + live.profit_target); never below cost (no_loss_guard)
optional: step scaled by short-term volatility (C-G3); lot scaled by RSI (V3) or vol ratio (V7)
```

## Evidence

* **This repository's best known configuration**
  (`config/best_known_2026-08-24.yaml`): 25.38% CAGR, 45.57% maximum
  drawdown, 86,087 trades; a retune reached 38.61% CAGR at 82.4%
  drawdown, and high-frequency sweeps sit at 73–82% drawdown. Measured
  under `intrabar_fill="level"` and without cash yield (ledger V5
  caveats).
* **Chen, Chen & Jang (2025), "Dynamic Grid Trading Strategy: From Zero
  Expectation to Market Outperformance" (arXiv 2506.11921):** a static
  finite grid has roughly zero expected return; resetting the grid as
  price leaves its range beat the static grid and buy-and-hold on minute
  Bitcoin and Ethereum data, 2021–2024 (see C-G4). (Abstract.)
* **Avellaneda & Zhang (2010), "Path-dependence of leveraged ETF
  returns," *SIAM Journal on Financial Mathematics* 1, 586–603:** a
  leveraged fund's return equals the multiple of the index return minus
  a term proportional to realised variance (β(β − 1)/2 · σ² for leverage
  β), confirmed on 56 funds at quarterly horizons. (Abstract.)
* **Hallerbach (2014), "Disentangling rebalancing return," *Journal of
  Asset Management* 15(5):** rebalancing return splits into a volatility
  return and a dispersion discount; it pays with high, dispersed
  volatility and low correlation, before costs. (Abstract and summary.)

## Against, and failure modes

* A persistent decline fills every rung and strands capital; drawdown is
  the binding problem (V5), which the regime exit and drawdown throttle
  address.
* A persistent rise strands the grid without lots; the rolling local
  reference is V5's answer.
* Back-test results depend on the fill model (`intrabar_fill`) and on
  ignored cash yield.

## Fit with volatility-ai

It is the project. Every other entry in this list is judged by whether
it improves this book's drawdown or return without breaking its rules.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* This repository: `research/strategies/high_frequency_sizing.py` (V5),
  `harvest_sleeve_sizing.py`, `grid_spacing.py` (C-G3),
  `grid_lifecycle.py` (C-G4, C-G6), `engine/trading/no_loss_guard.py`,
  `config/best_known_2026-08-24.yaml`.
* Chen, Chen & Jang (2025). "Dynamic Grid Trading Strategy: From Zero
  Expectation to Market Outperformance."
  <https://arxiv.org/abs/2506.11921>. Abstract.
* Avellaneda, M., Zhang, S. (2010). "Path-dependence of leveraged ETF
  returns." *SIAM J. Financial Math.* 1, 586–603.
  <https://math.nyu.edu/~avellane/LeveragedETF20090515.pdf>.
* Hallerbach, W. G. (2014). "Disentangling rebalancing return." *Journal
  of Asset Management* 15(5), 301–316. Abstract.
