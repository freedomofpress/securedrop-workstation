import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from securedrop_tor_browser import core, session

ONION_HOSTNAME = f"{'a' * 56}.onion"


class FakeProcess:
    def __init__(self, returncode: int | None = None) -> None:
        self.returncode = returncode
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        assert timeout is not None
        assert self.returncode is not None
        return self.returncode


def write_bundle_layout(state_root: Path) -> None:
    browser = state_root / "browser" / "Browser"
    baseline = browser / "TorBrowser" / "Data" / "Browser" / "profile.default"
    baseline.mkdir(parents=True)
    (baseline / "baseline-marker").write_text("pristine")
    tor = browser / "TorBrowser" / "Tor" / "tor"
    tor.parent.mkdir(parents=True, exist_ok=True)
    tor.write_text("tor")
    tor.chmod(0o755)
    firefox = browser / "firefox.real"
    firefox.write_text("firefox")
    firefox.chmod(0o755)


def test_managed_policy_has_read_only_navigation_and_disables_internal_updates() -> None:
    policy = core.managed_browser_policy(ONION_HOSTNAME)
    policies = policy["policies"]

    assert policies["DisableAppUpdate"] is True
    assert policies["Homepage"] == {
        "URL": f"http://{ONION_HOSTNAME}",
        "Locked": True,
        "StartPage": "homepage-locked",
    }
    assert policies["ManagedBookmarks"] == [
        {"toplevel_name": "SecureDrop"},
        {
            "name": "Journalist Interface",
            "url": f"http://{ONION_HOSTNAME}",
        },
    ]


def test_packaged_policy_template_is_valid_json_with_managed_urls() -> None:
    template = Path("files/tor-browser-policies.json.j2").read_text()
    rendered = template.replace("{{ onion_hostname }}", ONION_HOSTNAME)

    assert json.loads(rendered) == core.managed_browser_policy(ONION_HOSTNAME)


def test_apparmor_assets_separate_tor_secrets_from_ephemeral_browser_state() -> None:
    tor_profile = Path("files/tor-browser-tor.apparmor").read_text()
    firefox_profile = Path("files/tor-browser-firefox.apparmor").read_text()
    torrc = Path("files/tor-browser-torrc").read_text()

    assert f"profile {session.TOR_PROFILE_NAME} " in tor_profile
    assert f"profile {session.FIREFOX_PROFILE_NAME} " in firefox_profile
    assert "/home/user/.local/share/securedrop-tor-browser/onion-auth/ r," in tor_profile
    assert "app-journalist.auth_private r," in tor_profile
    assert "deny /home/user/.local/share/securedrop-tor-browser/onion-auth/** r," in firefox_profile
    assert "network inet stream," in tor_profile
    assert "network unix stream," in tor_profile
    assert "network inet stream," not in firefox_profile
    assert "/etc/firefox/policies/policies.json r," in firefox_profile
    assert (
        "/home/user/.local/share/securedrop-tor-browser/browser/Browser/** rixm," in firefox_profile
    )
    assert "deny owner @{HOME}/.Private/{,**} rwklmx," in firefox_profile
    assert (
        "deny owner @{HOME}/{.ICEauthority,.Xauthority,.XCompose,.drirc} rwklmx," in firefox_profile
    )
    assert "deny owner @{HOME}/.config/fontconfig/{,**} rwklmx," in firefox_profile
    assert "/run/user/1000/securedrop-tor-browser/** rwkl," in firefox_profile
    assert (
        "deny owner /run/user/1000/securedrop-tor-browser/lifecycle.lock rwkl," in firefox_profile
    )
    assert "deny owner /run/user/1000/securedrop-tor-browser/tor/{,**} rwkl," in firefox_profile
    assert "/home/user/**" not in firefox_profile.replace(
        "/home/user/.local/share/securedrop-tor-browser", ""
    )
    assert "/dev/shm/" not in firefox_profile
    assert "SocksPort unix:/run/user/1000/securedrop-tor-browser/socks.socket" in torrc
    assert "ControlPort unix:/run/user/1000/securedrop-tor-browser/control.socket" in torrc
    assert "CookieAuthFile /run/user/1000/securedrop-tor-browser/control.authcookie" in torrc
    assert "control.authcookie.tmp" in tor_profile


