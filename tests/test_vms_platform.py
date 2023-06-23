import json
import unittest
import subprocess

from qubesadmin import Qubes
from base import WANTED_VMS, CURRENT_FEDORA_TEMPLATE


BULLSEYE_STRING = "Debian GNU/Linux 11 (bullseye)"

SUPPORTED_SD_DEBIAN_DIST = "bullseye"
SUPPORTED_WHONIX_PLATFORMS = [BULLSEYE_STRING]


apt_url = ""
FPF_APT_TEST_SOURCES = "deb [arch=amd64] https://apt-test.freedom.press {dist} {component}"
FPF_APT_SOURCES = "deb [arch=amd64] https://apt.freedom.press {dist} {component}"
APT_SOURCES_FILE = "/etc/apt/sources.list.d/securedrop_workstation.list"


class SD_VM_Platform_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()
        with open("config.json") as c:
            config = json.load(c)
            if "environment" not in config:
                config["environment"] = "dev"

            dist = SUPPORTED_SD_DEBIAN_DIST

            if config["environment"] == "prod":
                self.apt_url = FPF_APT_SOURCES.format(dist=dist, component="main")
            elif config["environment"] == "staging":
                self.apt_url = FPF_APT_TEST_SOURCES.format(dist=dist, component="main")
            else:
                self.apt_url = FPF_APT_TEST_SOURCES.format(dist=dist, component="nightlies")

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
        SUPPORTED_<XX>_PLATFORMS list, as specified in tests.
        sd-whonix is based on the whonix-16 template.
        All other workstation-provisioned VMs should be
        SUPPORTED_SD_DEBIAN_DIST based.
        """
        platform = self._get_platform_info(vm)
        if vm.name in ["sd-whonix"]:
            self.assertIn(platform, SUPPORTED_WHONIX_PLATFORMS)
        else:
            self.assertIn(SUPPORTED_SD_DEBIAN_DIST, platform)

    def _validate_apt_sources(self, vm):
        """
        Asserts that the given AppVM has the proper apt sources list in
        /etc/apt/sources.list.d/securedrop_workstation.list
        """

        # sd-whonix does not use the fpf-apt-test-repo
        if vm.name in ["sd-whonix"]:
            return

        cmd = "cat {}".format(APT_SOURCES_FILE)
        stdout, stderr = vm.run(cmd)
        contents = stdout.decode("utf-8").rstrip("\n")

        self.assertTrue(self.apt_url in contents)

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
            stdout_lines = results.split("\n")
            # filter out gpgcheck warning present on all dnf operations
            stdout_lines = [
                x
                for x in stdout_lines
                if not x.startswith("Warning: Enforcing GPG signature check")
            ]
            results = "".join(stdout_lines)
            self.assertEqual(results, "", fail_msg)

    def _ensure_keyring_package_exists_and_has_correct_key(self, vm):
        """
        Inspect the securedrop-keyring used by apt to ensure the correct key
        and only the correct key is installed in that location.
        """
        # sd-whonix does not require the keyring package
        if vm.name in ["sd-whonix"]:
            return

        keyring_path = "/etc/apt/trusted.gpg.d/securedrop-keyring.gpg"
        cmd = "gpg --homedir /tmp --no-default-keyring --keyring {} -k".format(keyring_path)
        cmd = "apt-key --keyring {} finger".format(keyring_path)
        stdout, stderr = vm.run(cmd)
        results = stdout.rstrip().decode("utf-8")
        fpf_gpg_pub_key_info = """/etc/apt/trusted.gpg.d/securedrop-keyring.gpg
---------------------------------------------
pub   rsa4096 2021-05-10 [SC] [expires: 2024-07-08]
      2359 E653 8C06 13E6 5295  5E6C 188E DD3B 7B22 E6A3
uid           [ unknown] SecureDrop Release Signing Key <securedrop-release-key-2021@freedom.press>
sub   rsa4096 2021-05-10 [E] [expires: 2024-07-08]"""
        # display any differences
        self.maxDiff = None
        self.assertEqual(results, fpf_gpg_pub_key_info), "Keyring incorrect in " + vm.name

    def _ensure_trusted_keyring_securedrop_key_removed(self, vm):
        """
        Ensures the production key is no longer found in the default apt keyring.
        In dev/staging environments, that keyring will be used for the test apt key,
        so we only check against the production fingerprint. The goal is to ensure
        the production key is kept separate from other keys.
        """
        # apt-key finger doesnt work here due to stdout/terminal
        cmd = "gpg --no-default-keyring --keyring /etc/apt/trusted.gpg -k"
        stdout, stderr = vm.run(cmd)
        results = stdout.rstrip().decode("utf-8")
        fpf_gpg_pub_key_fp = "2359E6538C0613E652955E6C188EDD3B7B22E6A3"
        self.assertFalse(fpf_gpg_pub_key_fp in results)

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
        # AppVMs are based on the most recent Fedora version.
        vm_name = CURRENT_FEDORA_TEMPLATE
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

    def test_debian_keyring_config(self):
        """
        Ensure the securedrop keyring package is properly installed and the
        key it contains is up-to-date.
        """
        for vm_name in WANTED_VMS:
            vm = self.app.domains[vm_name]
            self._ensure_keyring_package_exists_and_has_correct_key(vm)
            self._ensure_trusted_keyring_securedrop_key_removed(vm)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Platform_Tests)
    return suite
