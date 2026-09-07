"""What the ML research has found so far -- read-only, and precomputed.

--------------------------------------------------------------------
THIS IS A RESEARCH VIEW, NOT A TRADING INPUT

Nothing in this module is on the path from a bar to an order. No
sizing strategy reads it, no live loop imports it, and it cannot
become one by mistake: it only formats artifacts that
tools/fetch_market_inputs.py, tools/build_ml_dataset.py,
tools/evaluate_ml_features.py and tools/ablate_ml_features.py already
wrote to disk. ml_plan.md's own sequencing puts a model on the sizing
path behind Phase 1 baselines and pre-registered evaluation; nothing
here jumps that queue. See ml_plan.md, "Phase ML-0" for what has
actually been measured, and how weak most of it still is.

--------------------------------------------------------------------
PRECOMPUTED, NOT RECOMPUTED PER REQUEST

Evaluating one (ticker, feature-block) pair is a five-fold LightGBM fit
-- seconds, not milliseconds, and the full ablation sweep run by
tools/ablate_ml_features.py takes minutes. An HTTP GET is not the place
to trigger that, so these endpoints only read JSON that a human
already chose to generate and are honest when it is missing: a 404
naming the command to run, never a fabricated empty result that reads
as "nothing here" instead of "nobody has built this yet".

--------------------------------------------------------------------
WHY NO IMPORT OF src.ml.* HERE

src/ml/sources.py and features.py pull in network calls and pandas
transforms this module has no reason to trigger, and evaluate/ablate
need lightgbm -- a dependency this project deliberately keeps out of
the Raspberry Pi's install (see requirements-ml.txt). Reading the JSON
these tools already wrote needs none of that. Keeping this module to
stdlib json + pathlib is what makes it safe to run anywhere
server/app.py itself runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/ml", tags=["ml"])

DATA_ROOT = Path(__file__).resolve().parent.parent / "data"
EXTERNAL_DIR = DATA_ROOT / "external"
ML_DIR = DATA_ROOT / "ml"


def _read_json(path: Path, *, missing_hint: str) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{path.relative_to(DATA_ROOT.parent)} does not exist yet. Run: {missing_hint}",
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500, detail=f"{path.name} is not valid JSON: {exc}"
        ) from exc


@router.get("/sources")
def sources() -> dict[str, Any]:
    """The public data inventory: what was fetched, and how much of it."""
    manifest = _read_json(
        EXTERNAL_DIR / "manifest.json",
        missing_hint="python tools/fetch_market_inputs.py",
    )

    by_category: dict[str, int] = {}
    for entry in manifest.values():
        by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1

    series = sorted(
        (
            {
                "key": key,
                "provider": entry["provider"],
                "remote_id": entry["remote_id"],
                "category": entry["category"],
                "description": entry["description"],
                "lag_days": entry["lag_days"],
                "rows": entry["rows"],
                "first": entry["first"],
                "last": entry["last"],
            }
            for key, entry in manifest.items()
        ),
        key=lambda row: (row["category"], row["provider"], row["remote_id"]),
    )

    return {
        "total_series": len(manifest),
        "by_category": dict(sorted(by_category.items())),
        "series": series,
    }


@router.get("/datasets")
def datasets() -> dict[str, Any]:
    """Per-ticker training sets: size, coverage, and label base rates."""
    schema = _read_json(
        ML_DIR / "schema.json",
        missing_hint="python tools/build_ml_dataset.py --tickers RSP COWZ SPYD",
    )

    tickers = {}
    for ticker, entry in schema.items():
        tickers[ticker] = {
            "rows": entry["rows"],
            "stride": entry["stride"],
            "first": entry["first"],
            "last": entry["last"],
            "feature_count": len(entry["feature_columns"]),
            "label_count": len(entry["label_columns"]),
            "features_fully_present": entry["features_fully_present"],
            "features_below_half": entry["features_below_half"],
            "base_rate": entry["base_rate"],
        }
    return {"tickers": tickers}


@router.get("/evaluation")
def evaluation(label: str = "reached_t0.5_h390") -> dict[str, Any]:
    """Does the macro/cross-asset block beat the bar-only baseline?

    `label` names one (profit_target, horizon) pair, e.g.
    reached_t0.5_h390 = a 0.5%% target within one session. Only labels
    someone has actually run tools/evaluate_ml_features.py for exist;
    others 404 naming the command.
    """
    payload = _read_json(
        ML_DIR / f"evaluation_{label}.json",
        missing_hint=f"python tools/evaluate_ml_features.py --label {label}",
    )
    return {"label": label, "tickers": payload}


@router.get("/evaluation/available")
def evaluation_available() -> dict[str, Any]:
    """Which labels have a saved evaluation, so the UI can offer only those."""
    if not ML_DIR.exists():
        return {"labels": []}
    labels = sorted(
        path.stem.removeprefix("evaluation_") for path in ML_DIR.glob("evaluation_*.json")
    )
    return {"labels": labels}


@router.get("/ablation")
def ablation(label: str = "reached_t0.5_h390") -> dict[str, Any]:
    """Which FEATURE CATEGORY carries any lift found in /evaluation.

    A lift attributed to "macro" is not actionable by itself -- it is
    73 columns across fourteen categories. This is the breakdown by
    category, from tools/ablate_ml_features.py.
    """
    payload = _read_json(
        ML_DIR / f"ablation_{label}.json",
        missing_hint=f"python tools/ablate_ml_features.py --label {label}",
    )
    return {"label": label, "tickers": payload}


__all__ = ["ablation", "datasets", "evaluation", "evaluation_available", "router", "sources"]
