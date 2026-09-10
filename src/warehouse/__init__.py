"""
DuckDB + Polars analytical warehouse over bar history and sweep output.

OPTIONAL DEPENDENCY BOUNDARY

This is the second subpackage (after src/ml/) exempted from
requirements.txt's core-only rule, and it carries the same obligation:
nothing in src/ outside this package may import it, and a sweep that
does not ask for a warehouse must never load it. See
requirements-warehouse.txt for the reasoning.

That is why the sink Protocol lives in src/optimization/result_sink.py
(stdlib only) and the implementation lives here. run_sweep types its
parameter against the Protocol and never imports duckdb.

WHY TWO DATABASES

market_data.duckdb is slowly-changing reference data (what instruments
exist, what happened to them) shared across every experiment.
sim_results.duckdb is append-heavy output of one machine's sweeps.
Splitting them means the expensive-to-rebuild half can be copied
between machines, deleted, or version-pinned independently of the
disposable half. ATTACH makes the split invisible at query time --
connection.open_warehouse() returns one connection that sees both.

WHAT IS NOT IN A DATABASE FILE

The heavy data -- OHLCV bars and trade executions -- lives in
ZSTD-compressed Parquet partitioned on disk, with a VIEW over it in
the catalog. DuckDB reads Parquet natively, so this costs nothing at
query time and keeps the .duckdb files small enough to be catalogs
rather than data stores.
"""

from __future__ import annotations

__all__ = [
    "DuckDBResultSink",
    "initialize",
    "open_warehouse",
    "parameter_hash",
]


def __getattr__(name: str):
    """Lazily re-export, so `import src.warehouse` alone does not pull
    in duckdb/polars. Only hashing is dependency-free; the rest is
    resolved on first use."""
    if name == "parameter_hash":
        from src.warehouse.hashing import parameter_hash

        return parameter_hash
    if name in ("open_warehouse",):
        from src.warehouse.connection import open_warehouse

        return open_warehouse
    if name in ("initialize",):
        from src.warehouse.schema import initialize

        return initialize
    if name == "DuckDBResultSink":
        from src.warehouse.duckdb_sink import DuckDBResultSink

        return DuckDBResultSink
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
