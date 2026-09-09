"""
Performance metrics for a completed simulation run.

Original, from-scratch implementation (no existing
src/performance_analyzer.py was available to read -- see the chat this
was produced in).

Targets optimization_controller.py's current call site:

    metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_portfolio_value, 100000.0)
    metrics["Max Drawdown %"] = state.max_drawdown * 100.0

Only (ledger, final_portfolio_value, initial_cash) are available here --
no equity-curve time series is passed in, so time-series metrics
(Sharpe, Sortino, running peak/drawdown) are not computable in this
function and are not attempted.

"Max Drawdown %" is deliberately NOT included in this function's return
value. optimization_controller.py assigns it directly from its own
per-bar peak-equity tracking immediately after calling this function,
and implementation_task_specs.md Task 1.6 flags a real risk of this
function silently colliding with (and being overwritten by) that
assignment if it computed its own drawdown figure under the same key.
Keeping this function's schema free of that key resolves the collision
by construction.

"Capital Velocity Index" -- confirmed to exist by name only (referenced
in optimization_controller.py's sort_values(by="Capital Velocity
Index", ...)), with no formula specified anywhere in
architecture_overview.md or implementation_task_specs.md. Defined here
as closed_lots / total_lots: the fraction of opened positions that
completed a full buy-to-harvest cycle by the end of the run, i.e. how
much of the capital that was put to work actually cycled back to cash
rather than sitting in still-open lots. This is an original,
reasoned interpretation, not a confirmed pre-existing formula -- flag
this if a different original definition existed.
"""

from __future__ import annotations

import pandas as pd


def annual_returns(equity: pd.Series) -> pd.Series:
    """Calendar-year percentage returns from an equity (or price) series.

    The first year is measured from the series' own start rather than
    from a prior year that does not exist, so a partial first year is
    reported honestly instead of as NaN.

    Written plainly on purpose -- shared between analyze_annual.py and
    optimization_controller.py's per-run metrics precisely because an
    early version of this (before it was shared) reindexed a
    concatenated shifted series and produced badly misaligned results:
    it reported TQQQ down 37% in 2023, a year it roughly tripled. A
    year-over-year return is one shift; anything more elaborate is a
    place for an off-by-one to hide, and two independent copies is two
    places for it to hide differently.
    """
    yearly = equity.resample("YE").last()
    prev = yearly.shift(1)
    prev.iloc[0] = equity.iloc[0]
    return ((yearly / prev) - 1.0) * 100.0


