# Topology-aware approach to topological-feature portfolio allocation

**Concept page** · shared by **74** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,805) ·
researched 2026-10-30

| | |
|---|---|
| Task | Topological-feature portfolio allocation |
| Method | Topological data analysis (persistent homology) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The task is defined by topological features, which have no out-of-sample evidence (RK262); the method word does not change that. |
| Implemented in volatility-ai | Persistence diagrams and landscapes are research code (`topology`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK262, RK265, RK269 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Topological Scholarly
Topological Betti Allocator Ref-202") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Derive persistent-homology or Betti-number features from asset
relationships and test whether they improve allocation beyond simpler
baselines. The topology-aware version derives persistent-homology
features (Betti numbers, persistence landscapes) from sliding windows of
returns. I found no study of this method on this task.

## The CSV's description

Proposed topology-aware approach to topological-feature portfolio
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
* The best-known topological crash study is in sample (Gidea & Katz
  2018), and the features depend on window and scale choices.

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
| 3805 | Topological Scholarly Topological Betti Allocator Ref-202 | Robust optimization / Distributionally robust CVaR / Index tracking | 8252 | 11304 | No |
| 3891 | Topological Scholarly Topological Betti Allocator Ref-682 | Robust optimization / Distributionally robust CVaR / Index tracking | 8293 | 11325 | No |
| 5044 | Topological Scholarly Topological Betti Allocator Eng-122 | Robust optimization / Distributionally robust CVaR / Index tracking | 5062 | 4465 | No |
| 5130 | Topological Scholarly Topological Betti Allocator Eng-602 | Robust optimization / Distributionally robust CVaR / Index tracking | 5087 | 4558 | No |
| 5216 | Topological Scholarly Topological Betti Allocator Eng-1082 | Robust optimization / Distributionally robust CVaR / Index tracking | 5112 | 4651 | No |
| 5302 | Topological Scholarly Topological Betti Allocator Eng-1562 | Robust optimization / Distributionally robust CVaR / Index tracking | 5137 | 4744 | No |
| 5388 | Topological Scholarly Topological Betti Allocator Eng-2042 | Robust optimization / Distributionally robust CVaR / Index tracking | 5162 | 4837 | No |
| 5474 | Topological Scholarly Topological Betti Allocator Eng-2522 | Robust optimization / Distributionally robust CVaR / Index tracking | 5187 | 4930 | No |
| 5560 | Topological Scholarly Topological Betti Allocator Eng-3002 | Robust optimization / Distributionally robust CVaR / Index tracking | 5212 | 5023 | No |
| 5646 | Topological Scholarly Topological Betti Allocator Eng-3482 | Robust optimization / Distributionally robust CVaR / Index tracking | 5237 | 5116 | No |
| 5732 | Topological Scholarly Topological Betti Allocator Eng-3962 | Robust optimization / Distributionally robust CVaR / Index tracking | 5262 | 5209 | No |
| 5818 | Topological Scholarly Topological Betti Allocator Eng-4442 | Robust optimization / Distributionally robust CVaR / Index tracking | 5287 | 5302 | No |
| 5904 | Topological Scholarly Topological Betti Allocator Eng-4922 | Robust optimization / Distributionally robust CVaR / Index tracking | 5312 | 5395 | No |
| 5990 | Topological Scholarly Topological Betti Allocator Eng-5402 | Robust optimization / Distributionally robust CVaR / Index tracking | 5337 | 5488 | No |
| 6076 | Topological Scholarly Topological Betti Allocator Eng-5882 | Robust optimization / Distributionally robust CVaR / Index tracking | 5362 | 5581 | No |
| 6224 | Topological Scholarly Topological Betti Allocator Ref-394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6525 | 3109 | No |
| 6270 | Topological Scholarly Topological Betti Allocator Ref-874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6568 | 3226 | No |
| 6859 | Topological Scholarly Topological Betti Allocator Eng-314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5505 | 8941 | No |
| 6905 | Topological Scholarly Topological Betti Allocator Eng-794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5513 | 8976 | No |
| 6951 | Topological Scholarly Topological Betti Allocator Eng-1274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5521 | 9011 | No |
| 6997 | Topological Scholarly Topological Betti Allocator Eng-1754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5529 | 9046 | No |
| 7043 | Topological Scholarly Topological Betti Allocator Eng-2234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5537 | 9081 | No |
| 7089 | Topological Scholarly Topological Betti Allocator Eng-2714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5545 | 9116 | No |
| 7135 | Topological Scholarly Topological Betti Allocator Eng-3194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5553 | 9151 | No |
| 7181 | Topological Scholarly Topological Betti Allocator Eng-3674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5561 | 9186 | No |
| 7227 | Topological Scholarly Topological Betti Allocator Eng-4154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5569 | 9221 | No |
| 7273 | Topological Scholarly Topological Betti Allocator Eng-4634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5577 | 9256 | No |
| 7319 | Topological Scholarly Topological Betti Allocator Eng-5114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5585 | 9291 | No |
| 7365 | Topological Scholarly Topological Betti Allocator Eng-5594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5593 | 9326 | No |
| 8680 | Topological Scholarly Topological Betti Allocator Ref-10 | Neural operators / Deep operator networks / ETF rotation | 7634 | 3013 | No |
| 8718 | Topological Scholarly Topological Betti Allocator Ref-106 | Quantum machine learning / Variational circuits / Index prediction | 11290 | 5965 | No |
| 8793 | Topological Scholarly Topological Betti Allocator Ref-298 | Attention networks / Transformer encoders / Stock alpha generation | 3219 | 3084 | No |
| 8871 | Topological Scholarly Topological Betti Allocator Ref-490 | Neural operators / Deep operator networks / ETF rotation | 7642 | 3130 | No |
| 8909 | Topological Scholarly Topological Betti Allocator Ref-586 | Quantum machine learning / Variational circuits / Index prediction | 11315 | 5985 | No |
| 8984 | Topological Scholarly Topological Betti Allocator Ref-778 | Attention networks / Transformer encoders / Stock alpha generation | 3235 | 3201 | No |
| 9062 | Topological Scholarly Topological Betti Allocator Ref-970 | Neural operators / Deep operator networks / ETF rotation | 7650 | 3247 | No |
| 11453 | Topological Scholarly Topological Betti Allocator Eng-26 | Quantum machine learning / Variational circuits / Index prediction | 14097 | 14098 | No |
| 11530 | Topological Scholarly Topological Betti Allocator Eng-218 | Attention networks / Transformer encoders / Stock alpha generation | 12979 | 12220 | No |
| 11607 | Topological Scholarly Topological Betti Allocator Eng-410 | Neural operators / Deep operator networks / ETF rotation | 9543 | 8005 | No |
| 11644 | Topological Scholarly Topological Betti Allocator Eng-506 | Quantum machine learning / Variational circuits / Index prediction | 14105 | 14106 | No |
| 11721 | Topological Scholarly Topological Betti Allocator Eng-698 | Attention networks / Transformer encoders / Stock alpha generation | 12989 | 12243 | No |
| 11798 | Topological Scholarly Topological Betti Allocator Eng-890 | Neural operators / Deep operator networks / ETF rotation | 9559 | 8037 | No |
| 11835 | Topological Scholarly Topological Betti Allocator Eng-986 | Quantum machine learning / Variational circuits / Index prediction | 14113 | 14114 | No |
| 11912 | Topological Scholarly Topological Betti Allocator Eng-1178 | Attention networks / Transformer encoders / Stock alpha generation | 12999 | 12266 | No |
| 11989 | Topological Scholarly Topological Betti Allocator Eng-1370 | Neural operators / Deep operator networks / ETF rotation | 9575 | 8069 | No |
| 12026 | Topological Scholarly Topological Betti Allocator Eng-1466 | Quantum machine learning / Variational circuits / Index prediction | 14121 | 14122 | No |
| 12103 | Topological Scholarly Topological Betti Allocator Eng-1658 | Attention networks / Transformer encoders / Stock alpha generation | 13009 | 12289 | No |
| 12180 | Topological Scholarly Topological Betti Allocator Eng-1850 | Neural operators / Deep operator networks / ETF rotation | 9591 | 8101 | No |
| 12217 | Topological Scholarly Topological Betti Allocator Eng-1946 | Quantum machine learning / Variational circuits / Index prediction | 14129 | 14130 | No |
| 12294 | Topological Scholarly Topological Betti Allocator Eng-2138 | Attention networks / Transformer encoders / Stock alpha generation | 13019 | 12312 | No |
| 12371 | Topological Scholarly Topological Betti Allocator Eng-2330 | Neural operators / Deep operator networks / ETF rotation | 9607 | 8133 | No |
| 12408 | Topological Scholarly Topological Betti Allocator Eng-2426 | Quantum machine learning / Variational circuits / Index prediction | 14137 | 14138 | No |
| 12485 | Topological Scholarly Topological Betti Allocator Eng-2618 | Attention networks / Transformer encoders / Stock alpha generation | 13029 | 12335 | No |
| 12562 | Topological Scholarly Topological Betti Allocator Eng-2810 | Neural operators / Deep operator networks / ETF rotation | 9623 | 8165 | No |
| 12599 | Topological Scholarly Topological Betti Allocator Eng-2906 | Quantum machine learning / Variational circuits / Index prediction | 14145 | 14146 | No |
| 12676 | Topological Scholarly Topological Betti Allocator Eng-3098 | Attention networks / Transformer encoders / Stock alpha generation | 13039 | 12358 | No |
| 12753 | Topological Scholarly Topological Betti Allocator Eng-3290 | Neural operators / Deep operator networks / ETF rotation | 9639 | 8197 | No |
| 12790 | Topological Scholarly Topological Betti Allocator Eng-3386 | Quantum machine learning / Variational circuits / Index prediction | 14153 | 14154 | No |
| 12867 | Topological Scholarly Topological Betti Allocator Eng-3578 | Attention networks / Transformer encoders / Stock alpha generation | 13049 | 12381 | No |
| 12944 | Topological Scholarly Topological Betti Allocator Eng-3770 | Neural operators / Deep operator networks / ETF rotation | 9655 | 8229 | No |
| 12981 | Topological Scholarly Topological Betti Allocator Eng-3866 | Quantum machine learning / Variational circuits / Index prediction | 14161 | 14162 | No |
| 13058 | Topological Scholarly Topological Betti Allocator Eng-4058 | Attention networks / Transformer encoders / Stock alpha generation | 13059 | 12404 | No |
| 13135 | Topological Scholarly Topological Betti Allocator Eng-4250 | Neural operators / Deep operator networks / ETF rotation | 9671 | 8261 | No |
| 13172 | Topological Scholarly Topological Betti Allocator Eng-4346 | Quantum machine learning / Variational circuits / Index prediction | 14169 | 14170 | No |
| 13249 | Topological Scholarly Topological Betti Allocator Eng-4538 | Attention networks / Transformer encoders / Stock alpha generation | 13069 | 12427 | No |
| 13326 | Topological Scholarly Topological Betti Allocator Eng-4730 | Neural operators / Deep operator networks / ETF rotation | 9687 | 8293 | No |
| 13363 | Topological Scholarly Topological Betti Allocator Eng-4826 | Quantum machine learning / Variational circuits / Index prediction | 14177 | 14178 | No |
| 13440 | Topological Scholarly Topological Betti Allocator Eng-5018 | Attention networks / Transformer encoders / Stock alpha generation | 13079 | 12450 | No |
| 13517 | Topological Scholarly Topological Betti Allocator Eng-5210 | Neural operators / Deep operator networks / ETF rotation | 9703 | 8325 | No |
| 13554 | Topological Scholarly Topological Betti Allocator Eng-5306 | Quantum machine learning / Variational circuits / Index prediction | 14185 | 14186 | No |
| 13631 | Topological Scholarly Topological Betti Allocator Eng-5498 | Attention networks / Transformer encoders / Stock alpha generation | 13089 | 12473 | No |
| 13708 | Topological Scholarly Topological Betti Allocator Eng-5690 | Neural operators / Deep operator networks / ETF rotation | 9719 | 8357 | No |
| 13745 | Topological Scholarly Topological Betti Allocator Eng-5786 | Quantum machine learning / Variational circuits / Index prediction | 14193 | 14194 | No |
| 13822 | Topological Scholarly Topological Betti Allocator Eng-5978 | Attention networks / Transformer encoders / Stock alpha generation | 13099 | 12496 | No |
