# Ultimate-RSP

A strategy for RSP (equal-weight S&P 500), designed from scratch using what
every algorithm in this project's ledger and catalog taught about this
instrument. It is not derived from the Ultimate algorithm
(`ultimate-algorithm.md`), which is a leveraged-ETF design. The strategy
is `research/strategies/ultimate_rsp_sizing.py`, registered as
`ultimate_rsp`, with the recommended configuration in
`config/ultimate_rsp.yaml`.

## Goal and constraints

- **Objective.** plan.md's RSP bar: beat buy-and-hold's return/drawdown
  (0.31), or cut max drawdown by at least 10 points for at most 1 point
  of CAGR, keeping CAGR at or above 11%. The Ultimate brief adds two
  aims: succeed as an intraday strategy, and hold up in downturns.
- **Loss policy (owner).** Long only, RSP only. A lot may be sold below
  cost only through a signal exit (`lots_to_liquidate` with
  `execution.allow_signal_exit`). No price stops and no end-of-day
  flatten.
- **Data.** RSP regular-session minute bars from 2016-01-04 to
  2026-08-28. Results are scored from 2017-01-03, after the warm-up.

## What the review of every algorithm said about RSP

Each family in `docs/algorithm_ledger.md` and the catalog was checked
against RSP, using its recorded evidence or a measurement made here.

