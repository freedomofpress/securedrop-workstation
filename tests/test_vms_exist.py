import unittest
import json

from qubesadmin import Qubes
from base import WANTED_VMS


EXPECTED_KERNEL_VERSION = "4.14.186-grsec-workstation"


class SD_VM_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()
        with open("config.json") as c:
            self.config = json.load(c)

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
        assert kernel_version.endswith("-grsec-workstation")
        assert kernel_version == EXPECTED_KERNEL_VERSION

        u2mfn_filepath = "/usr/lib/modules/{}/updates/dkms/u2mfn.ko".format(EXPECTED_KERNEL_VERSION)
        # cmd will raise exception if file not found
        stdout, stderr = vm.run("sudo test -f {}".format(u2mfn_filepath))
        assert stdout == b""
        assert stderr == b""

    def _check_service_running(self, vm, service):
        """
        Ensures a given service is running inside a given VM.
        Uses systemctl is-active to query the service state.
        """
        cmd = "systemctl is-active {}".format(service)
        stdout, stderr = vm.run(cmd)
        service_status = stdout.decode("utf-8").rstrip()
        assert service_status == "active"

    def test_sd_whonix_config(self):
        vm = self.app.domains["sd-whonix"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sys-firewall")
        wanted_kernelopts = "nopat apparmor=1 security=apparmor"
        self.assertEqual(vm.kernelopts, wanted_kernelopts)
        self.assertTrue(vm.template == "whonix-gw-15")
        self.assertTrue(vm.provides_network)
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.template_for_dispvms)
        self.assertTrue("sd-workstation" in vm.tags)

    def test_sd_proxy_config(self):
        vm = self.app.domains["sd-proxy"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sd-whonix")
        self.assertTrue(vm.template == "sd-small-buster-template")
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self.assertTrue("sd-workstation" in vm.tags)

    def test_sd_app_config(self):
        vm = self.app.domains["sd-app"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == "sd-small-buster-template")
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)
        self._check_service_running(vm, "paxctld")
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertTrue("sd-client" in vm.tags)
        # Check the size of the private volume
        # Should be 10GB
        # >>> 1024 * 1024 * 10 * 1024
        size = self.config["vmsizes"]["sd_app"]
        vol = vm.volumes["private"]
        self.assertEqual(vol.size, size * 1024 * 1024 * 1024)

    def test_sd_viewer_config(self):
        vm = self.app.domains["sd-viewer"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == "sd-large-buster-template")
        self.assertFalse(vm.provides_network)
        self.assertTrue(vm.template_for_dispvms)
        self._check_kernel(vm)
        self._check_service_running(vm, "paxctld")
        self.assertTrue("sd-workstation" in vm.tags)

    def test_sd_gpg_config(self):
        vm = self.app.domains["sd-gpg"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        # No sd-gpg-template, since keyring is managed in $HOME
        self.assertTrue(vm.template == "sd-small-buster-template")
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)
        self.assertTrue("sd-workstation" in vm.tags)

    def test_sd_log_config(self):
        vm = self.app.domains["sd-log"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == "sd-small-buster-template")
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)
        self._check_service_running(vm, "paxctld")
        self._check_service_running(vm, "securedrop-log")
        self.assertFalse(vm.template_for_dispvms)
        self.assertTrue("sd-workstation" in vm.tags)
        # Check the size of the private volume
        # Should be same of config.json
        # >>> 1024 * 1024 * 5 * 1024
        size = self.config["vmsizes"]["sd_log"]
        vol = vm.volumes["private"]
        self.assertEqual(vol.size, size * 1024 * 1024 * 1024)

    def test_sd_workstation_template(self):
        vm = self.app.domains["securedrop-workstation-buster"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.virt_mode == "hvm")
        self.assertTrue(vm.kernel == "")
        self.assertTrue("sd-workstation" in vm.tags)
        self._check_kernel(vm)
        self._check_service_running(vm, "paxctld")

    def test_sd_proxy_template(self):
        vm = self.app.domains["sd-small-buster-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)

    def sd_app_template(self):
        vm = self.app.domains["sd-small-buster-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self._check_kernel(vm)

    def sd_viewer_template(self):
        vm = self.app.domains["sd-large-buster-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertTrue(vm.template_for_dispvms)

    def sd_export_template(self):
        vm = self.app.domains["sd-large-buster-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self._check_kernel(vm)

    def sd_export_dvm(self):
        vm = self.app.domains["sd-devices-dvm"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertTrue(vm.template_for_dispvms)
        self._check_kernel(vm)

    def sd_export(self):
        vm = self.app.domains["sd-devices"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        vm_type = vm.klass
        self.assertTrue(vm_type == "DispVM")
        self.assertTrue("sd-workstation" in vm.tags)
        self._check_kernel(vm)

    def sd_small_template(self):
        vm = self.app.domains["sd-small-buster-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)

    def sd_large_template(self):
        vm = self.app.domains["sd-large-buster-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Tests)
    return suite
