"""
Generic deep-RL and evolutionary tools on the catalog's autodiff, plus the
portfolio entries that use them (ledger RK220, RK227, RK234, RK351). The
execution and market-making entries reuse DQN, MADDPG and genetic_search
from here. Toy-scale research code: the pages record no independent
out-of-sample evidence for any of these, and MADDPG did markedly worse
than a genetic algorithm in the one portfolio comparison found (RK351).

Sources:

  * DQN -- Mnih et al., Nature 518, 2015; double DQN -- van Hasselt, Guez &
    Silver, AAAI 2016.
  * MADDPG -- Lowe et al., "Multi-agent actor-critic for mixed
    cooperative-competitive environments", NeurIPS 2017 (decentralised
    actors, centralised critics that see every agent's action).
  * Genetic algorithms -- Holland, 1975; tournament selection, blend
    crossover (BLX-alpha, Eshelman & Schaffer 1993), Gaussian mutation, elitism.
  * Continuous-time exploratory mean-variance -- Wang & Zhou, "Continuous-
    time mean-variance portfolio selection: a reinforcement learning
    framework", Math. Finance 30, 2020: the optimal exploratory policy is
    Gaussian with mean -(rho/sigma)(x - w)/sigma and variance growing as
    exp(rho^2 (T - t)), and the Lagrange multiplier w is learned by
    w <- w - a (x_T - z). Here the policy keeps that parametric form (mean
    slope and log-variance schedule learned by REINFORCE with an entropy
    bonus) rather than the paper's exact actor-critic gradients.
  * Wasserstein-robust policies -- for a reward linear in the returns,
    w_t'r_t, the worst case over a type-1 Wasserstein ball of radius eps
    around the empirical returns is the empirical mean minus eps times the
    largest ||w_t||_2 (the adversary spends its whole budget where the
    reward is most sensitive); a log-sum-exp smooths the max.
"""

from __future__ import annotations

import numpy as np

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import MLP, Adam, Tensor, concat, logsumexp, param, softmax

# ---------------------------------------------------------------- shared plumbing


def copy_params(src: list[Tensor], dst: list[Tensor], tau: float = 1.0) -> None:
    """dst <- tau src + (1 - tau) dst (tau = 1 copies)."""
    for s, d in zip(src, dst, strict=True):
        d.data[...] = tau * s.data + (1 - tau) * d.data


class ReplayBuffer:
    def __init__(self, capacity: int = 10_000, seed: int = 0):
        self.capacity, self.items = capacity, []
        self.rng = np.random.default_rng(seed)

    def add(self, *transition) -> None:
        self.items.append(transition)
        if len(self.items) > self.capacity:
            self.items.pop(0)

    def sample(self, n: int) -> list[np.ndarray]:
        idx = self.rng.integers(0, len(self.items), size=n)
        return [np.array(col) for col in zip(*[self.items[i] for i in idx], strict=True)]

    def __len__(self) -> int:
        return len(self.items)


# ---------------------------------------------------------------- DQN


class DQN:
    """Double DQN with an MLP Q-network, epsilon-greedy exploration, a replay
    buffer and a soft-updated target network."""

    def __init__(
        self,
        n_state: int,
        n_actions: int,
        hidden: int = 32,
        gamma: float = 0.99,
        lr: float = 1e-3,
        tau: float = 0.05,
        seed: int = 0,
    ):
        rng = np.random.default_rng(seed)
        self.q = MLP([n_state, hidden, hidden, n_actions], rng, act="relu")
        self.target = MLP([n_state, hidden, hidden, n_actions], rng, act="relu")
        copy_params(self.q.params, self.target.params)
        self.opt = Adam(self.q.params, lr)
        self.gamma, self.tau, self.n_actions = gamma, tau, n_actions
        self.buffer, self.rng = ReplayBuffer(seed=seed), rng

    def values(self, state) -> np.ndarray:
        return self.q(Tensor(np.atleast_2d(state))).data

    def act(self, state, epsilon: float = 0.0) -> int:
        if self.rng.random() < epsilon:
            return int(self.rng.integers(self.n_actions))
        return int(np.argmax(self.values(state)[0]))

    def update(self, batch_size: int = 32) -> float:
        if len(self.buffer) < batch_size:
            return float("nan")
        s, a, r, s2, done = self.buffer.sample(batch_size)
        best = np.argmax(self.q(Tensor(s2)).data, axis=1)
        nxt = self.target(Tensor(s2)).data[np.arange(batch_size), best]
        y = r + self.gamma * (1 - done) * nxt
        self.opt.zero_grad()
        q = self.q(Tensor(s))[np.arange(batch_size), a.astype(int)]
        loss = ((q - y) ** 2).mean()
        loss.backward()
        self.opt.step()
        copy_params(self.q.params, self.target.params, self.tau)
        return float(loss.data)


