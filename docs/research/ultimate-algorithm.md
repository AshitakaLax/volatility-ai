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
| 9 | The deployable single-instrument `UltimateSizing` on TQQQ (calm: champion grid; turbulent: TQQQ close-reversal), one engine run with shared cash; 36 reversal settings + cash mode; internal regime vs injected map. | **Calmar 1.30 → 1.50 as one strategy:** session ≤ −9%, +6% target, 20% lots, cap 4: 30.0% CAGR, 20.0% max DD, 2022 −7.3% (cash mode: 29.0% / 22.3% / −10.8%). **The strategy's own bar-by-bar regime reproduces the injected-map run exactly** (identical CAGR, DD, every year). |
| 8 | Close-reversal turbulent sleeve (`reversal_gate="close"`): one event lot per qualifying session, profit-only exits. 90 variants, QQQ and TQQQ. | **The first component consistently positive in downturns.** QQQ, session ≤ −3%, +0.5% target: 57 trades, all 57 exited at target; alone 10/12 corrections positive, worst −0.9%, 2022 +1.4%. +2% target: 48/51 at target, 11/12 positive, 2022 +2.1%. TQQQ ≤ −9%: 9/12. **Capacity-limited** (5–13 events a year): +0.1–0.3pp on the book. |
