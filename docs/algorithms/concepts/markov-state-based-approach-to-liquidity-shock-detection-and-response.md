# Markov-state-based approach to liquidity-shock detection and response

**Concept page** · shared by **72** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,756) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Hidden Markov / regime-switching states |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A hidden Markov model could drive a buy gate, but no study shows it beating the simple spread and volume gates already built (RK244, RK247); background. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Markovian Scholarly
Liquidity Shock Deflector Ref-262") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The Markov-state version
infers hidden states (calm, turbulent, crisis) and conditions on the
current one. I found no study of this method on this task.

## The CSV's description

Proposed Markov-state-based approach to liquidity-shock detection and
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
* States are clear only after the fact; causal (filtered) state
  probabilities lag turning points.

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
| 1756 | Markovian Scholarly Liquidity Shock Deflector Ref-262 | Robust optimization / Distributionally robust CVaR / Index tracking | 8257 | 11306 | No |
| 1811 | Markovian Scholarly Liquidity Shock Deflector Ref-742 | Robust optimization / Distributionally robust CVaR / Index tracking | 8298 | 11327 | No |
| 2499 | Markovian Scholarly Liquidity Shock Deflector Eng-182 | Robust optimization / Distributionally robust CVaR / Index tracking | 5067 | 4481 | No |
| 2554 | Markovian Scholarly Liquidity Shock Deflector Eng-662 | Robust optimization / Distributionally robust CVaR / Index tracking | 5092 | 4574 | No |
| 2609 | Markovian Scholarly Liquidity Shock Deflector Eng-1142 | Robust optimization / Distributionally robust CVaR / Index tracking | 5117 | 4667 | No |
| 2664 | Markovian Scholarly Liquidity Shock Deflector Eng-1622 | Robust optimization / Distributionally robust CVaR / Index tracking | 5142 | 4760 | No |
| 2719 | Markovian Scholarly Liquidity Shock Deflector Eng-2102 | Robust optimization / Distributionally robust CVaR / Index tracking | 5167 | 4853 | No |
| 2774 | Markovian Scholarly Liquidity Shock Deflector Eng-2582 | Robust optimization / Distributionally robust CVaR / Index tracking | 5192 | 4946 | No |
| 2829 | Markovian Scholarly Liquidity Shock Deflector Eng-3062 | Robust optimization / Distributionally robust CVaR / Index tracking | 5217 | 5039 | No |
| 2884 | Markovian Scholarly Liquidity Shock Deflector Eng-3542 | Robust optimization / Distributionally robust CVaR / Index tracking | 5242 | 5132 | No |
| 2939 | Markovian Scholarly Liquidity Shock Deflector Eng-4022 | Robust optimization / Distributionally robust CVaR / Index tracking | 5267 | 5225 | No |
| 2994 | Markovian Scholarly Liquidity Shock Deflector Eng-4502 | Robust optimization / Distributionally robust CVaR / Index tracking | 5292 | 5318 | No |
| 3049 | Markovian Scholarly Liquidity Shock Deflector Eng-4982 | Robust optimization / Distributionally robust CVaR / Index tracking | 5317 | 5411 | No |
| 3104 | Markovian Scholarly Liquidity Shock Deflector Eng-5462 | Robust optimization / Distributionally robust CVaR / Index tracking | 5342 | 5504 | No |
| 3159 | Markovian Scholarly Liquidity Shock Deflector Eng-5942 | Robust optimization / Distributionally robust CVaR / Index tracking | 5367 | 5597 | No |
| 3191 | Markovian Scholarly Liquidity Shock Deflector Ref-454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6530 | 3123 | No |
| 3207 | Markovian Scholarly Liquidity Shock Deflector Ref-934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6573 | 3240 | No |
| 3464 | Markovian Scholarly Liquidity Shock Deflector Eng-374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5506 | 8947 | No |
| 3480 | Markovian Scholarly Liquidity Shock Deflector Eng-854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5514 | 8982 | No |
| 3496 | Markovian Scholarly Liquidity Shock Deflector Eng-1334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5522 | 9017 | No |
| 3512 | Markovian Scholarly Liquidity Shock Deflector Eng-1814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5530 | 9052 | No |
| 3528 | Markovian Scholarly Liquidity Shock Deflector Eng-2294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5538 | 9087 | No |
| 3544 | Markovian Scholarly Liquidity Shock Deflector Eng-2774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5546 | 9122 | No |
| 3560 | Markovian Scholarly Liquidity Shock Deflector Eng-3254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5554 | 9157 | No |
| 3576 | Markovian Scholarly Liquidity Shock Deflector Eng-3734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5562 | 9192 | No |
| 3592 | Markovian Scholarly Liquidity Shock Deflector Eng-4214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5570 | 9227 | No |
| 3608 | Markovian Scholarly Liquidity Shock Deflector Eng-4694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5578 | 9262 | No |
| 3624 | Markovian Scholarly Liquidity Shock Deflector Eng-5174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5586 | 9297 | No |
| 3640 | Markovian Scholarly Liquidity Shock Deflector Eng-5654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5594 | 9332 | No |
| 7476 | Markovian Scholarly Liquidity Shock Deflector Ref-358 | Attention networks / Transformer encoders / Stock alpha generation | 3221 | 3098 | No |
| 7510 | Markovian Scholarly Liquidity Shock Deflector Ref-838 | Attention networks / Transformer encoders / Stock alpha generation | 3237 | 3215 | No |
| 7935 | Markovian Scholarly Liquidity Shock Deflector Eng-278 | Attention networks / Transformer encoders / Stock alpha generation | 12980 | 12223 | No |
| 7969 | Markovian Scholarly Liquidity Shock Deflector Eng-758 | Attention networks / Transformer encoders / Stock alpha generation | 12990 | 12246 | No |
| 8003 | Markovian Scholarly Liquidity Shock Deflector Eng-1238 | Attention networks / Transformer encoders / Stock alpha generation | 13000 | 12269 | No |
| 8037 | Markovian Scholarly Liquidity Shock Deflector Eng-1718 | Attention networks / Transformer encoders / Stock alpha generation | 13010 | 12292 | No |
| 8071 | Markovian Scholarly Liquidity Shock Deflector Eng-2198 | Attention networks / Transformer encoders / Stock alpha generation | 13020 | 12315 | No |
| 8105 | Markovian Scholarly Liquidity Shock Deflector Eng-2678 | Attention networks / Transformer encoders / Stock alpha generation | 13030 | 12338 | No |
| 8139 | Markovian Scholarly Liquidity Shock Deflector Eng-3158 | Attention networks / Transformer encoders / Stock alpha generation | 13040 | 12361 | No |
| 8173 | Markovian Scholarly Liquidity Shock Deflector Eng-3638 | Attention networks / Transformer encoders / Stock alpha generation | 13050 | 12384 | No |
| 8207 | Markovian Scholarly Liquidity Shock Deflector Eng-4118 | Attention networks / Transformer encoders / Stock alpha generation | 13060 | 12407 | No |
| 8241 | Markovian Scholarly Liquidity Shock Deflector Eng-4598 | Attention networks / Transformer encoders / Stock alpha generation | 13070 | 12430 | No |
| 8275 | Markovian Scholarly Liquidity Shock Deflector Eng-5078 | Attention networks / Transformer encoders / Stock alpha generation | 13080 | 12453 | No |
| 8309 | Markovian Scholarly Liquidity Shock Deflector Eng-5558 | Attention networks / Transformer encoders / Stock alpha generation | 13090 | 12476 | No |
| 8704 | Markovian Scholarly Liquidity Shock Deflector Ref-70 | Neural operators / Deep operator networks / ETF rotation | 7635 | 3028 | No |
| 8741 | Markovian Scholarly Liquidity Shock Deflector Ref-166 | Quantum machine learning / Variational circuits / Index prediction | 11294 | 5968 | No |
| 8895 | Markovian Scholarly Liquidity Shock Deflector Ref-550 | Neural operators / Deep operator networks / ETF rotation | 7643 | 3145 | No |
| 8932 | Markovian Scholarly Liquidity Shock Deflector Ref-646 | Quantum machine learning / Variational circuits / Index prediction | 11319 | 5988 | No |
| 11477 | Markovian Scholarly Liquidity Shock Deflector Eng-86 | Quantum machine learning / Variational circuits / Index prediction | 14098 | 14099 | No |
| 11628 | Markovian Scholarly Liquidity Shock Deflector Eng-470 | Neural operators / Deep operator networks / ETF rotation | 9545 | 8009 | No |
| 11668 | Markovian Scholarly Liquidity Shock Deflector Eng-566 | Quantum machine learning / Variational circuits / Index prediction | 14106 | 14107 | No |
| 11819 | Markovian Scholarly Liquidity Shock Deflector Eng-950 | Neural operators / Deep operator networks / ETF rotation | 9561 | 8041 | No |
| 11859 | Markovian Scholarly Liquidity Shock Deflector Eng-1046 | Quantum machine learning / Variational circuits / Index prediction | 14114 | 14115 | No |
| 12010 | Markovian Scholarly Liquidity Shock Deflector Eng-1430 | Neural operators / Deep operator networks / ETF rotation | 9577 | 8073 | No |
| 12050 | Markovian Scholarly Liquidity Shock Deflector Eng-1526 | Quantum machine learning / Variational circuits / Index prediction | 14122 | 14123 | No |
| 12201 | Markovian Scholarly Liquidity Shock Deflector Eng-1910 | Neural operators / Deep operator networks / ETF rotation | 9593 | 8105 | No |
| 12241 | Markovian Scholarly Liquidity Shock Deflector Eng-2006 | Quantum machine learning / Variational circuits / Index prediction | 14130 | 14131 | No |
| 12392 | Markovian Scholarly Liquidity Shock Deflector Eng-2390 | Neural operators / Deep operator networks / ETF rotation | 9609 | 8137 | No |
| 12432 | Markovian Scholarly Liquidity Shock Deflector Eng-2486 | Quantum machine learning / Variational circuits / Index prediction | 14138 | 14139 | No |
| 12583 | Markovian Scholarly Liquidity Shock Deflector Eng-2870 | Neural operators / Deep operator networks / ETF rotation | 9625 | 8169 | No |
| 12623 | Markovian Scholarly Liquidity Shock Deflector Eng-2966 | Quantum machine learning / Variational circuits / Index prediction | 14146 | 14147 | No |
| 12774 | Markovian Scholarly Liquidity Shock Deflector Eng-3350 | Neural operators / Deep operator networks / ETF rotation | 9641 | 8201 | No |
| 12814 | Markovian Scholarly Liquidity Shock Deflector Eng-3446 | Quantum machine learning / Variational circuits / Index prediction | 14154 | 14155 | No |
| 12965 | Markovian Scholarly Liquidity Shock Deflector Eng-3830 | Neural operators / Deep operator networks / ETF rotation | 9657 | 8233 | No |
| 13005 | Markovian Scholarly Liquidity Shock Deflector Eng-3926 | Quantum machine learning / Variational circuits / Index prediction | 14162 | 14163 | No |
| 13156 | Markovian Scholarly Liquidity Shock Deflector Eng-4310 | Neural operators / Deep operator networks / ETF rotation | 9673 | 8265 | No |
| 13196 | Markovian Scholarly Liquidity Shock Deflector Eng-4406 | Quantum machine learning / Variational circuits / Index prediction | 14170 | 14171 | No |
| 13347 | Markovian Scholarly Liquidity Shock Deflector Eng-4790 | Neural operators / Deep operator networks / ETF rotation | 9689 | 8297 | No |
| 13387 | Markovian Scholarly Liquidity Shock Deflector Eng-4886 | Quantum machine learning / Variational circuits / Index prediction | 14178 | 14179 | No |
| 13538 | Markovian Scholarly Liquidity Shock Deflector Eng-5270 | Neural operators / Deep operator networks / ETF rotation | 9705 | 8329 | No |
| 13578 | Markovian Scholarly Liquidity Shock Deflector Eng-5366 | Quantum machine learning / Variational circuits / Index prediction | 14186 | 14187 | No |
| 13729 | Markovian Scholarly Liquidity Shock Deflector Eng-5750 | Neural operators / Deep operator networks / ETF rotation | 9721 | 8361 | No |
| 13769 | Markovian Scholarly Liquidity Shock Deflector Eng-5846 | Quantum machine learning / Variational circuits / Index prediction | 14194 | 14195 | No |
