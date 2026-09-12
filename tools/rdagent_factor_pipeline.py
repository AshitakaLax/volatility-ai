#!/usr/bin/env python
"""Run RD-Agent's factor mining against THIS project's ETFs, and funnel
what it finds into the evaluation gate that already exists here.

    python tools/rdagent_factor_pipeline.py export-qlib --tickers URSP XBI COWZ
    python tools/rdagent_factor_pipeline.py scaffold    --tickers URSP XBI COWZ
    # ... run the rdagent CLI (scaffold prints the exact command) ...
    python tools/rdagent_factor_pipeline.py ingest --ticker XBI \
        --workspace ~/.rdagent/log/factor_xbi --out data/ml

--------------------------------------------------------------------
READ THIS BEFORE SPENDING MONEY ON IT

RD-Agent is an LLM-driven research loop. It proposes a factor, writes
the code, runs a backtest in a Docker sandbox, reads the result, and
iterates. Three consequences follow, and none of them are incidental:

1. IT COSTS REAL API SPEND PER LOOP, and the loop is the product. A
   session that produces a handful of surviving factors is hours of
   wall time and a non-trivial LLM bill. Budget it as an experiment,
   not as a build step.

2. ITS NATIVE SHAPE IS CROSS-SECTIONAL, AND THIS PROJECT IS NOT.
   fin_factor's scenario ranks MANY instruments on one date -- that is
   what an Alpha158-style factor is FOR, and what its IC/ICIR scoring
   measures. This project trades ONE ETF at a time through a grid;
   there is no cross-section to rank. A factor with a beautiful
   cross-sectional IC can be worthless as a time-series signal on a
   single symbol, and RD-Agent will not tell you that, because it is
   not the question it was asked.

   The reframe this script implements: mine over a UNIVERSE (a basket
   of liquid ETFs, or a fund's own constituents), then keep the factor
   EXPRESSIONS and evaluate them as time-series features on the one
   symbol actually being traded. That is a legitimate use of the tool
   and it is not the use the tool advertises, so the mined score is a
   candidate filter, never a result.

3. IT IS A MACHINE FOR GENERATING PLAUSIBLE OVERFITS. An LLM proposing
   factors against a scored backtest is, mechanically, a search over
   hypothesis space with the test set in the loop. This project already
   knows what that costs -- tools/probe_regime_signals.py's own
   docstring calls searching for an indicator that "works in 2022"
   close to the definition of curve-fitting, with a sample size of one.
   Nothing RD-Agent emits is evidence until it has been through the
   SAME gate every other feature here went through.

--------------------------------------------------------------------
WHICH IS WHY THIS SCRIPT'S REAL JOB IS `ingest`

export-qlib and scaffold are plumbing: they get this project's bars
into the format RD-Agent's qlib scenario expects, and write a config
pointing at the right universe. Useful, mechanical, uninteresting.

`ingest` is the part that matters. It merges mined factor columns into
data/ml/{ticker}_ml.parquet -- the dataset tools/evaluate_ml_features.py
and tools/ablate_ml_features.py already read -- tagged as their own
block. That means a mined factor is graded by the paired, purged
walk-forward those tools implement, per block, against the bar-only
baseline, exactly as the vol/rates/labour/fx/curve blocks were. The
ablation table in ml_plan.md is the format the answer comes back in.

The gate is deliberately not reimplemented here. It exists, it is
harsher than RD-Agent's own scoring, and routing through it is the
whole point.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# The universe mined over. Deliberately wider than the funds actually
# traded: a cross-sectional scenario needs a cross-section, and mining
# over three symbols would produce factors fitted to three symbols.
DEFAULT_UNIVERSE = [
    "SPY",
    "QQQ",
    "IWM",
    "RSP",
    "URSP",
    "XBI",
    "COWZ",
    "SPYD",
    "XLF",
    "XLE",
    "XLK",
    "XLV",
    "XLI",
    "XLP",
    "XLU",
    "XLY",
    "XLB",
    "XLRE",
    "IBB",
    "ARKG",
    "GLD",
    "TLT",
    "HYG",
    "EFA",
    "EEM",
]

FACTOR_BLOCK = "rdagent"


def _bars_path(ticker: str, data_dir: Path) -> Path | None:
    for candidate in (
        data_dir / f"{ticker}_1min.csv",
        data_dir / f"{ticker}_daily.csv",
        data_dir / f"{ticker}.csv",
    ):
        if candidate.exists():
            return candidate
    return None


def cmd_export_qlib(args: argparse.Namespace) -> int:
    """CSV bars -> qlib's binary layout, which its scenarios require.

    qlib does not read a directory of CSVs at runtime; it reads a .bin
    calendar/instruments/features tree produced by its own dump_bin
    script. This shells out to that script rather than reimplementing
    the format, because the format is qlib's to change and a
    hand-rolled writer would break silently on their next release.
    """
    data_dir = Path(args.data)
    staging = Path(args.staging)
    staging.mkdir(parents=True, exist_ok=True)

    exported, missing = [], []
    for ticker in args.tickers:
        source = _bars_path(ticker, data_dir)
        if source is None:
            missing.append(ticker)
            continue
        frame = pd.read_csv(source, parse_dates=["timestamp"]).set_index("timestamp")
        # Daily, because every scenario here is a daily-horizon
        # question and a minute .bin tree for 25 symbols is enormous
        # for no gain.
        agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
        available = {k: v for k, v in agg.items() if k in frame.columns}
        daily = frame.resample("1D").agg(available).dropna(subset=["close"])
        if "volume" in frame.columns:
            daily["volume"] = frame["volume"].resample("1D").sum()
        # qlib's dump_bin expects a `date` column and lowercase fields.
        daily.index.name = "date"
        daily.reset_index().to_csv(staging / f"{ticker}.csv", index=False)
        exported.append(ticker)

    if missing:
        print(f"  ! no bars found for: {', '.join(missing)} under {data_dir}", file=sys.stderr)
    if not exported:
        print("nothing exported", file=sys.stderr)
        return 1

    dump_bin = Path(args.dump_bin).expanduser()
    if not dump_bin.exists():
        print(
            f"\nStaged {len(exported)} csv(s) in {staging}, but qlib's dump_bin.py was not found "
            f"at {dump_bin}.\nClone it and re-run with --dump-bin:\n"
            "  git clone https://github.com/microsoft/qlib.git\n"
            "  python tools/rdagent_factor_pipeline.py export-qlib "
            "--dump-bin qlib/scripts/dump_bin.py",
            file=sys.stderr,
        )
        return 1

    target = Path(args.qlib_dir).expanduser()
    result = subprocess.run(
        [
            sys.executable,
            str(dump_bin),
            "dump_all",
            "--csv_path",
            str(staging),
            "--qlib_dir",
            str(target),
            "--include_fields",
            "open,high,low,close,volume",
            "--date_field_name",
            "date",
        ],
        check=False,
    )
    if result.returncode != 0:
        return result.returncode
    print(f"\n{len(exported)} symbols -> {target}")
    return 0


SCENARIO_TEMPLATE = """\
# RD-Agent qlib factor scenario, pointed at this project's ETF universe
# instead of the CSI300 default.
#
# GENERATED by tools/rdagent_factor_pipeline.py scaffold -- edit the
# generator, not this file, or the next scaffold overwrites you.
#
# The keys below track RD-Agent's qlib factor template. That template
# moves between releases: if `rdagent fin_factor` rejects this file,
# diff it against the template shipped in your installed version
# (rdagent/scenarios/qlib/experiment/factor_template/) rather than
# guessing -- the field NAMES change more often than the structure.

