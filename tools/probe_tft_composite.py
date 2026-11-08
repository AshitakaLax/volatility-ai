#!/usr/bin/env python
"""
The TFT in buy x sell compositions, on the bars it was never trained on.

    python cli.py train --config config/ml/tft_tqqq.yaml          # and the other three
    python tools/precompute_tft_forecasts.py --model data/ml/models/tft_tqqq   # each model
    python tools/probe_tft_composite.py --dry-run
    python tools/probe_tft_composite.py --out output/tft_composite --jobs 40
    python tools/probe_tft_composite.py --report output/tft_composite

For each fund, every buy policy below with every sell policy, as `composed`
strategies through OptimizationController.run_sweep, from the models'
valid_from (2024-01-01) to the latest bar. The models train on everything
before it, so every cell -- with a TFT or without -- is judged on the same
out-of-sample window:

  buys    base           the fund's base config's own buying: paper_aggressive's
                         hf_local_reference on TQQQ, the live RSP profile's
                         hf_entry_gated on RSP (config/hf_entry_gated_rsp.yaml)
          tft  <model>   ml_tft from each model, at three per-trade caps (CAPS):
                         the committed 5% of equity, and two nearer the base's
                         own lot size, so a result is not just more exposure
          null <model>   the CONTROL (null_take_profit is the sell's): ml_tft from the price-only model's
                         table with every forecast replaced by the model's
                         average one (`--build-null`). The same trigger,
                         caps, drawdown decay and intrabar effect; none of
                         the model's bar-to-bar information. A TFT cell
                         that does not beat its null did not use the TFT.
          ultimate       the reference book (config/ultimate_tqqq.yaml /
                         ultimate_rsp.yaml), at its own grid
  sells   the sell-policy library's no-loss policies, tft_take_profit from each
          model (the TFT as the SELL model), regime_exit, and the reference
          book's own exit

Each fund's models are `<--models>/tft_<fund>` (price only) and
`tft_<fund>_inputs` (with the outside series, tools/build_tft_inputs.py); a
model absent there is left out. Every TFT run reads the model's forecast
table (`forecasts.npz`, tools/precompute_tft_forecasts.py), which makes it
quick and changes nothing (research/ml/tft_cache.py).

Fills are causal intrabar (never the exact trigger level), costs dynamic
slippage, $100,000; a loss-capable sell opens execution.allow_signal_exit
for its own cells only. The Ultimate family is warmed on the sessions before
the window (run_sweep's warm_up_daily), so it does not spend the window's
first year blind. Rank by Calmar and total return; buy-and-hold over the
same window is the bar every cell is set against.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

START = "2024-01-01"
CAPS = (0.001, 0.005, 0.05)
MIN_GAIN = 0.002
TFT_CHECK_BARS = 15
INITIAL_CASH = 100_000.0
METRICS = (
    "Total Return %",
    "CAGR %",
    "Max Drawdown %",
    "Sharpe",
    "Trade Count",
    "Closed Trade Count",
    "Open Trade Count",
    "Signal Exit Count",
    "Stuck Capital Value",
    "Final Equity",
)

FUNDS: dict[str, dict[str, Any]] = {
    "TQQQ": {
        "base": "config/paper_aggressive.yaml",
        "reference": ("config/ultimate_tqqq.yaml", "ultimate", "ultimate_exit"),
        "bars_per_day": 387,
    },
    "RSP": {
        "base": "config/hf_entry_gated_rsp.yaml",
        "reference": ("config/ultimate_rsp.yaml", "ultimate_rsp", "rsp_rebalance"),
        "bars_per_day": 390,
    },
}

# The no-loss library at its committed defaults, and the NATR regime exit.
LIBRARY_SELLS: tuple[tuple[str, str, dict], ...] = (
    ("fixed_target", "fixed_target", {}),
    ("trailing", "trailing", {"trail_pct": 0.01, "min_profit_target": 0.001}),
    ("age_decay", "age_decay", {}),
    ("vol_scaled_target", "vol_scaled_target", {}),
    ("scale_out", "scale_out", {}),
    ("signal_take_profit", "signal_take_profit", {"signal": "zscore", "min_gain": MIN_GAIN}),
    ("regime_exit", "regime_exit", {}),
)


def _yaml(path: str) -> dict:
    return yaml.safe_load((_REPO_ROOT / path).read_text()) or {}


def models_for(fund: str, models_dir: Path) -> list[tuple[str, Path, Path]]:
    """(label, model dir, forecast table) of each trained model of the fund."""
    out = []
    for suffix in ("", "_inputs"):
        directory = models_dir / f"tft_{fund.lower()}{suffix}"
        table = directory / "forecasts.npz"
        if (directory / "manifest.json").exists() and table.exists():
            out.append((f"tft{suffix}", directory, table))
    return out


def build_null(fund: str, directory: Path) -> Path:
    """`forecasts_null.npz` beside the model's table: each forecast replaced
    by the bar's origin (the encoder's last log close) plus the model's
    AVERAGE return quantiles over the window -- what the sizer would see
    if the model knew only the window's mean and spread."""
    import numpy as np

    from research.ml import tft_cache
    from research.ml.tft_model import CHECKPOINT, read_manifest

    manifest = read_manifest(directory)
    bars, _ = _window(fund)
    rows, _ = tft_cache.frame_rows(bars, manifest)
    L = int(manifest["encoder_length"])
    with np.load(directory / "forecasts.npz", allow_pickle=False) as data:
        keys, values = data["keys"], data["values"]
        first_bar = data["first_bar"]
    origins = rows[L - 1 : len(rows) - 1, 0]
    if len(origins) != len(keys):
        raise SystemExit(
            f"{directory}: the table is not this window's ({len(keys)} vs {len(origins)})"
        )
    offsets = values[:, -1, :] - origins[:, None]
    null = np.broadcast_to(origins[:, None, None] + offsets.mean(axis=0), values.shape).copy()
    out = directory / "forecasts_null.npz"
    np.savez(
        out,
        keys=keys,
        values=null,
        checkpoint=np.array(manifest["files"][CHECKPOINT]),
        first_bar=first_bar,
    )
    print(f"{out}: mean horizon return quantiles {offsets.mean(axis=0)}")
    return out


