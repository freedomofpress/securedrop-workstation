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
    sys_vm = all_vms[sys_vm_name]
    if sys_vm.klass == "DispVM":
        assert sys_vm.template.template.name == CURRENT_FEDORA_TEMPLATE
    else:
        assert sys_vm.template.name == CURRENT_FEDORA_TEMPLATE
