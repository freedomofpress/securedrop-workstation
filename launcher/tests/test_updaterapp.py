import os
import pytest
import subprocess
from unittest import TestCase
from unittest import mock
from unittest.mock import call
from importlib.machinery import SourceFileLoader

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from sdw_updater_gui.UpdaterAppUiQt5 import Ui_UpdaterDialog

relpath_updaterapp_script = "../sdw_updater_gui/UpdaterApp.py"
path_to_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_updaterapp_script)
updater_app = SourceFileLoader("UpdaterApp", path_to_script).load_module()

relpath_strings_script = "../sdw_updater_gui/strings.py"
path_to_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_strings_script)
strings = SourceFileLoader("strings", path_to_script).load_module()


class TestUpdaterApp(TestCase):
    _app = None

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication([])  # noqa: F841

    @classmethod
    def tearDownClass(cls):
        cls._app.quit()

    @mock.patch("UpdaterApp.Util.get_qubes_version", return_value="4.1")
    @mock.patch("UpdaterApp.subprocess.check_output", return_value=b"none")
    def test_netcheck_no_network_should_fail(self, mocked_output, mocked_qubes_version):
        """
        When the host machine has no network connectivity
        Then the error is logged
         And netcheck returns False
        """
        assert not updater_app._is_netcheck_successful()

    @mock.patch("Util.get_qubes_version", return_value=None)
    @mock.patch("UpdaterApp.logger.error")
    def test_netcheck_no_qubes_should_fail_with_error(self, mocked_error, mocked_qubes_version):
        """
        When the network connectivity check is run outside of Qubes
        Then the check should return not succeed
         And an error should be logged
        """
        assert not updater_app._is_netcheck_successful()
        assert mocked_error.called

    @mock.patch("subprocess.check_output", return_value=b"full")
    @mock.patch("UpdaterApp.Util.get_qubes_version", return_value="4.1")
    def test_netcheck_should_succeed(self, mocked_qubes_version, mocked_output):
        """
        When the network connectivity check is run in Qubes
         And nmcli detects a connection
        Then the network check should succeed
        """
        assert updater_app._is_netcheck_successful()

    @mock.patch("UpdaterApp.Util.get_qubes_version", return_value="4.1")
    @mock.patch("UpdaterApp.logger.error")
    @mock.patch("subprocess.check_output", return_value=b"none")
    def test_updater_app_with_no_connectivity_should_error(
        self, mocked_output, mocked_error, mocked_qubes_version
    ):
        """
        When the netcheck method is run
         And the network check is unsuccessful
        Then the network error view should be visible
        """
        updater_app_dialog = updater_app.UpdaterApp()
        updater_app_dialog._check_network_and_update()
        assert self._is_network_fail_view(updater_app_dialog)

    @mock.patch("UpdaterApp.Util.get_qubes_version", return_value="4.1")
    @mock.patch("subprocess.check_output", return_value=b"full")
    @mock.patch("UpdaterApp.logger.info")
    @mock.patch("UpdaterApp.UpgradeThread")
    def test_updater_app_with_connectivity_should_succeed(
        self, mocked_thread, mocked_logger, mocked_output, mocked_qubes_version
    ):
        """
        When the netcheck is run
         And the network check is successful
        Then the Preflight Updater should begin to check for updates
         And the progress view should be visible
        """
        updater_app_dialog = updater_app.UpdaterApp()
        updater_app_dialog._check_network_and_update()
        assert self._is_progress_view(updater_app_dialog)

    @mock.patch("UpdaterApp.UpgradeThread")
    def test_updater_app_with_override(self, mocked_thread):
        """
        When the netcheck is overridden (skipped)
         And there is no network connectivity
        Then `apply updates` should still be called
         And the progress bar should be visible
        """
        updater_app_dialog = updater_app.UpdaterApp(should_skip_netcheck=True)
        updater_app_dialog._check_network_and_update()
        assert self._is_progress_view(updater_app_dialog)

    def _is_progress_view(self, dialog: updater_app.UpdaterApp) -> bool:
        """
        Helper method to test assumptions about Dialog UI state.
        """
        return (
            dialog.progressBar.isVisible()
            and not dialog.applyUpdatesButton.isVisible()
            and dialog.cancelButton.isVisible()
            and not dialog.cancelButton.isEnabled()
            and dialog.proposedActionDescription.text()
            == strings.description_status_applying_updates
        )

    def _is_network_fail_view(self, dialog: updater_app.UpdaterApp) -> bool:
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
