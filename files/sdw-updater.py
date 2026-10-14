#!/usr/bin/python3
import argparse
import sys

from PyQt6.QtWidgets import QApplication

from sdw_updater import Updater
from sdw_updater.Updater import is_qubes_mid_upgrade, should_launch_updater
from sdw_updater.UpdaterApp import (
    LaunchTarget,
    UpdaterApp,
    default_launch_target,
    launch_in_vm,
)
from sdw_util import Util

DEFAULT_INTERVAL = 28800  # 8hr default for update interval


def parse_argv(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-delta", type=int)
    parser.add_argument("--skip-netcheck", action="store_true")
    parser.add_argument(
        "--launch",
        nargs=3,
        metavar=("NAME", "VM", "DESKTOP"),
        help="Application to launch after updating (default: SecureDrop Inbox)",
    )
    args = parser.parse_args(argv)

    if args.launch is None:
        args.launch_target = default_launch_target()
    else:
        name, vm, desktop = args.launch
        args.launch_target = LaunchTarget(name=name, vm=vm, desktop=desktop)
    return args


def launch_updater(launch_target: LaunchTarget | None, should_skip_netcheck: bool = False) -> None:
    """
    Start the updater GUI.
    """

    app = QApplication(sys.argv)
    form = UpdaterApp(should_skip_netcheck, launch_target=launch_target)
    form.show()
    sys.exit(app.exec())


def main(argv: list[str]) -> None:
    Util.configure_logging(Updater.LOG_FILE)
    Util.configure_logging(Updater.DETAIL_LOG_FILE, Updater.DETAIL_LOGGER_PREFIX, backup_count=10)
    sdlog = Util.get_logger()

    lock_handle = Util.obtain_lock(Updater.LOCK_FILE)
    if lock_handle is None:
        # Preflight updater already running or problems accessing lockfile.
        # Logged.
        sys.exit(1)

    if is_qubes_mid_upgrade():
        sdlog.info("Detected inplace upgrade in process. Exiting!")
        sys.exit(0)

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
        launch_updater(args.launch_target, args.skip_netcheck)
    elif args.launch_target:
        launch_in_vm(args.launch_target)
    else:
        # This should only happen on admin-only workstations that were recently updated,
        # e.g. after a mandated reboot. In that case we don't know what they wanted to
        # launch so we show/do nothing and let them re-launch it.
        sdlog.info("Updates not required and nothing to launch, exiting.")


if __name__ == "__main__":
    main(sys.argv[1:])
