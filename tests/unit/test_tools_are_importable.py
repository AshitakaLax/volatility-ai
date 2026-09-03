"""
Every script in tools/ must parse, and importing one must do nothing.

Neither property was checked before, and both were broken.

tools/ is excluded from the strategy-path test suite by design -- these
are research scripts, not the trading path -- but "not the trading path"
became "never even compiled". A file with a syntax error sat committed
and green, because nothing ever read it.

These tests are cheap (ast.parse, no execution of module bodies beyond
import) and they close the specific gap that let that happen.
"""

from __future__ import annotations

import ast
import importlib
import time
from pathlib import Path

import pytest

TOOLS = sorted(p for p in Path("tools").glob("*.py") if p.name != "__init__.py")
ROOT_SCRIPTS = sorted(Path(".").glob("*.py"))


@pytest.mark.parametrize("path", TOOLS + ROOT_SCRIPTS, ids=lambda p: p.name)
def test_every_script_parses(path):
    """A syntax error in tools/ was committed and shipped.

    It came from a heredoc that turned a backslash-n into a literal
    newline inside a string, which is invisible in a diff and fatal at
    parse time. The file had been run successfully BEFORE that edit and
    never again after it.
    """
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


@pytest.mark.parametrize("path", TOOLS, ids=lambda p: p.name)
def test_no_tool_does_work_at_import_time(path):
    """Importing a probe must not load data or run a sweep.

    Two of these did, because they had no `if __name__ == "__main__"`
    guard -- so reusing a strategy class from them fired a full
    multi-minute sweep as a side effect of the import statement, which is
    how it was finally noticed.

    The assertion is on module-level WORK, not on the presence of a
    guard. session_bars.py is a pure library of functions and correctly
    has no guard; demanding one would have been a test asserting a habit
    rather than a property.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    loaders = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.Expr, ast.For, ast.While))
        and any(
            call in ast.unparse(node)
            for call in ("read_csv(", "run_sweep(", "OptimizationController(")
        )
    ]
    assert loaders == [], (
        f"{path.name} loads data or runs a sweep at module level: "
        f"{[ast.unparse(n)[:60] for n in loaders]}"
    )


@pytest.mark.parametrize("path", TOOLS, ids=lambda p: p.name)
def test_a_tool_defining_main_actually_guards_it(path):
    """A main() with no guard either never runs or always runs. Both are
    bugs; which one depends on nothing the reader can see."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    has_main = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body)
    if not has_main:
        return
    guarded = any(
        isinstance(node, ast.If) and ast.unparse(node.test).startswith("__name__")
        for node in tree.body
    )
    assert guarded, f"{path.name} defines main() but never calls it under a guard"


@pytest.mark.parametrize("name", [p.stem for p in TOOLS], ids=lambda n: n)
def test_importing_a_tool_is_fast_and_silent(name, capsys):
    """The behavioural version of the test above: import it and see."""
    started = time.monotonic()
    importlib.import_module(f"tools.{name}")
    elapsed = time.monotonic() - started
    assert elapsed < 5.0, f"tools.{name} took {elapsed:.1f}s to import"
    assert capsys.readouterr().out == "", f"tools.{name} printed during import"


def test_the_three_escalating_copies_still_agree():
    """Three independent definitions of the same strategy.

    They ARE equivalent -- verified by running all three over the 2020
    COVID episode and getting identical returns and trade counts to ten
    decimal places, which is why every cross-probe comparison in this
    project is valid. This pins that agreement, because three copies
    that agree today are three chances to disagree tomorrow, silently,
    invalidating every published comparison between them.

    Compares BEHAVIOUR, not source. An earlier version diffed normalised
    ASTs and failed: the copies genuinely differ in text -- one carries a
    `max_mult <= 1.0` short-circuit, another uses a ternary -- while
    computing the identical number. Testing the text would have
    forbidden harmless edits and still missed a harmful one written to
    look the same.
    """
    from dataclasses import dataclass

    from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing

    @dataclass
    class Ctx:
        price: float

    # Pin the PARENT's contribution to a constant so what is compared is
    # the escalation multiplier alone -- the only part these three copies
    # actually implement. Without this the parent returns 0 on an
    # unwarmed strategy, every copy "agrees" on 0.0, and the test passes
    # while measuring nothing. The trailing sanity assert exists because
    # the first version did exactly that.
    monkey = pytest.MonkeyPatch()
    monkey.setattr(
        HighFrequencyLocalReferenceSizing,
        "calculate_trade_value",
        lambda self, context: 1000.0,
    )
    try:
        sized = {}
        for module in ("probe_downturn_tactics", "probe_escalating_risk", "probe_regime_combo"):
            cls = importlib.import_module(f"tools.{module}").Escalating
            strategy = cls(
                lookback_days=20,
                bars_per_day=390,
                per_lot_pct=0.02,
                max_mult=400.0,
                dd_ref=0.75,
            )
            strategy._price_peak = 100.0
            sized[module] = [
                round(strategy.calculate_trade_value(Ctx(price=p)), 9)
                for p in (100.0, 90.0, 75.0, 50.0, 25.0, 10.0)
            ]
    finally:
        monkey.undo()

    unique = {tuple(v) for v in sized.values()}
    assert len(unique) == 1, (
        "the Escalating copies have DIVERGED. Every cross-probe comparison "
        "in this project assumed they were the same strategy.\n"
        + "\n".join(f"  {k}: {v}" for k, v in sized.items())
    )
    values = next(iter(unique))
    assert values[0] == 1000.0, "no drawdown means no escalation"
    assert values[-1] > values[0], "the multiplier must rise with drawdown"
    assert values[-1] == pytest.approx(400_000.0), "and saturate at max_mult"
