"""
Utility library for warning the user that security updates have not been applied
in some time.
"""

import os
from datetime import datetime

from sdw_util import Util

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


def is_update_check_necessary():
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
            last_update_time = f.readline().splitlines()[0]
        try:
            last_update_time = datetime.strptime(last_update_time, LAST_UPDATED_FORMAT)
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


def get_uptime_seconds():
    # Obtain current uptime
    with open("/proc/uptime") as f:
        return float(f.readline().split()[0])
