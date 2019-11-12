import unittest
import json
from jinja2 import Template

from base import SD_VM_Local_Test


class SD_Whonix_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-whonix"
        self.whonix_apt_list = "/etc/apt/sources.list.d/whonix.list"
        super(SD_Whonix_Tests, self).setUp()

    def test_accept_sd_xfer_extracted_file(self):
        with open("config.json") as c:
            config = json.load(c)
            t = Template("HidServAuth {{ d.hidserv.hostname }}"
                         " {{ d.hidserv.key }}")
            line = t.render(d=config)

            self.assertFileHasLine("/usr/local/etc/torrc.d/50_user.conf", line)

    def test_sd_whonix_repo_disabled(self):
        assert self._fileExists(self.whonix_apt_list) is False


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Whonix_Tests)
    return suite
