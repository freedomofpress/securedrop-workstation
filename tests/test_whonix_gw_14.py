import unittest

from base import SD_VM_Local_Test


class Whonix_Gateway_14_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "whonix-gw-14"
        self.whonix_apt_list = "/etc/apt/sources.list.d/whonix.list"
        super(Whonix_Gateway_14_Tests, self).setUp()

    def test_whonix_ws_14_repo_disabled(self):
        assert self._fileExists(self.whonix_apt_list) is False


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(Whonix_Gateway_14_Tests)
    return suite
