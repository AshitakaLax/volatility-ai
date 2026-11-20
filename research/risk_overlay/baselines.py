"""
Each fund's baselines: the scale a report's figures are measured against.

The daily tiers and the grid spacing compare a report's expected 1-day move
with the fund's MEDIAN expected move over the research window; the weekly
cap compares its 21- and 63-session expected shortfall with the fund's
median for that horizon. Both medians are the proxy's
(research/risk_overlay/proxy.py) over 2016-01-04 to the latest session, the
window the deployed books were researched on, so a report and the proxy are
measured on one scale.

They are frozen numbers, committed in baselines.json beside this file and
written only by `python tools/build_proxy_reports.py --baselines`: a mapping
that recomputed its own baseline from a moving window would drift under
the thresholds pre-registered against it. A fund with no entry has no
baseline, and the mappings abstain for it (the session trades as
configured) rather than guess one.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

BASELINES_FILE = Path(__file__).resolve().parent / "baselines.json"


@dataclass(frozen=True)
class Baseline:
    """One fund's frozen baselines. `move_pct` is the median expected 1-day
    move; `es5_pct` the median 5% expected shortfall by horizon (negative
    percentages); `window` the sessions they were measured over."""

    symbol: str
    move_pct: float
    es5_pct: Mapping[str, float] = field(default_factory=dict)
    window: tuple[str, str] | None = None
    source: str = ""
    computed_at: str | None = None

    def es5(self, horizon: str) -> float | None:
        value = self.es5_pct.get(horizon)
        return float(value) if value is not None else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "move_pct": self.move_pct,
            "es5_pct": dict(self.es5_pct),
            "window": list(self.window) if self.window else None,
            "source": self.source,
            "computed_at": self.computed_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Baseline:
        window = data.get("window")
        return cls(
            symbol=str(data["symbol"]).upper(),
            move_pct=float(data["move_pct"]),
            es5_pct={str(k): float(v) for k, v in (data.get("es5_pct") or {}).items()},
            window=tuple(window) if window else None,
            source=str(data.get("source") or ""),
            computed_at=data.get("computed_at"),
        )


def read_baselines(path: Path | str = BASELINES_FILE) -> dict[str, Baseline]:
    """{symbol: Baseline} from `path`; {} when it is missing."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    funds = data.get("funds", {}) if isinstance(data, dict) else {}
    return {
        symbol.upper(): Baseline.from_dict({**row, "symbol": symbol})
        for symbol, row in funds.items()
    }


@lru_cache(maxsize=4)
def _cached(path: str) -> dict[str, Baseline]:
    return read_baselines(path)


def baseline_for(symbol: str, path: Path | str = BASELINES_FILE) -> Baseline | None:
    """The committed baseline for `symbol`, or None."""
    return _cached(str(path)).get(symbol.upper())


def write_baselines(
    baselines: Mapping[str, Baseline], path: Path | str = BASELINES_FILE, **meta
) -> None:
    """Write `baselines` (tools/build_proxy_reports.py --baselines only)."""
    data = {
        "note": (
            "Frozen baselines for research/risk_overlay/mapping.py; written by "
            "tools/build_proxy_reports.py --baselines. Do not edit by hand."
        ),
        **meta,
        "funds": {
            symbol: {k: v for k, v in b.to_dict().items() if k != "symbol"}
            for symbol, b in sorted(baselines.items())
        },
    }
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _cached.cache_clear()


__all__ = ["BASELINES_FILE", "Baseline", "baseline_for", "read_baselines", "write_baselines"]
