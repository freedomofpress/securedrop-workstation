"""
Utility library for warning the user that security updates have not been applied
in some time.
"""
import logging
import os

from datetime import datetime

sdlog = logging.getLogger(__name__)

# The directory where status files and logs are stored
BASE_DIRECTORY = os.path.join(os.path.expanduser("~"), ".securedrop_launcher")

# The file and format that contains the timestamp of the last successful update
LAST_UPDATED_FILE = os.path.join(BASE_DIRECTORY, "sdw-last-updated")
LAST_UPDATED_FORMAT = "%Y-%m-%d %H:%M:%S"

# The lockfile basename used to ensure this script can only be executed once.
# Default path for lockfiles is specified in sdw_util
LOCK_FILE = "sdw-notify.lock"

# Log file name, base directories defined in sdw_util
LOG_FILE = "sdw-notify.log"

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
        with open(LAST_UPDATED_FILE, 'r') as f:
            last_update_time = f.readline().splitlines()[0]
        try:
            last_update_time = datetime.strptime(last_update_time, LAST_UPDATED_FORMAT)
        except ValueError:
            sdlog.error("Data in {} not in the expected format. "
                        "Expecting a timestamp in format '{}'."
                        .format(LAST_UPDATED_FILE, LAST_UPDATED_FORMAT))
            return None

        now = datetime.now()
        updated_seconds_ago = (now - last_update_time).total_seconds()
        updated_hours_ago = updated_seconds_ago / 60 / 60

    uptime_seconds = get_uptime_seconds()
    uptime_hours = uptime_seconds / 60 / 60

    if not last_updated_file_exists:
        sdlog.info("Timestamp file '{}' does not exist. "
                   "Preflight updater may not have been run yet."
                   .format(LAST_UPDATED_FILE))

        # If we do not have the timestamp file, and the system has been running
        # for a long time, we should show the warning.
        if uptime_seconds > WARNING_THRESHOLD:
            sdlog.warning("Uptime ({0:.1f} hours) is above warning threshold "
                          "({1:.1f} hours). Showing security warning."
                          .format(uptime_hours,
                                  warning_threshold_hours))
            return True
        else:
            sdlog.info("Uptime ({0:.1f} hours) is below warning threshold "
                       "({1:.1f} hours). Exiting without warning."
                       .format(uptime_hours,
                               warning_threshold_hours))
            return False
    else:
        if updated_seconds_ago > WARNING_THRESHOLD:
            if uptime_seconds > UPTIME_GRACE_PERIOD:
                sdlog.warning("Last successful update ({0:.1f} hours ago) is above "
                              "warning threshold ({1:.1f} hours). Uptime grace period of "
                              "{2:.1f} hours has elapsed (uptime: {3:.1f} hours). "
                              "Showing security warning."
                              .format(updated_hours_ago,
                                      warning_threshold_hours,
                                      grace_period_hours,
                                      uptime_hours))
                return True
            else:
                sdlog.info("Last successful update ({0:.1f} hours ago) is above "
                           "warning threshold ({1:.1f} hours). Uptime grace period "
                           "of {2:.1f} hours has not elapsed yet (uptime: {3:.1f} "
                           "hours). Exiting without warning."
                           .format(updated_hours_ago,
                                   warning_threshold_hours,
                                   grace_period_hours,
                                   uptime_hours))
                return False
        else:
            sdlog.info("Last successful update ({0:.1f} hours ago) "
                       "is below the warning threshold ({1:.1f} hours). "
                       "Exiting without warning."
                       .format(updated_hours_ago,
                               warning_threshold_hours))
            return False


def get_uptime_seconds():
    # Obtain current uptime
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
    return uptime_seconds
