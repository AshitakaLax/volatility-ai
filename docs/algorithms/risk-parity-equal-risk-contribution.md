# Risk Parity / Equal Risk Contribution

**Ledger ID RK61** · rank 61 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio construction |
| Potential effectiveness rank | 61 (1 = strongest) |
| AI implementability rank | 45 (1 = easiest) |
| Retail advantage rank | 122 (1 = strongest) |
| Fit with this project | ⏳ unlevered long-only ERC over ETFs · ⛔ the levered form (borrowing to lever bonds) |
| Implemented in volatility-ai | **Partial.** HRP (A5) is built; equal risk contribution is not. |
| Related ledger entries | A5, RK56, RK60, RK95, RK99 |

## In one paragraph

Weight assets so each contributes the same share of portfolio risk, then
(in the classic form) lever the whole book up to a target volatility.
Because bonds are less volatile, an equal-risk book holds much more of
them than a 60/40, and the leverage brings the return back. Asness,
Frazzini and Pedersen's justification is leverage aversion: investors
who will not borrow overpay for risky assets, so the safe ones earn more
per unit of risk. The unlevered weights fit this project; the leverage
does not.

## The rule

```
risk contribution RC_i = w_i x (Sigma w)_i / sqrt(w' Sigma w)
solve for w >= 0, sum w = 1 with RC_i equal for all i          # ERC (Maillard, Roncalli & Teiletche)
special case (zero correlations): w_i proportional to 1 / sigma_i   # inverse volatility
classic risk parity: then lever the book to a target volatility (e.g. 10%)
```

## Evidence

* **Maillard, Roncalli & Teiletche (2010), *Journal of Portfolio
  Management* 36(4):** defines the equally weighted risk-contribution
  portfolio and shows its volatility lies between minimum-variance and
  equal-weight portfolios. (Summaries.)
* **Asness, Frazzini & Pedersen (2012), *Financial Analysts Journal*
  68(1), 47–59:** leverage aversion makes safer assets offer higher
  risk-adjusted returns; risk parity exploits this by overweighting
  them. (Abstract; the authors' firm offers risk-parity funds.)
* Contested in the same journal: Goldberg and co-authors, "Will My Risk
  Parity Outperform?" (2012), and a reply. (Index records.)

## Against, and failure modes

* Risk contributions change suddenly when correlations jump (the CSV's
  caveat).
* The classic levered form depends on bonds: 2022's simultaneous stock
  and bond losses were its worst case.

## Fit with volatility-ai

Unlevered ERC over a few ETFs fits; borrowing to lever the bond leg is
out. As with every allocator, the testing ground is the rotation
harness's additive account (ledger §11 item 11 is a real allocator).

## How to test it here

Add an ERC solver (a few lines of scipy `minimize`, or skfolio) as
`--mode erc` beside `--mode hrp` in `tools/rotation.py`; compare ERC,
HRP, minimum variance (RK60) and equal weight over one universe chosen
in advance.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Maillard, S., Roncalli, T., Teiletche, J. (2010). "The Properties of
  Equally Weighted Risk Contribution Portfolios." *Journal of Portfolio
  Management* 36(4), 60–70. Summaries.
* Asness, C., Frazzini, A., Pedersen, L. H. (2012). "Leverage Aversion
  and Risk Parity." *Financial Analysts Journal* 68(1), 47–59.
  <https://ideas.repec.org/a/taf/ufajxx/v68y2012i1p47-59.html>. Abstract.
* The CSV's own reference: <https://github.com/PyPortfolio/PyPortfolioOpt>.
