# Intangibles-Adjusted Value and Profitability Factor

**Ledger ID RK31** · rank 31 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity factor / fundamental valuation / intangible capital |
| Potential effectiveness rank | 31 (1 = strongest) |
| AI implementability rank | 46 (1 = easiest) |
| Retail advantage rank | 60 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket (needs R&D and statement data) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK48, RK12, RK13 |

## In one paragraph

Book value misses capital that firms build by spending: R&D, brand and
organisation. Capitalise those expenses into an intangible asset, add it
to book equity and adjust profitability to match, then rank stocks on
the adjusted value and profitability. The motivation is strong: the
value factor's worst drawdown on record (2017–2020) is partly blamed on
book-to-price missing intangibles. The specific hybrid in the CSV is
one of the five rows it added with research references and no
backtest, and it says so: the papers support the idea, not this rule.

## The rule (the CSV's specification)

```
intangible capital K_t = (1 - delta) K_{t-1} + R&D_t                  # perpetual inventory; delta e.g. 15% for R&D
(optional, tested separately) + a share of SG&A as organisation capital
adjusted book    = book equity + K
adjusted profits = operating profits + R&D - delta K                  # R&D treated as investment
rank within industry on adjusted B/M and adjusted profitability; long-only diversified basket
```

Every parameter (depreciation rate, which expenses, industry
normalisation, rebalance frequency) must be fixed before testing; the
CSV lists them as open.

## Evidence

* **Peters & Taylor (2017), *Journal of Financial Economics* 123(2),
  251–272:** with intangible capital counted, Tobin's q explains physical
  and intangible investment about equally well and total investment
  better; their total-q measure divides market value by physical plus
  intangible capital. (Abstract.) This is the capitalisation method the
  rule borrows.
* **Arnott, Harvey, Kalesnik & Linnainmaa (2021):** value's recent
  underperformance is partly an outdated book-to-price definition that
  misses intangibles. (Summary.)
* **"Revisiting Asset Pricing Models: The Case for an Intangibles
  Factor," *Financial Management* (2025):** an intangibles-intensity
  factor strongly predicts returns, adds explanatory power to the
  five-factor and q-factor models and makes the investment factor
  redundant. (Abstract; very probably the CSV's `fima.70001` reference,
  not confirmed by DOI.)
* The CSV's second reference (`fima.12505`) is still unconfirmed. The
  owner-supplied Gemini answer attributes it to Ozdagli & Ryfe, "Asset
  Manager Commonality and Portfolio Similarity". A Federal Reserve Bank
  of Dallas working paper of that title exists (WP 2515, on life insurers
  that share an asset manager), but its publication under this DOI could
  not be confirmed. If the attribution is right, the reference has
  nothing to do with intangibles.

## Against, and failure modes

* Many free choices (depreciation rates, SG&A share), each one a way to
  overfit.
* Reporting lags and the R&D line itself (not every firm reports it).
* The 2025 factor is intangibles *intensity*, not this adjusted-value
  hybrid; evidence for one is not evidence for the other.

## Fit with volatility-ai

A long-only stock basket fits the instrument rule; R&D histories and
point-in-time statements are not in the repository. Reference entry.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Peters, R. H., Taylor, L. A. (2017). "Intangible Capital and the
  Investment-q Relation." *Journal of Financial Economics* 123(2),
  251–272. Abstract.
* Arnott, R., Harvey, C. R., Kalesnik, V., Linnainmaa, J. (2021).
  "Reports of Value's Death May Be Greatly Exaggerated." *Financial
  Analysts Journal* 77(1). Summary.
* "Revisiting Asset Pricing Models: The Case for an Intangibles Factor."
  *Financial Management* (2025).
  <https://onlinelibrary.wiley.com/doi/full/10.1111/fima.70001> (the
  CSV's reference). Abstract via the Erasmus repository listing.
* <https://onlinelibrary.wiley.com/doi/full/10.1111/fima.12505> (the
  CSV's second reference): not confirmed. Possibly Ozdagli, A., Ryfe, D.
  "Asset Manager Commonality and Portfolio Similarity." Federal Reserve
  Bank of Dallas Working Paper 2515 (revised 2025),
  <https://ideas.repec.org/p/fip/feddwp/99954.html>. Abstract.
