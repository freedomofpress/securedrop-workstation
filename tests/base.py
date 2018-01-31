import subprocess
import time
import unittest

from qubesadmin import Qubes

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
        try:
            for v in self.vm.connected_vms.values():
                if v.is_running():
                    msg = ("Need to halt connected VM {}"
                           " before testing".format(v))
                    print(msg)
                    v.shutdown()
                    while v.is_running():
                        time.sleep(1)
        except:
            pass

        if self.vm.is_running():
            self.vm.shutdown()

        while self.vm.is_running():
            time.sleep(1)

        self.vm.start()

    def _get_file_contents(self, path):
        contents = subprocess.check_output(["qvm-run", "-p", self.vm_name,
                                            "/bin/cat {}".format(path)])
        return contents

    def assertFilesMatch(self, remote_path, local_path):
        remote_content = self._get_file_contents(remote_path)

        content = False
        with open(local_path) as f:
            content = f.read()
        import difflib
        print "".join(difflib.unified_diff(remote_content, content))
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
