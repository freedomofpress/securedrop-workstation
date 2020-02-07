#!/usr/bin/env python3
from PyQt4 import QtGui
from sdw_updater_gui.UpdaterApp import UpdaterApp
from sdw_updater_gui.Updater import configure_logging, obtain_lock
import logging
import sys


def main():
    sdlog = logging.getLogger(__name__)
    configure_logging()
    lock_handle = obtain_lock()  # noqa: F841
    if lock_handle is None:
        # Preflight updater already running or problems accessing lockfile.
        # Logged.
        sys.exit(1)
    sdlog.info("Starting SecureDrop Launcher")
    app = QtGui.QApplication(sys.argv)
    form = UpdaterApp()
    form.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
