#!/usr/bin/python3
"""
Utility script for SecureDrop Workstation. Launches the SecureDrop Workstation
updater on boot. It will prompt users to apply template and dom0 updates
"""

import logging
import os
import subprocess
import time

SCRIPT_NAME = os.path.basename(__file__)
logger = logging.getLogger(SCRIPT_NAME)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    # Wait for the dom0 GUI widgets to load
    # If we don't wait, a "Houston, we have a problem..." message is displayed
    # to the user.
    time.sleep(5)

    subprocess.check_call(["sdw-updater"])
