# Daily Ultimate — an algorithm for +0.1% of equity a session

Nov 5, 2026 · Built and swept · `daily_ultimate` (`research/strategies/daily_ultimate_sizing.py`),
`tools/probe_daily_ultimate.py`, `config/daily_ultimate_tqqq.yaml`

## Goal

The owner's goal: **+0.1% of equity per session**, which compounds to 28.6% a year over 252
sessions, with buys and sells every day. The questions were which fund, which buy algorithm
and which sell algorithm reach it, validated by a sweep.

## Answer

| | Choice |
|---|---|
| **Fund** | **TQQQ.** The only fund where the goal is reached inside a 30% drawdown. SOXL reaches it only at a 43.5% drawdown. Every unleveraged fund tops out between 0.00% and 0.05% a session, below its own buy-and-hold. |
| **Buy** | **`daily_ultimate`** (Ultimate's buying). Buys only in a calm regime: NATR(14) below its 100-session median, held 5 sessions, price within 50% of its 250-session high. While calm, it buys a lot of 0.8% of starting equity at each 0.2% pullback from the local reference. While turbulent, it buys one 20% reversal lot after a session down 8%, with at most 4 open. |
| **Sell** | **`daily_ultimate_exit`**. Each calm lot sells at +12%, each reversal lot at +8%. Every calm lot is sold an hour into the first turbulent session: the regime exit, the one sale that may realise a loss. The daily goal is tracked, but neither daily take-profit is on. |
| **Pinned** | `config/daily_ultimate_tqqq.yaml`: step 0.2%, target 12%, `STRATEGY_DEFAULTS["daily_ultimate"]` |

Measured with intrabar causal fills, dynamic slippage and no cash yield, from 2016-01-04 to
2026-11-03, scored from 2017-01-03:

| | Per session | CAGR | Max DD | Sharpe | Worst day | 2022 | Sessions at +0.1% |
|---|---|---|---|---|---|---|---|
| **Daily Ultimate** | **0.160%** | **49.6%** | **29.9%** | **1.67** | −11.8% | −12.3% | 34.7% |
| 2017–2021 | 0.220% | 73.8% | 20.5% | | | | |
| 2022 onward | 0.099% | 28.2% | 19.3% | | | | |
| TQQQ buy-and-hold | 0.128% | 37.8% | 81.7% | 0.82 | −34.8% | −79.1% | 54.9% |
| 2022 onward | 0.033% | 8.5% | 81.0% | | | | |

**What it is not: a day trader.** The median lot is held 10 sessions, and only 14% of sessions
sell anything. The daily switches that make it one are built and measured below. Each costs
return per session, and none reaches the goal after 2022.

## What was built

`DailyUltimateSizing` is Ultimate plus three switches. With all three off it is Ultimate
exactly, blotter for blotter (`research/tests/test_daily_ultimate.py`).

| Switch | What it does |
|---|---|
| `compound_lots` | Sizes each session's lots, reversal lots included, from that session's opening equity rather than the run's first. |
| `daily_goal` (+ `goal_pause_buys`, `goal_lock`) | The session's target return on its opening equity. Once reached, the goal can pause the calm grid for the rest of the session, or sell every calm lot already up `harvest_min_gain` at the market. |
| `eod_harvest_minute` | From this minute to the close, sells every calm lot already up `harvest_min_gain` at the market. |

Both take-profits are profit-target sales: the lot's target is moved to the price, as
`signal_take_profit` does, so the no-loss guard checks them. Nothing new can sell below cost.
The halves are composable:
- **`daily_ultimate`** is a buy policy;
- **`daily_ultimate_exit`** is Ultimate's exit plus the take-profits. Its regime defaults match the buy, which `ultimate_exit`'s do not;
- **`daily_harvest`** is the take-profits alone, for any buyer.

`composed(daily_ultimate, daily_ultimate_exit)` is pinned identical to `daily_ultimate`.

## How it was measured

`tools/probe_daily_ultimate.py` runs four stages, 734 configurations in all, one process each:

1. **funds:** 11 funds × 36 cells.
2. **grid:** TQQQ, 300 cells.
3. **pairs:** buy × sell at the choice, 24 cells.
4. **robust:** one change at a time, 14 cells.

**Conditions:**
- Intrabar fills with **causal** booking. The warehouse's 397k server runs all use `level`, which the ledger records as biased.
- Dynamic slippage of 0.5 bp plus 0.3 × the bar's range.
- **No yield on idle cash.**
- Scored after a one-year warm-up, against buy-and-hold over the same window.

On every fund but TQQQ, each price distance (step, target, reversal threshold and target) is
scaled by the fund's daily volatility relative to TQQQ's.

**The choice:** the highest geometric daily return within a 30% maximum drawdown.

## Results

### 1. Fund: only the leveraged Nasdaq fund gets there

| Fund | Buy-and-hold /session | B&H max DD | Best /session | Its DD | Best within 30% DD |
|---|---|---|---|---|---|
| **TQQQ** | 0.128% | 81.7% | 0.151% | 38.7% | **0.116%** (29.5%) |
| SOXL | 0.122% | 90.5% | 0.120% | 62.3% | none (0.101% at 43.5%) |
| QQQ | 0.073% | 35.0% | 0.047% | 25.3% | 0.047% |
| SPY | 0.055% | 33.8% | 0.027% | 19.5% | 0.027% |
| URSP_SIM | 0.056% | 65.6% | 0.021% | 33.4% | 0.019% |
| RSP | 0.044% | 39.1% | 0.022% | 14.1% | 0.022% |
| IWM, XBI, SPYD, COWZ, EEM | 0.03–0.05% | 39–64% | 0.00–0.01% | | |

On an unleveraged fund the regime design halves return and drawdown together. The ledger
already records this as Ultimate's lesson L16, and it holds for every fund here. 0.1% a
session needs a fund that moves about 3× the index.

### 2. Compounding exposes the real risk

At a fixed 0.4% lot with the closing harvest, compounding raised the return from 0.092% to
0.128% a session. It also raised the drawdown from 19% to 60%, and 2022 went from −12% to −49%.
Ultimate's fixed-dollar lots shrink as the account grows. The chosen configuration's account
was about 15× its start by 2022, so its lots were a sliver of it; compounded lots stay the same
share of the book. Two separate diagnostics measured the cause:

| Compounded variant (0.4% lots, 4% target, closing harvest) | Per session | Max DD | 2022 |
|---|---|---|---|
| 20% reversal lots, compounded (up to 80% of equity while turbulent) | 0.128% | 60.3% | −49.2% |
| 5% reversal lots | 0.113% | 37.8% | −21.4% |
| no reversal lots (cash while turbulent) | 0.108% | 30.8% | −12.1% |
| exposure cap of 50% of equity | 0.081% | 49.2% | −42.5% |

In the buy × sell stage, compounding the chosen configuration left its return unchanged (0.160%)
and doubled its drawdown (59.9%). **The fixed-dollar Ultimate is cheaper risk for the same
return**, so `compound_lots` is off in the choice.

### 3. The daily switches cost return per session

Grid medians over 12 cells each (target × lot), compounded:

| How lots leave | Per session, all | Per session, 2022 on | Max DD |
|---|---|---|---|
| at their target (hold) | 0.139–0.147% | 0.090–0.092% | 34–45% |
| + goal lock | 0.118–0.127% | 0.070–0.072% | 28–43% |
| + closing harvest | 0.108–0.120% | 0.066–0.069% | 30–45% |
| + both | 0.099–0.110% | 0.053–0.056% | 28–43% |
| any of these + goal pause | 0.036–0.123% | 0.017–0.072% | 20–37% |

Selling the day's winners early gives up the trend the grid exists to hold. Pausing at +0.1%
gives up the rest of the up days, which are where the year is made.

### 4. Choosing: the rule that rewards a narrow margin fails

The first rule tried was the shallowest drawdown among cells that reach the goal. Applied to
2017–2021 alone, it picked a fixed-lot, 4%-target cell. That cell made **0.046% a session from
2022, 184th of 300**: a rule that rewards clearing a bar by the least margin picks the cell that
falls short.

The rule adopted is the highest return within a 30% drawdown. Picking on 2017–2021, it chose the
same cell as on the whole history (12% target, 0.8% lots). That cell made **0.099% a session
from 2022, 2nd of 300**, with a 19.3% drawdown. The same rule with a 25% or 35% budget picks the
same cell.

**No cell of 300 reaches 0.1% a session in both 2017–2021 and 2022 onward.** The best second
half is 0.099%. Buy-and-hold made 0.033% then.

### 5. Buy × sell: the regime has to sit on both sides

At the chosen grid point:

| Buy × sell | /session | 2022 on | Max DD | 2022 | Sessions selling |
|---|---|---|---|---|---|
| **daily_ultimate × daily_ultimate_exit** (≡ ultimate × ultimate_exit) | **0.160%** | **0.099%** | **29.9%** | −12.3% | 14% |
| daily_ultimate compounded × daily_ultimate_exit | 0.160% | 0.089% | 59.9% | −49.4% | 10% |
| daily_ultimate × daily_ultimate_exit + goal lock | 0.113% | 0.047% | 21.7% | −11.7% | 39% |
| daily_ultimate × daily_ultimate_exit + closing harvest | 0.110% | 0.058% | 22.4% | −13.1% | 46% |
| daily_ultimate × fixed_target (no regime exit) | 0.152% | 0.039% | 77.8% | −75.5% | 12% |
| daily_ultimate × daily_harvest (no regime exit) | 0.089% | 0.020% | 74.5% | −72.4% | 37% |
| hf_local_reference (no regime) × daily_ultimate_exit | 0.119% | 0.018% | 81.3% | −79.1% | 14% |

The regime exit is what protects the book. Without it, drawdown returns to buy-and-hold's.
The regime on the buy side matters as much: the champion keeps buying through a bear market
after the exit has sold its lots.

### 6. Robustness of the choice

| Change | /session | 2022 on | Max DD |
|---|---|---|---|
| none | 0.160% | 0.099% | 29.9% |
| slippage ×4 / ×10 | 0.160% / 0.158% | 0.099% / 0.098% | 30.0% / 30.3% |
| target ×0.75 / ×1.5 / ×2 | 0.158% / 0.159% / 0.165% | 0.094% / 0.101% / 0.099% | 29.6–30.1% |
| lots ×0.5 / ×1.5 / ×2 | 0.155% / 0.159% / 0.153% | 0.091% / 0.100% / 0.093% | 24.5% / 32.6% / 34.7% |
| step ×0.5 / ×2 | 0.156% / 0.142% | 0.096% / 0.075% | 33.6% / 20.1% |
| cash while turbulent | 0.156% | 0.101% | 29.2% |
| **bear_window 125** | 0.153% | 0.084% | **53.9%** |
| **NATR(10), −9% / +6% reversals** | 0.139% | 0.078% | **42.5%** |

It is a plateau in target, lots and costs. It is sensitive to the bear filter's window, which
must stay long (Ultimate's L12 found the same), and to the regime's period.

## The daily-trading variant

For buys and sells every session, add the goal lock to the sell: `daily_ultimate_exit` with
`goal_lock: true` and `daily_goal: 0.001`. On the chosen configuration that gives:
- **0.113% a session** (32.7% CAGR) at a **21.7%** max drawdown, Sharpe 1.45;
- sales on 39% of sessions, with 90% of lots closed within 5 sessions;
- the day's realised profit reaching +0.1% of equity on 25% of sessions.

It reaches the goal over 2017–2026 but makes only **0.047% a session from 2022**. The closing
harvest (`eod_harvest_minute: 380`) is the most intraday form: 53% of lots close the session
they were bought in, at 0.110% a session overall and 0.058% from 2022.

## Caveats

- **It rests on one bear market.** The bear filter and the regime were designed by studying
  2022 (Ultimate's caveats), and the second half's edge over buy-and-hold is mostly 2022.
- **Selection.** 734 configurations were run. The walk-forward check covers parameter
  selection within this design, not the design's discovery.
- **No cash yield.** Fidelity's core position would pay a money-market rate on the ~25% of
  sessions spent in cash, which is extra return not counted here.
- **Fixed-dollar lots do not grow with the account.** Live, `per_lot_pct` is a share of the
  ledger's starting cash, so re-base it as the account grows, or accept a lower return on
  equity.
- **At Fidelity** a lot rounds up to one whole TQQQ share (about $59 on 2026-11-02); 0.8% of a
  $25k account is $200, about 3 shares.
- `regular_session_only`, and `execution.allow_signal_exit` is required (the regime exit).

## Reproduce

```bash
python tools/probe_daily_ultimate.py --stage funds  --out output/daily_ultimate --jobs 30
python tools/probe_daily_ultimate.py --stage grid   --fund TQQQ --out output/daily_ultimate --jobs 28
python tools/probe_daily_ultimate.py --stage pairs  --fund TQQQ --out output/daily_ultimate
python tools/probe_daily_ultimate.py --stage robust --fund TQQQ --out output/daily_ultimate
python tools/probe_daily_ultimate.py --report output/daily_ultimate
python cli.py backtest --config config/daily_ultimate_tqqq.yaml   # 44.4% CAGR full window, 30.2% DD
```

A TQQQ configuration takes about 100 s with 58 running at once (Dell R630, 64 threads), so the
300-cell grid takes about 18 minutes on 28 workers.
