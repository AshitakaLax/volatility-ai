"""
Market-making entries of the ranked list (ledger RK307, RK313, RK335,
RK339, RK341, RK344, RK345, RK354, RK359, RK361). Market making quotes a
sell as well as a buy and carries short inventory, which the owner's rules
exclude; this is research code on a simulator, not a strategy for the book.

The simulator is Avellaneda & Stoikov's: the mid follows Brownian motion
and a quote at distance delta from it fills with intensity A exp(-k delta).

Sources:

  * Avellaneda & Stoikov, "High-frequency trading in a limit order book",
    Quantitative Finance 8, 2008 (reservation price s - q gamma sigma^2 (T - t),
    total spread gamma sigma^2 (T - t) + (2 / gamma) log(1 + gamma / k)).
  * RL market making on a discretised action grid -- Spooner, Fearnley,
    Savani & Koukorinis, AAMAS 2018; an adaptively refined grid is this
    module's reading of RK313's "adaptive mesh".
  * Multi-agent dealers learning to skew against inventory and model a
    competitor -- Ganesh et al., "Reinforcement learning for market making in
    a multi-agent dealer market", arXiv:1911.05892, 2019.
  * Nash equilibrium by fictitious play -- Brown, 1951; replicator dynamics
    and evolutionarily stable strategies -- Taylor & Jonker, Math. Biosci.
    40, 1978; Stackelberg leader-follower -- von Stackelberg, 1934.
  * Robust market making (worst case over fill models) -- in the spirit of
    Cartea, Donnelly & Jaimungal, "Algorithmic trading with model
    uncertainty", SIAM J. Financial Math. 8, 2017; here the worst of a
    sampled set of (A, k) inside a ball.
  * Cross-exchange market making -- Hummingbot's XEMM strategy documentation.
"""

from __future__ import annotations

import numpy as np

from engine.core.exceptions import ConfigurationError
from research.catalog.deep_rl import DQN, genetic_search

# ---------------------------------------------------------------- Avellaneda-Stoikov


def as_quotes(
    mid: float, inventory: float, t: float, horizon: float, sigma: float, gamma: float, k: float
) -> tuple[float, float]:
    """(bid, ask) around the reservation price."""
    tau = max(horizon - t, 0.0)
    r = mid - inventory * gamma * sigma**2 * tau
    half = 0.5 * (gamma * sigma**2 * tau + 2 / gamma * np.log1p(gamma / k))
    return r - half, r + half


def fill_probability(delta, a: float, k: float, dt: float):
    return np.clip(a * np.exp(-k * np.asarray(delta, float)) * dt, 0.0, 1.0)


def simulate_market_maker(
    policy,
    steps: int = 200,
    dt: float = 0.005,
    sigma: float = 2.0,
    a: float = 140.0,
    k: float = 1.5,
    mid0: float = 100.0,
    max_inventory: int = 50,
    rng=None,
) -> dict:
    """Run policy(t, mid, inventory) -> (bid_delta, ask_delta) on the AS
    simulator. Returns terminal P&L (cash + inventory at mid), the inventory
    path and the number of fills."""
    rng = np.random.default_rng(rng)
    mid, cash, q, path, fills = mid0, 0.0, 0, [], 0
    for i in range(steps):
        db, da = policy(i * dt, mid, q)
        if q < max_inventory and rng.random() < fill_probability(db, a, k, dt):
            q, cash, fills = q + 1, cash - (mid - db), fills + 1
        if q > -max_inventory and rng.random() < fill_probability(da, a, k, dt):
            q, cash, fills = q - 1, cash + (mid + da), fills + 1
        mid += sigma * np.sqrt(dt) * rng.normal()
        path.append(q)
    return {"pnl": cash + q * mid, "inventory": np.array(path), "fills": fills}


def as_policy(gamma: float = 0.1, k: float = 1.5, sigma: float = 2.0, horizon: float = 1.0):
    def policy(t, mid, q):
        bid, ask = as_quotes(mid, q, t, horizon, sigma, gamma, k)
        return mid - bid, ask - mid

    return policy


