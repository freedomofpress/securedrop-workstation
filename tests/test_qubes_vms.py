import pytest

from tests.base import CURRENT_FEDORA_DVM, CURRENT_FEDORA_TEMPLATE

"""
Ensures that the upstream, Qubes-maintained VMs are
sufficiently up to date.
"""


@pytest.mark.provisioning
@pytest.mark.parametrize(
    ("sys_vm", "expected_templates"),
    [
        ("sys-firewall", [CURRENT_FEDORA_TEMPLATE, CURRENT_FEDORA_DVM]),
        ("sys-net", [CURRENT_FEDORA_TEMPLATE]),
        ("sys-usb", [CURRENT_FEDORA_TEMPLATE, f"sd-{CURRENT_FEDORA_DVM}"]),
        ("default-mgmt-dvm", [CURRENT_FEDORA_TEMPLATE]),
    ],
)
def test_current_fedora_for_sys_vms(sys_vm, expected_templates, all_vms):
    """
    Checks that all sys-* VMs are configured to use an up-to-date version of Fedora.
    """
    vm = all_vms[sys_vm]

    assert vm.template.name in expected_templates, (
        f"Unexpected template for {sys_vm}\n"
        + f"Current: {vm.template.name}\n"
        + "Expected: {}".format(", ".join(expected_templates))
    )
