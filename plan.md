# Indicator sweep: brute-force every untested input, on two instruments

## What this is

An exhaustive search over the technical indicators this project has never
tried, run as **two independent objectives** — TQQQ and RSP — because they
are different problems with different bars, and a configuration that wins
on one has proven nothing about the other.

| | TQQQ | RSP |
|---|---|---|
| Annualised vol | 65.9% | 18.1% |
| Best strategy found so far | 41.65% CAGR | 12.44% CAGR |
| …against its buy-and-hold | **+2.9pp** | **−0.1pp** |

### The bar, computed once, with its provenance

A buy-and-hold CAGR moves by half a point depending on which file and
which resolution you take it from — and this sweep is hunting a two-point
edge, so that ambiguity is not tolerable. Both numbers below come from the
exact files the runner reads, and **the daily and minute bars are
different numbers on purpose**: Stages 1–2 run on daily bars and are judged
against the daily row, Stage 3 runs the minute engine and is judged against
the minute row. Comparing a Stage-1 result to the minute bar would hand a
candidate 0.14pp it did not earn.

| instrument | file | resolution | CAGR | max DD | return/DD |
|---|---|---|---|---|---|
| TQQQ | `TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv` | daily close | **39.15%** | −81.68% | 0.479 |
| TQQQ | same | minute | **39.29%** | −82.29% | 0.477 |
| RSP | `RSP_1Min_sip_all_rthuniform_2016-01-01_2026-08-30.csv` | daily close | **12.46%** | −39.11% | 0.319 |
| RSP | same | minute | **12.52%** | −40.04% | 0.313 |

Windows are 2016-01-04 → 2026-08-21 (TQQQ) and → 2026-08-28 (RSP). The
earlier figures of 38.73% and 12.52% came from Alpaca *daily* bars over a
slightly longer window in `tools/screen_daily_fitness.py`; they are a
different measurement of the same thing and are not the bar here.

**What a win looks like**

* **TQQQ** — beat the buy-and-hold CAGR for its stage, or match it at
  materially lower drawdown.
* **RSP** — beat return/DD of 0.319 (daily) / 0.313 (minute), **or** cut
  max drawdown by ≥10pp at a cost of ≤1pp of CAGR.

The objectives differ because the instruments do. TQQQ is held for return
and its strategy already clears buy-and-hold, so the question is *how much
more*. RSP is held for the diversification of 500 equal-weighted names, and
nothing has beaten simply owning it — so the question is whether any input
makes owning it **safer** at an acceptable price.

**Never rank the two together.** A combined leaderboard would be dominated
by TQQQ's larger numbers and would silently answer the RSP question with
the TQQQ answer.

---

## The trap this plan exists to avoid

Brute force is what was asked for and it is the right instinct — the
indicator space has never been swept, and hand-picking candidates is how
you find what you already expected. But this project has already paid for
naive brute force twice, and both receipts are in the tree:

> "sweeping them tripled the space from 6,272 to 18,816 — which dropped
> coverage from 3.2% to 0.30% at a 200-trial budget and caused that run to
> never even propose the best configuration a smaller earlier sweep had
> already found." — `config/search_hf_volscaled.yaml`

> "TPE evaluated 14 distinct combinations out of 250 trials on this space."
> — `config/search_hf_volume_sweep.yaml`

So the space is searched in **stages**, widest-and-cheapest first. This is
not a reduction in coverage; every indicator is still tested. It is a
reordering, so that the expensive engine only ever runs on inputs a cheap
screen has already shown to be worth the minutes.

### The statistical trap, which is worse

Testing ~500 configurations against a fixed bar and reporting the winner is
**guaranteed** to produce something that beats the bar, whether or not
anything real is there. At a 5% threshold, 25 of 500 pass by chance alone.
This is the single most likely way for this plan to produce a confident,
wrong answer, and the mitigations are non-negotiable:

