"""Train the meta-label model: a time-series walk-forward over one fund's
bars, written out as an artifact the `ml_meta_label` strategy trades.

    python cli.py train --config config/ml/meta_label_tqqq.yaml [--compare]

--------------------------------------------------------------------
WHY THIS MODEL (docs/ml_plan.md; ledger RK291, RK317, RK294, RK271)

Of every learned method the ledger researched, gradient-boosted trees used
as a meta-labeller are the one that fits this project's rules and its
evidence at once:

  * It cannot break the grid. The model never decides to buy, never moves
    a target and never sells; it only shrinks or skips a buy the champion
    trigger has already chosen, so the no-loss guard, the trigger's
    stranding fix and the owner's long-only rule all stay as they are.
  * Trees are the strongest learners on tabular, noisy, partly missing
    inputs (Gu, Kelly & Xiu 2020; Krauss, Do & Huck 2017), and they meet
    the inference budget: one prediction per buy, not per bar.
  * Meta-labelling is the published way to turn a high-recall rule into a
    higher-precision one (López de Prado 2018 ch. 3; Joubert 2022), and the
    grid trigger is exactly such a rule.
  * The deep alternatives the ledger looked at (LSTM, transformers, RL)
    were rejected or deferred for this data: weak signal, few independent
    observations, no evidence they beat trees here.

--------------------------------------------------------------------
THE TIME-SERIES TRAINING SCHEME

Expanding-window walk-forward with purging and an embargo:

    boundaries b_1 < b_2 < ... every `refit_days`, the first after
    `min_train_days` of data; one more at the end of the data

    segment k   trains on every row whose label was RESOLVED before
                b_k - embargo (ts1 < b_k - embargo: purged, so no training
                label overlaps the period it will answer for)
                answers for bars in [b_k, b_{k+1})
                is scored on the rows that start in that period

Inside a segment's training rows the last `validation_fraction` (by time)
is held out, purged again at its start: the booster is fitted on the head,
stops early on the tail, and its isotonic calibration is fitted on the
tail's predictions. Nothing a segment is scored on, or trades on, was
seen by it.

Rows are weighted by average uniqueness (meta_dataset.average_uniqueness),
because overlapping labels are not independent observations.

The out-of-sample predictions of every segment, pooled, are the honest
score. Two references sit beside it:

  * the base rate: Brier skill is measured against predicting each
    segment's training base rate, the no-skill forecast available at the
    time;
  * a shuffled-label control: the same scheme with training labels
    permuted. Its AUC should sit at 0.5; if it does not, the harness leaks
    and no other number in the report can be believed (docs/ml_plan.md's
    control, averaged over `shuffled_label_runs` seeds).

--------------------------------------------------------------------
WHAT IT WRITES (research/ml/meta_model.py reads it)

    <output>/manifest.json      the spec, the data, each segment, the scores
    <output>/segment_NN.txt     LightGBM text boosters
    <output>/oos_predictions.csv  every scored row: time, entry, label, p
    <output>/report.md          the scores, for a person
    <output>/backtest.yaml      cli.py backtest config: the model on the base config
    <output>/baseline.yaml      the same run with the base strategy, to compare

The directory is written beside the old one and swapped in at the end, so
a running backtest or live session never reads half a model.

`--compare` runs both configs in-process on the out-of-sample window
(warmed with the history before it) and prints them side by side.
"""

from __future__ import annotations

import copy
import json
import math
import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from research.ml.meta_dataset import BarrierLabel, PrimarySignal, build_dataset
from research.ml.meta_features import DAILY_HISTORY_SESSIONS, FEATURE_NAMES
from research.ml.meta_model import FORMAT_VERSION, KIND, MANIFEST, sha256_of

BASE_STRATEGY = "hf_local_reference"
STRATEGY_ID = "ml_meta_label"

