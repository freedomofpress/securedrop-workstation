#!/usr/bin/python3
"""
Displays a warning to the user if the workstation has been running continuously
for too long without checking for security updates. Writes output to a logfile,
not stdout. All settings are in Notify utility module.
"""

import sys

from PyQt5.QtWidgets import QApplication

from sdw_notify import Notify, NotifyApp
from sdw_updater import Updater, UpdaterApp
from sdw_util import Util

Util.configure_logging(Notify.LOG_FILE)
log = Util.get_logger(Notify.LOG_FILE)


def main():
    """
    Show security warning, if and only if a warning is not already displayed,
    the preflight updater is running, and certain checks suggest that the
    system has not been updated for a specified period
    """

    if Util.is_conflicting_process_running(Notify.CONFLICTING_PROCESSES):
        # Conflicting system process may be running in dom0. Logged.
        sys.exit(1)

    if Util.can_obtain_lock(Updater.LOCK_FILE) is False:
        # Preflight updater is already running. Logged.
        sys.exit(1)

    # Hold on to lock handle during execution
    lock_handle = Util.obtain_lock(Notify.LOCK_FILE)
    if lock_handle is None:
        # Can't write to lockfile or notifier already running. Logged.
        sys.exit(1)

    warning_should_be_shown = Notify.is_update_check_necessary()
    if warning_should_be_shown is None:
        # Data integrity issue with update timestamp. Logged.
        sys.exit(1)
    elif warning_should_be_shown is True:
        show_update_warning()


def show_update_warning():
    """
    Show a graphical warning reminding the user to check for security updates
    using the Preflight Updater.

    If the user opts to check for updates, launch the Preflight Updater.
    If the user opts to defer, they will be reminded again the next time the
    notify script runs.
    """

    app = QApplication([])
    dialog = NotifyApp.NotifyDialog(Util.is_sdapp_halted())
    result = dialog.run()

    # Check results of Notify Dialog and launch the Preflight Updater if user
    # has opted to check for updates.
    if result == NotifyApp.NotifyStatus.CHECK_UPDATES:
        log.info("Launching Preflight Updater")
        updater = UpdaterApp.UpdaterApp()
        updater.show()
        sys.exit(app.exec_())
    elif result == NotifyApp.NotifyStatus.DEFER_UPDATES:
        # Currently, `DEFER_UPDATES` is a no-op, because the deferral period is
        # simply the period before the next run of the notify script (defined in
        # `securedrop-workstation/securedrop_salt/sd-dom0-crontab.sls`).
        log.info(
            "User has deferred update check. sdw-notify will run "
            "again at the next scheduled interval."
        )
        sys.exit(0)
    else:
        # NotifyApp.NotifyStatus.ERROR_UNKNOWN, meaning the dialog returned an
        # unexpected state. The error is logged in NotifyDialog.run().
        log.info(
            "Unexpected result from NotifyDialog. sdw-notify will run "
            "again at the next scheduled interval."
        )
        sys.exit(result)


if __name__ == "__main__":
    main()
