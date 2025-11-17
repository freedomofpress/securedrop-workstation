import os
import re
import subprocess
import unittest

import pytest

from tests.base import (
    CURRENT_FEDORA_TEMPLATE,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    SD_VMS,
)

BOOKWORM_STRING = "Debian GNU/Linux 12 (bookworm)"

SUPPORTED_SD_DEBIAN_DIST = "bookworm"

IS_CI = os.environ.get("CI") == "true"


class SD_VM_Platform_Tests:
    def _get_platform_info(self, vm):
        """
        Retrieve PRETTY_NAME for an AppVM.
        """
        stdout, stderr = vm.run("cat /etc/os-release")
        search = re.search(r'^PRETTY_NAME="(.*)"', stdout.decode())
        if not search:
            raise RuntimeError(f"Unable to determine platform for {vm.name}")
        return search.group(1)

    def _validate_vm_platform(self, vm):
        """
        Asserts that the given AppVM is based on an OS listed in the
        SUPPORTED_<XX>_PLATFORMS list, as specified in tests.
        All workstation-provisioned VMs should be SUPPORTED_SD_DEBIAN_DIST based.
        """
        platform = self._get_platform_info(vm)
        assert SUPPORTED_SD_DEBIAN_DIST in platform

    def _ensure_packages_up_to_date(self, vm, fedora=False):
        """
        Asserts that all available packages are installed; no pending
        updates. Assumes VM is Debian-based, so uses apt, but supports
        `fedora=True` to use dnf instead.
        """
        # Create custom error message, so failing test cases display
        # which VM caused the looped check to fail.
        fail_msg = f"Unapplied updates for VM '{vm}'"
        if not fedora:
            cmd = "apt list --upgradable"
            stdout, stderr = vm.run(cmd)
            results = stdout.rstrip().decode("utf-8")
            # `apt list` will always print "Listing..." to stdout,
            # so expect only that string.
            assert results == "Listing...", fail_msg
        else:
            cmd = "sudo dnf check-update"
            # Will raise CalledProcessError if updates available
            try:
                stdout, stderr = vm.run(cmd)
            except subprocess.CalledProcessError:
                pytest.fail(fail_msg)
            # 'stdout' will contain timestamped progress info; ignore it
            results = stderr.rstrip().decode("utf-8")
            stdout_lines = results.split("\n")
            # filter out gpgcheck warning present on all dnf operations
            stdout_lines = [
                x
                for x in stdout_lines
                if not x.startswith("Warning: Enforcing GPG signature check")
            ]
            results = "".join(stdout_lines)
            assert results == "", fail_msg

    @unittest.skipIf(IS_CI, "Skipping on CI")
    def test_all_sd_vms_uptodate(self, all_vms):
        """
        Asserts that all VMs have all available apt packages at the latest
        versions, with no updates pending.
        """
        for vm_name in SD_VMS:
            vm = all_vms[vm_name]
            self._ensure_packages_up_to_date(vm)

    @unittest.skipIf(IS_CI, "Skipping on CI")
    def test_all_fedora_vms_uptodate(self, all_vms):
        """
        Asserts that all Fedora-based templates, such as sys-net, have all
        available packages at the latest versions, with no updates pending.
        """
        # Technically we want to know whether the sys-firewall, sys-net, and
        # sys-usb VMs have their updates installed. This test assumes those
        # AppVMs are based on the most recent Fedora version.
        vm_name = CURRENT_FEDORA_TEMPLATE
        vm = all_vms[vm_name]
        self._ensure_packages_up_to_date(vm, fedora=True)
        vm.shutdown()

    def test_sd_proxy_template(self, all_vms):
        """
        Asserts that the 'sd-proxy' VM is using a supported base OS.
        """
        # This test is a single example of the method for testing: it would
        # be ideal to use a loop construct (such as pytest.mark.parametrize),
        # but doing so would introduce additional dependencies to dom0.
        vm = all_vms["sd-proxy"]
        self._validate_vm_platform(vm)

    def test_all_sd_vm_platforms(self, all_vms):
        """
        Test all VM platforms iteratively.

        Due to for-loop implementation, the first failure will stop the test.
        Therefore, even if multiple VMs are NOT running a supported platform,
        only a single failure will be reported.
        """
        # Would prefer to use a feature like pytest.mark.parametrize
        # for better error output here, but not available in dom0.
        for vm_name in SD_VMS:
            if vm_name == "sd-viewer":
                # sd-viewer is unable to start because of the securedrop-mime-handling
                # systemd service failing, so skip it here.
                continue
            vm = all_vms[vm_name]
            self._validate_vm_platform(vm)

    def test_dispvm_default_platform(self):
        """
        Query dom0 Qubes preferences and confirm that new DispVMs
        will be created under a supported OS. Requires a separate
        test because DispVMs may not be running at present.
        """
        cmd = ["qubes-prefs", "default_dispvm"]
        result = subprocess.check_output(cmd).decode("utf-8").rstrip("\n")
        assert result == "sd-viewer"

    def test_sd_vm_apt_sources(self, config, all_vms):
        """
        Test that the three templates we install our apt sources into are correct
        """
        for vm_name in [
            SD_TEMPLATE_SMALL,
            SD_TEMPLATE_LARGE,
        ]:
            vm = all_vms[vm_name]

            # First, check the prod apt repo is configured, which happens unconditionally
            # via securedrop-keyring deb package
            self.assert_apt_source(
                vm,
                "main",
                "https://apt.freedom.press",
                "/etc/apt/sources.list.d/apt_freedom_press.sources",
            )

            if config["environment"] == "prod":
                # No test sources should be present
                stdout, stderr = vm.run("ls /etc/apt/sources.list.d/")
                sources_list = stdout.decode("utf-8").rstrip("\n")
                assert "apt-test_freedom_press.sources" not in sources_list
                continue

            # we're in staging or dev, so check for that file
            components = ["main"]
            if config["environment"] == "dev":
                components.append("nightlies")

            self.assert_apt_source(
                vm,
                " ".join(components),
                "https://apt-test.freedom.press",
                "/etc/apt/sources.list.d/apt-test_freedom_press.sources",
            )

    def assert_apt_source(self, vm, component, url, filename):
        stdout, stderr = vm.run(f"cat {filename}")
        contents = stdout.decode("utf-8").rstrip("\n")

        assert f"Components: {component}\n" in contents, f"{vm.name} wrong component"
        assert f"URIs: {url}\n" in contents, f"{vm.name} wrong URL"
        assert (
            f"Suites: {SUPPORTED_SD_DEBIAN_DIST}\n" in contents
        ), f"{vm.name} wrong suite/codename"
