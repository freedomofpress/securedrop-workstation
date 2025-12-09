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
    SD_TAG,
    SD_TEMPLATE_SMALL,
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Log_Common,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper("sd-log")


@pytest.mark.configuration
def test_sd_log_package_installed(qube):
    assert qube.package_is_installed("securedrop-log")


@pytest.mark.configuration
def test_sd_log_redis_is_installed(qube):
    assert qube.package_is_installed("redis")
    assert qube.package_is_installed("redis-server")


@pytest.mark.configuration
def test_log_utility_installed(qube):
    assert qube.fileExists("/usr/sbin/securedrop-log-saver")
    assert qube.fileExists("/etc/qubes-rpc/securedrop.Log")


@pytest.mark.configuration
def test_sd_log_has_no_custom_rsyslog(qube):
    assert not qube.fileExists("/etc/rsyslog.d/sdlog.conf")


@pytest.mark.configuration
def test_sd_log_service_running(qube):
    assert qube.service_is_active("securedrop-log-server")


@pytest.mark.configuration
def test_redis_service_running(qube):
    assert qube.service_is_active("redis")


@pytest.mark.configuration
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
        try:
            subprocess.check_call(["qvm-run", vm.name, f"sudo echo {token}"])
        except subprocess.CalledProcessError:
            raise RuntimeError(f"failed to insert token for logging check on VM '{vm.name}")

    for vm in sdw_tagged_vms:
        if vm.name in skip:
            continue
        syslog = f"/home/user/QubesIncomingLogs/{vm.name}/syslog.log"
        if vm.name in no_log_vms:
            assert not qube.fileExists(syslog)
        else:
            assert token in qube.get_file_contents(syslog)


@pytest.mark.configuration
def test_log_dirs_properly_named(qube):
    cmd_output = qube.run("ls -1 /home/user/QubesIncomingLogs")
    log_dirs = cmd_output.split("\n")
    # Confirm we don't have 'host' entries from Whonix VMs
    assert "host" not in log_dirs


@pytest.mark.configuration
def test_sd_log_service(qube):
    assert qube.service_is_active("securedrop-log-server")


@pytest.mark.provisioning
def test_sd_log_config(qube, config, all_vms):
    """
    Confirm that qvm-prefs match expectations for the sd-log VM.
    """
    vm = all_vms["sd-log"]
    nvm = vm.netvm
    assert nvm is None
    assert vm.template.name == SD_TEMPLATE_SMALL
    assert vm.autostart
    assert not vm.provides_network
    assert not vm.template_for_dispvms
    assert vm.features["service.securedrop-log-server"] == "1"
    assert vm.features["service.securedrop-logging-disabled"] == "1"
    # See sd-log.sls "sd-install-epoch" feature
    assert vm.features["sd-install-epoch"] == "1001"

    assert not vm.template_for_dispvms
    assert SD_TAG in vm.tags
    # Check the size of the private volume
    # Should be same of config.json
    # >>> 1024 * 1024 * 5 * 1024
    size = config["vmsizes"]["sd_log"]
    vol = vm.volumes["private"]
    assert vol.size == size * 1024 * 1024 * 1024
