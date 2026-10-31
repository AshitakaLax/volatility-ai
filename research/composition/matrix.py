"""
The buy x sell matrix runner (Phase 5 of docs/research/buy-sell-composition.md).

One matrix config names a list of buy policies, a list of sell policies and
a universe of funds; every (buy, sell) pair is a CELL, run on every fund,
each cell with the SAME trial budget drawn at random from its own parameter
space (so a policy with a big grid does not beat one with a small grid by
search luck alone). Each trial is reduced, as it finishes, to the few numbers
the analysis needs -- headline metrics, per-calendar-year figures, monthly
returns, returns by market regime -- and its ~35 MB SimulationResult is let
go (the sink rule that once OOM'd a machine).

    matrix:
      name: first-8x8x4
      symbols: [TQQQ, QQQ, SOXL, RSP]   # or "all": every fund in the warehouse
      min_history_years: 10             # recommended 10+, never below 5
      trials_per_cell: 8
      seed: 7
      buys:  [{id: hf_local_reference, params: {...}}, {id: rk62_ma_cross, params: {...}}]
      sells: [{id: fixed_target}, {id: trailing, params: {trail_pct: [0.005, 0.01, 0.02]}}]
    grid: {steps: [...], profit_targets: [...]}   # part of every cell's space
    costs: {...}            # use the real cost model: tranches pay per trade
    execution: {...}        # allow_signal_exit is set PER CELL from its sell policy
    backtest: {initial_cash: 100000}

Runs through OptimizationController.run_sweep -- never research/
run_hf_sweep.py, which drops allow_signal_exit and cash yield -- with the
loss gate opened only for cells whose sell policy is on the loss-capable
track, and each track reported separately by the analysis.

A cell whose policy was researched on other funds (an ML model's ticker) is
skipped on a fund it does not fit, and recorded as skipped. A fund with less
history than min_history_years is skipped; one under 10 years is run and
marked `short_history`.
"""

from __future__ import annotations

import contextlib
import json
import logging
import math
import zlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from engine.core.config import BacktestConfig, expand_component
from engine.core.exceptions import ConfigurationError
from research.composition.composed_strategy import ComposedStrategy
from research.optimization.optimization_controller import OptimizationController
from research.optimization.search_strategies import RandomSearch

logger = logging.getLogger(__name__)

HISTORY_FLOOR_YEARS = 5.0
RECOMMENDED_HISTORY_YEARS = 10.0
METRICS = (
    "Total Return %",
    "CAGR %",
    "Max Drawdown %",
    "Sharpe",
    "Sortino",
    "Final Equity",
    "Realized PnL",
    "Trade Count",
    "Closed Trade Count",
    "Open Trade Count",
    "Signal Exit Count",
    "Stuck Capital Value",
)
# Named stress windows, reported on their own (Phase 6).
STRESS_WINDOWS = {
    "2018Q4": ("2018-10-01", "2018-12-31"),
    "covid_2020": ("2020-02-19", "2020-03-31"),
    "bear_2022": ("2022-01-01", "2022-12-31"),
}


@dataclass(frozen=True)
class MatrixSpec:
    name: str
    symbols: tuple[str, ...] | str
    buys: tuple[dict, ...]
    sells: tuple[dict, ...]
    base: dict
    min_history_years: float = RECOMMENDED_HISTORY_YEARS
    trials_per_cell: int = 8
    seed: int = 0

    def __post_init__(self) -> None:
        if self.min_history_years < HISTORY_FLOOR_YEARS:
            raise ConfigurationError(
                f"min_history_years must be at least {HISTORY_FLOOR_YEARS:g} "
                f"(10 or more recommended), got {self.min_history_years}"
            )
        if self.trials_per_cell < 1:
            raise ConfigurationError("trials_per_cell must be >= 1")
        if not self.buys or not self.sells:
            raise ConfigurationError("a matrix needs at least one buy and one sell policy")