DEFAULT_MODEL: dict[str, Any] = {
    "objective": "binary",
    "learning_rate": 0.03,
    "num_leaves": 15,
    "min_data_in_leaf": 200,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "max_bin": 63,
    "seed": 7,
    "deterministic": True,
    "verbose": -1,
}
DEFAULT_SIZING: dict[str, float] = {"skip_below": 0.5, "full_size_at": 0.7, "size_floor": 0.5}
_SIZING_KEYS = frozenset(DEFAULT_SIZING)
_COMPARE_COLUMNS = (
    "Total Return %",
    "CAGR %",
    "Max Drawdown %",
    "Calmar Ratio",
    "Final Equity",
    "Realized PnL",
    "Trade Count",
    "Closed Trade Count",
    "Harvest to Stuck Ratio",
    "Stuck Capital Value",
)


@dataclass(frozen=True)
class WalkForward:
    min_train_days: float = 730.0
    refit_days: float = 365.0
    embargo_days: float = 1.0
    validation_fraction: float = 0.2
    min_train_rows: int = 500

    def __post_init__(self) -> None:
        if self.min_train_days <= 0 or self.refit_days <= 0:
            raise ConfigurationError("walk_forward.min_train_days and refit_days must be > 0")
        if self.embargo_days < 0:
            raise ConfigurationError("walk_forward.embargo_days must be >= 0")
        if not 0 < self.validation_fraction < 0.5:
            raise ConfigurationError("walk_forward.validation_fraction must be in (0, 0.5)")


@dataclass(frozen=True)
class TrainConfig:
    name: str
    base_config_path: Path
    base_raw: dict
    symbol: str
    signal: PrimarySignal
    label: BarrierLabel
    output: Path
    bars_path: Path | None = None
    start_date: str | None = None
    end_date: str | None = None
    min_gap_bars: int = 1
    walk_forward: WalkForward = field(default_factory=WalkForward)
    model: dict = field(default_factory=lambda: dict(DEFAULT_MODEL))
    num_boost_round: int = 500
    early_stopping_rounds: int = 50
    shuffled_label_runs: int = 1
    sizing: dict = field(default_factory=lambda: dict(DEFAULT_SIZING))

    @classmethod
    def from_yaml(cls, path: str | Path) -> TrainConfig:
        path = Path(path)
        if not path.exists():
            raise ConfigurationError(f"training config not found: {path}")
        return cls.from_dict(yaml.safe_load(path.read_text()) or {})

    @classmethod
    def from_dict(cls, data: dict) -> TrainConfig:
        known = {
            "kind",
            "name",
            "base_config",
            "bars",
            "start_date",
            "end_date",
            "label",
            "events",
            "walk_forward",
            "model",
            "controls",
            "sizing",
            "output",
        }
        unknown = set(data) - known
        if unknown:
            raise ConfigurationError(f"unknown training config keys: {sorted(unknown)}")
        if data.get("kind", "meta_label") != "meta_label":
            raise ConfigurationError(f"kind {data['kind']!r} is not a meta-label config")
        for key in ("name", "base_config"):
            if not data.get(key):
                raise ConfigurationError(f"training config needs {key!r}")
        base_path = Path(data["base_config"])
        if not base_path.exists():
            raise ConfigurationError(f"base_config not found: {base_path}")
        base_raw = yaml.safe_load(base_path.read_text()) or {}
        base = BacktestConfig.from_dict(copy.deepcopy(base_raw))
        base.validate()
        if base.strategy.strategy_id != BASE_STRATEGY:
            raise ConfigurationError(
                f"base_config must run {BASE_STRATEGY} (the trigger the model filters); "
                f"{base_path} runs {base.strategy.strategy_id}"
            )
        if len(base.grid.steps) != 1 or len(base.grid.profit_targets) != 1:
            raise ConfigurationError(
                f"base_config must name ONE grid step and ONE profit target (the model is "
                f"trained for one trigger and one lot target); {base_path} has steps "
                f"{list(base.grid.steps)} and targets {list(base.grid.profit_targets)}"
            )
        params = base.strategy.strategy_params
        for key in ("lookback_days", "bars_per_day"):
            if isinstance(params.get(key), list | tuple):
                raise ConfigurationError(f"base_config strategy_params.{key} must be one value")
        signal = PrimarySignal(
            step=float(base.grid.steps[0]),
            lookback_days=float(params["lookback_days"]),
            bars_per_day=int(params["bars_per_day"]),
            fill_model=base.execution.fill_model,
            intrabar_fill=base.execution.intrabar_fill,
        )
        label_raw = dict(data.get("label") or {})
        unknown = set(label_raw) - {"max_hold_days", "stop"}
        if unknown:
            raise ConfigurationError(f"unknown label keys: {sorted(unknown)}")
        max_hold_days = float(label_raw.get("max_hold_days", 1.0))
        label = BarrierLabel(
            profit_target=float(base.grid.profit_targets[0]),
            max_hold_bars=max(1, round(max_hold_days * signal.bars_per_day)),
            stop=label_raw.get("stop"),
        )
        events = dict(data.get("events") or {})
        model_raw = dict(data.get("model") or {})
        num_boost_round = int(model_raw.pop("num_boost_round", 500))
        early_stopping_rounds = int(model_raw.pop("early_stopping_rounds", 50))
        controls = dict(data.get("controls") or {})
        sizing = {**DEFAULT_SIZING, **(data.get("sizing") or {})}
        if set(sizing) - _SIZING_KEYS:
            raise ConfigurationError(f"unknown sizing keys: {sorted(set(sizing) - _SIZING_KEYS)}")
        return cls(
            name=str(data["name"]),
            base_config_path=base_path,
            base_raw=base_raw,
            symbol=base.backtest.symbol,
            signal=signal,
            label=label,
            output=Path(data.get("output") or f"data/ml/models/{data['name']}"),
            bars_path=Path(data["bars"]) if data.get("bars") else None,
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            min_gap_bars=int(events.get("min_gap_bars", 1)),
            walk_forward=WalkForward(**(data.get("walk_forward") or {})),
            model={**DEFAULT_MODEL, **model_raw},
            num_boost_round=num_boost_round,
            early_stopping_rounds=early_stopping_rounds,
            shuffled_label_runs=int(controls.get("shuffled_label_runs", 1)),
            sizing={k: float(v) for k, v in sizing.items()},
        )


