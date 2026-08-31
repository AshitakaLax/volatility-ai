"""Safety tests for fidelity_recon.py -- the step-1 reconnaissance harness.

Nothing here touches a browser, a network, or a real account. A fake
`fidelity` module is injected into sys.modules so that `run_recon`'s
deferred import resolves to a double, which lets the whole flow be driven
end to end while asserting the properties that actually matter:

  * transaction() is NEVER called with dry=False. Not "defaults to True" --
    never called otherwise, at all.
  * The library is constructed with debug=False and save_state=False, the
    two settings that write credentials to disk.
  * An account that does not match EXACTLY is refused before any
    transaction call happens.

These are the tests that would catch a regression turning a read-only
recon script into one that can place a real order.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import fidelity_recon
from src.exceptions import ConfigurationError
from src.secrets import FidelityCredentials


class FakePage:
    def __init__(self) -> None:
        self.handlers: dict[str, list] = {}
        self.goto_urls: list[str] = []
        self.load_state_waits = 0
        # url_sequence lets a manual-login test drive the page from the
        # sign-in page to a signed-in one. Each read of `.url` advances
        # by one until the last entry, which then repeats -- so a test
        # can say "still signing in, still signing in, now done".
        self.url_sequence: list[str] = [
            "https://digital.fidelity.com/ftgw/digital/portfolio/summary"
        ]
        self._url_reads = 0
        # Snapshot of how much had happened at the moment capture
        # attached, so a test can prove ordering rather than infer it.
        self.attached_after_gotos: int | None = None

    @property
    def url(self) -> str:
        value = self.url_sequence[min(self._url_reads, len(self.url_sequence) - 1)]
        self._url_reads += 1
        return value

    def goto(self, url=None, **kwargs):
        self.goto_urls.append(url)

    def wait_for_load_state(self, *args, **kwargs):
        self.load_state_waits += 1

    def wait_for_timeout(self, ms):
        self.settle_ms = ms

    def on(self, event, handler):
        if self.attached_after_gotos is None:
            self.attached_after_gotos = len(self.goto_urls)
        self.handlers.setdefault(event, []).append(handler)


class FakeContext:
    """Mirrors the BrowserContext surface the script actually uses.

    Exists because the real bug was invisible without it: the script
    used to watch a single page, and the fake only had a single page, so
    the fake could not express the situation that broke a real run --
    login moving the human to a DIFFERENT page while the original sat on
    the sign-in URL forever.
    """

    def __init__(self, *pages):
        self.pages = list(pages)
        self.handlers: dict[str, list] = {}

    def on(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)

    def open_page(self, page):
        """Simulate a new tab appearing, as a login redirect does."""
        self.pages.append(page)
        for handler in self.handlers.get("page", []):
            handler(page)
        return page


class FakeFidelityAutomation:
    """Records every call so the tests can assert on what was asked of it."""

    instances: list[FakeFidelityAutomation] = []

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.page = FakePage()
        self.context = FakeContext(self.page)
        self.transactions: list[dict] = []
        self.closed = False
        self.accounts = {"Z12345678": {"withdrawal_balance": 1000.0}}
        self.login_result = (True, True)
        self.transaction_result = (True, None)
        FakeFidelityAutomation.instances.append(self)

    def login(self, **kwargs):
        self.login_kwargs = kwargs
        return self.login_result

    def get_list_of_accounts(self, **kwargs):
        self.list_accounts_kwargs = kwargs
        return self.accounts

    def transaction(self, **kwargs):
        self.transactions.append(kwargs)
        return self.transaction_result

    def close_browser(self):
        self.closed = True


@pytest.fixture
def fake_fidelity(monkeypatch):
    """Inject a fake `fidelity` package for run_recon's deferred import.

    MIRRORS THE REAL PACKAGE LAYOUT, and that matters. fidelity-api ships
    a package whose __init__.py is only `from . import fidelity` with
    __all__ = ["fidelity"] -- the class lives in the `fidelity.fidelity`
    SUBMODULE and is never re-exported at package level.

    An earlier version of this fixture registered a single flat module
    exposing FidelityAutomation directly, which made
    `from fidelity import FidelityAutomation` pass here while failing
    against the real library. The double was shaped to the assumption
    instead of to the package, so the entire suite went green on an
    import that could not work -- and the bug surfaced only on the first
    real run. Registering both names keeps the double honest.
    """
    FakeFidelityAutomation.instances = []
    package = type(sys)("fidelity")
    submodule = type(sys)("fidelity.fidelity")
    submodule.FidelityAutomation = FakeFidelityAutomation
    package.fidelity = submodule
    monkeypatch.setitem(sys.modules, "fidelity", package)
    monkeypatch.setitem(sys.modules, "fidelity.fidelity", submodule)
    return FakeFidelityAutomation


CREDENTIALS = FidelityCredentials(
    username="bob", password="hunter2", totp_secret="SEED"
)


def _args(tmp_path: Path, **overrides):
    argv = [
        "--account",
        "Z12345678",
        "--artifact-dir",
        str(tmp_path),
        "--i-understand-this-logs-into-my-real-brokerage-account",
    ]
    for key, value in overrides.items():
        flag = "--" + key.replace("_", "-")
        argv.append(flag)
        if value is not None:
            argv.append(str(value))
    return fidelity_recon.parse_args(argv)


# -- the script cannot place an order ----------------------------------


def test_transaction_is_only_ever_called_with_dry_true(fake_fidelity, tmp_path):
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)

    fid = fake_fidelity.instances[0]
    assert len(fid.transactions) == 1
    assert fid.transactions[0]["dry"] is True


def test_no_source_path_can_set_dry_false():
    """Structural, not behavioral: the capability must be ABSENT rather
    than defaulted-off. A grep is the honest way to assert that."""
    source = Path(fidelity_recon.__file__).read_text(encoding="utf-8")
    code_lines = [
        line
        for line in source.splitlines()
        if "dry=False" in line and not line.strip().startswith("#")
    ]
    assert code_lines == []


def test_dry_run_is_passed_explicitly_not_left_to_the_library_default(
    fake_fidelity, tmp_path
):
    """An upstream change to transaction()'s default must not silently
    flip this script into submitting orders."""
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)
    assert "dry" in fake_fidelity.instances[0].transactions[0]


def test_skip_preview_opens_no_order_ticket_at_all(fake_fidelity, tmp_path):
    args = _args(tmp_path)
    args.skip_preview = True
    fidelity_recon.run_recon(args, CREDENTIALS)

    assert fake_fidelity.instances[0].transactions == []


# -- credential-to-disk hardening --------------------------------------


def test_library_is_constructed_with_credential_writes_disabled(
    fake_fidelity, tmp_path
):
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)

    kwargs = fake_fidelity.instances[0].init_kwargs
    # debug=True writes the password to ./fidelity_trace*.zip in cleartext.
    assert kwargs["debug"] is False
    # save_state=True dumps the authenticated session's cookies to disk.
    assert kwargs["save_state"] is False


def test_profile_path_is_the_artifact_dir_not_the_repo(fake_fidelity, tmp_path):
    """Defense in depth for save_state: if that guard ever regresses
    upstream, the file must land somewhere private rather than somewhere
    committable."""
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)

    profile_path = Path(fake_fidelity.instances[0].init_kwargs["profile_path"])
    assert profile_path == tmp_path
    assert Path.cwd() not in profile_path.parents
    assert profile_path != Path.cwd()


def test_debug_and_save_state_are_not_exposed_as_arguments():
    """They are not decisions a caller of a recon script should make."""
    parser_help = fidelity_recon.parse_args(
        ["--account", "Z1", "--i-understand-this-logs-into-my-real-brokerage-account"]
    )
    assert not hasattr(parser_help, "debug")
    assert not hasattr(parser_help, "save_state")


def test_a_2fa_bypass_token_is_never_persisted(fake_fidelity, tmp_path):
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)
    assert fake_fidelity.instances[0].login_kwargs["save_device"] is False


# -- account allowlist -------------------------------------------------


def test_an_account_absent_from_the_list_is_refused(fake_fidelity, tmp_path):
    args = _args(tmp_path)
    args.account = "Z99999999"

    with pytest.raises(ConfigurationError, match="not present"):
        fidelity_recon.run_recon(args, CREDENTIALS)

    assert fake_fidelity.instances[0].transactions == []


def test_a_substring_of_a_real_account_is_refused(fake_fidelity, tmp_path):
    """The library selects accounts by case-insensitive SUBSTRING match on
    dropdown text, so a truncated number could uniquely match the WRONG
    account. Exact match, enforced here, before it ever gets there."""
    args = _args(tmp_path)
    args.account = "Z1234"

    with pytest.raises(ConfigurationError, match="not present"):
        fidelity_recon.run_recon(args, CREDENTIALS)


def test_a_case_variant_of_a_real_account_is_refused(fake_fidelity, tmp_path):
    args = _args(tmp_path)
    args.account = "z12345678"

    with pytest.raises(ConfigurationError, match="not present"):
        fidelity_recon.run_recon(args, CREDENTIALS)


def test_accounts_are_enumerated_with_withdrawal_balances(fake_fidelity, tmp_path):
    """account_dict[acct]["balance"] is a live upstream bug -- it holds one
    arbitrary position's value, not the balance."""
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)
    assert fake_fidelity.instances[0].list_accounts_kwargs["get_withdrawal_bal"] is True


