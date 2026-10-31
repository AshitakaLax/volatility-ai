# State-Filtered Momentum

**Ledger ID RK10** · rank 10 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / regime-aware momentum |
| Potential effectiveness rank | 10 (1 = strongest) |
| AI implementability rank | 35 (1 = easiest) |
| Retail advantage rank | 17 (1 = strongest) |
| Fit with this project | ⏳ as a regime condition on a long-only momentum rotation · ⛔ long/short |
| Implemented in volatility-ai | **Yes, as a backtest book.** `research/strategies/allocators.py` `state_filtered_momentum`, run by the portfolio book (`python -m tools.portfolio_book --allocator state_filtered_momentum --market SPY`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **No.** The pieces exist separately: market-state regimes (N5 NATR, `--regime sma`) and a relative-strength rotation (X3), but the rotation cannot yet be switched off by a regime. |
| Related ledger entries | X3, N5, V16, RK6, RK7 |

## In one paragraph

Run a momentum strategy only when the market is in a state where
momentum has historically paid. The founding result: US stock momentum
earned about 0.93% a month after the market had risen over the prior
three years and about −0.37% after it had fallen. A later strand uses
volatility instead of trend: momentum crashes happen in high-volatility
"panic" states after declines. The filter is the transferable part for
this project, because volatility-regime filters are what its own
research found robust.

## The rule

```
state_t = UP   if market return over the prior L months > 0   (Cooper et al.: L = 36)
          DOWN otherwise
alternative state: market volatility high/low (Daniel & Moskowitz)
if state_t is favourable: hold the momentum portfolio (RK6/RK7)
else: hold cash (or the market)
```

## Evidence

* **Cooper, Gutierrez & Hameed (2004)**, 1929–1995: momentum profits
  depend on the market state, about 0.93% a month after positive market
  returns and −0.37% after negative ones; the up-market profits reverse
  in the long run; macroeconomic factors do not explain them. (Abstract
  and record.)
* **Daniel & Moskowitz (2016):** momentum crashes cluster in panic states
  (after declines, high volatility) and are partly forecastable; a
  dynamic strategy built on forecasts of momentum's mean and variance
  roughly doubles its alpha and Sharpe ratio. (Abstract.)

## Against, and failure modes

* **Few states, many choices.** The lookback (12, 24, 36 months), the
  threshold and the volatility measure are all free; the CSV's own
  caveat is data mining. Treat any chosen filter as one of a family and
  deflate (C-ML4).
* **Contradicting evidence** exists: a 2006 EFMA paper reports results
  against the Cooper et al. prediction and points to disposition-prone
  investors instead.
* **The filter is late by construction** at turning points, the same lag
  as RK1.

## Fit with volatility-ai

The momentum book itself must be long-only (an ETF rotation, RK7/X3, or
a momentum ETF). The state filter is a regime map, which the repository
already builds causally (`natr_regime.calm_by_date`, the trend regimes),
and the project's own lesson L1 is that volatility-magnitude regimes
work where direction regimes do not.

## How to test it here

1. Give X3 a regime gate: hold the relative-strength pick only while a
   `--regime` map says risk-on, cash otherwise. `assign_defensive`
   already has this shape with a fixed lead; the change is to let the
   lead be X3's pick.
2. Compare three gates fixed in advance: none, NATR calm (N5), and
   36-month market return above zero. Report switches and drawdown.
3. Research-only alternative: test the same gates on the Ken French
   momentum factor, monthly, before building anything.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cooper, M. J., Gutierrez, R. C., Hameed, A. (2004). "Market States and
  Momentum." *Journal of Finance* 59(3), 1345–1365.
  <https://doi.org/10.1111/j.1540-6261.2004.00665.x>. Abstract and
  index records.
* Daniel, K., Moskowitz, T. (2016). "Momentum Crashes." *Journal of
  Financial Economics* 122(2), 221–247.
  <https://www.nber.org/papers/w20439>. Abstract.
* "Momentum, market states and investor behavior." EFMA 2006 symposium
  paper. Search-result summary only.