| Component (ledger IDs) | Evidence on RSP | Verdict |
|---|---|---|
| Accumulation grids: V1–V5, C-G2–C-G6 | The grid lost to holding RSP in every measurement (plan.md). The RSP champion makes 9.8% CAGR at a 20.8% drawdown, against buy-and-hold's 12.0% at 39.1%. | Not the core |
| Regime-gated grid, liquidate on flip: V15–V17, N5–N7, Ultimate | plan.md Stage 3: PLUS_DM-gated grid −0.19% CAGR (37,407 signal exits); hold-through 40% DD. exp19: the Ultimate with RSP's own regime, Calmar 0.04–0.17. A small-lot grid cannot re-enter after an exit. | Rejected |
| Long/cash timing on volatility-like indicators: V15 Stages 1–2 | PLUS_DM-below and ADOSC-below were the only ridges, holding buy-and-hold's return at a third of its drawdown in a shell. They failed inside the grid. | **The core**, built to survive the engine |
| Volatility targeting: V18, S4, C-S4 | plan.md: cut DD 54%, but the edge sat in Feb–Jun 2020. A4: on top of the core it lowered Calmar in every case. | Not used |
| Trend and drawdown filters: V16, S2, C-E2 | A1: close > SMA 50/100/200, TSMOM and drawdown filters, Calmar 0.23–0.47 | Not used |
| Market volatility regime: L15, QQQ NATR | A5: as a third vote it cuts DD to ~8.5% in-sample, consistently across its family. A6: no gain out of sample (median Calmar 0.91 with or without it), at 2–3 points less CAGR. | Not used (recorded as an option) |
| Short-term mean reversion: C-MR1, Connors RSI(2), IBS, N-day lows, X4 | A2: Calmar ≤ 0.51 standalone, 10–30% time in market. B2: a capitulation-close layer adds ≤ 0.6 points of CAGR but lifts DD to 13–26% (COVID). | Rejected |
| Regime debounce: N10 | A4: holding 2–5 sessions cuts CAGR and deepens drawdowns. The edge is short-lived. | Not used |
| Intraday timing: X1, C-M1, Ultimate L13 (delayed exit) | A4 and B3: executing at +30 to +120 minutes is a plateau; at the open it is the worst choice (Calmar 0.59 in the engine, the open's slippage). | Execute at +60 |
| Drawdown throttle, event and volume scaling: V6–V9, V11 | These size grid lots. There are no grid lots here. | Not applicable |
| ML sizing and regimes: V13, V14 | RSP's models are weak (held-out AUC 0.54–0.60) | Not used |
| Turbulence index, HMM / Markov regimes, LPPLS: A2, C-R3, A3 | Not measured here: heavier signals, open follow-ups | Future work |
| Rotation, inverse, options, volatility ETFs: X2, X3, X5–X8, S1 | A single-instrument strategy, or out of scope. Idle cash earns the engine's historical cash yield (≈ T-bills). | Out of scope |

## The design

**Not a grid: a daily-timed exposure book.** The book holds a target
fraction of equity in RSP and resets it once per session.

```
target(D+1) = ½ × share of PD votes "in" + ½ × share of AD votes "in"

PD votes: PLUS_DM(p) < its trailing median over lb sessions, p ∈ {14, 21, 42}, lb ∈ {100, 250}
AD votes: ADOSC(f/s) < its trailing median over lb sessions, f/s ∈ {3/10, 5/20, 10/40}, lb ∈ {100, 250}
```

The target is decided from sessions up to and including the close of D.
A vote whose median is not yet defined counts as out.

- **PLUS_DM in price units is an upside-volatility measure.**
  Normalised by ATR (PLUS_DI), its protection vanishes (Calmar 0.25).
  Normalised by price, the protection survives. The vote is "in" during
  calm tape and in the quiet after a sell-off, which is how it caught
  2022's reversal days (+4.5% on 2022-10-13).
- **ADOSC below its median means distribution.** This vote is contrarian
  on money flow.
- **The two families are uncorrelated on RSP.** For the central pair
  (PD21/100, AD10-40/250) the correlation is −0.03: both are "in" 25% of
  the time, only PD 28%, only AD 24%. Averaging them is steadier
  than either: PD alone gives Calmar 0.75 and AD alone 0.87 in the
  engine, against 0.94 for the average.
- **The parameters are averaged, not chosen.** A walk-forward put the
  rank correlation between in-sample and out-of-sample performance at
  0.16 across the 36 PD × AD pairs. Choosing one pair is noise.

**Execution.** At the first bar at or after minute 60, the book moves to
the target if it is more than 5% of equity away:

- **Buying:** one lot for the shortfall, filled at that bar's open.
- **Selling:** a signal exit of whole lots, newest first, worth about the
  excess.

The signal exit is the only sale that may realise a loss. Lots otherwise
carry an out-of-reach profit target, because the book holds rather than
harvests.

## Results (research lab, real engine)

Intrabar causal fills, dynamic slippage, the engine's historical cash
yield, RSP 2017-01 → 2026-08:

| Book | CAGR | Max DD | Calmar | Sharpe | 2018 | 2020 | 2022 |
|---|---|---|---|---|---|---|---|
| Buy and hold | 12.0% | 39.1% | 0.31 | 0.70 | −7.8% | +12.6% | −11.6% |
| RSP champion grid (always in) | 9.8% | 20.8% | 0.47 | 0.85 | −7.7% | +9.0% | −8.8% |
| Ultimate, TQQQ's regime, best (exp19) | 5.6% | 11.0% | 0.51 | 0.93 | +2.0% | +17.5% | +1.0% |
| **Ultimate-RSP (recommended)** | **11.2%** | **11.9%** | **0.94** | **1.12** | **−1.2%** | **+12.6%** | **+10.2%** |
| Best in-sample pair (PD21/100 + AD10-40/250) | 14.0% | 12.4% | 1.13 | 1.35 | +0.4% | +16.9% | +23.3% |

Ultimate-RSP year by year:

| 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to Aug) |
|---|---|---|---|---|---|---|---|---|---|
| 12.4% | −1.2% | 10.7% | 12.6% | 24.7% | 10.2% | 3.8% | 9.6% | 15.6% | 10.7% |

- **It meets plan.md's RSP bar.** The drawdown falls 27 points for 0.85
  points of CAGR, and CAGR stays above 11%.
- **Every era's drawdown is at most 11.8%,** against buy-and-hold's
  18–39%.
