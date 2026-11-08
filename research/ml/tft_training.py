"""Train the `ml_tft` sizer's Temporal Fusion Transformer.

    python cli.py train --config config/ml/tft_tqqq.yaml [--compare]

Needs requirements-dl.txt (torch, lightning, pytorch-forecasting). Writes
the directory research/ml/tft_model.py loads, plus report.md and the
backtest.yaml / baseline.yaml that run it.

--------------------------------------------------------------------
THE TimeSeriesDataSet, AND WHY EACH ARGUMENT IS WHAT IT IS

The covariate groups are tft_features.py's; this is how they map onto
pytorch-forecasting:

    TimeSeriesDataSet(
        frame,                                   # tft_features.build_frame
        time_idx="time_idx",                     # consecutive bar number
        target="log_close",                      # forecast log price, H bars out
        group_ids=["group"],                     # the fund
        min_encoder_length=L, max_encoder_length=L,          # exactly the ring's length
        min_prediction_length=H, max_prediction_length=H,
        static_categoricals=["group"],
        time_varying_known_reals=["e_event", "t_open", "t_close"],   # decoder sees the future
        time_varying_unknown_reals=["log_close", "ret_1", "ret_2",   # encoder only
                                    "s_macro", "s_earnings", "s_news"],
        target_normalizer=EncoderNormalizer(),   # per window: scale-free across price levels
        add_relative_time_idx=True,              # position in the window, a known input
        add_target_scales=True,                  # the window's centre/scale, a static input
    )

* min = max encoder length: the live ring holds exactly L rows, so the
  model is trained only on full windows -- the shape it will be given.
* The target is log price rather than return so the quantile at decoder
  step H is directly the H-bar-ahead price; subtracting log(entry) turns
  it into the lot's return quantiles (quantiles commute with a shift).
  EncoderNormalizer standardises each window by its own encoder, so a
  model trained across TQQQ's $1-$90 history sees one scale.
* E_event is a 0/1 real rather than a categorical: an embedding learned
  from ~8 decision days a year is mostly noise, and a real lets the
  variable-selection network weigh it like the clock features.
* The loss is QuantileLoss at the configured levels (default 0.1, 0.5,
  0.9 -- the set quantiles_to_moments' Swanson branch is exact for).

--------------------------------------------------------------------
THE SPLIT IS A DATE, AND NOTHING AFTER IT IS TRAINED ON

Training windows are cut from bars before `validation_start` only, so
every training target precedes it. Validation windows are built from the
whole frame with min_prediction_idx at that date: their encoders may
reach back into training bars (inputs, not labels), their targets never
do. The manifest's valid_from is that date, and the sizer refuses to size
an earlier bar (tft_sizing.py, "IN SAMPLE IS REFUSED").

A TFT is too slow to refit once a year over a decade of minute bars on a
CPU, so this is one cutoff rather than the meta-label model's
walk-forward. Retrain with a later validation_start to roll it forward.

--------------------------------------------------------------------
THE REPORT

On up to `eval_samples` validation windows, at the horizon step:

* coverage: the share of realised log prices at or below each forecast
  quantile (a calibrated q90 covers 90%);
* pinball loss against a naive forecast (the last price plus the
  training period's own H-bar return quantiles) -- a TFT that cannot beat
  that has learned nothing about the next H bars;
* the rank correlation of the forecast mean mu with the realised return,
  and the realised return by quintile of the confidence mu / sigma^2.
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

import numpy as np
import pandas as pd
import yaml

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from research.ml.meta_model import sha256_of
from research.ml.meta_training import read_bars_file, window
from research.ml.tft_features import KNOWN, OBSERVED, SOURCES, TARGET, build_frame, load_sources
from research.ml.tft_model import CHECKPOINT, DATASET, FORMAT_VERSION, KIND, MANIFEST
from research.ml.tft_sizing import precision_weighted_confidence, quantiles_to_moments

STRATEGY_ID = "ml_tft"
DEFAULT_MODEL = {
    "hidden_size": 16,
    "attention_head_size": 2,
    "dropout": 0.1,
    "hidden_continuous_size": 8,
    "learning_rate": 0.003,
}
DEFAULT_TRAINER = {
    "max_epochs": 5,
    "batch_size": 128,
    "limit_train_batches": 200,
    "limit_val_batches": 50,
    "gradient_clip_val": 0.1,
    "patience": 2,
    "seed": 7,
}
DEFAULT_SIZING = {
    "max_trade_pct": 0.05,
    "kelly_scale": 0.5,
    "sigma_floor": 0.0001,
    "min_confidence": 0.0,
    "dd_decay": 3.0,
    "duration_decay": 0.01,
    "refresh_bars": 1,
    "lookback_days": None,
}


@dataclass(frozen=True)
class TftTrainConfig:
    name: str
    base_config_path: Path
    base_raw: dict
    symbol: str
    bars_per_day: int
    validation_start: str
    output: Path
    bars_path: Path | None = None
    start_date: str | None = None
    end_date: str | None = None
    encoder_length: int = 120
    prediction_length: int = 30
    quantiles: tuple[float, ...] = (0.1, 0.5, 0.9)
    sources: dict = field(default_factory=dict)
    model: dict = field(default_factory=lambda: dict(DEFAULT_MODEL))
    trainer: dict = field(default_factory=lambda: dict(DEFAULT_TRAINER))
    sizing: dict = field(default_factory=lambda: dict(DEFAULT_SIZING))
    eval_samples: int = 20000

    @classmethod
    def from_yaml(cls, path: str | Path) -> TftTrainConfig:
        path = Path(path)
        if not path.exists():
            raise ConfigurationError(f"training config not found: {path}")
        return cls.from_dict(yaml.safe_load(path.read_text()) or {})

    @classmethod
    def from_dict(cls, data: dict) -> TftTrainConfig:
        known = {
            "kind",
            "name",
            "base_config",
            "bars",
            "start_date",
            "end_date",
            "validation_start",
            "bars_per_day",
            "encoder_length",
            "prediction_length",
            "quantiles",
            "sources",
            "model",
            "trainer",
            "sizing",
            "eval_samples",
            "output",
        }
        unknown = set(data) - known
        if unknown:
            raise ConfigurationError(f"unknown TFT training config keys: {sorted(unknown)}")
        if data.get("kind") != KIND:
            raise ConfigurationError(f"a TFT training config needs kind: {KIND}")
        for key in ("name", "base_config", "validation_start"):
            if not data.get(key):
                raise ConfigurationError(f"TFT training config needs {key!r}")
        base_path = Path(data["base_config"])
        if not base_path.exists():
            raise ConfigurationError(f"base_config not found: {base_path}")
        base_raw = yaml.safe_load(base_path.read_text()) or {}
        base = BacktestConfig.from_dict(copy.deepcopy(base_raw))
        base.validate()
        bars_per_day = data.get("bars_per_day") or base.strategy.strategy_params.get("bars_per_day")
        if not bars_per_day:
            raise ConfigurationError("set bars_per_day (or give the base config's strategy one)")
        quantiles = tuple(float(q) for q in data.get("quantiles") or (0.1, 0.5, 0.9))
        if sorted(quantiles) != list(quantiles) or not all(0 < q < 1 for q in quantiles):
            raise ConfigurationError(f"quantiles must be increasing, in (0, 1): {quantiles}")
        sources = dict(data.get("sources") or {})
        unknown = set(sources) - set(SOURCES)
        if unknown:
            raise ConfigurationError(f"unknown sources {sorted(unknown)}; expected {SOURCES}")
        sizing = {**DEFAULT_SIZING, **(data.get("sizing") or {})}
        if set(sizing) - set(DEFAULT_SIZING):
            raise ConfigurationError(
                f"unknown sizing keys: {sorted(set(sizing) - set(DEFAULT_SIZING))}"
            )
        encoder_length = int(data.get("encoder_length", 120))
        prediction_length = int(data.get("prediction_length", 30))
        if encoder_length < 2 or prediction_length < 1:
            raise ConfigurationError("encoder_length must be >= 2 and prediction_length >= 1")
        return cls(
            name=str(data["name"]),
            base_config_path=base_path,
            base_raw=base_raw,
            symbol=base.backtest.symbol,
            bars_per_day=int(bars_per_day),
            validation_start=str(data["validation_start"]),
            output=Path(data.get("output") or f"data/ml/models/{data['name']}"),
            bars_path=Path(data["bars"]) if data.get("bars") else None,
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            encoder_length=encoder_length,
            prediction_length=prediction_length,
            quantiles=quantiles,
            sources={name: sources.get(name) for name in SOURCES},
            model={**DEFAULT_MODEL, **(data.get("model") or {})},
            trainer={**DEFAULT_TRAINER, **(data.get("trainer") or {})},
            sizing=sizing,
            eval_samples=int(data.get("eval_samples", 20000)),
        )


def load_bars(config: TftTrainConfig) -> pd.DataFrame:
    if config.bars_path is not None:
        bars = read_bars_file(config.bars_path)
    else:
        from engine.warehouse.bars import load_frame

        bars = load_frame(config.symbol)
        if bars.empty:
            raise ConfigurationError(
                f"No warehouse bars for {config.symbol}; ingest them or set `bars:` to a file"
            )
    return window(bars, config.start_date, config.end_date)


def dataset_kwargs(config: TftTrainConfig) -> dict:
    """The TimeSeriesDataSet arguments; see the module docstring."""
    from pytorch_forecasting.data import EncoderNormalizer

    L, H = config.encoder_length, config.prediction_length
    return {
        "time_idx": "time_idx",
        "target": TARGET,
        "group_ids": ["group"],
        "min_encoder_length": L,
        "max_encoder_length": L,
        "min_prediction_length": H,
        "max_prediction_length": H,
        "static_categoricals": ["group"],
        "time_varying_known_reals": list(KNOWN),
        "time_varying_unknown_reals": [TARGET, *OBSERVED],
        "target_normalizer": EncoderNormalizer(),
        "add_relative_time_idx": True,
        "add_target_scales": True,
        "add_encoder_length": False,
    }


def _pinball(y: np.ndarray, q: np.ndarray, levels) -> float:
    total = 0.0
    for j, p in enumerate(levels):
        e = y - q[:, j]
        total += float(np.mean(np.maximum(p * e, (p - 1) * e)))
    return total / len(levels)


def evaluate(model, validation, config: TftTrainConfig, horizon_returns_train: np.ndarray) -> dict:
    """Calibration and skill at the horizon step on validation windows."""
    import torch
    from torch.utils.data import DataLoader, Subset

    n = len(validation)
    if n == 0:
        return {"n": 0}
    rng = np.random.default_rng(int(config.trainer["seed"]))
    idx = np.sort(rng.choice(n, size=min(n, config.eval_samples), replace=False))
    loader = DataLoader(
        Subset(validation, idx.tolist()),
        batch_size=256,
        shuffle=False,
        collate_fn=validation._collate_fn,
        num_workers=0,
    )
    qs, ys, origins = [], [], []
    model.eval()
    with torch.no_grad():
        for x, y in loader:
            out = model(x)
            qs.append(out["prediction"][:, -1, :].cpu().numpy())
            ys.append(y[0][:, -1].cpu().numpy())
            origins.append(x["encoder_target"][:, -1].cpu().numpy())
    q = np.concatenate(qs)
    y = np.concatenate(ys)
    origin = np.concatenate(origins)
    levels = config.quantiles
    naive = origin[:, None] + np.quantile(horizon_returns_train, levels)[None, :]
    moments = [quantiles_to_moments(row - o, levels) for row, o in zip(q, origin, strict=True)]
    mu = np.array([m[0] for m in moments])
    sigma = np.array([m[1] for m in moments])
    realised = y - origin
    conf = np.array(
        [
            precision_weighted_confidence(m, s, 1.0, float(config.sizing["sigma_floor"]))
            for m, s in zip(mu, sigma, strict=True)
        ]
    )
    rank = pd.Series(mu).rank().corr(pd.Series(realised).rank())
    order = np.argsort(mu / np.maximum(sigma, float(config.sizing["sigma_floor"])) ** 2)
    by_quintile = [
        {
            "quintile": k + 1,
            "n": int(c.size),
            "mean_mu": float(mu[c].mean()),
            "mean_realised": float(realised[c].mean()),
        }
        for k, c in enumerate(np.array_split(order, 5))
    ]
    pinball, pinball_naive = _pinball(y, q, levels), _pinball(y, naive, levels)
    return {
        "n": int(y.size),
        "coverage": {str(p): float(np.mean(y <= q[:, j])) for j, p in enumerate(levels)},
        "pinball": pinball,
        "pinball_naive": pinball_naive,
        "pinball_skill": (1.0 - pinball / pinball_naive) if pinball_naive > 0 else None,
        "mu_rank_corr": None if math.isnan(rank) else float(rank),
        "mean_sigma": float(sigma.mean()),
        "share_buying": float(np.mean(conf > 0)),
        "by_confidence_quintile": by_quintile,
    }


def train(config: TftTrainConfig, bars: pd.DataFrame | None = None, log=print) -> dict:
    from research.ml.tft_model import deep_learning

    torch, dataset_cls, model_cls = deep_learning()
    import lightning.pytorch as pl
    from lightning.pytorch.callbacks import EarlyStopping
    from pytorch_forecasting.metrics import QuantileLoss

    started = time.monotonic()
    if bars is None:
        bars = load_bars(config)
    sources = load_sources(config.sources)
    frame = build_frame(bars, sources, config.symbol)
    cutoff = pd.Timestamp(config.validation_start)
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    stamps = pd.DatetimeIndex(frame["timestamp"])
    cut_idx = int(stamps.searchsorted(cutoff))
    L, H = config.encoder_length, config.prediction_length
    if cut_idx < L + H + 100 or len(frame) - cut_idx < H + 1:
        raise ConfigurationError(
            f"validation_start {config.validation_start} leaves {cut_idx} training and "
            f"{len(frame) - cut_idx} validation bars; need room for {L}+{H}-bar windows on both"
        )
    log(
        f"{config.symbol}: {len(frame):,} bars, training before {cutoff.date()} "
        f"({cut_idx:,}), validating after ({len(frame) - cut_idx:,}); L={L}, H={H}"
    )
    pl.seed_everything(int(config.trainer["seed"]), workers=True)
    columns = ["time_idx", "group", TARGET, *OBSERVED, *KNOWN]
    data = frame[columns]
    training = dataset_cls(data.iloc[:cut_idx], **dataset_kwargs(config))
    validation = dataset_cls.from_dataset(
        training, data, min_prediction_idx=cut_idx, stop_randomization=True
    )
    network = model_cls.from_dataset(
        training,
        loss=QuantileLoss(quantiles=list(config.quantiles)),
        output_size=len(config.quantiles),
        log_interval=-1,
        **config.model,
    )
    trainer = pl.Trainer(
        max_epochs=int(config.trainer["max_epochs"]),
        accelerator="cpu",
        gradient_clip_val=float(config.trainer["gradient_clip_val"]),
        limit_train_batches=config.trainer["limit_train_batches"],
        limit_val_batches=config.trainer["limit_val_batches"],
        callbacks=[EarlyStopping(monitor="val_loss", patience=int(config.trainer["patience"]))],
        enable_checkpointing=False,
        logger=False,
        enable_progress_bar=False,
        enable_model_summary=False,
    )
    batch = int(config.trainer["batch_size"])
    trainer.fit(
        network,
        train_dataloaders=training.to_dataloader(train=True, batch_size=batch, num_workers=0),
        val_dataloaders=validation.to_dataloader(train=False, batch_size=batch * 4, num_workers=0),
    )
    log(f"fitted {trainer.current_epoch} epoch(s) ({time.monotonic() - started:.0f}s)")
    log_close = frame[TARGET].to_numpy()
    train_horizon = log_close[H:cut_idx] - log_close[: cut_idx - H]
    metrics = evaluate(network, validation, config, train_horizon)

    out = Path(config.output)
    staging = out.with_name(f"{out.name}.tmp-{os.getpid()}")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    trainer.save_checkpoint(str(staging / CHECKPOINT))
    torch.save(training.get_parameters(), staging / DATASET)
    import lightning
    import pytorch_forecasting

    manifest = {
        "kind": KIND,
        "format_version": FORMAT_VERSION,
        "name": config.name,
        "strategy_id": STRATEGY_ID,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "versions": {
            "torch": torch.__version__,
            "lightning": lightning.__version__,
            "pytorch_forecasting": pytorch_forecasting.__version__,
        },
        "symbol": config.symbol,
        "bars_per_day": config.bars_per_day,
        "encoder_length": L,
        "prediction_length": H,
        "quantiles": list(config.quantiles),
        "target": TARGET,
        "observed": list(OBSERVED),
        "known": list(KNOWN),
        "sources": {name: config.sources.get(name) for name in SOURCES},
        "valid_from": cutoff.isoformat(),
        "data": {
            "first_bar": stamps[0].isoformat(),
            "last_bar": stamps[-1].isoformat(),
            "bars": len(frame),
            "training_bars": cut_idx,
            "source": str(config.bars_path) if config.bars_path else "warehouse",
        },
        "model": config.model,
        "trainer": {**config.trainer, "epochs_run": int(trainer.current_epoch)},
        "sizing": config.sizing,
        "validation": metrics,
        "files": {name: sha256_of(staging / name) for name in (CHECKPOINT, DATASET)},
    }
    (staging / MANIFEST).write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    backtest, baseline = run_configs(config, out)
    (staging / "backtest.yaml").write_text(yaml.safe_dump(backtest, sort_keys=False))
    (staging / "baseline.yaml").write_text(yaml.safe_dump(baseline, sort_keys=False))
    (staging / "report.md").write_text(report(manifest))
    if out.exists():
        shutil.rmtree(out)
    staging.rename(out)
    log(f"wrote {out} ({time.monotonic() - started:.0f}s)")
    return manifest


def run_configs(config: TftTrainConfig, model_dir: Path) -> tuple[dict, dict]:
    """(model, baseline): the base config from valid_from on, without its
    live block, with the strategy swapped for ml_tft in the first."""
    base = copy.deepcopy(config.base_raw)
    base.pop("live", None)
    section = dict(base.get("backtest") or {})
    section["symbol"] = config.symbol
    section["start_date"] = str(pd.Timestamp(config.validation_start).date())
    section.pop("end_date", None)
    base["backtest"] = section
    model = copy.deepcopy(base)
    params = {
        "bars_per_day": config.bars_per_day,
        "model": str(model_dir),
        **{k: v for k, v in config.sizing.items() if v is not None},
    }
    model["strategy"] = {"strategy_id": STRATEGY_ID, "strategy_params": params}
    return model, base


def _fmt(v, digits: int = 4) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    return f"{v:.{digits}f}" if isinstance(v, float) else str(v)


def report(manifest: dict) -> str:
    v = manifest["validation"]
    lines = [
        f"# TFT sizer model: {manifest['name']}",
        "",
        f"{manifest['symbol']}, trained {manifest['created_at']} on bars before "
        f"{manifest['valid_from'][:10]}; encoder {manifest['encoder_length']} bars, horizon "
        f"{manifest['prediction_length']} bars, quantiles {manifest['quantiles']}.",
        "",
        "## Validation (after the cutoff, at the horizon step)",
        "",
        f"* windows scored: {v.get('n', 0):,}",
        "* coverage (share of outcomes at or below each quantile): "
        + ", ".join(f"q{float(k) * 100:g} {_fmt(c, 3)}" for k, c in v.get("coverage", {}).items()),
        f"* pinball loss {_fmt(v.get('pinball'), 6)} vs naive {_fmt(v.get('pinball_naive'), 6)} "
        f"(skill {_fmt(v.get('pinball_skill'), 3)}; above 0 beats the naive forecast)",
        f"* rank correlation of mu with the realised return: {_fmt(v.get('mu_rank_corr'), 3)}",
        f"* share of windows with a buy (mu > 0): {_fmt(v.get('share_buying'), 3)}",
        "",
        "| confidence quintile | n | mean mu | mean realised |",
        "|---|---|---|---|",
    ]
    for row in v.get("by_confidence_quintile", []):
        lines.append(
            f"| {row['quintile']} | {row['n']:,} | {row['mean_mu']:.6f} | "
            f"{row['mean_realised']:.6f} |"
        )
    lines += [
        "",
        "## Run it",
        "",
        "```bash",
        "python cli.py backtest --config <model dir>/backtest.yaml   # ml_tft from valid_from",
        "python cli.py backtest --config <model dir>/baseline.yaml   # the base config, same window",
        "```",
        "",
        "Calibration and pinball skill are not P&L: keep the model only if the backtest beats the "
        "baseline on return and drawdown.",
        "",
    ]
    return "\n".join(lines)


def compare(config: TftTrainConfig, bars: pd.DataFrame, log=print) -> pd.DataFrame:
    """Both configs on the validation window, in-process."""
    from research.ml.meta_training import _COMPARE_COLUMNS
    from research.optimization.optimization_controller import OptimizationController
    from research.strategies.strategy_registry import resolve_strategy

    out = Path(config.output)
    frame = window(bars, str(pd.Timestamp(config.validation_start).date()), config.end_date)
    rows = []
    for label, name in (("model", "backtest.yaml"), ("baseline", "baseline.yaml")):
        cfg = BacktestConfig.from_yaml(str(out / name))
        kwargs = cfg.to_run_sweep_kwargs(resolve_strategy(cfg.strategy.strategy_id))
        kwargs["return_full_results"] = False
        result = OptimizationController(historical_data=frame).run_sweep(**kwargs).iloc[0]
        if isinstance(result.get("error"), str):
            raise ConfigurationError(f"the {label} run failed: {result['error']}")
        row = {"run": label, "strategy": cfg.strategy.strategy_id}
        row.update({c: result[c] for c in _COMPARE_COLUMNS if c in result.index})
        rows.append(row)
    table = pd.DataFrame(rows).set_index("run")
    log(f"\nvalidation window, {frame.index[0].date()} .. {frame.index[-1].date()}:")
    log(table.T.to_string())
    return table


def run_cli(config_path: str, bars_path: str | None, output: str | None, do_compare: bool) -> int:
    config = TftTrainConfig.from_yaml(config_path)
    overrides = {}
    if bars_path:
        overrides["bars_path"] = Path(bars_path)
    if output:
        overrides["output"] = Path(output)
    if overrides:
        config = TftTrainConfig(**{**vars(config), **overrides})
    bars = load_bars(config)
    manifest = train(config, bars=bars)
    v = manifest["validation"]
    print(
        f"\nvalidation: pinball skill {_fmt(v.get('pinball_skill'), 3)} vs naive, coverage "
        + ", ".join(f"{k}:{_fmt(c, 2)}" for k, c in v.get("coverage", {}).items())
    )
    print(f"report: {config.output / 'report.md'}")
    print(f"run it: python cli.py backtest --config {config.output / 'backtest.yaml'}")
    if do_compare:
        compare(config, bars)
    return 0


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_SIZING",
    "DEFAULT_TRAINER",
    "STRATEGY_ID",
    "TftTrainConfig",
    "compare",
    "dataset_kwargs",
    "evaluate",
    "load_bars",
    "report",
    "run_cli",
    "run_configs",
    "train",
]
