"""
Reinforcement learning from three trading papers (ledger C-RL5, C-RL4 and
RL3/A4; all ❌ for now). NumPy only.

  * C-RL5  Moody & Saffell, "Learning to Trade via Direct Reinforcement",
           IEEE Transactions on Neural Networks 12(4), 2001; Moody, Wu, Liao
           & Saffell, "Performance functions and reinforcement learning for
           trading systems and portfolios", J. Forecasting 17, 1998. A
           recurrent trader F_t = tanh(w . [1, r_{t-m+1..t}, F_{t-1}]) is
           trained by gradient ascent on the Sharpe ratio (batch) or on the
           differential Sharpe ratio (online), with transaction costs in
           the return R_t = mu (F_{t-1} r_t - delta |F_t - F_{t-1}|).
  * C-RL4  Huang, "Financial Trading as a Game: A Deep Reinforcement
           Learning Approach" (arXiv 1807.02787, 2018). A recurrent Q-network
           over actions {short, neutral, long}; because the trader's action
           does not move the market, the reward of EVERY action is known at
           each step, so all three Q-values are updated at once ("action
           augmentation"), each against its own next state (the position it
           would leave). Soft target-network updates.
  * RL3    Jiang, Xu & Liang, "A Deep Reinforcement Learning Framework for the
           Financial Portfolio Management Problem" (arXiv 1706.10059, 2017) --
           the EIIE policy behind PGPortfolio: one shared evaluator scores
           each asset from its own normalised price window and its previous
           weight, a cash bias joins the softmax, the reward is the log
           return net of the transaction remainder factor mu (their Eq. 14),
           previous weights come from a portfolio-vector memory, and
           mini-batches are drawn geometrically favouring recent periods
           (online stochastic batch learning).

Simplifications, stated: the DRQN's recurrence is an Elman (tanh) layer, not
an LSTM, and the position enters at the output layer so the hidden state is
action-independent (which is what makes augmentation exact); the EIIE
evaluator is linear in the window instead of a CNN, and its gradient uses
the paper's first-order cost mu ~ 1 - c sum|w'_i - w_i| while evaluation
uses the exact Eq. 14.
"""

from __future__ import annotations

import numpy as np

from engine.core.exceptions import ConfigurationError
from research.catalog.rl_agents import Adam, soft_update

# ---------------------------------------------------------------- C-RL5 RRL / DSR


def differential_sharpe(returns, eta: float = 0.01, a0=None, b0=None, warmup: int = 10):
    """Moody's differential Sharpe ratio: with exponential moving estimates
    A_t = A_{t-1} + eta (R_t - A_{t-1}) and B_t likewise of R_t^2,

        D_t = (B_{t-1} dA_t - A_{t-1} dB_t / 2) / (B_{t-1} - A_{t-1}^2)^{3/2},

    the first-order sensitivity of the moving Sharpe ratio A/sqrt(B - A^2)
    to eta. A and B start at the mean and mean square of the first `warmup`
    returns unless given. Returns (D, A, B) per step."""
    r = np.asarray(returns, dtype=float)
    a = float(np.mean(r[:warmup])) if a0 is None else float(a0)
    b = float(np.mean(r[:warmup] ** 2)) if b0 is None else float(b0)
    d, aa, bb = np.zeros(len(r)), np.zeros(len(r)), np.zeros(len(r))
    for t, x in enumerate(r):
        da, db = x - a, x * x - b
        var = b - a * a
        d[t] = (b * da - 0.5 * a * db) / var**1.5 if var > 0 else 0.0
        a, b = a + eta * da, b + eta * db
        aa[t], bb[t] = a, b
    return d, aa, bb


