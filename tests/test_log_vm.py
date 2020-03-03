import unittest

from base import SD_VM_Local_Test


class SD_Log_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-log"
        super(SD_Log_Tests, self).setUp()

    def test_sd_log_package_installed(self):
        self.assertTrue(self._package_is_installed("securedrop-log"))

    def test_sd_log_redis_is_installed(self):
        self.assertTrue(self._package_is_installed("redis"))
        self.assertTrue(self._package_is_installed("redis-server"))

    def test_log_utility_installed(self):
        self.assertTrue(self._fileExists("/usr/sbin/securedrop-log"))
        self.assertTrue(self._fileExists("/etc/qubes-rpc/securedrop.Log"))

    def test_sd_log_has_no_custom_rsyslog(self):
        self.assertFalse(self._fileExists("/etc/rsyslog.d/sdlog.conf"))

    def test_sd_log_service_running(self):
        results = self._run("sudo systemctl is-active securedrop-log")
        assert results == "active"

    def test_redis_service_running(self):
        results = self._run("sudo systemctl is-active redis")
        assert results == "active"


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Log_Tests)
    return suite