def load_spec(source: str | Path | dict) -> MatrixSpec:
    """A matrix config, from a YAML path or the parsed mapping."""
    data = source if isinstance(source, dict) else yaml.safe_load(Path(source).read_text())
    data = dict(data or {})
    matrix = dict(data.pop("matrix", None) or {})
    if not matrix:
        raise ConfigurationError("a matrix config needs a `matrix:` section")
    if "strategy" in data:
        raise ConfigurationError("a matrix config names buys and sells, not a strategy")
    symbols = matrix.get("symbols", "all")
    if not (symbols == "all" or (isinstance(symbols, list) and symbols)):
        raise ConfigurationError("matrix.symbols must be a list of funds or 'all'")
    return MatrixSpec(
        name=str(matrix.get("name") or "matrix"),
        symbols=tuple(str(s).upper() for s in symbols) if symbols != "all" else "all",
        buys=tuple(matrix.get("buys") or ()),
        sells=tuple(matrix.get("sells") or ()),
        base=data,
        min_history_years=float(matrix.get("min_history_years", RECOMMENDED_HISTORY_YEARS)),
        trials_per_cell=int(matrix.get("trials_per_cell", 8)),
        seed=int(matrix.get("seed", 0)),
    )


@dataclass(frozen=True)
class Cell:
    buy_id: str
    sell_id: str
    buys: tuple[dict, ...]
    sells: tuple[dict, ...]

    @property
    def params(self) -> dict:
        return {"buy": list(self.buys), "sell": list(self.sells)}

    @property
    def key(self) -> str:
        return f"{self.buy_id}|{self.sell_id}"


def _defaults(side: str, policy_id: str) -> dict:
    from research.composition.catalog import defaults_for

    return defaults_for("buy" if side == "buys" else "sell", policy_id)


def _group(components: Iterable[dict], side: str) -> dict[str, tuple[dict, ...]]:
    """Every concrete variant of each policy id, in first-seen order. A
    parameter not given takes the policy's committed default, so a matrix
    can name a policy by its id alone."""
    out: dict[str, list[dict]] = {}
    for raw in components:
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
            raise ConfigurationError(f"matrix.{side} entries must be {{id, params}}, got {raw!r}")
        raw = {
            "id": raw["id"],
            "params": {**_defaults(side, raw["id"]), **(raw.get("params") or {})},
        }
        for variant in expand_component(raw, side):
            out.setdefault(variant["id"], []).append(variant)
    return {k: tuple(v) for k, v in out.items()}


def plan_cells(spec: MatrixSpec) -> list[Cell]:
    buys, sells = _group(spec.buys, "buys"), _group(spec.sells, "sells")
    return [Cell(b, s, buys[b], sells[s]) for b in buys for s in sells]


def _replaces_target(cell: Cell) -> bool:
    from research.composition.exits import EXITS

    return all(getattr(EXITS.get(s["id"]), "replaces_target", False) for s in cell.sells)


def track_of(cell: Cell) -> str:
    from research.strategies.strategy_registry import may_realize_loss

    return "loss_capable" if may_realize_loss("composed", cell.params) else "no_loss"


def _cell_seed(spec: MatrixSpec, cell: Cell) -> int:
    """The same draw for a cell on every fund, stable across processes (no
    salted hash()), so a cell's funds are compared on the same parameters."""
    return zlib.crc32(f"{spec.seed}:{cell.key}".encode())


def _fits(cell: Cell, symbol: str) -> str | None:
    """Why this cell cannot run on `symbol`, or None."""
    for buy in cell.buys:
        for sell in cell.sells:
            try:
                strategy = ComposedStrategy(buy=buy, sell=sell)
            except ConfigurationError as exc:
                return f"does not construct: {exc}"
            ticker = getattr(strategy, "ticker", None)
            if ticker and str(ticker).upper() != symbol:
                return f"researched on {ticker}"
    return None


# --------------------------------------------------------------- per trial


def _daily_equity(curve: pd.Series) -> pd.Series:
    if curve is None or curve.empty:
        return pd.Series(dtype=float)
    index = pd.DatetimeIndex(curve.index)
    if index.tz is not None:
        index = index.tz_convert("America/New_York").tz_localize(None)
    return pd.Series(curve.to_numpy(float), index=index).groupby(index.normalize()).last()