def _sections(base: dict) -> dict:
    """The base config less its strategy, grid and live block, on the window
    with causal fills."""
    config = {k: copy.deepcopy(v) for k, v in base.items() if k not in ("strategy", "grid", "live")}
    config.pop("search", None)
    config["backtest"] = {**config.get("backtest", {}), "initial_cash": INITIAL_CASH}
    config["backtest"].pop("start_date", None)
    config["execution"] = {**config.get("execution", {}), "intrabar_fill": "causal"}
    config["output"] = {"return_full_results": False}
    return config


def _split(entry_id: str, params: dict) -> dict:
    from research.composition import entries

    selling = entries.sell_params(entry_id)
    return {k: v for k, v in params.items() if k not in selling}


def _accepted(exit_id: str, params: dict) -> dict:
    """The reference book's parameters its exit takes (its regime's)."""
    import inspect

    from research.composition import exits

    signature = inspect.signature(exits.resolve_exit(exit_id).__init__).parameters
    return {k: v for k, v in params.items() if k in signature}


def plan(models_dir: Path, funds=tuple(FUNDS)) -> list[dict]:
    """Every cell of every fund, as a spec run_one runs."""
    from research.composition import exits

    specs = []
    for fund in funds:
        info = FUNDS[fund]
        base = _yaml(info["base"])
        ref_path, ref_buy, ref_sell = info["reference"]
        ref = _yaml(ref_path)
        per_day = info["bars_per_day"]
        grid = (base["grid"]["steps"][0], base["grid"]["profit_targets"][0])
        ref_grid = (ref["grid"]["steps"][0], ref["grid"]["profit_targets"][0])
        models = models_for(fund, models_dir)

        buys = [
            (
                "base",
                {
                    "id": base["strategy"]["strategy_id"],
                    "params": base["strategy"]["strategy_params"],
                },
                grid,
            )
        ]
        for label, directory, table in models:
            for cap in CAPS:
                params = {
                    "bars_per_day": per_day,
                    "model": str(directory),
                    "forecast_cache": str(table),
                    "max_trade_pct": cap,
                    "kelly_scale": 0.5,
                    "sigma_floor": 0.0001,
                    "dd_decay": 3.0,
                    "duration_decay": 0.01,
                    "refresh_bars": 1,
                    "lookback_days": 0.02,
                }
                buys.append((f"{label} cap{cap:g}", {"id": "ml_tft", "params": params}, grid))
        null = models_dir / f"tft_{fund.lower()}"
        if (null / "forecasts_null.npz").exists():
            for cap in CAPS:
                params = {
                    **buys[1][1]["params"],
                    "model": str(null),
                    "forecast_cache": str(null / "forecasts_null.npz"),
                    "max_trade_pct": cap,
                }
                buys.append((f"null cap{cap:g}", {"id": "ml_tft", "params": params}, grid))
        ref_params = ref["strategy"]["strategy_params"]
        buys.append(("ultimate", {"id": ref_buy, "params": _split(ref_buy, ref_params)}, ref_grid))

        sells = [(label, {"id": sid, "params": p}) for label, sid, p in LIBRARY_SELLS]
        for label, directory, table in models:
            sells.append(
                (
                    f"{label}_take_profit",
                    {
                        "id": "tft_take_profit",
                        "params": {
                            "model": str(directory),
                            "forecast_cache": str(table),
                            "bars_per_day": per_day,
                            "min_gain": MIN_GAIN,
                            "check_bars": TFT_CHECK_BARS,
                        },
                    },
                )
            )
        if (null / "forecasts_null.npz").exists():
            # The sell's control: tft_take_profit reading the null table, which
            # turns "bearish" whenever the price is above its last close by more
            # than the window's mean return -- a naive sell-into-strength rule.
            params = {**sells[-1][1]["params"], "model": str(null)}
            params["forecast_cache"] = str(null / "forecasts_null.npz")
            sells.append(("null_take_profit", {"id": "tft_take_profit", "params": params}))
        sells.append((ref_sell, {"id": ref_sell, "params": _accepted(ref_sell, ref_params)}))

        sections = _sections(base)
        for buy_label, buy, (step, target) in buys:
            for sell_label, sell in sells:
                loss = bool(exits.resolve_exit(sell["id"]).can_realize_loss)
                config = copy.deepcopy(sections)
                config["backtest"]["symbol"] = fund
                config["execution"]["allow_signal_exit"] = loss
                config["strategy"] = {
                    "strategy_id": "composed",
                    "strategy_params": {"buy": buy, "sell": sell},
                }
                config["grid"] = {"steps": [step], "profit_targets": [target]}
                specs.append(
                    {
                        "name": f"{fund} | {buy_label} x {sell_label}",
                        "fund": fund,
                        "buy": buy_label,
                        "sell": sell_label,
                        "loss_track": loss,
                        "config": config,
                    }
                )
    return specs


