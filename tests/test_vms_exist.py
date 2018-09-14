import unittest

from qubesadmin import Qubes


class SD_VM_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()

    def tearDown(self):
        pass

    def test_expected(self):
        vm_set = set(self.app.domains)

        wanted_vms = ["sd-whonix", "sd-journalist",
                      "sd-svs", "sd-svs-disp",
                      "sd-gpg"]
        for test_vm in wanted_vms:
            self.assertTrue(test_vm in vm_set)

    def test_sd_whonix_net(self):
        vm = self.app.domains["sd-whonix"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sys-firewall")

    def test_sd_journalist_net(self):
        vm = self.app.domains["sd-journalist"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sd-whonix")

    def test_sd_svs_net(self):
        vm = self.app.domains["sd-svs"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)

    def test_sd_svs_disp_net(self):
        vm = self.app.domains["sd-svs-disp"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)

    def test_sd_gpg_net(self):
        vm = self.app.domains["sd-gpg"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Tests)
    return suite