1. **Every result is reported on both halves of the record**, split
   chronologically. An indicator whose halves disagree is describing one
   regime, not stating a rule. `tools/probe_regime_signals.py` already
   prints `16–20` and `21–26` columns for exactly this reason.
2. **The full distribution is reported, not the winner.** If 200 configs
   were tested and the best beat the bar by 2pp while the median trailed by
   4pp, that is a different finding than 200 configs clustering 2pp above.
   The runner writes every row; the report shows the histogram.
3. **A win must survive dropping the single best year and the single worst
   year.** The vol-targeting result on RSP looked robust across every
   parameter from 10% to 26% and evaporated when Feb–Jun 2020 was removed.
   That check goes in from the start, not after something looks good.
4. **Nothing from this sweep goes near live trading on this evidence
   alone.** Clearing the bar here earns a candidate a dedicated,
   pre-registered out-of-sample test, not a config change.

---

## Two roles, and they are different experiments

The same indicator can enter this system two ways, and conflating them
would halve the search without saying so.

**As a REGIME FILTER** — a boolean that says in-market or out. Runs through
the existing shell in `tools/probe_regime_signals.py`: long when true, cash
when false, switching costs charged, signal from day *t* applied to day
*t+1*. Nineteen rules already run this way, so a new one is a dictionary
entry and is directly comparable to everything already measured.

**As a SIZING INPUT** — a continuous multiplier on trade size, the way
`vol_scale_exponent` and `volume_scale_exponent` already work in
`src/high_frequency_sizing.py`. Exposure scales with the indicator rather
than switching on it.

**Prior, stated so it can be falsified rather than assumed:** the sizing
role is more likely to pay. Every measurement this project has made points
that way — every *faster* regime signal made 2022 worse (EMA20 −65.0%,
RSI(14) −65.7%), the continuous vol filter beat binary SMA200 on every
axis, and volatility targeting on RSP cut drawdown 54% where a trend filter
cost 5.7pp of CAGR to cut it 14pp. Direction is hard; magnitude persists.
The sweep tests both roles anyway, because that prior is exactly the kind
of thing a brute-force search exists to overturn.

---

## The inventory

Every indicator absent from the codebase, from the audit of `src/`,
`tools/`, and `optimization_controller.py`.

### These come from libraries, not from memory

Thirty-five indicators written by hand is thirty-five chances at a silent
wrong answer propagating through every result computed on top of it.
`requirements-indicators.txt` pins five reference implementations — TA-Lib
(161 functions, the C reference), pandas-ta-classic (427, pure Python), ta
(48), finta (90, for breadth), and talipp (incremental, for the live loop
if anything is ever promoted).

**Separate from `requirements.txt`, deliberately**, on the same reasoning
that put Playwright in `requirements-fidelity.txt`: the Dockerfile installs
`requirements.txt` for every image, and the Raspberry Pi runs a trading
loop that computes no indicators. TA-Lib in particular may want a source
build on ARM, and the Pi should never be asked to compile it.

### But a library is not automatically safer, and this was measured

Six implementations of RSI(14) over 1,500 TQQQ daily bars:

| implementation | largest deviation from TA-Lib |
|---|---|
| `src.sizing_indicators.WilderRSI` | **0.000000** |
| `pandas_ta_classic` | **0.000000** |
| `ta` | 7.911761 |
| `finta` | 7.911761 |
| `stockstats` | 7.911761 |

All six converge to the same value and agree **exactly** after bar ~104.
The disagreement is entirely **warmup seeding** — TA-Lib and Wilder seed
with a simple average of the first N periods then smooth, the others run an
EWM from bar one. ATR(14) behaves identically: 0.06 apart early,
`0.00000000` after bar 250.

Note what that table also says: this project's own hand-rolled `WilderRSI`
is exactly right, and three well-known libraries disagree with the
reference. "Fewer bugs" is earned by cross-checking, not by importing.

**So two rules, both load-bearing:**

