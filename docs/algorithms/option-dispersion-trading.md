# Option Dispersion Trading

**Ledger ID RK87** · rank 87 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Options volatility relative value |
| Potential effectiveness rank | 87 (1 = strongest) |
| AI implementability rank | 98 (1 = easiest) |
| Retail advantage rank | 257 (1 = strongest) |
| Fit with this project | ⛔ (options) |
| Implemented in volatility-ai | **Research code** in `research.catalog.derivatives`: `implied_correlation`, `realized_correlation`, `dispersion_pnl`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK21 |

## In one paragraph

Index options are priced off the components' volatilities and their
correlation, and implied correlation tends to be higher than the
correlation that is later realised. Sell index volatility and buy the
components' volatility (delta-hedged straddles or variance swaps on
both), and the position is short correlation and collects that
premium. The academic evidence that correlation risk is priced is
strong. The same study finds the premium cannot be captured once
realistic trading frictions are included.

## The rule

```
implied correlation rho_impl from index IV and component IVs (weights w_i)
rho_impl high vs realised: short index straddles, long weighted component straddles (vega-matched), delta-hedge daily
hold to expiry or until the spread normalises
```

## Evidence

* **Driessen, Maenhout & Vilkov (2009), "The Price of Correlation Risk:
  Evidence from Equity Options," *Journal of Finance* 64(3), 1377–1406:**
  S&P 100 index options and options on all components; correlation risk
  is priced and explains the cross-section of index and individual option
  returns; a strategy exploiting it has a high alpha that does not
  survive realistic trading frictions (limits to arbitrage). (Abstract.)

## Against, and failure modes

* Correlation spikes in crashes; jump and earnings risk on components;
  costs on dozens of option positions (the CSV's caveat).

## Fit with volatility-ai

Out of scope: options.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Driessen, J., Maenhout, P. J., Vilkov, G. (2009). *Journal of Finance*
  64(3), 1377–1406.
  <https://ideas.repec.org/a/bla/jfinan/v64y2009i3p1377-1406.html>.
  Abstract.
