"""analyze_annual must re-simulate each row with the class that made it.

It used to hardcode hf_local_reference. For a GatedLocalReferenceSizing
row that silently dropped every gate column (HF's signature does not
accept them) and printed the champion's year-by-year under the gated
row's headline numbers. These tests pin the per-row resolution and that
the gate parameters survive the round trip through a sweep CSV.
"""

from __future__ import annotations

import io

import pandas as pd
import pytest

from research.analysis.analyze_annual import _constructor_params, _strategy_class_for
from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing


def _merged_csv_rows() -> pd.DataFrame:
    """One HF row and one gated row, written and read back through CSV
    exactly as output/*.csv is -- which is what turns the gated int
    columns into float64 (the HF row leaves them blank)."""
    rows = pd.DataFrame(
        [
            {
                "Grid Step": 0.00075,
                "Profit Target": 0.3,
                "Strategy": "HighFrequencyLocalReferenceSizing",
                "per_lot_pct": 0.0002,
                "lookback_days": 0.02,
                "bars_per_day": 387,
                "Total Return %": 10.0,
            },
            {
                "Grid Step": 0.00075,
                "Profit Target": 0.3,
                "Strategy": "GatedLocalReferenceSizing",
                "per_lot_pct": 0.0002,
                "lookback_days": 0.02,
                "bars_per_day": 387,
                "breakdown_gate": "dual_thrust",
                "breakdown_release": "session",
                "dt_lookback_days": 3,
                "dt_k": 0.7,
                "Total Return %": 12.0,
            },
        ]
    )
    buffer = io.StringIO()
    rows.to_csv(buffer, index=False)
    buffer.seek(0)
    return pd.read_csv(buffer)


def test_each_row_resolves_to_its_own_class():
    hf_row, gated_row = (row for _, row in _merged_csv_rows().iterrows())
    assert _strategy_class_for(hf_row) is HighFrequencyLocalReferenceSizing
    assert _strategy_class_for(gated_row) is GatedLocalReferenceSizing


def test_gate_parameters_survive_the_csv_round_trip():
    _, gated_row = (row for _, row in _merged_csv_rows().iterrows())
    assert isinstance(gated_row["dt_lookback_days"], float)  # the trap itself
    params = _constructor_params(GatedLocalReferenceSizing, gated_row)
    strategy = GatedLocalReferenceSizing(**params)
    assert strategy.breakdown.mode == "dual_thrust"
    assert strategy.breakdown.release == "session"
    assert strategy.breakdown.dt_lookback_days == 3
    assert strategy.breakdown.dt_k == pytest.approx(0.7)


def test_a_row_without_a_strategy_column_is_treated_as_hf():
    """Sweeps from before the column existed were all HF."""
    row = pd.Series({"Grid Step": 0.001, "per_lot_pct": 0.001})
    assert _strategy_class_for(row) is HighFrequencyLocalReferenceSizing


def test_an_unregistered_class_name_stops_rather_than_guessing():
    row = pd.Series({"Strategy": "SomethingDeleted"})
    with pytest.raises(SystemExit):
        _strategy_class_for(row)
