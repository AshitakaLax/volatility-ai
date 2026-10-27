# Volatility Targeting / Risk Scaling

**Ledger ID RK22** · rank 22 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Risk management |
| Potential effectiveness rank | 22 (1 = strongest) |
| AI implementability rank | 137 (1 = easiest) |
| Retail advantage rank | 123 (1 = strongest) |
| Fit with this project | 🧪 built on the grid (S4); measured on RSP (V18) |
| Implemented in volatility-ai | **Yes.** `vol_target` on `hf_entry_gated` scales each lot by `clamp(vol_target / realized vol, 0.25, 2.0)`, realized vol from completed sessions (Yang-Zhang by default, S3). Probe config `config/probe_vol_target.yaml`; never run on TQQQ. |
| Related ledger entries | S4, S3, V18, V7, RK2, RK54 |

## In one paragraph

Scale exposure so the book's expected volatility stays near a target:
more exposure when markets are calm, less when they are wild. It is the
scaling half of volatility-scaled trend following (RK2), used on its own.
For equities it has a structural reason to work (volatility rises when
prices fall, so smaller positions arrive just before the worst days) and
a structural reason to matter more for TQQQ (daily-reset drag grows with
the square of volatility, about 3σ² a year). It is built here as a
lot-size lever and has one measurement, on RSP, that cut drawdown but
not on its own beat this project's better signals.

## The rule

```
sigma_hat_t = annualised realized volatility over the last N completed sessions (N = 10-60)
exposure_t  = clamp(sigma_target / sigma_hat_t, lo, hi)        # hi <= 1 for an unlevered book
grid form (S4): every new lot's size x exposure_t; existing lots untouched
```

## Evidence

* **Harvey et al. (2018), *JPM* 45(1):** volatility targeting raises
  Sharpe ratios for equities and credit (the leverage effect) and
  reduces extreme returns in every asset class. (Abstract.)
* **Moreira & Muir (2017):** inverse-variance scaling raises Sharpe
  ratios for the market and most factors. (Abstract.)
* **In this repository:** volatility targeting on RSP cut drawdown 54%,
  with the edge concentrated in February–June 2020 (plan.md, V18); on
  top of the Ultimate-RSP votes it lowered Calmar in every case
  (ultimate-rsp.md, A4).

## Against, and failure modes

* **Cederburg et al. (2020):** across 103 strategies, real-time
  volatility management generally did not beat the unmanaged portfolio.
* De-risks after a fall and re-risks after calm (the CSV's caveat); does
  not prevent gap losses.

## Fit with volatility-ai

Fits (a sizing change; never sells below cost) and is built. On the grid
it only shrinks or grows *new* lots, so it reduces the inventory a
correction accumulates rather than the exposure already held, which is a
different lever from an exposure book's.

## How to test it here

```bash
python -m research.run_hf_sweep --config config/probe_vol_target.yaml \
    --search grid --intrabar-fill causal --output output/probe_vol_target_causal.csv
```

Ledger §11 item 5: run beside V11 `dd_throttle`, the other exposure lever.
Score with the deflated Sharpe ratio across all 12 combinations.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Harvey, C. R., Hoyle, E., Korgaonkar, R., Rattray, S., Sargaison, M.,
  Van Hemert, O. (2018). "The Impact of Volatility Targeting." *Journal
  of Portfolio Management* 45(1), 14–33. Abstract.
* Moreira, A., Muir, T. (2017). "Volatility-Managed Portfolios." *Journal
  of Finance* 72(4), 1611–1644. Abstract.
* Cederburg, S., O'Doherty, M. S., Wang, F., Yan, X. (2020). *Journal of
  Financial Economics* 138(1), 95–117. Abstract.
* RK2's page has the full discussion and the leveraged-ETF drag formula.
