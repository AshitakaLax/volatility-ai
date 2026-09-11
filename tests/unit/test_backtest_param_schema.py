"""The per-strategy parameter schema the dynamic backtest form renders.

`server/backtest.py`'s `describe_params` turns each sizing strategy's
constructor into a typed, seeded field list. These tests pin the parts a
form gets quietly wrong: a `float | None` read as non-nullable, a `bool`
mistaken for an `int`, a server-managed argument offered as an input, or
the `target_return` / ml-`ticker` overrides not surfaced as locked.
"""

from __future__ import annotations

import pytest

from server.backtest import (
    _DERIVED_PARAMS,
    _HIDDEN_PARAMS,
    _PARAM_ENUMS,
    STRATEGY_DEFAULTS,
    _safe_describe,
    _wire_type,
    describe_params,
    required_parameters,
)
from src.trading.strategy_registry import STRATEGIES


class TestWireType:
    def test_a_plain_builtin_maps_to_its_wire_name(self):
        assert _wire_type(float, has_default=True, default=1.0) == ("float", False)
        assert _wire_type(str, has_default=True, default="stdev") == ("str", False)

    def test_bool_is_not_int(self):
        """bool is a subclass of int; a checkbox is not a number field."""
        assert _wire_type(bool, has_default=True, default=False) == ("bool", False)
        assert _wire_type(int, has_default=True, default=14) == ("int", False)

    def test_optional_is_nullable(self):
        assert _wire_type(float | None, has_default=True, default=None) == ("float", True)

    def test_a_required_argument_is_never_nullable(self):
        """No default -> a blank must block the run, not be omitted."""
        assert _wire_type(float, has_default=False, default=None) == ("float", False)

    def test_an_unresolvable_annotation_falls_back_to_a_number(self):
        assert _wire_type(None, has_default=True, default=0.0) == ("float", False)


class TestCuratedMaps:
    """The three things inspect.signature cannot see are named by hand;
    a renamed constructor argument must fail here, not rot silently."""

    def _all_param_names(self) -> set[str]:
        names: set[str] = set()
        for cls in STRATEGIES.values():
            names.update(required_parameters(cls))
            import inspect

            for parameter in inspect.signature(cls.__init__).parameters.values():
                if parameter.name != "self":
                    names.add(parameter.name)
        return names

    def test_every_curated_key_is_a_real_constructor_argument(self):
        real = self._all_param_names()
        for key in (*_PARAM_ENUMS, *_HIDDEN_PARAMS, *_DERIVED_PARAMS):
            assert key in real, f"{key!r} is curated but not a parameter of any strategy"


