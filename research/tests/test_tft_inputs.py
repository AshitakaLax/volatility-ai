"""The TFT's outside series (research/ml/tft_inputs.py) and the free sources
behind them (research/ml/sources.py): each is causal, the earnings reaction
is measured over the right two sessions, and the San Francisco Fed's
spreadsheet is read without openpyxl."""

from __future__ import annotations

import io
import math
import zipfile

import numpy as np
import pandas as pd
import pytest

from research.ml import sources, tft_features, tft_inputs


def _closes(values, start="2024-01-02"):
    days = pd.bdate_range(start, periods=len(values))
    index = days.tz_localize("UTC") + pd.Timedelta(hours=21)
    return pd.Series(np.asarray(values, float), index=index)


# --------------------------------------------------------------- s_macro


def test_the_uncertainty_shock_reads_only_readings_at_or_before_it():
    rng = np.random.default_rng(3)
    epu = _closes(np.exp(rng.normal(5, 0.4, 400)))
    shock = tft_inputs.uncertainty_shock(epu, smooth=5, window=100)
    changed = epu.copy()
    changed.iloc[300:] *= 10  # a regime change after bar 300
    later = tft_inputs.uncertainty_shock(changed, smooth=5, window=100)
    before = shock.index < epu.index[300]
    pd.testing.assert_series_equal(shock[before], later[before])
    assert later.loc[epu.index[300]] > shock.loc[epu.index[300]]
    assert shock.abs().max() <= tft_inputs.UNCERTAINTY_CLIP
    assert shock.index[0] == epu.index[5 + 100 - 2]  # both windows full


# ------------------------------------------------------------ s_earnings


def test_a_release_is_graded_on_its_reaction_session():
    sessions = pd.DatetimeIndex(pd.bdate_range("2024-07-01", periods=10))
    after = pd.Timestamp("2024-07-02 16:05", tz="America/New_York").tz_convert("UTC")
    assert tft_inputs.reaction_sessions(after, sessions) == (sessions[1], sessions[2])
    before_open = pd.Timestamp("2024-07-02 07:00", tz="America/New_York").tz_convert("UTC")
    assert tft_inputs.reaction_sessions(before_open, sessions) == (sessions[0], sessions[1])
    friday = pd.Timestamp("2024-07-05 16:30", tz="America/New_York").tz_convert("UTC")
    assert tft_inputs.reaction_sessions(friday, sessions) == (sessions[4], sessions[5])  # Monday
    assert tft_inputs.reaction_sessions(after, sessions[:2]) is None


def test_the_earnings_reaction_is_the_reporters_move_less_the_index():
    bench = _closes([100, 100, 101, 101, 101, 101])
    stock = _closes([50, 50, 55, 55, 55, 55])  # +10% on the reaction session
    release = pd.Timestamp("2024-01-03 16:10", tz="America/New_York").tz_convert("UTC")
    events = pd.DataFrame({"ticker": ["GOOGL", "GOOG"], "release": [release, release]})
    s = tft_inputs.earnings_reaction(events, {"GOOGL": stock, "GOOG": stock}, bench, halflife=1.0)
    ear = math.log(55 / 50) - math.log(101 / 100)
    first = s.iloc[0]
    assert s.index[0] == bench.index[2]  # stamped at the reaction session's close
    assert first == pytest.approx(math.tanh(ear / tft_inputs.EAR_SCALE))  # GOOG counted once
    assert list(s.iloc[1:4]) == pytest.approx([first / 2, first / 4, first / 8])  # it fades


def test_earnings_reactions_average_within_a_season():
    bench = _closes([100] * 8)
    a, b = _closes([10, 10, 11, 11, 11, 11, 11, 11]), _closes([10, 10, 9, 9, 9, 9, 9, 9])
    day = pd.Timestamp("2024-01-03", tz="America/New_York")
    events = pd.DataFrame(
        {
            "ticker": ["A", "B"],
            "release": [day + pd.Timedelta(hours=17), day + pd.Timedelta(days=1, hours=7)],
        }
    )
    s = tft_inputs.earnings_reaction(events, {"A": a, "B": b}, bench, halflife=1e9)
    # Both react on the session after 01-03: 01-04 for A (after the close),
    # 01-04 for B too (before the open). With no decay, their mean.
    score = (math.tanh(math.log(1.1) / 0.05) + math.tanh(math.log(0.9) / 0.05)) / 2
    assert s.iloc[0] == pytest.approx(score)


# ------------------------------------------------------ the CSVs the TFT reads


def test_an_input_csv_is_read_point_in_time_by_the_tft(tmp_path):
    series = _closes([0.1, 0.2, 0.3])
    path = tmp_path / "s.csv"
    tft_inputs.as_csv_frame(series).to_csv(path, index=False)
    reader = tft_features.PointInTimeSeries(str(path))
    assert reader.at(series.index[1]) == pytest.approx(0.1)  # strictly after its stamp
    assert reader.at(series.index[1] + pd.Timedelta(minutes=1)) == pytest.approx(0.2)


# ------------------------------------------------------------- the sources


def _xlsx(rows: list[tuple]) -> bytes:
    """A one-sheet workbook ("Data") with shared-string headers and numeric
    cells, as Excel writes it."""
    shared = list(rows[0])
    sheet_rows = []
    for i, row in enumerate(rows, 1):
        cells = []
        for j, value in enumerate(row):
            ref = f"{'AB'[j]}{i}"
            if i == 1:
                cells.append(f'<c r="{ref}" t="s"><v>{shared.index(value)}</v></c>')
            else:
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
        sheet_rows.append(f'<row r="{i}">{"".join(cells)}</row>')
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rel = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "xl/workbook.xml",
            f'<workbook {ns} {rel}><sheets><sheet name="Methodology" sheetId="1" r:id="rId1"/>'
            f'<sheet name="Data" sheetId="2" r:id="rId2"/></sheets></workbook>',
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>',
        )
        z.writestr(
            "xl/sharedStrings.xml",
            f"<sst {ns}>" + "".join(f"<si><t>{s}</t></si>" for s in shared) + "</sst>",
        )
        z.writestr("xl/worksheets/sheet1.xml", f"<worksheet {ns}><sheetData/></worksheet>")
        z.writestr(
            "xl/worksheets/sheet2.xml",
            f"<worksheet {ns}><sheetData>{''.join(sheet_rows)}</sheetData></worksheet>",
        )
    return buf.getvalue()


def test_the_sf_fed_sheet_is_read_and_stamped_a_week_late(monkeypatch):
    # Excel day numbers: 45293 is 2024-01-02.
    body = _xlsx([("date", "News Sentiment"), (45293, -0.12), (45294, 0.05)])
    monkeypatch.setattr(sources, "_http_get", lambda url: body)
    source = next(s for s in sources.registry() if s.provider == "frbsf")
    frame = sources.fetch_frbsf(source)
    assert list(frame["close"]) == pytest.approx([-0.12, 0.05])
    assert frame["timestamp"].iloc[0] == pd.Timestamp("2024-01-09 21:00", tz="UTC")


def test_the_new_free_series_are_registered():
    keys = {f"{s.provider}_{s.key}" for s in sources.registry()}
    assert {tft_inputs.NEWS_SERIES, tft_inputs.UNCERTAINTY_SERIES, "yahoo_AAPL"} <= keys
    with pytest.raises(sources.SourceUnavailable):
        sources._xlsx_rows(b"not a zip", "Data")
