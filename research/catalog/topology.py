"""
Topological-data-analysis entries of the ranked list (ledger RK254, RK255,
RK262, RK263, RK265, RK268, RK398, RK401, RK403): Vietoris-Rips persistent
homology in dimensions 0-2, persistence landscapes and their norms, Betti
curves, diagram distances and clustering. Research code with no trading
evidence of its own; the long-only use is an exposure governor that cuts
risk when a topological stress score spikes.

Sources:

  * Persistence by boundary-matrix reduction over Z/2 -- Edelsbrunner,
    Letscher & Zomorodian, "Topological persistence and simplification",
    Discrete Comput. Geom. 28, 2002; Zomorodian & Carlsson, 2005.
  * Persistence landscapes and their Lp norms -- Bubenik, "Statistical
    topological data analysis using persistence landscapes", JMLR 16, 2015.
  * Crash early warning -- Gidea & Katz, "Topological data analysis of
    financial time series: landscapes of crashes", Physica A 491, 2018
    (sliding windows of four index return series, L1/L2 norm of the H1
    landscape rising before 2000 and 2008).
  * Correlation networks and H0 (single linkage) -- Mantegna, "Hierarchical
    structure in financial markets", EPJ B 11, 1999 (distance
    sqrt(2(1 - rho))).
  * Diagram Wasserstein distance -- Cohen-Steiner, Edelsbrunner, Harer &
    Mileyko, Found. Comput. Math. 10, 2010 (optimal matching with the diagonal).
  * Delay embedding -- Takens, 1981.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import pdist, squareform

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- persistence


def rips_filtration(distances, max_dim: int = 1, max_edge: float = np.inf) -> list:
    """Simplices of the Vietoris-Rips complex up to dimension max_dim + 1, as
    (vertices, filtration value) sorted by value then dimension."""
    d = np.asarray(distances, float)
    n = len(d)
    adj = (d <= max_edge) & ~np.eye(n, dtype=bool)
    level = [((i,), 0.0) for i in range(n)]
    out = list(level)
    for _ in range(max_dim + 1):
        nxt = []
        for verts, val in level:
            common = np.flatnonzero(adj[list(verts)].all(axis=0))
            for v in common[common > verts[-1]]:
                nxt.append(((*verts, int(v)), max(val, float(d[list(verts), v].max()))))
        out += nxt
        level = nxt
    out.sort(key=lambda s: (s[1], len(s[0]), s[0]))
    return out


def persistence(filtration: list, max_dim: int = 1) -> dict[int, np.ndarray]:
    """Persistence pairs by column reduction over Z/2: {dim: array of (birth,
    death)}; classes never killed die at +inf. Zero-length pairs are dropped."""
    index = {s: i for i, (s, _) in enumerate(filtration)}
    cols: list[set] = []
    low_to_col: dict[int, int] = {}
    paired = set()
    pairs = {k: [] for k in range(max_dim + 1)}
    for j, (s, val) in enumerate(filtration):
        col = {index[f] for f in combinations(s, len(s) - 1)} if len(s) > 1 else set()
        while col:
            low = max(col)
            if low not in low_to_col:
                break
            col ^= cols[low_to_col[low]]
        cols.append(col)
        if col:
            low = max(col)
            low_to_col[low] = j
            paired.update((low, j))
            dim = len(filtration[low][0]) - 1
            if dim <= max_dim and val > filtration[low][1]:
                pairs[dim].append((filtration[low][1], val))
    for i, (s, val) in enumerate(filtration):
        if i not in paired and len(s) - 1 <= max_dim:
            pairs[len(s) - 1].append((val, np.inf))
    return {k: np.array(v, float).reshape(-1, 2) for k, v in pairs.items()}


def rips_persistence(points=None, distances=None, max_dim: int = 1, max_edge=np.inf) -> dict:
    """Persistence diagrams of a point cloud (rows) or a distance matrix."""
    if (points is None) == (distances is None):
        raise ConfigurationError("pass exactly one of points or distances")
    if distances is None:
        distances = squareform(pdist(np.atleast_2d(np.asarray(points, float))))
    return persistence(rips_filtration(distances, max_dim, max_edge), max_dim)


def finite(diagram, cap: float | None = None) -> np.ndarray:
    """Drop (or cap at `cap`) the infinite deaths."""
    dg = np.asarray(diagram, float).reshape(-1, 2)
    if cap is None:
        return dg[np.isfinite(dg[:, 1])]
    return np.column_stack([dg[:, 0], np.minimum(dg[:, 1], cap)])


def total_persistence(diagram, p: float = 1.0) -> float:
    dg = finite(diagram)
    return float(((dg[:, 1] - dg[:, 0]) ** p).sum())


# ---------------------------------------------------------------- summaries


def persistence_landscape(diagram, grid, k: int = 3) -> np.ndarray:
    """Bubenik's landscape: lambda_j(t) = j-th largest max(0, min(t - b, d - t))."""
    dg = finite(diagram)
    grid = np.asarray(grid, float)
    out = np.zeros((k, len(grid)))
    if len(dg):
        tents = np.maximum(0.0, np.minimum(grid - dg[:, :1], dg[:, 1:] - grid))
        tents = -np.sort(-tents, axis=0)
        m = min(k, len(dg))
        out[:m] = tents[:m]
    return out


