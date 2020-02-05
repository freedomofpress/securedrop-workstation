#!/usr/bin/env python3
"""
Displays a warning to the user if the workstation has been running continuously
for too long without checking for security updates. Writes output to a logfile,
not stdout. All settings are in Notify utility module.
"""

from sdw_notify import Notify
from PyQt4 import QtGui
from PyQt4.QtGui import QMessageBox


def main():
    """
    Show security warning, if and only if a warning is not already displayed,
    the preflight updater is running, and certain checks suggest that the
    system has not been updated for a specified period
    """

    Notify.configure_logging()
    Notify.obtain_and_release_updater_lock()
    # Hold on to lock handle during execution
    lock_handle = Notify.obtain_notify_lock()  # noqa: F841
    if Notify.warning_should_be_shown():
        show_update_warning()


def show_update_warning():
    """
    Show a graphical warning reminding the user to check for security updates
    using the preflight updater.
    """
    app = QtGui.QApplication([])  # noqa: F841

    QMessageBox.warning(None,
                        'Security check recommended',
                        'The workstation has been running continuously for a long time. '
                        'We recommend that you launch or restart the SecureDrop app to '
                        'check for security updates.',
                        QMessageBox.Ok,
                        QMessageBox.Ok)


if __name__ == "__main__":
    main()
