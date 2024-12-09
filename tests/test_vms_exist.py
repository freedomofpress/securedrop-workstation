import json
import subprocess
import unittest

from base import (
    SD_DVM_TEMPLATES,
    SD_TEMPLATE_BASE,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    SD_TEMPLATES,
    SD_VMS,
)
from qubesadmin import Qubes

with open("config.json") as f:
    CONFIG = json.load(f)


class SD_VM_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()
        with open("config.json") as c:
            self.config = json.load(c)
        # @tag:sd-workstation
        self.sdw_tagged_vms = [vm for vm in self.app.domains if "sd-workstation" in vm.tags]

    def tearDown(self):
        pass

    def test_expected(self):
        sdw_tagged_vm_names = [vm.name for vm in self.sdw_tagged_vms]
        expected_vms = set(SD_VMS + SD_DVM_TEMPLATES + SD_TEMPLATES)
        self.assertEqual(set(sdw_tagged_vm_names), set(expected_vms))

    @unittest.skipIf(CONFIG["environment"] != "prod", "Skipping on non-prod system")
    def test_internal(self):
        internal = ["sd-proxy", "sd-proxy-dvm", "sd-viewer"]

        for vm_name in internal:
            vm = self.app.domains[vm_name]
            self.assertEqual(vm.features.get("internal"), "1")

    def test_grsec_kernel(self):
        """
        Confirms expected grsecurity-patched kernel is running.
        """
        # base doesn't have kernel configured and whonix uses dom0 kernel
        # TODO: test in sd-viewer based dispVM
        exceptions = [SD_TEMPLATE_BASE, "sd-whonix", "sd-viewer"]

        for vm in self.sdw_tagged_vms:
            if vm.name in exceptions:
                continue
            # Running custom kernel in PVH mode requires pvgrub2-pvh
            self.assertEqual(vm.virt_mode, "pvh")
            self.assertEqual(vm.kernel, "pvgrub2-pvh")

            # Check running kernel is grsecurity-patched
            stdout, stderr = vm.run("uname -r")
            assert stdout.decode().strip().endswith("-grsec-workstation")
            self._check_service_running(vm, "paxctld")

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
        self.assertEqual(service_status, "active" if running else "inactive")

    def test_default_dispvm(self):
        """Verify the default DispVM is none for all except sd-app and sd-devices"""
        for vm in self.sdw_tagged_vms:
            if vm.name == "sd-app":
                self.assertEqual(vm.default_dispvm.name, "sd-viewer")
            else:
                self.assertIsNone(vm.default_dispvm, f"{vm.name} has dispVM set")

    def test_sd_whonix_config(self):
        vm = self.app.domains["sd-whonix"]
        nvm = vm.netvm
        self.assertEqual(nvm.name, "sys-firewall")
        wanted_kernelopts = "apparmor=1 security=apparmor"
        self.assertEqual(vm.kernelopts, wanted_kernelopts)
        self.assertEqual(vm.template, "whonix-gateway-17")
        self.assertTrue(vm.provides_network)
        self.assertTrue(vm.autostart)
        self.assertFalse(vm.template_for_dispvms)
        self.assertIn("sd-workstation", vm.tags)

    def test_sd_proxy_config(self):
        vm = self.app.domains["sd-proxy"]
        self.assertEqual(vm.template, "sd-proxy-dvm")
        self.assertEqual(vm.klass, "DispVM")
        self.assertEqual(vm.netvm.name, "sd-whonix")
        self.assertTrue(vm.autostart)
        self.assertFalse(vm.provides_network)
        self.assertIsNone(vm.default_dispvm)
        self.assertIn("sd-workstation", vm.tags)
        self.assertEqual(vm.features["service.securedrop-mime-handling"], "1")
        self.assertEqual(vm.features["vm-config.SD_MIME_HANDLING"], "default")
        self._check_service_running(vm, "securedrop-mime-handling")

    def test_sd_proxy_dvm(self):
        vm = self.app.domains["sd-proxy-dvm"]
        self.assertTrue(vm.template_for_dispvms)
        self.assertEqual(vm.netvm.name, "sd-whonix")
        self.assertEqual(vm.template, SD_TEMPLATE_SMALL)
        self.assertIsNone(vm.default_dispvm)
        self.assertIn("sd-workstation", vm.tags)
        self.assertFalse(vm.autostart)
        self.assertNotIn("service.securedrop-mime-handling", vm.features)
        self._check_service_running(vm, "securedrop-mime-handling", running=False)

    def test_sd_app_config(self):
        vm = self.app.domains["sd-app"]
        nvm = vm.netvm
        self.assertIsNone(nvm)
        self.assertEqual(vm.template, SD_TEMPLATE_SMALL)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self.assertNotIn("service.securedrop-log-server", vm.features)
        self.assertIn("sd-workstation", vm.tags)
        self.assertIn("sd-client", vm.tags)
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
        self.assertIsNone(nvm)
        self.assertEqual(vm.template, SD_TEMPLATE_LARGE)
        self.assertFalse(vm.provides_network)
        self.assertTrue(vm.template_for_dispvms)
        self.assertIn("sd-workstation", vm.tags)

        # MIME handling
        self.assertEqual(vm.features["service.securedrop-mime-handling"], "1")
        self.assertEqual(vm.features["vm-config.SD_MIME_HANDLING"], "sd-viewer")

    def test_sd_gpg_config(self):
        vm = self.app.domains["sd-gpg"]
        nvm = vm.netvm
        self.assertIsNone(nvm)
        # No sd-gpg-template, since keyring is managed in $HOME
        self.assertEqual(vm.template, SD_TEMPLATE_SMALL)
        self.assertTrue(vm.autostart)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self.assertEqual(vm.features["service.securedrop-logging-disabled"], "1")
        self.assertIn("sd-workstation", vm.tags)

    def test_sd_log_config(self):
        vm = self.app.domains["sd-log"]
        nvm = vm.netvm
        self.assertIsNone(nvm)
        self.assertEqual(vm.template, SD_TEMPLATE_SMALL)
        self.assertTrue(vm.autostart)
        self.assertFalse(vm.provides_network)
        self.assertFalse(vm.template_for_dispvms)
        self._check_service_running(vm, "securedrop-log-server")
        self.assertEqual(vm.features["service.securedrop-log-server"], "1")
        self.assertEqual(vm.features["service.securedrop-logging-disabled"], "1")

        self.assertFalse(vm.template_for_dispvms)
        self.assertIn("sd-workstation", vm.tags)
        # Check the size of the private volume
        # Should be same of config.json
        # >>> 1024 * 1024 * 5 * 1024
        size = self.config["vmsizes"]["sd_log"]
        vol = vm.volumes["private"]
        self.assertEqual(vol.size, size * 1024 * 1024 * 1024)

    def test_sd_export_dvm(self):
        vm = self.app.domains["sd-devices-dvm"]
        nvm = vm.netvm
        self.assertIsNone(nvm)
        self.assertIn("sd-workstation", vm.tags)
        self.assertTrue(vm.template_for_dispvms)

        # MIME handling (dvm does NOT setup mime, only its disposables do)
        self.assertNotIn("service.securedrop-mime-handling", vm.features)
        self._check_service_running(vm, "securedrop-mime-handling", running=False)

    def test_sd_export(self):
        vm = self.app.domains["sd-devices"]
        nvm = vm.netvm
        self.assertIsNone(nvm)
        vm_type = vm.klass
        self.assertEqual(vm_type, "DispVM")
        self.assertIn("sd-workstation", vm.tags)

        # MIME handling
        self.assertEqual(vm.features["service.securedrop-mime-handling"], "1")
        self.assertEqual(vm.features["vm-config.SD_MIME_HANDLING"], "sd-devices")
        self._check_service_running(vm, "securedrop-mime-handling")

    def test_sd_small_template(self):
        # Kernel check is handled in test_grsec_kernel
        vm = self.app.domains[SD_TEMPLATE_SMALL]
        nvm = vm.netvm
        self.assertIsNone(nvm)
        self.assertIn("sd-workstation", vm.tags)

    def test_sd_large_template(self):
        # Kernel check is handled in test_grsec_kernel
        vm = self.app.domains[SD_TEMPLATE_LARGE]
        nvm = vm.netvm
        self.assertIsNone(nvm)
        self.assertIn("sd-workstation", vm.tags)


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_VM_Tests)
