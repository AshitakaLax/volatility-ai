# Diffusion-model-based approach to liquidity-shock detection and response

**Concept page** · shared by **68** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,951) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Diffusion generative models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of diffusion models detecting liquidity shocks; the disputed VPIN result (RK247) is the best the literature offers. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Diffusion Scholarly
Liquidity Shock Deflector Sys-2") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The diffusion-model version
trains a denoising generative model and samples scenarios or forecasts
from it. I found no study of this method on this task.

## The CSV's description

Proposed diffusion-model-based approach to liquidity-shock detection and
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
* Generative models trained on a few thousand days memorise more than
  they generalise; no trading evidence found.

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
| 3951 | Diffusion Scholarly Liquidity Shock Deflector Sys-2 | Robust optimization / Distributionally robust CVaR / Index tracking | 4702 | 3256 | No |
| 4037 | Diffusion Scholarly Liquidity Shock Deflector Sys-482 | Robust optimization / Distributionally robust CVaR / Index tracking | 4733 | 3351 | No |
| 4123 | Diffusion Scholarly Liquidity Shock Deflector Sys-962 | Robust optimization / Distributionally robust CVaR / Index tracking | 4764 | 3446 | No |
| 4209 | Diffusion Scholarly Liquidity Shock Deflector Sys-1442 | Robust optimization / Distributionally robust CVaR / Index tracking | 4795 | 3541 | No |
| 4295 | Diffusion Scholarly Liquidity Shock Deflector Sys-1922 | Robust optimization / Distributionally robust CVaR / Index tracking | 4826 | 3636 | No |
| 4322 | Diffusion Scholarly Liquidity Shock Deflector Mod-62 | Robust optimization / Distributionally robust CVaR / Index tracking | 4835 | 3663 | No |
| 4407 | Diffusion Scholarly Liquidity Shock Deflector Mod-542 | Robust optimization / Distributionally robust CVaR / Index tracking | 4862 | 3758 | No |
| 4492 | Diffusion Scholarly Liquidity Shock Deflector Mod-1022 | Robust optimization / Distributionally robust CVaR / Index tracking | 4889 | 3853 | No |
| 4577 | Diffusion Scholarly Liquidity Shock Deflector Mod-1502 | Robust optimization / Distributionally robust CVaR / Index tracking | 4916 | 3948 | No |
| 4662 | Diffusion Scholarly Liquidity Shock Deflector Mod-1982 | Robust optimization / Distributionally robust CVaR / Index tracking | 4943 | 4043 | No |
| 4747 | Diffusion Scholarly Liquidity Shock Deflector Mod-2462 | Robust optimization / Distributionally robust CVaR / Index tracking | 4970 | 4138 | No |
| 4832 | Diffusion Scholarly Liquidity Shock Deflector Mod-2942 | Robust optimization / Distributionally robust CVaR / Index tracking | 4997 | 4233 | No |
| 4917 | Diffusion Scholarly Liquidity Shock Deflector Mod-3422 | Robust optimization / Distributionally robust CVaR / Index tracking | 5024 | 4328 | No |
| 5002 | Diffusion Scholarly Liquidity Shock Deflector Mod-3902 | Robust optimization / Distributionally robust CVaR / Index tracking | 5051 | 4423 | No |
| 6297 | Diffusion Scholarly Liquidity Shock Deflector Sys-194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5402 | 8481 | No |
| 6338 | Diffusion Scholarly Liquidity Shock Deflector Sys-674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5410 | 8516 | No |
| 6379 | Diffusion Scholarly Liquidity Shock Deflector Sys-1154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5418 | 8551 | No |
| 6420 | Diffusion Scholarly Liquidity Shock Deflector Sys-1634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5426 | 8586 | No |
| 6476 | Diffusion Scholarly Liquidity Shock Deflector Mod-254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5437 | 8631 | No |
| 6521 | Diffusion Scholarly Liquidity Shock Deflector Mod-734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5445 | 8668 | No |
| 6566 | Diffusion Scholarly Liquidity Shock Deflector Mod-1214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5453 | 8705 | No |
| 6611 | Diffusion Scholarly Liquidity Shock Deflector Mod-1694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5461 | 8742 | No |
| 6656 | Diffusion Scholarly Liquidity Shock Deflector Mod-2174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5469 | 8779 | No |
| 6701 | Diffusion Scholarly Liquidity Shock Deflector Mod-2654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5477 | 8816 | No |
| 6746 | Diffusion Scholarly Liquidity Shock Deflector Mod-3134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5485 | 8853 | No |
| 6791 | Diffusion Scholarly Liquidity Shock Deflector Mod-3614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5493 | 8890 | No |
| 8512 | Diffusion Scholarly Liquidity Shock Deflector Alpha-90 | Neural operators / Fourier layers / ETF rotation | 5807 | 2138 | No |
| 8552 | Diffusion Scholarly Liquidity Shock Deflector Alpha-190 | Neural operators / Fourier layers / ETF rotation | 7630 | 2939 | No |
| 8592 | Diffusion Scholarly Liquidity Shock Deflector Alpha-290 | Neural operators / Fourier layers / ETF rotation | 9282 | 7580 | No |
| 8632 | Diffusion Scholarly Liquidity Shock Deflector Alpha-390 | Neural operators / Fourier layers / ETF rotation | 5820 | 2146 | No |
| 8672 | Diffusion Scholarly Liquidity Shock Deflector Alpha-490 | Neural operators / Fourier layers / ETF rotation | 7633 | 3007 | No |
| 9113 | Diffusion Scholarly Liquidity Shock Deflector Sys-98 | Attention networks / Transformer encoders / Stock alpha generation | 12835 | 11927 | No |
| 9186 | Diffusion Scholarly Liquidity Shock Deflector Sys-290 | Neural operators / Deep operator networks / ETF rotation | 9331 | 7650 | No |
| 9225 | Diffusion Scholarly Liquidity Shock Deflector Sys-386 | Quantum machine learning / Variational circuits / Index prediction | 13999 | 14004 | No |
| 9300 | Diffusion Scholarly Liquidity Shock Deflector Sys-578 | Attention networks / Transformer encoders / Stock alpha generation | 12845 | 11950 | No |
| 9373 | Diffusion Scholarly Liquidity Shock Deflector Sys-770 | Neural operators / Deep operator networks / ETF rotation | 9347 | 7672 | No |
| 9412 | Diffusion Scholarly Liquidity Shock Deflector Sys-866 | Quantum machine learning / Variational circuits / Index prediction | 14008 | 14012 | No |
| 9487 | Diffusion Scholarly Liquidity Shock Deflector Sys-1058 | Attention networks / Transformer encoders / Stock alpha generation | 12855 | 11973 | No |
| 9560 | Diffusion Scholarly Liquidity Shock Deflector Sys-1250 | Neural operators / Deep operator networks / ETF rotation | 9363 | 7694 | No |
| 9599 | Diffusion Scholarly Liquidity Shock Deflector Sys-1346 | Quantum machine learning / Variational circuits / Index prediction | 14017 | 14020 | No |
| 9674 | Diffusion Scholarly Liquidity Shock Deflector Sys-1538 | Attention networks / Transformer encoders / Stock alpha generation | 12865 | 11996 | No |
| 9747 | Diffusion Scholarly Liquidity Shock Deflector Sys-1730 | Neural operators / Deep operator networks / ETF rotation | 9379 | 7716 | No |
| 9786 | Diffusion Scholarly Liquidity Shock Deflector Sys-1826 | Quantum machine learning / Variational circuits / Index prediction | 14026 | 14028 | No |
| 9912 | Diffusion Scholarly Liquidity Shock Deflector Mod-158 | Attention networks / Transformer encoders / Stock alpha generation | 12878 | 12025 | No |
| 9993 | Diffusion Scholarly Liquidity Shock Deflector Mod-350 | Neural operators / Deep operator networks / ETF rotation | 9400 | 7751 | No |
| 10030 | Diffusion Scholarly Liquidity Shock Deflector Mod-446 | Quantum machine learning / Variational circuits / Index prediction | 14037 | 14038 | No |
| 10103 | Diffusion Scholarly Liquidity Shock Deflector Mod-638 | Attention networks / Transformer encoders / Stock alpha generation | 12890 | 12048 | No |
| 10184 | Diffusion Scholarly Liquidity Shock Deflector Mod-830 | Neural operators / Deep operator networks / ETF rotation | 9417 | 7781 | No |
| 10221 | Diffusion Scholarly Liquidity Shock Deflector Mod-926 | Quantum machine learning / Variational circuits / Index prediction | 14045 | 14046 | No |
| 10294 | Diffusion Scholarly Liquidity Shock Deflector Mod-1118 | Attention networks / Transformer encoders / Stock alpha generation | 12902 | 12071 | No |
| 10375 | Diffusion Scholarly Liquidity Shock Deflector Mod-1310 | Neural operators / Deep operator networks / ETF rotation | 9434 | 7811 | No |
| 10412 | Diffusion Scholarly Liquidity Shock Deflector Mod-1406 | Quantum machine learning / Variational circuits / Index prediction | 14053 | 14054 | No |
| 10485 | Diffusion Scholarly Liquidity Shock Deflector Mod-1598 | Attention networks / Transformer encoders / Stock alpha generation | 12914 | 12094 | No |
| 10566 | Diffusion Scholarly Liquidity Shock Deflector Mod-1790 | Neural operators / Deep operator networks / ETF rotation | 9451 | 7841 | No |
| 10603 | Diffusion Scholarly Liquidity Shock Deflector Mod-1886 | Quantum machine learning / Variational circuits / Index prediction | 14061 | 14062 | No |
| 10676 | Diffusion Scholarly Liquidity Shock Deflector Mod-2078 | Attention networks / Transformer encoders / Stock alpha generation | 12926 | 12117 | No |
| 10757 | Diffusion Scholarly Liquidity Shock Deflector Mod-2270 | Neural operators / Deep operator networks / ETF rotation | 9468 | 7871 | No |
| 10794 | Diffusion Scholarly Liquidity Shock Deflector Mod-2366 | Quantum machine learning / Variational circuits / Index prediction | 14069 | 14070 | No |
| 10867 | Diffusion Scholarly Liquidity Shock Deflector Mod-2558 | Attention networks / Transformer encoders / Stock alpha generation | 12938 | 12140 | No |
| 10948 | Diffusion Scholarly Liquidity Shock Deflector Mod-2750 | Neural operators / Deep operator networks / ETF rotation | 9485 | 7901 | No |
| 10985 | Diffusion Scholarly Liquidity Shock Deflector Mod-2846 | Quantum machine learning / Variational circuits / Index prediction | 14077 | 14078 | No |
| 11058 | Diffusion Scholarly Liquidity Shock Deflector Mod-3038 | Attention networks / Transformer encoders / Stock alpha generation | 12950 | 12163 | No |
| 11139 | Diffusion Scholarly Liquidity Shock Deflector Mod-3230 | Neural operators / Deep operator networks / ETF rotation | 9502 | 7931 | No |
| 11176 | Diffusion Scholarly Liquidity Shock Deflector Mod-3326 | Quantum machine learning / Variational circuits / Index prediction | 14085 | 14086 | No |
| 11249 | Diffusion Scholarly Liquidity Shock Deflector Mod-3518 | Attention networks / Transformer encoders / Stock alpha generation | 12962 | 12186 | No |
| 11330 | Diffusion Scholarly Liquidity Shock Deflector Mod-3710 | Neural operators / Deep operator networks / ETF rotation | 9519 | 7961 | No |
| 11367 | Diffusion Scholarly Liquidity Shock Deflector Mod-3806 | Quantum machine learning / Variational circuits / Index prediction | 14093 | 14094 | No |
| 11440 | Diffusion Scholarly Liquidity Shock Deflector Mod-3998 | Attention networks / Transformer encoders / Stock alpha generation | 12974 | 12209 | No |
