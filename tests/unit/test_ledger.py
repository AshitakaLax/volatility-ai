import pytest

from src.ledger import AssetLotLedger, Lot


def test_register_buy_creates_open_lot_with_computed_target():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=50.0, shares=10.0, profit_target=0.005)

    assert lot in ledger.open_lots
    assert ledger.closed_lots == []
    assert lot.target_sell_price == pytest.approx(50.25)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(shares=0),
        dict(shares=-5),
        dict(buy_price=0),
        dict(buy_price=-1),
        dict(profit_target=0),
        dict(profit_target=-0.01),
    ],
)
def test_register_buy_rejects_invalid_input(kwargs):
    ledger = AssetLotLedger()
    base = dict(order_id="ord-1", symbol="TQQQ", buy_price=50.0, shares=10.0, profit_target=0.005)
    base.update(kwargs)
    with pytest.raises(ValueError):
        ledger.register_buy(**base)


def test_get_marketable_lots_boundary_exactly_at_target_is_marketable():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=100.0, shares=1.0, profit_target=0.01)
    # target_sell_price is exactly 101.0
    assert ledger.get_marketable_lots(100.99) == []
    assert ledger.get_marketable_lots(101.00) == [lot]
    assert ledger.get_marketable_lots(101.01) == [lot]


def test_get_marketable_lots_only_returns_open_lots_meeting_target():
    ledger = AssetLotLedger()
    cheap = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    ledger.register_buy("ord-2", "TQQQ", buy_price=60.0, shares=1.0, profit_target=0.01)

    marketable = ledger.get_marketable_lots(current_price=41.0)
    assert marketable == [cheap]


def test_get_marketable_lots_does_not_mutate_state():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    ledger.get_marketable_lots(current_price=100.0)
    assert lot in ledger.open_lots
    assert lot not in ledger.closed_lots


def test_close_lot_moves_lot_from_open_to_closed():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    ledger.close_lot(lot)
    assert lot not in ledger.open_lots
    assert lot in ledger.closed_lots


def test_close_lot_twice_raises():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    ledger.close_lot(lot)
    with pytest.raises(ValueError):
        ledger.close_lot(lot)


def test_close_lot_unknown_lot_raises():
    ledger = AssetLotLedger()
    stray = Lot(order_id="ghost", symbol="TQQQ", buy_price=1.0, shares=1.0, profit_target=0.01)
    with pytest.raises(ValueError):
        ledger.close_lot(stray)


def test_close_lot_with_no_sell_qty_and_completed_false_is_rejected():
    # Task 7.2 replaced the old NotImplementedError: partial closes are
    # implemented now, but completed=False with NO sell_qty is
    # genuinely ambiguous (how much was filled?) and is rejected.
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    with pytest.raises(ValueError, match="ambiguous"):
        ledger.close_lot(lot, completed=False)
    assert lot in ledger.open_lots


def test_partial_close_leaves_lot_open_with_reduced_shares():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=10.0, profit_target=0.01)
    ledger.close_lot(lot, sell_qty=4.0, execution_price=41.0)
    assert lot in ledger.open_lots
    assert lot.shares == pytest.approx(6.0)
    assert lot not in ledger.closed_lots


def test_partial_close_never_mutates_cost_basis_or_target():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=10.0, profit_target=0.01)
    original_buy_price = lot.buy_price
    original_target = lot.target_sell_price
    ledger.close_lot(lot, sell_qty=4.0, execution_price=99.0)
    assert lot.buy_price == original_buy_price
    assert lot.target_sell_price == original_target


def test_successive_partial_closes_exhausting_the_lot_close_it():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=10.0, profit_target=0.01)
    ledger.close_lot(lot, sell_qty=4.0)
    ledger.close_lot(lot, sell_qty=3.0)
    assert lot in ledger.open_lots
    ledger.close_lot(lot, sell_qty=3.0)  # exhausts it
    assert lot not in ledger.open_lots
    assert lot in ledger.closed_lots
    assert lot.shares == 0.0


def test_partial_close_within_epsilon_closes_the_lot():
    # Floating-point drift must not leave a phantom sliver open.
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=10.0, profit_target=0.01)
    ledger.close_lot(lot, sell_qty=10.0 - 1e-12)
    assert lot not in ledger.open_lots
    assert lot.shares == 0.0


def test_partial_close_rejects_oversell():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=10.0, profit_target=0.01)
    with pytest.raises(ValueError, match="exceeds"):
        ledger.close_lot(lot, sell_qty=11.0)
    assert lot.shares == pytest.approx(10.0)  # unchanged


