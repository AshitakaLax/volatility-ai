# Markov-state-based approach to topological-feature portfolio allocation

**Concept page** · shared by **61** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,985) ·
researched 2026-10-30

| | |
|---|---|
| Task | Topological-feature portfolio allocation |
| Method | Hidden Markov / regime-switching states |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The task is defined by topological features, which have no out-of-sample evidence (RK262); the method word does not change that. |
| Implemented in volatility-ai | Persistence diagrams and landscapes are research code (`topology`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK262, RK265, RK269 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Markovian Scholarly
Topological Betti Allocator Sys-182") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Derive persistent-homology or Betti-number features from asset
relationships and test whether they improve allocation beyond simpler
baselines. The Markov-state version infers hidden states (calm,
turbulent, crisis) and conditions on the current one. I found no study
of this method on this task.

## The CSV's description

Proposed Markov-state-based approach to topological-feature portfolio
allocation: Derive persistent-homology or Betti-number features from
market/asset relationships and test whether they improve allocation or
risk control beyond simpler baselines. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gidea & Katz (2018), "Topological data analysis of financial time
  series: Landscapes of crashes," *Physica A* 491, 820–834:**
  persistence landscapes of index returns rose before the 2000 and 2008
  crashes, shown in sample (see RK262). (Abstract.)

## Against, and failure modes

* The best-known topological crash signal is in sample, and the ledger's
  TDA entries found no out-of-sample evidence.
* States are clear only after the fact; causal (filtered) state
  probabilities lag turning points.

## Fit with volatility-ai

The ledger's topological entries are ⛔ for want of evidence (RK262,
RK265, RK269), and the book has one asset to allocate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3985 | Markovian Scholarly Topological Betti Allocator Sys-182 | Robust optimization / Distributionally robust CVaR / Index tracking | 4714 | 3292 | No |
| 4071 | Markovian Scholarly Topological Betti Allocator Sys-662 | Robust optimization / Distributionally robust CVaR / Index tracking | 4745 | 3387 | No |
| 4157 | Markovian Scholarly Topological Betti Allocator Sys-1142 | Robust optimization / Distributionally robust CVaR / Index tracking | 4776 | 3482 | No |
| 4243 | Markovian Scholarly Topological Betti Allocator Sys-1622 | Robust optimization / Distributionally robust CVaR / Index tracking | 4807 | 3577 | No |
| 4375 | Markovian Scholarly Topological Betti Allocator Mod-362 | Robust optimization / Distributionally robust CVaR / Index tracking | 4852 | 3723 | No |
| 4460 | Markovian Scholarly Topological Betti Allocator Mod-842 | Robust optimization / Distributionally robust CVaR / Index tracking | 4879 | 3818 | No |
| 4545 | Markovian Scholarly Topological Betti Allocator Mod-1322 | Robust optimization / Distributionally robust CVaR / Index tracking | 4906 | 3913 | No |
| 4630 | Markovian Scholarly Topological Betti Allocator Mod-1802 | Robust optimization / Distributionally robust CVaR / Index tracking | 4933 | 4008 | No |
| 4715 | Markovian Scholarly Topological Betti Allocator Mod-2282 | Robust optimization / Distributionally robust CVaR / Index tracking | 4960 | 4103 | No |
| 4800 | Markovian Scholarly Topological Betti Allocator Mod-2762 | Robust optimization / Distributionally robust CVaR / Index tracking | 4987 | 4198 | No |
| 4885 | Markovian Scholarly Topological Betti Allocator Mod-3242 | Robust optimization / Distributionally robust CVaR / Index tracking | 5014 | 4293 | No |
| 4970 | Markovian Scholarly Topological Betti Allocator Mod-3722 | Robust optimization / Distributionally robust CVaR / Index tracking | 5041 | 4388 | No |
| 6314 | Markovian Scholarly Topological Betti Allocator Sys-374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5405 | 8494 | No |
| 6355 | Markovian Scholarly Topological Betti Allocator Sys-854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5413 | 8529 | No |
| 6396 | Markovian Scholarly Topological Betti Allocator Sys-1334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5421 | 8564 | No |
| 6437 | Markovian Scholarly Topological Betti Allocator Sys-1814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5429 | 8599 | No |
| 6461 | Markovian Scholarly Topological Betti Allocator Mod-74 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5434 | 8618 | No |
| 6506 | Markovian Scholarly Topological Betti Allocator Mod-554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5442 | 8655 | No |
| 6551 | Markovian Scholarly Topological Betti Allocator Mod-1034 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5450 | 8692 | No |
| 6596 | Markovian Scholarly Topological Betti Allocator Mod-1514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5458 | 8729 | No |
| 6641 | Markovian Scholarly Topological Betti Allocator Mod-1994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5466 | 8766 | No |
| 6686 | Markovian Scholarly Topological Betti Allocator Mod-2474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5474 | 8803 | No |
| 6731 | Markovian Scholarly Topological Betti Allocator Mod-2954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5482 | 8840 | No |
| 6776 | Markovian Scholarly Topological Betti Allocator Mod-3434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5490 | 8877 | No |
| 6821 | Markovian Scholarly Topological Betti Allocator Mod-3914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5498 | 8914 | No |
| 9105 | Markovian Scholarly Topological Betti Allocator Sys-86 | Quantum machine learning / Variational circuits / Index prediction | 13994 | 13999 | No |
| 9182 | Markovian Scholarly Topological Betti Allocator Sys-278 | Attention networks / Transformer encoders / Stock alpha generation | 12838 | 11935 | No |
| 9257 | Markovian Scholarly Topological Betti Allocator Sys-470 | Neural operators / Deep operator networks / ETF rotation | 9339 | 7657 | No |
| 9292 | Markovian Scholarly Topological Betti Allocator Sys-566 | Quantum machine learning / Variational circuits / Index prediction | 14003 | 14007 | No |
| 9369 | Markovian Scholarly Topological Betti Allocator Sys-758 | Attention networks / Transformer encoders / Stock alpha generation | 12848 | 11958 | No |
| 9444 | Markovian Scholarly Topological Betti Allocator Sys-950 | Neural operators / Deep operator networks / ETF rotation | 9355 | 7679 | No |
| 9479 | Markovian Scholarly Topological Betti Allocator Sys-1046 | Quantum machine learning / Variational circuits / Index prediction | 14012 | 14015 | No |
| 9556 | Markovian Scholarly Topological Betti Allocator Sys-1238 | Attention networks / Transformer encoders / Stock alpha generation | 12858 | 11981 | No |
| 9631 | Markovian Scholarly Topological Betti Allocator Sys-1430 | Neural operators / Deep operator networks / ETF rotation | 9371 | 7701 | No |
| 9666 | Markovian Scholarly Topological Betti Allocator Sys-1526 | Quantum machine learning / Variational circuits / Index prediction | 14021 | 14023 | No |
| 9743 | Markovian Scholarly Topological Betti Allocator Sys-1718 | Attention networks / Transformer encoders / Stock alpha generation | 12868 | 12004 | No |
| 9818 | Markovian Scholarly Topological Betti Allocator Sys-1910 | Neural operators / Deep operator networks / ETF rotation | 9387 | 7723 | No |
| 9917 | Markovian Scholarly Topological Betti Allocator Mod-170 | Neural operators / Deep operator networks / ETF rotation | 9395 | 7738 | No |
| 9959 | Markovian Scholarly Topological Betti Allocator Mod-266 | Quantum machine learning / Variational circuits / Index prediction | 14034 | 14035 | No |
| 10035 | Markovian Scholarly Topological Betti Allocator Mod-458 | Attention networks / Transformer encoders / Stock alpha generation | 12886 | 12040 | No |
| 10108 | Markovian Scholarly Topological Betti Allocator Mod-650 | Neural operators / Deep operator networks / ETF rotation | 9412 | 7768 | No |
| 10150 | Markovian Scholarly Topological Betti Allocator Mod-746 | Quantum machine learning / Variational circuits / Index prediction | 14042 | 14043 | No |
| 10226 | Markovian Scholarly Topological Betti Allocator Mod-938 | Attention networks / Transformer encoders / Stock alpha generation | 12898 | 12063 | No |
| 10299 | Markovian Scholarly Topological Betti Allocator Mod-1130 | Neural operators / Deep operator networks / ETF rotation | 9429 | 7798 | No |
| 10341 | Markovian Scholarly Topological Betti Allocator Mod-1226 | Quantum machine learning / Variational circuits / Index prediction | 14050 | 14051 | No |
| 10417 | Markovian Scholarly Topological Betti Allocator Mod-1418 | Attention networks / Transformer encoders / Stock alpha generation | 12910 | 12086 | No |
| 10490 | Markovian Scholarly Topological Betti Allocator Mod-1610 | Neural operators / Deep operator networks / ETF rotation | 9446 | 7828 | No |
| 10532 | Markovian Scholarly Topological Betti Allocator Mod-1706 | Quantum machine learning / Variational circuits / Index prediction | 14058 | 14059 | No |
| 10608 | Markovian Scholarly Topological Betti Allocator Mod-1898 | Attention networks / Transformer encoders / Stock alpha generation | 12922 | 12109 | No |
| 10681 | Markovian Scholarly Topological Betti Allocator Mod-2090 | Neural operators / Deep operator networks / ETF rotation | 9463 | 7858 | No |
| 10723 | Markovian Scholarly Topological Betti Allocator Mod-2186 | Quantum machine learning / Variational circuits / Index prediction | 14066 | 14067 | No |
| 10799 | Markovian Scholarly Topological Betti Allocator Mod-2378 | Attention networks / Transformer encoders / Stock alpha generation | 12934 | 12132 | No |
| 10872 | Markovian Scholarly Topological Betti Allocator Mod-2570 | Neural operators / Deep operator networks / ETF rotation | 9480 | 7888 | No |
| 10914 | Markovian Scholarly Topological Betti Allocator Mod-2666 | Quantum machine learning / Variational circuits / Index prediction | 14074 | 14075 | No |
| 10990 | Markovian Scholarly Topological Betti Allocator Mod-2858 | Attention networks / Transformer encoders / Stock alpha generation | 12946 | 12155 | No |
| 11063 | Markovian Scholarly Topological Betti Allocator Mod-3050 | Neural operators / Deep operator networks / ETF rotation | 9497 | 7918 | No |
| 11105 | Markovian Scholarly Topological Betti Allocator Mod-3146 | Quantum machine learning / Variational circuits / Index prediction | 14082 | 14083 | No |
| 11181 | Markovian Scholarly Topological Betti Allocator Mod-3338 | Attention networks / Transformer encoders / Stock alpha generation | 12958 | 12178 | No |
| 11254 | Markovian Scholarly Topological Betti Allocator Mod-3530 | Neural operators / Deep operator networks / ETF rotation | 9514 | 7948 | No |
| 11296 | Markovian Scholarly Topological Betti Allocator Mod-3626 | Quantum machine learning / Variational circuits / Index prediction | 14090 | 14091 | No |
| 11372 | Markovian Scholarly Topological Betti Allocator Mod-3818 | Attention networks / Transformer encoders / Stock alpha generation | 12970 | 12201 | No |