def landscape_norm(landscape, grid, p: float = 2.0) -> float:
    """(sum_j integral |lambda_j|^p dt)^(1/p) by the trapezoid rule."""
    return float(np.trapezoid(np.abs(landscape) ** p, grid, axis=1).sum() ** (1.0 / p))


def betti_curve(diagram, grid) -> np.ndarray:
    """Number of classes alive at each grid value: #{b <= t < d}."""
    dg = np.asarray(diagram, float).reshape(-1, 2)
    g = np.asarray(grid, float)[:, None]
    return ((dg[:, 0] <= g) & (g < dg[:, 1])).sum(axis=1)


def diagram_distance(d1, d2, q: float = 2.0) -> float:
    """q-Wasserstein distance between finite diagrams (L-inf ground metric),
    matching points to each other or to the diagonal."""
    a, b = finite(d1), finite(d2)
    n, m = len(a), len(b)
    if n + m == 0:
        return 0.0
    big = 1e12
    c = np.full((n + m, m + n), big)
    if n and m:
        c[:n, :m] = np.abs(a[:, None, :] - b[None, :, :]).max(-1) ** q
    c[:n, m:][np.arange(n), np.arange(n)] = ((a[:, 1] - a[:, 0]) / 2) ** q
    c[n:, :m][np.arange(m), np.arange(m)] = ((b[:, 1] - b[:, 0]) / 2) ** q
    c[n:, m:] = 0.0
    r, k = linear_sum_assignment(c)
    return float(c[r, k].sum() ** (1.0 / q))


def delay_embedding(series, dim: int = 3, tau: int = 1) -> np.ndarray:
    """Takens embedding: rows (x_t, x_{t+tau}, ..., x_{t+(dim-1)tau})."""
    x = np.asarray(series, float)
    n = len(x) - (dim - 1) * tau
    if n < 1:
        raise ConfigurationError("series too short for the embedding")
    return np.column_stack([x[i * tau : i * tau + n] for i in range(dim)])


def correlation_distance(returns) -> np.ndarray:
    """Mantegna's metric sqrt(2 (1 - rho)) between the columns of `returns`."""
    rho = np.corrcoef(np.asarray(returns, float).T)
    return np.sqrt(np.clip(2.0 * (1.0 - rho), 0.0, None))


# ---------------------------------------------------------------- trading applications


def landscape_norm_series(
    returns, window: int = 50, dim: int = 1, p: float = 2.0, k: int = 3, n_grid: int = 100
) -> np.ndarray:
    """RK254/RK255 (Gidea & Katz), RK401 (dim 1), RK398/RK403 (dim 2): for each
    day, the window of multi-asset (standardised) returns as a point cloud, its
    dim-`dim` diagram and the Lp norm of its landscape. Causal: day t uses rows
    t-window+1..t; NaN before the first full window."""
    r = np.asarray(returns, float)
    out = np.full(len(r), np.nan)
    for t in range(window - 1, len(r)):
        cloud = r[t - window + 1 : t + 1]
        cloud = (cloud - cloud.mean(0)) / (cloud.std(0) + 1e-12)
        dist = squareform(pdist(cloud))
        dg = rips_persistence(distances=dist, max_dim=dim)[dim]
        grid = np.linspace(0.0, dist.max(), n_grid)
        out[t] = landscape_norm(persistence_landscape(dg, grid, k), grid, p)
    return out


