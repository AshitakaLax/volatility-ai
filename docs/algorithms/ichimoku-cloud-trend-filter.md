# Ichimoku Cloud Trend Filter

**Ledger ID RK111** · rank 111 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Trend / breakout |
| Potential effectiveness rank | 111 (1 = strongest) |
| AI implementability rank | 21 (1 = easiest) |
| Retail advantage rank | 88 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Parameter-sensitive and redundant with the trend filters already researched; the evidence does not favour it. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK17, RK38, V15 |

## In one paragraph

Combine the Tenkan and Kijun lines, the cloud and the lagging span into
a directional bias. The more careful tests find some profitable settings
on stock indices in one period and none that hold up consistently; a
widely cited energy-stock result failed once look-ahead bias was
removed.

## Evidence

* **Deng et al. (2021), *International Journal of Finance & Economics*
  26(4):** default (9, 26, 52) Ichimoku rules on four stock indices
  (1995–2018) and four currency pairs were not consistently profitable;
  parameter sweeps found some index strategies, none for currencies.
  (Abstract.)
* **QuantConnect replication of Gurrib (2020):** with look-ahead bias
  removed, an Ichimoku strategy on energy stocks failed to beat the
  sector ETF over five years.

## Against, and failure modes

* Five lines and three periods to tune; the cloud is a lagged
  moving-average band.

## Fit with volatility-ai

A trend filter for the grid's regime would duplicate the moving-average
and NATR filters already tested, with more parameters and no better
evidence.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Deng, S. et al. (2021). *International Journal of Finance & Economics*
  26(4), 5321–5336. Abstract.
* QuantConnect research, Ichimoku clouds in the energy sector. Read.
