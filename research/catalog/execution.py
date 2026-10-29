"""
Execution entries of the ranked list (ledger RK249, RK251, RK256, RK310,
RK312, RK358, RK360, RK364, RK365, RK368, RK369, RK370, RK410, RK419,
RK421, RK422, RK423, RK425). The book trades one ETF in lots far too
small to need an execution algorithm (ledger section 8C), so this is
research code on simulators. Selling is the convention throughout: a
parent order of `shares` is liquidated over `steps` periods.

The liquidation simulator is Almgren-Chriss in discrete time: the price
moves by sigma * noise - gamma * shares sold (permanent impact) and a
slice of n fills at S - eta * n (temporary impact). Implementation
shortfall is arrival value minus cash received.

Sources:

  * Almgren & Chriss, "Optimal execution of portfolio transactions", J. Risk
    3, 2000 (research.catalog.leads.almgren_chriss).
  * Hidden orders -- Bessembinder, Panayides & Venkataraman, "Hidden
    liquidity", J. Financial Econ. 94, 2009.
  * Volume curves -- Bialkowski, Darolles & Le Fol, "Improving VWAP
    strategies: a dynamic volume approach", J. Banking Finance 32, 2008
    (market component by PCA across stocks, specific component AR(1)).
  * Deep Markov models -- Krishnan, Shalit & Sontag, AAAI 2017 (gated
    transition, Gaussian emission, ELBO with a filtering inference network).
  * DQN execution -- Nevmyvaka, Feng & Kearns, ICML 2006 (tabular); Ning,
    Lin & Jaimungal, "Double deep Q-learning for optimal execution", Appl.
    Math. Finance 28, 2021. Learning from demonstrations -- Hester et al.,
    "Deep Q-learning from demonstrations", AAAI 2018 (RK419's expert guidance).
  * Mean-field execution -- Cardaliaguet & Lehalle, "Mean field game of
    controls and an application to trade crowding", Math. Financial Econ.
    12, 2018 (follow the crowd, but not too fast).
  * Predatory trading -- Brunnermeier & Pedersen, J. Finance 60, 2005
    (RK423's followers).
  * Neural operators -- Lu et al., "DeepONet", Nature Mach. Intell. 3, 2021
    (branch net on the input function, trunk net on time).
"""

from __future__ import annotations

import numpy as np

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import (
    LSTM,
    MLP,
    Adam,
    Tensor,
    concat,
    fit,
    log_softmax,
    param,
    softmax,
)
from research.catalog.deep_rl import DQN, MADDPG, genetic_search
from research.catalog.leads import almgren_chriss

# ---------------------------------------------------------------- schedules (RK249, RK364, RK365)


def twap_schedule(shares: float, steps: int) -> np.ndarray:
    if shares <= 0 or steps < 1:
        raise ConfigurationError("need positive shares and at least one step")
    return np.full(steps, shares / steps)


def vwap_schedule(shares: float, volume_profile) -> np.ndarray:
    """RK364: slice in proportion to the expected intraday volume curve."""
    v = np.asarray(volume_profile, float)
    return shares * v / v.sum()


def pov_schedule(shares: float, market_volumes, rate: float = 0.1) -> np.ndarray:
    """RK365: trade `rate` of each period's realised volume until done; the
    tail is zero once the order completes (completion time is not fixed)."""
    out, left = [], shares
    for v in np.asarray(market_volumes, float):
        n = min(rate * v, left)
        out.append(n)
        left -= n
    return np.array(out)


def iceberg_fills(
    total: float,
    display: float,
    market_volumes,
    participation: float = 0.2,
    refresh_jitter: float = 0.0,
    rng=None,
) -> dict:
    """RK249: only `display` (optionally jittered) is visible; each period the
    visible clip fills up to `participation` of market volume and is
    refilled from the reserve. Returns fills and the visible size per period."""
    rng = np.random.default_rng(rng)
    left, fills, shown = total, [], []
    for v in np.asarray(market_volumes, float):
        clip = min(left, display * (1 + refresh_jitter * rng.uniform(-1, 1)))
        filled = min(clip, participation * v)
        shown.append(clip)
        fills.append(filled)
        left -= filled
    return {"fills": np.array(fills), "visible": np.array(shown), "remaining": left}


