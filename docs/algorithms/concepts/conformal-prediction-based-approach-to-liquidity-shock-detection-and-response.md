# Conformal-prediction-based approach to liquidity-shock detection and response

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,863) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Conformal prediction intervals |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Conformal prediction could drive a buy gate, but no study shows it beating the simple spread and volume gates already built (RK244, RK247); background. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Conformal Scholarly
Liquidity Shock Deflector Sys-242") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The conformal version wraps
a forecast in distribution-free prediction intervals and acts only when
the interval is decisive. I found no study of this method on this task.

## The CSV's description

Proposed conformal-prediction-based approach to liquidity-shock
detection and response: Estimate when spreads, depth, or order-flow
intensity may deteriorate and adapt trade size, timing, or order
placement to reduce execution risk. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

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
* Conformal intervals measure a forecast's uncertainty; they do not
  create a forecast where none exists.

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
| 1863 | Conformal Scholarly Liquidity Shock Deflector Sys-242 | Robust optimization / Distributionally robust CVaR / Index tracking | 4716 | 3304 | No |
| 1912 | Conformal Scholarly Liquidity Shock Deflector Sys-722 | Robust optimization / Distributionally robust CVaR / Index tracking | 4747 | 3399 | No |
| 1961 | Conformal Scholarly Liquidity Shock Deflector Sys-1202 | Robust optimization / Distributionally robust CVaR / Index tracking | 4778 | 3494 | No |
| 2010 | Conformal Scholarly Liquidity Shock Deflector Sys-1682 | Robust optimization / Distributionally robust CVaR / Index tracking | 4809 | 3589 | No |
| 2071 | Conformal Scholarly Liquidity Shock Deflector Mod-302 | Robust optimization / Distributionally robust CVaR / Index tracking | 4850 | 3711 | No |
| 2124 | Conformal Scholarly Liquidity Shock Deflector Mod-782 | Robust optimization / Distributionally robust CVaR / Index tracking | 4877 | 3806 | No |
| 2177 | Conformal Scholarly Liquidity Shock Deflector Mod-1262 | Robust optimization / Distributionally robust CVaR / Index tracking | 4904 | 3901 | No |
| 2230 | Conformal Scholarly Liquidity Shock Deflector Mod-1742 | Robust optimization / Distributionally robust CVaR / Index tracking | 4931 | 3996 | No |
| 2283 | Conformal Scholarly Liquidity Shock Deflector Mod-2222 | Robust optimization / Distributionally robust CVaR / Index tracking | 4958 | 4091 | No |
| 2336 | Conformal Scholarly Liquidity Shock Deflector Mod-2702 | Robust optimization / Distributionally robust CVaR / Index tracking | 4985 | 4186 | No |
| 2389 | Conformal Scholarly Liquidity Shock Deflector Mod-3182 | Robust optimization / Distributionally robust CVaR / Index tracking | 5012 | 4281 | No |
| 2442 | Conformal Scholarly Liquidity Shock Deflector Mod-3662 | Robust optimization / Distributionally robust CVaR / Index tracking | 5039 | 4376 | No |
| 3228 | Conformal Scholarly Liquidity Shock Deflector Sys-434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5406 | 8499 | No |
| 3250 | Conformal Scholarly Liquidity Shock Deflector Sys-914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5414 | 8534 | No |
| 3272 | Conformal Scholarly Liquidity Shock Deflector Sys-1394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5422 | 8569 | No |
| 3294 | Conformal Scholarly Liquidity Shock Deflector Sys-1874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5430 | 8604 | No |
| 3302 | Conformal Scholarly Liquidity Shock Deflector Mod-14 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5433 | 8613 | No |
| 3320 | Conformal Scholarly Liquidity Shock Deflector Mod-494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5441 | 8650 | No |
| 3338 | Conformal Scholarly Liquidity Shock Deflector Mod-974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5449 | 8687 | No |
| 3356 | Conformal Scholarly Liquidity Shock Deflector Mod-1454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5457 | 8724 | No |
| 3374 | Conformal Scholarly Liquidity Shock Deflector Mod-1934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5465 | 8761 | No |
| 3392 | Conformal Scholarly Liquidity Shock Deflector Mod-2414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5473 | 8798 | No |
| 3410 | Conformal Scholarly Liquidity Shock Deflector Mod-2894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5481 | 8835 | No |
| 3428 | Conformal Scholarly Liquidity Shock Deflector Mod-3374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5489 | 8872 | No |
| 3446 | Conformal Scholarly Liquidity Shock Deflector Mod-3854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5497 | 8909 | No |
| 7540 | Conformal Scholarly Liquidity Shock Deflector Sys-338 | Attention networks / Transformer encoders / Stock alpha generation | 12839 | 11938 | No |
| 7571 | Conformal Scholarly Liquidity Shock Deflector Sys-818 | Attention networks / Transformer encoders / Stock alpha generation | 12849 | 11961 | No |
| 7602 | Conformal Scholarly Liquidity Shock Deflector Sys-1298 | Attention networks / Transformer encoders / Stock alpha generation | 12859 | 11984 | No |
| 7633 | Conformal Scholarly Liquidity Shock Deflector Sys-1778 | Attention networks / Transformer encoders / Stock alpha generation | 12869 | 12007 | No |
| 7676 | Conformal Scholarly Liquidity Shock Deflector Mod-398 | Attention networks / Transformer encoders / Stock alpha generation | 12884 | 12037 | No |
| 7708 | Conformal Scholarly Liquidity Shock Deflector Mod-878 | Attention networks / Transformer encoders / Stock alpha generation | 12896 | 12060 | No |
| 7740 | Conformal Scholarly Liquidity Shock Deflector Mod-1358 | Attention networks / Transformer encoders / Stock alpha generation | 12908 | 12083 | No |
| 7772 | Conformal Scholarly Liquidity Shock Deflector Mod-1838 | Attention networks / Transformer encoders / Stock alpha generation | 12920 | 12106 | No |
| 7804 | Conformal Scholarly Liquidity Shock Deflector Mod-2318 | Attention networks / Transformer encoders / Stock alpha generation | 12932 | 12129 | No |
| 7836 | Conformal Scholarly Liquidity Shock Deflector Mod-2798 | Attention networks / Transformer encoders / Stock alpha generation | 12944 | 12152 | No |
| 7868 | Conformal Scholarly Liquidity Shock Deflector Mod-3278 | Attention networks / Transformer encoders / Stock alpha generation | 12956 | 12175 | No |
| 7900 | Conformal Scholarly Liquidity Shock Deflector Mod-3758 | Attention networks / Transformer encoders / Stock alpha generation | 12968 | 12198 | No |
| 9092 | Conformal Scholarly Liquidity Shock Deflector Sys-50 | Neural operators / Deep operator networks / ETF rotation | 9324 | 7639 | No |
| 9129 | Conformal Scholarly Liquidity Shock Deflector Sys-146 | Quantum machine learning / Variational circuits / Index prediction | 13995 | 14000 | No |
| 9279 | Conformal Scholarly Liquidity Shock Deflector Sys-530 | Neural operators / Deep operator networks / ETF rotation | 9340 | 7661 | No |
| 9316 | Conformal Scholarly Liquidity Shock Deflector Sys-626 | Quantum machine learning / Variational circuits / Index prediction | 14004 | 14008 | No |
| 9466 | Conformal Scholarly Liquidity Shock Deflector Sys-1010 | Neural operators / Deep operator networks / ETF rotation | 9356 | 7683 | No |
| 9503 | Conformal Scholarly Liquidity Shock Deflector Sys-1106 | Quantum machine learning / Variational circuits / Index prediction | 14013 | 14016 | No |
| 9653 | Conformal Scholarly Liquidity Shock Deflector Sys-1490 | Neural operators / Deep operator networks / ETF rotation | 9372 | 7705 | No |
| 9690 | Conformal Scholarly Liquidity Shock Deflector Sys-1586 | Quantum machine learning / Variational circuits / Index prediction | 14022 | 14024 | No |
| 9840 | Conformal Scholarly Liquidity Shock Deflector Sys-1970 | Neural operators / Deep operator networks / ETF rotation | 9388 | 7727 | No |
| 9896 | Conformal Scholarly Liquidity Shock Deflector Mod-110 | Neural operators / Deep operator networks / ETF rotation | 9392 | 7735 | No |
| 9933 | Conformal Scholarly Liquidity Shock Deflector Mod-206 | Quantum machine learning / Variational circuits / Index prediction | 14033 | 14034 | No |
| 10087 | Conformal Scholarly Liquidity Shock Deflector Mod-590 | Neural operators / Deep operator networks / ETF rotation | 9409 | 7765 | No |
| 10124 | Conformal Scholarly Liquidity Shock Deflector Mod-686 | Quantum machine learning / Variational circuits / Index prediction | 14041 | 14042 | No |
| 10278 | Conformal Scholarly Liquidity Shock Deflector Mod-1070 | Neural operators / Deep operator networks / ETF rotation | 9426 | 7795 | No |
| 10315 | Conformal Scholarly Liquidity Shock Deflector Mod-1166 | Quantum machine learning / Variational circuits / Index prediction | 14049 | 14050 | No |
| 10469 | Conformal Scholarly Liquidity Shock Deflector Mod-1550 | Neural operators / Deep operator networks / ETF rotation | 9443 | 7825 | No |
| 10506 | Conformal Scholarly Liquidity Shock Deflector Mod-1646 | Quantum machine learning / Variational circuits / Index prediction | 14057 | 14058 | No |
| 10660 | Conformal Scholarly Liquidity Shock Deflector Mod-2030 | Neural operators / Deep operator networks / ETF rotation | 9460 | 7855 | No |
| 10697 | Conformal Scholarly Liquidity Shock Deflector Mod-2126 | Quantum machine learning / Variational circuits / Index prediction | 14065 | 14066 | No |
| 10851 | Conformal Scholarly Liquidity Shock Deflector Mod-2510 | Neural operators / Deep operator networks / ETF rotation | 9477 | 7885 | No |
| 10888 | Conformal Scholarly Liquidity Shock Deflector Mod-2606 | Quantum machine learning / Variational circuits / Index prediction | 14073 | 14074 | No |
| 11042 | Conformal Scholarly Liquidity Shock Deflector Mod-2990 | Neural operators / Deep operator networks / ETF rotation | 9494 | 7915 | No |
| 11079 | Conformal Scholarly Liquidity Shock Deflector Mod-3086 | Quantum machine learning / Variational circuits / Index prediction | 14081 | 14082 | No |
| 11233 | Conformal Scholarly Liquidity Shock Deflector Mod-3470 | Neural operators / Deep operator networks / ETF rotation | 9511 | 7945 | No |
| 11270 | Conformal Scholarly Liquidity Shock Deflector Mod-3566 | Quantum machine learning / Variational circuits / Index prediction | 14089 | 14090 | No |
| 11424 | Conformal Scholarly Liquidity Shock Deflector Mod-3950 | Neural operators / Deep operator networks / ETF rotation | 9528 | 7975 | No |
