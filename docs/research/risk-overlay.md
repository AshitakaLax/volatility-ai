# The risk report overlay: the measurement

Nov 20, 2026 · Phase 2 of [docs/daily_risk_report_plan.md](../daily_risk_report_plan.md) ·
**Measured. No proxy-driven lever passes its gate, and a report would have to beat the proxy by a
wide margin before one could** (see [Status](#status))

The plan's question: how much should a nightly risk report change a session's buying, on which
kind of day, through which lever, and how accurate does a report have to be before following it
is worth anything? This page is the method and the record. The plan's [Gates](../daily_risk_report_plan.md#gates)
decide what happens with the answer.

## Status

The code for every stage exists and is tested on synthetic data:

| Piece | Where | Tested by |
|---|---|---|
| Proxy reports, built causally from the outside lake and the fund's bars | `research/risk_overlay/proxy.py`, `tools/build_proxy_reports.py` | `research/tests/test_proxy_reports.py` |
| Each fund's frozen baselines (median expected move, median 21/63-session ES5) | `tools/build_proxy_reports.py --baselines` → `research/risk_overlay/baselines.json` | `research/tests/test_risk_overlay_mapping.py` |
| The tier thresholds set by frequency on the proxy, 2011–2018 | `tools/build_proxy_reports.py --calibrate` | `tools/tests/test_build_proxy_reports.py` |
| Reports at a chosen accuracy (mixture, noisy, proxy+, and the error knobs) | `research/risk_overlay/synthetic.py` | `research/tests/test_synthetic_reports.py` |
| A backtest's schedule from an archive or a schedule file | `research/risk_overlay/schedules.py`, `risk.overlay.source`/`path` | `research/tests/test_risk_overlay_control.py` |
| Every stage, its report, and the AUC check | `tools/probe_risk_overlay.py` | `tools/tests/test_probe_risk_overlay.py` |

**Built and frozen on Nov 20, 2026** (step 1 below):
- **The TQQQ proxy archive:** 3,994 reports, 2011-01-04 to 2026-11-19, every one passing the
  audit.
- **TQQQ's baselines** (`research/risk_overlay/baselines.json`, over 2016-01-04 to 2026-11-19):
  a median expected move of 3.56%, and median expected shortfalls of −33.1% at 21 sessions and
  −56.2% at 63.
- **The tier thresholds:** S from 0.1002 (tier 1), 0.30075 (tier 2) and 0.4618 (tier 3), set on
  the 2,011 sessions of 2011–2018. They put 10.0% of those sessions in tier 3, 13.9% in tier 2,
  25.1% in tier 1 and 51.0% in tier 0, against the plan's 10/15/25/50. They were frozen before
  any backtest of the overlay. Over 2019–2026 the same thresholds give tier 3 on about 19% of
  sessions, because those years were rougher.

The engine runs (steps 2 and 3) are in [Results](#results): every stage, the `accuracy` stage's
6,123 runs included.

## Reproducing it

From a checkout of this branch, with the warehouse and the outside lake at their usual places (or
`VAI_WAREHOUSE_DIR` and `VAI_EXTERNAL_DIR` pointing at them):

```bash
# 1. Proxy reports for TQQQ from 2011, its baselines frozen, the tiers calibrated
python tools/build_proxy_reports.py --symbol TQQQ --out output/risk_overlay/proxy/TQQQ --baselines --calibrate
#    -> copy the printed thresholds into research/risk_overlay/mapping.py's TIER_THRESHOLDS,
#       set THRESHOLDS_PROVISIONAL = False, and commit baselines.json beside it

# 2. Each book's attribution, then the cheap check before any other engine run
P=output/risk_overlay/proxy/TQQQ; O=output/risk_overlay/runs
python tools/probe_risk_overlay.py --stage attribution --proxy $P --out $O --jobs 3
python tools/probe_risk_overlay.py --stage auc --proxy $P --out $O

# 3. Every stage, every book (about 420 runs a book without accuracy; 2,040 more with it)
python tools/probe_risk_overlay.py --stage all --proxy $P --out $O --jobs 40
python tools/probe_risk_overlay.py --report $O > docs/research/risk-overlay-results.md
```

A run already in `results.jsonl` is skipped, so an interrupted stage resumes where it stopped.

## What is measured, and how

**The books** are the three algorithms the TQQQ deployments trade:
- `grid`: the champion grid, `config/paper_aggressive.yaml`'s `hf_local_reference`.
- `ultimate`: `config/ultimate_paper.yaml`'s, with its drawdown throttle.
- `daily`: Daily Ultimate, `config/daily_ultimate_tqqq.yaml`.

Each is measured as the risk governor was:
- causal intrabar fills and dynamic slippage, with no cash yield;
- run from 2016-01-04 and scored from 2017-01-03;
- the halves 2017–21 and 2022 on reported separately;
- ranked by Calmar and total return.

**A schedule reaches the engine** as the deployments would trade it: an enforced
`SessionOverlay` per session on the `RiskManager` (the clamp's pause, blackout, multiplier and
ceiling) and the grid step (`session_step`). Behind that:
- With no schedule, a run is bit-for-bit the one before reports existed
  (`research/tests/test_regression_baseline.py`).
- One schedule gives the same buys in the backtest and the live loop
  (`tests/test_risk_overlay_parity.py`).
- Each run's row carries the schedule's hash, mapping and mode, so runs that differ only in risk
  never collide in the warehouse.
- Each run reports its overlay sessions, paused sessions, mean step multiplier, and the buys and
  dollars withheld.

**The stages** (`tools/probe_risk_overlay.py --stage NAME`) are the plan's:

| Stage | Question |
|---|---|
| `auc` | Does the proxy's score S rank the sessions that were bad to buy on? Bad means the share of that session's lots at target within 21 sessions is below the median, from the `attribution` run. This is checked year by year, before any other run. |
| `tiers` | What does each level of risk cost and buy, applied every session regardless of any signal? |
| `oracle` | What is the most any report could add? It pauses, or halves buys on, the worst 5, 10 and 20% of sessions by attribution. |
| `matrix` | The proxy's tier (rows) against a response (×0.75, ×0.5, ×0.25, pause), applied on those sessions only: the dose-response for each kind of day. |
| `proxy` | Mapping v1 on the proxy in four forms: a binary pause, the graded tiers, a continuous ×(1 − S), and the ceiling alone. |
| `spacing`, `weekly` | Lever B and lever G alone and with the others, over the plan's settings. |
| `null` | 40 copies of each lever's schedule, moved in time by random offsets. |
| `robust` | Thresholds ±0.05, each component left out, reversal buys not exempt. |
| `stress` | `tools/stress_paths.py`'s paths, with and without the tiers. |
| `perturb` | 10, 25 and 50% of tiers randomised; inverted; always tier 3; always tier 0. |
| `catalysts` | The blackout at 10, 15 and 30 minutes. |
| `priority` | Superseding both day-level levers, the governor alone, or neither. |
| `advisory` | An operator who follows a tier-3 pause with probability 0.5, 0.8 or 1, acting 0, 30 or 90 minutes after the open, over 20 seeds. |
| `accuracy` | The value-of-accuracy curves (below). |

`walk` is read from the others rather than run on its own. Each choice is made on 2017–21 (the
matrix's response per row, the robust variant) and scored from 2022.

### The value-of-accuracy curves

Synthetic reports are built from what actually happened next, with controlled randomness. That
is lookahead by design: they measure what accuracy is worth, never whether any source has it.

Each is the session's proxy report with the fields the mappings read replaced:

| Field | Measured against |
|---|---|
| the move | the session's \|return\| |
| the gap | its \|open/previous close − 1\| |
| the regime and the skew | the worst drawdown over the next 21 sessions |
| the 21- and 63-session ES5 | the worst drawdown from the open over each horizon |

How the replacement values are made:
- **A latent z per field.** Each field's truth, ranked over the whole history, is mixed with noise
  by the family's knob: mixture `p`, noisy `rho` or proxy+ `lambda`.
- **Values drawn from the proxy's own.** Each z is mapped back onto the proxy's distribution of
  that field, so every value is a realistic one.
- **The proxy's tier frequencies at every accuracy.** The daily tier is set by ranking the
  synthetic score onto the proxy's tiers, so accuracy changes which days are flagged and never
  how often.

The runs:
- Four levers: the tiers, B, G, and all three together.
- Three families: mixture and noisy at 0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9 and 1; proxy+ at 0, 0.1,
  0.2, 0.3 and 0.5.
- 20 seeds at every setting.
- Then the error knobs, one at a time on the noisy family at 0.2, 0.5 and 0.9: persistence 0.8,
  shared error 0.7, bias ±0.5, 10% missing, 30% of catalysts missed.

The report gives each lever's median Δ Calmar and its 10th–90th percentile band by accuracy. It
also gives each lever's break-even accuracies:
- **ρ\***: the lowest accuracy at which the median Δ Calmar is above zero.
- **ρ\*90**: the lowest at which 90% of seeds are above zero.

The nightly scorecard (`tools/score_risk_reports.py`) measures the real reports on the same
scale.

## Where this differs from the plan, and why

- **Ties in the calibration.** S takes few values on the proxy: four of its five components
  are categorical, and the volatility one is 0 on 74% of 2011–2018's sessions. One value, 0.10,
  is 15% of them by itself. A plain quantile lands on such a tie, and `S ≥ threshold` then takes
  the whole tie into the higher tier. The first calibration did that, giving 36/37/17/10% where
  the plan asks for 50/25/15/10%. `calibrate()` now picks, at each boundary, the cut nearest the
  plan's share, at a midpoint between two values so no score sits on a threshold.

- **No `tools/build_synthetic_reports.py`.** Writing about 2,500 synthetic archives of 2,700
  reports each would be about 30 GB. Each worker builds its synthetic history in memory from the
  proxy archive and the truths, deterministically from the run's family, accuracy and seed, so
  nothing is lost.
- **The proxy's realised volatility before 2016.** The warehouse's TQQQ bars begin on 2016-01-04,
  so the proxy's fund closes before then are QQQ's daily closes at three times the leverage. Only
  the proxy's inputs use this splice; a backtest never trades on it.
- **The regime and the skew read the 21-session drawdown.** Their truths are not otherwise
  defined, and a synthetic report's regime and skew must carry no information at accuracy 0. The
  catalysts are the calendars' either way, since they are scheduled.
- **The operator model's accuracy curve is not run.** The plan's fifth lever is the advisory
  operator at its middle setting on synthetic reports. The `advisory` stage measures that operator
  on the proxy; combining the two is a follow-up.
- **The bias knob moves each rank's quantile instead of z.** The plan's form, z + β before
  mapping, changes nothing: the quantile map keeps only ranks, and the score is ranked onto the
  proxy's tiers again afterwards. The first bias runs, named `complacent` and `alarmist`, came out
  identical to plain noise, which is how this was found. Now β moves each rank's normal quantile
  before its value is picked, in the fields and in the tiers (`synthetic.py`). On TQQQ from 2016,
  an alarmist history (β +0.5) puts 33% of sessions in tier 3 against the proxy's 18%, and a
  complacent one (β −0.5) puts 8% there. Those runs were redone as `bias -0.5` and `bias +0.5`; the
  report leaves out the old ones.
- **proxy+ draws no noise**, so its 20 seeds a setting are one run made 20 times. That is harmless
  apart from 1,140 runs of wasted time.

## Results

### The cheap check: does the proxy's S rank the bad sessions?

A session is bad for a book when fewer of the lots it bought reached their target within 21
sessions than on the book's median session. The median is 1.0 for all three books, so bad means
some lot did not. The pooled AUC across 2016–2026 has a 95% interval from a month-block
bootstrap:

| Book | Buying sessions | Bad | AUC of S | Bad rate in tiers 0 / 1 / 2 / 3 |
|---|---|---|---|---|
| grid | 2,737 | 269 | 0.570 (0.516–0.625) | 7.6% / 10.3% / 10.4% / 13.7% |
| ultimate | 846 | 353 | 0.449 (0.377–0.521) | 45% / 39% / 48% / 18% |
| daily | 725 | 162 | 0.469 (0.390–0.553) | 23% / 23% / 28% / 9% |

Year by year (`--stage auc`) the AUC swings with no pattern: 0.39–0.67 for the grid, 0.31–0.67
for Ultimate and 0.33–0.73 for Daily Ultimate.

- **Grid:** S ranks the bad sessions only weakly, though in the right direction, and the bad rate
  rises steadily with the tier.
- **Ultimate and Daily Ultimate:** S does not rank them. Their tier 3 sessions were their best
  buying days, and their bad rate in tier 3 is less than half that of tier 0. This matches the
  risk governor's finding that outside data does not help Daily Ultimate.
- **Gap risk and skew:** no component ranks better than S, and these two rank at chance on
  every book.

By the plan's rule, a schedule built on the proxy is not expected to help either Ultimate
book. The engine runs below were made anyway, for two reasons. The accuracy curves ask a
different question: how good a report would have to be, not how good the proxy is. And the
grid passes the check weakly.

### The engine runs (Nov 20, 2026; every stage but `accuracy`)

1,197 full-history backtests, 2016-01-04 to 2026-11-19, on the three books as deployed. Every
figure compares with the same book with no overlay:

| Book | CAGR | Max DD | Calmar |
|---|---|---|---|
| grid | 8.5% | 38.4% | 0.22 |
| ultimate | 27.5% | 16.5% | 1.67 |
| daily | 48.5% | 29.9% | 1.62 |

**The verdict: no lever driven by the proxy passes its gate on any book.** The gate asks for the
real schedule to beat at least 36 of its 40 time-shifted copies on Calmar. The closest is Daily
Ultimate's grid spacing, at 30:

| Shifted copies beaten (of 40) | Daily tiers | B, spacing | G, weekly cap |
|---|---|---|---|
| grid | 20 | 18 | 13 |
| ultimate | 29 | 17 | 13 |
| daily | 21 | 30 | 7 |

What each stage found:

- **`tiers`, the price of each response applied every session.**
  - Grid: each cut costs return roughly in proportion to its size, and Calmar falls with every one
    (0.18–0.21).
  - Ultimate: the cuts lose Calmar too, x0.25 most (1.67 to 0.96).
  - Daily Ultimate: buying less is better on Calmar *every* session. x0.5 gives 1.93 and x0.25
    gives 2.18, because it is sized past its best Calmar. So any overlay that buys less flatters
    this book, and only the shifted copies tell timing from size.
  - "x1.0" (an overlay that changes nothing but stands in for the strategy's own governor and
    event-day boosts) costs the grid 0.4 points of CAGR (its boosts) and Ultimate 0.6; it gives
    Daily Ultimate 0.2.
- **`oracle`, the most a report could add.**
  - Grid: a great deal. Pausing the worst 10% of sessions, known in hindsight, gives 9.9% CAGR at
    a 9.3% drawdown, a Calmar of 1.06 against 0.22. Halving buys on them gives 0.55.
  - Ultimate and Daily Ultimate: nothing. Every oracle form is within −0.21 to +0.00 of no
    overlay. A session whose lots miss target within 21 sessions is not what costs these books.
- **`matrix` and `proxy`, the proxy's own tiers.**
  - Grid: pausing its tier-3 sessions gives Calmar 0.20, and the four forms of mapping v1 give
    0.18–0.20, all below doing nothing. The best cells pause or quarter tier *1* (0.29–0.30, by
    cutting drawdown from 38% to 22–23%), but no other tier or response shows it, so it looks
    like chance.
  - Ultimate: the four forms give −0.04 to +0.01. Daily Ultimate: −0.06 to 0.00, and −0.15 for
    the 50% ceiling.
- **`spacing` (lever B).**
  - Grid: B alone gives back 0.00 to 0.03 of Calmar.
  - Daily Ultimate: B without the target following gives +0.05 to +0.06 (49.2% CAGR, 29.3%
    drawdown), the only positive lever measured, but it beats 30 of 40 shifted copies, not 36.
    With the target following it loses (−0.01 to −0.05).
- **`weekly` (lever G) never binds on the grid.** Every slope, horizon and reset gives the same
  8.1% and 39.3% as "x1.0": the grid's open lots never reach the cap. On Ultimate it moves
  Calmar by −0.01 to +0.02. On Daily Ultimate the steeper slopes cost up to 0.23, and the real
  schedule beats only 7 of its 40 copies.
- **`robust`.** Every variant of mapping v1 (thresholds ±0.05, each component left out) stays
  below no overlay on the grid (−0.04 to −0.07) and Ultimate (0.00 to −0.04). Making Ultimate's
  turbulent reversal buys subject to a pause costs more (Ultimate −0.08, Daily Ultimate −0.13),
  which supports the exemption.
- **`stress`, `tools/stress_paths.py`'s paths.** The tiers are insurance on the grid: they cut
  its drawdown by 5.5 to 16.4 points on every path, the most on the slow grind (82.4% to 66.0%),
  for 0.7 to 2.6 points of CAGR. On Ultimate they move drawdown by at most 1.1 points, and on
  Daily Ultimate by +0.3 to −3.7.
- **`perturb`.**
  - Inverting the tiers costs Ultimate far more than the real tiers do (Calmar 1.14 against
    1.63): pausing its calm sessions is what hurts it. So the real ordering beats its reverse,
    but not doing nothing. On the grid, inverted and real are alike (0.19 and 0.18).
  - "Always tier 3" stops the grid buying at all, and leaves Ultimate (0.20) and Daily Ultimate
    (0.23) only their exempt reversal buys.
- **`catalysts`.** A blackout of 10 to 30 minutes around high-impact events moves Calmar by −0.02
  on the grid, +0.02 to +0.03 on Ultimate and +0.01 to +0.02 on Daily Ultimate.
- **`priority`.** Superseding the governor, both day-level levers or neither changes Calmar by at
  most 0.01 on any book, so the `supersedes` default costs nothing measurable.
- **`advisory`, an operator following the proxy's tier-3 pauses by hand.** 20 seeds per setting:

  | Follows | Grid: d Calmar (seeds better) | Ultimate | Daily Ultimate |
  |---|---|---|---|
  | 50% | −0.013 (3–4 of 20) | −0.016 (0–2) | +0.005 (13–15) |
  | 80% | −0.019 (0) | −0.024 (0) | +0.008 (17–19) |
  | 100% | −0.024 (0) | −0.031 (0) | +0.004 (20) |

  Acting at once, or 30 or 90 minutes late, changes these by at most 0.006.

**What this leaves for the LLM's reports.** The proxy is the schema built from the outside lake.
On these books it is not a signal worth trading on its own: it does not rank the Ultimate
books' bad sessions, and its timing on the grid is no better than its shifted copies. The grid
is the only book with room to gain by the oracle. There, a report would have to pick out the
sessions that cost the grid far better than the proxy does. How good it must be is the
`accuracy` stage's question, next.

*The full `--report` output is [risk-overlay-results.md](risk-overlay-results.md).*

### The value of accuracy

There are 6,123 runs, 2,041 a book, plus 360 redone for the bias knob. Each figure is the median Δ
Calmar over 20 seeds, compared with the same book with no overlay. On the noisy family, ρ is
close to each field's rank correlation with its truth: at ρ 0.3 the six fields measure 0.29 to
0.35.

| Noisy ρ | 0 | 0.1 | 0.2 | 0.3 | 0.5 | 0.7 | 0.9 | 1 |
|---|---|---|---|---|---|---|---|---|
| grid, tiers | −0.06 | −0.04 | −0.02 | 0.00 | +0.05 | +0.12 | +0.16 | +0.16 |
| grid, all three | −0.06 | −0.05 | −0.03 | −0.01 | +0.04 | +0.11 | +0.14 | +0.14 |
| ultimate, tiers | 0.00 | +0.03 | +0.05 | +0.07 | +0.11 | +0.14 | +0.16 | +0.15 |
| ultimate, all three | 0.00 | +0.04 | +0.06 | +0.10 | +0.11 | +0.14 | +0.15 | +0.13 |
| daily, tiers | +0.12 | +0.22 | +0.23 | +0.34 | +0.46 | +0.58 | +0.71 | +0.86 |
| daily, all three | +0.18 | +0.27 | +0.35 | +0.48 | +0.63 | +0.80 | +1.01 | +1.17 |
| daily, G | 0.00 | +0.02 | +0.04 | +0.06 | +0.12 | +0.17 | +0.28 | +0.33 |

On proxy+, λ = 0 is the proxy itself, and λ adds back some of what the proxy missed:

| proxy+ λ | 0 | 0.1 | 0.2 | 0.3 | 0.5 |
|---|---|---|---|---|---|
| grid, tiers | −0.04 | −0.04 | −0.04 | −0.01 | +0.04 |
| ultimate, tiers | −0.04 | −0.02 | +0.01 | +0.03 | +0.07 |
| daily, tiers | −0.06 | −0.06 | −0.02 | +0.06 | +0.32 |
| daily, all three | −0.08 | −0.04 | +0.01 | +0.11 | +0.35 |

The break-even accuracies. λ\* is the lowest λ at which the median is above zero:

| Book, lever | ρ\* | ρ\*90 | λ\* | At accuracy 0 |
|---|---|---|---|---|
| grid, tiers | 0.5 | 0.5 | 0.5 | −0.06 |
| grid, all three | 0.5 | 0.7 | 0.5 | −0.06 |
| ultimate, tiers | 0.1 | 0.2 | 0.2 | 0.00 |
| ultimate, all three | 0.1 | 0.2 | 0.3 | 0.00 |
| daily, tiers | 0 | 0 | 0.3 | +0.12 |
| daily, all three | 0 | 0 | 0.2 | +0.18 |
| daily, G | 0 | 0.3 | 0.2 | 0.00 |

What the curves say:

- **The ceiling, at the proxy's tier frequencies.** A perfect report is worth +0.16 of Calmar to the grid (0.22 to 0.38) and +0.15
  to Ultimate (1.67 to 1.81). To Daily Ultimate it is worth +1.17 with all three levers (1.62 to
  2.79: 52.0% CAGR at an 18.6% drawdown, against 48.5% at 29.9%).
  - This is the reverse of the oracle. Pausing the Ultimate books' worst sessions by lot
    attribution gained nothing, but knowing the fund's next drawdowns gains a great deal: what
    costs these books is the drawdown, not lots missing their target.
  - On the grid the oracle (1.06) is far above this ceiling. Mapping v1 at the proxy's frequencies
    pauses 18% of sessions since 2016, while the oracle paused the grid's own worst 10%.
- **The return.** On the grid, the tiers give up 22 to 30% of the CAGR at every accuracy (6.0 to
  6.6% against 8.5%), so no report can meet the gate's "less than 5% of the return given up" with
  mapping v1. Ultimate gives up 5 to 10% and meets it only near ρ 1 (26.2% against 27.5%). Daily
  Ultimate gains return from ρ 0.3.
- **The cost of no skill** (accuracy 0) is −0.06 on the grid and nothing on Ultimate. On Daily
  Ultimate it is a gain, +0.12 to +0.18. Buying less on any days helps that book, since it is sized
  past its best Calmar (the `tiers` stage). So ρ\* = 0 there says nothing; what information adds is
  the curve's rise above its value at 0, already +0.10 at ρ 0.1.
- **Which levers carry the information.**
  - The plan expected the weekly cap (G) to need the least accuracy, then the spacing (B), then
    the daily pause. Instead the daily tiers carry almost all of it.
  - On the grid, B and G are flat at every accuracy (−0.03 and −0.02, the latter the cost of
    "x1.0").
  - On Ultimate, B is about 0 and G about +0.04, both flat, so G's small gain is not information.
  - Only on Daily Ultimate does G rise with accuracy (0 to +0.33). B starts at +0.06 at λ 0 and
    reaches +0.14 at ρ 1.
- **The proxy on the curve.** The nightly scorecard measures each field's rank correlation with
  what followed. Over 2016 to 2026, the proxy's correlations and what proxy+ adds to them:

  | Field (its truth) | Proxy | λ 0.2 | λ 0.3 | λ 0.5 |
  |---|---|---|---|---|
  | move (the session's \|return\|) | 0.40 | 0.59 | 0.67 | 0.79 |
  | gap (\|open/previous close − 1\|) | 0.26 | 0.31 | 0.39 | 0.57 |
  | regime (the next 21 sessions' drawdown) | 0.22 | 0.32 | 0.45 | 0.64 |
  | skew (the same) | −0.15 | −0.14 | −0.02 | 0.35 |
  | 21-session ES5 (the drawdown from the open) | 0.25 | 0.47 | 0.57 | 0.71 |
  | 63-session ES5 | 0.16 | 0.39 | 0.49 | 0.65 |

  - **ρ overstates the proxy.** On the noisy scale the proxy would clear Ultimate's ρ\*90 of 0.2 on
    four fields. Yet its own schedule loses on every book: −0.04 on the grid, −0.04 on Ultimate and
    −0.06 on Daily Ultimate. That is worse than random tiers on both Ultimate books.
  - **The likely reason.** The noisy family's errors are independent from day to day; the
    proxy's are not. What the proxy knows is the volatility state, which persists and which the
    books already answer, and its tier-3 days were the Ultimate books' best buying days (the AUC
    check).
  - **So the gate's test misleads.** A ρ read off the scorecard against ρ\*90 would have passed
    the proxy on Ultimate. λ is the scale that agrees with the engine.
- **The bar a report must clear: λ\*, what it adds over the proxy.** λ\* is 0.2 to 0.3 on the
  Ultimate books and 0.5 on the grid. At λ 0.3 the expected move would have to correlate 0.67
  with the session's |return|, against the proxy's 0.40. The 21-session shortfall would have to
  correlate 0.57 with the drawdown that follows, against 0.25. The plan's gate for the LLM's
  reports asks only for λ above 0. By these curves it should ask for λ above the lever's λ\*.
  That is the owner's decision.
- **The error knobs** (all three levers, the noisy family; median Δ Calmar at ρ 0.2 / 0.5 / 0.9):

  | Knob | grid | ultimate | daily |
  |---|---|---|---|
  | none | −0.03 / +0.04 / +0.14 | +0.06 / +0.11 / +0.15 | +0.35 / +0.63 / +1.01 |
  | persistence 0.8 | −0.02 / +0.06 / +0.14 | +0.02 / +0.10 / +0.15 | +0.32 / +0.66 / +1.03 |
  | shared error 0.7 | −0.04 / +0.02 / +0.13 | +0.04 / +0.09 / +0.16 | +0.26 / +0.53 / +0.96 |
  | 10% missing | −0.04 / +0.01 / +0.07 | +0.06 / +0.11 / +0.14 | +0.35 / +0.49 / +0.87 |
  | complacent, β −0.5 | −0.03 / 0.00 / +0.09 | +0.06 / +0.08 / +0.09 | +0.13 / +0.27 / +0.45 |
  | alarmist, β +0.5 | −0.05 / +0.03 / +0.13 | +0.02 / +0.14 / +0.19 | +0.46 / +0.98 / +1.58 |

  - No knob moves a break-even across one of the measured accuracies, so by the plan's
    robustness readout the curves hold. The nearest is a complacent report, which leaves the grid
    at 0.00 at ρ 0.5.
  - Missing reports cost the most where accuracy is high: half the grid's gain at ρ 0.9. A
    session without a report trades with no overlay at all.
  - Persistent errors cost Ultimate most at low accuracy (+0.02 against +0.06 at ρ 0.2).
  - The 30% catalyst miss changes nothing. The proxy's only catalysts are the engine's own
    calendar, which mapping v1 adds back to every report (`session_catalysts`).
  - **The bias matters most, and not as the plan expected.**
    - A complacent report, flagging fewer sessions, costs every book at high accuracy, Daily
      Ultimate most (+0.45 against +1.01 at ρ 0.9).
    - An alarmist one, flagging more, costs the grid a little but pays on both Ultimate books from
      ρ 0.5. On Ultimate it costs return as well (25.7% CAGR at ρ 0.9 against 27.5%). On Daily
      Ultimate it does not (51.0% at a 15.9% drawdown).
    - On Daily Ultimate at ρ 0.9 it reaches +1.58, above the ρ 1 figure of +1.17. So at the proxy's
      frequencies even a perfect report flags too few sessions for these books.
- **Perfect is not the best.** On Ultimate, ρ 0.9 is a little better than ρ 1 (+0.16 against
  +0.15). The truths are what the fund did, not what each book is scored on.

**What this means for the LLM's reports.** To drive a lever, a report must add to the outside
lake's information about as much again as the proxy already holds about the next session's move,
and more than that about the month's drawdown. Until the scorecard measures that over at least
120 sessions, the overlay should stay advisory on every book.

On the grid the problem is what the report is about, as well as how good it is.
- **Even a perfect report about the fund's path** costs the grid a quarter of its return.
- **Flagging fewer days does not fix that.** A complacent report, with 8% of sessions in tier 3,
  still gives up 16% of the return at ρ 0.9 (7.1% CAGR) and gains less Calmar.
- **The oracle shows what the grid needs instead:** its own worst sessions by how its lots turned
  out. Pausing those 10% raised its return to 9.9%. A report about the fund's next moves does not
  pick those sessions out, even when it is right.