class RRLTrader:
    """Moody-Saffell recurrent reinforcement learner on one asset's returns."""

    def __init__(
        self,
        m: int = 8,
        mu: float = 1.0,
        delta: float = 0.001,
        seed=None,
        scale: float = 0.1,
        input_scale: float = 1.0,
    ):
        if m < 1 or input_scale <= 0:
            raise ConfigurationError("m must be >= 1 and input_scale > 0")
        self.m, self.mu, self.delta, self.input_scale = m, mu, delta, input_scale
        self.w = np.random.default_rng(seed).normal(0.0, scale, m + 2)

    def _x(self, r: np.ndarray, t: int, f_prev: float) -> np.ndarray:
        """[1, r_{t-m+1..t} / input_scale, F_{t-1}] -- returns as inputs are
        divided by input_scale (e.g. their training std; the papers feed
        normalised inputs), but R_t uses the raw returns."""
        return np.r_[1.0, r[t - self.m + 1 : t + 1] / self.input_scale, f_prev]

    def positions(self, returns, w=None) -> np.ndarray:
        """F_t in (-1, 1), decided at the close of t from returns through t
        (so it earns r_{t+1}); 0 before the first full window."""
        r, w = np.asarray(returns, dtype=float), self.w if w is None else w
        f = np.zeros(len(r))
        for t in range(self.m - 1, len(r)):
            f[t] = np.tanh(w @ self._x(r, t, f[t - 1] if t > 0 else 0.0))
        return f

    def trading_returns(self, returns, f) -> np.ndarray:
        """R_t = mu (F_{t-1} r_t - delta |F_t - F_{t-1}|) from the first
        decision on (the opening trade pays its cost)."""
        r = np.asarray(returns, dtype=float)
        prev = np.r_[0.0, f[:-1]]
        return (self.mu * (prev * r - self.delta * np.abs(f - prev)))[self.m - 1 :]

    def sharpe_and_gradient(self, returns, w=None) -> tuple[float, np.ndarray]:
        """Batch Sharpe S = A / sqrt(B - A^2) of the trading returns and its
        exact gradient through the recurrence
        dF_t/dw = (1 - F_t^2)(x_t + w_F dF_{t-1}/dw)."""
        r, w = np.asarray(returns, dtype=float), self.w if w is None else w
        t0 = self.m - 1
        n = len(r) - t0
        f_prev, df_prev = 0.0, np.zeros_like(w)
        rs, drs = np.zeros(n), np.zeros((n, len(w)))
        for k, t in enumerate(range(t0, len(r))):
            x = self._x(r, t, f_prev)
            f = np.tanh(w @ x)
            df = (1 - f * f) * (x + w[-1] * df_prev)
            s = np.sign(f - f_prev)
            rs[k] = self.mu * (f_prev * r[t] - self.delta * abs(f - f_prev))
            drs[k] = self.mu * (r[t] * df_prev - self.delta * s * (df - df_prev))
            f_prev, df_prev = f, df
        a, b = rs.mean(), (rs * rs).mean()
        var = b - a * a
        if var <= 0:
            return 0.0, np.zeros_like(w)
        ds_dr = (b - a * rs) / (var**1.5 * n)
        return float(a / np.sqrt(var)), ds_dr @ drs

    def fit(self, returns, epochs: int = 200, lr: float = 0.1) -> list[float]:
        """Batch training: gradient ascent on the in-sample Sharpe ratio."""
        history = []
        for _ in range(epochs):
            s, g = self.sharpe_and_gradient(returns)
            self.w = self.w + lr * g
            history.append(s)
        return history

    def fit_online(self, returns, rho: float = 0.01, eta: float = 0.01, warmup: int = 20) -> dict:
        """Online training on the differential Sharpe ratio: at each step
        w += rho dD_t/dR_t dR_t/dw, with dD_t/dR_t = (B_{t-1} - A_{t-1} R_t)
        / (B_{t-1} - A_{t-1}^2)^{3/2} and dF_{t-1}/dw carried from the
        previous step (the paper's online approximation). A and B are
        seeded from the first `warmup` decisions' returns at the initial
        weights."""
        r = np.asarray(returns, dtype=float)
        seed_r = self.trading_returns(
            r[: self.m - 1 + warmup], self.positions(r[: self.m - 1 + warmup])
        )
        a, b = float(seed_r.mean()), float((seed_r**2).mean())
        f_prev, df_prev = 0.0, np.zeros_like(self.w)
        fs, rs, ds = [], [], []
        for t in range(self.m - 1, len(r)):
            x = self._x(r, t, f_prev)
            f = np.tanh(self.w @ x)
            df = (1 - f * f) * (x + self.w[-1] * df_prev)
            s = np.sign(f - f_prev)
            big_r = self.mu * (f_prev * r[t] - self.delta * abs(f - f_prev))
            drdw = self.mu * (r[t] * df_prev - self.delta * s * (df - df_prev))
            var = b - a * a
            if var > 0:
                ds.append((b * (big_r - a) - 0.5 * a * (big_r * big_r - b)) / var**1.5)
                self.w = self.w + rho * (b - a * big_r) / var**1.5 * drdw
            else:
                ds.append(0.0)
            a, b = a + eta * (big_r - a), b + eta * (big_r * big_r - b)
            fs.append(f)
            rs.append(big_r)
            f_prev, df_prev = f, df
        return {"positions": np.array(fs), "returns": np.array(rs), "dsr": np.array(ds)}


