import unittest
import json

from base import SD_VM_Local_Test


class SD_Proxy_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-proxy"
        self.whonix_apt_list = "/etc/apt/sources.list.d/whonix.list"
        super(SD_Proxy_Tests, self).setUp()

    def test_do_not_open_here(self):
        self.assertFilesMatch("/usr/bin/do-not-open-here",
                              "sd-proxy/do-not-open-here")

    def test_sd_proxy_package_installed(self):
        self.assertTrue(self._package_is_installed("securedrop-proxy"))

    def test_sd_proxy_yaml_config(self):
        with open("config.json") as c:
            config = json.load(c)
            hostname = config['hidserv']['hostname']

        wanted_lines = [
            "host: {}".format(hostname),
            "scheme: http",
            "port: 80",
            "target_vm: sd-app",
            "dev: False",
        ]
        for line in wanted_lines:
            self.assertFileHasLine("/etc/sd-proxy.yaml", line)

    def test_whonix_ws_repo_enabled(self):
        """
        During Whonix 14 -> 15 migration, we removed the apt list file
        (because the repo wasn't serving, due to EOL status). Let's
        make sure it's there, since we're past 14 now.
        """
        assert self._fileExists(self.whonix_apt_list)

    def test_logging_configured(self):
        self.logging_configured()


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Proxy_Tests)
    return suite
