# Ultimate-URSP

A strategy for URSP, the ProShares Ultra S&P 500 Equal Weight fund: 2× the
daily performance of the S&P 500 Equal Weight Index, reset daily, trading
since 2025-08-27.

- **Strategy:** `research/strategies/ultimate_ursp_sizing.py`, registered
  as `ultimate_ursp`, with the recommended configuration in
  `config/ultimate_ursp.yaml`.
- **Simulated history:** built by `tools/simulate_ursp.py`, because the
  real fund is barely a year old.
- **Lineage:** it extends [Ultimate-RSP](ultimate-rsp.md) with the one
  lesson Ultimate-RSP's 2017–2026 record could not teach: a leveraged
  book must leave a prolonged bear market.

## The simulated URSP

**The formula.** RSP has tracked the same index since 2003. Each session
*t*, with *d* calendar days since the previous session:

```
index_t = RSP total return_t + 0.20% × d/365          (RSP's fee added back)
URSP_t  = 2 × index_t − (DFF_t + spread) × d/360       (financing the borrowed 1×)
                      − 0.95% × d/365                  (URSP's net expense ratio)
```

- **Intraday prices.** Open, high and low follow the same daily-reset
  rule relative to the previous close. That map is increasing, so RSP's
  high becomes URSP's high.
- **Spread calibration.** The spread (2.09%/yr over fed funds) is set so
  the simulated total return over the real fund's first 278 sessions
  equals its actual total return. It is close to RSP's dividend yield
  plus a small swap spread, consistent with swaps that pay the index's
  price return.
- **Splice.** The simulated history is back-cast from the real fund's
  first close (2025-08-27), and the real bars follow. Simulated volume is
  RSP's volume scaled to URSP's level, so volume-based signals do not jump
  at the splice.

**Bad prints.** Two RSP prints are clipped before doubling: the
2010-05-06 Flash Crash low of −58%, from trades that were later
cancelled, and a stray 2007-08-01 high. The rule clips any extreme more
than 6% beyond the day's open, close and prior close. At 5% it would also
clip genuine October 2008 and March 2020 reversals.

**Minute bars.** The engine needs minute bars.
- **2016–2026:** on each session the warehouse holds RSP minutes for,
  the URSP day is that same day's RSP path mapped onto the URSP day's
  OHLC. That is the fund's actual intraday relationship.
- **Other sessions (mostly 2003–2015):** the URSP day borrows the shape of
  the most similar RSP day. This is the method validated on TQQQ, where
  it reproduced CAGR and overstated drawdowns slightly.
- **Exactness:** daily OHLC is exact in both cases.

**Validation.**

| Check | Result |
|---|---|
| Yahoo RSP against the warehouse's RSP (2016+) | daily correlation 0.997 |
| Simulated against actual URSP (278 sessions) | daily correlation 0.955, tracking error 6.9%/yr |
| Buy and hold, 2003–2026 | simulated URSP 13.5% CAGR at an 88.5% max DD; RSP 11.1% at 59.9% |
| Calendar years | simulated URSP 2008 −71.5%, 2022 −29.0% |

The real fund's thin trading (below) explains most of the tracking
error: its last trade is often not at the close, and its intraday ranges
are narrower than 2× RSP's.

## The design, from the evidence

Every candidate was screened on simulated URSP from 2004-07 to 2026-10 in
a daily long/cash shell: decided at the close, executed at +60 minutes,
with the engine's cash yield.

