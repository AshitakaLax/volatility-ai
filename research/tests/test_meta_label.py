"""The meta-label line: research/ml/meta_features.py, meta_dataset.py,
meta_training.py, meta_model.py and the `ml_meta_label` strategy.

  1. The features are causal, and the strategy computes inside the real
     engine exactly the vectors the dataset builder trained on.
  2. The triple-barrier labels match a brute-force walk; the uniqueness
     weights match their definition.
  3. The walk-forward never trains a segment on a label resolved after
     its start (minus the embargo), and the shuffled-label control sits
     at chance.
  4. The artifact is checked on load, and answers only from a segment's
     own start.
  5. The strategy is hf_local_reference exactly whenever the model has no
     say, only ever shrinks or skips a buy, and refuses a model trained
     for another trigger.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest
import yaml

from engine.core.exceptions import ConfigurationError
from research.ml import meta_dataset as md
from research.ml.meta_features import (
    FEATURE_NAMES,
    MetaFeatures,
    session_clock,
    session_clock_arrays,
)
from research.optimization.optimization_controller import OptimizationController
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from research.strategies.param_schema import STRATEGY_DEFAULTS
from research.strategies.strategy_registry import STRATEGIES

lgb = pytest.importorskip("lightgbm")
pytest.importorskip("sklearn")

from research.ml import meta_training as mt  # noqa: E402
from research.ml.meta_label_sizing import MetaLabelSizing  # noqa: E402
from research.ml.meta_model import MetaLabelModel  # noqa: E402

BARS_PER_DAY = 26  # 15-minute bars
LOOKBACK_DAYS = 0.25
STEP, TARGET = 0.003, 0.004
OUTCOMES = ("Final Equity", "Realized PnL", "Trade Count", "Closed Trade Count", "Max Drawdown %")


def synthetic_bars(days: int = 260, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    sessions = pd.bdate_range("2021-01-04", periods=days)
    rows, price, regime = [], 40.0, 0
    for d in sessions:
        if rng.random() < 0.03:
            regime = 1 - regime
        mu, sd = (0.0002, 0.002) if regime == 0 else (-0.0002, 0.006)
        open_at = pd.Timestamp(d.date()).tz_localize("America/New_York") + pd.Timedelta(
            hours=9, minutes=30
        )
        for m in range(BARS_PER_DAY):
            o = price
            c = price * float(np.exp(mu + sd * rng.standard_normal()))
            h = max(o, c) * (1 + abs(rng.normal(0, sd / 3)))
            lo = min(o, c) * (1 - abs(rng.normal(0, sd / 3)))
            rows.append((open_at + pd.Timedelta(minutes=15 * m), o, h, lo, c, 1000.0))
            price = c
    frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    return frame.set_index(pd.DatetimeIndex(frame["timestamp"]).tz_convert("UTC")).drop(
        columns="timestamp"
    )


BARS = synthetic_bars()
HF = {"per_lot_pct": 0.002, "lookback_days": LOOKBACK_DAYS, "bars_per_day": BARS_PER_DAY}


def base_config(tmp_path, fill_model="intrabar", intrabar_fill="causal"):
    path = tmp_path / "base.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "strategy": {"strategy_id": "hf_local_reference", "strategy_params": dict(HF)},
                "grid": {"steps": [STEP], "profit_targets": [TARGET]},
                "backtest": {"symbol": "SYN", "initial_cash": 100000.0},
                "costs": {"model_type": "zero"},
                "execution": {
                    "fill_model": fill_model,
                    "intrabar_fill": intrabar_fill,
                    "enforce_no_loss": True,
                },
                "live": {"enabled": False, "step": STEP, "profit_target": TARGET},
            }
        )
    )
    return path


def train_config(tmp_path, **overrides):
    data = {
        "name": "syn",
        "base_config": str(base_config(tmp_path)),
        "label": {"max_hold_days": 1.0, "stop": 0.01},
        "walk_forward": {"min_train_days": 120, "refit_days": 60, "min_train_rows": 100},
        "model": {"num_boost_round": 60, "early_stopping_rounds": 10, "min_data_in_leaf": 20},
        "output": str(tmp_path / "model"),
    }
    data.update(overrides)
    return mt.TrainConfig.from_dict(data)


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("meta")
    config = train_config(tmp)
    manifest = mt.train(config, bars=BARS, log=lambda *_: None)
    return config, manifest


def run(cls, params, fill_model="intrabar", intrabar_fill="causal", bars=BARS):
    return (
        OptimizationController(historical_data=bars)
        .run_sweep(
            grid_steps=[STEP],
            profit_targets=[TARGET],
            strategy_class=cls,
            strategy_params_grid=[params],
            fill_model=fill_model,
            intrabar_fill=intrabar_fill,
        )
        .iloc[0]
    )


# ------------------------------------------------------------- 1. features


def test_session_clock_scalar_matches_the_batch_form_across_dst():
    index = pd.date_range("2024-03-08 13:00", "2024-03-12 21:00", freq="13min", tz="UTC").append(
        pd.date_range("2024-10-31 13:00", "2024-11-05 21:00", freq="13min", tz="UTC")
    )
    day, minute, weekday = session_clock_arrays(index)
    for i, ts in enumerate(index):
        d, m, w = session_clock(ts)
        assert (d, w) == (day[i], weekday[i])
        assert m == pytest.approx(minute[i])
    # 09:30 New York is minute 0 in both winter and summer time.
    assert session_clock(datetime(2024, 1, 3, 14, 30, tzinfo=UTC))[1] == 0
    assert session_clock(datetime(2024, 7, 3, 13, 30, tzinfo=UTC))[1] == 0


def test_a_snapshot_never_reads_its_own_bar_or_later():
    """The vector at bar t is the same whatever bar t's high, low and close
    turn out to be, and whatever follows."""
    signal = md.PrimarySignal(STEP, LOOKBACK_DAYS, BARS_PER_DAY, "intrabar", "causal")
    pos, entries = md.trigger_events(BARS, signal)
    t = int(pos[len(pos) // 2])
    before = md.feature_rows(BARS, np.array([t]), entries[[len(pos) // 2]], signal)
    wild = BARS.copy()
    wild.iloc[t, wild.columns.get_loc("high")] *= 3
    wild.iloc[t, wild.columns.get_loc("low")] *= 0.2
    wild.iloc[t:, wild.columns.get_loc("close")] *= 1.7
    after = md.feature_rows(wild, np.array([t]), entries[[len(pos) // 2]], signal)
    np.testing.assert_array_equal(before, after)


class _Recording(MetaLabelSizing):
    seen: ClassVar[dict] = {}

    def calculate_trade_value(self, context):
        value = super().calculate_trade_value(context)
        day, minute, weekday = self._pending_clock
        row = self._features.snapshot(day, minute, weekday, self._pending[1], context.price)
        _Recording.seen[context.bar_index] = (row, context.price)
        return value


@pytest.mark.parametrize(
    ("fill_model", "intrabar_fill"),
    [("close", "level"), ("intrabar", "causal"), ("intrabar", "open_or_level")],
)
def test_the_strategy_sees_the_vectors_the_builder_trained_on(trained, fill_model, intrabar_fill):
    """Through the real controller: wherever the engine asks for a size on
    a bar the builder also counted as a trigger, the entry price and the
    feature vector are the builder's, bit for bit."""
    config, _ = trained
    _Recording.seen = {}
    run(
        _Recording,
        {**HF, "model": str(config.output), "skip_below": 0.0, "full_size_at": 0.0},
        fill_model=fill_model,
        intrabar_fill=intrabar_fill,
    )
    signal = md.PrimarySignal(STEP, LOOKBACK_DAYS, BARS_PER_DAY, fill_model, intrabar_fill)
    pos, entries = md.trigger_events(BARS, signal)
    rows = md.feature_rows(BARS, pos, entries, signal)
    built = {int(p): (rows[i], entries[i]) for i, p in enumerate(pos)}
    compared = 0
    for b in (b for b in _Recording.seen if b in built):
        row, price = _Recording.seen[b]
        if price != pytest.approx(built[b][1]):
            continue  # the last fill, not the rolling high, set this level
        np.testing.assert_array_equal(row, built[b][0])
        compared += 1
    assert compared > 200, compared


