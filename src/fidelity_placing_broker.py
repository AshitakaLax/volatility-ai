"""
The adapter that CAN place a real Fidelity order. Read this before using it.

This is the only module in the project that moves real money at a real
venue. Everything else is a simulation, a preview, or a read.

--------------------------------------------------------------------
WHY IT IS A SEPARATE MODULE AND NOT A FLAG

`src/fidelity_broker.py` is preview-only, and three tests assert that:
no string constant names a place endpoint, no endpoint constant resolves
to one, and the transport refuses those paths at its preview-only
setting. Adding a `can_place=True` switch there would have falsified all
three, and the file would no longer be safe to reason about at a glance.

So placing lives here, subclassing the preview adapter. That keeps the
shared ticket-building in one place while leaving the statement "the
preview adapter cannot place an order" literally true rather than
conditionally true.

--------------------------------------------------------------------
THE FIVE CONDITIONS, ALL REQUIRED

None of these defaults to permissive, and none is inferred:

  1. confirm_live_orders=True   -- typed by a human at a call site.
  2. A session with allow_order_endpoints=True. The TRANSPORT must
     permit /placeOrder; this class cannot grant itself that.
  3. allowed_symbols            -- exact match, empty means nothing.
  4. max_order_value            -- a hard dollar ceiling per order.
  5. journal                    -- durable storage for the confNum,
     written BEFORE the order is committed.

Condition 5 is the one that looks like bookkeeping and is not. See below.

--------------------------------------------------------------------
THE AMBIGUITY WINDOW, AND WHY THE JOURNAL IS LOAD-BEARING

Reconnaissance established the property this design rests on:
`previewSrvc` MINTS the confNum, and `placeOrder` takes that same
confNum as an INPUT. So the order's identifier exists before anything is
committed -- which is strictly better than the Alpaca flow this codebase
was built around, where the id only comes back with the response.

That property only helps if the confNum survives the process. If
`placeOrder` times out and the confNum was only ever in memory, the
outcome is genuinely unknowable and the order may be live. Journalling
it first converts every timeout into a lookup: query
`transactions/pending` for that confNum and the venue answers
definitively.

So a place with no journal is refused. Not because journalling is tidy,
but because without it this adapter would be no safer than the DOM
scraping it replaced.

--------------------------------------------------------------------
WHAT HAPPENS WHEN placeOrder FAILS

Never a retry. `AmbiguousSubmissionError` is raised carrying the
confNum, and that type exists precisely so a caller cannot handle it in
the same `except` branch as an ordinary failure -- an ambiguous
submission goes to reconciliation, never back through submission.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from src.exceptions import ConfigurationError
from src.fidelity_broker import FidelityBroker, FidelityOrder, _find_first
from src.fidelity_session import PLACE_ENDPOINTS
from src.order_lifecycle import OrderState
from src.retry_policy import AmbiguousSubmissionError

logger = logging.getLogger("Optimizer")

PLACE_PATH = "/ftgw/digital/trade-equity/placeOrder"
assert PLACE_PATH in PLACE_ENDPOINTS, "the transport must know this is a place endpoint"

# Cancelling is a two-step round-trip of the same shape as placing --
# preview the cancellation, then commit it -- and both steps take the
# identical envelope. Transcribed from captured requests, not designed.
CANCEL_PREVIEW_PATH = "/ftgw/digital/trade-equity/cancelPreviewOrder"
CANCEL_PLACE_PATH = "/ftgw/digital/trade-equity/cancelPlaceOrder"
assert CANCEL_PLACE_PATH in PLACE_ENDPOINTS, "cancelling must sit behind the order gate"


class ConfNumJournal(Protocol):
    """Durable record of a confNum, written before the order is committed."""

    def record(self, decision_id: str, conf_num: str, detail: dict) -> None:
        """Persist the mapping. MUST be durable before returning."""
        ...


class FidelityPlacingBroker(FidelityBroker):
    """Places real orders at Fidelity. Every gate is explicit."""

    def __init__(
        self,
        session: Any,
        account: str,
        allowed_accounts: tuple[str, ...] | list[str],
        *,
        confirm_live_orders: bool = False,
        allowed_symbols: tuple[str, ...] | list[str] = (),
        max_order_value: float = 0.0,
        journal: ConfNumJournal | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(session, account, allowed_accounts, **kwargs)

        if not confirm_live_orders:
            raise ConfigurationError(
                "FidelityPlacingBroker PLACES REAL ORDERS WITH REAL MONEY. Construct "
                "it with confirm_live_orders=True to say so deliberately, at a call "
                "site a human can see. If you did not mean to place orders, use "
                "src.fidelity_broker.FidelityBroker, which cannot."
            )
        if not allowed_symbols:
            raise ConfigurationError(
                "allowed_symbols is empty. An empty allowlist means nothing is "
                "permitted, never everything -- name the exact tickers this "
                "deployment may trade."
            )
        if max_order_value <= 0:
            raise ConfigurationError(
                "max_order_value must be a positive dollar ceiling. It is the last "
                "thing standing between a sizing bug and an order the account "
                "cannot afford."
            )
        if journal is None:
            raise ConfigurationError(
                "A ConfNumJournal is required. previewSrvc mints the confNum before "
                "anything is committed, which is what makes a placeOrder timeout "
                "RECOVERABLE rather than ambiguous -- but only if the confNum "
                "survives the process. Without a journal this adapter would be no "
                "safer than the DOM scraping it replaces."
            )

        self._allowed_symbols = tuple(str(sym).upper() for sym in allowed_symbols)
        self._max_order_value = float(max_order_value)
        self._journal = journal
        logger.warning(
            "LIVE ORDER PLACEMENT ENABLED for account ...%s, symbols %s, ceiling $%.2f per order.",
            str(account)[-4:],
            ",".join(self._allowed_symbols),
            self._max_order_value,
        )

    # -- gates ----------------------------------------------------------

    def _check_symbol(self, symbol: str) -> str:
        """Exact match against the configured symbol allowlist.

        Re-checked per order rather than trusted from construction, for
        the same reason the account is: an authorization consulted once
        is one refactor away from being decorative.
        """
        upper = str(symbol).upper()
        if upper not in self._allowed_symbols:
            raise ConfigurationError(
                f"{symbol!r} is not in allowed_symbols {self._allowed_symbols}. "
                "Refusing to place an order in an instrument this deployment was "
                "not configured to trade."
            )
        return upper

    def _check_value(self, side: str, qty: float, limit_price: float) -> None:
        """Cap what an order can SPEND. Buys only, deliberately.

        A ceiling applied to sells blocks EXITS, and being unable to
        leave a position you already hold is strictly worse than being
        unable to enter one. The first version checked both, so a book
        built one $20 share at a time could not be sold in one order
        under a $50 ceiling -- the ceiling would have trapped capital it
        was meant to protect.

        Selling reduces exposure and needs no ceiling for that reason.
        """
        if side != "buy":
            return
        value = float(qty) * float(limit_price)
        if value > self._max_order_value:
            raise ConfigurationError(
                f"{qty} x ${limit_price:.2f} = ${value:.2f} exceeds the "
                f"max_order_value ceiling of ${self._max_order_value:.2f}. "
                "Refusing rather than trimming the order: a size this code did not "
                "expect is a bug to surface, not a number to quietly adjust."
            )

    # -- placing --------------------------------------------------------

    def place(
        self,
        symbol: str,
        side: str,
        qty: float,
        limit_price: float,
        decision_id: str,
    ) -> FidelityOrder:
        """Preview, journal the confNum, then commit. A REAL order.

        The sequence is not negotiable and is the whole design:
        preview mints the id -> the id is made durable -> only then is
        anything committed. Reordering these would reopen the window
        reconnaissance closed.
        """
        if side not in ("buy", "sell"):
            raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")
        if limit_price <= 0:
            raise ValueError(f"limit_price must be positive, got {limit_price}")
        symbol = self._check_symbol(symbol)
        self._check_value(side, qty, limit_price)

        # 1. PREVIEW. Commits nothing, and mints the identifier.
        previewed = self._preview(symbol, side, qty, limit_price, decision_id)
        conf = previewed.id
        ticket = self.build_ticket(symbol, side, qty, limit_price)

        # 2. JOURNAL, before anything is committed.
        self._journal.record(
            decision_id,
            conf,
            {
                "symbol": symbol,
                "side": side,
                "qty": float(qty),
                "limit_price": float(limit_price),
                "account": self._account,
            },
        )

        # 3. COMMIT. Same ticket, plus the confNum the preview minted.
        logger.warning(
            "PLACING A REAL ORDER: %s %s %s limit %.2f (confNum %s, decision %s)",
            side,
            qty,
            symbol,
            limit_price,
            conf,
            decision_id,
        )
        try:
            response = self._session.post_json(
                PLACE_PATH, {"orderDetails": dict(ticket, confNum=conf)}
            )
        except ConfigurationError:
            # NOT ambiguous. The transport's endpoint gate fires BEFORE
            # any network call, so nothing was sent and no order can be
            # live. Reporting this as an ambiguous submission would send
            # an operator into a recovery hunt for an order that never
            # existed -- and would teach them to distrust the warning
            # that does matter. Re-raised unchanged.
            #
            # Everything else stays ambiguous on purpose, including
            # FidelitySessionExpired: post_json can raise that either
            # side of the fetch, so it is genuinely unknowable.
            raise
        except Exception as exc:
            # NEVER a retry. The order may be live; the confNum is
            # journalled, so reconciliation can settle it definitively.
            raise AmbiguousSubmissionError(
                f"placeOrder did not return cleanly for confNum {conf} "
                f"(decision {decision_id}). The order MAY BE LIVE. Do not "
                f"resubmit -- query transactions/pending for {conf}."
            ) from exc

        echoed = _find_first(response, "confNum")
        if str(echoed) != conf:
            raise AmbiguousSubmissionError(
                f"placeOrder echoed confNum {echoed!r} but the preview minted "
                f"{conf!r}. Refusing to assume which order is live -- reconcile "
                "both before placing anything further."
            )
        self._assert_echoed_account(response, self._account)

        logger.warning("ORDER PLACED: confNum %s (decision %s)", conf, decision_id)
        return FidelityOrder(
            id=conf,
            client_order_id=decision_id,
            symbol=symbol,
            state=OrderState.SUBMITTED,
            qty=float(qty),
            raw={"placed": True},
        )

    def cancel(self, conf_num: str) -> dict:
        """Cancel a working order by confNum. Two steps, like placing.

        NO SYMBOL OR VALUE GATE, deliberately, and the asymmetry is the
        point. The allowlists exist to stop this deployment ENTERING
        positions it was not configured for; a cancellation only ever
        reduces exposure. Refusing to cancel an order because its symbol
        drifted out of a config file would strand a live order in the
        market to satisfy a check that was never about that -- the same
        reasoning that keeps max_order_value on buys only.

        The account IS re-checked: cancelling is still an instruction
        aimed at one account, and aiming it at the wrong one is exactly
        what the allowlist is for.

        Not idempotent, because the venue's answer to "cancel an order
        that is already gone" is information rather than an error to
        swallow. Callers get the response and decide.
        """
        conf_num = str(conf_num).strip()
        if not conf_num:
            raise ValueError("conf_num is required to cancel an order")
        account = self._check_account(self._account)
        envelope = {"cancelOrderDetails": {"acctNum": account, "confNum": conf_num}}

        logger.warning("CANCELLING order %s on account ...%s", conf_num, account[-4:])
        # Step 1 discards nothing if it fails -- a cancel preview is as
        # inert as an order preview, so this half needs no recovery path.
        self._session.post_json(CANCEL_PREVIEW_PATH, envelope)
        try:
            response = self._session.post_json(CANCEL_PLACE_PATH, envelope)
        except ConfigurationError:
            raise
        except Exception as exc:
            # Ambiguous in the same way a place is, and MORE tolerable:
            # the unknown outcome of a failed cancel is that the order is
            # still working, which is the state it was already in.
            raise AmbiguousSubmissionError(
                f"cancelPlaceOrder did not return cleanly for {conf_num}. The order "
                f"may still be WORKING. Do not assume it is gone -- query "
                f"transactions/pending for {conf_num}."
            ) from exc
        self._assert_echoed_account(response, account)
        logger.warning("CANCEL ACCEPTED for order %s", conf_num)
        return response if isinstance(response, dict) else {"response": response}

    # -- the LiveBroker surface, now actually submitting ----------------

    def submit_buy(
        self, symbol: str, trade_value: float, client_order_id: str | None = None
    ) -> FidelityOrder:
        if trade_value <= 0:
            raise ValueError(f"trade_value must be positive, got {trade_value}")
        if not client_order_id:
            raise ValueError(
                "client_order_id is required when placing a real order: it is the "
                "decision_id the journal and reconciliation key on."
            )
        price = self.get_quote(symbol)
        qty = int(trade_value // price)
        if qty < 1:
            raise ValueError(
                f"${trade_value:.2f} does not buy one whole share of {symbol} at ${price:.2f}."
            )
        return self.place(symbol, "buy", qty, price, client_order_id)

    def submit_sell(
        self,
        symbol: str,
        qty: float,
        target_price: float,
        client_order_id: str | None = None,
    ) -> FidelityOrder:
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")
        if not client_order_id:
            raise ValueError(
                "client_order_id is required when placing a real order: it is the "
                "decision_id the journal and reconciliation key on."
            )
        return self.place(symbol, "sell", qty, target_price, client_order_id)


class FileConfNumJournal:
    """Append-only JSON-lines journal, flushed and fsynced before returning.

    Deliberately dull. The thing it must do is survive a process dying
    one line after the write, so it opens, writes, flushes, fsyncs and
    closes on every record rather than holding a handle -- the ordinary
    reasons to keep a file open do not apply to a few records a day, and
    a buffered handle is exactly how a journal loses its last entry.
    """

    def __init__(self, path: str) -> None:
        self._path = path

    def record(self, decision_id: str, conf_num: str, detail: dict) -> None:
        import json
        import os
        import time

        line = json.dumps(
            {"ts": time.time(), "decision_id": decision_id, "conf_num": conf_num, **detail},
            sort_keys=True,
        )
        with open(self._path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def read_all(self) -> list[dict]:
        """Every journalled order, for recovery after an ambiguous submit."""
        import json
        import os

        if not os.path.exists(self._path):
            return []
        with open(self._path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]


def unresolved_orders(journal: FileConfNumJournal, broker: FidelityBroker) -> list[dict]:
    """Journalled orders the venue does not report. THE RECOVERY PATH.

    After an AmbiguousSubmissionError this is the question that matters:
    of the orders we recorded an intent to place, which does the venue
    not know about? Those never landed. Everything else did, whatever the
    submission call appeared to do.

    Returns the journal entries with no matching order at the venue, so
    an operator sees intents rather than a bare count.
    """
    live = {str(order.get("orderNum")) for order in broker._orders()}
    return [entry for entry in journal.read_all() if entry["conf_num"] not in live]
