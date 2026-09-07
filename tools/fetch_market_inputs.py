#!/usr/bin/env python
"""Pull every public market input in the registry to data/external/.

    python tools/fetch_market_inputs.py --list
    python tools/fetch_market_inputs.py
    python tools/fetch_market_inputs.py --provider fred --refresh

Writes one `timestamp,close` CSV per series -- the shape
ExternalIndexSeries.from_csv already reads -- plus a manifest.json
recording what was actually obtained, so the next stage selects from
measured availability rather than from this file's intentions.

A FAILED SOURCE IS RECORDED, NOT RAISED. Roughly a hundred endpoints are
contacted and some will be retired, renamed or rate-limited on any given
day; a run that aborts on the first of those tells you far less than one
that finishes and hands you the list. TEDRATE, for instance, stopped
publishing in 2022 and is kept deliberately for its history.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ml.sources import SourceUnavailable, default_directory, fetch, registry

# Four at a time. These are public endpoints being asked for a hundred
# files; the sequential version takes about two minutes and a heavier
# pool is how a free service starts refusing you. FRED already resets
# the connection on a sufficiently greedy request.
WORKERS = 4


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=None, help="Defaults to data/external/")
    parser.add_argument("--provider", nargs="+", help="Limit to fred, cboe and/or yahoo.")
    parser.add_argument("--category", nargs="+", help="Limit to categories, e.g. vol credit.")
    parser.add_argument("--refresh", action="store_true", help="Re-fetch series already on disk.")
    parser.add_argument("--list", action="store_true", help="Show the registry and exit.")
    args = parser.parse_args(argv)

    sources = registry()
    if args.provider:
        wanted = {p.lower() for p in args.provider}
        sources = [s for s in sources if s.provider in wanted]
    if args.category:
        wanted = {c.lower() for c in args.category}
        sources = [s for s in sources if s.category in wanted]

    if args.list:
        for source in sources:
            print(
                f"{source.provider:<6} {source.remote_id:<14} {source.category:<14} "
                f"lag {source.lag!s:<10} {source.description}"
            )
        print(f"\n{len(sources)} sources")
        return 0

    directory = args.out or default_directory()
    directory.mkdir(parents=True, exist_ok=True)
    print(f"{len(sources)} sources -> {directory}\n")

    todo = [s for s in sources if args.refresh or not (directory / s.filename).exists()]
    skipped = len(sources) - len(todo)
    if skipped:
        print(f"{skipped} already on disk (use --refresh to re-fetch)\n")

    results: dict[str, dict] = {}
    failures: list[tuple[str, str]] = []

    def pull(source):
        began = time.time()
        try:
            frame = fetch(source)
        except SourceUnavailable as exc:
            return source, None, str(exc), time.time() - began
        except Exception as exc:  # a parse error in one source is still just one source
            return source, None, f"{type(exc).__name__}: {exc}", time.time() - began
        frame.to_csv(directory / source.filename, index=False)
        return source, frame, None, time.time() - began

    started = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for index, (source, frame, error, elapsed) in enumerate(pool.map(pull, todo), 1):
            label = f"[{index:>3}/{len(todo)}] {source.provider:<6} {source.remote_id:<14}"
            if error is not None:
                failures.append((source.remote_id, error))
                print(f"{label} FAILED  {error[:70]}")
                continue
            first, last = frame["timestamp"].iloc[0], frame["timestamp"].iloc[-1]
            # Keyed by provider AND key: Yahoo's ^VIX and CBOE's VIX
            # both reduce to "VIX", and keying on that alone silently
            # drops one of the two from the index of what exists.
            results[f"{source.provider}_{source.key}"] = {
                "provider": source.provider,
                "remote_id": source.remote_id,
                "category": source.category,
                "description": source.description,
                "lag_days": source.lag.total_seconds() / 86400,
                "file": source.filename,
                "rows": len(frame),
                "first": str(first),
                "last": str(last),
                "columns": list(frame.columns),
            }
            print(
                f"{label} {len(frame):>7,} rows  {str(first)[:10]} -> {str(last)[:10]}  {elapsed:4.1f}s"
            )

    # Merged, not overwritten: a --provider run must not erase the
    # record of everything fetched by an earlier one.
    manifest_path = directory / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            print("\n(existing manifest.json was unreadable and has been rebuilt)")
    manifest.update(results)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))

    print(f"\n{len(results)} fetched, {len(failures)} failed, {(time.time() - started):.0f}s")
    print(f"manifest: {manifest_path}  ({len(manifest)} series known)")
    if failures:
        print("\nfailures:")
        for remote_id, error in failures:
            print(f"  {remote_id:<16} {error[:90]}")

    by_category: dict[str, int] = {}
    for entry in manifest.values():
        by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1
    print("\nby category: " + ", ".join(f"{c} {n}" for c, n in sorted(by_category.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
