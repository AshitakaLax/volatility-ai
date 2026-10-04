"""
Reinforcement-learning trading agents (ledger A1, RL1, RL2, RL6; all
❌ for now: far more free parameters than the repo's multiple-comparison
discipline supports, and few correction episodes to learn from). NumPy
only -- the sources use TensorFlow 1.x and stable-baselines3, rebuilt here
as a one-hidden-layer MLP with hand-written backprop and Adam.

Sources:

  * RL6 / A1: huseinzol05/Stock-Prediction-Models agent/5.q-learning-agent,
    7.double-q-learning-agent and 6.evolution-strategy-agent notebooks --
    the single-unit trader, its window state, cash-only reward, replay and
    epsilon schedules, and the Deep_Evolution_Strategy optimiser.
  * A1: Watkins & Dayan, "Q-learning", Machine Learning 8 (1992) -- the
    tabular update the deep agents approximate.
  * RL1 / RL2: AI4Finance-Foundation/FinRL,
    finrl/meta/env_stock_trading/env_stocktrading.py (StockTradingEnv step,
    _sell_stock, _buy_stock) and finrl/agents/stablebaselines3/models.py
    (DRLEnsembleAgent: rolling windows, validation Sharpe, turbulence
    threshold); Liu et al., "Deep Reinforcement Learning for Automated
    Stock Trading: An Ensemble Strategy", ICAIF 2020.
  * RL2 update rules: Schulman et al. 2016 (GAE), 2017 (PPO clip); Mnih et
    al. 2016 (A2C); Lillicrap et al. 2016 (DDPG); Fujimoto et al. 2018
    (TD3); Haarnoja et al. 2018 (SAC).

Source quirks preserved on purpose:

  * huseinzol05 agents reward CASH only, (cash - initial) / initial, so an
    open unit counts against the reward until it is sold; `done` is
    "cash below initial". The Q-learning agent replays the LAST
    batch_size transitions, not a random sample.
  * FinRL's validation Sharpe annualises with sqrt(4), and its adaptive
    turbulence threshold is computed and then overwritten by the in-sample
    99th percentile; `adaptive=True` keeps the branch the source discards.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- shared numerics


class MLP:
    """dense(relu) -> dense, initialised like tf.layers.dense (Glorot
    uniform weights, zero biases)."""

    def __init__(self, n_in: int, n_hidden: int, n_out: int, rng: np.random.Generator) -> None:
        def glorot(a: int, b: int) -> np.ndarray:
            limit = np.sqrt(6.0 / (a + b))
            return rng.uniform(-limit, limit, (a, b))

        self.params = {
            "w1": glorot(n_in, n_hidden),
            "b1": np.zeros(n_hidden),
            "w2": glorot(n_hidden, n_out),
            "b2": np.zeros(n_out),
        }

    def forward(self, x):
        x = np.atleast_2d(np.asarray(x, dtype=float))
        pre = x @ self.params["w1"] + self.params["b1"]
        h = np.maximum(pre, 0.0)
        return h @ self.params["w2"] + self.params["b2"], (x, pre, h)

    def predict(self, x) -> np.ndarray:
        return self.forward(x)[0]

    def backward(self, cache, dout) -> dict[str, np.ndarray]:
        x, pre, h = cache
        dh = (dout @ self.params["w2"].T) * (pre > 0)
        return {"w1": x.T @ dh, "b1": dh.sum(0), "w2": h.T @ dout, "b2": dout.sum(0)}

    def copy_from(self, other: MLP) -> None:
        self.params = {k: v.copy() for k, v in other.params.items()}


class Adam:
    """tf.train.AdamOptimizer defaults (beta1 0.9, beta2 0.999, eps 1e-8)."""

    def __init__(self, lr: float, b1: float = 0.9, b2: float = 0.999, eps: float = 1e-8) -> None:
        self.lr, self.b1, self.b2, self.eps = lr, b1, b2, eps
        self.m: dict = {}
        self.v: dict = {}
        self.t = 0

    def step(self, params: dict, grads: dict) -> None:
        self.t += 1
        lr_t = self.lr * np.sqrt(1 - self.b2**self.t) / (1 - self.b1**self.t)
        for k, g in grads.items():
            self.m[k] = self.b1 * self.m.get(k, 0.0) + (1 - self.b1) * g
            self.v[k] = self.b2 * self.v.get(k, 0.0) + (1 - self.b2) * g * g
            params[k] = params[k] - lr_t * self.m[k] / (np.sqrt(self.v[k]) + self.eps)


# ---------------------------------------------------------------- A1 tabular Q-learning


class QTable:
    """Watkins Q-learning: Q(s,a) += alpha * (r + gamma max_a' Q(s',a') - Q(s,a)),
    epsilon-greedy behaviour."""

    def __init__(
        self, n_states: int, n_actions: int, alpha=0.1, gamma=0.95, epsilon=0.1, seed=None
    ):
        self.q = np.zeros((n_states, n_actions))
        self.alpha, self.gamma, self.epsilon = alpha, gamma, epsilon
        self.rng = np.random.default_rng(seed)

    def act(self, s: int, greedy: bool = False) -> int:
        if not greedy and self.rng.random() < self.epsilon:
            return int(self.rng.integers(self.q.shape[1]))
        return int(np.argmax(self.q[s]))

    def update(self, s: int, a: int, r: float, s_next: int, done: bool = False) -> float:
        target = r if done else r + self.gamma * self.q[s_next].max()
        td = target - self.q[s, a]
        self.q[s, a] += self.alpha * td
        return td


def sign_pattern_state(returns, k: int, position: int) -> int:
    """A small discrete trading state: the up/down pattern of the last k
    returns (2^k codes) times the current position (flat 0 / long 1)."""
    r = np.asarray(returns, dtype=float)[-k:]
    if len(r) < k:
        raise ConfigurationError(f"need {k} returns")
    code = int("".join("1" if x > 0 else "0" for x in r), 2)
    return code * 2 + int(position)


# ---------------------------------------------------------------- RL6 huseinzol05 agents


def window_state(trend, t: int, window: int) -> np.ndarray:
    """huseinzol05 `get_state`: the window first differences ending at t,
    left-padded with the first price."""
    data = list(trend)
    size = window + 1
    d = t - size + 1
    block = data[d : t + 1] if d >= 0 else -d * [data[0]] + data[0 : t + 1]
    return np.array([block[i + 1] - block[i] for i in range(size - 1)], dtype=float)


QAGENT_PRESETS: dict[str, dict] = {
    # agent/5.q-learning-agent.ipynb
    "q_learning": {
        "hidden": 256,
        "lr": 1e-5,
        "optimizer": "sgd",
        "loss": "mean",
        "gamma": 0.95,
        "epsilon": 0.5,
        "epsilon_min": 0.01,
        "epsilon_decay": 0.999,
        "schedule": "per_replay",
        "memory": 1000,
        "replay": "last",
        "batch": 32,
        "double": False,
        "copy_every": None,
        "buy_cutoff": True,
    },
    # agent/7.double-q-learning-agent.ipynb
    "double_q_learning": {
        "hidden": 500,
        "lr": 0.003,
        "optimizer": "adam",
        "loss": "sum",
        "gamma": 0.99,
        "epsilon": 0.5,
        "epsilon_min": 0.1,
        "decay_rate": 0.005,
        "schedule": "per_epoch",
        "memory": 300,
        "replay": "random",
        "batch": 32,
        "double": True,
        "copy_every": 1000,
        "buy_cutoff": False,
    },
}


class HuseinQAgent:
    """The huseinzol05 deep-Q single-unit trader. Actions: 0 hold, 1 buy one
    unit (if cash allows; the Q-learning preset only before the last
    window/2 bars), 2 sell the oldest unit. Reward after every bar is
    (cash - initial) / initial, done = cash < initial. The 'double' preset
    evaluates the online network's argmax with a target network copied
    every 1000 steps (double DQN)."""

    def __init__(
        self, trend, window: int = 30, skip: int = 1, preset="q_learning", seed=None, **kw
    ):
        if preset not in QAGENT_PRESETS:
            raise ConfigurationError(f"preset must be one of {sorted(QAGENT_PRESETS)}")
        self.cfg = {**QAGENT_PRESETS[preset], **kw}
        self.trend = [float(x) for x in trend]
        self.window, self.skip, self.half_window = window, skip, window // 2
        self.rng = np.random.default_rng(seed)
        self.model = MLP(window, self.cfg["hidden"], 3, self.rng)
        self.target = MLP(window, self.cfg["hidden"], 3, self.rng) if self.cfg["double"] else None
        self.opt = Adam(self.cfg["lr"]) if self.cfg["optimizer"] == "adam" else None
        self.memory: deque = deque(maxlen=self.cfg["memory"])
        self.epsilon = self.cfg["epsilon"]
        self.steps = 0

    def act(self, state, greedy: bool = False) -> int:
        if not greedy and self.rng.random() < self.epsilon:
            return int(self.rng.integers(3))
        return int(np.argmax(self.model.predict(state)[0]))

    def _targets(self, batch):
        states = np.array([b[0] for b in batch])
        nexts = np.array([b[3] for b in batch])
        q = self.model.predict(states)
        q_new = self.model.predict(nexts)
        q_tgt = self.target.predict(nexts) if self.target is not None else None
        y = q.copy()
        for i, (_, a, r, _, done) in enumerate(batch):
            y[i, a] = r
            if not done:
                if q_tgt is not None:
                    y[i, a] += self.cfg["gamma"] * q_tgt[i, int(np.argmax(q_new[i]))]
                else:
                    y[i, a] += self.cfg["gamma"] * q_new[i].max()
        return states, y

    def replay(self) -> float:
        n = min(self.cfg["batch"], len(self.memory))
        if self.cfg["replay"] == "last":
            batch = list(self.memory)[len(self.memory) - n :]
        else:
            idx = self.rng.choice(len(self.memory), size=n, replace=False)
            batch = [self.memory[i] for i in idx]
        x, y = self._targets(batch)
        out, cache = self.model.forward(x)
        diff = out - y
        scale = 2.0 / diff.size if self.cfg["loss"] == "mean" else 2.0
        grads = self.model.backward(cache, scale * diff)
        if self.opt is not None:
            self.opt.step(self.model.params, grads)
        else:
            for k, g in grads.items():
                self.model.params[k] -= self.cfg["lr"] * g
        if self.cfg["schedule"] == "per_replay" and self.epsilon > self.cfg["epsilon_min"]:
            self.epsilon *= self.cfg["epsilon_decay"]
        cost = float((diff**2).mean() if self.cfg["loss"] == "mean" else (diff**2).sum())
        return cost

    def _step_trade(self, action, t, cash, inventory):
        price = self.trend[t]
        cutoff = not self.cfg["buy_cutoff"] or t < len(self.trend) - self.half_window
        if action == 1 and cash >= price and cutoff:
            inventory.append(price)
            return cash - price, 0.0
        if action == 2 and inventory:
            bought = inventory.pop(0)
            return cash + price, price - bought
        return cash, 0.0

    def train(self, iterations: int, initial_money: float = 10_000.0) -> list[float]:
        """One pass over the trend per iteration; returns realised profit per
        iteration."""
        profits = []
        for i in range(iterations):
            cash, inventory, total = initial_money, [], 0.0
            state = window_state(self.trend, 0, self.window)
            for t in range(0, len(self.trend) - 1, self.skip):
                if self.target is not None and (self.steps + 1) % self.cfg["copy_every"] == 0:
                    self.target.copy_from(self.model)
                action = self.act(state)
                nxt = window_state(self.trend, t + 1, self.window)
                cash, gain = self._step_trade(action, t, cash, inventory)
                total += gain
                reward = (cash - initial_money) / initial_money
                self.memory.append((state, action, reward, nxt, cash < initial_money))
                state = nxt
                self.replay()
                self.steps += 1
                if self.cfg["schedule"] == "per_epoch":
                    lo = self.cfg["epsilon_min"]
                    self.epsilon = lo + (1.0 - lo) * np.exp(-self.cfg["decay_rate"] * i)
            profits.append(total)
        return profits

    def trade(self, initial_money: float = 10_000.0) -> dict:
        """The notebooks' `buy`, greedy: buy/sell bars and the cash return."""
        cash, inventory, buys, sells = initial_money, [], [], []
        state = window_state(self.trend, 0, self.window)
        for t in range(0, len(self.trend) - 1, self.skip):
            action = self.act(state, greedy=True)
            before = len(inventory)
            cash, _ = self._step_trade(action, t, cash, inventory)
            if len(inventory) > before:
                buys.append(t)
            elif len(inventory) < before:
                sells.append(t)
            state = window_state(self.trend, t + 1, self.window)
        gains = cash - initial_money
        return {
            "buys": buys,
            "sells": sells,
            "total_gains": gains,
            "invest": gains / initial_money * 100,
        }


class DeepEvolutionStrategy:
    """agent/6.evolution-strategy-agent `Deep_Evolution_Strategy`: per epoch
    draw population_size Gaussian perturbations, score weights + sigma*eps,
    standardise the rewards, and move along the reward-weighted noise:
    w += lr / (population_size * sigma) * eps' rewards."""

    def __init__(
        self,
        weights: list[np.ndarray],
        reward_function: Callable[[list[np.ndarray]], float],
        population_size: int = 15,
        sigma: float = 0.1,
        learning_rate: float = 0.03,
        seed=None,
    ) -> None:
        self.weights = [np.array(w, dtype=float) for w in weights]
        self.reward_function = reward_function
        self.population_size, self.sigma, self.learning_rate = population_size, sigma, learning_rate
        self.rng = np.random.default_rng(seed)

    def step(self) -> np.ndarray:
        population = [
            [self.rng.standard_normal(w.shape) for w in self.weights]
            for _ in range(self.population_size)
        ]
        rewards = np.array(
            [
                self.reward_function(
                    [w + self.sigma * e for w, e in zip(self.weights, p, strict=True)]
                )
                for p in population
            ]
        )
        z = (rewards - rewards.mean()) / (rewards.std() + 1e-7)
        for k, w in enumerate(self.weights):
            a = np.array([p[k] for p in population])
            self.weights[k] = w + self.learning_rate / (
                self.population_size * self.sigma
            ) * np.tensordot(z, a, axes=1)
        return rewards

    def train(self, epochs: int = 100) -> list[float]:
        history = []
        for _ in range(epochs):
            self.step()
            history.append(self.reward_function(self.weights))
        return history


def es_model_weights(input_size: int, layer_size: int = 500, output_size: int = 3, seed=None):
    """The ES agent's `Model`: [W_in (input x layer), W_out (layer x 3),
    bias (1 x layer)], standard normal; decision = (x W_in + bias) W_out --
    linear, no activation."""
    rng = np.random.default_rng(seed)
    return [
        rng.standard_normal((input_size, layer_size)),
        rng.standard_normal((layer_size, output_size)),
        rng.standard_normal((1, layer_size)),
    ]


def es_agent_reward(
    weights, trend, window: int = 30, skip: int = 1, initial_money: float = 10_000.0
):
    """The ES agent's `get_reward`: trade one unit per signal through the
    trend with argmax actions (1 buy if affordable, 2 sell the oldest) and
    score the percentage change in CASH."""
    data = [float(x) for x in trend]
    money = initial_money
    inventory: list[float] = []
    state = window_state(data, 0, window)
    for t in range(0, len(data) - 1, skip):
        feed = state[None, :] @ weights[0] + weights[-1]
        action = int(np.argmax((feed @ weights[1])[0]))
        if action == 1 and money >= data[t]:
            inventory.append(data[t])
            money -= data[t]
        elif action == 2 and inventory:
            inventory.pop(0)
            money += data[t]
        state = window_state(data, t + 1, window)
    return (money - initial_money) / initial_money * 100


# ---------------------------------------------------------------- RL1/RL2 FinRL


class FinRLStockTradingEnv:
    """FinRL StockTradingEnv's trading mechanics on arrays: prices (T x n),
    optional indicators (T x k) and turbulence (T). State =
    [cash, prices, holdings, indicators]. Each step scales actions in
    [-1, 1] by hmax to integer shares; when turbulence >= threshold every
    action becomes -hmax and sells liquidate the whole holding while buys
    are blocked. Sells run first (most negative action first), then buys
    (largest first), each net of its cost; reward = change in total assets
    x reward_scaling. Turbulence starts at 0 and is read for the new day
    after each step."""

    def __init__(
        self,
        prices,
        indicators=None,
        turbulence=None,
        hmax: int = 100,
        initial_amount: float = 1_000_000.0,
        buy_cost_pct: float = 0.001,
        sell_cost_pct: float = 0.001,
        reward_scaling: float = 1e-4,
        turbulence_threshold: float | None = None,
    ) -> None:
        self.prices = np.atleast_2d(np.asarray(prices, dtype=float))
        if self.prices.shape[0] == 1 and np.ndim(prices) == 1:
            self.prices = self.prices.T
        self.n = self.prices.shape[1]
        t = self.prices.shape[0]
        self.indicators = (
            np.zeros((t, 0))
            if indicators is None
            else np.asarray(indicators, dtype=float).reshape(t, -1)
        )
        self.turbulence_series = None if turbulence is None else np.asarray(turbulence, dtype=float)
        self.hmax, self.initial_amount = hmax, initial_amount
        self.buy_cost, self.sell_cost = buy_cost_pct, sell_cost_pct
        self.reward_scaling, self.turbulence_threshold = reward_scaling, turbulence_threshold
        self.reset()

    def reset(self) -> np.ndarray:
        self.day, self.cash, self.turbulence = 0, self.initial_amount, 0.0
        self.holdings = np.zeros(self.n)
        self.trades, self.cost = 0, 0.0
        self.asset_memory = [self.initial_amount]
        return self.state

    @property
    def state(self) -> np.ndarray:
        return np.r_[self.cash, self.prices[self.day], self.holdings, self.indicators[self.day]]

    def total_asset(self) -> float:
        return float(self.cash + self.prices[self.day] @ self.holdings)

    def _turbulent(self) -> bool:
        return (
            self.turbulence_threshold is not None and self.turbulence >= self.turbulence_threshold
        )

    def _sell(self, i: int, action: int) -> float:
        price = self.prices[self.day, i]
        if self.holdings[i] <= 0 or (self._turbulent() and price <= 0):
            return 0.0
        shares = self.holdings[i] if self._turbulent() else min(abs(action), self.holdings[i])
        self.cash += price * shares * (1 - self.sell_cost)
        self.cost += price * shares * self.sell_cost
        self.holdings[i] -= shares
        self.trades += 1
        return shares

    def _buy(self, i: int, action: int) -> float:
        if self._turbulent():
            return 0.0
        price = self.prices[self.day, i]
        available = self.cash // (price * (1 + self.buy_cost))
        shares = min(available, action)
        self.cash -= price * shares * (1 + self.buy_cost)
        self.cost += price * shares * self.buy_cost
        self.holdings[i] += shares
        self.trades += 1
        return shares

    def step(self, actions) -> tuple[np.ndarray, float, bool]:
        if self.day >= self.prices.shape[0] - 1:
            return self.state, 0.0, True
        acts = (np.asarray(actions, dtype=float) * self.hmax).astype(int)
        if self._turbulent():
            acts = np.full(self.n, -self.hmax)
        begin = self.total_asset()
        order = np.argsort(acts)
        for i in order[: int((acts < 0).sum())]:
            self._sell(int(i), int(acts[i]))
        for i in order[::-1][: int((acts > 0).sum())]:
            self._buy(int(i), int(acts[i]))
        self.day += 1
        if self.turbulence_threshold is not None and self.turbulence_series is not None:
            self.turbulence = float(self.turbulence_series[self.day])
        end = self.total_asset()
        self.asset_memory.append(end)
        return self.state, (end - begin) * self.reward_scaling, self.day >= self.prices.shape[0] - 1


def finrl_validation_sharpe(daily_returns) -> float:
    """DRLEnsembleAgent.get_validation_sharpe: sqrt(4) * mean / std (ddof=1)
    of the validation window's daily returns; zero variance gives inf for a
    positive mean, else 0."""
    r = pd.Series(daily_returns, dtype=float)
    if r.var() == 0:
        return float("inf") if r.mean() > 0 else 0.0
    return float(4**0.5 * r.mean() / r.std())


def finrl_turbulence_threshold(insample, recent=None, adaptive: bool = False) -> float:
    """run_ensemble_strategy's threshold. The source computes: if the mean
    turbulence of the 63 days before validation exceeds the in-sample 90th
    percentile, use that percentile, else the in-sample max -- and then
    overwrites it with the in-sample 99th percentile. adaptive=True returns
    the discarded branch."""
    ins = np.asarray(insample, dtype=float)
    if not adaptive:
        return float(np.quantile(ins, 0.99))
    q90 = float(np.quantile(ins, 0.90))
    if recent is None:
        raise ConfigurationError("adaptive=True needs the recent turbulence window")
    return q90 if float(np.mean(recent)) > q90 else float(np.quantile(ins, 1.0))


def finrl_ensemble_windows(
    n_dates: int, rebalance_window: int = 63, validation_window: int = 63
) -> list[dict[str, int]]:
    """The ensemble's rolling schedule over trade-date indices: for
    i = rebalance + validation, ... step rebalance: train on [0, i - r - v),
    validate on [i - r - v, i - r), trade on [i - r, i)."""
    out = []
    for i in range(rebalance_window + validation_window, n_dates, rebalance_window):
        out.append(
            {
                "train_end": i - rebalance_window - validation_window,
                "validation": (i - rebalance_window - validation_window, i - rebalance_window),
                "trade": (i - rebalance_window, i),
            }
        )
    return out


def finrl_ensemble_pick(sharpes: dict[str, float]) -> str:
    """The model with the highest validation Sharpe (first on a tie)."""
    names = list(sharpes)
    return names[int(np.argmax([sharpes[k] for k in names]))]


# ---------------------------------------------------------------- RL2 update rules


def gae(rewards, values, dones, last_value: float, gamma: float = 0.99, lam: float = 0.95):
    """Generalised advantage estimation: delta_t = r_t + gamma V_{t+1}(1-d_t)
    - V_t, A_t = delta_t + gamma lam (1-d_t) A_{t+1}. Returns (advantages,
    returns = advantages + values)."""
    r, v, d = (np.asarray(x, dtype=float) for x in (rewards, values, dones))
    adv = np.zeros_like(r)
    nxt_v, running = last_value, 0.0
    for t in range(len(r) - 1, -1, -1):
        delta = r[t] + gamma * nxt_v * (1 - d[t]) - v[t]
        running = delta + gamma * lam * (1 - d[t]) * running
        adv[t] = running
        nxt_v = v[t]
    return adv, adv + v


def ppo_clip_loss(ratio, advantages, eps: float = 0.2) -> tuple[float, np.ndarray]:
    """PPO's clipped surrogate, as a loss: -mean(min(r A, clip(r, 1-eps,
    1+eps) A)). Returns (loss, d loss / d ratio)."""
    r, a = np.asarray(ratio, dtype=float), np.asarray(advantages, dtype=float)
    unclipped, clipped = r * a, np.clip(r, 1 - eps, 1 + eps) * a
    use_unclipped = unclipped <= clipped
    grad = np.where(use_unclipped, a, np.where((r > 1 - eps) & (r < 1 + eps), a, 0.0))
    return float(-np.minimum(unclipped, clipped).mean()), -grad / len(r)


def ddpg_target(reward, done, q_next, gamma: float = 0.99):
    return np.asarray(reward) + gamma * (1 - np.asarray(done)) * np.asarray(q_next)


def td3_target(reward, done, q1_next, q2_next, gamma: float = 0.99):
    """Clipped double-Q target (Q evaluated at the smoothed target action)."""
    return np.asarray(reward) + gamma * (1 - np.asarray(done)) * np.minimum(q1_next, q2_next)


def td3_smoothed_action(action, rng, sigma=0.2, noise_clip=0.5, low=-1.0, high=1.0):
    """Target policy smoothing: a + clip(N(0, sigma), -c, c), clipped to the
    action bounds."""
    a = np.asarray(action, dtype=float)
    noise = np.clip(rng.normal(0.0, sigma, a.shape), -noise_clip, noise_clip)
    return np.clip(a + noise, low, high)


def sac_target(reward, done, q1_next, q2_next, logp_next, alpha: float = 0.2, gamma: float = 0.99):
    """Soft Bellman target: r + gamma (1-d) (min Q - alpha log pi(a'|s'))."""
    soft = np.minimum(q1_next, q2_next) - alpha * np.asarray(logp_next)
    return np.asarray(reward) + gamma * (1 - np.asarray(done)) * soft


def soft_update(target: dict, source: dict, tau: float = 0.005) -> None:
    """Polyak averaging: target <- tau source + (1 - tau) target."""
    for k in target:
        target[k] = tau * source[k] + (1 - tau) * target[k]


class LinearA2C:
    """Advantage actor-critic with a linear softmax policy and a linear
    value function: policy step along (onehot(a) - pi(s)) s A, value step
    along (G - V(s)) s, with A = G - V(s)."""

    def __init__(self, n_features: int, n_actions: int, lr_pi=0.05, lr_v=0.1, seed=None):
        self.theta = np.zeros((n_features, n_actions))
        self.w = np.zeros(n_features)
        self.lr_pi, self.lr_v = lr_pi, lr_v
        self.rng = np.random.default_rng(seed)

    def policy(self, s) -> np.ndarray:
        z = np.asarray(s, dtype=float) @ self.theta
        e = np.exp(z - z.max())
        return e / e.sum()

    def act(self, s) -> int:
        return int(self.rng.choice(self.theta.shape[1], p=self.policy(s)))

    def update(self, states, actions, returns) -> None:
        for s, a, g in zip(states, actions, returns, strict=True):
            s = np.asarray(s, dtype=float)
            adv = g - s @ self.w
            onehot = np.eye(self.theta.shape[1])[a]
            self.theta += self.lr_pi * np.outer(s, onehot - self.policy(s)) * adv
            self.w += self.lr_v * adv * s