# --------------------------------------------------------------- 2. labels


def brute_label(high, low, entry, t0, target, stop, horizon):
    up, dn = entry * (1 + target), entry * (1 - stop) if stop else None
    for t in range(t0 + 1, min(t0 + horizon, len(high) - 1) + 1):
        hit_up, hit_dn = high[t] >= up, dn is not None and low[t] <= dn
        if hit_up and not hit_dn:
            return 1, t
        if hit_dn:
            return 0, t
    return 0, min(t0 + horizon, len(high) - 1)


@pytest.mark.parametrize("stop", [None, 0.004])
def test_barrier_outcomes_match_a_brute_force_walk(stop):
    signal = md.PrimarySignal(STEP, LOOKBACK_DAYS, BARS_PER_DAY)
    label = md.BarrierLabel(TARGET, 40, stop)
    pos, entries = md.trigger_events(BARS, signal)
    out = md.barrier_outcomes(BARS, pos, entries, label)
    high, low = BARS["high"].to_numpy(), BARS["low"].to_numpy()
    checked = 0
    for row in out.dropna(subset=["label"]).itertuples():
        i = int(np.searchsorted(pos, row.t0))
        y, t1 = brute_label(high, low, entries[i], row.t0, TARGET, stop, 40)
        assert (row.label, row.t1) == (y, t1)
        checked += 1
    assert checked > 100
    assert out["label"].isna().sum() > 0  # the last window is incomplete, not shortened


