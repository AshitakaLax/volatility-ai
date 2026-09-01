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
import time
from datetime import UTC, datetime
from pathlib import Path

from src.exceptions import ConfigurationError
from src.fidelity_capture import TrafficCapture
from src.secrets import FidelityCredentials, load_fidelity_credentials

# Where the session profile and the traffic dump go by default: outside
# the repo, so that neither a git add nor a Docker `COPY . .` can pick
# them up even if every other defense fails.
DEFAULT_ARTIFACT_DIR = Path.home() / ".fidelity_recon"

# A different front end from the classic pages fidelity-api drives, with
# its own API surface, and the one an active trader actually uses.
TRADERPLUS_URL = "https://digital.fidelity.com/ftgw/digital/traderplus"


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
        "--cdp-url",
        default=None,
        help="Attach to an ALREADY-RUNNING Chromium browser (Edge or Chrome) over "
        "the DevTools protocol, e.g. http://localhost:9222. Uses your real "
        "browser, real profile and real session -- nothing is launched, no "
        "credentials are read, and the library is not used at all. This is the "
        "mode that works when Fidelity refuses a Playwright-launched browser. "
        "See the module docstring for how to start the browser with debugging "
        "enabled.",
    )
    parser.add_argument(
        "--capture-seconds",
        type=float,
        default=300.0,
        help="With --cdp-url: how long to keep recording while you browse "
        "(default: 300). Recording stops early if you close every tab.",
    )
    parser.add_argument(
        "--manual-login",
        action="store_true",
        help="Open the browser to Fidelity's sign-in page and wait for YOU to "
        "log in by hand, instead of driving the login with credentials. "
        "Requires no FIDELITY_USERNAME/PASSWORD/TOTP_SECRET at all. Implies "
        "--no-headless (you cannot type into a hidden browser). Capture is "
        "attached AFTER login in this mode -- see the module docstring for "
        "why that is deliberate.",
    )
    parser.add_argument(
        "--login-timeout",
        type=float,
        default=300.0,
        help="Seconds to wait for a manual login to complete (default: 300). "
        "Only meaningful with --manual-login.",
    )
    parser.add_argument(
        "--no-traderplus",
        dest="visit_traderplus",
        action="store_false",
        help="Skip the Trader+ visit. By default a manual-login run loads "
        f"{TRADERPLUS_URL} after sign-in, because it is a different front "
        "end from the one the library drives and is the likeliest place to "
        "find real order/position endpoints.",
    )
    parser.set_defaults(visit_traderplus=True)
    parser.add_argument(
        "--settle-ms",
        type=int,
        default=8000,
        help="Milliseconds to keep recording after a page reports idle "
        "(default: 8000). WebSocket traffic often starts only after the "
        "initial load settles, so leaving this at zero can miss exactly "
        "the traffic this script exists to find.",
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


# Read from the library's own login(), not guessed: it navigates to
# https://digital.fidelity.com/prgw/digital/signin/retail, while every
# authenticated page it later visits (the transfers page
# get_list_of_accounts scrapes, the trade ticket) lives under
# /ftgw/digital/. So "the URL no longer contains the sign-in path" is a
# source-derived signal that login finished, not a guess about Fidelity's
# routing.
FIDELITY_LOGIN_URL = "https://digital.fidelity.com/prgw/digital/signin/retail"
_SIGNIN_PATH_MARKER = "/prgw/digital/signin"
# POSITIVE signal for "authenticated", not merely "no longer on the
# sign-in page". Every signed-in Fidelity surface observed so far lives
# under /ftgw/digital/ -- the transfers page get_list_of_accounts
# scrapes, the portfolio summary, and Trader+
# (/ftgw/digital/traderplus). Requiring the authenticated marker rather
# than the absence of the sign-in one means an interstitial, an error
# page, or about:blank cannot be mistaken for a completed login.
_AUTHENTICATED_PATH_MARKER = "/ftgw/digital/"


def _context_pages(context) -> list:
    """Every live page in the context, newest last. Tolerates a context
    double that does not implement `.pages`."""
    try:
        return list(getattr(context, "pages", []) or [])
    except Exception:  # noqa: BLE001 -- a torn-down context is handled by the caller
        return []


def _wait_for_manual_login(context, timeout_seconds: float, poll_seconds: float = 2.0):
    """Wait until the human has logged in, watching EVERY page.

    Returns the page that reached an authenticated URL.

    WATCHES THE WHOLE CONTEXT, NOT ONE PAGE, and that is the entire
    lesson of the first real run. The original version polled the single
    page object the library created at construction. Fidelity's sign-in
    moved the human to a different page, that original page sat on the
    sign-in URL forever, and the wait timed out after ten minutes while
    a perfectly good authenticated session sat in the next tab. Capture
    attaches only after this returns, so the run also recorded nothing:
    a dump with zero records and no errors in it, which looks exactly
    like "Fidelity sends no traffic" and is not that at all.

    Detection is by URL rather than by prompting on stdin: this script
    is routinely run through wrappers that attach stdin to the null
    device, where input() would raise EOFError instantly. Watching pages
    needs no stdin.

    A URL check is still a heuristic, so it is not the only guard --
    _assert_account_allowed runs straight afterwards and fails loudly if
    the session is not really authenticated. This wait exists to give
    the human time, not to prove authentication.
    """
    deadline = time.monotonic() + timeout_seconds
    print(
        "\n"
        "==================================================================\n"
        "  LOG IN IN THE BROWSER WINDOW THAT JUST OPENED.\n"
        "\n"
        "  Nothing is being typed for you and no credentials were read.\n"
        "  Take as long as you need, 2FA included.\n"
        "  A new tab is fine -- every tab is being watched.\n"
        f"  Waiting up to {timeout_seconds:.0f}s for a signed-in page,\n"
        "  then reconnaissance continues automatically.\n"
        "==================================================================\n",
        file=sys.stderr,
        flush=True,
    )
    reported: set[str] = set()
    while time.monotonic() < deadline:
        pages = _context_pages(context)
        if not pages:
            raise ConfigurationError(
                "The browser has no open pages left -- the window was closed "
                "before login completed."
            )
        for page in pages:
            try:
                current = page.url
            except Exception:  # noqa: BLE001 -- one dead tab must not end the wait
                continue
            if current not in reported:
                print(f"[recon]   tab at {current}", file=sys.stderr, flush=True)
                reported.add(current)
            if _AUTHENTICATED_PATH_MARKER in current:
                try:
                    page.wait_for_load_state("load")
                except Exception:  # noqa: BLE001 -- best effort
                    pass
                print(
                    f"[recon] login detected on {current}", file=sys.stderr, flush=True
                )
                return page
        time.sleep(poll_seconds)
    seen = ", ".join(sorted(reported)) or "(no pages seen)"
    raise ConfigurationError(
        f"Timed out after {timeout_seconds:.0f}s waiting for a manual login. "
        f"No tab reached a URL containing {_AUTHENTICATED_PATH_MARKER!r}. "
        f"Tabs seen: {seen}. Re-run with a larger --login-timeout if you "
        "simply need more time."
    )


def run_cdp_recon(args: argparse.Namespace) -> int:
    """Record traffic from a browser the USER is already running.

    This mode exists because Fidelity refuses a Playwright-launched
    browser outright -- a fresh automated profile with no cookies and no
    history is answered with "Sorry, we can't complete this action right
    now", while the same person logs in fine in their ordinary browser.

    Nothing here defeats that check; it removes the reason for it. The
    browser is the user's own, the profile is their own, the login is
    performed by them by hand. We only listen. That also makes this a
    STRICTLY better recon record than the launched-browser path would
    have produced: a real session rather than a synthetic one.

    Deliberately does NOT use FidelityAutomation. The library owns a
    browser it launched itself, which is the thing that does not work
    here; and reconnaissance needs no library at all, only listeners.
    Account enumeration is skipped for the same reason -- the human can
    simply open the Accounts page, and that navigation is captured like
    any other.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ConfigurationError(
            f"playwright is not installed: {exc}\n"
            "    pip install -r requirements-fidelity.txt"
        ) from exc

    artifact_dir = _prepare_artifact_dir(args.artifact_dir)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    dump_path = artifact_dir / f"recon_{stamp}.json"

    # No secret_values: this mode never sees a password, so there is
    # nothing to scrub by exact match. Key-based redaction still applies
    # to every payload (see TrafficCapture / redact_secrets).
    capture = TrafficCapture()

    playwright = sync_playwright().start()
    browser = None
    try:
        print(f"[recon] connecting to {args.cdp_url} ...", file=sys.stderr)
        try:
            browser = playwright.chromium.connect_over_cdp(args.cdp_url)
        except Exception as exc:  # noqa: BLE001 -- the actionable part is the advice
            raise ConfigurationError(
                f"Could not attach to a browser at {args.cdp_url}: {exc}\n"
                "\n"
                "Start Edge with remote debugging FIRST, using a separate profile "
                "directory:\n"
                '    & "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" '
                "--remote-debugging-port=9222 "
                '--user-data-dir="C:\\Users\\%USERNAME%\\edge-debug-profile"\n'
                "\n"
                "--user-data-dir is REQUIRED, not optional: current Chrome and Edge "
                "refuse to enable remote debugging on the DEFAULT profile. Omitting "
                "it looks like the browser simply ignored the flag."
            ) from exc

        contexts = list(browser.contexts)
        if not contexts:
            raise ConfigurationError(
                "Attached, but the browser reports no contexts -- it has no open "
                "windows. Open a tab and re-run."
            )
        for context in contexts:
            capture.attach_context(context)

        print(
            f"[recon] attached to {capture.attached_page_count} page(s) across "
            f"{len(contexts)} context(s).",
            file=sys.stderr,
        )
        print(
            "\n"
            "==================================================================\n"
            "  RECORDING. Use the browser normally.\n"
            "\n"
            "  To answer the questions that matter, visit:\n"
            "    * Trader+            " + TRADERPLUS_URL + "\n"
            "    * your Orders / Activity page  (question 2: is there an\n"
            "      orders-list endpoint?)\n"
            "    * Positions\n"
            "\n"
            "  Do NOT place an order. Opening a trade ticket is fine and is\n"
            "  worth doing -- filling one in without submitting shows what a\n"
            "  preview round-trip looks like.\n"
            f"\n  Recording for up to {args.capture_seconds:.0f}s.\n"
            "==================================================================\n",
            file=sys.stderr,
            flush=True,
        )

        deadline = time.monotonic() + args.capture_seconds
        last_report = 0.0
        while time.monotonic() < deadline:
            time.sleep(2.0)
            # Surface progress, so a silent run is distinguishable from a
            # stalled one without waiting out the whole timer.
            elapsed = args.capture_seconds - (deadline - time.monotonic())
            if elapsed - last_report >= 30.0:
                summary = capture.summary()
                print(
                    f"[recon]   {elapsed:5.0f}s  frames={summary['frames']} "
                    f"responses={summary['responses']} "
                    f"pages={capture.attached_page_count}",
                    file=sys.stderr,
                    flush=True,
                )
                last_report = elapsed
            still_open = any(_context_pages(ctx) for ctx in browser.contexts)
            if not still_open:
                print(
                    "[recon] every tab was closed; stopping early.", file=sys.stderr
                )
                break
    finally:
        try:
            _write_dump(capture, dump_path)
            print(f"[recon] wrote {dump_path}", file=sys.stderr)
        except OSError as exc:
            print(f"[recon] FAILED to write dump: {exc}", file=sys.stderr)
        # NEVER browser.close() here. This browser belongs to the user
        # and they are still using it -- closing it would discard their
        # session and, on a brokerage site, quite possibly their
        # patience. Dropping the connection is all that is wanted.
        try:
            playwright.stop()
        except Exception as exc:  # noqa: BLE001 -- teardown must not mask
            print(f"[recon] playwright.stop() raised: {exc}", file=sys.stderr)

    _report(capture, dump_path)
    return 0


def run_recon(args: argparse.Namespace, credentials: FidelityCredentials | None) -> int:
    # Imported here, not at module scope, so that `--help` and the unit
    # tests work without playwright or fidelity-api installed. Those are
    # optional dependencies (requirements-fidelity.txt), absent from the
    # Docker image and from every backtest environment.
    try:
        # NOT `from fidelity import FidelityAutomation`. fidelity-api's
        # package __init__.py is only:
        #     from . import fidelity
        #     __all__ = ["fidelity"]
        # It never re-exports the class, so the package-level import
        # raises ImportError even when fidelity-api is installed
        # perfectly. This was found the hard way -- the short form was
        # written from the plan rather than from the installed package,
        # and the first real run failed on it.
        from fidelity.fidelity import FidelityAutomation
    except ImportError as exc:
        # The underlying error is interpolated deliberately. The previous
        # version reported a flat "fidelity-api is not installed", which
        # is exactly what it said when the package WAS installed and only
        # the import path was wrong -- sending the reader off to reinstall
        # a dependency that was already there. Never hide the cause.
        raise ConfigurationError(
            f"Could not import FidelityAutomation from fidelity-api: {exc}\n"
            "If the package is genuinely missing, it is an opt-in dependency:\n"
            "    pip install -r requirements-fidelity.txt\n"
            "    playwright install firefox"
        ) from exc

    artifact_dir = _prepare_artifact_dir(args.artifact_dir)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    dump_path = artifact_dir / f"recon_{stamp}.json"

    capture = TrafficCapture(
        secret_values=credentials.secret_values() if credentials is not None else ()
    )

    fid = FidelityAutomation(
        headless=args.headless,
        # Hard-wired, not exposed as arguments -- see module docstring.
        debug=False,
        save_state=False,
        profile_path=str(artifact_dir),
    )

    try:
        if args.manual_login:
            # CAPTURE IS ATTACHED AFTER LOGIN HERE, AND THAT INVERSION IS
            # THE WHOLE POINT. In the credentialed path below, attaching
            # first is safe because we hold the exact secret strings and
            # TrafficCapture scrubs them out of every recorded payload.
            # In manual mode we deliberately never learn the password --
            # which is the entire security benefit -- so we could not
            # scrub it if we captured the login POST that carries it.
            # Recording a credential we cannot redact would be strictly
            # worse than not recording it.
            #
            # Nothing of value is lost: all three reconnaissance
            # questions (submit round-trip IDs, an orders-list endpoint,
            # a client-reference field) concern traffic AFTER
            # authentication. The login round-trip was never the target.
            print(
                "[recon] manual login: opening Fidelity's sign-in page...",
                file=sys.stderr,
            )
            fid.page.goto(url=FIDELITY_LOGIN_URL)
            landed = _wait_for_manual_login(fid.context, args.login_timeout)
            # attach_context, not attach(page): the login may well have
            # moved the human to a page that did not exist when this run
            # started, and any later tab must be captured too.
            capture.attach_context(fid.context)
            print(
                f"[recon] capture attached to {capture.attached_page_count} page(s) "
                "(post-login, so no password is recorded).",
                file=sys.stderr,
            )
            # The library drives the classic UI, but Trader+ is a
            # different front end with its own API surface, and it is
            # the one an active trader actually uses. Visiting it is the
            # cheapest way to find out whether it exposes the
            # order/position endpoints the classic pages do not -- which
            # is reconnaissance question 2, the one worth the most.
            if args.visit_traderplus:
                try:
                    print(
                        f"[recon] visiting Trader+ ({TRADERPLUS_URL})...",
                        file=sys.stderr,
                    )
                    landed.goto(url=TRADERPLUS_URL)
                    landed.wait_for_load_state("networkidle")
                except Exception as exc:  # noqa: BLE001 -- recon must not die here
                    print(
                        f"[recon] Trader+ visit did not complete: {exc}",
                        file=sys.stderr,
                    )
                # Give any lazily-loaded XHR/WebSocket traffic a moment
                # to arrive; networkidle can fire before a socket opens.
                try:
                    landed.wait_for_timeout(args.settle_ms)
                except Exception:  # noqa: BLE001
                    pass
        else:
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
    print(
        f"frames={summary['frames']} responses={summary['responses']} "
        f"attached_pages={capture.attached_page_count}"
    )
    # An empty dump has two completely different causes that look
    # identical in the file: "Fidelity sent nothing" and "we were not
    # listening". The first real run produced the second and was read as
    # the first. Say which it was.
    if capture.attached_page_count == 0:
        print(
            "  NOTE: capture was never attached to any page, so an empty result "
            "here says nothing about what Fidelity sends."
        )
    elif not summary["frames"] and not summary["responses"]:
        print(
            f"  NOTE: attached to {capture.attached_page_count} page(s) and still "
            "recorded nothing -- that IS a finding about the traffic, not a "
            "wiring failure."
        )
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
        if args.cdp_url:
            # No credentials, no library, no launched browser -- see
            # run_cdp_recon's docstring. --account is still required by
            # the parser, but nothing here selects or acts on an account:
            # the human drives their own browser, and this only listens.
            return run_cdp_recon(args)
        if args.manual_login:
            # Not merely "credentials are optional here" -- they are never
            # read at all, so a stale or wrong FIDELITY_PASSWORD in the
            # environment cannot be picked up and cannot be sent anywhere.
            # The human types into the browser directly.
            #
            # Forced visible: you cannot type into a headless browser, and
            # silently honouring --headless would hang until --login-timeout
            # with no indication of why.
            if args.headless:
                print(
                    "[recon] --manual-login implies a visible browser; "
                    "ignoring the headless default.",
                    file=sys.stderr,
                )
                args.headless = False
            credentials = None
        else:
            credentials = load_fidelity_credentials()
        return run_recon(args, credentials)
    except ConfigurationError as exc:
        print(f"[recon] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
