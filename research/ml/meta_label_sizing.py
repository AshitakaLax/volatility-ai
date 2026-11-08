"""`ml_meta_label`: the champion grid, with each buy sized by a trained
meta-label model's probability that the lot reaches its target.

--------------------------------------------------------------------
WHAT IT CHANGES, AND WHAT IT CANNOT

Everything hf_local_reference does is unchanged: the rolling-reference
trigger (so the stranding fix carries over), the per-lot dollar size and
every scaler on it, trailing targets, the event boosts. The model is asked
one question per buy the trigger has already decided on:

    p = P(this lot touches its profit target within the training horizon,
          before the optional stop)                  -- calibrated

and the buy is multiplied by

    0                                            p <  skip_below
    size_floor .. 1, linearly                    skip_below <= p < full_size_at
    1                                            p >= full_size_at

so the model can skip or shrink a buy and never grow one past the base
size. It does not move a target, sell, or touch the no-loss guard. A
skipped buy costs foregone profit, never a realised loss.

Before the artifact's first walk-forward segment there is no model (none
had been trained by then) and the multiplier is 1: the run is the base
strategy, exactly. From then on each bar is answered by the segment fitted
on labels resolved before that segment began, so a backtest over the whole
history is out of sample everywhere the model speaks (research/ml/
meta_model.py). Live, the last segment answers: the one trained on
everything.

--------------------------------------------------------------------
THE FEATURES ARE THE TRAINING FEATURES, BY CONSTRUCTION

research/ml/meta_features.MetaFeatures is fed here exactly as the dataset
builder feeds it: at bar t the state holds bars up to t-1, the snapshot
adds bar t's time, open and the entry price, and bar t is folded in at the
next record_tick. The entry price is the sizing context's price, which the
engine sets to the fill price under fill_model="intrabar".

--------------------------------------------------------------------
THE MODEL MUST MATCH THE RUN

A model is trained for one trigger (step, lookback_days, bars_per_day,
fill model) and one lot target. This class refuses a run whose
lookback_days, bars_per_day or grid step differ from the artifact's; the
profit target and the fund are not visible to a strategy, so the
`backtest.yaml` the trainer writes carries the ones the model was trained
for. Train a model per configuration you mean to trade.

lightgbm and the artifact are loaded on the first bar, not at
construction, so the registry, the parameter schema and the server work on
a machine with neither (research/ml/meta_model.py).
"""

from __future__ import annotations

import math

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.ml.meta_features import DAILY_HISTORY_SESSIONS, MetaFeatures, session_clock
from research.ml.meta_model import MetaLabelModel, read_manifest
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from research.strategies.sizing_indicators import bars_from_days, clamp

DEFAULT_MODEL_DIR = "data/ml/models/meta_label_tqqq"


