#!/usr/bin/python3
"""
Sets the XFCE trust metadata on the SecureDrop desktop launcher so that
XFCE does not show an "untrusted application" warning when clicking it.
"""

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import dnf

CHECKSUM_PROPERTY = "metadata::xfce-exe-checksum"
DESKTOP_FILE_NAME = "press.freedom.SecureDropUpdater.desktop"


def dbus_env() -> dict:
    """Return environment with DBUS_SESSION_BUS_ADDRESS set for the current user."""
    env = os.environ.copy()
    env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{os.getuid()}/bus"
    return env


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 if the trust metadata is already correct, non-zero otherwise",
    )
    args = parser.parse_args()

    if dnf.rpm.detect_releasever("/") == "4.2":
        print("This script isn't needed on Qubes 4.2.", file=sys.stderr)
        sys.exit(0)

    if os.geteuid() == 0:
        print("This script must not be run as root.", file=sys.stderr)
        sys.exit(1)

    desktop_file = Path.home() / "Desktop" / DESKTOP_FILE_NAME

    if not desktop_file.is_file():
        print(f"sdw-desktop-trust: desktop file not found: {desktop_file}", file=sys.stderr)
        sys.exit(1)

    sha256 = checksum(desktop_file)

    if args.check:
        result = subprocess.run(
            ["gio", "info", f"--attributes={CHECKSUM_PROPERTY}", desktop_file],
            capture_output=True,
            text=True,
            env=dbus_env(),
            check=True,
        )
        if sha256 in result.stdout:
            print(f"sdw-desktop-trust: already set xfce-exe-checksum on {desktop_file}")
            sys.exit(0)
        else:
            print(f"sdw-desktop-trust: incorrect/missing xfce-exe-checksum on {desktop_file}")
            sys.exit(1)

    subprocess.run(
        ["gio", "set", "-t", "string", desktop_file, CHECKSUM_PROPERTY, sha256],
        check=True,
        env=dbus_env(),
    )
    print(f"sdw-desktop-trust: set xfce-exe-checksum on {desktop_file}")


if __name__ == "__main__":
    main()
