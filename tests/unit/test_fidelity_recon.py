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

import json
import os
import sys
from pathlib import Path

import pytest

import fidelity_recon
from src.exceptions import ConfigurationError
from src.secrets import FidelityCredentials


class FakePage:
    def __init__(self) -> None:
        self.handlers: dict[str, list] = {}

    def on(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)


class FakeFidelityAutomation:
    """Records every call so the tests can assert on what was asked of it."""

    instances: list[FakeFidelityAutomation] = []

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.page = FakePage()
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
    """Inject a fake `fidelity` module for run_recon's deferred import."""
    FakeFidelityAutomation.instances = []
    module = type(sys)("fidelity")
    module.FidelityAutomation = FakeFidelityAutomation
    monkeypatch.setitem(sys.modules, "fidelity", module)
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

    sys.modules["fidelity"].FidelityAutomation = NoAccounts
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

    sys.modules["fidelity"].FidelityAutomation = FailedLogin
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

    sys.modules["fidelity"].FidelityAutomation = Ordered
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

    sys.modules["fidelity"].FidelityAutomation = Chatty
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
    """The module is imported at the top of this file and playwright is
    not installed in this environment -- so reaching here proves it. The
    Docker image installs only requirements.txt."""
    assert "playwright" not in sys.modules
    assert fidelity_recon.main is not None


def test_a_missing_fidelity_api_gives_an_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "fidelity", None)
    with pytest.raises(ConfigurationError, match="requirements-fidelity.txt"):
        fidelity_recon.run_recon(_args(tmp_path), CREDENTIALS)
