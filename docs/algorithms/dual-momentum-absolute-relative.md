# Dual Momentum (Absolute + Relative)

**Ledger ID RK3** · rank 3 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / allocation |
| Potential effectiveness rank | 3 (1 = strongest) |
| AI implementability rank | 24 (1 = easiest) |
| Retail advantage rank | 2 (1 = strongest) |
| Fit with this project | 🧪 fits as published (long-only, cash or bonds as the defensive asset) |
| Implemented in volatility-ai | **Yes**, as a harness mode: `python -m tools.rotation --mode relative_strength` ([`tools/rotation.py`](../../tools/rotation.py), ledger X3). It differs from the published rule in four ways (below) and has never been run on real data. |
| Related ledger entries | X3, X2 (defensive rotation), C-E2 (Faber TAA), A5 (HRP), RK1 (absolute momentum is long-or-cash TSMOM) |

## In one paragraph

Each month, rank a few assets by their trailing 12-month return and hold
the leader (**relative momentum**), but only if the leader has also beaten
T-bills over the same window (**absolute momentum**); otherwise hold the
safe asset. Gary Antonacci's argument is that the two filters do
different jobs: relative momentum picks where the return is, absolute
momentum is what cuts volatility and drawdown. It is the only one of the
top three ranked algorithms that fits this project's constraints as
published, which is why its retail-advantage rank (2) is so high: it
needs no shorting, no futures and one trade a month at most. The
repository already has a version of it; the version differs from the
published rule enough that it should be run both ways.

## The rule

### Global Equities Momentum (GEM), the reference form

Antonacci's best-known model, from *Dual Momentum Investing* (2014):

```
once a month, on total-return indices:
    if R12(S&P 500) > R12(T-bills):                    # absolute momentum
        hold argmax(R12(S&P 500), R12(MSCI ACWI ex-US)) # relative momentum
    else:
        hold US aggregate bonds                          # the safe asset
```

`R12` is the trailing 12-month total return. Four parameters: the
universe (two equity indices), the safe asset (aggregate bonds), the
hurdle (T-bills) and the lookback (12 months). The 1974–2013 backtest in
the book used the MSCI World ex-US index before ACWI ex-US existed and,
per secondary reviews, deducted no transaction costs.

### The general form

```
candidates  = risky assets A_1 .. A_n
best        = argmax_i R_k(A_i)                      # relative momentum, lookback k
hold        = best   if R_k(best) > R_k(T-bills)     # absolute momentum
              safe   otherwise                       # bonds, T-bills or cash
rebalance   = monthly, at month end, act next session
```

### What volatility-ai has (ledger X3)

`assign_relative_strength` in `tools/rotation.py`:

```python
rs = (closes / closes.shift(days) - 1.0).shift(1)  # through the PREVIOUS session
best = row.idxmax()
out[day] = best if row[best] > 0 else CASH  # absolute momentum against zero
```

| | GEM | X3 as built |
|---|---|---|
| Universe | S&P 500, ACWI ex-US | `--universe`, default QQQ RSP XLP USMV (the lead TQQQ is not in it) |
| Lookback | 12 months | `--rs-days`, default **63 sessions (~3 months)** |
| Hurdle | T-bills over the same window | **zero** |
| Safe asset | aggregate bonds | cash at the engine's cash yield (≈ T-bills) |
| Rebalance | monthly | **every session** (with the lagged return) |
| What is held | the index | **the champion grid** in that ETF, step and target scaled by its warm-up range; a sleeve is liquidated when rotated out (`allow_signal_exit`) |

The last two rows matter most. Daily reassignment can switch far more
often than monthly, and each switch is a regime exit that may sell lots
below cost. Holding a grid rather than the index also means the book
earns the grid's harvest, not the index's trend, while it is held.

## Evidence for

* **Antonacci (2012, published 2017)**, "Risk Premia Harvesting Through
  Dual Momentum": relative strength first, then absolute momentum against
  T-bills as both a hurdle and the alternative investment; absolute
  momentum "does far more to lessen volatility and drawdown", and the
  combination gives the best results. (Abstract.) A Quantpedia summary
  lists 1974–2011, about 15% a year at about 14% volatility.
* **Antonacci (2013)**, "Absolute Momentum": the single parameter is the
  lookback; absolute momentum identifies regime change and works as an
  overlay on stocks, bonds, real assets, 60/40 and risk parity. (Abstract.)
* **Relative momentum** across assets and sectors is the
  long-documented cross-sectional effect (Jegadeesh & Titman 1993 for
  stocks); **absolute momentum** is RK1's time-series effect. Dual
  momentum is the long-only intersection of the two.
* Antonacci's own site reports GEM about 4.4 points a year above the
  S&P 500 from 1950, with the warning to judge it only over a full bull
  and bear cycle.

## Evidence against

* **Post-publication decay.** A practitioner replication with ETFs (SPY,
  VEU, AGG) reports a marked drop after publication and attributes it to
  selection bias and regime change (Price Action Lab). One replication is
  not a verdict, but the original record is a backtest chosen with
  hindsight of the period it covers.
* **The parameters are arbitrary, and that risk is unpaid.** ReSolve's
  review finds GEM attractive in and out of sample since 1950 but that
  the alternative specifications (lookbacks, universes) are
  statistically indistinguishable from each other, so picking one is an
  *uncompensated* risk; outcomes differ a lot by specification.
* **Whipsaw.** A monthly 12-month signal still flips back and forth in
  sideways markets; each round trip costs the move between the top and
  the signal, twice.
