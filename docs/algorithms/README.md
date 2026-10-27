# Algorithm pages

One page per algorithm in the ranked list of
[`docs/algorithm_ledger.md` §8C](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import),
the 14,225-row CSV import of 2026-10-27. The ledger's tables say, for
every row, whether volatility-ai implements it and link here.

| Path | What it is | Written by |
|---|---|---|
| `<slug>.md` without a `generated` first line | A **researched** page: the rule, evidence for and against, fit with the project's constraints, what the repository already has, and how to test it here. Ledger IDs RK1–RK3. | hand |
| `<slug>.md` with a `generated` first line | A **card** for one of the 425 specific algorithms (ranks 1–425): the CSV's own text plus the implementation status. | `tools/build_algorithm_ledger.py` |
| `concepts/<slug>.md` | One page per description shared by the 13,800 title-reconstructed rows (ranks 426–14,225): the description, every variant of the other fields its members carry, and the members. [Index](concepts/README.md). | the build |
| `ranked/ranks-*.md` | The title-reconstructed rows by rank, 1,000 per page, each linked to its concept page. | the build |
| `implementation_status.csv` | Which algorithms have code here: status, ledger IDs, code references, a note. Not listed means not implemented. | hand |
| `source/*.csv.xz` | The import itself, every field of every row (`xz -dk` to read it). | the import |

## Researched so far

| ID | Algorithm | Rank | Implemented |
|---|---|---|---|
| RK1 | [Time-Series Momentum (TSMOM)](time-series-momentum-tsmom.md) | 1 | Research code (as published) |
| RK2 | [Volatility-Scaled Trend Following](volatility-scaled-trend-following.md) | 2 | Research code; the scaling half is wired (S4) |
| RK3 | [Dual Momentum (Absolute + Relative)](dual-momentum-absolute-relative.md) | 3 | Yes, as `tools/rotation.py --mode relative_strength` (X3) |

## Implementation status values

| Value | Meaning |
|---|---|
| `yes` | Runs on the platform: a registered strategy, a strategy option, an engine feature or a harness mode. |
| `research` | The algorithm as described is tested standalone code in `research/`, not wired into a strategy or harness. |
| `partial` | A component, a long-only adaptation or a close variant exists; the algorithm as described does not. |
| `no` | Nothing in the repository (a row with `no` is only there to carry a note). |

In `implementation_status.csv`, `ledger` and `code` take several values
separated by `;`. A code reference is `package.module:qualname`,
`package.module` or a path such as `tools/rotation.py`; the tests import
or find every one.

## Changing anything here

```bash
# after editing implementation_status.csv, or researching a page
python tools/build_algorithm_ledger.py
python tools/build_algorithm_ledger.py --check     # what the test runs: exit 1 if stale
# a new export of the list
python tools/build_algorithm_ledger.py --source docs/algorithms/source/<new>.csv.xz
```

Generated pages are overwritten and, when the import stops producing
them, deleted. A page whose first line is not the `generated` comment is
never touched. To research an algorithm: write its page over the card
(keep the file name, drop the comment line), add an `RK<rank>` entry to
the ledger's §8C and to `research/catalog/registry.py`, put the RK ID in
its `implementation_status.csv` row, and re-run the build.
