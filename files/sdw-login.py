#!/usr/bin/python3
"""
Utility script for SecureDrop Workstation. Launches the SecureDrop Workstation
updater on boot. It will prompt users to apply template and dom0 updates
"""

import argparse
import logging
import os
import subprocess
import time

SCRIPT_NAME = os.path.basename(__file__)
logger = logging.getLogger(SCRIPT_NAME)
logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch-app", action="store_true")
    args = parser.parse_args()

    # Wait for the dom0 GUI widgets to load
    # If we don't wait, a "Houston, we have a problem..." message is displayed
    # to the user.
    time.sleep(5)

    cmd = ["sdw-updater"]
    if args.launch_app:
        cmd.append("--launch-app")

    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
