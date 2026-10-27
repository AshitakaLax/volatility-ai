# Hierarchical Risk Parity (HRP)

**Ledger ID RK56** · rank 56 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio construction |
| Potential effectiveness rank | 56 (1 = strongest) |
| AI implementability rank | 3 (1 = easiest) |
| Retail advantage rank | 36 (1 = strongest) |
| Fit with this project | 🧪 built (A5) |
| Implemented in volatility-ai | **Yes.** `research/strategies/hrp.py:hrp_weights` (NumPy only), used by `tools/rotation.py --mode hrp` to size concurrent sleeves from weights fitted on the warm-up only. Unmeasured. |
| Related ledger entries | A5, Q13, RK60, RK61 |

## In one paragraph

Cluster assets by correlation into a tree, then split capital down the
tree in inverse proportion to each branch's variance. It needs no
expected returns and no matrix inversion, so it avoids the instability
and concentration of mean-variance optimisers. López de Prado's Monte
Carlo experiments show lower out-of-sample variance than the
critical-line (minimum-variance) optimiser, even on that optimiser's own
objective. The repository has it, tested to give inverse-variance weights
for independent assets and to stop a duplicated asset doubling its
weight.

## The rule

```
1. distance d_ij = sqrt((1 - corr_ij) / 2); single-linkage hierarchical clustering
2. quasi-diagonalise: order assets by the dendrogram
3. recursive bisection: split the ordered list in two; allocate between halves in inverse
   proportion to each half's inverse-variance-portfolio variance; repeat within each half
```

## Evidence

* **López de Prado (2016), *Journal of Portfolio Management* 42(4),
  59–69:** HRP addresses instability, concentration and underperformance
  of quadratic optimisers; it does not need an invertible covariance
  matrix; Monte Carlo experiments show lower out-of-sample variance than
  the critical-line algorithm and less risky portfolios than traditional
  risk parity. (Abstract.) These are simulations, not live results.

## Against, and failure modes

* Sensitive to the estimation window and the distance metric (the CSV's
  caveat); single linkage chains clusters.
* Does not guarantee lower realised risk: correlations converge in
  crashes, collapsing the tree.

## Fit with volatility-ai

Built and in scope. In `tools/rotation.py --mode hrp` every sleeve runs
concurrently, which stretches the additive-account approximation (total
deployed capital can exceed one account's), as the ledger notes for A5.

## How to test it here

```bash
python -m tools.rotation --mode hrp                          # QQQ RSP XLP USMV, weights from the warm-up
python -m tools.rotation --mode hrp --universe QQQ RSP GLD USMV
```

Compare with equal weights over the same sleeves: DeMiguel, Garlappi &
Uppal (2009) found no optimiser consistently beat 1/N out of sample, so
equal weight (rank 117 in the list) is the right null.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* López de Prado, M. (2016). "Building Diversified Portfolios that
  Outperform Out of Sample." *Journal of Portfolio Management* 42(4),
  59–69. <https://papers.ssrn.com/abstract=2708678>. Abstract.
* DeMiguel, V., Garlappi, L., Uppal, R. (2009). "Optimal Versus Naive
  Diversification: How Inefficient is the 1/N Portfolio Strategy?"
  *Review of Financial Studies* 22(5), 1915–1953. Abstract.
* This repository: ledger A5; `research/strategies/hrp.py`;
  `tools/rotation.py`.
