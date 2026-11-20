# The risk report overlay: the measurement

Nov 20, 2026 · Phase 2 of [docs/daily_risk_report_plan.md](../daily_risk_report_plan.md) ·
**The tools are built and tested; the runs on the real data have not been made yet** (see
[Status](#status))

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
| The tier thresholds set by frequency on the proxy, 2011–2018 | `tools/build_proxy_reports.py --calibrate` | |
| Reports at a chosen accuracy (mixture, noisy, proxy+, and the error knobs) | `research/risk_overlay/synthetic.py` | `research/tests/test_synthetic_reports.py` |
| A backtest's schedule from an archive or a schedule file | `research/risk_overlay/schedules.py`, `risk.overlay.source`/`path` | `research/tests/test_risk_overlay_control.py` |
| Every stage, its report, and the AUC check | `tools/probe_risk_overlay.py` | `tools/tests/test_probe_risk_overlay.py` |

**Not yet run:**
- No proxy archive has been built.
- `baselines.json` does not exist yet, so the mappings abstain for every fund ("no frozen
  baseline").
- The tier thresholds are still the plan's provisional 0.35, 0.55 and 0.75.

Running them needs the worktree's tools to read the warehouse and `data/external/`. The session
that built them was not permitted to. The commands are below.

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

## Results

*Pending the runs above.* When they exist:
- the `--report` output belongs beside this page;
- the gates' verdict for each lever is written here.
