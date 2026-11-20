# Daily risk report — the nightly LLM forecast as the next session's risk

Nov 20, 2026 · **A plan: nothing here is built or measured yet** · for the TQQQ deployments
(`paper`, `paper-ultimate`, `live`, `fidelity`)

- [Goal](#goal)
- [Answer](#answer)
- [What already exists to build on](#what-already-exists-to-build-on)
- [Tonight's report, audited](#tonights-report-audited)
- [Design](#design)
- [Backtesting reports of differing risk on different days](#backtesting-reports-of-differing-risk-on-different-days)
- [Gates](#gates)
- [Phases](#phases)
- [Prompt changes (schema 1.2.0)](#prompt-changes-schema-120)
- [Owner decisions](#owner-decisions)
- [Tests](#tests)

## Goal

Every evening the owner runs a five-stage prompt through Google's LLM, with live web search. It
returns one JSON report (schema 1.1.0): data quality, regime, volatility state, an expected 1-day
move, overnight gap risk, a Kelly cap, the next day's catalysts, strategy weights, and return
distributions over 1, 5, 21, 63 and 252 sessions. The owner wants three things:

1. to drop that report on the Live page;
2. to have it set the risk the trading algorithm takes in the next session;
3. to know from backtests what reports of differing risk on different days would have done.

## Answer

| | |
|---|---|
| **What a report changes** | One session's **buying**: a size multiplier, an exposure ceiling, or a pause on new grid buys. Never a sale, a target, the regime or the strategy. |
| **Where** | The engine's risk clamp (`RiskManager.clamp_trade_value`). Backtest and live already share it, and it can only shrink a buy (0 ≤ approved ≤ proposed). |
| **Who decides** | Not the LLM. A versioned, deterministic **mapping** turns report fields into the overlay, inside bounds the deployment's YAML sets. The mapping is what gets backtested and promoted. |
| **How it gets in** | A new command, `apply_risk_report`. The Live page previews it, the server queues it, and the trader re-validates it, applies it to the report's target session and archives it. |
| **How it is backtested** | There are no historical LLM reports, and none can be made honestly: a model with web search replaying the past reads the future. So three sources stand in. **Proxy reports** are the same schema built causally from the warehouse's outside series (2011 on); they design and stress-test the mapping. **Synthetic schedules** (constant tiers, a risk-response matrix, an oracle, time-shifted nulls, perturbations) answer the differing-risk question. The **real reports**, archived from now on, are scored as forecasts every night and enter the same backtest as their history grows. |
| **What to expect** | Small effects. The closest precedent, the risk governor, bought about two points of drawdown on the reserve book and nothing measurable on Daily Ultimate ([its log](research/risk-governor.md)). |

What this deliberately does not do: switch algorithms day to day, sell anything, put an LLM on the
path from a bar to an order, or let a browser raise a limit above what the reviewed YAML trades.

## What already exists to build on

| Piece | Where | What it gives this plan |
|---|---|---|
| Risk governor | `research/strategies/risk_governor.py`, `daily_ultimate`'s `caution_*` parameters | A per-session pause from outside files, read at each session's cold start. Point-in-time cutoff, stale data abstains, and `caution_by_date` injects a `{session: paused}` map for research. Measured: a **pause** helps; a regime **veto** or **override** loses money. |
| Risk clamp | `engine/trading/risk_manager.py` | The portfolio-level clamp every buy passes through. It never grows a buy. Its docstring records why a ceiling off *current* equity works where shrinking a strategy's fixed lot did not. |
| Decision cycle | `engine/trading/decision_cycle.py` `evaluate_grid_decision` | The one place backtest and live size and clamp a buy. |
| Commands | `engine/trading/control_inbox.py`, `operator_control.py`, `server/live_control.py` | Intents queued as files, with `now`/`next_session` timings, supersession, TTLs, the cross-site guard and the real-money confirm. The directory is the audit trail, and the trader is the only writer. |
| Override beside the ledger | `research/strategies/live_algorithm.py` (`algorithm.json`) | The pattern for a file laid over the YAML at every start, which stops the start if it does not validate. |
| Grants | `LiveControlConfig` in `engine/core/config.py` | "Pausing new buys only ever reduces exposure, so it is always allowed"; every other grant comes from the YAML. |
| Outside series | `research/ml/sources.py`, `tools/refresh_external.py` (20:45 and 07:30 ET) | VIX, VIX9D, VIX3M, VXN, VIX1D, SKEW, VVIX, 2- and 10-year yields, DXY, WTI, high-yield OAS, NFCI, the OFR stress index, CFTC positioning and GEX, all point in time. Nearly every input the prompt searches the web for. |
| Calendars | `engine/data/fomc_calendar.py`, `event_calendar.py`, `data/external/fomc_calendar.csv` | FOMC decision days and earnings reaction sessions. There is no CPI, payrolls or UMich release calendar yet. |
| Measurement harness | `tools/probe_risk_governor.py`, `tools/probe_daily_ultimate.py`, `tools/stress_paths.py` | Staged runs (forms, frontier, robust, null, stress), 40 time-shifted null maps, and the stress paths. |
| Live shadow | `tools/track_live.py` (the `tracking` service, 20:40 ET) | A backtest of the algorithm in force on each session's bars: the place for a with-and-without-overlay counterfactual. |
| Validation | `research/optimization/walk_forward.py`, `monte_carlo.py` | Train/test folds and the block bootstrap. |
| Promotion | `engine/promotion.py` | The paper → live gate. |

## Tonight's report, audited

The 2026-11-20 report is kept as `tests/fixtures/risk_reports/tqqq_2026-11-20.json`. It is stamped
02:38 UTC, which is 21:38 ET on Nov 19, so its target session is Thursday Nov 20.

- **Its arithmetic holds.** Every horizon sums to 1.0000, the CDFs chain, the quantiles are
  monotone, `prob_positive` equals 1 − CDF(0) and the weights sum to 1.00.
- **Its bins hold almost nothing.** They are the schema's SPY template. The 1-day bins span ±2.5%
  against a 1-day σ of 7.91%, so the open-ended underflow and overflow carry 72% of the
  probability (64–65% from 21 days out). The prompt's own check that `mean_pct` and `std_pct` match
  the bin moments cannot be done. What is usable is the quantiles, the expected shortfall and the
  execution signals.
- **Its volatility can be checked.** An 8.38% expected move is 133% a year on TQQQ, about 44 on a
  QQQ volatility index. VXN, which the outside lake holds, says what options priced that evening.
  A large disagreement should downgrade the report (the mapping's step 1).
- **Two of its three missing inputs are already in the lake**: DXY (`yahoo_DXY`) and high-yield OAS
  (`fred_BAMLH0A0HYM2`). TQQQ's skew is what `fidelity_gateway/options_capture.py` began collecting
  on 2026-11-10. Handing the prompt our own numbers closes that gap
  ([prompt changes](#prompt-changes-schema-120)).
- **It fits in a command**: 5.8 KB as compact JSON, against the 16 KB a queued command may carry.

Under mapping v1 below it is a **tier 3** report: no new grid buys in the Nov 20 session, and
sells continue at their targets.

## Design

### Data flow

```
evening
  20:45 ET   market-inputs refreshes data/external/
  ~21:30     the prompt runs; its JSON is pasted or dropped on the Live page
             Check   -> server parses, audits and maps it, writes nothing, and shows the
                        findings and each deployment's overlay
             Apply   -> server queues apply_risk_report for each deployment chosen
                        (the id typed back for real money)
  between    the supervisor claims it, parses and maps it again (never trusting the server's
  sessions   parse), and writes control_dir/risk_reports/<session>.json

next morning
  start      cli.py live starts cold: algorithm.effective_config(), then today's overlay from
             risk_reports/ checked against the freshest outside data, then a RiskManager
             carrying it -- every buy's clamp
  trading    status.json names the overlay in force; decision.blocked says when it holds a
             buy back; server/live.py (read-only) carries both to the Live page
  20:40 ET   track_live: the shadow with and without the overlay, and the forecast scored
             against the close
```

### The overlay: what one session may be told

`engine/core/risk_overlay.py` (new, layer 0, standard library only):

| Field | Meaning | Bound |
|---|---|---|
| `session` | the NYSE session it applies to | exactly one |
| `pause` | no new buys, exempt ones excepted | |
| `buy_multiplier` | each proposed buy × this | `[0, 1]`: never grows a buy |
| `exposure_ceiling` | the share of equity open lots may hold | at least the YAML's `exposure_floor`; combined with the drawdown ramp by `min` |
| `blackouts` | UTC windows with no new buys, around catalysts | |
| `tier`, `reasons`, `mapping_id`, `report_sha256` | what the Live page and the journals say | |

`NEUTRAL` is the overlay that changes nothing. An `OverlaySchedule` maps sessions to overlays: a
session it does not name reads NEUTRAL, and `content_hash()` identifies the schedule.

### The engine seam

- `RiskManager(..., overlay: OverlaySchedule | None = None)`, and
  `clamp_trade_value(..., at: datetime | None = None)`. The order is the lot cap, then the pause,
  then the blackout, then the multiplier, then `min(the drawdown-ramped ceiling, the overlay's)`.
  With no schedule or `at=None`, the result is bit-for-bit today's, so the regression baseline does
  not move. `exposure_ceiling(drawdown, at)` gives the Live page's "blocked" line its number.
- `evaluate_grid_decision` passes `at=context.timestamp`, unless the strategy exempts the buy.
- **Exempt buys.** A duck-typed hook beside `next_lot_tag`, `SizingStrategy.risk_overlay_exempt()
  -> bool`, default False, asked once per buy (`decision_cycle.overlay_exempt`). The Ultimate
  family answers `self.mode == TURBULENT`: in that mode every buy is a capitulation reversal lot
  (`ultimate_sizing.py`'s `_grid_trigger_level`). A pause then lands on calm-grid buying alone,
  which is the form the governor measured. Whether reversal buys are exempt is a deployment
  setting, and the backtest runs it both ways.
- The live loop also clamps in `_exposure_room` and `_whole_share_refusal`. Both pass `at`.
- `cli.py` builds the session's `RiskManager` with its overlay and hands it to `LiveTradingLoop`,
  which today builds its own from `config.risk.build()`. Tightening mid-session swaps the trader's
  own overlay in place between ticks, with no rebuild.

### Config (frozen, validated up front)

```yaml
risk:
  overlay:
    mapping: v1               # a key of research/risk_overlay/mapping.py's MAPPINGS; opaque at the
                              # config layer, as strategy_id is
    source: reports           # live: the trader's risk_reports/. backtest: reports | proxy | schedule
    path: null                # backtest only: an archive directory or a schedule file
    exposure_floor: 0.10      # the lowest ceiling a report may set
    exempt: [reversal]        # buys a pause does not stop
    blackout_minutes: 0       # either side of a high-impact catalyst; 0 is off
    missing: neutral          # no valid report for the session: neutral | cautious (tier 1)
live:
  control:
    risk_reports: false       # whether the Live page may submit reports for this deployment
```

There is no `max_multiplier`. The clamp cannot grow a buy, so a report can only take risk *away*
from what the reviewed file trades. "More aggressive on calm days" becomes a larger researched
baseline in the YAML (stage `joint`), with the overlay scaling down from it on the other days. That
change is made in a reviewable file, never by a browser.

### The mapping (v1, pre-registered here)

`research/risk_overlay/mapping.py` (new) is a pure, deterministic `map_report(report, inputs) ->
SessionOverlay`. It is monotone (raising any risk input never loosens the overlay) and versioned by
id. It reads only fields the proxy also produces with the same meaning, so one mapping runs on
fifteen years of proxy reports and on the real ones.

1. **Abstain** to NEUTRAL (or tier 1 with `missing: cautious`) when the report is for another
   symbol or another session, arrived after its session ended, has a `confidence_score` below 0.6
   or `source_coverage: degraded`, or has a `base_price` more than 5% from our last close. When its
   expected move is outside 0.5× to 2× the move VXN implies, the proxy's volatility component
   replaces it, and the reasons say so.
2. **Score** S from 0 to 1, a weighted mean of five components:

   | Component | Report field | Score | Weight |
   |---|---|---|---|
   | volatility | `expected_1d_move_pct` ÷ the fund's median 1-day move over the research window | 0 at 1×, 1 at 2.5×, linear between | 0.35 |
   | gap | `overnight_gap_risk` | low 0, moderate 0.5, high 1 | 0.20 |
   | regime | `regime` | low_vol_uptrend 0, mean_reverting_range 0.2, breakout_expansion 0.5, event_driven 0.6, high_vol_downtrend 1 | 0.20 |
   | catalyst | `next_day_catalysts` inside the session | none 0, medium 0.5, high 1 | 0.15 |
   | tail | `skew_bias` | bullish_tail 0, neutral 0.5, bearish_tail 1 | 0.10 |

3. **Tier** by S. The thresholds are set by frequency on the proxy over 2011–2018 and then frozen
   as numbers: tier 3 on the riskiest 10% of sessions, tier 2 on the next 15%, tier 1 on the next
   25% (the governor paused 13%). Before that calibration they are provisionally 0.35, 0.55 and
   0.75.

   | Tier | New buys | Size | Exposure ceiling |
   |---|---|---|---|
   | 0 | yes | ×1.00 | the YAML's |
   | 1 | yes | ×0.75 | the YAML's |
   | 2 | yes | ×0.50 | min(the YAML's, 50%) |
   | 3 | paused, exempt buys excepted | | |

Fields v1 does not read, and why:

- `mean_pct` and `prob_positive` are a directional call one session ahead, which no evidence here
  supports.
- The 21-, 63- and 252-day horizons outlast the one session an overlay governs.
- `suggested_strategy_weights`: each deployment trades one researched strategy, so there is nothing
  to weight.
- `kelly_fraction_cap` is unanchored (0.15 of what?).

The last two have no proxy equivalent. They are variants measured on real reports only:
`1 − cash_defensive` as the exposure ceiling, and `kelly_fraction_cap` over its archive median as a
multiplier.

**Tonight's report:** the volatility component is 0.45 to 0.93 for any baseline move between 3.5%
and 5%, and every other component is 1, so S is 0.81 to 0.98. That is tier 3.

### Getting a report in: the command

| Piece | Change |
|---|---|
| `engine/trading/control_inbox.py` | `COMMAND_TYPES` gains `apply_risk_report` and `clear_risk_report` |
| `engine/trading/operator_control.py` | `_FAMILY`: both join a `risk_report` family, so a newer queued report supersedes an older one not yet applied |
| `server/live_control.py` | `_GRANT`: both need `risk_reports`. `POST /api/live/deployments/{id}/risk-report/preview` parses, audits and maps a report against that deployment's config, and writes nothing; the panel asks it once per deployment that takes reports. The command goes through the existing `.../{id}/commands` route. Both POSTs carry `same_origin`; real money needs the id typed back and a promoted mapping. |
| `engine/core/risk_report.py` (new) | the schema and its audit, standard library only: what the server, the trader, the tracking service and the backtests all parse with, so no two of them disagree |
| `research/risk_overlay/control.py` (new) | `risk_report_handlers(...)`, registered beside `algorithm_handlers` in `cli.py` (LoopControl) and `tools/market_hours_supervisor.py` (SupervisorControl). The trader parses and maps again, then writes `risk_reports/<session>.json` with the raw report, its SHA-256, the operator, the client address, the time received, the mapping id, the overlay and the outcome. |
| `cli.py` `cmd_live` | after `algorithm.effective_config()`: today's overlay from `risk_reports/`, re-checked against the freshest outside data, built into the `RiskManager`, printed, and written into `status.json` |
| `engine/trading/live_trading_loop.py` `_describe` | `blocked` names the report when the report is what holds a buy back |
| `server/live.py` | `GET /api/live/deployments/{id}/risk-reports`, read-only from the control directory |

The handler's rules:

- **A report applies to exactly one session**: the first whose window opens after `as_of`, where
  `as_of` falls after the previous session's close. An `as_of` inside a session is refused as not
  an end-of-day report.
- **Before the session opens**, a newer report replaces the old one. **After it opens**, a report
  that tightens applies at the next tick, and one that loosens is archived but not applied.
- **An operator pause and a circuit-breaker halt win.** A report cannot resume buying.
- **Real money takes one report a session.**

### The Live page

- `web/src/components/live/RiskReportPanel.tsx` (new). Paste or drop the JSON. **Check** shows the
  server's preview: the target session, the audit findings (hard failures refuse; warnings such as
  the bin coverage or a disagreement with VXN are shown), and the overlay in words for each TQQQ
  deployment that takes reports ("Thu Nov 20: no new grid buys; reversal lots allowed; sells
  unchanged"). Then **Apply to** the deployments chosen.
- `OverviewCard`: today's tier and the report it came from, with a history of tiers, the forecast
  against the realised move, and what the shadow says each overlay cost or saved.
- `lib/attention.ts`: "no risk report for today" (only where `missing: cautious`, or where the
  owner wants it) and "the trader refused tonight's report: …".
- The contract is hand-mirrored: `types/control.ts` (`CommandType`, `TraderStatus.risk_overlay`)
  and a new `types/riskReport.ts`, changed with the server's shapes.

## Backtesting reports of differing risk on different days

### Why there are no historical LLM reports to replay

None exist before 2026-11-20, and they cannot be made after the fact:

- Re-running the prompt "as of" a past date with live search reads what happened next.
- The model's training data knows how every session before its cutoff turned out: the 2020 crash,
  the 2022 bear. Fed only our point-in-time numbers, with dates and prices disguised and no web
  access (a **sealed replay**), it can still recognise the shape. Only sessions after its training
  cutoff are clean. A sealed replay before then is an ablation, labelled contaminated, and never
  evidence.

### Four sources, one archive format

| Source | Sessions | Lookahead | Used for |
|---|---|---|---|
| **Proxy reports** (`tools/build_proxy_reports.py`, new) | 2011 on (VIX9D); 2007 on without it | none by construction: inputs stamped before 04:00 UTC of the session, the fund's bars to the prior close | designing and stress-testing the mapping; the baseline the LLM must beat |
| **Synthetic schedules** | any | not applicable | constant tiers, the risk-response matrix, the oracle, nulls, perturbations |
| **Real reports** (archived from Phase 0) | 2026-11-20 on | none, if received before the session's first window | the forward test and the nightly scoring |
| Sealed replays (optional) | after the model's training cutoff | contaminated before it | an ablation only |

Each report is one JSON per (symbol, session): `{session, source: llm | proxy | synthetic | replay,
received_at, prompt_version, model, report, sha256}`. A flat `risk_reports.csv` holds the fields
the mappings read, for fast runs. A real report counts for session D only if `received_at` is
before D's first window.

### The proxy report

The proxy is the same schema built causally from data we already hold, a quant twin of the LLM:

| Field | Proxy rule (frozen with v1) |
|---|---|
| `expected_1d_move_pct` | 3 × VXN / √252, blended with the fund's 10-session realised σ |
| quantiles, `expected_shortfall_5pct` | a Student-t scaled to that move, its ν from the fund's trailing kurtosis, skewed by CBOE SKEW |
| `volatility_state` | the move's percentile over 252 sessions: below 20 compressed, below 70 normal, below 95 elevated, else extreme |
| `regime` | QQQ against its 50-session mean and its 20-session return, crossed with the volatility state; `event_driven` on an FOMC day |
| `overnight_gap_risk` | high when VIX9D/VIX is above 1 or an event comes before the open; moderate when VIX/VIX3M is above 0.95; else low |
| `skew_bias` | SKEW's 252-session percentile: above 80 bearish, below 20 bullish |
| `next_day_catalysts` | FOMC decisions and megacap earnings from the engine's calendars; CPI, payrolls, UMich and ISM once a release calendar exists (a data gap) |
| `data_quality` | the share of inputs fresh at the cutoff |

Credit comes from HYG/IEF, as the governor's does: FRED serves only three years of the high-yield
OAS. The proxy also anchors the real report each morning: the panel shows the two side by side,
field by field.

### Engine support for a schedule

- `risk.overlay.source: proxy | reports | schedule` builds an `OverlaySchedule` when the config is
  loaded. A probe can instead inject `{session: SessionOverlay}` directly, as `caution_by_date`
  does.
- **The schedule must be part of a result's identity.** The warehouse sink hashes a result from
  its row (`engine/warehouse/duckdb_sink.py` `split_row`, `engine/warehouse/hashing.py`).
  `_run_one_combination` puts the execution flags in that row but no `risk:` setting, so two runs
  that differ only in risk already collide as one simulation, the failure its own comment describes
  fixing for `fill_model`. The risk section, the overlay's mapping id and the schedule's hash go
  into the row first.
- **Per-run diagnostics**: sessions in each tier, buys paused or shrunk, dollars not deployed, and
  the return given up on paused sessions.
- **Cash yield both ways.** A schedule that holds cash back should be credited what that cash
  earns (`execution.cash_yield_pct: null`), and also measured without it, as the governor was.

### The stages (`tools/probe_risk_overlay.py`, new)

The books are the algorithms the deployments trade: the champion grid (`config/paper_aggressive.yaml`'s),
Ultimate (`config/ultimate_paper.yaml`'s, with its drawdown throttle) and Daily Ultimate
(`config/daily_ultimate_tqqq.yaml`). They are
measured as the governor was: causal intrabar fills, dynamic slippage, 2016-01-04 to the latest
session, scored from 2017-01-03, with the halves 2017–21 and 2022 on. Results are ranked by
Total Return % and Calmar.

| Stage | Question | Runs a book |
|---|---|---|
| `tiers` | What does each level of risk cost and buy when applied every session, regardless of any signal? Every session at ×1, ×0.75, ×0.5 and ×0.25; a 50% ceiling; a pause on a random 13% of sessions. | ~7 |
| `attribution` | Which sessions were bad ones to buy on? For each session of the tier-0 run: its lots, the share at target within 5 and 21 sessions, the capital-days locked, the worst excursion, how many are still open at the end. This is the label a report should predict. It is computed inside the worker, so no `SimulationResult` is kept. | 1 |
| `oracle` | What is the most any report could add? Pause (or set to tier 2) the worst 5, 10 and 20% of sessions by attribution. | 6 |
| `matrix` | **How much risk to take off on which kind of day.** Rows: the proxy's tier for the session. Columns: the response applied on those sessions only (×0.75, ×0.5, ×0.25, pause), every other session untouched. Each cell is one schedule, and its Δ return, Δ drawdown and Δ Calmar against no overlay are the answer for that day type and that dose. | 16 |
| `proxy` | Mapping v1 on proxy reports, in four forms: a binary pause, the graded tiers, a continuous ×(1 − S), and the ceiling alone. | 4 |
| `null` | Do the dates matter? 40 copies of the v1 schedule, each moved in time by a random offset: the same tiers in the same runs, on other dates. | 40 |
| `robust` | Thresholds ±0.05, weights ±50%, each component left out. A plateau, not a point. | ~15 |
| `walk` | Thresholds and the matrix's choices fitted on 2016–2021, frozen, and scored from 2022; then yearly folds. | ~10 |
| `stress` | `tools/stress_paths.py`'s `deeper`, `grind`, `fast`, `twice` and `top`: no harm on a worse path. | 10 |
| `perturb` | What does a wrong report cost? 10%, 25% and 50% of sessions' tiers randomised, the schedule inverted, always tier 3, always tier 0. | 6 |
| `catalysts` | The blackout alone, at ±10, 15 and 30 minutes around FOMC decisions (and other releases once their calendar exists), with the strategies' event-day boosts as researched. | 3 |
| `llm` | Recurring, once real reports accumulate: the LLM's schedule against the proxy's and against none, on the same sessions. | 3 |
| `joint` | Only if an overlay passes: re-fit the baseline lot size and ceiling with the overlay on. This is the one honest route to "more aggressive on calm days". | ~8 |

**The matrix answers the differing-risk question directly.** Reading across a row gives the
dose-response for that kind of day. The cell chosen in each row (on 2016–2021, checked from 2022)
becomes the mapping's tier table. Those four choices together are then run as one schedule: if the
result is far from the sum of their separate effects, the days interact through the book (its
cash, its lot cap), and the rows must be re-fit together.

**The oracle and the null bracket it.** A source of reports scores
`(schedule − null median) / (oracle − null median)`: the share of the attainable gain it captures.

**First, a cheap check before any engine run**: the AUC of the proxy's S at ranking the
attribution's bad sessions, year by year. If S cannot rank them, no schedule built on it will
help.

That is about 130 runs a book. The governor's runs took about 50 seconds each, and its whole
measurement under fifteen minutes on 40 cores.

### Scoring the forecasts every night

A few months of real reports give a P&L test no power. The forecast itself can be scored every
day. After the close, `tools/track_live.py` (calling `tools/score_risk_reports.py`, new) scores the
report that applied:

| Measure | Against |
|---|---|
| coverage of [p05, p95] (90% wanted) and [p25, p75] (50%), and the PIT histogram | the realised close-to-close return |
| mean pinball loss over the six quantiles (about the CRPS) | the same |
| realised \|return\| ÷ `expected_1d_move_pct` | the same |
| `volatility_state` against the realised range's percentile | the session's range |
| the 5-day horizon | the close five sessions later |

Each is computed for the LLM, for the proxy and for a naive baseline (a normal at VXN's implied
move). Skill is 1 − loss ÷ the baseline's loss, with a block-bootstrap interval. For **stability**,
the prompt runs twice on some nights: a tier that flips between two runs of the same prompt is noise
at the tier level.

### Statistics hygiene

- This document pre-registers mapping v1, its frequency thresholds and the stages. Every other
  variant tried is counted and reported; the governor's log counted about 160 scratch runs.
- Session-level differences (overlay minus none) are block-bootstrapped
  (`research/optimization/monte_carlo.py`), and the deflated Sharpe is reported for the chosen form.
- Nothing is promoted on the half of the history its choices were made on.

## Gates

| Step | Passes when |
|---|---|
| A proxy-driven overlay trades on paper | On the book as deployed: a better Calmar than no overlay in **both** halves; less than 5% of the baseline's return given up; the real schedule beats at least 36 of its 40 shifted copies on return over drawdown; no stress path more than a point worse in drawdown; a plateau in `robust`; and it holds in `walk`. |
| The LLM's reports drive it instead of the proxy's | At least 120 scored sessions; 1-day skill over the VXN baseline above 0, with its 90% interval clear of 0; the LLM schedule's shadow at least the proxy's over the same sessions; and tiers stable on a rerun on at least 80% of nights. |
| Real money | A passing paper `PromotionEvaluation` with the overlay on (at least 20 sessions), a promoted mapping id, and `live.control.risk_reports` granted in `config/production.yaml`. |

If nothing passes, the system keeps Phase 0 (archive and score) and the manual pause it already
has, and the write-up says so. If the proxy passes and the LLM adds nothing over it, the nightly
step is unnecessary: the proxy runs itself.

## Phases

| Phase | Work | Done when | Size |
|---|---|---|---|
| **0. Record and score** (no effect on trading) | the parser and audit (`engine/core/risk_report.py`), the archive, the Live page panel in record-only mode, the nightly scorecard; the prompt committed with a version | a report is archived one evening, and its scorecard row exists after the next close | S |
| **1. The seam** | `risk_overlay.py`, the `RiskManager` overlay and `at`, the `risk.overlay` and `live.control.risk_reports` config, the exemption hook, the command and its handlers, the risk section in the result row | the regression baseline is unchanged, and a parity test runs one schedule through backtest and live and gets the same buys | M |
| **2. Measure** | `build_proxy_reports.py`, `probe_risk_overlay.py`, every stage above | `docs/research/risk-overlay.md`, with the tables, the null and the gates' verdict | L |
| **3. Paper** | the passing mapping on `paper-ultimate` and/or `paper`, with the shadow with and without it | 20 or more sessions and a promotion record | M (calendar time) |
| **4. Real money** | an owner decision on the record | | |
| 5. Later | report features in the meta-label model (`research/ml/meta_*`); a CPI, payrolls and UMich release calendar; the prompt called by API on a schedule | | |

**Start Phase 0 first.** Every evening that goes unarchived is a session of real-report history lost.

## Prompt changes (schema 1.2.0)

1. **Scale the bins to the symbol.** Make the width a fixed share of the fund's typical move (for
   TQQQ, 1-day bins in 1.5% steps to ±15%) so they hold 90% or more of the mass. Or drop the bins and
   keep the quantiles.
2. **Hand it our numbers.** Paste `tools/refresh_external.py`'s reading into INPUT CONTEXT: VXN, the
   VIX term structure, yields, DXY, high-yield OAS, the last close and realised volatility. Ask the
   model to use them rather than search for them. What it adds is then what our data lacks: news,
   unscheduled events and the day's calendar. The comparison with the proxy measures exactly that.
3. **Add `target_session`, `prompt_version` and `model` fields**, and give catalysts full ISO
   timestamps rather than `HH:MM`.
4. **Replace the template's `"symbol": "SPY"`** with the target symbol.
5. **Set the temperature to 0**, where the interface allows it.

## Owner decisions

1. **De-risk only from the browser?** Proposed: yes. More risk on calm days comes only through a
   larger researched baseline in the YAML.
2. **No report for a session**: neutral (the researched baseline, as the governor's stale rule
   gives) or cautious (tier 1)?
3. **Which deployments take reports**, and whether real money ever does.
4. **The governor and the overlay together.** On `daily-ultimate-governed-tqqq` the two pauses
   overlap. Measure both, keep one?
5. **Blackouts against event boosts.** The strategies buy *more* on FOMC and earnings days
   (`event_day_boost_multiplier` 2.5), a measured effect. A blackout should not undo it without
   evidence of its own.
6. **A budget** for sealed replays and reruns, if wanted.

## Tests

Each test lives in the section that owns its subject, with clocks injected:

- `engine/tests/test_risk_report.py`: tonight's report parses; broken sums, CDFs, quantile order,
  enums, symbol and `as_of` are each refused, with every problem listed; the target session across
  weekends, holidays and DST.
- `engine/tests/test_risk_manager_overlay.py`: 0 ≤ approved ≤ proposed for random overlays; no
  overlay is identical to today; the pause, the blackout's edges, the ceiling's `min` with the
  drawdown ramp, exempt buys.
- `tests/test_task_7_1_live_backtest_parity.py`: the same schedule gives the same buys.
- `research/tests/test_risk_overlay_mapping.py`: monotone in every input, bounded, abstains as
  specified; tonight's report maps to tier 3, pinned.
- `research/tests/test_proxy_reports.py`: causal (changing any input after a session's cutoff
  leaves that session's report unchanged), and every proxy report passes the audit.
- `server/tests/test_server_capability.py`: the preview writes nothing, the command only enqueues,
  both POSTs carry `same_origin`, a report is refused without the grant, and real money needs the
  typed id.
- `engine/tests/test_operator_control.py`: supersession, loosening after the open refused, the
  archive written.
- `web/src/lib/riskReport.test.ts` and `attention.test.ts`.
