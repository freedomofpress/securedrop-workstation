from PyQt4 import QtGui
from PyQt4.QtCore import QThread, pyqtSignal
from sdw_updater_gui.UpdaterAppUi import Ui_UpdaterDialog
from sdw_updater_gui import strings
from sdw_updater_gui import Updater
from sdw_updater_gui.Updater import UpdateStatus
import logging
import subprocess
import sys
import time

UPDATE_FLAGFILE = "/home/user/.securedrop_client/securedrop-update-required-flag"
logger = logging.getLogger(__name__)


class UpdaterApp(QtGui.QMainWindow, Ui_UpdaterDialog):
    def __init__(self, parent=None):
        super(UpdaterApp, self).__init__(parent)

        self.progress = 0
        self.setupUi(self)
        self.clientOpenButton.setEnabled(False)
        self.clientOpenButton.clicked.connect(self.launch_securedrop_client)
        self.rebootButton.setEnabled(False)
        self.rebootButton.clicked.connect(self.reboot_workstation)
        self.applyUpdatesButton.setEnabled(False)
        self.applyUpdatesButton.clicked.connect(self.apply_all_updates)

        self.show()

        self.proposedActionLabel.setText(strings.label_status_checking_updates)
        self.proposedActionDescription.setText(
            strings.description_status_checking_updates
        )

        self.progress += 1
        self.progressBar.setProperty("value", self.progress)

        logger.info("Starting UpdateThread")
        self.update_thread = UpdateThread(self.progress_status)
        self.update_thread.start()
        self.update_thread.signal.connect(self.update_status)
        self.vms_to_update = []

        logger.info("Starting ProgressBarUpdaterThread")
        self.progress_bar_updater_thread = ProgressBarUpdaterThread()
        self.progress_bar_updater_thread.start()
        self.progress_bar_updater_thread.signal.connect(self.update_progress_ui)

    def update_status(self, result):
        """
        This slot will receive update signals from UpdateThread, thread which
        is used to check for TemplateVM updates
        """
        logger.info("Signal: update_status {}".format(str(result)))
        self.progress = 100
        self.progressBar.setProperty("value", self.progress)

        if result["recommended_action"] == UpdateStatus.UPDATES_REQUIRED:
            logger.info("Updates required")
            self.vms_to_update = self.get_vms_that_need_upgrades(result)
            self.applyUpdatesButton.setEnabled(True)
            self.proposedActionLabel.setText(strings.label_status_updates_available)
            self.proposedActionDescription.setText(
                strings.description_status_updates_available
            )
        elif result["recommended_action"] == UpdateStatus.UPDATES_OK:
            logger.info("VMs up-to-date, OK to start client")
            self.clientOpenButton.setEnabled(True)
            self.proposedActionLabel.setText(strings.label_status_up_to_date)
            self.proposedActionDescription.setText(
                strings.description_status_up_to_date
            )
        else:
            logger.error("Error checking for updates")
            logger.error(str(result))
            self.proposedActionLabel.setText(strings.label_error_check_update_failed)
            self.proposedActionDescription.setText(
                strings.description_error_check_updates_failed
            )

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
            self.proposedActionLabel.setText(strings.label_status_reboot_required)
            self.proposedActionDescription.setText(
                strings.description_status_reboot_required
            )
        elif result["recommended_action"] == UpdateStatus.UPDATES_OK:
            logger.info("VMs have been succesfully updated, OK to start client")
            self.clientOpenButton.setEnabled(True)
            self.proposedActionLabel.setText(strings.label_status_updates_complete)
            self.proposedActionDescription.setText(
                strings.description_status_updates_complete
            )

    def update_progress_ui(self, result):
        """
        This slot will receive periodic messages from ProgressBarUpdaterThread
        to update the progress bar with the progress variable.
        """
        logger.debug("Signal update_progress_ui: {}".format(result))
        self.progressBar.setProperty("value", self.progress)

    def get_vms_that_need_upgrades(self, results):
        """
        Helper method that returns a list of VMs that need upgrades based
        on the results returned by the UpdateThread
        """
        vms_to_upgrade = []
        for vm in results.keys():
            if vm != "recommended_action":  # ignore this higher_level key
                if results[vm] == UpdateStatus.UPDATES_REQUIRED:
                    vms_to_upgrade.append(vm)
        return vms_to_upgrade

    def progress_status(self, current_progress):
        """
        Helper method that will update the progress bar. It is used as a callback
        method to both UpdaterThread and UpgraderThread as they have no visibility
        into the UpdaterApp object.
        """
        current_progress = int(current_progress)
        if current_progress <= 0:
            current_progress = 5
        elif current_progress > 100:
            current_progress = 100
        self.progress = current_progress

    def launch_securedrop_client(self):
        """
        Helper method to launch the SecureDrop Client
        """
        try:
            self.proposedActionLabel.setText(strings.label_status_launching_client)
            logger.info("Launching SecureDrop client")
            subprocess.Popen(["qvm-run", "sd-svs", "gtk-launch securedrop-client"])
        except subprocess.CalledProcessError as e:
            self.proposedActionLabel.setText(strings.label_error_launching_client)
            self.proposedActionDescription.setText(strings.descri)
            logger.error("Error while launching SecureDrop client")
            logger.error(str(e))
        sys.exit(0)

    def apply_all_updates(self):
        """
        Method used by the applyUpdatesButton that will create and start an
        UpgradeThread to apply updates to TemplateVMs
        """
        logger.info("Starting UpgradeThread")
        self.progress = 5
        self.progressBar.setProperty("value", self.progress)
        self.proposedActionLabel.setText(strings.label_status_applying_updates)
        self.proposedActionDescription.setText(
            strings.description_status_applying_updates
        )
        self.applyUpdatesButton.setEnabled(False)
        # Create thread with list of VMs to update
        self.upgrade_thread = UpgradeThread(self.vms_to_update, self.progress_status)
        self.upgrade_thread.start()
        self.upgrade_thread.signal.connect(self.upgrade_status)

    def reboot_workstation(self):
        """
        Helper method to reboot the Workstation
        """
        try:
            logger.info("Rebooting the workstation")
            subprocess.check_call(["sudo", "reboot"])
            self.proposedActionLabel.setText(strings.label_status_rebooting)
        except subprocess.CalledProcessError as e:
            self.proposedActionLabel.setText(strings.label_error_reboot)
            self.proposedActionDescription.setText(strings.description_error_reboot)
            logger.error("Error while rebooting the workstation")
            logger.error(str(e))

    def run_unit_tests(self):
        pass


