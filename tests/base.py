import subprocess
import time
import unittest

from qubesadmin import Qubes


# Reusable constant for DRY import across tests
WANTED_VMS = [
    "sd-gpg",
    "sd-log",
    "sd-proxy",
    "sd-svs",
    "sd-svs-disp",
    "sd-whonix",
    "sd-export-usb"
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

    def _run(self, cmd):
        full_cmd = ["qvm-run", "-p", self.vm_name, cmd]
        contents = subprocess.check_output(full_cmd).decode("utf-8").strip()
        return contents

    def _get_file_contents(self, path):
        cmd = ["qvm-run", "-p", self.vm_name,
               "/bin/cat {}".format(path)]
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
