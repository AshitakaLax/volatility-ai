"""
Warehouse DDL.

THREE DUCKDB BEHAVIORS THIS SCHEMA IS SHAPED AROUND, ALL MEASURED

1. Inside a DDL body, `sim.broker_environments` resolves as
   SCHEMA.table, not CATALOG.table -- so a REFERENCES clause written
   that way fails with 'schema "sim" does not exist' even though the
   catalog is attached. The sim-side DDL therefore runs under
   `USE sim` with unqualified names, which is also simply easier to
   read than three-part `sim.main.broker_environments`.

2. A view cannot be indexed ("can only create an index on a base
   table"). The OHLCV view is a window onto Parquet, so what replaces
   an index is (a) Hive partitioning on ticker/year, which prunes whole
   directories, and (b) row-group min/max zonemaps on timestamp, which
   only prune if the data was SORTED at write time. That is why
   ingest.py sorts by (ticker, timestamp) before COPY -- the sort is
   the index, and skipping it silently costs a full scan on every ASOF
   join.

3. A single transaction may write to only one attached database
   ("Attempting to write to database "sim" in a transaction that has
   already modified database "market_data""). Nothing here spans both,
   and the sink keeps its writes on the sim side alone.

WHY dataset_version IS A PLAIN VARCHAR AND NOT A FOREIGN KEY

It identifies a bar dataset living in market_data, and DuckDB does not
support foreign keys across attached databases. Making it a real FK
would force the two catalogs into one file and give up the
independence described in the package docstring. The tradeoff is
accepted deliberately: lineage is recorded, not enforced.
"""

from __future__ import annotations

from typing import Any

from src.warehouse.connection import EXECUTIONS_DIR, EXTERNAL_DIR, OHLCV_DIR, lake_path

# --------------------------------------------------------------------
# market_data
# --------------------------------------------------------------------

# active_from / active_through are what prevent survivorship bias. A
# universe query filters on them rather than on "which CSVs happen to
# be sitting in data/", which is the mistake that quietly excludes
# every fund that closed before today.
ASSETS_DDL = """
CREATE TABLE IF NOT EXISTS assets (
    ticker         VARCHAR PRIMARY KEY,
    cusip          VARCHAR,
    sector         VARCHAR,
    active_from    DATE NOT NULL,
    active_through DATE,
    is_leveraged   BOOLEAN DEFAULT FALSE,
    leverage_ratio DOUBLE,
    notes          VARCHAR
)
"""

# Point-in-time: event_timestamp is when the market LEARNED the fact,
# so a query that filters `event_timestamp <= bar.timestamp` cannot
# leak a future dividend or split into a backtest. The PK is the
# natural key rather than a surrogate id, so re-ingesting the same
# source is idempotent instead of duplicating rows.
MARKET_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS market_events (
    ticker          VARCHAR NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    event_type      VARCHAR NOT NULL,
    value           DOUBLE,
    source          VARCHAR,
    PRIMARY KEY (ticker, event_timestamp, event_type)
)
"""

MARKET_EVENTS_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_market_events_ticker_ts
    ON market_events (ticker, event_timestamp)
"""

# The dimension table for the external Parquet lake (FRED / CBOE /
# Yahoo macro series). Mirrors `assets`: one row per series, carrying
# the metadata that a raw value column cannot.
#
# lag_days is the load-bearing column. A FRED macro print for month M
# is published weeks after M ends, but its observation timestamp in the
# CSV is dated within M. Joining a backtest bar to the observation
# timestamp would let the bar "see" a number that did not exist yet --
# the same silent lookahead src/ml/'s causal-transform rule guards
# against. The lag-aware query in queries.py shifts every observation
# forward by this many days before the ASOF match, so a bar only ever
# joins a value that had actually been released by then. Sourced from
# data/external/manifest.json, which tools/fetch_market_inputs.py
# writes alongside the CSVs.
EXTERNAL_SERIES_DDL = """
CREATE TABLE IF NOT EXISTS external_series (
    series_key   VARCHAR PRIMARY KEY,
    provider     VARCHAR NOT NULL,
    remote_id    VARCHAR,
    category     VARCHAR,
    description  VARCHAR,
    lag_days     DOUBLE DEFAULT 0.0,
    first_date   TIMESTAMPTZ,
    last_date    TIMESTAMPTZ,
    row_count    BIGINT
)
"""

# --------------------------------------------------------------------
# sim_results
# --------------------------------------------------------------------

SIMULATION_STATUS_DDL = """
CREATE TYPE simulation_status AS ENUM ('QUEUED','RUNNING','COMPLETED','FAILED')
"""

# Columns mirror src/core/config.py's CostConfig exactly, so a
# BacktestConfig round-trips into a broker row without inventing a
# second vocabulary for the same five numbers.
BROKER_ENVIRONMENTS_DDL = """
CREATE TABLE IF NOT EXISTS broker_environments (
    broker_id            VARCHAR PRIMARY KEY,
    label                VARCHAR NOT NULL,
    model_type           VARCHAR NOT NULL,
    commission_per_trade DOUBLE DEFAULT 0.0,
    slippage_bps         DOUBLE DEFAULT 0.0,
    base_bps             DOUBLE DEFAULT 0.0,
    vol_multiplier       DOUBLE DEFAULT 1.0
)
"""