def _max_drawdown_pct(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    peak = values.cummax()
    return float(((peak - values) / peak).max() * 100.0)


def _lot_book(blotter: pd.DataFrame) -> pd.DataFrame:
    """Per lot: when bought, at what cost, how many shares, and when its LAST
    share sold (NaT while open). Several sells per lot are partial sales."""
    if blotter is None or blotter.empty or "lot_id" not in blotter.columns:
        return pd.DataFrame(columns=["opened", "cost", "qty", "sold_qty", "closed", "sells"])
    stamps = pd.to_datetime(blotter["timestamp"], utc=True)
    frame = blotter.assign(ts=stamps)
    buys = frame[frame["side"] == "buy"].set_index("lot_id")
    sells = frame[frame["side"] == "sell"]
    book = pd.DataFrame(
        {
            "opened": buys["ts"],
            "cost": buys["price"] * buys["qty"],
            "qty": buys["qty"],
            "sold_qty": sells.groupby("lot_id")["qty"].sum(),
            "sells": sells.groupby("lot_id").size(),
            "last_sell": sells.groupby("lot_id")["ts"].max(),
        }
    )
    book = book.dropna(subset=["opened"]).fillna({"sold_qty": 0.0, "sells": 0})
    done = book["sold_qty"] >= book["qty"] * (1 - 1e-9) - 1e-9
    book["closed"] = book["last_sell"].where(done)
    return book


def trial_summary(row: dict, sim_result: Any, regimes: pd.DataFrame | None) -> dict:
    """Everything the analysis needs from one finished trial, small."""
    metrics = {name: _number(row.get(name)) for name in METRICS}
    cagr, mdd = metrics["CAGR %"], metrics["Max Drawdown %"]
    metrics["Calmar"] = (cagr / mdd) if cagr is not None and mdd else None
    blotter = getattr(sim_result, "trade_blotter", None)
    equity = _daily_equity(getattr(sim_result, "equity_curve", None))
    final = _number(row.get("Final Equity"))
    if not equity.empty and final is not None:
        # The curve holds each bar's START-of-bar equity, so its last point
        # misses the last bar's move: end the last day where the run ended.
        equity.iloc[-1] = final
    book = _lot_book(blotter)
    sold_lots = book[book["sells"] > 0]
    metrics["Partial Sale Lots"] = int((book["sells"] > 1).sum())
    metrics["Sales Per Sold Lot"] = float(sold_lots["sells"].mean()) if not sold_lots.empty else 0.0

    years = []
    if not equity.empty:
        prev = float(row.get("initial_cash") or equity.iloc[0])
        sells = (
            blotter[blotter["side"] == "sell"].assign(
                ts=pd.to_datetime(blotter["timestamp"], utc=True)
            )
            if blotter is not None and not blotter.empty
            else None
        )
        for year, values in equity.groupby(equity.index.year):
            end = float(values.iloc[-1])
            year_end = pd.Timestamp(f"{year}-12-31 23:59", tz="America/New_York").tz_convert("UTC")
            open_at = book[(book["opened"] <= year_end) & ~(book["closed"] <= year_end)]
            realized = 0.0
            signal_exits = 0
            if sells is not None:
                in_year = sells[sells["ts"].dt.tz_convert("America/New_York").dt.year == year]
                realized = float(in_year["profit_realized"].fillna(0).sum())
                signal_exits = int(in_year["sell_reason"].astype(str).str.contains("signal").sum())
            years.append(
                {
                    "year": int(year),
                    "return_pct": (end / prev - 1.0) * 100.0 if prev else None,
                    "max_drawdown_pct": _max_drawdown_pct(pd.concat([pd.Series([prev]), values])),
                    "realized_pnl": realized,
                    "signal_exits": signal_exits,
                    "open_lots_end": len(open_at),
                    "committed_end": float(open_at["cost"].sum()),
                }
            )
            prev = end

    monthly = equity.resample("ME").last().pct_change().dropna() if not equity.empty else equity
    stress = {}
    for name, (start, end) in STRESS_WINDOWS.items():
        window = equity[(equity.index >= start) & (equity.index <= end)]
        if len(window) >= 2:
            before = equity[equity.index < start]
            base = float(before.iloc[-1]) if not before.empty else float(window.iloc[0])
            stress[name] = {
                "return_pct": (float(window.iloc[-1]) / base - 1.0) * 100.0,
                "max_drawdown_pct": _max_drawdown_pct(pd.concat([pd.Series([base]), window])),
            }

    by_regime = {}
    if regimes is not None and not equity.empty:
        daily = np.log(equity).diff().dropna()
        tags = regimes.reindex(daily.index.normalize())
        for column in ("calm", "uptrend"):
            flag = tags[column]
            for value, label in ((True, column), (False, f"not_{column}")):
                # A session with no reading yet (warm-up) is neither.
                mask = flag.map(
                    lambda x, v=value: x is not pd.NA and x is not None and bool(x) == v
                )
                chosen = daily[mask.fillna(False).astype(bool).to_numpy()]
                by_regime[label] = {
                    "log_return": float(chosen.sum()),
                    "days": len(chosen),
                }
    return {
        "metrics": metrics,
        "years": years,
        "monthly": [float(x) for x in monthly.to_numpy()],
        "monthly_index": [d.strftime("%Y-%m") for d in monthly.index],
        "stress": stress,
        "regimes": by_regime,
    }


def _number(value) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def symbol_regimes(bars: pd.DataFrame) -> pd.DataFrame:
    """Per session: the causal NATR regime (calm?) and the trend (close above
    its 200-session average), each as known BEFORE that session -- the
    labels a trial's daily returns are split by."""
    from research.strategies.natr_regime import calm_by_date, daily_bars

    daily = daily_bars(bars)
    index = pd.DatetimeIndex(daily.index)
    if index.tz is not None:
        index = index.tz_convert("America/New_York").tz_localize(None)
    index = index.normalize()
    calm_map = calm_by_date(daily, lag=1)
    calm = pd.Series([calm_map.get(ts.date()) for ts in daily.index], index=index)
    close = pd.Series(daily["close"].to_numpy(float), index=index)
    uptrend = (close > close.rolling(200, min_periods=200).mean()).shift(1)
    return pd.DataFrame({"calm": calm, "uptrend": uptrend.astype("boolean")})


class _TrialSink:
    """Reduces each finished trial to trial_summary and lets the result go.
    Never raises (a storage fault must not destroy a matrix run) and never
    retains a SimulationResult."""

    def __init__(self, record: Callable[[dict], None], context: dict, regimes) -> None:
        self._record = record
        self._context = context
        self._regimes = regimes
        self.recorded = 0

    def open_sweep(self, **_: Any) -> str:
        return self._context["cell"]

    def record(self, *, row: dict, sim_result: Any, elapsed_ms: int) -> None:
        try:
            out = {
                **self._context,
                "grid_step": row.get("Grid Step"),
                "profit_target": row.get("Profit Target"),
                "buy_params": (row.get("buy") or {}).get("params"),
                "sell_params": (row.get("sell") or {}).get("params"),
                "elapsed_ms": elapsed_ms,
            }
            if row.get("error") or sim_result is None:
                out["error"] = str(row.get("error") or "no result")
            else:
                out.update(trial_summary(row, sim_result, self._regimes))
            self._record(out)
            self.recorded += 1
        except Exception as exc:  # never fail the matrix over one trial's record
            logger.error(f"matrix: could not record a trial of {self._context['cell']}: {exc}")
            with contextlib.suppress(Exception):
                self._record({**self._context, "error": f"could not record: {exc}"})

    def close_sweep(self) -> None:
        pass


# --------------------------------------------------------------- the run


def _warehouse_loader(symbol: str) -> pd.DataFrame:
    from engine.warehouse.bars import load_frame

    return load_frame(symbol)


def _warehouse_symbols() -> list[str]:
    from engine.warehouse.bars import available_tickers

    return sorted(available_tickers())


def history_years(bars: pd.DataFrame) -> float:
    if bars.empty:
        return 0.0
    return (bars.index[-1] - bars.index[0]).days / 365.25


@dataclass
class MatrixRun:
    spec: MatrixSpec
    trials: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)

    def trials_frame(self) -> pd.DataFrame:
        rows = []
        for trial in self.trials:
            rows.append(
                {
                    k: trial.get(k)
                    for k in (
                        "symbol",
                        "buy_id",
                        "sell_id",
                        "cell",
                        "track",
                        "short_history",
                        "history_years",
                        "grid_step",
                        "profit_target",
                        "error",
                    )
                }
                | (trial.get("metrics") or {})
            )
        return pd.DataFrame(rows)

    def years_frame(self) -> pd.DataFrame:
        rows = []
        for n, trial in enumerate(self.trials):
            for year in trial.get("years") or ():
                rows.append({"trial": n, "symbol": trial["symbol"], "cell": trial["cell"], **year})
        return pd.DataFrame(rows)


