"""parameter_hash's identity boundary.

These tests need no optional dependency -- hashing is pure stdlib on
top of src/core/artifacts.py -- so they run on every checkout, unlike
tests/unit/test_warehouse_schema.py which skips without duckdb.

What is being pinned here is not "the hash function works" but WHERE
THE BOUNDARY SITS. parameter_hash carries a UNIQUE constraint in
sim_results.duckdb, so every field wrongly left out of it silently
rejects a legitimate experiment as a duplicate, and every field
wrongly folded in silently defeats the dedup. Both failures look like
a working warehouse.
"""

from __future__ import annotations

import pytest

from src.core.exceptions import ConfigurationError
from src.warehouse.hashing import (
    EXECUTION_FLAG_FIELDS,
    broker_id_for,
    execution_flags,
    parameter_hash,
)

BASE = {
    "strategy_id": "FixedPortfolioPercentage",
    "strategy_params": {"allocation_pct": 0.05},
    "grid_step": 0.01,
    "profit_target": 0.02,
    "dataset_version": "abc123",
    "broker_id": "zero-000000000000",
    "execution": {"fill_model": "close", "enforce_no_loss": True},
}


def test_identical_inputs_hash_identically():
    assert parameter_hash(**BASE) == parameter_hash(**BASE)


def test_hash_is_stable_across_key_insertion_order():
    """canonical_json sorts keys, so a dict built in a different order
    is the same experiment. Without this, a params dict assembled by a
    different code path would look like new work every run."""
    shuffled = dict(BASE)
    shuffled["strategy_params"] = {"beta": 2, "allocation_pct": 0.05}
    forward = dict(BASE)
    forward["strategy_params"] = {"allocation_pct": 0.05, "beta": 2}
    assert parameter_hash(**shuffled) == parameter_hash(**forward)


@pytest.mark.parametrize(
    "field,changed",
    [
        ("strategy_id", "RsiMomentumSizing"),
        ("grid_step", 0.02),
        ("profit_target", 0.03),
        ("dataset_version", "def456"),
        ("broker_id", "slippage_commission-111111111111"),
    ],
)
def test_changing_any_identity_field_changes_the_hash(field, changed):
    altered = dict(BASE)
    altered[field] = changed
    assert parameter_hash(**altered) != parameter_hash(**BASE)


def test_dataset_version_is_inside_the_hash():
    """The single most tempting field to leave out.

    A hash that is 'purely about parameters' reads clean and makes the
    warehouse refuse to re-measure a strategy against a newer data
    vintage -- the UNIQUE constraint rejects it as already done.
    """
    other_vintage = dict(BASE, dataset_version="a-longer-history")
    assert parameter_hash(**other_vintage) != parameter_hash(**BASE)


def test_broker_environment_is_inside_the_hash():
    """Same parameters at zero cost and at 5bps are different results."""
    assert parameter_hash(**dict(BASE, broker_id="costly")) != parameter_hash(**BASE)


def test_changing_an_execution_flag_changes_the_hash():
    altered = dict(BASE, execution={"fill_model": "intrabar", "enforce_no_loss": True})
    assert parameter_hash(**altered) != parameter_hash(**BASE)


def test_strategy_params_are_not_confused_with_execution_flags():
    """A strategy parameter that happens to share a name with nothing
    in EXECUTION_FLAG_FIELDS still participates in identity."""
    altered = dict(BASE, strategy_params={"allocation_pct": 0.10})
    assert parameter_hash(**altered) != parameter_hash(**BASE)


def test_nan_parameter_is_rejected_rather_than_hashed():
    """Inherited from artifacts.canonical_json's allow_nan=False.

    Two NaNs are not equal, so any hash of one would be a lie -- and a
    NaN parameter is a bug worth surfacing loudly rather than storing.
    """
    with pytest.raises(ConfigurationError):
        parameter_hash(**dict(BASE, strategy_params={"allocation_pct": float("nan")}))


def test_infinite_parameter_is_rejected():
    with pytest.raises(ConfigurationError):
        parameter_hash(**dict(BASE, strategy_params={"cap": float("inf")}))


def test_secret_looking_parameter_is_rejected():
    """artifacts._assert_no_secret_fields rejects credential-shaped
    keys. Surprising if hit, but correct: this is a permanent
    provenance record."""
    with pytest.raises(ConfigurationError):
        parameter_hash(**dict(BASE, strategy_params={"api_key": "xyz"}))


def test_execution_flags_reads_a_mapping():
    flags = execution_flags({"fill_model": "close", "symbol": "TQQQ", "not_a_flag": 1})
    assert flags == {"symbol": "TQQQ", "fill_model": "close"}


def test_execution_flags_reads_an_object():
    class Section:
        fill_model = "intrabar"
        enforce_no_loss = False

    assert execution_flags(Section()) == {"fill_model": "intrabar", "enforce_no_loss": False}


def test_execution_flags_omits_absent_fields_rather_than_defaulting():
    """A wrong default would be indistinguishable from a real value and
    would poison the hash silently."""
    assert execution_flags({}) == {}


def test_every_execution_flag_field_actually_moves_the_hash():
    """Guards the tuple itself: a field listed there but ignored by the
    hash would be dead weight, and one omitted from it that changes
    results would collide two different runs."""
    for field in EXECUTION_FLAG_FIELDS:
        altered = dict(BASE, execution={**BASE["execution"], field: "SENTINEL"})
        assert parameter_hash(**altered) != parameter_hash(**BASE), field


def test_broker_id_is_content_addressed():
    """Two configs describing the same economics share one broker row,
    regardless of what their YAML files were named."""

    class Cost:
        model_type = "slippage_commission"
        commission_per_trade = 1.0
        slippage_bps = 5.0
        base_bps = 0.0
        vol_multiplier = 1.0

    class SameNumbersDifferentObject:
        model_type = "slippage_commission"
        commission_per_trade = 1.0
        slippage_bps = 5.0
        base_bps = 0.0
        vol_multiplier = 1.0

    assert broker_id_for(Cost()) == broker_id_for(SameNumbersDifferentObject())
    assert broker_id_for(Cost()).startswith("slippage_commission-")


def test_broker_id_changes_when_economics_change():
    class Cheap:
        model_type = "slippage_commission"
        commission_per_trade = 1.0
        slippage_bps = 5.0

    class Dear:
        model_type = "slippage_commission"
        commission_per_trade = 1.0
        slippage_bps = 25.0

    assert broker_id_for(Cheap()) != broker_id_for(Dear())
