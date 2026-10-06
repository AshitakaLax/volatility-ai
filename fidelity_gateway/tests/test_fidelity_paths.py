"""Every file a Fidelity message or doc points at must exist.

This code moved from flat scripts at the repo root, to src/, to
fidelity_gateway/, and its error messages kept naming the old homes --
"see fidelity_recon.py --cdp-url", "in src/fidelity_session.py". An
operator following an error to a file that is not there is lost at the
exact moment the message was written for.

Reads source off disk, so it covers the package's own modules and docs
plus the one engine module that talks about them. The package's tests
are left out on purpose: several tell the story of these moves, old
names and all.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = REPO_ROOT / "fidelity_gateway"

SCANNED = [
    *sorted(PACKAGE.glob("*.py")),
    PACKAGE / "CLAUDE.md",
    REPO_ROOT / "engine" / "brokers" / "broker_selection.py",
]

# src/... or src.module, and the flat fidelity_*.py scripts that predate
# the package.
LEGACY = re.compile(
    r"(?<![\w/.])src[/.]\w"
    r"|\bfidelity_(?:recon|place_test_order|session|broker|placing_broker|capture|analyze_har)\.py"
)

# fidelity_gateway/recon.py, fidelity_gateway.broker, -m fidelity_gateway.recon
REFERENCE = re.compile(r"\bfidelity_gateway[/.](\w+)")


@pytest.mark.parametrize("path", SCANNED, ids=lambda p: p.name)
def test_nothing_points_at_an_old_location(path):
    hits = LEGACY.findall(path.read_text(encoding="utf-8"))
    assert hits == [], f"{path.name} names files that moved away: {hits}"


@pytest.mark.parametrize("path", SCANNED, ids=lambda p: p.name)
def test_every_fidelity_gateway_module_it_names_exists(path):
    named = set(REFERENCE.findall(path.read_text(encoding="utf-8")))
    missing = sorted(
        name
        for name in named
        if not (PACKAGE / f"{name}.py").is_file() and not (PACKAGE / name).is_dir()
    )
    assert missing == [], f"{path.name} names modules that do not exist: {missing}"


def test_the_scan_still_covers_the_package():
    """A file move can silently gut a scanner that reads by path."""
    names = {path.name for path in SCANNED}
    assert {"session.py", "broker.py", "placing_broker.py", "recon.py", "CLAUDE.md"} <= names
    assert all(path.is_file() for path in SCANNED)
