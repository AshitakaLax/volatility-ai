"""engine/core/build_info.py: which code a process runs, without git."""

from __future__ import annotations

from engine.core import build_info


def _tree(root, body: str = "x = 1\n"):
    (root / "engine").mkdir(parents=True, exist_ok=True)
    (root / "engine" / "a.py").write_text(body)
    (root / "cli.py").write_text("print('hi')\n")
    return root


def test_equal_code_gives_an_equal_fingerprint(tmp_path):
    first = build_info.code_fingerprint.__wrapped__(_tree(tmp_path / "one"))
    second = build_info.code_fingerprint.__wrapped__(_tree(tmp_path / "two"))
    assert first == second and len(first) == 12


def test_any_change_changes_it(tmp_path):
    before = build_info.code_fingerprint.__wrapped__(_tree(tmp_path / "one"))
    after = build_info.code_fingerprint.__wrapped__(_tree(tmp_path / "two", "x = 2\n"))
    assert before != after


def test_bytecode_does_not_count(tmp_path):
    root = _tree(tmp_path / "one")
    before = build_info.code_fingerprint.__wrapped__(root)
    (root / "engine" / "__pycache__").mkdir()
    (root / "engine" / "__pycache__" / "a.py").write_text("stale")
    assert build_info.code_fingerprint.__wrapped__(root) == before


def test_tests_do_not_count_they_never_run_in_a_deployment(tmp_path):
    root = _tree(tmp_path / "one")
    before = build_info.code_fingerprint.__wrapped__(root)
    (root / "engine" / "tests").mkdir()
    (root / "engine" / "tests" / "test_a.py").write_text("assert True\n")
    assert build_info.code_fingerprint.__wrapped__(root) == before


def test_nothing_to_fingerprint_says_so(tmp_path):
    assert build_info.code_fingerprint.__wrapped__(tmp_path) is None


def test_the_commit_comes_only_from_the_build(monkeypatch):
    monkeypatch.delenv("VAI_BUILD_COMMIT", raising=False)
    assert build_info.identity()["commit"] is None
    monkeypatch.setenv("VAI_BUILD_COMMIT", "c8bf06c")
    identity = build_info.identity()
    assert identity["commit"] == "c8bf06c"
    assert identity["code"] == build_info.code_fingerprint()
