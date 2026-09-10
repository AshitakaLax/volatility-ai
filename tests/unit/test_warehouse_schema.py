"""Warehouse schema, sink and the ASOF join.

SKIPS WITHOUT DUCKDB, ON PURPOSE. duckdb and polars are in
requirements-warehouse.txt, not requirements.txt, and a clean checkout
that has installed only the core requirements must still get a green
suite -- otherwise an optional dependency has quietly become mandatory.
importorskip is the same bargain the rest of the project makes for
optional extras.

Several of these pin DuckDB behaviors that were measured rather than
assumed, and that would each produce a plausible wrong answer rather
than an error if they regressed. Those are called out individually.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

duckdb = pytest.importorskip("duckdb")
pytest.importorskip("polars")

from src.warehouse import ingest, queries, schema  # noqa: E402
from src.warehouse.connection import open_warehouse, total_system_ram_bytes  # noqa: E402
from src.warehouse.duckdb_sink import (  # noqa: E402
    BLOTTER_SCHEMA,
    METRIC_KEYS,
    DuckDBResultSink,
    ensure_broker_environment,
    split_row,
)


class _Cost:
    model_type = "zero"
    commission_per_trade = 0.0
    slippage_bps = 0.0
    base_bps = 0.0
    vol_multiplier = 1.0


def _bars(n: int = 200, start: str = "2016-01-04 14:30:00+00:00") -> pd.DataFrame:
    """Deterministic bars that actually trade.

    A pure sawtooth does NOT work here and the reason is worth stating:
    it oscillates above its opening price and never below it, so
    last_buy_price is never undercut, no grid step ever triggers, and
    every combination returns a legitimate zero-trade result. The
    downward drift is what makes the grid fire; the sawtooth on top is
    what lets lots reach their profit target and close.
    """
    idx = pd.date_range(start, periods=n, freq="1min")
    close = [100.0 * (1 - 0.0008 * i) + (i % 7) * 0.25 for i in range(n)]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [c + 0.1 for c in close],
            "low": [c - 0.1 for c in close],
            "close": close,
            "volume": [1000 + i for i in range(n)],
        },
        index=idx,
    )
    frame.index.name = "timestamp"
    return frame


def _write_csv(frame: pd.DataFrame, path):
    out = frame.copy()
    out.index = [t.isoformat() for t in out.index]
    out.to_csv(path, index_label="timestamp")
    return path


@pytest.fixture
def warehouse(tmp_path):
    root = tmp_path / "warehouse"
    con = open_warehouse(root)
    schema.initialize(con, root)
    yield con, root
    con.close()


# -- Part 1: initialization and tuning -------------------------------


def test_both_databases_are_attached(warehouse):
    con, _ = warehouse
    names = {r[0] for r in con.execute("SELECT database_name FROM duckdb_databases()").fetchall()}
    assert {"market_data", "sim"} <= names


def test_tuning_pragmas_are_applied(warehouse):
    con, _ = warehouse
    settings = dict(
        con.execute(
            "SELECT name, value FROM duckdb_settings() "
            "WHERE name IN ('threads','memory_limit','TimeZone')"
        ).fetchall()
    )
    assert int(settings["threads"]) >= 1
    assert settings["memory_limit"] not in (None, "", "0 bytes")
    # Measured: DuckDB's default TimeZone is the SYSTEM zone, and it
    # changes what TIMESTAMPTZ::TIMESTAMP produces. A warehouse whose
    # answers depend on the developer's timezone is a reproducibility
    # bug, so this is pinned rather than inherited.
    assert settings["TimeZone"] == "UTC"


def test_total_system_ram_is_plausible():
    ram = total_system_ram_bytes()
    assert ram >= 1024**3, "less than 1 GiB reported; the platform branch is probably wrong"


# -- Part 2: market_data ---------------------------------------------


def test_assets_upsert_is_idempotent(warehouse):
    con, _ = warehouse
    row = {"ticker": "TQQQ", "sector": "Leveraged", "active_from": dt.date(2010, 2, 9)}
    ingest.upsert_assets(con, [row])
    ingest.upsert_assets(con, [row])
    assert con.execute("SELECT count(*) FROM market_data.assets").fetchone()[0] == 1


def test_assets_upsert_updates_rather_than_duplicating(warehouse):
    con, _ = warehouse
    ingest.upsert_assets(
        con, [{"ticker": "X", "sector": "Old", "active_from": dt.date(2010, 1, 1)}]
    )
    ingest.upsert_assets(
        con,
        [
            {
                "ticker": "X",
                "sector": "New",
                "active_from": dt.date(2010, 1, 1),
                "active_through": dt.date(2020, 6, 1),
            }
        ],
    )
    sector, through = con.execute(
        "SELECT sector, active_through FROM market_data.assets WHERE ticker='X'"
    ).fetchone()
    assert sector == "New"
    assert through == dt.date(2020, 6, 1)


def test_delisted_asset_stays_in_a_historical_universe(warehouse):
    """The whole point of active_from/active_through: a fund that died
    in 2020 must still be in a 2018 universe. Filtering on 'what is in
    data/ today' instead is exactly survivorship bias."""
    con, _ = warehouse
    ingest.upsert_assets(
        con,
        [
            {
                "ticker": "DEAD",
                "active_from": dt.date(2010, 1, 1),
                "active_through": dt.date(2020, 6, 1),
            },
            {"ticker": "ALIVE", "active_from": dt.date(2010, 1, 1)},
        ],
    )
    in_2018 = {
        r[0] for r in con.execute(queries.UNIVERSE_AS_OF, [dt.date(2018, 1, 1)] * 2).fetchall()
    }
    in_2024 = {
        r[0] for r in con.execute(queries.UNIVERSE_AS_OF, [dt.date(2024, 1, 1)] * 2).fetchall()
    }
    assert in_2018 == {"DEAD", "ALIVE"}
    assert in_2024 == {"ALIVE"}


