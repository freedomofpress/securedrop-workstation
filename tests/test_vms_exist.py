import json
import subprocess
import unittest

from tests.base import (
    SD_DVM_TEMPLATES,
    SD_TAG,
    SD_TEMPLATE_BASE,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    SD_TEMPLATES,
    SD_UNTAGGED_DEPRECATED_VMS,
    SD_VMS,
)

with open("config.json") as f:
    CONFIG = json.load(f)


class SD_VM_Tests:
    def test_expected(self, all_vms, sdw_tagged_vms):
        sdw_tagged_vm_names = [vm.name for vm in sdw_tagged_vms]
        expected_vms = set(SD_VMS + SD_DVM_TEMPLATES + SD_TEMPLATES)
        assert set(sdw_tagged_vm_names) == set(expected_vms)

        # Check for untagged VMs
        for vm_name in SD_UNTAGGED_DEPRECATED_VMS:
            assert vm_name not in all_vms

    @unittest.skipIf(CONFIG["environment"] != "prod", "Skipping on non-prod system")
    def test_internal(self, all_vms):
        all_vms["sd-proxy-dvm"].features.get("internal") == "1"
        all_vms["sd-viewer"].features.get("internal") == "1"

    def test_grsec_kernel(self, sdw_tagged_vms):
        """
        Confirms expected grsecurity-patched kernel is running.
        """
        # base doesn't have kernel configured
        # TODO: test in sd-viewer based dispVM
        exceptions = [SD_TEMPLATE_BASE, "sd-viewer"]

        for vm in sdw_tagged_vms:
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

    def test_default_dispvm(self, sdw_tagged_vms):
        """Verify the default DispVM is none for all except sd-app and sd-devices"""
        for vm in sdw_tagged_vms:
            if vm.name == "sd-app":
                assert vm.default_dispvm.name == "sd-viewer"
            else:
                assert vm.default_dispvm is None, f"{vm.name} has dispVM set"

    def test_sd_whonix_absent(self, all_vms):
        """
        The sd-whonix once existed to proxy sd-proxy's traffic throgh Tor.
        But we've since removed it and included a Tor proxy in sd-proxy.
        """
        assert "sd-whonix" not in all_vms

    def test_whonix_vms_reset(self, all_vms):
        """
        Whonix templates used to be modified by the workstation (<=1.4.0).
        Ensure they were properly reset.
        """

        whonix_qubes = [
            "whonix-workstation-17",
            "whonix-gateway-17",
            "sys-whonix",
            "anon-whonix",
            "whonix-workstation-17-dvm",
        ]
        for qube_name in whonix_qubes:
            if qube_name not in all_vms:
                # skip check on nonexitent qubes
                continue
            qube = all_vms[qube_name]
            assert qube.property_is_default("kernelopts")

    def test_sd_proxy_config(self, all_vms):
        vm = all_vms["sd-proxy"]
        assert vm.template == "sd-proxy-dvm"
        assert vm.klass == "DispVM"
        assert vm.netvm.name == "sys-firewall"
        assert vm.autostart
        assert not vm.provides_network
        assert vm.default_dispvm is None
        assert SD_TAG in vm.tags
        assert vm.features["service.securedrop-mime-handling"] == "1"
        assert vm.features["service.securedrop-arti"] == "1"
        assert vm.features["vm-config.SD_MIME_HANDLING"] == "default"
        self._check_service_running(vm, "securedrop-mime-handling")
        self._check_service_running(vm, "securedrop-proxy-onion-config")
        self._check_service_running(vm, "tor")

    def test_sd_proxy_dvm(self, all_vms):
        vm = all_vms["sd-proxy-dvm"]
        assert vm.template_for_dispvms
        assert vm.netvm.name == "sys-firewall"
        assert vm.template == SD_TEMPLATE_SMALL
        assert vm.default_dispvm is None
        assert SD_TAG in vm.tags
        assert not vm.autostart
        assert "service.securedrop-mime-handling" not in vm.features
        self._check_service_running(vm, "securedrop-mime-handling", running=False)

    def test_sd_app_config(self, config, all_vms):
        vm = all_vms["sd-app"]
        nvm = vm.netvm
        assert nvm is None
        assert vm.template == SD_TEMPLATE_SMALL
        assert not vm.provides_network
        assert not vm.template_for_dispvms
        assert "service.securedrop-log-server" not in vm.features
        assert SD_TAG in vm.tags
        assert "sd-client" in vm.tags
        # Check the size of the private volume
        # Should be 10GB
        # >>> 1024 * 1024 * 10 * 1024
        size = config["vmsizes"]["sd_app"]
        vol = vm.volumes["private"]
        assert vol.size == size * 1024 * 1024 * 1024

        # MIME handling
        assert vm.features["service.securedrop-mime-handling"] == "1"
        assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-app"
        self._check_service_running(vm, "securedrop-mime-handling")

        # Arti should *not* be running
        self._check_service_running(vm, "securedrop-arti", running=False)

    def test_sd_viewer_config(self, all_vms):
        vm = all_vms["sd-viewer"]
        nvm = vm.netvm
        assert nvm is None
        assert vm.template == SD_TEMPLATE_LARGE
        assert not vm.provides_network
        assert vm.template_for_dispvms
        assert SD_TAG in vm.tags

        # MIME handling
        assert vm.features["service.securedrop-mime-handling"] == "1"
        assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-viewer"

    def test_sd_gpg_config(self, all_vms):
        vm = all_vms["sd-gpg"]
        nvm = vm.netvm
        assert nvm is None
        # No sd-gpg-template, since keyring is managed in $HOME
        assert vm.template == SD_TEMPLATE_SMALL
        assert vm.autostart
        assert not vm.provides_network
        assert not vm.template_for_dispvms
        assert vm.features["service.securedrop-logging-disabled"] == "1"
        assert SD_TAG in vm.tags

    def test_sd_log_config(self, config, all_vms):
        vm = all_vms["sd-log"]
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
        assert SD_TAG in vm.tags
        # Check the size of the private volume
        # Should be same of config.json
        # >>> 1024 * 1024 * 5 * 1024
        size = config["vmsizes"]["sd_log"]
        vol = vm.volumes["private"]
        assert vol.size == size * 1024 * 1024 * 1024

    def test_sd_export_dvm(self, all_vms):
        vm = all_vms["sd-devices-dvm"]
        nvm = vm.netvm
        assert nvm is None
        assert SD_TAG in vm.tags
        assert vm.template_for_dispvms

        assert "service.avahi" not in vm.features
        # MIME handling (dvm does NOT setup mime, only its disposables do)
        assert "service.securedrop-mime-handling" not in vm.features
        self._check_service_running(vm, "securedrop-mime-handling", running=False)

    def test_sd_export(self, all_vms):
        vm = all_vms["sd-devices"]
        nvm = vm.netvm
        assert nvm is None
        vm_type = vm.klass
        assert vm_type == "DispVM"
        assert SD_TAG in vm.tags

        assert vm.features["service.avahi"] == "1"

        # MIME handling
        assert vm.features["service.securedrop-mime-handling"] == "1"
        assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-devices"
        self._check_service_running(vm, "securedrop-mime-handling")

    def test_sd_small_template(self, all_vms):
        # Kernel check is handled in test_grsec_kernel
        vm = all_vms[SD_TEMPLATE_SMALL]
        nvm = vm.netvm
        assert nvm is None
        assert SD_TAG in vm.tags

    def test_sd_large_template(self, all_vms):
        # Kernel check is handled in test_grsec_kernel
        vm = all_vms[SD_TEMPLATE_LARGE]
        nvm = vm.netvm
        assert nvm is None
        assert SD_TAG in vm.tags
