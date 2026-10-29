"""
Quantum and quantum-inspired entries of the ranked list (ledger RK223,
RK229, RK236, RK238, RK260, RK270, RK305, RK375, RK387, RK389, RK393,
RK397, RK420). There is no quantum hardware here: every "quantum" step is
either an exact statevector simulation (QAOA, adiabatic evolution, feature-
map kernels, variational circuits, amplitude estimation with simulated
shots) or the classical stand-in the papers benchmark against (simulated
annealing for an annealer). Problem sizes are therefore toy-scale (about
<= 14 binary variables). Research code: the pages record no evidence that
any of these beat a classical solver or learner on financial data.

Sources:

  * Portfolio selection as a QUBO -- Rosenberg et al., "Solving the optimal
    trading trajectory problem using a quantum annealer", IEEE J. Sel. Top.
    Signal Process. 10, 2016 (also the execution QUBO of RK420); Venturelli
    & Kondratyev, Quantum Mach. Intell. 1, 2019.
  * Adiabatic computation -- Farhi, Goldstone, Gutmann & Sipser, 2000;
    QAOA -- Farhi, Goldstone & Gutmann, arXiv:1411.4028, 2014.
  * Simulated annealing -- Kirkpatrick, Gelatt & Vecchi, Science 220, 1983.
  * Tensor networks for portfolio optimisation -- Mugel et al., "Dynamic
    portfolio optimization with real datasets using quantum processors and
    quantum-inspired tensor networks", Phys. Rev. Research 4, 2022 (an MPS
    optimised by DMRG-style sweeps; here over a diagonal QUBO Hamiltonian).
  * Quantum risk analysis -- Woerner & Egger, npj Quantum Inf. 5, 2019;
    maximum-likelihood amplitude estimation -- Suzuki et al., Quantum Inf.
    Process. 19, 2020.
  * Binary matrix factorisation on an annealer -- O'Malley, Vesselinov,
    Alexandrov & Alexandrov, PLoS ONE 13, 2018.
  * ZZ feature-map kernels -- Havlicek et al., Nature 567, 2019; variational
    circuits and the parameter-shift rule -- Mitarai et al., Phys. Rev. A 98,
    2018; Schuld et al., Phys. Rev. A 99, 2019.
  * Entropic value-at-risk -- Ahmadi-Javid, J. Optim. Theory Appl. 155, 2012.
  * Simplified graph convolution (parameter-free propagation) -- Wu et al.,
    ICML 2019.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize
from scipy.special import logsumexp
from sklearn.svm import SVC, SVR

from engine.core.exceptions import ConfigurationError
from research.catalog.leads import almgren_chriss

_MAX_QUBITS = 14

# ---------------------------------------------------------------- QUBO and annealing


def bitstrings(n: int) -> np.ndarray:
    """All 2^n bitstrings, row x holding qubit q at bit (n - 1 - q) of x."""
    if n > _MAX_QUBITS:
        raise ConfigurationError(f"{n} binary variables exceed the {_MAX_QUBITS}-qubit simulator")
    return (np.arange(2**n)[:, None] >> (n - 1 - np.arange(n))) & 1


def qubo_energy(q, x, offset: float = 0.0) -> np.ndarray:
    """x'Qx + offset for one bitstring or a batch (rows). Q symmetric, linear
    terms on its diagonal (x_i^2 = x_i)."""
    x = np.asarray(x, float)
    return np.einsum("...i,ij,...j->...", x, np.asarray(q, float), x) + offset


def portfolio_qubo(mu, cov, k: int, risk_aversion: float = 1.0, penalty: float | None = None):
    """Select k of n assets (equal weight 1/k): minimise
    risk_aversion x'Cov x / k^2 - mu'x / k + penalty (sum x - k)^2. Returns (Q, offset)."""
    mu, cov = np.asarray(mu, float), np.asarray(cov, float)
    n = len(mu)
    pen = penalty if penalty is not None else 2.0 * (np.abs(mu).max() / k + np.abs(cov).max())
    q = risk_aversion * cov / k**2 + pen * np.ones((n, n))
    q[np.diag_indices(n)] += -mu / k - 2.0 * pen * k
    return q, pen * k**2


def brute_force(q, offset: float = 0.0) -> tuple[np.ndarray, float]:
    x = bitstrings(len(q))
    e = qubo_energy(q, x, offset)
    i = int(np.argmin(e))
    return x[i], float(e[i])


def simulated_annealing(
    q,
    offset: float = 0.0,
    sweeps: int = 500,
    t0: float | None = None,
    t1: float = 1e-3,
    restarts: int = 5,
    rng=None,
) -> tuple[np.ndarray, float]:
    """Single-flip Metropolis annealing on a QUBO with a geometric schedule --
    the classical baseline every annealer paper reports."""
    rng = np.random.default_rng(rng)
    q = np.asarray(q, float)
    q = (q + q.T) / 2
    n = len(q)
    t0 = t0 if t0 is not None else max(np.abs(q).sum(1).max(), 1e-9)
    temps = t0 * (t1 / t0) ** np.linspace(0, 1, sweeps)
    best_x, best_e = None, np.inf
    for _ in range(restarts):
        x = rng.integers(0, 2, n).astype(float)
        field = q @ x
        for temp in temps:
            for i in rng.permutation(n):
                s = 1.0 - 2.0 * x[i]
                delta = q[i, i] + 2.0 * s * field[i]
                if delta <= 0 or rng.random() < np.exp(-delta / temp):
                    x[i] += s
                    field += s * q[:, i]
        e = float(qubo_energy(q, x, offset))
        if e < best_e:
            best_x, best_e = x.astype(int), e
    return best_x, best_e


def anneal_objective(
    objective,
    n: int,
    sweeps: int = 200,
    t0: float = 1.0,
    t1: float = 1e-3,
    rng=None,
    cardinality: int | None = None,
) -> tuple[np.ndarray, float]:
    """Annealing for a non-quadratic objective over bitstrings (e.g. EVaR).
    With `cardinality` the moves are swaps, so exactly that many bits stay on."""
    rng = np.random.default_rng(rng)
    x = np.zeros(n, int)
    if cardinality is not None:
        x[rng.permutation(n)[:cardinality]] = 1
    cur = objective(x)
    best_x, best = x.copy(), cur
    for temp in t0 * (t1 / t0) ** np.linspace(0, 1, sweeps):
        y = x.copy()
        if cardinality is None:
            y[rng.integers(n)] ^= 1
        else:  # swap one held for one not held
            on, off = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
            y[rng.choice(on)], y[rng.choice(off)] = 0, 1
        val = objective(y)
        if val <= cur or rng.random() < np.exp(-(val - cur) / temp):
            x, cur = y, val
            if cur < best:
                best_x, best = x.copy(), cur
    return best_x, float(best)


# ---------------------------------------------------------------- statevector simulator

_H = np.array([[1, 1], [1, -1]], complex) / np.sqrt(2)


def rx(theta):
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]])


def ry(theta):
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -s], [s, c]], complex)


def rz(theta):
    return np.array([[np.exp(-0.5j * theta), 0], [0, np.exp(0.5j * theta)]])


def apply_gate(psi: np.ndarray, gate: np.ndarray, qubit: int) -> np.ndarray:
    """psi has shape (batch, 2, ..., 2); gate is (2, 2) or per-sample (batch, 2, 2)."""
    psi = np.moveaxis(psi, qubit + 1, -1)
    psi = psi @ gate.T if gate.ndim == 2 else np.einsum("b...j,bij->b...i", psi, gate)
    return np.moveaxis(psi, -1, qubit + 1)


def apply_cnot(psi: np.ndarray, control: int, target: int) -> np.ndarray:
    psi = psi.copy()
    idx = [slice(None)] * psi.ndim
    idx[control + 1] = 1
    sub = psi[tuple(idx)]
    psi[tuple(idx)] = np.flip(sub, axis=target + 1 if target < control else target)
    return psi


def plus_state(n: int, batch: int = 1) -> np.ndarray:
    return np.full((batch,) + (2,) * n, 2 ** (-n / 2), complex)


def expect_z(psi: np.ndarray, qubit: int) -> np.ndarray:
    p = np.abs(np.moveaxis(psi, qubit + 1, 1)) ** 2
    return p[:, 0].reshape(len(p), -1).sum(1) - p[:, 1].reshape(len(p), -1).sum(1)


def _mixer(psi, beta, n):
    g = rx(2.0 * beta)
    for qb in range(n):
        psi = apply_gate(psi, g, qb)
    return psi


def _scaled(energies):
    e = np.asarray(energies, float)
    span = e.max() - e.min()
    return (e - e.min()) / (span if span > 0 else 1.0)


def qaoa(q, offset: float = 0.0, layers: int = 2, restarts: int = 4, rng=None) -> dict:
    """QAOA on the QUBO's diagonal Hamiltonian (exact statevector): optimise
    the 2p angles of the expected (rescaled) energy, then read the most
    probable bitstring."""
    rng = np.random.default_rng(rng)
    n = len(q)
    x = bitstrings(n)
    e = qubo_energy(q, x, offset)
    es = _scaled(e)

    def state(angles):
        psi = plus_state(n)
        for g, b in zip(angles[:layers], angles[layers:], strict=True):
            psi = psi * np.exp(-1j * g * np.pi * es).reshape(psi.shape)
            psi = _mixer(psi, b, n)
        return np.abs(psi.reshape(-1)) ** 2

    best = None
    for _ in range(restarts):
        res = minimize(
            lambda a: state(a) @ es,
            rng.uniform(0, 1, 2 * layers),
            method="Nelder-Mead",
            options={"maxiter": 400 * layers},
        )
        if best is None or res.fun < best.fun:
            best = res
    probs = state(best.x)
    i = int(np.argmax(probs))
    return {
        "x": x[i],
        "energy": float(e[i]),
        "probabilities": probs,
        "angles": best.x,
        "expected_energy": float(probs @ e),
    }


def adiabatic_evolution(q, offset: float = 0.0, total_time: float = 30.0, steps: int = 300) -> dict:
    """Trotterised H(s) = (1 - s)(-sum X) + s H_QUBO from |+>^n (RK229/RK236/RK305):
    slow enough evolution ends near the ground state."""
    n = len(q)
    x = bitstrings(n)
    e = qubo_energy(q, x, offset)
    es = _scaled(e) * n  # comparable scale to the mixer's gap
    dt = total_time / steps
    psi = plus_state(n)
    for k in range(1, steps + 1):
        s = k / steps
        psi = psi * np.exp(-1j * dt * s * es).reshape(psi.shape)
        psi = _mixer(psi, -dt * (1 - s), n)
    probs = np.abs(psi.reshape(-1)) ** 2
    i = int(np.argmax(probs))
    return {
        "x": x[i],
        "energy": float(e[i]),
        "probabilities": probs,
        "ground_probability": float(probs[e <= e.min() + 1e-12].sum()),
    }


# ---------------------------------------------------------------- tensor networks (RK223, RK238)


def mps_minimize(
    q, offset: float = 0.0, bond_dim: int = 2, sweeps: int = 4, restarts: int = 4, rng=None
) -> dict:
    """A real MPS psi(x) = A1[x1]...An[xn] optimised by DMRG-style site
    updates: with all other tensors fixed psi is linear in A_i, so the energy is
    a ratio of quadratic forms and the update is a generalised eigenproblem.
    Like any local sweep it can stop in a local minimum -- under a cardinality
    penalty a single site cannot swap two holdings -- so it is a heuristic and
    the best of `restarts` random starts is returned."""
    rng = np.random.default_rng(rng)
    n = len(q)
    x = bitstrings(n)
    e = qubo_energy(q, x, offset)
    dims = [1] + [bond_dim] * (n - 1) + [1]

    def env(mps, sites):
        m = np.ones((len(x), 1, 1))
        for j in sites:
            m = np.einsum("xab,xbc->xac", m, mps[j][x[:, j]])
        return m

    best = None
    for _ in range(restarts):
        mps = [rng.normal(size=(2, dims[i], dims[i + 1])) for i in range(n)]
        for _ in range(sweeps):
            for i in [*range(n), *range(n - 2, 0, -1)]:
                left = env(mps, range(i))[:, 0, :]  # (X, d_l)
                right = env(mps, range(i + 1, n))[:, :, 0]  # (X, d_r)
                dl, dr = dims[i], dims[i + 1]
                v = np.zeros((len(x), 2, dl, dr))
                v[np.arange(len(x)), x[:, i]] = left[:, :, None] * right[:, None, :]
                v = v.reshape(len(x), -1)
                h, nrm = v.T @ (e[:, None] * v), v.T @ v
                # Solve in the range of the norm matrix: directions psi does not
                # depend on would otherwise give spurious 0/0 eigenvalues.
                s_vals, s_vecs = np.linalg.eigh(nrm)
                keep = s_vals > 1e-10 * s_vals.max()
                w = s_vecs[:, keep] / np.sqrt(s_vals[keep])
                a = w @ eigh(w.T @ h @ w)[1][:, 0]
                mps[i] = (a / np.linalg.norm(a)).reshape(2, dl, dr)
        psi = env(mps, range(n))[:, 0, 0]
        probs = psi**2 / (psi**2).sum()
        k = int(np.argmax(probs))
        if best is None or e[k] < best["energy"]:
            best = {
                "x": x[k],
                "energy": float(e[k]),
                "expected_energy": float(probs @ e),
                "mps": mps,
            }
    return best


# ---------------------------------------------------------------- applications


def rebalance_qubo(
    current,
    mu,
    cov,
    lots: int = 3,
    unit: float | None = None,
    risk_aversion: float = 1.0,
    cost: float = 0.01,
    budget_penalty: float = 10.0,
):
    """RK229/RK305: integer target lots per asset encoded in `lots` bits each
    (w_i = unit * sum_b 2^b x_ib); minimise risk - return + quadratic trading
    cost to `current` + a budget penalty (sum w - 1)^2. Returns (Q, offset, decode)."""
    w0, mu, cov = (np.asarray(a, float) for a in (current, mu, cov))
    n = len(mu)
    unit = unit if unit is not None else 1.0 / (2**lots - 1)
    enc = np.kron(np.eye(n), unit * 2.0 ** np.arange(lots))  # (n, n*lots): w = enc @ x
    quad = risk_aversion * cov + cost * np.eye(n) + budget_penalty * np.ones((n, n))
    lin = -mu - 2 * cost * w0 - 2 * budget_penalty * np.ones(n)
    q = enc.T @ quad @ enc
    q[np.diag_indices_from(q)] += enc.T @ lin
    offset = cost * w0 @ w0 + budget_penalty

    def decode(bits):
        return enc @ np.asarray(bits, float)

    return q, offset, decode


def sgc_scores(signal, adjacency, hops: int = 2) -> np.ndarray:
    """Parameter-free graph convolution (RK236's GNN stage): smooth a signal
    over the normalised adjacency with self-loops, `hops` times."""
    a = np.asarray(adjacency, float) + np.eye(len(adjacency))
    d = 1.0 / np.sqrt(a.sum(1))
    a_hat = d[:, None] * a * d[None, :]
    s = np.asarray(signal, float)
    for _ in range(hops):
        s = a_hat @ s
    return s


def gnn_adiabatic_portfolio(mu, cov, adjacency, k: int, **kw) -> dict:
    """RK236: graph-smoothed expected returns, then adiabatic QUBO selection."""
    q, off = portfolio_qubo(sgc_scores(mu, adjacency), cov, k)
    return adiabatic_evolution(q, off, **kw)


def mps_portfolio(mu, cov, k: int, bond_dim: int = 2, rng=None) -> dict:
    """RK223/RK238: the selection QUBO solved by the tensor-network optimiser."""
    q, off = portfolio_qubo(mu, cov, k)
    return mps_minimize(q, off, bond_dim=bond_dim, rng=rng)


def amplitude_estimate(a: float, schedule=(0, 1, 2, 4, 8), shots: int = 100, rng=None) -> float:
    """MLAE: after m Grover iterations a measurement succeeds with probability
    sin^2((2m + 1) theta), sin^2 theta = a. Simulate the shots and return the
    maximum-likelihood a."""
    rng = np.random.default_rng(rng)
    theta = np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    grid = np.linspace(1e-6, np.pi / 2 - 1e-6, 20001)
    ll = np.zeros_like(grid)
    for m in schedule:
        hits = rng.binomial(shots, np.sin((2 * m + 1) * theta) ** 2)
        p = np.clip(np.sin((2 * m + 1) * grid) ** 2, 1e-12, 1 - 1e-12)
        ll += hits * np.log(p) + (shots - hits) * np.log(1 - p)
    return float(np.sin(grid[np.argmax(ll)]) ** 2)


def quantum_var(losses, probs, alpha: float = 0.95, rng=None, **kw) -> float:
    """RK260 (Woerner & Egger): VaR by bisection over the loss grid, each tail
    probability P(L > l) estimated by simulated amplitude estimation of the
    state that loads `probs` and flags losses above l."""
    rng = np.random.default_rng(rng)
    order = np.argsort(losses)
    grid, p = np.asarray(losses, float)[order], np.asarray(probs, float)[order]
    p = p / p.sum()
    lo, hi = 0, len(grid) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if amplitude_estimate(p[grid > grid[mid]].sum(), rng=rng, **kw) <= 1 - alpha:
            hi = mid
        else:
            lo = mid + 1
    return float(grid[lo])


def binary_matrix_factorization(
    r, k: int, iters: int = 10, restarts: int = 5, rng=None
) -> tuple[np.ndarray, np.ndarray]:
    """RK270 (O'Malley et al.): R (assets x days) ~ B F with B binary (factor
    membership) and F real. Alternate: F by least squares, then each row of B
    by solving its QUBO ||r_i - b F||^2 = b'(F F')b - 2 b'F r_i + const
    (exactly for k <= 10, else by annealing). Alternation finds local optima,
    so the best of `restarts` random starts is kept."""
    rng = np.random.default_rng(rng)
    r = np.asarray(r, float)
    best = None
    for _ in range(restarts):
        b = rng.integers(0, 2, (len(r), k))
        for _ in range(iters):
            f = np.linalg.lstsq(b.astype(float), r, rcond=None)[0]
            g = f @ f.T
            for i in range(len(r)):
                q = g.copy()
                q[np.diag_indices(k)] -= 2 * f @ r[i]
                b[i] = brute_force(q)[0] if k <= 10 else simulated_annealing(q, rng=rng)[0]
        f = np.linalg.lstsq(b.astype(float), r, rcond=None)[0]
        err = float(((r - b @ f) ** 2).sum())
        if best is None or err < best[0]:
            best = (err, b.copy(), f)
    return best[1], best[2]


def evar(losses, alpha: float = 0.05) -> float:
    """Entropic VaR: inf_{z>0} (log E[exp(z L)] - log alpha) / z."""
    loss = np.asarray(losses, float)

    def f(logz):
        z = np.exp(logz)
        return (logsumexp(z * loss) - np.log(len(loss)) - np.log(alpha)) / z

    res = minimize(lambda v: f(v[0]), [0.0], method="Nelder-Mead")
    return float(min(res.fun, loss.max()))


def evar_selection(returns, k: int, alpha: float = 0.05, rng=None) -> np.ndarray:
    """RK389: choose k assets (equal weight) minimising the EVaR of the
    portfolio loss, by annealing over the cardinality-k bitstrings."""
    r = np.asarray(returns, float)

    def obj(x):
        return evar(-(r @ x) / max(x.sum(), 1), alpha)

    return anneal_objective(obj, r.shape[1], sweeps=150, rng=rng, cardinality=k)[0]


def covariance_mask_qubo(train_cov, val_cov, adjacency, coupling: float = 0.1):
    """RK397: choose which off-diagonal covariances to keep. Keeping pair e
    changes the validation Frobenius error by s_e^2 - 2 s_e v_e (linear);
    pairs sharing an asset that are linked in the asset graph are coupled
    (-coupling) so the graph favours keeping neighbourhoods together."""
    s, v, a = (np.asarray(m, float) for m in (train_cov, val_cov, adjacency))
    n = len(s)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(pairs)
    q = np.zeros((m, m))
    for e, (i, j) in enumerate(pairs):
        q[e, e] = 2 * (s[i, j] ** 2 - 2 * s[i, j] * v[i, j])
        for f in range(e + 1, m):
            pair = set(pairs[f])
            shared = {i, j} & pair
            others = ({i, j} | pair) - shared
            if len(shared) == 1 and a[tuple(others)] > 0:
                q[e, f] = q[f, e] = -coupling / 2
    return q, pairs


def masked_covariance(train_cov, pairs, keep) -> np.ndarray:
    """Apply a kept-pairs mask and clip eigenvalues so the result is PSD."""
    s = np.asarray(train_cov, float)
    out = np.diag(np.diag(s))
    for (i, j), k in zip(pairs, keep, strict=True):
        if k:
            out[i, j] = out[j, i] = s[i, j]
    vals, vecs = np.linalg.eigh(out)
    return (vecs * np.clip(vals, 1e-10, None)) @ vecs.T


def execution_qubo(
    shares: float,
    periods: int,
    sigma: float,
    eta: float,
    risk_aversion: float,
    bits: int = 3,
    penalty: float | None = None,
):
    """RK420 (Rosenberg et al.): shares sold per period in `bits` binary digits;
    minimise temporary impact eta sum n_k^2 + risk lambda sigma^2 sum x_k^2
    (x = shares still held) + penalty (sum n_k - X)^2. Returns (Q, offset, decode)."""
    unit = shares / (2**bits - 1) * 2 / periods
    enc = np.kron(np.eye(periods), unit * 2.0 ** np.arange(bits))  # n = enc @ bits
    tri = np.tril(np.ones((periods, periods)))  # cumulative sold
    hold = -tri @ enc  # x_k = X - cum_k: linear part
    pen = penalty if penalty is not None else 10.0 * (eta + risk_aversion * sigma**2) * periods
    quad = eta * enc.T @ enc + risk_aversion * sigma**2 * hold.T @ hold
    quad += pen * enc.T @ np.ones((periods, periods)) @ enc
    lin = 2 * risk_aversion * sigma**2 * shares * hold.sum(0) - 2 * pen * shares * enc.sum(0)
    q = quad.copy()
    q[np.diag_indices_from(q)] += lin
    offset = risk_aversion * sigma**2 * shares**2 * periods + pen * shares**2

    def decode(b):
        return enc @ np.asarray(b, float)

    return q, offset, decode


def annealed_execution(
    shares: float,
    periods: int,
    sigma: float,
    eta: float,
    risk_aversion: float,
    bits: int = 3,
    rng=None,
) -> dict:
    """RK420: anneal the execution QUBO and report it next to Almgren-Chriss."""
    q, off, decode = execution_qubo(shares, periods, sigma, eta, risk_aversion, bits)
    x, energy = simulated_annealing(q, off, sweeps=400, rng=rng)
    ac = almgren_chriss(shares, float(periods), periods, sigma, eta, risk_aversion=risk_aversion)
    return {"trades": decode(x), "energy": energy, "almgren_chriss": ac["trades"]}


# ---------------------------------------------------------------- quantum kernels and QNN


def zz_feature_states(x, bandwidth: float = 1.0) -> np.ndarray:
    """Havlicek's ZZ feature map |phi(x)> = U(x) H U(x) H |0>, with
    U(x) = exp(i sum x_i Z_i + i sum_{i<j} (pi - x_i)(pi - x_j) Z_i Z_j),
    applied to bandwidth * x (Shaydulin & Wild, Phys. Rev. A 106, 2022: without
    a bandwidth below 1 the kernel is close to the identity and does not generalise)."""
    x = bandwidth * np.atleast_2d(np.asarray(x, float))
    b, n = x.shape
    z = 1.0 - 2.0 * bitstrings(n)  # (2^n, n) Z eigenvalues
    iu = np.triu_indices(n, 1)
    phase = (
        x @ z.T + ((np.pi - x)[:, iu[0]] * (np.pi - x)[:, iu[1]]) @ (z[:, iu[0]] * z[:, iu[1]]).T
    )
    u = np.exp(1j * phase).reshape((b,) + (2,) * n)
    psi = plus_state(n, b) * u
    for qb in range(n):
        psi = apply_gate(psi, _H, qb)
    return (psi * u).reshape(b, -1)


def quantum_kernel(x, y=None, bandwidth: float = 1.0) -> np.ndarray:
    """k(x, y) = |<phi(x)|phi(y)>|^2."""
    sx = zz_feature_states(x, bandwidth)
    sy = sx if y is None else zz_feature_states(y, bandwidth)
    return np.abs(sx.conj() @ sy.T) ** 2


def qsvm_predict(x_train, y_train, x_test, c: float = 1.0, bandwidth: float = 1.0) -> np.ndarray:
    """RK387: SVM classifier on the precomputed quantum kernel."""
    k_train = quantum_kernel(x_train, bandwidth=bandwidth)
    clf = SVC(kernel="precomputed", C=c).fit(k_train, y_train)
    return clf.predict(quantum_kernel(x_test, x_train, bandwidth))


def qsvr_predict(
    x_train, y_train, x_test, c: float = 1.0, epsilon: float = 0.01, bandwidth: float = 1.0
) -> np.ndarray:
    """RK375: support vector regression on the precomputed quantum kernel."""
    reg = SVR(kernel="precomputed", C=c, epsilon=epsilon)
    reg.fit(quantum_kernel(x_train, bandwidth=bandwidth), y_train)
    return reg.predict(quantum_kernel(x_test, x_train, bandwidth))


class QNNRegressor:
    """RK393: angle-encoded variational circuit (RY(x_i) per qubit, then layers
    of RY/RZ rotations and a CNOT ring), output a * <Z_0> + b. The rotation
    angles are trained by the parameter-shift rule (exact gradients of the
    circuit); a and b by least squares at each step."""

    def __init__(self, n_qubits: int, layers: int = 2, seed: int = 0):
        self.n, self.layers = n_qubits, layers
        self.theta = np.random.default_rng(seed).uniform(-np.pi, np.pi, (layers, n_qubits, 2))
        self.a, self.b = 1.0, 0.0

    def circuit(self, x, theta=None) -> np.ndarray:
        theta = self.theta if theta is None else theta
        x = np.atleast_2d(np.asarray(x, float))
        psi = np.zeros((len(x),) + (2,) * self.n, complex)
        psi[(slice(None),) + (0,) * self.n] = 1.0
        for qb in range(self.n):
            psi = apply_gate(psi, np.stack([ry(v) for v in x[:, qb]]), qb)
        for layer in theta:
            for qb in range(self.n):
                psi = apply_gate(apply_gate(psi, ry(layer[qb, 0]), qb), rz(layer[qb, 1]), qb)
            for qb in range(self.n if self.n > 2 else self.n - 1):
                psi = apply_cnot(psi, qb, (qb + 1) % self.n)
        return expect_z(psi, 0)

    def gradient(self, x, weights) -> np.ndarray:
        """d(sum weights * <Z_0>)/d theta by the parameter-shift rule."""
        g = np.zeros_like(self.theta)
        for idx in np.ndindex(self.theta.shape):
            plus, minus = self.theta.copy(), self.theta.copy()
            plus[idx] += np.pi / 2
            minus[idx] -= np.pi / 2
            g[idx] = weights @ (self.circuit(x, plus) - self.circuit(x, minus)) / 2
        return g

    def fit(self, x, y, steps: int = 60, lr: float = 0.1) -> list[float]:
        y = np.asarray(y, float)
        m, v = np.zeros_like(self.theta), np.zeros_like(self.theta)
        hist = []
        for t in range(1, steps + 1):
            z = self.circuit(x)
            design = np.column_stack([z, np.ones_like(z)])
            self.a, self.b = np.linalg.lstsq(design, y, rcond=None)[0]
            resid = self.a * z + self.b - y
            hist.append(float((resid**2).mean()))
            g = self.gradient(x, 2 * self.a * resid / len(y))
            m = 0.9 * m + 0.1 * g
            v = 0.999 * v + 0.001 * g**2
            self.theta -= lr * (m / (1 - 0.9**t)) / (np.sqrt(v / (1 - 0.999**t)) + 1e-8)
        return hist

    def predict(self, x) -> np.ndarray:
        return self.a * self.circuit(x) + self.b