1. **Every indicator is computed by two libraries and their steady-state
   values asserted equal.** Disagreement is a finding to resolve before the
   indicator enters the sweep, not a tolerance to widen.
2. **The warmup region is discarded explicitly**, by our own rule, rather
   than trusting any library's seeding. 104 bars of 7.9-point RSI error is
   precisely the artifact class that already cost this project a year: an
   unwarmed 200-day mean put 79.4% of 2016 inside its window and made that
   year's −7.70% meaningless.

Versions are pinned exactly. A library that changes its seeding in a point
release would silently move every result in the sweep.

Data needed is noted because it decides implementation order: the existing
daily probes load `close` only, and anything needing OHLC or volume needs
the loader widened first. Both instruments' files carry
`open,high,low,close,volume`, so nothing here is blocked on a download.

### Bands and channels — needs OHLC

| indicator | params to sweep | regime use | sizing use |
|---|---|---|---|
| Bollinger Bands | period 10/20/50, k 1.5/2/2.5 | close above/below mid; %B | bandwidth as a vol proxy |
| Keltner Channels | period 10/20, ATR mult 1.5/2/3 | position vs channel | channel width |
| Donchian width | period 20/50/100 | *(entry already tested)* | width as range proxy |

### Volatility — needs OHLC

| indicator | params | regime use | sizing use |
|---|---|---|---|
| **ATR / ATR%** | period 7/14/21 | ATR% below median | **the direct replacement for the single-bar-move proxy `src/cost_models.py:120` already flags as owed** |
| True Range percentile | window 60/250 | percentile filter | percentile as scalar |
| Parkinson / Garman-Klass vol | window 20/60 | — | higher-efficiency vol estimators; the sizing input is already a stdev, and these use the whole bar |

### Trend strength — direction-agnostic, which is the interesting part

| indicator | params | regime use | sizing use |
|---|---|---|---|
| ADX / DMI | period 14/21 | ADX > 20/25 | **ADX as a harvest gate** — the strategy is measured to win in choppy regimes and lose in rallies, and ADX is the standard measure of exactly that |
| Aroon | period 14/25 | up > down | oscillator as scalar |
| Vortex | period 14/21 | VI+ > VI− | spread magnitude |
| TRIX | period 9/15 | > 0, > signal | slope magnitude |
| Supertrend | period 10, mult 2/3 | direction flag | — |
| Parabolic SAR | af 0.02, max 0.2 | price vs SAR | — |
| Ichimoku | 9/26/52 | price vs cloud | cloud thickness |

### Oscillators — needs OHLC for most

| indicator | params | regime use | sizing use |
|---|---|---|---|
| Stochastic %K/%D | 14/3/3, 21/5/5 | %K > 50, cross | distance from 50 |
| Williams %R | period 14/21 | > −50 | level as scalar |
| CCI | period 14/20 | > 0, > −100 | magnitude |
| Ultimate Oscillator | 7/14/28 | > 50 | level |
| Connors RSI | 3/2/100 | > 50 | designed for mean reversion, which is this system's whole premise |

### Volume — the largest untested block

| indicator | params | regime use | sizing use |
|---|---|---|---|
| **VWAP distance** | session, rolling 20/60 | price above VWAP | **(price − VWAP)/VWAP as a sizing scalar** |
| OBV | slope 20/60 | OBV > its own SMA | slope magnitude |
| Chaikin Money Flow | period 20/21 | > 0 | level |
| Accumulation/Distribution | slope 20/60 | rising | slope |
| Money Flow Index | period 14 | > 50 | level |
| Force Index | period 13 | > 0 | magnitude |
| Ease of Movement | period 14 | > 0 | magnitude |
| Volume z-score | window 20/60 | — | relative volume, a cleaner form of the existing fast/slow ratio |

**VWAP is the cheapest thing on this list and should be tested first.**
`src/historical_data.py:371` already downloads a `vwap` column with every
bar and nothing in the project reads it. No fetch, no new data, no new
dependency — and it is a *reference price*, which is precisely the
mechanism the champion configurations turned out to be exploiting: they
buy dips and hold, so the edge is entry price against a local reference.

