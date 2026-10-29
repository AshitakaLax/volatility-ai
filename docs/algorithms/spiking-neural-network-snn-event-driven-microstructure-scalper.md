# Spiking Neural Network (SNN) Event-Driven Microstructure Scalper

**Ledger ID RK407** · rank 407 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Neuromorphic AI / Event-based trading |
| Potential effectiveness rank | 407 (1 = strongest) |
| AI implementability rank | 3,188 (1 = easiest) |
| Retail advantage rank | 10,332 (1 = strongest) |
| Fit with this project | ⛔ (tick-level scalping; one unreviewed backtest) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK258, RK306 |

## In one paragraph

Feed limit-order-book events to a spiking neural network, whose leaky
integrate-and-fire neurons respond to event streams natively and can run
on low-power neuromorphic hardware, and scalp the predicted next move. A
late-2025 preprint converts high-frequency stock data into spike trains
and reports a 76.8% cumulative return in a simple backtest for its best
spiking model, against 42.5% for a supervised baseline. That is one
unreviewed result without costs. The CSV's reference, arXiv 2109.12894,
could not be identified.

## Evidence

* **"Predicting Price Movements in High-Frequency Financial Data with
  Spiking Neural Networks" (arXiv 2512.05868, 2025):** STDP-trained and
  inhibitory-competition SNNs on spike-encoded stock data; tuned on a
  custom penalised spike-accuracy objective; 76.8% cumulative return in
  simple backtesting against 42.5% for backpropagation. (Abstract.)
* **Sirignano (2016) and DeepLOB (Zhang, Zohren & Roberts):**
  conventional deep networks are the order-book forecasting benchmark;
  no SNN comparison with them found. (Abstracts.)

## Against, and failure modes

* Custom objective tuned on the test period; simple backtest without
  costs or queue simulation.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. Tick scalping is out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Predicting Price Movements in High-Frequency Financial Data with
  Spiking Neural Networks (2025). <https://arxiv.org/abs/2512.05868>.
  Abstract.
* Zhang, Z., Zohren, S., Roberts, S. "DeepLOB."
  <https://arxiv.org/abs/1808.03668>. Abstract.
