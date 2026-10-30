# Stochastic-process-based approach to liquidity-shock detection and response

**Concept page** · shared by **76** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,727) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Stochastic-process model (diffusion, jumps, mean reversion) |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A stochastic-process model could drive a buy gate, but no study shows it beating the simple spread and volume gates already built (RK244, RK247); background. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Stochastic Scholarly
Liquidity Shock Deflector Ref-22") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The stochastic-process
version models the quantity as a diffusion, jump or mean-reverting
process and acts on the fitted parameters. I found no study of this
method on this task.

## The CSV's description

Proposed stochastic-process-based approach to liquidity-shock detection
and response: Estimate when spreads, depth, or order-flow intensity may
deteriorate and adapt trade size, timing, or order placement to reduce
execution risk. This is a concept-level interpretation of the title, not
a complete trading specification: the exact model inputs/target,
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
* A fitted process is only as good as its specification, and its
  parameters drift between regimes.

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
| 1727 | Stochastic Scholarly Liquidity Shock Deflector Ref-22 | Robust optimization / Distributionally robust CVaR / Index tracking | 8238 | 11296 | No |
| 1782 | Stochastic Scholarly Liquidity Shock Deflector Ref-502 | Robust optimization / Distributionally robust CVaR / Index tracking | 8279 | 11317 | No |
| 1837 | Stochastic Scholarly Liquidity Shock Deflector Ref-982 | Robust optimization / Distributionally robust CVaR / Index tracking | 8320 | 11338 | No |
| 2527 | Stochastic Scholarly Liquidity Shock Deflector Eng-422 | Robust optimization / Distributionally robust CVaR / Index tracking | 5079 | 4528 | No |
| 2582 | Stochastic Scholarly Liquidity Shock Deflector Eng-902 | Robust optimization / Distributionally robust CVaR / Index tracking | 5104 | 4621 | No |
| 2637 | Stochastic Scholarly Liquidity Shock Deflector Eng-1382 | Robust optimization / Distributionally robust CVaR / Index tracking | 5129 | 4714 | No |
| 2692 | Stochastic Scholarly Liquidity Shock Deflector Eng-1862 | Robust optimization / Distributionally robust CVaR / Index tracking | 5154 | 4807 | No |
| 2747 | Stochastic Scholarly Liquidity Shock Deflector Eng-2342 | Robust optimization / Distributionally robust CVaR / Index tracking | 5179 | 4900 | No |
| 2802 | Stochastic Scholarly Liquidity Shock Deflector Eng-2822 | Robust optimization / Distributionally robust CVaR / Index tracking | 5204 | 4993 | No |
| 2857 | Stochastic Scholarly Liquidity Shock Deflector Eng-3302 | Robust optimization / Distributionally robust CVaR / Index tracking | 5229 | 5086 | No |
| 2912 | Stochastic Scholarly Liquidity Shock Deflector Eng-3782 | Robust optimization / Distributionally robust CVaR / Index tracking | 5254 | 5179 | No |
| 2967 | Stochastic Scholarly Liquidity Shock Deflector Eng-4262 | Robust optimization / Distributionally robust CVaR / Index tracking | 5279 | 5272 | No |
| 3022 | Stochastic Scholarly Liquidity Shock Deflector Eng-4742 | Robust optimization / Distributionally robust CVaR / Index tracking | 5304 | 5365 | No |
| 3077 | Stochastic Scholarly Liquidity Shock Deflector Eng-5222 | Robust optimization / Distributionally robust CVaR / Index tracking | 5329 | 5458 | No |
| 3132 | Stochastic Scholarly Liquidity Shock Deflector Eng-5702 | Robust optimization / Distributionally robust CVaR / Index tracking | 5354 | 5551 | No |
| 3182 | Stochastic Scholarly Liquidity Shock Deflector Ref-214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6508 | 3064 | No |
| 3198 | Stochastic Scholarly Liquidity Shock Deflector Ref-694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6551 | 3181 | No |
| 3456 | Stochastic Scholarly Liquidity Shock Deflector Eng-134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5502 | 8930 | No |
| 3472 | Stochastic Scholarly Liquidity Shock Deflector Eng-614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5510 | 8965 | No |
| 3488 | Stochastic Scholarly Liquidity Shock Deflector Eng-1094 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5518 | 9000 | No |
| 3504 | Stochastic Scholarly Liquidity Shock Deflector Eng-1574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5526 | 9035 | No |
| 3520 | Stochastic Scholarly Liquidity Shock Deflector Eng-2054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5534 | 9070 | No |
| 3536 | Stochastic Scholarly Liquidity Shock Deflector Eng-2534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5542 | 9105 | No |
| 3552 | Stochastic Scholarly Liquidity Shock Deflector Eng-3014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5550 | 9140 | No |
| 3568 | Stochastic Scholarly Liquidity Shock Deflector Eng-3494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5558 | 9175 | No |
| 3584 | Stochastic Scholarly Liquidity Shock Deflector Eng-3974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5566 | 9210 | No |
| 3600 | Stochastic Scholarly Liquidity Shock Deflector Eng-4454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5574 | 9245 | No |
| 3616 | Stochastic Scholarly Liquidity Shock Deflector Eng-4934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5582 | 9280 | No |
| 3632 | Stochastic Scholarly Liquidity Shock Deflector Eng-5414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5590 | 9315 | No |
| 3648 | Stochastic Scholarly Liquidity Shock Deflector Eng-5894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5598 | 9350 | No |
| 7459 | Stochastic Scholarly Liquidity Shock Deflector Ref-118 | Attention networks / Transformer encoders / Stock alpha generation | 3213 | 3039 | No |
| 7493 | Stochastic Scholarly Liquidity Shock Deflector Ref-598 | Attention networks / Transformer encoders / Stock alpha generation | 3229 | 3156 | No |
| 7918 | Stochastic Scholarly Liquidity Shock Deflector Eng-38 | Attention networks / Transformer encoders / Stock alpha generation | 12976 | 12212 | No |
| 7952 | Stochastic Scholarly Liquidity Shock Deflector Eng-518 | Attention networks / Transformer encoders / Stock alpha generation | 12986 | 12235 | No |
| 7986 | Stochastic Scholarly Liquidity Shock Deflector Eng-998 | Attention networks / Transformer encoders / Stock alpha generation | 12996 | 12258 | No |
| 8020 | Stochastic Scholarly Liquidity Shock Deflector Eng-1478 | Attention networks / Transformer encoders / Stock alpha generation | 13006 | 12281 | No |
| 8054 | Stochastic Scholarly Liquidity Shock Deflector Eng-1958 | Attention networks / Transformer encoders / Stock alpha generation | 13016 | 12304 | No |
| 8088 | Stochastic Scholarly Liquidity Shock Deflector Eng-2438 | Attention networks / Transformer encoders / Stock alpha generation | 13026 | 12327 | No |
| 8122 | Stochastic Scholarly Liquidity Shock Deflector Eng-2918 | Attention networks / Transformer encoders / Stock alpha generation | 13036 | 12350 | No |
| 8156 | Stochastic Scholarly Liquidity Shock Deflector Eng-3398 | Attention networks / Transformer encoders / Stock alpha generation | 13046 | 12373 | No |
| 8190 | Stochastic Scholarly Liquidity Shock Deflector Eng-3878 | Attention networks / Transformer encoders / Stock alpha generation | 13056 | 12396 | No |
| 8224 | Stochastic Scholarly Liquidity Shock Deflector Eng-4358 | Attention networks / Transformer encoders / Stock alpha generation | 13066 | 12419 | No |
| 8258 | Stochastic Scholarly Liquidity Shock Deflector Eng-4838 | Attention networks / Transformer encoders / Stock alpha generation | 13076 | 12442 | No |
| 8292 | Stochastic Scholarly Liquidity Shock Deflector Eng-5318 | Attention networks / Transformer encoders / Stock alpha generation | 13086 | 12465 | No |
| 8326 | Stochastic Scholarly Liquidity Shock Deflector Eng-5798 | Attention networks / Transformer encoders / Stock alpha generation | 13096 | 12488 | No |
| 8391 | Stochastic Scholarly Liquidity Shock Detector MK-12 | Persistence landscapes / Topological data analysis / Equity index | 2040 | 2833 | No |
| 8409 | Stochastic Scholarly Liquidity Shock Detector MK-72 | Persistence landscapes / Topological data analysis / Equity index | 2048 | 2845 | No |
| 8797 | Stochastic Scholarly Liquidity Shock Deflector Ref-310 | Neural operators / Deep operator networks / ETF rotation | 7639 | 3087 | No |
| 8836 | Stochastic Scholarly Liquidity Shock Deflector Ref-406 | Quantum machine learning / Variational circuits / Index prediction | 11305 | 5978 | No |
| 8988 | Stochastic Scholarly Liquidity Shock Deflector Ref-790 | Neural operators / Deep operator networks / ETF rotation | 7647 | 3204 | No |
| 9027 | Stochastic Scholarly Liquidity Shock Deflector Ref-886 | Quantum machine learning / Variational circuits / Index prediction | 11330 | 5998 | No |
| 11534 | Stochastic Scholarly Liquidity Shock Deflector Eng-230 | Neural operators / Deep operator networks / ETF rotation | 9538 | 7993 | No |
| 11569 | Stochastic Scholarly Liquidity Shock Deflector Eng-326 | Quantum machine learning / Variational circuits / Index prediction | 14102 | 14103 | No |
| 11725 | Stochastic Scholarly Liquidity Shock Deflector Eng-710 | Neural operators / Deep operator networks / ETF rotation | 9554 | 8025 | No |
| 11760 | Stochastic Scholarly Liquidity Shock Deflector Eng-806 | Quantum machine learning / Variational circuits / Index prediction | 14110 | 14111 | No |
| 11916 | Stochastic Scholarly Liquidity Shock Deflector Eng-1190 | Neural operators / Deep operator networks / ETF rotation | 9570 | 8057 | No |
| 11951 | Stochastic Scholarly Liquidity Shock Deflector Eng-1286 | Quantum machine learning / Variational circuits / Index prediction | 14118 | 14119 | No |
| 12107 | Stochastic Scholarly Liquidity Shock Deflector Eng-1670 | Neural operators / Deep operator networks / ETF rotation | 9586 | 8089 | No |
| 12142 | Stochastic Scholarly Liquidity Shock Deflector Eng-1766 | Quantum machine learning / Variational circuits / Index prediction | 14126 | 14127 | No |
| 12298 | Stochastic Scholarly Liquidity Shock Deflector Eng-2150 | Neural operators / Deep operator networks / ETF rotation | 9602 | 8121 | No |
| 12333 | Stochastic Scholarly Liquidity Shock Deflector Eng-2246 | Quantum machine learning / Variational circuits / Index prediction | 14134 | 14135 | No |
| 12489 | Stochastic Scholarly Liquidity Shock Deflector Eng-2630 | Neural operators / Deep operator networks / ETF rotation | 9618 | 8153 | No |
| 12524 | Stochastic Scholarly Liquidity Shock Deflector Eng-2726 | Quantum machine learning / Variational circuits / Index prediction | 14142 | 14143 | No |
| 12680 | Stochastic Scholarly Liquidity Shock Deflector Eng-3110 | Neural operators / Deep operator networks / ETF rotation | 9634 | 8185 | No |
| 12715 | Stochastic Scholarly Liquidity Shock Deflector Eng-3206 | Quantum machine learning / Variational circuits / Index prediction | 14150 | 14151 | No |
| 12871 | Stochastic Scholarly Liquidity Shock Deflector Eng-3590 | Neural operators / Deep operator networks / ETF rotation | 9650 | 8217 | No |
| 12906 | Stochastic Scholarly Liquidity Shock Deflector Eng-3686 | Quantum machine learning / Variational circuits / Index prediction | 14158 | 14159 | No |
| 13062 | Stochastic Scholarly Liquidity Shock Deflector Eng-4070 | Neural operators / Deep operator networks / ETF rotation | 9666 | 8249 | No |
| 13097 | Stochastic Scholarly Liquidity Shock Deflector Eng-4166 | Quantum machine learning / Variational circuits / Index prediction | 14166 | 14167 | No |
| 13253 | Stochastic Scholarly Liquidity Shock Deflector Eng-4550 | Neural operators / Deep operator networks / ETF rotation | 9682 | 8281 | No |
| 13288 | Stochastic Scholarly Liquidity Shock Deflector Eng-4646 | Quantum machine learning / Variational circuits / Index prediction | 14174 | 14175 | No |
| 13444 | Stochastic Scholarly Liquidity Shock Deflector Eng-5030 | Neural operators / Deep operator networks / ETF rotation | 9698 | 8313 | No |
| 13479 | Stochastic Scholarly Liquidity Shock Deflector Eng-5126 | Quantum machine learning / Variational circuits / Index prediction | 14182 | 14183 | No |
| 13635 | Stochastic Scholarly Liquidity Shock Deflector Eng-5510 | Neural operators / Deep operator networks / ETF rotation | 9714 | 8345 | No |
| 13670 | Stochastic Scholarly Liquidity Shock Deflector Eng-5606 | Quantum machine learning / Variational circuits / Index prediction | 14190 | 14191 | No |
| 13826 | Stochastic Scholarly Liquidity Shock Deflector Eng-5990 | Neural operators / Deep operator networks / ETF rotation | 9730 | 8377 | No |
