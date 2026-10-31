# Conformally Constrained Risk Parity Portfolio

**Ledger ID RK99** · rank 99 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Conformal prediction / portfolio construction |
| Potential effectiveness rank | 99 (1 = strongest) |
| AI implementability rank | 18 (1 = easiest) |
| Retail advantage rank | 47 (1 = strongest) |
| Fit with this project | ⏳ (an allocator plus a tail constraint) |
| Implemented in volatility-ai | **Yes, as a backtest book.** `research/strategies/allocators.py` `conformal_risk_parity`, run by the portfolio book (`python -m tools.portfolio_book --allocator conformal_risk_parity`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Partial.** Split-conformal intervals and conformal long sizing exist (`position_sizing.split_conformal_interval`, `conformal_long_size`; catalog S5); HRP exists (A5); no ERC and no combination. |
| Related ledger entries | RK61, A5, V13 (catalog S5) |

## In one paragraph

Take an equal-risk-contribution portfolio (RK61) and add a constraint
that a conformal prediction interval for the portfolio's loss stays
below a limit, so the tail bound holds without assuming a distribution.
Each half exists in the literature; I found no published method that
combines them. The CSV's own caveat is the crux: plain conformal
prediction assumes exchangeable data, which returns are not, so it needs
an adaptive variant that updates the coverage level as the distribution
drifts.

## The rule (as the CSV describes it)

```
1. w_ERC from the covariance matrix (RK61)
2. calibration: residuals of a loss forecaster on a held-out window -> conformal quantile q_alpha
3. constraint: forecast loss(w) + q_alpha <= L_max; if violated, scale w toward cash
4. adapt alpha online (adaptive conformal inference) as coverage drifts
```

## Evidence

* **Kato (2024), "Conformal Predictive Portfolio Selection" (arXiv
  2410.16333):** conformal intervals around predicted portfolio returns;
  a rule that maximises the interval's lower bound did best on US and
  Japanese stocks. (Abstract.)
* **Schmitt (2026, arXiv 2602.03903):** regime-weighted conformal
  calibration for nonstationary portfolio VaR, tested on the CRSP US
  equity portfolio. (Abstract.)
* **Adaptive conformal inference** (Gibbs & Candès 2021) is the usual
  fix for distribution shift; not verified from search here.
* **Gap:** no source found combining ERC with conformal tail bounds;
  the rule above is the CSV's construction, not a published method. The
  owner-supplied Gemini answer cites only the foundations (Vovk,
  Gammerman & Shafer 2005, *Algorithmic Learning in a Random World*) and
  states a turnover result without naming a study.

## Against, and failure modes

* Coverage guarantees break under nonstationarity unless the method
  adapts (the CSV's caveat); in a crash the calibration window is stale
  exactly when the bound matters.
* Two layers of estimation (covariance and a loss forecaster).

## Fit with volatility-ai

Long-only weights fit; the conformal code exists for single-position
sizing. As with the other allocators it waits on a multi-instrument
book; the conformal tail check could equally gate the existing
single-instrument grid's total exposure, which is the more practical use.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Kato, M. (2024). "Conformal Predictive Portfolio Selection." arXiv
  2410.16333. <https://ideas.repec.org/p/arx/papers/2410.16333.html>.
  Abstract.
* Schmitt, M. (2026). "Taming Tail Risk in Financial Markets: Conformal
  Risk Control for Nonstationary Portfolio VaR." arXiv 2602.03903.
  Abstract.
* Gibbs, I., Candès, E. (2021). "Adaptive Conformal Inference Under
  Distribution Shift." NeurIPS 2021. Not verified here.
* The CSV's own references: Riskfolio-Lib; MAPIE
  (<https://github.com/mapie-dev/mapie>).
