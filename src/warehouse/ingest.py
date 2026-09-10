"""
Getting data into the warehouse: CSV -> partitioned Parquet, plus the
two reference tables.

THE DIVISION OF LABOUR BETWEEN POLARS AND DUCKDB

Polars scans and normalizes; DuckDB writes the partitions. That split
is deliberate and worth defending, because either tool could in
principle do both.

Polars owns the read because pl.scan_csv is lazy and streaming: the
predicate/projection pushdown means a 149 MB file's columns are parsed
once, in Rust, without ever materializing the full frame the way
pd.read_csv does. It also parses the ISO-8601 "+00:00" timestamps
straight to datetime[us, UTC] (measured), which is exactly the physical
type DuckDB maps to TIMESTAMP WITH TIME ZONE -- so the tz-correctness
that the ASOF join depends on is established at the point of reading
rather than patched afterwards.

DuckDB owns the write because COPY ... (PARTITION_BY ...) is the
battle-tested path for a Hive layout, handles ZSTD and the directory
fan-out itself, and -- the part that matters -- lets the ORDER BY sit
inside the same statement. Polars' partitioned sink API has churned
across releases; DuckDB's COPY has not.

The handoff is zero-copy: DuckDB's replacement scan reads the Polars
frame through Arrow, so `FROM normalized` in the SQL below refers to
the local Python variable without a serialization step.

HONEST NOTE: for OHLCV alone, DuckDB's own read_csv_auto could do the
whole job and Polars would be ceremony. Polars earns its place here on
the normalization (pinning dtypes, deriving `year`, renaming provider
quirks) and in duckdb_sink.py, where a pandas blotter has to become
Arrow anyway. It is not load-bearing for correctness of the read.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.warehouse.connection import EXECUTIONS_DIR, EXTERNAL_DIR, OHLCV_DIR, lake_path

logger = logging.getLogger(__name__)

# The canonical bar schema, matching src/data/historical_data.py's
# BACKTEST_COLUMNS plus the two partition keys. Pinned explicitly
# rather than inferred: a lake whose partitions disagree about a
# column's type cannot be read back through one view.
OHLCV_COLUMNS = ("ticker", "year", "timestamp", "open", "high", "low", "close", "volume")


def dataset_version(csv_path: str | Path) -> str:
    """Lineage id for a bar file.

    Prefers the sha256 that src/data/historical_data.py already wrote
    into the .meta.json sidecar at download time -- it is computed over
    the exact bytes fetched, so it identifies the DATA rather than the
    file's current mtime or name. Falls back to hashing the file
    ourselves for hand-made CSVs that never had a sidecar (SQQQ_rth_full.csv
    and friends predate the sidecar convention).
    """
    csv_path = Path(csv_path)
    for candidate in (csv_path.with_suffix(".meta.json"), Path(f"{csv_path}.meta.json")):
        if candidate.exists():
            try:
                meta = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                logger.warning(f"Sidecar {candidate} unreadable ({e}); hashing the CSV instead.")
                break
            sha = meta.get("sha256")
            if sha:
                return str(sha)
            logger.warning(f"Sidecar {candidate} has no sha256; hashing the CSV instead.")
            break

    import hashlib

    digest = hashlib.sha256()
    with open(csv_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_bars(csv_path: Path, ticker: str):
    """Lazily scan one OHLCV CSV into the canonical schema."""
    import polars as pl

    frame = (
        pl.scan_csv(csv_path, try_parse_dates=True)
        .with_columns(
            # A file written without an offset parses naive; one written
            # with "+00:00" parses tz-aware. replace_time_zone on a
            # naive column and convert_time_zone on an aware one are
            # different operations, so the branch is resolved by dtype
            # rather than assumed.
            pl.col("timestamp").cast(pl.Datetime(time_unit="us")),
        )
        .with_columns(
            pl.col("timestamp").dt.replace_time_zone("UTC"),
        )
        .with_columns(
            pl.lit(ticker).alias("ticker"),
            pl.col("timestamp").dt.year().cast(pl.Int32).alias("year"),
            pl.col("open").cast(pl.Float64),
            pl.col("high").cast(pl.Float64),
            pl.col("low").cast(pl.Float64),
            pl.col("close").cast(pl.Float64),
            # int64 upstream, but resample_uniform.py emits 0.0 floats
            # for synthetic bars, so the cast is not a no-op.
            pl.col("volume").cast(pl.Int64),
        )
        .select(OHLCV_COLUMNS)
    )
    return frame


def ingest_ohlcv_csv(
    con: Any,
    root: str | Path,
    csv_path: str | Path,
    ticker: str,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Ingest one bar CSV into the ticker/year Parquet lake.

    Returns a report dict (ticker, rows, years, dataset_version).
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No such bar file: {csv_path}")

    # Looks unused: it is read by name from the COPY statement below,
    # via DuckDB's replacement scan over the local Arrow frame.
    normalized = _normalize_bars(csv_path, ticker).collect()
    row_count = normalized.height
    if row_count == 0:
        raise ValueError(f"{csv_path} produced zero rows; refusing to write an empty partition.")

    destination = lake_path(root, OHLCV_DIR)
    Path(destination).mkdir(parents=True, exist_ok=True)
    mode = "OVERWRITE_OR_IGNORE" if overwrite else "APPEND"

    # ORDER BY is the index -- see schema.py's header. Without it the
    # row-group zonemaps do not prune and every ASOF join degrades to a
    # full scan of the partition.
    con.execute(f"""
        COPY (SELECT {", ".join(OHLCV_COLUMNS)} FROM normalized ORDER BY ticker, timestamp)
        TO '{destination}'
        (FORMAT PARQUET, PARTITION_BY (ticker, year), COMPRESSION ZSTD, {mode})
    """)

    years = sorted(normalized["year"].unique().to_list())
    version = dataset_version(csv_path)
    logger.info(f"Ingested {row_count} {ticker} bars covering {years[0]}-{years[-1]}")
    return {
        "ticker": ticker,
        "rows": row_count,
        "years": years,
        "dataset_version": version,
        "source": str(csv_path),
    }


def upsert_assets(con: Any, rows: list[dict[str, Any]]) -> int:
    """Insert or replace asset dimension rows.

    DuckDB has no ON CONFLICT DO UPDATE for every constraint shape, so
    this deletes-then-inserts inside one transaction: re-running an
    ingest must not double the dimension table, and a corrected sector
    or delisting date must actually land.
    """
    if not rows:
        return 0
    con.execute("USE market_data")
    con.execute("BEGIN TRANSACTION")
    try:
        for row in rows:
            con.execute("DELETE FROM assets WHERE ticker = ?", [row["ticker"]])
            con.execute(
                """INSERT INTO assets
                   (ticker, cusip, sector, active_from, active_through, is_leveraged,
                    leverage_ratio, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    row["ticker"],
                    row.get("cusip"),
                    row.get("sector"),
                    row["active_from"],
                    row.get("active_through"),
                    bool(row.get("is_leveraged", False)),
                    row.get("leverage_ratio"),
                    row.get("notes"),
                ],
            )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return len(rows)


