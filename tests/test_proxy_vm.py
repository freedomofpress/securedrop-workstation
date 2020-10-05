import unittest
import json

from base import SD_VM_Local_Test


class SD_Proxy_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-proxy"
        super(SD_Proxy_Tests, self).setUp()

    def test_do_not_open_here(self):
        """
        The do-not-open here script has been removed from sd-proxy.
        All VMs now default to using open-in-dvm.
        """
        assert not self._fileExists("/usr/bin/do-not-open-here")

    def test_sd_proxy_package_installed(self):
        self.assertTrue(self._package_is_installed("securedrop-proxy"))

    def test_sd_proxy_yaml_config(self):
        with open("config.json") as c:
            config = json.load(c)
            hostname = config["hidserv"]["hostname"]

        wanted_lines = [
            "host: {}".format(hostname),
            "scheme: http",
            "port: 80",
            "target_vm: sd-app",
            "dev: False",
        ]
        for line in wanted_lines:
            self.assertFileHasLine("/etc/sd-proxy.yaml", line)

    def test_whonix_ws_repo_absent(self):
        """
        The sd-proxy VM was previously based on Whonix Workstation,
        but we've since moved to the standard SDW Debian-based template.
        Guard against regressions by ensuring the old Whonix apt list
        is missing.
        """
        assert not self._fileExists("/etc/apt/sources.list.d/whonix.list")

    def test_logging_configured(self):
        self.logging_configured()

    def test_mime_types(self):
        cmd = "perl -F= -lane 'print $F[0]' /usr/share/applications/mimeapps.list"
        results = self._run(cmd)
        for line in results.split("\n"):
            if line != "[Default Applications]" and not line.startswith("#"):
                actual_app = self._run("xdg-mime query default {}".format(line))
                self.assertEqual(actual_app, "open-in-dvm.desktop")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Proxy_Tests)
    return suite
