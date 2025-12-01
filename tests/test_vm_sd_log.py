"""
Integration tests for validating SecureDrop Workstation config,
specifically for the "sd-log" VM and related functionality.
"""

import secrets
import string
import subprocess

import pytest

from tests.base import (
    DEBIAN_VERSION,
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Log_Common,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper("sd-log")


def test_sd_log_package_installed(qube):
    assert qube.package_is_installed("securedrop-log")


def test_sd_log_redis_is_installed(qube):
    assert qube.package_is_installed("redis")
    assert qube.package_is_installed("redis-server")


def test_log_utility_installed(qube):
    assert qube.fileExists("/usr/sbin/securedrop-log-saver")
    assert qube.fileExists("/etc/qubes-rpc/securedrop.Log")


def test_sd_log_has_no_custom_rsyslog(qube):
    assert not qube.fileExists("/etc/rsyslog.d/sdlog.conf")


def test_sd_log_service_running(qube):
    assert qube.service_is_active("securedrop-log-server")


def test_redis_service_running(qube):
    assert qube.service_is_active("redis")


def test_logs_are_flowing(qube, sdw_tagged_vms):
    """
    To test that logs work, we run a unique command in each VM we care
    about that gets logged, and then check for that string in the logs.
    """
    # Random string, to avoid collisions with other test runs
    token = "".join(secrets.choice(string.ascii_uppercase) for _ in range(10))

    # base template doesn't have sd-log configured
    # TODO: test a sd-viewer based dispVM
    skip = [f"sd-base-{DEBIAN_VERSION}-template", "sd-viewer"]
    # VMs we expect logs will not go to
    no_log_vms = ["sd-gpg", "sd-log"]

    # We first run the command in each VM, and then do a second loop to
    # look for the token in the log entry, so there's enough time for the
    # log entry to get written.
    for vm in sdw_tagged_vms:
        if vm.name in skip:
            continue
        # The sudo call will make it into syslog
        subprocess.check_call(["qvm-run", vm.name, f"sudo echo {token}"])

    for vm in sdw_tagged_vms:
        if vm.name in skip:
            continue
        syslog = f"/home/user/QubesIncomingLogs/{vm.name}/syslog.log"
        if vm.name in no_log_vms:
            assert not qube.fileExists(syslog)
        else:
            assert token in qube.get_file_contents(syslog)


def test_log_dirs_properly_named(qube):
    cmd_output = qube.run("ls -1 /home/user/QubesIncomingLogs")
    log_dirs = cmd_output.split("\n")
    # Confirm we don't have 'host' entries from Whonix VMs
    assert "host" not in log_dirs
