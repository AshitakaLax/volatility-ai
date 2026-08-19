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


class PerformanceAnalyzer:
    """Computes end-of-run summary metrics from a ledger.

    Stateless by design -- a static method rather than an instance, so
    there is no accumulated state to reset between combinations.
    """

    @staticmethod
    def calculate_metrics(ledger, final_portfolio_value: float, initial_cash: float) -> dict:
        """Summary metrics for one completed run.

        Deliberately does NOT return "Max Drawdown %": the controller
        tracks that per-bar and assigns it itself, and producing it here
        too would create two figures under one key that could silently
        disagree.

        Realized PnL counts only closed lots; open lots contribute to
        Final Equity through mark-to-market instead.
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

        return {
            "Final Equity": final_portfolio_value,
            "Total Return %": total_return_pct,
            "Realized PnL": realized_pnl,
            "Trade Count": total_lots,
            "Closed Trade Count": len(closed_lots),
            "Open Trade Count": len(open_lots),
            "Capital Velocity Index": capital_velocity_index,
        }
