"""
Neural time-series forecasters of the ranked list, on the catalog's
autodiff (ledger RK258, RK272, RK275, RK288, RK301, RK316, RK331, RK334,
RK337, RK348, RK407, RK408, RK413). Small, CPU-sized versions of each
architecture; the pages record that accuracy is not profit, and none of
these has independent trading evidence. Research code only.

Sources:

  * Temporal Fusion Transformer -- Lim, Arik, Loeff & Pfister, Int. J.
    Forecasting 37, 2021 (variable selection, LSTM encoder, gated residual,
    interpretable attention, quantile outputs). This version keeps one of
    each block and one attention head.
  * TCN -- Bai, Kolter & Koltun, arXiv:1803.01271, 2018 (dilated causal
    convolutions with residual blocks).
  * DeepLOB -- Zhang, Zohren & Roberts, IEEE Trans. Signal Process. 67,
    2019 (convolutions over the book, an LSTM, three-class labels from the
    smoothed future mid-price change).
  * Neural CDEs -- Kidger, Morrill, Foster & Lyons, NeurIPS 2020; neural RDEs
    (log-signature steps) -- Morrill et al., ICML 2021; Euler discretisation
    dz = f(z) dX here.
  * Neural jump ODEs -- Herrera, Krach & Teichmann, ICLR 2021 (ODE between
    observations, jump at each, loss (|x - y| + |y - y_-|)^2).
  * Neural ODEs -- Chen et al., NeurIPS 2018 (RK4 steps here); phase-space
    reconstruction -- Takens, 1981.
  * Spiking networks with surrogate gradients -- Neftci, Mostafa & Zenke,
    IEEE Signal Process. Mag. 36, 2019 (leaky integrate-and-fire neurons,
    Heaviside forward, sigmoid-derivative backward).
  * Causal Haar a trous wavelets -- Shensa, IEEE Trans. Signal Process. 40,
    1992 (each level averages the previous one with its 2^(j-1)-lagged
    value, so no future data enters a coefficient).
"""

from __future__ import annotations

import numpy as np

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import (
    LSTM,
    MLP,
    Tensor,
    bce_with_logits,
    causal_conv1d,
    concat,
    fit,
    log_softmax,
    mse,
    param,
    softmax,
    stack,
    where,
)
from research.catalog.topology import delay_embedding

# ---------------------------------------------------------------- custom ops


def spike(v: Tensor, slope: float = 5.0) -> Tensor:
    """Heaviside(v) forward; slope * sigmoid'(slope v) backward (surrogate)."""
    sig = 1 / (1 + np.exp(-slope * v.data))
    return Tensor(
        (v.data > 0).astype(float),
        _parents=(v,),
        _backward=lambda g: ((v, g * slope * sig * (1 - sig)),),
    )


def quantile_loss(pred: Tensor, target, quantiles) -> Tensor:
    """Pinball loss; pred (..., Q), target broadcastable to pred."""
    e = Tensor(np.asarray(target, float)) - pred
    q = Tensor(np.asarray(quantiles, float))
    return where(e.data >= 0, e * q, e * (q - 1.0)).mean()


