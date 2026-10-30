"""tools/build_algorithm_ledger.py: the ranked list in docs/algorithm_ledger.md
section 8C and docs/algorithms/ stay in step with the import and with
implementation_status.csv, and every code reference in it exists."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from research.catalog.registry import REGISTRY, resolve
from tools.build_algorithm_ledger import (
    BEGIN,
    COLUMNS,
    DASH,
    END,
    GENERATED_MARK,
    PAGES,
    RECONSTRUCTED,
    ROOT,
    SOURCE,
    STATUS,
    build,
    cell,
    is_generated,
    read_source,
    slugify,
    split_refs,
    stale_generated,
    unique_slugs,
)


def _status_rows() -> list[dict[str, str]]:
    with STATUS.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_committed_pages_match_the_import_and_the_status_file():
    """What `python tools/build_algorithm_ledger.py --check` checks: an
    edit to implementation_status.csv (or to a generated page) without a
    re-run fails here, not in a reader's hands."""
    outputs = build()
    stale = [p for p, text in outputs.items() if not p.is_file() or p.read_text("utf-8") != text]
    assert not stale, f"re-run tools/build_algorithm_ledger.py: {stale[:5]}"
    assert stale_generated(PAGES, outputs) == []


@pytest.mark.parametrize(
    "ref", sorted({r for row in _status_rows() for r in split_refs(row["code"])})
)
def test_every_code_reference_resolves(ref):
    if ref.endswith(".py"):
        assert (ROOT / ref).is_file(), ref
    else:
        assert resolve(ref) is not None


def test_every_ledger_id_in_the_status_file_is_registered():
    cited = {i for row in _status_rows() for i in split_refs(row["ledger"])}
    assert cited - set(REGISTRY) == set()


def test_every_rk_entry_has_a_researched_page_and_cites_itself():
    """RK<n> is the algorithm at rank n of the import: its page is
    hand-written, and its status row names the RK ID."""
    by_rank = {a.rank: a for a in read_source(SOURCE)}
    status = {row["algorithm"]: row for row in _status_rows()}
    rk = sorted(i for i in REGISTRY if i.startswith("RK"))
    assert rk, "no RK entries registered"
    for ledger_id in rk:
        algorithm = by_rank[int(ledger_id[2:])]
        page = PAGES / f"{slugify(algorithm.name)}.md"
        assert page.is_file() and not is_generated(page), page
        assert ledger_id in split_refs(status[algorithm.name]["ledger"])


def test_slugs_keep_dashes_and_stay_unique():
    assert slugify(f"12{DASH}1 Momentum (Skip-Month)") == "12-1-momentum-skip-month"
    assert slugify(f"Fama{DASH}French Five-Factor Model Portfolio") == (
        "fama-french-five-factor-model-portfolio"
    )
    assert slugify(f"Ornstein{DASH}Uhlenbeck Spread Trading") == "ornstein-uhlenbeck-spread-trading"
    assert unique_slugs(["A b", "a-b", "A  B"]) == ["a-b", "a-b-2", "a-b-3"]


def test_table_cells_escape_pipes_brackets_and_newlines():
    assert cell("a | b\n<c>") == "a \\| b &lt;c&gt;"
    assert cell("") == "—"


# ---------------------------------------------------------------- a small import


def _row(rank: int, name: str, description: str, basis: str) -> dict[str, str]:
    row = {col: f"{key} of {name}" for key, col in COLUMNS.items()}
    row.update(
        {
            COLUMNS["name"]: name,
            COLUMNS["rank"]: str(rank),
            COLUMNS["ai_rank"]: str(rank + 100),
            COLUMNS["retail_rank"]: str(rank + 200),
            COLUMNS["description"]: description,
            COLUMNS["basis"]: basis,
            COLUMNS["references"]: "https://example.org/a\nhttps://example.org/b",
        }
    )
    return row


@pytest.fixture
def small(tmp_path: Path) -> dict[str, Path]:
    specific = "Existing specific description retained."
    generic = f"{RECONSTRUCTED}; executable rules are not established."
    rows = [
        _row(1, "Alpha Trend", "Buy the trend.", specific),
        _row(2, "Beta Reversion", "Sell the rally.", specific),
        _row(3, "Gamma Scholarly Pair MK-1", "Proposed pair model: trade a pair.", generic),
        _row(4, "Delta Scholarly Pair MK-2", "Proposed pair model: trade a pair.", generic),
        _row(5, "Eps Scholarly Basket MK-3", "Proposed basket model: hold a basket.", generic),
    ]
    source = tmp_path / "list_2026-01-02.csv"
    with source.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(COLUMNS.values()))
        writer.writeheader()
        writer.writerows(rows)
    status = tmp_path / "status.csv"
    status.write_text(
        "algorithm,status,ledger,code,note\n"
        'Alpha Trend,yes,X3,tools/rotation.py,"Run by rotation."\n',
        encoding="utf-8",
    )
    ledger = tmp_path / "ledger.md"
    ledger.write_text(f"# Ledger\n\n{BEGIN}\nold\n{END}\n\n## 9. After\n", encoding="utf-8")
    pages = tmp_path / "algorithms"
    pages.mkdir()
    return {"source": source, "status": status, "ledger": ledger, "pages": pages}


