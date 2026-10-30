# Conformal-prediction-based approach to topological-feature portfolio allocation

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,828) ·
researched 2026-10-30

| | |
|---|---|
| Task | Topological-feature portfolio allocation |
| Method | Conformal prediction intervals |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The task is defined by topological features, which have no out-of-sample evidence (RK262); the method word does not change that. |
| Implemented in volatility-ai | Persistence diagrams and landscapes are research code (`topology`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK262, RK265, RK269 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Conformal Scholarly
Topological Betti Allocator Ref-322") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Derive persistent-homology or Betti-number features from asset
relationships and test whether they improve allocation beyond simpler
baselines. The conformal version wraps a forecast in distribution-free
prediction intervals and acts only when the interval is decisive. I
found no study of this method on this task.

## The CSV's description

Proposed conformal-prediction-based approach to topological-feature
portfolio allocation: Derive persistent-homology or Betti-number
features from market/asset relationships and test whether they improve
allocation or risk control beyond simpler baselines. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Gidea & Katz (2018), "Topological data analysis of financial time
  series: Landscapes of crashes," *Physica A* 491, 820–834:**
  persistence landscapes of index returns rose before the 2000 and 2008
  crashes, shown in sample (see RK262). (Abstract.)

## Against, and failure modes

* The best-known topological crash signal is in sample, and the ledger's
  TDA entries found no out-of-sample evidence.
* Conformal intervals measure a forecast's uncertainty; they do not
  create a forecast where none exists.

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
| 3828 | Conformal Scholarly Topological Betti Allocator Ref-322 | Robust optimization / Distributionally robust CVaR / Index tracking | 8262 | 11309 | No |
| 3914 | Conformal Scholarly Topological Betti Allocator Ref-802 | Robust optimization / Distributionally robust CVaR / Index tracking | 8303 | 11330 | No |
| 5066 | Conformal Scholarly Topological Betti Allocator Eng-242 | Robust optimization / Distributionally robust CVaR / Index tracking | 5068 | 4488 | No |
| 5152 | Conformal Scholarly Topological Betti Allocator Eng-722 | Robust optimization / Distributionally robust CVaR / Index tracking | 5093 | 4581 | No |
| 5238 | Conformal Scholarly Topological Betti Allocator Eng-1202 | Robust optimization / Distributionally robust CVaR / Index tracking | 5118 | 4674 | No |
| 5324 | Conformal Scholarly Topological Betti Allocator Eng-1682 | Robust optimization / Distributionally robust CVaR / Index tracking | 5143 | 4767 | No |
| 5410 | Conformal Scholarly Topological Betti Allocator Eng-2162 | Robust optimization / Distributionally robust CVaR / Index tracking | 5168 | 4860 | No |
| 5496 | Conformal Scholarly Topological Betti Allocator Eng-2642 | Robust optimization / Distributionally robust CVaR / Index tracking | 5193 | 4953 | No |
| 5582 | Conformal Scholarly Topological Betti Allocator Eng-3122 | Robust optimization / Distributionally robust CVaR / Index tracking | 5218 | 5046 | No |
| 5668 | Conformal Scholarly Topological Betti Allocator Eng-3602 | Robust optimization / Distributionally robust CVaR / Index tracking | 5243 | 5139 | No |
| 5754 | Conformal Scholarly Topological Betti Allocator Eng-4082 | Robust optimization / Distributionally robust CVaR / Index tracking | 5268 | 5232 | No |
| 5840 | Conformal Scholarly Topological Betti Allocator Eng-4562 | Robust optimization / Distributionally robust CVaR / Index tracking | 5293 | 5325 | No |
| 5926 | Conformal Scholarly Topological Betti Allocator Eng-5042 | Robust optimization / Distributionally robust CVaR / Index tracking | 5318 | 5418 | No |
| 6012 | Conformal Scholarly Topological Betti Allocator Eng-5522 | Robust optimization / Distributionally robust CVaR / Index tracking | 5343 | 5511 | No |
| 6189 | Conformal Scholarly Topological Betti Allocator Ref-34 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6493 | 3019 | No |
| 6235 | Conformal Scholarly Topological Betti Allocator Ref-514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6536 | 3136 | No |
| 6281 | Conformal Scholarly Topological Betti Allocator Ref-994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6579 | 3253 | No |
| 6869 | Conformal Scholarly Topological Betti Allocator Eng-434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5507 | 8952 | No |
| 6915 | Conformal Scholarly Topological Betti Allocator Eng-914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5515 | 8987 | No |
| 6961 | Conformal Scholarly Topological Betti Allocator Eng-1394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5523 | 9022 | No |
| 7007 | Conformal Scholarly Topological Betti Allocator Eng-1874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5531 | 9057 | No |
| 7053 | Conformal Scholarly Topological Betti Allocator Eng-2354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5539 | 9092 | No |
| 7099 | Conformal Scholarly Topological Betti Allocator Eng-2834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5547 | 9127 | No |
| 7145 | Conformal Scholarly Topological Betti Allocator Eng-3314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5555 | 9162 | No |
| 7191 | Conformal Scholarly Topological Betti Allocator Eng-3794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5563 | 9197 | No |
| 7237 | Conformal Scholarly Topological Betti Allocator Eng-4274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5571 | 9232 | No |
| 7283 | Conformal Scholarly Topological Betti Allocator Eng-4754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5579 | 9267 | No |
| 7329 | Conformal Scholarly Topological Betti Allocator Eng-5234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5587 | 9302 | No |
| 7375 | Conformal Scholarly Topological Betti Allocator Eng-5714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5595 | 9337 | No |
| 8727 | Conformal Scholarly Topological Betti Allocator Ref-130 | Neural operators / Deep operator networks / ETF rotation | 7636 | 3042 | No |
| 8765 | Conformal Scholarly Topological Betti Allocator Ref-226 | Quantum machine learning / Variational circuits / Index prediction | 11297 | 5970 | No |
| 8841 | Conformal Scholarly Topological Betti Allocator Ref-418 | Attention networks / Transformer encoders / Stock alpha generation | 3223 | 3115 | No |
| 8918 | Conformal Scholarly Topological Betti Allocator Ref-610 | Neural operators / Deep operator networks / ETF rotation | 7644 | 3159 | No |
| 8956 | Conformal Scholarly Topological Betti Allocator Ref-706 | Quantum machine learning / Variational circuits / Index prediction | 11322 | 5990 | No |
| 9032 | Conformal Scholarly Topological Betti Allocator Ref-898 | Attention networks / Transformer encoders / Stock alpha generation | 3239 | 3232 | No |
| 11463 | Conformal Scholarly Topological Betti Allocator Eng-50 | Neural operators / Deep operator networks / ETF rotation | 9531 | 7981 | No |
| 11503 | Conformal Scholarly Topological Betti Allocator Eng-146 | Quantum machine learning / Variational circuits / Index prediction | 14099 | 14100 | No |
| 11575 | Conformal Scholarly Topological Betti Allocator Eng-338 | Attention networks / Transformer encoders / Stock alpha generation | 12981 | 12226 | No |
| 11654 | Conformal Scholarly Topological Betti Allocator Eng-530 | Neural operators / Deep operator networks / ETF rotation | 9547 | 8013 | No |
| 11694 | Conformal Scholarly Topological Betti Allocator Eng-626 | Quantum machine learning / Variational circuits / Index prediction | 14107 | 14108 | No |
| 11766 | Conformal Scholarly Topological Betti Allocator Eng-818 | Attention networks / Transformer encoders / Stock alpha generation | 12991 | 12249 | No |
| 11845 | Conformal Scholarly Topological Betti Allocator Eng-1010 | Neural operators / Deep operator networks / ETF rotation | 9563 | 8045 | No |
| 11885 | Conformal Scholarly Topological Betti Allocator Eng-1106 | Quantum machine learning / Variational circuits / Index prediction | 14115 | 14116 | No |
| 11957 | Conformal Scholarly Topological Betti Allocator Eng-1298 | Attention networks / Transformer encoders / Stock alpha generation | 13001 | 12272 | No |
| 12036 | Conformal Scholarly Topological Betti Allocator Eng-1490 | Neural operators / Deep operator networks / ETF rotation | 9579 | 8077 | No |
| 12076 | Conformal Scholarly Topological Betti Allocator Eng-1586 | Quantum machine learning / Variational circuits / Index prediction | 14123 | 14124 | No |
| 12148 | Conformal Scholarly Topological Betti Allocator Eng-1778 | Attention networks / Transformer encoders / Stock alpha generation | 13011 | 12295 | No |
| 12227 | Conformal Scholarly Topological Betti Allocator Eng-1970 | Neural operators / Deep operator networks / ETF rotation | 9595 | 8109 | No |
| 12267 | Conformal Scholarly Topological Betti Allocator Eng-2066 | Quantum machine learning / Variational circuits / Index prediction | 14131 | 14132 | No |
| 12339 | Conformal Scholarly Topological Betti Allocator Eng-2258 | Attention networks / Transformer encoders / Stock alpha generation | 13021 | 12318 | No |
| 12418 | Conformal Scholarly Topological Betti Allocator Eng-2450 | Neural operators / Deep operator networks / ETF rotation | 9611 | 8141 | No |
| 12458 | Conformal Scholarly Topological Betti Allocator Eng-2546 | Quantum machine learning / Variational circuits / Index prediction | 14139 | 14140 | No |
| 12530 | Conformal Scholarly Topological Betti Allocator Eng-2738 | Attention networks / Transformer encoders / Stock alpha generation | 13031 | 12341 | No |
| 12609 | Conformal Scholarly Topological Betti Allocator Eng-2930 | Neural operators / Deep operator networks / ETF rotation | 9627 | 8173 | No |
| 12649 | Conformal Scholarly Topological Betti Allocator Eng-3026 | Quantum machine learning / Variational circuits / Index prediction | 14147 | 14148 | No |
| 12721 | Conformal Scholarly Topological Betti Allocator Eng-3218 | Attention networks / Transformer encoders / Stock alpha generation | 13041 | 12364 | No |
| 12800 | Conformal Scholarly Topological Betti Allocator Eng-3410 | Neural operators / Deep operator networks / ETF rotation | 9643 | 8205 | No |
| 12840 | Conformal Scholarly Topological Betti Allocator Eng-3506 | Quantum machine learning / Variational circuits / Index prediction | 14155 | 14156 | No |
| 12912 | Conformal Scholarly Topological Betti Allocator Eng-3698 | Attention networks / Transformer encoders / Stock alpha generation | 13051 | 12387 | No |
| 12991 | Conformal Scholarly Topological Betti Allocator Eng-3890 | Neural operators / Deep operator networks / ETF rotation | 9659 | 8237 | No |
| 13031 | Conformal Scholarly Topological Betti Allocator Eng-3986 | Quantum machine learning / Variational circuits / Index prediction | 14163 | 14164 | No |
| 13103 | Conformal Scholarly Topological Betti Allocator Eng-4178 | Attention networks / Transformer encoders / Stock alpha generation | 13061 | 12410 | No |
| 13182 | Conformal Scholarly Topological Betti Allocator Eng-4370 | Neural operators / Deep operator networks / ETF rotation | 9675 | 8269 | No |
| 13222 | Conformal Scholarly Topological Betti Allocator Eng-4466 | Quantum machine learning / Variational circuits / Index prediction | 14171 | 14172 | No |
| 13294 | Conformal Scholarly Topological Betti Allocator Eng-4658 | Attention networks / Transformer encoders / Stock alpha generation | 13071 | 12433 | No |
| 13373 | Conformal Scholarly Topological Betti Allocator Eng-4850 | Neural operators / Deep operator networks / ETF rotation | 9691 | 8301 | No |
| 13413 | Conformal Scholarly Topological Betti Allocator Eng-4946 | Quantum machine learning / Variational circuits / Index prediction | 14179 | 14180 | No |
| 13485 | Conformal Scholarly Topological Betti Allocator Eng-5138 | Attention networks / Transformer encoders / Stock alpha generation | 13081 | 12456 | No |
| 13564 | Conformal Scholarly Topological Betti Allocator Eng-5330 | Neural operators / Deep operator networks / ETF rotation | 9707 | 8333 | No |
| 13604 | Conformal Scholarly Topological Betti Allocator Eng-5426 | Quantum machine learning / Variational circuits / Index prediction | 14187 | 14188 | No |
| 13676 | Conformal Scholarly Topological Betti Allocator Eng-5618 | Attention networks / Transformer encoders / Stock alpha generation | 13091 | 12479 | No |
| 13755 | Conformal Scholarly Topological Betti Allocator Eng-5810 | Neural operators / Deep operator networks / ETF rotation | 9723 | 8365 | No |
| 13795 | Conformal Scholarly Topological Betti Allocator Eng-5906 | Quantum machine learning / Variational circuits / Index prediction | 14195 | 14196 | No |
