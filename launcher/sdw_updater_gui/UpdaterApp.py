from PyQt4 import QtGui
from PyQt4.QtCore import QThread, pyqtSignal, pyqtSlot
from sdw_updater_gui.UpdaterAppUi import Ui_UpdaterDialog
from sdw_updater_gui import strings
from sdw_updater_gui import Updater
from sdw_updater_gui.Updater import UpdateStatus
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


class UpdaterApp(QtGui.QMainWindow, Ui_UpdaterDialog):
    def __init__(self, parent=None):
        super(UpdaterApp, self).__init__(parent)

        self.progress = 0
        self.setupUi(self)
        self.clientOpenButton.setEnabled(False)
        self.clientOpenButton.hide()
        self.clientOpenButton.clicked.connect(self.launch_securedrop_client)
        self.rebootButton.setEnabled(False)
        self.rebootButton.hide()
        self.rebootButton.clicked.connect(self.reboot_workstation)
        self.applyUpdatesButton.setEnabled(False)
        self.applyUpdatesButton.hide()
        self.applyUpdatesButton.clicked.connect(self.apply_all_updates)

        self.cancelButton.setEnabled(False)
        self.cancelButton.hide()
        self.cancelButton.clicked.connect(self.exit_launcher)

        self.show()

        self.proposedActionDescription.setText(
            strings.description_status_checking_updates
        )

        self.progress += 1
        self.progressBar.setProperty("value", self.progress)

        self.vms_to_update = []

        logger.info("Starting UpdateThread")
        self.update_thread = UpdateThread()
        self.update_thread.update_signal.connect(self.update_status)
        self.update_thread.progress_signal.connect(self.update_progress_bar)
        self.update_thread.start()

    @pyqtSlot(dict)
    def update_status(self, result):
        """
        This slot will receive update signals from UpdateThread, thread which
        is used to check for TemplateVM updates
        """
        logger.info("Signal: update_status {}".format(str(result)))

        if result["recommended_action"] == UpdateStatus.UPDATES_REQUIRED:
            logger.info("Updates required")
            self.vms_to_update = self.get_vms_that_need_upgrades(result)
            self.applyUpdatesButton.setEnabled(True)
            self.applyUpdatesButton.show()
            self.cancelButton.setEnabled(True)
            self.cancelButton.show()
            self.proposedActionDescription.setText(
                strings.description_status_updates_available
            )
        elif result["recommended_action"] == UpdateStatus.UPDATES_OK:
            logger.info("VMs up-to-date, OK to start client")
            self.clientOpenButton.setEnabled(True)
            self.clientOpenButton.show()
            self.cancelButton.setEnabled(True)
            self.cancelButton.show()
            self.proposedActionDescription.setText(
                strings.description_status_up_to_date
            )
        elif result["recommended_action"] == UpdateStatus.REBOOT_REQUIRED:
            logger.info("Reboot will be required")
            # We also have further updates to do, let's apply updates and reboot
            # once those are done
            if len(self.get_vms_that_need_upgrades(result)) > 0:
                logger.info("Reboot will be after applying upgrades")
                self.vms_to_update = self.get_vms_that_need_upgrades(result)
                self.applyUpdatesButton.setEnabled(True)
                self.applyUpdatesButton.show()
                self.cancelButton.setEnabled(True)
                self.cancelButton.show()
                self.proposedActionDescription.setText(
                    strings.description_status_updates_available
                )
            # No updates required, show reboot button.
            else:
                logger.info("Reboot required")
                self.rebootButton.setEnabled(True)
                self.rebootButton.show()
                self.cancelButton.setEnabled(True)
                self.cancelButton.show()
                self.proposedActionDescription.setText(
                    strings.description_status_reboot_required
                )
        else:
            logger.error("Error checking for updates")
            logger.error(str(result))
            self.proposedActionDescription.setText(
                strings.description_error_check_updates_failed
            )

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
            self.proposedActionDescription.setText(
                strings.description_status_reboot_required
            )
        elif result["recommended_action"] == UpdateStatus.UPDATES_OK:
            logger.info("VMs have been succesfully updated, OK to start client")
            self.clientOpenButton.setEnabled(True)
            self.clientOpenButton.show()
            self.cancelButton.setEnabled(True)
            self.cancelButton.show()
            self.proposedActionDescription.setText(
                strings.description_status_updates_complete
            )
        else:
            logger.info("Error upgrading VMs")
            self.cancelButton.setEnabled(True)
            self.cancelButton.show()
            self.proposedActionDescription.setText(
                strings.description_status_security_updates_failed
            )

    @pyqtSlot(int)
    def update_progress_bar(self, value):
        """
        This slot will receive updates from UpdateThread and UpgradeThread which
        will provide a int representing the percentage of the progressBar. This
        slot will update the progressBar value once it receives the signal.
        """
        current_progress = int(value)
        if current_progress <= 0:
            current_progress = 5
        elif current_progress > 100:
            current_progress = 100

        logger.info("Signal: Progress {}%".format(current_progress))
        self.progress = current_progress
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

    def launch_securedrop_client(self):
        """
        Helper method to launch the SecureDrop Client
        """
        try:
            logger.info("Launching SecureDrop client")
            subprocess.Popen(["qvm-run", "sd-app", "gtk-launch securedrop-client"])
        except subprocess.CalledProcessError as e:
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
        self.proposedActionDescription.setText(
            strings.description_status_applying_updates
        )
        self.applyUpdatesButton.setEnabled(False)
        self.applyUpdatesButton.hide()
        self.cancelButton.setEnabled(False)
        self.cancelButton.hide()
        # Create thread with list of VMs to update
        self.upgrade_thread = UpgradeThread(self.vms_to_update)
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
            self.proposedActionDescription.setText(strings.description_status_rebooting)
        except subprocess.CalledProcessError as e:
            self.proposedActionDescription.setText(strings.description_error_reboot)
            logger.error("Error while rebooting the workstation")
            logger.error(str(e))

    def exit_launcher(self):
        """
        Exits the launcher if the user clicks cancel
        """
        sys.exit()


