import unittest

from base import SD_VM_Local_Test


class SD_Log_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-log"
        super(SD_Log_Tests, self).setUp()

    def test_sd_log_package_installed(self):
        self.assertTrue(self._package_is_installed("securedrop-log"))

    def test_log_utility_installed(self):
        self.assertTrue(self._fileExists("/usr/sbin/securedrop-log"))
        self.assertTrue(self._fileExists("/etc/qubes-rpc/securedrop.Log"))


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Log_Tests)
    return suite
