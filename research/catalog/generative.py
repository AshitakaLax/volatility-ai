"""
Generative scenario models of the ranked list (ledger RK200, RK228,
RK332, RK336, RK343, RK349, RK373, RK378, RK383, RK390, RK395, RK399,
RK402, RK405). They synthesise returns, curves, order flow or rankings for
stress tests; none is a trading signal by itself, and the pages found no
evidence that any beats historical simulation. Small CPU versions on the
catalog's autodiff; research code only.

Sources:

  * DDPM -- Ho, Jain & Abbeel, NeurIPS 2020 (predict the added noise; the
    ancestral sampler with sigma_t^2 = beta_t); score-based view -- Song et
    al., ICLR 2021.
  * Flow matching -- Lipman, Chen, Ben-Hamu, Nickel & Le, "Flow matching for
    generative modeling", ICLR 2023 (regress v(x_t, t) on x1 - x0 along
    straight paths, then integrate the ODE).
  * Diffusion factor models -- Chen, Xu, Xu & Zhang, "Diffusion factor
    models", 2025: the score lives in the factor subspace; here returns are
    generated as B f + e with the diffusion model on the factors f.
  * TabDDPM -- Kotelnikov et al., ICML 2023 (Gaussian diffusion for numeric
    columns, multinomial diffusion for categorical ones; this version
    diffuses one-hot categories as Gaussians and decodes by argmax -- a
    stated simplification).
  * TimeGAN -- Yoon, Jarrett & van der Schaar, NeurIPS 2019 (embedding and
    recovery, supervised next-step loss in latent space, adversarial loss).
  * GMMN -- Li, Swersky & Zemel, ICML 2015; Dziugaite, Roy & Ghahramani, UAI
    2015; quasi-random inputs for risk -- Hofert, Prasad & Zhu,
    "Quasi-random sampling for multivariate distributions via generative
    neural networks", J. Comput. Graph. Stat. 30, 2021.
  * WGAN-GP -- Gulrajani et al., NeurIPS 2017 (critic gradient penalty
    (||grad C|| - 1)^2 at interpolates; the one-hidden-layer critic's input
    gradient is written out so the penalty can be differentiated).
  * Order-book diffusion -- Berti, Prenkaj & Velardi, "TRADES", 2025 (the
    conditional simulator RK336 describes).
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm, qmc

from engine.core.exceptions import ConfigurationError
from research.catalog.allocation import cvar_weights
from research.catalog.autodiff import (
    LSTM,
    MLP,
    Adam,
    Tensor,
    bce_with_logits,
    concat,
    fit,
    mse,
    param,
    stack,
)
from research.catalog.cross_section import spectral_features

# ---------------------------------------------------------------- DDPM


def _time_features(t, n_steps: int) -> np.ndarray:
    s = np.asarray(t, float)[:, None] / n_steps
    return np.column_stack([np.sin(np.pi * s[:, 0]), np.cos(np.pi * s[:, 0]), s[:, 0]])


class DDPM:
    """Denoising diffusion on vectors (optionally conditional). eps_theta is an
    MLP of [x_t, time features, condition]. Data are standardised inside."""

    def __init__(
        self, dim: int, cond_dim: int = 0, hidden: int = 64, n_steps: int = 50, seed: int = 0
    ):
        self.dim, self.cond_dim, self.n_steps = dim, cond_dim, n_steps
        self.rng = np.random.default_rng(seed)
        self.net = MLP([dim + 3 + cond_dim, hidden, hidden, dim], self.rng, act="tanh")
        self.betas = np.linspace(1e-3, 0.2, n_steps)
        self.alphas = 1 - self.betas
        self.abar = np.cumprod(self.alphas)

    def _eps(self, x, t, cond=None) -> Tensor:
        parts = [
            Tensor(x) if not isinstance(x, Tensor) else x,
            Tensor(_time_features(t, self.n_steps)),
        ]
        if self.cond_dim:
            parts.append(Tensor(cond))
        return self.net(concat(parts, axis=1))

    def fit(
        self, data, cond=None, steps: int = 500, batch: int = 128, lr: float = 2e-3
    ) -> list[float]:
        x = np.asarray(data, float)
        self.mu, self.sd = x.mean(0), x.std(0) + 1e-12
        z = (x - self.mu) / self.sd
        c = None if cond is None else np.asarray(cond, float)
        if self.cond_dim and c is None:
            raise ConfigurationError("this model is conditional: pass cond")

        def loss():
            idx = self.rng.integers(0, len(z), min(batch, len(z)))
            t = self.rng.integers(0, self.n_steps, len(idx))
            eps = self.rng.normal(size=(len(idx), self.dim))
            ab = self.abar[t][:, None]
            xt = np.sqrt(ab) * z[idx] + np.sqrt(1 - ab) * eps
            return mse(self._eps(xt, t, None if c is None else c[idx]), eps)

        return fit(loss, self.net.params, steps, lr)

    def sample(self, n: int, cond=None, rng=None) -> np.ndarray:
        rng = np.random.default_rng(rng)
        x = rng.normal(size=(n, self.dim))
        c = None if cond is None else np.broadcast_to(np.atleast_2d(cond), (n, self.cond_dim))
        for t in range(self.n_steps - 1, -1, -1):
            eps = self._eps(x, np.full(n, t), c).data
            x = (x - self.betas[t] / np.sqrt(1 - self.abar[t]) * eps) / np.sqrt(self.alphas[t])
            if t:
                x = x + np.sqrt(self.betas[t]) * rng.normal(size=x.shape)
        return x * self.sd + self.mu


# ---------------------------------------------------------------- flow matching


class FlowMatching:
    """Conditional flow matching with straight paths x_t = (1 - t) x0 + t x1,
    x0 ~ N(0, I); the velocity MLP regresses x1 - x0; sampling integrates
    dx/dt = v(x, t) with Euler steps."""

    def __init__(self, dim: int, cond_dim: int = 0, hidden: int = 64, seed: int = 0):
        self.dim, self.cond_dim = dim, cond_dim
        self.rng = np.random.default_rng(seed)
        self.net = MLP([dim + 1 + cond_dim, hidden, hidden, dim], self.rng, act="tanh")

    def _v(self, x, t, cond=None) -> Tensor:
        parts = [Tensor(x), Tensor(np.asarray(t, float).reshape(-1, 1))]
        if self.cond_dim:
            parts.append(Tensor(cond))
        return self.net(concat(parts, axis=1))

    def fit(
        self, data, cond=None, steps: int = 500, batch: int = 128, lr: float = 2e-3
    ) -> list[float]:
        x = np.asarray(data, float)
        self.mu, self.sd = x.mean(0), x.std(0) + 1e-12
        z = (x - self.mu) / self.sd
        c = None if cond is None else np.asarray(cond, float)

        def loss():
            idx = self.rng.integers(0, len(z), min(batch, len(z)))
            x0 = self.rng.normal(size=(len(idx), self.dim))
            t = self.rng.uniform(size=len(idx))
            xt = (1 - t[:, None]) * x0 + t[:, None] * z[idx]
            return mse(self._v(xt, t, None if c is None else c[idx]), z[idx] - x0)

        return fit(loss, self.net.params, steps, lr)

    def sample(self, n: int, cond=None, n_steps: int = 20, rng=None) -> np.ndarray:
        rng = np.random.default_rng(rng)
        x = rng.normal(size=(n, self.dim))
        c = None if cond is None else np.broadcast_to(np.atleast_2d(cond), (n, self.cond_dim))
        for k in range(n_steps):
            x = x + self._v(x, np.full(n, k / n_steps), c).data / n_steps
        return x * self.sd + self.mu


# ---------------------------------------------------------------- applications


def scenario_portfolio(model, n_scenarios: int = 2000, alpha: float = 0.95, rng=None) -> dict:
    """RK200/RK228: sample joint return scenarios from a fitted generator and
    allocate by minimum CVaR over them (long-only)."""
    scen = model.sample(n_scenarios, rng=rng)
    return {"scenarios": scen, "weights": cvar_weights(scen, alpha)}


class FactorDiffusion:
    """RK399 (and RK395 on macro panels): estimate k factors by PCA, run the
    diffusion model on the factor returns only, and generate cross-sections
    r = B f + e with e drawn from the residuals' diagonal variance."""

    def __init__(self, factors: int = 2, seed: int = 0, **kw):
        self.k, self.seed, self.kw = factors, seed, kw

    def fit(self, returns, **fit_kw) -> list[float]:
        r = np.asarray(returns, float)
        self.mu = r.mean(0)
        vt = np.linalg.svd(r - self.mu, full_matrices=False)[2]
        self.b = vt[: self.k].T  # loadings (n, k)
        f = (r - self.mu) @ self.b
        self.resid_sd = (r - self.mu - f @ self.b.T).std(0)
        self.model = DDPM(self.k, seed=self.seed, **self.kw)
        return self.model.fit(f, **fit_kw)

    def sample(self, n: int, rng=None) -> np.ndarray:
        rng = np.random.default_rng(rng)
        f = self.model.sample(n, rng=rng)
        return self.mu + f @ self.b.T + rng.normal(size=(n, len(self.mu))) * self.resid_sd


