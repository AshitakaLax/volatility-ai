"""
A long-only multi-asset book on daily closes: rebalance to an allocator's
target weights, and never sell below cost except as a declared signal exit.

    result = run_portfolio(closes, allocators.inverse_volatility, rebalance="monthly")

The loop, for each session d after `min_history`:

  1. On a rebalance session, the allocator sees closes through d-1 only
     (`closes.iloc[:i]`) and returns target weights.
  2. The book trades to those weights at d's close: sells first, then buys
     with the cash available (no margin, no shorts, whole-share fractions
     allowed as in the engine's backtests).
  3. Every sale goes through engine/trading/no_loss_guard.validate_sell
     -- the one place a sale is checked against cost basis. With
     no_loss=True (the default, the owner's rule) a sale that would
     realise a loss is skipped and counted, and the position is held
     overweight until its price recovers; with no_loss=False the sale is
     a SIGNAL_EXIT and the loss is realised and recorded, the regime-exit
     route that is the only way a loss is allowed live.
  4. Idle cash earns `cash_yield` (annual), accrued daily.

Each instrument's cost basis is its average buy price per share with buy
costs folded in, as the engine's lots carry it. This is a backtest
harness: the engine trades one symbol per deployment, so nothing here can
trade live until a multi-asset deployment exists (engine/roadmap.md).
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from types import SimpleNamespace

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from engine.execution.cost_models import SlippageCommissionModel, TransactionCostModel
from engine.trading.no_loss_guard import NoLossViolation, SellReason, validate_sell


@dataclass
class PortfolioResult:
    equity: pd.Series
    weights: pd.DataFrame
    trades: pd.DataFrame
    metrics: dict = field(default_factory=dict)


def _rebalance_days(index: pd.DatetimeIndex, rebalance) -> set:
    """The first session of each month or week, or every Nth session."""
    naive = index.tz_localize(None) if index.tz is not None else index
    if rebalance == "monthly":
        months = naive.to_period("M")
        first = ~pd.Series(months, index=index).duplicated()
        return set(index[first.to_numpy()])
    if rebalance == "weekly":
        weeks = naive.to_period("W")
        first = ~pd.Series(weeks, index=index).duplicated()
        return set(index[first.to_numpy()])
    if isinstance(rebalance, int) and rebalance >= 1:
        return set(index[::rebalance])
    raise ConfigurationError(
        f"rebalance must be 'monthly', 'weekly' or an int >= 1, got {rebalance!r}"
    )


def metrics_of(equity: pd.Series, periods_per_year: int = 252) -> dict:
    eq = equity.dropna()
    if len(eq) < 2 or eq.iloc[0] <= 0:
        return {}
    years = len(eq) / periods_per_year
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1 if years > 0 else 0.0
    dd = float((eq / eq.cummax() - 1).min())
    rets = eq.pct_change().dropna()
    sd = float(rets.std())
    sharpe = float(rets.mean()) / sd * np.sqrt(periods_per_year) if sd > 0 else 0.0
    return {
        "Total Return %": (eq.iloc[-1] / eq.iloc[0] - 1) * 100,
        "CAGR %": cagr * 100,
        "Max Drawdown %": dd * 100,
        "Calmar": cagr / -dd if dd < 0 else float("inf"),
        "Sharpe": sharpe,
    }


def run_portfolio(
    closes: pd.DataFrame,
    allocator,
    *,
    rebalance="monthly",
    min_history: int = 253,
    initial_cash: float = 100_000.0,
    cost_model: TransactionCostModel | None = None,
    cash_yield: float = 0.0,
    no_loss: bool = True,
    min_trade: float = 1.0,
    allocator_kwargs: dict | None = None,
) -> PortfolioResult:
    """Run `allocator` over `closes` (daily, oldest first). See module docstring."""
    if closes.isna().any().any():
        raise ConfigurationError("closes must be aligned with no gaps (drop or fill first)")
    if (closes <= 0).any().any():
        raise ConfigurationError("closes must be positive")
    if len(closes) <= min_history:
        raise ConfigurationError(f"need more than min_history={min_history} sessions")
    model = cost_model or SlippageCommissionModel()
    kwargs = dict(allocator_kwargs or {})
    try:
        wants_current = "current" in inspect.signature(allocator).parameters
    except (TypeError, ValueError):
        wants_current = False
    names = list(closes.columns)
    shares = dict.fromkeys(names, 0.0)
    basis = dict.fromkeys(names, 0.0)  # per-share cost basis, buy costs folded in
    cash = float(initial_cash)
    daily_yield = (1.0 + cash_yield) ** (1 / 252) - 1.0
    rebal = _rebalance_days(closes.index[min_history:], rebalance)
    equity, weights_log, trades = {}, {}, []
    blocked = losses = 0
    realized = 0.0
    for i in range(min_history, len(closes)):
        day = closes.index[i]
        px = closes.iloc[i]
        cash *= 1.0 + daily_yield
        if day in rebal:
            if wants_current:  # a turnover rule (top-K dropout) needs today's book
                held = {n: shares[n] * px[n] for n in names}
                value_now = cash + sum(held.values())
                kwargs["current"] = pd.Series({n: held[n] / value_now for n in names})
            target = allocator(closes.iloc[:i], **kwargs)
            target = target.reindex(names).fillna(0.0).clip(lower=0.0)
            if target.sum() > 1.0 + 1e-9:
                raise ConfigurationError(f"allocator returned weights summing to {target.sum()}")
            value = cash + sum(shares[n] * px[n] for n in names)
            desired = {n: target[n] * value / px[n] for n in names}
            for n in names:  # sells first
                qty = shares[n] - desired[n]
                if qty * px[n] < min_trade or qty <= 0:
                    continue
                lot = SimpleNamespace(buy_price=basis[n], order_id=f"{n}@{day.date()}")
                reason = SellReason.PROFIT_TARGET if no_loss else SellReason.SIGNAL_EXIT
                try:
                    econ = validate_sell(lot, qty, float(px[n]), model, reason=reason)
                except NoLossViolation:
                    blocked += 1
                    continue
                cash += econ.net_sell_proceeds
                realized += econ.realized_pnl
                losses += econ.realized_pnl < 0
                shares[n] -= qty
                trades.append((day, n, -qty, float(px[n]), econ.realized_pnl))
            for n in names:  # then buys, with the cash there is
                qty = desired[n] - shares[n]
                if qty * px[n] < min_trade or qty <= 0:
                    continue
                fill, fee = model.apply_buy(float(px[n]), qty)
                cost = qty * fill + fee
                if cost > cash:
                    qty = max(0.0, (cash - fee) / fill)
                    cost = qty * fill + fee
                    if qty * px[n] < min_trade:
                        continue
                cash -= cost
                basis[n] = (basis[n] * shares[n] + cost) / (shares[n] + qty)
                shares[n] += qty
                trades.append((day, n, qty, float(px[n]), 0.0))
        held = {n: shares[n] * px[n] for n in names}
        total = cash + sum(held.values())
        equity[day] = total
        weights_log[day] = {n: held[n] / total for n in names}
    eq = pd.Series(equity, name="equity")
    result = PortfolioResult(
        equity=eq,
        weights=pd.DataFrame.from_dict(weights_log, orient="index"),
        trades=pd.DataFrame(trades, columns=["date", "instrument", "shares", "price", "pnl"]),
    )
    result.metrics = {
        **metrics_of(eq),
        "Realized PnL": realized,
        "Trades": len(trades),
        "Sells blocked by the no-loss guard": blocked,
        "Sells realising a loss": int(losses),
    }
    return result


__all__ = ["PortfolioResult", "metrics_of", "run_portfolio"]
