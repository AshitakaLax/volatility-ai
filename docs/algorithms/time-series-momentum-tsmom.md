# Time-Series Momentum (TSMOM)

**Ledger ID RK1** · rank 1 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / momentum |
| Potential effectiveness rank | 1 (1 = strongest) |
| AI implementability rank | 10 (1 = easiest) |
| Retail advantage rank | 28 (1 = strongest) |
| Fit with this project | ⛔ as published (short side, futures) · ⏳ as a long-or-cash regime |
| Implemented in volatility-ai | **Research code**: the published long/short form is [`research/catalog/trend_following.py:tsmom_weights`](../../research/catalog/trend_following.py) (ledger X7). No long-or-cash TSMOM regime exists yet. |
| Related ledger entries | X7 (managed-futures sleeve), X3 (relative-strength rotation, whose cash rule is absolute momentum), V16 / Q1 / Q3 / Q5 / Q8 (trend regimes), RK2, RK3 |

## In one paragraph

Hold each asset long when its own return over the past year is
positive and short (or flat) when it is negative, sized so every asset
contributes the same volatility. That is the whole rule. It is the
strategy behind most managed-futures funds, and it has the longest
evidence record of any trend rule: positive in every decade since 1880 in
one study, and positive in most of the worst equity drawdowns of that
century. The two things to know before using it here are that **most of
its published edge comes from the volatility scaling and the short
side**, both of which this project either treats separately (RK2) or
excludes, and that **this repository's own measurements of direction
regimes on TQQQ are poor**. The long-or-cash form is cheap to build and
worth one causal measurement, mainly as a slow re-entry filter rather
than as an on/off switch for the grid.

## The rule

### As published (Moskowitz, Ooi & Pedersen 2012)

For each instrument *s* at the end of month *t*:

1. **Signal.** The sign of its excess return over the past 12 months,
   `sign(r[t-12, t])`. The paper studies lookbacks *k* of 1–48 months
   and holding periods *h* of 1–48 months; *k* = 12, *h* = 1 is the
   headline strategy.
2. **Size.** Position = signal × 40% / σ_t, where σ_t is the ex-ante
   annualised volatility: an exponentially weighted variance of daily
   returns about their exponentially weighted mean, with centre of mass
   δ/(1 − δ) = 60 days, annualised with 261 days. The 40% target makes
   each position's volatility comparable regardless of how volatile the
   instrument is.
3. **Portfolio.** Average the positions across instruments (the paper
   uses 58 liquid futures and forwards: equity indices, currencies,
   commodities and government bonds), rebalance monthly.

The repository already has this rule, as research code (abridged here):

```text
# research/catalog/trend_following.py (ledger X7), abridged
def tsmom_weights(daily_returns, lookback=252, vol_target=0.40, com=60.0, annualize=261):
    past  = (1 + r).rolling(lookback).apply(np.prod) - 1          # trailing 12-month return
    sigma = sqrt(EWM variance about EWM mean, centre of mass 60) * sqrt(261)
    return (sign(past) * vol_target / sigma).shift(1)             # known at t-1
```

### The long-or-cash form ("absolute momentum")