class MetaLabelSizing(HighFrequencyLocalReferenceSizing):
    """hf_local_reference, each buy multiplied by the model's verdict."""

    def __init__(
        self,
        per_lot_pct: float,
        lookback_days: float,
        bars_per_day: int,
        event_day_boost_multiplier: float = 1.0,
        earnings_day_boost_multiplier: float = 1.0,
        vol_scale_exponent: float = 0.0,
        vol_fast_days: float = 0.5,
        vol_slow_days: float = 20.0,
        vol_scale_min: float = 0.5,
        vol_scale_max: float = 2.0,
        time_of_day_exponent: float = 0.0,
        vol_measure: str = "stdev",
        volume_scale_exponent: float = 0.0,
        trail_pct: float | None = None,
        trail_min_profit_target: float = 0.001,
        weighted_event_boost_multiplier: float = 1.0,
        dd_throttle_start: float | None = None,
        dd_throttle_full: float = 0.60,
        dd_throttle_floor: float = 0.25,
        implied_vol_exponent: float = 0.0,
        implied_vol_scale_min: float = 0.5,
        implied_vol_scale_max: float = 2.0,
        model: str = DEFAULT_MODEL_DIR,
        skip_below: float = 0.5,
        full_size_at: float = 0.7,
        size_floor: float = 0.5,
    ) -> None:
        super().__init__(
            per_lot_pct=per_lot_pct,
            lookback_days=lookback_days,
            bars_per_day=bars_per_day,
            event_day_boost_multiplier=event_day_boost_multiplier,
            earnings_day_boost_multiplier=earnings_day_boost_multiplier,
            vol_scale_exponent=vol_scale_exponent,
            vol_fast_days=vol_fast_days,
            vol_slow_days=vol_slow_days,
            vol_scale_min=vol_scale_min,
            vol_scale_max=vol_scale_max,
            time_of_day_exponent=time_of_day_exponent,
            vol_measure=vol_measure,
            volume_scale_exponent=volume_scale_exponent,
            trail_pct=trail_pct,
            trail_min_profit_target=trail_min_profit_target,
            weighted_event_boost_multiplier=weighted_event_boost_multiplier,
            dd_throttle_start=dd_throttle_start,
            dd_throttle_full=dd_throttle_full,
            dd_throttle_floor=dd_throttle_floor,
            implied_vol_exponent=implied_vol_exponent,
            implied_vol_scale_min=implied_vol_scale_min,
            implied_vol_scale_max=implied_vol_scale_max,
        )
        for name, value in (
            ("skip_below", skip_below),
            ("full_size_at", full_size_at),
            ("size_floor", size_floor),
        ):
            if not 0.0 <= value <= 1.0:
                raise ConfigurationError(f"{name} must be in [0, 1], got {value}")
        if not model:
            raise ConfigurationError("model must name a trained model directory")
        self.model = model
        self.skip_below = skip_below
        self.full_size_at = full_size_at
        self.size_floor = size_floor
        self._model: MetaLabelModel | None = None
        self._features = MetaFeatures(bars_per_day, bars_from_days(lookback_days, bars_per_day))
        self._pending: tuple | None = None
        self._pending_clock: tuple[int, float, int] = (0, 0.0, 0)
        self._pending_ts = None
        self._step_checked = False
        self.last_probability: float | None = None
        self.decisions = 0
        self.skipped = 0

    # -- the model -------------------------------------------------------

    def ensure_model_available(self) -> MetaLabelModel:
        """Load and check the artifact now (the first bar does it anyway;
        a startup check can call it to fail before a session)."""
        if self._model is None:
            loaded = MetaLabelModel(self.model)
            primary = loaded.primary
            mismatched = [
                f"{key} {primary[key]} (this run: {mine})"
                for key, mine in (
                    ("lookback_days", self.lookback_days),
                    ("bars_per_day", self.bars_per_day),
                )
                if not math.isclose(float(primary[key]), float(mine))
            ]
            if mismatched:
                raise ConfigurationError(
                    f"{self.model} was trained for " + ", ".join(mismatched) + ". Retrain for "
                    "this configuration, or run the backtest.yaml written beside the model."
                )
            self._model = loaded
        return self._model

    def check_run(self, grid_steps, profit_targets) -> None:
        """Refuse, before a run starts, a model trained for another trigger
        or lot target -- from the manifest alone, no booster loaded. The
        server and `cli.py backtest` call it: inside the sweep the same
        refusal would become a failed-combination row, and the caller
        would see "rank_by column not found" instead of the reason."""
        manifest = read_manifest(self.model)
        primary, label = manifest["primary"], manifest["label"]
        problems = [
            f"{key} {primary[key]} (this run: {mine})"
            for key, mine in (
                ("lookback_days", self.lookback_days),
                ("bars_per_day", self.bars_per_day),
            )
            if not math.isclose(float(primary[key]), float(mine))
        ]
        problems += [
            f"grid step {primary['step']} (this run: {s})"
            for s in grid_steps
            if not math.isclose(float(primary["step"]), float(s))
        ]
        problems += [
            f"profit target {label['profit_target']} (this run: {t})"
            for t in profit_targets
            if not math.isclose(float(label["profit_target"]), float(t))
        ]
        if problems:
            raise ConfigurationError(
                f"{self.model} was trained for " + ", ".join(problems) + ". Retrain for this "
                "configuration, or run the backtest.yaml written beside the model."
            )

    @property
    def model_fingerprint(self) -> str | None:
        return None if self._model is None else self._model.fingerprint

    def multiplier(self, probability: float) -> float:
        if probability < self.skip_below:
            return 0.0
        if self.full_size_at <= self.skip_below:
            return 1.0
        frac = clamp((probability - self.skip_below) / (self.full_size_at - self.skip_below), 0, 1)
        return self.size_floor + (1.0 - self.size_floor) * frac

    # -- the engine's calls ---------------------------------------------

    def warm_up(self, daily) -> int:
        """Seed the completed-session features from the history before a
        windowed backtest's first bar (session OHLC, natr_regime.daily_bars'
        shape). The live loop replays bars instead (live_history_sessions)."""
        return self._features.warm_up(daily["close"].tolist())

    def live_history_sessions(self) -> int:
        return max(super().live_history_sessions(), DAILY_HISTORY_SESSIONS + 5)

    def record_tick(self, context: MarketContext) -> None:
        super().record_tick(context)
        self.ensure_model_available()
        if self._pending is not None:
            day, open_, high, low, close = self._pending
            self._features.fold(day, open_, high, low, close)
        day, minute, weekday = session_clock(context.timestamp)
        self._pending = (day, context.open, context.high, context.low, context.close)
        self._pending_clock = (day, minute, weekday)
        self._pending_ts = context.timestamp

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        if not self._step_checked:
            trained = float(self.ensure_model_available().primary["step"])
            if not math.isclose(trained, step):
                raise ConfigurationError(
                    f"{self.model} was trained for grid step {trained}; this run uses {step}. "
                    "Retrain for this step, or run the backtest.yaml written beside the model."
                )
            self._step_checked = True
        return super()._grid_trigger_level(context, last_buy_price, step)

    def calculate_trade_value(self, context: MarketContext) -> float:
        value = super().calculate_trade_value(context)
        if value <= 0 or self._pending is None:
            return value
        day, minute, weekday = self._pending_clock
        row = self._features.snapshot(day, minute, weekday, self._pending[1], context.price)
        probability = self.ensure_model_available().probability(self._pending_ts, row)
        self.last_probability = probability
        if probability is None:
            return value  # before the first segment: the base strategy
        self.decisions += 1
        m = self.multiplier(probability)
        if m == 0.0:
            self.skipped += 1
        return value * m


__all__ = ["DEFAULT_MODEL_DIR", "MetaLabelSizing"]
