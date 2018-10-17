import unittest

from qubesadmin import Qubes
from base import WANTED_VMS


class SD_VM_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()

    def tearDown(self):
        pass

    def test_expected(self):
        vm_set = set(self.app.domains)
        for test_vm in WANTED_VMS:
            self.assertTrue(test_vm in vm_set)

    def test_sd_whonix_config(self):
        vm = self.app.domains["sd-whonix"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sys-firewall")
        self.assertTrue(vm.template == "sd-whonix-template")
        self.assertTrue(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)

    def test_sd_journalist_config(self):
        vm = self.app.domains["sd-journalist"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sd-whonix")
        self.assertTrue(vm.template == "sd-journalist-template")
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)

    def test_sd_svs_config(self):
        vm = self.app.domains["sd-svs"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == "sd-svs-template")
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)

    def test_sd_svs_disp_config(self):
        vm = self.app.domains["sd-svs-disp"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == "sd-svs-disp-template")
        self.assertFalse(vm.provides_network)
        self.assertTrue(vm.template_for_dispvms)

    def test_sd_gpg_config(self):
        vm = self.app.domains["sd-gpg"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        # No sd-gpg-template, since keyring is managed in $HOME
        self.assertTrue(vm.template == "sd-workstation-template")
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)

    def test_sd_workstation_template(self):
        vm = self.app.domains["sd-workstation-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.virt_mode == "hvm")
        self.assertTrue(vm.kernel == "")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Tests)
    return suite
