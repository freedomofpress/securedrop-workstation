"""
Utility functions used by both the launcher and notifier scripts
"""

import fcntl
import os
import logging
import subprocess

from logging.handlers import TimedRotatingFileHandler
from shlex import quote

# The directory where status files and logs are stored
BASE_DIRECTORY = os.path.join(os.path.expanduser("~"), ".securedrop_launcher")

# Directory for lock files to avoid contention or multiple instantiation.
LOCK_DIRECTORY = os.path.join("/run/user", str(os.getuid()))

# Folder where logs are stored
LOG_DIRECTORY = os.path.join(BASE_DIRECTORY, "logs")

# Shared error string
LOCK_ERROR = "Error obtaining lock on '{}'. Process may already be running."

# Format for those logs
LOG_FORMAT = (
    "%(asctime)s - %(name)s:%(lineno)d(%(funcName)s) " "%(levelname)s: %(message)s"
)

sdlog = logging.getLogger(__name__)


def configure_logging(log_file):
    """
    All logging related settings are set up by this function.
    """

    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    formatter = logging.Formatter((LOG_FORMAT))

    handler = TimedRotatingFileHandler(os.path.join(LOG_DIRECTORY, log_file))
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.addHandler(handler)


def obtain_lock(basename):
    """
    Obtain an exclusive lock during the execution of this process.
    """
    lock_file = os.path.join(LOCK_DIRECTORY, basename)
    try:
        lh = open(lock_file, "w")
    except PermissionError:  # noqa: F821
        sdlog.error(
            "Error writing to lock file '{}'. User may lack the "
            "required permissions.".format(lock_file)
        )
        return None

    try:
        # Obtain an exclusive, nonblocking lock
        fcntl.lockf(lh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sdlog.error(LOCK_ERROR.format(lock_file))
        return None

    return lh


def can_obtain_lock(basename):
    """
    We temporarily obtain a shared, nonblocking lock to a lockfile to determine
    whether the associated process is currently running. Returns True if it is
    safe to continue execution (no lock conflict), False if not.

    `basename` is the basename of a lockfile situated in the LOCK_DIRECTORY.
    """
    lock_file = os.path.join(LOCK_DIRECTORY, basename)
    try:
        lh = open(lock_file, "r")
    except FileNotFoundError:  # noqa: F821
        # Process may not have run during this session, safe to continue
        return True

    try:
        # Obtain a nonblocking, shared lock
        fcntl.lockf(lh, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except IOError:
        sdlog.error(LOCK_ERROR.format(lock_file))
        return False

    return True


def is_conflicting_process_running(list):
    """
    Check if any process of the given name is currently running. Aborts on the
    first match.
    """
    for name in list:
        result = subprocess.run(args=["pgrep", quote(name)], stdout=subprocess.DEVNULL)
        if result.returncode == 0:
            sdlog.error("Conflicting process '{}' is currently running.".format(name))
            return True
    return False