# ---------------------------------------------------------------- MADDPG


class MADDPG:
    """N agents with deterministic tanh actors on their own observations and
    centralised critics Q_i(all observations, all actions)."""

    def __init__(
        self,
        obs_dims,
        act_dims,
        hidden: int = 32,
        gamma: float = 0.95,
        lr_actor: float = 1e-3,
        lr_critic: float = 1e-3,
        tau: float = 0.05,
        seed: int = 0,
    ):
        rng = np.random.default_rng(seed)
        self.obs_dims, self.act_dims = list(obs_dims), list(act_dims)
        joint = sum(self.obs_dims) + sum(self.act_dims)
        self.actors = [MLP([o, hidden, a], rng) for o, a in zip(obs_dims, act_dims, strict=True)]
        self.actors_t = [MLP([o, hidden, a], rng) for o, a in zip(obs_dims, act_dims, strict=True)]
        self.critics = [MLP([joint, hidden, hidden, 1], rng, act="relu") for _ in obs_dims]
        self.critics_t = [MLP([joint, hidden, hidden, 1], rng, act="relu") for _ in obs_dims]
        for src, dst in [
            *zip(self.actors, self.actors_t, strict=True),
            *zip(self.critics, self.critics_t, strict=True),
        ]:
            copy_params(src.params, dst.params)
        self.opt_a = [Adam(a.params, lr_actor) for a in self.actors]
        self.opt_c = [Adam(c.params, lr_critic) for c in self.critics]
        self.gamma, self.tau = gamma, tau
        self.buffer, self.rng = ReplayBuffer(seed=seed), rng

    def act(self, observations, noise: float = 0.0) -> list[np.ndarray]:
        out = []
        for actor, o, d in zip(self.actors, observations, self.act_dims, strict=True):
            a = actor(Tensor(np.atleast_2d(o))).tanh().data[0]
            out.append(np.clip(a + noise * self.rng.normal(size=d), -1, 1))
        return out

    def update(self, batch_size: int = 64) -> list[float]:
        if len(self.buffer) < batch_size:
            return []
        obs, acts, rewards, obs2, done = self.buffer.sample(batch_size)
        # obs/obs2: (B, sum obs); acts: (B, sum act); rewards: (B, N)
        osplit = np.cumsum(self.obs_dims)[:-1]
        asplit = np.cumsum(self.act_dims)[:-1]
        o_i, o2_i = np.split(obs, osplit, axis=1), np.split(obs2, osplit, axis=1)
        a_i = np.split(acts, asplit, axis=1)
        a2 = np.column_stack(
            [act(Tensor(o)).tanh().data for act, o in zip(self.actors_t, o2_i, strict=True)]
        )
        losses = []
        for i, (critic, critic_t) in enumerate(zip(self.critics, self.critics_t, strict=True)):
            y = (
                rewards[:, i]
                + self.gamma * (1 - done) * critic_t(Tensor(np.column_stack([obs2, a2]))).data[:, 0]
            )
            self.opt_c[i].zero_grad()
            q = critic(Tensor(np.column_stack([obs, acts])))[:, 0]
            loss = ((q - y) ** 2).mean()
            loss.backward()
            self.opt_c[i].step()
            losses.append(float(loss.data))
            self.opt_a[i].zero_grad()
            parts = [Tensor(a) for a in a_i]
            parts[i] = self.actors[i](Tensor(o_i[i])).tanh()
            q_pi = critic(concat([Tensor(obs), *parts], axis=1))
            (-q_pi.mean()).backward()
            self.opt_a[i].step()
        for src, dst in [
            *zip(self.actors, self.actors_t, strict=True),
            *zip(self.critics, self.critics_t, strict=True),
        ]:
            copy_params(src.params, dst.params, self.tau)
        return losses