- **Downturns.** Across the 12 QQQ corrections of 10% or more, the mean
  return is −2.0% and the worst −9.6%, against buy-and-hold's −9.0% and
  −32.9%. The 2021-11 → 2022-11 bear market returned +19.8% for the pair
  form against buy-and-hold's −13.5%.
- **Activity.** 73% of months are positive. The book makes about 155
  trades a year, all rebalances at minute 60, and is in the market
  about half the time.

## Validation

- **Engine against shell.** The engine gives 11.15% / 11.85% / 0.94
  against the shell's 11.00% / 11.87% / 0.93. Injecting the shell's
  exposure map reproduces the internal computation trade for trade
  (749 buys, 745 sells). This is the step where plan.md's grid version
  failed.
- **Walk-forward** (choose on 2017–21, score on 2022–26):
  - Out of sample, every two-vote pair beats buy-and-hold's Calmar of
    0.40. The median is 0.91 and the worst 0.61.
  - The in-sample pick scores 11.3% / 11.8% / 0.96.
  - The ensemble scores 0.94 with no selection at all.
- **Halves and COVID.** 2017–21 gives 11.6% / 11.8%, and 2022–26 gives
  10.7% / 11.3%. Without Feb–Jun 2020 the result is 10.9% / 11.3%.
- **Deflated Sharpe ratio** (N = 1,400 screened configurations, Sharpe
  dispersion across 578 recorded trials): **0.88**. It is 0.93 at
  N = 400.
- **PBO by CSCV** (10 groups): 0.03 over the 36 two-vote pairs plus the
  ensemble, and 0.13 over the three-vote family.
- **Stress tests, one change at a time** (exp B3), against the
  recommended Calmar of 0.94:

  | Change | Calmar |
  |---|---|
  | Execute at minute 30 / 90 / 120 | 0.90 / 0.94 / 0.92 |
  | Execute at the open (minute 0) | **0.59** |
  | Rebalance band 0.03 / 0.10 | 0.94 / 0.91 |
  | Costs ×2 / ×4 / ×10 | 0.90 / 0.83 / 0.61 |
  | Level / close-only fills | 0.91 / 0.94 |
  | No cash yield | 0.87 |
  | Exposure capped at 80% | 0.99 (9.9% / 10.1%) |
  | PD weight 0.3 / 0.7 | 0.97 / 0.89 |

## Caveats

- **The two families were found on this same data.** plan.md's 2026-09
  indicator sweep named PLUS_DM and ADOSC as RSP's ridges. This work
  re-screened a wider space on the same years. The robustness is at the
  family level (most parameter settings work, both halves, without
  COVID, a deflated Sharpe of 0.88), but no data was held back from
  discovery.
- **PD's best years rest on a few reversal days.** In 2022, eight days
  made nearly all of the PLUS_DM signal's gain on its own (+33.8% in a
  year RSP fell 11.6%). The ensemble's 2022 (+10.2%)
  is far less lucky than the pair's (+23.3%), which is one reason to
  prefer it.
- **It realises losses often, by design.** All 745 sales are signal
  exits, so this is a timing strategy rather than the no-loss grid this
  project started from. It fits the owner's loss policy because every
  exit is a signal exit. It never uses a price stop.
- **It lags buy-and-hold in strong years** (2019: +10.7% against +28.9%).
  The payoff is the drawdown, not extra return.
- **Server runs are not the research runs.** `RunRequest` has no cost
  model (server runs are zero-cost) and no intrabar-fill field (server
  runs use level fills; B3: Calmar 0.91).
