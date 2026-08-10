"""
Task 1.1 acceptance test: "The example script in Run_Instructions,
copy-pasted verbatim, runs to completion without raising."

This extracts the exact script text from Run_Instructions, drops it
into a throwaway directory alongside the real optimization_controller.py
and src/ package, and runs it as a real subprocess -- not a
reconstruction or paraphrase of the script.

Run_Instructions documents data/TQQQ_historical.csv as user-supplied
real historical data, which this repo does not have and should not
fabricate under that name. For this test only, the synthetic
regression fixture (tests/fixtures/regression_ohlcv.csv) is copied to
that path inside the throwaway directory -- clearly test-local, never
written back into the real repo -- purely to exercise the script's
mechanics (imports, constructor, run_sweep call shape) end to end.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _extract_script_from_run_instructions() -> str:
    text = (REPO_ROOT / "Run_Instructions").read_text()
    marker = "Script Example & Ingestion Configuration:"
    assert marker in text, "Run_Instructions no longer contains the expected script section header"
    script = text.split(marker, 1)[1].strip()
    # Guard against silently testing an empty/near-empty extraction.
    assert "run_sweep(" in script, "Extracted script does not contain a run_sweep(...) call"
    return script


def test_run_instructions_example_runs_verbatim_without_raising(tmp_path):
    script_text = _extract_script_from_run_instructions()

    shutil.copy(REPO_ROOT / "optimization_controller.py", tmp_path / "optimization_controller.py")
    shutil.copytree(REPO_ROOT / "src", tmp_path / "src")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shutil.copy(
        REPO_ROOT / "tests" / "fixtures" / "regression_ohlcv.csv",
        data_dir / "TQQQ_historical.csv",
    )

    script_path = tmp_path / "run_instructions_example.py"
    script_path.write_text(script_text)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"Run_Instructions example raised (exit {result.returncode}).\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "Capital Velocity Index" in result.stdout or "Grid Step" in result.stdout, (
        f"Script ran but produced no recognizable results output.\nstdout:\n{result.stdout}"
    )


def test_allocation_pct_matches_real_constructor_keyword():
    # Guards against Run_Instructions silently drifting from the real
    # FixedPortfolioPercentage signature again.
    from src.size_calculators import FixedPortfolioPercentage

    FixedPortfolioPercentage(allocation_pct=0.05)  # raises TypeError if the kwarg name is wrong

    script_text = _extract_script_from_run_instructions()
    assert re.search(r"allocation_pct", script_text), "Run_Instructions example no longer uses allocation_pct"
    assert "allocations=" not in script_text, "Run_Instructions example still uses the non-existent allocations= param"
