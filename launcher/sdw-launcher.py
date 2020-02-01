#!/usr/bin/env python3
from logging.handlers import TimedRotatingFileHandler
from PyQt4 import QtGui
from sdw_updater_gui.UpdaterApp import UpdaterApp
import fcntl
import logging
import os
import sys

# This script is run as a user, so it does not use /run, which requires root
# access
LOCK_FILE = "/tmp/sdw-launcher.lock"
DEFAULT_HOME = os.path.join(os.path.expanduser("~"), ".securedrop_launcher")

logger = ""  # Global logger object, configured later
lock_handle = ""  # File handle for lockfile, must be kept open during execution


def main():
    global logger
    logger = logging.getLogger(__name__)
    obtain_lock()
    logger.info("Starting SecureDrop Launcher")
    configure_logging()
    app = QtGui.QApplication(sys.argv)
    form = UpdaterApp()
    form.show()
    sys.exit(app.exec_())


def obtain_lock():
    """
    Obtain an exclusive lock to ensure that only one updater can run at a time,
    and to inform other processes that it is running.
    """
    global lock_handle

    # Attempt to obtain a file handle for the lockfile
    try:
        lock_handle = open(LOCK_FILE, 'w')
    except IOError:
        logger.error("Error obtaining write access to lock file {}\n"
                     "User may lack required permissions. Exiting."
                     .format(LOCK_FILE))
        sys.exit(1)

    # Attempt to obtain an exlusive, nonblocking lock
    try:
        fcntl.lockf(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        logger.error("Error obtaining lock on {}\n"
                     "Launcher may already be running. Exiting."
                     .format(LOCK_FILE))
        sys.exit(1)


def configure_logging():
    """
    All logging related settings are set up by this function.
    """
    log_folder = os.path.join(DEFAULT_HOME, "logs")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_file = os.path.join(DEFAULT_HOME, "logs", "launcher.log")

    # set logging format
    log_fmt = (
        "%(asctime)s - %(name)s:%(lineno)d(%(funcName)s) " "%(levelname)s: %(message)s"
    )
    formatter = logging.Formatter(log_fmt)

    handler = TimedRotatingFileHandler(log_file)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    # set up primary log
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.addHandler(handler)


if __name__ == "__main__":
    main()
