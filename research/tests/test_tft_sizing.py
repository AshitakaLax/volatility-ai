"""The `ml_tft` sizer (research/ml/tft_sizing.py) and its covariates
(research/ml/tft_features.py), without torch: a stub forecaster stands in
for the TFT. tests at the end train and load a real one where
pytorch-forecasting is installed (requirements-dl.txt).

  1. Quantiles become (mu, sigma) exactly for a normal, and the Swanson
     mean tracks a skewed mean; the confidence throttles as sigma^2; the
     drawdown decay compounds depth and duration.
  2. The covariates are point-in-time, the ring is the training frame's
     rows, and the decoder's known inputs follow the NYSE calendar.
  3. The sizer never exceeds max_trade_pct, buys nothing without a full
     encoder or a positive mean, reads only completed bars, forecasts at
     most once per refresh, and refuses in-sample bars and missing inputs.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from statistics import NormalDist
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.ml import tft_features as tf
from research.ml.tft_sizing import (
    TemporalFusionTransformerSizer,
    drawdown_decay,
    precision_weighted_confidence,
    quantiles_to_moments,
)
from research.optimization.optimization_controller import OptimizationController
from research.strategies.param_schema import STRATEGY_DEFAULTS
from research.strategies.strategy_registry import STRATEGIES

N = NormalDist()

# ---------------------------------------------------------------- 1. the math


@pytest.mark.parametrize(
    "levels", [(0.1, 0.5, 0.9), (0.02, 0.1, 0.25, 0.5, 0.75, 0.9, 0.98), (0.25, 0.5, 0.75)]
)
def test_a_normal_is_recovered_exactly(levels):
    mu, sigma = 0.004, 0.012
    q = [mu + sigma * N.inv_cdf(p) for p in levels]
    m, s = quantiles_to_moments(q, levels)
    assert m == pytest.approx(mu, abs=1e-12) and s == pytest.approx(sigma, rel=1e-12)


def test_the_10_50_90_formulas():
    q10, q50, q90 = -0.02, 0.001, 0.03
    m, s = quantiles_to_moments([q10, q50, q90], (0.1, 0.5, 0.9))
    assert m == pytest.approx(0.3 * q10 + 0.4 * q50 + 0.3 * q90)
    assert s == pytest.approx((q90 - q10) / (2 * 1.2815515655446004))


def test_swanson_tracks_a_skewed_mean_better_than_the_median():
    # A lognormal return 1 + r = exp(X), X ~ N(0, 0.3): right-skewed.
    levels = (0.1, 0.5, 0.9)
    q = [math.exp(0.3 * N.inv_cdf(p)) - 1 for p in levels]
    true_mean = math.exp(0.3**2 / 2) - 1
    m, _ = quantiles_to_moments(q, levels)
    assert abs(m - true_mean) < abs(q[1] - true_mean)


def test_crossed_quantiles_are_repaired():
    m, s = quantiles_to_moments([0.03, 0.0, -0.02], (0.1, 0.5, 0.9))
    assert s > 0 and m == pytest.approx(0.3 * -0.02 + 0.4 * 0.0 + 0.3 * 0.03)
    with pytest.raises(ConfigurationError):
        quantiles_to_moments([0.0, 1.0], (0.0, 0.5))


def test_confidence_is_kelly_and_throttles_with_sigma_squared():
    c = precision_weighted_confidence(0.001, 0.1, 1.0, 1e-4)
    assert c == pytest.approx(0.001 / 0.01)
    assert precision_weighted_confidence(0.001, 0.2, 1.0, 1e-4) == pytest.approx(c / 4)
    assert precision_weighted_confidence(-0.001, 0.1, 1.0, 1e-4) == 0.0
    assert precision_weighted_confidence(0.5, 0.01, 1.0, 1e-4) == 1.0  # capped
    assert precision_weighted_confidence(1e-6, 0.0, 1.0, 1e-2) == pytest.approx(1e-2)  # floored
    assert precision_weighted_confidence(float("nan"), 0.1, 1.0, 1e-4) == 0.0


def test_drawdown_decay_compounds_depth_and_duration():
    assert drawdown_decay(0.0, 0, 3.0, 0.01) == 1.0
    assert drawdown_decay(0.3, 0, 3.0, 0.01) == pytest.approx(math.exp(-0.9))
    assert drawdown_decay(0.0, 100, 3.0, 0.01) == pytest.approx(math.exp(-1.0))
    both = drawdown_decay(0.3, 100, 3.0, 0.01)
    assert both == pytest.approx(math.exp(-0.9) * math.exp(-1.0))
    assert drawdown_decay(-0.1, -5, 3.0, 0.01) == 1.0


# -------------------------------------------------------- 2. the covariates


def _csv(tmp_path, name, rows, header):
    path = tmp_path / name
    path.write_text(header + "\n" + "\n".join(rows) + "\n")
    return str(path)


def test_series_are_read_strictly_after_their_stamp(tmp_path):
    ts = _csv(
        tmp_path,
        "news.csv",
        ["2024-03-05T15:00:00Z,0.4", "2024-03-05T15:30:00Z,-0.2"],
        "timestamp,value",
    )
    s = tf.PointInTimeSeries(ts)
    at = datetime(2024, 3, 5, 15, 0, tzinfo=UTC)
    assert s.at(at) == 0.0  # the bar opening at the stamp cannot know it
    assert s.at(datetime(2024, 3, 5, 15, 1, tzinfo=UTC)) == 0.4
    assert s.at(datetime(2024, 3, 5, 16, 0, tzinfo=UTC)) == -0.2
    assert s.at(datetime(2024, 3, 5, 15, 10, tzinfo=UTC)) == 0.4  # backwards: bisected
    daily = tf.PointInTimeSeries(_csv(tmp_path, "macro.csv", ["2024-03-05,1.5"], "date,value"))
    assert daily.at(datetime(2024, 3, 5, 20, 0, tzinfo=UTC)) == 0.0  # the day is in progress
    assert daily.at(datetime(2024, 3, 6, 14, 30, tzinfo=UTC)) == 1.5
    index = pd.date_range("2024-03-05 14:30", periods=200, freq="13min", tz="UTC")
    fresh = tf.PointInTimeSeries(ts)
    assert np.array_equal(fresh.over(index), [tf.PointInTimeSeries(ts).at(t) for t in index])
    assert tf.PointInTimeSeries("").at(at) == 0.0
    with pytest.raises(ConfigurationError):
        tf.PointInTimeSeries(_csv(tmp_path, "bad.csv", ["x,1"], "when,value"))


def test_known_inputs_match_their_batch_form_across_dst():
    index = pd.date_range("2024-03-08 13:00", "2024-03-12 21:00", freq="17min", tz="UTC").append(
        pd.date_range("2024-10-31 13:00", "2024-11-05 21:00", freq="17min", tz="UTC")
    )
    batch = tf.known_frame(index)
    for i, t in enumerate(index):
        assert tf.known_at(t) == pytest.approx(tuple(batch.iloc[i]))
    assert tf.known_at(datetime(2024, 1, 3, 14, 30, tzinfo=UTC))[1:] == (0.0, 1.0)
    fomc = datetime(2024, 1, 31, 15, 0, tzinfo=UTC)  # a decision day
    assert (
        tf.known_at(fomc)[0] == 1.0 and tf.known_at(datetime(2024, 1, 30, 15, tzinfo=UTC))[0] == 0
    )


def test_future_bars_follow_the_nyse_calendar():
    last = datetime(2024, 7, 3, 19, 55, tzinfo=UTC)  # 15:55 New York, the 3rd of July
    times = tf.future_bar_times(last, 2, 78)  # 5-minute bars
    assert times[0].astimezone(tf.NEW_YORK).date() == date(2024, 7, 5)  # the 4th is a holiday
    assert times[0].astimezone(tf.NEW_YORK).strftime("%H:%M") == "09:30"
    assert times[1] - times[0] == pd.Timedelta(minutes=5)
    friday = datetime(2024, 3, 8, 20, 55, tzinfo=UTC)  # 15:55 New York
    assert tf.future_bar_times(friday, 1, 78)[0].astimezone(tf.NEW_YORK).date() == date(2024, 3, 11)
    early = datetime(2024, 3, 11, 12, 0, tzinfo=UTC)  # 08:00 New York, before the open
    assert tf.future_bar_times(early, 1, 78)[0].astimezone(tf.NEW_YORK).strftime("%H:%M") == "09:30"


def bars(days=40, per=26, seed=0):
    rng = np.random.default_rng(seed)
    sessions = pd.bdate_range("2024-01-02", periods=days)
    rows, price = [], 50.0
    for d in sessions:
        start = pd.Timestamp(d.date()).tz_localize("America/New_York") + pd.Timedelta(
            hours=9, minutes=30
        )
        for m in range(per):
            o = price
            c = price * float(np.exp(0.003 * rng.standard_normal()))
            rows.append((start + pd.Timedelta(minutes=15 * m), o, max(o, c), min(o, c), c))
            price = c
    f = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close"])
    return f.set_index(pd.DatetimeIndex(f["ts"]).tz_convert("UTC")).drop(columns="ts")


BARS = bars()


def test_the_ring_holds_the_training_frames_rows(tmp_path):
    news = _csv(
        tmp_path,
        "news.csv",
        [f"{t.isoformat()},{k / 10}" for k, t in enumerate(BARS.index[::37])],
        "timestamp,value",
    )
    sources = tf.load_sources({"s_news": news})
    frame = tf.build_frame(BARS, sources, "X")
    ring = tf.CovariateRing(30)
    live = tf.load_sources({"s_news": news})
    for t in range(500):
        ring.push_bar(BARS.index[t], BARS["close"].iloc[t], live)
    assert ring.full and ring.count == 500
    np.testing.assert_array_equal(ring.window(), frame.iloc[470:500][list(tf.ROW)].to_numpy())
    assert ring.window()[-1, 0] == pytest.approx(math.log(BARS["close"].iloc[499]))


# ------------------------------------------------------------- 3. the sizer


class StubForecaster:
    """A TFT stand-in: quantiles of log price centred `mu` above the last
    encoder close, `sigma` wide; records what it was given."""

    levels = (0.1, 0.5, 0.9)
    encoder_length = 20
    prediction_length = 4
    bars_per_day = 26
    valid_from = None
    sources: ClassVar[dict] = {"s_macro": None, "s_earnings": None, "s_news": None}

    def __init__(self, mu=0.01, sigma=0.02):
        self.mu, self.sigma = mu, sigma
        self.calls = []

    def forecast(self, encoder, decoder_known):
        self.calls.append((encoder.copy(), decoder_known.copy()))
        base = encoder[-1, 0] + self.mu
        q = [base + self.sigma * N.inv_cdf(p) for p in self.levels]
        return np.tile(q, (self.prediction_length, 1))


class StubSizer(TemporalFusionTransformerSizer):
    stub: ClassVar[StubForecaster] = StubForecaster()

    def _load_forecaster(self):
        return type(self).stub


def ctx(t, price=None, equity=1e5, drawdown=0.0, frame=BARS):
    row = frame.iloc[t]
    return MarketContext(
        timestamp=frame.index[t],
        open=row.open,
        high=row.high,
        low=row.low,
        close=row.close if price is None else price,
        cash=equity,
        equity=equity,
        peak_equity=equity,
        drawdown=drawdown,
        open_lot_count=0,
        bar_index=t,
    )


def feed(sizer, upto):
    """record_tick for bars 0 .. upto-1. Size bar upto-1 afterwards, as the
    engine does: its record_tick always comes before its trigger."""
    for t in range(upto):
        sizer.record_tick(ctx(t))


def make(**kw):
    params = {"max_trade_pct": 0.05, "bars_per_day": 26, "model": "stub", **kw}
    return StubSizer(**params)


def test_registered_with_constructible_defaults():
    assert STRATEGIES["ml_tft"] is TemporalFusionTransformerSizer
    TemporalFusionTransformerSizer(**STRATEGY_DEFAULTS["ml_tft"])  # loads nothing


def test_no_full_encoder_means_no_buy():
    StubSizer.stub = StubForecaster()
    s = make()
    feed(s, 10)
    assert s.calculate_trade_value(ctx(10)) == 0.0 and StubSizer.stub.calls == []


def test_it_never_exceeds_the_per_trade_cap():
    StubSizer.stub = StubForecaster(mu=0.5, sigma=0.001)  # absurdly confident
    s = make(kelly_scale=10.0)
    feed(s, 31)  # the engine's order: record_tick(bar 30) first
    value = s.calculate_trade_value(ctx(30))
    assert value == pytest.approx(1e5 * 0.05)
    assert s.last_confidence == 1.0


def test_size_is_cap_times_kelly_times_decay():
    StubSizer.stub = StubForecaster(mu=0.001, sigma=0.1)
    s = make(kelly_scale=1.0, dd_decay=3.0, duration_decay=0.0)
    feed(s, 31)  # the engine's order: record_tick(bar 30) first
    entry = BARS.close.iloc[29]  # the forecast's own origin: mu is exactly the stub's
    value = s.calculate_trade_value(ctx(30, price=entry))
    assert s.last_mu == pytest.approx(0.001) and s.last_sigma == pytest.approx(0.1)
    assert value == pytest.approx(1e5 * 0.05 * 0.001 / 0.1**2)
    deep = s.calculate_trade_value(ctx(30, price=entry, drawdown=0.3))
    assert deep == pytest.approx(value * math.exp(-0.9))
    lower = s.calculate_trade_value(ctx(30, price=entry * 0.99))  # a deeper fill expects more
    assert lower > value


def test_a_non_positive_mean_or_low_confidence_buys_nothing():
    StubSizer.stub = StubForecaster(mu=-0.01, sigma=0.02)
    s = make()
    feed(s, 31)  # the engine's order: record_tick(bar 30) first
    assert s.calculate_trade_value(ctx(30)) == 0.0
    StubSizer.stub = StubForecaster(mu=0.0005, sigma=0.05)
    s = make(min_confidence=0.5)
    feed(s, 31)  # the engine's order: record_tick(bar 30) first
    assert s.calculate_trade_value(ctx(30, price=BARS.close.iloc[29])) == 0.0  # C = 0.1


def test_uncertainty_quarters_the_buy_when_sigma_doubles():
    values = []
    for sigma in (0.05, 0.1):
        StubSizer.stub = StubForecaster(mu=0.001, sigma=sigma)  # below the cap
        s = make(kelly_scale=1.0)
        feed(s, 31)  # the engine's order: record_tick(bar 30) first
        values.append(s.calculate_trade_value(ctx(30, price=BARS.close.iloc[29])))
    assert values[1] == pytest.approx(values[0] / 4)


def test_it_reads_only_completed_bars_and_the_calendar():
    """At bar t the encoder ends at t-1 and the decoder starts at t."""
    StubSizer.stub = StubForecaster()
    s = make()
    feed(s, 31)
    s.calculate_trade_value(ctx(30))
    encoder, decoder = StubSizer.stub.calls[-1]
    assert encoder.shape == (20, len(tf.ROW))
    assert encoder[-1, 0] == pytest.approx(math.log(BARS.close.iloc[29]))
    assert tuple(decoder[0]) == pytest.approx(tf.known_at(BARS.index[30]))
    assert decoder.shape == (4, len(tf.KNOWN))


def test_one_forecast_per_refresh():
    StubSizer.stub = StubForecaster()
    s = make(refresh_bars=5)
    feed(s, 21)
    for t in range(21, 31):
        s.record_tick(ctx(t))
        s.calculate_trade_value(ctx(t))
    assert s.forecasts == 2  # bars 21 and 26


def test_sessions_underwater_count_and_reset():
    StubSizer.stub = StubForecaster()
    s = make()
    for t in range(0, 26 * 3):
        s.record_tick(ctx(t, drawdown=0.1))
    assert s._underwater == 3
    s.record_tick(ctx(26 * 3, drawdown=0.0))
    assert s._underwater == 0


def test_in_sample_bars_are_refused():
    StubSizer.stub = StubForecaster()
    StubSizer.stub.valid_from = BARS.index[100]
    s = make()
    feed(s, 31)
    with pytest.raises(ConfigurationError, match="training data"):
        s.calculate_trade_value(ctx(30))
    s = make(allow_in_sample=True)
    feed(s, 31)
    assert s.calculate_trade_value(ctx(30)) > 0


def test_inputs_must_match_training(tmp_path):
    news = _csv(tmp_path, "n.csv", ["2024-01-01,0.1"], "date,value")
    StubSizer.stub = StubForecaster()
    with pytest.raises(ConfigurationError, match="without a s_news"):
        make(news_path=news).ensure_model_available()
    with pytest.raises(ConfigurationError, match="bars a day"):
        make(bars_per_day=78).ensure_model_available()


def test_a_trained_series_is_required_at_trade_time(tmp_path):
    news = _csv(tmp_path, "n.csv", ["2024-01-01,0.1"], "date,value")
    trained = StubForecaster()
    trained.sources = {"s_macro": None, "s_earnings": None, "s_news": news}
    StubSizer.stub = trained
    make().ensure_model_available()  # the manifest's path is used
    trained.sources = {"s_macro": None, "s_earnings": None, "s_news": str(tmp_path / "gone.csv")}
    with pytest.raises(ConfigurationError, match="not found"):
        make().ensure_model_available()


def test_through_the_real_controller():
    StubSizer.stub = StubForecaster(mu=0.004, sigma=0.01)
    result = (
        OptimizationController(historical_data=BARS)
        .run_sweep(
            grid_steps=[0.003],
            profit_targets=[0.004],
            strategy_class=StubSizer,
            strategy_params_grid=[
                {"max_trade_pct": 0.05, "bars_per_day": 26, "model": "stub", "lookback_days": 0.5}
            ],
            fill_model="intrabar",
            intrabar_fill="causal",
        )
        .iloc[0]
    )
    assert "error" not in result or not isinstance(result["error"], str)
    assert result["Trade Count"] > 0
    assert "lots_to_liquidate" not in TemporalFusionTransformerSizer.__dict__


def test_the_rolling_high_is_optional():
    assert make()._rolling_high is None
    assert make(lookback_days=0.5)._rolling_high is not None


def test_live_history_covers_the_encoder():
    StubSizer.stub = StubForecaster()
    s = make()
    s.ensure_model_available()
    assert s.live_history_sessions() * 26 >= StubSizer.stub.encoder_length


# ------------------------------------------- with the real TFT, where installed


def test_a_real_tft_trains_loads_and_matches_its_dataset(tmp_path):
    pytest.importorskip("pytorch_forecasting")
    import torch
    import yaml

    from research.ml import tft_training as tt
    from research.ml.tft_model import TftForecaster

    long = bars(days=90, per=26, seed=3)
    base = tmp_path / "base.yaml"
    base.write_text(
        yaml.safe_dump(
            {
                "strategy": {
                    "strategy_id": "hf_local_reference",
                    "strategy_params": {
                        "bars_per_day": 26,
                        "per_lot_pct": 0.002,
                        "lookback_days": 0.2,
                    },
                },
                "grid": {"steps": [0.003], "profit_targets": [0.004]},
                "backtest": {"symbol": "SYN", "initial_cash": 100000.0},
                "costs": {"model_type": "zero"},
            }
        )
    )
    config = tt.TftTrainConfig.from_dict(
        {
            "kind": "tft",
            "name": "t",
            "base_config": str(base),
            "validation_start": str(long.index[26 * 70].date()),
            "bars_per_day": 26,
            "encoder_length": 20,
            "prediction_length": 4,
            "trainer": {
                "max_epochs": 1,
                "batch_size": 32,
                "limit_train_batches": 5,
                "limit_val_batches": 2,
            },
            "eval_samples": 200,
            "output": str(tmp_path / "model"),
        }
    )
    manifest = tt.train(config, bars=long, log=lambda *_: None)
    assert manifest["validation"]["n"] > 0
    fc = TftForecaster(config.output)
    frame = tf.build_frame(long, tf.load_sources({}), "SYN")
    t = 26 * 75
    enc = frame.iloc[t - 20 : t][list(tf.ROW)].to_numpy()
    dec = frame.iloc[t : t + 4][list(tf.KNOWN)].to_numpy()
    q = fc.forecast(enc, dec)
    ds = fc._dataset_cls.from_parameters(
        fc.parameters,
        frame[["time_idx", "group", *tf.ROW]].iloc[t - 20 : t + 4].reset_index(drop=True),
        predict=True,
        stop_randomization=True,
    )
    x, _ = next(iter(ds.to_dataloader(train=False, batch_size=1)))
    with torch.no_grad():
        ref = fc.network(x)["prediction"][0].numpy()
    np.testing.assert_allclose(q, ref, atol=1e-6)
    assert q.shape == (4, 3) and np.all(np.diff(np.sort(q[-1])) >= 0)
    (tmp_path / "model" / "model.ckpt").write_bytes(b"tampered")
    with pytest.raises(ConfigurationError, match="SHA-256"):
        TftForecaster(config.output)
