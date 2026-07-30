import json
import runpy
import socket
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from securedrop_tor_browser import core
from securedrop_tor_browser import main as launcher


def test_graphical_error_keeps_application_alive_while_constructing_widget():
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


def test_launcher_accepts_a_workstation_managed_json_object(tmp_path):
    config_path = tmp_path / "tor-browser.json"
    config_path.write_text(json.dumps({"managed_by": "SecureDrop Workstation"}))

    with (
        mock.patch.object(core, "MANAGED_CONFIG_PATH", config_path),
        mock.patch.object(launcher.frontend, "show_error") as show_error,
        mock.patch.object(launcher.frontend, "show_ready", return_value=0) as show_ready,
    ):
        result = launcher.main()

    assert result == 0
    show_ready.assert_called_once_with()
    show_error.assert_not_called()


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
