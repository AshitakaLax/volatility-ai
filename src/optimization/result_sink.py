"""
The seam between a running sweep and a durable result store.

WHY A PROTOCOL AND NOT JUST AN IMPORT

run_sweep needs to hand every finished combination somewhere durable.
The obvious implementation is DuckDB (src/warehouse/), but
requirements.txt's standing rule is that the live trading loop and the
Raspberry Pi that runs it must never need an optional dependency to
start -- and src/optimization is imported by the live path. Importing
duckdb here would make a Pi that only ever runs the trading loop fail
at import time over an analytics library it has no use for.

So this module is stdlib-only and defines the shape; src/warehouse
supplies the implementation, and only a caller that explicitly asks for
a warehouse ever imports it. run_sweep's parameter is typed against
SweepResultSink, which is a typing.Protocol -- structural, so the
implementation does not import this module either, and the two
directions stay decoupled.

WHY THE PARENT PROCESS OWNS EVERY CALL

DuckDB permits one read-write process per database file. run_sweep's
parallel branch resolves futures with as_completed in the parent, so
routing sink calls through that loop serializes writes for free -- no
lock, no queue, no worker-side connection. A sink is therefore NEVER
called from a worker process, and implementations may assume single
-threaded access.

WHY record() MUST NOT RETAIN sim_result

optimization_controller.py:1398 records a real incident: appending
every SimulationResult unconditionally exhausted RAM on a
1,260-combination run, because each one carries a per-bar equity curve
(~1.03M entries on the 10-year minute dataset) and a full trade blotter
(~540k rows). A sink is handed the same object. It must write what it
needs and drop the reference before returning; anything that
accumulates them across a sweep reintroduces exactly that failure.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SweepResultSink(Protocol):
    """Receives sweep results as they complete, in the parent process.

    Implemented by src.warehouse.duckdb_sink.DuckDBResultSink. Kept
    minimal on purpose: a sweep should not have to know whether the far
    side is a database, a file, or a test spy.
    """

    def open_sweep(
        self,
        *,
        algorithm: str,
        base_parameters: dict[str, Any],
        broker_id: str,
        dataset_version: str,
    ) -> str:
        """Begin a batch and return its id.

        Called once, before the first combination runs. `algorithm` is
        the search strategy name ("grid"/"bayesian"/"random"),
        `dataset_version` the identity of the bars being swept -- both
        are lineage, not parameters, which is why they are fixed for
        the batch rather than repeated per row.
        """
        ...

    def record(
        self,
        *,
        row: dict[str, Any],
        sim_result: Any | None,
        elapsed_ms: int,
    ) -> None:
        """Record one finished combination.

        `row` is run_sweep's flat result row. `sim_result` is the
        SimulationResult, or None -- _run_one_combination returns None
        on failure and puts the message in row["error"], so a sink
        distinguishes success from failure by that, not by exceptions.

        Must not raise: a sweep is minutes-to-hours of engine time and
        losing it to a storage hiccup is a worse outcome than losing
        the record. Implementations log and continue, the same bargain
        run_sweep already makes for progress_callback.

        Must not retain sim_result -- see the module docstring.
        """
        ...

    def close_sweep(self) -> None:
        """Finalize the batch. Called once, in a finally block, so it
        runs even when a sweep raises partway through."""
        ...