# ---------------------------------------------------------------- volume forecasts (RK251, RK256)


def static_volume_profile(volumes) -> np.ndarray:
    """Average share of daily volume in each intraday bin (days x bins)."""
    v = np.asarray(volumes, float)
    return (v / v.sum(1, keepdims=True)).mean(0)


def bdf_volume_forecast(turnover, stock: int, n_factors: int = 1) -> dict:
    """RK251 (Bialkowski-Darolles-Le Fol): turnover (days, bins, stocks).
    The market component is the rank-k PCA fit of the stacked (day-bin x
    stock) matrix; its forecast for tomorrow is its average across past days
    per bin. The stock's specific component follows an AR(1) across bins.
    Returns tomorrow's predicted bin turnover for `stock` given the specific
    component's last value, plus a function to update intraday."""
    x = np.asarray(turnover, float)
    days, bins, stocks = x.shape
    m = x.reshape(days * bins, stocks)
    u, s, vt = np.linalg.svd(m - m.mean(0), full_matrices=False)
    common = (u[:, :n_factors] * s[:n_factors]) @ vt[:n_factors] + m.mean(0)
    specific = (m - common)[:, stock]
    phi, c = np.polyfit(specific[:-1], specific[1:], 1)
    common_next = common[:, stock].reshape(days, bins).mean(0)

    def update(observed_specific_last: float, bin_index: int) -> np.ndarray:
        """Forecasts for the bins after `bin_index` given the last specific value."""
        e, out = observed_specific_last, []
        for b in range(bin_index + 1, bins):
            e = c + phi * e
            out.append(common_next[b] + e)
        return np.array(out)

    first = np.array([common_next[0] + c + phi * specific[-1]])
    return {
        "forecast": np.concatenate([first, update(c + phi * specific[-1], 0)]),
        "phi": phi,
        "update": update,
        "common": common_next,
    }


