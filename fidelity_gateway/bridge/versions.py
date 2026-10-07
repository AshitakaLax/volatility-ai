"""
Which Fidelity Bridge extension this engine expects, and what to tell
someone running an older one.

Two versions matter:

  * MINIMUM_EXTENSION_VERSION -- the oldest that has everything this
    engine relies on: its order reports, the engine status it shows, the
    calls the algorithm editor makes. An older extension still trades,
    but the popup cannot show what the engine is doing and the editor
    cannot work.
  * the version checked out beside the engine, in the
    fidelity-bridge-chrome-extension submodule -- the one this engine was
    committed with. An extension older than that has an update waiting:
    `python -m fidelity_gateway.bridge build-extension`, then Reload.

The server sends both to every extension that connects (a sealed
"versions" message), logs when the one connecting is older, and the
extension's popup says what to do.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

MINIMUM_EXTENSION_VERSION = "0.3.0"
EXTENSION_ROOT = Path(__file__).resolve().parents[2] / "fidelity-bridge-chrome-extension"
_VERSION = re.compile(r"^\d+(\.\d+){0,3}$")


def parse_version(value: object) -> tuple[int, ...] | None:
    """'0.10.2' -> (0, 10, 2); None for anything that is not one. Compared
    as numbers, so 0.10 is newer than 0.9."""
    if not isinstance(value, str) or not _VERSION.match(value.strip()):
        return None
    return tuple(int(part) for part in value.strip().split("."))


def older(version: object, than: object) -> bool:
    """Whether `version` is older than `than`. False when either is not a version."""
    a, b = parse_version(version), parse_version(than)
    if a is None or b is None:
        return False
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) < b + (0,) * (width - len(b))


def checked_out_extension_version(root: Path = EXTENSION_ROOT) -> str | None:
    """The version in the submodule's manifest.json, or None when the
    submodule is not checked out (a deployment without the extension's
    source, or a CI that does not fetch it)."""
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    version = manifest.get("version") if isinstance(manifest, dict) else None
    return version if parse_version(version) is not None else None


def expected_extension_versions(root: Path = EXTENSION_ROOT) -> dict:
    """What the server tells every extension: {"minimum", "latest"}."""
    return {"minimum": MINIMUM_EXTENSION_VERSION, "latest": checked_out_extension_version(root)}


def version_advice(connected: object, expected: dict) -> str | None:
    """A sentence for the engine's log when the connecting extension is
    older than it should be; None when it is not."""
    if parse_version(connected) is None:
        return (
            f"it did not say its version, so it predates {expected['minimum']}: update it "
            "(python -m fidelity_gateway.bridge build-extension, then Reload)"
        )
    if older(connected, expected.get("minimum")):
        return (
            f"it is older than {expected['minimum']}, which this engine needs for its order "
            "reports, its status in the popup and the algorithm editor: update it "
            "(python -m fidelity_gateway.bridge build-extension, then Reload)"
        )
    if older(connected, expected.get("latest")):
        return (
            f"{expected['latest']} is checked out beside the engine: build it "
            "(python -m fidelity_gateway.bridge build-extension), then press Reload now in "
            "the extension's popup"
        )
    return None