def stress_alert(score, lookback: int = 250, z: float = 2.0) -> np.ndarray:
    """Alert when a score's z-score against its own trailing `lookback` values
    (excluding today) exceeds z."""
    s = np.asarray(score, float)
    out = np.zeros(len(s), bool)
    for t in range(lookback, len(s)):
        hist = s[t - lookback : t]
        hist = hist[np.isfinite(hist)]
        if len(hist) > 2 and np.isfinite(s[t]):
            out[t] = (s[t] - hist.mean()) / (hist.std() + 1e-12) > z
    return out


def tda_exposure(score, lookback: int = 250, z: float = 2.0, floor: float = 0.0) -> np.ndarray:
    """Long-only governor: full exposure, cut to `floor` on a stress alert."""
    return np.where(stress_alert(score, lookback, z), floor, 1.0)


def betti0_contagion(returns, window: int = 60, threshold: float = 1.0) -> np.ndarray:
    """RK262: Betti-0 of the correlation network at distance `threshold` per
    window -- the number of clusters still apart. A fall means assets are
    merging into one block (contagion)."""
    r = np.asarray(returns, float)
    out = np.full(len(r), np.nan)
    for t in range(window - 1, len(r)):
        dg = rips_persistence(distances=correlation_distance(r[t - window + 1 : t + 1]), max_dim=0)
        out[t] = betti_curve(dg[0], [threshold])[0]
    return out


def diagram_clusters(diagrams, n_clusters: int = 2, q: float = 2.0) -> tuple[np.ndarray, int]:
    """RK263: cluster diagrams by Wasserstein distance (average linkage); the
    crisis cluster is the one with the highest mean total persistence.
    Returns (labels, crisis label)."""
    n = len(diagrams)
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            dist[i, j] = dist[j, i] = diagram_distance(diagrams[i], diagrams[j], q)
    labels = fcluster(linkage(squareform(dist), "average"), n_clusters, "maxclust")
    tp = np.array([total_persistence(dg) for dg in diagrams])
    crisis = max(set(labels), key=lambda c: tp[labels == c].mean())
    return labels, int(crisis)


def betti2_macro_stress(series, dim: int = 4, tau: int = 1, window: int = 30) -> np.ndarray:
    """RK265: total H2 persistence of the delay embedding of a macro series
    (or standardised panel rows) over trailing windows."""
    x = np.asarray(series, float)
    cloud = delay_embedding(x, dim, tau) if x.ndim == 1 else x
    out = np.full(len(cloud), np.nan)
    for t in range(window - 1, len(cloud)):
        win = cloud[t - window + 1 : t + 1]
        win = (win - win.mean(0)) / (win.std(0) + 1e-12)
        out[t] = total_persistence(rips_persistence(win, max_dim=2)[2])
    return out


def multiscale_rips_score(returns, windows=(20, 40, 60), lookback: int = 120) -> np.ndarray:
    """RK268: average over window lengths and dims 0-1 of the z-scored total
    persistence -- one multi-scale topological risk score."""
    r = np.asarray(returns, float)
    parts = []
    for w in windows:
        tp = np.full((len(r), 2), np.nan)
        for t in range(w - 1, len(r)):
            cloud = r[t - w + 1 : t + 1]
            dg = rips_persistence((cloud - cloud.mean(0)) / (cloud.std(0) + 1e-12), max_dim=1)
            tp[t] = total_persistence(dg[0]), total_persistence(dg[1])
        for col in tp.T:
            z = np.full(len(r), np.nan)
            for t in range(lookback, len(r)):
                hist = col[t - lookback : t]
                hist = hist[np.isfinite(hist)]
                if len(hist) > 2 and np.isfinite(col[t]):
                    z[t] = (col[t] - hist.mean()) / (hist.std() + 1e-12)
            parts.append(z)
    with np.errstate(all="ignore"):
        stacked = np.array(parts)
        valid = np.isfinite(stacked).any(axis=0)
        out = np.full(len(r), np.nan)
        out[valid] = np.nanmean(stacked[:, valid], axis=0)
    return out