qlib_init:
    provider_uri: "{qlib_dir}"
    region: us

market: &market {market_name}
benchmark: &benchmark SPY

data_handler_config: &data_handler_config
    start_time: {start_time}
    end_time: {end_time}
    fit_start_time: {start_time}
    fit_end_time: {fit_end_time}
    instruments: *market

port_analysis_config: &port_analysis_config
    strategy:
        class: TopkDropoutStrategy
        module_path: qlib.contrib.strategy
        kwargs:
            signal: <PRED>
            # Small universe: topk must stay a meaningful fraction of
            # it. The CSI300 default (50/5) against ~25 symbols would
            # hold most of the universe and measure nothing.
            topk: 5
            n_drop: 1
    backtest:
        start_time: {fit_end_time}
        end_time: {end_time}
        account: 100000
        benchmark: *benchmark
        exchange_kwargs:
            limit_threshold: null       # US ETFs have no limit-up/down
            deal_price: close
            open_cost: 0.0000           # see the note in scaffold's output
            close_cost: 0.0000
            min_cost: 0

task:
    model:
        class: LGBModel
        module_path: qlib.contrib.model.gbdt
        kwargs:
            loss: mse
            learning_rate: 0.03
            num_leaves: 31
            max_depth: 6
            num_threads: 8
    dataset:
        class: DatasetH
        module_path: qlib.data.dataset
        kwargs:
            handler:
                class: Alpha158
                module_path: qlib.contrib.data.handler
                kwargs: *data_handler_config
            segments:
                train: [{start_time}, {train_end}]
                valid: [{valid_start}, {fit_end_time}]
                test: [{fit_end_time}, {end_time}]