def test_average_uniqueness_matches_its_definition():
    t0 = np.array([0, 1, 2, 10])
    t1 = np.array([3, 3, 6, 12])
    u = md.average_uniqueness(t0, t1, 20)
    windows = [range(a + 1, b + 1) for a, b in zip(t0, t1, strict=True)]
    for k, w in enumerate(windows):
        conc = [sum(b in v for v in windows) for b in w]
        assert u[k] == pytest.approx(np.mean([1 / c for c in conc]))


def test_the_dataset_is_sorted_and_complete(trained):
    config, _ = trained
    frame = md.build_dataset(BARS, config.signal, config.label)
    assert list(frame.columns[: len(FEATURE_NAMES)]) == list(FEATURE_NAMES)
    assert frame["t0"].is_monotonic_increasing
    assert (frame["t1"] >= frame["t0"]).all()
    assert set(frame["label"].unique()) <= {0, 1}
    assert ((frame["weight"] > 0) & (frame["weight"] <= 1)).all()


# ----------------------------------------------------------- 3. walk-forward


def test_no_segment_trains_on_a_label_resolved_after_its_start(trained, monkeypatch):
    config, _ = trained
    frame = md.build_dataset(BARS, config.signal, config.label)
    seen = []
    real = mt._fit_segment

    def spy(lgb_, data, rows, *rest):
        seen.append(rows.copy())
        return real(lgb_, data, rows, *rest)

    monkeypatch.setattr(mt, "_fit_segment", spy)
    records, _, oos = mt.walk_forward(frame, config, BARS.index[-1], log=lambda *_: None)
    embargo = pd.Timedelta(days=config.walk_forward.embargo_days)
    trained_records = [r for r in records if "skipped" not in r]
    assert len(seen) == len(trained_records) >= 3
    for rows, record in zip(seen, records, strict=False):
        start = pd.Timestamp(record["valid_from"])
        assert (frame["ts1"].iloc[rows] < start - embargo).all()
    # Every scored row starts at or after the segment that scored it.
    first = pd.Timestamp(trained_records[0]["valid_from"])
    assert (frame["ts0"][~np.isnan(oos)] >= first).all()
    assert np.isnan(oos[(frame["ts0"] < first).to_numpy()]).all()


def test_the_artifact_and_its_report(trained):
    config, manifest = trained
    out = config.output
    for name in (
        "manifest.json",
        "report.md",
        "backtest.yaml",
        "baseline.yaml",
        "oos_predictions.csv",
    ):
        assert (out / name).exists(), name
    assert manifest["features"]["names"] == list(FEATURE_NAMES)
    assert manifest["segments"][-1]["valid_from"] == BARS.index[-1].isoformat()
    starts = [pd.Timestamp(s["valid_from"]) for s in manifest["segments"]]
    assert starts == sorted(starts)
    control = manifest["control"]["mean_auc"]
    assert control is not None and abs(control - 0.5) < 0.08
    backtest = yaml.safe_load((out / "backtest.yaml").read_text())
    assert backtest["strategy"]["strategy_id"] == "ml_meta_label"
    assert backtest["strategy"]["strategy_params"]["model"] == str(out)
    assert "live" not in backtest
    assert yaml.safe_load((out / "baseline.yaml").read_text())["strategy"]["strategy_id"] == (
        "hf_local_reference"
    )


def test_training_config_refusals(tmp_path):
    with pytest.raises(ConfigurationError, match="ONE grid step"):
        path = base_config(tmp_path)
        data = yaml.safe_load(path.read_text())
        data["grid"]["steps"] = [0.001, 0.002]
        path.write_text(yaml.safe_dump(data))
        mt.TrainConfig.from_dict({"name": "x", "base_config": str(path)})
    with pytest.raises(ConfigurationError, match="unknown training config keys"):
        mt.TrainConfig.from_dict({"name": "x", "base_config": str(base_config(tmp_path)), "x": 1})


# --------------------------------------------------------------- 4. artifact


def test_a_changed_booster_is_refused(trained, tmp_path):
    config, manifest = trained
    import shutil

    copy = tmp_path / "copy"
    shutil.copytree(config.output, copy)
    seg = copy / manifest["segments"][0]["file"]
    seg.write_text(seg.read_text() + "\n")
    with pytest.raises(ConfigurationError, match="SHA-256"):
        MetaLabelModel(copy)


