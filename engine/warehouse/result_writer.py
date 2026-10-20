"""
Recording a long-running process's sweep results in the warehouse, without
holding the warehouse open.

DuckDBResultSink is written for a process that owns the warehouse for a whole
sweep (`cli.py backtest --warehouse`): one read-write connection from first
configuration to last. The server cannot do that. It also READS the warehouse
-- every backtest loads its bars through engine/warehouse/bars.py -- and DuckDB
refuses a second connection to a file this process already holds in another
mode, so a sink held open for an hours-long sweep would fail every bar read in
the server for its duration, and lock every other process (a backtest on the
host, the backup) out of the files as well.

So this buffers rows and writes them in short batches: open read-write under
connection.WAREHOUSE_LOCK's write side, record the batch through
DuckDBResultSink, close. Reads in this process wait for a batch instead of
failing; other processes are locked out only while one is written. A batch the
warehouse refuses (another process holding it) is kept and retried with the
next. Like the sink it wraps, nothing here raises: the warehouse is a record of
a sweep, never a reason to lose one.

Metrics for every configuration, plus the trade log of the best one only, at
finish() -- the configuration Run History keeps fills for. Every configuration's
trade log would run a brute-force sweep to tens of gigabytes.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BatchedResultWriter:
    """Records one sweep's rows into sim_results.duckdb, a batch at a time."""

    def __init__(
        self,
        root: str | Path,
        *,
        sweep_id: str,
        algorithm: str,
        base_parameters: dict[str, Any],
        cost_config: Any,
        dataset_version: str,
        flush_rows: int = 250,
        flush_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._root = Path(root)
        self._sweep_id = sweep_id
        self._algorithm = algorithm
        self._base_parameters = base_parameters
        self._cost_config = cost_config
        self._dataset_version = dataset_version
        self._flush_rows = flush_rows
        self._flush_seconds = flush_seconds
        self._clock = clock
        self._last_flush = clock()
        self._pending: list[tuple[dict[str, Any], int]] = []
        self._initialized = False
        self.stats = {"recorded": 0, "failed": 0, "skipped_duplicate": 0, "errors": 0}

    @property
    def sweep_id(self) -> str:
        return self._sweep_id

    def add(self, row: dict[str, Any], elapsed_ms: int = 0) -> None:
        """Buffer one finished configuration; write the batch once it is
        flush_rows long or flush_seconds old."""
        self._pending.append((dict(row), int(elapsed_ms)))
        due = self._clock() - self._last_flush >= self._flush_seconds
        if len(self._pending) >= self._flush_rows or due:
            self.flush()

    def flush(self) -> None:
        """Write what is buffered now. Kept for the next attempt if the
        warehouse cannot be opened."""
        self._last_flush = self._clock()
        if self._pending:
            self._write(best=None)

    def finish(self, best_row: dict[str, Any] | None = None, best_result: Any = None) -> dict:
        """Write the rest, and the best configuration's trade log. Returns
        the counts, with `unwritten` for rows the warehouse never took."""
        best = (best_row, best_result) if best_row is not None and best_result is not None else None
        if self._pending or best is not None:
            self._write(best=best)
        if self._pending:
            logger.error(
                f"Warehouse sweep {self._sweep_id}: {len(self._pending)} result(s) could not be "
                "written. They remain in the run's history and checkpoint."
            )
        return {**self.stats, "unwritten": len(self._pending)}

    def _write(self, *, best: tuple[dict[str, Any], Any] | None) -> None:
        try:
            from engine.warehouse import schema
            from engine.warehouse.connection import EXECUTIONS_DIR, WAREHOUSE_LOCK, open_warehouse
            from engine.warehouse.duckdb_sink import DuckDBResultSink, ensure_broker_environment
            from engine.warehouse.hashing import broker_id_for
        except ImportError as e:
            logger.error(f"Warehouse unavailable ({e}); {len(self._pending)} result(s) dropped.")
            self._pending.clear()
            return

        with WAREHOUSE_LOCK.writing():
            try:
                con = open_warehouse(self._root)
            except Exception as e:
                logger.warning(
                    f"Warehouse busy or unreadable ({type(e).__name__}: {e}); "
                    f"{len(self._pending)} result(s) kept for the next write."
                )
                return
            try:
                if not self._initialized:
                    schema.initialize(con, self._root)
                    self._initialized = True
                broker_id = broker_id_for(self._cost_config)
                model = getattr(self._cost_config, "model_type", "zero")
                ensure_broker_environment(con, broker_id, self._cost_config, f"{model} costs")
                sink = DuckDBResultSink(con, self._root, dataset_version=self._dataset_version)
                sink.open_sweep(
                    algorithm=self._algorithm,
                    base_parameters=self._base_parameters,
                    broker_id=broker_id,
                    dataset_version=self._dataset_version,
                    sweep_id=self._sweep_id,
                )
                for row, elapsed_ms in self._pending:
                    sink.record(row=row, sim_result=None, elapsed_ms=elapsed_ms)
                self._pending.clear()
                if best is not None:
                    row, result = best
                    simulation_id = sink.simulation_id(row)
                    lake = self._root / EXECUTIONS_DIR / f"simulation_id={simulation_id}"
                    # A configuration recorded by an earlier run already has its
                    # trade log; appending it again would double every fill.
                    if not lake.exists() and sink.attach_execution(simulation_id, result):
                        schema.refresh_views(con, self._root)
                for key, value in sink.stats.items():
                    self.stats[key] += value
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(
                    f"Warehouse sweep {self._sweep_id} could not record a batch "
                    f"({type(e).__name__}: {e})"
                )
            finally:
                con.close()


__all__ = ["BatchedResultWriter"]
