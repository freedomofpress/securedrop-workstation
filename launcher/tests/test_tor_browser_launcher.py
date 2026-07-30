import json
import runpy
import socket
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path
from unittest import mock

import pytest

from securedrop_tor_browser import core, lifecycle, release
from securedrop_tor_browser import main as launcher

FINGERPRINT = "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"
VALID_CREDENTIAL = f"{'a' * 56}.onion" ":descriptor:x25519:" f"{'B' * 52}"


def write_valid_prerequisites(tmp_path: Path) -> Path:
    credential_dir = tmp_path / "auth"
    credential_dir.mkdir()
    credential = credential_dir / "app-journalist.auth_private"
    credential.write_text(VALID_CREDENTIAL + "\n")
    credential.chmod(0o600)

    torrc = tmp_path / "torrc"
    torrc.write_text("ClientOnly 1\n")
    key = tmp_path / "tor-browser-signing-key.asc"
    key.write_text("pinned key")
    minimum_version = tmp_path / "minimum-version"
    minimum_version.write_text("15.0.1\n")
    config = {
        "managed_by": "SecureDrop Workstation",
        "minimum_version": "15.0.1",
        "minimum_version_path": str(minimum_version),
        "minimum_version_sha256": core.sha256_file(minimum_version),
        "onion_auth_dir": str(credential_dir),
        "torrc_path": str(torrc),
        "torrc_sha256": core.sha256_file(torrc),
        "signing_key_path": str(key),
        "signing_key_fingerprint": FINGERPRINT,
        "signing_key_sha256": core.sha256_file(key),
    }
    config_path = tmp_path / "tor-browser.json"
    config_path.write_text(json.dumps(config))
    return config_path


def assert_lifecycle_lock_is_held(state_root: Path) -> None:
    with (
        pytest.raises(lifecycle.LifecycleBusy),
        lifecycle.exclusive_lifecycle(state_root),
    ):
        pytest.fail("the Tor Browser lifecycle lock must remain held")


