"""
Utility library for warning the user that security updates have not been applied
in some time.
"""

import fcntl
import os
import subprocess
from collections.abc import Iterable
from datetime import datetime

from sdw_util import Util
from securedrop_manage.products import get_installed_product

sdlog = Util.get_logger(module=__name__)

# The directory where status files and logs are stored
BASE_DIRECTORY = Util.BASE_DIRECTORY

# The file and format that contains the timestamp of the last successful update
LAST_UPDATED_FILE = os.path.join(BASE_DIRECTORY, "sdw-last-updated")
LAST_UPDATED_FORMAT = "%Y-%m-%d %H:%M:%S"

# The lockfile basename used to ensure this script can only be executed once.
# Default path for lockfiles is specified in sdw_util
LOCK_FILE = "sdw-notify.lock"

# Log file name, base directories defined in sdw_util
LOG_FILE = "sdw-notify.log"

# Process names that should not be running while this script runs. We do not
# want to encourage running the updater during provisioning or system updates.
# Caution is advised in expanding this list; a more precise detection method
# is generally preferable.
CONFLICTING_PROCESSES = ["qubesctl", "make"]

# The maximum uptime this script should permit (specified in seconds) before
# showing a warning. This is to avoid situations where the user boots the
# computer after several days and immediately sees a warning.
UPTIME_GRACE_PERIOD = 1800  # 30 minutes

# The amount of time without updates (specified in seconds) which this script
# should permit before showing a warning to the user
WARNING_THRESHOLD = 432000  # 5 days


def is_update_check_necessary() -> bool:
    """
    Perform a series of checks to determine if a security warning should be
    shown to the user, reminding them to check for available software updates
    using the preflight updater.
    """
    last_updated_file_exists = os.path.exists(LAST_UPDATED_FILE)
    # For consistent logging
    grace_period_hours = UPTIME_GRACE_PERIOD / 60 / 60
    warning_threshold_hours = WARNING_THRESHOLD / 60 / 60

    # Get timestamp from last update (if it exists)
    if last_updated_file_exists:
        with open(LAST_UPDATED_FILE) as f:
            last_update_str = f.readline().splitlines()[0]
        try:
            last_update_time = datetime.strptime(last_update_str, LAST_UPDATED_FORMAT)
        except ValueError:
            sdlog.error(
                f"Data in {LAST_UPDATED_FILE} not in the expected format. "
                f"Expecting a timestamp in format '{LAST_UPDATED_FORMAT}'. "
                "Showing security warning."
            )
            return True

        now = datetime.now()
        updated_seconds_ago = (now - last_update_time).total_seconds()
        updated_hours_ago = updated_seconds_ago / 60 / 60

    uptime_seconds = get_uptime_seconds()
    uptime_hours = uptime_seconds / 60 / 60

    if not last_updated_file_exists:
        sdlog.warning(
            f"Timestamp file '{LAST_UPDATED_FILE}' does not exist. "
            "Updater may never have run. Showing security warning."
        )
        return True
    if updated_seconds_ago > WARNING_THRESHOLD:
        if uptime_seconds > UPTIME_GRACE_PERIOD:
            sdlog.warning(
                f"Last successful update ({updated_hours_ago:.1f} hours ago) is above "
                f"warning threshold ({warning_threshold_hours:.1f} hours). Uptime grace period of "
                f"{grace_period_hours:.1f} hours has elapsed (uptime: {uptime_hours:.1f} hours). "
                "Showing security warning."
            )
            return True

        sdlog.info(
            f"Last successful update ({updated_hours_ago:.1f} hours ago) is above "
            f"warning threshold ({warning_threshold_hours:.1f} hours). Uptime grace period "
            f"of {grace_period_hours:.1f} hours has not elapsed yet (uptime: {uptime_hours:.1f} "
            "hours). Exiting without warning."
        )
        return False

    sdlog.info(
        f"Last successful update ({updated_hours_ago:.1f} hours ago) "
        f"is below the warning threshold ({warning_threshold_hours:.1f} hours). "
        "Exiting without warning."
    )
    return False


def get_uptime_seconds() -> float:
    # Obtain current uptime
    with open("/proc/uptime") as f:
        return float(f.readline().split()[0])


def can_obtain_lock(basename: str) -> bool:
    """
    We temporarily obtain a shared, nonblocking lock to a lockfile to determine
    whether the associated process is currently running. Returns True if it is
    safe to continue execution (no lock conflict), False if not.

    `basename` is the basename of a lockfile situated in Util.LOCK_DIRECTORY.
    """
    lock_file = os.path.join(Util.LOCK_DIRECTORY, basename)
    try:
        lh = open(lock_file)  # noqa: SIM115
    except FileNotFoundError:
        # Process may not have run during this session, safe to continue
        return True

    try:
        # Obtain a nonblocking, shared lock
        fcntl.lockf(lh, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except OSError:
        sdlog.error(Util.LOCK_ERROR.format(lock_file))
        return False

    return True


def is_conflicting_process_running(names: Iterable[str]) -> bool:
    """
    Check if any process of the given name is currently running. Aborts on the
    first match.
    """
    for name in names:
        result = subprocess.run(
            args=["pgrep", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
        )
        if result.returncode == 0:
            sdlog.error(f"Conflicting process '{name}' is currently running.")
            return True
    return False


def are_session_vms_halted() -> bool:
    """
    Detect if sd-app and/or sd-admin are running so we can display a message
    to the user that they'll be restarted.
    """

    if not Util.get_qubes_version():
        sdlog.error("QubesOS not detected, are_session_vms_halted will return False")
        return False

    product = get_installed_product()
    vms = []
    if product.contains_journalist:
        vms.append("sd-app")
    if product.contains_admin:
        vms.append("sd-admin")

    for vm in vms:
        try:
            output = subprocess.check_output(["qvm-ls", vm]).decode("utf-8")
        except subprocess.CalledProcessError as e:
            sdlog.error(f"Failed to return {vm} VM status via qvm-ls")
            sdlog.error(str(e))
            return False
        if "Halted" not in output:
            return False
    return True
