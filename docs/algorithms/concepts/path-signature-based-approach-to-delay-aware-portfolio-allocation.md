# Path-signature-based approach to delay-aware portfolio allocation

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,207) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Path signatures |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of path signatures improving allocation through lagged dynamics, and the book trades one symbol. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Signature Scholarly Delay
Differential Allocator Ref-445") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The path-signature
version describes price paths by their iterated-integral signatures and
fits on those features. I found no study of this method on this task.

## The CSV's description

Proposed path-signature-based approach to delay-aware portfolio
allocation: Model delayed or lagged relationships in market variables
and use the estimated dynamics to adjust portfolio weights; the state
equations and decision rules require specification. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Gârleanu & Pedersen (2013), "Dynamic Trading with Predictable
  Returns and Transaction Costs," *Journal of Finance* 68(6),
  2309–2340:** with costs, aim in front of the target and trade only
  partway toward the aim; slower-decaying signals get more weight. Net
  of costs it beat naive rules on commodity futures. (Abstract.)

## Against, and failure modes

* The title's delay-differential dynamics are unspecified; lagged
  relations between liquid ETFs are small and quickly arbitraged.
* Signature features multiply with depth and dimension; no out-of-sample
  trading evidence found (RK328).

## Fit with volatility-ai

Trading partway toward a moving target matters for a multi-asset book
turned over at cost. The engine trades one symbol in lots, which is
already a form of partial trading.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gârleanu, N., Pedersen, L. H. (2013). *Journal of Finance* 68(6),
  2309–2340. doi:10.1111/jofi.12080. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1207 | Signature Scholarly Delay Differential Allocator Ref-445 | Rough path theory / Tensor signatures / Stock trend forecasting | 6529 | 3121 | No |
| 1218 | Signature Scholarly Delay Differential Allocator Ref-925 | Rough path theory / Tensor signatures / Stock trend forecasting | 6572 | 3238 | No |
| 3179 | Signature Scholarly Delay Differential Allocator Ref-157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10048 | 11301 | No |
| 3195 | Signature Scholarly Delay Differential Allocator Ref-637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10058 | 11322 | No |
| 3833 | Signature Scholarly Delay Differential Allocator Ref-349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8263 | 3097 | No |
| 3919 | Signature Scholarly Delay Differential Allocator Ref-829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8304 | 3214 | No |
| 7455 | Signature Scholarly Delay Differential Allocator Ref-61 | Graph attention / Sector contagion / Stock baskets | 704 | 1010 | No |
| 7489 | Signature Scholarly Delay Differential Allocator Ref-541 | Graph attention / Sector contagion / Stock baskets | 720 | 1045 | No |
| 8777 | Signature Scholarly Delay Differential Allocator Ref-253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7789 | 5972 | No |
| 8968 | Signature Scholarly Delay Differential Allocator Ref-733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7806 | 5992 | No |
