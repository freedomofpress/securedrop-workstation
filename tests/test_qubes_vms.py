import pytest

from tests.base import CURRENT_FEDORA_TEMPLATE

"""
Ensures that the upstream, Qubes-maintained VMs are
sufficiently up to date.
"""


@pytest.mark.provisioning
@pytest.mark.parametrize(
    "sys_vm_name",
    [
        "sys-firewall",
        "sys-net",
        "sys-usb",
        "default-mgmt-dvm",
    ],
)
def test_current_fedora_for_sys_vms(sys_vm_name, all_vms):
    """
    Checks that all sys-* VMs are configured to use an up-to-date version of Fedora.
    """
    # Look up all VMs that use the current Fedora as their TemplateVM.
    fedora_based_vms = all_vms[CURRENT_FEDORA_TEMPLATE].derived_vms
    sys_vm = all_vms[sys_vm_name]
    assert (
        sys_vm in fedora_based_vms
    ), f"VM {sys_vm_name} should have {CURRENT_FEDORA_TEMPLATE} as TemplateVM"
