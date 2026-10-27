# Volatility-Scaled Trend Following

**Ledger ID RK2** · rank 2 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / risk scaling |
| Potential effectiveness rank | 2 (1 = strongest) |
| AI implementability rank | 26 (1 = easiest) |
| Retail advantage rank | 6 (1 = strongest) |
| Fit with this project | ⛔ as published (long/short futures) · ⏳ as a long-or-cash exposure book · the scaling half is built (S4) |
| Implemented in volatility-ai | **Research code** for the combined rule: [`tsmom_weights`](../../research/catalog/trend_following.py) (40% / σ, ledger X7) and [`pytrendfollow_position`](../../research/catalog/trend_following.py) (Carver's 12.5% target, ledger S2). The scaling alone is wired: `vol_target` on `hf_entry_gated` (S4, [`gated_local_reference_sizing.py`](../../research/strategies/gated_local_reference_sizing.py)) with the estimators of S3. |
| Related ledger entries | S4, S3, V18 (volatility targeting), V7 (vol-ratio lots), C-G3 (volatility-scaled step), X7, S2, RK1 |

## In one paragraph

Take a trend signal (RK1's, or a moving-average crossover) and size the
position by `target volatility / forecast volatility`, so a calm market
gets more exposure and a turbulent one less. The literature on time-series
momentum turns out to be, to a large degree, a literature on this
scaling: remove it and the trend signal's alpha mostly disappears. The
scaling also has an independent case that is unusually strong for
**equities** (the leverage effect: volatility rises when prices fall)
and even stronger for a **3× daily-reset ETF**, whose volatility drag
grows with the square of volatility. This repository already runs the
scaling as a lot-size lever (S4) and found "magnitude persists,
direction is hard" (plan.md). The honest summary is that the half of
this algorithm that fits the project is already here and unmeasured on
TQQQ; the trend half adds little on this data.

## The rule

```
position_t = signal_t × clamp( σ_target / σ̂_{t−1}, min, max )

signal_t   ∈ {+1, 0}        long-or-cash (this project); {+1, −1} as published
σ̂_{t−1}    volatility forecast from data through the previous session
σ_target   chosen once (40% per instrument in MOP; 10–12.5% for a portfolio)
```

| Choice | Published values | In this repository |
|---|---|---|
| Signal | sign of the 12-month return (MOP); EWMAC crossovers 8/32 … 64/256 (Carver) | `tsmom_weights`, `ewmac_forecasts` (research code) |
| Volatility forecast | EWMA variance, centre of mass 60 days (MOP); EWMA std, span 36 (Carver) | S3 estimators: close-to-close, Parkinson, Garman-Klass, Rogers-Satchell, **Yang-Zhang (default)** over N completed sessions |
| Target | 40% per instrument (MOP), 12.5% portfolio (PyTrendFollow template), 10% (Harvey et al.) | `vol_target`, annualised |
| Caps | leverage limits, position rounding (`chunk_trades`) | `vol_target_min` / `vol_target_max` (default 0.25 / 2.0) |
| Rebalance | monthly (MOP), daily with a ~10% buffer (Carver) | per lot (S4); daily for an exposure book |

### Why the scaling matters most for a leveraged ETF

A daily-reset fund with leverage *L* on an index with volatility σ
returns, in logs and ignoring fees and financing,

```
log(F_T / F_0) = L · log(S_T / S_0) − L(L − 1)/2 · ∫ σ_t² dt
```

(Avellaneda & Zhang 2010). For TQQQ, *L* = 3, so the drag is **3σ² per
year**: about 12% a year when the Nasdaq-100 runs at 20% volatility, and
about 37% at 35%. The drag is paid on every day held, and it is
quadratic, so exposure held through high-volatility stretches is
expensive even when the index ends flat. Gayed & Bilello's
"Leverage for the Long Run" (2016) makes the same point empirically:
leverage pays in low-volatility environments, and a moving average is a
usable proxy for them. Volatility scaling is the direct form of that
idea.

## Evidence for

* **The scaling is where TSMOM's alpha is.** Kim, Tse & Wald (2016):
  MOP's large alpha comes from volatility-scaled returns, not from time
  series momentum; unscaled, TSMOM and buy-and-hold have similar
  cumulative returns and alphas.
* **Volatility targeting helps equities specifically.** Harvey, Hoyle,
  Korgaonkar, Rattray, Sargaison & Van Hemert (2018), 60+ assets with
  daily data back to 1926, 10% target, costs included: Sharpe ratios rise
  for risk assets (equities, credit) because of the leverage effect, and
  the frequency of extreme returns falls in **every** asset class, since
  large losses tend to arrive when volatility is already high and the
  position is already smaller.
* **Volatility-managed factors.** Moreira & Muir (2017): scaling monthly
  factor returns by the inverse of last month's realised variance raises
  Sharpe ratios for the market and most equity factors, because
  volatility changes are not matched by proportional changes in expected
  return. Barroso & Santa-Clara (2015): scaling momentum by its own
  forecast volatility nearly doubles its Sharpe ratio and removes most of
  its crashes.
* **Cheaper with a better estimator.** Baltas & Kosowski: better
  volatility estimators and a continuous trend signal cut turnover by
  over a third with no significant loss of performance.

## Evidence against

* **Out of sample it often does not beat the unmanaged portfolio.**
  Cederburg, O'Doherty, Wang & Yan (2020), 103 equity strategies: the
  in-sample spanning-regression alphas replicate, but real-time
  volatility-managed portfolios generally earn *lower* certainty
  equivalents and Sharpe ratios than simply holding the original
  portfolio; the weights the scaling needs are unstable.
* **Forecasts lag jumps.** The CSV's own caveat: volatility estimates lag
  abrupt jumps and do not cap gap losses. A crash that starts from a calm
  market (February 2018, February 2020) arrives at full size.
* **On this repository's data, mixed.** plan.md: volatility targeting on
  RSP cut drawdown 54% (V18), but the edge sat in February–June 2020;
  layered on top of the Ultimate-RSP votes it lowered Calmar in every
  case ([ultimate-rsp.md](../research/ultimate-rsp.md), A4).

## Failure modes

1. **Gap at low volatility.** Maximum exposure is held exactly when the
   forecast is lowest, which is when a surprise does the most damage.
   The `vol_target_max` cap is the guard.
2. **Re-risking too early.** After a spike the forecast decays and
   exposure rises while the decline may still be running. A slow
   estimator, or a trend gate (the "trend" in this algorithm), delays it.
3. **Turnover and costs.** Daily rescaling trades small amounts every
   day; a buffer (trade only when the target moves by more than ~10%,
   `chunk_trades` in PyTrendFollow) is standard.
4. **Estimator error at regime breaks.** Overnight gaps defeat
   range-only estimators; this repository's S3 defaults to Yang-Zhang
   for exactly that reason (in a market whose every move is an overnight
   gap the range estimators read zero).

## Fit with volatility-ai

The algorithm splits cleanly into two halves that fit differently:

| Half | Constraint check | Status here |
|---|---|---|
| Volatility scaling of exposure | A sizing change; it never sells below cost on its own | **Built** for grid lots (S4, unmeasured on TQQQ); V7 scales by a fast/slow *ratio*; C-G3 scales the step instead |
| Trend signal gating the exposure | Long-or-cash only; turning it off is a regime exit | Not built as a TSMOM regime (see RK1); direction regimes measured poorly here (ultimate-algorithm.md L1) |

Two places in the platform could carry the combined rule:

* **The grid (TQQQ).** `hf_entry_gated` with `vol_target` already
  scales buys by `vol_target / realized vol`, clamped. The trend half
  would be a regime sleeve flag (RK1's `tsmom_risk_on`), liquidating on
  the flip under `allow_signal_exit`.
* **An exposure book (QQQ, RSP).** `UltimateRspSizing` already holds a
  daily target fraction of equity and rebalances once per session. A
  target of `1{trend} × min(1, σ_target / σ̂)` is a new target function
  for that machinery, not a new strategy class. With a 100% cap it never
  borrows, so it fits the long-only, no-margin reading of the
  constraints.

## How to test it here

1. **Measure what exists first.** `config/probe_vol_target.yaml`
   (targets 0.45 / 0.60 / 0.75 × 10 / 20 sessions × Yang-Zhang vs
   close-to-close) has never been run:
   ```bash
   python -m research.run_hf_sweep --config config/probe_vol_target.yaml \
       --search grid --intrabar-fill causal --output output/probe_vol_target_causal.csv
   ```
   This is ledger §11 item 5, alongside V11 `dd_throttle`.
2. **Exposure book on QQQ and TQQQ**, causal, daily, 2 bp a side, the
   engine's cash yield: (a) buy-and-hold, (b) vol-scaled only,
   (c) vol-scaled × TSMOM gate, (d) the NATR regime. Report CAGR, max
   drawdown, Calmar and the correction windows the Ultimate scoreboard
   uses (13 QQQ corrections of 10% or more).
3. **Read the drag directly.** For each run, estimate the realized
   `3σ²` drag avoided by the scaling: it is the mechanism this rule is
   supposed to exploit on TQQQ, and it can be checked against
   `research/catalog/excluded.py:daily_reset_path`.
4. **Deflate.** Score every target × window × estimator combination
   with the deflated Sharpe ratio and PBO (C-ML4); Cederburg et al. is
   the warning that the in-sample winner will look better than it is.

## Open questions

* Target on TQQQ's own volatility or on QQQ's (ledger L15 says take the
  regime from the market)? The scaling ratio is the same up to *L*, but
  the drag argument is about the index's σ.
* Should the scaled exposure cap at 1.0 (never more than fully invested)
  or allow the grid's lots to exceed it in calm markets, as S4's
  `vol_target_max` = 2.0 does?
* Is the trend gate worth its flips once the scaling is in place? Kim,
  Tse & Wald suggest the gate's marginal value is small; the RSP result
  (A4) suggests the scaling's is too, on that instrument.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T., Ooi, Y. H., Pedersen, L. H. (2012). "Time Series
  Momentum." *Journal of Financial Economics* 104(2), 228–250.
  <https://doi.org/10.1016/j.jfineco.2011.11.003>. Abstract; the
  construction as transcribed in `research/catalog/trend_following.py`.
* Kim, A. Y., Tse, Y., Wald, J. K. (2016). "Time Series Momentum and
  Volatility Scaling." *Journal of Financial Markets* 30, 103–124.
  <https://doi.org/10.1016/j.finmar.2016.05.003>. Abstract and summaries.
* Harvey, C. R., Hoyle, E., Korgaonkar, R., Rattray, S., Sargaison, M.,
  Van Hemert, O. (2018). "The Impact of Volatility Targeting."
  *Journal of Portfolio Management* 45(1), 14–33.
  <https://doi.org/10.3905/jpm.2018.45.1.014>. Abstract and summaries.
* Moreira, A., Muir, T. (2017). "Volatility-Managed Portfolios."
  *Journal of Finance* 72(4), 1611–1644. NBER w22208
  <https://www.nber.org/papers/w22208>. Abstract.
* Cederburg, S., O'Doherty, M. S., Wang, F., Yan, X. (2020). "On the
  Performance of Volatility-Managed Portfolios." *Journal of Financial
  Economics* 138(1), 95–117.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:138:y:2020:i:1:p:95-117>.
  Abstract and summaries.
* Barroso, P., Santa-Clara, P. (2015). "Momentum Has Its Moments."
  *Journal of Financial Economics* 116(1), 111–120.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:116:y:2015:i:1:p:111-120>.
  Abstract.
* Baltas, N., Kosowski, R. "Demystifying Time-Series Momentum
  Strategies: Volatility Estimators, Trading Rules and Pairwise
  Correlations." <https://papers.ssrn.com/abstract=2140091>. Abstract.
* Avellaneda, M., Zhang, S. (2010). "Path-Dependence of Leveraged ETF
  Returns." *SIAM Journal on Financial Mathematics* 1, 586–603. Abstract
  and the formula as restated in later work.
* Gayed, M., Bilello, C. (2016). "Leverage for the Long Run." Charles H.
  Dow Award paper, CMT Association. Summary (the repository's
  `trend_regimes.sma_risk_on` implements its rule).
* Carver, R. (2015). *Systematic Trading.* Harriman House; as
  implemented in chrism2671/PyTrendFollow (ledger S2).
* The CSV's own references for this row:
  <https://doi.org/10.1016/j.jfineco.2011.11.003>,
  <https://www.quantconnect.com/docs/v2/writing-algorithms/strategy-library>.
