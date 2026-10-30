# Adaptive approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,500) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | 🧪 worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** Scale leverage with recent volatility, which the decay result and the volatility-targeting literature both support and N7 and V18 already implement; measure it on the grid. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly
Leveraged ETF Rebalancer Alpha-63") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The adaptive version lets its parameters or
thresholds move with recent data. Adapting leverage to volatility is the
evidence-backed version: decay grows with realised variance, and
volatility-managed equity exposure has shown higher Sharpe ratios and
milder left tails.

## The CSV's description

Proposed adaptive approach to leveraged-ETF exposure rebalancing: Adjust
exposure to maintain a specified leveraged-ETF allocation or target
exposure, while accounting for daily-reset effects, path dependency, and
transaction costs. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Avellaneda & Zhang (2010), "Path-Dependence of Leveraged ETF
  Returns," *SIAM Journal on Financial Mathematics* 1, 586–603:** the
  gap between a leveraged ETF and a static leveraged position is driven
  mainly by the underlying's realised variance; fees and funding are
  predictable. (Abstract and author slides.)
* **Cheng & Madhavan (2009), "The Dynamics of Leveraged and Inverse
  ETFs," *Journal of Investment Management*:** daily rebalancing makes
  leveraged ETFs path-dependent and creates end-of-day rebalancing flows
  in the direction of the day's move (see C-MS6). (Paper; cited in the
  ledger.)
* **Gayed & Bilello (2016), "Leverage for the Long Run":** hold leverage
  above the index's 200-day average and T-bills below it; volatility,
  which erodes daily-reset leverage, clusters below the average. The
  repository's measurement of the same switch carries a same-session
  lookahead (V16, R1). (Paper summary in
  `docs/research/correction-strategies.md`.)
* **Moreira & Muir (2017), "Volatility-Managed Portfolios," *Journal of
  Finance* 72(4), 1611–1644:** taking less risk when volatility is high
  gave the market portfolio a 4.9% annual alpha and higher Sharpe
  ratios. (Abstract.)
* **Harvey, Hoyle, Korgaonkar, Rattray, Sargaison & Van Hemert (2018),
  "The Impact of Volatility Targeting," *Journal of Portfolio
  Management* 45(1), 14–33:** over 60+ assets since 1926, volatility
  scaling raised Sharpe ratios for equities and credit and made
  left-tail events less severe for all assets. (Abstract.)

## Against, and failure modes

* Volatility decay is a property of the path, not a forecastable edge:
  rebalancing toward a target chooses how much leverage to hold, it does
  not remove the decay.
* A target-exposure rule and a lot-harvesting grid pull in different
  directions; every sale still has to pass the no-loss guard.
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

## Fit with volatility-ai

This is the project's home ground. The engine trades TQQQ and already
varies its exposure three ways: volatility targeting (V18), the leverage
step-down between TQQQ and QQQ (N7) and the SMA leverage switch (V16).
An exposure rule here is a sizing lever on the grid, not a separate
strategy.

## How to test it here

Compare fixed TQQQ exposure with a volatility-scaled target (V18's rule
applied to the TQQQ book, or N7's step-down) on causal signals; judge by
Calmar and maximum drawdown, not by return alone.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Zhang, S. (2010). "Path-Dependence of Leveraged ETF
  Returns." *SIAM Journal on Financial Mathematics* 1, 586–603.
  doi:10.1137/090760805. Abstract.
* Cheng, M., Madhavan, A. (2009). "The Dynamics of Leveraged and Inverse
  ETFs." *Journal of Investment Management*. Cited in the ledger
  (C-MS6).
* Gayed, M. A., Bilello, C. (2016). "Leverage for the Long Run."
  Practitioner paper; see `docs/research/correction-strategies.md` R1.
* Moreira, A., Muir, T. (2017). "Volatility-Managed Portfolios."
  *Journal of Finance* 72(4), 1611–1644. doi:10.1111/jofi.12513.
  Abstract.
* Harvey, C. R., et al. (2018). "The Impact of Volatility Targeting."
  *Journal of Portfolio Management* 45(1), 14–33. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8500 | Adaptive Scholarly Leveraged ETF Rebalancer Alpha-63 | Topological data analysis / Persistent homology / Stock pairs | 2084 | 9372 | No |
| 8540 | Adaptive Scholarly Leveraged ETF Rebalancer Alpha-163 | Topological data analysis / Persistent homology / Stock pairs | 2095 | 7436 | No |
| 8580 | Adaptive Scholarly Leveraged ETF Rebalancer Alpha-263 | Topological data analysis / Persistent homology / Stock pairs | 11274 | 13110 | No |
| 8620 | Adaptive Scholarly Leveraged ETF Rebalancer Alpha-363 | Topological data analysis / Persistent homology / Stock pairs | 2114 | 9378 | No |
| 8660 | Adaptive Scholarly Leveraged ETF Rebalancer Alpha-463 | Topological data analysis / Persistent homology / Stock pairs | 2125 | 7441 | No |
