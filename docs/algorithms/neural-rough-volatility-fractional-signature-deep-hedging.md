# Neural Rough Volatility Fractional signature Deep Hedging

**Ledger ID RK391** · rank 391 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Rough path theory / Neural SDEs / Derivatives hedging |
| Potential effectiveness rank | 391 (1 = strongest) |
| AI implementability rank | 699 (1 = easiest) |
| Retail advantage rank | 10,284 (1 = strongest) |
| Fit with this project | ⛔ (options hedging) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK352, RK303, RK328 |

## In one paragraph

Deep hedging under rough volatility, with signature features of the path
as the network's inputs. Deep hedging has been studied under rough
volatility directly: the original architecture struggles with
non-Markovian paths and needs path-aware designs. The CSV's reference,
arXiv 2102.05678, looks like a placeholder ID (sequential digits, like
arXiv 1908.01234 on RK97) and could not be identified.

## Evidence

* **Horvath, Teichmann & Žurič (2021), "Deep Hedging under Rough
  Volatility," *Risks* 9(7), 138 (arXiv 2102.01962):** the deep-hedging
  network trained on non-Markovian rough volatility paths; architectures
  for path dependence; P&L compared with jump-diffusion models under
  infrequent rebalancing. (Abstract.)
* **Buehler, Gonon, Teichmann & Wood (2019), "Deep hedging,"
  *Quantitative Finance* 19(8), 1271–1291 (arXiv 1802.03042):** a
  network chooses hedge positions to minimise a convex risk measure of
  terminal P&L under transaction costs, liquidity limits and risk
  limits; in a Heston market with costs it beats the complete-market
  hedge that ignores frictions; also run on S&P 500 data. (Abstract.)

## Against, and failure modes

* Signature features grow quickly with truncation depth.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Horvath, B., Teichmann, J., Žurič, Ž. (2021). *Risks* 9(7), 138.
  doi:10.3390/risks9070138. Abstract.
* Buehler, H., Gonon, L., Teichmann, J., Wood, B. (2019). "Deep
  hedging." *Quantitative Finance* 19(8), 1271–1291.
  <https://arxiv.org/abs/1802.03042>. Abstract.