# ---------------------------------------------------------------- evolution


def genetic_search(
    fitness,
    dim: int,
    pop: int = 30,
    gens: int = 40,
    sigma: float = 0.1,
    elite: int = 2,
    init_scale: float = 0.5,
    rng=None,
) -> dict:
    """Maximise fitness(x) over R^dim: tournament selection (size 3), BLX-0.5
    crossover, Gaussian mutation, `elite` survivors per generation."""
    rng = np.random.default_rng(rng)
    population = rng.normal(0, init_scale, (pop, dim))
    history = []
    for _ in range(gens):
        scores = np.array([fitness(p) for p in population])
        order = np.argsort(-scores)
        history.append(float(scores[order[0]]))
        nxt = [population[i].copy() for i in order[:elite]]
        while len(nxt) < pop:
            p1, p2 = (
                population[max(rng.choice(pop, 3), key=lambda i: scores[i])] for _ in range(2)
            )
            lo, hi = np.minimum(p1, p2), np.maximum(p1, p2)
            span = hi - lo
            child = rng.uniform(lo - 0.5 * span, hi + 0.5 * span)
            nxt.append(child + sigma * rng.normal(size=dim))
        population = np.array(nxt)
    scores = np.array([fitness(p) for p in population])
    best = int(np.argmax(scores))
    return {"best": population[best], "fitness": float(scores[best]), "history": history}


# ---------------------------------------------------------------- portfolio applications


def softmax_weights(features, theta) -> np.ndarray:
    """Linear-softmax policy: w_t = softmax(features_t @ Theta)."""
    z = np.asarray(features, float) @ theta
    z = np.exp(z - z.max(axis=1, keepdims=True))
    return z / z.sum(axis=1, keepdims=True)


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / (x.std() + 1e-12) * np.sqrt(252))


def evolve_portfolio_agents(features, returns, pop: int = 30, gens: int = 30, rng=None) -> dict:
    """RK227: a population of linear-softmax allocation agents evolved for
    in-sample Sharpe (features_t decide the weights held over returns_t)."""
    f, r = np.asarray(features, float), np.asarray(returns, float)
    shape = (f.shape[1], r.shape[1])

    def fitness(x):
        w = softmax_weights(f, x.reshape(shape))
        return sharpe((w * r).sum(1))

    out = genetic_search(fitness, int(np.prod(shape)), pop=pop, gens=gens, rng=rng)
    out["theta"] = out["best"].reshape(shape)
    return out


def train_wdro_policy(
    features,
    returns,
    radius: float = 0.0,
    risk: float = 0.0,
    steps: int = 300,
    lr: float = 0.05,
    seed: int = 0,
) -> dict:
    """RK234: train the linear-softmax policy on the worst-case mean return
    over a Wasserstein ball (mean - radius * smooth-max ||w_t||_2) minus a
    variance penalty; radius = 0 is the ordinary empirical objective."""
    f, r = np.asarray(features, float), np.asarray(returns, float)
    theta = param((f.shape[1], r.shape[1]), np.random.default_rng(seed), scale=0.01)
    opt, hist = Adam([theta], lr), []
    for _ in range(steps):
        opt.zero_grad()
        w = softmax(Tensor(f) @ theta, axis=1)
        pr = (w * Tensor(r)).sum(axis=1)
        norms = ((w**2).sum(axis=1) + 1e-12).sqrt()
        worst = pr.mean() - radius * logsumexp(norms * 50.0, axis=0) * (1 / 50.0)
        obj = worst - risk * ((pr - pr.mean()) ** 2).mean()
        (-obj).backward()
        opt.step()
        hist.append(float(obj.data))
    return {"theta": theta.data.copy(), "history": hist}


