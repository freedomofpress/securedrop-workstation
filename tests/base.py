import json
import subprocess
import time
import unittest

from qubesadmin import Qubes

# Reusable constant for DRY import across tests
DEBIAN_VERSION = "bookworm"
SD_TEMPLATE_BASE = f"sd-base-{DEBIAN_VERSION}-template"
SD_TEMPLATE_LARGE = f"sd-large-{DEBIAN_VERSION}-template"
SD_TEMPLATE_SMALL = f"sd-small-{DEBIAN_VERSION}-template"

SD_VMS = ["sd-gpg", "sd-log", "sd-proxy", "sd-app", "sd-viewer", "sd-whonix", "sd-devices"]
SD_DVM_TEMPLATES = ["sd-devices-dvm", "sd-proxy-dvm"]
SD_TEMPLATES = [SD_TEMPLATE_BASE, SD_TEMPLATE_LARGE, SD_TEMPLATE_SMALL]

CURRENT_FEDORA_VERSION = "40"
CURRENT_FEDORA_TEMPLATE = "fedora-" + CURRENT_FEDORA_VERSION + "-xfce"
CURRENT_FEDORA_DVM = "fedora-" + CURRENT_FEDORA_VERSION + "-dvm"
CURRENT_WHONIX_VERSION = "17"
CURRENT_DEBIAN_VERSION = "bookworm"


# Lifted from launcher/sdw_util/Util.py
def get_qubes_version():
    """
    Helper function for checking the Qubes version. Returns None if not on Qubes.
    """
    is_qubes = False
    version = None
    try:
        with open("/etc/os-release") as f:
            for line in f:
                try:
                    key, value = line.rstrip().split("=")
                except ValueError:
                    continue
                if key == "NAME" and "qubes" in value.lower():
                    is_qubes = True
                if key == "VERSION_ID":
                    version = value
    except FileNotFoundError:
        return None
    if not is_qubes:
        return None
    return version


# base class for per-VM testing