def test_an_empty_account_list_refuses_rather_than_proceeding(fake_fidelity, tmp_path):
    args = _args(tmp_path)
    FakeFidelityAutomation.instances = []
    fid_holder = {}

    class NoAccounts(FakeFidelityAutomation):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.accounts = None
            fid_holder["fid"] = self

    sys.modules["fidelity.fidelity"].FidelityAutomation = NoAccounts
    with pytest.raises(ConfigurationError, match="not present"):
        fidelity_recon.run_recon(args, CREDENTIALS)
    assert fid_holder["fid"].transactions == []


# -- login failure -----------------------------------------------------


def test_a_failed_login_stops_before_any_account_work(fake_fidelity, tmp_path):
    FakeFidelityAutomation.instances = []

    class FailedLogin(FakeFidelityAutomation):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.login_result = (False, False)

    sys.modules["fidelity.fidelity"].FidelityAutomation = FailedLogin
    with pytest.raises(ConfigurationError, match="Login failed"):
        fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)


# -- capture wiring ----------------------------------------------------


def test_capture_is_attached_before_login(fake_fidelity, tmp_path):
    """Playwright only delivers events for activity after a listener is
    registered, so attaching after login would miss the login round-trip
    -- and the constructor launches the browser WITHOUT navigating, which
    is what makes attaching first possible."""
    order: list[str] = []

    FakeFidelityAutomation.instances = []

    class Ordered(FakeFidelityAutomation):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            outer = self

            class RecordingPage(FakePage):
                def on(self, event, handler):
                    order.append("attach")
                    super().on(event, handler)

            outer.page = RecordingPage()

        def login(self, **kwargs):
            order.append("login")
            return super().login(**kwargs)

    sys.modules["fidelity.fidelity"].FidelityAutomation = Ordered
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)

    assert order.index("attach") < order.index("login")


