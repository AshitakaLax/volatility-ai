# Markov-state-based approach to sector allocation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,507) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Hidden Markov / regime-switching states |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Business-cycle sector rotation fails even with perfect foresight of the cycle (at most about 2.3% a year gross, less after costs); a regime model cannot do better than foresight. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Markovian Scholarly Sector
Allocation Strategy Alpha-81") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The Markov-state version infers hidden states (calm, turbulent, crisis)
and conditions on the current one. Rotating sectors by economic regime
is the conventional version, and the evidence is against it: perfect
knowledge of the business cycle bought little before costs.

## The CSV's description

Proposed Markov-state-based approach to sector allocation: Compare
sector-level return, trend, or risk signals and periodically adjust
weights among sector funds; concentration and turnover need to be
controlled. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Moskowitz & Grinblatt (1999), "Do Industries Explain Momentum?"
  *Journal of Finance* 54(4), 1249–1290:** industry momentum is highly
  profitable after controls and accounts for much of stock momentum.
  (Abstract.)
* **Stangl, Jacobsen & Visaltanachoti (2009), "Sector rotation over
  business cycles":** rotating sectors by the conventional
  business-cycle map, even with perfect foresight of the cycle, beat the
  market by at most about 2.3% a year gross (1948–2007), and less with
  timing errors and costs; a 2023 follow-up by Molchanov and Stangl
  finds no systematic sector performance where the map expects it.
  (Abstracts and summaries.)

## Against, and failure modes

* Sector rotation adds turnover and taxes; the long-only half keeps only
  part of the long-short industry-momentum premium.
* States are clear only after the fact; causal (filtered) state
  probabilities lag turning points.

## Fit with volatility-ai

Built as X3 (relative-strength rotation across a small ETF universe) and
RK19 (sector momentum), neither yet measured. A sector sleeve would sit
beside the grid, not inside it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T. J., Grinblatt, M. (1999). *Journal of Finance* 54(4),
  1249–1290. Abstract.
* Stangl, J., Jacobsen, B., Visaltanachoti, N. (2009). "Sector rotation
  over business cycles." Working paper. Molchanov, A., Stangl, J.
  (2023). "The myth of business cycle sector rotation." Abstracts.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8507 | Markovian Scholarly Sector Allocation Strategy Alpha-81 | Graph neural networks / Sector contagion / Equity baskets | 4607 | 2916 | No |
| 8547 | Markovian Scholarly Sector Allocation Strategy Alpha-181 | Graph neural networks / Sector contagion / Equity baskets | 4615 | 2937 | No |
| 8587 | Markovian Scholarly Sector Allocation Strategy Alpha-281 | Graph neural networks / Sector contagion / Equity baskets | 13472 | 13703 | No |
| 8627 | Markovian Scholarly Sector Allocation Strategy Alpha-381 | Graph neural networks / Sector contagion / Equity baskets | 4635 | 2984 | No |
| 8667 | Markovian Scholarly Sector Allocation Strategy Alpha-481 | Graph neural networks / Sector contagion / Equity baskets | 4643 | 3005 | No |