def _window(fund: str):
    import pandas as pd

    from engine.warehouse.bars import load_frame
    from research.ml.meta_training import window
    from research.strategies.natr_regime import daily_bars

    bars = load_frame(fund)
    before = bars[bars.index < pd.Timestamp(START, tz="UTC")]
    # Session OHLCV, as server/backtest.warm_up_history builds it: the RSP
    # book's accumulation/distribution reads the volume.
    warm = daily_bars(before)
    warm["volume"] = before["volume"].resample("1D").sum().reindex(warm.index)
    return window(bars, START, None), warm


def run_one(spec: dict) -> dict:
    """One cell, reduced to its metrics; never raises."""
    started = time.time()
    out = {k: spec[k] for k in ("name", "fund", "buy", "sell", "loss_track")}
    try:
        from engine.core.config import BacktestConfig
        from research.optimization.optimization_controller import OptimizationController
        from research.strategies.strategy_registry import resolve_strategy, session_bars

        config = BacktestConfig.from_dict(spec["config"])
        cls = resolve_strategy(config.strategy.strategy_id)
        bars, warm = _window(spec["fund"])
        frame = session_bars(cls, bars, config.strategy.strategy_params)
        kwargs = config.to_run_sweep_kwargs(cls)
        kwargs.update(n_jobs=1, return_full_results=False, warm_up_daily=warm)
        row = OptimizationController(historical_data=frame).run_sweep(**kwargs).iloc[0]
        if isinstance(row.get("error"), str):
            out["error"] = row["error"]
        else:
            out["metrics"] = {k: _num(row.get(k)) for k in METRICS}
            out["window"] = [str(frame.index[0]), str(frame.index[-1])]
    except Exception as exc:  # one failed cell is a row, not a failed sweep
        out["error"] = f"{type(exc).__name__}: {exc}"
    out["elapsed_s"] = round(time.time() - started, 1)
    return out


