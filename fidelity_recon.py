#!/usr/bin/env python
"""Fidelity reconnaissance harness -- step 1 of the Fidelity integration.

WHAT THIS IS FOR
----------------
It answers three empirical questions that cannot be settled by reading
`fidelity-api`'s source, because they are about what FIDELITY transmits,
not what the library does with it:

  1. Does an order submit round-trip return an order/confirmation ID?
     This is what would close the ambiguity window at submission time.
  2. Is there an orders-list endpoint the Orders/Positions page calls?
     This is the bigger prize -- it would give genuine `snapshot.orders`
     enumeration and restore real reconciliation after a restart or a
     crash, which a submit-time ID alone does not.
  3. Can our `decision_id` be attached to an order at all (some client
     reference field), or must we keep a local decision_id -> Fidelity
     order ID map?

Until those are answered, the reconciliation mode and the payload parsers
cannot be designed -- only guessed at. So this script comes first, and
nothing downstream of it should be written before its dump has been read.

WHY IT IS SAFE TO RUN
---------------------
It cannot place an order. `transaction()` is called with `dry=True`, and
there is no flag, env var, or code path in this file that can set it
otherwise -- the capability is absent rather than defaulted-off. In dry
mode the library fills the order ticket and stops at the preview, so
there is no submitted order and therefore no ambiguity window at all.
That is precisely the state in which to do reconnaissance.

Three further hardening choices, all deliberate:

  * `save_state=False` -- `close_browser()` calls `save_storage_state()`
    unconditionally, but that method guards on `self.save_state`
    internally, so this flag genuinely prevents the write. The write
    would otherwise dump the complete cookie + localStorage set for an
    authenticated brokerage session, plaintext, into the CWD.
  * `profile_path` outside the repo -- defense in depth for the above.
    If the guard ever regresses upstream, the file lands somewhere
    private rather than somewhere committable.
  * `debug=False` -- `debug=True` starts a Playwright trace, which
    records `.fill()` arguments. That is the username and the password,
    in cleartext, in `./fidelity_trace*.zip`.

Neither `save_state` nor `debug` is exposed as an argument here. They are
not decisions a caller of a recon script should be able to make.

THE DUMP IS A SECRET
--------------------
Captured traffic from an authenticated session contains session tokens
and account numbers. `TrafficCapture` scrubs the literal credential
values and redacts secret-looking JSON keys, but that is mitigation, not
elimination. The dump is written outside the repo by default, mode 0600.
Read it, extract what you need, delete it.

USAGE
-----
    pip install -r requirements-fidelity.txt
    playwright install firefox

    export FIDELITY_USERNAME=... FIDELITY_PASSWORD=... FIDELITY_TOTP_SECRET=...
    python fidelity_recon.py --account Z12345678 --symbol TQQQ --quantity 1 \\
        --i-understand-this-logs-into-my-real-brokerage-account

Run it non-headless the first time (`--no-headless`) so you can watch what
it does and abandon the ticket yourself if anything looks wrong.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path

from src.exceptions import ConfigurationError
from src.fidelity_capture import TrafficCapture
from src.secrets import FidelityCredentials, load_fidelity_credentials

# Where the session profile and the traffic dump go by default: outside
# the repo, so that neither a git add nor a Docker `COPY . .` can pick
# them up even if every other defense fails.
DEFAULT_ARTIFACT_DIR = Path.home() / ".fidelity_recon"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run Fidelity reconnaissance: capture network traffic "
        "during login and an order PREVIEW. Never submits an order."
    )
    parser.add_argument(
        "--account",
        required=True,
        help="Full Fidelity account number. Must match EXACTLY -- the library "
        "selects accounts by case-insensitive SUBSTRING match on a dropdown, "
        "so a truncated value could uniquely match the wrong account.",
    )
    parser.add_argument("--symbol", default="TQQQ", help="Ticker for the preview.")
    parser.add_argument(
        "--quantity",
        type=float,
        default=1.0,
        help="Share quantity for the preview. Kept small on principle: nothing "
        "is submitted, but the ticket is filled in against a real account.",
    )
    parser.add_argument(
        "--action", choices=["buy", "sell"], default="buy", help="Preview side."
    )
    parser.add_argument(
        "--limit-price",
        type=float,
        default=None,
        help="Explicit limit price. Recommended: extended-hours trading cannot "
        "be disabled in the library, which forces the limit-order branch, and "
        "its internal last-price derivation has a comma-parsing bug that "
        "breaks on prices over $1,000.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ARTIFACT_DIR,
        help=f"Where the traffic dump and browser profile go (default: "
        f"{DEFAULT_ARTIFACT_DIR}). Keep this OUTSIDE the repo.",
    )
    parser.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Show the browser. Recommended for the first run.",
    )
    parser.set_defaults(headless=True)
    parser.add_argument(
        "--skip-preview",
        action="store_true",
        help="Log in and enumerate accounts only -- do not open an order "
        "ticket. Answers question 2 without touching a trade screen.",
    )
    parser.add_argument(
        "--i-understand-this-logs-into-my-real-brokerage-account",
        dest="confirmed",
        action="store_true",
        help="Required. This script authenticates against a live Fidelity "
        "account. It cannot place an order, but it does log in.",
    )
    return parser.parse_args(argv)


def _prepare_artifact_dir(path: Path) -> Path:
    """Create the artifact directory private to this user.

    0700 is set explicitly rather than left to the umask, because the
    default umask on a shared machine can leave it group- or
    world-readable, and what lands here is credential-equivalent. On
    Windows the chmod is a no-op -- NTFS ACLs are what matter there and
    a user profile directory is already restricted -- so its failure is
    tolerated rather than fatal.
    """
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(stat.S_IRWXU)
    except OSError:
        pass
    return path


def _write_dump(capture: TrafficCapture, path: Path) -> None:
    """Write the capture to disk, readable only by this user."""
    payload = capture.to_dict()
    # Create with 0600 BEFORE writing rather than chmod-ing after: a
    # chmod afterwards leaves a window in which the file exists with
    # default permissions and already contains the session traffic.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _assert_account_allowed(
    fid, requested: str
) -> dict:  # noqa: ANN001 -- duck-typed FidelityAutomation
    """Enumerate accounts and require an EXACT match for the requested one.

    Uses `get_list_of_accounts`, not `getAccountInfo`: the latter
    silently skips Y-prefixed managed accounts and misses accounts with
    no holdings, and the two produce differently-formatted keys that
    nothing reconciles. An enumeration that can silently omit an account
    is the wrong thing to check an allowlist against.

    Exact match, never substring. The library's own selection is a
    case-insensitive substring match against dropdown text, which fails
    closed on ambiguity (Playwright strict mode raises on 2+ matches) but
    would happily click a uniquely-matching WRONG account given a
    truncated number.
    """
    accounts = fid.get_list_of_accounts(get_withdrawal_bal=True)
    available = sorted(str(k) for k in (accounts or {}))
    if requested not in available:
        raise ConfigurationError(
            f"Requested account is not present in this login's account list. "
            f"Requested: {requested!r}. Available: {available!r}. "
            f"Refusing to proceed -- an account number that does not match "
            f"exactly must never be passed to the library's substring-based "
            f"selector."
        )
    return accounts


def run_recon(args: argparse.Namespace, credentials: FidelityCredentials) -> int:
    # Imported here, not at module scope, so that `--help` and the unit
    # tests work without playwright or fidelity-api installed. Those are
    # optional dependencies (requirements-fidelity.txt), absent from the
    # Docker image and from every backtest environment.
    try:
        from fidelity import FidelityAutomation
    except ImportError as exc:
        raise ConfigurationError(
            "fidelity-api is not installed. This is an opt-in dependency:\n"
            "    pip install -r requirements-fidelity.txt\n"
            "    playwright install firefox"
        ) from exc

    artifact_dir = _prepare_artifact_dir(args.artifact_dir)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    dump_path = artifact_dir / f"recon_{stamp}.json"

    capture = TrafficCapture(secret_values=credentials.secret_values())

    fid = FidelityAutomation(
        headless=args.headless,
        # Hard-wired, not exposed as arguments -- see module docstring.
        debug=False,
        save_state=False,
        profile_path=str(artifact_dir),
    )

    try:
        # BEFORE login. The constructor launches the browser without
        # navigating anywhere (login() is a separate call), and Playwright
        # only delivers events for activity after a listener is attached --
        # so this is the one moment at which the whole session, login
        # round-trip included, is capturable.
        capture.attach(fid.page)

        print(f"[recon] logging in (headless={args.headless})...", file=sys.stderr)
        logged_in, needs_2fa_code = fid.login(
            username=credentials.username,
            password=credentials.password,
            totp_secret=credentials.totp_secret,
            # Never persist a 2FA-bypass token for a recon run.
            save_device=False,
        )
        if not logged_in:
            raise ConfigurationError(
                "Login failed. Nothing was captured beyond the login attempt."
            )
        if not needs_2fa_code:
            # login() returns (True, False) on the SMS path and then waits
            # for an out-of-band code. There is no callback or hook to
            # supply one, so an unattended run stalls here rather than
            # failing -- worth saying out loud rather than letting it hang.
            print(
                "[recon] WARNING: login reported the SMS 2FA path, not TOTP. "
                "Supply FIDELITY_TOTP_SECRET for an unattended run.",
                file=sys.stderr,
            )

        print("[recon] enumerating accounts...", file=sys.stderr)
        _assert_account_allowed(fid, args.account)
        print(f"[recon] account {args.account} confirmed present.", file=sys.stderr)

        if args.skip_preview:
            print("[recon] --skip-preview: not opening an order ticket.", file=sys.stderr)
        else:
            print(
                f"[recon] DRY-RUN preview: {args.action} {args.quantity} "
                f"{args.symbol} in {args.account}...",
                file=sys.stderr,
            )
            # dry=True is passed explicitly rather than relying on the
            # library's default, so that this line reads as a decision
            # and an upstream default change cannot silently flip it.
            result = fid.transaction(
                stock=args.symbol,
                quantity=args.quantity,
                action=args.action,
                account=args.account,
                dry=True,
                limit_price=args.limit_price,
            )
            # Annotated `-> bool` upstream but actually returns
            # (bool, str|None). Unpacked defensively so a future upstream
            # correction to the annotation does not crash this script.
            if isinstance(result, tuple):
                succeeded, detail = (result + (None,))[:2]
            else:
                succeeded, detail = bool(result), None
            print(
                f"[recon] preview result: success={succeeded} detail={detail!r}",
                file=sys.stderr,
            )
    finally:
        # Always write the dump, even on failure. A run that broke
        # halfway still captured the traffic up to the break, and that
        # traffic is the entire point of the exercise.
        try:
            _write_dump(capture, dump_path)
            print(f"[recon] wrote {dump_path}", file=sys.stderr)
        except OSError as exc:
            print(f"[recon] FAILED to write dump: {exc}", file=sys.stderr)
        try:
            fid.close_browser()
        except Exception as exc:  # noqa: BLE001 -- teardown must not mask
            print(f"[recon] close_browser raised: {exc}", file=sys.stderr)

    _report(capture, dump_path)
    return 0


def _report(capture: TrafficCapture, dump_path: Path) -> None:
    """Print the inventory a human needs to answer the three questions."""
    summary = capture.summary()
    print("\n===== RECON SUMMARY =====")
    print(f"frames={summary['frames']} responses={summary['responses']}")
    if summary["dropped_records"]:
        print(f"DROPPED {summary['dropped_records']} records (hit the cap)")
    if summary["handler_errors"]:
        print(f"handler errors: {summary['handler_errors']}")

    print("\n-- WebSocket URLs (question 1: does submit round-trip an ID?) --")
    for url, count in sorted(
        summary["websocket_urls"].items(), key=lambda kv: -kv[1]
    ):
        print(f"  {count:6d}  {url}")
    if not summary["websocket_urls"]:
        print("  (none -- no WebSocket traffic was seen at all)")

    print("\n-- XHR endpoints (question 2: is there an orders-list endpoint?) --")
    for endpoint, count in sorted(summary["endpoints"].items(), key=lambda kv: -kv[1]):
        print(f"  {count:6d}  {endpoint}")
    if not summary["endpoints"]:
        print("  (none)")

    candidates = capture.candidate_id_fields()
    print(f"\n-- Payloads containing ID-shaped keys ({len(candidates)}) --")
    for hit in candidates[:40]:
        where = f"{hit['kind']}[{hit['index']}]"
        print(f"  {where:16s} {hit['keys']}  {hit['url'][:80]}")
    if len(candidates) > 40:
        print(f"  ... and {len(candidates) - 40} more (see the dump)")
    if not candidates:
        print("  (none -- this is itself an answer, and a discouraging one)")

    print(
        f"\nFull dump: {dump_path}\n"
        "This file contains authenticated-session traffic. Read it, extract\n"
        "what you need, then delete it."
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.confirmed:
        print(
            "Refusing to run without "
            "--i-understand-this-logs-into-my-real-brokerage-account.\n"
            "This script cannot place an order (dry-run only), but it does "
            "authenticate against a live account.",
            file=sys.stderr,
        )
        return 2
    try:
        credentials = load_fidelity_credentials()
        return run_recon(args, credentials)
    except ConfigurationError as exc:
        print(f"[recon] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