def trade_metrics(blotter: pd.DataFrame) -> dict:
    """Per-trade metrics, from ACTUAL FILLS rather than from targets.

    WHY NOT FROM THE LEDGER. PerformanceAnalyzer.calculate_metrics below
    derives realised PnL as (target_sell_price - buy_price) * shares,
    which is correct only while signal exits are off -- the backtest
    path calls close_lot(lot) with no execution_price, so a closed lot
    does not record what it actually sold for. A target is ALWAYS above
    its own cost basis, so a win rate computed that way would report
    100% by construction, on every run, forever. That is worse than no
    metric at all.

    The blotter's sell rows carry economics.realized_pnl, which is the
    figure the no-loss guard itself computes and the one that can be
    negative on a signal exit. These read that.

    Returns zeros for an empty or unenriched blotter rather than
    raising: a run with no closed trades is a real outcome, and callers
    should not have to branch on it.
    """
    empty = {
        "Profit Factor": 0.0,
        "Win Rate %": 0.0,
        "Max Consecutive Losses": 0,
        "Average Hold Duration": 0.0,
    }
    if blotter is None or blotter.empty or "profit_realized" not in blotter.columns:
        return empty

    sells = blotter[blotter["side"] == "sell"].dropna(subset=["profit_realized"])
    if sells.empty:
        return empty

    pnl = sells["profit_realized"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_loss = float(-losses.sum())

    # A book with no losing trade has an undefined ratio, not an
    # infinite one. inf serialises to JSON as null and sorts
    # unpredictably, so the gross profit is reported instead -- a large
    # finite number that ranks correctly against other runs.
    gross_profit = float(wins.sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit

    streak = worst_streak = 0
    for value in pnl:
        streak = streak + 1 if value < 0 else 0
        worst_streak = max(worst_streak, streak)

    hold = 0.0
    if "lot_id" in blotter.columns and "bar_index" in blotter.columns:
        opened = (
            blotter[blotter["side"] == "buy"]
            .dropna(subset=["lot_id"])
            .groupby("lot_id")["bar_index"]
            .min()
        )
        closed = sells.dropna(subset=["lot_id"]).groupby("lot_id")["bar_index"].max()
        spans = (closed - opened).dropna()
        hold = float(spans.mean()) if not spans.empty else 0.0

    return {
        "Profit Factor": round(profit_factor, 4),
        "Win Rate %": round(float(len(wins)) / len(pnl) * 100.0, 4),
        "Max Consecutive Losses": int(worst_streak),
        "Average Hold Duration": round(hold, 2),
    }


def curve_metrics(equity: pd.Series, periods_per_year: int = 252) -> dict:
    """Risk-adjusted metrics, which need the time series the ledger lacks.

    calculate_metrics' docstring correctly explains that Sharpe and
    Sortino "are not computable in this function" -- it receives only a
    ledger and two scalars. They ARE computable here, because
    SimulationResult.equity_curve exists and is passed in.

    Resampled to DAILY before measuring. On minute bars, the per-bar
    standard deviation annualised by sqrt(98280) is not a Sharpe ratio
    anyone would recognise, and this project's data is minute bars.

    Sortino divides by DOWNSIDE deviation only, which is the whole point
    of it: a strategy whose no-loss guard suppresses losing exits has
    very little downside deviation, and a metric that punished it for
    upside volatility would say the opposite of what is true.
    """
    empty = {"Sharpe": 0.0, "Sortino": 0.0}
    if equity is None or len(equity) < 3:
        return empty
    try:
        daily = equity.resample("1D").last().dropna()
    except (TypeError, ValueError):
        # A non-datetime index cannot be resampled; measure as given
        # rather than failing a whole run over a metric.
        daily = equity.dropna()
    returns = daily.pct_change().dropna()
    if returns.empty or returns.std(ddof=0) == 0:
        return empty

    scale = periods_per_year**0.5
    sharpe = float(returns.mean() / returns.std(ddof=0)) * scale
    downside = returns[returns < 0]
    sortino = (
        float(returns.mean() / downside.std(ddof=0)) * scale
        if not downside.empty and downside.std(ddof=0) > 0
        else 0.0
    )
    return {"Sharpe": round(sharpe, 4), "Sortino": round(sortino, 4)}


class PerformanceAnalyzer:
    """Computes end-of-run summary metrics from a ledger.

    Stateless by design -- a static method rather than an instance, so
    there is no accumulated state to reset between combinations.
    """

    @staticmethod
    def calculate_metrics(
        ledger, final_portfolio_value: float, initial_cash: float, mark_price: float | None = None
    ) -> dict:
        """Summary metrics for one completed run.

        Deliberately does NOT return "Max Drawdown %": the controller
        tracks that per-bar and assigns it itself, and producing it here
        too would create two figures under one key that could silently
        disagree.

        Realized PnL counts only closed lots; open lots contribute to
        Final Equity through mark-to-market instead.

        REALIZED PNL IS TARGET-BASED AND THEREFORE APPROXIMATE ONCE
        SIGNAL EXITS ARE ON. It assumes each closed lot sold at its
        target, which the backtest guarantees only while
        execution.allow_signal_exit is false -- the default, and the
        configuration the pinned regression baseline was measured under.
        A signal exit fills at the market and may realise a loss. It is
        left as-is rather than corrected because changing it would move
        a pinned number; trade_metrics() above reads the blotter's
        actual fills and is the figure to trust per-trade.

        mark_price is the final bar's close, used to value open
        inventory. Optional so the original three-argument call site
        keeps working; Stuck Capital Value is 0.0 without it rather than
        silently wrong.
        """
        closed_lots = ledger.closed_lots
        open_lots = ledger.open_lots
        total_lots = len(closed_lots) + len(open_lots)

        # Assumes each closed lot sold at its target_sell_price, which
        # holds for optimization_controller.py's current flow (it calls
        # execute_sell(..., lot.target_sell_price) and this OMS fills
        # exactly at the requested price -- see order_management_system.py).
        # No buy/sell transaction costs are modeled yet (Phase 2 scope).
        realized_pnl = sum(
            (lot.target_sell_price - lot.buy_price) * lot.shares for lot in closed_lots
        )

        total_return_pct = (
            (final_portfolio_value / initial_cash - 1.0) * 100.0 if initial_cash else 0.0
        )
        capital_velocity_index = (len(closed_lots) / total_lots) if total_lots else 0.0

        # CAPITAL TIED UP IN INVENTORY THAT HAS NOT COME BACK. The grid
        # only sells at a profit, so an open lot is not a paper loss to
        # be ignored -- it is capital the strategy cannot redeploy until
        # the market returns to its target. That is the real cost of the
        # no-loss invariant, and nothing reported it before.
        stuck_capital_value = (
            float(sum(lot.shares * mark_price for lot in open_lots)) if mark_price else 0.0
        )

        # THE UI SPEC'S READING OF "capital velocity": completed harvest
        # cycles per stuck lot. Deliberately NOT merged into
        # "Capital Velocity Index" above, which is closed/TOTAL and is
        # the default rank_by -- every sweep result recorded in
        # README.md is ordered by it, so redefining it would silently
        # restate published rankings. Two names, two definitions, no
        # collision.
        harvest_to_stuck_ratio = (
            len(closed_lots) / len(open_lots) if open_lots else float(len(closed_lots))
        )

        return {
            "Final Equity": final_portfolio_value,
            "Total Return %": total_return_pct,
            "Realized PnL": realized_pnl,
            "Trade Count": total_lots,
            "Closed Trade Count": len(closed_lots),
            "Open Trade Count": len(open_lots),
            "Capital Velocity Index": capital_velocity_index,
            "Stuck Capital Value": stuck_capital_value,
            "Harvest to Stuck Ratio": harvest_to_stuck_ratio,
        }
