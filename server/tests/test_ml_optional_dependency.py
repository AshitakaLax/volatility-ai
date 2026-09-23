"""server.app must import cleanly with lightgbm/sklearn absent.

The Raspberry Pi's image installs requirements.txt and
requirements-web.txt only -- never requirements-ml.txt (see that
file's own docstring: "the live trading loop and the Raspberry Pi that
runs it must never need these to start"). server/app.py imports
`backtest`, and therefore `strategy_registry`, UNCONDITIONALLY at
module load time regardless of whether VAI_BACKTEST_UPSTREAM routes
those requests elsewhere -- so if research/ml/reachability_sizing.py ever
imported lightgbm at its own module level instead of lazily inside
MLReachabilitySizing.__init__, simply STARTING the Pi's web container
would crash with ModuleNotFoundError, taking /api/live/* and the halt
endpoint down with it -- not just backtesting.

This blocks the two named modules at import time (not by uninstalling
anything, which would affect every other test in the suite) and
re-imports server.app fresh, so it is exercised exactly as a cold
process on the Pi would experience it.
"""

from __future__ import annotations

import builtins
import importlib
import sys

import pytest


@pytest.fixture
def lightgbm_and_sklearn_unavailable(monkeypatch):
    """Simulates a machine with only requirements.txt installed."""
    blocked = {"lightgbm", "sklearn"}
    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name in blocked or name.split(".")[0] in blocked:
            raise ModuleNotFoundError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)

    # Modules already imported earlier in the test session must be
    # forgotten too, or Python serves the cached (successful) import
    # instead of re-running it under the block. Their CURRENT objects
    # are saved first -- by reference, not by name -- so teardown can
    # put back the EXACT objects that were here, not merely something
    # that re-imports without error.
    #
    # A same-name reimport is not good enough: `from x import y`
    # elsewhere in the suite copies a reference at THAT call's moment,
    # and a later same-name-but-different-object module would leave
    # such a reference silently stale -- pointing at a class that no
    # longer `is`/`==` the one a fresh import now hands back. Measured:
    # test_ml_reachability_wiring.py's own equality check against a
    # freshly-imported MLReachabilitySizing failed under the full suite
    # while passing standalone, for exactly that reason, even after an
    # eager-reimport version of this teardown. Restoring the original
    # objects by reference is the only fix that does not just move the
    # same fragility to a different pair of names.
    reload_targets = [
        name
        for name in list(sys.modules)
        if (name.split(".")[0] in {"server", "engine", "research"} and "ml" in name)
        or name in ("server.app", "server.backtest", "research.strategies.strategy_registry")
    ]
    saved = {name: sys.modules[name] for name in reload_targets}
    for name in reload_targets:
        del sys.modules[name]
    yield

    # Popped again (the test body may have re-imported some of these
    # under the block, or left partial entries behind), then the
    # ORIGINAL objects are put back directly -- restoring the exact
    # module identities every other already-imported reference expects,
    # rather than creating new ones under the same names.
    for name in reload_targets:
        sys.modules.pop(name, None)
    sys.modules.update(saved)

    # sys.modules IS NOT THE ONLY PLACE A SUBMODULE IS REACHABLE.
    # `import server.app` also binds `sys.modules["server"].app = <that
    # module>` as an ATTRIBUTE of the parent package, and Python's import
    # system does not undo that when sys.modules["server.app"] is later
    # deleted or reassigned -- confirmed directly: after this fixture's
    # own re-import-under-block dance and restoring the ORIGINAL object
    # into sys.modules, `sys.modules["server"].app` still pointed at the
    # test's fresh (now-discarded) module, not the restored one.
    #
    # That single stale attribute is enough to break a LATER, unrelated
    # test: `from server import app as app_module` resolves via getattr
    # on the cached `server` package object, not a fresh sys.modules
    # lookup, so it silently bound the stale module -- and the next
    # `importlib.reload(app_module)` then raised "module server.app not
    # in sys.modules" (reload() requires identity with the current
    # sys.modules entry, which the restored original no longer matched).
    # Caught by test_server_api.py's TestSplitDeployment failing only
    # when run in the SAME session as this file, never standalone.
    for name, original in saved.items():
        parent_name, dot, attr = name.rpartition(".")
        if dot:
            parent = sys.modules.get(parent_name)
            if parent is not None:
                setattr(parent, attr, original)


def test_server_app_imports_without_lightgbm_or_sklearn(lightgbm_and_sklearn_unavailable):
    module = importlib.import_module("server.app")
    assert module.app is not None


def test_strategy_registry_imports_and_lists_ml_strategies(lightgbm_and_sklearn_unavailable):
    registry = importlib.import_module("research.strategies.strategy_registry")
    assert "ml_reachability_cowz" in registry.STRATEGIES


def test_only_constructing_the_ml_strategy_needs_the_missing_dependency(
    lightgbm_and_sklearn_unavailable,
):
    from engine.core.exceptions import ConfigurationError
    from research.strategies.strategy_registry import resolve_strategy

    # Construction alone must not need lightgbm -- the model loads lazily
    # on first use (like MLRegimeScaledSizing), so validation and the
    # /funds response work on a machine without requirements-ml.txt.
    # Only actually USING it does.
    strategy = resolve_strategy("ml_reachability_cowz")(max_trade_pct=0.05, ticker="COWZ")
    with pytest.raises(ConfigurationError, match=r"requirements-ml.txt"):
        strategy.ensure_model_available()

    # Every other strategy is completely unaffected.
    resolve_strategy("fixed")(allocation_pct=0.1)
    resolve_strategy("hf_local_reference")