def test_market_events_reingest_is_a_noop(warehouse):
    con, _ = warehouse
    rows = [
        {
            "ticker": "TQQQ",
            "event_timestamp": dt.datetime(2022, 1, 13, 14, 30, tzinfo=dt.UTC),
            "event_type": "split",
            "value": 3.0,
        }
    ]
    ingest.upsert_market_events(con, rows)
    ingest.upsert_market_events(con, rows)
    assert con.execute("SELECT count(*) FROM market_data.market_events").fetchone()[0] == 1


def test_ohlcv_ingest_types_and_partitions(tmp_path, warehouse):
    con, root = warehouse
    csv = _write_csv(_bars(), tmp_path / "TQQQ_1Min.csv")
    report = ingest.ingest_ohlcv_csv(con, root, csv, "TQQQ")
    schema.refresh_views(con, root)

    assert report["rows"] == 200
    assert con.execute("SELECT count(*) FROM market_data.ohlcv").fetchone()[0] == 200

    types = con.execute(
        "SELECT typeof(timestamp), typeof(close), typeof(volume) FROM market_data.ohlcv LIMIT 1"
    ).fetchone()
    # TIMESTAMPTZ on both sides is what makes the ASOF join correct --
    # see the note in queries.py.
    assert types[0] == "TIMESTAMP WITH TIME ZONE"
    assert types[1] == "DOUBLE"

    partitions = {p.name for p in (root / "ohlcv").iterdir()}
    assert partitions == {"ticker=TQQQ"}
    assert {p.name for p in (root / "ohlcv" / "ticker=TQQQ").iterdir()} == {"year=2016"}


def test_ohlcv_is_sorted_on_disk(tmp_path, warehouse):
    """The sort IS the index: row-group zonemaps only prune a
    partition if it was written in timestamp order. Losing the ORDER BY
    would not fail any query, it would just make every ASOF join a full
    scan."""
    con, root = warehouse
    csv = _write_csv(_bars(), tmp_path / "TQQQ_1Min.csv")
    ingest.ingest_ohlcv_csv(con, root, csv, "TQQQ")
    schema.refresh_views(con, root)
    stamps = [r[0] for r in con.execute("SELECT timestamp FROM market_data.ohlcv").fetchall()]
    assert stamps == sorted(stamps)


