import json
import subprocess
import unittest

from base import WANTED_VMS
from qubesadmin import Qubes

DEBIAN_VERSION = "bookworm"


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
        # Running custom kernel in PVH mode requires pvgrub2-pvh
        self.assertTrue(vm.virt_mode == "pvh")
        self.assertTrue(vm.kernel == "pvgrub2-pvh")

        # Check kernel flavor in VM
        stdout, stderr = vm.run("uname -r")
        kernel_version = stdout.decode("utf-8").rstrip()
        assert kernel_version.endswith("-grsec-workstation")

    def _check_service_running(self, vm, service, running=True):
        """
        Ensures a given service is running inside a given VM.
        Uses systemctl is-active to query the service state.
        """
        try:
            cmd = f"systemctl is-active {service}"
            stdout, stderr = vm.run(cmd)
            service_status = stdout.decode("utf-8").rstrip()
        except subprocess.CalledProcessError as e:
            if e.returncode == 3:
                service_status = "inactive"
            else:
                raise e
        self.assertTrue(service_status == "active" if running else "inactive")

    def test_sd_whonix_config(self):
        vm = self.app.domains["sd-whonix"]
        nvm = vm.netvm
        self.assertTrue(nvm.name == "sys-firewall")
        wanted_kernelopts = "nopat apparmor=1 security=apparmor"
        self.assertEqual(vm.kernelopts, wanted_kernelopts)
        self.assertTrue(vm.template == "whonix-gateway-17")
        self.assertTrue(vm.provides_network)
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.template_for_dispvms)
        self.assertTrue("sd-workstation" in vm.tags)

    def test_sd_proxy_config(self):
        vm = self.app.domains["sd-proxy"]
        self.assertTrue(vm.template == "sd-proxy-dvm")
        self.assertTrue(vm.klass == "DispVM")
        self.assertTrue(vm.netvm.name == "sd-whonix")
        self.assertTrue(vm.autostart)
        self.assertFalse(vm.provides_network)
        self.assertIsNone(vm.default_dispvm)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertEqual(vm.features["service.securedrop-mime-handling"], "1")
        self.assertEqual(vm.features["vm-config.SD_MIME_HANDLING"], "default")
        self._check_service_running(vm, "securedrop-mime-handling")

    def test_sd_proxy_dvm(self):
        vm = self.app.domains["sd-proxy-dvm"]
        self.assertTrue(vm.template_for_dispvms)
        self.assertTrue(vm.netvm.name == "sd-whonix")
        self.assertTrue(vm.template == f"sd-small-{DEBIAN_VERSION}-template")
        self.assertIsNone(vm.default_dispvm)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertFalse(vm.autostart)
        self.assertFalse(vm.features.get("service.securedrop-mime-handling", False))
        self._check_service_running(vm, "securedrop-mime-handling", running=False)
        self._check_kernel(vm)

    def test_sd_app_config(self):
        vm = self.app.domains["sd-app"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == f"sd-small-{DEBIAN_VERSION}-template")
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)
        self._check_service_running(vm, "paxctld")
        self.assertNotIn("service.securedrop-log-server", vm.features)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertTrue("sd-client" in vm.tags)
        # Check the size of the private volume
        # Should be 10GB
        # >>> 1024 * 1024 * 10 * 1024
        size = self.config["vmsizes"]["sd_app"]
        vol = vm.volumes["private"]
        self.assertEqual(vol.size, size * 1024 * 1024 * 1024)

        # MIME handling
        self.assertEqual(vm.features["service.securedrop-mime-handling"], "1")
        self.assertEqual(vm.features["vm-config.SD_MIME_HANDLING"], "sd-app")
        self._check_service_running(vm, "securedrop-mime-handling")

    def test_sd_viewer_config(self):
        vm = self.app.domains["sd-viewer"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == f"sd-large-{DEBIAN_VERSION}-template")
        self.assertFalse(vm.provides_network)
        self.assertTrue(vm.template_for_dispvms)
        # sd-viewer should not be able to create other disposable VMs
        self.assertIsNone(vm.default_dispvm)
        self._check_kernel(vm)
        self.assertTrue("sd-workstation" in vm.tags)

        # MIME handling
        self.assertEqual(vm.features["service.securedrop-mime-handling"], "1")
        self.assertEqual(vm.features["vm-config.SD_MIME_HANDLING"], "sd-viewer")

    def test_sd_gpg_config(self):
        vm = self.app.domains["sd-gpg"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        # No sd-gpg-template, since keyring is managed in $HOME
        self.assertTrue(vm.template == f"sd-small-{DEBIAN_VERSION}-template")
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)
        self.assertEqual(vm.features["service.securedrop-logging-disabled"], "1")
        self.assertTrue("sd-workstation" in vm.tags)

    def test_sd_log_config(self):
        vm = self.app.domains["sd-log"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue(vm.template == f"sd-small-{DEBIAN_VERSION}-template")
        self.assertTrue(vm.autostart is True)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)
        self._check_service_running(vm, "paxctld")
        self._check_service_running(vm, "securedrop-log-server")
        self.assertEqual(vm.features["service.securedrop-log-server"], "1")
        self.assertEqual(vm.features["service.securedrop-logging-disabled"], "1")

        self.assertFalse(vm.template_for_dispvms)
        self.assertTrue("sd-workstation" in vm.tags)
        # Check the size of the private volume
        # Should be same of config.json
        # >>> 1024 * 1024 * 5 * 1024
        size = self.config["vmsizes"]["sd_log"]
        vol = vm.volumes["private"]
        self.assertEqual(vol.size, size * 1024 * 1024 * 1024)

    def sd_app_template(self):
        vm = self.app.domains[f"sd-small-{DEBIAN_VERSION}-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self._check_kernel(vm)

    def sd_viewer_template(self):
        vm = self.app.domains[f"sd-large-{DEBIAN_VERSION}-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertTrue(vm.template_for_dispvms)

    def sd_export_template(self):
        vm = self.app.domains[f"sd-large-{DEBIAN_VERSION}-template"]
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

        # MIME handling (dvm does NOT setup mime, only its disposables do)
        self.assertFalse(vm.features.get("service.securedrop-mime-handling", False))
        self._check_service_running(vm, "securedrop-mime-handling")

    def sd_export(self):
        vm = self.app.domains["sd-devices"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        vm_type = vm.klass
        self.assertTrue(vm_type == "DispVM")
        self.assertTrue("sd-workstation" in vm.tags)
        self._check_kernel(vm)

        # MIME handling
        self.assertEqual(vm.features["service.securedrop-mime-handling"], "1")
        self.assertEqual(vm.features["vm-config.SD_MIME_HANDLING"], "sd-devices")
        self._check_service_running(vm, "securedrop-mime-handling")

    def sd_small_template(self):
        vm = self.app.domains[f"sd-small-{DEBIAN_VERSION}-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)

    def sd_large_template(self):
        vm = self.app.domains[f"sd-large-{DEBIAN_VERSION}-template"]
        nvm = vm.netvm
        self.assertTrue(nvm is None)
        self.assertTrue("sd-workstation" in vm.tags)
        self.assertFalse(vm.template_for_dispvms)
        self._check_kernel(vm)


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_VM_Tests)