| Design | CAGR | Max DD | Calmar | GFC | COVID | 2022 |
|---|---|---|---|---|---|---|
| Buy & hold URSP | 11.2% | 88.5% | 0.13 | −88% | −66% | −40% |
| Ultimate-RSP's timing core on URSP | 14.1% | 68.7% | 0.21 | −66% | −28% | +2% |
| The TQQQ Ultimate's NATR regime | 2.3% | 43.4% | 0.05 | −34% | 0% | −11% |
| Core + single bear filter (out below 50% of the 1-yr high) | 14.3% | 29.0% | 0.49 | −21% | −18% | +2% |
| Core + trend filter (close > SMA 200) | 6.3% | 25.8% | 0.25 | −1% | −10% | −10% |
| Core + 30% vol target | 11.2% | 38.6% | 0.29 | −34% | −18% | 0% |
| **Core × graded bear gate (25% → 55%)** | **11.9%** | **28.7%** | **0.41** | **−22%** | **−18%** | **−1%** |

- **Ultimate-RSP's votes stay "in" through much of 2008.** Its record
  (2017–2026) held no prolonged bear market. On a 2× fund the GFC costs
  66%.
- **A single drawdown threshold is a spike, not a ridge.** Neighbouring
  settings range from 0.15 to 0.49. 2008 is one event, and the result
  depends on the day the threshold fires.
- **Trend filters dodge 2008 but whipsaw after 2015.** Their 2015–2026
  CAGR is below 5%.
- **The graded gate is a ridge.** It scales exposure linearly from 100%
  at a 25% drawdown from the 250-session high to 0% at 55%. Calmar is
  0.30–0.41 across 30 settings (start 15–35% × end 45–70%), with a median
  of 0.38. The design uses the centre of the best column.
- **The TQQQ Ultimate's own regime does not suit an equal-weight 2×
  fund.**

**The strategy:** target = Ultimate-RSP's averaged PLUS_DM / ADOSC votes
× the graded bear gate, both read at the previous close and computed from
URSP's own bars. It is reached an hour into the session in whole lots,
with signal exits. It moves only when the target is more than 20% of
equity away (Ultimate-RSP uses 5%), because URSP is thin.

## Results (research lab, real engine)

Simulated URSP, 2004-07 → 2026-10: intrabar causal fills, dynamic
slippage, the engine's cash yield.

| | CAGR | Max DD | Calmar | Sharpe | 2008 | 2022 |
|---|---|---|---|---|---|---|
| **Ultimate-URSP** | **11.7%** | **28.0%** | **0.42** | **0.72** | **−16.4%** | **+11.7%** |
| Buy & hold URSP | 11.2% | 88.5% | 0.13 | 0.47 | −71.5% | −29.0% |
| Buy & hold RSP | 10.1% | 59.9% | 0.17 | 0.58 | −40.1% | −11.6% |
| Ultimate-RSP book on URSP, no gate | 13.9% | 68.9% | 0.20 | 0.65 | | |

**Eras (CAGR / max DD), Ultimate-URSP against buy-and-hold URSP:**

| Era | Ultimate-URSP | Buy & hold URSP |
|---|---|---|
| 2004–2009 | 4.5% / 28.0% | −5.1% / 88.5% |
| 2010–2014 | 21.1% / 23.4% | 28.1% / 43.5% |
| 2015–2019 | 7.6% / 21.3% | 13.2% / 37.3% |
| 2020–2026 | 13.8% / 22.6% | 11.9% / 65.6% |

- **Years.** Only 3 of 23 calendar years are negative (2008 −16%, 2015
  −5%, 2018 −2%).
- **Downturns.** Across RSP's 8 corrections of 10% or more, the mean is
  −16% and the worst −27%, against buy-and-hold URSP's −46% and −88%.
- **Since the real fund launched** (2025-08-27 on): +16.9% at an 8.9%
  drawdown.

## Validation

- **Engine against shell.** The engine gives 11.6% / 29.8% at the 5% band,
  against the shell's 11.9% / 28.7%. Injecting the shell's target map
  reproduces the internal computation trade for trade (1,638 buys).
- **Walk-forward** (choose on 2004–14, score on 2015–26): the gate
  surface's out-of-sample Calmar has a median of 0.46 and a minimum of
  0.33. The core alone scores 0.47 out of sample, because there was no
  catastrophic bear market to insure against.
