import subprocess
import time
import unittest

from qubesadmin import Qubes


# Reusable constant for DRY import across tests
WANTED_VMS = [
    "sd-gpg",
    "sd-log",
    "sd-proxy",
    "sd-app",
    "sd-viewer",
    "sd-whonix",
    "sd-devices"
]


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
                msg = ("Need to halt connected VM {}"
                       " before testing".format(v))
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
        cmd = ["qvm-run", "-p", self.vm_name,
               "sudo /bin/cat {}".format(path)]
        contents = subprocess.check_output(cmd).decode("utf-8")
        return contents

    def _package_is_installed(self, pkg):
        """
        Confirms that a given package is installed inside the VM.
        """
        # dpkg --verify will exit non-zero for a non-installed pkg,
        # and dom0 will percolate that error code
        subprocess.check_call(["qvm-run", "-a", "-q", self.vm_name,
                               "dpkg --verify {}".format(pkg)])
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
        msg = "File {} does not contain expected line {}".format(remote_path,
                                                                 wanted_line)
        raise AssertionError(msg)

    def _fileExists(self, remote_path):
        # ls will return non-zero if the file doesn't exists
        # and error will be propagated to the unittest
        # ls will return non-zero and an exception will be thrown if the file
        # does not exist, so we return false in that case.
        try:
            subprocess.check_call(["qvm-run", "-a", "-q", self.vm_name,
                                   "ls {}".format(remote_path)])
        except subprocess.CalledProcessError:
            return False

        return True

    def logging_configured(self, vmname=False):
        """
        Make sure rsyslog is configured to send in data to sd-log vm.
        Takes an optional 'vmname' argument, in case hostname
        returned by system is an insufficient identifier, e.g. Whonix.
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
        # A hardcoded vmname should only be present if required,
        # since securedrop-log will default to value of `hostname`.
        if vmname:
            static_content += "localvm = {}\n".format(self.vm_name)
        self.assertEqual(file_content, static_content)
        # Check for evidence of misconfigured logging in syslog,
        # fail if matching events found
        # Several VMs show this error message even though they're shipping logs,
        # so let's investigate further.
        # cmd_output = self._run("sudo grep -F \"action 'action-0-omprog' suspended (module 'omprog')\" /var/log/syslog | wc -l").strip()  # noqa
        # self.assertTrue(cmd_output == "0")