class SD_VM_Local_Test(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()
        self.vm = self.app.domains[self.vm_name]
        # self._reboot()
        if self.vm.is_running():
            pass
        else:
            self.vm.start()

        # Make the dom0 "config.json" available to tests.
        with open("config.json") as config_file:
            self.dom0_config = json.load(config_file)

        # A VM shouldn't have any configuration keys it doesn't explicitly
        # expect.
        self.expected_config_keys = set()

        # Which Linux Security Module (LSM) should be enabled
        self.lsm = "apparmor"
        # AppArmor profiles that should be enforced.
        self.enforced_apparmor_profiles = set()

    # def tearDown(self):
    #     self.vm.shutdown()

    def _reboot(self):
        # The for-loop below should be couched in a try/except block.
        # Further testing required to determine which specific exceptions
        # to catch; a few ideas:
        #
        #   * CalledProcessorError
        #   * QubesVMError (from qubesadmin.base)
        #   * QubesVMNotStartedError (from qubesadmin.base)
        for v in list(self.vm.connected_vms.values()):
            if v.is_running():
                msg = f"Need to halt connected VM {v}" " before testing"
                print(msg)
                v.shutdown()
                while v.is_running():
                    time.sleep(1)

        if self.vm.is_running():
            self.vm.shutdown()

        while self.vm.is_running():
            time.sleep(1)

        self.vm.start()

    def _run(self, cmd, user=""):
        full_cmd = ["qvm-run", "-p"]
        if user:
            full_cmd += ["-u", user]
        full_cmd += [self.vm_name, cmd]
        return subprocess.check_output(full_cmd).decode("utf-8").strip()

    def _get_file_contents(self, path):
        cmd = ["qvm-run", "-p", self.vm_name, f"sudo /bin/cat {path}"]
        return subprocess.check_output(cmd).decode("utf-8")

    def _get_symlink_location(self, path):
        cmd = ["qvm-run", "-p", self.vm_name, f"/usr/bin/readlink -f {path}"]
        return subprocess.check_output(cmd).decode("utf-8").strip()

    def _package_is_installed(self, pkg):
        """
        Confirms that a given package is installed inside the VM.
        """
        # dpkg --verify will exit non-zero for a non-installed pkg,
        # catch that and return False
        try:
            subprocess.check_call(["qvm-run", "-a", "-q", self.vm_name, f"dpkg --verify {pkg}"])
        except subprocess.CalledProcessError:
            return False

        return True

    def _service_is_active(self, service):
        try:
            results = self._run(f"sudo systemctl is-active {service}")
        except subprocess.CalledProcessError as e:
            if e.returncode == 3:
                return False  # exit code 3 == inactive
            else:
                raise e
        return results == "active"

    def assertFilesMatch(self, remote_path, local_path):
        remote_content = self._get_file_contents(remote_path)

        content = False
        with open(local_path) as f:
            content = f.read()
        import difflib

        print("".join(difflib.unified_diff(remote_content, content)), end="")
        self.assertEqual(remote_content, content)

    def assertFileHasLine(self, remote_path, wanted_line):
        remote_content = self._get_file_contents(remote_path)
        lines = remote_content.splitlines()
        for line in lines:
            if line == wanted_line:
                return True
        msg = f"File {remote_path} does not contain expected line {wanted_line}"
        raise AssertionError(msg)

    def _fileExists(self, remote_path):
        # ls will return non-zero if the file doesn't exists
        # and error will be propagated to the unittest
        # ls will return non-zero and an exception will be thrown if the file
        # does not exist, so we return false in that case.
        try:
            subprocess.check_call(["qvm-run", "-a", "-q", self.vm_name, f"ls {remote_path}"])
        except subprocess.CalledProcessError:
            return False

        return True

    def _qubes_service_enabled(self, service):
        """Check whether the named Qubes service is enabled on this
        VM."""
        return self._fileExists(f"/var/run/qubes-service/{service}")

    def _vm_config_read(self, key):
        """Read `key` from the QubesDB `/vm-config/` hierarchy and return its
        value if set, otherwise `None`.
        """
        try:
            return self._run(f"qubesdb-read /vm-config/{key}")
        except subprocess.CalledProcessError:
            return None

    def _vm_config_check(self, expected):
        """Check that the set of expected by the VM keys equals the set of keys
        actually configured.
        """
        actual = set(self._run("qubesdb-list /vm-config/").split("\n"))
        actual.discard("")  # if "qubesdb-list" returned nothing
        self.assertEqual(actual, set(expected))

    def logging_configured(self):
        """
        Make sure rsyslog is configured to send in data to sd-log vm.
        """
        # Logging is not disabled
        self.assertFalse(self._fileExists("/var/run/qubes-service/securedrop-logging-disabled"))

        self.assertTrue(self._package_is_installed("securedrop-log"))
        self.assertTrue(self._fileExists("/usr/sbin/sd-rsyslog"))
        self.assertTrue(self._fileExists("/etc/rsyslog.d/sdlog.conf"))
        self.assertTrue(self._fileExists("/etc/sd-rsyslog.conf"))
        # Then we check the configuration inside of the file.
        file_content = self._get_file_contents("/etc/sd-rsyslog.conf")
        static_content = """[sd-rsyslog]
remotevm = sd-log
"""
        self.assertEqual(file_content, static_content)
        # Check for evidence of misconfigured logging in syslog,
        # fail if matching events found
        # Several VMs show this error message even though they're shipping logs,
        # so let's investigate further.
        # cmd_output = self._run("sudo grep -F \"action 'action-0-omprog' suspended (module 'omprog')\" /var/log/syslog | wc -l").strip()  # noqa
        # self.assertEqual(cmd_output, "0")

    def mailcap_hardened(self):
        """
        Ensure that mailcap rules are not used as a fallback when looking up
        appropriate viewer applications for files of a given MIME type.
        """

        # Ensure that mailcap configuration files are present in the expected
        # locations and contain the expected contents. Rules in `~/.mailcap`
        # take precedence over those in `/etc/mailcap`.
        self.assertTrue(self._fileExists("/home/user/.mailcap"))
        self.assertTrue(self._fileExists("/opt/sdw/mailcap.default"))
        self.assertFileHasLine("/home/user/.mailcap", '*/*; logger "Mailcap is disabled."')

        # Because we target an AppVM, we cannot easily use the Pyhton tempfile
        # module here without relying on a helper script. Instead, we use the
        # mktemp utility to create a test file with the OpenDocument extension.
        tmpfile_name = self._run("mktemp -t XXXXXX.odt")

        # The --norun argument ensures that we do not launch any application,
        # regardless of the result of this invocation.
        mailcap_result = self._run(f"run-mailcap --norun {tmpfile_name}")

        # For simplicity, we remove the tempfile here instead of in a separate
        # teardown method.
        self._run(f"rm {tmpfile_name}")

        # Ensure that the wildcard rule worked as expected.
        self.assertEqual(mailcap_result, f'logger "Mailcap is disabled." <{tmpfile_name}')

    def test_vm_config_keys(self):
        """Every VM should check that it has only the configuration keys it
        expects.
        """
        self._vm_config_check(self.expected_config_keys)

    def test_lsm_enabled(self):
        """Check that the expected LSM is enabled"""
        if self.lsm == "apparmor":
            self.assertTrue(self._package_is_installed("apparmor"))
            # returns error code if AppArmor not enabled
            self._run("sudo aa-status --enabled")
        elif self.lsm == "selinux":
            sestatus = self._run("sudo sestatus")
            self.assertIn("SELinux status:                 enabled\n", sestatus)
            self.assertIn("Current mode:                   enforcing\n", sestatus)
        else:
            raise ValueError(f"Unsupported LSM: {self.lsm}")

    def test_enforced_apparmor_profiles(self):
        """Check the expected AppArmor profiles are enforced"""
        if not self.enforced_apparmor_profiles:
            raise unittest.SkipTest(f"No enforced AppArmor profiles in {self.vm_name}")
        results = json.loads(self._run("sudo aa-status --json"))
        for profile in self.enforced_apparmor_profiles:
            self.assertEqual(results["profiles"][profile], "enforce")


class SD_Unnamed_DVM_Local_Test(SD_VM_Local_Test):
    """Tests disposables based on the provided DVM template"""

    @classmethod
    def _kill_test_vm(cls):
        subprocess.run(["qvm-kill", cls.vm_name], check=True)

    @classmethod
    def setUpClass(cls, dispvm_template_name):
        cls.app = Qubes()
        cls.vm_name = f"{dispvm_template_name}-disposable"

        # VM was running and needs a restart to test on the latest version
        if cls.vm_name in cls.app.domains:
            cls._kill_test_vm()
        # Create disposable based on specified template
        cmd_create_disp = (
            f"qvm-create --disp --property auto_cleanup=True "
            f"--template {dispvm_template_name} {cls.vm_name}"
        )
        subprocess.run(cmd_create_disp.split(), check=True)

    @classmethod
    def tearDownClass(cls):
        cls._kill_test_vm()
