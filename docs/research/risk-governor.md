# Risk governor — what outside data adds to the Daily Ultimate reserve

Nov 10, 2026 · Measured, with a null control · `research/strategies/risk_governor.py`,
`tools/probe_risk_governor.py`, `tools/refresh_external.py`,
`config/daily_ultimate_governed_tqqq.yaml`

## Goal

The owner asked what would give the trading the best advantage, which data would provide it, and
for that data to be collected automatically. The book in question is the
[Daily Ultimate reserve](daily-ultimate-reserve.md): TQQQ, +0.1% of equity a session at the least
drawdown. Its regime reads only the fund's own range (NATR). The question here is whether series
from outside the fund improve it, and in what form.

## Answer

| | |
|---|---|
| **What helps** | A **pause on new buying** when at least four of five outside warnings are raised for a session. Lots still sell at their targets, nothing is liquidated, the regime is untouched. |
| **What does not** | The same warnings as a veto on the regime, or as an override of it. Both cost return. |
| **The five warnings** | Nasdaq-100 implied volatility above its 100-session median; semiconductors lagging the Nasdaq-100; high yield lagging Treasuries; QQQ below its 100-session mean; the OFR financial stress index rising |
| **Switch** | `caution_min_votes` on `daily_ultimate`, off by default; pinned in `config/daily_ultimate_governed_tqqq.yaml` |
| **Data** | `data/external/`, kept current by `tools/refresh_external.py` (the compose `market-inputs` service) |

Measured as the reserve was (causal intrabar fills, dynamic slippage, no cash yield), from
2016-01-04 to 2026-11-09, scored from 2017-01-03:

| | Per session | CAGR | Max DD | Sharpe | 2017–21 | 2022 on |
|---|---|---|---|---|---|---|
| Reserve, no governor | 0.098% | 28.0% | 20.6% | 1.41 | 0.124%, DD 18.5% | 0.072%, DD 20.6% |
| **With the governor** | **0.100%** | **28.4%** | **18.5%** | **1.43** | 0.122%, DD 18.5% | **0.076%, DD 15.9%** |

The reserve's own numbers have moved since its write-up (0.101%, 18.5% to 2026-11-04): the
drawdown it was in then has deepened to 20.6%.

**What it buys:** about two points of drawdown at the same return, at every lot size tried.

**What it does not buy:**

- **It still does not make 0.1% a session from 2022 on** (0.076%). No amount of outside data
  tried here changes that.
- **The drawdown it removes is one episode: the current one** (2026-10-06 onward, 20.6% without
  the governor, 15.9% with it). The 2021 drawdown (18.5%) is untouched, and 2017–21 return is
  slightly lower with the governor on (0.122% against 0.124%).
- **The form and the threshold were chosen after looking.** About 160 scratch runs over 28
  candidate flags preceded the committed stages below, on the same history. The null control
  shows the dates matter; it cannot correct for that search.

## Results

Every stage is `tools/probe_risk_governor.py`; 118 engine runs in all.

### forms: only the pause helps

| Form | Per session | Max DD | 2022 on |
|---|---|---|---|
| no governor | 0.098% | 20.6% | 0.072% |
| **pause**, four of five | **0.100%** | **18.5%** | **0.076%** |
| pause, one warning alone (best: QQQ trend) | 0.096% | 18.5% | 0.076% |
| pause, one warning alone (worst: semiconductors) | 0.070% | 18.5% | 0.058% |
| **veto**, four of five | 0.092% | 20.5% | 0.071% |
| veto, one warning alone (range) | 0.042% to 0.093% | 18.2% to 20.5% | |
| **override** while no core warning is raised | 0.092% | 20.8% | 0.055% |
| override while QQQ is above its trend | 0.010% | 30.9% | −0.005% |

- **A veto flips the regime**, and a flip sells the calm book below cost. The drawdowns it was
  meant to avoid happen inside calm spells, where the drawdown throttle already bounds them.
- **An override keeps the grid buying in wide ranges.** Its 0.4% steps are sized for narrow
  ones, so it loads up and the next regime exit sells the load at a loss.
- **One warning alone pauses too often.** Each is raised on 19% to 47% of sessions; four of five
  agree on 13%.

### frontier: the gain is not a lot-size artefact

| Lot | No governor | With the governor |
|---|---|---|
| 0.25% | 0.098%, DD 20.6% | 0.100%, DD 18.5% |
| 0.30% | 0.104%, DD 20.7% | 0.106%, DD 18.5% |
| 0.35% | 0.107%, DD 21.0% | 0.108%, DD 18.7% |
| 0.45% | 0.108%, DD 21.0% | 0.108%, DD 18.6% |

### robust: a plateau, not a point

| Change | Per session | Max DD |
|---|---|---|
| votes ≥ 2 of 5 | 0.078% | 18.9% |
| votes ≥ 3 of 5 | 0.096% | 18.5% |
| **votes ≥ 4 of 5** | **0.100%** | **18.5%** |
| votes ≥ 5 of 5 | 0.098% | 20.8% |
| any one core warning left out, 3 of 4 | 0.096% to 0.100% | 18.5% |
| any one core warning left out, 4 of 4 | 0.097% to 0.101% | 18.5% to 20.8% |
| eight warnings (adds dollar, MOVE, NFCI), ≥ 5 | 0.099% | 18.5% |
| eight warnings, ≥ 6 | 0.100% | 18.5% |

