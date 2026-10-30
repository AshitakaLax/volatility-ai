# Continuous-Time Mean-Field Portfolio Game with Competition

**Ledger ID RK125** · rank 125 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Game Theory / Mean-field games / Portfolio theory |
| Potential effectiveness rank | 125 (1 = strongest) |
| AI implementability rank | 176 (1 = easiest) |
| Retail advantage rank | 77 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A theory of competing fund managers, not a trading rule. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK368 |

## In one paragraph

Solve for Nash-equilibrium allocations when fund managers care about
performance relative to their peers' average. Lacker and Zariphopoulou
give explicit equilibria: competition pushes CARA managers into more
risk; CRRA managers may over- or under-invest. It explains herding; it
does not tell a single account what to hold, and the CSV's reference,
arXiv 1908.05678, could not be identified.

## Evidence

* **Lacker & Zariphopoulou (2019), *Mathematical Finance* 29(4):**
  explicit constant equilibria for n-agent and mean-field games under
  relative performance; competition raises CARA agents' risky holdings.
  (Abstract.)

## Against, and failure modes

* A model of benchmark-chasing institutions; a private account has no
  peer benchmark.

## Fit with volatility-ai

Nothing to implement for one private book: the result is an equilibrium
of other investors' behaviour.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lacker, D., Zariphopoulou, T. (2019). Mean field and n-agent games for
  optimal investment under relative performance criteria. *Mathematical
  Finance* 29(4), 1003–1038. Abstract.
* The CSV's reference, arXiv 1908.05678 (not identified).
