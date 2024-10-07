import unittest

from base import SD_VM_Local_Test


class SD_Proxy_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-proxy"
        super().setUp()
        self.expected_config_keys = {"SD_PROXY_ORIGIN", "SD_MIME_HANDLING"}
        self.enforced_apparmor_profiles = {"/usr/bin/securedrop-proxy"}

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

    def test_mimeapps(self):
        results = self._run("cat /usr/share/applications/mimeapps.list")
        for line in results.splitlines():
            if line.startswith(("#", "[Default")):
                # Skip comments and the leading [Default Applications]
                continue
            mime, target = line.split("=", 1)
            self.assertEqual(target, "open-in-dvm.desktop;")
            # Now functionally test it
            actual_app = self._run(f"xdg-mime query default {mime}")
            self.assertEqual(actual_app, "open-in-dvm.desktop")

    def test_mailcap_hardened(self):
        self.mailcap_hardened()


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_Proxy_Tests)
