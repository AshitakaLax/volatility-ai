# The Ultimate Algorithm — design and research log

*Started 2026-10-03. A living document: every claim below is either a
measurement (with the experiment that produced it) or marked as a
hypothesis. Experiments run through the real engine
(`OptimizationController.run_sweep`, intrabar fill, causal booking,
historical cash yield) via the research lab in the session scratchpad.*

## Goal

Design for (1) the greatest success trading **intraday**, and (2)
**consistent gains during market downturns**, using the lessons of every
algorithm in [`docs/algorithm_ledger.md`](../algorithm_ledger.md).

**Constraints kept** (the owner's, from the ledger): long-only standard
stocks and ETFs (leveraged long ETFs allowed); no shorts, inverse ETFs,
options or volatility ETFs; a lot is sold below cost **only** through a
regime exit (`lots_to_liquidate` + `execution.allow_signal_exit`) — no
price stops, no end-of-day flatten.

**How "consistent gains in a downturn" is scored:** the book's return
over each QQQ correction of 10% or more, peak to trough — 13 windows in
the warehouse's data (2016-01 to 2026-08). The scoreboard is how many of
those windows the book ends positive, its mean and its worst, alongside
CAGR, max drawdown and calendar-year returns.

## Lessons learned (with evidence)

| # | Lesson | Evidence |
|---|---|---|
| L1 | **Regime on volatility magnitude, never on direction.** | Causal regimes gating the TQQQ grid, CAGR/maxDD: NATR 1.30–1.40; LPPLS 0.55–0.60; Awesome 0.56–0.63; MACD 0.12–0.26; PSAR 0.06–0.17; Heikin-Ashi −0.09–0.11 (step-down runs, 2026-10-03). Trend switches liquidate near lows and re-enter near highs. plan.md: "direction is hard; magnitude persists". |
| L2 | **The grid's edge is volatility harvesting; its risk is inventory.** Under the no-loss guard every lot bought in a decline needs a bigger recovery. | Champion TQQQ: 50.8% CAGR, 71.7% max DD (ledger batch). |
| L3 | **Entry gates are refinements, not the core.** | Ledger batch: N1–N4, X1, Q10 move CAGR by ±0.5pp on most funds; N2 trims TQQQ/SOXL drawdown 6–9pp for 1.5–2.3pp CAGR. |
| L4 | **Shrinking lots as drawdown deepens scales return and drawdown together** — it changes size, not shape. | V11 TQQQ: −10.6pp CAGR, −12.3pp DD; SOXL −17.5 / −11.5. |
| L5 | **The champion is a dip accumulator, not an intraday round-tripper.** `profit_target` is a fraction (`target = buy × (1 + 0.30)`): $20 lots on every 0.075% pullback, each held until +30%. | config/best_known_2026-08-24.yaml; engine/core/ledger.py. |
| L6 | **A causal NATR regime survives the lookahead fix.** | NATR(10) vs 100-day median, lag 1: stepdown 29.95% CAGR / 21.4% DD vs always-in champion 25.7% / 42.2% (same harness). The lookahead version read 38.6% / 26.7%. |
| L7 | **Every flip costs; debounce helps.** | plan.md: liquidation cost return in 146 of 147 paired runs. Min-hold 5: 138 → 94 flips, Calmar 1.32 → 1.40. |
| L8 | **The downturn loss is calm-sleeve RE-ENTRY inside bear markets, not a slow first exit.** | The causal regime turns turbulent 0–5 sessions after each QQQ peak (TQQQ only 1.4–8.9% down in 10 of 12). But it called 43% of 2022's sessions calm; the calm sleeve's regime exits realized −$164k in 2022 against +$93k of target profits (exp1). |
| L9 | **Harvesting needs size.** Champion-sized ($20) lots in the turbulent sleeve earn cents per round trip and do not move the book. | exp2: 40 small-target QQQ/TQQQ turbulent sleeves; none makes a correction window positive (0/12 each); capped ones leave the book within ~0.5pp of cash. |
| L11 | **The downturn edge that survives long-only is CAPITULATION reversal at the close.** After a turbulent session down hard, the next days bounce often enough that a limit sell slightly above a close-entry fills with high probability. | Offline, daily bars, causal regime: QQQ after a ≤ −2% turbulent session, +1% limit fills next day 59%, within 5 days 84%, within 20 days 95% (+0.5%: 82 / 93 / 98%); TQQQ after ≤ −6%, +3%: 58 / 81 / 92%. Worst-decile 5-day adverse excursion −8% (QQQ), −23% (TQQQ). Next-day mean close-to-close +0.45% (QQQ) / +1.26% (TQQQ) — the short-term reversal premium of C-MR1, strongest when volatility is high. Engine test: exp8. |
| L12 | **Filter calm RE-ENTRY with a bear-market condition** (price near its recent high, or above its long average). It removes the low-volatility stretches inside bear markets that L8 identified, without delaying the first exit. | exp5: Calmar 1.30 → 1.63–1.75, max DD 22.3% → 16.5%, 2022 −10.8% → −1.4% to +0.9%, CAGR −0.2 to −2.1pp. |
| L13 | **Capitulation-close reversal is consistent but capacity-limited.** It cannot carry a book alone; it is what the book does *inside* a detected downturn, on top of the cash yield. | exp8: 94–100% of trades exit at target, 9–11 of 12 corrections positive, but 51–132 trades in ten years. |
| L14 | **Never execute the regime exit at the flip session's open.** The flip follows a volatility spike, so that open is usually a panic gap that recovers intraday — the selling-side mirror of L11. Wait an hour, or sell at the close. | exp11: detection cost −8% to −10% → +1% to +3%; max DD 16.4% → 13.6%; Calmar 1.74 → 2.14. |
| L15 | **Take the volatility regime from the MARKET, not from the traded instrument.** A sector leveraged ETF's own NATR is noisy with idiosyncratic shocks; the Nasdaq-100's regime transfers. | exp13 vs exp15, SOXL: own regime Calmar 0.43–0.67 (no better than the champion's 0.57); market regime 1.06–1.16. |
| L16 | **It is a leveraged-ETF design.** Its payoff is sidestepping the catastrophic drawdowns of a leveraged fund; an unleveraged fund has no such drawdowns to sidestep, so gating it halves return and drawdown together. | exp17: Calmar on QQQ 0.72 → 1.13 but CAGR 10.4% → 4.5%; RSP/SPYD/COWZ roughly unchanged vs TQQQ 0.61 → 2.16. |
| L10 | **Even sized properly, long-only intraday harvesting in turbulent regimes does not beat the downside drift.** The fewer lots the sleeve buys, the better it does in corrections. Target decay cannot help a lot that is under water — the no-loss guard (rightly) blocks it. | exp4: 48 sized QQQ harvest sleeves ($200–$500 lots, 30–100 cap, steps 0.2–0.4%, targets 0.4–1.5%, ± decay): alone, 1.5–4.0% CAGR, 0–4 of 12 corrections positive, mean −0.3% to −5.2%. |

## Architecture (current, evidence-backed)

```
 Layer 0  REGIME (causal, debounced)                              L1, L6, L7, exp3
          NATR(10) vs its 100-session median on TQQQ, applied next session,
          min hold 5
          + BEAR FILTER on calm re-entry: price near its recent high,      L12, exp5
            or above its 200-session average
 Layer 1  CALM: the champion accumulation grid on TQQQ                     L5, exp6
          (fixed $ lots on every 0.075% local pullback, +30% targets)
 Layer 2  TURBULENT: no grid. CASH (earning the short rate) plus           L10, L11, L13
          CAPITULATION-CLOSE REVERSAL entries: in the last 10 minutes of     exp7, exp8
          a session down past a threshold, one event lot with a small
          profit target, a hard cap on open event lots
 Exits    profit targets through the no-loss guard; the calm sleeve is
          liquidated on the flip to turbulent (the one loss path, L6)
```

What the evidence says it delivers, and what it cannot:

* **Inside a detected downturn it makes money every time.** With cash
  plus the reversal sleeve, the book is positive in **47 of 47**
  detected turbulent spells (worst 0.00%), against 42 of 47 for the old
  step-down's QQQ grid (worst −4.95%). This is the "consistent gains
  during a downturn" a long-only book can deliver.
* **It cannot avoid the first leg.** No causal volatility regime knows a
  correction has started until it has: the flips cost about −10%
  compounded over 47 flips in ten years (the *detection* cost), so the
  book still loses, mostly a little, from each QQQ peak to its trough.
  Experiment 11 attacks that cost (when and how much to liquidate).

Scoring now also reports, per book, the **in-spell** return (from the
close of a turbulent spell's first session to its last) and the
**detection** return (the close before the spell to the close of its
first session), via `lab.spell_stats`.

New code: `research/strategies/natr_regime.IncrementalNatrRegime` — the
causal NATR regime (with optional bear filters) computed bar by bar,
matching `calm_by_date(lag=1)` + `debounce` date for date (tested), so a
deployed strategy can carry its own regime. And
`research/strategies/harvest_sleeve_sizing.py` —
RegimeSleeveSizing plus inventory decay (C-S4), inventory skew (C-G2),
volatility-scaled step (C-G3), profit-only target decay (C-X2), and the
noise-area (C-M1), VWAP (C-MS3) and session-throttle (C-X4) gates, and a
close-reversal entry mode (buy only in the last minutes of a session down
past a threshold, one lot per session, decided causally); all off by
default, where it reproduces RegimeSleeveSizing exactly (tested).

## Recommended configuration (deployable, one strategy on TQQQ)

`research/strategies/ultimate_sizing.UltimateSizing`, chosen for
robustness over the top cell (PBO, below):

| Layer | Setting |
|---|---|
| Calm grid | the champion: `config/best_known_2026-08-24.yaml` (step 0.075%, target +30%, $ lots of 0.02% of capital) |
| Regime | NATR(10) vs its 100-session median, lag 1, `regime_min_hold=5` |
| Bear filter | `bear_dd=0.5, bear_window=250` (calm only within 50% of the 1-year high) |
| Regime exit | `liquidate_minute=60` (an hour into the flip session) |
| Turbulent | `turbulent_mode="reversal"`, `reversal_threshold=-0.09`, `reversal_target=0.06`, `reversal_lot_pct=0.2`, `reversal_max_lots=4`, last 10 minutes |

Measured (engine, intrabar causal fills, historical cash yield,
2016-12 → 2026-08): **29.7% CAGR, 13.7% max DD, Calmar 2.16, Sharpe
1.66; every detected downturn positive (42/42).** By calendar year
(return / intra-year max DD): 2017 +43.0 / 13.7 · 2018 **+32.7** / 13.7
(TQQQ −19.6) · 2019 +93.2 / 8.3 · 2020 +65.3 / 13.1 · 2021 +16.4 / 9.1 ·
2022 **−1.5 / 3.5** (TQQQ −79) · 2023 +25.5 / 3.1 · 2024 +15.8 / 3.7 ·
2025 +16.6 / 3.7 · 2026 YTD +4.1 / 3.3.

**Stress test (exp16):** slippage ×2 / ×4 / ×10 → Calmar 2.08 / 1.90 / 1.81;
level or close-only fills 2.05 / 1.96; no cash yield 2.05; every
parameter on a plateau except two limits — keep the bear window long
(≥ 250 sessions) and the reversal threshold at −8% or deeper.

**Caveats, stated plainly:**

* The deflated Sharpe ratio is 0.63–0.70 over 556 trials: the Sharpe
  *uplift* is not significant at 95%. The robust gains are drawdown
  (42% → 14%) and downturn behaviour.
* PBO 0.76 within the 30-variant deployable family: the top variant is
  not distinguishable from its siblings; every bear-filtered,
  delayed-exit variant sits at Calmar 1.9–2.2.
* The bear filter was found by studying 2022 and most of its benefit is
  in that one episode. The rule form is a standard one (drawdown from the
  high / long moving average), but on this data it rests on one bear
  market. The delayed exit (all 47 flips) and the reversal sleeve (~55
  trades, ~95% hit rate) are broad-based.
* On another instrument the regime must be the market's (L15): SOXL with
  its own NATR regime gains nothing (exp13), with TQQQ's regime its
  Calmar doubles (exp15). The single-symbol engine cannot see a second
  ticker's bars, so for SOXL the market regime is injected
  (`regime_by_date`) or fed from a market-data job.
* "Consistent gains in a downturn" means inside a *detected* downturn.
  No causal volatility regime avoids the first leg of a correction; from
  each QQQ peak to its trough the book still usually loses a little.

## Integration (registered as `ultimate`)

* **Registered** in `strategy_registry.py` as `ultimate`. The
  constructor spells out every `GatedLocalReferenceSizing` argument (the
  server builds its run form from `inspect.signature` and skips
  `**kwargs`); tests pin that every parent argument is mirrored with the
  same default and passed through. Its defaults are the recommended
  configuration above.
* **Server** (`server/backtest.py`): `STRATEGY_DEFAULTS["ultimate"]` is
  the champion's full committed set plus the recommended Ultimate values;
  `turbulent_mode` is a dropdown; `regime_by_date` is hidden; the grid
  trigger is its own locked method, `regime_switched` (local_reference
  over `lookback_days` while calm, only the reversal level while
  turbulent), with the window still editable in the form.
* **The regime exit is on for server runs.** `SIGNAL_EXIT_STRATEGIES`
  makes `build_config` set `execution.allow_signal_exit` for this id;
  without it the calm lots ride the downturn and the run is a different,
  unresearched strategy. A loss needs the flag *and* `lots_to_liquidate`,
  so the flag changes nothing for any other strategy.
  `BacktestConfig.to_run_sweep_kwargs` also used to drop
  `allow_signal_exit` (and `settlement_days`), so a YAML that set it ran
  without it; both pass through now.
* **Warm-up.** The internal regime flags nothing until
  max(250, 5 × natr_period, natr_lookback) sessions have completed, and
  the strategy buys nothing while the regime is unknown.
  `UltimateSizing.warm_up(daily)` (→ `IncrementalNatrRegime.warm_up`)
  seeds it from session OHLC; tests show it gives the same flag on every
  later bar as replaying the minute bars, including a partial last
  session. `run_sweep(warm_up_daily=...)` hands that history to each
  combination's strategy, and the server passes the sessions its
  date window cut off, so a window starting in 2022 trades 2022 on the
  full-history regime instead of sitting idle (tested: identical to
  injecting the full-history causal map). The row records
  `warm_up_sessions`, which keeps warmed and cold runs apart in the
  warehouse identity.
* **`config/ultimate_tqqq.yaml`** pins the recommended configuration
  (intrabar causal fills, `allow_signal_exit: true`), and is tested equal
  to the server defaults. A `cli.py backtest` of it covers the whole file
  with no warm-up, like the research runs: the first ~250 sessions are
  idle.

### Not done yet

* **Live warm-up.** `cli.py`'s `_run_trading_loop` constructs the
  strategy with no history, so a live start would carry no regime flag,
  and buy nothing, for about a year. The wiring is one call,
  `strategy.warm_up(daily)` after construction, but it needs ~400
  sessions of *regular-session* daily OHLC from the live market-data
  feed (`engine/data/alpaca_market_data.py`). Vendor daily bars can
  include extended hours, so building them from regular-session minute
  bars is the safe source. The live loop already honours
  `execution.allow_signal_exit` and per-lot retargeting
  (`decision_cycle`), which this strategy needs.
* **Other instruments** need the market's regime (L15), which a
  single-symbol strategy cannot compute from its own bars: inject it
  (`regime_by_date`, research path only).
* **Server runs are not the research runs.** `RunRequest` has no cost
  model (server runs are zero-cost) or intrabar-fill field (server runs
  use level fills; exp16: Calmar 2.05 against causal's 2.16).
* **Cash yield** is the historical short rate in every result above;
  without it Calmar falls from 2.16 to 2.05 (exp16).

## Walk-forward selection check

Choosing among the 155 deployable TQQQ variants using **2017–2021 only**
selects the 1-year filter, exit +120 min, reversal −9% / +6% / 20%
(in-sample Calmar 3.81). **On the unseen 2022–2026 data it returns 12.8%
CAGR with a 4.3% max DD — Calmar 2.95, 11th of 155.** In-sample and
out-of-sample Calmar rank-correlate at 0.34. In 2017–2021 the bear filter
costs nothing (median Calmar 2.67 filtered vs 2.68 unfiltered), which is
why an honest 2021 selection keeps it; out of sample it is decisive
(2.02 vs 0.66). This checks parameter *selection*, not design
*discovery*: the bear-filter and delayed-exit ideas came from studying
the full period.

## Validation (exp10 finalists)

* **Every era profitable, every era's drawdown shallow** (best book):
  2017–19 50.6% CAGR / 15.5% max DD; 2020–21 37.2% / 14.1%; 2022–23
  15.7% / 12.9%; 2024–26 14.5% / 4.0%. The 1-year-filter variant made
  12.2% through 2022–23 with a 3.8% max DD.
* **Design class, year by year** (return / intra-year max DD):

  | Year | Champion always-in | NATR regime, cash | Full design (E) | E, 1-yr filter |
  |---|---|---|---|---|
  | 2018 | −0.3 / 38.0 | +26.7 / 13.6 | **+30.8** / 15.5 | +30.8 / 15.5 |
  | 2020 | +52.5 / 42.2 | +64.6 / 14.0 | +61.4 / 14.1 | +61.4 / 14.1 |
  | 2022 | −25.0 / 26.2 | −10.8 / 22.2 | **−1.0** / 12.8 | −1.9 / **3.8** |
  | 2023 | +20.8 / 6.2 | **+51.3** / 10.8 | +34.9 / 9.3 | +28.1 / 3.4 |

  E has the best return/drawdown in 4 of 10 years; the always-in
  champion wins only the pure bull years (2017, 2021). The cost of the
  bear filter is a later re-entry into recoveries (2023).
* **Deflated Sharpe ratio 0.69–0.75 over 424 trials** — the Sharpe
  *uplift* over simpler books (1.46 → 1.56–1.63) is not significant at
  95% once every trial is counted. The design's measured value is in
  drawdown and downturn behaviour, not Sharpe.
* **Probability of backtest overfitting 0.54 within the 72-book family**
  — picking one variant over its near-identical siblings is noise. Every
  bear-filtered variant sits at Calmar 1.75–1.91: the *design* matters,
  the exact parameters do not, so the recommended configuration should be
  chosen for simplicity and robustness, not for the top cell.

## Experiment log

| Exp | Question | Result |
|---|---|---|
| 1 | Reproduce the step-down book; attribute its downturn losses. | Reproduced (29.95% / 21.4%, 2022 −10.3%). Loses in all 12 measurable QQQ corrections, peak to trough (mean −6.8%, worst −19.8%). Calm-sleeve regime exits: −$109k over the run, −$164k in 2022. The +10% QQQ sleeve exits by target in only 3,144 of 128,313 sales. |
| 2 | Does a small-target turbulent harvest sleeve help (champion-sized lots)? | No — too small to matter (L9). |
| 3 | Regime speed: NATR period 5/10/20 × median lookback 50/100/200 × min hold 1/3/5/10 (36 regimes, cash and stepdown books). | Regime speed is not the lever. The original cell (period 10, lookback 100) is the best region and robust across min holds (Calmar 1.30–1.40); faster periods and shorter or longer lookbacks are all worse (Calmar 0.67–1.17). No regime makes a correction window positive in the stepdown book; best 2022 −8.0% (cash, min hold 1). |
| 4 | A properly sized harvest sleeve ($200–$500 lots, 30–100 lot cap, target decay). | No (L10). Best book barely above cash (29.4% vs 29.0% CAGR; 2022 −10.1%). |
| 5 | Bear filter on calm re-entry (drawdown-from-high or SMA, ANDed with NATR calm; 15 filters). | **The first lever that changes downturns.** Cash book: no filter 29.0% / 22.3% DD / Calmar 1.30 / 2022 −10.8%; within 15% of the 20-session high 28.9% / 16.5% / **1.75** / −1.4%; within 50% of the 1-year high 28.1% / 16.5% / 1.70 / −2.0% (Sharpe 1.55; calm regime exits net **+$37k** vs −$109k); above the 200-day SMA 27.0% / 16.5% / 1.63 / **+0.9%**. Stepdown books do not improve: the wider "not calm" set lets the champion-shaped QQQ sleeve accumulate through bear-market calm stretches — the turbulent side must be cash or selective entries. |
| 6 | Calm-sleeve shape: target 3–30% × step 0.075%/0.2% × lot cap 2,000/6,000 (24 shapes). | **Keep the champion's shape.** Smaller targets hold less inventory at peaks and soften correction windows (3%: mean −1.5% vs −3.6%, worst −9.0% vs −11.0%) but cut CAGR from 29% to 9–15%; no shape beats the +30% target's Calmar in the cash book. |
| 7 | Capitulation-only turbulent sleeve (W-bottom entries) and gated harvest (noise / VWAP / throttle). | **First sleeve positive on average in corrections:** the bounded harvest shape ($200 lots, 100 cap, 0.8% target) behind the W-bottom gate ends 7/12 corrections positive alone, mean +0.18% — but trades rarely (1,854 buys) so it barely moves the book. W-bottom with the champion's large targets is worse (holds too long); noise / VWAP / throttle gates do not help. Capitulation entries + quick targets is the right shape; scale is the open question. |
| 18 | Intraday refinements on the recommended configuration: calm-mode gates N2 / N3 / X1 / N4, exit minute 90 / 120 / 150, reversal window 5 / 20 / 30 (12 runs). | **Converged.** Gates are neutral inside the design (N2 2.17, X1 2.16, N3 2.08, N4 never fires) — the regime and bear filter already do their job (L3). Exit minute is a plateau 60–385 (Calmar 2.11–2.36), best at +120 (2.36, 12.7% DD). Reversal window 5–30 min: no meaningful change. |
| 17 | Generality across UNLEVERAGED funds (QQQ, RSP, SPYD, COWZ): each fund's own champion grid, market regime + 1-year filter, exit +60, cash or −3% / +2% reversal (12 runs). | **A leveraged-ETF design.** Regime gating roughly halves both return and drawdown on unleveraged funds — QQQ 10.4% / 14.4% DD → 4.5% / 4.0% (Calmar 0.72 → 1.13); RSP 0.47 → 0.43; SPYD 0.18 → 0.36; COWZ 0.36 → 0.42 — while every detected downturn stays positive in cash mode. A −3% reversal is too loose for them (SPYD worst spell −13.9%). |
| 16 | **Stress test of the recommended configuration**, one change at a time (32 runs). | **Robust.** Internal bar-by-bar regime reproduces exp14's injected map exactly (29.69 / 13.7 / 2.16). Slippage ×2 / ×4 / ×10: Calmar 2.08 / 1.90 / 1.81. Level fills 2.05; close-only fills 1.96. No cash yield 2.05. Plateaus: bear depth 0.35–0.7 (2.03–2.19), exit minute 60–385 (2.11–2.36; +120 best at 12.7% DD), reversal target, lot 10–25%, threshold −8% to −12%. **Sensitive:** bear window must be long (125 sessions → 1.22, 2022 −14%) and the threshold no looser than −8% (−7% → 1.57). Without the bear filter 1.53; cash mode 1.93. |
| 15 | SOXL with the MARKET's regime (computed from TQQQ, injected) instead of its own; exit at the open or +60; reversal −9% or −12% (scaled for SOXL); cash (12 runs). | **The design transfers when the regime is the market's.** SOXL: 28–31% CAGR, 26–27% max DD, **Calmar 1.06–1.16** (champion 0.57; own-regime Ultimate 0.43–0.67). 1-year filter: 2022 −14.5% → −3%. −12% reversal: 41/42 downturns positive, worst −0.1%. |
| 14 | **The deployable `UltimateSizing` with every lesson:** bear filter × delayed regime exit (+60 min, close) × cash or TQQQ reversal (30 runs). | **20-session filter, exit +60, reversal ≤ −9% / +6% / 20%: 30.3% CAGR, 13.7% max DD, Calmar 2.21**, Sharpe 1.60, 2022 −1.3%, 46/47 downturns positive. **1-year filter, exit +60: 29.7% / 13.7% / 2.16, Sharpe 1.66, 2022 −1.5% with a 3.5% intra-year max DD, 42/42 downturns positive.** Champion always-in (same fill model): 25.7% / 42.2% / 0.61. |
| 13 | **Out-of-sample instrument:** the design, untouched, on SOXL (never used in design work) with SOXL's own champion grid and the regime computed from SOXL's own bars (9 runs). | **Transfers only weakly.** SOXL always-in champion (causal fills) 17.7% / 31.1% DD / Calmar 0.57; best Ultimate variant (1-year filter + reversal) 26.1% / 38.8% / 0.67 — more return, *deeper* drawdown. Cash-mode variants stay positive in all 66 detected downturns; the −9% reversal threshold is not extreme for SOXL (8–10 of 66 spells lose, up to −14%). The edges are tuned to Nasdaq-100 dynamics; SOXL's own NATR is noisier. |
| 12 | The deployable `UltimateSizing` (one strategy, TQQQ) with the bear filters × TQQQ reversal settings, regime exit still at the open (52 runs). | 20-session filter + reversal ≤ −9% / +6% / 20% lots: **29.9% CAGR, 16.5% max DD, Calmar 1.81, 2022 −0.7%**, 46/47 downturns positive. With the 1-year or stacked filter every detected downturn is positive (42/42, 41/41; worst 0.00%). |
| 11 | The detection cost: liquidate the calm sleeve at the open / +30 / +60 / midday / close of the flip session, all lots or the highest-cost 75 / 50 / 25%, under the reference and the 1-year-filter regimes, with the QQQ reversal sleeve (40 books). | **Selling later turns the detection cost positive.** 1-year filter: at the open 28.4% / 16.4% DD / Calmar 1.74 / detection −8.3%; at +60 min 29.0% / 13.6% / 2.13 / +2.1%; at the close **29.2% / 13.6% / 2.14 / +3.0%**, Sharpe 1.65, 42/42 detected downturns positive. Reference regime: Calmar 1.36 → 1.50 at +30 min, detection −10.0% → +0.7%. **Partial exits are worse** (75%: DD 18%; 25%: DD 42%) — sell everything, just not at the open. |
| 10 | The combined design: 4 bear-filtered regimes × the champion calm sleeve × capitulation sleeves in turbulence (QQQ/TQQQ close-reversal, W-bottom harvest at 5–10× size), alone and stacked (72 books). | **Best so far: 29.6% CAGR, 15.5% max DD, Calmar 1.91, Sharpe 1.56, 2022 −1.0%** (filter: within 15% of the 20-session high; TQQQ reversal ≤ −5% / +3% / 10% lots + QQQ W-bottom harvest 2% lots / +1.5%). In-spell: 46/47 detected downturns positive, worst −0.8%. The 1-year-filter variant: Sharpe 1.63, 2022 −1.9% with a 3.8% intra-year max DD. Validation below. |
| 9 | The deployable single-instrument `UltimateSizing` on TQQQ (calm: champion grid; turbulent: TQQQ close-reversal), one engine run with shared cash; 36 reversal settings + cash mode; internal regime vs injected map. | **Calmar 1.30 → 1.50 as one strategy:** session ≤ −9%, +6% target, 20% lots, cap 4: 30.0% CAGR, 20.0% max DD, 2022 −7.3% (cash mode: 29.0% / 22.3% / −10.8%). **The strategy's own bar-by-bar regime reproduces the injected-map run exactly** (identical CAGR, DD, every year). |
| 8 | Close-reversal turbulent sleeve (`reversal_gate="close"`): one event lot per qualifying session, profit-only exits. 90 variants, QQQ and TQQQ. | **The first component consistently positive in downturns.** QQQ, session ≤ −3%, +0.5% target: 57 trades, all 57 exited at target; alone 10/12 corrections positive, worst −0.9%, 2022 +1.4%. +2% target: 48/51 at target, 11/12 positive, 2022 +2.1%. TQQQ ≤ −9%: 9/12. **Capacity-limited** (5–13 events a year): +0.1–0.3pp on the book. |