def test_partial_close_rejects_non_positive_sell_qty():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=10.0, profit_target=0.01)
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError):
            ledger.close_lot(lot, sell_qty=bad)
    assert lot.shares == pytest.approx(10.0)


# --- the incremental share total (a performance invariant) ---


def _recomputed(ledger) -> float:
    return sum(lot.shares for lot in ledger.open_lots)


def test_the_running_share_total_matches_a_recomputed_sum():
    """THE invariant the optimisation rests on. total_open_shares
    replaces a per-bar walk of the whole book, so if it ever disagrees
    with the truth the backtest silently marks to market at the wrong
    value -- and nothing else would notice."""
    ledger = AssetLotLedger()
    for i in range(20):
        ledger.register_buy(f"L{i}", "TQQQ", 100.0 + i, 1.5 + i * 0.1, 0.05)
    assert ledger.total_open_shares == pytest.approx(_recomputed(ledger))

    # A partial, a full close, and another partial on the same lot.
    ledger.close_lot(ledger.open_lots[3], sell_qty=0.5, completed=False)
    assert ledger.total_open_shares == pytest.approx(_recomputed(ledger))

    ledger.close_lot(ledger.open_lots[0], completed=True)
    assert ledger.total_open_shares == pytest.approx(_recomputed(ledger))

    ledger.close_lot(ledger.open_lots[5], sell_qty=0.25, completed=False)
    assert ledger.total_open_shares == pytest.approx(_recomputed(ledger))


def test_a_closing_partial_removes_the_whole_remainder_not_just_sell_qty():
    """The subtle case. close_lot snaps a sub-epsilon remainder to zero
    before removing the lot, so a closing partial takes slightly MORE out
    of the book than was sold. Subtracting sell_qty would leave a
    permanent phantom holding."""
    ledger = AssetLotLedger()
    lot = ledger.register_buy("L1", "TQQQ", 100.0, 2.0, 0.05)
    ledger.close_lot(lot, sell_qty=2.0 - 1e-12, completed=False)

    assert lot not in ledger.open_lots, "fixture must actually trigger the snap"
    assert ledger.total_open_shares == pytest.approx(_recomputed(ledger))
    assert ledger.total_open_shares == 0.0


def test_an_empty_book_reads_exactly_zero_not_a_float_residue():
    """Incremental arithmetic does not cancel exactly. Over a 10-year run
    with tens of thousands of round trips that residue would compound, so
    a flat book -- the one moment the answer is known exactly -- resyncs."""
    ledger = AssetLotLedger()
    for i in range(50):
        lot = ledger.register_buy(f"L{i}", "TQQQ", 100.0, 0.1 + i * 0.017, 0.05)
        ledger.close_lot(lot, completed=True)

    assert ledger.open_lots == []
    assert ledger.total_open_shares == 0.0, "a flat book must be exactly zero"


def test_a_fresh_ledger_starts_at_zero():
    assert AssetLotLedger().total_open_shares == 0.0


def test_resync_recovers_a_ledger_populated_directly():
    """src/persistence.py rebuilds a ledger by appending to open_lots,
    bypassing register_buy. Without the explicit resync it calls, a
    restored book would mark to market as zero."""
    ledger = AssetLotLedger()
    ledger.open_lots.append(
        Lot(order_id="R1", symbol="TQQQ", buy_price=100.0, shares=3.0, profit_target=0.05)
    )
    assert ledger.total_open_shares == 0.0, "the direct append is invisible, as expected"

    assert ledger.resync_total_open_shares() == pytest.approx(3.0)
    assert ledger.total_open_shares == pytest.approx(_recomputed(ledger))


def test_the_total_survives_a_long_random_sequence():
    """Property test over interleaved buys and partial/full closes -- the
    shape a real run produces, which no hand-written case covers."""
    import random

    rng = random.Random(7)
    ledger = AssetLotLedger()
    for step in range(400):
        if not ledger.open_lots or rng.random() < 0.5:
            ledger.register_buy(f"L{step}", "TQQQ", 100.0, rng.uniform(0.1, 5.0), 0.05)
        else:
            lot = rng.choice(ledger.open_lots)
            if rng.random() < 0.5:
                ledger.close_lot(lot, completed=True)
            else:
                ledger.close_lot(
                    lot, sell_qty=min(lot.shares, rng.uniform(0.05, 2.0)), completed=False
                )
        assert ledger.total_open_shares == pytest.approx(_recomputed(ledger), abs=1e-9), (
            f"drifted at step {step}"
        )
