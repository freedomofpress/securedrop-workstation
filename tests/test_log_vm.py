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

    def test_logs_are_flowing(self):
        cmd_output = self._run("ls -1 /home/user/QubesIncomingLogs")
        log_dirs = cmd_output.split("\n")
        # Confirm AppVMs are sending logs
        self.assertTrue("sd-app" in log_dirs)
        # The following will only have logs if the machine has booted,
        # which is not guaranteed given that we randomize test order.
        # self.assertTrue("sd-devices" in log_dirs)
        # self.assertTrue("sd-proxy" in log_dirs)
        # self.assertTrue("sd-viewer" in log_dirs)

    def test_log_dirs_properly_named(self):
        # Rerunning this command to keep test output readable
        cmd_output = self._run("ls -1 /home/user/QubesIncomingLogs")
        log_dirs = cmd_output.split("\n")
        # Confirm we don't have 'host' entries from Whonix VMs
        self.assertFalse("host" in log_dirs)

    def test_gpg_domain_configured(self):
        self.qubes_gpg_domain_configured(self.vm_name)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Log_Tests)
    return suite
