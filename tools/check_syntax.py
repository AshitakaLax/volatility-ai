#!/usr/bin/env python
"""
Every .py file in the repository must parse. Nothing more.

--------------------------------------------------------------------
WHY A WHOLE SCRIPT FOR ONE ast.parse CALL

Because a file that did not parse was committed, pushed, and stayed
green. tools/ is excluded from the strategy test paths by design --
these are research scripts, not the trading path -- and "not the
trading path" became "never even compiled". The specific failure was a
heredoc that turned a backslash-n into a literal newline inside a
string: invisible in review, fatal at parse time, and the file had run
successfully BEFORE that edit and never again after it.

tests/unit/test_tools_are_importable.py asserts the same thing, but it
needs pandas and the rest of the dependency stack just to be collected.
This needs nothing but the standard library, so CI can run it in
seconds without installing anything -- which means it still works on
the exact commit where a dependency install is what broke.

Deliberately does NOT import anything it checks. Importing runs module
bodies; parsing does not.

Usage:
    python tools/check_syntax.py [--root .]
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

# Directories that are not this project's source.
SKIP = frozenset({".venv", "venv", "build", "dist", ".git", "__pycache__", "node_modules"})


def broken_files(root: Path) -> list[tuple[Path, int, str]]:
    """Every file that fails to parse, with the line and reason."""
    failures = []
    for path in sorted(root.rglob("*.py")):
        if SKIP & set(path.parts):
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append((path, exc.lineno or 0, exc.msg))
        except (OSError, UnicodeDecodeError) as exc:
            # Unreadable is a failure too: a file that cannot be opened
            # cannot be verified, and reporting it as fine would be a lie.
            failures.append((path, 0, f"could not read: {exc}"))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that every .py file parses.")
    parser.add_argument("--root", default=".", help="Directory to scan (default: .)")
    args = parser.parse_args(argv)

    root = Path(args.root)
    checked = sum(1 for p in root.rglob("*.py") if not (SKIP & set(p.parts)))
    failures = broken_files(root)

    if not failures:
        print(f"{checked} files parse.")
        return 0

    print(f"{len(failures)} of {checked} files DO NOT PARSE:", file=sys.stderr)
    for path, line, msg in failures:
        print(f"  {path}:{line}: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
