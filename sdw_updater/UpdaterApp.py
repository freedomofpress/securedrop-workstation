import subprocess
import sys

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog

from sdw_updater import Updater, strings
from sdw_updater.Updater import UpdateStatus, current_templates
from sdw_updater.UpdaterAppUiQt5 import Ui_UpdaterDialog
from sdw_util import Util

logger = Util.get_logger(module=__name__)


def launch_securedrop_client():
    """
    Helper function to launch the SecureDrop Client
    """
    try:
        logger.info("Launching SecureDrop client")
        subprocess.Popen(["qvm-run", "sd-app", "gtk-launch press.freedom.SecureDropClient"])
    except subprocess.CalledProcessError as e:
        logger.error("Error while launching SecureDrop client")
        logger.error(str(e))
    sys.exit(0)


class UpdaterApp(QDialog, Ui_UpdaterDialog):
    def __init__(self, should_skip_netcheck: bool = False, parent=None):
        super().__init__(parent)

        self.progress = 0
        self._skip_netcheck = should_skip_netcheck
        self.setupUi(self)

        # We use a single dialog with button visibility toggled at different
        # stages. In the first stage, we only show the "Start Updates" and
        # "Cancel" buttons.

        self.applyUpdatesButton.setEnabled(True)
        self.applyUpdatesButton.show()
        self.applyUpdatesButton.clicked.connect(self._check_network_and_update)

        self.cancelButton.setEnabled(True)
        self.cancelButton.show()
        self.cancelButton.clicked.connect(self.exit_updater)

        self.clientOpenButton.setEnabled(False)
        self.clientOpenButton.hide()
        self.clientOpenButton.clicked.connect(launch_securedrop_client)

        self.rebootButton.setEnabled(False)
        self.rebootButton.hide()
        self.rebootButton.clicked.connect(self.reboot_workstation)

        self.show()

        self.headline.setText(strings.headline_introduction)
        self.proposedActionDescription.setText(strings.description_introduction)

        self.progress += 1
        self.progressBar.setProperty("value", self.progress)
        self.progressBar.hide()

    @pyqtSlot(dict)
    def upgrade_status(self, result):
        """
        This slot will receive update signals from UpgradeThread, thread which
        is used to check for TemplateVM upgrades
        """
        logger.info(f"Signal: upgrade_status {str(result)}")
        self.progress = 100
        self.progressBar.setProperty("value", self.progress)

        if result["recommended_action"] == UpdateStatus.REBOOT_REQUIRED:
            logger.info("Reboot required")
            self.rebootButton.setEnabled(True)
            self.rebootButton.show()
            self.cancelButton.setEnabled(True)
            self.cancelButton.show()
            self.headline.setText(strings.headline_status_reboot_required)
            self.proposedActionDescription.setText(strings.description_status_reboot_required)
        elif result["recommended_action"] == UpdateStatus.UPDATES_OK:
            logger.info("VMs have been succesfully updated, OK to start client")
            self.clientOpenButton.setEnabled(True)
            self.clientOpenButton.show()
            self.cancelButton.setEnabled(True)
            self.cancelButton.show()
            self.headline.setText(strings.headline_status_updates_complete)
            self.proposedActionDescription.setText(strings.description_status_updates_complete)
        else:
            logger.info("Error upgrading VMs")
            self.cancelButton.setEnabled(True)
            self.cancelButton.show()
            self.headline.setText(strings.headline_status_updates_failed)
            self.proposedActionDescription.setText(strings.description_status_updates_failed)

    @pyqtSlot(int)
    def update_progress_bar(self, value):
        """
        This slot will receive updates from UpgradeThread which will provide a
        int representing the percentage of the progressBar. This slot will
        update the progressBar value once it receives the signal.
        """
        current_progress = int(value)
        if current_progress <= 0:
            current_progress = 5
        elif current_progress > 100:
            current_progress = 100

        self.progress = current_progress
        self.progressBar.setProperty("value", self.progress)

    def _check_network_and_update(self):
        """
        Wrapper for `apply_all_updates` that ensures network connectivity
        before updating, else stops the update and shows a connectivity error
        message to the user.

        Because this check happens before updates begin, an error at this stage
        simply stops the update attempt and does not affect the last
        UpdateStatus or affect the update timestamp.
        """

        if self._skip_netcheck:
            logger.info("Network check skipped; launching updater")
            self.apply_all_updates()
        elif _is_netcheck_successful():
            logger.info("Network check successful; checking for updates.")
            self.apply_all_updates()
        else:
            logger.error("Network connectivity check failed; cannot check for updates.")
            self._show_network_error()

    def _show_network_error(self):
        """
        Show the network error dialog state.
        """
        self.headline.setText(strings.headline_error_network)
        self.proposedActionDescription.setText(strings.description_error_network)
        self.cancelButton.setEnabled(True)
        self.applyUpdatesButton.hide()

    def apply_all_updates(self):
        """
        Method used by the applyUpdatesButton that will create and start an
        UpgradeThread to apply updates to TemplateVMs
        """
        logger.info("Starting UpgradeThread")
        self.progress = 5
        self.progressBar.setProperty("value", self.progress)
        self.progressBar.show()
        self.headline.setText(strings.headline_applying_updates)
        self.proposedActionDescription.setText(strings.description_status_applying_updates)
        self.applyUpdatesButton.setEnabled(False)
        self.applyUpdatesButton.hide()
        self.cancelButton.setEnabled(False)
        self.upgrade_thread = UpgradeThread()
        self.upgrade_thread.start()
        self.upgrade_thread.upgrade_signal.connect(self.upgrade_status)
        self.upgrade_thread.progress_signal.connect(self.update_progress_bar)

    def reboot_workstation(self):
        """
        Helper method to reboot the Workstation
        """
        try:
            logger.info("Rebooting the workstation")
            subprocess.check_call(["sudo", "reboot"])
            self.headline.setText(strings.headline_status_rebooting)
            self.proposedActionDescription.setText(strings.description_status_rebooting)
        except subprocess.CalledProcessError as e:
            self.headline.setText(strings.headline_error_reboot)
            self.proposedActionDescription.setText(strings.description_error_reboot)
            logger.error("Error while rebooting the workstation")
            logger.error(str(e))

    def exit_updater(self):
        """
        Exits the updater if the user clicks cancel
        """
        sys.exit()


