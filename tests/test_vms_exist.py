import pytest

from tests.base import (
    SD_DVM_TEMPLATES,
    SD_TAG,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    SD_TEMPLATES,
    SD_UNTAGGED_DEPRECATED_VMS,
    SD_VMS,
)


def test_all_sdw_vms_present(all_vms, sdw_tagged_vms):
    """
    Confirm that all SDW-managed VMs are present on the system.
    Seeks to detect errors in provisioning that result in VMs
    failing to be created. Compares to a hardcoded list in fixtures.
    """
    # This integration test suite will create an ephemeral "sd-viewer-disposable" VM,
    # and then destroy it, post-test-run. We can't assume the VM exists for general tests,
    # so we exclude it from the general shared-state fixture. The sd-viewer test suite
    # will handle targeting it with the appropriate tests, then clean up the DispVM.
    sdw_tagged_vm_names = [vm for vm in sdw_tagged_vms if vm != "sd-viewer-disposable"]

    expected_vm_names = set(SD_VMS + SD_DVM_TEMPLATES + SD_TEMPLATES)

    assert set(sdw_tagged_vm_names) == set(expected_vm_names)

    # Check for untagged VMs
    for vm_name in SD_UNTAGGED_DEPRECATED_VMS:
        assert vm_name not in all_vms


def test_default_dispvm(all_vms, sdw_tagged_vms):
    """Verify the default DispVM is none for all except sd-app and sd-devices"""
    for vm_name in sdw_tagged_vms:
        vm = all_vms[vm_name]
        if vm_name == "sd-app":
            assert vm.default_dispvm.name == "sd-viewer"
        else:
            assert vm.default_dispvm is None, f"{vm_name} has dispVM set"


def test_sd_whonix_absent(all_vms):
    """
    The sd-whonix once existed to proxy sd-proxy's traffic through Tor.
    But we've since removed it and included a Tor proxy in sd-proxy.
    """
    assert "sd-whonix" not in all_vms


WHONIX_QUBES = [
    "whonix-workstation-17",
    "whonix-gateway-17",
    "sys-whonix",
    "anon-whonix",
    "whonix-workstation-17-dvm",
]


@pytest.mark.parametrize("whonix_vm_name", WHONIX_QUBES)
def test_whonix_vms_reset(whonix_vm_name, all_vms):
    """
    Whonix templates used to be modified by the workstation (<=1.4.0).
    Ensure they were properly reset.
    """

    # skip check on non-existent qubes
    if whonix_vm_name not in all_vms:
        pytest.skip(f"skipping qvm-prefs check on non-existent qube: '{whonix_vm_name}'")
    qube = all_vms[whonix_vm_name]
    assert qube.property_is_default("kernelopts")


def test_sd_small_template(all_vms):
    """
    Confirm that the "small" version of the SDW TemplateVM is configured correctly.
    """
    vm = all_vms[SD_TEMPLATE_SMALL]
    assert vm.netvm is None
    assert SD_TAG in vm.tags


def test_sd_large_template(all_vms):
    """
    Confirm that the "large" version of the SDW TemplateVM is configured correctly.
    """
    vm = all_vms[SD_TEMPLATE_LARGE]
    assert vm.netvm is None
    assert SD_TAG in vm.tags
