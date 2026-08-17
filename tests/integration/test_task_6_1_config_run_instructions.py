"""
Task 6.1 acceptance test (documentation completeness half): the new
config-driven example in Run_Instructions (Step 3, added by this
task's rewrite), copy-pasted verbatim including its config.yaml, runs
to completion without raising -- same verbatim-subprocess approach as
tests/integration/test_task_1_1_run_instructions.py uses for Step 2's
script, applied to Step 3.
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _extract_between(text: str, start_marker: str, end_marker: str) -> str:
    assert start_marker in text, f"Run_Instructions no longer contains {start_marker!r}"
    after_start = text.split(start_marker, 1)[1]
    assert end_marker in after_start, f"Run_Instructions no longer contains {end_marker!r} after {start_marker!r}"
    return after_start.split(end_marker, 1)[0].strip()


def test_config_driven_example_runs_verbatim_without_raising(tmp_path):
    text = (REPO_ROOT / "Run_Instructions").read_text()

    yaml_text = _extract_between(
        text,
        "Example config.yaml (every section except strategy/grid is optional -- omitted sections use the defaults shown):\n",
        "\nScript Example:",
    )
    script_text = _extract_between(text, "Script Example:\n", "\nStep 4:")

    assert "run_sweep(" in script_text
    assert "strategy_id" in yaml_text

    shutil.copy(REPO_ROOT / "optimization_controller.py", tmp_path / "optimization_controller.py")
    shutil.copytree(REPO_ROOT / "src", tmp_path / "src")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shutil.copy(
        REPO_ROOT / "tests" / "fixtures" / "regression_ohlcv.csv",
        data_dir / "TQQQ_historical.csv",
    )
    (tmp_path / "config.yaml").write_text(yaml_text)
    script_path = tmp_path / "run_config_example.py"
    script_path.write_text(script_text)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"Config-driven Run_Instructions example raised (exit {result.returncode}).\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "Capital Velocity Index" in result.stdout or "Grid Step" in result.stdout


def test_every_run_sweep_kwarg_named_in_run_instructions_actually_exists():
    import inspect

    from optimization_controller import OptimizationController

    text = (REPO_ROOT / "Run_Instructions").read_text()
    reference_section = _extract_between(
        text,
        "Step 4: Optional run_sweep() Capabilities Reference\n",
        "\n\nAdditional, related tools beyond run_sweep() itself:",
    )
    named_params = [
        "cost_model", "risk_manager", "on_flat_reentry", "symbol", "initial_cash",
        "n_jobs", "search_strategy", "search_seed", "search_direction",
        "rank_by", "tie_break_by", "return_full_results",
    ]
    real_params = set(inspect.signature(OptimizationController.run_sweep).parameters.keys())
    for param in named_params:
        assert param in reference_section, f"{param} is missing from Run_Instructions' own capabilities reference"
        assert param in real_params, f"Run_Instructions documents {param}, but it isn't a real run_sweep() parameter"