class EMVAgent:
    """RK220: exploratory mean-variance agent. Dollar position in the risky
    asset u ~ N(-k (x - w), exp(a + b (T - t))): it buys while wealth x is
    below the multiplier w and its exploration shrinks toward the horizon.
    k, a, b are learned by REINFORCE on -(x_T - w)^2 + lam * entropy; w by
    w <- w - lr_w (mean x_T - z)."""

    def __init__(
        self, target: float, horizon: int, lam: float = 0.1, seed: int = 0, long_only: bool = False
    ):
        self.z, self.horizon, self.lam, self.long_only = target, horizon, lam, long_only
        self.k, self.a, self.b, self.w = 0.5, np.log(0.1), 0.0, target
        self.rng = np.random.default_rng(seed)

    def policy(self, t: int, x: float) -> tuple[float, float]:
        return -self.k * (x - self.w), float(
            np.exp(self.a + self.b * (self.horizon - t) / self.horizon)
        )

    def episode(self, returns, x0: float = 1.0) -> dict:
        x, grads, entropy = x0, np.zeros(3), 0.0
        for t, r in enumerate(returns[: self.horizon]):
            mean, var = self.policy(t, x)
            u = mean + np.sqrt(var) * self.rng.normal()
            dev = u - mean  # the score function uses the draw, before any clipping
            if self.long_only:
                u = float(np.clip(u, 0.0, x))
            s = (self.horizon - t) / self.horizon
            grads += [
                dev / var * -(x - self.w),
                0.5 * (dev**2 / var - 1),
                0.5 * (dev**2 / var - 1) * s,
            ]
            entropy += 0.5 * np.log(2 * np.pi * np.e * var)
            x += u * r
        return {
            "wealth": x,
            "score": -((x - self.w) ** 2) + self.lam * entropy / self.horizon,
            "grads": grads,
        }

    def train(
        self,
        returns,
        episodes: int = 300,
        batch: int = 20,
        lr: float = 0.05,
        lr_w: float = 0.1,
        x0: float = 1.0,
    ) -> list[float]:
        r = np.asarray(returns, float)
        if len(r) < self.horizon:
            raise ConfigurationError("need at least `horizon` returns")
        means = []
        for _ in range(episodes // batch):
            eps = []
            for _ in range(batch):
                start = self.rng.integers(0, len(r) - self.horizon + 1)
                eps.append(self.episode(r[start : start + self.horizon], x0))
            scores = np.array([e["score"] for e in eps])
            adv = (scores - scores.mean()) / (scores.std() + 1e-12)
            g = np.mean([a * e["grads"] for a, e in zip(adv, eps, strict=True)], axis=0)
            self.k, self.a, self.b = np.array([self.k, self.a, self.b]) + lr * g
            self.k = max(self.k, 0.0)
            terminal = float(np.mean([e["wealth"] for e in eps]))
            self.w -= lr_w * (terminal - self.z)
            means.append(terminal)
        return means


class MADDPGAllocator:
    """RK351: one MADDPG agent per asset. Agent i sees its asset's last
    `lookback` returns and outputs a score; weights = softmax(scale * scores);
    every agent is rewarded with the portfolio's next-step log return."""

    def __init__(self, n_assets: int, lookback: int = 5, scale: float = 3.0, seed: int = 0, **kw):
        self.n, self.lookback, self.scale = n_assets, lookback, scale
        self.agent = MADDPG([lookback] * n_assets, [1] * n_assets, seed=seed, **kw)

    def weights(self, window) -> np.ndarray:
        obs = [np.asarray(window, float)[-self.lookback :, i] for i in range(self.n)]
        s = np.array([a[0] for a in self.agent.act(obs)]) * self.scale
        e = np.exp(s - s.max())
        return e / e.sum()

    def train(self, returns, epochs: int = 3, noise: float = 0.3, batch: int = 64) -> list[float]:
        r = np.asarray(returns, float)
        losses = []
        for _ in range(epochs):
            for t in range(self.lookback, len(r) - 1):
                obs = [r[t - self.lookback : t, i] for i in range(self.n)]
                acts = self.agent.act(obs, noise)
                s = np.array([a[0] for a in acts]) * self.scale
                w = np.exp(s - s.max())
                w /= w.sum()
                reward = np.log1p(w @ r[t])
                obs2 = [r[t - self.lookback + 1 : t + 1, i] for i in range(self.n)]
                self.agent.buffer.add(
                    np.concatenate(obs),
                    np.concatenate(acts),
                    np.full(self.n, reward),
                    np.concatenate(obs2),
                    0.0,
                )
                out = self.agent.update(batch)
                if out:
                    losses.append(float(np.mean(out)))
        return losses
