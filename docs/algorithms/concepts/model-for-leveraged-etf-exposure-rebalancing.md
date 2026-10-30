# Model for leveraged-ETF exposure rebalancing

**Concept page** · shared by **4** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,427) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Unspecified model |
| Fit with this project | 🧪 worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** The task is the project's own: a target-exposure rule for TQQQ is a sizing lever to measure beside V18 and N7. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Optimal Scholarly Leveraged
ETF Rebalancer Ver-28") combine a method word, "Scholarly", a task and a
serial number, and the rows' references are software libraries or papers
the CSV's own review calls unrelated. There is no specific algorithm
behind each name to research, so this page researches what the members
share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The title names no method beyond "model", so this
page judges the task itself. The decay that drives the task is well
understood: realised variance of the underlying explains most of the gap
between a leveraged ETF and a static leveraged position, and leverage
held only in calm trends keeps most of the upside.

## The CSV's description

Proposed model for leveraged-ETF exposure rebalancing: Adjust exposure
to maintain a specified leveraged-ETF allocation or target exposure,
while accounting for daily-reset effects, path dependency, and
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

## Against, and failure modes

* Volatility decay is a property of the path, not a forecastable edge:
  rebalancing toward a target chooses how much leverage to hold, it does
  not remove the decay.
* A target-exposure rule and a lot-harvesting grid pull in different
  directions; every sale still has to pass the no-loss guard.

## Fit with volatility-ai

This is the project's home ground. The engine trades TQQQ and already
varies its exposure three ways: volatility targeting (V18), the leverage
step-down between TQQQ and QQQ (N7) and the SMA leverage switch (V16).
An exposure rule here is a sizing lever on the grid, not a separate
strategy.

## How to test it here

Run the grid with and without the TQQQ/QQQ step-down (N7) and the SMA
switch (V16) on causal signals, on the same windows, and compare CAGR,
maximum drawdown and Calmar; the no-loss guard stays in force.

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

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8427 | Optimal Scholarly Leveraged ETF Rebalancer Ver-28 | Point processes / Recurrent neural networks / Stock volatility | 5380 | 7431 | No |
| 8433 | Ensemble Scholarly Leveraged ETF Rebalancer Ver-48 | Point processes / Recurrent neural networks / Stock volatility | 5381 | 9367 | No |
| 8456 | Optimal Scholarly Leveraged ETF Rebalancer Ver-128 | Point processes / Recurrent neural networks / Stock volatility | 13571 | 13104 | No |
| 8462 | Ensemble Scholarly Leveraged ETF Rebalancer Ver-148 | Point processes / Recurrent neural networks / Stock volatility | 5387 | 7433 | No |
