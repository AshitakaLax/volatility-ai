# Extreme Value Theory (EVT) Dynamic Tail-Risk Hedge

**Ledger ID RK130** · rank 130 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Quantitative risk management / Tail risk |
| Potential effectiveness rank | 130 (1 = strongest) |
| AI implementability rank | 214 (1 = easiest) |
| Retail advantage rank | 260 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** The put-buying hedge is excluded, but an EVT expected-shortfall forecast is a candidate exposure governor next to the NATR regime. |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk130_evt`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=evt`, component `EvtSizer`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.catalog.concepts`: `pot_var_es`, `tail_budget_exposure`. |
| Related ledger entries | V17, N5, RK133 |

## In one paragraph

Fit a generalised Pareto distribution to the tail of returns (after
GARCH filtering, as McNeil and Frey do), forecast VaR and expected
shortfall, and buy out-of-the-money puts when tail risk spikes. The
forecasting half is well established; the hedge half uses options, which
the owner excludes, and puts are costly protection (RK133).

## Evidence

* **McNeil & Frey (2000), *Journal of Empirical Finance* 7:** GARCH-EVT
  conditional VaR and ES forecasts, with good forecasting properties in
  later comparisons. (Abstract.)
* **This repository:** `concepts.pot_var_es` and `tail_budget_exposure`
  scale exposure to an ES budget; `econometrics.garch11_fit` provides
  the filter.

## Against, and failure modes

* Tail fits on a few thousand days rest on a handful of crashes; a
  de-risk trigger that fires after a crash starts sells lots below cost
  unless it is the regime exit.

## Fit with volatility-ai

Drop the puts; keep the forecast. An EVT expected-shortfall forecast
could cut new lots or trigger the regime exit when tail risk rises. Test
it against the NATR regime, which already does that job well.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* McNeil, A. J., Frey, R. (2000). *Journal of Empirical Finance* 7(3–4),
  271–300. Abstract.
