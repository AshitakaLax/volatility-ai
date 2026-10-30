# Diffusion-model-based approach to macro-driven index allocation

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,813) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven index allocation |
| Method | Diffusion generative models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of diffusion models extracting a usable signal from macro data, where even simple predictors fail out of sample. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Diffusion Scholarly
Macro-Driven Index Allocator Ref-242") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The
diffusion-model version trains a denoising generative model and samples
scenarios or forecasts from it. I found no study of this method on this
task.

## The CSV's description

Proposed diffusion-model-based approach to macro-driven index
allocation: Use macroeconomic and market indicators to adjust
allocations among index-linked assets, with explicit publication lags
and rebalance rules needed to prevent look-ahead bias. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Welch & Goyal (2008), "A Comprehensive Look at the Empirical
  Performance of Equity Premium Prediction," *Review of Financial
  Studies* 21(4), 1455–1508:** the standard macro and valuation
  predictors of the equity premium performed poorly out of sample.
  (Standard reference.)
* **Rapach, Strauss & Zhou (2010), *Review of Financial Studies* 23(2),
  821–862:** combining the individual predictors' forecasts gives small
  but consistent out-of-sample gains, linked to the business cycle.
  (Abstract.)

## Against, and failure modes

* Macro data are monthly or quarterly, revised and published with lags;
  a few decades give few independent observations.
* Each predictor alone has failed out of sample (Welch & Goyal); gains
  come only from combining many, and they are small.
* Generative models trained on a few thousand days memorise more than
  they generalise; no trading evidence found.

## Fit with volatility-ai

The warehouse already holds macro series, shifted by their publication
lag before the as-of join (`engine/warehouse/queries.py`), so a macro
input is possible. The evidence says expect little; a macro signal would
be one more regime input, tested against the NATR exit like any other.
The inflation-regime rotation (RK41) is the researched candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Welch, I., Goyal, A. (2008). *Review of Financial Studies* 21(4),
  1455–1508. Standard reference.
* Rapach, D. E., Strauss, J. K., Zhou, G. (2010). *Review of Financial
  Studies* 23(2), 821–862. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3813 | Diffusion Scholarly Macro-Driven Index Allocator Ref-242 | Robust optimization / Distributionally robust CVaR / Index tracking | 4659 | 3069 | No |