### Moving-average variants — low prior, cheap to include

WMA, HMA, DEMA, TEMA, KAMA, VWMA, ZLEMA. Periods 20/50/100/200. Regime use
only. These are lag/smoothness variations on SMA and EMA, which are already
measured, and the measured finding is that faster made 2022 *worse*.
Included for completeness because they cost minutes, and flagged as the
block most likely to produce a false positive purely from its size.

### Structure and statistics

| indicator | params | notes |
|---|---|---|
| Heikin-Ashi trend | — | smoothed candles; regime flag |
| Pivot points | daily S/R | intraday levels, needs session grouping |
| Fibonacci retracement | 250d swing | levels off the rolling peak/trough |
| Hurst exponent | window 100/250 | direct persistence-vs-reversion measure; conceptually the closest thing here to the variance ratio already used in `tools/screen_daily_fitness.py` |
| Rolling z-score | window 20/60 | mean-reversion band |
| Rolling skew / kurtosis | window 60/250 | tail-shape as a risk scalar |
| Autocorrelation | lag 1/5, window 60 | regime-conditional mean reversion |

---

## Stages

### Stage 0 — the adapter and its cross-checks

`src/indicator_library.py` is a thin **adapter**, not a set of
implementations: one function per indicator, delegating to the pinned
libraries, normalising their differing APIs (TA-Lib takes numpy arrays,
finta takes a lowercase-column DataFrame, pandas-ta-classic takes Series)
to one signature that returns a `pd.Series` aligned to the input index.

Each indicator gets:

* a **cross-library agreement test** — computed two ways, steady-state
  values asserted equal within a tight tolerance. This is the test that
  makes the libraries worth using; without it we have merely moved where
  the bug would live.
* a **warmup test** asserting `NaN` until the window is full, applied by
  *us* regardless of what the library returns. The RSI measurement above is
  why: three libraries emit confident, wrong-by-8-points values through
  their first hundred bars rather than `NaN`.