# ---------------------------------------------------------------- C-RL4 DRQN with action augmentation

ACTIONS = np.array([-1.0, 0.0, 1.0])  # short, neutral, long


class ElmanQNetwork:
    """h_t = tanh(x_t Wx + h_{t-1} Wh + bh); Q(h_t, position) =
    [h_t, onehot(position)] Wo + bo over the three actions."""

    def __init__(self, n_features: int, hidden: int, rng: np.random.Generator) -> None:
        def init(a, b):
            return rng.normal(0.0, 1.0 / np.sqrt(a), (a, b))

        self.hidden = hidden
        self.params = {
            "wx": init(n_features, hidden),
            "wh": init(hidden, hidden) * 0.5,
            "bh": np.zeros(hidden),
            "wo": init(hidden + 3, 3),
            "bo": np.zeros(3),
        }

    def hidden_states(self, xs) -> np.ndarray:
        p = self.params
        hs = np.zeros((len(xs), self.hidden))
        h = np.zeros(self.hidden)
        for t, x in enumerate(np.asarray(xs, dtype=float)):
            h = np.tanh(x @ p["wx"] + h @ p["wh"] + p["bh"])
            hs[t] = h
        return hs

    def q(self, h, pos_index) -> np.ndarray:
        """Q-values for hidden state(s) h and position index(es) (0, 1, 2)."""
        h = np.atleast_2d(h)
        idx = np.atleast_1d(pos_index)
        oh = np.eye(3)[np.broadcast_to(idx, (len(h),)) if idx.size == 1 else idx]
        return np.hstack([h, oh]) @ self.params["wo"] + self.params["bo"]

    def loss_and_grads(self, xs, pos_idx, targets, mask) -> tuple[float, dict]:
        """L = 1/2 sum_t mask_t sum_a (Q_t[a] - y_t[a])^2 and its BPTT
        gradients."""
        p = self.params
        xs = np.asarray(xs, dtype=float)
        hs = self.hidden_states(xs)
        qs = self.q(hs, pos_idx)
        dq = (qs - targets) * mask[:, None]
        loss = 0.5 * float((dq * (qs - targets)).sum())
        oh = np.eye(3)[pos_idx]
        g = {k: np.zeros_like(v) for k, v in p.items()}
        g["wo"] = np.hstack([hs, oh]).T @ dq
        g["bo"] = dq.sum(0)
        dh_next = np.zeros(self.hidden)
        for t in range(len(xs) - 1, -1, -1):
            dh = dq[t] @ p["wo"][: self.hidden].T + dh_next
            dpre = dh * (1 - hs[t] ** 2)
            h_prev = hs[t - 1] if t > 0 else np.zeros(self.hidden)
            g["wx"] += np.outer(xs[t], dpre)
            g["wh"] += np.outer(h_prev, dpre)
            g["bh"] += dpre
            dh_next = dpre @ p["wh"].T
        return loss, g


def augmented_rewards(prices, positions, lot: float = 1.0, cost: float = 0.0) -> np.ndarray:
    """Reward of every action at every step: r_t(a) = a (p_{t+1} - p_t) lot
    - cost |a - pos_t|, for t = 0..T-2. positions are the actual position
    values held entering each step (-1, 0, 1)."""
    p = np.asarray(prices, dtype=float)
    pos = np.asarray(positions, dtype=float)
    move = np.diff(p)[:, None]
    return ACTIONS[None, :] * move * lot - cost * np.abs(ACTIONS[None, :] - pos[:-1, None])


