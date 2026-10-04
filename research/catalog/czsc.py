"""
S5 czsc -- Chan theory (缠论) structure detection, ported from waditu/czsc's
Rust core (crates/czsc-core/src/analyze/utils.rs, analyze/mod.rs,
objects/bi.rs, objects/zs.rs). The ledger leaves czsc ❌ (unvetted: no
published evidence base); this is the structure itself, for the record.

The pipeline:

  1. K-line inclusion (`remove_include`): when one bar's range contains
     the next's, the two merge -- upward (higher high AND higher low kept)
     if the previous pair was rising, downward (lower high and lower low)
     if falling. Equal highs in the previous pair mean no merge.
  2. Fractals (`check_fx`): a top (G) is a merged bar whose high and low are
     both above its neighbours'; a bottom (D) has both below. Consecutive
     fractals of the same kind keep the first (`check_fxs`).
  3. Strokes (笔, `check_bi`): from the first fractal, the most extreme
     opposite fractal beyond it ends a stroke, provided the two fractals do
     not contain each other and the stroke spans at least min_bi_len merged
     bars (czsc's default 6).
  4. `CZSC` runs this bar by bar, extending the last stroke when price
     breaks beyond its end, and keeps the last max_bi_num strokes (50).
  5. Pivot zones (中枢, `get_zs_seq`): consecutive strokes overlap into a
     zone with ZG = min of the first three strokes' highs and ZD = max of
     their lows; a stroke that leaves entirely above ZG (down stroke) or
     below ZD (up stroke) starts a new one.

Not ported: the same-timestamp bar update (a forming bar being revised),
signals, positions and the plotting/caching layer.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field

from engine.core.exceptions import ConfigurationError


@dataclass(frozen=True)
class RawBar:
    dt: int
    open: float
    high: float
    low: float
    close: float
    vol: float = 0.0


@dataclass
class NewBar:
    """A bar after inclusion processing; `elements` are the raw bars merged
    into it (at most the last 100, as in the source)."""

    dt: int
    open: float
    high: float
    low: float
    close: float
    vol: float
    elements: list[RawBar] = field(default_factory=list)

    @classmethod
    def from_raw(cls, bar: RawBar) -> NewBar:
        return cls(bar.dt, bar.open, bar.high, bar.low, bar.close, bar.vol, [bar])


@dataclass
class FX:
    dt: int
    mark: str  # "G" top, "D" bottom
    high: float
    low: float
    fx: float
    elements: list[NewBar]


@dataclass
class BI:
    fx_a: FX
    fx_b: FX
    fxs: list[FX]
    direction: str  # "up" or "down"
    bars: list[NewBar]

    @property
    def high(self) -> float:
        return max(self.fx_a.high, self.fx_b.high)

    @property
    def low(self) -> float:
        return min(self.fx_a.low, self.fx_b.low)

    @property
    def power_price(self) -> float:
        return round(abs(self.fx_b.fx - self.fx_a.fx), 2)


@dataclass
class ZS:
    bis: list[BI]

    @property
    def zg(self) -> float:
        return min(b.high for b in self.bis[:3])

    @property
    def zd(self) -> float:
        return max(b.low for b in self.bis[:3])

    @property
    def zz(self) -> float:
        return self.zd + (self.zg - self.zd) * 0.5

    @property
    def gg(self) -> float:
        return max(b.high for b in self.bis)

    @property
    def dd(self) -> float:
        return min(b.low for b in self.bis)

    def is_valid(self) -> bool:
        zg, zd = self.zg, self.zd
        if zg < zd:
            return False
        return all(
            (zd <= b.high <= zg) or (zd <= b.low <= zg) or (b.high >= zg and b.low <= zd)
            for b in self.bis
        )


def remove_include(k1: NewBar, k2: NewBar, k3: RawBar) -> tuple[bool, NewBar]:
    """utils.rs `remove_include`: (merged?, the bar to keep or append)."""
    if k1.high < k2.high:
        up = True
    elif k1.high > k2.high:
        up = False
    else:
        return False, NewBar.from_raw(k3)
    included = (k2.high <= k3.high and k2.low >= k3.low) or (
        k2.high >= k3.high and k2.low <= k3.low
    )
    if not included:
        return False, NewBar.from_raw(k3)
    if up:
        high, low = max(k2.high, k3.high), max(k2.low, k3.low)
        dt = k2.dt if k2.high > k3.high else k3.dt
    else:
        high, low = min(k2.high, k3.high), min(k2.low, k3.low)
        dt = k2.dt if k2.low < k3.low else k3.dt
    open_, close = (high, low) if k3.open > k3.close else (low, high)
    elements = [x for x in k2.elements[:100] if x.dt != k3.dt] + [k3]
    return True, NewBar(dt, open_, high, low, close, k2.vol + k3.vol, elements)


def check_fx(k1: NewBar, k2: NewBar, k3: NewBar) -> FX | None:
    if k1.high < k2.high > k3.high and k1.low < k2.low > k3.low:
        return FX(k2.dt, "G", k2.high, k2.low, k2.high, [k1, k2, k3])
    if k1.low > k2.low < k3.low and k1.high > k2.high < k3.high:
        return FX(k2.dt, "D", k2.high, k2.low, k2.low, [k1, k2, k3])
    return None


def check_fxs(bars: list[NewBar]) -> list[FX]:
    fxs: list[FX] = []
    for i in range(len(bars) - 2):
        fx = check_fx(bars[i], bars[i + 1], bars[i + 2])
        if fx is not None and not (fxs and fx.mark == fxs[-1].mark):
            fxs.append(fx)
    return fxs


def check_bi(bars: list[NewBar], min_bi_len: int = 6) -> tuple[BI | None, list[NewBar]]:
    """utils.rs `check_bi`: (stroke or None, the bars still to analyse)."""
    fxs = check_fxs(bars)
    if len(fxs) < 2:
        return None, bars
    fx_a = fxs[0]
    if fx_a.mark == "D":
        direction = "up"
        cands = [x for x in fxs if x.mark == "G" and x.dt > fx_a.dt and x.fx > fx_a.fx]
        fx_b = None
        for x in cands:
            if fx_b is None or x.high > fx_b.high:
                fx_b = x
    else:
        direction = "down"
        cands = [x for x in fxs if x.mark == "D" and x.dt > fx_a.dt and x.fx < fx_a.fx]
        fx_b = None
        for x in cands:
            if fx_b is None or x.low < fx_b.low:
                fx_b = x
    if fx_b is None:
        return None, bars
    dts = [b.dt for b in bars]
    start_dt, end_dt = fx_a.elements[0].dt, fx_b.elements[2].dt
    start_idx, end_idx = bisect_left(dts, start_dt), bisect_right(dts, end_dt)
    if start_idx >= end_idx:
        return None, bars
    bars_a = bars[start_idx:end_idx]
    bars_b = bars[bisect_left(dts, fx_b.elements[0].dt) :]
    ab_include = (fx_a.high > fx_b.high and fx_a.low < fx_b.low) or (
        fx_a.high < fx_b.high and fx_a.low > fx_b.low
    )
    if not ab_include and len(bars_a) >= min_bi_len:
        inner = [x for x in fxs if start_dt <= x.dt <= end_dt]
        return BI(fx_a, fx_b, inner, direction, bars_a), bars_b
    return None, bars


class CZSC:
    """analyze/mod.rs `CZSC`, fed one raw bar at a time (strictly increasing
    dt)."""

    def __init__(self, bars=(), max_bi_num: int = 50, min_bi_len: int = 6) -> None:
        if min_bi_len < 1 or max_bi_num < 1:
            raise ConfigurationError("min_bi_len and max_bi_num must be >= 1")
        self.max_bi_num, self.min_bi_len = max_bi_num, min_bi_len
        self.bars_ubi: list[NewBar] = []
        self.bi_list: list[BI] = []
        self._last_dt: int | None = None
        for b in bars:
            self.update_bar(b)

    def update_bar(self, bar: RawBar) -> None:
        if self._last_dt is not None and bar.dt <= self._last_dt:
            raise ConfigurationError("bars must arrive with strictly increasing dt")
        self._last_dt = bar.dt
        if len(self.bars_ubi) < 2:
            self.bars_ubi.append(NewBar.from_raw(bar))
        else:
            merged, k3 = remove_include(self.bars_ubi[-2], self.bars_ubi[-1], bar)
            if merged:
                self.bars_ubi[-1] = k3
            else:
                self.bars_ubi.append(k3)
        self._update_bi()
        if len(self.bi_list) > self.max_bi_num:
            del self.bi_list[: len(self.bi_list) - self.max_bi_num]

    def _update_bi(self) -> None:
        if len(self.bars_ubi) < 3:
            return
        if not self.bi_list:
            fxs = check_fxs(self.bars_ubi)
            if not fxs:
                return
            first = fxs[0]
            fx_a = first
            for x in fxs[1:]:
                if x.mark != first.mark:
                    continue
                if (first.mark == "D" and x.low <= fx_a.low) or (
                    first.mark == "G" and x.high >= fx_a.high
                ):
                    fx_a = x
            bars = [x for x in self.bars_ubi if x.dt >= fx_a.elements[0].dt]
            bi, rest = check_bi(bars, self.min_bi_len)
            if bi is not None:
                self.bi_list.append(bi)
            self.bars_ubi = list(rest)
            return
        bi, rest = check_bi(self.bars_ubi, self.min_bi_len)
        if bi is not None:
            self.bi_list.append(bi)
        self.bars_ubi = list(rest)
        last = self.bi_list[-1]
        tail = self.bars_ubi[-1] if self.bars_ubi else None
        if tail is not None and (
            (last.direction == "up" and tail.high > last.high)
            or (last.direction == "down" and tail.low < last.low)
        ):
            merge_point = last.bars[-2].dt
            self.bars_ubi = last.bars[:-2] + [x for x in self.bars_ubi if x.dt >= merge_point]
            self.bi_list.pop()

    @property
    def finished_bis(self) -> list[BI]:
        """The last stroke counts as finished once five merged bars follow."""
        if not self.bi_list:
            return []
        return self.bi_list[:-1] if len(self.bars_ubi) < 5 else list(self.bi_list)

    @property
    def fx_list(self) -> list[FX]:
        out: list[FX] = []
        for bi in self.bi_list:
            for x in bi.fxs[1:]:
                if not out or x.dt > out[-1].dt:
                    out.append(x)
        for x in check_fxs(self.bars_ubi) if self.bars_ubi else []:
            if not out or x.dt > out[-1].dt:
                out.append(x)
        return out


def get_zs_seq(bis: list[BI]) -> list[ZS]:
    """utils.rs `get_zs_seq`: split consecutive strokes into pivot zones."""
    zs_list: list[ZS] = []
    for bi in bis:
        if not zs_list:
            zs_list.append(ZS([bi]))
            continue
        last = zs_list[-1]
        if (bi.direction == "up" and bi.high < last.zd) or (
            bi.direction == "down" and bi.low > last.zg
        ):
            zs_list.append(ZS([bi]))
        else:
            zs_list[-1] = ZS([*last.bis, bi])
    return zs_list


def is_symmetry_zs(bis: list[BI], threshold: float = 0.1) -> bool:
    """utils.rs `is_symmetry_zs`: an odd number (>= 3) of overlapping strokes
    whose price spans have a coefficient of variation <= threshold."""
    if len(bis) < 3 or len(bis) % 2 == 0 or not threshold >= 0:
        return False
    zs = ZS(list(bis))
    if zs.zd > zs.zg or max(b.low for b in bis) > min(b.high for b in bis):
        return False
    powers = [b.power_price for b in bis]
    mean = sum(powers) / len(powers)
    if mean == 0:
        return False
    std = (sum((p - mean) ** 2 for p in powers) / len(powers)) ** 0.5
    return std / abs(mean) <= threshold


def is_bis_up(bis: list[BI]) -> bool:
    """An odd run of strokes that ends on the high and starts on the low."""
    if len(bis) < 3 or len(bis) % 2 == 0:
        return False
    return (
        bis[-1].direction == "up"
        and bis[-1].high == max(b.high for b in bis)
        and bis[0].low == min(b.low for b in bis)
    )


def is_bis_down(bis: list[BI]) -> bool:
    if len(bis) < 3 or len(bis) % 2 == 0:
        return False
    return (
        bis[-1].direction == "down"
        and bis[0].high == max(b.high for b in bis)
        and bis[-1].low == min(b.low for b in bis)
    )