* a **known-answer test** for anything available from only one library
  (finta's exclusives), since there is nothing to cross-check it against.

### Stage 1 — every indicator alone, daily bars, both instruments

Each indicator, in each applicable role, at 2–3 default parameterisations.
Roughly **35 indicators → ~90 configs per instrument per role**, so ~360
runs. Daily bars: seconds each, the whole stage in minutes.

Output per run: CAGR, max DD, Ulcer, Sharpe, worst year, return/DD,
time-in-market, switches, **and the two chronological halves**.

Gate to Stage 2:
* **TQQQ** — beats the daily buy-and-hold CAGR of 39.15%, or matches it at
  materially lower drawdown.
* **RSP** — beats daily return/DD of 0.319, or cuts max drawdown by ≥10pp
  at ≤1pp of CAGR.
* **Both** — the two halves must agree in sign.

### Stage 2 — parameter sweep of the survivors, daily bars

Full grid over each survivor's parameters. Expect 5–15 survivors, ~50
configs each, so ~500 runs per instrument. Still daily, still minutes.

This is where the multiple-comparisons discipline bites hardest: report the
distribution, and treat a lone spike surrounded by mediocre neighbours as
noise. A real parameter effect is a **ridge**, not a point — the
volatility-targeting result was believable partly because Sharpe was flat
at 0.76–0.78 across the whole 10–26% range.

### Stage 3 — survivors through the real engine, minute bars

Only now does `run_hf_sweep.py` run, on 1-minute data with costs, the
no-loss guard, and intrabar fills. ~35s per combination. Budget ~50
combinations per instrument.

Daily-bar promise does not guarantee minute-bar delivery, and the gap is
itself a finding: the strategy trades minutes, and an indicator that only
works on daily bars is telling you the effect is slower than the machinery.

### Stage 4 — pairwise combination, survivors only

**Coordinate descent, one axis at a time.** Never a full cross-product —
that is the mistake the two config files quoted above are receipts for.
Combination rule, from `src/high_frequency_sizing.py`: `max()` when the
second indicator restates the first's claim, multiply (and **clamp**) when
it is a genuinely independent axis.

---

## The runner

`tools/indicator_sweep.py`. One script, all four stages, driven by
`--stage`.

### Progress logging, which is the part that has to be right

These runs are long, the box has had at least one memory incident from
overlapping sweeps, and a run that loses six hours of work to a crash gets
abandoned rather than restarted.

* **Append-only JSONL, flushed and fsynced per row.** Every completed
  configuration is durable the moment it finishes. Same discipline as
  `FileConfNumJournal` in `src/fidelity_placing_broker.py`, and for the
  same reason: a buffered handle is exactly how a journal loses its last
  entry.
* **`--resume` is the default.** On start, read the log, skip every
  configuration already present, report how many were skipped. Interrupting
  and restarting must cost one configuration, not the run.
* **A stable `config_id`** — a hash of (instrument, role, indicator, params)
  — is the resume key. Not the row index, which changes the moment the
  inventory grows.
* **Progress line per configuration**: `[  47/360] RSP regime bollinger
  p=20,k=2.0  CAGR 9.14%  DD -22.1%  Sharpe 0.71  (2.3s, eta 0.19h)`.
  Matching `run_hf_sweep.py`'s existing format, so both are readable by the
  same eye.
* **Heartbeat every 30 configurations**: elapsed, remaining, best-so-far
  per instrument. A silent run is indistinguishable from a stalled one, and
  that distinction has cost real time here already.
* **Failures are logged and skipped, never fatal.** One indicator raising
  on a degenerate window must not end a six-hour run; the row records the
  exception and the sweep continues. A stage that ends with 3 failures out
  of 360 is a result; one that dies at configuration 47 is nothing.

### Usage

```bash
# Stage 1, both instruments, both roles. Minutes.
python tools/indicator_sweep.py --stage 1 --out output/indicator_sweep.jsonl

# Resume after an interruption -- default, shown for clarity.
python tools/indicator_sweep.py --stage 1 --resume

# Survivors only, full parameter grids.
python tools/indicator_sweep.py --stage 2 --from output/indicator_sweep.jsonl

# Read the results: distributions and both halves, not just the winner.
python tools/indicator_sweep.py --report output/indicator_sweep.jsonl
```

---

## Stage 1 results — run 2026-09-04

**784 configurations, 134 indicators, both funds, 0 failures, 12 seconds.**
`output/indicator_sweep.jsonl`, reproducible with
`python tools/indicator_sweep.py --stage 1`.

### A scoring bug the first report surfaced, before any finding

The first RSP leaderboard was twelve candlestick patterns with
return/drawdown near **118**. That was 4.07% CAGR over a 0.03% drawdown —
and 4.07% *is* the cash yield. Patterns fire on a handful of bars a year,
so the "strategy" sat in cash and could not draw down, which
return/drawdown rewards perfectly. **The metric is degenerate at low
exposure, not merely noisy.** `--min-market` (default 20%) now drops such
configurations, and it dropped **277 of 784**.

Worth stating plainly: had the report been read before that was noticed,
the recommendation would have been a candlestick pattern that never trades.

### TQQQ — 5 of 266 beat the bar (1.9%)

| indicator | CAGR | max DD | first half | second half |
|---|---|---|---|---|
| **LINEARREG above** | **46.16%** | **−54.22%** | 58.17% | 35.10% |
| TSF above | 44.89% | −55.36% | 58.05% | 32.86% |
| BBANDS middleband above | 42.01% | −65.31% | 49.12% | 35.26% |
| BBANDS lowerband above | 41.79% | −48.71% | 54.07% | 30.53% |
| T3 above | 41.60% | −65.51% | 47.01% | 36.42% |
| *buy and hold* | *39.15%* | *−81.68%* | | |

**1.9% beating the bar is below what chance alone would produce**, and the
five are one coherent family — price above a smoothed trend line
(LINEARREG, TSF = its extrapolation, BBANDS middleband = an SMA, T3 = a
smoothed MA). Scattered noise does not cluster like that.

LINEARREG: **+7.0pp of CAGR and 27pp less drawdown, on 27 switches in ten
years**, and it gets *better* with COVID removed (49.17%, −37.38%). It also
beats the existing best-ever configuration of 41.65%.

### RSP — the risk objective, answered

| indicator | CAGR | max DD | Sharpe | in market | first half | second half |
|---|---|---|---|---|---|---|
| **PLUS_DM below** | **12.37%** | **−13.37%** | 1.12 | 46.2% | 11.02% | 13.73% |
| CCI sizing/rank | 7.28% | −8.77% | 0.90 | | 9.41% | 5.21% |
| ADOSC below | 12.75% | −15.52% | 0.95 | | 17.42% | 8.29% |
| *buy and hold* | *12.46%* | *−39.11%* | *0.73* | *100%* | | |

PLUS_DM holds buy-and-hold's return at **one third of its drawdown**, and
survives COVID removal (11.01% against buy-and-hold's 12.46%, at −13.37%
against −21.38%). That is a far better trade than volatility targeting
offered — 1.45pp of CAGR for 8pp of drawdown, against 1pp for 0.6pp.

Note what it is: PLUS_DM is the magnitude of upward directional movement,
so "below its trailing median" means **invest when the market is calm**.
That is a volatility filter wearing a trend indicator's name, and it agrees
with everything else this project has measured — the strategy wins in
choppy regimes, and `SMA200 and vol20 < median` already topped the earlier
nineteen-rule table.

### What these results are NOT, yet

* **Daily bars.** Stage 3 has not run. The strategy trades minutes.
* **One threshold rule.** Every indicator was binarised against its own
  250-day trailing median. That is a defensible generic rule, not a swept
  parameter — Stage 2 exists for that.
* **39.8% of RSP configurations beat the RSP bar**, because return/drawdown
  of 0.319 is easy to beat by de-risking. The TQQQ figure of 1.9% is the
  meaningful one; the RSP bar needs a companion return floor.
* **Not out-of-sample.** Both halves agreeing is a consistency check, and
  784 configurations were tested. LINEARREG and PLUS_DM have earned a
  pre-registered out-of-sample test, not a config change.

---

## What would make this dishonest

* **Lookahead.** Every signal is computed from data through day *t* and
  applied to day *t+1*. Any rolling threshold uses an **expanding** or
  trailing quantile, never one computed over the whole sample — a
  full-sample `quantile(0.9)` knows the future.
* **Survivorship in the instrument choice.** Both instruments are fixed in
  advance and both are reported, including when RSP's answer is "nothing
  helped". A sweep that quietly drops the instrument where nothing worked
  is a sweep that cannot produce a negative result.
* **Costs.** Charged on every switch and every unit of turnover. A
  continuous sizing input that rebalances daily can lose to a binary filter
  purely on friction, and it should be allowed to.
* **The bar moving.** Buy-and-hold per instrument is computed once, written
  down here, and not recomputed per experiment.

## What success and failure both look like

**Success** is a small number of indicators — plausibly one or two — that
clear their instrument's bar, hold across both halves, survive dropping the
best and worst year, and still deliver through the minute-bar engine.

**Failure is a legitimate and likely outcome, and is worth the run.** Most
of these have been tested to death by the whole industry; the prior that
any given one carries alpha on a leveraged ETF is low. A sweep that returns
"none of the 35 cleared the bar on TQQQ, two cut RSP drawdown at a price"
is a real finding, and it retires a large question permanently.

The failure mode to actively guard against is neither of those: it is
**finding a winner that is noise**, promoting it, and discovering that in
production. Everything in the multiple-comparisons section exists for that
one risk.
