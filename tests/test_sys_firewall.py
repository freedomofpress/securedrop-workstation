import json
import unittest

from base import SD_VM_Local_Test
from test_dom0_rpm_repo import SD_Dom0_Rpm_Repo_Tests


class SD_Sys_Firewall_Tests(SD_VM_Local_Test):
    pubkey_wanted = ""

    def setUp(self):
        self.vm_name = "sys-firewall"
        super(SD_Sys_Firewall_Tests, self).setUp()
        with open("config.json") as c:
            config = json.load(c)
            # default to prod
            if 'environment' not in config:
                config['environment'] = 'prod'

            if config['environment'] == 'prod':
                self.pubkey_wanted = SD_Dom0_Rpm_Repo_Tests.pubkey_wanted_prod
            else:
                self.pubkey_wanted = SD_Dom0_Rpm_Repo_Tests.pubkey_wanted_test

    def test_rpm_repo_public_key(self):
        self.assertFilesMatch(SD_Dom0_Rpm_Repo_Tests.pubkey_actual,  # noqa
                              self.pubkey_wanted)

    def test_rpm_repo_public_key_script(self):
        self.assertFilesMatch("/rw/config/sd-copy-rpm-repo-pubkey.sh",
                              "sys-firewall/sd-copy-rpm-repo-pubkey.sh")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Sys_Firewall_Tests)
    return suite