# -- the dump ----------------------------------------------------------


def test_the_dump_is_written(fake_fidelity, tmp_path):
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)

    dumps = list(tmp_path.glob("recon_*.json"))
    assert len(dumps) == 1
    payload = json.loads(dumps[0].read_text(encoding="utf-8"))
    assert "frames" in payload
    assert "responses" in payload
    assert "summary" in payload


def test_the_dump_is_written_even_when_the_run_fails(fake_fidelity, tmp_path):
    """A run that broke halfway still captured the traffic up to the
    break, and that traffic is the entire point of the exercise."""
    args = _args(tmp_path)
    args.account = "Z99999999"

    with pytest.raises(ConfigurationError):
        fidelity_recon.run_recon(args, CREDENTIALS)

    assert len(list(tmp_path.glob("recon_*.json"))) == 1


def test_the_browser_is_closed_even_when_the_run_fails(fake_fidelity, tmp_path):
    args = _args(tmp_path)
    args.account = "Z99999999"

    with pytest.raises(ConfigurationError):
        fidelity_recon.run_recon(args, CREDENTIALS)

    assert fake_fidelity.instances[0].closed is True


@pytest.mark.skipif(
    os.name == "nt", reason="POSIX mode bits are not meaningful on NTFS"
)
def test_the_dump_is_private_to_this_user(fake_fidelity, tmp_path):
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)

    dump = next(tmp_path.glob("recon_*.json"))
    assert dump.stat().st_mode & 0o077 == 0