class TestDescribeParams:
    def test_every_registered_strategy_describes_without_raising(self):
        for strategy_id, cls in STRATEGIES.items():
            specs = describe_params(strategy_id, cls)
            assert specs, f"{strategy_id} produced no parameter specs"

    def test_required_constructor_args_are_marked_required(self):
        for strategy_id, cls in STRATEGIES.items():
            by_name = {s["name"]: s for s in describe_params(strategy_id, cls)}
            for name in required_parameters(cls):
                assert by_name[name]["required"] is True
                assert by_name[name]["nullable"] is False

    def test_group_is_required_or_committed(self):
        for strategy_id, cls in STRATEGIES.items():
            committed = STRATEGY_DEFAULTS.get(strategy_id, {})
            required = set(required_parameters(cls))
            for spec in describe_params(strategy_id, cls):
                expected = (
                    "primary"
                    if (spec["name"] in required or spec["name"] in committed)
                    else "advanced"
                )
                assert spec["group"] == expected, (strategy_id, spec["name"])

    def test_hidden_filesystem_params_are_never_offered(self):
        for strategy_id, cls in STRATEGIES.items():
            names = {s["name"] for s in describe_params(strategy_id, cls)}
            assert names.isdisjoint(_HIDDEN_PARAMS)

    def test_fixed_seeds_allocation_pct_and_locks_the_percentage_alias(self):
        by_name = {s["name"]: s for s in describe_params("fixed", STRATEGIES["fixed"])}
        assert by_name["allocation_pct"]["suggested"] == 0.05
        assert by_name["allocation_pct"]["group"] == "primary"
        assert by_name["allocation_pct"]["editable"] is True
        # `float | None` on the constructor, but the strategy raises
        # without one, so the form treats it as required rather than
        # letting a blank fall through to the server's default.
        assert by_name["allocation_pct"]["required"] is True
        assert by_name["allocation_pct"]["nullable"] is False
        assert by_name["percentage"]["editable"] is False
        assert "alias" in by_name["percentage"]["locked_reason"]

    def test_bayesian_target_return_is_locked_and_mirrors_the_profit_target(self):
        by_name = {
            s["name"]: s
            for s in describe_params("bayesian_dual_scale", STRATEGIES["bayesian_dual_scale"])
        }
        target = by_name["target_return"]
        assert target["editable"] is False
        assert target["mirrors"] == "profit_target"
        assert target["locked_reason"]
        assert by_name["vol_measure"]["enum"] == ["stdev", "range"]
        assert by_name["allow_target_return_mismatch"]["type"] == "bool"
        assert by_name["bars_per_day"]["type"] == "int"
        assert by_name["bars_per_day"]["step"] == "1"

    def test_ml_ticker_is_locked_to_the_id(self):
        for strategy_id, expected in (
            ("ml_reachability_cowz", "COWZ"),
            ("ml_reachability_rsp", "RSP"),
            ("ml_reachability_spyd", "SPYD"),
        ):
            by_name = {s["name"]: s for s in describe_params(strategy_id, STRATEGIES[strategy_id])}
            assert by_name["ticker"]["editable"] is False
            assert by_name["ticker"]["suggested"] == expected
            assert by_name["baseline_price"]["editable"] is False

    def test_suggested_is_the_committed_value_or_the_constructor_default(self):
        for strategy_id, cls in STRATEGIES.items():
            committed = STRATEGY_DEFAULTS.get(strategy_id, {})
            for spec in describe_params(strategy_id, cls):
                if spec["name"] in committed:
                    assert spec["suggested"] == committed[spec["name"]]
                else:
                    assert spec["suggested"] == spec["default"]

    def test_safe_describe_swallows_a_broken_strategy(self):
        class Broken:
            def __init__(self, *, needs_a_thing):
                pass

        # A get_type_hints failure or similar must not 500 /funds.
        assert _safe_describe("broken", Broken) == {"params": describe_params("broken", Broken)}

        class Explodes:
            __init__ = property(lambda self: (_ for _ in ()).throw(RuntimeError("boom")))

        assert _safe_describe("explodes", Explodes) == {"params": []}

    def test_one_unresolvable_annotation_only_untypes_its_own_field(self):
        """A single bad hint used to blank get_type_hints entirely and
        make every field render as a number."""

        def ctor(self, good: int = 3, broken: "NoSuchType" = 0, flag: bool = False):  # noqa: F821, UP037
            pass

        Fake = type("Fake", (), {"__init__": ctor})
        by_name = {s["name"]: s for s in describe_params("fake", Fake)}
        assert by_name["good"]["type"] == "int"  # survived
        assert by_name["flag"]["type"] == "bool"  # survived
        assert by_name["broken"]["type"] == "float"  # only this one degraded


