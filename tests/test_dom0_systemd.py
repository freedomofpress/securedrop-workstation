#!/usr/bin/env python3
import subprocess
import unittest

# .spec file shows which units are shipped with rpm
SYSTEM_UNITS = ["securedrop-logind-override-disable.service"]

USER_UNITS = [
    "securedrop-user-xfce-icon-size.service",
    "securedrop-user-xfce-settings.service",
    "sdw-notify.timer",
]

# list all system unit files (append "--user" for user files)
# that match our naming convention
SYSTEMD_LIST_UNITS = ["systemctl", "--legend=false", "list-unit-files", "--all", "*securedrop*"]

# from systemctl status format
SYSTEMD_EXIT_SUCCESS = "status=0/SUCCESS"


class Dom0_Systemd(unittest.TestCase):
    def _systemd_verify_sd_units(
        self, services: list[str] = None, is_userspace: bool = False
    ) -> bool:
        args = ["systemd-analyze"]
        if is_userspace:
            args.append("--user")
        if services:
            args.append("verify")
            args.extend(services)
        try:
            # systemd-analyze [--user] verify [service1.service service2.service]
            # exits 0 on success
            subprocess.check_call(args)
            return True
        except subprocess.CalledProcessError:
            return False

    def _systemd_list_sd_units(self, is_userspace: bool = False) -> str:
        args = SYSTEMD_LIST_UNITS
        if is_userspace:
            args.append("--user")
        try:
            return subprocess.check_output(args).decode()
        except subprocess.CalledProcessError:
            self.fail("Error listing units")

    def _get_unit_last_status(self, unit: str, is_userspace: bool = False) -> tuple[str, str]:
        args = ["systemctl", "status", unit]
        if is_userspace:
            args.append("--user")
        status = None
        try:
            status = subprocess.check_output(args).decode()
        except subprocess.CalledProcessError:
            self.fail(f"Error checking status for {unit}")

        if status:
            # Parse output and return tuple of (code, status)
            status_lines = status.split("\n")
            for line in status_lines:
                if line.startswith("Main PID"):
                    # format:
                    # "Main PID: $pid (code=code, status=retcode/STATUS)"
                    return line.split("(")[-1].replace(")", "").split(", ")

        self.fail("Could not parse status")
        return None

    def _units_present_enabled(self, expected_units: list[str], is_userspace: bool = False):
        # Format of systemctl list-unit-files is UNIT_FILE\tSTATE\tPRESET
        unit_count = 0
        units = self._systemd_list_sd_units(is_userspace=is_userspace).split("\n")
        for unit_and_status in units:
            unit = unit_and_status.split()
            if unit not in expected_units:
                self.fail(f"Unexpected unit file {unit[0]}")
            else:
                # Right now, all units are enabled
                unit_count += 1
                if unit[1] != "enabled":
                    self.fail(f"{unit[0]} is not enabled")

                if self._get_unit_last_status(unit[0], is_userspace) is not SYSTEMD_EXIT_SUCCESS:
                    self.fail(f"{unit[0]} not {SYSTEMD_EXIT_SUCCESS}")

        expected = len(expected_units)
        if unit_count != expected:
            self.fail(f"Missing units (got {unit_count}, need {expected})")

        # If we got here, we have exactly the correct number of units, and
        # they are all enabled, and their last runs were all successful
        return True

    def test_system_units_well_formed(self):
        assert self._systemd_verify_sd_units(SYSTEM_UNITS)

    def test_user_units_well_formed(self):
        assert self._systemd_verify_sd_units(USER_UNITS, is_userspace=True)

    def test_system_units_present_enabled(self):
        self._units_present_enabled(SYSTEM_UNITS)

    def test_user_units_present_enabled(self):
        self._units_present_enabled(USER_UNITS, is_userspace=True)
