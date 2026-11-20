# Daily risk report — the nightly LLM forecast as the next session's risk

Nov 20, 2026 · **Phases 0 and 1 are built; Phase 2's tools are built and its runs are pending** ([the measurement](research/risk-overlay.md)) · for the TQQQ deployments
(`paper`, `paper-ultimate`, `live`, `fidelity`) · the owner's decisions are recorded in
[Owner decisions](#owner-decisions)

- [Goal](#goal)
- [Answer](#answer)
- [What already exists to build on](#what-already-exists-to-build-on)
- [Tonight's report, audited](#tonights-report-audited)
- [Design](#design): [the levers](#the-levers-and-the-two-modes),
  [advisory mode (A)](#advisory-mode-a), [grid spacing (B)](#grid-spacing-from-the-expected-move-b),
  [weekly exposure cap (G)](#the-weekly-exposure-cap-g)
- [Backtesting reports of differing risk on different days](#backtesting-reports-of-differing-risk-on-different-days)
- [Backtesting at chosen levels of report accuracy](#backtesting-at-chosen-levels-of-report-accuracy)
- [Gates](#gates)
- [Phases](#phases)
- [Prompt changes (schema 1.2.0)](#prompt-changes-schema-120)
- [Owner decisions](#owner-decisions)
- [Tests](#tests)

## Goal

Every evening the owner runs a five-stage prompt through Google's LLM, with live web search. It
returns one JSON report (schema 1.1.0): data quality, regime, volatility state, an expected 1-day
move, overnight gap risk, a Kelly cap, the next day's catalysts, strategy weights, and return
distributions over 1, 5, 21, 63 and 252 sessions. The owner wants:

1. to drop that report on the Live page;
2. to have it set the risk the trading algorithm takes in the next session;
3. to know from backtests what reports of differing risk on different days would have done, and
   how accurate a report has to be before it is worth following.

## Answer

| | |
|---|---|
| **What a report changes** | One session's **buying**, through three levers: the daily tiers (a size multiplier, an exposure ceiling or a pause on new grid buys), **grid spacing** (a wider step on days the report expects a large move), and a **weekly exposure cap** from its 21- and 63-session tail risk. Never a sale, the regime or the strategy. |
| **Mode** | Each deployment runs the levers in **advisory** mode first: the overlay is computed, shown on the Live page, shadowed and logged, and you act with the existing Pause and Resume buttons. **Enforce** mode trades it, per deployment and per lever, once its gates pass. |
| **Where** | The engine's risk clamp (`RiskManager.clamp_trade_value`) and the step passed to the grid trigger. Backtest and live already share both. The clamp can only shrink a buy (0 ≤ approved ≤ proposed), and the step can only widen. |
| **Who decides** | Not the LLM. Versioned, deterministic **mappings** turn report fields into the overlay, inside bounds the deployment's YAML sets. The mappings are what get backtested and promoted. |
| **Priority** | On a session a report sets, the report is the day's risk decision: the risk governor's pause and the FOMC and earnings-day boosts stand down, and the report's own catalysts (checked against the engine's FOMC and earnings calendars) take their place. With no report the session trades exactly as configured, governor and boosts included. |
| **How it gets in** | A new command, `apply_risk_report`. The Live page previews it, the server queues it, and the trader re-validates it, applies it to the report's target session and archives it. |
| **How it is backtested** | There are no historical LLM reports, and none can be made honestly: a model with web search replaying the past reads the future. Four sources stand in. **Proxy reports** are the same schema built causally from the warehouse's outside series (2011 on); they design and stress-test the mappings. **Synthetic schedules** (constant tiers, a risk-response matrix, an oracle, time-shifted nulls, perturbations) answer the differing-risk question. **Reports at a chosen accuracy** are built from what actually happened next, with a controlled amount of randomness, to measure how much each lever gains or loses as accuracy runs from none to perfect. The **real reports**, archived from now on, are scored every night on that same accuracy scale. |
| **What to expect** | Small effects. The closest precedent, the risk governor, bought about two points of drawdown on the reserve book and nothing measurable on Daily Ultimate ([its log](research/risk-governor.md)). |

What this deliberately does not do: switch algorithms day to day, sell anything, put an LLM on the
path from a bar to an order, or let a browser raise a limit above what the reviewed YAML trades.

## What already exists to build on

| Piece | Where | What it gives this plan |
|---|---|---|
| Risk governor | `research/strategies/risk_governor.py`, `daily_ultimate`'s `caution_*` parameters | A per-session pause from outside files, read at each session's cold start. Point-in-time cutoff, stale data abstains, and `caution_by_date` injects a `{session: paused}` map for research. Measured: a **pause** helps; a regime **veto** or **override** loses money. |
| Risk clamp | `engine/trading/risk_manager.py` | The portfolio-level clamp every buy passes through. It never grows a buy. Its docstring records why a ceiling off *current* equity works where shrinking a strategy's fixed lot did not. |
| Decision cycle | `engine/trading/decision_cycle.py` `evaluate_grid_decision` | The one place backtest and live size and clamp a buy, with the step passed in by the caller. |
| Commands | `engine/trading/control_inbox.py`, `operator_control.py`, `server/live_control.py` | Intents queued as files, with `now`/`next_session` timings, supersession, TTLs, the cross-site guard and the real-money confirm. The directory is the audit trail, and the trader is the only writer. |
| Override beside the ledger | `research/strategies/live_algorithm.py` (`algorithm.json`) | The pattern for a file laid over the YAML at every start, which stops the start if it does not validate. |
| Grants | `LiveControlConfig` in `engine/core/config.py` | "Pausing new buys only ever reduces exposure, so it is always allowed"; every other grant comes from the YAML. |
| Outside series | `research/ml/sources.py`, `tools/refresh_external.py` (20:45 and 07:30 ET) | VIX, VIX9D, VIX3M, VIX6M, VXN, VIX1D, SKEW, VVIX, 2- and 10-year yields, DXY, WTI, high-yield OAS, NFCI, the OFR stress index, CFTC positioning and GEX, all point in time. Nearly every input the prompt searches the web for. |
| Calendars | `engine/data/fomc_calendar.py`, `event_calendar.py`, `data/external/fomc_calendar.csv` | FOMC decision days and earnings reaction sessions. There is no CPI, payrolls or UMich release calendar yet. |
| Measurement harness | `tools/probe_risk_governor.py`, `tools/probe_daily_ultimate.py`, `tools/stress_paths.py` | Staged runs (forms, frontier, robust, null, stress), 40 time-shifted null maps, and the stress paths. |
| Live shadow | `tools/track_live.py` (the `tracking` service, 20:40 ET) | A backtest of the algorithm in force on each session's bars: the place for the as-traded, as-suggested and no-report counterfactuals. |
| Validation | `research/optimization/walk_forward.py`, `monte_carlo.py` | Train/test folds and the block bootstrap. |
| Promotion | `engine/promotion.py` | The paper → live gate. |

## Tonight's report, audited

The 2026-11-20 report is kept as `tests/fixtures/risk_reports/tqqq_2026-11-20.json`. It is stamped
02:38 UTC, which is 21:38 ET on Thursday Nov 19, so its target session is Friday Nov 20.

- **Its arithmetic holds.** Every horizon sums to 1.0000, the CDFs chain, the quantiles are
  monotone, `prob_positive` equals 1 − CDF(0) and the weights sum to 1.00.
- **Its bins hold almost nothing.** They are the schema's SPY template. The 1-day bins span ±2.5%
  against a 1-day σ of 7.91%, so the open-ended underflow and overflow carry 72% of the
  probability (64–65% from 21 days out). The prompt's own check that `mean_pct` and `std_pct` match
  the bin moments cannot be done. What is usable is the quantiles, the expected shortfall and the
  execution signals.
- **Its volatility can be checked.** An 8.38% expected move is 133% a year on TQQQ, about 44 on a
  QQQ volatility index. VXN, which the outside lake holds, says what options priced that evening.
  A large disagreement should downgrade the report (the daily mapping's step 1).
- **Two of its three missing inputs are already in the lake**: DXY (`yahoo_DXY`) and high-yield OAS
  (`fred_BAMLH0A0HYM2`). TQQQ's skew is what `fidelity_gateway/options_capture.py` began collecting
  on 2026-11-10. Handing the prompt our own numbers closes that gap
  ([prompt changes](#prompt-changes-schema-120)).
- **It fits in a command**: 5.8 KB as compact JSON, against the 16 KB a queued command may carry.

What each lever would make of it:

| Lever | Tonight |
|---|---|
| Daily tiers | **tier 3**: no new grid buys in the Nov 20 session; sells continue at their targets |
| Grid spacing | step ×1.7 to ×2.4 for any baseline move between 3.5% and 5%: the champion grid's 0.075% becomes about 0.13–0.18% |
| Weekly cap | a Thursday report can only tighten this week's cap. Its 21-session ES5 of −53.9% sets a ceiling once the proxy supplies the baseline: at an illustrative baseline of −30%, the ratio is 1.8 and the ceiling 60% of equity |
| Mode | advisory: all three are shown and logged, and a "Pause buys" suggestion is offered; nothing is enforced |

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
             risk_reports/ checked against the freshest outside data. In enforce mode the
             RiskManager and the step carry it; in advisory mode they trade the YAML and the
             overlay is only reported.
  trading    status.json names the overlay (in force, or suggested); decision.blocked says
             when it holds a buy back; server/live.py (read-only) carries both to the Live page
  20:40 ET   track_live: the shadows (as traded, as suggested, no report), whether a
             suggestion was followed, and the forecast scored against the close
```

### The levers and the two modes

| Lever | Report fields | What changes | Cadence | Allowed direction |
|---|---|---|---|---|
| **Daily tiers** (mapping v1) | expected move, gap risk, regime, catalysts, skew | buy size ×, exposure ceiling, pause | each session | down only |
| **B. Grid spacing** | `expected_1d_move_pct` | the grid step for the session's buys; optionally the target of lots bought that session | each session | the step only widens; the target follows only where the YAML opts in |
| **G. Weekly exposure cap** | `next_month` (and `next_quarter`) expected shortfall and p05 | an exposure ceiling held for the week | weekly | down only; tightens mid-week, loosens only at the weekly reset |

A deployment's YAML chooses which levers it takes and its **mode**:

- **`advisory`** (the default): the trader builds the session's overlay exactly as enforce would,
  reports it and archives it, and trades the YAML. This is lever **A**.
- **`enforce`**: the overlay trades.

The session's final overlay combines the levers:

- the pause, if the daily tier is 3;
- the buy multiplier, from the daily tier;
- the step multiplier, from B;
- the exposure ceiling, the `min` of the YAML's (with its drawdown ramp), the daily tier's and the
  week's.

### The overlay: what one session may be told

`engine/core/risk_overlay.py` (new, layer 0, standard library only):

| Field | Meaning | Bound |
|---|---|---|
| `session` | the NYSE session it applies to | exactly one |
| `pause` | no new buys, exempt ones excepted | |
| `buy_multiplier` | each proposed buy × this | `[0, 1]`: never grows a buy |
| `exposure_ceiling` | the share of equity open lots may hold: the `min` of the daily and weekly ceilings | at least the YAML's `exposure_floor`; combined with the drawdown ramp by `min` |
| `step_multiplier` | the grid step × this, for buys decided this session | `[1, spacing.max_multiplier]`: never narrower than the YAML's step |
| `target_multiplier` | the profit target × this, for lots bought this session | 1 unless `spacing.target_follows`; then equal to `step_multiplier` |
| `blackouts` | UTC windows with no new buys, around catalysts | |
| `supersedes` | the strategy's day-level levers this session's report replaces (`governor`, `event_boosts`) | only those the YAML's `risk.overlay.supersedes` names; empty on a session no report set |
| `mode` | `advisory` or `enforce` | the YAML's |
| `tier`, `weekly_ceiling`, `reasons`, `mapping_id`, `report_sha256` | what the Live page and the journals say | |

`NEUTRAL` is the overlay that changes nothing, `supersedes` included: a session without a report
keeps the governor and the boosts. An `OverlaySchedule` maps sessions to overlays: a session it
does not name reads NEUTRAL, and `content_hash()` identifies the schedule.

### The engine seam

- `RiskManager(..., overlay: OverlaySchedule | None = None)`, and
  `clamp_trade_value(..., at: datetime | None = None)`. The order is the lot cap, then the pause,
  then the blackout, then the multiplier, then `min(the drawdown-ramped ceiling, the overlay's)`.
  With no schedule or `at=None`, the result is bit-for-bit today's, so the regression baseline does
  not move. `exposure_ceiling(drawdown, at)` gives the Live page's "blocked" line its number.
- `evaluate_grid_decision` passes `at=context.timestamp`, unless the strategy exempts the buy.
- **The step (B).** The grid trigger is the strategy's own (`_grid_trigger_level(context,
  last_buy_price, step)`), but the step is always the caller's argument. One helper,
  `risk_overlay.session_step(step, overlay)`, gives every call site the session's step: the
  backtest's close and intrabar branches in `optimization_controller.py` `_simulate_single`, and the
  live loop's buy path, `_describe` and `_buy_level`. Every strategy that takes a step widens with
  it; Ultimate's turbulent-mode reversal level ignores the step, so reversal buys are untouched.
- **The target (B, opt-in).** Where a lot is opened (the backtest's `_apply_buy_fill`, the live
  loop's order placement), its target is the profit target × `target_multiplier`. The no-loss
  guard checks the sale like any other.
- **Exempt buys.** A duck-typed hook beside `next_lot_tag`, `SizingStrategy.risk_overlay_exempt()
  -> bool`, default False, asked once per buy (`decision_cycle.overlay_exempt`). The Ultimate
  family answers `self.mode == TURBULENT`: in that mode every buy is a capitulation reversal lot
  (`ultimate_sizing.py`'s `_grid_trigger_level`). A pause then lands on calm-grid buying alone,
  which is the form the governor measured. Whether reversal buys are exempt is a deployment
  setting, and the backtest runs it both ways.
- **The report's priority.** The governor and the boosts live inside strategies, which the clamp
  cannot reach, so the overlay tells them through the bar's snapshot: a new
  `MarketContext.report_supersedes: frozenset[str]` (default empty, so every existing run is
  unchanged), filled from the schedule where the backtest builds its contexts
  (`optimization_controller.py` `_simulate_single`) and where the live loop does
  (`live_trading_loop.py`). Two strategies read it:
  - `DailyUltimateSizing.record_tick`: with `governor` in it, the session is not `cautious`
    whatever the votes say, and its diagnostics say the report superseded them.
  - `HighFrequencyLocalReferenceSizing`'s event multipliers (`is_macro_event_day`,
    `is_earnings_reaction_day`, the weighted event boost): with `event_boosts` in it, each is
    ×1. Ultimate and Daily Ultimate inherit this.
- **Advisory mode** passes no overlay to the `RiskManager`, `session_step` or the context, so an
  advisory session trades exactly what the YAML trades. The overlay goes to `status.json` and the
  archive only.
- The live loop also clamps in `_exposure_room` and `_whole_share_refusal`. Both pass `at`.
- `cli.py` builds the session's `RiskManager` with its overlay and hands it to `LiveTradingLoop`,
  which today builds its own from `config.risk.build()`. Tightening mid-session swaps the trader's
  own overlay in place between ticks, with no rebuild.

### Config (frozen, validated up front)

```yaml
risk:
  overlay:
    mode: advisory            # advisory: computed, shown, shadowed and logged, not traded | enforce
    mapping: v1               # a key of research/risk_overlay/mapping.py's MAPPINGS; opaque at the
                              # config layer, as strategy_id is
    source: reports           # live: the trader's risk_reports/. backtest: reports | proxy |
                              # synthetic | schedule
    path: null                # backtest only: an archive directory or a schedule file
    exposure_floor: 0.10      # the lowest ceiling a report may set
    exempt: [reversal]        # buys a pause does not stop
    blackout_minutes: 0       # either side of a high-impact catalyst; 0 is off
    supersedes: [governor, event_boosts]   # the day-level levers a session's report replaces;
                                           # [] applies the report after them instead
    daily: true               # the v1 tiers: size, ceiling, pause
    spacing:                  # B
      enabled: true
      exponent: 1.0           # step x (expected move / baseline move) ^ exponent
      max_multiplier: 4.0     # never wider than this; never narrower than live.step
      target_follows: false   # lots bought this session get target x the same factor
    weekly:                   # G
      enabled: true
      horizon: next_month     # next_month | next_quarter | max (the tighter of the two)
      slope: 0.5              # ceiling = 1 - slope x (tail ratio - 1)
      reset: monday           # the week's first session takes a new cap
      max_age_days: 7         # the newest report at most this old sets the week
live:
  control:
    risk_reports: false       # whether the Live page may submit reports for this deployment
```

There is no `max_multiplier` on buy size. The clamp cannot grow a buy and the step cannot narrow,
so a report can only take risk *away* from what the reviewed file trades. "More aggressive on calm
days" becomes a larger researched baseline in the YAML (stage `joint`), with the overlay scaling
down from it on the other days. That change is made in a reviewable file, never by a browser.

**The two exceptions are the YAML's own.** Where `supersedes` names the governor, a calm report
lifts a pause the governor would have called for that session; dropping the event boosts can only
lower buying. Where `spacing.target_follows` is on, lots bought on a wide-step day carry a larger
target and are held longer. Both are the owner's choice, made in the deployment's file, not by the
report.

### The daily tiers (mapping v1, pre-registered here)

`research/risk_overlay/mapping.py` (new) holds every mapping as a pure, deterministic function,
versioned by id. `map_report(report, inputs) -> SessionOverlay` is monotone: raising any risk input
never loosens the overlay. The daily tiers read only fields the proxy also produces with the same
meaning, so one mapping runs on fifteen years of proxy reports and on the real ones.

1. **Abstain** to NEUTRAL, so the session trades as configured, when the report is for another
   symbol or another session, arrived after its session ended, has a `confidence_score` below 0.6
   or `source_coverage: degraded`, or has a `base_price` more than 5% from our last close. When its
   expected move is outside 0.5× to 2× the move VXN implies, the proxy's volatility component
   replaces it (for the tiers and for B), and the reasons say so.
2. **Score** S from 0 to 1, a weighted mean of five components:

   | Component | Report field | Score | Weight |
   |---|---|---|---|
   | volatility | `expected_1d_move_pct` ÷ the fund's median 1-day move over the research window | 0 at 1×, 1 at 2.5×, linear between | 0.35 |
   | gap | `overnight_gap_risk` | low 0, moderate 0.5, high 1 | 0.20 |
   | regime | `regime` | low_vol_uptrend 0, mean_reverting_range 0.2, breakout_expansion 0.5, event_driven 0.6, high_vol_downtrend 1 | 0.20 |
   | catalyst | `next_day_catalysts` inside the session, merged with the engine's own FOMC and earnings calendars (an FOMC decision or a megacap reaction session the report missed is added as high) | none 0, medium 0.5, high 1 | 0.15 |
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

Fields no mapping reads, and why:

- `mean_pct` and `prob_positive` are a directional call one session ahead, which no evidence here
  supports.
- `suggested_strategy_weights`: each deployment trades one researched strategy, so there is nothing
  to weight.
- `kelly_fraction_cap` is unanchored (0.15 of what?).

The last two have no proxy equivalent. They are variants measured on real reports only:
`1 − cash_defensive` as the exposure ceiling, and `kelly_fraction_cap` over its archive median as a
multiplier.

**Tonight's report:** the volatility component is 0.45 to 0.93 for any baseline move between 3.5%
and 5%, and every other component is 1, so S is 0.81 to 0.98. That is tier 3.

### Advisory mode (A)

The first way the report touches trading, and the default for every deployment that takes reports.

- **What is shown.** The trader builds the overlay at session start and writes it into
  `status.json` as a suggestion: "Suggested for today: tier 3, pause new grid buys; grid step ×2.1;
  this week's cap 60%". The Live page shows it beside the proxy's suggestion for the same session.
- **What you can act on.** The pause, with the existing Pause buys and Resume buys commands
  (resuming needs `live.control.resume_buys`, as now). When the suggestion is a pause and buying is
  on, the panel puts a Pause buys button beside it. Size, spacing and the weekly cap have no button;
  they are shown and shadowed.
- **What is logged.** Each session's archive records the suggestion. The tracking service joins it
  with the command log (who paused or resumed, and when) and records, per session:
  - whether the suggestion was followed, not followed or followed late;
  - three shadows on the session's bars: **as traded**, **as suggested** (every lever enforced) and
    **no report**.
- **What it builds.** The Live page keeps the running tally ("followed 14 of 20 suggestions;
  enforcing would have changed realised profit by …"). That is the evidence for moving a deployment
  to `enforce`, a change to its YAML, one lever at a time.
- **Its backtest** is the `advisory` stage: an operator model that follows a tier-3 pause with a
  given probability, a given number of minutes after the open, and never acts on tiers 1 and 2.

Advisory mode needs no change to the engine: the mappings, the archive and a few lines in `cli.py`
that write the suggestion. That is why it comes first ([Phases](#phases)).

### Grid spacing from the expected move (B)

On a day the report expects an 8% move, a 0.075% step triggers hundreds of buys on the way down.
Spacing the grid to the day's expected range buys the same dip in fewer, deeper lots.

- **The factor.** `step_multiplier = clip((move / baseline) ^ exponent, 1, max_multiplier)`, where
  `move` is the report's `expected_1d_move_pct` after the VXN cross-check and `baseline` is the
  fund's median 1-day move over the research window, the same baseline the daily tiers use.
  Defaults: exponent 1 (spacing in proportion to the expected move), at most ×4.
- **Widen only.** A calm report never narrows the step below `live.step`, which is the owner's
  "only reduce risk" decision applied to spacing.
- **The target (opt-in).** `target_follows: true` gives lots bought that session the same factor on
  their profit target, which keeps the target-to-step ratio the champion was researched at
  (`config/paper_aggressive.yaml`'s note: "a target near 6x the step is what actually cycles"). It
  is off by default, because a larger target holds a lot longer.
- **Against the vol scaling already there.** The strategies already shrink lots when *realised*
  volatility rises (`vol_scale_exponent -1.5` over 0.25 against 10 sessions). B adds the
  *forward-looking* view, from implied volatility and the report. The stages measure B on the books
  as deployed, vol scaling on.
- **Exempt buys** are untouched: Ultimate's reversal level does not read the step.

### The weekly exposure cap (G)

The long horizons are the report's least checkable fields, and a daily decision from them would be
mostly noise. Held for a week, five reports' worth of error averages out, and the decision matches
the horizon the field describes.

- **Who sets it.** At the week's first session, the newest report received before it and at most
  `max_age_days` old (normally the Friday or Sunday evening report). If there is none, the week is
  NEUTRAL, as decided for a missing report.
- **The ceiling.** The tail ratio is `r = |ES5| ÷ |baseline ES5|` for the chosen horizon's
  `expected_shortfall_5pct` (21 sessions by default; `max` takes the tighter of 21 and 63), where
  the baseline is the fund's median for that horizon over the research window, from the proxy.
  Then `ceiling = clip(1 − slope × (r − 1), exposure_floor, 1)`: no cap at r ≤ 1, 50% of equity at
  r = 2 with the default slope, the floor beyond.
- **During the week.** A later report whose ceiling is lower tightens the cap at once (the next
  tick live; the next session in a backtest). A higher one waits for the next reset.
- **With the other ceilings.** The session's ceiling is the `min` of the YAML's (with its drawdown
  ramp), the daily tier's and the week's.

### Getting a report in: the command

| Piece | Change |
|---|---|
| `engine/trading/control_inbox.py` | `COMMAND_TYPES` gains `apply_risk_report` and `clear_risk_report` |
| `engine/trading/operator_control.py` | `_FAMILY`: both join a `risk_report` family, so a newer queued report supersedes an older one not yet applied |
| `server/live_control.py` | `_GRANT`: both need `risk_reports`. `POST /api/live/deployments/{id}/risk-report/preview` parses, audits and maps a report against that deployment's config, and writes nothing; the panel asks it once per deployment that takes reports. The command goes through the existing `.../{id}/commands` route. Both POSTs carry `same_origin`; real money needs the id typed back and a promoted mapping. |
| `engine/core/risk_report.py` (new) | the schema and its audit, standard library only: what the server, the trader, the tracking service and the backtests all parse with, so no two of them disagree |
| `research/risk_overlay/control.py` (new) | `risk_report_handlers(...)`, registered beside `algorithm_handlers` in `cli.py` (LoopControl) and `tools/market_hours_supervisor.py` (SupervisorControl). The trader parses and maps again, then writes `risk_reports/<session>.json` with the raw report, its SHA-256, the operator, the client address, the time received, the mapping id, the overlay, the mode and the outcome. |
| `cli.py` `cmd_live` | after `algorithm.effective_config()`: today's overlay from `risk_reports/` (and the week's cap), re-checked against the freshest outside data; in enforce mode built into the `RiskManager` and the step; in either mode printed and written into `status.json` |
| `engine/trading/live_trading_loop.py` `_describe` | `blocked` names the report when the report is what holds a buy back; the decision carries the session's step |
| `server/live.py` | `GET /api/live/deployments/{id}/risk-reports`, read-only from the control directory |

The handler's rules:

- **A report applies to exactly one session**: the first whose window opens after `as_of`, where
  `as_of` falls after the previous session's close. An `as_of` inside a session is refused as not
  an end-of-day report. The weekly cap reads the archive under its own rule (above).
- **Before the session opens**, a newer report replaces the old one. **After it opens**, a report
  that tightens applies at the next tick, and one that loosens is archived but not applied.
- **An operator pause and a circuit-breaker halt win.** A report cannot resume buying.
- **Real money takes one report a session.**

### The Live page

- `web/src/components/live/RiskReportPanel.tsx` (new). Paste or drop the JSON. **Check** shows the
  server's preview: the target session, the audit findings (hard failures refuse; warnings such as
  the bin coverage or a disagreement with VXN are shown), and the overlay in words for each TQQQ
  deployment that takes reports ("Thu Nov 20: no new grid buys; grid step ×2.1; reversal lots
  allowed; sells unchanged"). **Apply to** lists every deployment whose YAML takes reports, paper
  and real money alike, each with a checkbox, all checked by default; unchecking one leaves it out
  of that report. Real-money deployments still ask for their id typed back.
- `OverviewCard`: today's overlay and whether it is **in force** or **suggested**, the report it
  came from, or "no report: trading as configured". Beneath it, a history of sessions: the tier,
  the step and the week's cap; the forecast against the realised move; whether a suggestion was
  followed; and what the shadows say each overlay cost or saved.
- `lib/attention.ts`: "the trader refused tonight's report: …". A session without a report is
  not an attention item; it trades as configured.
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

### Five sources, one archive format

| Source | Sessions | Lookahead | Used for |
|---|---|---|---|
| **Proxy reports** (`tools/build_proxy_reports.py`, new) | 2011 on (VIX9D); 2007 on without it | none by construction: inputs stamped before 04:00 UTC of the session, the fund's bars to the prior close | designing and stress-testing the mappings; the baseline the LLM must beat |
| **Synthetic schedules** | any | not applicable | constant tiers, the risk-response matrix, the oracle, nulls, perturbations |
| **Reports at a chosen accuracy** (`tools/build_synthetic_reports.py`, new) | any session with a known future | **deliberate hindsight**, mixed with controlled randomness | the value-of-accuracy curves ([below](#backtesting-at-chosen-levels-of-report-accuracy)); never evidence of an edge |
| **Real reports** (archived from Phase 0) | 2026-11-20 on | none, if received before the session's first window | the forward test and the nightly scoring |
| Sealed replays (optional) | after the model's training cutoff | contaminated before it | an ablation only |

Each report is one JSON per (symbol, session): `{session, source: llm | proxy | synthetic |
replay, received_at, prompt_version, model, report, sha256}`, and for a synthetic report its
`family`, `accuracy` and `seed`. A flat `risk_reports.csv` holds the fields the mappings read, for
fast runs. A real report counts for session D only if `received_at` is before D's first window.

### The proxy report

The proxy is the same schema built causally from data we already hold, a quant twin of the LLM:

| Field | Proxy rule (frozen with v1) |
|---|---|
| `expected_1d_move_pct` | 3 × VXN / √252, blended with the fund's 10-session realised σ |
| 1-day quantiles, `expected_shortfall_5pct` | a Student-t scaled to that move, its ν from the fund's trailing kurtosis, skewed by CBOE SKEW |
| 21- and 63-session quantiles and ES5 (for G) | VXN's 30-day implied σ (and VIX6M's slope for 63 sessions) scaled to the horizon, ×3, with the same Student-t tails |
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

- `risk.overlay.source: proxy | reports | synthetic | schedule` builds an `OverlaySchedule` when the
  config is loaded. A probe can instead inject `{session: SessionOverlay}` directly, as
  `caution_by_date` does.
- **The schedule must be part of a result's identity.** The warehouse sink hashes a result from
  its row (`engine/warehouse/duckdb_sink.py` `split_row`, `engine/warehouse/hashing.py`).
  `_run_one_combination` puts the execution flags in that row but no `risk:` setting, so two runs
  that differ only in risk already collide as one simulation, the failure its own comment describes
  fixing for `fill_model`. The risk section, the overlay's mapping id and mode, and the schedule's
  hash go into the row first.
- **Per-run diagnostics**: sessions in each tier, the mean step multiplier, sessions under each
  weekly cap, buys paused or shrunk, dollars not deployed, and the return given up on paused
  sessions.
- **Cash yield both ways.** A schedule that holds cash back should be credited what that cash
  earns (`execution.cash_yield_pct: null`), and also measured without it, as the governor was.

### The stages (`tools/probe_risk_overlay.py`, new)

The books are the algorithms the deployments trade: the champion grid (`config/paper_aggressive.yaml`'s),
Ultimate (`config/ultimate_paper.yaml`'s, with its drawdown throttle) and Daily Ultimate
(`config/daily_ultimate_tqqq.yaml`). They are measured as the governor was: causal intrabar fills,
dynamic slippage, 2016-01-04 to the latest session, scored from 2017-01-03, with the halves 2017–21
and 2022 on. Results are ranked by Total Return % and Calmar.

| Stage | Question | Runs a book |
|---|---|---|
| `tiers` | What does each level of risk cost and buy when applied every session, regardless of any signal? Every session at ×1, ×0.75, ×0.5 and ×0.25; a 50% ceiling; a pause on a random 13% of sessions. | ~7 |
| `attribution` | Which sessions were bad ones to buy on? For each session of the tier-0 run: its lots, the share at target within 5 and 21 sessions, the capital-days locked, the worst excursion, how many are still open at the end. This is the label a report should predict. It is computed inside the worker, so no `SimulationResult` is kept. | 1 |
| `oracle` | What is the most any report could add? Pause (or set to tier 2) the worst 5, 10 and 20% of sessions by attribution. | 6 |
| `matrix` | **How much risk to take off on which kind of day.** Rows: the proxy's tier for the session. Columns: the response applied on those sessions only (×0.75, ×0.5, ×0.25, pause), every other session untouched. Each cell is one schedule, and its Δ return, Δ drawdown and Δ Calmar against no overlay are the answer for that day type and that dose. | 16 |
| `proxy` | Mapping v1 on proxy reports, in four forms: a binary pause, the graded tiers, a continuous ×(1 − S), and the ceiling alone. | 4 |
| `spacing` | B alone and with the tiers: exponent 0.5 and 1, at most ×2 and ×4, the target following or not. | ~10 |
| `weekly` | G alone and with the others: 21 sessions, 63 or the tighter; slope 0.25, 0.5 and 1; reset on Mondays or every five sessions. | ~10 |
| `null` | Do the dates matter? 40 copies of each lever's schedule, each moved in time by a random offset: the same settings in the same runs, on other dates. | 40 a lever |
| `robust` | Thresholds ±0.05, weights ±50%, each component left out. A plateau, not a point. | ~15 |
| `walk` | Thresholds and the matrix's choices fitted on 2016–2021, frozen, and scored from 2022; then yearly folds. | ~10 |
| `stress` | `tools/stress_paths.py`'s `deeper`, `grind`, `fast`, `twice` and `top`: no harm on a worse path. | 10 |
| `perturb` | What does a wrong report cost? 10%, 25% and 50% of sessions' tiers randomised, the schedule inverted, always tier 3, always tier 0. | 6 |
| `catalysts` | The blackout alone, at ±10, 15 and 30 minutes around FOMC decisions (and other releases once their calendar exists), with the strategies' event-day boosts as researched. | 3 |
| `priority` | What does the report's priority cost or buy? The v1 schedule three ways: superseding the governor and the event boosts (the owner's choice), superseding the governor alone, and applied after both (`supersedes: []`). On the champion grid the governor is absent, so this isolates the boosts; on Daily Ultimate the governed profile adds the governor. The boosts were a measured gain (2.5× on FOMC days), and on report sessions they are given up. | 3 |
| `advisory` | A as a human runs it: an operator who follows a tier-3 pause with probability 0.5, 0.8 or 1, acting 0, 30 or 90 minutes after the open, and never acting on tiers 1 and 2. 20 seeds each, for which days the operator misses. | ~180 |
| `accuracy` | Each lever at chosen levels of report accuracy ([next section](#backtesting-at-chosen-levels-of-report-accuracy)). | ~2,500 |
| `llm` | Recurring, once real reports accumulate: the LLM's schedule against the proxy's and against none, on the same sessions, for each lever. | ~10 |
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

Without the accuracy stage that is about 420 runs a book, most of them the nulls and the operator
model. The governor's runs took about 50 seconds each, and its whole measurement under fifteen
minutes on 40 cores; at that rate this is about nine minutes a book.

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
| **accuracy**, on the scale the synthetic reports use: the rank correlation of `expected_1d_move_pct` with the realised move, of `overnight_gap_risk` with the realised gap, and of the 21-session ES5 with the worst drawdown over the next 21 sessions | the realised values, as each becomes known |

Each is computed for the LLM, for the proxy and for a naive baseline (a normal at VXN's implied
move). Skill is 1 − loss ÷ the baseline's loss, with a block-bootstrap interval. For **stability**,
the prompt runs twice on some nights: a tier that flips between two runs of the same prompt is noise
at the tier level.

### Statistics hygiene

- This document pre-registers mapping v1, the spacing and weekly formulas with their defaults, the
  frequency thresholds and the stages. Every other variant tried is counted and reported; the
  governor's log counted about 160 scratch runs.
- Session-level differences (overlay minus none) are block-bootstrapped
  (`research/optimization/monte_carlo.py`), and the deflated Sharpe is reported for the chosen form.
- Nothing is promoted on the half of the history its choices were made on.

## Backtesting at chosen levels of report accuracy

The real LLM's accuracy will not be known for months, and the proxy's is a single point. This
section measures **how much each lever gains or loses as a report's accuracy runs from none to
perfect**. Reports are built for past sessions from what actually happened next, with a controlled
amount of randomness in which days they get wrong. The result is a curve for each lever. Once the
real reports' accuracy is measured on the same scale, the curve says what following them is worth.

`research/risk_overlay/synthetic.py` (new) builds them and `tools/build_synthetic_reports.py` (new)
writes them, in the archive format with `source: synthetic`.

### 1. The truth for each session, from what came after

| Truth | Measured from the bars after session D's report |
|---|---|
| move | the absolute close-to-close return of D, and D's realised σ from its minute bars |
| gap | the absolute move from D−1's close to D's open |
| direction | the sign of D's close-to-close return |
| 21- and 63-session tail | the worst drawdown from D's open over the next 21 (63) sessions |
| buy quality | the `attribution` label: the share of D's lots at target within 5 and 21 sessions |
| catalysts | the calendar's events in D (scheduled, so known ahead either way) |

This is lookahead by design and is labelled so. A synthetic report is a ruler for how much
accuracy is worth, never evidence that any source has it.

### 2. Three families of report

Each field gets a latent signal z (a standard normal), built from the truth's rank over the whole
history (`z_truth`) and noise:

| Family | How a session's report is made | Accuracy knob |
|---|---|---|
| **mixture** (the plain one) | on each session, with probability p the report is built from that session's truth; otherwise from the truth of a randomly drawn other session (from the whole history, so a wrong report carries no information, not even the year's regime) | p, the share of days the report tells the truth |
| **noisy** | `z = ρ·z_truth + √(1−ρ²)·e`: every day partly right | ρ, the rank correlation with the truth, exact by construction |
| **proxy+** | the proxy plus some of what the proxy missed: `z = standardise(z_proxy + λ·z_resid + σ·e)`, where `z_resid` is the part of the truth the proxy did not predict | λ, the skill *beyond the proxy*: the real question for the LLM |

### 3. Realistic values at every accuracy

Each latent z is turned back into a report value by **quantile mapping**: z's rank among the
sessions picks the value at that rank in the proxy's distribution of the same field. Every
synthetic report therefore has realistic values and the **same tier frequencies as the proxy,
whatever the accuracy**: accuracy changes *which* days are flagged, never how often. Categorical
fields follow from the mapped values by the proxy's own rules, the quantiles and ES scale with the
mapped move, and every synthetic report must pass the audit.

### 4. The other ways a report goes wrong

| Knob | Values | What it models |
|---|---|---|
| persistence φ | 0, 0.8 | errors that last: AR(1) noise, `e_D = φ·e_{D−1} + √(1−φ²)·u_D`. A report wrong for weeks in a crash costs more than one wrong on scattered days |
| shared error η | 0, 0.7 | how far one misreading spreads across fields: `e_field = √η·e_common + √(1−η)·e_own`. A report that misreads the regime usually misreads the volatility too |
| bias β | −0.5, 0, +0.5 (in z units) | a habitually complacent or alarmist forecaster: z + β before mapping. Alarmist costs missed buys; complacent costs drawdown |
| direction ρ_dir | 0 (default), 0.2 | skill on the sign of the next return. No lever reads it, so it should change nothing; a check that none leaks it |
| missing rate | 0, 10% | sessions with no report, which trade as configured |
| catalyst miss rate | 0, 30% | scheduled events the report leaves out. The engine's calendars add FOMC and megacap earnings back; other releases stay missing |
| seeds | 20 a setting | which days are wrong. The spread across seeds is the variety of outcomes one accuracy level can produce |

### 5. The runs and what they give

Five levers are swept:

- the daily tiers, B and G, each alone;
- all three together;
- A's operator model at its middle setting: 80% of pauses followed, 30 minutes after the open.

Each runs on the mixture and noisy families at p or ρ ∈ {0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1}, and
on proxy+ at λ ∈ {0, 0.1, 0.2, 0.3, 0.5}. That is 21 settings with 20 seeds each, about 2,100 runs.
Then the other knobs (persistence, shared error, bias, direction and the missing rates) are varied
one at a time on the noisy family, at three accuracies (0.2, 0.5 and 0.9), for all three levers
together: about 400 more. In all, about 2,500 runs a book, under an hour on 40 cores.

The result, per lever and book, is a **value-of-accuracy curve**: the median Δ Calmar, Δ return and
Δ max drawdown against no report, with the 10th–90th percentile band across seeds, plotted against
accuracy.

| Readout | Meaning |
|---|---|
| **break-even accuracy** ρ* | the lowest accuracy at which the median Δ Calmar is above 0; ρ*90 where 90% of seeds are |
| **the cost of no skill** | the curve at accuracy 0: what a report that flags the right *number* of days, but random ones, costs. A stricter null than the time shift, since the tier frequencies match exactly |
| **the ceiling** | accuracy 1, the curve's end, near the oracle |
| **robustness** | how far persistence, shared error and bias move ρ*. A lever whose ρ* jumps with persistent errors is fragile in exactly the episode that matters |
| **the incremental bar** | on the proxy+ family, the λ at which a report beating the proxy starts to pay: what the LLM must add over data we already hold |

Expectations to test, not assume: the weekly cap (G) should need the least accuracy, since a week
of errors averages out. Spacing (B) is likely forgiving too, because a wrong wide step still buys,
just deeper. The daily pause is likely the least forgiving, because a wrong pause misses a whole
day's buying.

### 6. Placing the real sources on the curve

The nightly scoring measures the real reports' accuracy on the same scale: the rank correlation of
each field with its realised value, with a block-bootstrap interval. The proxy's accuracy is
measured over its whole history. A lever runs in enforce mode for a source only when the lower end
of that source's 90% interval clears the lever's ρ*90.

That interval is about ±0.15 at 120 sessions (1.645/√120). So a lever with ρ*90 = 0.2 needs a report
measuring about 0.35 or more after six months. The curves say in advance roughly how long the
forward test has to run for each lever.

## Gates

| Step | Passes when |
|---|---|
| A lever moves from advisory to enforce on paper (proxy-driven) | On the book as deployed: a better Calmar than no overlay in **both** halves; less than 5% of the baseline's return given up; the real schedule beats at least 36 of its 40 shifted copies on return over drawdown; no stress path more than a point worse in drawdown; a plateau in `robust`; it holds in `walk`; and the proxy's measured accuracy clears the lever's ρ*90. Measured in the `supersedes` form the deployment will trade; if `priority` shows superseding costs more than applying after, the write-up says so and the owner re-decides. At least 10 advisory sessions with no refused report come first. |
| The LLM's reports drive a lever instead of the proxy's | At least 120 scored sessions; the lower end of its accuracy interval clears the lever's ρ*90 and its proxy+ skill λ is above 0; 1-day forecast skill over the VXN baseline above 0, with its 90% interval clear of 0; the LLM schedule's shadow at least the proxy's over the same sessions; and tiers stable on a rerun on at least 80% of nights. |
| Real money | The owner wants real money to take reports, checked by default on the Live page beside paper. Real money runs advisory from Phase 0. Enforce mode there, and granting `live.control.risk_reports` in `config/production.yaml` and `fidelity_live.yaml`, waits for a passing paper `PromotionEvaluation` with the lever enforced (at least 20 sessions) and a promoted mapping id, as every real-money change in this repository does. Until then the panel shows those deployments unticked and says why. |

If nothing passes, the system keeps advisory mode, the archive and the scoring, plus the manual
pause it already has, and the write-up says so. If the proxy passes and the LLM adds nothing over
it, the nightly step is unnecessary: the proxy runs itself.

## Phases

| Phase | Work | Done when | Size |
|---|---|---|---|
| **0. Record, score and advise (A)** | the parser and audit (`engine/core/risk_report.py`); the mappings for the tiers, spacing and the weekly cap (`research/risk_overlay/mapping.py`, pure functions); the archive; the Live page panel; the suggestion in `status.json`; the tracking service's followed/not-followed log and its as-suggested shadow; the nightly scorecard; the prompt committed with a version. No engine change | a report applied one evening shows as tomorrow's suggestion, and its scorecard row and shadows exist after the close | S–M |
| **1. The seam** | `risk_overlay.py`; the `RiskManager` overlay and `at`; `session_step` at every step call site and the opt-in target; the weekly composition; the `risk.overlay` and `live.control.risk_reports` config; the exemption hook; `MarketContext.report_supersedes` and the two strategies that read it; the command and its handlers; the risk section in the result row | the regression baseline is unchanged, advisory trades exactly what no overlay trades, and a parity test runs one schedule through backtest and live and gets the same buys and steps | M |
| **2. Measure** | `build_proxy_reports.py`, `build_synthetic_reports.py`, `probe_risk_overlay.py`, every stage above | `docs/research/risk-overlay.md`, with the tables, the nulls, the value-of-accuracy curves and the gates' verdict for each lever | L |
| **3. Enforce on paper** | each lever that passed, switched to enforce on `paper-ultimate` and/or `paper`, one at a time, with the shadows | 20 or more sessions per lever and a promotion record | M (calendar time) |
| **4. Real money** | an owner decision on the record | | |
| 5. Later | report features in the meta-label model (`research/ml/meta_*`); a skill-weighted blend of the LLM and the proxy; a CPI, payrolls and UMich release calendar; the prompt called by API on a schedule | | |

**Start Phase 0 first.** Every evening that goes unarchived is a session of real-report history lost,
and advisory mode uses the report from the first night.

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

Decided Nov 20, 2026:

| Question | Decision | What follows in this plan |
|---|---|---|
| May the browser only reduce risk? | **Yes.** | No buy-size multiplier above 1; the clamp never grows a buy and the step never narrows. More risk on calm days only through a larger researched baseline in the YAML (stage `joint`). |
| No report for a session? | **Trade as normal.** | NEUTRAL: the YAML's algorithm exactly, governor and event boosts included. No `cautious` fallback, and no attention item for a missing report. A week with no report has no weekly cap. |
| Which deployments take reports; real money? | **Selectable per deployment, all by default, paper and real money.** | The Apply step lists every deployment configured for reports, all checked. Real money still types its id back, runs advisory until its paper gate passes, and its YAML grant follows that gate ([Gates](#gates)). |
| The governor and the FOMC boosts? | **The report takes priority; it accounts for FOMC days itself.** | `risk.overlay.supersedes: [governor, event_boosts]`. On a report session the governor's pause and the event-day boosts stand down, and the mapping's catalyst component (merged with the engine's FOMC and earnings calendars) takes over. Stage `priority` measures what giving up the boosts costs. |
| Which other ways of using the report? | **A (advisory), B (grid spacing) and G (weekly cap)**, beside the daily tiers. | A is the default mode and Phase 0; B and G are levers of their own, each with its stages and its gate. |
| How to backtest accuracy? | **Reports for past sessions built from what actually followed, with controlled randomness, at a range of accuracies.** | [Backtesting at chosen levels of report accuracy](#backtesting-at-chosen-levels-of-report-accuracy): three families, the error knobs, 20 seeds a setting, the value-of-accuracy curves and the ρ*90 each lever's gate uses. |

Still open:

- **Blackouts against event boosts** no longer conflict on report sessions (the boosts stand
  down), but the blackout stays off until `catalysts` measures it.
- **`target_follows` for B**: off until `spacing` shows whether keeping the target-to-step ratio
  pays for the longer holds.
- **A budget** for sealed replays and reruns, if wanted.

## Tests

Each test lives in the section that owns its subject, with clocks injected:

- `engine/tests/test_risk_report.py`: tonight's report parses; broken sums, CDFs, quantile order,
  enums, symbol and `as_of` are each refused, with every problem listed; the target session across
  weekends, holidays and DST.
- `engine/tests/test_risk_manager_overlay.py`: 0 ≤ approved ≤ proposed for random overlays; no
  overlay is identical to today; the pause, the blackout's edges, the ceiling's `min` with the
  drawdown ramp and the weekly cap, exempt buys.
- `engine/tests/test_risk_overlay.py`: `session_step` is never below the YAML's step and never
  above `max_multiplier`; the target multiplier is 1 unless `target_follows`; the weekly cap
  tightens mid-week at once, loosens only at the reset, and is NEUTRAL past `max_age_days`.
- `tests/test_task_7_1_live_backtest_parity.py`: the same schedule gives the same buys and steps;
  an advisory schedule gives exactly the buys no overlay does.
- `research/tests/test_risk_overlay_mapping.py`: each mapping monotone in every input, bounded, and
  abstaining as specified; tonight's report maps to tier 3 and a step multiplier of ×1.7 to ×2.4,
  pinned.
- `research/tests/test_daily_ultimate.py` and the high-frequency sizing tests: with
  `report_supersedes` empty nothing changes; with `governor` a session the governor would pause
  is not paused; with `event_boosts` an FOMC or earnings session sizes at ×1; a NEUTRAL session
  (no report) keeps both.
- `research/tests/test_proxy_reports.py`: causal (changing any input after a session's cutoff
  leaves that session's report unchanged), and every proxy report passes the audit.
- `research/tests/test_synthetic_reports.py`:
  - the achieved rank correlation with the truth is within ±0.05 of ρ;
  - the mixture family tells the truth on p ± 0.02 of sessions;
  - the tier frequencies equal the proxy's at every accuracy;
  - a seed reproduces its reports exactly;
  - accuracy 1 reproduces the truth's ranking;
  - every synthetic report passes the audit.
- `server/tests/test_server_capability.py`: the preview writes nothing, the command only enqueues,
  both POSTs carry `same_origin`, a report is refused without the grant, and real money needs the
  typed id.
- `engine/tests/test_operator_control.py`: supersession, loosening after the open refused, the
  archive written.
- `tools/tests/test_track_live.py`: a suggestion is marked followed, not followed or late from the
  command log; the as-suggested shadow differs from as-traded only on sessions whose overlay changed
  something.
- `web/src/lib/riskReport.test.ts` and `attention.test.ts`.
