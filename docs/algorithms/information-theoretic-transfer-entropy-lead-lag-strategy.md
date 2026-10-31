# Information-Theoretic Transfer Entropy Lead-Lag Strategy

**Ledger ID RK221** · rank 221 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Information theory / Cross-asset lead-lag |
| Potential effectiveness rank | 221 (1 = strongest) |
| AI implementability rank | 374 (1 = easiest) |
| Retail advantage rank | 6,477 (1 = strongest) |
| Fit with this project | ⏳ as a measurement (lead-lag) · ⛔ as a trade (no evidence) |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk221_transfer_entropy`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=transfer_entropy`, component `TransferEntropyGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** in `research.catalog.information`: `te_lead_lag_positions`, `transfer_entropy`; tested on synthetic data, not wired into the engine. The linear and Hayashi–Yoshida lead-lag estimators exist (RK204). |
| Related ledger entries | RK204, RK257, RK264 |

## In one paragraph

Transfer entropy measures how much knowing X's past reduces uncertainty
about Y's next move beyond Y's own past, capturing nonlinear and
directional information flow. It is used to measure information flows
between markets (CDS and bonds, VIX and credit indices). I found no
study of trading on transfer-entropy lead-lag signals, which would face
the same spread problem as linear lead-lag (RK204).

## The rule

```text
TE(X -> Y) = sum p(y_(t+1), y_t^k, x_t^l) log [ p(y_(t+1) | y_t^k, x_t^l) / p(y_(t+1) | y_t^k) ]   # on discretised returns
significance by surrogate (shuffled) series; direction = sign(TE(X->Y) - TE(Y->X))
```

## Evidence

* **Dimpfl & Peter (2013), "Using transfer entropy to measure
  information flows between financial markets," *Studies in Nonlinear
  Dynamics & Econometrics* 17(1), 85–102:** model-free information flow
  between CDS and bond markets and between VIX and iTraxx, before,
  during and after the 2008 crisis. A measurement study, not a trading
  test. (Abstract.)
* **Schreiber (2000):** the measure. (Standard reference.)
* **No trading study found.**

## Against, and failure modes

* Needs long samples and discretisation choices; significance testing is
  costly.
* Any lead it finds is subject to RK204's spread problem.

## Fit with volatility-ai

A measurement tool for asking whether Nasdaq-100 futures or QQQ lead
TQQQ nonlinearly; the linear estimators in RK204 should come first.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Schreiber, T. (2000). "Measuring Information Transfer." *Physical
  Review Letters* 85(2). Standard reference.
* Dimpfl, T., Peter, F. J. (2013). *Studies in Nonlinear Dynamics &
  Econometrics* 17(1), 85–102. Abstract.
