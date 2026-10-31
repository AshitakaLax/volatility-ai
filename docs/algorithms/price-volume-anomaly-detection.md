# Price/Volume Anomaly Detection

**Ledger ID RK243** · rank 243 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Machine learning / microstructure |
| Potential effectiveness rank | 243 (1 = strongest) |
| AI implementability rank | 223 (1 = easiest) |
| Retail advantage rank | 54 (1 = strongest) |
| Fit with this project | 🧪 as a data-quality or risk flag · ❌ as an alpha source |
| Implemented in volatility-ai | **Yes.** Tradeable as an entry gate on the `hf_signal_gated` strategy: `anomaly_gate=price|price_volume` (`research/strategies/signal_gates.py`, `AnomalyGate`). Off by default; unmeasured. Before this change: **Partial.** Exponentially weighted anomaly bands (`forecasting.ewm_anomalies`, ledger A8); not used to filter trades. |
| Related ledger entries | A8, C-MS5 |

## In one paragraph

Flag unusual prices, spreads, volumes or order flow with statistical
bands or unsupervised models (isolation forests, autoencoders) and use
the flags to skip trades or raise risk alerts. As the CSV says, an
anomaly is not a prediction: bad ticks, corporate actions and scheduled
events produce most of them. I found no study showing that anomaly
filtering improves a trading strategy's returns.

## The rule

```text
z_t = (x_t - EWMA_span(x)) / EWMSD_span(x) for price change, volume, spread
flag when |z_t| > z*; skip new entries (or cut size) while flagged
```

## Evidence

* Surveys of anomaly detection in finance concentrate on fraud and data
  quality, not trading returns. (Search.)
* **No study found** of anomaly filters improving strategy returns.

## Against, and failure modes

* Most anomalies are bad ticks or scheduled events (the CSV's caveat);
  filtering them can remove exactly the volatile sessions a harvesting
  grid profits from.

## Fit with volatility-ai

Useful as a data-quality check on incoming bars (a bad tick can trigger
a grid buy). As a trading filter it would fight the grid, which wants
volatile sessions. The EWM bands exist as research code.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* This repository: `research/catalog/forecasting.py` (`ewm_anomalies`),
  ledger A8.