def _num(value) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def buy_and_hold(fund: str) -> dict:
    bars, _ = _window(fund)
    close = bars["close"].astype(float)
    years = (bars.index[-1] - bars.index[0]).days / 365.25
    total = close.iloc[-1] / close.iloc[0] - 1
    return {
        "Total Return %": 100 * total,
        "CAGR %": 100 * ((1 + total) ** (1 / years) - 1),
        "Max Drawdown %": 100 * float((1 - close / close.cummax()).max()),
    }


def calmar(m: dict) -> float | None:
    cagr, dd = m.get("CAGR %"), m.get("Max Drawdown %")
    if cagr is None or not dd:
        return None
    return cagr / dd


def load(out_dir: Path) -> list[dict]:
    """Each cell's latest row (a re-run replaces a failed one)."""
    path = out_dir / "results.jsonl"
    if not path.exists():
        return []
    rows = {}
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["name"]] = row
    return list(rows.values())


def report(out_dir: Path) -> str:
    rows = load(out_dir)
    lines = [f"# The TFT in buy x sell compositions ({len(rows)} cells)", ""]
    for fund in FUNDS:
        cells = [r for r in rows if r["fund"] == fund]
        if not cells:
            continue
        bh = buy_and_hold(fund)
        ok = [r for r in cells if "metrics" in r]
        bad = [r for r in cells if "error" in r]
        lines += [
            f"## {fund}: {len(ok)} cells ran, {len(bad)} failed; window {ok[0]['window'][0][:10]}"
            f" .. {ok[0]['window'][1][:10]}"
            if ok
            else f"## {fund}",
            "",
            f"Buy-and-hold: total {bh['Total Return %']:.1f}%, CAGR {bh['CAGR %']:.1f}%, max "
            f"drawdown {bh['Max Drawdown %']:.1f}%, Calmar {calmar(bh):.2f}.",
            "",
            "| buy | sell | total % | CAGR % | max DD % | Calmar | trades | open lots |",
            "|---|---|---|---|---|---|---|---|",
        ]
        ranked = sorted(ok, key=lambda r: calmar(r["metrics"]) or -1e9, reverse=True)
        for r in ranked:
            m = r["metrics"]
            lines.append(
                f"| {r['buy']} | {r['sell']}{' (may lose)' if r['loss_track'] else ''} | "
                f"{m['Total Return %']:.1f} | {m['CAGR %']:.1f} | {m['Max Drawdown %']:.1f} | "
                f"{(calmar(m) or 0):.2f} | {int(m['Trade Count'] or 0):,} | "
                f"{int(m['Open Trade Count'] or 0):,} |"
            )
        lines += _against_null(ok) + _sell_against_fixed(ok)
        if bad:
            lines += ["", "Failed:"] + [f"- {r['name']}: {r['error'][:160]}" for r in bad]
        lines.append("")
    return "\n".join(lines)


def _cell(rows: list[dict], buy: str, sell: str) -> dict | None:
    return next((r["metrics"] for r in rows if r["buy"] == buy and r["sell"] == sell), None)