| 3899 | Diffusion Scholarly Macro-Driven Index Allocator Ref-722 | Robust optimization / Distributionally robust CVaR / Index tracking | 4686 | 3186 | No |
| 5080 | Diffusion Scholarly Macro-Driven Index Allocator Eng-322 | Robust optimization / Distributionally robust CVaR / Index tracking | 8830 | 11504 | No |
| 5166 | Diffusion Scholarly Macro-Driven Index Allocator Eng-802 | Robust optimization / Distributionally robust CVaR / Index tracking | 8866 | 11518 | No |
| 5252 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1282 | Robust optimization / Distributionally robust CVaR / Index tracking | 8902 | 11532 | No |
| 5338 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1762 | Robust optimization / Distributionally robust CVaR / Index tracking | 8938 | 11546 | No |
| 5424 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2242 | Robust optimization / Distributionally robust CVaR / Index tracking | 8974 | 11560 | No |
| 5510 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2722 | Robust optimization / Distributionally robust CVaR / Index tracking | 9010 | 11574 | No |
| 5596 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3202 | Robust optimization / Distributionally robust CVaR / Index tracking | 9046 | 11588 | No |
| 5682 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3682 | Robust optimization / Distributionally robust CVaR / Index tracking | 9082 | 11602 | No |
| 5768 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4162 | Robust optimization / Distributionally robust CVaR / Index tracking | 9118 | 11616 | No |
| 5854 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4642 | Robust optimization / Distributionally robust CVaR / Index tracking | 9154 | 11630 | No |
| 5940 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5122 | Robust optimization / Distributionally robust CVaR / Index tracking | 9190 | 11644 | No |
| 6026 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5602 | Robust optimization / Distributionally robust CVaR / Index tracking | 9226 | 11658 | No |
| 6229 | Diffusion Scholarly Macro-Driven Index Allocator Ref-434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5394 | 8443 | No |
| 6275 | Diffusion Scholarly Macro-Driven Index Allocator Ref-914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5398 | 8463 | No |
| 6832 | Diffusion Scholarly Macro-Driven Index Allocator Eng-34 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7097 | 4449 | No |
| 6878 | Diffusion Scholarly Macro-Driven Index Allocator Eng-514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7139 | 4542 | No |
| 6924 | Diffusion Scholarly Macro-Driven Index Allocator Eng-994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7181 | 4635 | No |
| 6970 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7223 | 4728 | No |
| 7016 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7265 | 4821 | No |
| 7062 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7307 | 4914 | No |
| 7108 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7349 | 5007 | No |
| 7154 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7391 | 5100 | No |
| 7200 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7433 | 5193 | No |
| 7246 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7475 | 5286 | No |
| 7292 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7517 | 5379 | No |
| 7338 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7559 | 5472 | No |
| 7384 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7601 | 5565 | No |
| 8697 | Diffusion Scholarly Macro-Driven Index Allocator Ref-50 | Neural operators / Deep operator networks / ETF rotation | 9292 | 7588 | No |
| 8731 | Diffusion Scholarly Macro-Driven Index Allocator Ref-146 | Quantum machine learning / Variational circuits / Index prediction | 13984 | 13983 | No |
| 8808 | Diffusion Scholarly Macro-Driven Index Allocator Ref-338 | Attention networks / Transformer encoders / Stock alpha generation | 12825 | 11889 | No |
| 8888 | Diffusion Scholarly Macro-Driven Index Allocator Ref-530 | Neural operators / Deep operator networks / ETF rotation | 9308 | 7612 | No |
| 8922 | Diffusion Scholarly Macro-Driven Index Allocator Ref-626 | Quantum machine learning / Variational circuits / Index prediction | 13988 | 13991 | No |
| 8999 | Diffusion Scholarly Macro-Driven Index Allocator Ref-818 | Attention networks / Transformer encoders / Stock alpha generation | 12830 | 11912 | No |
| 11496 | Diffusion Scholarly Macro-Driven Index Allocator Eng-130 | Neural operators / Deep operator networks / ETF rotation | 7703 | 4467 | No |
| 11532 | Diffusion Scholarly Macro-Driven Index Allocator Eng-226 | Quantum machine learning / Variational circuits / Index prediction | 11685 | 6220 | No |
| 11610 | Diffusion Scholarly Macro-Driven Index Allocator Eng-418 | Attention networks / Transformer encoders / Stock alpha generation | 3525 | 4527 | No |
| 11687 | Diffusion Scholarly Macro-Driven Index Allocator Eng-610 | Neural operators / Deep operator networks / ETF rotation | 7707 | 4560 | No |
| 11723 | Diffusion Scholarly Macro-Driven Index Allocator Eng-706 | Quantum machine learning / Variational circuits / Index prediction | 11710 | 6241 | No |
| 11801 | Diffusion Scholarly Macro-Driven Index Allocator Eng-898 | Attention networks / Transformer encoders / Stock alpha generation | 3545 | 4620 | No |
| 11878 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1090 | Neural operators / Deep operator networks / ETF rotation | 7711 | 4653 | No |
| 11914 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1186 | Quantum machine learning / Variational circuits / Index prediction | 11735 | 6262 | No |
| 11992 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1378 | Attention networks / Transformer encoders / Stock alpha generation | 3565 | 4713 | No |
| 12069 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1570 | Neural operators / Deep operator networks / ETF rotation | 7715 | 4746 | No |
| 12105 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1666 | Quantum machine learning / Variational circuits / Index prediction | 11760 | 6283 | No |
| 12183 | Diffusion Scholarly Macro-Driven Index Allocator Eng-1858 | Attention networks / Transformer encoders / Stock alpha generation | 3585 | 4806 | No |
| 12260 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2050 | Neural operators / Deep operator networks / ETF rotation | 7719 | 4839 | No |
| 12296 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2146 | Quantum machine learning / Variational circuits / Index prediction | 11785 | 6304 | No |
| 12374 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2338 | Attention networks / Transformer encoders / Stock alpha generation | 3605 | 4899 | No |
| 12451 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2530 | Neural operators / Deep operator networks / ETF rotation | 7723 | 4932 | No |
| 12487 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2626 | Quantum machine learning / Variational circuits / Index prediction | 11810 | 6325 | No |
| 12565 | Diffusion Scholarly Macro-Driven Index Allocator Eng-2818 | Attention networks / Transformer encoders / Stock alpha generation | 3625 | 4992 | No |
| 12642 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3010 | Neural operators / Deep operator networks / ETF rotation | 7727 | 5025 | No |
| 12678 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3106 | Quantum machine learning / Variational circuits / Index prediction | 11835 | 6346 | No |
| 12756 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3298 | Attention networks / Transformer encoders / Stock alpha generation | 3645 | 5085 | No |
| 12833 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3490 | Neural operators / Deep operator networks / ETF rotation | 7731 | 5118 | No |
| 12869 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3586 | Quantum machine learning / Variational circuits / Index prediction | 11860 | 6367 | No |
| 12947 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3778 | Attention networks / Transformer encoders / Stock alpha generation | 3665 | 5178 | No |
| 13024 | Diffusion Scholarly Macro-Driven Index Allocator Eng-3970 | Neural operators / Deep operator networks / ETF rotation | 7735 | 5211 | No |
| 13060 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4066 | Quantum machine learning / Variational circuits / Index prediction | 11885 | 6388 | No |
| 13138 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4258 | Attention networks / Transformer encoders / Stock alpha generation | 3685 | 5271 | No |
| 13215 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4450 | Neural operators / Deep operator networks / ETF rotation | 7739 | 5304 | No |
| 13251 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4546 | Quantum machine learning / Variational circuits / Index prediction | 11910 | 6409 | No |
| 13329 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4738 | Attention networks / Transformer encoders / Stock alpha generation | 3705 | 5364 | No |
| 13406 | Diffusion Scholarly Macro-Driven Index Allocator Eng-4930 | Neural operators / Deep operator networks / ETF rotation | 7743 | 5397 | No |
| 13442 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5026 | Quantum machine learning / Variational circuits / Index prediction | 11935 | 6430 | No |
| 13520 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5218 | Attention networks / Transformer encoders / Stock alpha generation | 3725 | 5457 | No |
| 13597 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5410 | Neural operators / Deep operator networks / ETF rotation | 7747 | 5490 | No |
| 13633 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5506 | Quantum machine learning / Variational circuits / Index prediction | 11960 | 6451 | No |
| 13711 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5698 | Attention networks / Transformer encoders / Stock alpha generation | 3745 | 5550 | No |
| 13788 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5890 | Neural operators / Deep operator networks / ETF rotation | 7751 | 5583 | No |
| 13824 | Diffusion Scholarly Macro-Driven Index Allocator Eng-5986 | Quantum machine learning / Variational circuits / Index prediction | 11985 | 6472 | No |
