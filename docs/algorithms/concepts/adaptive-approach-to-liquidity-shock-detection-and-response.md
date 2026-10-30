# Adaptive approach to liquidity-shock detection and response

**Concept page** · shared by **74** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,743) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** An adaptive rule could drive a buy gate, but no study shows it beating the simple spread and volume gates already built (RK244, RK247); background. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly
Liquidity Shock Deflector Ref-142") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The adaptive version lets
its parameters or thresholds move with recent data. I found no study of
this method on this task.

## The CSV's description

Proposed adaptive approach to liquidity-shock detection and response:
Estimate when spreads, depth, or order-flow intensity may deteriorate
and adapt trade size, timing, or order placement to reduce execution
risk. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

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
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

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
| 1743 | Adaptive Scholarly Liquidity Shock Deflector Ref-142 | Robust optimization / Distributionally robust CVaR / Index tracking | 8248 | 11300 | No |
| 1798 | Adaptive Scholarly Liquidity Shock Deflector Ref-622 | Robust optimization / Distributionally robust CVaR / Index tracking | 8289 | 11321 | No |
| 2486 | Adaptive Scholarly Liquidity Shock Deflector Eng-62 | Robust optimization / Distributionally robust CVaR / Index tracking | 5060 | 4457 | No |
| 2541 | Adaptive Scholarly Liquidity Shock Deflector Eng-542 | Robust optimization / Distributionally robust CVaR / Index tracking | 5085 | 4550 | No |
| 2596 | Adaptive Scholarly Liquidity Shock Deflector Eng-1022 | Robust optimization / Distributionally robust CVaR / Index tracking | 5110 | 4643 | No |
| 2651 | Adaptive Scholarly Liquidity Shock Deflector Eng-1502 | Robust optimization / Distributionally robust CVaR / Index tracking | 5135 | 4736 | No |
| 2706 | Adaptive Scholarly Liquidity Shock Deflector Eng-1982 | Robust optimization / Distributionally robust CVaR / Index tracking | 5160 | 4829 | No |
| 2761 | Adaptive Scholarly Liquidity Shock Deflector Eng-2462 | Robust optimization / Distributionally robust CVaR / Index tracking | 5185 | 4922 | No |
| 2816 | Adaptive Scholarly Liquidity Shock Deflector Eng-2942 | Robust optimization / Distributionally robust CVaR / Index tracking | 5210 | 5015 | No |
| 2871 | Adaptive Scholarly Liquidity Shock Deflector Eng-3422 | Robust optimization / Distributionally robust CVaR / Index tracking | 5235 | 5108 | No |
| 2926 | Adaptive Scholarly Liquidity Shock Deflector Eng-3902 | Robust optimization / Distributionally robust CVaR / Index tracking | 5260 | 5201 | No |
| 2981 | Adaptive Scholarly Liquidity Shock Deflector Eng-4382 | Robust optimization / Distributionally robust CVaR / Index tracking | 5285 | 5294 | No |
| 3036 | Adaptive Scholarly Liquidity Shock Deflector Eng-4862 | Robust optimization / Distributionally robust CVaR / Index tracking | 5310 | 5387 | No |
| 3091 | Adaptive Scholarly Liquidity Shock Deflector Eng-5342 | Robust optimization / Distributionally robust CVaR / Index tracking | 5335 | 5480 | No |
| 3146 | Adaptive Scholarly Liquidity Shock Deflector Eng-5822 | Robust optimization / Distributionally robust CVaR / Index tracking | 5360 | 5573 | No |
| 3187 | Adaptive Scholarly Liquidity Shock Deflector Ref-334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6520 | 3093 | No |
| 3203 | Adaptive Scholarly Liquidity Shock Deflector Ref-814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6563 | 3210 | No |
| 3459 | Adaptive Scholarly Liquidity Shock Deflector Eng-254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5504 | 8937 | No |
| 3475 | Adaptive Scholarly Liquidity Shock Deflector Eng-734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5512 | 8972 | No |
| 3491 | Adaptive Scholarly Liquidity Shock Deflector Eng-1214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5520 | 9007 | No |
| 3507 | Adaptive Scholarly Liquidity Shock Deflector Eng-1694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5528 | 9042 | No |
| 3523 | Adaptive Scholarly Liquidity Shock Deflector Eng-2174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5536 | 9077 | No |
| 3539 | Adaptive Scholarly Liquidity Shock Deflector Eng-2654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5544 | 9112 | No |
| 3555 | Adaptive Scholarly Liquidity Shock Deflector Eng-3134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5552 | 9147 | No |
| 3571 | Adaptive Scholarly Liquidity Shock Deflector Eng-3614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5560 | 9182 | No |
| 3587 | Adaptive Scholarly Liquidity Shock Deflector Eng-4094 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5568 | 9217 | No |
| 3603 | Adaptive Scholarly Liquidity Shock Deflector Eng-4574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5576 | 9252 | No |
| 3619 | Adaptive Scholarly Liquidity Shock Deflector Eng-5054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5584 | 9287 | No |
| 3635 | Adaptive Scholarly Liquidity Shock Deflector Eng-5534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5592 | 9322 | No |
| 7468 | Adaptive Scholarly Liquidity Shock Deflector Ref-238 | Attention networks / Transformer encoders / Stock alpha generation | 3217 | 3068 | No |
| 7502 | Adaptive Scholarly Liquidity Shock Deflector Ref-718 | Attention networks / Transformer encoders / Stock alpha generation | 3233 | 3185 | No |
| 7925 | Adaptive Scholarly Liquidity Shock Deflector Eng-158 | Attention networks / Transformer encoders / Stock alpha generation | 12978 | 12217 | No |
| 7959 | Adaptive Scholarly Liquidity Shock Deflector Eng-638 | Attention networks / Transformer encoders / Stock alpha generation | 12988 | 12240 | No |
| 7993 | Adaptive Scholarly Liquidity Shock Deflector Eng-1118 | Attention networks / Transformer encoders / Stock alpha generation | 12998 | 12263 | No |
| 8027 | Adaptive Scholarly Liquidity Shock Deflector Eng-1598 | Attention networks / Transformer encoders / Stock alpha generation | 13008 | 12286 | No |
| 8061 | Adaptive Scholarly Liquidity Shock Deflector Eng-2078 | Attention networks / Transformer encoders / Stock alpha generation | 13018 | 12309 | No |
| 8095 | Adaptive Scholarly Liquidity Shock Deflector Eng-2558 | Attention networks / Transformer encoders / Stock alpha generation | 13028 | 12332 | No |
| 8129 | Adaptive Scholarly Liquidity Shock Deflector Eng-3038 | Attention networks / Transformer encoders / Stock alpha generation | 13038 | 12355 | No |
| 8163 | Adaptive Scholarly Liquidity Shock Deflector Eng-3518 | Attention networks / Transformer encoders / Stock alpha generation | 13048 | 12378 | No |
| 8197 | Adaptive Scholarly Liquidity Shock Deflector Eng-3998 | Attention networks / Transformer encoders / Stock alpha generation | 13058 | 12401 | No |
| 8231 | Adaptive Scholarly Liquidity Shock Deflector Eng-4478 | Attention networks / Transformer encoders / Stock alpha generation | 13068 | 12424 | No |
| 8265 | Adaptive Scholarly Liquidity Shock Deflector Eng-4958 | Attention networks / Transformer encoders / Stock alpha generation | 13078 | 12447 | No |
| 8299 | Adaptive Scholarly Liquidity Shock Deflector Eng-5438 | Attention networks / Transformer encoders / Stock alpha generation | 13088 | 12470 | No |
| 8333 | Adaptive Scholarly Liquidity Shock Deflector Eng-5918 | Attention networks / Transformer encoders / Stock alpha generation | 13098 | 12493 | No |
| 8695 | Adaptive Scholarly Liquidity Shock Deflector Ref-46 | Quantum machine learning / Variational circuits / Index prediction | 11287 | 5963 | No |
| 8845 | Adaptive Scholarly Liquidity Shock Deflector Ref-430 | Neural operators / Deep operator networks / ETF rotation | 7641 | 3118 | No |
| 8886 | Adaptive Scholarly Liquidity Shock Deflector Ref-526 | Quantum machine learning / Variational circuits / Index prediction | 11312 | 5983 | No |
| 9036 | Adaptive Scholarly Liquidity Shock Deflector Ref-910 | Neural operators / Deep operator networks / ETF rotation | 7649 | 3235 | No |
| 11579 | Adaptive Scholarly Liquidity Shock Deflector Eng-350 | Neural operators / Deep operator networks / ETF rotation | 9542 | 8001 | No |
| 11619 | Adaptive Scholarly Liquidity Shock Deflector Eng-446 | Quantum machine learning / Variational circuits / Index prediction | 14104 | 14105 | No |
| 11770 | Adaptive Scholarly Liquidity Shock Deflector Eng-830 | Neural operators / Deep operator networks / ETF rotation | 9558 | 8033 | No |
| 11810 | Adaptive Scholarly Liquidity Shock Deflector Eng-926 | Quantum machine learning / Variational circuits / Index prediction | 14112 | 14113 | No |
| 11961 | Adaptive Scholarly Liquidity Shock Deflector Eng-1310 | Neural operators / Deep operator networks / ETF rotation | 9574 | 8065 | No |
| 12001 | Adaptive Scholarly Liquidity Shock Deflector Eng-1406 | Quantum machine learning / Variational circuits / Index prediction | 14120 | 14121 | No |
| 12152 | Adaptive Scholarly Liquidity Shock Deflector Eng-1790 | Neural operators / Deep operator networks / ETF rotation | 9590 | 8097 | No |
| 12192 | Adaptive Scholarly Liquidity Shock Deflector Eng-1886 | Quantum machine learning / Variational circuits / Index prediction | 14128 | 14129 | No |
| 12343 | Adaptive Scholarly Liquidity Shock Deflector Eng-2270 | Neural operators / Deep operator networks / ETF rotation | 9606 | 8129 | No |
| 12383 | Adaptive Scholarly Liquidity Shock Deflector Eng-2366 | Quantum machine learning / Variational circuits / Index prediction | 14136 | 14137 | No |
| 12534 | Adaptive Scholarly Liquidity Shock Deflector Eng-2750 | Neural operators / Deep operator networks / ETF rotation | 9622 | 8161 | No |
| 12574 | Adaptive Scholarly Liquidity Shock Deflector Eng-2846 | Quantum machine learning / Variational circuits / Index prediction | 14144 | 14145 | No |
| 12725 | Adaptive Scholarly Liquidity Shock Deflector Eng-3230 | Neural operators / Deep operator networks / ETF rotation | 9638 | 8193 | No |
| 12765 | Adaptive Scholarly Liquidity Shock Deflector Eng-3326 | Quantum machine learning / Variational circuits / Index prediction | 14152 | 14153 | No |
| 12916 | Adaptive Scholarly Liquidity Shock Deflector Eng-3710 | Neural operators / Deep operator networks / ETF rotation | 9654 | 8225 | No |
| 12956 | Adaptive Scholarly Liquidity Shock Deflector Eng-3806 | Quantum machine learning / Variational circuits / Index prediction | 14160 | 14161 | No |
| 13107 | Adaptive Scholarly Liquidity Shock Deflector Eng-4190 | Neural operators / Deep operator networks / ETF rotation | 9670 | 8257 | No |
| 13147 | Adaptive Scholarly Liquidity Shock Deflector Eng-4286 | Quantum machine learning / Variational circuits / Index prediction | 14168 | 14169 | No |
| 13298 | Adaptive Scholarly Liquidity Shock Deflector Eng-4670 | Neural operators / Deep operator networks / ETF rotation | 9686 | 8289 | No |
| 13338 | Adaptive Scholarly Liquidity Shock Deflector Eng-4766 | Quantum machine learning / Variational circuits / Index prediction | 14176 | 14177 | No |
| 13489 | Adaptive Scholarly Liquidity Shock Deflector Eng-5150 | Neural operators / Deep operator networks / ETF rotation | 9702 | 8321 | No |
| 13529 | Adaptive Scholarly Liquidity Shock Deflector Eng-5246 | Quantum machine learning / Variational circuits / Index prediction | 14184 | 14185 | No |
| 13680 | Adaptive Scholarly Liquidity Shock Deflector Eng-5630 | Neural operators / Deep operator networks / ETF rotation | 9718 | 8353 | No |
| 13720 | Adaptive Scholarly Liquidity Shock Deflector Eng-5726 | Quantum machine learning / Variational circuits / Index prediction | 14192 | 14193 | No |
| 13839 | Adaptive Scholarly Liquidity Shock Detector Ver-56 | Koopman operator / Model predictive control / ETF execution | 13169 | 13689 | No |
| 13843 | Adaptive Scholarly Liquidity Shock Detector Ver-156 | Koopman operator / Model predictive control / ETF execution | 3839 | 2886 | No |