"""

ENV_TEMPLATE = """\
# RD-Agent LLM configuration. NEVER COMMIT THIS FILE.
#
# This project already has a secrets discipline (src/core/secrets.py,
# .env chmod 600, gitignored) -- hold to it here. An LLM key with a
# billing account attached is a credential in exactly the sense
# docs/DEPLOY_RASPBERRY_PI.md means it.

CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=<your key>

# Or an Anthropic model through RD-Agent's LiteLLM backend:
# BACKEND=rdagent.oai.backend.LiteLLMAPIBackend
# CHAT_MODEL=claude-sonnet-5
# ANTHROPIC_API_KEY=<your key>

# Cap the loop. Without this it runs until you stop it, and the bill
# tracks the loop count.
FACTOR_CoSTEER_max_loop=10
"""


def cmd_scaffold(args: argparse.Namespace) -> int:
    """Write the scenario config and .env template, print the CLI."""
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    universe = args.universe or DEFAULT_UNIVERSE
    market_file = out / "etf_universe.txt"
    market_file.write_text("\n".join(universe) + "\n")

    config = SCENARIO_TEMPLATE.format(
        qlib_dir=Path(args.qlib_dir).expanduser().as_posix(),
        market_name="etf_universe",
        start_time=args.start,
        end_time=args.end,
        train_end=args.train_end,
        valid_start=args.valid_start,
        fit_end_time=args.cutoff,
    )
    config_path = out / "qlib_etf_factor.yaml"
    config_path.write_text(config)

    env_path = out / "env.template"
    env_path.write_text(ENV_TEMPLATE)

    print(f"""
Wrote:
  {config_path}     scenario config
  {market_file}     the mining universe ({len(universe)} symbols)
  {env_path}        LLM config template -- copy to .env and fill in

Next:

  1. cp {env_path} .env && chmod 600 .env && $EDITOR .env
  2. docker info >/dev/null     # RD-Agent runs experiments in a sandbox
  3. rdagent fin_factor --conf_path {config_path}

     Volatility-clustering and mean-reversion factors are what the
     hypothesis prompt should steer toward. RD-Agent takes that
     steer through its scenario description, so if the loop drifts
     into momentum, say so explicitly in the scenario prompt rather
     than hoping.

  4. rdagent fin_quant --conf_path {config_path}
     Joint factor+model evolution. Run it AFTER fin_factor has
     produced something worth modelling, not instead of it.

  5. rdagent ui --port 19899 --log_dir ~/.rdagent/log/
     Read what it actually tried. The loop's rejected hypotheses are
     more informative than its accepted ones.

  6. python tools/rdagent_factor_pipeline.py ingest --ticker XBI \\
         --workspace <the run's workspace dir> --out data/ml
     Then grade it:
       python tools/ablate_ml_features.py --tickers XBI --data data/ml

