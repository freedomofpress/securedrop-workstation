#!/usr/bin/env python3
from logging.handlers import TimedRotatingFileHandler
from PyQt4 import QtGui
from sdw_updater_gui.UpdaterApp import UpdaterApp
import logging
import os
import sys

DEFAULT_HOME = os.path.join(os.path.expanduser("~"), ".securedrop_launcher")
logger = ""


def main():
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting SecureDrop Launcher")
    app = QtGui.QApplication(sys.argv)
    form = UpdaterApp()
    form.show()
    sys.exit(app.exec_())


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
    handler.setLevel(logging.DEBUG)

    # set up primary log
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)


if __name__ == "__main__":
    main()