def ranks_to_scores(ranks) -> np.ndarray:
    """RK405: rankings (1 = best) to normal scores, so a Gaussian diffusion
    model can learn them."""
    r = np.asarray(ranks, float)
    return norm.ppf(r / (r.shape[1] + 1))


def scores_to_ranks(scores) -> np.ndarray:
    return np.argsort(np.argsort(np.asarray(scores, float), axis=1), axis=1) + 1


def synthesize_rankings(model: DDPM, n: int, rng=None) -> np.ndarray:
    """Sample normal-score vectors and turn each back into a ranking."""
    return scores_to_ranks(model.sample(n, rng=rng))


def encode_tabular(numeric, categorical, n_categories: int) -> np.ndarray:
    """RK378: numeric columns as they are plus one-hot categorical columns."""
    num = np.atleast_2d(np.asarray(numeric, float).T).T
    cat = np.eye(n_categories)[np.asarray(categorical, int)]
    return np.column_stack([num, cat])


def decode_tabular(rows, n_numeric: int) -> tuple[np.ndarray, np.ndarray]:
    r = np.asarray(rows, float)
    return r[:, :n_numeric], np.argmax(r[:, n_numeric:], axis=1)


def order_messages(times, sizes, sides, levels) -> np.ndarray:
    """RK336/RK343/RK332: messages as vectors (log inter-arrival, log size,
    side +1/-1, price level offset) for the generators to learn."""
    t = np.asarray(times, float)
    gaps = np.diff(np.r_[t[0], t]) + 1e-6
    return np.column_stack(
        [
            np.log(gaps),
            np.log(np.asarray(sizes, float)),
            np.asarray(sides, float),
            np.asarray(levels, float),
        ]
    )