class DeepMarkovVolume:
    """RK256: deep Markov model of an intraday (log-)volume curve. Latent
    z_b follows a Gaussian transition whose mean is an MLP of z_{b-1};
    log-volume x_b ~ N(MLP(z_b), s^2). The filtering inference network
    q(z_b | z_{b-1}, x_b) is trained with the reparameterised ELBO, one
    day per sequence."""

    def __init__(self, latent: int = 2, hidden: int = 16, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.latent, self.rng = latent, rng
        self.trans = MLP([latent, hidden, 2 * latent], rng)
        self.emit = MLP([latent, hidden, 1], rng)
        self.infer = MLP([latent + 1, hidden, 2 * latent], rng)
        self.log_s = Tensor(np.zeros(1), requires_grad=True)

    @property
    def params(self) -> list[Tensor]:
        return [*self.trans.params, *self.emit.params, *self.infer.params, self.log_s]

    def elbo(self, curves, noise) -> Tensor:
        x = Tensor(curves)  # (days, bins)
        days, bins = curves.shape
        z = Tensor(np.zeros((days, self.latent)))
        total = Tensor(0.0)
        for b in range(bins):
            pr = self.trans(z)
            p_mu, p_ls = pr[:, : self.latent], pr[:, self.latent :].clip(-5, 2)
            q = self.infer(concat([z, x[:, b : b + 1]], axis=1))
            q_mu, q_ls = q[:, : self.latent], q[:, self.latent :].clip(-5, 2)
            z = q_mu + q_ls.exp() * Tensor(noise[:, b])
            mean = self.emit(z)[:, 0]
            ll = -0.5 * ((x[:, b] - mean) ** 2 * (-2.0 * self.log_s).exp()) - self.log_s
            kl = (
                p_ls
                - q_ls
                + ((2.0 * q_ls).exp() + (q_mu - p_mu) ** 2) * (0.5 * (-2.0 * p_ls).exp())
                - 0.5
            ).sum(axis=1)
            total = total + (ll - kl).mean()
        return total

    def fit(self, log_volumes, steps: int = 200, lr: float = 0.01) -> list[float]:
        v = np.asarray(log_volumes, float)
        self.mu, self.sd = v.mean(), v.std() + 1e-12
        x = (v - self.mu) / self.sd
        noise = self.rng.normal(size=(len(x), x.shape[1], self.latent))
        return fit(lambda: -self.elbo(x, noise), self.params, steps, lr)

    def forecast(self, observed, bins: int) -> np.ndarray:
        """Filter on the bins observed so far today, then roll the transition
        mean forward to give log-volume forecasts for the remaining bins."""
        z = Tensor(np.zeros((1, self.latent)))
        for xb in (np.asarray(observed, float) - self.mu) / self.sd:
            q = self.infer(concat([z, Tensor([[xb]])], axis=1))
            z = q[:, : self.latent]
        out = []
        for _ in range(bins - len(observed)):
            z = self.trans(z)[:, : self.latent]
            out.append(self.emit(z).data[0, 0] * self.sd + self.mu)
        return np.array(out)


# ---------------------------------------------------------------- the liquidation simulator


class LiquidationEnv:
    """Discrete Almgren-Chriss liquidation. Actions index `multiples` of the
    TWAP rate on what is left (remaining / steps left); the last step sells
    everything. Reward = cash received minus the arrival value of the shares
    sold, so episode reward = -implementation shortfall."""

    multiples = (0.0, 0.5, 1.0, 1.5, 2.0)

    def __init__(
        self,
        shares: float = 1000.0,
        steps: int = 10,
        sigma: float = 0.5,
        eta: float = 0.002,
        gamma: float = 0.0005,
        price0: float = 100.0,
        rng=None,
    ):
        self.shares, self.steps, self.sigma, self.eta, self.gamma = shares, steps, sigma, eta, gamma
        self.price0 = price0
        self.rng = np.random.default_rng(rng)

    def reset(self) -> np.ndarray:
        self.t, self.left, self.price = 0, self.shares, self.price0
        return self.state()

    def state(self) -> np.ndarray:
        return np.array(
            [
                (self.steps - self.t) / self.steps,
                self.left / self.shares,
                (self.price - self.price0) / self.price0 * 10,
            ]
        )

    def sell(self, n: float, extra_permanent: float = 0.0) -> float:
        n = float(np.clip(n, 0.0, self.left))
        cash = n * (self.price - self.eta * n)
        reward = cash - n * self.price0
        self.price += self.sigma * self.rng.normal() - self.gamma * (n + extra_permanent)
        self.left -= n
        self.t += 1
        return reward

    def step(self, action: int, extra_permanent: float = 0.0):
        steps_left = self.steps - self.t
        n = self.left if steps_left == 1 else self.multiples[action] * self.left / steps_left
        reward = self.sell(n, extra_permanent)
        done = self.t >= self.steps
        return self.state(), reward, done


def run_schedule(env: LiquidationEnv, schedule) -> float:
    """Implementation shortfall of a fixed schedule (shares per step)."""
    env.reset()
    total = 0.0
    for k, n in enumerate(schedule):
        total += env.sell(env.left if k == env.steps - 1 else n)
    return -total


def _bc_update(agent: DQN, states, actions) -> None:
    """Supervised step pushing the expert's action to the top of Q (the
    classification part of DQfD's pre-training)."""
    agent.opt.zero_grad()
    logits = agent.q(Tensor(np.asarray(states, float)))
    loss = -(log_softmax(logits, axis=1)[np.arange(len(actions)), np.asarray(actions)]).mean()
    loss.backward()
    agent.opt.step()


def train_dqn_liquidation(
    episodes: int = 300,
    env_kw: dict | None = None,
    expert_episodes: int = 0,
    models=None,
    seed: int = 0,
) -> dict:
    """RK312: double DQN on the liquidation simulator. RK419: with
    expert_episodes > 0 the buffer is first filled with TWAP demonstrations and
    the network pre-trained to imitate them before reinforcement learning.
    RK421: `models` = list of (sigma, eta) inside the ambiguity ball; each
    episode runs under the one where the current greedy policy's shortfall is
    worst. Returns the agent and its greedy shortfall vs TWAP on fresh paths."""
    env_kw = env_kw or {}
    env = LiquidationEnv(rng=seed, **env_kw)
    agent = DQN(3, len(LiquidationEnv.multiples), hidden=32, gamma=1.0, lr=1e-3, seed=seed)
    scale = env.shares * env.price0 * 1e-3
    twap_action = LiquidationEnv.multiples.index(1.0)
    demos = []
    for _ in range(expert_episodes):
        s, done = env.reset(), False
        while not done:
            s2, r, done = env.step(twap_action)
            agent.buffer.add(s, twap_action, r / scale, s2, float(done))
            demos.append((s, twap_action))
            s = s2
    for _ in range(4 * expert_episodes):
        idx = agent.rng.integers(0, len(demos), size=min(32, len(demos)))
        _bc_update(agent, [demos[i][0] for i in idx], [demos[i][1] for i in idx])
        agent.update(32)

    def greedy_shortfall(e, n=5):
        out = []
        for _ in range(n):
            s, done, total = e.reset(), False, 0.0
            while not done:
                s, r, done = e.step(agent.act(s))
                total += r
            out.append(-total)
        return float(np.mean(out))

    for ep in range(episodes):
        if models:
            cands = [
                LiquidationEnv(
                    sigma=sg,
                    eta=et,
                    rng=seed + ep,
                    **{k: v for k, v in env_kw.items() if k not in ("sigma", "eta")},
                )
                for sg, et in models
            ]
            env = max(cands, key=lambda e: greedy_shortfall(e, 2))
        eps = max(0.05, 1.0 - ep / (0.7 * episodes))
        s, done = env.reset(), False
        while not done:
            a = agent.act(s, eps)
            s2, r, done = env.step(a)
            agent.buffer.add(s, a, r / scale, s2, float(done))
            agent.update(32)
            s = s2
    test = LiquidationEnv(rng=seed + 10_000, **env_kw)
    dqn = greedy_shortfall(test, 50)
    test_twap = LiquidationEnv(rng=seed + 10_000, **env_kw)
    twap = float(
        np.mean(
            [run_schedule(test_twap, twap_schedule(test.shares, test.steps)) for _ in range(50)]
        )
    )
    return {"agent": agent, "dqn_shortfall": dqn, "twap_shortfall": twap}


def train_multi_agent_liquidation(
    n_agents: int = 2, episodes: int = 200, env_kw: dict | None = None, seed: int = 0
) -> dict:
    """RK310: independent DQN sellers liquidating the same stock at once; each
    one's price is pushed by everyone's permanent impact. Returns the agents
    and their mean greedy schedules (multiples of TWAP)."""
    env_kw = env_kw or {}
    envs = [LiquidationEnv(rng=seed + i, **env_kw) for i in range(n_agents)]
    agents = [
        DQN(3, len(LiquidationEnv.multiples), hidden=16, gamma=1.0, seed=seed + i)
        for i in range(n_agents)
    ]
    scale = envs[0].shares * envs[0].price0 * 1e-3
    for ep in range(episodes):
        eps = max(0.05, 1.0 - ep / (0.7 * episodes))
        states = [e.reset() for e in envs]
        done = False
        while not done:
            acts = [ag.act(s, eps) for ag, s in zip(agents, states, strict=True)]
            sold = [
                e.multiples[a] * e.left / (e.steps - e.t) for e, a in zip(envs, acts, strict=True)
            ]
            noise = envs[0].rng.normal()  # one shared price path
            rewards, total_sold = [], 0.0
            for i, e in enumerate(envs):
                n = e.left if e.steps - e.t == 1 else sold[i]
                n = float(np.clip(n, 0, e.left))
                rewards.append(n * (e.price - e.eta * n) - n * e.price0)
                e.left -= n
                e.t += 1
                total_sold += n
            done = envs[0].t >= envs[0].steps
            for i, e in enumerate(envs):
                e.price += e.sigma * noise - e.gamma * total_sold
                s2 = e.state()
                agents[i].buffer.add(states[i], acts[i], rewards[i] / scale, s2, float(done))
                agents[i].update(32)
                states[i] = s2
    schedules = []
    for ag, e in zip(agents, envs, strict=True):
        s, done, path = e.reset(), False, []
        while not done:
            a = ag.act(s)
            path.append(e.multiples[a])
            s, _, done = e.step(a)
        schedules.append(path)
    return {"agents": agents, "schedules": np.array(schedules)}


# ---------------------------------------------------------------- crowds and games (RK368, RK369, RK423)


def mean_field_execution(
    steps: int = 20,
    kappa: float = 0.1,
    phi: float = 0.01,
    alpha: float = 0.05,
    terminal: float = 10.0,
    q0: float = 1.0,
    iters: int = 2000,
    damping: float = 0.1,
) -> dict:
    """RK368: discrete mean-field control. Each trader sells v_t, holds
    q_{t+1} = q_t - v_t, and pays kappa v^2 + phi q^2 + alpha mu_t q_t, where
    mu_t is the crowd's mean selling rate (its permanent impact lowers the
    value of what is still held), plus terminal * q_T^2. Given mu the
    problem is linear-quadratic (backward Riccati); the equilibrium is the
    fixed point mu = the representative trader's rate, found by damped
    iteration (raises if it does not converge)."""
    mu = np.full(steps, q0 / steps)
    for _ in range(iters):
        a, b = terminal, 0.0  # V_{t+1}(q) = a q^2 + b q
        gains = []
        for t in range(steps - 1, -1, -1):
            # minimise kappa v^2 + phi q^2 + alpha mu_t q + a (q - v)^2 + b (q - v)
            k = a / (kappa + a)
            c = b / (2 * (kappa + a))
            gains.append((k, c))  # v = k q + c
            a_new = phi + kappa * k**2 + a * (1 - k) ** 2
            b_new = alpha * mu[t] + 2 * kappa * k * c - 2 * a * (1 - k) * c + b * (1 - k)
            a, b = a_new, b_new
        gains.reverse()
        q, rates = q0, []
        for k, c in gains:
            v = k * q + c
            rates.append(v)
            q -= v
        rates = np.array(rates)
        if not np.isfinite(rates).all() or np.abs(rates).max() > 1e6 * q0:
            break  # diverging
        if np.max(np.abs(rates - mu)) < 1e-10:
            return {"rates": rates, "inventory": q0 - np.r_[0.0, np.cumsum(rates)]}
        mu = (1 - damping) * mu + damping * rates
    raise ConfigurationError("mean-field iteration did not converge; lower damping or alpha")


def mfg_venue_split(fees, congestion, crowd: float = 1.0, iters: int = 500) -> np.ndarray:
    """RK369: a crowd of routers splits flow across venues whose cost per share
    is fee_v + congestion_v * (crowd flow sent there). Each router best-
    responds to the crowd's split; the mean-field equilibrium is the Wardrop
    split where every used venue has the same cost (solved by damped
    best-response averaging)."""
    f, k = np.asarray(fees, float), np.asarray(congestion, float)
    m = np.full(len(f), 1.0 / len(f))
    for i in range(1, iters + 1):
        cost = f + k * crowd * m
        br = np.zeros_like(m)
        br[np.argmin(cost)] = 1.0
        m += (br - m) / (i + 1)
    return m


def stackelberg_execution(
    shares: float,
    periods: int,
    sigma: float,
    eta: float,
    gamma: float,
    eta_follower: float,
    cost_follower: float,
    risk_grid=(0.0, 1e-6, 1e-5, 1e-4, 1e-3),
    risk_aversion: float = 1e-6,
) -> dict:
    """RK423: the broker (leader) picks an Almgren-Chriss urgency; a predator
    (follower) sells phi n_k ahead of each slice and buys it back after,
    choosing phi_k = clip((gamma n_k - c_f) / (2 eta_f n_k), 0, 1) to maximise
    gamma phi n^2 - eta_f (phi n)^2 - c_f phi n. Each step costs the leader an
    extra gamma phi_k n_k^2. The leader chooses the urgency minimising its
    cost + risk_aversion * variance given that response."""
    best = None
    for lam in risk_grid:
        ac = almgren_chriss(shares, float(periods), periods, sigma, eta, gamma, 0.0, lam)
        n = ac["trades"]
        phi = np.clip((gamma * n - cost_follower) / (2 * eta_follower * np.maximum(n, 1e-12)), 0, 1)
        cost = ac["expected_cost"] + (gamma * phi * n**2).sum() + risk_aversion * ac["variance"]
        if best is None or cost < best["cost"]:
            best = {"urgency": lam, "trades": n, "follower_phi": phi, "cost": float(cost)}
    return best


# ---------------------------------------------------------------- robust and learned schedules


def wdro_execution(
    shares: float,
    periods: int,
    sigma: float,
    eta: float,
    risk_aversion: float,
    radius_sigma: float = 0.0,
    radius_eta: float = 0.0,
) -> dict:
    """RK370: worst case of the Almgren-Chriss objective over Wasserstein
    balls on the impact coefficient (cost linear in eta: eta + radius_eta) and
    the volatility (Gaussian W2 ball: sigma + radius_sigma), then the AC
    schedule under those worst-case parameters. The two radii pull opposite
    ways: more volatility front-loads the sale, more impact flattens it."""
    return almgren_chriss(
        shares,
        float(periods),
        periods,
        sigma + radius_sigma,
        eta + radius_eta,
        risk_aversion=risk_aversion,
    )


def evolve_execution(
    shares: float, periods: int, venues: int, cost_fn, gens: int = 30, pop: int = 24, rng=None
) -> dict:
    """RK358/RK360: evolve a (periods x venues) allocation of the parent order
    (softmax over all cells) minimising cost_fn(allocation in shares)."""

    def decode(x):
        e = np.exp(x - x.max())
        return shares * (e / e.sum()).reshape(periods, venues)

    out = genetic_search(
        lambda x: -cost_fn(decode(x)), periods * venues, pop=pop, gens=gens, rng=rng
    )
    out["allocation"] = decode(out["best"])
    return out


def venue_cost(fees, impacts):
    """Cost of an allocation (periods x venues): fee_v x + impact_v x^2."""
    f, k = np.asarray(fees, float), np.asarray(impacts, float)
    return lambda alloc: float((alloc * f + k * alloc**2).sum())


def train_maddpg_router(
    n_venues: int = 2, episodes: int = 300, slice_size: float = 1.0, seed: int = 0
) -> dict:
    """RK422: one MADDPG agent per venue; each sees its venue's current
    liquidity l_v (impact eta_v = 0.1 / l_v) and outputs a score; the slice
    is split by softmax of the scores and all agents share the reward
    -sum_v eta_v x_v^2."""
    rng = np.random.default_rng(seed)
    agent = MADDPG([1] * n_venues, [1] * n_venues, hidden=16, gamma=0.0, seed=seed)

    def split(acts):
        e = np.exp(3 * np.array([a[0] for a in acts]))
        return slice_size * e / e.sum()

    for _ in range(episodes):
        liq = rng.uniform(0.5, 2.0, n_venues)
        obs = [np.array([v]) for v in liq]
        acts = agent.act(obs, noise=0.3)
        x = split(acts)
        reward = -float((0.1 / liq * x**2).sum())
        agent.buffer.add(
            np.concatenate(obs),
            np.concatenate(acts),
            np.full(n_venues, reward),
            np.concatenate(obs),
            1.0,
        )
        agent.update(32)
    return {
        "agent": agent,
        "split": lambda liquidity: split(agent.act([np.array([v]) for v in liquidity])),
    }


class NeuralOperatorExecution:
    """RK410: a DeepONet-style operator from a temporary-impact curve (eta at
    `periods` times, the branch input) to a liquidation schedule (softmax over
    periods via the trunk's time features). Trained over random impact curves
    on the worst case in a ball: each sampled curve is inflated by `radius`
    (linear cost, so eta + radius is the worst member) before scoring."""

    def __init__(self, periods: int = 10, width: int = 16, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.periods = periods
        self.branch = MLP([periods, width, width], rng)
        self.trunk = MLP([1, width, width], rng)
        self.t = np.linspace(0, 1, periods)[:, None]

    def schedule(self, eta_curve) -> Tensor:
        b = self.branch(Tensor(np.atleast_2d(eta_curve)))  # (B, width)
        tr = self.trunk(Tensor(self.t))  # (periods, width)
        return softmax(b @ tr.T, axis=1)  # (B, periods) fractions

    def fit(
        self,
        steps: int = 300,
        batch: int = 32,
        radius: float = 0.0,
        sigma: float = 0.02,
        risk: float = 1.0,
        lr: float = 0.01,
        rng=None,
    ) -> list[float]:
        rng = np.random.default_rng(rng)
        tri = Tensor(np.tril(np.ones((self.periods, self.periods))).T)  # w @ tri = sold so far

        def loss():
            base = rng.uniform(0.5, 1.5, (batch, 1))
            slope = rng.uniform(-0.5, 0.5, (batch, 1))
            eta = np.clip(base + slope * (self.t.T - 0.5), 0.1, None)
            w = self.schedule(eta)
            impact = (w**2 * Tensor(eta + radius)).sum(axis=1)
            held = 1.0 - w @ tri
            variance = (held**2).sum(axis=1) * (risk * sigma**2)
            return (impact + variance).mean()

        return fit(loss, [*self.branch.params, *self.trunk.params], steps, lr)


class AttentiveExecutionPolicy:
    """RK425: at each step, attention over the order book's depth levels
    summarises liquidity, an LSTM carries the history, and a sigmoid head
    sells that fraction of what is left (everything on the last step). The
    temporary impact of a slice falls with the visible depth. Trained by
    back-propagating the simulated shortfall through the episode (a pathwise
    policy gradient)."""

    def __init__(self, levels: int = 5, hidden: int = 8, steps: int = 10, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.levels, self.steps = levels, steps
        self.att_w = param((2, hidden), rng)
        self.att_v = param((hidden, 1), rng)
        self.lstm = LSTM(1 + 2, hidden, rng)
        self.head = MLP([hidden, 1], rng)
        self.opt = Adam([self.att_w, self.att_v, *self.lstm.params, *self.head.params], 0.02)

    def _episode(self, depth) -> tuple[Tensor, list[float]]:
        pos = np.linspace(0, 1, self.levels)
        h, c = self.lstm.zero_state()
        left, cost, fractions = Tensor(1.0), Tensor(0.0), []
        for k in range(self.steps):
            d = depth[k]
            feats = Tensor(np.column_stack([d / d.mean(), pos]))
            alpha = softmax((feats @ self.att_w).tanh() @ self.att_v, axis=0)  # (levels, 1)
            liquidity = (alpha[:, 0] * Tensor(d)).sum()
            x = concat([liquidity.reshape(1), Tensor([1 - k / self.steps]), left.reshape(1)])
            h, c = self.lstm.cell(x, h, c)
            frac = Tensor(1.0) if k == self.steps - 1 else self.head(h)[0].sigmoid()
            n = left * frac
            cost = cost + n * n * (1.0 / float(d.sum()))
            left = left - n
            fractions.append(float(frac.data))
        return cost, fractions

    def fit(self, depth_paths, epochs: int = 30) -> list[float]:
        hist = []
        for _ in range(epochs):
            total = 0.0
            for depth in depth_paths:
                self.opt.zero_grad()
                cost, _ = self._episode(np.asarray(depth, float))
                cost.backward()
                self.opt.step()
                total += float(cost.data)
            hist.append(total / len(depth_paths))
        return hist

    def act(self, depth) -> list[float]:
        return self._episode(np.asarray(depth, float))[1]
