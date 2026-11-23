# Forecast Harvest — a TQQQ book in whole shares, banking most sessions, read from the nightly report

Nov 23, 2026 · Built and swept · `forecast_harvest` (`research/strategies/forecast_harvest_sizing.py`),
`tools/probe_forecast_harvest.py`, `tools/probe_crash_entries.py`, `config/forecast_harvest_tqqq.yaml`

## The ask

A new TQQQ algorithm that:
- trades **whole shares**;
- takes **mostly daily profits**;
- **buys and sells dynamically**;
- lets the **nightly risk report** set the potential reward;
- starts with **$250,000 after TQQQ has fallen 43%**, the best way.

It also asked for fake risk reports over the past, to see the worst, normal and best outcomes, and
for the work to build on the earlier algorithms.

TQQQ crossed −43% on Nov 19, 2026. On Nov 20 it closed at $40.99, 52.8% below its June 2 high of
$86.84.

## Answer

| | Choice |
|---|---|
| **Algorithm** | **`forecast_harvest`**: Daily Ultimate's regime-gated TQQQ book in **whole shares**, with each calm lot split. **¾ of its shares are the day part**, sold at the session's level (the previous close × (1 + 0.25 × the report's p75), at least +0.2% over cost) or at the market from minute 375 once up 0.2%. **¼ is the swing part**, sold at +20%. Reversal lots are 10% of capital, at most 2 open. |
| **Pinned** | `config/forecast_harvest_tqqq.yaml`, plus the paper profile `config/live_profiles/forecast-harvest-tqqq.yaml` |
| **The report** | Wired in two ways: research reads it from a schedule, and a deployment reads it from the forecast database. It sets the day part's price level, and optionally the lot size. **It changes this configuration by under 0.002% a session at any accuracy short of perfect, so a wrong report cannot hurt it.** Turn up its weight (`day_k: 1`, `forecast_tilt: 0.5`) only once the forecast database shows the reports' median tracking the close (ρ ≈ 0.5 or better). |
| **How to start with $250,000 now** | **No seed and no lump sum: start the book itself, on paper first.** It is in its turbulent mode, so it buys only capitulation reversal lots: $25,000 in the last 10 minutes of a session down 8% or more, at most two open, each sold at +8%. The day-by-day grid restarts by itself when TQQQ calms. |
| **Aggressive profile** | `aggressive-forecast-harvest-tqqq`: the same book reading the report at ten times the weight (day level 2.5 × p75, day parts +0.3% to +8%, lots tilted by the report's median), so the day parts make **~25% of the profit**. 0.145% a session at a 25.4% drawdown; it gains when the report is right (0.151% at ρ 0.5) and loses a little when it is wrong (0.143%). Section 5. |

Measured with causal intrabar fills, dynamic slippage, no cash yield and $250,000, from 2016-01-04
to 2026-11-20, scored from 2017-01-03:

| | Per session | CAGR | Max DD | Calmar | 2022 on | Invested sessions banking a profit |
|---|---|---|---|---|---|---|
| **Forecast Harvest** | **0.144%** | **43.5%** | **24.5%** | **1.78** | 0.080% | **54%** |
| Daily Ultimate, whole shares | 0.158% | 48.8% | 29.9% | 1.63 | 0.097% | 12% |
| TQQQ held | 0.111% | 32.3% | 81.7% | | 0.001% | |

Started at each close 43% below TQQQ's high, with no seed:

| Outcome | Start | After 1 year | After 2 years | Lowest point | TQQQ held, after 1 year |
|---|---|---|---|---|---|
| **worst real** | 2022-02-18 | 0.88× | 2.03× | 0.84× | 0.45× |
| **median real** (four) | | 1.60× | 2.44× | 0.97× | 1.91× |
| **best real** | 2020-03-09 | 2.49× | 2.84× | 0.97× | 2.80× |
| **worst of three bears deeper than 2022** | `tools/stress_paths.py` | 0.74× | 1.43× | 0.72× | 0.13× (*grind*) |

**The trade:** this book gives up some of TQQQ's rebound (1.60× against 1.91× at the median) to
cut its worst year from 0.45× to 0.88×, and it survives a bear twice as deep.

## What was built

`ForecastHarvestSizing` is Daily Ultimate (`daily_ultimate_sizing.py`) with the additions below.
Each is a parameter, and with all of them off (`whole_shares: false`) it is Daily Ultimate exactly,
blotter for blotter (`research/tests/test_forecast_harvest.py`).

It keeps Daily Ultimate's base, because the earlier research says that is where the money is:
- **The regime gates the buying.** The calm grid buys only while NATR(14) is below its 100-session
  median and TQQQ is within 50% of its one-year high. Ultimate's lesson is that a regime gating
  the buy side is what keeps a 3× fund's drawdown near 30% rather than 80%.
- **Turbulent markets get capitulation reversal lots** after a −8% session, and nothing else.
- **The calm lots are sold an hour into the first turbulent session.** This regime exit is the
  one sale that may realise a loss.
- **Lots are fixed-dollar, not compounded.** Daily Ultimate found compounding doubles the drawdown.

| Addition | What it does |
|---|---|
| `whole_shares` (default **on**) | Every buy is rounded down to whole shares at its fill price, and a buy worth less than one share is not made. Partial sales are whole shares too. |
| **The day / swing split** (`day_fraction`) | That share of each calm lot's shares is its **day part**; the rest is its **swing part**, sold at the run's target. The day part sells at the session's **day level**: the previous close × (1 + `day_k` × the report's `day_quantile`, p75 by default), kept between `day_target_min` and `day_target_max` above its cost. Without a report the quantile is the fund's own EWMA volatility (λ 0.94), so the level moves with or without one. It is recomputed at every session's open for every open day part. |
| `day_close_minute` | From this minute, a day part already up `day_target_min` is sold at the market: the day's gain banked, not carried. |
| **Report-sized lots** (`forecast_size_exponent`, `forecast_tilt`) | A calm lot × (own volatility / the report's σ)^exponent, clamped to `size_min`–`size_max`. Then × (1 + tilt × the report's median / σ): a report leaning down buys less, or nothing. |
| **The opening** (`trade_from`, `seed_levels`, `seed_lot_pct`, `seed_target`) | Nothing is bought before `trade_from`. At each listed fall below the first session's open, one **seed lot** of `seed_lot_pct` of the capital is bought once, whatever the regime says. A seed sells only at `seed_target`: the regime exit never sells it, and it is never split. |
| **The report** (`forecast_by_date`, `forecast_db`) | Research injects `{session: {p05, p25, p50, p75, p95}}`. Live reads the newest report for the session from the forecast database every checked report is kept in (`research/risk_overlay/forecasts.py`); no database, or no report, means the fund's own volatility. |

Nothing new can sell below cost. A day part sells at a profit target (at least `day_target_min`)
through `engine/trading/no_loss_guard.py`, and a seed sells only at its target.

**Live, every session starts cold,** so `resume()` rebuilds the lots each morning:
- **Seeds** are known by their persisted `Lot.entry_tag`.
- **An open day part** is known by its target, which is at most `day_target_max`.
- **Its swing target** is `swing_target`, set equal to the run's profit target on a deployment,
  as the pinned config and the profile do.
- **A seed ladder** is one run's opening: a restarted trader never seeds again.

## How it was measured

Every run is measured as Daily Ultimate's were (`tools/probe_daily_ultimate.py`'s `run_one`):
- intrabar fills booked **causally**;
- dynamic slippage of 0.5 bp plus 0.3 × the bar's range;
- **no yield on idle cash**;
- $250,000;
- bars from 2016-01-04, scored from 2017-01-03.

The new measure is **invested sessions banking a profit**. It is the share of sessions that opened
holding TQQQ and realised a profit before the close; sessions in cash are left out. Beside it:
- the share of all sessions banking a profit;
- the day parts' share of target-sale profit;
- a check that every buy and sale was whole shares, which they all were.

**The choice** is the highest geometric daily return within a 30% drawdown among designs that bank
a profit on at least half their invested sessions.

**Fake risk reports, lookahead by design.** For session t, the proxy report gives a one-day σ_t
(its 5–95 spread / 3.29), and r_t is the session's real close-to-close return. Then:
- z_t = r_t / σ_t;
- a report at accuracy ρ draws e_t ~ N(0, 1) from its seed and forms x_t = ρ z_t + √(1−ρ²) e_t;
- it states quantile q as σ_t (|ρ| x_t + √(1−ρ²) Φ⁻¹(q)).

So the report is calibrated for ρ ≥ 0. At ρ 0 it is the proxy's σ and nothing more, and at ρ 1 it
knows the close. At ρ < 0 it is as confident as |ρ| and wrong: it leans up before the down days.
Accuracies run from −0.3 to 1, with six seeds each. Beside them are the causal **proxy** reports
(`research/risk_overlay/proxy.py`: VXN and realised volatility) and no report at all.

## Results

### 1. Whole shares cost nothing at $250,000

| | /session | CAGR | max DD | 2017–21 | 2022 on |
|---|---|---|---|---|---|
| Daily Ultimate, fractional (lot 0.8%, +20%) | 0.158% | 48.8% | 29.9% | 0.218% | 0.097% |
| the same in whole shares | 0.158% | 48.8% | 29.9% | 0.218% | 0.097% |
| TQQQ held | 0.111% | 32.3% | 81.7% | 0.217% | 0.001% |

A $2,000 lot is about 48 shares at $41, so rounding down loses little.

### 2. The day / swing split: the same return, a shallower drawdown, and more sessions banked

There were 120 runs: 84 over lot × swing target × day fraction × day level, then 36 over the day
part's reach and its closing sale.

| Design (lot 0.8%, swing +20%) | /session | CAGR | max DD | Calmar | 2022 on | invested sessions banking a profit | all sessions |
|---|---|---|---|---|---|---|---|
| no split (Daily Ultimate) | 0.158% | 48.8% | 29.9% | 1.63 | 0.097% | 12% | 10% |
| ½ day part, level 1.5 × p75 | 0.158% | 48.6% | 26.9% | 1.81 | 0.092% | 29% | 23% |
| ½ day part, level 0.25 × p75, ≥ +0.2%, sold at the close from 375 | 0.157% | 48.5% | 26.5% | 1.83 | 0.091% | 47% | 37% |
| **¾ day part, level 0.25 × p75, ≥ +0.2%, sold at the close from 375** | **0.146%** | **44.2%** | **24.8%** | **1.78** | **0.079%** | **55%** | **43%** |
| the whole lot as its day part, same settings | 0.062–0.087% | 17–24% | 23–27% | 0.65–1.0 | 0.02% | 28–58% | |

- **Selling everything at the day level halves the return.** This is Daily Ultimate's finding
  again: TQQQ's money is in the lots that ride a trend for weeks.
- **A split keeps most of it.** A swing part of a quarter to a half of each lot, at +20%, carries
  the trend.
- **The day part takes the drawdown down.** It sells part of each lot within days, so less is
  left for the regime exit to sell at a loss. With ¾ as the day part, the regime exit's losses fell
  from $5.4M to $2.5M over the run.
- **The closing sale is what lifts the banked sessions** (47–55%, against 29–43% without it), at
  no cost to the return.
- **What "mostly daily" means here.** The design banks a profit on 55% of invested sessions, and
  44% of all sessions have a sale, against Daily Ultimate's 14%. But the day parts are only
  **~10% of the target-sale profit**. Most of the dollars still come from the swing parts and the
  reversal lots. No design that takes most of its dollars day by day keeps more than 0.087% a
  session.
- **The landscape is flat** across the day level and the minimum (0.144–0.146% for every ¾ cell),
  so the choice does not hang on a lucky cell.

### 3. The nightly report: worst, normal and best outcomes

192 runs on the chosen design (with 20% × 4 reversal lots), each reading its day level and lot size
from reports of one quality: none, the causal proxy, or synthetic ones at accuracy ρ from −0.3 to 1
(six seeds each). The report was used in five ways:
- **level:** the chosen 0.25 × p75;
- **level k1:** the level at the report's full p75;
- **+size:** lots × (own σ / the report's σ);
- **+tilt:** lots × (1 + 0.5 × median / σ);
- **k1+tilt:** both of the last two together.

| Report | level (the choice) | level k1 | level + tilt | level k1 + tilt | level + size |
|---|---|---|---|---|---|
| none (own volatility) | 0.146% / 24.8% | 0.145% / 25.5% | | | |
| proxy (VXN + realised vol) | 0.146% / 24.8% | 0.146% / 25.6% | 0.146% / 24.8% | 0.146% / 25.6% | 0.147% / 26.0% |
| **worst:** ρ −0.3 (confidently wrong) | 0.146% / 25.0% | 0.144% / 26.1% | 0.145% / 25.6% | **0.143% / 26.8%** (worst seed 0.142% / 27.4%) | 0.147% / 26.5% |
| ρ 0 (σ only) | 0.146% / 24.9% | 0.145% / 25.8% | 0.146% / 24.9% | 0.145% / 25.8% | 0.147% / 26.1% |
| **normal:** ρ 0.1–0.3 | 0.146% / 24.7–24.9% | 0.145–0.146% / 25.5–25.8% | 0.146–0.147% / 23.9–24.8% | 0.145–0.148% / 24.9–25.7% | 0.147% / 26.1–26.3% |
| ρ 0.5 | 0.146% / 24.9% | 0.149% / 24.4% | 0.147% / 23.9% | 0.150% / 23.7% | 0.149% / 26.9% |
| **best:** ρ 1 (knows the close) | 0.147% / 23.8% | 0.154% / 20.3% | 0.154% / 17.2% | **0.161% / 15.4%** | 0.153% / 27.9% |

Medians over seeds, per session / max drawdown.

- **The report cannot move the chosen configuration.** From a confidently wrong report to a perfect
  one, the gentle level gives 0.146–0.147% a session. The day level only moves where a small
  profit is taken; the minimum (+0.2%) and the closing sale do most of the selling.
- **A bolder use is a real bet on the report.** At k 1 with the tilt, a wrong report costs
  0.003% a session and 2 points of drawdown (2.6 at its worst seed). A ρ 0.5 report adds 0.004% and takes 1 point off;
  a perfect one adds 0.015% and takes 9 points off. **The break-even accuracy is about ρ 0.2.**
- **Sizing by the report's width (+size) adds drawdown at every accuracy** (26–28%). It buys
  bigger when the report expects a calm day, which TQQQ punishes. This matches the risk overlay's
  finding (docs/research/risk-overlay.md): risk levers on the buying cost the Ultimate books.
- **The proxy is ρ ≈ 0 for direction:** its median is always 0, so the tilt does nothing, and its
  σ only moves the level, which barely matters.
- **What it means for the LLM report:** follow it boldly only if it can call TQQQ's next close
  with a correlation near 0.5. The forecast database scores every report against its close (PIT,
  pinball, in the 50% and 90% ranges); a correlation between its median and the close over 60 or
  more scored sessions is the number that would justify `day_k: 1` and `forecast_tilt: 0.5`. One
  report has been scored so far.

### 4. How to start: from the four crossings, and the three bears deeper than 2022

Each run puts $250,000 in at the first close 43% below TQQQ's high and buys nothing before it. It
runs on the real bars for 2018-12-17, 2020-03-09, 2022-02-18 and 2025-04-03. It also runs on
`tools/stress_paths.py`'s *deeper* (2022 at 1.5×, to −92%), *grind* (to −95%) and *fast* (2020
made deeper, −84% in a month) bears, from the session each crossed −43%. Results are multiples of
the start.

**First, 15 opening plans with the design's 20% × 4 reversal lots.** The plans were no seed, and
seeds of 20–40% at the crossing or ladders down to −40%, each sold at +50% or +100%:

| Plan | Real: median after 1y | worst after 1y | median after 2y | worst low | Deeper bears: worst after 2y | worst low |
|---|---|---|---|---|---|---|
| **no seed** | 1.68× | **0.94×** | 2.69× | **0.73×** | **0.82×** | **0.38×** |
| seed 20% at the crossing, +100% | 1.71× | 0.79× | 2.56× | 0.64× | 0.69× | 0.33× |
| seed 40% at the crossing, +100% | 1.77× | 0.69× | 2.50× | 0.51× | 0.40× | 0.13× |
| ladder 3 × 10% at 0 / −15% / −30%, +50% | 1.75× | 0.85× | 2.72× | 0.67× | 0.55× | 0.23× |
| ladder 3 × 20% at 0 / −15% / −30%, +100% | 1.94× | 0.62× | 2.65× | 0.49× | 0.41× | 0.13× |
| deep 3 × 15% at −10% / −25% / −40%, +100% | 1.86× | 0.69× | 2.92× | 0.53× | 0.59× | 0.24× |

- **A seed buys a little median for a lot of tail.** The best ladder adds 0.26× at the median
  after a year, and costs 0.32× in 2022 and two thirds of what was left in the deeper bears.
- **The book already seeds itself.** Its turbulent mode buys reversal lots on capitulation
  closes, which is a seed bought on the worst days and sold within weeks.
- **That is also the tail.** With 20% reversal lots, four open could hold 80% of the capital in a
  bear, and the regime exit never sells them. In the *grind* bear that left 0.38×.

**Then the reversal lots themselves**, with no seed:

| Reversal lots | Full history /session | max DD | Real: median after 1y | worst after 1y | worst low | Deeper bears: worst after 2y | worst low |
|---|---|---|---|---|---|---|---|
| 20% × 4 (Daily Ultimate's) | 0.146% | 24.8% | 1.68× | 0.94× | 0.73× | 0.82× | 0.38× |
| 20% × 2 | 0.145% | 24.7% | 1.67× | 0.88× | 0.80× | 1.22× | 0.62× |
| **10% × 2 (the choice)** | **0.144%** | **24.5%** | **1.60×** | **0.88×** | **0.84×** | **1.43×** | **0.72×** |
| 10% × 4 | 0.144% | 24.5% | 1.61× | 0.91× | 0.80× | 1.23× | 0.69× |
| 5% × 2 | 0.143% | 24.3% | 1.57× | 0.88× | 0.83× | 1.47× | 0.76× |

10% × 2 costs 0.002% a session over the whole history. Against that it nearly doubles what is
left in a bear deeper than 2022 (0.72× against 0.38×) and holds the real crossings' worst low to
0.84×. That is the one departure from the sweep's rule, which would keep 20% × 4 for its 0.002%.

### How to start now

As of Nov 23, 2026, TQQQ closed Nov 20 at $40.99, 52.8% below its June 2 high:
- **The regime is turbulent.** It has been since Nov 6: NATR(14) is 11.7 against a 100-session
  median of 5.0, and TQQQ is more than 50% below its 250-session high.
- **So the book buys only reversal lots.** One lot of $25,000 (10% of $250,000), in whole shares,
  goes in the last 10 minutes of a session that is down 8% or more. At most two are open, and
  each sells at +8%.
- **The calm grid restarts by itself.** That needs NATR(14) below its median for five sessions,
  with TQQQ back within 50% of its one-year high: above $43.42 while the June high is in the
  window. Each calm lot is then $2,000, about 48 shares at $41: 36 in the day part and 12 in the
  swing part.
- **Not a seed or a lump sum.** In the minute engine, both lowered the worst outcomes more than
  they raised the median. Over 1985–2026, 3 of 18 crossings were followed by a 55–98% fall
  within a year.
- **The report stays advisory.** Keep checking it every night: the database's growing score is
  the evidence that would justify turning its weight up.

### 5. The aggressive profile: leaning on the report, day parts ~25% of the profit

`config/live_profiles/aggressive-forecast-harvest-tqqq.yaml` (pinned as
`config/forecast_harvest_aggressive_tqqq.yaml`) is `forecast-harvest-tqqq` with five changes and
nothing else (`research/tests/test_forecast_harvest.py` holds it there):

| | base | aggressive |
|---|---|---|
| day level (`day_k`) | prev close × (1 + 0.25 × p75) | **prev close × (1 + 2.5 × p75)**, ten times the report's weight |
| day target (`day_target_min` – `day_target_max`) | +0.2% – +4% | **+0.3% – +8%** |
| lot tilt (`forecast_tilt`) | none | **× (1 + 0.5 × the report's median / σ)**, none when it leans hard down |
| the report (`forecast_from_db`) | not read | **read each session from the forecast database** |

**How it was chosen** (`tools/probe_forecast_harvest.py --stage aggressive`). There were 29 runs,
all reading the causal proxy reports:
- the day level at 1, 1.5, 2 and 2.5 × p75;
- caps of +4% and +8%;
- floors from +0.2% to +0.5%;
- with and without the closing sale.

The rule was the highest daily return within a 30% drawdown, among runs whose day parts make
22–30% of the target-sale profit and that still bank a profit on half the invested sessions. The
day parts' share is now read from the blotter: a lot's first, partial sale at its target. The old
column counted any sale under +4%, which a higher cap would break.

| Run (closing sale at 375 unless noted) | /session | max DD | invested sessions banking | day parts' share |
|---|---|---|---|---|
| base (k 0.25, +0.2%–4%) | 0.144% | 24.5% | 54% | ~10% |
| k 1, +0.2% | 0.144% | 25.2% | 53% | 15% |
| k 2, +0.2% | 0.145% | 25.3% | 51% | 22% |
| **k 2.5, +0.3%–8% (the choice)** | **0.145%** | **25.4%** | **52%** | **25%** |
| k 2, +0.5% | 0.146% | 26.0% | 49% | 27% |
| k 2, no closing sale | 0.146–0.147% | 25.3–26.2% | 22–29% | 39–46% |

**Against reports of chosen accuracy** (`--stage aggressive2`, three seeds each):

| Report | /session | max DD | day parts' share |
|---|---|---|---|
| wrong (ρ −0.3) | 0.142–0.143% | 25.7–26.7% | 22–23% |
| none (own volatility) | 0.146% | 25.1% | 26% |
| proxy | 0.145% | 25.4% | 25% |
| ρ 0.2 | 0.145–0.148% | 24.1–25.2% | 26% |
| ρ 0.5 | 0.150–0.152% | 22.6–23.0% | 24% |
| perfect (ρ 1) | 0.161% | 14.4% | 23% |

- **This is a bet on the report.** The base configuration makes about 0.146% at every accuracy.
  This one loses about 0.003% a session to a wrong report, and gains about 0.006% with one right
  at ρ 0.5. Its break-even is about ρ 0.1–0.2.
- **The day parts make 22–26% of the profit whatever the report.** The closing sale with a +0.3%
  floor and the higher level are what put them there.
- **Started at the −43% crossings it is the base's book:** 1.61× after a year at the median and
  0.88× at the worst (2022). Its lowest point was 0.84× on the real crossings and 0.73× on the
  deeper bears.

### Paper trial

Both profiles pass paper-ultimate's own validation (`research/tests/test_live_profiles.py`), and a
switch keeps the open lots as a legacy book the new algorithm never sells. Before trusting real
money with either:
- **Switching** is from the Live page: Algorithm → profile `forecast-harvest-tqqq` or
  `aggressive-forecast-harvest-tqqq`.
- **The drawdown throttle.** `config/ultimate_paper.yaml` carries the reserve's throttle
  (`risk.dd_exposure_*`), which this book was not measured with. On Daily Ultimate it cost about a
  fifth of the return.
- **The forecast database.** paper-ultimate now mounts `warehouse/forecasts/` read-only
  (`docker-compose.yml`). The aggressive profile reads each session's report there at the open,
  so check every evening's report on the Live page, which is what stores it. A session with no
  report uses TQQQ's own volatility. The base profile does not read it, since the sweep found the
  report changes nothing measurable at its weight.
- **The paper account's size** sets what whole shares mean. A $2,000 lot needs the account at
  about $250,000 for the trial to match this research.

### The long history: 18 times a 3× Nasdaq-100 fell 43%

`tools/probe_crash_entries.py` builds a daily 3× Nasdaq-100 from 1985 (NDX × 3, less twice the fed
funds rate and a 0.95% fee). It tracks TQQQ's own closes with a daily correlation of 0.9986, and
34.1% CAGR against TQQQ's 36.4% over 2010–26. A crossing is the first close 43% below the
two-year high. From each of the 18 before 2026:

| From the crossing | after 1 year: worst | median | best | after 3 years: worst | median | best |
|---|---|---|---|---|---|---|
| **TQQQ held** | **0.02×** (2000) | 1.92× | 5.60× | 0.00× | 1.89× | 9.81× |
| seed 40% at the crossing, sold at +100% | 0.61× | 1.40× | 1.46× | 0.60× | 1.41× | 1.46× |
| ladder 3 × 15% at 0 / −20% / −40%, +100% | 0.56× | 1.16× | 1.47× | 0.55× | 1.16× | 1.48× |
| ladder 3 × 20% at 0 / −15% / −30%, +100% | 0.42× | 1.22× | 1.62× | 0.40× | 1.27× | 1.64× |
| ladder 4 × 10% at 0 / −10% / −20% / −30%, +100% | 0.61× | 1.13× | 1.41× | 0.60× | 1.20× | 1.42× |

The seed sleeve alone is shown with the rest in cash; the trading book beside it is section 4.

- **The base rate favours buying.** After 15 of the 18 crossings the fund was higher a year later,
  and the median outcome nearly doubled.
- **Three crossings were disasters:** 2000 (−98% a year later), 2008 (−87%) and 2022 (−55%). A
  3× fund does not come back from 2000 within any horizon here.
- **That is why the seed is capped:** a 40% seed loses at most 40% of the account, however bad the
  bear.
- **Deep rungs mostly do not fill.** Half the crossings never fell another 20%, so a ladder's
  lower rungs leave money in cash in the good cases and buy the bad ones.

## Caveats

- **The synthetic reports are a ruler, not evidence.** They say what accuracy would be worth, not
  that the LLM has it. One real report has been scored so far: Nov 20, whose close fell below its
  90% range.
- **Fixed-dollar lots fade as the account grows.** A lot is 0.8% of the starting $250,000, as
  Daily Ultimate measured it, so after years of growth the grid trades a small share of the
  account. The first two years are what a $250,000 start lives through, and section 4 measures
  them.
- **All results are backtests with causal fills and a slippage model.** The live Fidelity fills
  sat 0.3 bp inside the limit against the model's +1.5 bp (the tracking report), but TQQQ on
  Alpaca has not been traded with this book.
- **The minute warehouse begins in 2016:** four real crossings, plus three synthetic deeper bears
  (`tools/stress_paths.py`). The 1985–2026 history is daily, for the seed sleeve only.

## Reproducing it

```bash
export VAI_WAREHOUSE_DIR=<main>/warehouse VAI_EXTERNAL_DIR=<main>/data/external
python tools/build_proxy_reports.py --symbol TQQQ --out OUT/proxy
python tools/probe_forecast_harvest.py --stage design   --out OUT/runs --jobs 32
python tools/probe_forecast_harvest.py --stage design2  --out OUT/runs --jobs 32
python tools/probe_forecast_harvest.py --stage forecast --out OUT/runs --proxy OUT/proxy --jobs 40
python tools/probe_forecast_harvest.py --stage entry    --out OUT/runs --proxy OUT/proxy --jobs 40
python tools/probe_forecast_harvest.py --stage entry2   --out OUT/runs --proxy OUT/proxy --jobs 40
python tools/probe_forecast_harvest.py --stage aggressive  --out OUT/agg --proxy OUT/proxy --jobs 29
python tools/probe_forecast_harvest.py --stage aggressive2 --out OUT/agg --proxy OUT/proxy --jobs 21
python tools/probe_forecast_harvest.py --report OUT/runs
python tools/probe_crash_entries.py --out OUT/crash_entries.csv
```

A full-history run takes 1–11 minutes. The stages (482 runs) take about four hours on 40
cores.
