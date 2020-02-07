"""
Utility functions used by both the launcher and notifier scripts
"""
import os
import logging

from logging.handlers import TimedRotatingFileHandler

# The directory where status files and logs are stored
BASE_DIRECTORY = os.path.join(os.path.expanduser("~"), ".securedrop_launcher")

# Folder where logs are stored
LOG_DIRECTORY = os.path.join(BASE_DIRECTORY, "logs")

# Format for those logs
LOG_FORMAT = "%(asctime)s - %(name)s:%(lineno)d(%(funcName)s) " "%(levelname)s: %(message)s"


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
