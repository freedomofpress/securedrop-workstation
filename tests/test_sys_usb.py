import unittest

from base import SD_VM_Local_Test


class SD_SysUSB_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sys-usb"
        super().setUp()
        self.lsm = "selinux"

    def test_files_are_properly_copied(self):
        self.assertTrue(self._fileExists("/etc/udev/rules.d/99-sd-devices.rules"))
        self.assertTrue(self._fileExists("/usr/local/bin/sd-attach-export-device"))


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_SysUSB_Tests)
