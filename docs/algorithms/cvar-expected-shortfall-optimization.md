# CVaR / Expected-Shortfall Optimization

**Ledger ID RK53** · rank 53 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio construction |
| Potential effectiveness rank | 53 (1 = strongest) |
| AI implementability rank | 202 (1 = easiest) |
| Retail advantage rank | 162 (1 = strongest) |
| Fit with this project | ⏳ for a multi-ETF book; not applicable to the single-instrument grid |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | A5, RK60, RK88, RK95 |

## In one paragraph

Choose portfolio weights to minimise (or cap) conditional value-at-risk,
the average loss in the worst α% of scenarios, instead of variance.
Rockafellar and Uryasev showed it reduces to a linear programme over
historical or simulated scenarios, which is why every optimisation
library offers it. It is the natural objective for a book judged on
drawdowns, but it needs a multi-asset book to have anything to choose
between, and tail estimates from a decade of data rest on a handful of
crashes.

## The rule

```
given scenarios r_s (s = 1..S, e.g. daily returns), weights w, level alpha (e.g. 95%):
minimise  VaR + 1/((1-alpha) S) x sum_s max(0, -w.r_s - VaR)       # Rockafellar-Uryasev
subject to sum w = 1, w >= 0 (long-only), optional return floor
```

## Evidence

* **Rockafellar & Uryasev (2000), *Journal of Risk* 2:** minimising CVaR
  (rather than VaR) yields portfolios with low VaR as well; VaR and CVaR
  are computed together and the problem reduces to linear or nonsmooth
  programming with scenarios; widely implemented in optimisation
  packages. (Abstract and records.)

## Against, and failure modes

* Data-hungry and unstable tail estimates; the result depends on which
  crises are in the sample (the CSV's caveat).
* With few assets and a short history, CVaR weights swing with the
  scenario set.

## Fit with volatility-ai

Long-only weights over ETFs fit the constraints. The project's live book
is one instrument at a time (the engine is single-symbol); the
multi-instrument books (N7, X2, X3, A5) are harnesses that add sleeves'
P&L, and an allocator is ledger §11 item 11. CVaR weights would belong
there, beside HRP.

## What it would take

A scenario matrix of sleeve returns (from the harness runs) and a small
LP (PyPortfolioOpt or skfolio, the CSV's references) to set sleeve
weights, compared with HRP and equal weights out of sample.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Rockafellar, R. T., Uryasev, S. (2000). "Optimization of Conditional
  Value-at-Risk." *Journal of Risk* 2, 21–41 (issue number differs by
  source). <https://ideas.repec.org/a/rsk/journ4/2161159.html>. Abstract.
* The CSV's own reference: <https://github.com/PyPortfolio/PyPortfolioOpt>.
