import unittest
import subprocess

from qubesadmin import Qubes
from base import WANTED_VMS


SUPPORTED_PLATFORMS = [
    "Debian GNU/Linux 9 (stretch)",
]


class SD_VM_Platform_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()

    def tearDown(self):
        pass

    def _get_platform_info(self, vm):
        """
        Retrieve base OS for running AppVM. Executes command on AppVM
        and returns the PRETTY_NAME field from /etc/os-release.
        """
        # Not using `lsb_release` for platform info, because it is not present
        # on Qubes AppVMs. Rather than install it simply for testing purposes,
        # let's maintain the default config and retrieve the value elsewise.
        cmd = "perl -nE '/^PRETTY_NAME=\"(.*)\"$/ and say $1' /etc/os-release"
        stdout, stderr = vm.run(cmd)
        platform = stdout.decode("utf-8").rstrip("\n")
        return platform

    def _validate_vm_platform(self, vm):
        """
        Asserts that the given AppVM is based on an OS listed in the
        SUPPORTED_PLATFORMS list, as specified in tests.
        """
        platform = self._get_platform_info(vm)
        self.assertIn(platform, SUPPORTED_PLATFORMS)

    def _ensure_packages_up_to_date(self, vm, fedora=False):
        """
        Asserts that all available packages are installed; no pending
        updates. Assumes VM is Debian-based, so uses apt, but supports
        `fedora=True` to use dnf instead.
        """
        if not fedora:
            cmd = "apt list --upgradable"
            stdout, stderr = vm.run(cmd)
            results = stdout.rstrip().decode("utf-8")
            # `apt list` will always print "Listing..." to stdout,
            # so expect only that string.
            self.assertEqual(results, "Listing...")
        else:
            cmd = "sudo dnf check-update"
            # Will raise CalledProcessError if updates available
            stdout, stderr = vm.run(cmd)
            # 'stdout' will contain timestamped progress info; ignore it
            results = stderr.rstrip().decode("utf-8")
            self.assertEqual(results, "")

    def _ensure_jessie_backports_disabled(self, vm):
        """
        Ensures that there are no Debian Jessie repos configured in
        apt source lists. This is only relevant for Debian Stretch,
        on which misconfigured apt sources containing Jessie references
        will cause apt commands to fail.
        """
        # Use a fileglob to account for /etc/apt/sources.list.d/, as well.
        # Add `|| true` to ensure dom0 receives a zero exit code.
        cmd = "grep -i jessie /etc/apt/sources.list* || true"
        # Will raise CalledProcessError if no hits found
        stdout, stderr = vm.run(cmd)
        results = stdout.rstrip().decode("utf-8")
        # We expect zero hits, so confirm output is empty string.
        self.assertEqual(results, "")

    def test_all_jessie_backports_disabled(self):
        """
        Asserts that all VMs lack references to Jessie in apt config.
        """
        for vm_name in WANTED_VMS:
            vm = self.app.domains[vm_name]
            self._ensure_jessie_backports_disabled(vm)

    def test_all_sd_vms_uptodate(self):
        """
        Asserts that all VMs have all available apt packages at the latest
        versions, with no updates pending.
        """
        for vm_name in WANTED_VMS:
            vm = self.app.domains[vm_name]
            self._ensure_packages_up_to_date(vm)

    def test_all_fedora_vms_uptodate(self):
        """
        Asserts that all Fedora-based templates, such as sys-net, have all
        available packages at the latest versions, with no updates pending.
        """
        # Technically we want to know whether the sys-firewall, sys-net, and
        # sys-usb VMs have their updates installed. This test assumes those
        # AppVMs are based on fedora-29.
        vm_name = "fedora-29"
        vm = self.app.domains[vm_name]
        self._ensure_packages_up_to_date(vm, fedora=True)
        vm.shutdown()

    def test_sd_proxy_template(self):
        """
        Asserts that the 'sd-proxy' VM is using a supported base OS.
        """
        # This test is a single example of the method for testing: it would
        # be ideal to use a loop construct (such as pytest.mark.parametrize),
        # but doing so would introduce additional dependencies to dom0.
        vm = self.app.domains["sd-proxy"]
        self._validate_vm_platform(vm)

    def test_all_sd_vm_platforms(self):
        """
        Test all VM platforms iteratively.

        Due to for-loop implementation, the first failure will stop the test.
        Therefore, even if multiple VMs are NOT running a supported platform,
        only a single failure will be reported.
        """
        # Would prefer to use a feature like pytest.mark.parametrize
        # for better error output here, but not available in dom0.
        for vm_name in WANTED_VMS:
            vm = self.app.domains[vm_name]
            self._validate_vm_platform(vm)

    def test_dispvm_default_platform(self):
        """
        Query dom0 Qubes preferences and confirm that new DispVMs
        will be created under a supported OS. Requires a separate
        test because DispVMs may not be running at present.
        """
        cmd = ["qubes-prefs", "default_dispvm"]
        result = subprocess.check_output(cmd).decode("utf-8").rstrip("\n")
        self.assertEqual(result, "fedora-29-dvm")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Platform_Tests)
    return suite
