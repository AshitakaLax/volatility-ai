"""
python -m fidelity_gateway.bridge keygen | serve | check

  keygen   Create the API key: append FIDELITY_BRIDGE_API_KEY to .env and
           print it once, for pasting into the extension's welcome form.
  serve    Run the bridge until Ctrl-C, reporting connections.
  check    Read-only end-to-end proof: wait for the extension, then read
           the account's orders, positions and settled cash through it.

Nothing here can place an order. `check` builds a read-only session, so
the engine-side transport refuses previews and orders before the
extension -- which refuses them too unless you switched them on -- is
even asked.
"""

from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge import DEFAULT_ALLOWED_CLIENTS, open_bridge
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import (
    API_KEY_ENV_VAR,
    default_env_file,
    generate_api_key,
    load_api_key,
    write_api_key,
)
from fidelity_gateway.bridge.server import DEFAULT_HOST, DEFAULT_PORT, BridgeError, BridgeServer
from fidelity_gateway.session import FidelitySession, FidelitySessionError


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _server_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Address to listen on. The default, 127.0.0.1, takes connections from this "
        "computer only; use 0.0.0.0 for a browser on another machine, with --allow-client.",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Default: 8765.")
    parser.add_argument(
        "--allow-client",
        action="append",
        default=None,
        metavar="IP_OR_CIDR",
        help="A browser address that may connect. Repeat for more. Default: 127.0.0.1 and ::1.",
    )
    parser.add_argument(
        "--block-client",
        action="append",
        default=[],
        metavar="IP_OR_CIDR",
        help="Always refused, even when also allowed. Repeat for more.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help=f"Where {API_KEY_ENV_VAR} is read from when it is not in the environment. "
        "Default: the repository's .env.",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m fidelity_gateway.bridge",
        description="The engine's end of the Fidelity Bridge browser extension.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    keygen = commands.add_parser("keygen", help="Create the API key in .env and print it.")
    keygen.add_argument(
        "--env-file", type=Path, default=None, help="Default: the repository's .env."
    )
    keygen.add_argument(
        "--print-only", action="store_true", help="Print a fresh key and write nothing."
    )

    serve = commands.add_parser("serve", help="Run the bridge until Ctrl-C.")
    _server_flags(serve)

    check = commands.add_parser("check", help="Read-only end-to-end check through the extension.")
    _server_flags(check)
    check.add_argument("--account", required=True, help="Full account number, exact.")
    check.add_argument(
        "--account-name",
        default="Traditional IRA",
        help="The account's display name; Fidelity's order list requires it.",
    )
    check.add_argument(
        "--wait", type=float, default=120.0, help="Seconds to wait for the extension."
    )
    return parser.parse_args(argv)


def run_keygen(args: argparse.Namespace) -> int:
    if args.print_only:
        print(generate_api_key())
        return 0
    path = args.env_file or default_env_file()
    key = write_api_key(path)
    print(
        f"Wrote {API_KEY_ENV_VAR} to {path}.\n\n"
        "Paste this key into the Fidelity Bridge extension's settings:\n\n"
        f"    {key}\n"
    )
    return 0


def run_serve(args: argparse.Namespace, stop: threading.Event | None = None) -> int:
    key = load_api_key(env_file=args.env_file)
    policy = AddressPolicy.from_entries(
        args.allow_client or DEFAULT_ALLOWED_CLIENTS, args.block_client
    )
    server = BridgeServer(key, host=args.host, port=args.port, policy=policy, log=_stderr)
    server.start()
    _stderr(
        f"[bridge] listening on {server.url} (allowed clients: {', '.join(policy.allowed)}). "
        "Ctrl-C to stop."
    )
    stop = stop or threading.Event()
    try:
        # A short wait in a loop, not one long one: on Windows a single
        # untimed wait would not see Ctrl-C until it returned.
        while not stop.wait(0.5):
            pass
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


def run_check(args: argparse.Namespace) -> int:
    from fidelity_gateway.broker import FidelityBroker

    server, page = open_bridge(
        host=args.host,
        port=args.port,
        allow=args.allow_client or DEFAULT_ALLOWED_CLIENTS,
        block=args.block_client,
        env_file=args.env_file,
        wait_seconds=args.wait,
    )
    try:
        status = server.request("status", {}, timeout=15)
        tab = (status.get("fidelityTab") or {}).get("url") or "none open"
        print(f"extension {status.get('extensionVersion', '?')}; Fidelity tab: {tab}")
        print(f"extension permissions: {status.get('permissions')}")

        # Read-only on purpose: neither previews nor orders are allowed
        # through this session, whatever the extension would permit.
        session = FidelitySession(page)
        session.attach()
        try:
            session.wait_for_credentials(timeout_seconds=10)
        except FidelitySessionError:
            _stderr("[bridge] no auth headers seen yet; loading Trader+ in the Fidelity tab")
            session.prime()
            session.wait_for_credentials(timeout_seconds=60)
        session.assert_authenticated()

        broker = FidelityBroker(
            session, args.account, (args.account,), account_name=args.account_name
        )
        orders = broker._orders()
        positions = broker._positions()
        cash = broker._cash()
        print(f"orders listed: {len(orders)}")
        print(f"positions: {positions or 'none'}")
        print(f"settled cash: {'unknown' if cash is None else f'${cash:,.2f}'}")
        print("\nThe bridge works end to end.")
        return 0
    finally:
        server.stop()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runners = {"keygen": run_keygen, "serve": run_serve, "check": run_check}
    try:
        return runners[args.command](args)
    except (ConfigurationError, FidelitySessionError, BridgeError) as exc:
        _stderr(f"\n{exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