* **Momentum crashes.** Relative momentum fails in rebounds after panics
  (Daniel & Moskowitz 2016), the same V-shape that hurts RK1.

## Failure modes

1. **The safe asset is not safe.** GEM's bonds fell with stocks in 2022
   (this repository's X5 rejects TLT as a hedge for that reason). Cash
   at the T-bill rate, which X3 uses, avoids it.
2. **A narrow universe concentrates the bet.** With QQQ in the universe
   the rotation will usually hold QQQ in a Nasdaq-led bull market; the
   rotation then adds value only at the turns.
3. **Signal lag on a leveraged lead.** If TQQQ were in the universe, its
   volatility drag (RK2) would make its trailing return understate the
   Nasdaq-100's, biasing the ranking against it in volatile years.
4. **Day-of-month luck.** A monthly rule's result depends on which day it
   trades; with few switches the difference between rebalance days can
   be large. Running every trading day of the month and averaging is the
   usual control.

## Fit with volatility-ai

Fits the constraints as published: long-only ETFs, no shorts, no
derivatives, cash or bonds as the defensive holding. Under the loss
policy a rotation out of an asset is a regime exit (`lots_to_liquidate`
with `allow_signal_exit`), which `tools/rotation.py` already sets. The
correction objective is served by the absolute-momentum leg, which moves
the book to cash after the trailing return turns negative, and is paid
for, like RK1, with a lag.

Related evidence in this repository, none of it a test of dual momentum
itself:

* Direction regimes gating the TQQQ grid measured poorly
  ([ultimate-algorithm.md](../research/ultimate-algorithm.md), L1), and
  TSMOM-type filters on RSP and QQQ reached Calmar 0.23–0.47 against
  RSP buy-and-hold's 0.31 ([ultimate-rsp.md](../research/ultimate-rsp.md),
  A1). Absolute momentum is that filter.
* Defensives fell with the market in March 2020, which is why X2 checks
  each defensive's own NATR regime before holding it; the same check
  could gate X3's choice.

## How to test it here

1. **Run X3 as built**, then **as published**. The harness needs two
   small options to express GEM: a monthly rebalance (assign on the
   first session of each month, hold for the month) and a T-bill hurdle
   (the cash-yield series over the same window, instead of zero).
   ```bash
   # as built: daily, 63 sessions, zero hurdle
   python -m tools.rotation --mode relative_strength
   # nearer GEM (lookback only; monthly rebalance and the hurdle need code)
   python -m tools.rotation --mode relative_strength --rs-days 252
   python -m tools.rotation --mode relative_strength --rs-days 252 \
       --universe QQQ RSP EFA                       # if EFA is ingested
   ```
   The harness prints the switch count; compare it with the regime
   step-down's flip counts, because every switch liquidates a sleeve.
2. **Lookbacks 63 / 126 / 252 and universes fixed in advance**, scored as
   a family with the deflated Sharpe ratio and PBO (C-ML4), per ReSolve's
   point that the choice among them is unpaid risk.
3. **Index-held control.** Run the same assignment holding each ETF
   outright (no grid) to separate the rotation's value from the grid's.
4. **Correction windows.** Score on the Ultimate scoreboard's 13 QQQ
   corrections of 10% or more, alongside CAGR, max drawdown and
   calendar years, against the champion and the NATR step-down (N7).

## Open questions

* Hold the grid or the index while an asset is selected? The grid's lots
  carry their own drawdown into each switch.
* Is a 12-month lookback too slow for a book whose lead is a 3× fund?
  The Ultimate design moved to a volatility regime for speed; a dual
  momentum *on top of* that regime (rotate only while turbulent) is the
  X2 shape with a momentum choice, and may be the better test.
* Should TQQQ itself be a candidate, with its ranking computed on QQQ's
  return (ledger L15) to avoid the drag bias?

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Antonacci, G. (2012). "Risk Premia Harvesting Through Dual Momentum."
  SSRN 2042750; *Journal of Management & Entrepreneurship* 11(1), 2017.
  Abstract and summaries.
* Antonacci, G. (2014). *Dual Momentum Investing: An Innovative Strategy
  for Higher Returns with Lower Risk.* McGraw-Hill. Reviews and
  descriptions of GEM.
* Antonacci, G. (2013). "Absolute Momentum: A Simple Rule-Based Strategy
  and Universal Trend-Following Overlay." SSRN 2244633. Abstract.
* ReSolve Asset Management (2019). "Global Equity Momentum: A Craftsman's
  Perspective." Advisor Perspectives, 2019-05-06.
  <https://www.advisorperspectives.com/articles/2019/05/06/global-equity-momentum-a-craftsmans-perspective>.
  Summary.
* Price Action Lab, post-publication analysis of GEM.
  <https://www.priceactionlab.com/Blog/?p=68274>. Summary.
* Jegadeesh, N., Titman, S. (1993). "Returns to Buying Winners and
  Selling Losers." *Journal of Finance* 48(1), 65–91.
* Daniel, K., Moskowitz, T. (2016). "Momentum Crashes." *Journal of
  Financial Economics* 122(2), 221–247.
  <https://www.nber.org/papers/w20439>. Abstract.
* Moskowitz, T., Ooi, Y. H., Pedersen, L. H. (2012). "Time Series
  Momentum." *Journal of Financial Economics* 104(2), 228–250 (the
  absolute leg; see RK1).
* The CSV's own references for this row:
  <https://www.quantconnect.com/docs/v2/writing-algorithms/strategy-library>,
  <https://github.com/polakowo/vectorbt>.
