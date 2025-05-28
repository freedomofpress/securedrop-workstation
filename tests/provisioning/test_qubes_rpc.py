import os
import subprocess

import pytest

from .. import SD_VMS_TAG

RETURNCODE_SUCCESS = 0
RETURNCODE_ERROR = 1
RETURNCODE_DENIED = 126


def _qrexec(source_vm, dest_vm, policy_name):
    cmd = [
        "qvm-run",
        "--pass-io",
        source_vm,
        f"qrexec-client-vm {dest_vm} {policy_name}",
    ]
    p = subprocess.run(cmd, input="test", capture_output=True, text=True, check=False)
    return p.returncode


@pytest.fixture(scope="module")
def running_sd_vms(app):
    """
    Running SD-tagged Running VMs
    """
    vms_with_tag = []
    for vm in app.domains:
        if vm.name != "dom0" and vm.is_running():
            if SD_VMS_TAG in list(vm.tags):
                vms_with_tag.append(vm.name)
    return vms_with_tag


@pytest.fixture(scope="module")
def running_non_sd_vms(app, running_sd_vms):
    """
    Running VMs not tagged with SD_VMS_TAG
    """
    return [vm for vm in app.domains if vm not in running_sd_vms]


def test_policies_exist():
    """verify the policies are installed"""
    assert os.path.exists("/etc/qubes/policy.d/31-securedrop-workstation.policy")
    assert os.path.exists("/etc/qubes/policy.d/32-securedrop-workstation.policy")


# securedrop.Log from @tag:sd-workstation to sd-log should be allowed
def test_sdlog_from_sdw_to_sdlog_allowed(running_sd_vms):
    for vm in running_sd_vms:
        if vm != "sd-log":
            assert _qrexec(vm, "sd-log", "securedrop.Log") == RETURNCODE_SUCCESS


# securedrop.Log from anything else to sd-log should be denied
def test_sdlog_from_other_to_sdlog_denied(running_non_sd_vms):
    for vm in running_non_sd_vms:
        if vm != "sd-log":
            assert _qrexec(vm, "sd-log", "securedrop.Log") == RETURNCODE_DENIED


# securedrop.Proxy from sd-app to sd-proxy should be allowed
def test_sdproxy_from_sdapp_to_sdproxy_allowed():
    # proxy RPC returns an error due to malformed input, but it still goes through
    # (i.e. not DENIED)
    assert _qrexec("sd-app", "sd-proxy", "securedrop.Proxy") == RETURNCODE_ERROR


# securedrop.Proxy from anything else to sd-proxy should be denied
def test_sdproxy_from_other_to_sdproxy_denied():
    assert _qrexec("sys-net", "sd-proxy", "securedrop.Proxy") == RETURNCODE_DENIED
    assert _qrexec("sys-firewall", "sd-proxy", "securedrop.Proxy") == RETURNCODE_DENIED


# qubes.Gpg, qubes.GpgImportKey, and qubes.Gpg2 from anything else to sd-gpg should be denied
def test_qubesgpg_from_other_to_sdgpg_denied():
    assert _qrexec("sys-net", "sd-gpg", "qubes.Gpg") == RETURNCODE_DENIED
    assert _qrexec("sys-firewall", "sd-gpg", "qubes.Gpg") == RETURNCODE_DENIED
    assert _qrexec("sys-net", "sd-gpg", "qubes.GpgImportKey") == RETURNCODE_DENIED
    assert _qrexec("sys-firewall", "sd-gpg", "qubes.GpgImportKey") == RETURNCODE_DENIED
    assert _qrexec("sys-net", "sd-gpg", "qubes.Gpg2") == RETURNCODE_DENIED
    assert _qrexec("sys-firewall", "sd-gpg", "qubes.Gpg2") == RETURNCODE_DENIED
