"""
python -m fidelity_gateway.bridge keygen | serve | host | check | build-extension

  keygen   Create the API key: append FIDELITY_BRIDGE_API_KEY to .env and
           print it once, for pasting into the extension's welcome form.
  serve    Run the bridge until Ctrl-C, reporting connections and the
           extension's order confirmations.
  host     A Fidelity deployment's bridge, for as long as it runs (host.py,
           the fidelity-bridge service): the extension stays connected
           between sessions, each session's trading loop attaches to it over
           --socket, and its readiness and events go to the control
           directory for the Live page and the supervisor.
  check    Read-only end-to-end proof: wait for the extension, show what
           it reports about its recent orders, then read the account's
           orders, positions and settled cash through it.
  build-extension
           Build the extension from its submodule into the folder the
           browser loads it from; its popup then offers Reload now.

Nothing here can place an order. `check` builds a read-only session, so
the engine-side transport refuses previews and orders before the
extension -- which refuses them too unless you switched them on -- is
even asked.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
from datetime import UTC, datetime
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
from fidelity_gateway.bridge.order_reports import OrderReports
from fidelity_gateway.bridge.server import DEFAULT_HOST, DEFAULT_PORT, BridgeError, BridgeServer
from fidelity_gateway.bridge.versions import EXTENSION_ROOT, version_advice
from fidelity_gateway.session import FidelitySession, FidelitySessionError

ORDER_LOG_WAIT_SECONDS = 5.0


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _status(mode: str, state: str, detail: str) -> dict:
    """What the extension's popup shows for a bridge with no trading loop."""
    return {
        "mode": mode,
        "state": state,
        "detail": detail,
        "updatedAt": datetime.now(UTC).isoformat(),
    }


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

    host = commands.add_parser(
        "host", help="Keep a Fidelity deployment's bridge up, for its sessions to attach to."
    )
    host.add_argument(
        "--config", required=True, help="The deployment's config (live.broker: fidelity)."
    )
    host.add_argument(
        "--socket",
        default=os.environ.get("VAI_BRIDGE_SOCKET"),
        help="Where trading loops attach. Default: $VAI_BRIDGE_SOCKET.",
    )
    host.add_argument(
        "--control-dir",
        default=os.environ.get("VAI_CONTROL_DIR"),
        help="The deployment's control directory: status, events and the Live page's "
        "check_connection go to its bridge/ folder. Default: $VAI_CONTROL_DIR.",
    )
    host.add_argument(
        "--deployment",
        default=os.environ.get("VAI_DEPLOYMENT"),
        help="The deployment's id, for the extension's popup. Default: $VAI_DEPLOYMENT.",
    )
    host.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help=f"Where {API_KEY_ENV_VAR} is read from when it is not in the environment.",
    )

    build = commands.add_parser(
        "build-extension",
        help="Build the extension from its submodule, for the browser to reload.",
    )
    build.add_argument("--node", default=None, help="The node to run. Default: node on PATH.")
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
    server.set_engine_status(
        _status("bridge", "running", "the bridge alone, with no trading loop behind it")
    )
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


def _config_stamp(path: Path) -> tuple | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


def _load_fidelity(path: Path):
    """(FidelityConfig, symbol) from a deployment's config, validated."""
    from engine.core.config import BacktestConfig

    config = BacktestConfig.from_yaml(str(path))
    config.validate()
    if config.live.broker != "fidelity" or config.live.fidelity is None:
        raise ConfigurationError(f"{path} is not a Fidelity deployment (live.broker: fidelity).")
    return config.live.fidelity, config.backtest.symbol