class ActionAugmentedDRQN:
    """Huang's trader: epsilon-greedy over {short, neutral, long}, trained
    on whole sequences with every action's target
    y_t(a) = r_t(a) + gamma max_a' Q_target(h_{t+1}, position=a)[a']."""

    def __init__(
        self,
        n_features: int,
        hidden: int = 16,
        gamma: float = 0.99,
        tau: float = 0.001,
        lr: float = 1e-3,
        lot: float = 1.0,
        cost: float = 0.0,
        epsilon: float = 0.1,
        seed=None,
    ) -> None:
        self.rng = np.random.default_rng(seed)
        self.net = ElmanQNetwork(n_features, hidden, self.rng)
        self.target = ElmanQNetwork(n_features, hidden, self.rng)
        self.target.params = {k: v.copy() for k, v in self.net.params.items()}
        self.gamma, self.tau, self.lot, self.cost, self.epsilon = gamma, tau, lot, cost, epsilon
        self.opt = Adam(lr)

    def rollout_positions(self, features, greedy: bool = False) -> np.ndarray:
        """Positions (values) entering each step under the current policy,
        starting flat."""
        hs = self.net.hidden_states(features)
        pos = np.zeros(len(hs))
        cur = 1  # index of neutral
        for t in range(len(hs)):
            pos[t] = ACTIONS[cur]
            if not greedy and self.rng.random() < self.epsilon:
                cur = int(self.rng.integers(3))
            else:
                cur = int(np.argmax(self.net.q(hs[t], cur)[0]))
        return pos

    def targets(self, features, prices, positions) -> np.ndarray:
        rewards = augmented_rewards(prices, positions, self.lot, self.cost)
        h_next = self.target.hidden_states(features)[1:]
        nxt = np.stack([self.target.q(h_next, a).max(axis=1) for a in range(3)], axis=1)
        return rewards + self.gamma * nxt

    def train_sequence(self, features, prices, positions) -> float:
        feats = np.asarray(features, dtype=float)
        y = np.vstack([self.targets(feats, prices, positions), np.zeros((1, 3))])
        mask = np.r_[np.ones(len(feats) - 1), 0.0]
        pos_idx = (np.asarray(positions) + 1).astype(int)
        loss, grads = self.net.loss_and_grads(feats, pos_idx, y, mask)
        self.opt.step(self.net.params, grads)
        soft_update(self.target.params, self.net.params, self.tau)
        return loss


# ---------------------------------------------------------------- RL3 EIIE


def price_relatives(close) -> np.ndarray:
    """y_t = [1 (cash), close_t / close_{t-1}]; y_0 = ones."""
    c = np.asarray(close, dtype=float)
    y = np.ones((len(c), c.shape[1] + 1))
    y[1:, 1:] = c[1:] / c[:-1]
    return y


def drift_weights(w, y) -> np.ndarray:
    """Weights at the end of a period: w' = (y * w) / (y . w)."""
    w, y = np.asarray(w, dtype=float), np.asarray(y, dtype=float)
    return y * w / (y @ w)


def transaction_remainder(
    w_prime, w, c_s: float = 0.0025, c_p: float = 0.0025, tol: float = 1e-13, max_iter: int = 1000
) -> float:
    """Jiang et al. Eq. 14, iterated to its fixed point from the first-order
    guess: mu = [1 - c_p w'_0 - (c_s + c_p - c_s c_p) sum_{i>=1}
    (w'_i - mu w_i)^+] / (1 - c_p w_0). Index 0 is cash."""
    wp, w = np.asarray(w_prime, dtype=float), np.asarray(w, dtype=float)
    c = (c_s + c_p) / 2
    mu = 1 - c * np.abs(wp[1:] - w[1:]).sum()
    for _ in range(max_iter):
        new = (
            1 - c_p * wp[0] - (c_s + c_p - c_s * c_p) * np.clip(wp[1:] - mu * w[1:], 0, None).sum()
        ) / (1 - c_p * w[0])
        if abs(new - mu) < tol:
            return float(new)
        mu = new
    return float(mu)


