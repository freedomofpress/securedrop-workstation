#!/usr/bin/python3
import argparse
import sys

try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    from PyQt5.QtWidgets import QApplication  # type: ignore [no-redef]


from sdw_updater import Updater
from sdw_updater.Updater import is_qubes_mid_upgrade, should_launch_updater
from sdw_updater.UpdaterApp import InboxTarget, LaunchTarget, UpdaterApp, launch_in_vm
from sdw_util import Util

DEFAULT_INTERVAL = 28800  # 8hr default for update interval


def parse_argv(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-delta", type=int)
    parser.add_argument("--skip-netcheck", action="store_true")
    # --name, --vm and --desktop must be specified together; if none are, launch the Inbox
    parser.add_argument("--name", help="Name of the application to launch")
    parser.add_argument("--vm", help="VM to launch the application in")
    parser.add_argument("--desktop", help="Desktop file of the application to launch")
    args = parser.parse_args(argv)

    target_args = [args.name, args.vm, args.desktop]
    if all(arg is None for arg in target_args):
        args.launch_target = InboxTarget
    elif any(arg is None for arg in target_args):
        parser.error("--name, --vm and --desktop must be specified together")
    else:
        args.launch_target = LaunchTarget(name=args.name, vm=args.vm, desktop=args.desktop)
    return args


def launch_updater(launch_target: LaunchTarget, should_skip_netcheck: bool = False) -> None:
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
    else:
        launch_in_vm(args.launch_target)


if __name__ == "__main__":
    main(sys.argv[1:])
