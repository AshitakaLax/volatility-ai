# Topology-aware approach to liquidity-shock detection and response

**Concept page** · shared by **65** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,972) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Topological data analysis (persistent homology) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of topological data analysis detecting liquidity shocks; the disputed VPIN result (RK247) is the best the literature offers. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Topological Scholarly
Liquidity Shock Deflector Sys-122") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The topology-aware version
derives persistent-homology features (Betti numbers, persistence
landscapes) from sliding windows of returns. I found no study of this
method on this task.

## The CSV's description

Proposed topology-aware approach to liquidity-shock detection and
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
* The best-known topological crash study is in sample (Gidea & Katz
  2018), and the features depend on window and scale choices.

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
| 3972 | Topological Scholarly Liquidity Shock Deflector Sys-122 | Robust optimization / Distributionally robust CVaR / Index tracking | 4708 | 3280 | No |
| 4058 | Topological Scholarly Liquidity Shock Deflector Sys-602 | Robust optimization / Distributionally robust CVaR / Index tracking | 4739 | 3375 | No |
| 4144 | Topological Scholarly Liquidity Shock Deflector Sys-1082 | Robust optimization / Distributionally robust CVaR / Index tracking | 4770 | 3470 | No |
| 4230 | Topological Scholarly Liquidity Shock Deflector Sys-1562 | Robust optimization / Distributionally robust CVaR / Index tracking | 4801 | 3565 | No |
| 4386 | Topological Scholarly Liquidity Shock Deflector Mod-422 | Robust optimization / Distributionally robust CVaR / Index tracking | 4856 | 3737 | No |
| 4471 | Topological Scholarly Liquidity Shock Deflector Mod-902 | Robust optimization / Distributionally robust CVaR / Index tracking | 4883 | 3832 | No |
| 4556 | Topological Scholarly Liquidity Shock Deflector Mod-1382 | Robust optimization / Distributionally robust CVaR / Index tracking | 4910 | 3927 | No |
| 4641 | Topological Scholarly Liquidity Shock Deflector Mod-1862 | Robust optimization / Distributionally robust CVaR / Index tracking | 4937 | 4022 | No |
| 4726 | Topological Scholarly Liquidity Shock Deflector Mod-2342 | Robust optimization / Distributionally robust CVaR / Index tracking | 4964 | 4117 | No |
| 4811 | Topological Scholarly Liquidity Shock Deflector Mod-2822 | Robust optimization / Distributionally robust CVaR / Index tracking | 4991 | 4212 | No |
| 4896 | Topological Scholarly Liquidity Shock Deflector Mod-3302 | Robust optimization / Distributionally robust CVaR / Index tracking | 5018 | 4307 | No |
| 4981 | Topological Scholarly Liquidity Shock Deflector Mod-3782 | Robust optimization / Distributionally robust CVaR / Index tracking | 5045 | 4402 | No |
| 6307 | Topological Scholarly Liquidity Shock Deflector Sys-314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5404 | 8489 | No |
| 6348 | Topological Scholarly Liquidity Shock Deflector Sys-794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5412 | 8524 | No |
| 6389 | Topological Scholarly Liquidity Shock Deflector Sys-1274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5420 | 8559 | No |
| 6430 | Topological Scholarly Liquidity Shock Deflector Sys-1754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5428 | 8594 | No |
| 6465 | Topological Scholarly Liquidity Shock Deflector Mod-134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5435 | 8623 | No |
| 6510 | Topological Scholarly Liquidity Shock Deflector Mod-614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5443 | 8660 | No |
| 6555 | Topological Scholarly Liquidity Shock Deflector Mod-1094 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5451 | 8697 | No |
| 6600 | Topological Scholarly Liquidity Shock Deflector Mod-1574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5459 | 8734 | No |
| 6645 | Topological Scholarly Liquidity Shock Deflector Mod-2054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5467 | 8771 | No |
| 6690 | Topological Scholarly Liquidity Shock Deflector Mod-2534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5475 | 8808 | No |
| 6735 | Topological Scholarly Liquidity Shock Deflector Mod-3014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5483 | 8845 | No |
| 6780 | Topological Scholarly Liquidity Shock Deflector Mod-3494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5491 | 8882 | No |
| 6825 | Topological Scholarly Liquidity Shock Deflector Mod-3974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5499 | 8919 | No |
| 9083 | Topological Scholarly Liquidity Shock Deflector Sys-26 | Quantum machine learning / Variational circuits / Index prediction | 13993 | 13998 | No |
| 9160 | Topological Scholarly Liquidity Shock Deflector Sys-218 | Attention networks / Transformer encoders / Stock alpha generation | 12837 | 11932 | No |
| 9234 | Topological Scholarly Liquidity Shock Deflector Sys-410 | Neural operators / Deep operator networks / ETF rotation | 9336 | 7655 | No |
| 9270 | Topological Scholarly Liquidity Shock Deflector Sys-506 | Quantum machine learning / Variational circuits / Index prediction | 14002 | 14006 | No |
| 9347 | Topological Scholarly Liquidity Shock Deflector Sys-698 | Attention networks / Transformer encoders / Stock alpha generation | 12847 | 11955 | No |
| 9421 | Topological Scholarly Liquidity Shock Deflector Sys-890 | Neural operators / Deep operator networks / ETF rotation | 9352 | 7677 | No |
| 9457 | Topological Scholarly Liquidity Shock Deflector Sys-986 | Quantum machine learning / Variational circuits / Index prediction | 14011 | 14014 | No |
| 9534 | Topological Scholarly Liquidity Shock Deflector Sys-1178 | Attention networks / Transformer encoders / Stock alpha generation | 12857 | 11978 | No |
| 9608 | Topological Scholarly Liquidity Shock Deflector Sys-1370 | Neural operators / Deep operator networks / ETF rotation | 9368 | 7699 | No |
| 9644 | Topological Scholarly Liquidity Shock Deflector Sys-1466 | Quantum machine learning / Variational circuits / Index prediction | 14020 | 14022 | No |
| 9721 | Topological Scholarly Liquidity Shock Deflector Sys-1658 | Attention networks / Transformer encoders / Stock alpha generation | 12867 | 12001 | No |
| 9795 | Topological Scholarly Liquidity Shock Deflector Sys-1850 | Neural operators / Deep operator networks / ETF rotation | 9384 | 7721 | No |
| 9831 | Topological Scholarly Liquidity Shock Deflector Sys-1946 | Quantum machine learning / Variational circuits / Index prediction | 14029 | 14030 | No |
| 9866 | Topological Scholarly Liquidity Shock Deflector Mod-38 | Attention networks / Transformer encoders / Stock alpha generation | 12875 | 12020 | No |
| 9944 | Topological Scholarly Liquidity Shock Deflector Mod-230 | Neural operators / Deep operator networks / ETF rotation | 9396 | 7743 | No |
| 9982 | Topological Scholarly Liquidity Shock Deflector Mod-326 | Quantum machine learning / Variational circuits / Index prediction | 14035 | 14036 | No |
| 10057 | Topological Scholarly Liquidity Shock Deflector Mod-518 | Attention networks / Transformer encoders / Stock alpha generation | 12887 | 12043 | No |
| 10135 | Topological Scholarly Liquidity Shock Deflector Mod-710 | Neural operators / Deep operator networks / ETF rotation | 9413 | 7773 | No |
| 10173 | Topological Scholarly Liquidity Shock Deflector Mod-806 | Quantum machine learning / Variational circuits / Index prediction | 14043 | 14044 | No |
| 10248 | Topological Scholarly Liquidity Shock Deflector Mod-998 | Attention networks / Transformer encoders / Stock alpha generation | 12899 | 12066 | No |
| 10326 | Topological Scholarly Liquidity Shock Deflector Mod-1190 | Neural operators / Deep operator networks / ETF rotation | 9430 | 7803 | No |
| 10364 | Topological Scholarly Liquidity Shock Deflector Mod-1286 | Quantum machine learning / Variational circuits / Index prediction | 14051 | 14052 | No |
| 10439 | Topological Scholarly Liquidity Shock Deflector Mod-1478 | Attention networks / Transformer encoders / Stock alpha generation | 12911 | 12089 | No |
| 10517 | Topological Scholarly Liquidity Shock Deflector Mod-1670 | Neural operators / Deep operator networks / ETF rotation | 9447 | 7833 | No |
| 10555 | Topological Scholarly Liquidity Shock Deflector Mod-1766 | Quantum machine learning / Variational circuits / Index prediction | 14059 | 14060 | No |
| 10630 | Topological Scholarly Liquidity Shock Deflector Mod-1958 | Attention networks / Transformer encoders / Stock alpha generation | 12923 | 12112 | No |
| 10708 | Topological Scholarly Liquidity Shock Deflector Mod-2150 | Neural operators / Deep operator networks / ETF rotation | 9464 | 7863 | No |
| 10746 | Topological Scholarly Liquidity Shock Deflector Mod-2246 | Quantum machine learning / Variational circuits / Index prediction | 14067 | 14068 | No |
| 10821 | Topological Scholarly Liquidity Shock Deflector Mod-2438 | Attention networks / Transformer encoders / Stock alpha generation | 12935 | 12135 | No |
| 10899 | Topological Scholarly Liquidity Shock Deflector Mod-2630 | Neural operators / Deep operator networks / ETF rotation | 9481 | 7893 | No |
| 10937 | Topological Scholarly Liquidity Shock Deflector Mod-2726 | Quantum machine learning / Variational circuits / Index prediction | 14075 | 14076 | No |
| 11012 | Topological Scholarly Liquidity Shock Deflector Mod-2918 | Attention networks / Transformer encoders / Stock alpha generation | 12947 | 12158 | No |
| 11090 | Topological Scholarly Liquidity Shock Deflector Mod-3110 | Neural operators / Deep operator networks / ETF rotation | 9498 | 7923 | No |
| 11128 | Topological Scholarly Liquidity Shock Deflector Mod-3206 | Quantum machine learning / Variational circuits / Index prediction | 14083 | 14084 | No |
| 11203 | Topological Scholarly Liquidity Shock Deflector Mod-3398 | Attention networks / Transformer encoders / Stock alpha generation | 12959 | 12181 | No |
| 11281 | Topological Scholarly Liquidity Shock Deflector Mod-3590 | Neural operators / Deep operator networks / ETF rotation | 9515 | 7953 | No |
| 11319 | Topological Scholarly Liquidity Shock Deflector Mod-3686 | Quantum machine learning / Variational circuits / Index prediction | 14091 | 14092 | No |
| 11394 | Topological Scholarly Liquidity Shock Deflector Mod-3878 | Attention networks / Transformer encoders / Stock alpha generation | 12971 | 12204 | No |
| 13838 | Topological Scholarly Liquidity Shock Detector Ver-16 | Koopman operator / Model predictive control / ETF execution | 3821 | 2856 | No |
| 13842 | Topological Scholarly Liquidity Shock Detector Ver-116 | Koopman operator / Model predictive control / ETF execution | 13171 | 13691 | No |
