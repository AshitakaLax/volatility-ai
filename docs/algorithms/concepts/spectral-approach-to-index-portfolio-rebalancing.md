# Spectral approach to index portfolio rebalancing

**Concept page** · shared by **4** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,613) ·
researched 2026-10-30

| | |
|---|---|
| Task | Index portfolio rebalancing |
| Method | Spectral (frequency-domain) decomposition |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A spectral method could set a sleeve's rebalance, but the book holds no constituents and no study shows it beating a plain threshold rebalance; background. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK210, X3 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Spectral Scholarly Stock
Index Rebalancer Ver-20") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Update constituent weights when a benchmark or target allocation
changes, managing tracking error, turnover and execution costs. The
spectral version works in the frequency domain, filtering or weighting
components by cycle length. I found no study of this method on this
task.

## The CSV's description

Proposed spectral approach to index portfolio rebalancing: Update
constituent weights when a benchmark or target allocation changes while
managing tracking error, turnover, and execution costs. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Petajisto (2011), "The index premium and its hidden cost for index
  funds," *Journal of Empirical Finance* 18(2), 271–288:** index
  reconstitution costs index funds at least 21–28 bp a year on the S&P
  500 and 38–77 bp on the Russell 2000. (Abstract.)
* **Gârleanu & Pedersen (2013), "Dynamic Trading with Predictable
  Returns and Transaction Costs," *Journal of Finance* 68(6),
  2309–2340:** with costs, aim in front of the target and trade only
  partway toward the aim; slower-decaying signals get more weight. Net
  of costs it beat naive rules on commodity futures. (Abstract.)

## Against, and failure modes

* Rebalancing more often adds cost without adding return; the
  reconstitution effect it trades around has been arbitraged (RK210).
* Spectral estimates need long stationary windows; market cycles are
  neither.

## Fit with volatility-ai

Relevant only to rebalancing a multi-ETF sleeve (X2, X3); the engine's
single-symbol book has no constituent weights. Owning index ETFs passes
the reconstitution cost on silently (Petajisto 2011).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Petajisto, A. (2011). *Journal of Empirical Finance* 18(2), 271–288.
  Abstract.
* Gârleanu, N., Pedersen, L. H. (2013). *Journal of Finance* 68(6),
  2309–2340. doi:10.1111/jofi.12080. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1613 | Spectral Scholarly Stock Index Rebalancer Ver-20 | Fractional calculus / ETF momentum strategy | 3822 | 2128 | No |
| 1637 | Spectral Scholarly Stock Index Rebalancer Ver-120 | Fractional calculus / ETF momentum strategy | 1886 | 308 | No |
| 8396 | Spectral Scholarly Stock Index Rebalancer MK-30 | Neural operators / Continuous normalizing flows / ETF rotation | 5792 | 2123 | No |
| 8414 | Spectral Scholarly Stock Index Rebalancer MK-90 | Neural operators / Continuous normalizing flows / ETF rotation | 5795 | 2126 | No |
