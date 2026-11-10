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
- **On Daily Ultimate it buys nothing** that can be told from chance
  ([On Daily Ultimate](#on-daily-ultimate-no-measurable-gain)). The result below is the
  reserve's.
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

## On Daily Ultimate: no measurable gain

The owner chose Daily Ultimate (`config/daily_ultimate_tqqq.yaml`: fixed 0.8% lots, reversal
lots while turbulent), not the reserve, for the paper trial. Measured the same way, in two
forms: as it was researched, and with the drawdown throttle `paper-ultimate`'s own risk section
applies to whatever it trades (`--stage daily`, `daily-null`, `daily-stress`; 110 runs).

| Book | | Per session | Max DD | 2017–21 | 2022 on |
|---|---|---|---|---|---|
| As researched | no governor | 0.158% | 29.9% | 0.220%, DD 20.5% | 0.095%, DD 21.0% |
| | with the governor | 0.159% | 30.1% | 0.215%, DD 20.8% | 0.101%, DD 19.4% |
| Under paper-ultimate's throttle | no governor | 0.124% | 22.4% | 0.189%, DD 18.2% | 0.056%, DD 21.5% |
| | with the governor | 0.123% | 22.5% | 0.187%, DD 18.2% | 0.056%, DD 20.0% |

| Null control | Return | Drawdown | Return over drawdown |
|---|---|---|---|
| Shifted maps at least as good, as researched | 2 of 40 | 21 of 40 | 15 of 40 |
| Shifted maps at least as good, under the throttle | 16 of 40 | 24 of 40 | 17 of 40 |

- **The governor changes nothing that can be told from chance here.** The same return and the
  same drawdown with it as without, and the real pause map sits in the middle of its
  time-shifted copies.
- **Why the reserve differs.** The reserve's deepest drawdown is a slide inside a calm spell
  (2026-10-06 to 2026-11-05), and the governor was pausing on 52% of those sessions. Daily
  Ultimate's is the 2022 bear (2021-09-07 to 2023-04-25), most of it turbulent, where the book
  holds reversal lots. The pause acts only on calm-grid buying. On the drawdown the two books
  share (2021-02-12 to 2021-05-05) the governor never paused.
- **The throttle costs Daily Ultimate a fifth of its return** (0.158% to 0.124% a session, and
  0.095% to 0.056% from 2022). It was added to `paper-ultimate` for the reserve's trial and
  applies to any algorithm that account trades. Daily Ultimate was not researched with it.
- **Stress:** within about a point and a half either way on `deeper`, `grind` and `fast`.
  Opened at the 2021 peak, the drawdown is 57.6% as researched and 44.1% under the throttle,
  with or without the governor.

The profile is `config/live_profiles/daily-ultimate-governed-tqqq.yaml`. What its trial tests is
the governor running live (the files read at each session's start, the pause, the staleness
rule), not an edge.

### Paper trial

1. **Start the data:** put `VAI_SEC_CONTACT=...` in `.env` if earnings releases are wanted, then
   `docker compose up -d --build market-inputs`. `docker compose logs market-inputs` shows the
   governor's reading.
2. **Rebuild the traders and the web** from this branch, so both have the governor:
   `docker compose up -d --build web paper-ultimate`.
3. **Check:** `docker compose run --rm preflight` now lists the governor's reading and any
   event calendar that has run out.
4. **Switch** `paper-ultimate` to **Daily Ultimate, TQQQ, with the risk governor** on the Live
   page, from a clean book as in [the reserve's trial](daily-ultimate-reserve.md#paper-trial).
   The Live page's diagnostics carry `caution_votes`, `caution_raised` and `caution_stale`.

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

`engine/data/fomc_calendar.py`'s list ends 2026-07-29 and the earnings reaction dates in
`engine/data/earnings_calendar.py` end 2026-07-31. Every strategy that sizes up on event days
(`event_day_boost_multiplier`, `earnings_day_boost_multiplier`; the reserve and Daily Ultimate
use 2.5 and 1.5) has not done so since.

| Calendar | Ends | Missed since | Next |
|---|---|---|---|
| FOMC decisions | 2026-07-29 | 2026-09-16, 2026-10-28 | 2026-12-09 |
| Earnings reaction sessions | 2026-07-31 | 2026-08-27, 09-03, 10-21, 10-22, 10-29, 10-30, 11-03 | after each release |

What now catches it, on every run of `refresh_external.py`:

- **FOMC:** the Federal Reserve's schedule (to the end of 2027) is written to
  `data/external/fomc_calendar.csv`, and every scheduled meeting the engine's list lacks is
  named.
- **Earnings:** each reporter's 8-K under Item 2.02 is read from SEC EDGAR, stamped the second
  the filing was accepted (NVDA's read 16:21 Eastern; its releases are at 16:20). One a quarter
  is kept, the later of two within 45 days, which drops Tesla's delivery counts. For the nine
  megacaps the engine's list covers, EDGAR's reaction sessions are 98.9% in that list. They are
  written to `earnings_releases_edgar.csv` and `earnings_reaction_days.csv`, new ones are
  appended to `data/earnings_releases_derived.csv` (the calendar the event table loads), and
  the reaction sessions the engine's list lacks are named. It needs `VAI_SEC_CONTACT`: the SEC
  asks an automated client for a way to reach its operator.
- **Preflight** warns when a calendar a configured boost reads has run out.

**The two lists themselves are unchanged.** They are source files under `engine/data/`, which
`.claude/settings.json`'s `Read(data/**)` rule keeps this work from opening, the owner's consent
notwithstanding. EDGAR gives releases, not a schedule: a reaction session is known the morning
after, which is when the sizing reads it, but the next release date is not.

## Open

- **The engine's two calendar lists need extending** from the files above, once
  `engine/data/*.py` can be opened: anchor the rule as `Read(/data/**)`, or add the dates by
  hand.
- **The governor's evidence is the reserve's.** Its edge there is small and its drawdown gain is
  one episode; on Daily Ultimate there is none. It reads five of five warnings on 2026-11-10.
- **Not measured:** the governor on Ultimate-RSP, or scaling lots by the vote count.
- **Options data has a source, and no history.** Fidelity's Trader+ serves TQQQ's chain from
  three read-only endpoints, found in a capture the owner saved on 2026-11-10.
  `fidelity_gateway/options_capture.py` reads them out of a capture and appends each reading to
  a series: IV30 and HV30 percentiles, put/call volume and open interest, at-the-money IV,
  25-delta skew, near-chain dealer gamma. That day: IV30 at its 56th percentile with HV30 at its
  100th, a 15.6-point 25-delta skew a week out, put/call volume 0.77. One capture is one moment
  and measures nothing. Collecting daily without a person saving a capture means the three
  endpoints joining `session.READ_ONLY_ENDPOINTS` and the extension's allowlist, a change to
  the real-money bridge and the owner's to make. A signal can be tested only once months of it
  exist.

## Reproduce

```bash
.venv/bin/python tools/refresh_external.py                    # the series, into data/external
for s in forms frontier robust null stress daily daily-null daily-stress; do
  .venv/bin/python tools/probe_risk_governor.py --stage $s --out output/risk_governor --jobs 40
done
.venv/bin/python tools/probe_risk_governor.py --report output/risk_governor
```

About 50 seconds a run; the whole measurement is under fifteen minutes on 40 cores.
