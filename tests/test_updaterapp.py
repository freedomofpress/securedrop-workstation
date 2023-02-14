import os
import subprocess
import unittest
from unittest import mock

import pytest
from PyQt5.QtWidgets import QApplication

from sdw_updater import UpdaterApp, strings


@pytest.fixture(scope="module", autouse=True)
def app():
    with subprocess.Popen(["/usr/bin/Xvfb", ":99"]) as xvfb:
        os.environ["DISPLAY"] = ":99"
        app = QApplication([])
        yield app
        app.quit()
        xvfb.kill()


@mock.patch("sdw_util.Util.get_qubes_version", return_value="4.1")
@mock.patch("sdw_updater.UpdaterApp.subprocess.check_output", return_value=b"none")
def test_netcheck_no_network_should_fail(mocked_output, mocked_qubes_version):
    """
    When the host machine has no network connectivity
    Then the error is logged
     And netcheck returns False
    """
    assert not UpdaterApp._is_netcheck_successful()


@mock.patch("sdw_util.Util.get_qubes_version", return_value=None)
@mock.patch("sdw_updater.UpdaterApp.logger.error")
def test_netcheck_no_qubes_should_fail_with_error(mocked_error, mocked_qubes_version):
    """
    When the network connectivity check is run outside of Qubes
    Then the check should return not succeed
     And an error should be logged
    """
    assert not UpdaterApp._is_netcheck_successful()
    assert mocked_error.called


@mock.patch("subprocess.check_output", return_value=b"full")
@mock.patch("sdw_util.Util.get_qubes_version", return_value="4.1")
def test_netcheck_should_succeed(mocked_qubes_version, mocked_output):
    """
    When the network connectivity check is run in Qubes
     And nmcli detects a connection
    Then the network check should succeed
    """
    assert UpdaterApp._is_netcheck_successful()


@mock.patch("sdw_util.Util.get_qubes_version", return_value="4.1")
@mock.patch("sdw_updater.UpdaterApp.logger.error")
@mock.patch("subprocess.check_output", return_value=b"none")
def test_updater_app_with_no_connectivity_should_error(
    mocked_output, mocked_error, mocked_qubes_version
):
    """
    When the netcheck method is run
     And the network check is unsuccessful
    Then the network error view should be visible
    """
    updater_app_dialog = UpdaterApp.UpdaterApp()
    updater_app_dialog._check_network_and_update()
    assert is_network_fail_view(updater_app_dialog)


@mock.patch("sdw_util.Util.get_qubes_version", return_value="4.1")
@mock.patch("subprocess.check_output", return_value=b"full")
@mock.patch("sdw_updater.UpdaterApp.logger.info")
@mock.patch("sdw_updater.UpdaterApp.UpgradeThread")
def test_updater_app_with_connectivity_should_succeed(
    mocked_thread, mocked_logger, mocked_output, mocked_qubes_version
):
    """
    When the netcheck is run
     And the network check is successful
    Then the Preflight Updater should begin to check for updates
     And the progress view should be visible
    """
    updater_app_dialog = UpdaterApp.UpdaterApp()
    updater_app_dialog._check_network_and_update()
    assert is_progress_view(updater_app_dialog)


@mock.patch("sdw_updater.UpdaterApp.UpgradeThread")
def test_updater_app_with_override(mocked_thread):
    """
    When the netcheck is overridden (skipped)
     And there is no network connectivity
    Then `apply updates` should still be called
     And the progress bar should be visible
    """
    updater_app_dialog = UpdaterApp.UpdaterApp(should_skip_netcheck=True)
    updater_app_dialog._check_network_and_update()
    assert is_progress_view(updater_app_dialog)


def is_progress_view(dialog: UpdaterApp.UpdaterApp) -> bool:
    """
    Helper method to test assumptions about Dialog UI state.
    """
    return (
        dialog.progressBar.isVisible()
        and not dialog.applyUpdatesButton.isVisible()
        and dialog.cancelButton.isVisible()
        and not dialog.cancelButton.isEnabled()
        and dialog.proposedActionDescription.text() == strings.description_status_applying_updates
    )


def is_network_fail_view(dialog: UpdaterApp.UpdaterApp) -> bool:
    """
    Helper method to test assumptions about Dialog UI state.
    """
    return (
        not dialog.progressBar.isVisible()
        and not dialog.applyUpdatesButton.isVisible()
        and dialog.cancelButton.isVisible()
        and dialog.cancelButton.isEnabled()
        and dialog.proposedActionDescription.text() == strings.description_error_network
    )


if __name__ == "__main__":
    unittest.main()
