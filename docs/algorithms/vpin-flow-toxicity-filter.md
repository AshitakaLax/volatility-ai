# VPIN Flow-Toxicity Filter

**Ledger ID RK247** · rank 247 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market microstructure / risk filter |
| Potential effectiveness rank | 247 (1 = strongest) |
| AI implementability rank | 363 (1 = easiest) |
| Retail advantage rank | 10,495 (1 = strongest) |
| Fit with this project | 🧪 as a buy gate (C-MM4) · evidence says it adds little beyond volume and volatility |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk247_vpin`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=vpin`, component `VpinGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code.** Bulk-classified VPIN from bars (`microstructure.vpin`, ledger C-MM4). |
| Related ledger entries | C-MM4, RK259, V7 |

## In one paragraph

VPIN estimates order-flow toxicity, the risk that liquidity providers
are trading with better-informed counterparties, from the imbalance
between buy- and sell-classified volume in equal-volume buckets. Its
authors proposed it as a warning of toxicity-induced volatility and
pointed to the 2010 flash crash. Critics found it peaked after the
crash, and that once current volume and volatility are controlled for it
has no incremental predictive power.

## The rule

```text
split volume into buckets of V shares; within each, buy share = Phi(dp / sigma) (bulk volume classification)
VPIN = mean over the last n buckets of |V_buy - V_sell| / V; flag toxicity above a percentile
```

## Evidence

* **Easley, López de Prado & O'Hara (2012), "Flow Toxicity and Liquidity
  in a High-frequency World," *Review of Financial Studies* 25(5),
  1457–1493:** VPIN in volume time with bulk classification, proposed as
  an indicator of short-term toxicity-induced volatility. (Abstract.)
* **Andersen & Bondarenko (2014), *Journal of Financial Markets* 17,
  1–46 and 53–64:** VPIN is a poor predictor of short-run volatility,
  peaked after the flash crash, is mechanically correlated with volume
  and volatility (depending on trade classification), and adds nothing
  once those are controlled. (Abstracts.) The authors' rejoinder (pp.
  47–52) disputes the critique.

## Against, and failure modes

* Predictive value debated and sensitive to trade classification (the
  CSV's caveat).

## Fit with volatility-ai

As a gate on grid buys (pause during toxic flow) it fits the rules, and
it is built from bars. But the critique says its content is volume and
volatility, which the champion already uses (V7 vol-ratio scaling, V8
volume scaling, the NATR regime). Low priority.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Easley, D., López de Prado, M., O'Hara, M. (2012). *Review of
  Financial Studies* 25(5), 1457–1493.
  <https://ideas.repec.org/a/oup/rfinst/v25y2012i5p1457-1493.html>.
  Abstract.
* Andersen, T. G., Bondarenko, O. (2014). "VPIN and the Flash Crash" and
  "Reflecting on the VPIN dispute." *Journal of Financial Markets* 17.
  Abstracts.
* This repository: `research/strategies/microstructure.py` (`vpin`,
  `bvc_buy_fraction`), ledger C-MM4.