def test_session_copies_pristine_profile_supervises_confined_processes_and_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_root = tmp_path / "state"
    write_bundle_layout(state_root)
    torrc = tmp_path / "torrc"
    torrc.write_text("managed")
    xauthority = tmp_path / "source-xauthority"
    xauthority.write_text("cookie")
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.setenv("XAUTHORITY", str(xauthority))

    calls: list[tuple[list[str], dict[str, Any]]] = []
    tor_process = FakeProcess()
    browser_process = FakeProcess(0)

    def popen(command: list[str], **kwargs: Any) -> FakeProcess:
        calls.append((command, kwargs))
        if len(calls) == 1:
            runtime = session.RUNTIME_ROOT
            (runtime / session.SOCKS_SOCKET_NAME).touch()
            (runtime / session.CONTROL_SOCKET_NAME).touch()
            (runtime / session.CONTROL_COOKIE_NAME).touch()
            return tor_process
        return browser_process

    result = session.run_browser_session(
        {"torrc_path": str(torrc)},
        state_root,
        popen=popen,
        sleep=lambda _seconds: None,
    )

    assert result == 0
    assert len(calls) == 2
    tor_command, tor_options = calls[0]
    browser_command, browser_options = calls[1]
    assert tor_command == [
        str(session.AA_EXEC_PATH),
        f"--profile={session.TOR_PROFILE_NAME}",
        "--",
        str(state_root / "browser/Browser/TorBrowser/Tor/tor"),
        "-f",
        str(torrc),
    ]
    assert browser_command == [
        str(session.AA_EXEC_PATH),
        f"--profile={session.FIREFOX_PROFILE_NAME}",
        "--",
        str(state_root / "browser/Browser/firefox.real"),
        "--no-remote",
        "--profile",
        str(session.RUNTIME_ROOT / "profile"),
    ]
    assert tor_options["cwd"] == state_root / "browser/Browser"
    assert tor_options["stdout"] is subprocess.DEVNULL
    assert tor_options["stderr"] is subprocess.DEVNULL
    browser_environment = browser_options["env"]
    assert browser_environment["TOR_SKIP_LAUNCH"] == "1"
    assert browser_environment["TOR_SOCKS_IPC_PATH"].endswith(session.SOCKS_SOCKET_NAME)
    assert browser_environment["TOR_CONTROL_IPC_PATH"].endswith(session.CONTROL_SOCKET_NAME)
    assert browser_environment["HOME"].startswith(str(session.RUNTIME_ROOT))
    assert browser_environment["DISPLAY"] == ":1"
    assert browser_environment["XAUTHORITY"].startswith(str(session.RUNTIME_ROOT))
    assert browser_options["stdout"] is subprocess.DEVNULL
    assert browser_options["stderr"] is subprocess.DEVNULL
    assert ONION_HOSTNAME not in " ".join(browser_command)
    assert tor_process.terminated
    assert list(session.RUNTIME_ROOT.iterdir()) == []
    baseline_marker = (
        state_root / "browser/Browser/TorBrowser/Data/Browser/profile.default/baseline-marker"
    )
    assert baseline_marker.is_file()
    captured = capsys.readouterr()
    assert captured.out == ""
    messages = [line.split(": ", 1)[1] for line in captured.err.splitlines()]
    assert messages == [
        "confinement launch configuration verified",
        "bundled Tor starting",
        "bundled Tor is ready",
        "browser starting",
        "browser exited with status 0",
        "session cleanup starting",
        "session cleanup completed",
    ]
    assert ONION_HOSTNAME not in captured.err
    assert str(torrc) not in captured.err
    assert str(xauthority) not in captured.err
    assert "--profile" not in captured.err
    assert "DISPLAY" not in captured.err