def decode_messages(vectors) -> dict:
    v = np.asarray(vectors, float)
    return {
        "gap": np.exp(v[:, 0]),
        "size": np.exp(v[:, 1]),
        "side": np.where(v[:, 2] >= 0, 1, -1),
        "level": np.maximum(np.round(v[:, 3]), 0).astype(int),
    }


def operator_flow_alpha(
    histories,
    next_returns,
    histories_now,
    modes: int = 4,
    n_samples: int = 200,
    top: int = 3,
    rng=None,
    **fit_kw,
) -> dict:
    """RK390: condition a flow-matching model of next returns on each stock's
    spectral (Fourier-operator) features; rank stocks by the mean of their
    sampled next-period returns and hold the top names."""
    feats = spectral_features(histories, modes)
    model = FlowMatching(1, cond_dim=feats.shape[1], seed=0)
    model.fit(np.asarray(next_returns, float)[:, None], feats, **fit_kw)
    now = spectral_features(histories_now, modes)
    means = np.array([model.sample(n_samples, cond=f, rng=rng).mean() for f in now])
    w = np.zeros(len(now))
    w[np.argsort(-means)[:top]] = 1.0 / top
    return {"expected": means, "weights": w, "model": model}


# ---------------------------------------------------------------- GMMN (RK373)


def mmd2(x: Tensor, y: np.ndarray, bandwidths=(0.1, 0.5, 1.0, 2.0)) -> Tensor:
    """Biased MMD^2 with a mixture of Gaussian kernels."""
    yt = Tensor(y)

    def k(a, b):
        d2 = (
            (a * a).sum(axis=1, keepdims=True)
            + (b * b).sum(axis=1).reshape(1, -1)
            - (a @ b.T) * 2.0
        )
        return sum(((d2 * (-0.5 / h**2)).exp() for h in bandwidths), Tensor(0.0))

    return k(x, x).mean() + k(yt, yt).mean() - k(x, yt).mean() * 2.0


