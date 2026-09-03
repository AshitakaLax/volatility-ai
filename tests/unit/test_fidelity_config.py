"""Config plumbing for the Fidelity venue -- step 2 of the Fidelity plan.

The tests that matter here are the ones about the ACCOUNT ALLOWLIST,
because it is the only thing standing between this system and an order
against the wrong brokerage account. fidelity-api provides no allowlist
and no validation: it selects an account by case-insensitive SUBSTRING
match against dropdown text, so a truncated number that uniquely matches
the wrong button gets clicked. Every check below exists to make that
impossible to reach.

The rest pins the compatibility property: a config written before
Fidelity existed must keep its exact previous meaning.
"""

from __future__ import annotations

import dataclasses
import re

import pytest

from src.config import BacktestConfig, FidelityConfig
from src.exceptions import ConfigurationError


def _config(live: dict | None = None) -> dict:
    """A minimal valid config, with the live section under test."""
    data = {
        "strategy": {"strategy_id": "fixed"},
        "grid": {"steps": [0.01], "profit_targets": [0.05]},
        "backtest": {"symbol": "TQQQ", "initial_cash": 100000.0},
    }
    if live is not None:
        data["live"] = live
    return data


def _build(live: dict | None = None) -> BacktestConfig:
    config = BacktestConfig.from_dict(_config(live))
    config.validate()
    return config


# -- backward compatibility --------------------------------------------


def test_broker_defaults_to_alpaca():
    """A second venue must be opted into by name, never arrived at."""
    assert _build().live.broker == "alpaca"


def test_a_config_with_no_live_section_has_no_fidelity_settings():
    assert _build().live.fidelity is None


def test_an_existing_alpaca_config_is_unchanged():
    config = _build({"enabled": True, "feed": "sip", "step": 0.01})
    assert config.live.broker == "alpaca"
    assert config.live.fidelity is None
    assert config.live.feed == "sip"


# -- the feed whitelist is Alpaca's ------------------------------------


def test_an_alpaca_config_still_rejects_an_unknown_feed():
    with pytest.raises(ConfigurationError, match=re.escape("live.feed")):
        _build({"feed": "nonsense"})


def test_a_fidelity_config_is_not_held_to_the_alpaca_feed_whitelist():
    """ "iex"/"sip" are names of ALPACA data feeds. Applying that list to
    a Fidelity deployment would reject a config for failing to name a
    feed it does not have."""
    config = _build(
        {
            "broker": "fidelity",
            "feed": "whatever-fidelity-calls-it",
            "fidelity": {"allowed_accounts": ["Z12345678"]},
        }
    )
    assert config.live.feed == "whatever-fidelity-calls-it"


def test_an_unknown_broker_is_rejected():
    with pytest.raises(ConfigurationError, match=re.escape("live.broker")):
        _build({"broker": "schwab"})


# -- the allowlist is mandatory for a Fidelity deployment --------------


def test_fidelity_broker_requires_a_fidelity_section():
    """There is no safe default for which brokerage account real orders
    go to."""
    with pytest.raises(ConfigurationError, match=re.escape("requires a live.fidelity")):
        _build({"broker": "fidelity"})


def test_fidelity_broker_requires_a_non_empty_allowlist():
    with pytest.raises(ConfigurationError, match="must not be empty"):
        _build({"broker": "fidelity", "fidelity": {"allowed_accounts": []}})


def test_a_blank_allowlist_entry_is_rejected():
    with pytest.raises(ConfigurationError, match="blank entry"):
        _build(
            {
                "broker": "fidelity",
                "fidelity": {"allowed_accounts": ["Z12345678", "  "]},
            }
        )


# -- the string-coercion trap ------------------------------------------


def test_a_bare_string_allowlist_is_rejected_not_coerced():
    """THE TRAP: tuple("Z12345678") is nine single-character entries. An
    allowlist that silently became nine one-character accounts would
    still be non-empty, still pass every emptiness check, and match
    either nothing or something terrible."""
    with pytest.raises(ConfigurationError, match="not a bare string"):
        _build({"broker": "fidelity", "fidelity": {"allowed_accounts": "Z12345678"}})


def test_a_non_iterable_allowlist_is_rejected():
    with pytest.raises(ConfigurationError, match="must be a list"):
        _build({"broker": "fidelity", "fidelity": {"allowed_accounts": 12345678}})


# -- account must be inside its own allowlist --------------------------


def test_an_account_outside_the_allowlist_is_rejected():
    with pytest.raises(ConfigurationError, match="not in allowed_accounts"):
        _build(
            {
                "broker": "fidelity",
                "fidelity": {
                    "allowed_accounts": ["Z12345678"],
                    "account": "Z99999999",
                },
            }
        )


