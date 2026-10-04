"""
Hierarchical risk parity (Lopez de Prado), NumPy only.

  1. distance d_ij = sqrt((1 - rho_ij) / 2)
  2. single-linkage agglomerative clustering on d
  3. allocate top-down along the dendrogram: at each merge, split the
     node's weight between its two children in inverse proportion to
     each child's inverse-variance-portfolio variance

Step 3 bisects along the TREE rather than halving the quasi-diagonal
list as the original paper does. With list-halving a duplicated asset
can land on both sides of a split and double its allocation; along the
tree, two perfectly correlated assets merge first and share one
cluster's weight (pinned in the tests).

Listed via skfolio (awesome-ai-in-finance) and quant-trading's Portfolio
Optimization project. Used by tools/rotation.py --mode hrp to weight
concurrent sleeves.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError


def _cluster_variance(cov: np.ndarray, members: list[int]) -> float:
    sub = cov[np.ix_(members, members)]
    ivp = 1.0 / np.diag(sub)
    ivp /= ivp.sum()
    return float(ivp @ sub @ ivp)


def _single_linkage(dist: np.ndarray):
    """Merge tree as nested tuples of leaf indices; ties broken by the
    lowest indices, so the result is deterministic."""
    nodes: dict[int, tuple[object, list[int]]] = {i: (i, [i]) for i in range(len(dist))}
    while len(nodes) > 1:
        ids = sorted(nodes)
        best = None
        for a_pos, a in enumerate(ids):
            for b in ids[a_pos + 1 :]:
                d = min(dist[x, y] for x in nodes[a][1] for y in nodes[b][1])
                if best is None or d < best[0] - 1e-15:
                    best = (d, a, b)
        _, a, b = best
        nodes[a] = ((nodes[a][0], nodes[b][0]), nodes[a][1] + nodes[b][1])
        del nodes[b]
    return next(iter(nodes.values()))[0]


def _leaves(node) -> list[int]:
    return [node] if isinstance(node, int) else _leaves(node[0]) + _leaves(node[1])


def hrp_weights(returns: pd.DataFrame) -> pd.Series:
    """Long-only weights summing to 1, one per column."""
    if returns.shape[1] < 2:
        raise ConfigurationError("HRP needs at least two assets")
    clean = returns.dropna(how="any")
    if len(clean) < returns.shape[1] + 2:
        raise ConfigurationError("not enough return rows to estimate a covariance")
    cov = clean.cov().to_numpy()
    if np.any(np.diag(cov) <= 0):
        raise ConfigurationError("every asset needs a positive variance")
    corr = clean.corr().to_numpy()
    dist = np.sqrt(np.clip((1.0 - corr) / 2.0, 0.0, None))
    weights = np.zeros(len(cov))

    def allocate(node, weight: float) -> None:
        if isinstance(node, int):
            weights[node] = weight
            return
        left, right = node
        vl = _cluster_variance(cov, _leaves(left))
        vr = _cluster_variance(cov, _leaves(right))
        alpha = 1.0 - vl / (vl + vr)
        allocate(left, weight * alpha)
        allocate(right, weight * (1.0 - alpha))

    allocate(_single_linkage(dist), 1.0)
    return pd.Series(weights, index=returns.columns)


__all__ = ["hrp_weights"]
