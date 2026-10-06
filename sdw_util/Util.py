"""
Utility functions used by both the updater and notifier scripts
"""

import fcntl
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import IO

# The directory where status files and logs are stored
BASE_DIRECTORY = os.path.join(os.path.expanduser("~"), ".securedrop_updater")

# Directory for lock files to avoid contention or multiple instantiation.
LOCK_DIRECTORY = os.path.join("/run/user", str(os.getuid()))

# Folder where logs are stored
LOG_DIRECTORY = os.path.join(BASE_DIRECTORY, "logs")

# File that contains Qubes version information (overridden by tests)
OS_RELEASE_FILE = "/etc/os-release"

# Shared error string
LOCK_ERROR = "Error obtaining lock on '{}'. Process may already be running."

# Format for those logs
LOG_FORMAT = "%(asctime)s - %(name)s:%(lineno)d(%(funcName)s) " "%(levelname)s: %(message)s"

# Namespace for primary logger, additional namespaces should be defined by module user
SD_LOGGER_PREFIX = "sd"

sdlog = logging.getLogger(SD_LOGGER_PREFIX + "." + __name__)


def configure_logging(
    log_file: str, logger_namespace: str = SD_LOGGER_PREFIX, backup_count: int = 0
) -> None:
    """
    All logging related settings are set up by this function.

    `log_file` - the filename
    `logger_namespace - the prefix used for all log events by this logger
    `backup_count` - if nonzero, at most backup_count files will be kept
    """

    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    formatter = logging.Formatter(LOG_FORMAT)

    handler = TimedRotatingFileHandler(
        os.path.join(LOG_DIRECTORY, log_file), backupCount=backup_count
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    log = logging.getLogger(logger_namespace)
    log.setLevel(logging.INFO)
    log.addHandler(handler)


def obtain_lock(basename: str) -> IO[str] | None:
    """
    Obtain an exclusive lock during the execution of this process.
    """
    lock_file = os.path.join(LOCK_DIRECTORY, basename)
    try:
        lh = open(lock_file, "w")
    except PermissionError:
        sdlog.error(
            f"Error writing to lock file '{lock_file}'. User may lack the required permissions."
        )
        return None

    try:
        # Obtain an exclusive, nonblocking lock
        fcntl.lockf(lh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sdlog.error(LOCK_ERROR.format(lock_file))
        return None

    return lh


def get_qubes_version() -> str | None:
    """
    Helper function for checking the Qubes version. Returns None if not on Qubes.
    """
    is_qubes = False
    version = None
    try:
        with open(OS_RELEASE_FILE) as f:
            for line in f:
                try:
                    key, value = line.rstrip().split("=")
                except ValueError:
                    continue

                if key == "NAME" and "qubes" in value.lower():
                    is_qubes = True
                if key == "VERSION":
                    version = value
    except FileNotFoundError:
        return None

    if not is_qubes:
        return None

    return version


def get_logger(prefix: str = SD_LOGGER_PREFIX, module: str | None = None) -> logging.Logger:
    if module is None:
        return logging.getLogger(prefix)

    return logging.getLogger(prefix + "." + module)
