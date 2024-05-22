import unittest

from base import SD_VM_Local_Test


class SD_Proxy_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-proxy"
        super(SD_Proxy_Tests, self).setUp()
        self.expected_config_keys = {"SD_PROXY_ORIGIN"}

    def test_do_not_open_here(self):
        """
        The do-not-open here script has been removed from sd-proxy.
        All VMs now default to using open-in-dvm.
        """
        assert not self._fileExists("/usr/bin/do-not-open-here")

    def test_sd_proxy_package_installed(self):
        self.assertTrue(self._package_is_installed("securedrop-proxy"))

    def test_sd_proxy_config(self):
        self.assertEqual(
            f"http://{self.dom0_config['hidserv']['hostname']}",
            self._vm_config_read("SD_PROXY_ORIGIN"),
        )

    def test_whonix_ws_repo_absent(self):
        """
        The sd-proxy VM was previously based on Whonix Workstation,
        but we've since moved to the standard SDW Debian-based template.
        Guard against regressions by ensuring the old Whonix apt list
        is missing.
        """
        # Whonix project changed the repo filename ~2021-05, so check both.
        assert not self._fileExists("/etc/apt/sources.list.d/whonix.list")
        assert not self._fileExists("/etc/apt/sources.list.d/derivative.list")

    def test_logging_configured(self):
        self.logging_configured()

    def test_mime_types(self):
        cmd = "perl -F= -lane 'print $F[0]' /usr/share/applications/mimeapps.list"
        results = self._run(cmd)
        for line in results.split("\n"):
            if line != "[Default Applications]" and not line.startswith("#"):
                actual_app = self._run("xdg-mime query default {}".format(line))
                self.assertEqual(actual_app, "open-in-dvm.desktop")

    def test_mailcap_hardened(self):
        self.mailcap_hardened()


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Proxy_Tests)
    return suite
