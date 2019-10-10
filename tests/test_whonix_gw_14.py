import unittest

from base import SD_VM_Local_Test


class Whonix_Gateway_14_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "whonix-gw-14"
        self.whonix_apt_list = "/etc/apt/sources.list.d/whonix.list"
        super(Whonix_Gateway_14_Tests, self).setUp()

    def test_whonix_gw_14_onion_repo_disabled(self):
        whonix_apt_repo_disabled = "#deb tor+http://deb.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion stretch main contrib non-free"  # noqa
        self.assertFileHasLine(self.whonix_apt_list, whonix_apt_repo_disabled)

    def test_whonix_gw_14_clearnet_repo_disabled(self):
        whonix_apt_repo_disabled = "#deb https://deb.whonix.org stretch main contrib non-free"  # noqa
        self.assertFileHasLine(self.whonix_apt_list, whonix_apt_repo_disabled)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(Whonix_Gateway_14_Tests)
    return suite
