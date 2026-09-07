"""MLReachabilitySizing's registry wiring: three ids, a mismatch guard
caught EARLY, and no import-time dependency on lightgbm.

The lazy-import guarantee has its own dedicated file
(test_ml_optional_dependency.py, which simulates the Raspberry Pi's
exact "requirements-ml.txt never installed" situation). This file
covers what happens once lightgbm IS available -- this machine's
normal state, and the workstation's in deployment -- and specifically
the failure this project has already been bitten by once before
(server/backtest.py's own comment: a missing argument used to surface
as "every combination erroring ... a confusing rank_by column not
found -- twenty seconds later, naming a column rather than the
argument that was missing"). MLReachabilitySizing reintroduced an
analogous version of exactly that bug for a ticker mismatch on its
first pass -- caught only by actually driving the failure through
server.backtest.run_backtest, the real path a browser takes, rather
than by unit-testing optimization_controller.py's guard in isolation.
These tests pin the FIX: the error surfaces immediately, from
build_config(), naming the actual mismatch.
"""

from __future__ import annotations

import pytest

# Deliberately NOT `from src.strategy_registry import STRATEGIES` at
# module level: that snapshots the dict object at COLLECTION time, and
# test_ml_optional_dependency.py in this same suite legitimately pops
# and re-imports src.ml.reachability_sizing / src.strategy_registry to
# simulate a machine without lightgbm. `from x import y` copies a
# REFERENCE, not a live link, so a snapshot taken before that reload
# and a fresh import taken after it can hold two different (if
# identically named) class objects -- measured: this file's own
# equality check against a freshly-imported MLReachabilitySizing
# failed under the full suite while passing standalone, for exactly
# that reason. Importing the module itself, everywhere below, and
# reading .STRATEGIES/.resolve_strategy off it fresh each time sidesteps
# the whole class of bug rather than requiring every OTHER test file
# to leave global module state pristine.
import src.strategy_registry as strategy_registry
from src.exceptions import ConfigurationError


def test_all_three_tickers_are_registered_to_the_same_class():
    from src.ml.reachability_sizing import MLReachabilitySizing

    ids = {"ml_reachability_rsp", "ml_reachability_cowz", "ml_reachability_spyd"}
    assert ids <= set(strategy_registry.STRATEGIES)
    assert {strategy_registry.STRATEGIES[i] for i in ids} == {MLReachabilitySizing}


def test_each_id_has_a_strategy_defaults_entry_with_a_matching_ticker():
    from server.backtest import STRATEGY_DEFAULTS

    for strategy_id, ticker in (
        ("ml_reachability_rsp", "RSP"),
        ("ml_reachability_cowz", "COWZ"),
        ("ml_reachability_spyd", "SPYD"),
    ):
        defaults = STRATEGY_DEFAULTS[strategy_id]
        assert defaults["ticker"] == ticker, (
            f"{strategy_id} defaults to ticker={defaults.get('ticker')!r}, expected {ticker!r}"
        )


def test_a_ticker_mismatch_is_refused_immediately_by_build_config():
    """The regression pin: this must raise HERE, with the real reason,
    not surface 20 seconds later as a missing rank_by column once every
    combination in the sweep has failed the same way."""
    from server.backtest import RunRequest, build_config

    request = RunRequest(
        tickers=["RSP"],
        grid_steps=[0.005],
        profit_targets=[0.005],
        sizing_model="ml_reachability_cowz",
        strategy_params={"max_trade_pct": 0.05, "ticker": "COWZ", "confidence_floor": 0.25},
    )
    with pytest.raises(ConfigurationError, match="trained on COWZ"):
        build_config(request)


def test_a_matching_ticker_builds_cleanly():
    from server.backtest import RunRequest, build_config

    request = RunRequest(
        tickers=["COWZ"],
        grid_steps=[0.005],
        profit_targets=[0.005],
        sizing_model="ml_reachability_cowz",
        strategy_params={"max_trade_pct": 0.05, "ticker": "COWZ", "confidence_floor": 0.25},
    )
    build_config(request)  # must not raise


def test_the_deeper_guard_in_optimization_controller_also_names_the_mismatch(caplog):
    """build_config() is server/backtest.py's early check -- a caller
    going through optimization_controller.run_sweep directly (the CLI,
    a script) never reaches it, so a SECOND guard lives in
    _run_one_combination, mirroring the pre-existing target_return
    check exactly. Driven through run_sweep itself (the real call
    graph a direct caller uses) rather than by guessing that internal
    function's own signature.

    With every combination in this sweep failing the same way, run_sweep
    itself goes on to raise its OWN (less specific) error trying to rank
    empty results -- the exact failure mode this project already
    documented once (server/backtest.py: "a confusing rank_by column
    not found ... naming a column rather than the argument that was
    missing") and the reason server/backtest.py's build_config() catches
    this mismatch EARLY instead of relying on this deeper guard alone.
    What this test pins is narrower and still worth pinning: the deeper
    guard is reached at all and logs the REAL reason, so a direct
    caller reading logs (rather than the API's clean 400) is not left
    with only "rank_by column not found".
    """
    import pandas as pd

    from optimization_controller import OptimizationController

    index = pd.date_range("2024-01-02 14:30", periods=200, freq="1min", tz="UTC")
    frame = pd.DataFrame(
        {"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0},
        index=index,
    )
    controller = OptimizationController(frame)

    with pytest.raises(ConfigurationError):
        controller.run_sweep(
            grid_steps=[0.005],
            profit_targets=[0.005],
            strategy_class=strategy_registry.resolve_strategy("ml_reachability_cowz"),
            strategy_params_grid=[
                {"max_trade_pct": 0.05, "ticker": "COWZ", "confidence_floor": 0.25}
            ],
            symbol="RSP",  # the mismatch: this model is trained on COWZ
            initial_cash=100_000.0,
        )

    assert any("trained on COWZ" in record.message for record in caplog.records), [
        record.message for record in caplog.records
    ]