def test_session_fails_closed_before_firefox_when_tor_does_not_create_managed_sockets(
    tmp_path: Path,
) -> None:
    state_root = tmp_path / "state"
    write_bundle_layout(state_root)
    torrc = tmp_path / "torrc"
    torrc.write_text("managed")
    calls = 0
    tor_process = FakeProcess(1)

    def popen(_command: list[str], **_kwargs: Any) -> FakeProcess:
        nonlocal calls
        calls += 1
        return tor_process

    with pytest.raises(session.SessionError, match="Tor exited before"):
        session.run_browser_session(
            {"torrc_path": str(torrc)},
            state_root,
            popen=popen,
            sleep=lambda _seconds: None,
        )

    assert calls == 1
    assert list(session.RUNTIME_ROOT.iterdir()) == []


def test_session_uses_only_a_small_environment_allowlist(tmp_path: Path) -> None:
    environment = session.browser_environment(
        tmp_path,
        inherited={
            "DISPLAY": ":1",
            "LANG": "en_US.UTF-8",
            "SSH_AUTH_SOCK": "/run/user/1000/keyring/ssh",
            "SECRET_TOKEN": "do-not-inherit",
        },
    )

    assert environment["DISPLAY"] == ":1"
    assert environment["LANG"] == "en_US.UTF-8"
    assert "SSH_AUTH_SOCK" not in environment
    assert "SECRET_TOKEN" not in environment
    assert environment["PATH"] == os.defpath


def test_session_attempts_all_cleanup_and_reports_process_stop_failure(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    write_bundle_layout(state_root)
    torrc = tmp_path / "torrc"
    torrc.write_text("managed")
    tor_process = FakeProcess()

    class StopFailureProcess(FakeProcess):
        def __init__(self) -> None:
            super().__init__()
            self.poll_results = iter((0, None, None))

        def poll(self) -> int | None:
            return next(self.poll_results, None)

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, timeout: float | None = None) -> int:
            raise subprocess.TimeoutExpired("firefox", timeout)

    browser_process = StopFailureProcess()
    calls = 0

    def popen(_command: list[str], **_kwargs: Any) -> FakeProcess:
        nonlocal calls
        calls += 1
        if calls == 1:
            runtime = session.RUNTIME_ROOT
            (runtime / session.SOCKS_SOCKET_NAME).touch()
            (runtime / session.CONTROL_SOCKET_NAME).touch()
            (runtime / session.CONTROL_COOKIE_NAME).touch()
            return tor_process
        return browser_process

    with pytest.raises(session.SessionError, match="cleanup"):
        session.run_browser_session(
            {"torrc_path": str(torrc)},
            state_root,
            popen=popen,
            sleep=lambda _seconds: None,
        )

    assert browser_process.terminated
    assert browser_process.killed
    assert tor_process.terminated
    assert list(session.RUNTIME_ROOT.iterdir()) == []


def test_session_reports_mutable_profile_removal_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_root = tmp_path / "state"
    write_bundle_layout(state_root)
    torrc = tmp_path / "torrc"
    torrc.write_text("managed")
    tor_process = FakeProcess()
    browser_process = FakeProcess(0)
    calls = 0

    def popen(_command: list[str], **_kwargs: Any) -> FakeProcess:
        nonlocal calls
        calls += 1
        if calls == 1:
            runtime = session.RUNTIME_ROOT
            (runtime / session.SOCKS_SOCKET_NAME).touch()
            (runtime / session.CONTROL_SOCKET_NAME).touch()
            (runtime / session.CONTROL_COOKIE_NAME).touch()
            return tor_process
        return browser_process

    def fail_removal(_path: Path) -> None:
        raise PermissionError("managed profile is busy")

    monkeypatch.setattr(session.shutil, "rmtree", fail_removal)

    with pytest.raises(session.SessionError, match="cleanup"):
        session.run_browser_session(
            {"torrc_path": str(torrc)},
            state_root,
            popen=popen,
            sleep=lambda _seconds: None,
        )

    assert tor_process.terminated
    assert session.RUNTIME_ROOT.exists()