COSTS ARE ZEROED IN THAT CONFIG ON PURPOSE, and it is a trap worth
naming. RD-Agent's backtest is being used here as a FACTOR SCREEN, and
charging a cross-sectional TopkDropout rotation this project's real
costs would mix "is this factor informative" with "does a 5-name
rotation survive fees" -- two questions, one number. The costs that
matter are charged where the money is: src/analysis/cost_models.py, in
the grid backtest, on the strategy actually traded.
""")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge mined factor columns into this project's ML dataset.

    RD-Agent writes each surviving factor's values as an HDF5/parquet
    in its workspace. Column layout varies by version and by what the
    LLM wrote, so this is deliberately forgiving about shape and strict
    about two things it will not guess at: the index must be dated, and
    a merged column must not collide with an existing feature name.
    """
    workspace = Path(args.workspace).expanduser()
    if not workspace.exists():
        print(f"{workspace} not found", file=sys.stderr)
        return 1

    frames = []
    for path in sorted(workspace.rglob("*")):
        if path.suffix not in {".h5", ".hdf5", ".parquet"}:
            continue
        try:
            frame = pd.read_hdf(path) if path.suffix in {".h5", ".hdf5"} else pd.read_parquet(path)
        except Exception as exc:
            print(f"  ! skipped {path.name}: {exc}", file=sys.stderr)
            continue
        if isinstance(frame, pd.Series):
            frame = frame.to_frame()
        if isinstance(frame.index, pd.MultiIndex):
            # (datetime, instrument) -- the cross-sectional layout. Take
            # only the traded symbol's rows; the rest of the universe
            # was scaffolding for the mining, not data about this fund.
            names = [n.lower() if n else "" for n in frame.index.names]
            if "instrument" in names:
                level = names.index("instrument")
                available = set(frame.index.get_level_values(level))
                if args.ticker not in available:
                    print(f"  ! {path.name}: no rows for {args.ticker}", file=sys.stderr)
                    continue
                frame = frame.xs(args.ticker, level=level)
        frame.index = pd.to_datetime(frame.index)
        frames.append(frame.add_prefix(f"{FACTOR_BLOCK}_"))
        print(f"  + {path.name}: {frame.shape[1]} column(s), {len(frame)} rows")

    if not frames:
        print("no factor files found in the workspace", file=sys.stderr)
        return 1

    factors = pd.concat(frames, axis=1)
    factors = factors.loc[:, ~factors.columns.duplicated()]

    dataset_path = Path(args.out) / f"{args.ticker}_ml.parquet"
    if not dataset_path.exists():
        print(
            f"{dataset_path} not found. Build the base dataset first:\n"
            f"  python tools/build_ml_dataset.py --tickers {args.ticker} --out {args.out}",
            file=sys.stderr,
        )
        return 1

    dataset = pd.read_parquet(dataset_path)
    collisions = set(factors.columns) & set(dataset.columns)
    if collisions:
        print(f"  ! refusing to overwrite existing columns: {sorted(collisions)}", file=sys.stderr)
        return 1

    backup = dataset_path.with_suffix(".parquet.bak")
    shutil.copy2(dataset_path, backup)

    # LAGGED BY ONE SESSION BEFORE THE JOIN. A mined factor's value is
    # computed from a session's own close, so joining it onto that same
    # session's row would let a model see a close it is being asked to
    # predict from. This is the identical hazard src/warehouse/queries.py
    # applies publication lags for, and the one src/CLAUDE.md's
    # causal-transform rule calls out as failing silently.
    factors = factors.shift(1)

    merged = dataset.join(factors, how="left")
    merged.to_parquet(dataset_path, index=True)

    manifest = Path(args.out) / f"{args.ticker}_rdagent_factors.json"
    manifest.write_text(
        json.dumps(
            {
                "ticker": args.ticker,
                "workspace": str(workspace),
                "block": FACTOR_BLOCK,
                "columns": sorted(factors.columns),
                "rows_matched": int(merged[sorted(factors.columns)[0]].notna().sum()),
                "lagged_sessions": 1,
            },
            indent=2,
        )
    )

    print(f"""
{len(factors.columns)} factor column(s) merged into {dataset_path}
  backup:   {backup}
  manifest: {manifest}

NOW GRADE THEM. Nothing above is evidence:

  python tools/evaluate_ml_features.py --tickers {args.ticker} --data {args.out}
  python tools/ablate_ml_features.py   --tickers {args.ticker} --data {args.out}

The '{FACTOR_BLOCK}' block competes on the same terms as vol/rates/
labour/fx/curve did. ml_plan.md's own summary of that exercise -- one
hit in six comparisons, and the winner worth +0.046 AUC -- is the prior
to beat, and the base rate to expect.
""")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    export = sub.add_parser("export-qlib", help="this project's bars -> qlib .bin")
    export.add_argument("--tickers", nargs="+", default=DEFAULT_UNIVERSE)
    export.add_argument("--data", default="data")
    export.add_argument("--staging", default="data/qlib_staging")
    export.add_argument("--qlib-dir", default="~/.qlib/qlib_data/us_etf")
    export.add_argument("--dump-bin", default="qlib/scripts/dump_bin.py")
    export.set_defaults(func=cmd_export_qlib)

    scaffold = sub.add_parser("scaffold", help="write the RD-Agent scenario config")
    scaffold.add_argument("--universe", nargs="+", default=None)
    scaffold.add_argument("--out", default="config/rdagent")
    scaffold.add_argument("--qlib-dir", default="~/.qlib/qlib_data/us_etf")
    scaffold.add_argument("--start", default="2015-01-01")
    scaffold.add_argument("--train-end", default="2021-12-31")
    scaffold.add_argument("--valid-start", default="2022-01-01")
    scaffold.add_argument("--cutoff", default="2024-01-01")
    scaffold.add_argument("--end", default="2026-01-01")
    scaffold.set_defaults(func=cmd_scaffold)

    ingest = sub.add_parser("ingest", help="merge mined factors into data/ml/{ticker}_ml.parquet")
    ingest.add_argument("--ticker", required=True)
    ingest.add_argument("--workspace", required=True)
    ingest.add_argument("--out", default="data/ml")
    ingest.set_defaults(func=cmd_ingest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
