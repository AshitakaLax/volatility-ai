"""Aggregate deterministic performance metrics for a simulation run."""

from __future__ import annotations

from .ledger import AssetLotLedger


class PerformanceAnalyzer:
    """Compute the metric row consumed by ``OptimizationController``.

    The controller currently supplies final portfolio value and initial cash,
    while the ledger supplies the number of completed harvest tickets.  The
    metric schema is intentionally small and stable; later tasks can extend it
    without changing the accounting primitives.
    """

    @staticmethod
    def calculate_metrics(
        ledger: AssetLotLedger,
        final_portfolio_value: float,
        initial_cash: float,
    ) -> dict[str, float | int]:
        initial = float(initial_cash)
        final = float(final_portfolio_value)
        if initial <= 0:
            raise ValueError("initial_cash must be positive")

        total_return = (final - initial) / initial
        trade_count = len(ledger.closed_lots)

        return {
            "Final Portfolio Value": final,
            "Trade Count": trade_count,
            "Total Return %": total_return * 100.0,
            # Current controller ranks on this field.  With no time basis in
            # the legacy simulation, the deterministic capital-velocity proxy
            # is realized portfolio growth relative to starting capital.
            "Capital Velocity Index": total_return,
        }
