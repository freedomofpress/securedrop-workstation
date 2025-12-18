"""
Integration tests for validating SecureDrop Workstation config,
specifically for the "sd-gpg" VM and related functionality.
"""

import re
import subprocess
import tempfile

import pytest

from tests.base import (
    SD_TAG,
    SD_TEMPLATE_SMALL,
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Gpg_Common,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper("sd-gpg")


def _extract_fingerprints(gpg_output):
    """Helper method to extract fingerprints from GPG command output"""
    return re.findall(r"[A-F0-9]{40}", gpg_output.decode())


@pytest.fixture
def config_fingerprint(dom0_config):
    """
    Obtain the fingerprint explicitly configured in dom0 and injected into VMs.
    """
    return dom0_config["submission_key_fpr"]


@pytest.fixture
def dom0_fingerprint():
    """
    Obtain the fingerprint of the key actually present in dom0.
    """
    with tempfile.TemporaryDirectory() as d:
        gpg_env = {"GNUPGHOME": d}
        subprocess.check_call(
            ["gpg", "--import", "sd-journalist.sec"],
            env=gpg_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        local_results = subprocess.check_output(["gpg", "--list-secret-keys"], env=gpg_env)
        return _extract_fingerprints(local_results)


@pytest.fixture
def vm_fingerprint(qube):
    """
    Obtain fingerprints for all keys actually present in GPG VM
    """
    cmd = [
        "qvm-run",
        "-p",
        qube.name,
        "/usr/bin/gpg --list-secret-keys",
    ]
    remote_results = subprocess.check_output(cmd)
    return _extract_fingerprints(remote_results)


@pytest.mark.configuration
def test_sd_gpg_timeout(qube):
    line = "export QUBES_GPG_AUTOACCEPT=2147483647"
    qube.assertFileHasLine("/home/user/.profile", line)


@pytest.mark.configuration
def test_local_key_in_remote_keyring(config_fingerprint, dom0_fingerprint, vm_fingerprint):
    """
    Verify the key present in dom0 and sd-gpg matches what's configured in config.json

    This also verifies only one secret key is in the keyring.
    """
    assert dom0_fingerprint == [config_fingerprint]
    assert vm_fingerprint == [config_fingerprint]


@pytest.mark.configuration
def test_logging_disabled(qube):
    # Logging to sd-log should be disabled on sd-gpg
    assert not qube.fileExists("/etc/rsyslog.d/sdlog.conf")
    assert qube.fileExists("/var/run/qubes-service/securedrop-logging-disabled")


@pytest.mark.provisioning
def test_sd_gpg_config(all_vms):
    """
    Confirm that qvm-prefs match expectations for the sd-gpg VM.
    """
    vm = all_vms["sd-gpg"]
    nvm = vm.netvm
    assert nvm is None
    # No sd-gpg-template, since keyring is managed in $HOME
    assert vm.template.name == SD_TEMPLATE_SMALL
    assert vm.autostart
    assert not vm.provides_network
    assert not vm.template_for_dispvms
    assert vm.features["service.securedrop-logging-disabled"] == "1"
    assert SD_TAG in vm.tags