class GMMN:
    """A generator MLP from uniform inputs to samples, trained by MMD; with a
    scrambled Sobol input set it gives quasi-Monte-Carlo scenarios."""

    def __init__(self, dim: int, noise_dim: int | None = None, hidden: int = 32, seed: int = 0):
        self.dim, self.noise_dim = dim, noise_dim or dim
        self.rng = np.random.default_rng(seed)
        self.net = MLP([self.noise_dim, hidden, hidden, dim], self.rng)

    def fit(self, data, steps: int = 400, batch: int = 128, lr: float = 5e-3) -> list[float]:
        x = np.asarray(data, float)
        self.mu, self.sd = x.mean(0), x.std(0) + 1e-12
        z = (x - self.mu) / self.sd

        def loss():
            idx = self.rng.integers(0, len(z), min(batch, len(z)))
            u = self.rng.uniform(size=(len(idx), self.noise_dim))
            return mmd2(self.net(Tensor(u)), z[idx])

        return fit(loss, self.net.params, steps, lr)

    def sample(self, n: int, quasi: bool = True, rng=None) -> np.ndarray:
        if quasi:
            u = qmc.Sobol(self.noise_dim, scramble=True, seed=rng).random(n)
        else:
            u = np.random.default_rng(rng).uniform(size=(n, self.noise_dim))
        return self.net(Tensor(u)).data * self.sd + self.mu


def expected_shortfall(losses, alpha: float = 0.95) -> float:
    loss = np.sort(np.asarray(losses, float))
    return float(loss[int(np.floor(alpha * len(loss))) :].mean())  # worst (1 - alpha) share


# ---------------------------------------------------------------- conditional WGAN-GP (RK383)


class ConditionalWGANGP:
    """Generator G(z, curve_t) -> curve change; critic C(change, curve_t) is a
    one-hidden-layer tanh network, so its input gradient
    W1x' (w2 * (1 - tanh^2)) is an explicit expression and the gradient
    penalty is differentiable with first-order autodiff."""

    def __init__(self, dim: int, noise_dim: int = 4, hidden: int = 32, seed: int = 0):
        self.rng = np.random.default_rng(seed)
        self.dim, self.noise_dim = dim, noise_dim
        self.gen = MLP([noise_dim + dim, hidden, dim], self.rng)
        self.w1 = param((2 * dim, hidden), self.rng)
        self.b1 = param(hidden)
        self.w2 = param((hidden, 1), self.rng)

    def critic(self, change: Tensor, cond: Tensor) -> tuple[Tensor, Tensor]:
        """Critic value and its gradient with respect to `change`."""
        a = (concat([change, cond], axis=1) @ self.w1 + self.b1).tanh()
        value = (a @ self.w2)[:, 0]
        grad = ((1.0 - a * a) * self.w2.reshape(1, -1)) @ self.w1[: self.dim].T
        return value, grad

    def fit(
        self,
        curves,
        steps: int = 300,
        batch: int = 64,
        n_critic: int = 3,
        gp: float = 10.0,
        lr: float = 1e-3,
    ) -> dict:
        c = np.asarray(curves, float)
        self.mu, self.sd = c.mean(0), c.std(0) + 1e-12
        z = (c - self.mu) / self.sd
        cond, change = z[:-1], np.diff(z, axis=0)
        opt_c, opt_g = Adam([self.w1, self.b1, self.w2], lr), Adam(self.gen.params, lr)
        hist = {"critic": [], "gen": []}
        for _ in range(steps):
            for _ in range(n_critic):
                idx = self.rng.integers(0, len(cond), min(batch, len(cond)))
                cd = Tensor(cond[idx])
                fake = self.gen(
                    concat([Tensor(self.rng.normal(size=(len(idx), self.noise_dim))), cd], axis=1)
                ).data
                eps = self.rng.uniform(size=(len(idx), 1))
                inter = Tensor(eps * change[idx] + (1 - eps) * fake)
                opt_c.zero_grad()
                real_v, _ = self.critic(Tensor(change[idx]), cd)
                fake_v, _ = self.critic(Tensor(fake), cd)
                _, g = self.critic(inter, cd)
                penalty = ((((g * g).sum(axis=1) + 1e-12).sqrt() - 1.0) ** 2).mean()
                loss_c = fake_v.mean() - real_v.mean() + penalty * gp
                loss_c.backward()
                opt_c.step()
            idx = self.rng.integers(0, len(cond), min(batch, len(cond)))
            cd = Tensor(cond[idx])
            opt_g.zero_grad()
            fake = self.gen(
                concat([Tensor(self.rng.normal(size=(len(idx), self.noise_dim))), cd], axis=1)
            )
            loss_g = -self.critic(fake, cd)[0].mean()
            loss_g.backward()
            opt_g.step()
            hist["critic"].append(float(loss_c.data))
            hist["gen"].append(float(loss_g.data))
        return hist

    def sample(self, curve, n: int, rng=None) -> np.ndarray:
        """n next-period curves given today's."""
        rng = np.random.default_rng(rng)
        cz = (np.asarray(curve, float) - self.mu) / self.sd
        cond = np.broadcast_to(cz, (n, self.dim))
        chg = self.gen(
            concat([Tensor(rng.normal(size=(n, self.noise_dim))), Tensor(cond)], axis=1)
        ).data
        return (cond + chg) * self.sd + self.mu


