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
    return re.findall(r"[A-F0-9]{40}", gpg_output)


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
        return _extract_fingerprints(local_results.decode())


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
    return _extract_fingerprints(remote_results.decode())


@pytest.mark.configuration
def test_sd_gpg_timeout(qube):
    assert "QUBES_GPG_AUTOACCEPT=2147483647" in qube.run("env")


def test_sd_gpg_timeout_not_in_home_profile(qube):
    """This is mostly a test against lingering state"""
    if qube.vm.klass == "DispVM":
        pytest.fail("Test may no longer be needed")
    assert "QUBES_GPG_AUTOACCEPT" not in qube.run("cat /home/user/.profile")


@pytest.mark.configuration
def test_dot_profile_was_reset(qube):
    """
    Past state is getting cleaned

    Previously .profile was edited with Salt. This tests that past state is
    getting cleaned.
    """

    if qube.vm.klass == "DispVM":
        pytest.fail("Test may no longer be needed")

    # $HOME/.profile is successfully getting reset
    assert qube.run("diff /etc/skel/.profile /home/user/.profile") == ""

    # Reset in current run (in practice this gets reset when a shell opened)
    time_in_vm = int(qube.run("date +%s"))
    profile_modif_time = int(qube.run("stat --format %Y /home/user/.profile"))
    assert -30 < time_in_vm - profile_modif_time < 30


@pytest.mark.configuration
def test_local_key_in_remote_keyring(config_fingerprint, dom0_fingerprint, vm_fingerprint):
    """
    Verify the key present in dom0 and sd-gpg matches what's configured in config.json

    This also verifies only one secret key is in the keyring.
    """
    assert dom0_fingerprint == [config_fingerprint]
    assert vm_fingerprint == [config_fingerprint]


@pytest.mark.configuration
def test_local_key_in_remote_keyring_clean(qube, config_fingerprint):
    """
    Confirm key presence in sd-gpg, but simulate clean environment.

    This test exists because until sd-gpg is disposable or we run the test in a
    perfectly new deployment, there is now way to tell if the key was already
    there from before or if it was in fact placed there by the workstation version
    under testing.
    """
    if qube.vm.klass == "DispVM":
        # This condition is just a note for developers
        pytest.fail("Test can be removed, as we no longer need to test against clean slate")

    tmp_dir = qube.run("mktemp -d")
    qube.run(f"GNUPGHOME={tmp_dir} securedrop-get-secret-keys")
    vm_fingerprints = _extract_fingerprints(
        qube.run(f"GNUPGHOME={tmp_dir} /usr/bin/gpg --list-secret-keys")
    )
    assert vm_fingerprints == [config_fingerprint]


@pytest.mark.configuration
def test_logging_disabled(qube):
    # Logging to sd-log should be disabled on sd-gpg
    assert not qube.fileExists("/etc/rsyslog.d/sdlog.conf")
    assert qube.fileExists("/var/run/qubes-service/securedrop-logging-disabled")


@pytest.mark.configuration
def test_sd_proxy_services(qube):
    assert qube.service_is_active("securedrop-get-secret-keys")


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
    assert vm.features["service.securedrop-get-secret-keys"] == "1"
    assert vm.features["service.securedrop-gpg-dismiss-prompt"] == "1"
    assert SD_TAG in vm.tags
