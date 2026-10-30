# Fractional-order approach to liquidity-shock detection and response

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,840) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Fractional-order models (long memory, fractional calculus) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of fractional-order models detecting liquidity shocks; the disputed VPIN result (RK247) is the best the literature offers. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Fractional Scholarly
Liquidity Shock Deflector Ref-382") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The fractional-order
version models long memory with fractional differencing or
fractional-order dynamics. I found no study of this method on this task.

## The CSV's description

Proposed fractional-order approach to liquidity-shock detection and
response: Estimate when spreads, depth, or order-flow intensity may
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
* Long memory in returns is weak once short-range dependence is allowed
  for (Lo 1991); in volatility, the simpler HAR model reproduces it
  (Corsi 2009).

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
| 3840 | Fractional Scholarly Liquidity Shock Deflector Ref-382 | Robust optimization / Distributionally robust CVaR / Index tracking | 8267 | 11311 | No |
| 3926 | Fractional Scholarly Liquidity Shock Deflector Ref-862 | Robust optimization / Distributionally robust CVaR / Index tracking | 8308 | 11332 | No |
| 5076 | Fractional Scholarly Liquidity Shock Deflector Eng-302 | Robust optimization / Distributionally robust CVaR / Index tracking | 5073 | 4504 | No |
| 5162 | Fractional Scholarly Liquidity Shock Deflector Eng-782 | Robust optimization / Distributionally robust CVaR / Index tracking | 5098 | 4597 | No |
| 5248 | Fractional Scholarly Liquidity Shock Deflector Eng-1262 | Robust optimization / Distributionally robust CVaR / Index tracking | 5123 | 4690 | No |
| 5334 | Fractional Scholarly Liquidity Shock Deflector Eng-1742 | Robust optimization / Distributionally robust CVaR / Index tracking | 5148 | 4783 | No |
| 5420 | Fractional Scholarly Liquidity Shock Deflector Eng-2222 | Robust optimization / Distributionally robust CVaR / Index tracking | 5173 | 4876 | No |
| 5506 | Fractional Scholarly Liquidity Shock Deflector Eng-2702 | Robust optimization / Distributionally robust CVaR / Index tracking | 5198 | 4969 | No |
| 5592 | Fractional Scholarly Liquidity Shock Deflector Eng-3182 | Robust optimization / Distributionally robust CVaR / Index tracking | 5223 | 5062 | No |
| 5678 | Fractional Scholarly Liquidity Shock Deflector Eng-3662 | Robust optimization / Distributionally robust CVaR / Index tracking | 5248 | 5155 | No |
| 5764 | Fractional Scholarly Liquidity Shock Deflector Eng-4142 | Robust optimization / Distributionally robust CVaR / Index tracking | 5273 | 5248 | No |
| 5850 | Fractional Scholarly Liquidity Shock Deflector Eng-4622 | Robust optimization / Distributionally robust CVaR / Index tracking | 5298 | 5341 | No |
| 5936 | Fractional Scholarly Liquidity Shock Deflector Eng-5102 | Robust optimization / Distributionally robust CVaR / Index tracking | 5323 | 5434 | No |
| 6022 | Fractional Scholarly Liquidity Shock Deflector Eng-5582 | Robust optimization / Distributionally robust CVaR / Index tracking | 5348 | 5527 | No |
| 6197 | Fractional Scholarly Liquidity Shock Deflector Ref-94 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6498 | 3035 | No |
| 6243 | Fractional Scholarly Liquidity Shock Deflector Ref-574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6541 | 3152 | No |
| 6829 | Fractional Scholarly Liquidity Shock Deflector Eng-14 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5500 | 8922 | No |
| 6875 | Fractional Scholarly Liquidity Shock Deflector Eng-494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5508 | 8957 | No |
| 6921 | Fractional Scholarly Liquidity Shock Deflector Eng-974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5516 | 8992 | No |
| 6967 | Fractional Scholarly Liquidity Shock Deflector Eng-1454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5524 | 9027 | No |
| 7013 | Fractional Scholarly Liquidity Shock Deflector Eng-1934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5532 | 9062 | No |
| 7059 | Fractional Scholarly Liquidity Shock Deflector Eng-2414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5540 | 9097 | No |
| 7105 | Fractional Scholarly Liquidity Shock Deflector Eng-2894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5548 | 9132 | No |
| 7151 | Fractional Scholarly Liquidity Shock Deflector Eng-3374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5556 | 9167 | No |
| 7197 | Fractional Scholarly Liquidity Shock Deflector Eng-3854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5564 | 9202 | No |
| 7243 | Fractional Scholarly Liquidity Shock Deflector Eng-4334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5572 | 9237 | No |
| 7289 | Fractional Scholarly Liquidity Shock Deflector Eng-4814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5580 | 9272 | No |
| 7335 | Fractional Scholarly Liquidity Shock Deflector Eng-5294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5588 | 9307 | No |
| 7381 | Fractional Scholarly Liquidity Shock Deflector Eng-5774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5596 | 9342 | No |
| 8751 | Fractional Scholarly Liquidity Shock Deflector Ref-190 | Neural operators / Deep operator networks / ETF rotation | 7637 | 3058 | No |
| 8789 | Fractional Scholarly Liquidity Shock Deflector Ref-286 | Quantum machine learning / Variational circuits / Index prediction | 11299 | 5973 | No |
| 8865 | Fractional Scholarly Liquidity Shock Deflector Ref-478 | Attention networks / Transformer encoders / Stock alpha generation | 3225 | 3127 | No |
| 8942 | Fractional Scholarly Liquidity Shock Deflector Ref-670 | Neural operators / Deep operator networks / ETF rotation | 7645 | 3175 | No |
| 8980 | Fractional Scholarly Liquidity Shock Deflector Ref-766 | Quantum machine learning / Variational circuits / Index prediction | 11324 | 5993 | No |
| 9056 | Fractional Scholarly Liquidity Shock Deflector Ref-958 | Attention networks / Transformer encoders / Stock alpha generation | 3241 | 3244 | No |
| 11487 | Fractional Scholarly Liquidity Shock Deflector Eng-110 | Neural operators / Deep operator networks / ETF rotation | 9534 | 7985 | No |
| 11524 | Fractional Scholarly Liquidity Shock Deflector Eng-206 | Quantum machine learning / Variational circuits / Index prediction | 14100 | 14101 | No |
| 11601 | Fractional Scholarly Liquidity Shock Deflector Eng-398 | Attention networks / Transformer encoders / Stock alpha generation | 12983 | 12229 | No |
| 11678 | Fractional Scholarly Liquidity Shock Deflector Eng-590 | Neural operators / Deep operator networks / ETF rotation | 9550 | 8017 | No |
| 11715 | Fractional Scholarly Liquidity Shock Deflector Eng-686 | Quantum machine learning / Variational circuits / Index prediction | 14108 | 14109 | No |
| 11792 | Fractional Scholarly Liquidity Shock Deflector Eng-878 | Attention networks / Transformer encoders / Stock alpha generation | 12993 | 12252 | No |
| 11869 | Fractional Scholarly Liquidity Shock Deflector Eng-1070 | Neural operators / Deep operator networks / ETF rotation | 9566 | 8049 | No |
| 11906 | Fractional Scholarly Liquidity Shock Deflector Eng-1166 | Quantum machine learning / Variational circuits / Index prediction | 14116 | 14117 | No |
| 11983 | Fractional Scholarly Liquidity Shock Deflector Eng-1358 | Attention networks / Transformer encoders / Stock alpha generation | 13003 | 12275 | No |
| 12060 | Fractional Scholarly Liquidity Shock Deflector Eng-1550 | Neural operators / Deep operator networks / ETF rotation | 9582 | 8081 | No |
| 12097 | Fractional Scholarly Liquidity Shock Deflector Eng-1646 | Quantum machine learning / Variational circuits / Index prediction | 14124 | 14125 | No |
| 12174 | Fractional Scholarly Liquidity Shock Deflector Eng-1838 | Attention networks / Transformer encoders / Stock alpha generation | 13013 | 12298 | No |
| 12251 | Fractional Scholarly Liquidity Shock Deflector Eng-2030 | Neural operators / Deep operator networks / ETF rotation | 9598 | 8113 | No |
| 12288 | Fractional Scholarly Liquidity Shock Deflector Eng-2126 | Quantum machine learning / Variational circuits / Index prediction | 14132 | 14133 | No |
| 12365 | Fractional Scholarly Liquidity Shock Deflector Eng-2318 | Attention networks / Transformer encoders / Stock alpha generation | 13023 | 12321 | No |
| 12442 | Fractional Scholarly Liquidity Shock Deflector Eng-2510 | Neural operators / Deep operator networks / ETF rotation | 9614 | 8145 | No |
| 12479 | Fractional Scholarly Liquidity Shock Deflector Eng-2606 | Quantum machine learning / Variational circuits / Index prediction | 14140 | 14141 | No |
| 12556 | Fractional Scholarly Liquidity Shock Deflector Eng-2798 | Attention networks / Transformer encoders / Stock alpha generation | 13033 | 12344 | No |
| 12633 | Fractional Scholarly Liquidity Shock Deflector Eng-2990 | Neural operators / Deep operator networks / ETF rotation | 9630 | 8177 | No |
| 12670 | Fractional Scholarly Liquidity Shock Deflector Eng-3086 | Quantum machine learning / Variational circuits / Index prediction | 14148 | 14149 | No |
| 12747 | Fractional Scholarly Liquidity Shock Deflector Eng-3278 | Attention networks / Transformer encoders / Stock alpha generation | 13043 | 12367 | No |
| 12824 | Fractional Scholarly Liquidity Shock Deflector Eng-3470 | Neural operators / Deep operator networks / ETF rotation | 9646 | 8209 | No |
| 12861 | Fractional Scholarly Liquidity Shock Deflector Eng-3566 | Quantum machine learning / Variational circuits / Index prediction | 14156 | 14157 | No |
| 12938 | Fractional Scholarly Liquidity Shock Deflector Eng-3758 | Attention networks / Transformer encoders / Stock alpha generation | 13053 | 12390 | No |
| 13015 | Fractional Scholarly Liquidity Shock Deflector Eng-3950 | Neural operators / Deep operator networks / ETF rotation | 9662 | 8241 | No |
| 13052 | Fractional Scholarly Liquidity Shock Deflector Eng-4046 | Quantum machine learning / Variational circuits / Index prediction | 14164 | 14165 | No |
| 13129 | Fractional Scholarly Liquidity Shock Deflector Eng-4238 | Attention networks / Transformer encoders / Stock alpha generation | 13063 | 12413 | No |
| 13206 | Fractional Scholarly Liquidity Shock Deflector Eng-4430 | Neural operators / Deep operator networks / ETF rotation | 9678 | 8273 | No |
| 13243 | Fractional Scholarly Liquidity Shock Deflector Eng-4526 | Quantum machine learning / Variational circuits / Index prediction | 14172 | 14173 | No |
| 13320 | Fractional Scholarly Liquidity Shock Deflector Eng-4718 | Attention networks / Transformer encoders / Stock alpha generation | 13073 | 12436 | No |
| 13397 | Fractional Scholarly Liquidity Shock Deflector Eng-4910 | Neural operators / Deep operator networks / ETF rotation | 9694 | 8305 | No |
| 13434 | Fractional Scholarly Liquidity Shock Deflector Eng-5006 | Quantum machine learning / Variational circuits / Index prediction | 14180 | 14181 | No |
| 13511 | Fractional Scholarly Liquidity Shock Deflector Eng-5198 | Attention networks / Transformer encoders / Stock alpha generation | 13083 | 12459 | No |
| 13588 | Fractional Scholarly Liquidity Shock Deflector Eng-5390 | Neural operators / Deep operator networks / ETF rotation | 9710 | 8337 | No |
| 13625 | Fractional Scholarly Liquidity Shock Deflector Eng-5486 | Quantum machine learning / Variational circuits / Index prediction | 14188 | 14189 | No |
| 13702 | Fractional Scholarly Liquidity Shock Deflector Eng-5678 | Attention networks / Transformer encoders / Stock alpha generation | 13093 | 12482 | No |
| 13779 | Fractional Scholarly Liquidity Shock Deflector Eng-5870 | Neural operators / Deep operator networks / ETF rotation | 9726 | 8369 | No |
| 13816 | Fractional Scholarly Liquidity Shock Deflector Eng-5966 | Quantum machine learning / Variational circuits / Index prediction | 14196 | 14197 | No |
