import json
import subprocess
import unittest

from tests.base import (
    SD_DVM_TEMPLATES,
    SD_TAG,
    SD_TEMPLATE_BASE,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    SD_TEMPLATES,
    SD_UNTAGGED_DEPRECATED_VMS,
    SD_VMS,
)

with open("config.json") as f:
    CONFIG = json.load(f)


def test_all_sdw_vms_present(all_vms, sdw_tagged_vms):
    """
    Confirm that all SDW-managed VMs are present on the system.
    Seeks to detect errors in provisioning that result in VMs
    failing to be created. Compares to a hardcoded list in fixtures.
    """
    sdw_tagged_vm_names = [vm.name for vm in sdw_tagged_vms]
    expected_vms = set(SD_VMS + SD_DVM_TEMPLATES + SD_TEMPLATES)

    assert set(sdw_tagged_vm_names) == set(expected_vms)

    # Check for untagged VMs
    for vm_name in SD_UNTAGGED_DEPRECATED_VMS:
        assert vm_name not in all_vms


@unittest.skipIf(CONFIG["environment"] != "prod", "Skipping on non-prod system")
def test_internal(all_vms):
    assert all_vms["sd-proxy-dvm"].features.get("internal") == "1"
    assert all_vms["sd-viewer"].features.get("internal") == "1"


def test_grsec_kernel(sdw_tagged_vms):
    """
    Confirms expected grsecurity-patched kernel is running.
    """
    # base doesn't have kernel configured
    # TODO: test in sd-viewer based dispVM
    exceptions = [SD_TEMPLATE_BASE, "sd-viewer"]

    for vm in sdw_tagged_vms:
        if vm.name in exceptions:
            continue
        # Running custom kernel in PVH mode requires pvgrub2-pvh
        assert vm.virt_mode == "pvh"
        assert vm.kernel == "pvgrub2-pvh"

        # Check running kernel is grsecurity-patched
        stdout, stderr = vm.run("uname -r")
        assert stdout.decode().strip().endswith("-grsec-workstation")
        check_service_running(vm, "paxctld")


def check_service_running(vm, service, running=True):
    """
    Ensures a given service is running inside a given VM.
    Uses systemctl is-active to query the service state.
    """
    try:
        cmd = f"systemctl is-active {service}"
        stdout, stderr = vm.run(cmd)
        service_status = stdout.decode("utf-8").rstrip()
    except subprocess.CalledProcessError as e:
        if e.returncode == 3:
            service_status = "inactive"
        else:
            raise e
    assert service_status == "active" if running else "inactive"


def test_default_dispvm(sdw_tagged_vms):
    """Verify the default DispVM is none for all except sd-app and sd-devices"""
    for vm in sdw_tagged_vms:
        if vm.name == "sd-app":
            assert vm.default_dispvm.name == "sd-viewer"
        else:
            assert vm.default_dispvm is None, f"{vm.name} has dispVM set"


def test_sd_whonix_absent(all_vms):
    """
    The sd-whonix once existed to proxy sd-proxy's traffic through Tor.
    But we've since removed it and included a Tor proxy in sd-proxy.
    """
    assert "sd-whonix" not in all_vms


def test_whonix_vms_reset(all_vms):
    """
    Whonix templates used to be modified by the workstation (<=1.4.0).
    Ensure they were properly reset.
    """

    whonix_qubes = [
        "whonix-workstation-17",
        "whonix-gateway-17",
        "sys-whonix",
        "anon-whonix",
        "whonix-workstation-17-dvm",
    ]
    for qube_name in whonix_qubes:
        if qube_name not in all_vms:
            # skip check on existent qubes
            continue
        qube = all_vms[qube_name]
        assert qube.property_is_default("kernelopts")


def test_sd_small_template(all_vms):
    # Kernel check is handled in test_grsec_kernel
    vm = all_vms[SD_TEMPLATE_SMALL]
    nvm = vm.netvm
    assert nvm is None
    assert SD_TAG in vm.tags


def test_sd_large_template(all_vms):
    # Kernel check is handled in test_grsec_kernel
    vm = all_vms[SD_TEMPLATE_LARGE]
    nvm = vm.netvm
    assert nvm is None
    assert SD_TAG in vm.tags