def upsert_market_events(con: Any, rows: list[dict[str, Any]]) -> int:
    """Insert point-in-time events, ignoring ones already recorded.

    The natural primary key (ticker, event_timestamp, event_type) makes
    re-ingesting the same earnings file a no-op rather than an error,
    which is what lets this be re-run on a schedule.
    """
    if not rows:
        return 0
    con.execute("USE market_data")
    con.execute("BEGIN TRANSACTION")
    try:
        for row in rows:
            con.execute(
                """INSERT OR IGNORE INTO market_events
                   (ticker, event_timestamp, event_type, value, source)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    row["ticker"],
                    row["event_timestamp"],
                    row["event_type"],
                    row.get("value"),
                    row.get("source"),
                ],
            )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return len(rows)


def earnings_events_from_csv(csv_path: str | Path, ticker_column: str = "symbol") -> list[dict]:
    """Read data/earnings_releases_derived.csv into market_events rows.

    That file is produced by tools/build_earnings_calendar.py and is
    already point-in-time correct -- release_utc is when the release
    actually hit the tape, which is the only timestamp that may be used
    as an event time without leaking the future.
    """
    import polars as pl

    frame = pl.read_csv(csv_path, try_parse_dates=True)
    if "release_utc" not in frame.columns:
        raise ValueError(
            f"{csv_path} has no release_utc column (found {frame.columns}); "
            "point-in-time correctness requires the UTC release instant."
        )
    events = []
    for row in frame.iter_rows(named=True):
        events.append(
            {
                "ticker": row[ticker_column],
                "event_timestamp": row["release_utc"],
                "event_type": "earnings",
                "value": row.get("postclose_peak_volume"),
                "source": Path(csv_path).name,
            }
        )
    return events


def suspect_bar_events(meta_json_path: str | Path, ticker: str) -> list[dict]:
    """Turn a dataset sidecar's suspect_bars into split candidates.

    src/data/data_validation.py flags any single-bar move over 15% and
    records it in the sidecar. Its module docstring names the case:
    an unadjusted 3:1 split looks like a ~66% crash. Those flags are
    the closest thing this project has to a corporate-actions feed, so
    they are recorded as 'split_candidate' -- candidate, not split,
    because a real 15% move on a 3x leveraged ETF is also perfectly
    possible and nothing here can tell the two apart.
    """
    path = Path(meta_json_path)
    if not path.exists():
        return []
    meta = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "ticker": ticker,
            "event_timestamp": entry["timestamp"] if isinstance(entry, dict) else entry[0],
            "event_type": "split_candidate",
            "value": entry.get("change_pct") if isinstance(entry, dict) else entry[1],
            "source": path.name,
        }
        for entry in meta.get("suspect_bars", [])
    ]


def executions_lake(root: str | Path) -> str:
    """Where the sink writes trade executions."""
    return lake_path(root, EXECUTIONS_DIR)


# --------------------------------------------------------------------
# External series (FRED / CBOE / Yahoo macro data)
# --------------------------------------------------------------------

# The canonical wide schema for the external lake. The sources do not
# agree on shape -- FRED is timestamp+close, some CBOE series add
# high/low, Yahoo adds volume -- so every series is projected onto this
# superset with NULLs for the columns it lacks. Pinned for the same
# reason OHLCV_COLUMNS is: one view has to bind partitions of differing
# origin.
EXTERNAL_COLUMNS = (
    "provider",
    "series_key",
    "category",
    "timestamp",
    "close",
    "high",
    "low",
    "volume",
)


def _normalize_external(csv_path: Path, series_key: str, provider: str, category: str | None):
    """Read one external CSV into EXTERNAL_COLUMNS.

    Reads eagerly rather than lazily: these files are small (the
    largest is ~16k daily rows) and the branch on which optional
    columns are present is cleaner against a materialized frame than
    against a lazy schema.
    """
    import polars as pl

    frame = pl.read_csv(csv_path, try_parse_dates=True).with_columns(
        # Same tz discipline as the bars: these timestamps are written
        # "YYYY-MM-DD 21:00:00+00:00" (space separator, explicit UTC
        # offset), which polars parses to a tz-aware datetime already;
        # the cast + replace_time_zone pins microsecond precision and
        # UTC so the lake column type is exactly TIMESTAMPTZ.
        pl.col("timestamp").cast(pl.Datetime(time_unit="us")),
    )
    frame = frame.with_columns(pl.col("timestamp").dt.replace_time_zone("UTC"))

    present = set(frame.columns)
    frame = frame.with_columns(
        pl.lit(provider).alias("provider"),
        pl.lit(series_key).alias("series_key"),
        pl.lit(category).alias("category"),
        pl.col("close").cast(pl.Float64),
    )
    for optional in ("high", "low", "volume"):
        if optional in present:
            frame = frame.with_columns(pl.col(optional).cast(pl.Float64))
        else:
            frame = frame.with_columns(pl.lit(None).cast(pl.Float64).alias(optional))
    return frame.select(EXTERNAL_COLUMNS)


def ingest_external_series(
    con: Any,
    root: str | Path,
    external_dir: str | Path,
    *,
    overwrite: bool = True,
) -> dict[str, Any]:
    """Ingest data/external/ into the external Parquet lake + dimension.

    Manifest-driven: data/external/manifest.json (written by
    tools/fetch_market_inputs.py) is the list of series and the source
    of every series' provider, category, publication lag and expected
    row count. A CSV with no manifest entry is skipped rather than
    guessed at -- its provider and lag would be unknown, and lag is not
    optional for point-in-time correctness.

    overwrite defaults True because, unlike the append-only bar lake,
    the external series are re-fetched wholesale by
    fetch_market_inputs.py -- a partial series is replaced, not
    extended.
    """
    external_dir = Path(external_dir)
    manifest_path = external_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"{manifest_path} not found. Run tools/fetch_market_inputs.py first -- "
            "the lake is built from the manifest, not from a directory glob."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    import polars as pl

    frames = []
    dim_rows: list[dict[str, Any]] = []
    skipped: list[str] = []
    for series_key, meta in sorted(manifest.items()):
        csv_path = external_dir / meta["file"]
        if not csv_path.exists():
            skipped.append(series_key)
            continue
        frame = _normalize_external(csv_path, series_key, meta["provider"], meta.get("category"))
        if frame.height == 0:
            skipped.append(series_key)
            continue
        frames.append(frame)
        dim_rows.append(
            {
                "series_key": series_key,
                "provider": meta["provider"],
                "remote_id": meta.get("remote_id"),
                "category": meta.get("category"),
                "description": meta.get("description"),
                "lag_days": float(meta.get("lag_days", 0.0) or 0.0),
                "first_date": meta.get("first"),
                "last_date": meta.get("last"),
                "row_count": frame.height,
            }
        )

    if not frames:
        raise ValueError(f"{external_dir} produced no ingestable series.")

    # One concat, one COPY -- 118 tiny frames, ~700k rows total. Read
    # by name from the COPY below via DuckDB's replacement scan.
    combined = pl.concat(frames, how="vertical")

    destination = lake_path(root, EXTERNAL_DIR)
    Path(destination).mkdir(parents=True, exist_ok=True)
    mode = "OVERWRITE_OR_IGNORE" if overwrite else "APPEND"
    con.execute(f"""
        COPY (SELECT {", ".join(EXTERNAL_COLUMNS)} FROM combined
              ORDER BY provider, series_key, timestamp)
        TO '{destination}'
        (FORMAT PARQUET, PARTITION_BY (provider, series_key), COMPRESSION ZSTD, {mode})
    """)

    upserted = upsert_external_series(con, dim_rows)
    logger.info(
        f"Ingested {len(frames)} external series ({combined.height} rows); "
        f"{len(skipped)} skipped (no file or empty)."
    )
    return {
        "series": len(frames),
        "rows": combined.height,
        "skipped": skipped,
        "dimension_rows": upserted,
    }


def upsert_external_series(con: Any, rows: list[dict[str, Any]]) -> int:
    """Insert or replace external_series dimension rows.

    Delete-then-insert inside one transaction, same as upsert_assets:
    a re-fetch that corrects a series' lag or extends its date range
    must land, and must not duplicate the row.
    """
    if not rows:
        return 0
    con.execute("USE market_data")
    con.execute("BEGIN TRANSACTION")
    try:
        for row in rows:
            con.execute("DELETE FROM external_series WHERE series_key = ?", [row["series_key"]])
            con.execute(
                """INSERT INTO external_series
                   (series_key, provider, remote_id, category, description, lag_days,
                    first_date, last_date, row_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    row["series_key"],
                    row["provider"],
                    row.get("remote_id"),
                    row.get("category"),
                    row.get("description"),
                    float(row.get("lag_days", 0.0) or 0.0),
                    row.get("first_date"),
                    row.get("last_date"),
                    row.get("row_count"),
                ],
            )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return len(rows)
