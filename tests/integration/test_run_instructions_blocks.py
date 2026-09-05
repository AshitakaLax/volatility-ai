"""Run_Instructions' examples must actually run, and name real parameters.

This replaces test_task_1_1_run_instructions.py and
test_task_6_1_config_run_instructions.py, which asserted the same
properties but located the examples by matching a full SENTENCE OF
PROSE -- e.g. "Example config.yaml (every section except strategy/grid
is optional -- omitted sections use the defaults shown):". Rewording
the surrounding paragraph broke them, which is exactly what happened
when the file was brought up to date: four tests failed for reasons
that had nothing to do with the code they exist to guard.

So the doc now carries named delimiters:

    --- BEGIN example-config.yaml ---
    ...
    --- END example-config.yaml ---

and this file keys on those. Prose can be rewritten freely; the
executable content is pinned. That is the property worth protecting --
a walkthrough whose examples are run on every test invocation cannot
quietly rot the way this one did.
"""

from __future__ import annotations

import inspect
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_INSTRUCTIONS = REPO_ROOT / "Run_Instructions"


def block(name: str) -> str:
    """The contents of one named block, or a failure naming it."""
    text = RUN_INSTRUCTIONS.read_text(encoding="utf-8")
    begin, end = f"--- BEGIN {name} ---", f"--- END {name} ---"
    assert begin in text, f"Run_Instructions has no {begin!r}"
    assert end in text, f"Run_Instructions has no {end!r}"
    return text.split(begin, 1)[1].split(end, 1)[0].strip()


def _sandbox(tmp_path: Path) -> Path:
    """A tree the examples can run in: the library plus one small CSV.

    The fixture stands in for data/TQQQ_historical.csv, which is the
    name both examples read. Real downloads are named for their
    parameters instead -- the examples use the short name because a
    walkthrough should not depend on which symbol-years someone
    happens to have fetched.
    """
    shutil.copy(REPO_ROOT / "optimization_controller.py", tmp_path / "optimization_controller.py")
    shutil.copytree(REPO_ROOT / "src", tmp_path / "src")
    (tmp_path / "data").mkdir()
    shutil.copy(
        REPO_ROOT / "tests" / "fixtures" / "regression_ohlcv.csv",
        tmp_path / "data" / "TQQQ_historical.csv",
    )
    return tmp_path


def _run(tmp_path: Path, script: str) -> subprocess.CompletedProcess:
    path = tmp_path / "example.py"
    path.write_text(script, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize("name", ["example-direct.py", "example-config.py"])
def test_each_documented_example_runs_verbatim(tmp_path, name):
    """Copy-paste the block, run it, require a real results table."""
    script = block(name)
    assert "run_sweep(" in script, f"{name} does not call run_sweep"

    _sandbox(tmp_path)
    if name == "example-config.py":
        (tmp_path / "config.yaml").write_text(block("example-config.yaml"), encoding="utf-8")

    result = _run(tmp_path, script)

    assert result.returncode == 0, (
        f"{name} raised (exit {result.returncode}).\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "Capital Velocity Index" in result.stdout or "Grid Step" in result.stdout, (
        f"{name} ran but produced no recognisable results table.\nstdout:\n{result.stdout}"
    )


def test_the_documented_yaml_is_accepted_by_the_real_config_loader(tmp_path):
    """The YAML is validated by BacktestConfig, not merely parsed."""
    from src.config import BacktestConfig

    path = tmp_path / "config.yaml"
    path.write_text(block("example-config.yaml"), encoding="utf-8")

    config = BacktestConfig.from_yaml(str(path))
    config.validate()

    assert config.strategy.strategy_id == "fixed"
    assert config.grid.steps and config.grid.profit_targets


def test_every_documented_yaml_field_is_a_real_config_field():
    """A field the loader silently ignores is worse than an absent one.

    BacktestConfig.from_dict is permissive about unknown keys, so a
    typo'd or removed setting would be documented here and quietly do
    nothing -- which is how a reader ends up believing they configured
    something they did not.
    """
    import dataclasses

    import yaml

    from src import config as config_module

    sections = {
        "strategy": config_module.StrategyConfig,
        "grid": config_module.GridConfig,
        "costs": config_module.CostConfig,
        "risk": config_module.RiskConfig,
        "search": config_module.SearchConfig,
        "execution": config_module.ExecutionConfig,
        "output": config_module.OutputConfig,
        "live": config_module.LiveConfig,
    }
    documented = yaml.safe_load(block("example-config.yaml"))

    for section, cls in sections.items():
        assert section in documented, f"the documented YAML no longer shows a {section!r} section"
        real = {f.name for f in dataclasses.fields(cls)}
        unknown = set(documented[section]) - real
        assert not unknown, (
            f"{section}: documented but not real fields on {cls.__name__}: {unknown}"
        )


def test_every_documented_run_sweep_kwarg_is_real():
    """The capabilities list is checked against the real signature."""
    from optimization_controller import OptimizationController

    documented = set(re.findall(r"^- (\w+)", block("run-sweep-kwargs"), flags=re.MULTILINE))
    real = set(inspect.signature(OptimizationController.run_sweep).parameters)

    assert documented, "the run-sweep-kwargs block lists nothing"
    assert documented <= real, f"documented but not real run_sweep parameters: {documented - real}"


def test_the_example_uses_the_real_constructor_keyword():
    """Guards the drift this file was originally written to catch:
    Run_Instructions once documented `allocations`, which has never
    been a parameter of anything."""
    from src.size_calculators import FixedPortfolioPercentage

    FixedPortfolioPercentage(allocation_pct=0.05)  # TypeError if the name is wrong

    script = block("example-direct.py")
    assert "allocation_pct" in script
    assert "allocations=" not in script


def test_the_registry_is_used_rather_than_a_hand_written_mapping():
    """Run_Instructions used to tell readers to hand-write a
    strategy_id-to-class dict, and src/strategy_registry.py's docstring
    names this file as one of the two copies it exists to remove."""
    script = block("example-config.py")
    assert "resolve_strategy" in script
    assert "STRATEGY_REGISTRY" not in script, "the hand-written mapping is back"
