# Order-Flow Imbalance (OFI) Cross-Sectional Alpha Predictor

**Ledger ID RK252** · rank 252 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market microstructure / Alpha generation |
| Potential effectiveness rank | 252 (1 = strongest) |
| AI implementability rank | 321 (1 = easiest) |
| Retail advantage rank | 10,483 (1 = strongest) |
| Fit with this project | 🧪 single-instrument OFI (C-MS1) as a possible buy gate · ⛔ cross-sectional model |
| Implemented in volatility-ai | **Partial.** Single-instrument order-flow imbalance (`microstructure.ofi`, `ofi_events`; ledger C-MS1; needs L1 quotes); no cross-sectional model. Deferred: needs Level 1 quotes from Fidelity ([engine/roadmap.md](../../engine/roadmap.md) item 3). |
| Related ledger entries | C-MS1, C-MS2, RK275 |

## In one paragraph

Order-flow imbalance (OFI) nets the changes in bid and ask queue sizes
at the best quotes. Over short intervals it explains most price changes,
linearly, with a slope inversely proportional to depth, in 50 NYSE
stocks. Multi-level and cross-asset versions extend it. As alpha it
lasts seconds and needs live L1/L2 data.

## The rule

```text
e_n = 1{b_n >= b_(n-1)} q^b_n - 1{b_n <= b_(n-1)} q^b_(n-1) - 1{a_n <= a_(n-1)} q^a_n + 1{a_n >= a_(n-1)} q^a_(n-1)
OFI over [t, t + dt] = sum e_n; dP ~ beta x OFI / depth
```

## Evidence

* **Cont, Kukanov & Stoikov (2014), "The Price Impact of Order Book
  Events," *Journal of Financial Econometrics* 12(1), 47–88:**
  short-interval price changes are mainly driven by OFI at the best
  quotes; linear, slope inversely proportional to depth; robust across
  50 NYSE stocks, time scales and seasonality. (Abstract.)

## Against, and failure modes

* Heavy data and compute for multi-level, multi-stock OFI (the CSV's
  caveat); the forecast horizon is seconds.

## Fit with volatility-ai

A sell-side OFI burst on TQQQ or QQQ could pause grid buys for a minute,
and the live loop has a quote stream (Alpaca, Fidelity). But the
warehouse holds minute bars only; no historical quotes, trades or depth.
So it cannot be backtested here first.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cont, R., Kukanov, A., Stoikov, S. (2014). *Journal of Financial
  Econometrics* 12(1), 47–88. <https://arxiv.org/abs/1011.6402>.
  Abstract.
* This repository: `research/strategies/microstructure.py` (`ofi`,
  `ofi_events`), ledger C-MS1.
