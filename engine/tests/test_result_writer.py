"""engine/warehouse/result_writer.py -- a long-running process records every
configuration in the warehouse without ever holding it open.

SKIPS WITHOUT DUCKDB/POLARS, like the other warehouse tests.
"""

from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")
pytest.importorskip("polars")

from engine.tests.test_warehouse_schema import _bars  # noqa: E402
from engine.warehouse.connection import open_warehouse  # noqa: E402
from engine.warehouse.result_writer import BatchedResultWriter  # noqa: E402

SWEEP = "server-abc123-TESTQ"


class _Cost:
    model_type = "zero"
    commission_per_trade = 0.0
    slippage_bps = 0.0
    base_bps = 0.0
    vol_multiplier = 1.0


@pytest.fixture(scope="module")
def finished() -> list[tuple[dict, object]]:
    """(row, SimulationResult) for three real configurations."""
    from research.optimization.optimization_controller import OptimizationController
    from research.strategies.size_calculators import FixedPortfolioPercentage

    collected = []

    class Collect:
        def record(self, *, row, sim_result, elapsed_ms):
            collected.append((row, sim_result))

    OptimizationController(historical_data=_bars(400)).run_sweep(
        grid_steps=[0.005, 0.01, 0.02],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        symbol="TESTQ",
        initial_cash=100_000.0,
        result_sink=Collect(),
    )
    assert len(collected) == 3
    return collected


def _writer(root, **kwargs) -> BatchedResultWriter:
    return BatchedResultWriter(
        root,
        sweep_id=SWEEP,
        algorithm="grid",
        base_parameters={"symbol": "TESTQ"},
        cost_config=_Cost(),
        dataset_version="v1",
        **kwargs,
    )


def _query(root, sql: str):
    con = open_warehouse(root, read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def _recorded(root) -> int:
    return _query(root, "SELECT COUNT(*) FROM sim.simulations")[0][0]


def test_rows_are_written_in_batches_and_the_rest_at_finish(tmp_path, finished):
    writer = _writer(tmp_path, flush_rows=2)
    writer.add(finished[0][0])
    writer.add(finished[1][0])
    assert _recorded(tmp_path) == 2
    writer.add(finished[2][0])
    assert _recorded(tmp_path) == 2, "the third waits for the next batch"

    stats = writer.finish()
    assert _recorded(tmp_path) == 3
    assert stats["recorded"] == 3 and stats["unwritten"] == 0
    assert _query(tmp_path, f"SELECT COUNT(*) FROM sim.sweeps WHERE sweep_id = '{SWEEP}'") == [(1,)]


def test_the_warehouse_is_closed_between_batches(tmp_path, finished):
    """A same-process read with sim attached -- what every bar read does --
    fails outright while another connection holds the files read-write."""
    writer = _writer(tmp_path, flush_rows=1)
    writer.add(finished[0][0])
    assert _recorded(tmp_path) == 1
    writer.add(finished[1][0])
    assert _recorded(tmp_path) == 2


def test_a_resumed_run_continues_its_sweep_without_recording_twice(tmp_path, finished):
    first = _writer(tmp_path)
    for row, _ in finished:
        first.add(row)
    first.finish()

    again = _writer(tmp_path)
    for row, _ in finished:
        again.add(row)
    stats = again.finish()

    assert stats["skipped_duplicate"] == 3 and stats["recorded"] == 0
    assert _recorded(tmp_path) == 3
    assert _query(tmp_path, "SELECT COUNT(*) FROM sim.sweeps") == [(1,)]


def test_finish_attaches_the_best_configurations_trade_log_once(tmp_path, finished):
    best_row, best_result = finished[0]
    fills = len(best_result.trade_blotter)
    assert fills > 0

    writer = _writer(tmp_path)
    for row, _ in finished:
        writer.add(row)
    writer.finish(best_row, best_result)
    count = "SELECT COUNT(*), COUNT(DISTINCT simulation_id) FROM sim.trade_executions"
    assert _query(tmp_path, count) == [(fills, 1)], "the best one's trade log only"

    _writer(tmp_path).finish(best_row, best_result)
    assert _query(tmp_path, count) == [(fills, 1)], "never appended twice"


def test_a_busy_warehouse_keeps_the_batch_for_the_next_write(tmp_path, finished, monkeypatch):
    """Another process holding the files refuses the open; nothing is lost."""
    import engine.warehouse.connection as connection

    real = connection.open_warehouse
    refusals = [RuntimeError("IO Error: Could not set lock on file")]

    def busy_once(root, **kwargs):
        if refusals:
            raise refusals.pop()
        return real(root, **kwargs)

    monkeypatch.setattr(connection, "open_warehouse", busy_once)
    writer = _writer(tmp_path, flush_rows=1)
    writer.add(finished[0][0])
    writer.add(finished[1][0])
    monkeypatch.undo()
    assert _recorded(tmp_path) == 2


def test_an_unusable_warehouse_never_raises(tmp_path):
    root = tmp_path / "not-a-directory"
    root.write_text("")
    writer = _writer(root, flush_rows=1)
    writer.add({"Grid Step": 0.01, "Profit Target": 0.02, "Strategy": "X"})
    assert writer.finish()["unwritten"] == 1
