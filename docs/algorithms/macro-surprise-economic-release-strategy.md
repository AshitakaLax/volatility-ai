# Macro Surprise / Economic Release Strategy

**Ledger ID RK211** · rank 211 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Macro / event-driven |
| Potential effectiveness rank | 211 (1 = strongest) |
| AI implementability rank | 207 (1 = easiest) |
| Retail advantage rank | 164 (1 = strongest) |
| Fit with this project | ⛔ as a release-reaction trade · ✅ scheduled event days as a sizing input (V6) |
| Implemented in volatility-ai | **Partial.** The champion sizes up on FOMC decision days (V6, `event_day_boost_multiplier` on `HighFrequencyLocalReferenceSizing`, from a hand-verified FOMC calendar); no surprise measure (actual minus consensus) and no release trade. |
| Related ledger entries | V6, RK45 |

## In one paragraph

Trade rates, FX or equity-index futures in the seconds and minutes after
a scheduled release when the number differs from consensus. That
reaction is a speed game for institutional desks. The finding that
matters for a long-only holder is different: equity excess returns are
concentrated on announcement days (11.4 bp against 1.1 bp on other days,
1958–2009), and in the day before FOMC decisions.

## The rule

```text
surprise = (actual - consensus) / std(past surprises), known at the release timestamp
trade the instrument's expected response in the first minutes; flat after the event window
```

## Evidence

* **Savor & Wilson (2013), *JFQA*:** average excess market return of
  11.4 bp on CPI, unemployment and FOMC announcement days against 1.1 bp
  on other days, 1958–2009; Sharpe ratio about ten times higher on those
  days. A later update reports 10.7 bp against 0.9 bp for 1961–2023.
  (Abstract and summaries.)
* **Lucca & Moench (2015), "The Pre-FOMC Announcement Drift," *Journal
  of Finance* 70(1):** large S&P 500 excess returns in the 24 hours
  before scheduled FOMC announcements. (Standard reference; the size was
  not re-checked here.)
* **Andersen, Bollerslev, Diebold & Vega (2003), *American Economic
  Review* 93(1):** announcement surprises produce conditional-mean jumps
  in exchange rates within minutes. (Standard reference; not
  re-checked.)
* **In this repository:** FOMC days carry +34.1% realised intraday
  volatility (74 sessions); sizing up on them (V6, 2.5×) added about 1.7
  points to a 166% backtest return (`high_frequency_sizing.py`
  docstring).

## Against, and failure modes

* Consensus snapshots and release timestamps must be point-in-time;
  revisions and headline/core splits (the CSV's caveat).
* The reaction trade needs sub-second execution.

## Fit with volatility-ai

The release trade is out. The calendar half is already in the champion
(V6). The pre-FOMC drift suggests one cheap variant: boost lots in the
session before an FOMC decision as well as on the day.

## How to test it here

Add a `pre_event_day_boost` beside V6's FOMC boost (the same calendar
shifted one session earlier) and run it against the champion with causal
fills. Expect a change of a point or two at most, as for V6 itself.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Savor, P., Wilson, M. (2013). "How Much Do Investors Care About
  Macroeconomic Risk? Evidence from Scheduled Economic Announcements."
  *Journal of Financial and Quantitative Analysis* 48(2). Abstract.
* Lucca, D. O., Moench, E. (2015). "The Pre-FOMC Announcement Drift."
  *Journal of Finance* 70(1). Not re-checked.
* Andersen, T. G., Bollerslev, T., Diebold, F. X., Vega, C. (2003).
  "Micro Effects of Macro Announcements." *American Economic Review*
  93(1). Not re-checked.
* This repository: `research/strategies/high_frequency_sizing.py` (V6),
  ledger V6.