- **The live loop does not warm up yet.** A `cli.py live` start would
  wait about 300 sessions for its medians. Wiring it needs
  regular-session daily OHLCV from the `engine/data` feed (the same gap
  as the Ultimate's).

## Integration

- **Registered as `ultimate_rsp`.** The constructor takes plain scalars
  only (comma-separated lists as strings), so the server's run form
  renders every field.
- **No TA-Lib at run time.** PLUS_DM and ADOSC are updated one session
  at a time with TA-Lib's own recursions, in plain numpy. The live loop
  loads the strategy registry and must start without the optional
  indicator libraries (requirements-indicators.txt). A first version
  imported TA-Lib and broke exactly that, which the `cli.py live` tests
  caught. Tests pin both indicators to TA-Lib value for value.
- **Server.**
  - `STRATEGY_DEFAULTS["ultimate_rsp"]` holds the recommended
    configuration.
  - `exposure_by_date` is hidden.
  - The locked trigger method is `exposure_target`.
  - `SIGNAL_EXIT_STRATEGIES` includes the id.
  - `warm_up_history` now carries volume, which this strategy's ADOSC
    needs.
- **Web.** The `exposure_target` label and help text.
- **Tests:** `research/tests/test_ultimate_rsp_sizing.py`.
  - The bar-by-bar target matches an independent pandas/TA-Lib
    computation, and warm-up matches replaying the bars.
  - Rebalances happen once per session at the minute, in whole lots.
  - In the engine, the internal target trades exactly like the injected
    map, the exit needs the flag, and every fill model books buys inside
    the bar.
  - The registration, server wiring and pinned config are covered.

## Experiment log

Stage A screens in a daily long/cash shell (`shell.py` in the research
scratchpad). It is causal: the close of D decides D+1, executed at a
chosen time of D+1 with 2 bps per side and the engine's cash yield.
Stage B runs the real engine.

| Exp | Question | Result |
|---|---|---|
| A1 | Every single regime signal (71): NATR, realized vol, PLUS_DM, ADOSC, SMA, TSMOM and drawdown, on RSP and QQQ | Only PLUS_DM (median Calmar 0.66, 5/8 settings good) and ADOSC (0.61, 4/6) are robust, as plan.md found. Trend and drawdown filters 0.23–0.47, RSP's own NATR and RV 0.25–0.32, QQQ NATR 0.42. Buy-and-hold 0.31. |
| A2 | Mean-reversion rules with hysteresis (54: RSI(2), IBS, N-day lows, down streaks, MFI) and normalised PD/AD (28) | PD's protection is its volatility content: /ATR 0.22–0.25, /price 0.62. Mean reversion ≤ 0.51 standalone. |
| A3 | PD × AD: AND / OR / AVG over all 144 pairs each | AVG is the most robust (median Calmar 0.76). OR has the highest returns but leans on 2020 (+61%). AND holds too little exposure. |
| A4 | Execution time, debounce, vol targeting and costs on 7 finalists | Execute at +30 to +60. No debounce. Vol targeting lowers Calmar everywhere. The slow forms stay robust to 10 bps. |
| A5 | Ridge surface of 36 averaged pairs; ~150 candidate third votes | A ridge: median 0.86, minimum 0.68, 78% of pairs ≥ 0.8. A QQQ-NATR third vote cuts DD to ~8.5% (Calmar 1.36–1.46, the whole family). PD and AD are uncorrelated. |
| A6 | Walk-forward selection for the two- and three-vote families | Two votes: the pick scores 0.96 out of sample, the median 0.91. Three votes: also a median of 0.91, but at lower CAGR. Rank correlation 0.16, so the parameters are averaged rather than chosen. |
| A7 | Parameter ensemble; asymmetric entry and exit timing | Ensemble 11.0% / 11.9% / 0.93, out of sample 0.94. Asymmetric timing is a plateau (0.87–0.93). |
| B1 | Engine against shell; internal target against injected map | 11.15% / 11.85% / 0.94 against 11.00% / 11.87% / 0.93. The internal and injected runs are identical. |
| B2 | A capitulation-close layer: −2/−3/−4% × +1/+2/+3%, on the ensemble and the pair | Rejected. At most +0.6 points of CAGR, with DD at 13–26%. Neutral at −4%. |
| B3 | Stress and sensitivity, one change at a time (19 runs) | Robust, apart from executing at the open. See Validation. |
| B4 | Deflated Sharpe ratio, PBO and eras | DSR 0.88 (N = 1,400). PBO 0.03 and 0.13. Every era's drawdown ≤ 11.8%. |
