# News / Financial Sentiment NLP

**Ledger ID RK293** · rank 293 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Machine learning / alternative data |
| Potential effectiveness rank | 293 (1 = strongest) |
| AI implementability rank | 300 (1 = easiest) |
| Retail advantage rank | 223 (1 = strongest) |
| Fit with this project | ⏳ as a risk input (market-level pessimism) · ⛔ as a stock-level news trade |
| Implemented in volatility-ai | **No.** The only sentiment series is the University of Michigan consumer survey (a registered FRED input), not text. |
| Related ledger entries | RK211, V6 |

## In one paragraph

Turn news, filings or social text into sentiment scores and trade on
them. The classic market-level finding is Tetlock's: high pessimism in a
Wall Street Journal column predicted downward pressure on prices
followed by a reversal, so media tone behaved like noise-trader
sentiment rather than news about fundamentals. Stock-level news trading
is a speed and data-licensing game.

## The rule

```text
score_i,t = model(text published before t)                 # dictionary (Loughran-McDonald) or FinBERT
market level: pessimism index -> expected short-term pressure, then reversal
```

## Evidence

* **Tetlock (2007), "Giving Content to Investor Sentiment," *Journal of
  Finance* 62(3), 1139–1168:** high media pessimism predicts downward
  price pressure followed by reversion to fundamentals; extreme
  pessimism predicts high volume; low returns predict pessimism; no
  evidence the content carries news about fundamentals. (Abstract.)
* Later work on a century of New York Times financial news finds the
  media-return link concentrated in recessions. (Summary.)

## Against, and failure modes

* Publication timestamps, duplicated stories, model drift and
  survivorship in news archives create hidden look-ahead (the CSV's
  caveat).
* Text data is licensed; the stock-level edge decays at the speed of the
  fastest reader.

## Fit with volatility-ai

For this book, market-level pessimism followed by reversal is the
interesting part: it says sentiment-driven selloffs tend to come back,
which is the grid's premise. Using it would need a licensed news archive
with exact timestamps; not a priority.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Tetlock, P. C. (2007). "Giving Content to Investor Sentiment: The Role
  of Media in the Stock Market." *Journal of Finance* 62(3), 1139–1168.
  <https://econpapers.repec.org/RePEc:bla:jfinan:v:62:y:2007:i:3:p:1139-1168>.
  Abstract.
* This repository: `research/ml/sources.py` (UMCSENT survey series
  only).
