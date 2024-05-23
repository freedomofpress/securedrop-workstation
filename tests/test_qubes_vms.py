import unittest

from base import CURRENT_FEDORA_DVM, CURRENT_FEDORA_TEMPLATE, CURRENT_WHONIX_VERSION
from qubesadmin import Qubes


class SD_Qubes_VM_Tests(unittest.TestCase):
    """
    Ensures that the upstream, Qubes-maintained VMs are
    sufficiently up to date.
    """

    def setUp(self):
        self.app = Qubes()

    def tearDown(self):
        pass

    def test_current_fedora_for_sys_vms(self):
        """
        Checks that all sys-* VMs are configured to use
        an up-to-date version of Fedora.
        """
        sys_vms = ["sys-firewall", "sys-net", "sys-usb", "default-mgmt-dvm"]
        sys_vms_maybe_disp = ["sys-firewall", "sys-usb"]
        sys_vms_custom_disp = ["sys-usb"]

        for sys_vm in sys_vms:
            vm = self.app.domains[sys_vm]
            wanted_templates = [CURRENT_FEDORA_TEMPLATE]
            if sys_vm in sys_vms_maybe_disp:
                if sys_vm in sys_vms_custom_disp:
                    wanted_templates.append(f"sd-{CURRENT_FEDORA_DVM}")
                else:
                    wanted_templates.append(CURRENT_FEDORA_DVM)

            self.assertTrue(
                vm.template.name in wanted_templates,
                f"Unexpected template for {sys_vm}\n"
                + f"Current: {vm.template.name}\n"
                + "Expected: {}".format(", ".join(wanted_templates)),
            )

    def test_current_whonix_vms(self):
        """
        Checks that the Qubes-maintained Whonix tooling
        has been updated to the most recent version.
        """
        whonix_vms = ["sys-whonix", "anon-whonix"]
        for whonix_vm in whonix_vms:
            vm = self.app.domains[whonix_vm]
            self.assertTrue(vm.template.name.startswith("whonix-"))
            self.assertTrue(vm.template.name.endswith("-" + CURRENT_WHONIX_VERSION))


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_Qubes_VM_Tests)
