"""bridge/versions.py -- which extension this engine expects, and what to
say to an older one."""

from __future__ import annotations

import json

from fidelity_gateway.bridge.versions import (
    EXTENSION_ROOT,
    MINIMUM_EXTENSION_VERSION,
    checked_out_extension_version,
    expected_extension_versions,
    older,
    parse_version,
    version_advice,
)


def test_versions_are_compared_as_numbers():
    assert parse_version("0.10.2") == (0, 10, 2)
    assert older("0.9.0", "0.10.0")
    assert not older("0.10.0", "0.9.0")
    assert not older("0.3", "0.3.0"), "missing parts count as zero"
    assert older("0.3", "0.3.1")


def test_what_is_not_a_version_is_never_older():
    for junk in (None, "", "latest", "1.x", "1..2", 3, "1.2.3.4.5"):
        assert parse_version(junk) is None, junk
        assert not older(junk, "1.0.0")
        assert not older("1.0.0", junk)


def test_the_checked_out_version_is_the_submodules_manifest(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({"version": "1.2.3"}), encoding="utf-8")
    assert checked_out_extension_version(tmp_path) == "1.2.3"
    assert checked_out_extension_version(tmp_path / "absent") is None
    (tmp_path / "manifest.json").write_text("{ not json", encoding="utf-8")
    assert checked_out_extension_version(tmp_path) is None
    (tmp_path / "manifest.json").write_text(json.dumps({"version": "soon"}), encoding="utf-8")
    assert checked_out_extension_version(tmp_path) is None


def test_this_repository_expects_at_least_the_minimum():
    expected = expected_extension_versions()
    assert expected["minimum"] == MINIMUM_EXTENSION_VERSION
    if (EXTENSION_ROOT / "manifest.json").is_file():
        # The submodule this engine was committed with is never older than
        # what the engine itself needs.
        assert not older(expected["latest"], expected["minimum"])


EXPECTED = {"minimum": "0.3.0", "latest": "0.4.0"}


def test_an_extension_below_the_minimum_is_told_what_it_lacks():
    advice = version_advice("0.2.0", EXPECTED)
    assert "older than 0.3.0" in advice and "algorithm editor" in advice
    assert "build-extension" in advice


def test_an_extension_behind_the_checkout_is_told_to_build_and_reload():
    advice = version_advice("0.3.0", EXPECTED)
    assert advice.startswith("0.4.0 is checked out beside the engine")
    assert "Reload now" in advice


def test_an_up_to_date_extension_hears_nothing():
    assert version_advice("0.4.0", EXPECTED) is None
    assert version_advice("0.5.0", EXPECTED) is None
    assert version_advice("0.3.0", {"minimum": "0.3.0", "latest": None}) is None


def test_an_extension_that_did_not_say_its_version_predates_the_minimum():
    assert "did not say its version" in version_advice(None, EXPECTED)
