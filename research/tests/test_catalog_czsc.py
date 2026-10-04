"""research/catalog/czsc.py -- the first six tests are czsc's own
(crates/czsc-core/tests/test_analyze_utils.rs), transcribed."""

from __future__ import annotations

import itertools

import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.czsc import (
    BI,
    CZSC,
    FX,
    NewBar,
    RawBar,
    check_bi,
    check_fx,
    check_fxs,
    get_zs_seq,
    is_bis_down,
    is_bis_up,
    is_symmetry_zs,
    remove_include,
)


def nb(ts, high, low):
    mid = (high + low) / 2
    return NewBar(ts, mid, high, low, mid, 100.0, [])


def test_check_fx_detects_top_pattern():
    fx = check_fx(nb(1, 11, 9), nb(2, 12, 10), nb(3, 11.5, 9.5))
    assert fx.mark == "G" and fx.fx == 12.0


def test_check_fx_detects_bottom_pattern():
    fx = check_fx(nb(1, 11, 9.5), nb(2, 10.5, 8), nb(3, 11, 9))
    assert fx.mark == "D" and fx.fx == 8.0


def test_check_fx_returns_none_when_no_pattern():
    assert check_fx(nb(1, 10, 9), nb(2, 11, 10), nb(3, 12, 11)) is None


def test_check_fxs_keeps_first_of_adjacent_tops():
    bars = [nb(1, 10, 0), nb(2, 12, 2), nb(3, 11, 1), nb(4, 11.5, 0.5), nb(5, 13, 3), nb(6, 10, 0)]
    fxs = check_fxs(bars)
    assert len(fxs) == 1 and fxs[0].mark == "G" and fxs[0].dt == 2


def test_check_fxs_keeps_first_of_adjacent_bottoms():
    bars = [nb(1, 12, 2), nb(2, 10, 0), nb(3, 11, 1), nb(4, 10.5, 1.5), nb(5, 9, -1), nb(6, 12, 2)]
    fxs = check_fxs(bars)
    assert len(fxs) == 1 and fxs[0].mark == "D" and fxs[0].dt == 2


def test_check_bi_returns_none_for_monotone_sequence():
    bars = [nb(i + 1, 10.0 + i, 9.0 + i) for i in range(6)]
    bi, rest = check_bi(bars, 6)
    assert bi is None and len(rest) <= len(bars)


# ---------------------------------------------------------------- inclusion


def test_remove_include_merges_with_the_prevailing_direction():
    k1, k2 = nb(1, 10, 8), nb(2, 12, 9)  # rising pair
    merged, k = remove_include(k1, k2, RawBar(3, 11, 11.5, 9.5, 10))  # inside bar
    assert merged and (k.high, k.low) == (12, 9.5) and k.dt == 2
    assert (k.open, k.close) == (12, 9.5)  # k3 closed down: open high, close low
    k1, k2 = nb(1, 12, 9), nb(2, 10, 8)  # falling pair
    merged, k = remove_include(k1, k2, RawBar(3, 9, 11, 7, 10))  # outside bar
    assert merged and (k.high, k.low) == (10, 7) and k.dt == 3
    merged, k = remove_include(nb(1, 10, 8), nb(2, 10, 9), RawBar(3, 9.5, 9.8, 9.2, 9.6))
    assert not merged  # equal highs: no direction, no merge
    merged, _ = remove_include(k1, k2, RawBar(3, 9, 9.5, 7.5, 9))
    assert not merged  # partial overlap only


# ---------------------------------------------------------------- strokes


def _zigzag(legs, leg_len=8, step=2.0, width=3.0, start=100.0):
    bars, level, t = [], start, 0
    for direction in legs:
        for _ in range(leg_len):
            level += direction * step
            t += 1
            bars.append(RawBar(t, level - width / 2, level, level - width, level - width / 2))
    return bars


def test_czsc_strokes_alternate_between_the_turning_points():
    bars = _zigzag([1, -1, 1, -1, 1, -1, 1])
    c = CZSC(bars)
    dirs = [b.direction for b in c.bi_list]
    assert len(dirs) >= 4
    assert all(a != b for a, b in itertools.pairwise(dirs))
    for bi in c.bi_list:
        assert len(bi.bars) >= 6
        assert bi.fx_a.mark == ("D" if bi.direction == "up" else "G")
        assert (bi.fx_b.fx > bi.fx_a.fx) == (bi.direction == "up")
    tops = {b.fx_b.fx for b in c.bi_list if b.direction == "up"}
    assert tops == {116.0}  # every peak of the band
    assert c.finished_bis == c.bi_list[: len(c.finished_bis)]


def test_czsc_min_bi_len_and_ordering():
    bars = _zigzag([1, -1, 1, -1], leg_len=2)  # a stroke spans 5 merged bars
    assert CZSC(bars, min_bi_len=6).bi_list == []
    assert CZSC(bars, min_bi_len=4).bi_list
    with pytest.raises(ConfigurationError):
        CZSC([RawBar(2, 1, 1, 1, 1), RawBar(1, 1, 1, 1, 1)])


# ---------------------------------------------------------------- pivot zones


def _bi(direction, low, high):
    lo_fx = FX(0, "D", low + 1, low, low, [nb(0, 0, 0)] * 3)
    hi_fx = FX(1, "G", high, high - 1, high, [nb(1, 0, 0)] * 3)
    a, b = (lo_fx, hi_fx) if direction == "up" else (hi_fx, lo_fx)
    return BI(a, b, [a, b], direction, [])


def test_zs_bounds_and_new_zone_on_departure():
    bis = [_bi("up", 10, 20), _bi("down", 12, 20), _bi("up", 12, 18), _bi("down", 15, 22)]
    zs = get_zs_seq(bis)
    assert len(zs) == 1  # a down stroke opens a zone only when it stays above ZG
    first = zs[0]
    assert (first.zg, first.zd) == (18, 12) and first.zz == 15
    leave = [*bis[:3], _bi("down", 19, 25)]  # low 19 > zg 18
    zones = get_zs_seq(leave)
    assert len(zones) == 2 and zones[0].is_valid()
    assert (zones[0].gg, zones[0].dd) == (20, 10)


def test_symmetry_and_structure_shapes():
    sym = [_bi("up", 10, 20), _bi("down", 10.5, 20.5), _bi("up", 10.2, 20.2)]
    assert is_symmetry_zs(sym, 0.1) and not is_symmetry_zs(sym[:2], 0.1)
    up = [_bi("up", 10, 20), _bi("down", 15, 20), _bi("up", 15, 30)]
    assert is_bis_up(up) and not is_bis_down(up)
    down = [_bi("down", 20, 30), _bi("up", 20, 25), _bi("down", 5, 25)]
    assert is_bis_down(down) and not is_bis_up(down)