Unanimity is too rare to act (five of five, and four of four in four of the five cases, read as
no governor). Dealer gamma (`gex_low`) and the VIX term structure (`term_flat`) alone do nothing
as a pause.

### null: the dates matter

The real pause map against 40 copies of itself moved in time by a random number of sessions:
the same number of paused sessions, in the same runs, on other dates.

| | Per session | Max DD |
|---|---|---|
| real map | 0.100% | 18.5% |
| no governor | 0.098% | 20.6% |
| median of 40 shifted maps | 0.090% | 20.6% |

Shifted maps at least as good as the real one: 4 of 40 on return, 3 of 40 on drawdown, **0 of 40
on return over drawdown**. A pause of this size at the wrong dates costs return and leaves the
drawdown where it was.

### stress: no harm on a worse path

| Path | No governor | With the governor |
|---|---|---|
| `deeper` | 0.093%, DD 20.6% | 0.094%, DD 18.5% |
| `grind` | 0.096%, DD 20.6% | 0.097%, DD 18.5% |
| `fast` | 0.082%, DD 20.6% | 0.083%, DD 18.5% |
| `top` (opened at the 2021 peak) | 0.075%, DD 20.6% | 0.079%, DD 15.9% |
| `twice` | 0.090%, DD 20.6% | 0.088%, DD 20.6% |

The fund's bars are the stressed ones and the outside series are history's, so this is a check
for harm, not a measure of what the warnings would have read on that path. `twice` moves the
fund's dates after its second bear, which puts the pauses on the wrong dates: it behaves like a
shifted map from the null stage.

## How it works

`RiskGovernor` reads `<provider>_<key>.csv` files as `research/ml/sources.py` writes them. Each
stamp is the moment its value could first be read.

- **Point in time.** A session reads the latest value stamped before 04:00 UTC of its own date.
  Windows count NYSE sessions.
- **Stale data abstains.** A warning whose newest reading is more than seven days old (fourteen
  for a weekly series) casts no vote. If the feed stops, the pause cannot be reached and the
  strategy trades as the plain reserve. A missing file refuses at construction.
- **Live.** The loop starts each session cold, so the strategy reads the files the service wrote
  the evening before. Its diagnostics carry the votes, the warnings raised and any that are stale.

## The data, and keeping it current

`tools/refresh_external.py` fetches the registry twice a day (20:45 and 07:30 Eastern), checks
each series before replacing the stored file, rewrites the warehouse's external lake without the
catalog's writer, and prints the governor's reading. The registry grew from 136 to 170 series:

| Added | Series | Lag |
|---|---|---|
| Office of Financial Research | Financial Stress Index and its eight contributions, daily from 2000 | 4 days |
| CFTC, Traders in Financial Futures | leveraged funds, asset managers and dealers, net share of open interest, Nasdaq-100 and S&P 500 futures, weekly from 2010 | 6 days |
| SqueezeMetrics | dealer gamma (GEX) and dark-pool short share (DIX), daily from 2011 | that evening |
| CBOE | VIX1D, VXD, VXEEM, implied correlation (COR1M, COR3M), dispersion (DSPX) | same day |
| Yahoo | MOVE, SOX, SMH, KRE, JNK, IWF, IWD, ARKK, copper, Nasdaq-100 futures, dollar index | same day |

Tried and left out:

| Source | Why |
|---|---|
| AAII sentiment survey | answers a bot challenge, not the file |
| CBOE put/call ratio files | stop in October 2019 |
| FINRA daily short volume | one file a day: a history is about 2,000 requests. DIX is the same measure in one file |
| NAAIM exposure index | no stable file address |
| Nasdaq earnings and economic calendars | answer browsers only; ruled out earlier |

## Found on the way: the event calendars have run out

`engine/data/fomc_calendar.py`'s list ends 2026-07-29 and the earnings reaction dates end
2026-07-31. Every strategy that sizes up on event days (`event_day_boost_multiplier`,
`earnings_day_boost_multiplier`; the reserve uses 2.5 and 1.5) has not done so since. The FOMC
decisions of 2026-09-16 and 2026-10-28 passed without it; the next is 2026-12-09.

`refresh_external.py` now reads the Federal Reserve's schedule (to the end of 2027), writes it to
`data/external/fomc_calendar.csv` and reports every scheduled meeting the engine's list lacks, on
each run. The list itself is unchanged: it is a source file under `engine/data/`, which this work
could not open.

## Open

- **A paper trial is the next evidence.** The edge here is small and its drawdown gain is one
  episode. The governor reads five of five warnings on 2026-11-10, so it would be pausing now.
- **The event calendars need extending**, and the earnings one needs a source: SEC EDGAR is free
  and asks for a contact address in the request.
- **Not measured:** the governor on Daily Ultimate (`daily_ultimate_tqqq.yaml`), on Ultimate-RSP,
  or scaling lots by the vote count.
- **Options data** (skew and gamma by strike for QQQ and TQQQ) is the one input with no free
  source that this family of signals would use.

## Reproduce

```bash
.venv/bin/python tools/refresh_external.py                    # the series, into data/external
for s in forms frontier robust null stress; do
  .venv/bin/python tools/probe_risk_governor.py --stage $s --out output/risk_governor --jobs 40
done
.venv/bin/python tools/probe_risk_governor.py --report output/risk_governor
```

About 50 seconds a run; the whole measurement is under ten minutes on 40 cores.