def test_empty_csv_is_refused(tmp_path, warehouse):
    con, root = warehouse
    empty = tmp_path / "empty.csv"
    empty.write_text("timestamp,open,high,low,close,volume\n", encoding="utf-8")
    with pytest.raises(ValueError, match="zero rows"):
        ingest.ingest_ohlcv_csv(con, root, empty, "TQQQ")


def test_dataset_version_prefers_the_sidecar_sha(tmp_path, warehouse):
    """Identity of the DATA, not of the file. historical_data.py already
    computed this over the exact bytes fetched."""
    csv = _write_csv(_bars(), tmp_path / "TQQQ_1Min.csv")
    csv.with_suffix(".meta.json").write_text('{"sha256": "SIDECAR_VALUE"}', encoding="utf-8")
    assert ingest.dataset_version(csv) == "SIDECAR_VALUE"


def test_dataset_version_falls_back_to_hashing_the_file(tmp_path):
    csv = _write_csv(_bars(), tmp_path / "no_sidecar.csv")
    version = ingest.dataset_version(csv)
    assert len(version) == 64
    assert ingest.dataset_version(csv) == version


# -- Part 2b: the external-series lake ------------------------------


def _external_dir(tmp_path, series: dict[str, dict]) -> Path:
    """Build a minimal data/external/ (CSVs + manifest.json).

    `series` maps series_key -> {provider, category, lag_days, rows:
    [(iso_ts, close[, extra...])], columns: [...]}.
    """
    ext = tmp_path / "external"
    ext.mkdir()
    manifest = {}
    for key, spec in series.items():
        cols = spec["columns"]
        lines = [",".join(cols)]
        for row in spec["rows"]:
            lines.append(",".join(str(v) for v in row))
        (ext / f"{key}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest[key] = {
            "file": f"{key}.csv",
            "provider": spec["provider"],
            "category": spec.get("category"),
            "description": spec.get("description", key),
            "remote_id": key.split("_", 1)[-1],
            "lag_days": spec.get("lag_days", 0.0),
            "columns": cols,
            "first": spec["rows"][0][0],
            "last": spec["rows"][-1][0],
            "rows": len(spec["rows"]),
        }
    import json

    (ext / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return ext


_THREE_PROVIDERS = {
    "fred_DGS10": {
        "provider": "fred",
        "category": "rates",
        "lag_days": 1.0,
        "columns": ["timestamp", "close"],
        "rows": [
            ("2016-01-04 21:00:00+00:00", "2.24"),
            ("2016-06-01 21:00:00+00:00", "1.84"),
        ],
    },
    "cboe_RVX": {
        "provider": "cboe",
        "category": "vol",
        "lag_days": 0.0,
        "columns": ["timestamp", "close", "high", "low"],
        "rows": [
            ("2016-01-04 21:00:00+00:00", "20.1", "21.0", "19.5"),
            ("2016-06-01 21:00:00+00:00", "17.2", "17.9", "16.8"),
        ],
    },
    "yahoo_AGG": {
        "provider": "yahoo",
        "category": "bond",
        "lag_days": 0.0,
        "columns": ["timestamp", "close", "volume"],
        "rows": [
            ("2016-01-04 21:00:00+00:00", "108.5", "1200000"),
            ("2016-06-01 21:00:00+00:00", "110.1", "980000"),
        ],
    },
}


def test_external_ingests_every_provider_and_normalizes_schema(tmp_path, warehouse):
    con, root = warehouse
    ext = _external_dir(tmp_path, _THREE_PROVIDERS)
    report = ingest.ingest_external_series(con, root, ext)
    schema.refresh_views(con, root)

    assert report["series"] == 3
    assert report["rows"] == 6

    # The heterogeneous shapes bind into one view: a FRED close-only
    # series and a CBOE OHLC series read back together, NULLs where a
    # source lacked the column.
    row = con.execute(
        "SELECT count(*) FILTER (WHERE high IS NOT NULL), "
        "       count(*) FILTER (WHERE volume IS NOT NULL), count(*) "
        "FROM market_data.external"
    ).fetchone()
    assert row == (2, 2, 6)

    types = con.execute(
        "SELECT typeof(timestamp), typeof(close), typeof(volume) FROM market_data.external LIMIT 1"
    ).fetchone()
    assert types == ("TIMESTAMP WITH TIME ZONE", "DOUBLE", "DOUBLE")


def test_external_lake_partitioned_by_provider_and_key(tmp_path, warehouse):
    con, root = warehouse
    ingest.ingest_external_series(con, root, _external_dir(tmp_path, _THREE_PROVIDERS))
    providers = {p.name for p in (root / "external").iterdir()}
    assert providers == {"provider=fred", "provider=cboe", "provider=yahoo"}
    fred_keys = {p.name for p in (root / "external" / "provider=fred").iterdir()}
    assert fred_keys == {"series_key=fred_DGS10"}


def test_external_dimension_records_lag_from_the_manifest(tmp_path, warehouse):
    con, root = warehouse
    ingest.ingest_external_series(con, root, _external_dir(tmp_path, _THREE_PROVIDERS))
    lag = dict(
        con.execute("SELECT series_key, lag_days FROM market_data.external_series").fetchall()
    )
    assert lag == {"fred_DGS10": 1.0, "cboe_RVX": 0.0, "yahoo_AGG": 0.0}


def test_external_ingest_without_a_manifest_is_refused(tmp_path, warehouse):
    con, root = warehouse
    (tmp_path / "bare").mkdir()
    with pytest.raises(FileNotFoundError, match="manifest"):
        ingest.ingest_external_series(con, root, tmp_path / "bare")


def test_external_reingest_replaces_rather_than_duplicating(tmp_path, warehouse):
    con, root = warehouse
    ext = _external_dir(tmp_path, _THREE_PROVIDERS)
    ingest.ingest_external_series(con, root, ext)
    ingest.ingest_external_series(con, root, ext)
    schema.refresh_views(con, root)
    assert con.execute("SELECT count(*) FROM market_data.external").fetchone()[0] == 6
    assert con.execute("SELECT count(*) FROM market_data.external_series").fetchone()[0] == 3


def test_external_asof_join_is_lag_aware(tmp_path, warehouse):
    """The point-in-time guarantee. A FRED series with a publication
    lag must not be visible to a bar until that lag has elapsed --
    joining on the raw observation timestamp would leak a macro print
    weeks before it existed."""
    con, root = warehouse
    # DGS10 observed 2016-01-04 21:00 UTC, published 30 days later.
    series = {
        "fred_LAGGED": {
            "provider": "fred",
            "category": "rates",
            "lag_days": 30.0,
            "columns": ["timestamp", "close"],
            "rows": [
                ("2016-01-04 21:00:00+00:00", "2.24"),
                ("2016-03-01 21:00:00+00:00", "1.99"),
            ],
        }
    }
    ingest.ingest_external_series(con, root, _external_dir(tmp_path, series))

    # ~42 days of continuous minute bars from 2016-01-05. The
    # 2016-01-04 observation is not published until 2016-02-03 (+30d),
    # so the first ~30 days of bars must see nothing and the rest must
    # see 2.24.
    csv = _write_csv(_bars(60_000, start="2016-01-05 14:30:00+00:00"), tmp_path / "TQQQ.csv")
    ingest.ingest_ohlcv_csv(con, root, csv, "TQQQ")
    schema.refresh_views(con, root)

    frame = con.execute(queries.EXTERNAL_SERIES_AT_BARS, ["fred_LAGGED", "TQQQ"]).pl()
    matched = frame.filter(frame["series_value"].is_not_null())
    assert matched.height > 0, "nothing matched at all -- the join is broken, not just strict"
    assert matched.height < frame.height, "every bar matched -- the lag was not applied"

    # No matched bar may sit before the value it was handed was published.
    bad = matched.filter(matched["known_at"] > matched["bar_time"]).height
    assert bad == 0

    # And the earliest bar that DOES see a value must be >= 30 days
    # after that value's observation.
    import datetime as _dt

    first = matched.sort("bar_time").row(0, named=True)
    assert first["bar_time"] - first["observed_at"] >= _dt.timedelta(days=30)


def test_external_value_at_matches_at_or_before(tmp_path, warehouse):
    con, root = warehouse
    ingest.ingest_external_series(con, root, _external_dir(tmp_path, _THREE_PROVIDERS))
    schema.refresh_views(con, root)
    # Between the two observations -> the earlier one.
    got = con.execute(
        queries.EXTERNAL_VALUE_AT, ["fred_DGS10", "2016-03-15 00:00:00+00:00"]
    ).fetchone()
    assert got[2] == 2.24
    # Before the first -> nothing.
    assert (
        con.execute(
            queries.EXTERNAL_VALUE_AT, ["fred_DGS10", "2015-01-01 00:00:00+00:00"]
        ).fetchone()
        is None
    )


# -- Part 3: sim_results and the sink --------------------------------


def test_parameter_hash_unique_constraint_is_enforced(warehouse):
    con, _ = warehouse
    ensure_broker_environment(con, "zero", _Cost(), "Zero")
    con.execute("USE sim")
    con.execute(
        "INSERT INTO sweeps (sweep_id, algorithm, base_parameters, broker_id) "
        "VALUES ('s1','grid','{}','zero')"
    )
    con.execute(
        "INSERT INTO simulations (simulation_id, sweep_id, dataset_version, parameters_json, "
        "parameter_hash, status) VALUES ('a','s1','v','{}','SAME','COMPLETED')"
    )
    with pytest.raises(duckdb.ConstraintException):
        con.execute(
            "INSERT INTO simulations (simulation_id, sweep_id, dataset_version, parameters_json, "
            "parameter_hash, status) VALUES ('b','s1','v','{}','SAME','COMPLETED')"
        )


def test_sweep_foreign_key_is_enforced(warehouse):
    con, _ = warehouse
    con.execute("USE sim")
    with pytest.raises(duckdb.ConstraintException):
        con.execute(
            "INSERT INTO sweeps (sweep_id, algorithm, base_parameters, broker_id) "
            "VALUES ('s2','grid','{}','NO_SUCH_BROKER')"
        )


def test_status_enum_rejects_an_unknown_value(warehouse):
    con, _ = warehouse
    ensure_broker_environment(con, "zero", _Cost(), "Zero")
    con.execute("USE sim")
    con.execute(
        "INSERT INTO sweeps (sweep_id, algorithm, base_parameters, broker_id) "
        "VALUES ('s3','grid','{}','zero')"
    )
    with pytest.raises(duckdb.ConversionException):
        con.execute(
            "INSERT INTO simulations (simulation_id, sweep_id, dataset_version, parameters_json, "
            "parameter_hash, status) VALUES ('c','s3','v','{}','H','NOT_A_STATUS')"
        )


def test_split_row_separates_params_from_metrics():
    params, execution, metrics = split_row(
        {
            "Grid Step": 0.01,
            "Profit Target": 0.02,
            "Strategy": "Fixed",
            "allocation_pct": 0.05,
            "fill_model": "close",
            "Sharpe": 1.2,
            "Total Return %": 4.0,
        }
    )
    assert params == {"allocation_pct": 0.05}
    assert execution == {"fill_model": "close"}
    assert metrics == {"Sharpe": 1.2, "Total Return %": 4.0}


def test_unknown_row_key_is_treated_as_a_parameter_not_a_metric():
    """Fails safe in the direction that matters: a NEW strategy
    parameter must never be silently swallowed as a metric, because
    that would collide two genuinely different configurations on one
    parameter_hash."""
    params, _, metrics = split_row({"Grid Step": 0.01, "Profit Target": 0.02, "brand_new_knob": 9})
    assert params == {"brand_new_knob": 9}
    assert metrics == {}


def test_metric_keys_covers_what_the_engine_actually_emits():
    """Guards against the engine adding a metric that this module then
    mistakes for a parameter."""
    from src.analysis.performance_analyzer import PerformanceAnalyzer
    from src.core.ledger import AssetLotLedger

    produced = PerformanceAnalyzer.calculate_metrics(
        AssetLotLedger(), final_portfolio_value=100.0, initial_cash=100.0
    )
    assert set(produced) <= METRIC_KEYS, set(produced) - METRIC_KEYS


def test_blotter_schema_covers_every_column_the_engine_writes():
    """The blotter's columns are fixed by _simulate_single; if one is
    added there and not here it silently never reaches the lake."""
    engine_columns = {
        "timestamp",
        "side",
        "price",
        "qty",
        "equity",
        "lot_id",
        "ticker",
        "bar_index",
        "rsi",
        "sell_reason",
        "profit_realized",
    }
    assert engine_columns <= {name for name, _ in BLOTTER_SCHEMA}


# -- the sink, end to end --------------------------------------------


def _run_sweep_into(con, root, *, dataset_version="v1", steps=(0.01,), targets=(0.02,)):
    from src.optimization.optimization_controller import OptimizationController
    from src.strategies.size_calculators import FixedPortfolioPercentage

    broker_id = ensure_broker_environment(con, "zero", _Cost(), "Zero")
    sink = DuckDBResultSink(con, root, dataset_version=dataset_version)
    sink.open_sweep(
        algorithm="grid",
        base_parameters={"symbol": "TQQQ"},
        broker_id=broker_id,
        dataset_version=dataset_version,
    )
    controller = OptimizationController(historical_data=_bars(400))
    controller.run_sweep(
        grid_steps=list(steps),
        profit_targets=list(targets),
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        symbol="TQQQ",
        initial_cash=100_000.0,
        result_sink=sink,
    )
    sink.close_sweep()
    return sink


def test_sink_records_every_combination(warehouse):
    con, root = warehouse
    sink = _run_sweep_into(con, root, steps=(0.005, 0.01), targets=(0.01, 0.02))
    assert sink.stats["recorded"] == 4
    assert sink.stats["errors"] == 0
    assert con.execute("SELECT count(*) FROM sim.simulations").fetchone()[0] == 4


def test_rerunning_the_same_sweep_is_deduplicated(warehouse):
    con, root = warehouse
    _run_sweep_into(con, root)
    again = _run_sweep_into(con, root)
    assert again.stats["recorded"] == 0
    assert again.stats["skipped_duplicate"] == 1


def test_a_new_data_vintage_is_not_a_duplicate(warehouse):
    """The boundary test for the UNIQUE constraint: the same parameters
    against different data are a different experiment and must be
    storable."""
    con, root = warehouse
    _run_sweep_into(con, root, dataset_version="v1")
    fresh = _run_sweep_into(con, root, dataset_version="v2-longer-history")
    assert fresh.stats["recorded"] == 1
    assert fresh.stats["skipped_duplicate"] == 0


def test_sink_never_raises_on_a_broken_connection(warehouse):
    """Rule 1: losing a multi-hour sweep to a storage fault is worse
    than losing the record."""
    con, root = warehouse
    sink = DuckDBResultSink(con, root, dataset_version="v")
    ensure_broker_environment(con, "zero", _Cost(), "Zero")
    sink.open_sweep(algorithm="grid", base_parameters={}, broker_id="zero", dataset_version="v")
    sink._con = None  # simulate the store going away mid-sweep
    sink.record(
        row={"Grid Step": 0.01, "Profit Target": 0.02, "Strategy": "X"},
        sim_result=None,
        elapsed_ms=1,
    )
    assert sink.stats["errors"] == 1


def test_failed_combination_is_recorded_as_failed(warehouse):
    con, root = warehouse
    ensure_broker_environment(con, "zero", _Cost(), "Zero")
    sink = DuckDBResultSink(con, root, dataset_version="v")
    sink.open_sweep(algorithm="grid", base_parameters={}, broker_id="zero", dataset_version="v")
    sink.record(
        row={"Grid Step": 0.01, "Profit Target": 0.02, "Strategy": "X", "error": "boom"},
        sim_result=None,
        elapsed_ms=7,
    )
    status, trace, sharpe = con.execute(
        "SELECT status, error_trace, sharpe_ratio FROM sim.simulations"
    ).fetchone()
    assert status == "FAILED"
    assert trace == "boom"
    assert sharpe is None


def test_non_finite_metrics_are_stored_as_null_not_crashed(warehouse):
    """Return/Drawdown is legitimately +/-inf on a zero-drawdown run,
    and json.dumps would emit a bare Infinity token that DuckDB's JSON
    type rejects."""
    con, root = warehouse
    ensure_broker_environment(con, "zero", _Cost(), "Zero")
    sink = DuckDBResultSink(con, root, dataset_version="v")
    sink.open_sweep(algorithm="grid", base_parameters={}, broker_id="zero", dataset_version="v")

    class Result:
        trade_blotter = pd.DataFrame()

    sink.record(
        row={
            "Grid Step": 0.01,
            "Profit Target": 0.02,
            "Strategy": "X",
            "Sharpe": float("inf"),
            "Total Return %": 5.0,
            "Return/Drawdown": float("inf"),
        },
        sim_result=Result(),
        elapsed_ms=3,
    )
    assert sink.stats["errors"] == 0
    sharpe, total = con.execute("SELECT sharpe_ratio, total_return FROM sim.simulations").fetchone()
    assert sharpe is None
    assert total == 5.0


# -- Part 4: the ASOF join -------------------------------------------


@pytest.fixture
def populated(tmp_path, warehouse):
    con, root = warehouse
    csv = _write_csv(_bars(400), tmp_path / "TQQQ_1Min.csv")
    ingest.ingest_ohlcv_csv(con, root, csv, "TQQQ")
    _run_sweep_into(con, root, steps=(0.005,), targets=(0.01,))
    schema.refresh_views(con, root)
    sim_id = con.execute(
        "SELECT simulation_id FROM sim.simulations WHERE status='COMPLETED' LIMIT 1"
    ).fetchone()[0]
    return con, root, sim_id


def test_asof_join_matches_a_bar_at_or_before_every_execution(populated):
    con, _, sim_id = populated
    rows = con.execute(queries.EXECUTIONS_AT_MARKET_PRICE, [sim_id]).fetchall()
    assert rows, "the sweep produced no executions to join"
    for row in rows:
        execution_time, bar_time = row[3], row[6]
        assert bar_time is not None, "ASOF LEFT JOIN found no bar at-or-before an execution"
        # The point-in-time guarantee. Flipping the inequality in the
        # query would match the NEXT bar -- lookahead, and silent.
        assert bar_time <= execution_time


def test_asof_join_is_a_left_join(populated):
    """An execution with no prior bar must surface as NULL, not vanish.
    An inner ASOF would understate the trade count while looking
    perfectly healthy."""
    con, root, _sim_id = populated
    before_any_bar = pd.Timestamp("2015-01-01T00:00:00Z")
    con.execute("USE sim")
    total_before = con.execute("SELECT count(*) FROM sim.trade_executions").fetchone()[0]

    import polars as pl

    orphan = pl.DataFrame(  # noqa: F841 -- read by DuckDB below
        {
            "simulation_id": ["orphan"],
            "timestamp": [before_any_bar.to_pydatetime()],
            "side": ["buy"],
            "price": [1.0],
            "qty": [1.0],
            "equity": [1.0],
            "lot_id": ["L0"],
            "ticker": ["TQQQ"],
            "bar_index": [0],
            "rsi": [None],
            "sell_reason": [None],
            "profit_realized": [None],
        },
        schema_overrides={
            "timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
            "rsi": pl.Float64,
            "sell_reason": pl.Utf8,
            "profit_realized": pl.Float64,
        },
    )
    destination = (root / "executions").resolve().as_posix()
    con.execute(
        f"COPY (SELECT * FROM orphan) TO '{destination}' "
        "(FORMAT PARQUET, PARTITION_BY (simulation_id), COMPRESSION ZSTD, APPEND)"
    )
    schema.refresh_views(con, root)

    assert (
        con.execute("SELECT count(*) FROM sim.trade_executions").fetchone()[0] == total_before + 1
    )
    rows = con.execute(queries.EXECUTIONS_AT_MARKET_PRICE, ["orphan"]).fetchall()
    assert len(rows) == 1, "the unmatched execution was dropped -- the join is not a LEFT join"
    assert rows[0][6] is None


def test_slippage_summary_reports_no_unmatched_executions(populated):
    con, _, _ = populated
    for row in con.execute(queries.SLIPPAGE_SUMMARY).fetchall():
        assert row[2] == 0, f"simulation {row[0]} has unmatched executions"


def test_executions_lake_is_partitioned_by_simulation(populated):
    _con, root, sim_id = populated
    partitions = {p.name for p in (root / "executions").iterdir()}
    assert f"simulation_id={sim_id}" in partitions