def test_credentials_never_reach_the_dump(fake_fidelity, tmp_path):
    """End-to-end: drive real traffic through the capture the harness
    attached, then read the file off disk."""
    FakeFidelityAutomation.instances = []

    class Chatty(FakeFidelityAutomation):
        def login(self, **kwargs):
            for handler in self.page.handlers.get("response", []):

                class Resp:
                    url = "https://digital.fidelity.com/login"
                    status = 200
                    request = type("R", (), {"method": "POST", "resource_type": "xhr"})()

                    def text(self):
                        return "username=bob&password=hunter2&totp=SEED"

                handler(Resp())
            return super().login(**kwargs)

    sys.modules["fidelity.fidelity"].FidelityAutomation = Chatty
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)

    text = next(tmp_path.glob("recon_*.json")).read_text(encoding="utf-8")
    assert "hunter2" not in text
    assert "SEED" not in text


# -- the confirmation gate ---------------------------------------------


def test_main_refuses_without_the_confirmation_flag(capsys):
    exit_code = fidelity_recon.main(["--account", "Z12345678"])
    assert exit_code == 2
    assert "Refusing to run" in capsys.readouterr().err


def test_parse_args_requires_an_account():
    with pytest.raises(SystemExit):
        fidelity_recon.parse_args([])


# -- optional dependency -----------------------------------------------