SWEEPS_DDL = """
CREATE TABLE IF NOT EXISTS sweeps (
    sweep_id        VARCHAR PRIMARY KEY,
    algorithm       VARCHAR NOT NULL,
    base_parameters JSON NOT NULL,
    broker_id       VARCHAR NOT NULL REFERENCES broker_environments(broker_id),
    dataset_version VARCHAR,
    code_commit     VARCHAR,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

# parameter_hash is UNIQUE: that constraint IS the dedup mechanism.
# metrics_json holds the full metric dict because three promoted
# columns cannot carry all 22 of them -- and because metrics like
# "Return/Drawdown" are legitimately +/-inf, which is valid JSON text
# but would be rejected by the canonical hasher. Stored, never hashed.
SIMULATIONS_DDL = """
CREATE TABLE IF NOT EXISTS simulations (
    simulation_id     VARCHAR PRIMARY KEY,
    sweep_id          VARCHAR NOT NULL REFERENCES sweeps(sweep_id),
    dataset_version   VARCHAR NOT NULL,
    parameters_json   JSON NOT NULL,
    parameter_hash    VARCHAR NOT NULL UNIQUE,
    status            simulation_status NOT NULL DEFAULT 'QUEUED',
    error_trace       VARCHAR,
    execution_time_ms BIGINT,
    sharpe_ratio      DOUBLE,
    max_drawdown      DOUBLE,
    total_return      DOUBLE,
    metrics_json      JSON,
    trade_count       BIGINT,
    completed_at      TIMESTAMPTZ
)
"""


def ohlcv_view_ddl(root) -> str:
    """The OHLCV view. union_by_name guards against a lake whose
    partitions were written by different code versions -- without it a
    single added column turns every older file into a bind error."""
    return f"""
CREATE OR REPLACE VIEW ohlcv AS
SELECT * FROM read_parquet(
    '{lake_path(root, OHLCV_DIR)}/**/*.parquet',
    hive_partitioning = true,
    union_by_name = true
)
"""


def executions_view_ddl(root) -> str:
    return f"""
CREATE OR REPLACE VIEW trade_executions AS
SELECT * FROM read_parquet(
    '{lake_path(root, EXECUTIONS_DIR)}/**/*.parquet',
    hive_partitioning = true,
    union_by_name = true
)
"""


def external_view_ddl(root) -> str:
    """The external-series view. union_by_name matters more here than
    anywhere else: the sources genuinely disagree on shape -- most FRED
    series are timestamp+close, some CBOE series add high/low, Yahoo
    adds volume -- so the per-partition Parquet files have different
    column sets and only union_by_name binds them into one view."""
    return f"""
CREATE OR REPLACE VIEW external AS
SELECT * FROM read_parquet(
    '{lake_path(root, EXTERNAL_DIR)}/**/*.parquet',
    hive_partitioning = true,
    union_by_name = true
)
"""


def _type_exists(con: Any, catalog: str, name: str) -> bool:
    return bool(
        con.execute(
            "SELECT 1 FROM duckdb_types() WHERE database_name = ? AND type_name = ? LIMIT 1",
            [catalog, name],
        ).fetchone()
    )


def initialize(con: Any, root) -> None:
    """Create every table, type and view. Idempotent.

    Views over the Parquet lakes are created only once a lake has at
    least one file: read_parquet over an empty glob is an error at
    CREATE VIEW time, and a warehouse that cannot be initialized before
    its first ingest would be useless. Callers re-run initialize (or
    refresh_views) after ingesting.
    """
    con.execute("USE market_data")
    con.execute(ASSETS_DDL)
    con.execute(MARKET_EVENTS_DDL)
    con.execute(MARKET_EVENTS_INDEX_DDL)
    con.execute(EXTERNAL_SERIES_DDL)

    con.execute("USE sim")
    # CREATE TYPE has no IF NOT EXISTS in DuckDB, so existence is
    # checked rather than exception-swallowed -- a genuine DDL error
    # here should still surface.
    if not _type_exists(con, "sim", "simulation_status"):
        con.execute(SIMULATION_STATUS_DDL)
    con.execute(BROKER_ENVIRONMENTS_DDL)
    con.execute(SWEEPS_DDL)
    con.execute(SIMULATIONS_DDL)

    con.execute("USE market_data")
    refresh_views(con, root)


def refresh_views(con: Any, root) -> dict[str, bool]:
    """(Re)create the lake views, skipping any lake that has no files
    yet. Returns which views now exist."""
    from pathlib import Path

    created = {}
    for name, subdir, ddl, catalog in (
        ("ohlcv", OHLCV_DIR, ohlcv_view_ddl, "market_data"),
        ("external", EXTERNAL_DIR, external_view_ddl, "market_data"),
        ("trade_executions", EXECUTIONS_DIR, executions_view_ddl, "sim"),
    ):
        has_files = any(Path(root, subdir).rglob("*.parquet"))
        if has_files:
            con.execute(f"USE {catalog}")
            con.execute(ddl(root))
        created[name] = has_files
    con.execute("USE market_data")
    return created
