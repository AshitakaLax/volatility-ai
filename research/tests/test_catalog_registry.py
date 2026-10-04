"""research/catalog/registry.py -- every ledger ID is mapped, once, to code
that exists (or to a reason it has none)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from research.catalog.registry import (
    CATALOG_ALIASES,
    CATALOG_VARIANTS,
    ENTRIES,
    LEAD_NOTES,
    LEADS,
    REGISTRY,
    implementations,
    resolve,
)

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "algorithm_ledger.md"
ID = r"[A-Z]+(?:-[A-Z]+)?\d+[a-z]?"
DASH = chr(0x2013)  # the ledger writes ID ranges with an en dash


def _ledger_ids() -> set[str]:
    text = LEDGER.read_text(encoding="utf-8")
    rows = set(re.findall(rf"^\|\s*({ID})\s*\|", text, re.M))
    heads = set(re.findall(rf"^### ({ID})[.{DASH}]", text, re.M))
    ranges = re.findall(rf"^### ([A-Z]+)(\d+){DASH}[A-Z]*(\d+)\.", text, re.M)
    for prefix, lo, hi in ranges:
        rows |= {f"{prefix}{i}" for i in range(int(lo), int(hi) + 1)}
    return rows | heads


def test_every_ledger_id_is_registered_exactly_once():
    ids = [e.ledger_id for e in ENTRIES]
    assert len(ids) == len(set(ids))
    missing = _ledger_ids() - set(ids)
    assert not missing, f"ledger IDs without a registry entry: {sorted(missing)}"
    extra = set(ids) - _ledger_ids()
    assert not extra, f"registry IDs not in the ledger: {sorted(extra)}"


def test_every_entry_has_code_or_a_reason():
    for e in ENTRIES:
        assert e.implementations or e.note, e.ledger_id


def _all_refs():
    for e in ENTRIES:
        yield from e.implementations
    for refs in (*CATALOG_VARIANTS.values(), *LEADS.values()):
        yield from refs


@pytest.mark.parametrize("ref", sorted(set(_all_refs())))
def test_every_reference_resolves(ref):
    if ref.endswith(".py"):
        assert (ROOT / ref).is_file(), ref
    else:
        obj = resolve(ref)
        assert obj is not None


def test_aliases_and_leads_point_at_known_entries():
    for code, targets in CATALOG_ALIASES.items():
        assert targets and all(t in REGISTRY for t in targets), code
    for lead, refs in LEADS.items():
        assert refs or lead in LEAD_NOTES, lead


def test_implementations_helper():
    objs = implementations("C-RJ5")
    assert callable(objs[0]) and objs[0].__name__ == "ghost_trader"
