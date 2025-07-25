#!/usr/bin/env python3
import subprocess

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


class Dom0TestException(Exception):
    pass


def systemd_verify_sd_units(services: list[str] = None, is_userspace: bool = False) -> bool:
    """
    Helper. systemd-analyze services to check if well-formed.
    If no units specified, `systemd-analyze` will run without
    the `verify` command.

    Option to run against user units via `is_userspace` boolean.
    """
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


def systemd_list_sd_units(is_userspace: bool = False) -> str | None:
    """
    Helper. List systemd units and pattern-match. Option to specify user units.
    """
    args = SYSTEMD_LIST_UNITS
    if is_userspace:
        args.append("--user")
    try:
        return subprocess.check_output(args).decode()
    except subprocess.CalledProcessError:
        user_flag = "user" if is_userspace else ""
        raise Dom0TestException(f"Failed to list {user_flag} units")


def get_unit_last_status(unit: str, is_userspace: bool = False) -> tuple[str, str]:
    """
    Helper. Given a systemd unit (.service/.timer), parse last
    unit status. Option to specify user unit via is_userspace flag.
    """
    args = ["systemctl", "status", unit]
    if is_userspace:
        args.append("--user")
    status = None
    try:
        status = subprocess.check_output(args).decode()
    except subprocess.CalledProcessError:
        raise Dom0TestException(f"Failed to get last unit status: {unit}")

    if status:
        # Parse output and return tuple of (code, status)
        status_lines = status.split("\n")
        for line in status_lines:
            if line.startswith("Main PID"):
                # format:
                # "Main PID: $pid (code=code, status=retcode/STATUS)"
                return line.split("(")[-1].replace(")", "").split(", ")

    raise Dom0TestException("Could not parse status")


def units_present_enabled(expected_units: list[str], is_userspace: bool = False):
    """
    Helper. Check list of expected units and assert that they are
    enabled. Option to specify user units.
    """
    # Format of systemctl list-unit-files is UNIT_FILE\tSTATE\tPRESET
    unit_count = 0
    units = systemd_list_sd_units(is_userspace=is_userspace).strip().split("\n")
    for unit_and_status in units:
        unit = unit_and_status.split()
        if unit not in expected_units:
            raise Dom0TestException(f"Unexpected unit file {unit[0]} (Expected: {expected_units})")
        else:
            # Right now, all units are enabled
            unit_count += 1
            if unit[1] != "enabled":
                raise Dom0TestException(f"{unit[0]} is not enabled")

            if get_unit_last_status(unit[0], is_userspace) is not SYSTEMD_EXIT_SUCCESS:
                raise Dom0TestException(f"{unit[0]} not {SYSTEMD_EXIT_SUCCESS}")

    expected = len(expected_units)
    if unit_count != expected:
        raise Dom0TestException(f"Missing units (got {unit_count}, need {expected})")

    # If we got here, we have exactly the correct number of units, and
    # they are all enabled, and their last runs were all successful
    return True


### Begin Tests ###


def test_system_units_well_formed():
    assert systemd_verify_sd_units(SYSTEM_UNITS)


def test_user_units_well_formed():
    assert systemd_verify_sd_units(USER_UNITS, is_userspace=True)


def test_system_units_present_enabled():
    assert units_present_enabled(SYSTEM_UNITS)


def test_user_units_present_enabled():
    assert units_present_enabled(USER_UNITS, is_userspace=True)
