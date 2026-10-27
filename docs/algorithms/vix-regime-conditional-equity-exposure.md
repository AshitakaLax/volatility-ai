# VIX-Regime Conditional Equity Exposure

**Ledger ID RK21** · rank 21 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Regime / volatility |
| Potential effectiveness rank | 21 (1 = strongest) |
| AI implementability rank | 196 (1 = easiest) |
| Retail advantage rank | 100 (1 = strongest) |
| Fit with this project | 🧪 (VIX as data; no volatility products) |
| Implemented in volatility-ai | **Yes.** V12 scales grid lots by an implied-volatility series (VIXY as the VXN proxy) in the champion strategy; VIX bands are research code (`research/strategies/vix_bands.py`, catalog R4); the VIX/VIX3M term-structure regime is a catalog lead (`leads.vix_term_structure_regime`). Unmeasured. |
| Related ledger entries | V12, Q15, R4 (catalog), N5, RK22 |

## In one paragraph

Change equity exposure when the VIX crosses historical percentiles. The
rule can point either way, and the evidence says the contrarian
direction is the one with support: excess returns after the VIX is above
roughly its 80th–85th percentile have been much higher, over 1-, 3-, 6-
and 12-month horizons. That fits this project's own finding that buying
capitulation inside turbulent regimes pays (ultimate-algorithm.md L11).
The CSV's caveat is the key one: the VIX is a risk-neutral price of
volatility, not a forecast of direction.

## The rule

```
p_t = percentile of VIX_t in its trailing 1-5-year history (data known at t)
defensive form:   exposure = high when p_t is low, reduced when p_t is high
contrarian form:  add exposure (or allow buying) when p_t > ~0.8, i.e. after spikes
always: act at the next session; the VIX is data only (no VIX futures or volatility ETFs)
```

## Evidence

* **Copeland & Copeland (1999), *Financial Analysts Journal* 55(2),
  73–81:** VIX changes lead daily returns of style and size portfolios:
  after VIX rises, large caps beat small and value beats growth. A later
  replication (1990–2008) finds the style effect significant only for
  holding periods of 30 days or more. (Abstract and summary.)
* **Bansal & Stivers (2023, SSRN working paper):** much higher excess
  equity returns follow when implied volatility is above a threshold near
  its 80th–85th percentile, at 1-, 3-, 6- and 12-month horizons,
  1990–2022. (Summary.)
* **In this repository:** inside detected turbulent spells, cash plus
  capitulation-close reversal buys was positive in 47 of 47 spells, and
  94–100% of the reversal trades exited at target (ultimate-algorithm.md,
  L11 and L13): the same contrarian mechanism, measured on volatility
  rather than the VIX.

## Against, and failure modes

* A high VIX usually follows a fall, so the high-VIX premium may be just
  the rebound after losses (an actuarial commentary's point).
* Spikes cluster: the first spike in a crash is not the bottom (2008).
* VIX measures S&P 500 options; this book trades the Nasdaq-100 (VXN is
  the matching index, which V12 could not source; Q15's calculator could
  compute it from option quotes).

## Fit with volatility-ai

Fits as data, and is partly built: V12's implied-vol lot scaling and the
VIX bands. Volatility ETFs as holdings remain excluded.

## How to test it here

The VIX series is in `data/external/` after the ML input fetch. Measure
V12 on TQQQ with a fixed exponent in both directions (smaller lots and
larger lots at high implied volatility), then a contrarian permission:
allow the Ultimate turbulent sleeve's reversal buys only when the VIX is
above its trailing 80th percentile, and compare with the unconditioned
sleeve.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Copeland, M. M., Copeland, T. E. (1999). "Market Timing: Style and
  Size Rotation Using the VIX." *Financial Analysts Journal* 55(2),
  73–81. <https://ideas.repec.org/a/taf/ufajxx/v55y1999i2p73-81.html>.
  Abstract.
* Bansal, N., Stivers, C. (2023). "Time-Varying Equity Premia with a
  High-VIX Threshold." SSRN working paper. Summary via Quantpedia.
* This repository: ledger V12, Q15; `research/strategies/vix_bands.py`;
  `research/catalog/leads.py`; `docs/research/ultimate-algorithm.md`.
