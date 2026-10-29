# Recurrent Neural Hawkes Point Process Execution Timing

**Ledger ID RK353** · rank 353 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Point processes / Recurrent neural networks / Execution |
| Potential effectiveness rank | 353 (1 = strongest) |
| AI implementability rank | 1,879 (1 = easiest) |
| Retail advantage rank | 10,337 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK355, RK357, RK367 |

## In one paragraph

Time child orders by a neural Hawkes forecast of when liquidity will
arrive. Hawkes order flow has execution theory (RK367) and the neural
Hawkes model exists (Mei and Eisner); I found no execution study using
the neural form, and the CSV's reference, arXiv 2104.09876, looks like a
placeholder ID (sequential digits, like arXiv 1908.01234 on RK97) and
could not be identified.

## Evidence

* **Alfonsi & Blanc (2016), "Dynamic optimal execution in a
  mixed-market-impact Hawkes price model," *Finance and Stochastics*
  20(1), 183–218 (arXiv 1404.0648):** with linear impact and other
  traders' orders arriving as a Hawkes process, the optimal execution
  strategy is explicit and reacts to their flow; Poisson arrivals admit
  price manipulation, and Hawkes parameters that balance self-excitation
  against resilience rule it out. (Abstract.)
* **Mei & Eisner (2017):** the neural Hawkes process (see RK304).

## Against, and failure modes

* Needs event-level data; toxicity is defined after the fact.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling. The warehouse holds minute bars only; no historical
quotes, trades or depth.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Alfonsi, A., Blanc, P. (2016). *Finance and Stochastics* 20(1),
  183–218. <https://arxiv.org/abs/1404.0648>. Abstract.
* Mei, H., Eisner, J. (2017). NeurIPS 30.
  <https://arxiv.org/abs/1612.09328>.