# ---------------------------------------------------------------- RL market makers (RK313, RK335)


def _action_grid(center, spacing, size: int = 5):
    offs = (np.arange(size) - size // 2) * spacing
    return [(max(center[0] + i, 0.01), max(center[1] + j, 0.01)) for i in offs for j in offs]


def train_rl_market_maker(
    episodes: int = 300,
    refinements: int = 2,
    max_inventory: int = 10,
    inventory_penalty: float = 0.01,
    models=None,
    robust: bool = False,
    sim: dict | None = None,
    rng=None,
) -> dict:
    """RK313: tabular Q-learning over inventory states with (bid, ask) offset
    actions on a 5x5 grid; after each phase the grid is re-centred on the
    greedy action of the flat-inventory state and its spacing halved (the
    adaptive mesh). Reward: one-step P&L minus inventory_penalty q^2.

    RK335 (robust=True): `models` is a list of (A, k) fill models inside the
    ambiguity ball; each episode is played under the one on which the current
    greedy policy earns least (the empirical worst case)."""
    rng = np.random.default_rng(rng)
    sim = {"steps": 100, "dt": 0.005, "sigma": 2.0, "a": 140.0, "k": 1.5} | (sim or {})
    models = models or [(sim["a"], sim["k"])]
    states = 2 * max_inventory + 1
    center, spacing = (0.7, 0.7), 0.25
    per_phase = episodes // (refinements + 1)
    hist = []
    for _ in range(refinements + 1):
        actions = _action_grid(center, spacing)
        q_tab = np.zeros((states, len(actions)))

        def greedy(t, mid, inv, q_tab=q_tab, actions=actions):
            return actions[
                int(
                    np.argmax(
                        q_tab[int(np.clip(inv, -max_inventory, max_inventory)) + max_inventory]
                    )
                )
            ]

        for _ in range(per_phase):
            a_fill, k_fill = models[0]
            if robust and len(models) > 1:
                scores = [
                    simulate_market_maker(greedy, 50, sim["dt"], sim["sigma"], ma, mk, rng=rng)[
                        "pnl"
                    ]
                    for ma, mk in models
                ]
                a_fill, k_fill = models[int(np.argmin(scores))]
            mid, cash, inv, total = 100.0, 0.0, 0, 0.0
            for _ in range(sim["steps"]):
                s = inv + max_inventory
                act = (
                    int(rng.integers(len(actions)))
                    if rng.random() < 0.2
                    else int(np.argmax(q_tab[s]))
                )
                db, da = actions[act]
                value0 = cash + inv * mid
                if inv < max_inventory and rng.random() < fill_probability(
                    db, a_fill, k_fill, sim["dt"]
                ):
                    inv, cash = inv + 1, cash - (mid - db)
                if inv > -max_inventory and rng.random() < fill_probability(
                    da, a_fill, k_fill, sim["dt"]
                ):
                    inv, cash = inv - 1, cash + (mid + da)
                mid += sim["sigma"] * np.sqrt(sim["dt"]) * rng.normal()
                reward = cash + inv * mid - value0 - inventory_penalty * inv**2
                s2 = inv + max_inventory
                q_tab[s, act] += 0.1 * (reward + 0.99 * q_tab[s2].max() - q_tab[s, act])
                total += reward
            hist.append(total)
        center = actions[int(np.argmax(q_tab[max_inventory]))]
        spacing /= 2
    return {
        "q": q_tab,
        "actions": actions,
        "policy": greedy,
        "history": hist,
        "max_inventory": max_inventory,
    }


# ---------------------------------------------------------------- games between quoters


def duopoly_payoffs(grid, a: float = 140.0, k: float = 1.5, cost: float = 0.0) -> np.ndarray:
    """Expected spread revenue per unit time for two makers quoting symmetric
    half-spreads from `grid`: order flow arrives at A exp(-k min(d1, d2)) per
    side and goes to the tighter quote (split on ties). payoff[i, j] is maker
    1's revenue when it quotes grid[i] and maker 2 quotes grid[j]."""
    g = np.asarray(grid, float)
    out = np.zeros((len(g), len(g)))
    for i, d1 in enumerate(g):
        for j, d2 in enumerate(g):
            flow = 2 * a * np.exp(-k * min(d1, d2))
            share = 1.0 if d1 < d2 else 0.5 if d1 == d2 else 0.0
            out[i, j] = flow * share * (d1 - cost)
    return out


def fictitious_play(payoff_1, payoff_2=None, iters: int = 2000) -> tuple[np.ndarray, np.ndarray]:
    """RK339: each player best-responds to the other's empirical mixture; the
    mixtures converge to a Nash equilibrium in two-player zero-sum and in
    potential games (symmetric duopoly: payoff_2 = payoff_1.T)."""
    p1 = np.asarray(payoff_1, float)
    p2 = p1.T if payoff_2 is None else np.asarray(payoff_2, float)
    c1, c2 = np.zeros(len(p1)), np.zeros(p1.shape[1])
    c1[0] = c2[0] = 1
    for _ in range(iters):
        c1[np.argmax(p1 @ (c2 / c2.sum()))] += 1
        c2[np.argmax((c1 / c1.sum()) @ p2)] += 1
    return c1 / c1.sum(), c2 / c2.sum()


def nash_spread(grid, **kw) -> float:
    """The half-spread the duopoly's fictitious play settles on (most played)."""
    m1, _ = fictitious_play(duopoly_payoffs(grid, **kw))
    return float(np.asarray(grid)[np.argmax(m1)])


def stackelberg_spread(grid, follower_response, leader_profit) -> dict:
    """RK341/RK344/RK345: the leader quotes first, the follower best-responds
    (follower_response(leader_action) -> follower_action), and the leader
    picks the action maximising leader_profit(leader, follower) along that
    response curve. Returns the equilibrium pair and the leader's profit."""
    best = max(grid, key=lambda d: leader_profit(d, follower_response(d)))
    resp = follower_response(best)
    return {"leader": best, "follower": resp, "profit": leader_profit(best, resp)}


def trader_demand_response(a: float = 140.0, k: float = 1.5):
    """Followers = liquidity takers: their best response to a half-spread d is
    the arrival rate A exp(-k d) (the demand curve); the leader's profit is
    2 d * rate - inventory cost."""
    return lambda d: a * np.exp(-k * d)


def undercutting_follower(grid, cost: float = 0.0, a: float = 140.0, k: float = 1.5):
    """A follower maker that best-responds to the leader's half-spread on the
    duopoly payoffs (usually by undercutting one tick)."""
    g = np.asarray(grid, float)
    pay = duopoly_payoffs(g, a, k, cost)

    def respond(d):
        j = int(np.argmin(np.abs(g - d)))
        return float(g[np.argmax(pay[:, j])])

    return respond


def replicator_dynamics(payoff, x0=None, steps: int = 5000, dt: float = 0.01) -> np.ndarray:
    """RK359: population shares x of quoting strategies evolve as
    dx_i = x_i (f_i - f_bar) dt with fitness f = payoff @ x; a stable rest
    point is an evolutionarily stable quoting mix."""
    a = np.asarray(payoff, float)
    x = np.full(len(a), 1.0 / len(a)) if x0 is None else np.asarray(x0, float)
    for _ in range(steps):
        f = a @ x
        x = np.clip(x + dt * x * (f - x @ f), 0, None)
        x /= x.sum()
    return x


def evolve_market_maker(
    generations: int = 15, pop: int = 16, risk: float = 0.01, episodes: int = 5, rng=None
) -> dict:
    """RK354: evolve (log gamma, spread multiplier, skew multiplier) of an
    Avellaneda-Stoikov quoter for mean P&L minus risk x P&L variance over
    simulated sessions."""
    rng = np.random.default_rng(rng)
    seeds = rng.integers(0, 2**31, size=episodes)

    def quoter(x):
        gamma, mult, skew = np.exp(x[0]), np.exp(x[1]), x[2]

        def policy(t, mid, q):
            db, da = as_policy(gamma)(t, mid, 0)
            shift = skew * q * 0.05
            return max(mult * db + shift, 0.01), max(mult * da - shift, 0.01)

        return policy

    def fitness(x):
        pnl = [simulate_market_maker(quoter(x), 100, rng=int(s))["pnl"] for s in seeds]
        return float(np.mean(pnl) - risk * np.var(pnl))

    out = genetic_search(fitness, 3, pop=pop, gens=generations, init_scale=0.5, rng=rng)
    out["policy"] = quoter(out["best"])
    return out


def train_competing_dqn_makers(
    episodes: int = 60,
    steps: int = 100,
    grid=(0.3, 0.6, 0.9, 1.2),
    a: float = 140.0,
    k: float = 1.5,
    dt: float = 0.005,
    seed: int = 0,
) -> dict:
    """RK361: two DQN market makers learn simultaneously; state = (own
    inventory, rival's last half-spread), action = half-spread from `grid`,
    and each side's order flow goes to the tighter quote."""
    rng = np.random.default_rng(seed)
    makers = [DQN(2, len(grid), hidden=16, gamma=0.9, seed=seed + i) for i in range(2)]
    g = np.asarray(grid, float)
    last = [1, 1]
    for _ in range(episodes):
        inv, cash, mid = [0, 0], [0.0, 0.0], 100.0
        for _ in range(steps):
            states = [np.array([inv[i] / 10, g[last[1 - i]]]) for i in range(2)]
            acts = [m.act(s, epsilon=0.2) for m, s in zip(makers, states, strict=True)]
            d = g[acts]
            values0 = [cash[i] + inv[i] * mid for i in range(2)]
            for side in (+1, -1):  # +1: a seller hits the bid; -1: a buyer lifts the ask
                if rng.random() < fill_probability(d.min(), a, k, dt):
                    i = int(np.argmin(d)) if d[0] != d[1] else int(rng.integers(2))
                    inv[i] += side
                    cash[i] -= side * (mid - side * d[i])
            mid += 2.0 * np.sqrt(dt) * rng.normal()
            for i in range(2):
                reward = cash[i] + inv[i] * mid - values0[i] - 0.01 * inv[i] ** 2
                s2 = np.array([inv[i] / 10, g[acts[1 - i]]])
                makers[i].buffer.add(states[i], acts[i], reward, s2, 0.0)
                makers[i].update(32)
            last = acts
    return {"makers": makers, "grid": g}


# ---------------------------------------------------------------- cross-exchange (RK307)


def xemm_quotes(
    liquid_bid: float,
    liquid_ask: float,
    min_profit: float = 0.002,
    maker_fee: float = 0.001,
    taker_fee: float = 0.001,
) -> tuple[float, float]:
    """Quotes on the illiquid venue that lock in at least `min_profit` after
    fees if hedged at the liquid venue's touch."""
    if liquid_bid >= liquid_ask:
        raise ConfigurationError("crossed liquid book")
    edge = min_profit + maker_fee + taker_fee
    return liquid_bid * (1 - edge), liquid_ask * (1 + edge)


def xemm_fill_pnl(
    side: str,
    quote: float,
    hedge_price: float,
    size: float = 1.0,
    maker_fee: float = 0.001,
    taker_fee: float = 0.001,
) -> float:
    """P&L of a maker fill hedged immediately: bought at `quote` (side 'bid')
    and sold at hedge_price on the liquid venue, or the reverse."""
    if side == "bid":
        return size * (hedge_price * (1 - taker_fee) - quote * (1 + maker_fee))
    return size * (quote * (1 - maker_fee) - hedge_price * (1 + taker_fee))