- **Halves.** 2004–14 gives 12.4% / 28.0%, and 2015–26 gives 11.0% /
  22.6%.
- **Stress tests** at the 5% band, one change at a time, against a
  Calmar of 0.39:

  | Change | Calmar |
  |---|---|
  | Execute at minute 30 / 120 | 0.36 / 0.45 |
  | Level / close-only fills | 0.36 / 0.39 |
  | No cash yield | 0.35 |
  | Gate 20→50% / 30→60% | 0.37 / 0.42 |
  | Bear window 125 / 500 | 0.34 / 0.33 |
  | Exposure capped at 75% | 0.36 |

- **Costs are the real risk.** At ×2 / ×4 / ×10 the model's costs, the
  5% band falls to 10.8% / 9.4% / 5.4% CAGR. The 20% band holds 11.7% /
  10.6% / 8.1%, which is why it is the default.
- **Deflated Sharpe ratio:** 0.42 at N = 1,500, 0.58 at N = 400, using the
  RSP study's cross-trial dispersion, since the timing core came from
  that search. It is not significant. PBO over the gate family is 0.65:
  picking among gate variants is noise, which is why the centre of the
  ridge was used rather than its best cell. The proven gain is the
  drawdown, not the Sharpe.

## Caveats

- **Most of the record is simulated.** The formula's financing spread is
  calibrated on one year of a thinly traded fund. Rates in 2003–2008 were
  higher, and so was the drag, which the formula includes.
- **URSP is thin.** It trades a median of ~12,000 shares (~$0.5M) a day,
  with 67 of 278 sessions below 5,000 shares. Its spread is likely several
  times the engine's cost model. Use limit orders and small size relative
  to its volume.
- **The bear gate's value rests on 2008.** It is insurance: it costs a
  little in quiet decades and is decisive in a prolonged bear market.
- **ADOSC on the real fund's volume is noisy.** After the splice, the
  ADOSC votes read URSP's own thin, erratic volume. Computing the votes
  from RSP would be cleaner, but a single-instrument strategy cannot see
  RSP.
- **Live warm-up and server costs.** The live warm-up is not wired (as
  for the other Ultimates), and server runs are zero-cost.

## Using it

```
python tools/simulate_ursp.py --minutes
python tools/build_warehouse.py --ingest URSP_SIM --csv data/simulated/URSP_simulated_1Min.csv
```

After that, select `ultimate_ursp` with the URSP_SIM ticker in the
backtest form, or run `config/ultimate_ursp.yaml`.

## Experiment log

| Exp | Question | Result |
|---|---|---|
| D1 | Build and calibrate the simulated URSP | 2× RSP total return with the costs above. Spread 2.09% calibrated on 278 real sessions. Two bad prints clipped. Spliced on 2025-08-27. |
| D2 | Minute bars | 2,299,050 bars: same-day RSP shapes for 2,677 sessions, borrowed shapes for 3,215. Daily OHLC exact. |
| A1 | 19 designs | The RSP core alone fails the GFC (−66%). A single 50% bear filter gives 0.49. The TQQQ regime does not fit. |
| A2 | Single-threshold surface, trend filters, vol target, timing, walk-forward | Spiky surface (0.15–0.49). SMA filters whipsaw. Vol targeting and timing make little difference. Out of sample, the median equals the core's. |
| A3 | Graded gates (family average, linear ramp) | The linear ramp is a ridge (0.30–0.41, median 0.38). Centre chosen: 25% → 55%. |
| B1 | Engine against shell; internal against injected | Agree; identical trades. |
| B2 | Stress tests, eras, annual | Robust except to costs. |
| B3 | Deflated Sharpe, PBO | DSR 0.42 (N = 1,500). PBO 0.65 within the gate family. |
| B4 | Rebalance band against costs | The 20% band is best at ×4–×10 costs and equal at ×1. Adopted. |
