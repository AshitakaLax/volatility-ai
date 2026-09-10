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


def test_there_is_exactly_one_escalating_definition():
    """Formerly "the three escalating copies still agree".

    There are no longer three copies to compare: the strategy has a
    single definition in tools/harness.py and the probes import it. That
    makes the old comparison structurally vacuous -- it would be diffing
    one class against itself and passing no matter what -- so this now
    pins the stronger property that replaced it: there is only ONE
    definition to disagree with.

    The behavioural assertions below are kept exactly as they were, so
    the escalation curve itself is still checked and this cannot rot
    into a pure identity test that verifies no arithmetic.
    """
    from dataclasses import dataclass

    from src.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
    from tools.harness import Escalating as Canonical

    @dataclass
    class Ctx:
        price: float

    consumers = ("probe_downturn_tactics", "probe_escalating_risk", "probe_regime_combo")
    for module in consumers:
        cls = importlib.import_module(f"tools.{module}").Escalating
        assert cls is Canonical, (
            f"tools/{module}.py has its own Escalating again. The point of "
            "harness.Escalating is that a cross-probe comparison cannot be "
            "invalidated by two definitions drifting apart."
        )

    # Pin the PARENT's contribution to a constant so what is measured is
    # the escalation multiplier alone. Without this the parent returns 0
    # on an unwarmed strategy and every assertion below passes against
    # 0.0 while measuring nothing.
    monkey = pytest.MonkeyPatch()
    monkey.setattr(
        HighFrequencyLocalReferenceSizing,
        "calculate_trade_value",
        lambda self, context: 1000.0,
    )
    try:
        strategy = Canonical(
            lookback_days=20,
            bars_per_day=390,
            per_lot_pct=0.02,
            max_mult=400.0,
            dd_ref=0.75,
        )
        strategy._price_peak = 100.0
        values = [
            round(strategy.calculate_trade_value(Ctx(price=p)), 9)
            for p in (100.0, 90.0, 75.0, 50.0, 25.0, 10.0)
        ]
    finally:
        monkey.undo()

    assert values[0] == 1000.0, "no drawdown means no escalation"
    assert values[-1] > values[0], "the multiplier must rise with drawdown"
    assert values[-1] == pytest.approx(400_000.0), "and saturate at max_mult"


def test_the_escalation_mechanism_is_written_exactly_once():
    """The formula and the peak-tracking line, in EXECUTABLE code only.

    tools/harness.py was written to absorb these and then adopted by
    three of thirty-seven scripts, so the copies it named kept being
    re-typed into new probes. This is the guard that makes the
    consolidation stick -- the same shape as
    tests/unit/test_no_loss_guard.py's duplicate scanner, and for the
    same reason: two definitions that agree today are two chances to
    disagree tomorrow, silently, invalidating every comparison between
    the probes that use them.

    Docstrings and comments are stripped before scanning, because
    several probes legitimately DESCRIBE the formula in their headers --
    that is documentation, not a second implementation.
    """
    import ast

    def executable_source(path: Path) -> str:
        src = path.read_text(encoding="utf-8")
        doc_lines: set[int] = set()
        for node in ast.walk(ast.parse(src)):
            if (
                isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and ast.get_docstring(node, clean=False) is not None
                and node.body
            ):
                first = node.body[0]
                doc_lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
        return "\n".join(
            line.split("#")[0]
            for i, line in enumerate(src.splitlines(), 1)
            if i not in doc_lines
        )

    for label, needles in (
        ("the escalation formula", ("max_mult **", "max_mult**")),
        ("the trailing-peak update", ("_price_peak is None else max(",)),
    ):
        sites = {}
        for path in sorted(Path("tools").glob("*.py")):
            code = executable_source(path)
            count = sum(code.count(n) for n in needles)
            if count:
                sites[path.name] = count
        assert sites == {"harness.py": 1}, (
            f"{label} should exist once, in tools/harness.py. Found: {sites}. "
            "Use harness.escalation() / DrawdownEscalation._track_peak instead "
            "of re-typing it."
        )
