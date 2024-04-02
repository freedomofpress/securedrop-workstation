import subprocess
import time
import unittest

from qubesadmin import Qubes


# Reusable constant for DRY import across tests
WANTED_VMS = ["sd-gpg", "sd-log", "sd-proxy", "sd-app", "sd-viewer", "sd-whonix", "sd-devices"]
CURRENT_FEDORA_VERSION = "39"
CURRENT_FEDORA_TEMPLATE = "fedora-" + CURRENT_FEDORA_VERSION + "-xfce"
CURRENT_FEDORA_DVM = "fedora-" + CURRENT_FEDORA_VERSION + "-dvm"
CURRENT_WHONIX_VERSION = "17"


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
                msg = "Need to halt connected VM {}" " before testing".format(v)
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
        contents = subprocess.check_output(full_cmd).decode("utf-8").strip()
        return contents

    def _get_file_contents(self, path):
        cmd = ["qvm-run", "-p", self.vm_name, "sudo /bin/cat {}".format(path)]
        contents = subprocess.check_output(cmd).decode("utf-8")
        return contents

    def _package_is_installed(self, pkg):
        """
        Confirms that a given package is installed inside the VM.
        """
        # dpkg --verify will exit non-zero for a non-installed pkg,
        # catch that and return False
        try:
            subprocess.check_call(
                ["qvm-run", "-a", "-q", self.vm_name, "dpkg --verify {}".format(pkg)]
            )
        except subprocess.CalledProcessError:
            return False

        return True

    def assertFilesMatch(self, remote_path, local_path):
        remote_content = self._get_file_contents(remote_path)

        content = False
        with open(local_path) as f:
            content = f.read()
        import difflib

        print("".join(difflib.unified_diff(remote_content, content)), end="")
        self.assertTrue(remote_content == content)

    def assertFileHasLine(self, remote_path, wanted_line):
        remote_content = self._get_file_contents(remote_path)
        lines = remote_content.splitlines()
        for line in lines:
            if line == wanted_line:
                return True
        msg = "File {} does not contain expected line {}".format(remote_path, wanted_line)
        raise AssertionError(msg)

    def _fileExists(self, remote_path):
        # ls will return non-zero if the file doesn't exists
        # and error will be propagated to the unittest
        # ls will return non-zero and an exception will be thrown if the file
        # does not exist, so we return false in that case.
        try:
            subprocess.check_call(
                ["qvm-run", "-a", "-q", self.vm_name, "ls {}".format(remote_path)]
            )
        except subprocess.CalledProcessError:
            return False

        return True

    def logging_configured(self):
        """
        Make sure rsyslog is configured to send in data to sd-log vm.
        """
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
        # self.assertTrue(cmd_output == "0")

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
        mailcap_result = self._run("run-mailcap --norun {}".format(tmpfile_name))

        # For simplicity, we remove the tempfile here instead of in a separate
        # teardown method.
        self._run("rm {}".format(tmpfile_name))

        # Ensure that the wildcard rule worked as expected.
        self.assertEqual(mailcap_result, 'logger "Mailcap is disabled." <{}'.format(tmpfile_name))

    def qubes_gpg_domain_configured(self, vmname=False):
        """
        Ensure the QUBES_GPG_DOMAIN is properly set for a given AppVM. This
        var is set by a script /etc/profile.d.
        sd-app should have it set to sd-gpg.
        All other AppVMs should not have this configured.
        """
        env_cmd = 'echo "$QUBES_GPG_DOMAIN"'
        env_contents = self._run(env_cmd)

        if vmname == "sd-app":
            expected_env = "sd-gpg"
        else:
            expected_env = ""

        self.assertEqual(env_contents, expected_env)