def run_host(args: argparse.Namespace, stop: threading.Event | None = None) -> int:
    """Until SIGTERM or Ctrl-C (or `stop`): the deployment's bridge host."""
    from engine.core.build_info import identity
    from engine.trading.control_inbox import ControlInbox
    from fidelity_gateway.bridge.host import CONFIG_POLL_SECONDS, BridgeHost, account_checker

    if not args.socket:
        _stderr("Name the socket trading loops attach to: --socket, or VAI_BRIDGE_SOCKET.")
        return 2
    stop = stop or threading.Event()

    def _stop(_signum, _frame) -> None:
        stop.set()

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)

    config_path = Path(args.config)
    said = False
    while not config_path.exists():
        # The config names the account, so it is written by hand on the host;
        # the service may well start first. Say so once, and wait for it.
        if not said:
            _stderr(f"[bridge-host] {config_path} does not exist yet; waiting for it.")
            said = True
        if stop.wait(CONFIG_POLL_SECONDS):
            return 0
    key = load_api_key(env_file=args.env_file)

    def make_server(settings, on_event) -> BridgeServer:
        policy = AddressPolicy.from_entries(settings.allowed_clients, settings.blocked_clients)
        return BridgeServer(
            key,
            host=settings.host,
            port=settings.port,
            policy=policy,
            log=_stderr,
            on_event=on_event,
        )

    settings = lambda: _load_fidelity(config_path)  # noqa: E731 -- re-read on a change
    inbox = ControlInbox(Path(args.control_dir) / "bridge") if args.control_dir else None
    host = BridgeHost(
        make_server=make_server,
        settings=settings,
        socket_path=args.socket,
        inbox=inbox,
        check=account_checker(settings),
        deployment=args.deployment,
        build=identity(),
    )
    stamp = {"value": _config_stamp(config_path)}

    def config_changed() -> bool:
        now = _config_stamp(config_path)
        changed, stamp["value"] = now != stamp["value"], now
        return changed

    _stderr(f"[bridge-host] trading loops attach at {args.socket}")
    host.run(stop, config_changed=config_changed)
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
        # Quiet: the summary below says it once, rather than a log line
        # per order as the extension's log arrives.
        order_reports=OrderReports(),
        client={"process": "check"},
    )
    try:
        server.set_engine_status(_status("check", "running", "checking the connection, read-only"))
        status = server.request("status", {}, timeout=15)
        tab = (status.get("fidelityTab") or {}).get("url") or "none open"
        print(f"extension {status.get('extensionVersion', '?')}; Fidelity tab: {tab}")
        advice = version_advice(server.extension.get("version"), server.extension_versions)
        if advice:
            print(f"  update: {advice}")
        print(f"extension permissions: {status.get('permissions')}")
        # The extension sends its order log once it has connected.
        if not server.order_reports.wait_for_log(ORDER_LOG_WAIT_SECONDS):
            print("orders the extension reports: it sent no order log (an older version?)")
        else:
            reports = server.order_reports.recent(3)
            print("orders the extension reports:" + ("" if reports else " none yet"))
            for report in reports:
                conf = f"  confNum {report.conf_num}" if report.conf_num else ""
                print(f"  {report.summary:<28} {report.state}{conf}")

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
        server.set_engine_status(_status("check", "stopped", "the check finished: it works"))
        return 0
    finally:
        server.stop()


def run_build_extension(args: argparse.Namespace, root: Path = EXTENSION_ROOT) -> int:
    """`npm run build` in the submodule, from the engine's side: the
    extension's scripts/build.mjs writes dist/fidelity-bridge, the folder
    the browser loads. The popup then sees the newer build on disk and
    offers Reload now -- no visit to the extensions page."""
    script = root / "scripts" / "build.mjs"
    if not script.is_file():
        _stderr(
            f"The extension's source is not checked out at {root}. Run: git submodule update --init"
        )
        return 2
    node = args.node or shutil.which("node")
    if not node:
        _stderr("Building the extension needs Node 22 or later on PATH: https://nodejs.org")
        return 2
    result = subprocess.run(
        [node, str(script)], cwd=root, capture_output=True, text=True, timeout=120, check=False
    )
    if result.returncode != 0:
        _stderr((result.stderr or result.stdout).strip() or f"node exited with {result.returncode}")
        return 2
    print(result.stdout.strip())
    print(
        "\nOpen the extension's popup and press Reload now to use it -- or Reload on "
        "edge://extensions. Load it from the same folder as before: its settings belong to "
        "that folder."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runners = {
        "keygen": run_keygen,
        "serve": run_serve,
        "host": run_host,
        "check": run_check,
        "build-extension": run_build_extension,
    }
    try:
        return runners[args.command](args)
    except (ConfigurationError, FidelitySessionError, BridgeError) as exc:
        _stderr(f"\n{exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
