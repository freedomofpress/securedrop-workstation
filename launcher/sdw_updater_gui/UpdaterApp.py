from sdw_updater_gui import strings
from sdw_updater_gui import Updater
from sdw_updater_gui.Updater import UpdateStatus
from sdw_util import Util
import logging
import subprocess
import sys

if Util.get_qt_version() == 5:
    from PyQt5.QtWidgets import QDialog
    from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
    from sdw_updater_gui.UpdaterAppUiQt5 import Ui_UpdaterDialog
else:
    from PyQt4.QtGui import QDialog
    from PyQt4.QtCore import QThread, pyqtSignal, pyqtSlot
    from sdw_updater_gui.UpdaterAppUi import Ui_UpdaterDialog


logger = logging.getLogger(__name__)


def launch_securedrop_client():
    """
    Helper function to launch the SecureDrop Client
    """
    try:
        logger.info("Launching SecureDrop client")
        subprocess.Popen(["qvm-run", "sd-app", "gtk-launch securedrop-client"])
    except subprocess.CalledProcessError as e:
        logger.error("Error while launching SecureDrop client")
        logger.error(str(e))
    sys.exit(0)


class UpdaterApp(QDialog, Ui_UpdaterDialog):
    def __init__(self, parent=None):
        super(UpdaterApp, self).__init__(parent)

        self.progress = 0
        self.setupUi(self)

        # We use a single dialog with button visibility toggled at different
        # stages. In the first stage, we only show the "Start Updates" and
        # "Cancel" buttons.

        self.applyUpdatesButton.setEnabled(True)
        self.applyUpdatesButton.show()
        self.applyUpdatesButton.clicked.connect(self.apply_all_updates)

        self.cancelButton.setEnabled(True)
        self.cancelButton.show()
        self.cancelButton.clicked.connect(self.exit_launcher)

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
        logger.info("Signal: upgrade_status {}".format(str(result)))
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

        logger.info("Signal: Progress {}%".format(current_progress))
        self.progress = current_progress
        self.progressBar.setProperty("value", self.progress)

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

    def exit_launcher(self):
        """
        Exits the launcher if the user clicks cancel
        """
        sys.exit()


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

        # Update dom0 first, then apply dom0 state. If full state run
        # is required, the dom0 state will drop a flag.
        self.progress_signal.emit(5)
        upgrade_generator = Updater.apply_updates(vms=["dom0"], progress_start=5, progress_end=10)

        results = {}
        for vm, progress, result in upgrade_generator:
            results[vm] = result
            self.progress_signal.emit(progress)

        # apply dom0 state
        self.progress_signal.emit(10)
        result = Updater.apply_dom0_state()
        # add to results dict, if it fails it will show error message
        results["apply_dom0"] = result.value

        self.progress_signal.emit(15)
        # rerun full config if dom0 checks determined it's required,
        # otherwise proceed with per-VM package updates
        if Updater.migration_is_required():
            # Progress bar will freeze for ~15m during full state run
            self.progress_signal.emit(35)
            Updater.run_full_install()
            self.progress_signal.emit(75)
        else:
            upgrade_generator = Updater.apply_updates(progress_start=15, progress_end=75)
            for vm, progress, result in upgrade_generator:
                results[vm] = result
                self.progress_signal.emit(progress)

        # reboot vms
        Updater.shutdown_and_start_vms()

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
