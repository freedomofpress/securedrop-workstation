import json
import subprocess
import unittest

from qubesadmin import Qubes

from sdw_util import Util
from tests.base import (
    CURRENT_WHONIX_VERSION,
    SD_DVM_TEMPLATES,
    SD_TEMPLATE_BASE,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    SD_TEMPLATES,
    SD_UNTAGGED_DEPRECATED_VMS,
    SD_VMS,
)

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
        assert set(sdw_tagged_vm_names) == set(expected_vms)

        # Check for untagged VMs
        for vm_name in SD_UNTAGGED_DEPRECATED_VMS:
            assert vm_name not in self.app.domains

    @unittest.skipIf(CONFIG["environment"] != "prod", "Skipping on non-prod system")
    def test_internal(self):
        internal = ["sd-proxy", "sd-proxy-dvm", "sd-viewer"]

        for vm_name in internal:
            vm = self.app.domains[vm_name]
            assert vm.features.get("internal") == "1"

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
            assert vm.virt_mode == "pvh"
            assert vm.kernel == "pvgrub2-pvh"

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
        assert service_status == "active" if running else "inactive"

    def test_default_dispvm(self):
        """Verify the default DispVM is none for all except sd-app and sd-devices"""
        for vm in self.sdw_tagged_vms:
            if vm.name == "sd-app":
                assert vm.default_dispvm.name == "sd-viewer"
            else:
                assert vm.default_dispvm is None, f"{vm.name} has dispVM set"

    def test_sd_whonix_config(self):
        vm = self.app.domains["sd-whonix"]
        nvm = vm.netvm
        assert nvm.name == "sys-firewall"
        wanted_kernelopts = "apparmor=1 security=apparmor"
        assert vm.kernelopts == wanted_kernelopts
        assert vm.provides_network
        assert vm.autostart
        assert not vm.template_for_dispvms
        assert "sd-workstation" in vm.tags

        # Whonix version checking:
        #   If mismatch, whonix may have been updated.
        #   Fix the test by bumping CURRENT_WHONIX_VERSION
        assert Util.get_whonix_version() == int(CURRENT_WHONIX_VERSION)

        assert vm.template.features.get("os-version") == CURRENT_WHONIX_VERSION

    def test_sd_proxy_config(self):
        vm = self.app.domains["sd-proxy"]
        assert vm.template == "sd-proxy-dvm"
        assert vm.klass == "DispVM"
        assert vm.netvm.name == "sys-firewall"
        assert vm.autostart
        assert not vm.provides_network
        assert vm.default_dispvm is None
        assert "sd-workstation" in vm.tags
        assert vm.features["service.securedrop-mime-handling"] == "1"
        assert vm.features["service.securedrop-arti"] == "1"
        assert vm.features["vm-config.SD_MIME_HANDLING"] == "default"
        self._check_service_running(vm, "securedrop-mime-handling")
        self._check_service_running(vm, "securedrop-proxy-onion-config")
        self._check_service_running(vm, "tor")

    def test_sd_proxy_dvm(self):
        vm = self.app.domains["sd-proxy-dvm"]
        assert vm.template_for_dispvms
        assert vm.netvm.name == "sys-firewall"
        assert vm.template == SD_TEMPLATE_SMALL
        assert vm.default_dispvm is None
        assert "sd-workstation" in vm.tags
        assert not vm.autostart
        assert "service.securedrop-mime-handling" not in vm.features
        self._check_service_running(vm, "securedrop-mime-handling", running=False)

    def test_sd_app_config(self):
        vm = self.app.domains["sd-app"]
        nvm = vm.netvm
        assert nvm is None
        assert vm.template == SD_TEMPLATE_SMALL
        assert not vm.provides_network
        assert not vm.template_for_dispvms
        assert "service.securedrop-log-server" not in vm.features
        assert "sd-workstation" in vm.tags
        assert "sd-client" in vm.tags
        # Check the size of the private volume
        # Should be 10GB
        # >>> 1024 * 1024 * 10 * 1024
        size = self.config["vmsizes"]["sd_app"]
        vol = vm.volumes["private"]
        assert vol.size == size * 1024 * 1024 * 1024

        # MIME handling
        assert vm.features["service.securedrop-mime-handling"] == "1"
        assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-app"
        self._check_service_running(vm, "securedrop-mime-handling")

        # Arti should *not* be running
        self._check_service_running(vm, "securedrop-arti", running=False)

    def test_sd_viewer_config(self):
        vm = self.app.domains["sd-viewer"]
        nvm = vm.netvm
        assert nvm is None
        assert vm.template == SD_TEMPLATE_LARGE
        assert not vm.provides_network
        assert vm.template_for_dispvms
        assert "sd-workstation" in vm.tags

        # MIME handling
        assert vm.features["service.securedrop-mime-handling"] == "1"
        assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-viewer"

    def test_sd_gpg_config(self):
        vm = self.app.domains["sd-gpg"]
        nvm = vm.netvm
        assert nvm is None
        # No sd-gpg-template, since keyring is managed in $HOME
        assert vm.template == SD_TEMPLATE_SMALL
        assert vm.autostart
        assert not vm.provides_network
        assert not vm.template_for_dispvms
        assert vm.features["service.securedrop-logging-disabled"] == "1"
        assert "sd-workstation" in vm.tags

    def test_sd_log_config(self):
        vm = self.app.domains["sd-log"]
        nvm = vm.netvm
        assert nvm is None
        assert vm.template == SD_TEMPLATE_SMALL
        assert vm.autostart
        assert not vm.provides_network
        assert not vm.template_for_dispvms
        self._check_service_running(vm, "securedrop-log-server")
        assert vm.features["service.securedrop-log-server"] == "1"
        assert vm.features["service.securedrop-logging-disabled"] == "1"
        # See sd-log.sls "sd-install-epoch" feature
        assert vm.features["sd-install-epoch"] == "1001"

        assert not vm.template_for_dispvms
        assert "sd-workstation" in vm.tags
        # Check the size of the private volume
        # Should be same of config.json
        # >>> 1024 * 1024 * 5 * 1024
        size = self.config["vmsizes"]["sd_log"]
        vol = vm.volumes["private"]
        assert vol.size == size * 1024 * 1024 * 1024

    def test_sd_export_dvm(self):
        vm = self.app.domains["sd-devices-dvm"]
        nvm = vm.netvm
        assert nvm is None
        assert "sd-workstation" in vm.tags
        assert vm.template_for_dispvms

        assert "service.avahi" not in vm.features
        # MIME handling (dvm does NOT setup mime, only its disposables do)
        assert "service.securedrop-mime-handling" not in vm.features
        self._check_service_running(vm, "securedrop-mime-handling", running=False)

    def test_sd_export(self):
        vm = self.app.domains["sd-devices"]
        nvm = vm.netvm
        assert nvm is None
        vm_type = vm.klass
        assert vm_type == "DispVM"
        assert "sd-workstation" in vm.tags

        assert vm.features["service.avahi"] == "1"

        # MIME handling
        assert vm.features["service.securedrop-mime-handling"] == "1"
        assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-devices"
        self._check_service_running(vm, "securedrop-mime-handling")

    def test_sd_small_template(self):
        # Kernel check is handled in test_grsec_kernel
        vm = self.app.domains[SD_TEMPLATE_SMALL]
        nvm = vm.netvm
        assert nvm is None
        assert "sd-workstation" in vm.tags

    def test_sd_large_template(self):
        # Kernel check is handled in test_grsec_kernel
        vm = self.app.domains[SD_TEMPLATE_LARGE]
        nvm = vm.netvm
        assert nvm is None
        assert "sd-workstation" in vm.tags
