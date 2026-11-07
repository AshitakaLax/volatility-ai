# The TFT in buy × sell compositions, on TQQQ and RSP

Nov 7, 2026 · Measured · `tools/probe_tft_composite.py` (242 cells), four trained models

## Question

Train `ml_tft`'s Temporal Fusion Transformer for TQQQ and RSP, then pair it with
the composition library's other buy and sell algorithms. Is there a
combination in which the TFT helps? And which combination is best?

## Answer

**The TFT adds nothing as a buy sizer, and a little, on RSP only, as a sell.**
The best combinations do not need it.

- **As a buy** (`ml_tft`), every cell was set against its **null**: the same
  sizer, caps and drawdown decay, fed the model's *average* forecast on every
  bar. On RSP the two are within a few tenths of a point everywhere. On TQQQ
  the TFT buys more often than its null, which raises return and drawdown
  together; Calmar barely moves. The models forecast the *spread* of the next
  30 minutes well (pinball skill +5–6% over a naive forecast, calibrated
  quantiles) and the *direction* not at all (rank correlation of the forecast
  mean with the outcome: −0.011 to +0.011). A Kelly sizer bets on the mean.
- **As a sell** (`tft_take_profit`, new): on TQQQ every sell gives the same
  result, because the 0.3% grid target sells first. On RSP the TFT take-profit
  beats its null, a naive sell-into-strength rule, for all 11 buys, by 1–4
  points of total return over the 2.85 years at the same drawdown. It is one
  signal on one window: treat it as a lead.
- **The outside series** (news sentiment, policy uncertainty, earnings
  reactions) improve the forecasts slightly (pinball skill 0.052 → 0.058 on
  TQQQ, 0.055 → 0.059 on RSP) and the trading not measurably.

**Best combinations**, from 2024-01-02 to 2026-11-06 with causal fills and costs:

| Fund | Buy × sell | Total | Max DD | Calmar | Buy-and-hold |
|---|---|---|---|---|---|
| TQQQ | `ultimate` × `regime_exit` | 171.2% | 20.9% | 2.01 | 117.6%, DD 62.2% |
| TQQQ | `ultimate` × `ultimate_exit` (the reference book) | 154.1% | 20.9% | 1.86 | |
| RSP | small grid buys (0.1% cap) × `rsp_rebalance` | 39.6% | 6.1% | 2.03 | 44.0%, DD 19.3% |
| RSP | `ultimate_rsp` × `rsp_rebalance` (the reference book) | 36.9% | 7.9% | 1.47 | |
| RSP | small grid buys × `scale_out` (most return) | 57.8% | 17.4% | 1.00 | |

The "small grid buys" rows are the null sizer: the TFT version of each
(39.0% / 6.0%, 56.3% / 17.3%) is no better. What earns them is the pairing,
many small dip buys whose exposure the RSP book's rebalance caps, not the
model. **None of the Ultimate or RSP-book parameters is out of sample here**:
they were chosen on histories that include this window. Only the TFT cells
are.

## The models

