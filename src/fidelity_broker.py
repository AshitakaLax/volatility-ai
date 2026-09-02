"""
Fidelity broker adapter -- PREVIEW ONLY. This module cannot place an order.

Step 4 of the Fidelity plan. Satisfies the same de facto interface
src/alpaca_broker.py does (submit_buy, submit_sell,
get_order_by_client_id, snapshot, ping) so src/live_trading_loop.py and
src/reconciliation.py work against either venue without edits.

--------------------------------------------------------------------
WHY THIS IS BUILT ON THE JSON API AND NOT ON fidelity-api

The plan's Part 3.C assumed the `fidelity-api` library driving the DOM.
That assumption is dead: Fidelity refuses a Playwright-LAUNCHED browser
outright (Akamai Bot Manager, visible in a capture as sensor POSTs), so
the library's own entry point cannot reach the site. What does work is
attaching to the user's OWN already-authenticated browser over CDP and
issuing the same JSON calls the page issues -- src/fidelity_session.py.

That turned out to be strictly better anyway. Reconnaissance showed the
JSON layer carries everything the DOM does and more:

  previewSrvc                      -> mints confNum, commits nothing
  placeOrder                       -> takes that confNum as INPUT
  activityapi/.../transactions/pending -> real order enumeration
  traderplus-api/api/positions/v1  -> positions
  trade-equity/balance             -> cash

So Fidelity qualifies for FULL order-level reconciliation, not the
positions-only fallback the plan hedged for.

--------------------------------------------------------------------
HOW "CANNOT PLACE AN ORDER" IS ENFORCED

Not by this class remembering not to call placeOrder. By the transport:
a preview-only session is constructed with allow_preview_endpoints=True
and allow_order_endpoints left False, and
src/fidelity_session.post_json REFUSES /placeOrder and /cancelPlaceOrder
outright at that setting. Even a bug in this file cannot submit.

Two further layers, so the guarantee does not rest on one mechanism:
  * `placeOrder` appears nowhere in this module. A test greps for it.
  * `submit_buy`/`submit_sell` return an order object whose state is
    CREATED, never SUBMITTED -- so a caller that ignored all of the
    above still cannot mistake a preview for a live order.

--------------------------------------------------------------------
THE STATUS TRAP, AND WHY amountDetail IS USED INSTEAD

Fidelity's `status` field is PROSE WITH THE FILL PRICE INTERPOLATED:

    "Open"   "Verified Canceled"   "Filled at $69.335"   "Filled at $69.53"

A map_broker_status built like the existing 18-key exact-match Alpaca
table would map every fill to UNKNOWN and halt the loop. Prefix-matching
"Filled at " would work but would be parsing English for money.

Neither is necessary. Every order carries a structured `amountDetail`:

    {"avgExecPrice": 69.35, "qty": 1, "qtyExec": 1, "qtyRemaining": 0,
     "commission": 0, "totalPriceImprovement": 0.01}

so state comes from qtyExec / qtyRemaining / cancelableInd, and `status`
is treated as a display label only. That also supplies filled_avg_price
and filled_qty directly, and gives partial fills for free.

--------------------------------------------------------------------
EXCEPTION TYPES, AND WHY THEY ARE SPLIT

ValueError for a bad ARGUMENT -- a non-positive quantity, a trade value
too small to buy a share. ExecutionError for a bad VENUE RESPONSE -- a
preview with no confNum, an account echoed back wrong, a quote with no
usable price.

This is not a stylistic preference. AlpacaBroker already raises
ValueError for exactly these argument cases and its tests pin that, so
the first run of tests/integration/test_broker_contract.py caught this
module diverging from it. Two adapters that reject the same bad input
with different exception types is precisely the divergence that
conformance test exists to find, and the older, live-money path is the
one that sets the convention.

--------------------------------------------------------------------
ACCOUNT SAFETY

The account is checked THREE times before any request carries it:
construction (is it in the allowlist), per call (has the allowlist
changed under us), and on the way out (does the payload name the account
we were asked for). The library this replaces selected accounts by
case-insensitive SUBSTRING match on a dropdown; nothing here does
anything but exact string equality against a configured full number.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.exceptions import ConfigurationError, ExecutionError
from src.fidelity_session import FidelitySession
from src.order_lifecycle import OrderState
from src.reconciliation import BrokerSnapshot

logger = logging.getLogger("Optimizer")

PENDING_PATH = "/ftgw/digital/activityapi/api/v1/transactions/pending"
# trade-equity/positions, NOT traderplus-api/api/positions/v1. Both are
# in the allowlist and only this one is safe: the traderplus response
# nests TWELVE accounts under acctDetails[], and its positionDetail rows
# carry symbol and quantity but NO acctNum -- so a key-search over it
# silently sums every account the user owns into one snapshot. This
# endpoint takes {"acctNum": ...} and returns a flat, already-scoped
# list. Verified from captured traffic, not assumed.
POSITIONS_PATH = "/ftgw/digital/trade-equity/positions"
BALANCE_PATH = "/ftgw/digital/trade-equity/balance"
QUOTE_PATH = "/ftgw/digital/trade-equity/getquote"
PREVIEW_PATH = "/ftgw/digital/trade-equity/previewSrvc"

# Fidelity's own codes, confirmed from captured payloads rather than
# guessed: orderAction B/S, priceTypeCode M/L, qtyTypeCode S (shares),
# tifCode D (day), condition N (none).
_ACTION = {"buy": "B", "sell": "S"}


@dataclass
class FidelityOrder:
    """The attributes live_trading_loop and reconciliation actually read.

    A plain object rather than a dict because callers do `order.id` and
    `.filled_qty` -- see src/fill_accounting.py and
    src/duplicate_order_guard.py. `state` is an OrderState so nothing
    downstream has to re-map a venue-specific string.
    """

    id: str
    client_order_id: str
    symbol: str
    state: OrderState = OrderState.CREATED
    filled_qty: float = 0.0
    filled_avg_price: float = 0.0
    qty: float = 0.0
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def status(self) -> str:
        """Alias so code written against Alpaca's `.status` still reads.

        Returns the canonical OrderState, NOT Fidelity's prose -- a
        caller passing this to map_broker_status must not receive
        "Filled at $69.35".
        """
        return str(self.state)


def derive_order_state(order: dict) -> OrderState:
    """Canonical state for one Fidelity order record.

    Reads the STRUCTURED fields, never the prose `status`. See the module
    docstring for why: `status` carries the fill price inside it, so no
    exact-match table can ever cover it.

    Ordering matters. Fill progress is checked before cancellation
    because a partially-filled order that is then cancelled has really
    had shares execute, and reporting it as CANCELED would lose them.
    """
    detail = order.get("amountDetail") or {}
    executed = _as_float(detail.get("qtyExec"))
    remaining = _as_float(detail.get("qtyRemaining"))
    ordered = _as_float(detail.get("qty")) or _as_float(order.get("quantity"))
    cancelable = _as_bool(order.get("cancelableInd"))

    if executed > 0:
        if remaining > 0:
            return OrderState.PARTIALLY_FILLED
        # remaining == 0 with shares executed is a completed order even
        # when `ordered` is unparseable -- Fidelity renders quantity as
        # "1 Share", so ordered can legitimately be 0 here.
        if ordered and executed + 1e-9 < ordered:
            return OrderState.PARTIALLY_FILLED
        return OrderState.FILLED

    if cancelable:
        return OrderState.ACCEPTED

    # Nothing executed and no longer cancelable: terminal without a fill.
    # Fidelity says "Verified Canceled" for both a user cancel and an
    # expiry, and the WebSocket's ORDER_STATUS enum agrees
    # (VERIFIED_CANCEL), so the two are genuinely not distinguished here
    # rather than being guessed apart.
    label = str(order.get("status", "")).lower()
    if "cancel" in label:
        return OrderState.CANCELED
    if "reject" in label:
        return OrderState.REJECTED
    if "expire" in label:
        return OrderState.EXPIRED
    logger.warning(
        f"Fidelity order {order.get('orderNum')!r} has no executed quantity, is not "
        f"cancelable, and has an unrecognised status {order.get('status')!r} -- "
        "mapping to UNKNOWN; reconciliation must resolve it."
    )
    return OrderState.UNKNOWN


def _as_float(value: Any) -> float:
    """Fidelity mixes numbers, numeric strings and '1 Share' in the same
    fields. Anything unparseable is 0.0, never an exception -- a snapshot
    that raises on one odd row tells you nothing about the other rows."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = "".join(c for c in value if c.isdigit() or c in ".-")
        try:
            return float(cleaned) if cleaned not in ("", "-", ".", "-.") else 0.0
        except ValueError:
            return 0.0
    return 0.0


