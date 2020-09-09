#!/usr/bin/env python3
"""
Displays a warning to the user if the workstation has been running continuously
for too long without checking for security updates. Writes output to a logfile,
not stdout. All settings are in Notify utility module.
"""

import sys

from sdw_notify import Notify
from sdw_updater_gui import Updater
from sdw_util import Util

if Util.get_qt_version() == 5:
    print("Using Qt5 (experimental)")
    from PyQt5.QtWidgets import QApplication, QMessageBox
else:
    from PyQt4.QtGui import QApplication, QMessageBox


def main():
    """
    Show security warning, if and only if a warning is not already displayed,
    the preflight updater is running, and certain checks suggest that the
    system has not been updated for a specified period
    """

    Util.configure_logging(Notify.LOG_FILE)

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
    using the preflight updater.
    """
    app = QApplication([])  # noqa: F841

    QMessageBox.warning(
        None,
        "Security check recommended",
        "This computer has not been checked for security updates recently. "
        "We recommend that you launch or restart the SecureDrop app to "
        "check for security updates.",
        QMessageBox.Ok,
        QMessageBox.Ok,
    )


if __name__ == "__main__":
    main()