def windows(series, length: int, horizon: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Sliding (input, target) pairs: x[t-length+1..t] -> y[t+1..t+horizon]."""
    x = np.asarray(series, float)
    if len(x) < length + horizon:
        raise ConfigurationError("series shorter than one window plus the horizon")
    xs, ys = [], []
    for t in range(length - 1, len(x) - horizon):
        xs.append(x[t - length + 1 : t + 1])
        ys.append(x[t + 1 : t + 1 + horizon])
    return np.array(xs), np.array(ys)


# ---------------------------------------------------------------- TCN (RK316)


class TCNForecaster:
    """Residual blocks of two dilated causal convolutions (dilations 1, 2, 4, ...);
    the whole series passes through at once, so y_t forecasts x_{t+1}."""

    def __init__(
        self, n_in: int = 1, channels: int = 8, levels: int = 3, kernel: int = 2, seed: int = 0
    ):
        rng = np.random.default_rng(seed)
        self.blocks = []
        c_in = n_in
        for lvl in range(levels):
            self.blocks.append(
                {
                    "d": 2**lvl,
                    "w1": param((kernel, c_in, channels), rng),
                    "b1": param(channels),
                    "w2": param((kernel, channels, channels), rng),
                    "b2": param(channels),
                    "skip": param((c_in, channels), rng) if c_in != channels else None,
                }
            )
            c_in = channels
        self.out = param((channels, 1), rng)
        self.receptive = 1 + 2 * (kernel - 1) * (2**levels - 1)

    @property
    def params(self) -> list[Tensor]:
        ps = [self.out]
        for b in self.blocks:
            ps += [b["w1"], b["b1"], b["w2"], b["b2"]] + (
                [b["skip"]] if b["skip"] is not None else []
            )
        return ps

    def __call__(self, x: Tensor) -> Tensor:
        h = x
        for b in self.blocks:
            y = causal_conv1d(h, b["w1"], b["b1"], b["d"]).relu()
            y = causal_conv1d(y, b["w2"], b["b2"], b["d"]).relu()
            h = (h if b["skip"] is None else h @ b["skip"]) + y
        return (h @ self.out)[:, 0]

    def fit(self, series, steps: int = 300, lr: float = 0.01) -> list[float]:
        s = np.asarray(series, float)
        self.mu, self.sd = s.mean(), s.std() + 1e-12
        z = ((s - self.mu) / self.sd)[:, None]
        r = self.receptive

        def loss():
            pred = self(Tensor(z[:-1]))
            return mse(pred[r:], z[1 + r :, 0])

        return fit(loss, self.params, steps, lr)

    def predict_next(self, series) -> float:
        z = ((np.asarray(series, float) - self.mu) / self.sd)[:, None]
        return float(self(Tensor(z)).data[-1] * self.sd + self.mu)


# ---------------------------------------------------------------- TFT (RK301, RK413)


class TemporalFusionTransformer:
    """Per-step variable selection (softmax weights over the inputs, each
    with its own embedding), an LSTM encoder, a gated residual, one
    interpretable attention head from the last step over the window, and a
    head emitting `quantiles` for each of `horizons` steps ahead."""

    def __init__(
        self,
        n_vars: int,
        hidden: int = 8,
        horizons: int = 3,
        quantiles=(0.1, 0.5, 0.9),
        seed: int = 0,
    ):
        rng = np.random.default_rng(seed)
        self.n_vars, self.h, self.horizons = n_vars, hidden, horizons
        self.quantiles = np.asarray(quantiles, float)
        self.sel = param((n_vars, n_vars), rng)
        self.emb = param((n_vars, hidden), rng)
        self.lstm = LSTM(hidden, hidden, rng)
        self.gate = param((hidden, hidden), rng)
        self.wq, self.wk, self.wv = (param((hidden, hidden), rng) for _ in range(3))
        self.head = MLP([2 * hidden, hidden, horizons * len(quantiles)], rng)

    @property
    def params(self) -> list[Tensor]:
        return [
            self.sel,
            self.emb,
            *self.lstm.params,
            self.gate,
            self.wq,
            self.wk,
            self.wv,
            *self.head.params,
        ]

    def forward(self, x) -> tuple[Tensor, Tensor, Tensor]:
        """x (batch, window, n_vars) -> (quantile forecasts (B, H, Q),
        attention (B, window), variable weights (B, window, n_vars))."""
        x = np.asarray(x, float)
        b, w, _ = x.shape
        xt = Tensor(x.transpose(1, 0, 2))  # (W, B, V)
        vw = softmax(xt @ self.sel, axis=2)  # variable selection weights
        e = (vw * xt) @ self.emb  # (W, B, hidden)
        h, c = self.lstm.zero_state(b)
        outs = []
        for t in range(w):
            h, c = self.lstm.cell(e[t], h, c)
            outs.append(h)
        enc = stack(outs, axis=0)  # (W, B, hidden)
        g = (enc @ self.gate).sigmoid()
        hid = e + g * enc  # gated residual
        q = hid[w - 1] @ self.wq  # (B, hidden)
        k = hid @ self.wk  # (W, B, hidden)
        scores = (k * q).sum(axis=2) * (1 / np.sqrt(self.h))  # (W, B)
        att = softmax(scores, axis=0)
        ctx = (att.reshape(w, b, 1) * (hid @ self.wv)).sum(axis=0)
        out = self.head(concat([hid[w - 1], ctx], axis=1)).reshape(
            b, self.horizons, len(self.quantiles)
        )
        return out, att.T, vw.transpose(1, 0, 2)

    def fit(self, x, y, steps: int = 200, lr: float = 0.01) -> list[float]:
        """x (B, window, n_vars), y (B, horizons): quantile loss."""
        yy = np.asarray(y, float)[:, :, None]
        return fit(
            lambda: quantile_loss(self.forward(x)[0], yy, self.quantiles), self.params, steps, lr
        )

    def predict(self, x) -> np.ndarray:
        return self.forward(x)[0].data


# ---------------------------------------------------------------- DeepLOB (RK275)


def lob_labels(mid, horizon: int = 5, alpha: float = 1e-4) -> np.ndarray:
    """Zhang et al.'s labels: compare the mean of the next `horizon` mids with
    the current mid; 0 = down, 1 = stationary, 2 = up (last horizon rows: 1)."""
    m = np.asarray(mid, float)
    out = np.ones(len(m), int)
    for t in range(len(m) - horizon):
        change = m[t + 1 : t + 1 + horizon].mean() / m[t] - 1
        out[t] = 2 if change > alpha else 0 if change < -alpha else 1
    return out


class DeepLOB:
    """Two causal convolutions over time across the book's features, an LSTM,
    and a three-class head (down / stationary / up)."""

    def __init__(self, n_features: int, channels: int = 8, hidden: int = 8, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.c1, self.b1 = param((2, n_features, channels), rng), param(channels)
        self.c2, self.b2 = param((2, channels, channels), rng), param(channels)
        self.lstm = LSTM(channels, hidden, rng)
        self.head = param((hidden, 3), rng)
        self.hb = param(3)

    @property
    def params(self) -> list[Tensor]:
        return [self.c1, self.b1, self.c2, self.b2, *self.lstm.params, self.head, self.hb]

    def logits(self, x) -> Tensor:
        """x (batch, window, features)."""
        xt = Tensor(np.asarray(x, float).transpose(1, 0, 2))
        h = causal_conv1d(xt, self.c1, self.b1).leaky_relu(0.01)
        h = causal_conv1d(h, self.c2, self.b2, dilation=2).leaky_relu(0.01)
        hs, cs = self.lstm.zero_state(xt.shape[1])
        for t in range(xt.shape[0]):
            hs, cs = self.lstm.cell(h[t], hs, cs)
        return hs @ self.head + self.hb

    def fit(self, x, labels, steps: int = 200, lr: float = 0.01) -> list[float]:
        lab = np.asarray(labels, int)
        return fit(
            lambda: -log_softmax(self.logits(x), axis=1)[np.arange(len(lab)), lab].mean(),
            self.params,
            steps,
            lr,
        )

    def predict(self, x) -> np.ndarray:
        return np.argmax(self.logits(x).data, axis=1)


# ---------------------------------------------------------------- neural CDE family


class NeuralCDE:
    """Euler-discretised neural CDE: z_0 = A x_0, z_{k+1} = z_k + f(z_k) dX_k
    with f(z) an (hidden x channels) matrix field from an MLP (tanh-bounded).
    Paths are (batch, steps, channels), time usually one of the channels."""

    def __init__(self, channels: int, hidden: int = 8, width: int = 16, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.c, self.h = channels, hidden
        self.init = param((channels, hidden), rng)
        self.field = MLP([hidden, width, hidden * channels], rng)

    @property
    def params(self) -> list[Tensor]:
        return [self.init, *self.field.params]

    def states(self, paths) -> list[Tensor]:
        x = np.asarray(paths, float)
        z = Tensor(x[:, 0]) @ self.init
        out = [z]
        for k in range(x.shape[1] - 1):
            f = self.field(z).tanh().reshape(x.shape[0], self.h, self.c)
            dx = Tensor(x[:, k + 1] - x[:, k]).reshape(x.shape[0], self.c, 1)
            z = z + (f @ dx).reshape(x.shape[0], self.h)
            out.append(z)
        return out


def log_signature_steps(path, window: int) -> np.ndarray:
    """RK331's neural-RDE input: each window's depth-2 log-signature
    (increments and Levy areas), as one step of a coarser path. path (T, d)
    -> cumulative path of shape (T // window + 1, d + d(d-1)/2)."""
    p = np.asarray(path, float)
    d = p.shape[1]
    iu = np.triu_indices(d, 1)
    steps = [np.zeros(d + len(iu[0]))]
    for s in range(0, len(p) - window + 1, window):
        seg = p[s : s + window + 1] if s + window < len(p) else p[s:]
        inc = seg[-1] - seg[0]
        dx = np.diff(seg - seg[0], axis=0)
        mid = seg[:-1] - seg[0]
        area = 0.5 * (mid.T @ dx - dx.T @ mid)
        steps.append(steps[-1] + np.r_[inc, area[iu]])
    return np.array(steps)


class CDEClassifier:
    """RK334 (and RK331 on log-signature paths): a neural CDE over the order-book
    path with a logistic head on the final state -> P(up-move)."""

    def __init__(self, channels: int, hidden: int = 8, seed: int = 0):
        self.cde = NeuralCDE(channels, hidden, seed=seed)
        self.w = param((hidden, 1), np.random.default_rng(seed + 1))
        self.b = param(1)

    def logit(self, paths) -> Tensor:
        return (self.cde.states(paths)[-1] @ self.w + self.b)[:, 0]

    def fit(self, paths, labels, steps: int = 200, lr: float = 0.02) -> list[float]:
        y = np.asarray(labels, float)
        return fit(
            lambda: bce_with_logits(self.logit(paths), y),
            [*self.cde.params, self.w, self.b],
            steps,
            lr,
        )

    def predict_proba(self, paths) -> np.ndarray:
        return 1 / (1 + np.exp(-self.logit(paths).data))


class CDEJumpPricer:
    """RK337: neural CDE state -> next mid-price return distribution as a
    two-component mixture: N(mu, s^2) with probability 1 - p and a jump
    N(mu + J, s^2 + sJ^2) with probability p; trained by its likelihood."""

    def __init__(self, channels: int, hidden: int = 8, seed: int = 0):
        self.cde = NeuralCDE(channels, hidden, seed=seed)
        self.head = MLP([hidden, 8, 5], np.random.default_rng(seed + 1))

    def _params(self, paths):
        o = self.head(self.cde.states(paths)[-1])
        mu, log_s, logit_p, jump, log_sj = (o[:, i] for i in range(5))
        return mu, log_s.clip(-6, 3).exp(), logit_p.sigmoid() * 0.5, jump, log_sj.clip(-6, 3).exp()

    def nll(self, paths, nxt) -> Tensor:
        y = Tensor(np.asarray(nxt, float))
        mu, s, p, jump, sj = self._params(paths)
        s2, j2 = s * s, s * s + sj * sj
        n0 = (-((y - mu) ** 2) / (s2 * 2.0)).exp() / (s2 * (2 * np.pi)).sqrt()
        n1 = (-((y - mu - jump) ** 2) / (j2 * 2.0)).exp() / (j2 * (2 * np.pi)).sqrt()
        return -(((1.0 - p) * n0 + p * n1) + 1e-12).log().mean()

    def fit(self, paths, nxt, steps: int = 200, lr: float = 0.01) -> list[float]:
        return fit(lambda: self.nll(paths, nxt), [*self.cde.params, *self.head.params], steps, lr)

    def expected_return(self, paths) -> np.ndarray:
        mu, _, p, jump, _ = self._params(paths)
        return (mu + p * jump).data


class CDEIntensityExecution:
    """RK288: a neural CDE over the market path drives the intensity
    lambda_k = softplus(w'z_k) of favourable events (e.g. contra-side
    liquidity arrivals); it is fitted by the point-process likelihood
    sum log lambda_k dN_k - sum lambda_k dt, and the execution rule trades
    when the predicted intensity is above its median."""

    def __init__(self, channels: int, hidden: int = 8, seed: int = 0):
        self.cde = NeuralCDE(channels, hidden, seed=seed)
        self.w = param((hidden, 1), np.random.default_rng(seed + 1))

    def intensity(self, paths) -> Tensor:
        zs = stack(self.cde.states(paths), axis=1)  # (B, T, hidden)
        return (zs @ self.w)[..., 0].softplus() + 1e-6

    def fit(self, paths, counts, dt: float = 1.0, steps: int = 200, lr: float = 0.02):
        n = np.asarray(counts, float)

        def nll():
            lam = self.intensity(paths)
            return -((lam.log() * Tensor(n)).sum() - (lam * dt).sum()) * (1 / n.size)

        return fit(nll, [*self.cde.params, self.w], steps, lr)

    def trade_signal(self, paths) -> np.ndarray:
        lam = self.intensity(paths).data
        return lam > np.median(lam, axis=1, keepdims=True)


# ---------------------------------------------------------------- neural ODEs (RK348, RK408)


def rk4_step(f, z: Tensor, dt: float = 1.0) -> Tensor:
    k1 = f(z)
    k2 = f(z + k1 * (dt / 2))
    k3 = f(z + k2 * (dt / 2))
    k4 = f(z + k3 * dt)
    return z + (k1 + k2 * 2.0 + k3 * 2.0 + k4) * (dt / 6)


class PSRNeuralODE:
    """RK348: delay-embed the standardised series (dimension m, lag 1) and fit
    a neural ODE whose one-unit RK4 flow maps each embedded state to the next."""

    def __init__(self, dim: int = 3, width: int = 16, seed: int = 0):
        self.dim = dim
        self.f = MLP([dim, width, dim], np.random.default_rng(seed))

    def fit(self, series, steps: int = 300, lr: float = 0.01) -> list[float]:
        s = np.asarray(series, float)
        self.mu, self.sd = s.mean(), s.std() + 1e-12
        emb = delay_embedding((s - self.mu) / self.sd, self.dim, 1)
        return fit(
            lambda: mse(rk4_step(self.f, Tensor(emb[:-1])), emb[1:]), self.f.params, steps, lr
        )

    def forecast(self, series, steps: int = 1) -> np.ndarray:
        z = (np.asarray(series, float)[-self.dim :] - self.mu) / self.sd
        out, state = [], Tensor(z[None])
        for _ in range(steps):
            state = rk4_step(self.f, state)
            out.append(state.data[0, -1] * self.sd + self.mu)
        return np.array(out)


class NeuralJumpODE:
    """RK408: hidden state follows dh = f(h) dt between observations on a time
    grid and jumps to j(h, x) at each; y = g(h) is the prediction. Batched
    paths share the grid; `mask` (batch, steps) marks observations."""

    def __init__(self, hidden: int = 8, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.f = MLP([hidden, 16, hidden], rng)
        self.j = MLP([hidden + 1, 16, hidden], rng)
        self.g = MLP([hidden, 1], rng)
        self.hidden = hidden

    @property
    def params(self) -> list[Tensor]:
        return [*self.f.params, *self.j.params, *self.g.params]

    def run(self, values, mask, dt: float):
        v, m = np.asarray(values, float), np.asarray(mask, bool)
        b, n = v.shape
        h = Tensor(np.zeros((b, self.hidden)))
        preds, before, after = [], [], []
        for k in range(n):
            if k:
                h = h + self.f(h).tanh() * dt
            y_minus = self.g(h)[:, 0]
            jumped = self.j(concat([h, Tensor(v[:, k : k + 1])], axis=1)).tanh()
            h = where(m[:, k : k + 1], jumped, h)
            y = self.g(h)[:, 0]
            preds.append(y)
            before.append(y_minus)
            after.append(y)
        return preds, before, after

    def loss(self, values, mask, dt: float) -> Tensor:
        v, m = np.asarray(values, float), np.asarray(mask, bool)
        _, before, after = self.run(v, m, dt)
        total, count = Tensor(0.0), max(int(m.sum()), 1)
        for k in range(v.shape[1]):
            if m[:, k].any():
                e1 = ((Tensor(v[:, k]) - after[k]) ** 2 + 1e-12).sqrt()
                e2 = ((after[k] - before[k]) ** 2 + 1e-12).sqrt()
                total = total + (((e1 + e2) ** 2) * Tensor(m[:, k].astype(float))).sum()
        return total * (1.0 / count)

    def fit(self, values, mask, dt: float, steps: int = 200, lr: float = 0.01) -> list[float]:
        return fit(lambda: self.loss(values, mask, dt), self.params, steps, lr)

    def predict(self, values, mask, dt: float) -> np.ndarray:
        return np.column_stack([p.data for p in self.run(values, mask, dt)[0]])


# ---------------------------------------------------------------- spiking networks (RK258, RK407)


class SpikingLayer:
    """Leaky integrate-and-fire: v <- beta v + input - threshold * spike_prev;
    spike = H(v - threshold) with a surrogate gradient."""

    def __init__(self, n_in: int, n_out: int, beta: float = 0.8, threshold: float = 1.0, rng=None):
        self.w = param((n_in, n_out), np.random.default_rng(rng))
        self.beta, self.threshold = beta, threshold

    def run(self, inputs: Tensor) -> Tensor:
        """inputs (T, B, n_in) -> spike counts (B, n_out)."""
        t_steps, b = inputs.shape[0], inputs.shape[1]
        v = Tensor(np.zeros((b, self.w.shape[1])))
        s = Tensor(np.zeros((b, self.w.shape[1])))
        count = Tensor(np.zeros((b, self.w.shape[1])))
        for t in range(t_steps):
            v = v * self.beta + inputs[t] @ self.w - s * self.threshold
            s = spike(v - self.threshold)
            count = count + s
        return count


def delta_spike_encode(series, threshold: float) -> np.ndarray:
    """Delta modulation: an up (down) spike whenever the series has moved by
    `threshold` above (below) the last spiking level. Returns (T, 2)."""
    x = np.asarray(series, float)
    level, out = x[0], np.zeros((len(x), 2))
    for t, v in enumerate(x):
        if v - level >= threshold:
            out[t, 0], level = 1.0, v
        elif level - v >= threshold:
            out[t, 1], level = 1.0, v
    return out


class SpikingScalper:
    """RK407: delta-modulated spike trains of the order-flow imbalance and the
    mid-price drive a LIF layer; a logistic readout of the spike counts
    predicts the next move (up vs not), trained with surrogate gradients."""

    def __init__(self, n_in: int = 4, hidden: int = 8, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.layer = SpikingLayer(n_in, hidden, rng=rng)
        self.w, self.b = param((hidden, 1), rng), param(1)

    def logit(self, spikes) -> Tensor:
        """spikes (B, T, n_in)."""
        x = Tensor(np.asarray(spikes, float).transpose(1, 0, 2) * 2.0)
        return (self.layer.run(x) @ self.w + self.b)[:, 0]

    def fit(self, spikes, labels, steps: int = 200, lr: float = 0.05) -> list[float]:
        y = np.asarray(labels, float)
        return fit(
            lambda: bce_with_logits(self.logit(spikes), y),
            [self.layer.w, self.w, self.b],
            steps,
            lr,
        )

    def predict_proba(self, spikes) -> np.ndarray:
        return 1 / (1 + np.exp(-self.logit(spikes).data))


class SpikingGCN:
    """RK258: node inputs are spike trains of each company's shocks; at each
    step the LIF layer integrates its own and its neighbours' spikes (graph
    convolution with the normalised adjacency), and a logistic readout per
    node predicts a shock next period."""

    def __init__(self, hidden: int = 4, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.layer = SpikingLayer(2, hidden, rng=rng)
        self.w, self.b = param((hidden, 1), rng), param(1)

    def logit(self, shock_windows, adjacency) -> Tensor:
        """shock_windows (B, T, nodes) binary; returns (B, nodes) logits."""
        s = np.asarray(shock_windows, float)
        a = np.asarray(adjacency, float)
        deg = a.sum(0)
        a_hat = np.divide(a, deg, out=np.zeros_like(a), where=deg > 0)
        b, t, n = s.shape
        feats = np.stack([s, s @ a_hat], axis=3)  # (B, T, nodes, 2)
        x = Tensor(feats.transpose(1, 0, 2, 3).reshape(t, b * n, 2) * 2.0)
        counts = self.layer.run(x)  # (B * nodes, hidden)
        return (counts @ self.w + self.b).reshape(b, n)

    def fit(self, shock_windows, adjacency, targets, steps: int = 200, lr: float = 0.05):
        y = np.asarray(targets, float)
        return fit(
            lambda: bce_with_logits(self.logit(shock_windows, adjacency), y),
            [self.layer.w, self.w, self.b],
            steps,
            lr,
        )


# ---------------------------------------------------------------- wavelet network (RK272)


def causal_haar(series, levels: int = 3) -> tuple[np.ndarray, list[np.ndarray]]:
    """A trous Haar with causal filters: s_j(t) = (s_{j-1}(t) + s_{j-1}(t - 2^(j-1))) / 2,
    d_j = s_{j-1} - s_j; early points reuse the first value. No coefficient at
    t uses data after t."""
    s = np.asarray(series, float)
    details = []
    for j in range(1, levels + 1):
        lag = 2 ** (j - 1)
        prev = np.r_[np.full(lag, s[0]), s[:-lag]]
        smooth = 0.5 * (s + prev)
        details.append(s - smooth)
        s = smooth
    return s, details


class WaveletScalper:
    """RK272: features at t = causal Haar details and (smooth - price), scaled;
    an MLP predicts P(next return > 0); long when it exceeds `enter`."""

    def __init__(self, levels: int = 3, hidden: int = 8, seed: int = 0):
        self.levels = levels
        self.net = MLP([levels + 1, hidden, 1], np.random.default_rng(seed))

    def features(self, prices) -> np.ndarray:
        p = np.log(np.asarray(prices, float))
        smooth, details = causal_haar(p, self.levels)
        f = np.column_stack([*details, smooth - p])
        return f / (np.abs(f).std(0) + 1e-12)

    def fit(self, prices, steps: int = 300, lr: float = 0.02) -> list[float]:
        p = np.asarray(prices, float)
        f = self.features(p)[:-1]
        y = (np.diff(np.log(p)) > 0).astype(float)
        return fit(
            lambda: bce_with_logits(self.net(Tensor(f))[:, 0], y), self.net.params, steps, lr
        )

    def positions(self, prices, enter: float = 0.55) -> np.ndarray:
        prob = 1 / (1 + np.exp(-self.net(Tensor(self.features(prices))).data[:, 0]))
        return (prob > enter).astype(float)