class UpdateThread(QThread):
    """
    This thread will check for TemplateVM updates
    """

    signal = pyqtSignal("PyQt_PyObject")
    progress_callback = None

    def __init__(self, callback_method=None):
        QThread.__init__(self)
        self.progress_callback = callback_method

    def run(self):
        results = Updater.check_all_updates(self.progress_callback)
        # populate signal contents
        message = results  # copy all the information from updater call
        message["recommended_action"] = Updater.overall_update_status(results)
        self.signal.emit(message)


class UpgradeThread(QThread):
    """
    This thread will apply updates for TemplateVMs based on the VM list
    specified in the object's contructor
    """

    signal = pyqtSignal("PyQt_PyObject")
    vms_to_upgrade = []
    progress_callback = None

    def __init__(self, vms, callback_method=None):
        QThread.__init__(self)
        self.vms_to_upgrade = vms
        self.progress_callback = callback_method

    def run(self):
        results = Updater.apply_updates(self.vms_to_upgrade, self.progress_callback)
        # populate signal results
        message = results  # copy all information from updater call
        message["recommended_action"] = Updater.overall_update_status(results)
        self.signal.emit(message)


class ProgressBarUpdaterThread(QThread):
    """
    Calling directly progressBar.setProperty will cause segfault because UI
    elements are accessed from another thread. This will be called by the main
    application thread and should be safe, it used the progress bar value
    `progress` updated via the callback method.
    """

    signal = pyqtSignal("PyQt_PyObject")

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        while 1:
            self.signal.emit("update")
            time.sleep(10)