def _as_bool(value: Any) -> bool:
    """cancelableInd arrives as a real bool in JSON and as the STRING
    'True'/'False' elsewhere in the same API. `bool("False")` is True,
    so this cannot be left to the built-in."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


class FidelityBroker:
    """Preview-only Fidelity adapter over an authenticated browser session."""

    def __init__(
        self,
        session: FidelitySession,
        account: str,
        allowed_accounts: tuple[str, ...] | list[str],
        *,
        symbol: str = "TQQQ",
        account_name: str | None = None,
        account_type_code: str | None = None,
    ) -> None:
        self._session = session
        self._account_name = account_name
        self._account_type_code = account_type_code
        self._allowed = tuple(str(a) for a in allowed_accounts)
        self._account = self._check_account(account)
        self._symbol = symbol
        # decision_id -> confNum, written at PREVIEW time. Reconnaissance
        # established that previewSrvc mints the id before anything is
        # committed, which is what closes the silent-partial-failure
        # window: the mapping is never a guess made after the fact.
        self._decision_to_conf: dict[str, str] = {}

    # -- account safety -------------------------------------------------

    def _check_account(self, account: str) -> str:
        """Exact match against the configured allowlist, or refuse.

        Re-checked on every call rather than trusted from construction:
        an allowlist consulted once is one refactor away from being
        decorative, and this is the check that decides whose money moves.
        """
        if not self._allowed:
            raise ConfigurationError(
                "live.fidelity.allowed_accounts is empty. Refusing to act against "
                "any account -- an empty allowlist means 'nothing is permitted', "
                "never 'everything is'."
            )
        account = str(account)
        if account not in self._allowed:
            raise ConfigurationError(
                f"Account {account[-4:]!r} (last 4) is not in "
                "live.fidelity.allowed_accounts. Exact full-number match is "
                "required -- the library this replaces selected accounts by "
                "case-insensitive SUBSTRING match, which a truncated value could "
                "satisfy against the wrong account."
            )
        return account

    # -- the LiveBroker surface ----------------------------------------

    def ping(self) -> None:
        """Prove the session is live and authenticated before trading."""
        self._session.assert_authenticated()

    def submit_buy(
        self, symbol: str, trade_value: float, client_order_id: str | None = None
    ) -> FidelityOrder:
        """PREVIEW a buy of trade_value dollars of symbol. Submits nothing.

        trade_value is NOTIONAL and Fidelity is share-based, so this
        converts using a fresh quote and rounds DOWN -- mirroring
        _floor_to_cent's conservative direction, so a rounding error can
        never overspend the intended amount.
        """
        if trade_value <= 0:
            raise ValueError(f"trade_value must be positive, got {trade_value}")
        price = self.get_quote(symbol)
        qty = int(trade_value // price)
        if qty < 1:
            raise ValueError(
                f"${trade_value:.2f} does not buy one whole share of {symbol} at "
                f"${price:.2f}. Fidelity orders here are whole-share "
                "(qtyTypeCode 'S'); fractional sizing is not modelled."
            )
        return self._preview(symbol, "buy", qty, price, client_order_id)

    def submit_sell(
        self,
        symbol: str,
        qty: float,
        target_price: float,
        client_order_id: str | None = None,
    ) -> FidelityOrder:
        """PREVIEW a limit sell of qty shares at target_price. Submits nothing.

        Callers must have cleared this through src/no_loss_guard.validate_sell
        first; this does not re-check, matching AlpacaBroker's contract that
        the guard lives in exactly one place.
        """
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")
        return self._preview(symbol, "sell", qty, target_price, client_order_id)

    def _preview(
        self,
        symbol: str,
        side: str,
        qty: float,
        limit_price: float,
        client_order_id: str | None,
    ) -> FidelityOrder:
        """Build and send the order ticket, stopping at preview.

        An explicit limitPrice is ALWAYS sent, never a market order.
        Extended-hours trading cannot be disabled in this venue's UI,
        which forces the limit branch anyway -- and a market order in a
        thin pre/post session is the one thing a grid strategy must
        never emit.
        """
        response = self._session.post_json(
            PREVIEW_PATH, {"orderDetails": self.build_ticket(symbol, side, qty, limit_price)}
        )
        account = self._account
        conf = _find_first(response, "confNum")
        if not conf:
            raise ExecutionError(
                "Fidelity accepted the preview but returned no confNum. Refusing to "
                "treat that as success: the confNum is the only handle by which this "
                "order could later be found or cancelled."
            )
        self._assert_echoed_account(response, account)
        if client_order_id:
            self._decision_to_conf[client_order_id] = conf
        logger.info(
            f"PREVIEW ONLY ({side} {qty} {symbol} limit {limit_price}) -> confNum "
            f"{conf}. Nothing was submitted; this adapter cannot place an order."
        )
        return FidelityOrder(
            id=conf,
            client_order_id=client_order_id or conf,
            symbol=symbol,
            state=OrderState.CREATED,
            qty=float(qty),
            raw={"preview": True},
        )

    def build_ticket(
        self, symbol: str, side: str, qty: float, limit_price: float
    ) -> dict:
        """The order ticket, field for field as the site's own page sends it.

        Transcribed from captured previewSrvc requests rather than
        designed. Two fields look wrong and are not: `previewInd` and
        `confInd` are BOTH true on a preview AND on a place -- what
        distinguishes them is the ENDPOINT and the presence of confNum,
        not these flags. An earlier version of this method set
        confInd=False on the reasoning that a preview is not a
        confirmation; the capture says otherwise, and matching the real
        client is worth more than a payload that reads sensibly.

        Exposed rather than private because the placing adapter builds
        the identical ticket and appends confNum. Two copies of a payload
        this fiddly is two chances to drift.
        """
        account = self._check_account(self._account)
        ticket = {
            "acctNum": account,
            "symbol": symbol,
            "orderAction": _ACTION[side],
            "orderActionCode": _ACTION[side],
            "priceTypeCode": "L",
            "limitPrice": round(float(limit_price), 2),
            "stopPrice": None,
            "qty": int(qty),
            "qtyTypeCode": "S",
            "tifCode": "D",
            "condition": "N",
            "routeCode": None,
            "isTradeTypeAvailable": False,
            "previewInd": True,
            "confInd": True,
        }
        # Present in every captured request. Passed through only when the
        # caller supplied them: inventing an acctTypeCode would be
        # guessing at a field that identifies the account.
        if self._account_name is not None:
            ticket["acctName"] = self._account_name
        if self._account_type_code is not None:
            ticket["acctTypeCode"] = self._account_type_code
        return ticket

    def _assert_echoed_account(self, response: Any, expected: str) -> None:
        """Read the account back out of Fidelity's own reply and compare.

        The request naming the right account is not proof the venue
        applied it. This is the readback the plan requires, and it is
        done against the response rather than against a DOM element
        whose existence was never verified.
        """
        echoed = _find_first(response, "acctNum")
        if echoed is not None and str(echoed) != expected:
            raise ExecutionError(
                "Fidelity echoed a DIFFERENT account than the one requested "
                f"(...{str(echoed)[-4:]} vs ...{expected[-4:]}). Refusing to "
                "continue."
            )

    def get_quote(self, symbol: str) -> float:
        """Current price for symbol, for notional -> share conversion.

        ASK is preferred over LAST, deliberately. This price converts a
        dollar amount into a share count for a BUY, and the ask is what a
        buy actually pays -- sizing against a lower last price would buy
        more shares than the cash covers. Same conservative direction as
        flooring the share count.

        Field names are Fidelity's, from captured traffic:
        QUOTE_DATA.ASK_PRICE / LAST_PRICE / BID_PRICE -- UPPER_SNAKE and
        string-valued. An earlier version looked for lastPrice / last /
        askPrice / bidPrice, camelCase names that appear NOWHERE in the
        response, so it could never have returned a price and every order
        would have died at "No usable price for ...".
        """
        response = self._session.post_json(QUOTE_PATH, {"symbols": symbol})
        for key in ("ASK_PRICE", "LAST_PRICE", "BID_PRICE"):
            price = _as_float(_find_first(response, key))
            if price > 0:
                return price
        raise ExecutionError(
            f"No usable price for {symbol} in the quote response. Refusing to size "
            "an order against a price this code had to guess at."
        )

    def get_order_by_client_id(self, client_order_id: str) -> FidelityOrder | None:
        """Look up an order by OUR decision_id, or None if absent.

        Fidelity has no client-reference field on an order -- the one
        reconnaissance question that came back NO -- so this resolves
        through the local decision_id -> confNum map written at preview
        time. That mapping is durable in the sense that matters: it is
        recorded BEFORE anything could be committed.
        """
        conf = self._decision_to_conf.get(client_order_id)
        if conf is None:
            return None
        for order in self._orders():
            if str(order.get("orderNum")) == conf:
                return self._to_order(order, client_order_id)
        return None

    def snapshot(self) -> BrokerSnapshot:
        """Current broker truth, shaped for src/reconciliation.Reconciler.

        Orders are keyed by OUR client_order_id where the local map knows
        one, and by Fidelity's confNum otherwise. An order placed by hand
        in the web UI therefore still appears -- as an unrecognised key,
        which is exactly what reconciliation should see rather than
        silently dropping it.
        """
        orders: dict[str, dict] = {}
        conf_to_decision = {v: k for k, v in self._decision_to_conf.items()}
        for raw in self._orders():
            conf = str(raw.get("orderNum"))
            key = conf_to_decision.get(conf, conf)
            detail = raw.get("amountDetail") or {}
            orders[key] = {
                "state": derive_order_state(raw),
                "filled_qty": _as_float(detail.get("qtyExec")),
                "avg_fill_price": _as_float(detail.get("avgExecPrice")),
                "symbol": raw.get("symbol"),
            }
        return BrokerSnapshot(
            positions=self._positions(), orders=orders, cash=self._cash()
        )

    # -- read-only fetches ---------------------------------------------

    def _orders(self) -> list[dict]:
        account = self._check_account(self._account)
        # Filter shape is Fidelity's own, from a captured request. A bare
        # {"acctNum": ...} is NOT what this endpoint takes.
        response = self._session.post_json(
            PENDING_PATH,
            {
                "filter": {
                    "accounts": [{"acctNum": account}],
                    "types": {
                        "orders": True,
                        "transfers": False,
                        "billpays": False,
                        "cryptoTOAs": False,
                        "alts": False,
                    },
                }
            },
        )
        return [
            o
            for o in _find_all_with_key(response, "orderNum")
            if _account_matches(o, account)
        ]

    def _positions(self) -> dict:
        """Share positions for this account. CASH IS NOT A POSITION.

        The core money-market fund appears here as an ordinary row --
        SPAXX, 27,336.03 "shares", securityType "Core", isCash true.
        Counting it would tell reconciliation the account holds tens of
        thousands of shares of something the strategy has never traded,
        which is worse than reporting nothing at all.
        """
        account = self._check_account(self._account)
        response = self._session.post_json(POSITIONS_PATH, {"acctNum": account})
        positions: dict[str, float] = {}
        for row in _find_all_with_key(response, "symbol"):
            if not _account_matches(row, account) or _is_cash_row(row):
                continue
            qty = _as_float(row.get("quantity") or row.get("qty"))
            symbol = row.get("symbol")
            if symbol and qty:
                positions[str(symbol)] = positions.get(str(symbol), 0.0) + qty
        return positions

    def _cash(self) -> float | None:
        """Settled cash, which in this cash IRA is what can actually trade.

        Prefers cashDetail.settledAmt over any headline "cash" figure:
        proceeds settle T+1 here, so unsettled cash is visible in the
        account and is NOT available without a good-faith violation. The
        conservative number is the correct one to reconcile against.
        """
        account = self._check_account(self._account)
        # A LIST of account objects, not a single object. Fidelity's shape.
        response = self._session.post_json(BALANCE_PATH, [{"acctNum": account}])
        for key in ("settledAmt", "cashAvailableToTrade", "cash"):
            value = _find_first(response, key)
            if value is not None:
                return _as_float(value)
        return None

    def _to_order(self, raw: dict, client_order_id: str) -> FidelityOrder:
        detail = raw.get("amountDetail") or {}
        return FidelityOrder(
            id=str(raw.get("orderNum")),
            client_order_id=client_order_id,
            symbol=str(raw.get("symbol") or ""),
            state=derive_order_state(raw),
            filled_qty=_as_float(detail.get("qtyExec")),
            filled_avg_price=_as_float(detail.get("avgExecPrice")),
            qty=_as_float(detail.get("qty")) or _as_float(raw.get("quantity")),
            raw=raw,
        )


# -- payload helpers ---------------------------------------------------
#
# Fidelity nests the same keys at different depths across endpoints
# (data.orders[], preview.orderConfirmDetail, ...). Searching by key
# rather than by a hard-coded path means a layout change surfaces as
# "not found" instead of a KeyError, and it does not need a schema this
# project cannot pin.


def _find_first(node: Any, key: str) -> Any:
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            found = _find_first(value, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_first(item, key)
            if found is not None:
                return found
    return None


def _find_all_with_key(node: Any, key: str) -> list[dict]:
    out: list[dict] = []
    if isinstance(node, dict):
        if key in node:
            out.append(node)
        for value in node.values():
            out.extend(_find_all_with_key(value, key))
    elif isinstance(node, list):
        for item in node:
            out.extend(_find_all_with_key(item, key))
    return out


def _is_cash_row(row: dict) -> bool:
    """True for the core money-market sweep, which is cash, not a holding.

    Three independent markers, because any one could be renamed: the
    explicit isCash flag, securityType "Core", and brokerageHoldingType.
    Cash misreported as a position is the failure that matters, so this
    errs toward excluding.
    """
    detail = row.get("securityDetail") or {}
    if detail.get("isCash") is True:
        return True
    if str(row.get("securityType", "")).strip().lower() == "core":
        return True
    return str(detail.get("brokerageHoldingType", "")).strip().lower() == "cash"


def _account_matches(row: dict, account: str) -> bool:
    """True when a row belongs to `account`, or names no account at all.

    Rows without an acctNum are kept: several endpoints return records
    already scoped to the requested account and do not repeat it. A row
    that DOES name a different account is dropped -- that is the case
    worth guarding, and dropping unlabelled rows instead would silently
    empty the snapshot.
    """
    value = row.get("acctNum") or row.get("accountNumber")
    return value is None or str(value) == account
