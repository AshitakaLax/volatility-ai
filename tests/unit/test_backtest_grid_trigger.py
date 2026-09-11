"""The per-strategy grid-step trigger descriptor the form uses.

`server/backtest.py`'s `describe_grid_trigger()` is PRESENTATION over the
`_grid_trigger_level` override point -- it must not claim a strategy
offers a method its class does not actually implement, and it must never
confuse a Gaussian sizing window (`bell_curve.lookback_days`) with a
rolling-high trigger window.
"""

from __future__ import annotations

import pytest

from server.backtest import _GRID_TRIGGER, describe_grid_trigger
from src.strategies.bayesian_sizing_calculators import BayesianDualScaleSizing
from src.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from src.strategies.size_calculators import SizingStrategy
from src.trading.strategy_registry import STRATEGIES

_LAST_BUY_ONLY = {
    "fixed",
    "rsi",
    "bell_curve",
    "ml_reachability_rsp",
    "ml_reachability_cowz",
    "ml_reachability_spyd",
}


class TestDescriptorShape:
    def test_every_registered_strategy_has_a_descriptor(self):
        for strategy_id in STRATEGIES:
            spec = describe_grid_trigger(strategy_id)
            assert set(spec) == {
                "methods",
                "default",
                "controlled_by",
                "window_param",
                "window_default",
            }
            assert spec["methods"], strategy_id
            assert spec["default"] == spec["methods"][0]

    def test_the_values_per_strategy(self):
        for strategy_id in _LAST_BUY_ONLY:
            spec = describe_grid_trigger(strategy_id)
            assert spec["methods"] == ["last_buy"]
            assert spec["controlled_by"] is None
            assert spec["window_param"] is None
            assert spec["window_default"] is None

        hf = describe_grid_trigger("hf_local_reference")
        assert hf["methods"] == ["local_reference"]
        assert hf["window_param"] == "lookback_days"
        assert hf["controlled_by"] is None  # locked -- no toggle
        assert hf["window_default"] is None  # seeds itself from the required committed value

        bayes = describe_grid_trigger("bayesian_dual_scale")
        assert bayes["methods"] == ["last_buy", "local_reference"]
        assert bayes["default"] == "last_buy"
        assert bayes["controlled_by"] == "lookback_days"
        assert bayes["window_param"] == "lookback_days"
        assert isinstance(bayes["window_default"], float) and bayes["window_default"] > 0

    def test_an_unknown_strategy_falls_back_to_last_buy(self):
        spec = describe_grid_trigger("not_a_strategy")
        assert spec["methods"] == ["last_buy"]
        assert spec["window_param"] is None

    def test_the_returned_dict_is_a_copy(self):
        """A caller mutating it must not corrupt the module table."""
        spec = describe_grid_trigger("bayesian_dual_scale")
        spec["methods"].append("junk")
        assert describe_grid_trigger("bayesian_dual_scale")["methods"] == [
            "last_buy",
            "local_reference",
        ]


class TestAntiRot:
    """Ties the descriptor to the actual override, like
    test_backtest_param_schema.py's curated-map sanity check."""

    def test_methods_match_whether_the_class_overrides_the_trigger(self):
        for strategy_id, cls in STRATEGIES.items():
            overrides = cls._grid_trigger_level is not SizingStrategy._grid_trigger_level
            offers_only_last_buy = describe_grid_trigger(strategy_id)["methods"] == ["last_buy"]
            assert overrides != offers_only_last_buy, strategy_id

    def test_every_named_param_is_a_real_constructor_argument(self):
        import inspect

        for strategy_id, spec in _GRID_TRIGGER.items():
            cls = STRATEGIES[strategy_id]
            names = set(inspect.signature(cls.__init__).parameters)
            for key in ("controlled_by", "window_param"):
                if spec[key] is not None:
                    assert spec[key] in names, (strategy_id, key)


class TestBehaviouralCrossCheck:
    """The one that would catch a wrong window_param: the strategies that
    advertise local_reference actually build a rolling high."""

    def test_hf_always_has_a_rolling_high(self):
        from server.backtest import STRATEGY_DEFAULTS

        strategy = HighFrequencyLocalReferenceSizing(**STRATEGY_DEFAULTS["hf_local_reference"])
        assert strategy._rolling_high is not None

    @pytest.mark.parametrize(
        ("lookback_days", "expected"),
        [(0.03, True), (None, False)],
    )
    def test_bayesian_rolling_high_tracks_lookback_days(self, lookback_days, expected):
        strategy = BayesianDualScaleSizing(
            max_trade_pct=0.05,
            target_return=0.0075,
            horizon_days=1.0,
            bars_per_day=387,
            lookback_days=lookback_days,
        )
        assert (strategy._rolling_high is not None) is expected
