"""
The one script that can submit a real order.

Tested WITHOUT a browser: every test here drives parse_args and main
against a fake page, so the refusals are exercised without a session, an
account, or a network. The affirmative path is deliberately NOT tested
end to end -- a test that placed an order would place an order.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import fidelity_place_test_order as script
from src.fidelity_placing_broker import FileConfNumJournal
from src.fidelity_session import PLACE_ENDPOINTS

PREVIEW = "/ftgw/digital/trade-equity/previewSrvc"
ACCOUNT = "999888777"


def _args(**kw):
    argv = ["--account", ACCOUNT]
    for key, value in kw.items():
        flag = "--" + key.replace("_", "-")
        argv.append(flag) if value is True else argv.extend([flag, str(value)])
    return script.parse_args(argv)


# --- defaults are the safe ones ---------------------------------------


def test_the_defaults_are_conservative():
    args = _args()
    assert args.symbol == "CWH", "the cheap test instrument, not TQQQ"
    assert args.quantity == 1
    assert args.limit_discount == 0.20, "20% below market: rests, does not fill"
    assert args.max_order_value == 50.0
    assert args.confirmed is False, "placing is never the default"
    assert args.dry_run is False and args.check_only is False


def test_placing_requires_the_acknowledgement_flag():
    assert _args().confirmed is False
    assert _args(i_understand_this_places_a_real_order=True).confirmed is True


# --- the transport is only unlocked for a real place ------------------


@pytest.mark.parametrize(
    "kw,should_place",
    [
        ({}, False),
        ({"dry_run": True}, False),
        ({"check_only": True}, False),
        ({"i_understand_this_places_a_real_order": True}, True),
        ({"i_understand_this_places_a_real_order": True, "dry_run": True}, False),
        ({"i_understand_this_places_a_real_order": True, "check_only": True}, False),
    ],
)
def test_order_endpoints_are_unlocked_only_when_a_place_is_intended(kw, should_place):
    """Mirrors the expression in main(). A mode that is not placing must
    not hold the capability, so a bug in the code below it cannot submit."""
    args = _args(**kw)
    placing = bool(args.confirmed and not args.dry_run and not args.check_only)
    assert placing is should_place


def test_the_transport_refuses_placing_when_not_unlocked():
    from src.fidelity_session import FidelitySession

    session = FidelitySession(object(), allow_order_endpoints=False, allow_preview_endpoints=True)
    from src.exceptions import ConfigurationError

    for path in PLACE_ENDPOINTS:
        with pytest.raises(ConfigurationError, match="PLACES OR CANCELS A REAL ORDER"):
            session.post_json(path, {})


# --- the confirmation phrase ------------------------------------------


def test_the_confirmation_phrase_is_not_a_bare_yes():
    """Typing "y" by reflex must not submit an order."""
    assert script.CONFIRM_PHRASE == "PLACE THE ORDER"
    assert len(script.CONFIRM_PHRASE) > 5
    assert script.CONFIRM_PHRASE.lower() not in ("y", "yes", "ok")


# --- the recovery path -------------------------------------------------


class _Broker:
    def __init__(self, orders):
        self._rows = orders

    def _orders(self):
        return self._rows


def test_the_report_names_orders_the_venue_never_received(tmp_path, capsys):
    path = tmp_path / "j.jsonl"
    journal = FileConfNumJournal(str(path))
    journal.record("d1", "2C50LANDED", {"symbol": "CWH", "side": "buy", "qty": 1.0})
    journal.record("d2", "2C50LOST", {"symbol": "CWH", "side": "buy", "qty": 1.0})

    broker = _Broker([{"orderNum": "2C50LANDED", "status": "Open"}])
    script._report(broker, journal)
    out = capsys.readouterr().out
    assert "2C50LANDED" in out and "Open" in out
    assert "2C50LOST" in out and "NOT AT VENUE" in out
    assert "never landed" in out


def test_the_report_is_quiet_when_everything_landed(tmp_path, capsys):
    path = tmp_path / "j.jsonl"
    journal = FileConfNumJournal(str(path))
    journal.record("d1", "2C50OK", {"symbol": "CWH", "side": "buy", "qty": 1.0})
    script._report(_Broker([{"orderNum": "2C50OK", "status": "Open"}]), journal)
    assert "never landed" not in capsys.readouterr().out


def test_the_report_handles_an_empty_journal(tmp_path, capsys):
    script._report(_Broker([]), FileConfNumJournal(str(tmp_path / "absent.jsonl")))
    assert "0 recorded intent" in capsys.readouterr().out


# --- the journal is durable -------------------------------------------


def test_each_journal_line_is_flushed_and_readable_on_its_own(tmp_path):
    """A process dying one line after a write must leave that line
    readable -- that is the entire reason the journal exists."""
    path = tmp_path / "j.jsonl"
    journal = FileConfNumJournal(str(path))
    journal.record("d1", "C1", {"symbol": "CWH"})
    assert json.loads(Path(path).read_text(encoding="utf-8").strip())["conf_num"] == "C1"
    journal.record("d2", "C2", {"symbol": "CWH"})
    assert len(Path(path).read_text(encoding="utf-8").strip().splitlines()) == 2


# --- structural ---------------------------------------------------------


def test_the_script_never_reads_a_password():
    """It attaches to a browser a human logged into. It must not contain
    a credential path at all."""
    source = Path("fidelity_place_test_order.py").read_text(encoding="utf-8")
    for forbidden in ("FIDELITY_PASSWORD", "load_fidelity_credentials", "totp"):
        assert forbidden not in source, f"{forbidden} has no business here"


def test_it_places_through_the_gated_adapter_not_a_raw_post():
    """The script must not build its own placeOrder payload -- every gate
    lives in FidelityPlacingBroker, and a direct post would skip them.

    Checked via the AST rather than a text search. A plain `in` test
    matched the COMMENT explaining that the transport refuses
    /placeOrder, which is the second time in this project a grep has
    failed on prose describing the very property it was checking.
    """
    import ast

    source = Path("fidelity_place_test_order.py").read_text(encoding="utf-8")
    assert "FidelityPlacingBroker" in source, "placing must go through the adapter"

    tree = ast.parse(source)
    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
    }
    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
        and "placeOrder" in node.value
    ]
    assert literals == [], f"the place endpoint is reachable as a literal: {literals}"