def test_segments_answer_only_from_their_own_start(trained):
    config, manifest = trained
    model = MetaLabelModel(config.output)
    first = pd.Timestamp(manifest["segments"][0]["valid_from"])
    row = np.zeros(len(FEATURE_NAMES))
    assert model.probability(first - pd.Timedelta(minutes=1), row) is None
    p = model.probability(first, row)
    assert p is not None and 0.0 <= p <= 1.0
    assert model.segment_for(BARS.index[-1] + pd.Timedelta(days=400)) is model.segments[-1]
    assert model.segment_for(first) is model.segments[0]


def test_a_missing_model_names_the_command():
    with pytest.raises(ConfigurationError, match=r"cli\.py train"):
        MetaLabelModel("does/not/exist")


# --------------------------------------------------------------- 5. strategy


def test_registered_with_constructible_defaults():
    assert STRATEGIES["ml_meta_label"] is MetaLabelSizing
    MetaLabelSizing(**STRATEGY_DEFAULTS["ml_meta_label"])  # loads nothing


def test_with_the_model_silenced_it_is_hf_local_reference_exactly(trained):
    config, _ = trained
    base = run(HighFrequencyLocalReferenceSizing, HF)
    silenced = run(
        MetaLabelSizing, {**HF, "model": str(config.output), "skip_below": 0.0, "full_size_at": 0.0}
    )
    assert base["Trade Count"] > 0
    for col in OUTCOMES:
        assert silenced[col] == base[col], col


def test_before_the_first_segment_it_is_hf_local_reference_exactly(trained):
    config, manifest = trained
    first = pd.Timestamp(manifest["segments"][0]["valid_from"])
    early = BARS[BARS.index < first]
    base = run(HighFrequencyLocalReferenceSizing, HF, bars=early)
    gated = run(
        MetaLabelSizing, {**HF, "model": str(config.output), "skip_below": 0.99}, bars=early
    )
    for col in OUTCOMES:
        assert gated[col] == base[col], col


def test_the_model_only_shrinks_or_skips(trained):
    config, _ = trained
    strategy = MetaLabelSizing(**HF, model=str(config.output))
    assert [strategy.multiplier(p) for p in (0.0, 0.49, 0.5, 0.6, 0.7, 1.0)] == pytest.approx(
        [0.0, 0.0, 0.5, 0.75, 1.0, 1.0]
    )
    base = run(HighFrequencyLocalReferenceSizing, HF)
    strict = run(MetaLabelSizing, {**HF, "model": str(config.output), "skip_below": 0.9})
    assert strict["Trade Count"] < base["Trade Count"]
    assert "lots_to_liquidate" not in MetaLabelSizing.__dict__


def test_refuses_a_model_trained_for_another_trigger(trained):
    config, _ = trained
    with pytest.raises(ConfigurationError, match="lookback_days"):
        MetaLabelSizing(
            **{**HF, "lookback_days": 0.5}, model=str(config.output)
        ).ensure_model_available()
    strategy = MetaLabelSizing(**HF, model=str(config.output))
    with pytest.raises(ConfigurationError, match="grid step"):
        strategy._grid_trigger_level(None, 100.0, STEP * 2)


def test_warm_up_seeds_the_session_features():
    f = MetaFeatures(BARS_PER_DAY, 6)
    assert f.warm_up([100.0 * 1.001**k for k in range(260)]) == 260
    row = dict(zip(FEATURE_NAMES, f.snapshot(800000, 0.0, 1, 130.0, 130.0), strict=True))
    assert not np.isnan(row["d_sma200"]) and not np.isnan(row["d_dd_252"])
    assert row["d_down_streak"] == 0
    with pytest.raises(ConfigurationError):
        f.warm_up([1.0])


def test_live_replays_enough_sessions_for_every_feature():
    strategy = MetaLabelSizing(**STRATEGY_DEFAULTS["ml_meta_label"])
    assert strategy.live_history_sessions() >= 253


def test_manifest_is_plain_json(trained):
    config, _ = trained
    json.loads((config.output / "manifest.json").read_text())


def test_naive_timestamps_read_as_utc():
    naive = datetime(2024, 1, 3, 14, 30)
    assert session_clock(naive) == session_clock(naive.replace(tzinfo=UTC))
    assert session_clock(naive + timedelta(minutes=5))[1] == 5


def test_check_run_refuses_another_step_or_target_before_any_bar(trained):
    config, _ = trained
    strategy = MetaLabelSizing(**HF, model=str(config.output))
    strategy.check_run([STEP], [TARGET])  # the trained pair
    with pytest.raises(ConfigurationError, match="grid step"):
        strategy.check_run([STEP, STEP * 2], [TARGET])
    with pytest.raises(ConfigurationError, match="profit target"):
        strategy.check_run([STEP], [TARGET * 3])
    with pytest.raises(ConfigurationError, match="No meta-label model"):
        MetaLabelSizing(**HF, model="nowhere").check_run([STEP], [TARGET])
    assert strategy._model is None  # the manifest alone; no booster loaded