def _is_netcheck_successful() -> bool:
    """
    Helper function to assess network connectivity before launching updater.

    Assess network connectivity by checking connection status (via nmcli) in
    sys-net.
    """
    command = b"nmcli networking connectivity check"

    if not Util.get_qubes_version():
        logger.error("QubesOS not detected, cannot check network.")
        return False
    try:
        # Use of `--pass-io` is required to check on network status, since
        # nmcli returns 0 for all connection states we need to report back to dom0.
        result = subprocess.check_output(["qvm-run", "-p", "sys-net", command])
        return result.decode("utf-8").strip() == "full"
    except subprocess.CalledProcessError as e:
        logger.error(
            "{} (connectivity check) failed; state reported as {}".format(
                command.decode("utf-8"), e.output
            )
        )
        return False


class UpgradeThread(QThread):
    """
    This thread will apply updates for TemplateVMs based on the VM list
    specified in the object's contructor
    """

    upgrade_signal = pyqtSignal("PyQt_PyObject")
    progress_signal = pyqtSignal("int")

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        results = self.run_full_update()

        # write flags to disk
        run_results = Updater.overall_update_status(results)
        Updater._write_updates_status_flag_to_disk(run_results)
        # Write the "last updated" date to disk if the system is up-to-date
        # after applying upgrades, regardless of whether a reboot is still pending.
        if run_results in {UpdateStatus.UPDATES_OK, UpdateStatus.REBOOT_REQUIRED}:
            Updater._write_last_updated_flags_to_disk()
        # populate signal results
        message = results  # copy all information from updater call
        message["recommended_action"] = run_results
        self.upgrade_signal.emit(message)

    def run_full_update(self):
        # Pre-populate results with all available steps for early exits
        results = {
            "dom0": UpdateStatus.UPDATES_REQUIRED,
            "apply_dom0": UpdateStatus.UPDATES_REQUIRED,
            "apply_all": UpdateStatus.UPDATES_REQUIRED,
            "templates": UpdateStatus.UPDATES_REQUIRED,
        }

        # Update dom0 first, then apply dom0 state. If full state run
        # is required, the dom0 state will drop a flag.
        self.progress_signal.emit(5)
        results["dom0"] = Updater.apply_updates_dom0()
        if results["dom0"] == UpdateStatus.UPDATES_FAILED:
            return results  # Fail early

        # apply dom0 state
        self.progress_signal.emit(10)
        # add to results dict, if it fails it will show error message
        results["apply_dom0"] = Updater.apply_dom0_state()
        if results["apply_dom0"] == UpdateStatus.UPDATES_FAILED:
            return results  # Fail early

        self.progress_signal.emit(15)
        # rerun full config if dom0 checks determined it's required
        if Updater.migration_is_required():
            # Progress bar will freeze for ~15m during full state run
            self.progress_signal.emit(35)
            # add to results dict, if it fails it will show error message
            results["apply_all"] = Updater.run_full_install()
            if results["apply_all"] == UpdateStatus.UPDATES_FAILED:
                return results  # Fail early

            self.progress_signal.emit(75)

            templates_progress_callback = self.templates_progress_callback_factory(
                progress_start=75,
                progress_end=90,
            )
        else:
            results["apply_all"] = UpdateStatus.UPDATES_OK  # No updates
            templates_progress_callback = self.templates_progress_callback_factory(
                progress_start=15,
                progress_end=90,
            )

        results["templates"] = Updater.apply_updates_templates(
            current_templates,
            templates_progress_callback,
        )

        return results

    def templates_progress_callback_factory(self, progress_start, progress_end):
        def bump_progress(templates_total_progress):
            """
            Figure out how much the progress bar should be bumped
            """
            template_prog_percentage = (progress_end - progress_start) / 100
            total_progress = int(
                progress_start + template_prog_percentage * templates_total_progress
            )

            return self.progress_signal.emit(total_progress)

        return bump_progress
