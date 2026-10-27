# ETF NAV / Creation-Redemption Arbitrage

**Ledger ID RK24** · rank 24 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Index / ETF relative value |
| Potential effectiveness rank | 24 (1 = strongest) |
| AI implementability rank | 206 (1 = easiest) |
| Retail advantage rank | 182 (1 = strongest) |
| Fit with this project | ⛔ (authorized-participant access, short legs) |
| Implemented in volatility-ai | **Research code.** The authorized participant's create/redeem decision, `excluded.creation_redemption_action` (ledger C-RJ6). |
| Related ledger entries | C-RJ6, RK91, RK25 |

## In one paragraph

When an ETF trades above the value of its basket, an authorized
participant (AP) delivers the basket, receives new ETF shares and sells
them; when it trades below, the AP buys shares and redeems them for the
basket. This mechanism keeps ETF prices near NAV, and the profit goes to
APs and market makers with the agreements, the creation-unit size and
the basket execution. Petajisto finds the band is still about 100 bp
wide after correcting for stale NAVs, and that trading against it
earned abnormal returns before costs.

## The rule

```
premium = ETF price / basket value (iNAV) - 1
premium > costs: sell ETF (short), buy the basket, create units to deliver
premium < -costs: buy ETF, short the basket, redeem units for the basket
```

## Evidence

* **Petajisto (2017), "Inefficiencies in the Pricing of Exchange-Traded
  Funds," *Financial Analysts Journal* 73(1), 24–54:** the whole US ETF
  sector, 2007–2014. Price deviations from NAV are typically within about
  200 bp, larger for international or illiquid holdings. Measured
  against peer ETFs to remove stale NAV pricing, the band is still about
  100 bp. Strategies trading the gap earn substantial abnormal returns
  before transaction costs. (Abstract.)

## Against, and failure modes

* Creation units, AP agreements, basket execution and borrow are
  institutional (the CSV's caveat); retail data rarely shows executable
  basket prices.
* The short legs are out of scope here.

## Fit with volatility-ai

Out of scope. The relevant fact for this book runs the other way: a
leveraged ETF's premium or discount to NAV is part of the execution cost
of a market order, worth checking around the open and the close.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Petajisto, A. (2017). "Inefficiencies in the Pricing of Exchange-Traded
  Funds." *Financial Analysts Journal* 73(1), 24–54.
  <https://econpapers.repec.org/RePEc:taf:ufajxx:v:73:y:2017:i:1:p:24-54>.
  Abstract and CFA Institute summary.
* This repository: ledger C-RJ6; `research/catalog/excluded.py`.
