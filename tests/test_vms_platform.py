import json
import unittest
import subprocess

from qubesadmin import Qubes
from base import WANTED_VMS


SUPPORTED_PLATFORMS = [
    "Debian GNU/Linux 10 (buster)",
]

apt_url = ""
FPF_APT_SOURCES_STRETCH_DEV = "deb [arch=amd64] https://apt-test.freedom.press stretch main"
FPF_APT_SOURCES_BUSTER_DEV = "deb [arch=amd64] https://apt-test.freedom.press buster main"
FPF_APT_SOURCES_STRETCH = "deb [arch=amd64] https://apt.freedom.press stretch main"
FPF_APT_SOURCES_BUSTER = "deb [arch=amd64] https://apt.freedom.press buster main"
APT_SOURCES_FILE = "/etc/apt/sources.list.d/securedrop_workstation.list"


class SD_VM_Platform_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()
        with open("config.json") as c:
            config = json.load(c)
            # default to prod
            if 'environment' not in config:
                config['environment'] = 'prod'

            if config['environment'] == 'prod':
                self.apt_url = FPF_APT_SOURCES_BUSTER
            else:
                self.apt_url = FPF_APT_SOURCES_BUSTER_DEV

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
        sd-whonix and sd-proxy are based on whonix-14 templates, which are
        derived from debian stretch. All other workstation-provisioned VMs
        should be buster based.
        """
        platform = self._get_platform_info(vm)
        self.assertIn(platform, SUPPORTED_PLATFORMS)

    def _validate_apt_sources(self, vm):
        """
        Asserts that the given AppVM has the proper apt sources list in
        /etc/apt/sources.list.d/securedrop_workstation.list
        """

        # sd-whonix does not use the fpf-apt-test-repo
        if vm.name in ["sd-whonix"]:
            pass
        else:
            cmd = "cat {}".format(APT_SOURCES_FILE)
            stdout, stderr = vm.run(cmd)
            contents = stdout.decode("utf-8").rstrip("\n")

            self.assertTrue(self.apt_url in contents)
            self.assertFalse(FPF_APT_SOURCES_STRETCH in contents)
            # Old alpha URL for apt repo should be absent
            self.assertFalse("apt-test-qubes.freedom.press" in contents)

    def _ensure_packages_up_to_date(self, vm, fedora=False):
        """
        Asserts that all available packages are installed; no pending
        updates. Assumes VM is Debian-based, so uses apt, but supports
        `fedora=True` to use dnf instead.
        """
        # Create custom error message, so failing test cases display
        # which VM caused the looped check to fail.
        fail_msg = "Unapplied updates for VM '{}'".format(vm)
        if not fedora:
            cmd = "apt list --upgradable"
            stdout, stderr = vm.run(cmd)
            results = stdout.rstrip().decode("utf-8")
            # `apt list` will always print "Listing..." to stdout,
            # so expect only that string.
            self.assertEqual(results, "Listing...", fail_msg)
        else:
            cmd = "sudo dnf check-update"
            # Will raise CalledProcessError if updates available
            stdout, stderr = vm.run(cmd)
            # 'stdout' will contain timestamped progress info; ignore it
            results = stderr.rstrip().decode("utf-8")
            self.assertEqual(results, "", fail_msg)

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
        # AppVMs are based on fedora-30.
        vm_name = "fedora-30"
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
        self.assertEqual(result, "sd-viewer")

    def test_sys_vms_use_supported_fedora(self):
        """
        The 'sys-*' VMs must be updated to use the latest version of Fedora,
        to ensure critical components such as 'sys-firewall' receive security
        updates.
        """
        sys_vms = [
            "sys-firewall",
            "sys-net",
            "sys-usb",
        ]
        for vm in sys_vms:
            wanted_template = "fedora-30"
            found_template = self.app.domains[vm].template.name
            self.assertEqual(wanted_template, found_template)

    def test_all_sd_vm_apt_sources(self):
        """
        Test all VMs fpf apt source list iteratively.

        Due to for-loop implementation, the first failure will stop the test.
        Therefore, even if multiple VMs are NOT running a supported platform,
        only a single failure will be reported.
        """
        for vm_name in WANTED_VMS:
            vm = self.app.domains[vm_name]
            self._validate_apt_sources(vm)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Platform_Tests)
    return suite
