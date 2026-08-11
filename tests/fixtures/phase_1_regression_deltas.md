# Phase 1 regression deltas

## Task 1.6 verification

The Task 0.1 fixture uses `FixedPortfolioPercentage`, which does not consume
per-bar drawdown or indicator state. Its non-drawdown metrics remain identical
to the frozen Phase 0 baseline after Tasks 1.2-1.5.

| Metric | Phase 0 baseline | Post Phase 1 | Expected delta |
|---|---:|---:|---:|
| Final Portfolio Value | 100099.81489816227 | 100099.81489816227 | 0 |
| Trade Count | 4 | 4 | 0 |
| Total Return % | 0.09981489816226531 | 0.09981489816226531 | 0 |
| Capital Velocity Index | 0.000998148981622653 | 0.000998148981622653 | 0 |
| Max Drawdown % | 0.0 | 0.4430668810465577 | +0.4430668810465577 percentage points |

The drawdown change is intentional and comes from Task 1.2: peak equity and
current drawdown are now sampled on every historical bar, including bars that
do not trigger a grid purchase. The fixture's deepest drawdown occurs on such
a non-trigger bar.

Task 1.3's `record_tick` hook and Task 1.4's drawdown-aware sizing API do not
change the FixedPortfolioPercentage result because that strategy ignores its
per-bar tick and drawdown inputs for sizing.

Task 1.5 preserves the simulation's complete-fill behavior. The simulation OMS
returns `FILLED`, so the fill-status guard does not change the fixture's
accounting.

## PerformanceAnalyzer drawdown ownership

`PerformanceAnalyzer.calculate_metrics()` returns final value, trade count,
total return, and Capital Velocity Index. It does not return `Max Drawdown %`.
Therefore the controller's `Max Drawdown %` assignment is not silently
overwriting an analyzer-provided drawdown metric; the controller owns this
metric for the current simulation path.