# ------------------------------------------------------------------ data


def _utc(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def read_bars_file(path: Path) -> pd.DataFrame:
    """OHLC bars from a CSV or Parquet file with a timestamp column (or
    index), as a UTC-indexed frame."""
    if not path.exists():
        raise ConfigurationError(f"bars file not found: {path}")
    frame = pd.read_parquet(path) if path.suffix in (".parquet", ".pq") else pd.read_csv(path)
    if "timestamp" in frame.columns:
        frame = frame.set_index("timestamp")
    frame.index = pd.DatetimeIndex(pd.to_datetime(frame.index, utc=True))
    frame.columns = [str(c).lower() for c in frame.columns]
    return frame.sort_index()


def load_bars(config: TrainConfig) -> pd.DataFrame:
    if config.bars_path is not None:
        bars = read_bars_file(config.bars_path)
    else:
        from engine.warehouse.bars import available_tickers, load_frame

        bars = load_frame(config.symbol)
        if bars.empty:
            known = ", ".join(sorted(available_tickers())) or "(none ingested yet)"
            raise ConfigurationError(
                f"No warehouse bars for {config.symbol}. Available: {known}. Fetch and ingest "
                f"them (cli.py fetch-data, tools/build_warehouse.py --ingest {config.symbol}) "
                "or set `bars:` to a CSV/Parquet file."
            )
    return window(bars, config.start_date, config.end_date)


def window(bars: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    if start:
        bars = bars[bars.index >= _utc(start)]
    if end:
        bars = bars[bars.index < _utc(end) + pd.Timedelta(days=1)]
    return bars


# --------------------------------------------------------------- scoring


def _auc(y: np.ndarray, p: np.ndarray) -> float | None:
    if y.size == 0 or y.min() == y.max():
        return None
    from sklearn.metrics import roc_auc_score

    return float(roc_auc_score(y, p))


def score(y: np.ndarray, p: np.ndarray, reference_rate: float) -> dict:
    """AUC, Brier, its skill against a constant `reference_rate`
    forecast, log loss, base rate and mean prediction."""
    y = np.asarray(y, dtype=float)
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    if y.size == 0:
        return {"n": 0}
    brier = float(np.mean((p - y) ** 2))
    ref = float(np.mean((reference_rate - y) ** 2))
    return {
        "n": int(y.size),
        "base_rate": float(y.mean()),
        "mean_p": float(p.mean()),
        "auc": _auc(y, p),
        "brier": brier,
        "brier_reference": ref,
        "brier_skill": (1.0 - brier / ref) if ref > 0 else None,
        "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
    }


def quintiles(y: np.ndarray, p: np.ndarray) -> list[dict]:
    """Hit rate by quintile of predicted probability (lowest first)."""
    if y.size < 5:
        return []
    order = np.argsort(p, kind="mergesort")
    out = []
    for k, chunk in enumerate(np.array_split(order, 5)):
        out.append(
            {
                "quintile": k + 1,
                "n": int(chunk.size),
                "mean_p": float(p[chunk].mean()),
                "hit_rate": float(y[chunk].mean()),
            }
        )
    return out


# -------------------------------------------------------------- training


@dataclass
class _Fit:
    booster: Any
    best_iteration: int
    knots_x: list
    knots_y: list
    n_train: int
    n_validation: int
    train_rate: float

    def predict(self, x: np.ndarray) -> np.ndarray:
        raw = self.booster.predict(x, num_iteration=self.best_iteration)
        if not self.knots_x:
            return raw
        return np.interp(raw, self.knots_x, self.knots_y)


def boundaries(ts0: pd.Series, data_end: pd.Timestamp, wf: WalkForward) -> list[pd.Timestamp]:
    """Segment start times: the first after min_train_days, then every
    refit_days while inside the data, then the end of the data."""
    first = ts0.iloc[0] + pd.Timedelta(days=wf.min_train_days)
    out = []
    b = first
    while b < data_end:
        out.append(b)
        b = b + pd.Timedelta(days=wf.refit_days)
    out.append(data_end)
    return out


def _utc_values(series: pd.Series) -> np.ndarray:
    """A timestamp column as naive-UTC datetime64, for fast comparisons."""
    return series.dt.tz_convert(None).to_numpy()


@dataclass(frozen=True)
class _Arrays:
    """The dataset's columns as arrays, built once per walk-forward."""

    x: np.ndarray
    w: np.ndarray
    ts0: np.ndarray  # naive UTC datetime64
    ts1: np.ndarray

    @classmethod
    def of(cls, frame: pd.DataFrame) -> _Arrays:
        return cls(
            x=frame[list(FEATURE_NAMES)].to_numpy(dtype=np.float64),
            w=frame["weight"].to_numpy(dtype=np.float64),
            ts0=_utc_values(frame["ts0"]),
            ts1=_utc_values(frame["ts1"]),
        )


def _fit_segment(
    lgb, data: _Arrays, rows: np.ndarray, y: np.ndarray, config: TrainConfig, rounds: int
) -> _Fit | None:
    """Fit one booster on `rows` (time-ordered positions into the dataset):
    head for fitting, purged tail for early stopping and calibration."""
    wf = config.walk_forward
    ts0 = data.ts0[rows]
    ts1 = data.ts1[rows]
    cut = rows.size - max(1, int(rows.size * wf.validation_fraction))
    tail_start = ts0[cut]
    head = np.flatnonzero(ts1[:cut] < tail_start)
    tail = np.arange(cut, rows.size)
    if head.size < wf.min_train_rows // 2 or tail.size < 20:
        return None
    yh, yt = y[rows[head]], y[rows[tail]]
    if yh.min() == yh.max():
        return None
    x, w = data.x, data.w
    wh = w[rows[head]] / w[rows[head]].mean()
    wt = w[rows[tail]] / w[rows[tail]].mean()
    train_set = lgb.Dataset(x[rows[head]], label=yh, weight=wh, feature_name=list(FEATURE_NAMES))
    valid_set = lgb.Dataset(x[rows[tail]], label=yt, weight=wt, reference=train_set)
    booster = lgb.train(
        config.model,
        train_set,
        num_boost_round=rounds,
        valid_sets=[valid_set],
        callbacks=[lgb.early_stopping(config.early_stopping_rounds, verbose=False)],
    )
    best = booster.best_iteration or rounds
    knots_x: list = []
    knots_y: list = []
    if yt.min() != yt.max():
        from sklearn.isotonic import IsotonicRegression

        raw = booster.predict(x[rows[tail]], num_iteration=best)
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(raw, yt, sample_weight=wt)
        knots_x = [float(v) for v in iso.X_thresholds_]
        knots_y = [float(v) for v in iso.y_thresholds_]
    return _Fit(
        booster=booster,
        best_iteration=int(best),
        knots_x=knots_x,
        knots_y=knots_y,
        n_train=int(head.size),
        n_validation=int(tail.size),
        train_rate=float(np.average(yh, weights=wh)),
    )


def walk_forward(
    frame: pd.DataFrame,
    config: TrainConfig,
    data_end: pd.Timestamp,
    *,
    labels: np.ndarray | None = None,
    rounds: int | None = None,
    log=print,
) -> tuple[list[dict], list[_Fit | None], np.ndarray]:
    """Run the scheme once. Returns per-segment records, the fits, and the
    out-of-sample probability of every row (NaN where no segment spoke)."""
    import lightgbm as lgb

    y = frame["label"].to_numpy() if labels is None else labels
    data = _Arrays.of(frame)
    ts0 = frame["ts0"]
    ts1 = data.ts1
    starts = boundaries(ts0, data_end, config.walk_forward)
    embargo = pd.Timedelta(days=config.walk_forward.embargo_days)
    oos = np.full(len(frame), np.nan)
    records: list[dict] = []
    fits: list[_Fit | None] = []
    for k, start in enumerate(starts):
        cutoff = (start - embargo).to_datetime64()
        rows = np.flatnonzero(ts1 < cutoff)
        record: dict[str, Any] = {"index": k, "valid_from": start.isoformat()}
        fit = None
        if rows.size >= config.walk_forward.min_train_rows:
            fit = _fit_segment(lgb, data, rows, y, config, rounds or config.num_boost_round)
        if fit is None:
            record["skipped"] = f"too few usable training rows ({rows.size})"
            fits.append(None)
            records.append(record)
            continue
        record.update(
            train_end=pd.Timestamp(ts1[rows].max(), tz="UTC").isoformat(),
            n_train=fit.n_train,
            n_validation=fit.n_validation,
            best_iteration=fit.best_iteration,
            train_base_rate=fit.train_rate,
        )
        end = starts[k + 1] if k + 1 < len(starts) else None
        test = (ts0 >= start) & (ts0 < end) if end is not None else ts0 >= start
        test_rows = np.flatnonzero(test.to_numpy())
        if test_rows.size:
            p = fit.predict(data.x[test_rows])
            oos[test_rows] = p
            record["test"] = score(frame["label"].to_numpy()[test_rows], p, fit.train_rate)
        fits.append(fit)
        records.append(record)
        if labels is None:
            t = record.get("test", {})
            auc = t.get("auc")
            log(
                f"  segment {k:2d} from {start.date()}: trained on {fit.n_train:>8,} rows "
                f"({fit.best_iteration} trees), tested on {t.get('n', 0):>8,}"
                + (f", AUC {auc:.3f}" if auc is not None else "")
            )
    return records, fits, oos


def train(config: TrainConfig, bars: pd.DataFrame | None = None, log=print) -> dict:
    """The whole pipeline: dataset, walk-forward, control, artifact.
    Returns the manifest."""
    try:
        import lightgbm  # noqa: F401
        import sklearn  # noqa: F401
    except ImportError as exc:
        raise ConfigurationError(
            "Training needs lightgbm and scikit-learn: pip install -r requirements-ml.txt"
        ) from exc
    import lightgbm as lgb

    started = time.monotonic()
    if bars is None:
        bars = load_bars(config)
    if bars.empty:
        raise ConfigurationError("no bars to train on in the requested window")
    log(
        f"{config.symbol}: {len(bars):,} bars, {bars.index[0]} .. {bars.index[-1]}; "
        f"trigger step {config.signal.step}, target {config.label.profit_target}, "
        f"hold {config.label.max_hold_bars} bars"
    )
    frame = build_dataset(bars, config.signal, config.label, min_gap_bars=config.min_gap_bars)
    if len(frame) < config.walk_forward.min_train_rows * 2:
        raise ConfigurationError(
            f"only {len(frame)} labelled triggers; need at least "
            f"{config.walk_forward.min_train_rows * 2}. Use more history or a smaller step."
        )
    log(
        f"dataset: {len(frame):,} triggers, base rate {frame['label'].mean():.3f}, "
        f"mean uniqueness {frame['weight'].mean():.4f} ({time.monotonic() - started:.0f}s)"
    )
    data_end = pd.Timestamp(bars.index[-1])
    log("walk-forward:")
    records, fits, oos = walk_forward(frame, config, data_end, log=log)
    if fits[-1] is None:
        raise ConfigurationError("the final segment could not be trained; see the log")
    scored = ~np.isnan(oos)
    y = frame["label"].to_numpy()
    reference = float(np.mean([r["train_base_rate"] for r in records if "train_base_rate" in r]))
    overall = score(y[scored], oos[scored], reference) if scored.any() else {"n": 0}
    bins = quintiles(y[scored], oos[scored]) if scored.any() else []

    controls = []
    rng = np.random.default_rng(int(config.model.get("seed", 7)))
    for run in range(config.shuffled_label_runs):
        shuffled = y.copy()
        rng.shuffle(shuffled)
        _, _, control_p = walk_forward(
            frame,
            config,
            data_end,
            labels=shuffled,
            rounds=min(config.num_boost_round, 200),
            log=log,
        )
        mask = ~np.isnan(control_p)
        controls.append({"run": run, "auc": _auc(y[mask], control_p[mask]), "n": int(mask.sum())})
    control_aucs = [c["auc"] for c in controls if c["auc"] is not None]

    final = fits[-1]
    gains = final.booster.feature_importance("gain", iteration=final.best_iteration)
    total = float(gains.sum()) or 1.0
    importance = sorted(
        (
            {"feature": n, "gain_share": float(g) / total}
            for n, g in zip(FEATURE_NAMES, gains, strict=True)
        ),
        key=lambda d: -d["gain_share"],
    )

    out = Path(config.output)
    staging = out.with_name(f"{out.name}.tmp-{os.getpid()}")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    segments = []
    for record, fit in zip(records, fits, strict=True):
        if fit is None:
            continue
        name = f"segment_{record['index']:02d}.txt"
        fit.booster.save_model(str(staging / name), num_iteration=fit.best_iteration)
        segments.append(
            {
                **record,
                "file": name,
                "sha256": sha256_of(staging / name),
                "calibration": {"x": fit.knots_x, "y": fit.knots_y},
            }
        )
    first_oos = next((s["valid_from"] for s in segments), None)
    manifest = {
        "kind": KIND,
        "format_version": FORMAT_VERSION,
        "name": config.name,
        "strategy_id": STRATEGY_ID,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "lightgbm_version": lgb.__version__,
        "symbol": config.symbol,
        "base_config": str(config.base_config_path),
        "primary": config.signal.to_dict(),
        "label": config.label.to_dict(),
        "features": {
            "names": list(FEATURE_NAMES),
            "bars_per_day": config.signal.bars_per_day,
            "lookback_bars": config.signal.lookback_bars,
            "daily_history_sessions": DAILY_HISTORY_SESSIONS,
        },
        "data": {
            "first_bar": bars.index[0].isoformat(),
            "last_bar": bars.index[-1].isoformat(),
            "bars": len(bars),
            "triggers": len(frame),
            "base_rate": float(y.mean()),
            "source": str(config.bars_path) if config.bars_path else "warehouse",
        },
        "walk_forward": vars(config.walk_forward),
        "model": {
            **config.model,
            "num_boost_round": config.num_boost_round,
            "early_stopping_rounds": config.early_stopping_rounds,
        },
        "sizing": config.sizing,
        "out_of_sample": {"first": first_oos, "overall": overall, "quintiles": bins},
        "control": {
            "shuffled_label_runs": controls,
            "mean_auc": float(np.mean(control_aucs)) if control_aucs else None,
        },
        "importance": importance,
        "segments": segments,
    }
    (staging / MANIFEST).write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    pd.DataFrame(
        {
            "ts0": frame["ts0"][scored].to_numpy(),
            "entry": frame["entry"][scored].to_numpy(),
            "label": y[scored],
            "p": oos[scored],
        }
    ).to_csv(staging / "oos_predictions.csv", index=False)
    backtest, baseline = run_configs(config, out)
    (staging / "backtest.yaml").write_text(yaml.safe_dump(backtest, sort_keys=False))
    (staging / "baseline.yaml").write_text(yaml.safe_dump(baseline, sort_keys=False))
    (staging / "report.md").write_text(report(manifest))
    if out.exists():
        shutil.rmtree(out)
    staging.rename(out)
    log(f"wrote {out} ({time.monotonic() - started:.0f}s)")
    return manifest


# ------------------------------------------------------- running the model


def run_configs(config: TrainConfig, model_dir: Path) -> tuple[dict, dict]:
    """(model, baseline) backtest configs: the base config with its live
    block removed, on the training window's start. The model's segments
    make the whole run out of sample: before the first one it sizes as
    the base strategy does."""
    base = copy.deepcopy(config.base_raw)
    base.pop("live", None)
    section = dict(base.get("backtest") or {})
    section["symbol"] = config.symbol
    section.pop("end_date", None)
    if config.start_date:
        section["start_date"] = str(config.start_date)
    base["backtest"] = section
    model = copy.deepcopy(base)
    params = dict(model["strategy"].get("strategy_params") or {})
    params.update({"model": str(model_dir), **config.sizing})
    model["strategy"] = {"strategy_id": STRATEGY_ID, "strategy_params": params}
    return model, base


def compare(manifest: dict, model_dir: Path, bars: pd.DataFrame, log=print) -> pd.DataFrame:
    """Both configs on the out-of-sample window, warmed with the history
    before it: the model's sizing against the base strategy's."""
    from research.optimization.optimization_controller import OptimizationController
    from research.strategies.natr_regime import daily_bars
    from research.strategies.strategy_registry import resolve_strategy

    first = manifest["out_of_sample"]["first"]
    if first is None:
        raise ConfigurationError("no out-of-sample window to compare on")
    start = pd.Timestamp(first)
    frame = bars[bars.index >= start]
    history = bars[bars.index < start]
    warm = daily_bars(history) if not history.empty else None
    rows = []
    for label, path in (
        ("model", model_dir / "backtest.yaml"),
        ("baseline", model_dir / "baseline.yaml"),
    ):
        cfg = BacktestConfig.from_yaml(str(path))
        cls = resolve_strategy(cfg.strategy.strategy_id)
        kwargs = cfg.to_run_sweep_kwargs(cls)
        kwargs["warm_up_daily"] = warm
        kwargs["return_full_results"] = False
        result = OptimizationController(historical_data=frame).run_sweep(**kwargs).iloc[0]
        if isinstance(result.get("error"), str):
            raise ConfigurationError(f"the {label} run failed: {result['error']}")
        row = {"run": label, "strategy": cfg.strategy.strategy_id}
        row.update({c: result[c] for c in _COMPARE_COLUMNS if c in result.index})
        rows.append(row)
    table = pd.DataFrame(rows).set_index("run")
    log(f"\nout of sample, {frame.index[0].date()} .. {frame.index[-1].date()}:")
    log(table.T.to_string())
    return table


def _fmt(value, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def report(manifest: dict) -> str:
    o = manifest["out_of_sample"]["overall"]
    c = manifest["control"]
    lines = [
        f"# Meta-label model: {manifest['name']}",
        "",
        f"{manifest['symbol']}, trained {manifest['created_at']} on "
        f"{manifest['data']['first_bar'][:10]} .. {manifest['data']['last_bar'][:10]} "
        f"({manifest['data']['bars']:,} bars, {manifest['data']['triggers']:,} triggers, "
        f"base rate {manifest['data']['base_rate']:.3f}).",
        "",
        f"Primary signal: {manifest['primary']}. Label: {manifest['label']}.",
        "",
        "## Out of sample (every segment's own test period, pooled)",
        "",
        "| n | base rate | mean p | AUC | Brier | Brier skill | log loss | shuffled-label AUC |",
        "|---|---|---|---|---|---|---|---|",
        f"| {o.get('n', 0):,} | {_fmt(o.get('base_rate'))} | {_fmt(o.get('mean_p'))} | "
        f"{_fmt(o.get('auc'))} | {_fmt(o.get('brier'), 4)} | {_fmt(o.get('brier_skill'))} | "
        f"{_fmt(o.get('log_loss'))} | {_fmt(c.get('mean_auc'))} |",
        "",
        "Brier skill is against each segment's training base rate. The shuffled-label AUC "
        "should be near 0.5; if it is not, the harness leaks and nothing above can be trusted.",
        "",
        "### Hit rate by predicted quintile",
        "",
        "| quintile | n | mean p | hit rate |",
        "|---|---|---|---|",
    ]
    for q in manifest["out_of_sample"]["quintiles"]:
        lines.append(f"| {q['quintile']} | {q['n']:,} | {q['mean_p']:.3f} | {q['hit_rate']:.3f} |")
    lines += [
        "",
        "## Segments",
        "",
        "| # | valid from | train rows | trees | test n | test AUC | Brier skill |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in manifest["segments"]:
        t = s.get("test", {})
        lines.append(
            f"| {s['index']} | {s['valid_from'][:10]} | {s['n_train']:,} | {s['best_iteration']} | "
            f"{t.get('n', 0):,} | {_fmt(t.get('auc'))} | {_fmt(t.get('brier_skill'))} |"
        )
    lines += ["", "## Feature importance (gain share, final segment)", ""]
    for item in manifest["importance"][:12]:
        lines.append(f"* `{item['feature']}` {item['gain_share']:.3f}")
    lines += [
        "",
        "## Run it",
        "",
        "```bash",
        "python cli.py backtest --config <model dir>/backtest.yaml   # the model",
        "python cli.py backtest --config <model dir>/baseline.yaml   # the base strategy",
        "```",
        "",
        "AUC is not P&L. The model earns a place only if the backtest beats the baseline "
        "on return and drawdown out of sample (docs/ml_plan.md).",
        "",
    ]
    return "\n".join(lines)


def run_cli(config_path: str, bars_path: str | None, output: str | None, do_compare: bool) -> int:
    config = TrainConfig.from_yaml(config_path)
    overrides = {}
    if bars_path:
        overrides["bars_path"] = Path(bars_path)
    if output:
        overrides["output"] = Path(output)
    if overrides:
        config = TrainConfig(**{**vars(config), **overrides})
    bars = load_bars(config)
    manifest = train(config, bars=bars)
    o = manifest["out_of_sample"]["overall"]
    print(
        f"\nout-of-sample AUC {_fmt(o.get('auc'))}, Brier skill {_fmt(o.get('brier_skill'))} "
        f"over {o.get('n', 0):,} triggers; shuffled-label AUC "
        f"{_fmt(manifest['control']['mean_auc'])}"
    )
    print(f"report: {config.output / 'report.md'}")
    print(f"run it: python cli.py backtest --config {config.output / 'backtest.yaml'}")
    if do_compare:
        compare(manifest, config.output, bars)
    return 0


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_SIZING",
    "STRATEGY_ID",
    "TrainConfig",
    "WalkForward",
    "boundaries",
    "compare",
    "load_bars",
    "read_bars_file",
    "report",
    "run_cli",
    "run_configs",
    "score",
    "train",
    "walk_forward",
]
