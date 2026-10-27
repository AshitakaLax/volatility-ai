# Long-Term Industry Reversal with Valuation Confirmation

**Ledger ID RK90** · rank 90 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Industry rotation / long-horizon contrarian |
| Potential effectiveness rank | 90 (1 = strongest) |
| AI implementability rank | 39 (1 = easiest) |
| Retail advantage rank | 50 (1 = strongest) |
| Fit with this project | ⏳ (long-only sector ETFs; a separate book) |
| Implemented in volatility-ai | **No.** The rotation harness ranks ETFs by trailing *strength* (X3), not weakness. |
| Related ledger entries | X3, RK19, RK7 |

## In one paragraph

Buy industries that have lagged badly over several years, but only
where valuations are cheap and fundamentals have stopped deteriorating.
Diversify and scale in. Industry returns do reverse over the long term:
across 48 US industries from 1963 to 2013, long-horizon losers
outperformed winners, and the valuation effects lasted up to ten years.
The valuation confirmation is the CSV's proposed filter, not an
established result. It is the slow opposite of sector momentum (RK19).

## The rule

```
rank industries (sector ETFs) on 3-5 year relative return; candidates = bottom quintile
confirm: valuation (P/E, P/B) in the cheapest third vs its history; margins/earnings no longer falling
buy in tranches; hold 1-3 years; compare against the pure reversal baseline
```

## Evidence

* **Bornholt, Gharaibeh & Malin (2015), "Industry long-term return
  reversal," *Journal of International Financial Markets, Institutions
  and Money* 38, 65–78 (the CSV's reference):** strong reversals in
  industries' long-term returns, persisting for many years, with
  valuation effects up to 10 years later and formation periods up to
  132 months; hard to square with simple overreaction. (Abstract; 48
  industries, 1963–2013, per a summary.)
* **Wu & Mazouz (2016), *Journal of Banking & Finance*:** UK firms in
  losing industries beat those in winning industries over the next five
  years. (Summary.)
* The CSV's second reference (*Journal of Empirical Finance*, 2019,
  PII S0927539819301033) was not identified.

## Against, and failure modes

* Structural decline and disruption look like cheap losers; value traps;
  multi-year drawdowns before any reversal (the CSV's caveat).

## Fit with volatility-ai

Long-only sector ETFs pass the instrument rule; this would be a slow
separate book, run on the rotation harness's universe with a reversed
ranking. It has nothing to do with the TQQQ grid's daily volatility.

## What it would take

`tools/rotation.py` with a "bottom of the five-year ranking" mode over
the SPDR sector ETFs, a valuation input (not in the warehouse), and a
long sample. The ETFs start in 1998, so few independent periods are
available.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bornholt, G., Gharaibeh, O., Malin, M. (2015). *Journal of
  International Financial Markets, Institutions and Money* 38, 65–78.
  <https://ideas.repec.org/a/eee/intfin/v38y2015icp65-78.html>. Abstract.
* Wu, Y., Mazouz, K. (2016). *Journal of Banking & Finance*. Summary.
* This repository: `tools/rotation.py` (X3).
