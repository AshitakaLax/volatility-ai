from src.audit import canonical_event_id, canonical_order_intent_id


def test_order_intent_id_uses_shared_canonical_scheme():
    kwargs = {
        "deployment_id": "deploy-1",
        "strategy_id": "strategy-1",
        "symbol": "TQQQ",
        "market_event_id": "bar-42",
        "sequence_number": 7,
    }

    assert canonical_order_intent_id(**kwargs) == canonical_event_id(
        **kwargs,
        decision_type="ORDER_INTENT",
    )


def test_order_intent_id_is_deterministic_and_sequence_sensitive():
    kwargs = {
        "deployment_id": "deploy-1",
        "strategy_id": "strategy-1",
        "symbol": "TQQQ",
        "market_event_id": "bar-42",
    }

    first = canonical_order_intent_id(**kwargs, sequence_number=7)
    repeat = canonical_order_intent_id(**kwargs, sequence_number=7)
    different_sequence = canonical_order_intent_id(**kwargs, sequence_number=8)

    assert first == repeat
    assert first != different_sequence
    assert len(first) == 64
    assert first == first.lower()
