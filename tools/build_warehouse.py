#!/usr/bin/env python
"""Build and inspect the DuckDB analytical warehouse.

    python tools/build_warehouse.py --init
    python tools/build_warehouse.py --ingest TQQQ QQQ
    python tools/build_warehouse.py --ingest-all          # bars + events + external
    python tools/build_warehouse.py --external            # macro series only
    python tools/build_warehouse.py --show-settings
    python tools/build_warehouse.py --top 20
    python tools/build_warehouse.py --explain-execution <simulation_id>
    python tools/build_warehouse.py --explain-series fred_DGS10 TQQQ

Writes warehouse/market_data.duckdb, warehouse/sim_results.duckdb and
the Parquet lakes beside them. Everything under warehouse/ is derived
and git-ignored; deleting the directory and re-running this script
rebuilds it from data/.

---

WHY THE HEAVY IMPORTS ARE INSIDE main()

tests/unit/test_tools_are_importable.py imports every tools/*.py and
asserts the import is fast and silent. duckdb and polars are in
requirements-warehouse.txt, NOT requirements.txt, so a developer or CI
job that has not installed them must still be able to import this
module -- otherwise adding an optional-dependency script turns the
whole test suite red on a clean checkout. Deferring the import into
main() is what keeps that true, and is also why this file does no work
at module scope.

---

WHY --ingest TAKES TICKERS AND NOT PATHS

The ticker -> file mapping already exists once, in
tools/export_ui_data.py's KNOWN_DATA, and server/backtest.py imports
it from there. A second copy here would be a second thing to update
when a dataset is re-downloaded under a new date-stamped name. Pass
--csv to ingest a file that is not in that registry.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

DEFAULT_ROOT = _REPO_ROOT / "warehouse"

# Seed rows for the assets dimension. active_from is the fund's actual
# inception, not the first date we happen to hold bars for -- the whole
# point of the column is to describe the instrument rather than our
# data. active_through is None for everything here because all seven
# are still listed; a delisted fund would carry its last trading day,
# and THAT is what keeps it in a historical universe query instead of
# silently vanishing (survivorship bias).
SEED_ASSETS = [
    {
        "ticker": "TQQQ",
        "sector": "Leveraged Equity Index",
        "active_from": dt.date(2010, 2, 9),
        "is_leveraged": True,
        "leverage_ratio": 3.0,
        "notes": "ProShares UltraPro QQQ. 3:1 forward split 2022-01-13.",
    },
    {
        "ticker": "SQQQ",
        "sector": "Inverse Leveraged Equity Index",
        "active_from": dt.date(2010, 2, 9),
        "is_leveraged": True,
        "leverage_ratio": -3.0,
        "notes": "ProShares UltraPro Short QQQ.",
    },
    {
        "ticker": "SOXL",
        "sector": "Leveraged Semiconductors",
        "active_from": dt.date(2010, 3, 11),
        "is_leveraged": True,
        "leverage_ratio": 3.0,
        "notes": "Direxion Daily Semiconductor Bull 3X.",
    },
    {
        "ticker": "QQQ",
        "sector": "Equity Index",
        "active_from": dt.date(1999, 3, 10),
        "is_leveraged": False,
        "leverage_ratio": 1.0,
        "notes": "Invesco QQQ Trust. The unleveraged reference.",
    },
    {
        "ticker": "RSP",
        "sector": "Equity Index (Equal Weight)",
        "active_from": dt.date(2003, 4, 24),
        "is_leveraged": False,
        "leverage_ratio": 1.0,
        "notes": "Invesco S&P 500 Equal Weight.",
    },
    {
        "ticker": "COWZ",
        "sector": "Value / Free Cash Flow",
        "active_from": dt.date(2016, 12, 19),
        "is_leveraged": False,
        "leverage_ratio": 1.0,
        "notes": "Pacer US Cash Cows 100. Inception mid-2016; file starts later than the others.",
    },
    {
        "ticker": "SPYD",
        "sector": "High Dividend Equity",
        "active_from": dt.date(2015, 10, 21),
        "is_leveraged": False,
        "leverage_ratio": 1.0,
        "notes": "SPDR Portfolio S&P 500 High Dividend.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="warehouse directory")
    parser.add_argument("--init", action="store_true", help="create tables, types and views")
    parser.add_argument("--ingest", nargs="*", metavar="TICKER", help="ingest these tickers")
    parser.add_argument("--ingest-all", action="store_true", help="ingest every known ticker")
    parser.add_argument("--csv", type=Path, help="ingest this file (requires a single --ingest)")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace existing partitions rather than appending to them",
    )
    parser.add_argument("--events", action="store_true", help="load the earnings calendar")
    parser.add_argument(
        "--external",
        action="store_true",
        help="ingest data/external/ (FRED/CBOE/Yahoo macro series) into the external lake",
    )
    parser.add_argument("--show-settings", action="store_true", help="print tuning + row counts")
    parser.add_argument("--top", type=int, metavar="N", help="print the top N simulations")
    parser.add_argument(
        "--explain-execution",
        metavar="SIMULATION_ID",
        help="run the ASOF join for one simulation and print the first rows",
    )
    parser.add_argument(
        "--explain-series",
        nargs=2,
        metavar=("SERIES_KEY", "TICKER"),
        help="lag-aware ASOF join of one external series onto a ticker's bars",
    )
    parser.add_argument("--slippage", action="store_true", help="per-simulation slippage summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Deferred -- see the module docstring.
    #
    # duckdb and polars are probed DIRECTLY rather than relying on the
    # src.warehouse import to raise. That package imports its own
    # dependencies lazily (so that `import src.warehouse` stays cheap),
    # which means importing it succeeds on a machine that has neither,
    # and the real ImportError would otherwise surface several frames
    # later as a traceback out of open_warehouse instead of the
    # actionable message below.
    try:
        import duckdb  # noqa: F401
        import polars  # noqa: F401

        from src.warehouse import ingest, queries, schema
        from src.warehouse.connection import open_warehouse
    except ImportError as e:
        print(
            f"The warehouse needs its optional dependencies: {e}\n"
            "  pip install -r requirements-warehouse.txt",
            file=sys.stderr,
        )
        return 2

    from tools.export_ui_data import KNOWN_DATA

    did_something = False
    con = open_warehouse(args.root)

    if args.init or args.ingest or args.ingest_all or args.events or args.external:
        schema.initialize(con, args.root)
        ingest.upsert_assets(con, SEED_ASSETS)
        print(f"Schema ready at {args.root} ({len(SEED_ASSETS)} assets seeded).")
        did_something = True

    tickers = list(args.ingest or [])
    if args.ingest_all:
        tickers = sorted(KNOWN_DATA)
    if args.csv and len(tickers) != 1:
        parser.error("--csv requires exactly one --ingest TICKER to name it")

    for ticker in tickers:
        source = args.csv if args.csv else Path(KNOWN_DATA.get(ticker, ""))
        if not source or not Path(source).exists():
            print(f"SKIP {ticker}: no bar file at {source or '<unknown ticker>'}")
            continue
        print(f"{ticker:<6} ingesting {source} ... ", end="", flush=True)
        report = ingest.ingest_ohlcv_csv(con, args.root, source, ticker, overwrite=args.overwrite)
        print(
            f"{report['rows']:,} bars, {report['years'][0]}-{report['years'][-1]}, "
            f"dataset_version={report['dataset_version'][:12]}"
        )
        # Suspect bars are this project's only corporate-actions signal.
        meta = Path(str(source)).with_suffix(".meta.json")
        events = ingest.suspect_bar_events(meta, ticker)
        if events:
            ingest.upsert_market_events(con, events)
            print(f"       {len(events)} split candidate(s) from the sidecar's suspect_bars")
        did_something = True

    if args.events:
        earnings = _REPO_ROOT / "data" / "earnings_releases_derived.csv"
        if earnings.exists():
            rows = ingest.earnings_events_from_csv(earnings)
            print(f"Loaded {ingest.upsert_market_events(con, rows)} earnings events.")
        else:
            print(f"SKIP events: {earnings} not found (run tools/build_earnings_calendar.py).")
        did_something = True

    if args.external or args.ingest_all:
        external_dir = _REPO_ROOT / "data" / "external"
        if (external_dir / "manifest.json").exists():
            report = ingest.ingest_external_series(con, args.root, external_dir)
            print(
                f"Loaded {report['series']} external series ({report['rows']:,} rows"
                + (f", {len(report['skipped'])} skipped" if report["skipped"] else "")
                + ")."
            )
        else:
            print(
                f"SKIP external: {external_dir / 'manifest.json'} not found "
                "(run tools/fetch_market_inputs.py)."
            )
        did_something = True

    if tickers or args.events or args.external or args.ingest_all or args.init:
        created = schema.refresh_views(con, args.root)
        print(
            "Views: " + ", ".join(f"{k}={'ok' if v else 'no data yet'}" for k, v in created.items())
        )

    if args.show_settings:
        _print_status(con, args.root)
        did_something = True

    if args.top:
        print(queries.top_simulations(con, args.top))
        did_something = True

    if args.explain_execution:
        frame = queries.executions_at_market_price(con, args.explain_execution)
        if frame.is_empty():
            print(f"No executions recorded for simulation {args.explain_execution}.")
        else:
            print(frame.head(25))
            unmatched = frame.filter(frame["bar_time"].is_null()).height
            print(f"\n{frame.height} execution(s); {unmatched} with no bar at-or-before them.")
        did_something = True

    if args.explain_series:
        series_key, ticker = args.explain_series
        frame = queries.external_series_at_bars(con, series_key, ticker)
        if frame.is_empty():
            print(f"No {ticker} bars found (or series {series_key!r} is unknown).")
        else:
            print(frame.head(25))
            unmatched = frame.filter(frame["series_value"].is_null()).height
            print(
                f"\n{frame.height:,} {ticker} bar(s); {unmatched:,} before {series_key} "
                "had published any value."
            )
        did_something = True

    if args.slippage:
        print(queries.slippage_summary(con))
        did_something = True

    con.close()
    if not did_something:
        parser.print_help()
        return 1
    return 0


def _print_status(con, root: Path) -> None:
    settings = con.execute(
        "SELECT name, value FROM duckdb_settings() "
        "WHERE name IN ('threads','memory_limit','TimeZone','temp_directory') ORDER BY name"
    ).fetchall()
    print(f"\nWarehouse: {root}")
    for name, value in settings:
        print(f"  {name:<16} {value}")

    print("\nRow counts:")
    for label, sql in (
        ("assets", "SELECT count(*) FROM market_data.assets"),
        ("market_events", "SELECT count(*) FROM market_data.market_events"),
        ("external_series", "SELECT count(*) FROM market_data.external_series"),
        ("broker_environments", "SELECT count(*) FROM sim.broker_environments"),
        ("sweeps", "SELECT count(*) FROM sim.sweeps"),
        ("simulations", "SELECT count(*) FROM sim.simulations"),
        ("ohlcv (view)", "SELECT count(*) FROM market_data.ohlcv"),
        ("external (view)", "SELECT count(*) FROM market_data.external"),
        ("trade_executions (view)", "SELECT count(*) FROM sim.trade_executions"),
    ):
        try:
            print(f"  {label:<26} {con.execute(sql).fetchone()[0]:,}")
        except Exception as e:
            print(f"  {label:<26} - ({type(e).__name__})")


if __name__ == "__main__":
    sys.exit(main())
