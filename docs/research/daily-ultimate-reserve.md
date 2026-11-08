# Daily Ultimate Reserve — +0.1% a session with the most cash, through a worse bear

Nov 8, 2026 · Swept and stress-tested · `tools/probe_daily_reserve.py`, `tools/stress_paths.py`,
`config/daily_ultimate_reserve_tqqq.yaml`

## Goal

The owner's follow-up to [Daily Ultimate](daily-ultimate.md): **+0.1% of equity a session at the
least drawdown, with as much of the account in cash as possible**, still standing if the next
bear is worse than 2022's.

## Answer

| | Choice |
|---|---|
| **Fund, buy, sell** | TQQQ; `daily_ultimate`, with its own regime exit, as in Daily Ultimate |
| **Lots** | **0.25% of the session's opening equity** (`compound_lots`), at each 0.4% pullback, each sold at +12% |
| **Turbulent** | **cash**: no reversal lots. Calm lots are still sold an hour into the first turbulent session |
| **Pause** | a calm session buys nothing more once it is up 0.1% (`goal_pause_buys`) |
| **Throttle** | the exposure ceiling ramps from 100% of equity at a 5% drawdown to 10% at a 20% drawdown (`risk.dd_exposure_*`) |
| **Pinned** | `config/daily_ultimate_reserve_tqqq.yaml`; `CHOSEN` in the probe |

Measured with intrabar causal fills, dynamic slippage and no cash yield, from 2016-01-04 to
2026-11-04, scored from 2017-01-03:

| | Per session | CAGR | Max DD | Worst stress DD | Avg in TQQQ | 2022 |
|---|---|---|---|---|---|---|
| **Reserve** | **0.101%** | **28.8%** | **18.5%** | **18.5%** | **25.1%** | −3% |
| 2017–2021 | 0.124% | | 18.5% | | | |
| 2022 onward | **0.077%** | | 16.4% | | | |
| Daily Ultimate (`daily_ultimate_tqqq.yaml`) | 0.161% | 49.7% | 29.9% | 57.6% (opened at the 2021 top) | 40.2% | −12% |
| TQQQ buy-and-hold | 0.129% | 38.2% | 81.7% | 96.4% (`twice`) | 100% | −79% |

**What it buys:** the drawdown is shallower than Daily Ultimate's (18.5% against 29.9%), with
less of the account in TQQQ (25% on average against 40%), and it doesn't get deeper on any
stress path. Opened at the 2021 peak it falls 16.4%, against Daily Ultimate's 57.6%. On 52% of
sessions it closes entirely in cash.

**What it costs:**