def _build(small: dict[str, Path]) -> dict[Path, str]:
    return build(small["source"], small["status"], small["pages"], small["ledger"])


def test_specific_rows_get_cards_and_reconstructed_rows_share_concepts(small):
    out = _build(small)
    pages = small["pages"]
    card = out[pages / "alpha-trend.md"]
    assert card.startswith(GENERATED_MARK)
    assert "| Implemented in volatility-ai | **Yes** |" in card
    assert "[`tools/rotation.py`](../../tools/rotation.py)" in card
    assert "- <https://example.org/a>" in card and "- <https://example.org/b>" in card
    assert "| Implemented in volatility-ai | **No** |" in out[pages / "beta-reversion.md"]

    pair = out[pages / "concepts" / "pair-model.md"]
    assert "**2** of the 5 algorithms" in pair and "| 3 | Gamma Scholarly Pair MK-1 |" in pair
    assert (pages / "concepts" / "basket-model.md") in out
    shard = out[pages / "ranked" / "ranks-00003-00005.md"]
    assert "[concept](../concepts/pair-model.md)" in shard
    assert "[concept](../concepts/basket-model.md)" in shard


def test_the_ledger_block_is_replaced_and_the_rest_kept(small):
    text = _build(small)[small["ledger"]]
    assert text.startswith("# Ledger\n\n" + BEGIN) and text.endswith(END + "\n\n## 9. After\n")
    assert "old" not in text
    assert "| 1 | Alpha Trend | family of Alpha Trend | 101 | 201 | Yes | X3 | [card]" in text
    assert f"| Specific (ranks 1{DASH}2) | 2 | 1 | 0 | 0 | 1 |" in text
    assert f"[ranks 3{DASH}5](algorithms/ranked/ranks-00003-00005.md)" in text


def test_a_researched_page_is_linked_and_never_overwritten(small):
    page = small["pages"] / "beta-reversion.md"
    page.write_text("# Beta Reversion\n\nResearched by hand.\n", encoding="utf-8")
    out = _build(small)
    assert page not in out
    assert "[**researched**](algorithms/beta-reversion.md)" in out[small["ledger"]]


def test_a_researched_concept_page_is_kept_and_linked_from_its_members(small):
    concepts = small["pages"] / "concepts"
    concepts.mkdir()
    page = concepts / "pair-model.md"
    page.write_text("# Pair model\n\nResearched by hand.\n", encoding="utf-8")
    out = _build(small)
    assert page not in out
    shard = out[small["pages"] / "ranked" / "ranks-00003-00005.md"]
    assert "| 3 | Gamma Scholarly Pair MK-1 |" in shard
    assert "[**researched** concept](../concepts/pair-model.md)" in shard
    assert "[concept](../concepts/basket-model.md)" in shard
    index = out[concepts / "README.md"]
    assert "[Pair model](pair-model.md) · **researched** |" in index
    assert "1 of them are researched." in index
    assert (
        "2 [concept pages](algorithms/concepts/README.md), 1 of them researched."
        in out[small["ledger"]]
    )
    assert stale_generated(small["pages"], out) == []


def test_marked_pages_the_import_no_longer_produces_are_stale(small):
    gone = small["pages"] / "dropped-algorithm.md"
    gone.write_text(f"{GENERATED_MARK} from x. -->\n", encoding="utf-8")
    kept = small["pages"] / "notes.md"
    kept.write_text("# Notes by hand\n", encoding="utf-8")
    assert stale_generated(small["pages"], _build(small)) == [gone]


def test_a_status_row_must_name_an_imported_algorithm(small):
    small["status"].write_text(
        "algorithm,status,ledger,code,note\nNo Such Thing,yes,,,\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="not in the import"):
        _build(small)


def test_the_ledger_needs_its_markers(small):
    small["ledger"].write_text("# Ledger without markers\n", encoding="utf-8")
    with pytest.raises(ValueError, match="needs exactly one"):
        _build(small)
