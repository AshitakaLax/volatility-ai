# Neural Rough Path Signature Delay-Differential Portfolio Control

**Ledger ID RK330** · rank 330 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Rough path theory / Delay differential equations / Portfolio control |
| Potential effectiveness rank | 330 (1 = strongest) |
| AI implementability rank | 251 (1 = easiest) |
| Retail advantage rank | 278 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.cross_section`: `signature_trading`, `signature_feature_panel`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK328 |

## In one paragraph

Control portfolio weights with a delay-differential equation whose
inputs are path signatures. Signature trading (RK328) gives an explicit
path-dependent mean-variance policy without delay equations; I found no
study of this combination.

## Evidence

* **Futter, Horvath & Wiese (2023):** signature trading (see RK328).
* **No study found** of signature delay-differential control.

## Against, and failure modes

* Two heavy layers on a problem signature trading already solves in
  closed form.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Futter, O., Horvath, B., Wiese, M. (2023).
  <https://arxiv.org/abs/2308.15135>. Abstract.