def test_a_substring_of_an_allowed_account_is_rejected():
    """Exact match only -- this is the specific hole in the library's
    substring-based selector."""
    with pytest.raises(ConfigurationError, match="not in allowed_accounts"):
        _build(
            {
                "broker": "fidelity",
                "fidelity": {"allowed_accounts": ["Z12345678"], "account": "Z1234"},
            }
        )


def test_a_case_variant_of_an_allowed_account_is_rejected():
    """The library's match is case-INsensitive; this check is not."""
    with pytest.raises(ConfigurationError, match="not in allowed_accounts"):
        _build(
            {
                "broker": "fidelity",
                "fidelity": {
                    "allowed_accounts": ["Z12345678"],
                    "account": "z12345678",
                },
            }
        )


def test_an_exactly_matching_account_is_accepted():
    config = _build(
        {
            "broker": "fidelity",
            "fidelity": {
                "allowed_accounts": ["Z12345678", "Z87654321"],
                "account": "Z87654321",
            },
        }
    )
    assert config.live.fidelity.account == "Z87654321"


def test_the_allowlist_is_checked_even_when_the_broker_is_alpaca():
    """A config naming an account outside its own allowlist is wrong
    however it is later used. Catching it only under broker='fidelity'
    would let a broker switch turn a latent contradiction into a live
    order against the wrong account."""
    with pytest.raises(ConfigurationError, match="not in allowed_accounts"):
        _build(
            {
                "broker": "alpaca",
                "fidelity": {
                    "allowed_accounts": ["Z12345678"],
                    "account": "Z99999999",
                },
            }
        )


# -- dry_run -----------------------------------------------------------


def test_dry_run_defaults_to_true():
    """A Fidelity account has no paper mode. dry_run is the only thing
    between a preview and a real order, so it defaults to safe and
    flipping it is the deliberate go-live act."""
    config = _build({"broker": "fidelity", "fidelity": {"allowed_accounts": ["Z12345678"]}})
    assert config.live.fidelity.dry_run is True


def test_dry_run_can_be_disabled_explicitly():
    config = _build(
        {
            "broker": "fidelity",
            "fidelity": {"allowed_accounts": ["Z12345678"], "dry_run": False},
        }
    )
    assert config.live.fidelity.dry_run is False


def test_dry_run_is_a_real_bool_not_a_truthy_string():
    """YAML's `dry_run: "false"` is a non-empty string, which is truthy
    -- but coercing it to True is the SAFE direction, so this pins that
    it lands on True rather than being read as False."""
    config = _build(
        {
            "broker": "fidelity",
            "fidelity": {"allowed_accounts": ["Z12345678"], "dry_run": "false"},
        }
    )
    assert config.live.fidelity.dry_run is True


# -- immutability and round-tripping -----------------------------------


def test_allowed_accounts_is_a_tuple_so_the_config_stays_hashable():
    """Artifact hashing (Task 6.3) requires it, same as GridConfig."""
    config = _build({"broker": "fidelity", "fidelity": {"allowed_accounts": ["Z12345678"]}})
    assert isinstance(config.live.fidelity.allowed_accounts, tuple)


def test_the_fidelity_config_is_frozen():
    """FrozenInstanceError specifically.

    A bare `pytest.raises(Exception)` passed for an AttributeError or a
    TypeError too, so it never actually asserted frozenness -- it would
    have stayed green if the field had simply been renamed.
    """
    fidelity = FidelityConfig(allowed_accounts=("Z1",))
    with pytest.raises(dataclasses.FrozenInstanceError):
        fidelity.account = "Z2"


def test_a_fidelity_config_round_trips_through_to_dict():
    live = {
        "broker": "fidelity",
        "fidelity": {
            "allowed_accounts": ["Z12345678", "Z87654321"],
            "account": "Z12345678",
            "dry_run": False,
        },
    }
    original = _build(live)
    restored = BacktestConfig.from_dict(original.to_dict())
    assert restored == original


def test_an_alpaca_config_round_trips_without_a_null_fidelity_section():
    original = _build({"enabled": True, "feed": "iex"})
    emitted = original.to_dict()
    assert "fidelity" not in emitted["live"]
    assert BacktestConfig.from_dict(emitted) == original


def test_to_dict_is_json_serializable_with_fidelity_settings():
    import json

    config = _build({"broker": "fidelity", "fidelity": {"allowed_accounts": ["Z12345678"]}})
    assert "Z12345678" in json.dumps(config.to_dict())