# ---------------------------------------------------------------- TimeGAN (RK349)


class TimeGAN:
    """Embedder (LSTM) and recovery map sequences to a latent space and back;
    a supervisor learns the latent one-step dynamics; a generator (LSTM on
    noise) plus the supervisor produce latent paths that a discriminator
    (LSTM) must tell from real ones. Phases: autoencoder, supervisor, joint."""

    def __init__(self, n_features: int, hidden: int = 8, seed: int = 0):
        self.rng = np.random.default_rng(seed)
        rng = self.rng
        self.h = hidden
        self.emb, self.rec = LSTM(n_features, hidden, rng), MLP([hidden, n_features], rng)
        self.gen, self.sup = LSTM(n_features, hidden, rng), MLP([hidden, hidden], rng)
        self.disc, self.dhead = LSTM(hidden, hidden, rng), MLP([hidden, 1], rng)
        self.n_features = n_features

    def _run(self, lstm: LSTM, x: Tensor) -> Tensor:
        """x (T, B, f) -> hidden states (T, B, hidden)."""
        h, c = lstm.zero_state(x.shape[1])
        outs = []
        for t in range(x.shape[0]):
            h, c = lstm.cell(x[t], h, c)
            outs.append(h)
        return stack(outs, axis=0).sigmoid()

    def _embed(self, x) -> Tensor:
        return self._run(self.emb, Tensor(np.asarray(x, float).transpose(1, 0, 2)))

    def fit(self, sequences, steps: int = 100, lr: float = 0.01) -> dict:
        """sequences (B, T, f), scaled to [0, 1] inside."""
        s = np.asarray(sequences, float)
        self.lo, self.hi = s.min((0, 1)), s.max((0, 1)) + 1e-12
        x = (s - self.lo) / (self.hi - self.lo)
        xt = x.transpose(1, 0, 2)
        hist = {}
        ae = [*self.emb.params, *self.rec.params]
        hist["autoencoder"] = fit(lambda: mse(self.rec(self._embed(x)), xt), ae, steps, lr)

        def sup_loss():
            h = self._embed(x)
            return mse(self.sup(h[:-1]), h.data[1:])

        hist["supervisor"] = fit(sup_loss, self.sup.params, steps, lr)
        opt_g = Adam([*self.gen.params, *self.sup.params], lr)
        opt_d = Adam([*self.disc.params, *self.dhead.params], lr)
        g_hist, d_hist = [], []
        b, t_len = x.shape[0], x.shape[1]
        for _ in range(steps):
            noise = Tensor(self.rng.uniform(size=(t_len, b, self.n_features)))
            opt_d.zero_grad()
            h_real = Tensor(self._embed(x).data)
            h_fake = Tensor(self.sup(self._run(self.gen, noise)).data)
            d_real = self.dhead(self._run(self.disc, h_real)[-1])[:, 0]
            d_fake = self.dhead(self._run(self.disc, h_fake)[-1])[:, 0]
            loss_d = bce_with_logits(d_real, np.ones(b)) + bce_with_logits(d_fake, np.zeros(b))
            loss_d.backward()
            opt_d.step()
            opt_g.zero_grad()
            e_hat = self._run(self.gen, noise)
            h_hat = self.sup(e_hat)
            d_hat = self.dhead(self._run(self.disc, h_hat)[-1])[:, 0]
            x_hat = self.rec(h_hat)
            moments = ((x_hat.mean(axis=(0, 1)) - Tensor(xt.mean(axis=(0, 1)))) ** 2).sum()
            loss_g = (
                bce_with_logits(d_hat, np.ones(b))
                + mse(self.sup(e_hat[:-1]), h_hat.data[1:])
                + moments * 10.0
            )
            loss_g.backward()
            opt_g.step()
            g_hist.append(float(loss_g.data))
            d_hist.append(float(loss_d.data))
        hist["generator"], hist["discriminator"] = g_hist, d_hist
        return hist

    def sample(self, n: int, length: int, rng=None) -> np.ndarray:
        rng = np.random.default_rng(rng)
        noise = Tensor(rng.uniform(size=(length, n, self.n_features)))
        x = self.rec(self.sup(self._run(self.gen, noise))).data.transpose(1, 0, 2)
        return x * (self.hi - self.lo) + self.lo