class EIIEPolicy:
    """Linear EIIE: score_i = theta . (close window_i / close_t,i)
    + beta * w_prev_i for each asset, cash scores cash_bias, w = softmax."""

    def __init__(self, n_assets: int, window: int = 50, commission: float = 0.0025, seed=None):
        rng = np.random.default_rng(seed)
        self.n, self.window, self.c = n_assets, window, commission
        self.theta = rng.normal(0.0, 0.1, window)
        self.beta, self.cash_bias = 0.0, 0.0

    def features(self, close, t: int) -> np.ndarray:
        c = np.asarray(close, dtype=float)
        win = c[t - self.window + 1 : t + 1]
        return (win / win[-1]).T  # n x window

    def weights(self, close, t: int, w_prev) -> np.ndarray:
        z = np.r_[self.cash_bias, self.features(close, t) @ self.theta + self.beta * w_prev[1:]]
        e = np.exp(z - z.max())
        return e / e.sum()

    def _period(self, close, y, t, pvm, grad: bool):
        w_prev = pvm[t - 1]
        w = self.weights(close, t, w_prev)
        wp = drift_weights(w_prev, y[t])
        mu = 1 - self.c * np.abs(wp[1:] - w[1:]).sum()
        gain = y[t + 1] @ w
        r = np.log(mu) + np.log(gain)
        if not grad:
            return w, r, None
        g_w = y[t + 1] / gain
        g_w[1:] += self.c * np.sign(wp[1:] - w[1:]) / mu
        g_z = w * (g_w - w @ g_w)
        v = self.features(close, t)
        return w, r, (g_z[1:] @ v, g_z[1:] @ w_prev[1:], g_z[0])

    def batch_objective(self, close, y, ts, pvm, grad: bool = True):
        """Mean first-order log return over decision times ts (previous
        weights read from, new weights written to, the PVM) and its
        gradient in (theta, beta, cash_bias)."""
        total, gt, gb, gc = 0.0, np.zeros_like(self.theta), 0.0, 0.0
        for t in ts:
            w, r, g = self._period(close, y, t, pvm, grad)
            pvm[t] = w
            total += r
            if grad:
                gt, gb, gc = gt + g[0], gb + g[1], gc + g[2]
        k = len(ts)
        return total / k, (gt / k, gb / k, gc / k)

    def train(
        self,
        close,
        steps: int = 200,
        batch: int = 50,
        lr: float = 0.05,
        geometric: float = 5e-3,
        seed=None,
    ) -> list[float]:
        """Online stochastic batch learning: batch start t_b drawn with
        probability proportional to geometric (1 - geometric)^(t_last - t_b),
        so recent stretches are favoured; gradient ascent on each batch."""
        close = np.asarray(close, dtype=float)
        y = price_relatives(close)
        first, last = self.window - 1, len(close) - batch - 1
        if last < first:
            raise ConfigurationError("series too short for the window and batch")
        rng = np.random.default_rng(seed)
        pvm = np.tile(np.r_[1.0, np.zeros(self.n)], (len(close), 1))
        starts = np.arange(first, last + 1)
        p = geometric * (1 - geometric) ** (last - starts)
        p /= p.sum()
        history = []
        for _ in range(steps):
            tb = int(rng.choice(starts, p=p))
            obj, (gt, gb, gc) = self.batch_objective(close, y, range(tb, tb + batch), pvm)
            self.theta += lr * gt
            self.beta += lr * gb
            self.cash_bias += lr * gc
            history.append(obj)
        return history

    def backtest(self, close) -> np.ndarray:
        """Walk forward with exact transaction remainders; returns the
        portfolio value path (start 1.0)."""
        close = np.asarray(close, dtype=float)
        y = price_relatives(close)
        w_prev = np.r_[1.0, np.zeros(self.n)]
        value = [1.0]
        for t in range(self.window - 1, len(close) - 1):
            wp = drift_weights(w_prev, y[t]) if t > self.window - 1 else w_prev
            w = self.weights(close, t, w_prev)
            mu = transaction_remainder(wp, w, self.c, self.c)
            value.append(value[-1] * mu * (y[t + 1] @ w))
            w_prev = w
        return np.array(value)
