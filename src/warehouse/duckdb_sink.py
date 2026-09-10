"""
The DuckDB implementation of src/optimization/result_sink.SweepResultSink.

STRUCTURAL, NOT NOMINAL: this class does not import or subclass the
Protocol it satisfies. That is what keeps src/optimization free of any
duckdb import -- see result_sink.py's header for the full argument.

THREE RULES THIS CLASS LIVES BY

1. record() never raises. A sweep is minutes to hours of engine time
   and losing it to a constraint violation or a full disk is strictly
   worse than losing the row. Failures are logged once each and
   counted; close_sweep() reports the tally so a silently half-written
   warehouse is still visible to the operator.

2. record() never retains sim_result. optimization_controller.py:1398
   records a 1,260-combination run that exhausted RAM by holding these
   objects; each carries a ~1M-entry equity curve and a blotter up to
   ~540k rows. The blotter is converted, written, and dropped before
   returning.

3. Every write goes to the sim catalog only. DuckDB refuses a
   transaction that touches two attached databases (measured), and
   nothing here has any reason to.

WHY THE BLOTTER SCHEMA IS PINNED

Measured: polars types an all-null column as String, and DuckDB then
reads it back as VARCHAR. A combination that closes no trades produces
a blotter whose sell_reason and profit_realized are entirely null --
so that run's Parquet file would disagree about profit_realized's type
with every other run's, and one view over the lake could not bind both.
BLOTTER_SCHEMA casts every column explicitly, so the lake stays
readable no matter what any individual combination did.
"""

from __future__ import annotations

import json
import logging
import math
import uuid
from pathlib import Path
from typing import Any

from src.warehouse.connection import EXECUTIONS_DIR, lake_path
from src.warehouse.hashing import EXECUTION_FLAG_FIELDS, parameter_hash

logger = logging.getLogger(__name__)

# Everything PerformanceAnalyzer, trade_metrics, curve_metrics and
# _simulate_single put on a result row. Listed so that params can be
# separated from metrics by subtraction -- the same technique
# src/scripts/run_hf_sweep.py uses for its "top distinct combinations"
# table, and for the same reason: a NEW strategy parameter must never
# be mistaken for a metric, and subtracting a known metric set fails
# safe in that direction.
METRIC_KEYS = frozenset(
    {
        "Final Equity",
        "Total Return %",
        "Realized PnL",
        "Trade Count",
        "Closed Trade Count",
        "Open Trade Count",
        "Capital Velocity Index",
        "Stuck Capital Value",
        "Harvest to Stuck Ratio",
        "Max Drawdown %",
        "Signal Exit Count",
        "Return/Drawdown",
        "CAGR %",
        "Average Annual Return %",
        "Best Year Return %",
        "Worst Year Return %",
        "Profit Factor",
        "Win Rate %",
        "Max Consecutive Losses",
        "Average Hold Duration",
        "Sharpe",
        "Sortino",
    }
)

# Row keys that are neither parameters nor metrics.
_STRUCTURAL_KEYS = frozenset({"Grid Step", "Profit Target", "Strategy", "error"})

# (column, duckdb/polars target type). Order is the on-disk column
# order; simulation_id leads because it is the partition key.
BLOTTER_SCHEMA: tuple[tuple[str, str], ...] = (
    ("simulation_id", "Utf8"),
    ("timestamp", "Datetime"),
    ("side", "Utf8"),
    ("price", "Float64"),
    ("qty", "Float64"),
    ("equity", "Float64"),
    ("lot_id", "Utf8"),
    ("ticker", "Utf8"),
    ("bar_index", "Int64"),
    ("rsi", "Float64"),
    ("sell_reason", "Utf8"),
    ("profit_realized", "Float64"),
)


def _jsonable(value: Any) -> Any:
    """Coerce to something json.dumps and DuckDB's JSON type accept.

    numpy scalars are not JSON-serializable, and NaN/Infinity are
    emitted by json.dumps as bare NaN/Infinity tokens, which are not
    valid JSON and which DuckDB's JSON type rejects on insert. Both
    show up here for real: metrics carry numpy floats throughout, and
    "Return/Drawdown" is legitimately +/-inf on a zero-drawdown run.
    Non-finite becomes null -- the value is preserved in the promoted
    DOUBLE columns, which have no such restriction.
    """
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (bool, str)) or value is None:
        return value
    if hasattr(value, "item"):  # numpy scalar
        try:
            value = value.item()
        except (AttributeError, ValueError):
            return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, int):
        return value
    return str(value)