def test_importing_the_module_does_not_require_playwright():
    """The property under test is that fidelity_recon's OWN imports stay
    free of playwright, so it works in the Docker image (which installs
    only requirements.txt).

    Checked in a fresh interpreter rather than by inspecting this
    process's sys.modules. The original version asserted
    `"playwright" not in sys.modules` and relied on playwright simply
    being absent from the environment -- which stopped being true the
    moment the Fidelity extras were installed, and was in any case
    polluted by any earlier test that imported playwright
    (test_retry_policy.py does, via _broker_error_types). That made a
    passing result depend on install state and test ordering rather than
    on the thing actually being asserted.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import fidelity_recon, sys; "
            "print('LOADED' if 'playwright' in sys.modules else 'CLEAN')",
        ],
        capture_output=True,
        text=True,
        cwd=Path(fidelity_recon.__file__).parent,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "CLEAN", (
        "importing fidelity_recon pulled playwright in at module scope -- it must "
        "stay a deferred import inside run_recon"
    )


def test_a_missing_fidelity_api_gives_an_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "fidelity", None)
    with pytest.raises(ConfigurationError, match="requirements-fidelity.txt"):
        fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)


# -- manual login: the human types, the script never learns the password --

SIGNIN = "https://digital.fidelity.com/prgw/digital/signin/retail"
SIGNED_IN = "https://digital.fidelity.com/ftgw/digital/portfolio/summary"


def _manual_args(tmp_path: Path, **overrides):
    argv = [
        "--account",
        "Z12345678",
        "--artifact-dir",
        str(tmp_path),
        "--manual-login",
        "--i-understand-this-logs-into-my-real-brokerage-account",
    ]
    for key, value in overrides.items():
        argv.append("--" + key.replace("_", "-"))
        if value is not None:
            argv.append(str(value))
    return fidelity_recon.parse_args(argv)


def test_manual_login_never_calls_login(fake_fidelity, tmp_path):
    """The credentialed path is not merely skipped by convention -- the
    library's login() must never be invoked, because invoking it is what
    would require a password to exist."""
    args = _manual_args(tmp_path)
    args.headless = False
    fidelity_recon.run_recon(args, None)
    fid = fake_fidelity.instances[-1]
    assert not hasattr(fid, "login_kwargs"), "login() was called in manual mode"
    assert SIGNIN in fid.page.goto_urls


def test_manual_login_reads_no_credentials_at_all(monkeypatch, fake_fidelity, tmp_path):
    """A stale FIDELITY_PASSWORD in the environment must not be picked
    up -- not loaded, not scrubbed against, not sent anywhere."""
    called = []
    monkeypatch.setattr(
        fidelity_recon, "load_fidelity_credentials", lambda: called.append(1)
    )
    fidelity_recon.main(
        [
            "--account",
            "Z12345678",
            "--artifact-dir",
            str(tmp_path),
            "--manual-login",
            "--i-understand-this-logs-into-my-real-brokerage-account",
        ]
    )
    assert called == [], "credentials were loaded despite --manual-login"


def test_capture_attaches_only_after_the_login_page_is_left(fake_fidelity, tmp_path):
    """THE security property of this mode. We never learn the password,
    so we could not scrub it from a captured login POST -- therefore the
    login round-trip must not be captured at all. Attaching after the
    navigation to the sign-in page proves the ordering."""
    args = _manual_args(tmp_path)
    args.headless = False
    fidelity_recon.run_recon(args, None)
    page = fake_fidelity.instances[-1].page
    assert page.attached_after_gotos == 1, (
        "capture attached before the sign-in navigation -- the login POST "
        "carrying the password would be recorded unredacted"
    )


def test_the_credentialed_path_still_attaches_before_login(fake_fidelity, tmp_path):
    """Contrast, so the inversion above cannot silently spread: with
    credentials we DO hold the secret strings and can scrub them, so
    capturing the whole session including login stays correct."""
    fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)
    page = fake_fidelity.instances[-1].page
    assert page.attached_after_gotos == 0


def test_manual_login_still_cannot_place_an_order(fake_fidelity, tmp_path):
    args = _manual_args(tmp_path)
    args.headless = False
    fidelity_recon.run_recon(args, None)
    for call in fake_fidelity.instances[-1].transactions:
        assert call["dry"] is True


def test_manual_login_forces_a_visible_browser(fake_fidelity, tmp_path, capsys):
    """You cannot type into a headless browser. Honouring the headless
    default would hang until the timeout with no stated reason."""
    fidelity_recon.main(
        [
            "--account",
            "Z12345678",
            "--artifact-dir",
            str(tmp_path),
            "--manual-login",
            "--i-understand-this-logs-into-my-real-brokerage-account",
        ]
    )
    assert fake_fidelity.instances[-1].init_kwargs["headless"] is False
    assert "visible browser" in capsys.readouterr().err


def test_manual_login_waits_while_still_on_the_signin_page(fake_fidelity, tmp_path):
    args = _manual_args(tmp_path)
    args.headless = False
    fid_page_urls = [SIGNIN, SIGNIN, SIGNIN, SIGNED_IN]

    def _make(**kwargs):
        inst = FakeFidelityAutomation(**kwargs)
        inst.page.url_sequence = list(fid_page_urls)
        return inst

    sys.modules["fidelity.fidelity"].FidelityAutomation = _make
    try:
        fidelity_recon.run_recon(args, None)
    finally:
        sys.modules["fidelity.fidelity"].FidelityAutomation = FakeFidelityAutomation
    # It kept reading the URL until the sign-in path went away, rather
    # than proceeding on the first look.
    assert FakeFidelityAutomation.instances[-1].page._url_reads >= 4


def test_manual_login_times_out_with_an_actionable_message(fake_fidelity, tmp_path):
    """A human who walks away must get a stated reason and the knob to
    fix it, not a silent hang."""
    args = _manual_args(tmp_path)
    args.headless = False
    args.login_timeout = 0.2

    def _make(**kwargs):
        inst = FakeFidelityAutomation(**kwargs)
        inst.page.url_sequence = [SIGNIN]  # never leaves the login page
        return inst

    sys.modules["fidelity.fidelity"].FidelityAutomation = _make
    try:
        with pytest.raises(ConfigurationError, match="login-timeout"):
            fidelity_recon.run_recon(args, None)
    finally:
        sys.modules["fidelity.fidelity"].FidelityAutomation = FakeFidelityAutomation


def test_wait_helper_raises_if_every_tab_is_closed():
    """A context with no pages means the human closed the window. That is
    a real answer, not something to keep waiting on."""
    with pytest.raises(ConfigurationError, match="no open pages"):
        fidelity_recon._wait_for_manual_login(FakeContext(), timeout_seconds=5.0)


def test_a_single_dead_tab_does_not_abort_the_wait():
    """One tab raising on .url must not end the wait -- a background tab
    can die while the human is mid-login in another. The earlier version
    treated any raising page as fatal."""

    class DeadTab:
        @property
        def url(self):
            raise RuntimeError("Target page, context or browser has been closed")

    live = FakePage()
    live.url_sequence = [SIGNED_IN]
    context = FakeContext(DeadTab(), live)
    assert fidelity_recon._wait_for_manual_login(context, timeout_seconds=5.0) is live


def test_login_is_detected_on_a_tab_that_did_not_exist_at_start():
    """THE regression this whole change exists for. Fidelity's sign-in
    moved the human to a different page; the original sat on the sign-in
    URL forever and the wait timed out after ten minutes beside a
    perfectly good authenticated session."""
    original = FakePage()
    original.url_sequence = [SIGNIN]  # never leaves the login page, ever
    context = FakeContext(original)

    new_tab = FakePage()
    new_tab.url_sequence = [SIGNED_IN]
    context.open_page(new_tab)

    found = fidelity_recon._wait_for_manual_login(context, timeout_seconds=5.0)
    assert found is new_tab, "login on a second tab was not detected"


def test_an_interstitial_is_not_mistaken_for_a_completed_login():
    """Detection requires the POSITIVE authenticated marker. Testing only
    for 'no longer on the sign-in path' would accept about:blank, an
    error page, or a redirect stop-over."""
    page = FakePage()
    page.url_sequence = ["about:blank"]
    with pytest.raises(ConfigurationError, match="Timed out"):
        fidelity_recon._wait_for_manual_login(
            FakeContext(page), timeout_seconds=0.2, poll_seconds=0.05
        )


def test_the_login_url_matches_the_librarys_own():
    """Derived from fidelity.py's login(), not guessed. If upstream moves
    it, this is the single place to correct."""
    assert fidelity_recon.FIDELITY_LOGIN_URL == SIGNIN
    assert fidelity_recon._SIGNIN_PATH_MARKER in SIGNIN
    assert fidelity_recon._SIGNIN_PATH_MARKER not in SIGNED_IN


# -- the import path, checked against the REAL package -------------------

_FIDELITY_INSTALLED = importlib.util.find_spec("fidelity") is not None


@pytest.mark.skipif(
    not _FIDELITY_INSTALLED,
    reason="fidelity-api is an opt-in dependency (requirements-fidelity.txt)",
)
def test_the_import_path_works_against_the_really_installed_package():
    """The test that was missing, and whose absence let a broken import
    ship green.

    Every other test here drives a DOUBLE, so they only ever proved the
    script agrees with the fake. The original code did
    `from fidelity import FidelityAutomation`, the fake exposed exactly
    that, and the suite passed -- while the real package raises
    ImportError, because its __init__.py is only `from . import fidelity`
    and never re-exports the class.

    This asserts against the installed library instead, so a wrong path
    fails here rather than on someone's first real brokerage login. It
    skips cleanly where the optional dependency is absent (the Docker
    image, every backtest environment).
    """
    import ast

    source = Path(fidelity_recon.__file__).read_text(encoding="utf-8")
    imports = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.split(".")[0] == "fidelity"
    ]
    assert imports, "fidelity_recon no longer imports FidelityAutomation at all"

    for node in imports:
        module = importlib.import_module(node.module)
        for alias in node.names:
            assert hasattr(module, alias.name), (
                f"fidelity_recon does `from {node.module} import {alias.name}`, but the "
                f"installed package has no such attribute. Real layout: the class lives "
                f"in the fidelity.fidelity submodule and is NOT re-exported at package level."
            )


def test_a_missing_class_reports_the_real_cause_not_a_reinstall_instruction(
    monkeypatch, tmp_path
):
    """The first failed run said 'fidelity-api is not installed' when it
    WAS installed and only the import path was wrong -- sending the
    reader off to reinstall a dependency already present. The underlying
    ImportError must reach the message."""
    package = type(sys)("fidelity")
    submodule = type(sys)("fidelity.fidelity")  # deliberately has no FidelityAutomation
    package.fidelity = submodule
    monkeypatch.setitem(sys.modules, "fidelity", package)
    monkeypatch.setitem(sys.modules, "fidelity.fidelity", submodule)

    with pytest.raises(ConfigurationError, match="FidelityAutomation") as excinfo:
        fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)
    assert "Could not import" in str(excinfo.value)