def _pair(m: dict | None) -> str:
    if m is None:
        return "-"
    return f"{m['Total Return %']:.1f} / {m['Max Drawdown %']:.1f}"


def _against_null(rows: list[dict]) -> list[str]:
    """Each TFT buy beside its null, cap by cap and sell by sell."""
    sells = sorted({r["sell"] for r in rows})
    out = [
        "",
        "TFT buy against its null (total % / max DD %; the null is the same sizer",
        "fed the model's average forecast on every bar):",
        "",
        "| sell | cap | tft | tft_inputs | null | tft beats null |",
        "|---|---|---|---|---|---|",
    ]
    wins = total = 0
    for sell in sells:
        for cap in CAPS:
            tft, inp, null = (
                _cell(rows, f"{m} cap{cap:g}", sell) for m in ("tft", "tft_inputs", "null")
            )
            if tft is None or null is None:
                continue
            better = calmar(tft) is not None and (calmar(tft) or 0) > (calmar(null) or 0)
            wins, total = wins + better, total + 1
            out.append(
                f"| {sell} | {cap:g} | {_pair(tft)} | {_pair(inp)} | {_pair(null)} | "
                f"{'yes' if better else 'no'} |"
            )
    out.append(f"\nOn Calmar the price-only TFT beats its null in {wins} of {total} cells.")
    return out


def _sell_against_fixed(rows: list[dict]) -> list[str]:
    """Each buy with the TFT as its sell, beside the same buy at its fixed target."""
    buys = sorted({r["buy"] for r in rows})
    out = [
        "",
        "TFT sell against the fixed target (total % / max DD %):",
        "",
        "| buy | fixed_target | tft_take_profit | tft_inputs_take_profit | null_take_profit |",
        "|---|---|---|---|---|",
    ]
    for buy in buys:
        fixed = _cell(rows, buy, "fixed_target")
        if fixed is None:
            continue
        out.append(
            f"| {buy} | {_pair(fixed)} | {_pair(_cell(rows, buy, 'tft_take_profit'))} | "
            f"{_pair(_cell(rows, buy, 'tft_inputs_take_profit'))} | "
            f"{_pair(_cell(rows, buy, 'null_take_profit'))} |"
        )
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="The TFT in buy x sell compositions.")
    parser.add_argument("--models", type=Path, default=_REPO_ROOT / "data" / "ml" / "models")
    parser.add_argument("--out", type=Path, default=_REPO_ROOT / "output" / "tft_composite")
    parser.add_argument("--fund", nargs="+", default=list(FUNDS), choices=list(FUNDS))
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument(
        "--build-null", action="store_true", help="Write each price-only model's null table first"
    )
    args = parser.parse_args(argv)
    if args.build_null:
        for fund in args.fund:
            build_null(fund, args.models / f"tft_{fund.lower()}")
    if args.report:
        text = report(args.out)
        (args.out / "report.md").write_text(text)
        print(text)
        return 0
    specs = plan(args.models, tuple(args.fund))
    done = {r["name"] for r in load(args.out) if "metrics" in r}
    todo = [s for s in specs if s["name"] not in done]
    print(f"{len(specs)} cells, {len(specs) - len(todo)} already run, {len(todo)} to run")
    if args.dry_run:
        for s in todo:
            print(" ", s["name"])
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with (
        ProcessPoolExecutor(max_workers=args.jobs) as pool,
        (args.out / "results.jsonl").open("a") as sink,
    ):
        futures = [pool.submit(run_one, s) for s in todo]
        for i, future in enumerate(as_completed(futures), 1):
            row = future.result()
            sink.write(json.dumps(row) + "\n")
            sink.flush()
            m = row.get("metrics") or {}
            print(
                f"[{i}/{len(todo)} {time.time() - started:.0f}s] {row['name']}: "
                + (
                    f"total {m.get('Total Return %', 0):.1f}% DD {m.get('Max Drawdown %', 0):.1f}%"
                    if m
                    else f"ERROR {row.get('error', '')[:100]}"
                )
                + f" ({row['elapsed_s']}s)",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