def _finite(value: Any) -> float | None:
    """A metric as a plain finite float, or None."""
    if value is None:
        return None
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (AttributeError, ValueError):
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def split_row(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Split a run_sweep result row into (strategy_params, execution, metrics).

    Anything that is not a known metric, a structural key, or an
    execution flag is a strategy parameter. See METRIC_KEYS on why the
    unknown case falls to "parameter" rather than "metric".
    """
    metrics = {k: v for k, v in row.items() if k in METRIC_KEYS}
    execution = {k: v for k, v in row.items() if k in EXECUTION_FLAG_FIELDS}
    params = {
        k: v
        for k, v in row.items()
        if k not in METRIC_KEYS and k not in _STRUCTURAL_KEYS and k not in EXECUTION_FLAG_FIELDS
    }
    # step/target duplicate Grid Step/Profit Target -- SimulationResult.params
    # carries both spellings. Dropped so they are not hashed twice under
    # two names.
    params.pop("step", None)
    params.pop("target", None)
    return params, execution, metrics


class DuckDBResultSink:
    """Writes sweep results into sim_results.duckdb + the Parquet lake."""

    def __init__(self, con: Any, root: str | Path, *, dataset_version: str = "unknown"):
        self._con = con
        self._root = Path(root)
        self._dataset_version = dataset_version
        self._sweep_id: str | None = None
        self._broker_id: str = "zero"
        self._recorded = 0
        self._failed = 0
        self._skipped_duplicate = 0
        self._errors = 0
        self._wrote_any_execution = False

    # -- lifecycle ---------------------------------------------------

    def open_sweep(
        self,
        *,
        algorithm: str,
        base_parameters: dict[str, Any],
        broker_id: str,
        dataset_version: str,
    ) -> str:
        self._sweep_id = uuid.uuid4().hex
        self._broker_id = broker_id
        self._dataset_version = dataset_version
        self._con.execute("USE sim")
        self._con.execute(
            """INSERT INTO sweeps
               (sweep_id, algorithm, base_parameters, broker_id, dataset_version, code_commit)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                self._sweep_id,
                algorithm,
                json.dumps(_jsonable(base_parameters)),
                broker_id,
                dataset_version,
                _code_commit(),
            ],
        )
        logger.info(f"Warehouse sweep {self._sweep_id} opened (algorithm={algorithm})")
        return self._sweep_id

    def close_sweep(self) -> None:
        logger.info(
            f"Warehouse sweep {self._sweep_id} closed: {self._recorded} recorded, "
            f"{self._failed} failed combinations, {self._skipped_duplicate} duplicate(s) skipped, "
            f"{self._errors} storage error(s)."
        )

    @property
    def stats(self) -> dict[str, int]:
        """Counts for the caller to print or assert on."""
        return {
            "recorded": self._recorded,
            "failed": self._failed,
            "skipped_duplicate": self._skipped_duplicate,
            "errors": self._errors,
        }

    # -- the hot path ------------------------------------------------

    def record(self, *, row: dict[str, Any], sim_result: Any | None, elapsed_ms: int) -> None:
        try:
            self._record(row=row, sim_result=sim_result, elapsed_ms=elapsed_ms)
        # Deliberately broad -- rule 1, see the module docstring.
        except Exception as e:
            self._errors += 1
            logger.error(f"Warehouse could not record a combination ({type(e).__name__}: {e})")
        finally:
            # Rule 2. The caller still holds its own reference when
            # return_full_results is set; this just guarantees the sink
            # is not the thing keeping it alive.
            sim_result = None

    def _record(self, *, row: dict[str, Any], sim_result: Any | None, elapsed_ms: int) -> None:
        if self._sweep_id is None:
            raise RuntimeError("record() called before open_sweep()")

        params, execution, metrics = split_row(row)
        error_text = row.get("error")
        succeeded = error_text is None and sim_result is not None

        phash = parameter_hash(
            strategy_id=str(row.get("Strategy", "unknown")),
            strategy_params=_jsonable(params),
            grid_step=float(row["Grid Step"]),
            profit_target=float(row["Profit Target"]),
            dataset_version=self._dataset_version,
            broker_id=self._broker_id,
            execution=_jsonable(execution),
        )
        simulation_id = phash[:16]

        self._con.execute("USE sim")
        already = self._con.execute(
            "SELECT 1 FROM simulations WHERE parameter_hash = ? LIMIT 1", [phash]
        ).fetchone()
        if already:
            # The UNIQUE constraint would catch this anyway; checking
            # first turns an exception path into a counted, expected
            # outcome. Re-running a sweep to extend it is a normal
            # thing to do, not an error.
            self._skipped_duplicate += 1
            logger.debug(f"Combination {simulation_id} already recorded; skipping.")
            return

        self._con.execute(
            """INSERT INTO simulations
               (simulation_id, sweep_id, dataset_version, parameters_json, parameter_hash,
                status, error_trace, execution_time_ms, sharpe_ratio, max_drawdown,
                total_return, metrics_json, trade_count, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())""",
            [
                simulation_id,
                self._sweep_id,
                self._dataset_version,
                json.dumps(
                    _jsonable(
                        {
                            "strategy": row.get("Strategy"),
                            "grid_step": row.get("Grid Step"),
                            "profit_target": row.get("Profit Target"),
                            "strategy_params": params,
                            "execution": execution,
                        }
                    )
                ),
                phash,
                "COMPLETED" if succeeded else "FAILED",
                None if succeeded else str(error_text),
                int(elapsed_ms),
                _finite(metrics.get("Sharpe")),
                _finite(metrics.get("Max Drawdown %")),
                _finite(metrics.get("Total Return %")),
                json.dumps(_jsonable(metrics)),
                _finite(metrics.get("Trade Count")),
            ],
        )

        if succeeded:
            self._recorded += 1
            self._write_executions(simulation_id, sim_result)
        else:
            self._failed += 1

    def _write_executions(self, simulation_id: str, sim_result: Any) -> None:
        """Append this combination's blotter to the executions lake."""
        import polars as pl

        blotter = getattr(sim_result, "trade_blotter", None)
        if blotter is None or getattr(blotter, "empty", True):
            return

        frame = pl.from_pandas(blotter)
        # Pin every column, adding any the combination never produced.
        # A run with no sells has no sell_reason column at all; one with
        # sells but no seeded RSI has an all-null rsi that polars types
        # as String. Both would fracture the lake's schema.
        projection = []
        for name, dtype in BLOTTER_SCHEMA:
            target = (
                pl.Datetime(time_unit="us", time_zone="UTC")
                if dtype == "Datetime"
                else getattr(pl, dtype)
            )
            if name == "simulation_id":
                projection.append(pl.lit(simulation_id).cast(pl.Utf8).alias(name))
            elif name in frame.columns:
                projection.append(pl.col(name).cast(target, strict=False).alias(name))
            else:
                projection.append(pl.lit(None).cast(target).alias(name))
        # Read by name from the COPY below (DuckDB replacement scan over
        # the local Arrow frame), which static analysis cannot see.
        executions = frame.select(projection)  # noqa: F841

        destination = lake_path(self._root, EXECUTIONS_DIR)
        Path(destination).mkdir(parents=True, exist_ok=True)
        self._con.execute(f"""
            COPY (SELECT * FROM executions ORDER BY timestamp)
            TO '{destination}'
            (FORMAT PARQUET, PARTITION_BY (simulation_id), COMPRESSION ZSTD, APPEND)
        """)
        self._wrote_any_execution = True

    @property
    def wrote_any_execution(self) -> bool:
        """Whether the executions view can be created yet."""
        return self._wrote_any_execution


def _code_commit() -> str | None:
    """Current git commit, for lineage. Best-effort: a warehouse built
    from an exported tarball with no .git is still a valid warehouse."""
    import subprocess

    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def ensure_broker_environment(con: Any, broker_id: str, cost_config: Any, label: str) -> str:
    """Insert the broker row a sweep's FK will point at, if absent."""
    con.execute("USE sim")
    con.execute(
        """INSERT OR IGNORE INTO broker_environments
           (broker_id, label, model_type, commission_per_trade, slippage_bps,
            base_bps, vol_multiplier)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            broker_id,
            label,
            getattr(cost_config, "model_type", "zero"),
            float(getattr(cost_config, "commission_per_trade", 0.0) or 0.0),
            float(getattr(cost_config, "slippage_bps", 0.0) or 0.0),
            float(getattr(cost_config, "base_bps", 0.0) or 0.0),
            float(getattr(cost_config, "vol_multiplier", 1.0) or 1.0),
        ],
    )
    return broker_id
