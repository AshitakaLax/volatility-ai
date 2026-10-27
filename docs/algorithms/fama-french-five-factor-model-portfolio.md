# Fama–French Five-Factor Model Portfolio

**Ledger ID RK9** · rank 9 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 9 (1 = strongest) |
| AI implementability rank | 88 (1 = easiest) |
| Retail advantage rank | 252 (1 = strongest) |
| Fit with this project | ⛔ as a long/short factor portfolio · ⏳ as an **attribution tool** for this project's own returns |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK13, RK15, RK48, RK58 |

## In one paragraph

The five-factor model explains stock returns with market, size (SMB),
value (HML), profitability (RMW, robust minus weak) and investment (CMA,
conservative minus aggressive). As a "portfolio" it means holding
exposures to those factors, usually as long/short spreads. Its most
useful role for this project is not as a strategy but as a measuring
stick: regress the grid's returns on the five factors and see how much
is alpha and how much is market beta in disguise.

## The model

```
R_i - R_f = a_i + b_i (R_M - R_f) + s_i SMB + h_i HML + r_i RMW + c_i CMA + e_i
```

Factor returns (daily, weekly, monthly) are published in Ken French's
data library.

## Evidence

* **Fama & French (2015), *Journal of Financial Economics*:** adding
  profitability and investment makes the value factor redundant for
  describing average returns in their US sample; HML's average return
  is absorbed by its exposures to the other factors, especially RMW and
  CMA. The model's main failure is small stocks that invest a lot
  despite low profitability. (Abstract.)
* **Rival: Hou, Xue & Zhang (2015)'s q-factor model** (market, size,
  investment, profitability) performs at least as well as Fama-French
  three-factor and Carhart on most of ~80 anomalies; about half the
  anomalies are insignificant in the broad cross-section. (Abstract.)
* **Critique: Cooper, Gulen & Ion (2024):** both models' investment
  factor is asset growth, and their pricing power depends heavily on
  that construction. (Abstract.)
* HML's redundancy does not carry to every market (studies on Indonesia
  and Singapore find HML not redundant; a Chinese study finds the
  reverse). (Summaries.)

## Against, and failure modes

As a trading strategy: long/short, leverage, a stock universe and
fundamentals; factor returns are research objects, not a direct rule
(the CSV's caveat).

## Fit with volatility-ai

Out of scope as a portfolio. In scope, and cheap, as attribution: daily
factor returns from Ken French, regressed against the champion's,
Ultimate's and the step-down books' daily returns, would say how much of
their CAGR is leveraged market beta (TQQQ is ~3× the Nasdaq-100, a large
growth/low-value tilt).

## How to test it here

A small research script: load the five daily factors, align with a
book's daily returns from a backtest's equity curve, run OLS with
Newey-West errors, report alpha and loadings for the champion, Ultimate
and buy-and-hold TQQQ. If the champion's alpha is indistinguishable from
zero with a market beta near 3, that reframes every comparison in this
ledger as a leverage-timing question.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Fama, E. F., French, K. R. (2015). "A Five-Factor Asset Pricing
  Model." *Journal of Financial Economics* 116(1), 1–22. Abstract.
* Hou, K., Xue, C., Zhang, L. (2015). "Digesting Anomalies: An
  Investment Approach." *Review of Financial Studies* 28(3), 650–705.
  <https://econpapers.repec.org/RePEc:oup:rfinst:v:28:y:2015:i:3:p:650-705.>.
  Abstract.
* Cooper, M., Gulen, H., Ion, M. (2024). "The Use of Asset Growth in
  Empirical Asset Pricing Models." *Journal of Financial Economics*.
  Abstract.
* Kenneth R. French data library (the CSV's reference).
