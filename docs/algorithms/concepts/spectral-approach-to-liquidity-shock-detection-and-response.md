# Spectral approach to liquidity-shock detection and response

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,874) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Spectral (frequency-domain) decomposition |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A spectral method could drive a buy gate, but no study shows it beating the simple spread and volume gates already built (RK244, RK247); background. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Spectral Scholarly
Liquidity Shock Deflector Sys-362") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The spectral version works
in the frequency domain, filtering or weighting components by cycle
length. I found no study of this method on this task.

## The CSV's description

Proposed spectral approach to liquidity-shock detection and response:
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
* Spectral estimates need long stationary windows; market cycles are
  neither.

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
| 1874 | Spectral Scholarly Liquidity Shock Deflector Sys-362 | Robust optimization / Distributionally robust CVaR / Index tracking | 4724 | 3328 | No |
| 1923 | Spectral Scholarly Liquidity Shock Deflector Sys-842 | Robust optimization / Distributionally robust CVaR / Index tracking | 4755 | 3423 | No |
| 1972 | Spectral Scholarly Liquidity Shock Deflector Sys-1322 | Robust optimization / Distributionally robust CVaR / Index tracking | 4786 | 3518 | No |
| 2021 | Spectral Scholarly Liquidity Shock Deflector Sys-1802 | Robust optimization / Distributionally robust CVaR / Index tracking | 4817 | 3613 | No |
| 2058 | Spectral Scholarly Liquidity Shock Deflector Mod-182 | Robust optimization / Distributionally robust CVaR / Index tracking | 4842 | 3686 | No |
| 2111 | Spectral Scholarly Liquidity Shock Deflector Mod-662 | Robust optimization / Distributionally robust CVaR / Index tracking | 4869 | 3781 | No |
| 2164 | Spectral Scholarly Liquidity Shock Deflector Mod-1142 | Robust optimization / Distributionally robust CVaR / Index tracking | 4896 | 3876 | No |
| 2217 | Spectral Scholarly Liquidity Shock Deflector Mod-1622 | Robust optimization / Distributionally robust CVaR / Index tracking | 4923 | 3971 | No |
| 2270 | Spectral Scholarly Liquidity Shock Deflector Mod-2102 | Robust optimization / Distributionally robust CVaR / Index tracking | 4950 | 4066 | No |
| 2323 | Spectral Scholarly Liquidity Shock Deflector Mod-2582 | Robust optimization / Distributionally robust CVaR / Index tracking | 4977 | 4161 | No |
| 2376 | Spectral Scholarly Liquidity Shock Deflector Mod-3062 | Robust optimization / Distributionally robust CVaR / Index tracking | 5004 | 4256 | No |
| 2429 | Spectral Scholarly Liquidity Shock Deflector Mod-3542 | Robust optimization / Distributionally robust CVaR / Index tracking | 5031 | 4351 | No |
| 3213 | Spectral Scholarly Liquidity Shock Deflector Sys-74 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5400 | 8472 | No |
| 3235 | Spectral Scholarly Liquidity Shock Deflector Sys-554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5408 | 8507 | No |
| 3257 | Spectral Scholarly Liquidity Shock Deflector Sys-1034 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5416 | 8542 | No |
| 3279 | Spectral Scholarly Liquidity Shock Deflector Sys-1514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5424 | 8577 | No |
| 3301 | Spectral Scholarly Liquidity Shock Deflector Sys-1994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5432 | 8612 | No |
| 3315 | Spectral Scholarly Liquidity Shock Deflector Mod-374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5439 | 8641 | No |
| 3333 | Spectral Scholarly Liquidity Shock Deflector Mod-854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5447 | 8678 | No |
| 3351 | Spectral Scholarly Liquidity Shock Deflector Mod-1334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5455 | 8715 | No |
| 3369 | Spectral Scholarly Liquidity Shock Deflector Mod-1814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5463 | 8752 | No |
| 3387 | Spectral Scholarly Liquidity Shock Deflector Mod-2294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5471 | 8789 | No |
| 3405 | Spectral Scholarly Liquidity Shock Deflector Mod-2774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5479 | 8826 | No |
| 3423 | Spectral Scholarly Liquidity Shock Deflector Mod-3254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5487 | 8863 | No |
| 3441 | Spectral Scholarly Liquidity Shock Deflector Mod-3734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5495 | 8900 | No |
| 7549 | Spectral Scholarly Liquidity Shock Deflector Sys-458 | Attention networks / Transformer encoders / Stock alpha generation | 12842 | 11944 | No |
| 7580 | Spectral Scholarly Liquidity Shock Deflector Sys-938 | Attention networks / Transformer encoders / Stock alpha generation | 12852 | 11967 | No |
| 7611 | Spectral Scholarly Liquidity Shock Deflector Sys-1418 | Attention networks / Transformer encoders / Stock alpha generation | 12862 | 11990 | No |
| 7642 | Spectral Scholarly Liquidity Shock Deflector Sys-1898 | Attention networks / Transformer encoders / Stock alpha generation | 12872 | 12013 | No |
| 7667 | Spectral Scholarly Liquidity Shock Deflector Mod-278 | Attention networks / Transformer encoders / Stock alpha generation | 12881 | 12031 | No |
| 7699 | Spectral Scholarly Liquidity Shock Deflector Mod-758 | Attention networks / Transformer encoders / Stock alpha generation | 12893 | 12054 | No |
| 7731 | Spectral Scholarly Liquidity Shock Deflector Mod-1238 | Attention networks / Transformer encoders / Stock alpha generation | 12905 | 12077 | No |
| 7763 | Spectral Scholarly Liquidity Shock Deflector Mod-1718 | Attention networks / Transformer encoders / Stock alpha generation | 12917 | 12100 | No |
| 7795 | Spectral Scholarly Liquidity Shock Deflector Mod-2198 | Attention networks / Transformer encoders / Stock alpha generation | 12929 | 12123 | No |
| 7827 | Spectral Scholarly Liquidity Shock Deflector Mod-2678 | Attention networks / Transformer encoders / Stock alpha generation | 12941 | 12146 | No |
| 7859 | Spectral Scholarly Liquidity Shock Deflector Mod-3158 | Attention networks / Transformer encoders / Stock alpha generation | 12953 | 12169 | No |
| 7891 | Spectral Scholarly Liquidity Shock Deflector Mod-3638 | Attention networks / Transformer encoders / Stock alpha generation | 12965 | 12192 | No |
| 9139 | Spectral Scholarly Liquidity Shock Deflector Sys-170 | Neural operators / Deep operator networks / ETF rotation | 9328 | 7645 | No |
| 9178 | Spectral Scholarly Liquidity Shock Deflector Sys-266 | Quantum machine learning / Variational circuits / Index prediction | 13997 | 14002 | No |
| 9326 | Spectral Scholarly Liquidity Shock Deflector Sys-650 | Neural operators / Deep operator networks / ETF rotation | 9344 | 7667 | No |
| 9365 | Spectral Scholarly Liquidity Shock Deflector Sys-746 | Quantum machine learning / Variational circuits / Index prediction | 14006 | 14010 | No |
| 9513 | Spectral Scholarly Liquidity Shock Deflector Sys-1130 | Neural operators / Deep operator networks / ETF rotation | 9360 | 7689 | No |
| 9552 | Spectral Scholarly Liquidity Shock Deflector Sys-1226 | Quantum machine learning / Variational circuits / Index prediction | 14015 | 14018 | No |
| 9700 | Spectral Scholarly Liquidity Shock Deflector Sys-1610 | Neural operators / Deep operator networks / ETF rotation | 9376 | 7711 | No |
| 9739 | Spectral Scholarly Liquidity Shock Deflector Sys-1706 | Quantum machine learning / Variational circuits / Index prediction | 14024 | 14026 | No |
| 9885 | Spectral Scholarly Liquidity Shock Deflector Mod-86 | Quantum machine learning / Variational circuits / Index prediction | 14031 | 14032 | No |
| 10039 | Spectral Scholarly Liquidity Shock Deflector Mod-470 | Neural operators / Deep operator networks / ETF rotation | 9405 | 7758 | No |
| 10076 | Spectral Scholarly Liquidity Shock Deflector Mod-566 | Quantum machine learning / Variational circuits / Index prediction | 14039 | 14040 | No |
| 10230 | Spectral Scholarly Liquidity Shock Deflector Mod-950 | Neural operators / Deep operator networks / ETF rotation | 9422 | 7788 | No |
| 10267 | Spectral Scholarly Liquidity Shock Deflector Mod-1046 | Quantum machine learning / Variational circuits / Index prediction | 14047 | 14048 | No |
| 10421 | Spectral Scholarly Liquidity Shock Deflector Mod-1430 | Neural operators / Deep operator networks / ETF rotation | 9439 | 7818 | No |
| 10458 | Spectral Scholarly Liquidity Shock Deflector Mod-1526 | Quantum machine learning / Variational circuits / Index prediction | 14055 | 14056 | No |
| 10612 | Spectral Scholarly Liquidity Shock Deflector Mod-1910 | Neural operators / Deep operator networks / ETF rotation | 9456 | 7848 | No |
| 10649 | Spectral Scholarly Liquidity Shock Deflector Mod-2006 | Quantum machine learning / Variational circuits / Index prediction | 14063 | 14064 | No |
| 10803 | Spectral Scholarly Liquidity Shock Deflector Mod-2390 | Neural operators / Deep operator networks / ETF rotation | 9473 | 7878 | No |
| 10840 | Spectral Scholarly Liquidity Shock Deflector Mod-2486 | Quantum machine learning / Variational circuits / Index prediction | 14071 | 14072 | No |
| 10994 | Spectral Scholarly Liquidity Shock Deflector Mod-2870 | Neural operators / Deep operator networks / ETF rotation | 9490 | 7908 | No |
| 11031 | Spectral Scholarly Liquidity Shock Deflector Mod-2966 | Quantum machine learning / Variational circuits / Index prediction | 14079 | 14080 | No |
| 11185 | Spectral Scholarly Liquidity Shock Deflector Mod-3350 | Neural operators / Deep operator networks / ETF rotation | 9507 | 7938 | No |
| 11222 | Spectral Scholarly Liquidity Shock Deflector Mod-3446 | Quantum machine learning / Variational circuits / Index prediction | 14087 | 14088 | No |
| 11376 | Spectral Scholarly Liquidity Shock Deflector Mod-3830 | Neural operators / Deep operator networks / ETF rotation | 9524 | 7968 | No |
| 11413 | Spectral Scholarly Liquidity Shock Deflector Mod-3926 | Quantum machine learning / Variational circuits / Index prediction | 14095 | 14096 | No |
