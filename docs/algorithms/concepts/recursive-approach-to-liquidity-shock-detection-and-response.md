# Recursive approach to liquidity-shock detection and response

**Concept page** · shared by **7** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,487) ·
researched 2026-10-30

| | |
|---|---|
| Task | Liquidity-shock detection and response |
| Method | Recursive (online) estimation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Recursive estimation could drive a buy gate, but no study shows it beating the simple spread and volume gates already built (RK244, RK247); background. |
| Implemented in volatility-ai | A VPIN measure is research code (`microstructure.vpin`, RK247); spread-aware limit pricing is in the engine (RK244); Amihud illiquidity is research code (RK59). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK247, RK244, RK59 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Recursive Scholarly
Liquidity Shock Deflector Alpha-30") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate when spreads, depth or order-flow intensity may deteriorate and
adapt trade size, timing or order placement. The recursive version
updates its estimates one observation at a time (recursive least
squares, Kalman-style updates). I found no study of this method on this
task.

## The CSV's description

Proposed recursive approach to liquidity-shock detection and response:
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
* A recursive estimate needs a forgetting rate: too slow lags, too fast
  is noise.

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
| 8487 | Recursive Scholarly Liquidity Shock Deflector Alpha-30 | Neural operators / Fourier layers / ETF rotation | 2036 | 2136 | No |
| 8527 | Recursive Scholarly Liquidity Shock Deflector Alpha-130 | Neural operators / Fourier layers / ETF rotation | 3195 | 2926 | No |
| 8567 | Recursive Scholarly Liquidity Shock Deflector Alpha-230 | Neural operators / Fourier layers / ETF rotation | 4620 | 7578 | No |
| 8607 | Recursive Scholarly Liquidity Shock Deflector Alpha-330 | Neural operators / Fourier layers / ETF rotation | 2037 | 2144 | No |
| 8647 | Recursive Scholarly Liquidity Shock Deflector Alpha-430 | Neural operators / Fourier layers / ETF rotation | 3206 | 2994 | No |
| 13840 | Recursive Scholarly Liquidity Shock Detector Ver-76 | Koopman operator / Model predictive control / ETF execution | 3828 | 2867 | No |
| 13844 | Recursive Scholarly Liquidity Shock Detector Ver-176 | Koopman operator / Model predictive control / ETF execution | 12061 | 13693 | No |
