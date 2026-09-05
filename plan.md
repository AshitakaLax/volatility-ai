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

## Stage 2 results — run 2026-09-04

**144 configurations: 8 surviving signals x 6 period scalings x 3
threshold lookbacks.** `output/indicator_stage2.jsonl`, reproducible with
`python tools/indicator_sweep.py --stage 2 --from output/indicator_sweep.jsonl`.

### First, the RSP bar was fixed

Stage 1 reported 96 of 392 RSP configurations beating the bar against 5 of
392 on TQQQ. That was not RSP being easier — a return/drawdown of 0.319 is
trivially beaten by de-risking, and a book that sits in cash beats it
without doing anything useful. Adding the return floor the objective always
implied (CAGR at least 11%, against buy-and-hold's 12.46%) collapses 96
survivors to **3**: PLUS_DM, ADOSC, TRIX.

### The ridge test, and the metric that had to be fixed first

The first version of `ridge_scores` compared each setting against the mean
of **every other setting** in the grid — which is not a neighbourhood, it is
"better than the average of a surface spanning periods 7–42 and lookbacks
100–500". It scored LINEARREG at +20 CAGR points of "ridge" and PLUS_DM at
+0.4, **making the fragile result look stronger than the robust one.** It
now compares against adjacent settings in both axes.

### The result reverses Stage 1's apparent ranking

| signal | best | neighbours | settings clearing the bar |
|---|---|---|---|
| TQQQ LINEARREG | 46.16% | 30.76% | **3 of 18** |
| TQQQ TSF | 44.89% | 30.90% | 2 of 18 |
| TQQQ BBANDS lower | 43.76% | 31.70% | 4 of 18 |
| TQQQ T3 | 41.60% | 30.22% | 3 of 18 |
| **RSP PLUS_DM** | 1.046 | 0.834 | **17 of 18** |
| **RSP ADOSC** | 1.159 | 0.877 | **17 of 18** |
| RSP TRIX | 0.640 | 0.511 | 10 of 18 |

**Every TQQQ survivor is a spike.** The surface shows why — the entire
effect lives in one lookback column:

```
LINEARREG CAGR      lookback 100    250    500
period  7                 26.34  37.92  18.69
period 14                 28.63  46.16  16.66     bar = 39.15
period 21                 26.61  43.70  13.30
period 42                 20.45  29.72  13.86
```

Stage 1 fixed the threshold lookback at 250 as a generic rule, and 250 is
the only column that works. That was luck, not design, and the honest
reading of the headline finding is that it is **one cell of eighteen**.

**Both RSP leaders are ridges.** PLUS_DM clears its bar at 17 of 18
settings, across periods 7–42 and lookbacks 100–500; the single failure is
the shortest period at the longest lookback. ADOSC is the same shape. An
effect that survives its parameters being wrong by a factor of six is
describing something about the instrument.

### Where that leaves the two objectives

* **RSP has a robust answer.** Invest when directional movement or
  accumulation flow is below its own trailing median — that is, when the
  market is calm — and take buy-and-hold's return at roughly a third of its
  drawdown. It survives COVID removal, both chronological halves, and its
  own parameters.
* **TQQQ does not yet.** The trend-line family is real enough to have
  produced five of the only five configurations that beat a hard bar, but
  at one lookback each. Stage 3 on minute bars is the test that matters,
  and the prior should now be that it will not hold.

---

## Stage 3 results — run 2026-09-04

**Both candidates fail, and the reason is the same one, and it is worth
more than either would have been.** `tools/probe_stage3_engine.py`,
`output/stage3_*.csv`.

The prior was written into the script before running: the TQQQ trend-line
family should not survive (3 of 18 settings), PLUS_DM and ADOSC should
(17 of 18). **The prior was right about TQQQ and wrong about RSP, but not
in the direction that would have helped.**

| | Stage 1–2 shell | real engine | buy and hold |
|---|---|---|---|
| TQQQ LINEARREG | 46.16% / −54.22% | **28.87%** / −54.85% | 39.15% / −81.68% |
| RSP PLUS_DM, liquidate on flip | 12.37% / −13.37% | **−0.19%** / −25.01% | 12.46% / −39.11% |
| RSP PLUS_DM, hold through bear | 12.37% / −13.37% | 10.39% / **−40.04%** | 12.46% / −39.11% |

### The mechanism, which the shell could not have shown

In a long/cash shell, "exit" means selling the index and holding cash. It
costs the spread and nothing else.

In the grid, "exit" means closing every open lot — and a signal exit is
the *one* path in this system permitted to realise a loss. PLUS_DM flips
**277 times** against SMA200's 27, so liquidate-on-flip crystallised the
losing half of the book on every one: **37,407 signal exits out of 38,359
trades**, and −0.19% CAGR.

Turn liquidation off and the drawdown protection vanishes with it — the
book simply holds through the bear, and max drawdown lands at **−40.04%**,
which *is* buy-and-hold's. PLUS_DM's entire risk benefit came from being
out of the market, and in the grid "out" is only available at a price the
strategy cannot pay.

So the signal is not weak. It is **not transferable**: Stages 1–2 measured
a long/cash overlay, and this project runs a lot ledger.

### What this changes

* **The RSP answer stands, but it is not a grid enhancement.** Hold RSP,
  overlay PLUS_DM-below, no grid engine involved. That is consistent with
  the earlier finding that the grid loses to buy-and-hold on RSP anyway —
  the two results were always pointing at the same deployment.
* **TQQQ has no answer.** The trend-line family was a spike in Stage 2 and
  lands 10 points under buy-and-hold here.
* **The sweep's shell was the wrong shell**, and that is a design fault in
  Stages 1–2 rather than a fact about the indicators. A future sweep that
  wants grid-relevant answers has to score inside the grid — which costs
  ~5 minutes per configuration against 0.4 seconds, and is why the staged
  design put it last. The correct lesson is not "score everything in the
  engine" but "state which strategy a screen is screening for", and these
  stages did not.

---

## Stage 1 REDONE inside the grid engine — run 2026-09-04

**294 engine runs, 0 failed, 111.5 minutes.** `tools/stage1_grid.py`,
`output/stage1_grid.jsonl`. Every indicator scored where the strategy
actually lives, after Stage 3 showed the long/cash shell answered a
different question.

### First, a cost estimate in this file was wrong by 10x

The staged design rests on the claim, written above, that an engine run
costs **~5 minutes**, which is why scoring in the engine was deferred to
last. Measured across 294 runs it is **23 seconds**. The full 507-signal
space is about four hours, not two days. The staging was built around a
number nobody had measured.

### The result: nothing beats buy-and-hold on return. Nothing.

| | settings | clear the return floor |
|---|---|---|
| TQQQ (floor 39.15%, = buy-and-hold) | 174 | **0** |
| RSP (floor 11.0%, vs buy-and-hold 12.46%) | 120 | **0** |

Best in class: TQQQ `NATR below` **34.24%** and RSP `NATR below` **10.65%**,
both under their instrument's floor. This is now the third independent
line of evidence pointing the same way, after "the grid loses to holding
RSP monotonically" and Stage 3.

### Known-answer check: the harness reproduces Stage 3

`tools/stage1_grid.py` and `tools/probe_stage3_engine.py` are separate
scripts. On the one configuration they share — TQQQ LINEARREG above,
period 14, lookback 250 — Stage 3 recorded **28.87% / −54.85%** and this
run produced **28.875% / −54.845%**. Two implementations, one number.

### The Stage 3 mechanism, now at n=147 instead of n=1

Liquidate-on-flip was measured against hold-through-bear on the same
signal, 147 paired runs:

| | median CAGR cost | worse in | median drawdown bought |
|---|---|---|---|
| TQQQ | **−11.21pp** | **87 of 87** | 0.43pp (better in 45 of 87) |
| RSP | −5.50pp | 59 of 60 | **10.12pp** (better in 51 of 60) |

Liquidating is worse for return in **146 of 147** paired runs. Stage 3
established that on one signal; it is now a property of the policy.

**But the drawdown half splits by instrument, and that is new.** On RSP
the money buys something: 10 points of drawdown, four fifths of the time.
On TQQQ it buys **nothing** — 0.43pp median, and better in 45 of 87, which
is a coin flip. TQQQ pays 11 CAGR points for protection it does not
receive. Its crashes outrun a daily signal.

The flip-rate correlation splits the same way: `corr(flips, CAGR cost)` is
**−0.717** on TQQQ and **−0.003** on RSP. On TQQQ the cost is the flipping,
exactly as Stage 3 argued. On RSP the cost is there but flip rate does not
explain it, and this run does not establish what does.

### On return/drawdown, 10 of 294 clear the bar — and one is interesting

Nine of the ten are `liquidate`, which is the RSP column of the table above
paying off. Every one of them still fails the return floor, so under Stage
2's discipline they are de-risking, not edge. But the leader is not the
usual cash-sitter:

| | in market | CAGR | maxDD | worst yr | neg yrs |
|---|---|---|---|---|---|
| **TQQQ NATR below, liquidate** | 49.4% | 29.74% | 46.70% | −36.07% | 1 of 10 |
| TQQQ buy and hold | 100% | 39.15% | 81.68% | ~−79% | — |

It is in the market half the time and returns 29.74%, so the `--min-market`
artifact that sank the candlestick patterns in the first Stage 1 does not
apply. It gives up 9.4 CAGR points to halve the drawdown and take the worst
year from −79% to −36%.

**Which bar applies is the user's call.** Against max CAGR it fails like
everything else. Against the objective stated earlier in this project —
"the worst year with a positive return, drawdown very small in comparison"
— it is the best row in 294, and it is the only signal to lead on **both**
instruments and **both** policies. `NATR above` is its mirror and is
catastrophic (−16.94% on TQQQ), so the direction carries the information:
**invest when volatility is below its own trailing median.**

That is volatility targeting, which this project has already measured once
on RSP and priced at ~1.4pp of CAGR as crash insurance. Stage 2-grid tests
whether it is a ridge or one lucky cell, which is the question Stage 2
existed to ask and the one that killed the last TQQQ leader.

---

## Stage 2 REDONE inside the grid engine — run 2026-09-04

**165 engine runs, 0 failed.** `tools/stage2_grid.py`,
`output/stage2_grid.jsonl`. The nine Stage 1-grid leaders swept across a
6x period range and lookbacks 100/250/500, scored on both surfaces.

### Eight of nine are spikes. One is not, and it is the strongest result
### this project has produced.

**TQQQ `NATR below`, liquidate-on-flip, clears buy-and-hold's
return/drawdown at 18 of 18 settings.** Not 17 of 18 like PLUS_DM, which
this file already called robust — every cell.

```
ret/dd            lookback 100    250    500      bar = 0.479
period  7                  1.189  0.972  0.834
period 10                  1.448  0.805  0.911
period 14                  0.905  0.637  0.635
period 21                  0.683  0.881  0.568
period 28                  0.669  0.672  0.530
period 42                  0.658  0.515  0.551
```

Range 0.515 to 1.448 against a bar of 0.479. Column means fall
monotonically with lookback — 0.925, 0.747, 0.671 — which is a gradient,
not the single lucky column that turned out to be LINEARREG's whole
effect.

At the best cell (period 10, lookback 100):

| | CAGR | maxDD | worst yr | neg yrs | in market |
|---|---|---|---|---|---|
| **NATR below, liquidate** | **38.64%** | **26.68%** | **−12.64%** | 2 of 10 | 54.0% |
| same signal, hold through bear | 38.38% | 69.38% | −66.91% | 3 of 10 | 54.0% |
| TQQQ buy and hold | 39.15% | 81.68% | ~−79% | — | 100% |

It gives up **0.5pp of CAGR** and cuts drawdown from 81.68% to 26.68%.

### Three things wrong with believing that yet

1. **A Stage 1 claim recorded above is too broad.** "TQQQ pays 11 CAGR
   points for protection it does not receive" was a median over 87
   heterogeneous signals, and it is false for this one. Here liquidating
   costs **0.26pp** and buys **42.7pp** of drawdown. The median hid a
   minority of signals that get real protection; NATR is in it.
2. **The optimum sits on the boundary of the swept range.** Lookback 100
   is the smallest value tested and the best; below it is unexplored, so
   the true optimum may be outside the grid. A boundary optimum is weaker
   evidence than an interior one.
3. **The peak is sharp even though the surface is not.** 1.448 against
   neighbours of 0.966 — the adjacency test calls the argmax a spike
   sitting on a robust plateau. Both are true, and the deployable choice
   is a mid-surface cell, never the argmax.

### THE CONTROL THAT HAS NOT RUN, AND IT IS THE ONE THAT MATTERS

NATR-below is in the market 54% of the time and flips 138 times. **No
test so far distinguishes "NATR is informative" from "any signal that
sits out half the time and liquidates on 138 flips does this to a
leveraged ETF."** Liquidate-on-flip forces sales the no-loss guard has
already shaped, so a policy effect could masquerade as a signal effect
and every stage to date would have scored it identically.

That is settled by a random regime matched on in-market fraction and
flip count, and nothing in this project has ever run one. Until it does,
the honest statement is that the *configuration* is robust, not that the
*indicator* is informative.

### The other eight

| signal | best ret/dd | neighbours | clear the bar |
|---|---|---|---|
| RSP MACD.macd above | 0.533 | 0.326 | 8 of 18 |
| RSP NATR below | 0.495 | 0.350 | 7 of 18 |
| RSP OBV above | 0.448 | 0.446 | 2 of 3¹ |
| RSP MACDFIX.macdsignal | 0.391 | 0.210 | 3 of 18 |
| RSP MACD.macdsignal above | 0.341 | 0.177 | 2 of 18 |
| TQQQ BBANDS lower above | 0.801 | 0.473 | 6 of 18 |
| TQQQ TSF above | 0.615 | 0.412 | 6 of 18 |
| TQQQ LINEARREG above | 0.560 | 0.383 | 5 of 18 |

¹ OBV takes no period parameter, so its surface is the lookback axis
alone — three cells, and a much weaker robustness claim than the others.

**Not one of the 165 settings clears the return floor on either
instrument.** The best CAGR anywhere is NATR-below-hold at 39.090%
against 39.15%. On raw return the answer is still buy-and-hold.

---

## Stage 3 REDONE — the control, and it comes back positive — run 2026-09-05

**85 engine runs, 0 failed.** `tools/stage3_grid.py`,
`output/stage3_grid.jsonl`.

### The control: NATR is not the policy in disguise

30 random regimes from a two-state Markov chain, matched on **both**
in-market fraction and flip count (realised 54.1% and 136 against the
signal's 54.0% and 138), full sample, same engine, same policy:

| liquidate-on-flip | ret/dd | CAGR | maxDD |
|---|---|---|---|
| matched random, mean of 30 | **−0.017** | −2.48% | 83.94% |
| matched random, best of 30 | 0.262 | 17.07% | — |
| **NATR below, tp 10, lb 100** | **1.448** | 38.64% | 26.68% |

**z = +11.99, exceeds 30 of 30.** And the null did not merely fail to
reach 1.448 — the policy applied to noise is actively destructive, at
−2.48% CAGR against an 83.94% drawdown. Liquidate-on-flip is not a free
de-risking mechanism that any 54%-in-market signal can exploit; it is a
loss engine that NATR happens to point in a useful direction.

Under `hold` the control lands at 0.353 and NATR at 0.553 (z = +3.69,
30 of 30) — the signal still carries information without the policy, but
a quarter of the effect size. **The two are complements, not
substitutes**, and that is the answer to the question this stage existed
to ask.

### The halves — and a comparison this file nearly recorded wrongly

The first read was "the effect degrades badly out of sample": ret/dd
falls from 3.92 in the first half to 0.907 in the second. That compares
a segment result against the FULL-SAMPLE bar, which is not the right
bar. Buy-and-hold degrades over the same split, and much harder.

| segment | span | buy-and-hold ret/dd | NATR ret/dd | ratio |
|---|---|---|---|---|
| full | 2016-01..2026-08 | 0.477 | 1.448 | **3.03x** |
| first half | 2016-01..2021-05 | 0.808 | 3.924 | 4.85x |
| **second half** | 2021-05..2026-08 | 0.268 | 0.907 | **3.39x** |
| ex-COVID | COVID removed | 0.477 | 1.430 | 3.00x |

Against its own benchmark the second half is **stronger** than the full
sample, not weaker. The apparent collapse was buy-and-hold falling from
0.808 to 0.268 underneath it.

**And in the second half it beats buy-and-hold on raw return too** —
40.10% against 22.03%, at 44.19% drawdown against 82.29%. That is the
first configuration anywhere in this project to clear the return floor
in any segment.

### Three things that keep this from being a result yet

1. **The halves are not out of sample.** The configuration was selected
   on the full sample, which contains both halves. A subsample is not a
   holdout, and the only genuine holdout is data after 2026-08-21, which
   does not exist. Walk-forward selection is the test that has not run.
2. **The ex-COVID check is weaker here than it was for RSP.** Removing
   February–May 2020 leaves buy-and-hold's maximum drawdown at 82.29%,
   unchanged — because TQQQ's worst drawdown is **2022, not COVID**. So
   the check passes, but it did not stress the thing it was designed to
   stress, and it should not be read as the same evidence the RSP
   reversal produced.
3. **544 engine configurations have now been scored.** The control is
   not vulnerable to that (it is a matched null with a 12-sigma
   separation, not an argmax), and neither is 18-of-18. The *specific
   cell* is.

### The boundary optimum is resolved: it is interior after all

Lookbacks 25/50/75, below Stage 2-grid's swept range:

```
ret/dd        lookback  25     50     75     100    250    500
period 10               0.566  1.368  0.956  1.448  0.805  0.911
period 14               0.665  1.320  1.083  0.905  0.637  0.635
```

25 is clearly off the edge, so the optimum sits inside [25, 500] rather
than on its boundary. The surface between 50 and 100 is bumpy — two
local peaks, not one smooth ridge — which argues for the plateau and
against the argmax when a cell has to be chosen.

### The mid-surface cell is the weaker one, which is backwards

tp 21 / lb 250 was picked as the safe deployable cell on the theory that
an argmax is not to be trusted. It delivers 0.881 on the full sample and
**0.423 in the second half — under buy-and-hold's full-sample bar**,
while the argmax holds at 0.907. Whatever is driving the effect prefers
the short period and short lookback, and "take the mid-surface cell" is
not automatically the conservative choice here.

---

## Stage 4 — the leverage prediction is FALSIFIED — run 2026-09-05

**132 engine runs, 0 failed, 52.1 min.** `tools/stage4_leverage.py`,
`output/stage4_leverage.jsonl`. QQQ downloaded for this test: 1,044,165
rows, 2,684 sessions, SIP/all-adjustment/RTH, matched to TQQQ's sidecar
so the comparison is like for like.

### The prediction, recorded before the run

An L-times daily-rebalanced fund loses about `(L^2 - L)/2 * sigma^2`
against L times its index — `3*sigma^2` at L=3, and **exactly zero** at
L=1. So avoiding high-volatility regimes should pay a 3x fund and do
nothing for an unleveraged one. Stated criterion: QQQ near RSP's 7 of
18; **15+ of 18 falsifies the mechanism.**

The drag itself is real and directly measurable here — 3x QQQ's 20.20%
would be ~60.6% CAGR with no drag, and TQQQ delivers 39.29%. That ~21pp
gap is the drag. The mechanism exists. It is just not what produces the
NATR result.

### The result: falsified twice over

| | leverage | index | clears bar | ratio to own b&h | control z |
|---|---|---|---|---|---|
| **TQQQ** | 3x | Nasdaq-100 | 18/18 | **3.03x** | +11.99 |
| QQQ | 1x | Nasdaq-100 | **16/18** | 1.73x | +4.90 |
| **SOXL** | **3x** | semis | **0/18** | **0.95x** | +6.80 |
| RSP | 1x | equal-weight | 7/18 | 1.55x | — |

QQQ cleared 16 of 18 against a stated falsification threshold of 15.
And SOXL — 3x leveraged, vol 1.019 against TQQQ's 0.666, so roughly
**2.3x more drag** — is the *weakest* of all four. The two 3x funds sit
at opposite ends of the table. Leverage does not order this.

### What the controls actually establish, and a correction

Every instrument beats its own matched-random control decisively: QQQ
z=+4.90, SOXL z=+6.80, TQQQ z=+11.99, each exceeding 30 of 30. **So
NATR-below carries real information on all three.** That much survives.

**SOXL then shows why that was never sufficient.** It beats noise at
z=+6.80 and still clears its buy-and-hold bar **0 times out of 18**.
Beating a random signal and beating buy-and-hold are different claims,
and this file recorded the first as though it bore on the second.

Which forces a correction to the Stage 3 entry above: it says the
control is immune to the 544-configuration multiple-comparisons problem.
**It is not.** The control kills exactly one null — *the exit policy
alone produces this* — and that null is genuinely dead. It says nothing
about a second: *134 indicators were searched against one price series
and the best fit was kept.* TQQQ's 3.03x is a **selected maximum** over
544 engine configurations; QQQ's 1.73x and SOXL's 0.95x are
**unselected** values handed the same signal over 18 cells each. A gap of
that shape is close to what selection bias alone predicts.

### A confound in this stage's own design, recorded against it

Both instruments preferred the **larger** of the two profit targets they
were given — QQQ 0.04 over 0.0134, SOXL 0.0612 over 0.04 — so neither
was at an optimum and the target is not really held fixed across
instruments. The vol-scaled pass was meant to make a null interpretable
and instead showed the target is a strong free parameter in its own
right.

This cuts *against* the leverage story rather than rescuing it: TQQQ was
run at 0.04 only, never optimised over target, and still sits at 3.03x
against SOXL's best-of-two 1.40x.

### Where this leaves the TQQQ result

Nothing measured is retracted — 18 of 18, the halves, ex-COVID and the
policy control all stand exactly as computed. What changes is what they
license. The configuration now has **no mechanism and no cross-instrument
support**, which returns it to "a strong in-sample fit on one
instrument."

Walk-forward — select on data through year T, score T+1, roll — is now
the deciding test rather than a formality, and the prior after this stage
should be that it will not hold. Recording that here so the result is
read against a prediction, the way Stage 3 was.

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
