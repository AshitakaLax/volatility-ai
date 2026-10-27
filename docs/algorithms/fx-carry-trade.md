# FX Carry Trade

**Ledger ID RK30** · rank 30 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Carry / macro |
| Potential effectiveness rank | 30 (1 = strongest) |
| AI implementability rank | 38 (1 = easiest) |
| Retail advantage rank | 101 (1 = strongest) |
| Fit with this project | ⛔ (FX forwards, a short funding currency) |
| Implemented in volatility-ai | **No.** (Q6, the Oil Money krone/Brent study, is the only FX code, and it is rejected.) |
| Related ledger entries | RK4, Q6 |

## In one paragraph

Borrow in low-interest-rate currencies and lend in high-rate ones. If
exchange rates moved to offset the rate gap (uncovered interest parity),
this would earn nothing; empirically they do not, and the trade earned
several percent a year with a Sharpe ratio around 0.6 in the decades
before 2008. It earns that by bearing crash risk: high-rate currencies
fall together and fast when risk appetite and funding liquidity
collapse, which is when every other risky book falls too.

## The rule

```
monthly: rank G10 (or broader) currencies by short-term interest rate (or forward discount)
long the top 3, short the bottom 3 via one-month forwards; equal or risk weights
```

## Evidence

* **Lustig, Roussanov & Verdelhan (2011), *Review of Financial Studies*
  24(11), 3731–3777:** a "slope" factor explains most of the
  cross-section of carry returns; high-rate currencies load on it more;
  the global factor tracks equity-market volatility. The working paper
  reports a spread of more than 5 percentage points a year, 1983–2007,
  Sharpe about 0.6. (Abstract and working paper.)
* **Brunnermeier, Nagel & Pedersen (2008):** carry returns are
  negatively skewed (crash risk) because of sudden unwinding when risk
  appetite and funding liquidity fall; skewness rises with the VIX.
  (Abstract.)

## Against, and failure modes

* Crashes: 2008 (yen-funded carry unwound), and episodes like the 2015
  Swiss franc de-pegging that break stop-losses.
* The rate differential alone is not the trade; forwards, funding and
  intervention risk matter (the CSV's caveat).

## Fit with volatility-ai

Out of scope: currencies and a short funding leg. The useful lesson is
the correlation: carry is a bet on calm, funded markets, the same bet a
leveraged equity grid makes, so it would not diversify this book.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lustig, H., Roussanov, N., Verdelhan, A. (2011). "Common Risk Factors
  in Currency Markets." *Review of Financial Studies* 24(11), 3731–3777.
  Abstract and working paper.
* Brunnermeier, M., Nagel, S., Pedersen, L. H. (2008). "Carry Trades and
  Currency Crashes." *NBER Macroeconomics Annual* 23; NBER w14473.
  <https://www.nber.org/papers/w14473>. Abstract.
