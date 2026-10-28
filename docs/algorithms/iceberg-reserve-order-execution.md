# Iceberg / Reserve-Order Execution

**Ledger ID RK249** · rank 249 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Execution / market impact |
| Potential effectiveness rank | 249 (1 = strongest) |
| AI implementability rank | 307 (1 = easiest) |
| Retail advantage rank | 6,474 (1 = strongest) |
| Fit with this project | ⛔ (not needed at this book's order sizes) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK244, RK250 |

## In one paragraph

Show only part of a large order and refill it from a hidden reserve as
it executes, to limit the visible footprint. On Euronext Paris hidden
orders made up 44% of order volume; they fill completely less often and
more slowly, and exposing size raised average execution costs, so large
patient orders tend to be hidden and aggressive ones shown.

## Evidence

* **Bessembinder, Panayides & Venkataraman (2009), "Hidden liquidity: An
  analysis of order exposure strategies in electronic stock markets,"
  *Journal of Financial Economics* 94(3), 361–383:** Euronext Paris;
  hidden orders 44% of order volume; lower probability of full execution
  and longer time to completion; exposing rather than hiding size raises
  average execution costs. (Abstract.)

## Against, and failure modes

* Venue support and priority rules differ; icebergs can lose queue
  priority and still move the price (the CSV's caveat).

## Fit with volatility-ai

This book's orders are small against TQQQ's volume. There is no
footprint to hide.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bessembinder, H., Panayides, M., Venkataraman, K. (2009). *Journal of
  Financial Economics* 94(3), 361–383.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:94:y:2009:i:3:p:361-383>.
  Abstract.