`python cli.py train --config config/ml/<name>.yaml`. Each was trained on minute
bars from 2016-01-04 up to 2024-01-01 and validated after that (L = 120-bar
encoder, H = 30-bar horizon, quantiles 10/50/90, 5 epochs × 200 batches of 128,
about 12 minutes on this machine's CPUs).

| Model | Inputs | Pinball skill vs naive | q10 / q50 / q90 coverage | Rank corr. of mu | Windows with mu > 0 |
|---|---|---|---|---|---|
| `tft_tqqq` | price | 0.052 | 0.10 / 0.48 / 0.87 | −0.011 | 22% |
| `tft_tqqq_inputs` | price + the three series | 0.058 | 0.11 / 0.48 / 0.84 | +0.011 | 31% |
| `tft_rsp` | price | 0.055 | 0.13 / 0.56 / 0.90 | +0.001 | 84% |
| `tft_rsp_inputs` | price + the three series | 0.059 | 0.14 / 0.55 / 0.88 | +0.011 | 84% |

`tft_rsp.yaml`'s base is `config/hf_entry_gated_rsp.yaml`, the live RSP
profile's algorithm (0.1% step, +20% target) as a single-point config.

## The data the TFT reads, and what was missing

The design names three outside series: a macro surprise, earnings sentiment
and news sentiment. None has a free source in that shape, because consensus
forecasts and transcripts are sold. So each is the closest free stand-in,
named for what it is (`research/ml/tft_inputs.py`, `tools/build_tft_inputs.py`):

| Input | Built from | Added to the warehouse |
|---|---|---|
| `s_news` | the SF Fed's Daily News Sentiment Index, from 1980; refreshed about weekly, so stamped 7 days late | `frbsf_NEWS_SENTIMENT` (new provider `frbsf`, read with the standard library, no openpyxl) |
| `s_macro` | a policy-uncertainty shock: the z-score of smoothed log daily EPU (Baker, Bloom & Davis) against its trailing 250 readings | `fred_USEPUINDXD` |
| `s_earnings` | the earnings announcement return of the calendar's 16 Nasdaq-100 reporters: each one's move over its reaction session less QQQ's, tanh-scored, decayed with a 10-session half-life | `yahoo_<ticker>` daily closes for the 16 |

The warehouse's external lake was also stale, with every FRED, CBOE and
Yahoo series ending 2026-09-04. It was refreshed to this week (136 series, 0
failed), as was the main checkout's `data/external/`.

**Still missing, and the free way to get each:**

- **The earnings calendar** (`market_events`) ends 2026-08-04, so
  `s_earnings` fades after it. Its builder's source (`hfmarketdata.io`) no
  longer answers. Two free routes:
  - SEC EDGAR's submissions API (8-K item 2.02 dates). SEC asks for a contact
    address in the User-Agent, which needs the owner's say.
  - Rebuilding `tools/build_earnings_calendar.py`'s gap-and-volume detector on
    Alpaca bars, using the key the `market-data` service already uses.
- **A consensus macro surprise** is not free with history. Nasdaq's
  calendars carry the consensus, but they refuse non-browser clients, and
  this project does not disguise its client. ALFRED (a free FRED API key)
  gives each release's true publication date, which would replace the
  45-day conservative lags, but not the consensus.
- **ICE BofA credit spreads** are still three years only (FRED's licence).

## The matrix

`tools/probe_tft_composite.py`. Every buy with every sell, as `composed`
strategies through `OptimizationController.run_sweep`, on each fund from
2024-01-01. Fills are causal intrabar, costs are dynamic slippage, and the
account starts at $100,000. The loss gate is open only for `regime_exit` and the
book exits. The Ultimate family is warmed on the sessions before the window.

- **Buys:**
  - the base config's buying;
  - `ml_tft` from each model at three per-trade caps (0.1%, 0.5% and the
    committed 5% of equity);
  - the null at the same caps;
  - the reference book's buying.
- **Sells:**
  - the no-loss library (`fixed_target`, `trailing`, `age_decay`,
    `vol_scaled_target`, `scale_out`, `signal_take_profit`);
  - `tft_take_profit` from each model, plus its null;
  - `regime_exit`;
  - the reference book's exit (`ultimate_exit` / `rsp_rebalance`).

**The forecast cache.** A forecast is a pure function of the bars before
it, so `tools/precompute_tft_forecasts.py` makes each one once per model,
across all cores. That took about 10.5 minutes for 279,000 bars. Each run
then looks it up (`research/ml/tft_cache.py`), keyed by a BLAKE2b digest of
the exact encoder and decoder inputs: a hit is what the model returned for
those inputs, and a miss runs the model. It was checked hit-for-hit and
bit-for-bit against the live sizer on real bars (`test_tft_cache.py` does
the same with a small real TFT). Without it, one `ml_tft` backtest over this
window takes more than an hour. With it, the median cell took 2 minutes.

## Caveats

- **One window**, 2.85 years, mostly a bull market: there is no 2022 in it.
  A longer out-of-sample test needs a model per cutoff, retrained (for
  example at 2021-07 and 2023-01).
- **The TFT was trained lightly** (5 epochs, 200 batches each). A bigger
  network or longer training might find direction where this one did not;
  the null makes that cheap to check.
- **The reference books' parameters were tuned on data that includes this
  window**, so their cells are not out of sample.
- The trainer's own `--compare` (level fills, uncached) is a different
  measurement; the matrix uses causal fills throughout. Its baseline is the
  base config, not the null, so it cannot separate the forecast from the
  sizing. For `tft_rsp`, `ml_tft` returned 41.3% with a 19.2% drawdown
  against the base config's 43.5% and 18.0%, worse on both;
  `tft_rsp_inputs` gave 41.4% and 19.1%. For `tft_tqqq`, `ml_tft` returned
  13.0% with a 12.5% drawdown against the base grid's −1.7% and 50.3%;
  `tft_tqqq_inputs` returned 33.2% with a 17.5% drawdown. In the matrix too
  the inputs model buys more than the price-only one. That
  grid baseline is far weaker than the matrix's `base` rows (31.3% / 32.9%
  with `fixed_target`); the gap was not traced.

## Reproduce

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements-dl.txt
python tools/fetch_market_inputs.py --refresh && python tools/build_warehouse.py --external
python tools/build_tft_inputs.py
for m in tft_tqqq tft_rsp tft_tqqq_inputs tft_rsp_inputs; do
  python cli.py train --config config/ml/$m.yaml
  python tools/precompute_tft_forecasts.py --model data/ml/models/$m
done
python tools/probe_tft_composite.py --build-null --out output/tft_composite --jobs 40
python tools/probe_tft_composite.py --report --out output/tft_composite
```