class UpdateThread(QThread):
    """
    This thread will check for TemplateVM updates
    """

    update_signal = pyqtSignal("PyQt_PyObject")
    progress_signal = pyqtSignal("int")

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        update_generator = Updater.check_all_updates()
        results = {}

        for vm, progress, result in update_generator:
            results[vm] = result
            self.progress_signal.emit(progress)

        # write the flags to disk
        run_results = Updater.overall_update_status(results)
        Updater._write_updates_status_flag_to_disk(run_results)
        if run_results == UpdateStatus.UPDATES_OK:
            Updater._write_last_updated_flags_to_disk()
        # populate signal contents
        message = results  # copy all the information from results
        message["recommended_action"] = run_results
        self.update_signal.emit(message)


class UpgradeThread(QThread):
    """
    This thread will apply updates for TemplateVMs based on the VM list
    specified in the object's contructor
    """

    upgrade_signal = pyqtSignal("PyQt_PyObject")
    progress_signal = pyqtSignal("int")
    vms_to_upgrade = []

    def __init__(self, vms):
        QThread.__init__(self)
        self.vms_to_upgrade = vms

    def run(self):
        upgrade_generator = Updater.apply_updates(self.vms_to_upgrade)
        results = {}

        for vm, progress, result in upgrade_generator:
            results[vm] = result
            self.progress_signal.emit(progress)
        # write flags to disk
        run_results = Updater.overall_update_status(results)
        Updater._write_updates_status_flag_to_disk(run_results)
        if run_results == UpdateStatus.UPDATES_OK:
            Updater._write_last_updated_flags_to_disk()
        # populate signal results
        message = results  # copy all information from updater call
        message["recommended_action"] = run_results
        self.upgrade_signal.emit(message)
