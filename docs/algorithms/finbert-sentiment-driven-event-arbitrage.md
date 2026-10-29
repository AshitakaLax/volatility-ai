# FinBERT Sentiment-Driven Event Arbitrage

**Ledger ID RK311** · rank 311 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | NLP / Machine learning / Event-driven |
| Potential effectiveness rank | 311 (1 = strongest) |
| AI implementability rank | 213 (1 = easiest) |
| Retail advantage rank | 98 (1 = strongest) |
| Fit with this project | ⏳ as a market-level input (RK293) · ⛔ as a stock-level event trade |
| Implemented in volatility-ai | **Research code** in `research.catalog.technical_ml`: `SentenceClassifier`, `event_sentiment_trades`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK293, V6, RK45 |

## In one paragraph

Score the sentiment of news, filings or call transcripts with FinBERT, a
BERT model further trained on financial text, and trade the price
reaction. FinBERT is a better classifier than dictionaries: it beats the
Loughran-McDonald word lists on analyst-report sentences, and it shows
conference calls to be more informative than other methods do. The
return evidence comes from larger language models: headline scores from
ChatGPT predict next-day returns out of sample, mostly in small stocks
and after bad news, and the effect shrinks as such models spread.

## Evidence

* **Araci (2019), "FinBERT: Financial Sentiment Analysis with
  Pre-trained Language Models" (arXiv 1908.10063):** state-of-the-art
  results on Financial PhraseBank and FiQA sentiment. (Abstract.)
* **Huang, Wang & Yang (2023), "FinBERT: A Large Language Model for
  Extracting Information from Financial Text," *Contemporary Accounting
  Research* 40(2), 806–841:** beats the Loughran-McDonald dictionary and
  other ML baselines on labelled analyst-report sentences; other methods
  understate the informativeness of earnings calls by at least 18%. A
  classification paper, not a trading test. (Abstract.)
* **Lopez-Lira & Tang, "Can ChatGPT Forecast Stock Price Movements?
  Return Predictability and Large Language Models" (arXiv 2304.07619):**
  LLM headline scores predict out-of-sample daily returns and subsume
  traditional methods; stronger in small stocks and after negative news;
  later versions find returns falling as LLM adoption rises. (Abstract.)

## Against, and failure modes

* Timestamps must be exact and archives licensed; duplicates leak the
  future.
* The tradable part is small-stock and fast-decaying.

## Fit with volatility-ai

As RK293: a market-level sentiment series could join the regime as one
more input, but it needs a licensed, timestamped archive this project
does not have. Stock-level event trades are out of scope. FOMC and
earnings dates are already used as calendar events (V6) without reading
the text.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Araci, D. (2019). <https://arxiv.org/abs/1908.10063>. Abstract.
* Huang, A. H., Wang, H., Yang, Y. (2023). *Contemporary Accounting
  Research* 40(2), 806–841. doi:10.1111/1911-3846.12832. Abstract.
* Lopez-Lira, A., Tang, Y. "Can ChatGPT Forecast Stock Price Movements?"
  <https://arxiv.org/abs/2304.07619>. Abstract.