- **It doesn't make 0.1% a session from 2022 on** (0.077%). Every configuration in the sweep
  that does has a drawdown of 34% or more (see [The price of the goal holding after
  2022](#the-price-of-the-goal-holding-after-2022)).
- **It isn't a cash reserve on its fullest days.** It holds 100% of the account in TQQQ at its
  peak, and 95% at the 95th percentile of sessions. A real cap on exposure misses the goal: the
  best at 50% is 0.085% a session.
- **It sits at the goal with no margin.** Most single changes push it below 0.1% (see
  [Robustness](#robustness)).
- **Its worst drawdown is long:** from 2021-02-12 to 2021-05-05 (18.5%), not recovered until
  2023-07-13. It sat out 2022 in cash, which is why it was flat rather than down.
- **It is in a drawdown now:** 16% from 2026-10-06 to 2026-11-02, and up 1% in 2026.

## How it was chosen

Every run is measured as `tools/probe_daily_ultimate.py` measures one, plus the share of the
account in TQQQ at every close. Every later stage ends on the reserve stage's last session
(2026-11-04), so bars added to the warehouse since do not move its history.

**Lots are compounded.** Daily Ultimate's lots are a share of *starting* equity. From 2016 they
shrink to a sliver of an account that has grown fourfold by 2022. That is most of why its
drawdown reads 29.9%: the same configuration opened at the 2021 peak falls 57.6%. Here every lot
is a share of the session's opening equity, so a drawdown means the same whenever the account
starts.

1. **reserve** (864 configurations), each over history:
   - **turbulent:** cash, or Ultimate's reversal lots at 5% of equity (four at most);
   - **cap:** none, or 50%, 30% or 20% of equity in TQQQ;
   - **lot:** 0.2%, 0.4% or 0.8%;
   - **step:** 0.2% or 0.4%;
   - **target:** +4%, +8% or +12%;
   - **pause:** on or off;
   - **protect:** none, the drawdown throttle, or a tighter bear filter (no calm buying 30% below
     the 250-session high, rather than 50%).
2. **stress:** the 30 shallowest-drawdown configurations at the goal, the shallowest at the goal
   for each turbulent × cap × protect group, and Daily Ultimate for reference (34 in all). Each
   runs under the five stress paths below.
3. **The choice:** among configurations at the goal over history, the shallowest *worst*
   drawdown across history and the five stress paths. Drawdowns within a point tie, and a tie
   goes to the lower average exposure.
4. **trim:** the choice's lot stepped down (×0.5 to ×0.875), each stressed, and the same rule
   chooses again. It spends the return the choice makes above the goal on a smaller book.
5. **robust:** one change at a time, run on history and on the choice's worst stress path.
6. **both:** every configuration at the goal in both halves, stressed. This shows the price of
   the goal holding after 2022; it doesn't change the choice.

### The stress paths (`tools/stress_paths.py`)

Each scenario is built from TQQQ's own minute bars. Everything up to the peak is untouched, and
after the bear the real bars continue from wherever the scenario left the price.

| Path | What it does | TQQQ max DD | B&H per session |
|---|---|---|---|
| history | | 81.7% | 0.129% |
| `deeper` | every bar's log move inside the 2022 bear ×1.5 | 92.2% | 0.094% |
| `grind` | the 2022 bars with a steady extra fall, so each bar's range reads like 2022 while the price goes further | 95.0% | 0.076% |
| `twice` | the 2022 bear, then the same bear again from its trough | 96.4% | 0.057% |
| `fast` | the 2020 crash made `deeper` the same way: −83.5% in a month | 83.5% | 0.105% |
| `top` | history, opened at the 2021 peak (bars from 252 sessions earlier, to warm the regime) | 81.7% | 0.031% |

## Results

### reserve: no capped configuration reaches the goal

142 of 864 configurations reach 0.1% a session over history, and **none of them has an exposure
cap**. Best per session at each cap:

| Cap | Best per session | Its DD | Avg / max in TQQQ |
|---|---|---|---|
| none | 0.153% | 38.7% | 49% / 100% |
| 50% | 0.085% | 24.7% | 27% / 53% |
| 30% | 0.054% | 18.9% | 17% / 33% |
| 20% | 0.038% | 15.8% | 12% / 22% |

At the goal, the shallowest drawdown on each axis:

| Axis | Value | At the goal | Shallowest DD there |
|---|---|---|---|
| turbulent | cash | 75 of 432 | 18.8% |
| | rev5 | 67 of 432 | 24.6% |
| protect | throttle | 25 of 288 | 18.8% |
| | none | 63 of 288 | 20.9% |
| | bear30 | 54 of 288 | 22.0% |
| pause | on | 61 of 432 | 18.8% |
| | off | 81 of 432 | 19.6% |

The drawdown throttle and cash in turbulence give the shallowest drawdowns. The tighter bear
filter doesn't help: its shallowest drawdown at the goal (22.0%) is deeper than with no
protection at all (20.9%).

### stress: the cash books barely notice a worse bear

For all but one of the cash-when-turbulent configurations, the worst drawdown over every stress
path stays within about two points of the history drawdown. They are out of the market through
the bear, so a deeper bear has nothing to take. The exception, lot 0.4%, t +4%, step 0.2% with
the pause, goes from 22.4% to 30.2% under `deeper`. The reversal-lot (`rev5`) books do hold TQQQ in turbulence and feel it
(24.9% → 28.9% under `deeper`). Daily Ultimate's fixed lots fall 33.8% under `deeper` and 57.6%
opened at the top.

| Configuration | Per session | History DD | Worst stress DD | Avg in TQQQ |
|---|---|---|---|---|
| **lot 0.4%, t +12%, step 0.4%, cash, pause, throttle** (chosen) | 0.111% | 18.8% | 19.5% (`deeper`) | 28.8% |
| lot 0.2%, t +8%, step 0.2%, cash, pause, throttle | 0.110% | 18.8% | 18.8% | 30.5% |
| lot 0.8%, t +8%, step 0.4%, cash, pause, throttle | 0.102% | 20.2% | 20.2% | 30.8% |
| lot 0.8%, t +12%, step 0.4%, cash, pause, throttle | 0.118% | 19.6% | 20.4% | 33.1% |
| best `rev5`: lot 0.2%, t +12%, step 0.2%, pause, throttle | 0.101% | 24.9% | 28.9% | 32.5% |
| Daily Ultimate | 0.161% | 29.9% | 57.6% (`top`) | 40.2% |

The first two tie within a point, so the tie went to the lower average exposure.

A worse bear costs these books return rather than capital: they sit out more of the recovery.
The choice under `fast` makes +19% in 2020 against +80% on history, and under `twice` it is flat
in 2023. The likely reason is that the price stays more than 50% below its 250-session high for
longer, and the bear filter buys nothing there.

| Path | Choice per session | Max DD |
|---|---|---|
| history | 0.101% | 18.5% |
| `deeper` | 0.095% | 18.5% |
| `grind` | 0.098% | 18.5% |
| `twice` | 0.092% | 18.5% |
| `fast` | 0.084% | 18.5% |
| `top` | 0.079% | 16.4% |

### trim: a smaller lot, at the goal

| Lot | Per session | History DD | Worst stress DD | Avg in TQQQ |
|---|---|---|---|---|
| 0.2% | 0.096% | 18.5% | 20.1% | 22.3% |
| **0.25%** (chosen) | **0.101%** | **18.5%** | **18.5%** | **25.1%** |
| 0.3% | 0.107% | 18.5% | 19.0% | 26.9% |
| 0.35% | 0.109% | 18.7% | 19.5% | 27.7% |
| 0.4% | 0.111% | 18.8% | 19.5% | 28.8% |

### Robustness

One change at a time, on history and on `fast`, the choice's worst path. The drawdown is never
deeper than 23.7% under any change, but the return doesn't hold. Five changes keep it at the
goal on history (slippage ×4, a 2% cash yield, step ×0.5, target ×1.5 and a 0.2% daily goal),
and none does on `fast`:

| Change | History per session | DD | `fast` per session | DD |
|---|---|---|---|---|
| (the choice) | 0.101% | 18.5% | 0.084% | 18.5% |
| slippage ×4 | 0.100% | 18.5% | 0.083% | 18.5% |
| slippage ×10 | 0.096% | 18.7% | 0.080% | 18.7% |
| cash yield 2% a year | 0.106% | 18.4% | 0.089% | 18.4% |
| step ×0.5 (0.2%) | 0.110% | 23.0% | 0.097% | 23.0% |
| step ×2 (0.8%) | 0.046% | 9.5% | 0.035% | 9.5% |
| target ×0.75 / ×1.5 | 0.098% / 0.104% | 17.5% / 19.8% | 0.083% / 0.086% | 17.5% / 19.8% |
| daily goal 0.05% / 0.2% | 0.095% / 0.107% | 15.6% / 19.2% | 0.081% / 0.090% | 15.6% / 19.2% |
| bear_dd 0.4 / 0.6 | 0.097% / 0.098% | 18.5% / 19.3% | 0.078% / 0.094% | 18.5% / 19.3% |
| bear_window 125 / 500 | 0.087% / 0.070% | 23.0% / 19.4% | 0.070% / 0.053% | 23.0% / 19.4% |
| natr_period 10 / 20 | 0.070% / 0.073% | 21.8% / 23.1% | 0.059% / 0.056% | 21.8% / 23.1% |
| regime_min_hold 1 / 10 | 0.092% / 0.063% | 19.5% / 23.7% | 0.079% / 0.045% | 19.5% / 23.7% |
| liquidate_minute 1 / 180 | 0.097% / 0.097% | 18.5% / 19.0% | 0.079% / 0.080% | 18.5% / 19.0% |

The regime's settings matter most. A different NATR period, a 500-session bear window or a
10-session hold costs 28–38% of the return.

### Walk-forward

Applied to 2017–2021 alone (at the goal there, shallowest drawdown there), the rule picks
`lot 0.4%, t +8%, step 0.2%, cap 50%, cash, pause, throttle`. That makes 0.108% a session in
2017–2021 (DD 9.8%) and **0.036% from 2022 on** (DD 12.9%), ranking 361st of 864 there. Only 7
of 864 configurations reach the goal in both halves.

### The price of the goal holding after 2022

The 7 configurations at the goal in both halves, stressed:

| Configuration | Per session | 2022 on | History DD | Worst stress DD | Avg in TQQQ |
|---|---|---|---|---|---|
| lot 0.8%, t +8%, step 0.2%, cash | 0.149% | 0.101% | 34.4% | 37.9% (`deeper`) | 46.9% |
| lot 0.4%, t +8%, step 0.2%, cash | 0.146% | 0.103% | 34.5% | 38.0% | 46.1% |
| lot 0.8%, t +12%, step 0.2%, cash | 0.147% | 0.101% | 34.4% | 38.2% | 47.1% |
| lot 0.4%, t +12%, step 0.2%, cash | 0.146% | 0.101% | 34.5% | 39.0% | 46.5% |
| lot 0.2%, t +8%, step 0.2%, cash | 0.143% | 0.100% | 35.2% | 40.0% | 44.5% |
| lot 0.8%, t +8%, step 0.2%, rev5 | 0.153% | 0.100% | 38.7% | 44.5% | 49.5% |
| lot 0.4%, t +8%, step 0.2%, rev5 | 0.150% | 0.101% | 38.8% | 44.6% | 48.7% |

All are uncapped, with no pause and no throttle. For 0.1% a session after 2022 as well, the
sweep's answer is about **twice the drawdown (34–40% worst) and nearly twice the exposure (46%
on average)**. Each one's worst drawdown runs from 2021-09-07 to 2023-04-25. Daily Ultimate itself
made 0.099% from 2022 on, but falls 57.6% if opened at the 2021 top.

## Caveats

- **One history.** 2022 is the only bear in the window. The stress paths are built from that
  bear and the 2020 crash, so they test depth and speed, not a different shape, such as a slow
  2000–02 bear with long rallies inside it.
- **Selected on the same history it is scored on.** The walk-forward check is not encouraging:
  the rule picked on 2017–2021 made 0.036% a session afterwards.
- **No cash yield.** Holding 75% of the account in cash on average, a money-market rate adds
  about 0.005% a session at 2% a year. That is the difference between 0.101% and 0.106%.
- **Calendar inputs don't move with the `twice` copy**, so its event and earnings days are
  mislabelled for its length. That changes a few lots' size and nothing else.
- The engine's exposure ceiling throttles new buys only. It never sells, so a drawdown past 20%
  still holds what was bought before it.

## Reproduce

```bash
python tools/probe_daily_reserve.py --stage reserve --out output/daily_reserve --jobs 24
python tools/probe_daily_reserve.py --stage stress  --out output/daily_reserve
python tools/probe_daily_reserve.py --stage trim    --out output/daily_reserve
python tools/probe_daily_reserve.py --stage robust  --out output/daily_reserve
python tools/probe_daily_reserve.py --stage both    --out output/daily_reserve
python tools/probe_daily_reserve.py --report output/daily_reserve
```

The reserve stage took about half an hour on this machine, and each later stage a few minutes.
