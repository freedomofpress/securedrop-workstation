#!/usr/bin/python3
import argparse
import sys

from PyQt5.QtWidgets import QApplication

from sdw_updater import Updater
from sdw_updater.Updater import should_launch_updater
from sdw_updater.UpdaterApp import UpdaterApp, launch_securedrop_client
from sdw_util import Util

DEFAULT_INTERVAL = 28800  # 8hr default for update interval


def parse_argv(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-delta", type=int)
    parser.add_argument("--skip-netcheck", action="store_true")
    return parser.parse_args(argv)


def launch_updater(should_skip_netcheck: bool = False):
    """
    Start the updater GUI.
    """

    app = QApplication(sys.argv)
    form = UpdaterApp(should_skip_netcheck)
    form.show()
    sys.exit(app.exec_())


def main(argv):
    Util.configure_logging(Updater.LOG_FILE)
    Util.configure_logging(Updater.DETAIL_LOG_FILE, Updater.DETAIL_LOGGER_PREFIX, backup_count=10)
    sdlog = Util.get_logger()
    lock_handle = Util.obtain_lock(Updater.LOCK_FILE)
    if lock_handle is None:
        # Preflight updater already running or problems accessing lockfile.
        # Logged.
        sys.exit(1)
    sdlog.info("Starting SecureDrop Launcher")

    args = parse_argv(argv)

    try:
        args.skip_delta
    except NameError:
        args.skip_delta = DEFAULT_INTERVAL

    if args.skip_delta is None:
        args.skip_delta = DEFAULT_INTERVAL

    interval = int(args.skip_delta)

    if should_launch_updater(interval):
        launch_updater(args.skip_netcheck)
    else:
        launch_securedrop_client()


if __name__ == "__main__":
    main(sys.argv[1:])
