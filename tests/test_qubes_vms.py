import unittest

from qubesadmin import Qubes


CURRENT_FEDORA_VERSION = "30"
CURRENT_WHONIX_VERSION = "15"


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
        sys_vms = [
            "sys-firewall",
            "sys-net",
            "sys-usb",
            "default-mgmt-dvm",
        ]
        for sys_vm in sys_vms:
            vm = self.app.domains[sys_vm]
            self.assertTrue(vm.template.name == "fedora-" + CURRENT_FEDORA_VERSION)

    def test_current_whonix_vms(self):
        """
        Checks that the Qubes-maintained Whonix tooling
        has been updated to the most recent version.
        """
        whonix_vms = [
            "sys-whonix",
            "anon-whonix",
        ]
        for whonix_vm in whonix_vms:
            vm = self.app.domains[whonix_vm]
            self.assertTrue(vm.template.name.startswith("whonix-"))
            self.assertTrue(vm.template.name.endswith("-" + CURRENT_WHONIX_VERSION))


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Qubes_VM_Tests)
    return suite
