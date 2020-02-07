"""
Utility library for warning the user that security updates have not been applied
in some time.
"""
import fcntl
import logging
import os
import sys

from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

sdlog = logging.getLogger(__name__)

# The directory where status files andlogs are stored
BASE_DIRECTORY = os.path.join(os.path.expanduser("~"), ".securedrop_launcher")

# The file and format that contains the timestamp of the last successful update
LAST_UPDATED_FILE = os.path.join(BASE_DIRECTORY, "sdw-last-updated")
LAST_UPDATED_FORMAT = "%Y-%m-%d %H:%M:%S"

# Lock files are created to avoid contention issues or multiple instantiation.
# /run is used because it is cleaned out at the end of the user's session
LOCK_DIRECTORY = os.path.join("/run/user", str(os.getuid()))

# The lockfile used by the launcher script
LOCK_FILE_LAUNCHER = os.path.join(LOCK_DIRECTORY, "sdw-launcher.lock")

# The lockfile used to ensure this script can only be executed once
LOCK_FILE_NOTIFIER = os.path.join(LOCK_DIRECTORY, "sdw-notify.lock")

# Folder where logs are stored
LOG_DIRECTORY = os.path.join(BASE_DIRECTORY, "logs")
# Full path to logfile
LOG_FILE = os.path.join(LOG_DIRECTORY, "sdw-notify.log")
# Format for those logs
LOG_FORMAT = "%(asctime)s - %(name)s:%(lineno)d(%(funcName)s) " "%(levelname)s: %(message)s"

# The maximum uptime this script should permit (specified in seconds) before
# showing a warning. This is to avoid situations where the user boots the
# computer after several days and immediately sees a warning.
UPTIME_GRACE_PERIOD = 1800  # 30 minutes

# The amount of time without updates (specified in seconds) which this script
# should permit before showing a warning to the user
WARNING_THRESHOLD = 432000  # 5 days


def can_obtain_updater_lock():
    """
    We temporarily obtain a shared, nonblocking lock to the updater's lock
    file to determine whether it is currently running. We do not need to
    hold on to this lock. Returns True if it is safe to continue execution,
    False if not.
    """
    try:
        lh = open(LOCK_FILE_LAUNCHER, 'r')
    except FileNotFoundError:  # noqa: F821
        # Updater may not have run yet during this session
        return True

    try:
        # Obtain a nonblocking, shared lock
        fcntl.lockf(lh, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except IOError:
        sdlog.error("Error obtaining lock on '{}'. "
                    "Preflight updater may already be running."
                    .format(LOCK_FILE_LAUNCHER))
        return False

    return True


def obtain_notify_lock():
    """
    Obtain an exclusive lock during the execution of this process.
    """
    try:
        lh = open(LOCK_FILE_NOTIFIER, 'w')
    except PermissionError:  # noqa: F821
        sdlog.error("Error writing to lock file '{}'. User may lack the "
                    "required permissions."
                    .format(LOCK_FILE_NOTIFIER))
        return None

    try:
        # Obtain an exclusive, nonblocking lock
        fcntl.lockf(lh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sdlog.error("Error obtaining lock on '{}'. "
                    "Notification may already be displaying."
                    .format(LOCK_FILE_NOTIFIER))
        return None

    return lh


def warning_should_be_shown():
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
            sys.exit(1)

        now = datetime.now()
        updated_seconds_ago = (now - last_update_time).total_seconds()
        updated_hours_ago = updated_seconds_ago / 60 / 60

    # Obtain current uptime
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
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


def configure_logging():
    """
    All logging related settings are set up by this function.
    """

    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    formatter = logging.Formatter((LOG_FORMAT))

    handler = TimedRotatingFileHandler(LOG_FILE)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.addHandler(handler)
