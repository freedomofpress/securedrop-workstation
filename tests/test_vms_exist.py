import unittest

from qubesadmin import Qubes
from base import WANTED_VMS


EXPECTED_KERNEL_VERSION = "4.14.74-grsec"


class SD_VM_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()

    def tearDown(self):
        pass

    def test_expected(self):
        vm_set = set(self.app.domains)
        for test_vm in WANTED_VMS:
            self.assertTrue(test_vm in vm_set)

    def _check_kernel(self, vm):
        """
        Confirms expected grsecurity-patched kernel is running.
        """
        # Running custom kernel requires HVM with empty kernel
        self.assertTrue(vm.virt_mode == "hvm")
        self.assertTrue(vm.kernel == "")

        # Check exact kernel version in VM
        stdout, stderr = vm.run("uname -r")
        kernel_version = stdout.decode("utf-8").rstrip()
        assert kernel_version.endswith("-grsec")
        assert kernel_version == EXPECTED_KERNEL_VERSION

    def test_sd_whonix_config(self):
        vm = self.app.domains["sd-whonix"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sys-firewall")
        wanted_kernelopts = "nopat apparmor=1 security=apparmor"
        self.assertEqual(vm.kernelopts, wanted_kernelopts)
        self.assertTrue(vm.template == "whonix-gw-14")
        self.assertTrue(vm.provides_network)
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.template_for_dispvms)
        self.assertTrue('sd-workstation' in vm.tags)

    def test_sd_proxy_config(self):
        vm = self.app.domains["sd-proxy"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sd-whonix")
        wanted_kernelopts = "nopat apparmor=1 security=apparmor"
        self.assertEqual(vm.kernelopts, wanted_kernelopts)
        self.assertTrue(vm.template == "sd-proxy-template")
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self.assertTrue('sd-workstation' in vm.tags)

    def test_sd_svs_config(self):
        vm = self.app.domains["sd-svs"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == "sd-svs-template")
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)
        self.assertTrue('sd-workstation' in vm.tags)

    def test_sd_svs_disp_config(self):
        vm = self.app.domains["sd-svs-disp"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == "sd-svs-disp-template")
        self.assertFalse(vm.provides_network)
        self.assertTrue(vm.template_for_dispvms)
        self._check_kernel(vm)
        self.assertTrue('sd-workstation' in vm.tags)

    def test_sd_gpg_config(self):
        vm = self.app.domains["sd-gpg"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        # No sd-gpg-template, since keyring is managed in $HOME
        self.assertTrue(vm.template == "sd-workstation-template")
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)
        self.assertTrue('sd-workstation' in vm.tags)

    def test_sd_workstation_template(self):
        vm = self.app.domains["sd-workstation-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self._check_kernel(vm)
        self.assertTrue('sd-workstation' in vm.tags)
        self._check_kernel(vm)

    def test_sd_proxy_template(self):
        vm = self.app.domains["sd-proxy-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue('sd-workstation' in vm.tags)

    def sd_svs_template(self):
        vm = self.app.domains["sd-svs-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue('sd-workstation' in vm.tags)
        self._check_kernel(vm)

    def sd_svs_disp_template(self):
        vm = self.app.domains["sd-svs-disp-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue('sd-workstation' in vm.tags)
        self.assertTrue(vm.template_for_dispvms)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Tests)
    return suite