class TestSweepable:
    """`sweepable` is what the "enable sweep" checkbox renders on --
    a numeric argument the operator actually owns. It must track the
    same rule everywhere, not drift into a second definition."""

    def test_the_rule_holds_for_every_param_of_every_strategy(self):
        for strategy_id, cls in STRATEGIES.items():
            for spec in describe_params(strategy_id, cls):
                expected = (
                    spec["type"] in ("int", "float")
                    and spec["editable"]
                    and spec["mirrors"] is None
                )
                assert spec["sweepable"] is expected, (strategy_id, spec["name"])

    def test_target_return_is_not_sweepable(self):
        """It mirrors the grid's profit target -- sweeping it
        independently would silently fight that alignment."""
        by_name = {
            s["name"]: s
            for s in describe_params("bayesian_dual_scale", STRATEGIES["bayesian_dual_scale"])
        }
        assert by_name["target_return"]["sweepable"] is False

    def test_ml_ticker_is_not_sweepable(self):
        """Locked to the model id -- the engine owns it, not the operator."""
        by_name = {
            s["name"]: s
            for s in describe_params("ml_reachability_cowz", STRATEGIES["ml_reachability_cowz"])
        }
        assert by_name["ticker"]["sweepable"] is False

    def test_baseline_price_and_the_fixed_percentage_alias_are_not_sweepable(self):
        ml_by_name = {
            s["name"]: s
            for s in describe_params("ml_reachability_cowz", STRATEGIES["ml_reachability_cowz"])
        }
        assert ml_by_name["baseline_price"]["sweepable"] is False
        fixed_by_name = {s["name"]: s for s in describe_params("fixed", STRATEGIES["fixed"])}
        assert fixed_by_name["percentage"]["sweepable"] is False

    def test_allocation_pct_is_sweepable(self):
        by_name = {s["name"]: s for s in describe_params("fixed", STRATEGIES["fixed"])}
        assert by_name["allocation_pct"]["sweepable"] is True

    def test_a_str_enum_param_is_not_sweepable(self):
        by_name = {
            s["name"]: s
            for s in describe_params("bayesian_dual_scale", STRATEGIES["bayesian_dual_scale"])
        }
        assert by_name["vol_measure"]["sweepable"] is False

    def test_an_editable_int_param_is_sweepable(self):
        by_name = {
            s["name"]: s
            for s in describe_params("bayesian_dual_scale", STRATEGIES["bayesian_dual_scale"])
        }
        assert by_name["bars_per_day"]["type"] == "int"
        assert by_name["bars_per_day"]["sweepable"] is True


def _simulate_build_strategy_params(specs: list[dict]) -> dict:
    """A faithful port of web/src/lib/strategyParams.ts
    seedValues + buildStrategyParams for a NO-EDIT submit, so the
    "a plain Run sends exactly the committed defaults" guarantee is
    pinned against the REAL schema, not a hand-written JS fixture.
    """
    values = {
        s["name"]: ("" if s["suggested"] is None else s["suggested"])
        for s in specs
        if s["mirrors"] is None
    }
    out: dict = {}
    for s in specs:
        if s["mirrors"] is not None:
            continue
        if not s["editable"] and s["name"] != "ticker":
            continue
        raw = values.get(s["name"], "")
        if raw == "":
            continue
        value = raw  # str/enum/bool/number pass straight through here
        if s["has_suggested"] or str(value) != str(s["default"]):
            out[s["name"]] = value
    return out


class TestNoEditSubmitParity:
    """MUST HOLD: pressing Run with no parameter edits submits exactly
    `STRATEGY_DEFAULTS[id]` -- byte-identical to the old blind
    `sizing_details.defaults` splat -- for every registered model."""

    @pytest.mark.parametrize("strategy_id", sorted(STRATEGIES))
    def test_a_plain_run_reproduces_the_committed_defaults(self, strategy_id):
        specs = describe_params(strategy_id, STRATEGIES[strategy_id])
        got = _simulate_build_strategy_params(specs)
        want = dict(STRATEGY_DEFAULTS.get(strategy_id, {}))
        # `target_return` is the one committed key the form never sends --
        # build_config re-derives it from the grid's profit target.
        want.pop("target_return", None)
        assert got == want


class TestRoundTrip:
    """The suggested values the form seeds with must actually build the
    strategy -- the whole point of pre-filling from committed configs."""

    @pytest.mark.parametrize("strategy_id", sorted(STRATEGIES))
    def test_seeded_params_construct_the_strategy(self, strategy_id):
        cls = STRATEGIES[strategy_id]
        params: dict = {}
        for spec in describe_params(strategy_id, cls):
            if spec["mirrors"] is not None:
                continue  # target_return: the server aligns it
            if not spec["editable"] and spec["name"] != "ticker":
                continue  # baseline_price, percentage: engine-owned
            if spec["suggested"] is None:
                continue  # blank optional -> constructor default
            params[spec["name"]] = spec["suggested"]
        if "target_return" in required_parameters(cls):
            params["target_return"] = 0.01  # what build_config would align to
        cls(**params)  # raises if the seeded set is insufficient