Antonacci's name for the same signal applied without a short side: hold
the asset while its trailing 12-month return beats T-bills', hold T-bills
otherwise ([Antonacci 2013](#references)). This is the only form that
fits this project's constraints, and it is not built. A sketch in the
shape of `research/strategies/trend_regimes.py`:

```python
def tsmom_risk_on(
    daily: pd.DataFrame, lookback: int = 252, hurdle: pd.Series | None = None
) -> pd.Series:
    """Risk-on while the trailing `lookback`-session return beats `hurdle`
    (the T-bill return over the same window; zero if None). Same-session
    flag; risk_on_by_date applies it to the NEXT session."""
    lookback = _count("lookback", lookback)
    close = daily["close"].astype(float)
    past = close / close.shift(lookback) - 1.0
    bar = 0.0 if hurdle is None else hurdle.reindex(past.index).ffill()
    return (past > bar).iloc[lookback:]
```

Registered as a `TREND_METHODS` entry it would become
`--regime tsmom` on `tools/leverage_stepdown.py` and `tools/rotation.py`,
lagged one session like every other regime.

### Variants worth knowing

| Variant | What changes | Source |
|---|---|---|
| Blended horizons | Equal-weight the 1-, 3- and 12-month signals; smoother, fewer whipsaws | Hurst, Ooi & Pedersen 2017 |
| Continuous signal | Replace ±1 with a trend-strength value in [−1, 1]; cuts turnover | Baltas & Kosowski |
| Moving-average crossover | Equivalent in its general form: any linear filter of past prices is a weighted sum of TSMOM signals | Levine & Pedersen 2016 |
| Excess vs total return | MOP use excess returns (over the risk-free rate); the long-or-cash form uses a T-bill hurdle | MOP 2012; Antonacci |
| Turning-point blend | Mix a slow and a fast signal when they disagree, because trend breaks are what hurt | Goulding, Harvey & Mazzoleni 2023; Garg et al. 2024 |

The Levine & Pedersen equivalence matters here: the SMA200 regime
(V16 / catalog R1), MACD (Q1) and Awesome Oscillator (Q5) regimes are
already members of the same family. A TSMOM regime is a different
weighting of past returns, not a new idea.

## Evidence for

* **Moskowitz, Ooi & Pedersen (2012)**, the defining paper. Twelve-month
  time-series momentum is positive for *every one* of the 58 instruments
  studied; returns persist for 1–12 months and partially reverse after
  that; the diversified portfolio earns substantial abnormal returns with
  little exposure to standard factors and **performs best in extreme
  markets**; speculators (per CFTC positions) earn it at hedgers'
  expense. (Abstract.)
* **Hurst, Ooi & Pedersen (2017)**, "A Century of Evidence on
  Trend-Following Investing". Blended 1/3/12-month TSMOM across 67
  markets back to 1880: positive average returns in every decade, low
  correlation to stocks and bonds, and good performance in 8 of the 10
  largest drawdowns of a 60/40 portfolio. (Abstract and publisher
  summary.)
* **Hamill, Rattray & Van Hemert (2016)**, Man Group / Oxford-Man,
  1960–2015: performance strongest in the worst equity *and* bond
  environments; returns positively skewed, more so for faster signals,
  resembling a long straddle. (Publisher summary.)

## Evidence against, and what it means here

* **The volatility scaling does most of the work.** Kim, Tse & Wald
  (2016) re-ran MOP on 55 futures, 1985–2013: without the 40%/σ scaling,
  TSMOM's cumulative return and alpha are statistically
  indistinguishable from buy-and-hold. A summary reports alpha falling
  from 1.27% to 0.41% a month when the scaling is removed. *For this
  project:* the scaling half is RK2 and the existing S4 lever; the
  signal half alone is the weak part.
* **The predictability is weak.** Huang, Li, Wang & Zhou (2020): asset
  by asset there is little return predictability in or out of sample;
  the pooled t-statistic falls below bootstrap critical values, and the
  strategy performs about as well as one built on each asset's
  historical mean, which needs no predictability at all.
* **The crisis alpha needs the short side.** Hamill et al. show that
  stopping the strategy from being long equities or bonds *raises* crisis
  performance; the reverse, forbidding shorts as this project does,
  removes the part that pays in a crash. A long-or-cash TSMOM can only
  step aside, and it steps aside late.
* **Trend breaks.** Goulding, Harvey & Mazzoleni (2023) and Garg et al.
  (2024) attribute the weak post-2008 record of monthly trend following
  to more frequent turning points; Baltas & Kosowski tie it to rising
  co-movement across assets.

## Failure modes

1. **Late exit, late re-entry.** A 12-month signal turns negative well
   into a decline and positive well into a recovery. On a 3× ETF the
   first leg of a correction costs three times as much, so the lag is
   paid at leverage.
2. **Whipsaw near zero.** When the trailing return hovers around the
   hurdle the flag flips repeatedly; under this project's loss policy
   every flip that turns the regime off liquidates the grid's lots,
   realizing losses (ledger N10: debounce exists for this).
3. **V-shaped rebounds.** After a fast crash the signal stays negative
   through the rebound (the March–April 2020 shape). Daniel &
   Moskowitz (2016) document the same "panic state" failure for
   cross-sectional momentum.
4. **Single-instrument concentration.** The published diversification
   (58 markets, four asset classes) is what keeps the Sharpe ratio up.
   One Nasdaq-100 exposure has none of it.

## Fit with volatility-ai

| Constraint (ledger §1) | Published TSMOM | Long-or-cash TSMOM |
|---|---|---|
| Long-only stocks/ETFs | ✗ shorts, futures | ✓ |
| No inverse / managed-futures ETFs | ✗ (X7: DBMF/KMLM run this) | ✓ |
| Loss only through a regime exit | — | ✓ if the flag drives `lots_to_liquidate` with `allow_signal_exit` |
| Objective: return/drawdown in corrections | crisis alpha comes from shorts | can only sidestep, after the lag |

### What this repository has already measured

These are the measurements most relevant to a TSMOM regime on this
data; none tests TSMOM itself on TQQQ.

* **Direction regimes gating the TQQQ grid do poorly.** Causal step-down
  runs, CAGR / max DD: MACD 0.12–0.26, PSAR 0.06–0.17, Heikin-Ashi
  −0.09–0.11, Awesome 0.56–0.63, against 1.30–1.40 for the NATR
  volatility regime ([ultimate-algorithm.md](../research/ultimate-algorithm.md),
  lesson L1: "trend switches liquidate near lows and re-enter near
  highs").
* **TSMOM was screened on RSP and QQQ** in a long/cash shell:
  trend and drawdown filters, TSMOM included, reached Calmar 0.23–0.47
  against buy-and-hold RSP's 0.31; only the volatility-like PLUS_DM and
  ADOSC signals were robust ([ultimate-rsp.md](../research/ultimate-rsp.md),
  experiment A1). The shell is causal (decide at D's close, act at D+1).
  The code for that screen lived in a session scratchpad and is not in
  the repository.
* **A slow trend condition on *re-entry* works.** The Ultimate strategy's
  bear filter (calm re-entry only within 50% of the one-year high, or
  above a long average) lifted Calmar from 1.30 to 1.63–1.75 and turned
  2022 from −10.8% to about flat (ultimate-algorithm.md L12, exp5), but
  most of that benefit is the one 2022 episode.
* plan.md's SMA200 / trend-line results (V16) carry the same-session
  lookahead and are not evidence either way until re-run causally.

The reading: as an *exit* signal for a leveraged grid, a 12-month trend
is too slow and direction regimes have measured badly here; as a
*re-entry permission* on top of the volatility regime it is the kind of
condition that has already helped once.

## How to test it here

1. **Build `tsmom_risk_on`** (the sketch above) in
   `research/strategies/trend_regimes.py`, with tests pinning it to
   `tsmom_weights`' sign on the same closes (lag included), and add
   `"tsmom"` to `TREND_METHODS`.
2. **Step-down comparison**, causal, with and without a minimum hold:
   ```bash
   for r in tsmom sma natr; do
     python -m tools.leverage_stepdown --regime $r
     python -m tools.leverage_stepdown --regime $r --min-hold 5
   done
   ```
   Lookbacks 63 / 126 / 252 sessions, decided before looking at results.
3. **As the Ultimate bear filter**: replace "within 50% of the 250-session
   high" with "250-session return above zero" and compare exp5's rows.
   This is the test most likely to matter.
4. **Score with the overfitting tools** (ledger C-ML4,
   `research/optimization/overfitting.py`): deflated Sharpe and PBO over
   every lookback tried, not just the best.

## Open questions

* Should the hurdle be zero or the T-bill return over the same window?
  The engine's historical cash yield makes the T-bill version possible.
* Is the signal better computed on QQQ (the market, ledger L15) than on
  TQQQ itself? On a 3× fund the volatility drag (RK2) can make the
  trailing return negative while QQQ's is positive.
* Does a blended 1/3/12-month signal change the flip count enough to
  matter under the liquidation cost (N10)?

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T., Ooi, Y. H., Pedersen, L. H. (2012). "Time Series
  Momentum." *Journal of Financial Economics* 104(2), 228–250.
  <https://doi.org/10.1016/j.jfineco.2011.11.003> · SSRN
  <https://papers.ssrn.com/abstract=2089463>. Abstract; the construction
  as transcribed in `research/catalog/trend_following.py`.
* Hurst, B., Ooi, Y. H., Pedersen, L. H. (2017). "A Century of Evidence
  on Trend-Following Investing." *Journal of Portfolio Management*
  44(1). <https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing>.
  Abstract and publisher summary.
* Kim, A. Y., Tse, Y., Wald, J. K. (2016). "Time Series Momentum and
  Volatility Scaling." *Journal of Financial Markets* 30, 103–124.
  <https://doi.org/10.1016/j.finmar.2016.05.003>. Abstract; the alpha
  figures are from a Quantpedia summary.
* Huang, D., Li, J., Wang, L., Zhou, G. (2020). "Time Series Momentum:
  Is It There?" *Journal of Financial Economics* 135(3), 774–794.
  <https://doi.org/10.1016/j.jfineco.2019.08.004>. Abstract.
* Hamill, C., Rattray, S., Van Hemert, O. (2016). "Trend Following:
  Equity and Bond Crisis Alpha." Man Group.
  <https://www.man.com/insights/trend-following-equity-and-bond-crisis-alpha>.
  Publisher summary.
* Levine, A., Pedersen, L. H. (2016). "Which Trend Is Your Friend?"
  *Financial Analysts Journal* 72(3), 51–66.
  <https://ideas.repec.org/a/taf/ufajxx/v72y2016i3p51-66.html>. Abstract.
* Baltas, N., Kosowski, R. "Demystifying Time-Series Momentum
  Strategies: Volatility Estimators, Trading Rules and Pairwise
  Correlations." <https://papers.ssrn.com/abstract=2140091>. Abstract.
* Goulding, C., Harvey, C. R., Mazzoleni, M. (2023). "Momentum Turning
  Points." *Journal of Financial Economics* 149(3), 378–406; Garg, A.,
  Goulding, C., Harvey, C. R., Mazzoleni, M. (2024). "Breaking Bad
  Trends." *Financial Analysts Journal* 80(1), 84–98. Index records.
* Daniel, K., Moskowitz, T. (2016). "Momentum Crashes." *Journal of
  Financial Economics* 122(2), 221–247.
  <https://www.nber.org/papers/w20439>. Abstract.
* Antonacci, G. (2013). "Absolute Momentum: A Simple Rule-Based Strategy
  and Universal Trend-Following Overlay." SSRN 2244633. Abstract.
* The CSV's own references for this row:
  <https://doi.org/10.1016/j.jfineco.2011.11.003>,
  <https://www.quantconnect.com/docs/v2/writing-algorithms/strategy-library>.
