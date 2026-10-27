# Adversarial Domain Generalization Cross-Market Momentum

**Ledger ID RK98** · rank 98 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Domain adaptation / ML momentum |
| Potential effectiveness rank | 98 (1 = strongest) |
| AI implementability rank | 175 (1 = easiest) |
| Retail advantage rank | 25 (1 = strongest) |
| Fit with this project | ⏳ (in principle, as a long-only ranking) · not a priority |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK7, RK1 |

## In one paragraph

Train a neural network to predict cross-sectional momentum returns
while an adversary tries to tell which market or regime each sample
came from. Penalising what the adversary can detect pushes the network
toward features that work everywhere, so the momentum rule should
generalise to new markets and regimes. The CSV cites Invariant Risk
Minimization and DomainBed. I found no study that applies this to
momentum. DomainBed's own result was that carefully tuned ordinary
training matched the domain-generalisation algorithms, which is a
reason for doubt.

## The rule

```
features x (past returns, fundamentals, macro) from several markets (domains d)
network f(x) predicts next-month return; adversary g(f's representation) predicts d; train f to fool g (gradient reversal)
rank by f(x) in each market; hold the top (long-only form)
```

## Evidence

* **Arjovsky, Bottou, Gulrajani & Lopez-Paz (2019), "Invariant Risk
  Minimization" (arXiv 1907.02893, the CSV's reference):** the
  invariance principle. (Recalled.)
* **Gulrajani & Lopez-Paz (2020), "In Search of Lost Domain
  Generalization" (DomainBed, the CSV's reference):** with careful
  tuning, plain empirical risk minimisation matched the
  domain-generalisation methods tested. (Recalled.)
* **Nearest finance work:** adversarial transfer for stock-movement
  prediction across markets (Li, Dai & Zheng, "STLAT", 2021), which
  predicts direction, not momentum returns. (Summary.)
* **No study of adversarial domain generalisation for momentum found.**

## Against, and failure modes

* Adversarial training is unstable and tuning-heavy (the CSV's caveat);
  few independent market regimes to train on.

## Fit with volatility-ai

A long-only ranking could pass the instrument rule, but there is no
evidence to justify the machinery.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Arjovsky, M., Bottou, L., Gulrajani, I., Lopez-Paz, D. (2019).
  "Invariant Risk Minimization." <https://arxiv.org/abs/1907.02893>.
  Recalled, not re-checked.
* Gulrajani, I., Lopez-Paz, D. (2020). "In Search of Lost Domain
  Generalization." DomainBed. Recalled, not re-checked.
* Li, Y., Dai, H.-N., Zheng, Z. (2021). "Selective transfer learning with
  adversarial training for stock movement prediction." Summary.
