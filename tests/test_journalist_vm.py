import unittest
import json

from base import SD_VM_Local_Test


class SD_Journalist_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-journalist"
        super(SD_Journalist_Tests, self).setUp()

    def test_do_not_open_here(self):
        self.assertFilesMatch("/usr/bin/do-not-open-here",
                              "sd-journalist/do-not-open-here")

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
            "target_vm: sd-svs",
            "dev: False",
        ]
        for line in wanted_lines:
            self.assertFileHasLine("/etc/sd-proxy.yaml", line)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Journalist_Tests)
    return suite
