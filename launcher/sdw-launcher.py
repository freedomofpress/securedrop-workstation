#!/usr/bin/env python3
from PyQt4 import QtGui
from sdw_updater_gui.UpdaterApp import UpdaterApp
from sdw_util import Util
from sdw_updater_gui import Updater
from sdw_updater_gui.UpdaterApp import launch_securedrop_client
from sdw_updater_gui.Updater import should_launch_updater
import logging
import sys
import argparse

DEFAULT_INTERVAL = 0




def parse_argv(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-delta", type=int, default=0)
    return parser.parse_args(argv)


def launch_updater():
    """
    Start the updater GUI
    """

    app = QtGui.QApplication(sys.argv)
    form = UpdaterApp()
    form.show()
    sys.exit(app.exec_())


def main(argv):
    sdlog = logging.getLogger(__name__)
    Util.configure_logging(Updater.LOG_FILE)
    lock_handle = Util.obtain_lock(Updater.LOCK_FILE)
    if lock_handle is None:
        # Preflight updater already running or problems accessing lockfile.
        # Logged.
        sys.exit(1)
    sdlog.info("Starting SecureDrop Launcher")
    sdlog = logging.getLogger(__name__)
    configure_logging()
    sdlog.info("Starting SecureDrop Launcher")

    interval = DEFAULT_INTERVAL
    args = parse_argv(argv)
    if args.skip_delta:
        interval = int(args.skip_delta)

    if should_launch_updater(interval):
        launch_updater()
    else:
        launch_securedrop_client()


if __name__ == "__main__":
    main(sys.argv[1:])