def run_matrix(
    spec: MatrixSpec,
    *,
    load_bars: Callable[[str], pd.DataFrame] = _warehouse_loader,
    list_symbols: Callable[[], list[str]] = _warehouse_symbols,
    n_jobs: int = 1,
    out_dir: str | Path | None = None,
    progress: Callable[[str], None] | None = None,
) -> MatrixRun:
    """Run every cell on every fund; return (and, with out_dir, write) the
    reduced trials. out_dir gets trials.jsonl (one trial per line, appended
    as it finishes, so an interrupted run keeps what it did) and
    skipped.json."""
    from research.strategies.strategy_registry import session_bars

    run = MatrixRun(spec)
    cells = plan_cells(spec)
    symbols = list(spec.symbols) if spec.symbols != "all" else list(list_symbols())
    out = Path(out_dir) if out_dir is not None else None
    sink_file = None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        sink_file = (out / "trials.jsonl").open("a", encoding="utf-8")

    def record(trial: dict) -> None:
        run.trials.append(trial)
        if sink_file is not None:
            sink_file.write(json.dumps(trial, default=str) + "\n")
            sink_file.flush()

    try:
        for symbol in symbols:
            bars = load_bars(symbol)
            years = history_years(bars)
            if years < spec.min_history_years:
                run.skipped.append(
                    {
                        "symbol": symbol,
                        "reason": f"{years:.1f} years of history, "
                        f"under min_history_years={spec.min_history_years:g}",
                    }
                )
                continue
            regimes = symbol_regimes(bars)
            for cell in cells:
                why = _fits(cell, symbol)
                if why is not None:
                    run.skipped.append({"symbol": symbol, "cell": cell.key, "reason": why})
                    continue
                frame = session_bars(ComposedStrategy, bars, cell.params)
                config = BacktestConfig.from_dict(
                    {
                        **spec.base,
                        "strategy": {"strategy_id": "composed", "strategy_params": cell.params},
                        "backtest": {**(spec.base.get("backtest") or {}), "symbol": symbol},
                    }
                )
                kwargs = config.to_run_sweep_kwargs(ComposedStrategy)
                grid = kwargs.pop("strategy_params_grid")
                if _replaces_target(cell):
                    # The sell policy sets every lot's target itself, so the
                    # grid's profit target changes nothing: one value, or the
                    # cell's budget is spent on bit-identical trials.
                    kwargs["profit_targets"] = kwargs["profit_targets"][:1]
                search = RandomSearch(
                    kwargs["grid_steps"],
                    kwargs["profit_targets"],
                    grid,
                    n_trials=spec.trials_per_cell,
                    seed=_cell_seed(spec, cell),
                )
                track = track_of(cell)
                sink = _TrialSink(
                    record,
                    {
                        "matrix": spec.name,
                        "symbol": symbol,
                        "buy_id": cell.buy_id,
                        "sell_id": cell.sell_id,
                        "cell": cell.key,
                        "track": track,
                        "history_years": round(years, 2),
                        "short_history": years < RECOMMENDED_HISTORY_YEARS,
                        "space": len(kwargs["grid_steps"])
                        * len(kwargs["profit_targets"])
                        * len(grid),
                    },
                    regimes,
                )
                kwargs.update(
                    strategy_params_grid=grid,
                    search_strategy=search,
                    allow_signal_exit=track == "loss_capable",
                    result_sink=sink,
                    return_full_results=False,
                    rank_by="Total Return %",
                    n_jobs=n_jobs,
                )
                if progress is not None:
                    progress(f"{symbol} {cell.key} ({track})")
                OptimizationController(historical_data=frame).run_sweep(**kwargs)
    finally:
        if sink_file is not None:
            sink_file.close()
        if out is not None:
            (out / "skipped.json").write_text(json.dumps(run.skipped, indent=1))
    return run


def load_trials(path: str | Path) -> list[dict]:
    """trials.jsonl as written by run_matrix."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]
