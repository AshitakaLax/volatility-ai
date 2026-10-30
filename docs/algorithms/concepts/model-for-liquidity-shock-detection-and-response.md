# Model for liquidity-shock detection and response

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,674) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Unspecified model |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Relevant as a buy gate for a grid that buys sell-offs, but the evidence for shock detectors is disputed (RK247) and the simple gates are built; background. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Manifold-Valued Scholarly
Liquidity Shock Detector Ver-36") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The title names no method
beyond "model", so this page judges the task itself. The evidence for
the task is summarised below.

## The CSV's description

Proposed model for liquidity-shock detection and response: Estimate when
spreads, depth, or order-flow intensity may deteriorate and adapt trade
size, timing, or order placement to reduce execution risk. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Easley, López de Prado & O'Hara (2012) and Andersen & Bondarenko
  (2014):** VPIN was proposed as a flow-toxicity warning; the critique
  finds the bar-level version adds nothing beyond volume and volatility
  (see RK247). (Abstracts.)
* **Nagel (2012), "Evaporating Liquidity," *Review of Financial Studies*
  25(7):** returns to liquidity provision (short-term reversal) rise
  sharply in turmoil and are predictable with the VIX. (Standard
  reference.)
* **Amihud (2002), *Journal of Financial Markets* 5(1), 31–56:** market
  illiquidity raises expected returns, and unexpected illiquidity lowers
  prices at the time (see RK59). (Standard reference.)

## Against, and failure modes

* The best-known shock detector (VPIN) is disputed; at bar level it adds
  little beyond volume and volatility.
* A grid that buys sell-offs is a liquidity provider: stepping back in a
  shock also skips the period when providing liquidity pays most (Nagel
  2012).

## Fit with volatility-ai

The engine's orders are small, and its grid buys into sell-offs. A shock
detector matters here only as a bid-side gate (RK247's VPIN gate,
RK244's spread gate), not as an execution system.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Easley, D., López de Prado, M., O'Hara, M. (2012). *Review of
  Financial Studies* 25(5); Andersen, T. G., Bondarenko, O. (2014).
  *Journal of Financial Markets* 17. See RK247.
* Nagel, S. (2012). "Evaporating Liquidity." *Review of Financial
  Studies* 25(7). Standard reference.
* Amihud, Y. (2002). "Illiquidity and stock returns." *Journal of
  Financial Markets* 5(1), 31–56. Standard reference.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3674 | Manifold-Valued Scholarly Liquidity Shock Detector Ver-36 | Koopman operator / Model predictive control / ETF execution | 3824 | 2767 | No |
| 3683 | Manifold-Valued Scholarly Liquidity Shock Detector Ver-136 | Koopman operator / Model predictive control / ETF execution | 3835 | 2773 | No |
| 7407 | Optimal Scholarly Liquidity Shock Detector MK-42 | Robust statistics / Mean-variance / Index allocation | 388 | 964 | No |
| 13841 | Recurrent Scholarly Liquidity Shock Detector Ver-96 | Koopman operator / Model predictive control / ETF execution | 3831 | 2873 | No |
| 13845 | Recurrent Scholarly Liquidity Shock Detector Ver-196 | Koopman operator / Model predictive control / ETF execution | 3842 | 2896 | No |
