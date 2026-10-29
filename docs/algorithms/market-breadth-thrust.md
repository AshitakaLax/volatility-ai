# Market Breadth Thrust

**Ledger ID RK212** · rank 212 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market internals / timing |
| Potential effectiveness rank | 212 (1 = strongest) |
| AI implementability rank | 58 (1 = easiest) |
| Retail advantage rank | 38 (1 = strongest) |
| Fit with this project | ⏳ as a slow risk-on (re-entry) input |
| Implemented in volatility-ai | **Research code** in `research.catalog.technical_ml`: `zweig_breadth_thrust`; tested on synthetic data, not wired into the engine. No constituent breadth data in the warehouse. |
| Related ledger entries | L12, RK17, RK21 |

## In one paragraph

Martin Zweig's breadth thrust: the 10-day exponential average of NYSE
advances over advances plus declines rises from below 0.40 to above
0.615 within ten sessions. It marks broad buying after a selloff. It is
rare (about 18 signals since 1945, by one vendor's count), and vendors
report the S&P 500 higher a year later after every past signal, with a
median gain near 23%. I found no peer-reviewed test; with about 18
events, little can be established statistically.

## The rule

```text
b_t = EMA_10( adv_t / (adv_t + dec_t) )                    # NYSE issues
signal when b falls below 0.40 and then exceeds 0.615 within 10 sessions
```

## Evidence

* Vendor event studies (SentimenTrader): 18 signals since 1945; the S&P
  500 rose over the next 12 months after each of the previous 17, median
  +22.9%. TradingView posts report about +16% at six months and +24% at
  twelve. In-sample counts with no costs or tests. (Summaries.)
* Near-misses include the March 2002 and February 2008 Nasdaq-100 cases,
  followed by losses of about 35%. (Vendor analysis.)
* **No peer-reviewed test found.**

## Against, and failure modes

* About 18 events: the evidence cannot separate skill from luck.
* Thresholds vary by source; breadth depends on the universe, and
  mega-cap concentration makes NYSE breadth a poor proxy for the
  Nasdaq-100 (the CSV's caveat).

## Fit with volatility-ai

In spirit it is a calm re-entry signal after a selloff, the job the
Ultimate strategy's bear filter already does from price (L12). NYSE
advances and declines are not in the warehouse, and Nasdaq-100 breadth
would need constituent history. Not worth the data work for so few
events.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Zweig, M. *Winning on Wall Street* (1986). Not opened.
* SentimenTrader blog posts on the Zweig Breadth Thrust; TradingView
  posts. Practitioner analyses.
