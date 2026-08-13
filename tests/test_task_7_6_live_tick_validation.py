from datetime import datetime, timezone

from src.live_execution import LiveExecutionLoop


def test_live_tick_validation_rejects_zero_and_spike_and_keeps_last_good_price():
    loop = object.__new__(LiveExecutionLoop)
    loop._last_known_good_price = None
    loop.rejected_tick_count = 0

    assert loop.validate_tick(100.0) is True
    assert loop._last_known_good_price == 100.0

    assert loop.validate_tick(0.0) is False
    assert loop._last_known_good_price == 100.0

    assert loop.validate_tick(130.0) is False
    assert loop._last_known_good_price == 100.0

    assert loop.validate_tick(101.0) is True
    assert loop._last_known_good_price == 101.0
    assert loop.rejected_tick_count == 2


def test_live_tick_validation_allows_boundary_move():
    loop = object.__new__(LiveExecutionLoop)
    loop._last_known_good_price = 100.0
    loop.rejected_tick_count = 0

    assert loop.validate_tick(115.0) is True
    assert loop._last_known_good_price == 115.0
    assert loop.rejected_tick_count == 0
