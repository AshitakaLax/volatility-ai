"""
Task 4.10 acceptance tests.

1. Applying the same fill event twice changes cash/position/lot state
   exactly once.
2. Replaying an already-processed event after "restart" remains a
   no-op -- demonstrated via ProcessedEventStore's injectable backend
   standing in for Task 7.3's not-yet-built persistence layer.
3. Event IDs are included in audit logs.
4. The identifier scheme is documented (module docstring check).
"""

import pandas as pd

from optimization_controller import OptimizationController
from src.idempotency import ProcessedEventStore
from src.size_calculators import FixedPortfolioPercentage


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_apply_once_runs_side_effect_exactly_once_for_a_repeated_id():
    store = ProcessedEventStore()
    calls = []

    def side_effect():
        calls.append(1)
        return "result"

    first = store.apply_once("evt-1", side_effect)
    second = store.apply_once("evt-1", side_effect)  # same ID again

    assert len(calls) == 1, (
        "side_effect must run exactly once despite two apply_once calls with the same ID"
    )
    assert first == second == "result"


def test_different_ids_each_apply_independently():
    store = ProcessedEventStore()
    calls = []
    store.apply_once("evt-1", lambda: calls.append(1))
    store.apply_once("evt-2", lambda: calls.append(2))
    assert calls == [1, 2]


def test_has_processed_reflects_state():
    store = ProcessedEventStore()
    assert not store.has_processed("evt-1")
    store.apply_once("evt-1", lambda: None)
    assert store.has_processed("evt-1")


def test_replaying_an_already_processed_id_after_simulated_restart_is_a_noop():
    # A plain set stands in for Task 7.3's not-yet-built persistent
    # store -- what matters here is that the *backend* (not the
    # ProcessedEventStore instance) is what survives "restart".
    persisted_backend = set()

    store_before_restart = ProcessedEventStore(backend=persisted_backend)
    calls = []
    store_before_restart.apply_once("evt-1", lambda: calls.append("first"))
    assert calls == ["first"]

    # "Restart": a brand new ProcessedEventStore instance, but backed
    # by the same (persisted) backend set. Only the ID set survives
    # the simulated restart, not the local result cache -- per
    # apply_once's own documented contract, this must degrade to None
    # rather than raising.
    store_after_restart = ProcessedEventStore(backend=persisted_backend)
    replay_result = store_after_restart.apply_once(
        "evt-1", lambda: calls.append("should not happen")
    )

    assert calls == ["first"], "Replaying evt-1 after restart must remain a no-op"
    assert replay_result is None


def test_event_ids_appear_in_logs(caplog):
    store = ProcessedEventStore()
    with caplog.at_level("INFO", logger="Optimizer"):
        store.apply_once("evt-audit-123", lambda: None)
        store.apply_once("evt-audit-123", lambda: None)  # duplicate
    messages = [r.message for r in caplog.records]
    assert any("evt-audit-123" in m for m in messages)
    assert any("Duplicate" in m and "evt-audit-123" in m for m in messages)


def test_simulate_single_applies_a_collided_fill_id_exactly_once(monkeypatch):
    # Force two buy fills to report the SAME order id -- the only way
    # to make a duplicate-delivery scenario actually happen in this
    # codebase's single-pass simulation loop, which has no natural
    # retry/redelivery path of its own.
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)

    from src.order_management_system import OrderManagementSystem as RealOMS

    class _FixedIdOMS:
        def __init__(self, mode="SIMULATION"):
            self._real = RealOMS(mode=mode)

        def execute_buy(self, symbol, trade_value, price):
            result = self._real.execute_buy(symbol, trade_value, price)
            result["id"] = "COLLIDED-ID"  # every buy reports the same id
            return result

        def execute_sell(self, symbol, qty, price):
            return self._real.execute_sell(symbol, qty, price)

    import optimization_controller as oc_module

    monkeypatch.setattr(oc_module, "OrderManagementSystem", _FixedIdOMS)

    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    ).iloc[0]

    # The fixture normally opens 4 lots (Task 0.1's baseline). With
    # every buy's id collided to the same value, only the FIRST buy's
    # side effects apply -- ledger.register_buy only ever runs once,
    # so exactly one lot registers even though 4 buy attempts fire.
    assert result["Trade Count"] == 1


def test_module_documents_the_shared_id_scheme_for_future_tasks():
    import src.idempotency as idempotency_module

    doc = idempotency_module.__doc__
    assert "7.4" in doc
    assert "7.14" in doc
    assert "SIMULATION" in doc and "LIVE" in doc