def test_graphical_error_keeps_application_alive_while_constructing_widget() -> None:
    script = """
from PyQt6.QtWidgets import QWidget
from securedrop_tor_browser import frontend

frontend.QMessageBox.critical = lambda *args: QWidget()
raise SystemExit(frontend.show_error("title", "message"))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        env={"QT_QPA_PLATFORM": "offscreen"},
        text=True,
    )

    assert result.returncode == 1, result.stderr
    assert "Must construct a QApplication" not in result.stderr


def test_lock_contention_message_reports_browser_is_starting_or_running() -> None:
    with (
        mock.patch.object(launcher.frontend, "_application") as application,
        mock.patch.object(launcher.frontend.QMessageBox, "information") as information,
    ):
        assert launcher.frontend.show_already_running() == 0

    assert information.call_args.args[1] == "Tor Browser is starting or running"
    assert "No second session was started" in information.call_args.args[2]
    application.return_value.quit.assert_called_once_with()


def test_packaged_entry_point_invokes_the_launcher():
    with (
        mock.patch("securedrop_tor_browser.main.main", return_value=23) as main,
        pytest.raises(SystemExit, match="23"),
    ):
        runpy.run_path("files/securedrop-tor-browser", run_name="__main__")

    main.assert_called_once_with()


def test_missing_managed_configuration_fails_closed_without_external_activity(tmp_path):
    missing_config = tmp_path / "tor-browser.json"

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", missing_config),
        mock.patch.object(socket, "create_connection") as create_connection,
        mock.patch.object(subprocess, "Popen") as popen,
        pytest.raises(core.ManagedConfigurationError) as exc_info,
    ):
        core.load_managed_config()

    assert str(missing_config) in str(exc_info.value)
    assert "administrator" in str(exc_info.value)
    create_connection.assert_not_called()
    popen.assert_not_called()


def test_launcher_reports_missing_configuration_as_a_graphical_error(tmp_path):
    missing_config = tmp_path / "tor-browser.json"

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", missing_config),
        mock.patch.object(launcher.frontend, "show_error", return_value=1) as show_error,
        mock.patch.object(launcher.frontend, "show_ready") as show_ready,
        mock.patch.object(socket, "create_connection") as create_connection,
        mock.patch.object(subprocess, "Popen") as popen,
    ):
        result = launcher.main()

    assert result == 1
    title, message = show_error.call_args.args
    assert title == "Tor Browser is not configured"
    assert str(missing_config) in message
    assert "administrator" in message
    show_ready.assert_not_called()
    create_connection.assert_not_called()
    popen.assert_not_called()


def test_second_launcher_reports_starting_or_running_without_checking_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    state_root = tmp_path / "state"
    monkeypatch.setattr(launcher.release, "STATE_ROOT", state_root)
    load_config = mock.Mock()
    monkeypatch.setattr(launcher.core, "load_managed_config", load_config)
    already_running = mock.Mock(return_value=0)
    monkeypatch.setattr(launcher.frontend, "show_already_running", already_running)

    with lifecycle.exclusive_lifecycle(state_root):
        assert launcher.main() == 0

    already_running.assert_called_once_with()
    load_config.assert_not_called()


def test_launcher_recovers_abandoned_state_while_holding_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    state_root = tmp_path / "state"
    abandoned_install = state_root / ".install-crashed"
    abandoned_install.mkdir(parents=True)
    abandoned_profile = state_root / lifecycle.RUNTIME_DIRECTORY / "profile-crashed"
    abandoned_profile.mkdir(parents=True)
    installed = state_root / "installations" / "15.0.19-crash-recovered"
    installed.mkdir(parents=True)
    installed_version = installed / ".securedrop-version"
    installed_version.write_text("15.0.19\n")
    active = state_root / "active"
    active.symlink_to(installed)
    high_water = state_root / "highest-version"
    high_water.write_text("15.0.18\n")
    monkeypatch.setattr(launcher.release, "STATE_ROOT", state_root)
    monkeypatch.setattr(launcher.release, "INSTALLED_VERSION_PATH", installed_version)
    monkeypatch.setattr(launcher.release, "HIGH_WATER_VERSION_PATH", high_water)
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )

    def load_config() -> dict[str, str]:
        assert not abandoned_install.exists()
        assert not abandoned_profile.exists()
        assert_lifecycle_lock_is_held(state_root)
        return {"minimum_version": "15.0.1"}

    monkeypatch.setattr(launcher.core, "load_managed_config", load_config)
    monkeypatch.setattr(
        launcher.frontend,
        "metadata_retrieval",
        lambda: nullcontext(lambda: False),
    )
    monkeypatch.setattr(launcher.release, "discover_stable_release", lambda **kwargs: stable)
    ready_versions: list[str] = []

    def show_ready(version: str) -> int:
        assert_lifecycle_lock_is_held(state_root)
        ready_versions.append(version)
        return 0

    monkeypatch.setattr(launcher.frontend, "show_ready", show_ready)

    assert launcher.main() == 0
    assert high_water.read_text() == "15.0.19\n"
    assert ready_versions == ["15.0.19"]


def test_launcher_accepts_valid_prerequisites_without_inspecting_apparmor(tmp_path):
    config_path = write_valid_prerequisites(tmp_path)
    stable = release.StableRelease(
        release.Version("15.0.1"),
        "https://dist.torproject.org/torbrowser/15.0.1/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.1/browser.tar.xz.asc",
    )

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", config_path),
        mock.patch.object(
            launcher.frontend,
            "metadata_retrieval",
            return_value=nullcontext(lambda: False),
        ),
        mock.patch.object(launcher.release, "discover_stable_release", return_value=stable),
        mock.patch.object(
            launcher.release, "read_optional_version", return_value=release.Version("15.0.1")
        ),
        mock.patch.object(launcher.frontend, "show_error") as show_error,
        mock.patch.object(launcher.frontend, "show_ready", return_value=0) as show_ready,
    ):
        result = launcher.main()

    assert result == 0
    show_ready.assert_called_once_with("15.0.1")
    show_error.assert_not_called()


def test_launcher_installs_required_bundle_before_reporting_ready(tmp_path):
    config_path = write_valid_prerequisites(tmp_path)
    stable = release.StableRelease(
        release.Version("15.0.2"),
        "https://dist.torproject.org/torbrowser/15.0.2/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.2/browser.tar.xz.asc",
    )
    progress = mock.Mock()
    progress.cancelled.return_value = False

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", config_path),
        mock.patch.object(
            launcher.frontend,
            "metadata_retrieval",
            return_value=nullcontext(lambda: False),
        ),
        mock.patch.object(
            launcher.frontend,
            "bundle_installation",
            return_value=nullcontext(progress),
        ),
        mock.patch.object(launcher.release, "discover_stable_release", return_value=stable),
        mock.patch.object(
            launcher.release,
            "read_optional_version",
            side_effect=[release.Version("15.0.1"), release.Version("15.0.1")],
        ),
        mock.patch.object(launcher.install, "install_verified_bundle") as install_bundle,
        mock.patch.object(launcher.frontend, "show_error") as show_error,
        mock.patch.object(launcher.frontend, "show_ready", return_value=0) as show_ready,
    ):
        result = launcher.main()

    assert result == 0
    install_bundle.assert_called_once_with(
        stable,
        signing_key_path=Path(json.loads(config_path.read_text())["signing_key_path"]),
        signing_key_fingerprint=FINGERPRINT,
        state_root=tmp_path / "tor-browser-state",
        cancelled=progress.cancelled,
        disable_cancellation=progress.disable_cancellation,
    )
    show_ready.assert_called_once_with("15.0.2")
    show_error.assert_not_called()


@pytest.mark.parametrize(
    ("failure", "title"),
    [
        (
            launcher.install.InstallationCancelled("download cancelled"),
            "Tor Browser installation cancelled",
        ),
        (
            launcher.install.InstallationSecurityError("invalid signature"),
            "Tor Browser installation blocked",
        ),
        (
            launcher.install.InstallationError("atomic switch failed"),
            "Tor Browser installation failed",
        ),
    ],
)
def test_launcher_never_reports_an_older_browser_ready_after_install_failure(
    tmp_path,
    failure,
    title,
):
    config_path = write_valid_prerequisites(tmp_path)
    stable = release.StableRelease(
        release.Version("15.0.2"),
        "https://dist.torproject.org/torbrowser/15.0.2/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.2/browser.tar.xz.asc",
    )
    progress = mock.Mock()

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", config_path),
        mock.patch.object(
            launcher.frontend,
            "metadata_retrieval",
            return_value=nullcontext(lambda: False),
        ),
        mock.patch.object(
            launcher.frontend,
            "bundle_installation",
            return_value=nullcontext(progress),
        ),
        mock.patch.object(launcher.release, "discover_stable_release", return_value=stable),
        mock.patch.object(
            launcher.release,
            "read_optional_version",
            side_effect=[release.Version("15.0.1"), release.Version("15.0.1")],
        ),
        mock.patch.object(
            launcher.install,
            "install_verified_bundle",
            side_effect=failure,
        ),
        mock.patch.object(launcher.frontend, "show_error", return_value=1) as show_error,
        mock.patch.object(launcher.frontend, "show_ready") as show_ready,
    ):
        result = launcher.main()

    assert result == 1
    assert show_error.call_args.args[0] == title
    show_ready.assert_not_called()


def test_unrecognized_json_object_fails_closed(tmp_path):
    config_path = tmp_path / "tor-browser.json"
    config_path.write_text("{}")

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", config_path),
        mock.patch.object(launcher.frontend, "show_error", return_value=1) as show_error,
        mock.patch.object(launcher.frontend, "show_ready") as show_ready,
    ):
        result = launcher.main()

    assert result == 1
    assert "invalid" in show_error.call_args.args[1]
    assert "administrator" in show_error.call_args.args[1]
    show_ready.assert_not_called()


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda config: Path(config["onion_auth_dir"])
            .joinpath("app-journalist.auth_private")
            .unlink(),
            "onion-auth credential",
        ),
        (
            lambda config: Path(config["onion_auth_dir"])
            .joinpath("extra.auth_private")
            .write_text(VALID_CREDENTIAL),
            "exactly one",
        ),
        (
            lambda config: Path(config["onion_auth_dir"])
            .joinpath("app-journalist.auth_private")
            .write_text("secret-value"),
            "malformed",
        ),
        (lambda config: Path(config["torrc_path"]).write_text("SocksPort 1"), "managed Tor"),
        (lambda config: config.__setitem__("signing_key_fingerprint", "0" * 40), "signing key"),
        (lambda config: Path(config["signing_key_path"]).unlink(), "signing key"),
        (lambda config: Path(config["signing_key_path"]).write_text("other key"), "signing key"),
        (lambda config: config.__setitem__("minimum_version", "latest"), "minimum version"),
        (lambda config: Path(config["minimum_version_path"]).unlink(), "minimum version"),
        (
            lambda config: Path(config["minimum_version_path"]).write_text("14.0\n"),
            "minimum version",
        ),
    ],
    ids=[
        "missing-onion-auth",
        "multiple-onion-auth",
        "malformed-onion-auth",
        "modified-torrc",
        "unexpected-signing-fingerprint",
        "missing-signing-key",
        "modified-signing-key",
        "invalid-minimum-version",
        "missing-minimum-version",
        "modified-minimum-version",
    ],
)
def test_invalid_security_prerequisite_fails_closed_without_exposing_secret(
    tmp_path, mutate, expected
):
    config_path = write_valid_prerequisites(tmp_path)
    config = json.loads(config_path.read_text())
    mutate(config)
    config_path.write_text(json.dumps(config))

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", config_path),
        mock.patch.object(socket, "create_connection") as create_connection,
        mock.patch.object(subprocess, "Popen") as popen,
        pytest.raises(core.ManagedConfigurationError) as exc_info,
    ):
        core.load_managed_config()

    message = str(exc_info.value)
    assert expected in message
    assert "secret-value" not in message
    assert VALID_CREDENTIAL not in message
    create_connection.assert_not_called()
    popen.assert_not_called()


def test_onion_auth_credential_requires_restrictive_permissions(tmp_path):
    config_path = write_valid_prerequisites(tmp_path)
    config = json.loads(config_path.read_text())
    credential = Path(config["onion_auth_dir"]) / "app-journalist.auth_private"
    credential.chmod(0o644)

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", config_path),
        pytest.raises(core.ManagedConfigurationError, match="permissions"),
    ):
        core.load_managed_config()


def test_admin_salt_exposes_only_the_supported_command_and_desktop_entry():
    state = Path("admin_salt/sd-admin-tor-browser.sls").read_text()
    desktop_entry = Path("files/press.freedom.SecureDropTorBrowser.desktop").read_text()

    assert "/usr/bin/securedrop-tor-browser" in state
    assert "/usr/share/applications/press.freedom.SecureDropTorBrowser.desktop" in state
    assert "Exec=securedrop-tor-browser" in desktop_entry
    assert "Terminal=false" in desktop_entry


def test_launcher_assets_are_limited_to_the_admin_rpm_subpackage():
    spec = Path("rpm-build/SPECS/securedrop-workstation-dom0-config.spec").read_text()
    admin_install = spec.index("%if %{with admin}", spec.index("%install"))
    standard_files = spec.index("%files\n")

    launcher_assets = (
        "securedrop_tor_browser",
        "securedrop-tor-browser",
        "press.freedom.SecureDropTorBrowser.desktop",
    )
    for asset in launcher_assets:
        assert asset not in spec[:admin_install]
        assert asset in spec[admin_install:standard_files]


def test_admin_salt_atomically_manages_all_security_prerequisites():
    state = Path("admin_salt/sd-admin-tor-browser.sls").read_text()

    assert "app-journalist.auth_private" in state
    assert 'mode: "0600"' in state
    assert "makedirs: true" in state
    assert "torrc" in state
    assert "tor-browser-signing-key.asc" in state
    assert "tor-browser-firefox.apparmor" in state
    assert "tor-browser-tor.apparmor" in state
    assert "tor-browser-minimum-version" in state


def test_admin_package_provisions_writable_private_install_state_and_gpgv():
    state = Path("admin_salt/sd-admin-tor-browser.sls").read_text()
    spec = Path("rpm-build/SPECS/securedrop-workstation-dom0-config.spec").read_text()
    admin_package = spec[spec.index("%package -n securedrop-admin-dom0-config") :]

    assert "manage-securedrop-tor-browser-state" in state
    assert "name: /var/lib/securedrop-tor-browser" in state
    assert "user: user" in state
    assert 'mode: "0700"' in state
    assert "Requires: gnupg2" in admin_package
