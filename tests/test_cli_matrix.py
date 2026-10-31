"""`cli.py matrix`, through a real subprocess (tests/CLAUDE.md): its exit
codes and what it writes. The run itself is research/tests/test_matrix.py's."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "cli.py", "matrix", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _trial(buy, sell, value):
    return {
        "symbol": "X",
        "buy_id": buy,
        "sell_id": sell,
        "cell": f"{buy}|{sell}",
        "track": "no_loss",
        "metrics": {"Calmar": value, "Total Return %": value * 10},
        "years": [{"year": 2020 + i, "return_pct": value + i} for i in range(3)],
    }


def test_analyze_writes_a_report(tmp_path):
    trials = [
        _trial(b, s, v)
        for b, s, v in [("b1", "s1", 1.0), ("b1", "s2", 2.0), ("b2", "s1", 3.0), ("b2", "s2", 4.0)]
    ]
    (tmp_path / "trials.jsonl").write_text("\n".join(json.dumps(t) for t in trials) + "\n")
    result = _cli("--analyze", str(tmp_path))
    assert result.returncode == 0, result.stderr
    report = (tmp_path / "report.md").read_text()
    assert "## Track: no-loss" in report and "b2" in report


def test_analyze_without_trials_exits_2(tmp_path):
    result = _cli("--analyze", str(tmp_path))
    assert result.returncode == 2
    assert "No trials.jsonl" in result.stderr


def test_a_run_needs_a_config_and_an_output():
    assert _cli().returncode == 2


def test_an_invalid_matrix_config_exits_2(tmp_path):
    config = tmp_path / "m.yaml"
    config.write_text(
        "matrix: {min_history_years: 2, buys: [{id: fixed}], sells: [{id: fixed_target}]}\n"
    )
    result = _cli("--config", str(config), "--output", str(tmp_path / "out"))
    assert result.returncode == 2
    assert "at least 5" in result.stderr


def test_the_committed_first_matrix_loads_and_plans_64_cells():
    from research.composition.matrix import load_spec, plan_cells

    spec = load_spec(ROOT / "config" / "matrix" / "first_8x8x4.yaml")
    assert len(plan_cells(spec)) == 64
    assert spec.min_history_years >= 10
